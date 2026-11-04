"""Shared loading of the Cloud Run database connection JSON."""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)
DEFAULT_SECRETS_PATH = Path("/secrets/db/connection")
LOCAL_SECRETS_PATH = Path(__file__).parent / "secrets" / "db" / "connection"


class ConfigurationError(Exception):
    """Raised when required application configuration is unavailable."""


def load_connection_secrets() -> dict:
    """Load the configured connection JSON, falling back to the local path."""
    configured_path = Path(os.environ.get("CLOUDB_CONFIG", DEFAULT_SECRETS_PATH))

    if configured_path.exists():
        logger.debug("loading secrets from %s", configured_path)
        return json.loads(configured_path.read_text(encoding="utf-8"))

    if LOCAL_SECRETS_PATH.exists():
        logger.debug("loading secrets from %s", LOCAL_SECRETS_PATH)
        return json.loads(LOCAL_SECRETS_PATH.read_text(encoding="utf-8"))

    logger.critical("no secrets file found")
    raise ConfigurationError("no secrets file found")
