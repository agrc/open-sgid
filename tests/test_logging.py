import json
import os
import subprocess
import sys

import pytest


def run_logging(code, **environment):
    env = os.environ.copy()
    for name in ("CLOUD_RUN_JOB", "K_SERVICE", "LOG_LEVEL"):
        env.pop(name, None)
    env.update(environment)
    return subprocess.run(
        [sys.executable, "-c", "import cloudb; import logging; " + code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("INFO", "INFO: updating tables location.addresspoints\nWARNING: retrying\n"),
        ("DEBUG", "DEBUG: discovering tables\nINFO: updating tables location.addresspoints\nWARNING: retrying\n"),
        ("WARNING", "WARNING: retrying\n"),
    ],
)
def test_local_logging_is_plain_text_and_respects_log_level(level, expected):
    result = run_logging(
        "logger = logging.getLogger('cloudb.main'); "
        "logger.debug('discovering tables'); "
        "logger.info('updating tables %s', 'location.addresspoints'); "
        "logger.warning('retrying')",
        LOG_LEVEL=level,
    )

    assert result.stdout == expected
    assert result.stderr == ""


@pytest.mark.parametrize("environment", [{"CLOUD_RUN_JOB": "cloudb"}, {"K_SERVICE": "cloudb"}])
def test_cloud_run_logging_remains_structured(environment):
    result = run_logging("logging.getLogger('cloudb.main').warning('retrying')", **environment)
    records = [json.loads(line) for line in result.stdout.splitlines()]
    messages = [record for record in records if "message" in record]

    assert len(messages) == 1
    assert messages[0]["severity"] == "WARNING"
    assert messages[0]["message"] == "WARNING:cloudb.main:retrying"
    assert messages[0]["logging.googleapis.com/labels"]["python_logger"] == "cloudb.main"
    assert result.stderr == ""


def test_local_logging_preserves_exception_tracebacks():
    result = run_logging(
        "\ntry:\n"
        "    raise RuntimeError('update failed')\n"
        "except RuntimeError:\n"
        "    logging.getLogger('cloudb.main').exception('could not update table')\n"
    )

    assert result.stdout.startswith("ERROR: could not update table\nTraceback (most recent call last):\n")
    assert result.stdout.endswith("RuntimeError: update failed\n")
    assert result.stderr == ""


def test_local_logging_defaults_to_info():
    result = run_logging("logging.debug('hidden'); logging.info('updating tables')")

    assert result.stdout == "INFO: updating tables\n"
