"""Configuration for Portainer MCP Server."""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

CREDS_PATH = Path.home() / ".config" / "portainer" / "credentials.json"


class Settings(BaseSettings):
    """Settings loaded from environment variables or credentials file.

    Priority order:
    1. Environment variables (PORTAINER_URL, PORTAINER_API_KEY)
    2. ~/.config/portainer/credentials.json
    """

    portainer_url: str = ""
    portainer_api_key: str = ""
    portainer_default_endpoint: int = 1
    portainer_transport: str = "stdio"
    portainer_log_level: str = "INFO"

    model_config = {"env_prefix": ""}

    def load_credentials(self) -> dict[str, Any]:
        """Load credentials with env-first, config-file-fallback pattern.

        Returns:
            Dict with url, api_key, and optional default_endpoint.
        """
        creds: dict[str, Any] = {}

        # 1. FIRST: Check environment variables
        if self.portainer_url:
            creds["url"] = self.portainer_url
        if self.portainer_api_key:
            creds["api_key"] = self.portainer_api_key
        if self.portainer_default_endpoint:
            creds["default_endpoint"] = self.portainer_default_endpoint

        # If we have all required creds from env, return early
        if creds.get("url") and creds.get("api_key"):
            logger.info("Using Portainer credentials from environment variables")
            return creds

        # 2. FALLBACK: Check credentials.json file
        if CREDS_PATH.exists():
            try:
                file_creds: dict[str, Any] = json.loads(CREDS_PATH.read_text())

                # Only use file values if NOT already set by env vars
                if "url" in file_creds and not creds.get("url"):
                    creds["url"] = file_creds["url"]
                if "api_key" in file_creds and not creds.get("api_key"):
                    creds["api_key"] = file_creds["api_key"]
                if "token" in file_creds and not creds.get("api_key"):  # Legacy support
                    creds["api_key"] = file_creds["token"]
                if "default_endpoint" in file_creds and not creds.get("default_endpoint"):
                    creds["default_endpoint"] = file_creds["default_endpoint"]

                logger.info(f"Loaded Portainer credentials from {CREDS_PATH}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load {CREDS_PATH}: {e}")

        if not (creds.get("url") and creds.get("api_key")):
            logger.warning(
                "No Portainer credentials configured. Set PORTAINER_URL/PORTAINER_API_KEY "
                f"env vars or create {CREDS_PATH}"
            )

        return creds
