"""Configuration for Portainer MCP Server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    portainer_url: str = ""
    portainer_api_key: str = ""
    portainer_default_endpoint: int = 1
    portainer_transport: str = "stdio"
    portainer_log_level: str = "INFO"
