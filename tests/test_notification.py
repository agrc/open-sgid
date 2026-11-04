import json
import os
import subprocess
import sys
import urllib.error

import pytest

from cloudb import config_loader, notification


def test_send_report_posts_bounded_human_readable_message(mocker):
    response = mocker.MagicMock(status=200)
    response.__enter__.return_value = response
    urlopen = mocker.patch.object(notification.urllib.request, "urlopen", return_value=response)

    assert notification.send_report(
        {
            "status": "success",
            "duration_seconds": 1.23,
            "phases": [{"name": "trim", "status": "success", "duration_seconds": 0.1}],
            "logs": "x" * 5000,
        },
        "https://chat.example/webhook",
    )

    request = urlopen.call_args.args[0]
    message = json.loads(request.data)["text"]
    assert len(message) <= notification.MAX_MESSAGE_LENGTH
    assert "phase trim: success (0.1s)" in message


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (urllib.error.HTTPError("https://chat.example/secret", 500, "bad", {}, None), "HTTP 500"),
        (urllib.error.URLError("offline"), "URLError"),
        (TimeoutError(), "TimeoutError"),
    ],
)
def test_send_report_has_safe_http_diagnostics(mocker, exception, message):
    mocker.patch.object(notification.urllib.request, "urlopen", side_effect=exception)

    with pytest.raises(notification.NotificationError, match=message) as raised:
        notification.send_report({"status": "failure"}, "https://chat.example/secret")

    assert "chat.example" not in str(raised.value)


@pytest.mark.parametrize("webhook", ["not-a-url", "ftp://chat.example/secret", "https://"])
def test_send_report_rejects_malformed_webhook(webhook):
    with pytest.raises(notification.NotificationError, match="URL is invalid"):
        notification.send_report({"status": "test"}, webhook)


def test_send_report_rejects_truthy_non_string_webhook():
    with pytest.raises(notification.NotificationError, match="URL is invalid"):
        notification.send_report({"status": "test"}, 123)


def test_send_report_is_disabled_without_webhook():
    assert notification.send_report({"status": "success"}) is False
    with pytest.raises(notification.NotificationError, match="googleChatWebhookUrl"):
        notification.send_report({"status": "test"}, required=True)


def test_load_webhook_uses_connection_json_without_db_fields(tmp_path, monkeypatch):
    path = tmp_path / "connection.json"
    path.write_text('{"googleChatWebhookUrl": "https://chat.example/test"}', encoding="utf-8")
    monkeypatch.setenv("CLOUDB_CONFIG", str(path))

    assert notification.load_webhook() == "https://chat.example/test"


def test_load_webhook_uses_shared_fallback_path(tmp_path, monkeypatch):
    path = tmp_path / "connection.json"
    path.write_text('{"googleChatWebhookUrl": "https://chat.example/fallback"}', encoding="utf-8")
    monkeypatch.delenv("CLOUDB_CONFIG", raising=False)
    monkeypatch.setattr(config_loader, "DEFAULT_SECRETS_PATH", path)
    monkeypatch.setattr(config_loader, "LOCAL_SECRETS_PATH", tmp_path / "missing.json")

    assert notification.load_webhook() == "https://chat.example/fallback"


def test_load_webhook_missing_field_disables_optional_reporting(tmp_path, monkeypatch):
    path = tmp_path / "connection.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CLOUDB_CONFIG", str(path))

    with pytest.raises(notification.NotificationError, match="googleChatWebhookUrl"):
        notification.load_webhook()


def test_load_webhook_reports_missing_connection_config(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDB_CONFIG", str(tmp_path / "missing.json"))
    monkeypatch.setattr(config_loader, "LOCAL_SECRETS_PATH", tmp_path / "also-missing.json")

    with pytest.raises(notification.NotificationError, match="configuration unavailable"):
        notification.load_webhook()


def test_notification_cli_success_without_db_fields(tmp_path, monkeypatch, capsys):
    path = tmp_path / "connection.json"
    path.write_text('{"googleChatWebhookUrl": "https://chat.example/test"}', encoding="utf-8")
    monkeypatch.setenv("CLOUDB_CONFIG", str(path))
    monkeypatch.setattr(notification, "send_report", lambda report, webhook, required: True)

    notification.main()

    assert "sent" in capsys.readouterr().out


def test_notification_cli_failure_is_sanitized(tmp_path, monkeypatch, capsys):
    path = tmp_path / "connection.json"
    path.write_text('{"googleChatWebhookUrl": "https://chat.example/secret"}', encoding="utf-8")
    monkeypatch.setenv("CLOUDB_CONFIG", str(path))
    monkeypatch.setattr(
        notification,
        "send_report",
        lambda report, webhook, required: (_ for _ in ()).throw(notification.NotificationError("HTTP 500")),
    )

    with pytest.raises(SystemExit) as raised:
        notification.main()

    assert raised.value.code == 1
    error_output = capsys.readouterr().err
    assert "HTTP 500" in error_output
    assert "chat.example" not in error_output


def test_notification_cli_rejects_truthy_non_string_webhook(tmp_path, monkeypatch, capsys):
    path = tmp_path / "connection.json"
    path.write_text('{"googleChatWebhookUrl": 123}', encoding="utf-8")
    monkeypatch.setenv("CLOUDB_CONFIG", str(path))

    with pytest.raises(SystemExit) as raised:
        notification.main()

    assert raised.value.code == 1
    assert "URL is invalid" in capsys.readouterr().err


def test_notification_import_does_not_load_database_modules(tmp_path):
    environment = {"PATH": os.environ["PATH"], "PYTHONPATH": os.pathsep.join(sys.path)}
    environment["CLOUDB_CONFIG"] = str(tmp_path / "unused.json")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import cloudb.notification; "
                "print(any(name in sys.modules for name in ('cloudb.config', 'osgeo', 'pyodbc')))"
            ),
        ],
        check=False,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "False"


def test_report_includes_attempt_and_encoded_logging_link(monkeypatch):
    monkeypatch.setenv("CLOUD_RUN_EXECUTION", "cloudb-123")
    monkeypatch.setenv("CLOUD_RUN_TASK_ATTEMPT", "2")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "project-1")
    monkeypatch.setenv("CLOUD_RUN_JOB", "nightly cloudb")

    report = notification.build_sync_report("failure", 1.25, [])

    assert report["attempt"] == "2"
    assert "nightly+cloudb" in report["logs"]
    assert "%22cloudb-123%22" in report["logs"]
