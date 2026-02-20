"""REST client for Portainer API."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PortainerClient:
    """Portainer REST API client with API-key auth.

    Args:
        base_url: The Portainer instance base URL (trailing slash is stripped).
        api_key: API key used in the ``X-API-Key`` header.
        default_endpoint: Default Docker endpoint ID used when none is specified.

    Attributes:
        base_url: The normalised Portainer base URL.
        default_endpoint: Default Docker endpoint ID.
    """

    def __init__(self, base_url: str, api_key: str, default_endpoint: int = 4) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_endpoint = default_endpoint
        self._http = httpx.Client(
            base_url=f"{self.base_url}/api",
            timeout=30.0,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            },
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def get(self, path: str) -> Any:
        """Send a GET request and return parsed JSON.

        Args:
            path: API path relative to ``/api``.

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: If the response status indicates an error.
        """
        resp = self._http.get(path)
        resp.raise_for_status()
        return resp.json()

    def get_raw(self, path: str) -> str:
        """Send a GET request and return the raw response text.

        Args:
            path: API path relative to ``/api``.

        Returns:
            Raw response body as a string.

        Raises:
            httpx.HTTPStatusError: If the response status indicates an error.
        """
        resp = self._http.get(path)
        resp.raise_for_status()
        return resp.text

    def post(self, path: str, data: Any = None) -> int:
        """Send a POST request and return the HTTP status code.

        Args:
            path: API path relative to ``/api``.
            data: JSON-serialisable payload (defaults to empty dict).

        Returns:
            HTTP status code of the response.

        Raises:
            httpx.HTTPStatusError: If the response status indicates an error.
        """
        resp = self._http.post(path, json=data or {})
        resp.raise_for_status()
        return resp.status_code

    def put(self, path: str, data: Any = None) -> Any:
        """Send a PUT request and return parsed JSON.

        Args:
            path: API path relative to ``/api``.
            data: JSON-serialisable payload.

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: If the response status indicates an error.
        """
        resp = self._http.put(path, json=data)
        resp.raise_for_status()
        return resp.json()

    def resolve_container(self, name: str, endpoint: int | None = None) -> str:
        """Resolve container name to container ID.

        Args:
            name: Container name (without leading /).
            endpoint: Endpoint ID (uses default if not set).

        Returns:
            Container ID string.

        Raises:
            ValueError: If container is not found.
        """
        ep = endpoint or self.default_endpoint
        containers = self.get(f"/endpoints/{ep}/docker/containers/json?all=true")
        for c in containers:
            names = [n.lstrip("/") for n in c.get("Names", [])]
            if name in names:
                return c["Id"]
        raise ValueError(f"Container '{name}' not found on endpoint {ep}")
