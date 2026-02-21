"""Configuration for Portainer MCP Server."""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

CREDS_PATH = Path.home() / ".config" / "portainer" / "credentials.json"


class Settings(BaseSettings):
    """Settings loaded from credentials file or environment variables.

    Priority order:
    1. ~/.config/portainer/credentials.json
    2. Environment variables (PORTAINER_URL, PORTAINER_API_KEY) - override

    Attributes:
        portainer_url: The Portainer instance base URL.
        portainer_api_key: API key for Portainer authentication.
        portainer_default_endpoint: Default Docker endpoint ID.
        portainer_transport: MCP transport type (``stdio`` or ``http``).
        portainer_log_level: Logging level name.
    """

    portainer_url: str = ""
    portainer_api_key: str = ""
    portainer_default_endpoint: int = 1
    portainer_transport: str = "stdio"
    portainer_log_level: str = "INFO"
    portainer_read_only: bool = False

    model_config = {"env_prefix": ""}

    def load_credentials(self) -> dict[str, Any]:
        """Load credentials with config-file-first, env-override pattern.

        Returns:
            Dict with url, api_key, and optional default_endpoint.
        """
        creds: dict[str, Any] = {}

        # 1. FIRST: Load from environment variables (base/fallback)
        if self.portainer_url:
            creds["url"] = self.portainer_url
        if self.portainer_api_key:
            creds["api_key"] = self.portainer_api_key
        if self.portainer_default_endpoint:
            creds["default_endpoint"] = self.portainer_default_endpoint

        # 2. THEN: Override with credentials.json file (takes priority)
        if CREDS_PATH.exists():
            try:
                file_creds: dict[str, Any] = json.loads(CREDS_PATH.read_text())

                if "url" in file_creds:
                    creds["url"] = file_creds["url"]
                if "api_key" in file_creds:
                    creds["api_key"] = file_creds["api_key"]
                elif "token" in file_creds:  # Legacy support
                    creds["api_key"] = file_creds["token"]
                if "default_endpoint" in file_creds:
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
