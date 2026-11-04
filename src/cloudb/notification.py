"""Google Chat run reports and the database-independent notification test command."""

import logging
import os
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode, urlsplit

from .config_loader import ConfigurationError, load_connection_secrets

logger = logging.getLogger(__name__)
WEBHOOK_KEY = "googleChatWebhookUrl"
MAX_MESSAGE_LENGTH = 4000


class NotificationError(RuntimeError):
    """Raised when a configured Google Chat notification cannot be delivered."""


def load_webhook() -> str:
    """Load the optional webhook from the shared connection JSON."""
    try:
        secrets = load_connection_secrets()
    except ConfigurationError:
        raise NotificationError("connection configuration unavailable") from None
    webhook = secrets.get(WEBHOOK_KEY)
    if not webhook:
        raise NotificationError(f"{WEBHOOK_KEY} is not configured")
    return webhook


def _logging_link() -> str | None:
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    execution = os.getenv("CLOUD_RUN_EXECUTION")
    if not project or not execution:
        return None
    job = os.getenv("CLOUD_RUN_JOB", "cloudb")
    query = (
        f'resource.type="cloud_run_job" resource.labels.job_name="{job}" '
        f'labels."run.googleapis.com/execution_name"="{execution}"'
    )
    return f"https://console.cloud.google.com/logs/query?{urlencode({'project': project, 'query': query})}"


def build_sync_report(status: str, duration: float, phases: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a bounded, credential-free report payload for a sync attempt."""
    report: dict[str, Any] = {
        "status": status,
        "duration_seconds": round(duration, 2),
        "phases": phases,
    }
    execution = os.getenv("CLOUD_RUN_EXECUTION")
    task = os.getenv("CLOUD_RUN_TASK_INDEX")
    attempt = os.getenv("CLOUD_RUN_TASK_ATTEMPT")
    if execution:
        report["execution"] = execution
    if task:
        report["task"] = task
    if attempt:
        report["attempt"] = attempt
    link = _logging_link()
    if link:
        report["logs"] = link
    return report


def _message(report: dict[str, Any]) -> str:
    lines = ["Open SGID sync report"]
    for key in ("status", "duration_seconds", "execution", "task", "attempt", "logs"):
        if key in report:
            lines.append(f"{key}: {report[key]}")
    for phase in report.get("phases", []):
        lines.append(
            f"phase {phase.get('name')}: {phase.get('status')} "
            f"({phase.get('duration_seconds')}s)"
        )
    if len("\n".join(lines)) > MAX_MESSAGE_LENGTH:
        lines = lines[:1] + [line for line in lines[1:] if not line.startswith("logs:")]
    message = "\n".join(lines)
    return message if len(message) <= MAX_MESSAGE_LENGTH else message[: MAX_MESSAGE_LENGTH - 24] + "\n(report truncated)"


def _validate_webhook(webhook: str) -> None:
    if not isinstance(webhook, str):
        raise NotificationError("Google Chat webhook URL is invalid")
    try:
        parsed = urlsplit(webhook)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError
    except (TypeError, ValueError) as error:
        raise NotificationError("Google Chat webhook URL is invalid") from error


def send_report(report: dict[str, Any], webhook: str | None = None, *, required: bool = False) -> bool:
    """Post a report when configured; optionally require configuration and delivery."""
    if not webhook:
        if required:
            raise NotificationError(f"{WEBHOOK_KEY} is not configured")
        return False
    _validate_webhook(webhook)

    try:
        import json

        request = urllib.request.Request(
            webhook,
            data=json.dumps({"text": _message(report)}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    except (TypeError, ValueError) as error:
        raise NotificationError("Google Chat webhook URL is invalid") from error
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise NotificationError(f"Google Chat returned HTTP {response.status}")
    except urllib.error.HTTPError as error:
        raise NotificationError(f"Google Chat returned HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        raise NotificationError(f"Google Chat request failed: {type(error).__name__}") from error
    return True


def main() -> None:
    """Send a notification test without importing the synchronization CLI or database config."""
    try:
        send_report({"status": "notification test"}, load_webhook(), required=True)
    except NotificationError as error:
        print(f"notification test failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print("Google Chat notification sent")


if __name__ == "__main__":
    main()
