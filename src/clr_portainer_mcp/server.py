"""Portainer MCP Server — FastMCP tools for Docker container management."""

import argparse
import logging
import logging.config
import sys
from typing import Any

from fastmcp import FastMCP

from clr_portainer_mcp.config import Settings
from clr_portainer_mcp.portainer_client import PortainerClient
from clr_portainer_mcp.middleware import ToolValidationMiddleware

mcp = FastMCP("Portainer")
mcp.add_middleware(ToolValidationMiddleware())
_client: PortainerClient | None = None

WRITE_TOOLS = ["portainer_start", "portainer_stop", "portainer_restart", "portainer_redeploy"]

# Imported here (not at the top) on purpose: annotations.py needs ``mcp`` from
# this module, so importing it before the ``mcp = FastMCP(...)`` line above
# would be a circular import. Do not move.
from clr_portainer_mcp.annotations import read_tool, write_tool  # noqa: E402


# ── Status tools ─────────────────────────────────────────────────────


@read_tool
def portainer_status() -> dict[str, Any]:
    """Get Portainer server version and status.

    Returns server version and instance info.
    """
    return _client.get("/status")


@read_tool
def portainer_endpoints() -> list[dict[str, Any]]:
    """List all Docker environments (endpoints).

    Returns list of endpoints with id, name, type (local/remote), and status.
    """
    endpoints = _client.get("/endpoints")
    return [
        {
            "id": ep.get("Id"),
            "name": ep.get("Name"),
            "type": "local" if ep.get("Type") == 1 else "remote",
            "status": "online" if ep.get("Status") == 1 else "offline",
            "url": ep.get("URL"),
        }
        for ep in endpoints
    ]


# ── Container tools ──────────────────────────────────────────────────


@read_tool
def portainer_containers(endpoint: int | None = None) -> list[dict[str, Any]]:
    """List all containers on an endpoint.

    Args:
        endpoint: Endpoint ID (default: 4, the production remote endpoint).

    Returns list of containers with name, state, status, image, and id.
    """
    ep = endpoint or _client.default_endpoint
    containers = _client.get(f"/endpoints/{ep}/docker/containers/json?all=true")
    return [
        {
            "name": c.get("Names", [""])[0].lstrip("/"),
            "id": c.get("Id", "")[:12],
            "state": c.get("State"),
            "status": c.get("Status"),
            "image": c.get("Image"),
        }
        for c in containers
    ]


@read_tool
def portainer_logs(
    container: str,
    endpoint: int | None = None,
    tail: int = 100,
) -> str:
    """Get recent logs from a container.

    Args:
        container: Container name (exact match, e.g. "steinbergerraum-web-1").
        endpoint: Endpoint ID (default: 4).
        tail: Number of log lines to return (default: 100).

    Returns log output as text.
    """
    ep = endpoint or _client.default_endpoint
    cid = _client.resolve_container(container, ep)
    raw = _client.get_raw(
        f"/endpoints/{ep}/docker/containers/{cid}/logs"
        f"?stdout=true&stderr=true&tail={tail}"
    )
    # Strip Docker log framing bytes (first 8 bytes per line)
    lines = []
    for line in raw.split("\n"):
        if len(line) > 8:
            lines.append(line[8:])
        else:
            lines.append(line)
    return "\n".join(lines)


@write_tool
def portainer_start(container: str, endpoint: int | None = None) -> str:
    """Start a stopped container.

    Args:
        container: Container name (exact match).
        endpoint: Endpoint ID (default: 4).

    Returns confirmation message.
    """
    ep = endpoint or _client.default_endpoint
    cid = _client.resolve_container(container, ep)
    _client.post(f"/endpoints/{ep}/docker/containers/{cid}/start")
    return f"Container '{container}' started"


@write_tool
def portainer_stop(container: str, endpoint: int | None = None) -> str:
    """Stop a running container.

    Args:
        container: Container name (exact match).
        endpoint: Endpoint ID (default: 4).

    Returns confirmation message.
    """
    ep = endpoint or _client.default_endpoint
    cid = _client.resolve_container(container, ep)
    _client.post(f"/endpoints/{ep}/docker/containers/{cid}/stop")
    return f"Container '{container}' stopped"


@write_tool
def portainer_restart(container: str, endpoint: int | None = None) -> str:
    """Restart a container.

    Args:
        container: Container name (exact match).
        endpoint: Endpoint ID (default: 4).

    Returns confirmation message.
    """
    ep = endpoint or _client.default_endpoint
    cid = _client.resolve_container(container, ep)
    _client.post(f"/endpoints/{ep}/docker/containers/{cid}/restart")
    return f"Container '{container}' restarted"


# ── Stack tools ──────────────────────────────────────────────────────


@read_tool
def portainer_stacks() -> list[dict[str, Any]]:
    """List all stacks.

    Returns list of stacks with id, name, status, endpoint, and type.
    """
    stacks = _client.get("/stacks")
    return [
        {
            "id": s.get("Id"),
            "name": s.get("Name"),
            "status": "active" if s.get("Status") == 1 else "inactive",
            "endpoint_id": s.get("EndpointId"),
            "type": s.get("Type"),
        }
        for s in stacks
    ]


@read_tool
def portainer_stack_info(stack_id: int) -> dict[str, Any]:
    """Get detailed info for a specific stack.

    Args:
        stack_id: The numeric stack ID.

    Returns stack details including git config and environment.
    """
    s = _client.get(f"/stacks/{stack_id}")
    git_config = s.get("GitConfig") or {}
    return {
        "id": s.get("Id"),
        "name": s.get("Name"),
        "status": "active" if s.get("Status") == 1 else "inactive",
        "endpoint_id": s.get("EndpointId"),
        "git_url": git_config.get("URL"),
        "git_ref": git_config.get("ReferenceName"),
        "update_date": s.get("UpdateDate"),
        "env_count": len(s.get("Env", [])),
    }


@write_tool
def portainer_redeploy(stack_id: int) -> str:
    """Pull latest from git and redeploy a stack.

    Fetches current stack config (env vars, git credentials) and triggers
    a git-based redeploy with image pull.

    Args:
        stack_id: The numeric stack ID to redeploy.

    Returns confirmation message or error.
    """
    stack = _client.get(f"/stacks/{stack_id}")
    endpoint_id = stack["EndpointId"]
    env_vars = stack.get("Env", [])
    git_config = stack.get("GitConfig") or {}
    git_auth = git_config.get("Authentication") or {}
    git_cred_id = git_auth.get("GitCredentialID", 0)

    payload = {
        "env": env_vars,
        "prune": False,
        "pullImage": True,
        "repositoryAuthentication": True,
        "repositoryGitCredentialID": git_cred_id,
    }

    result = _client.put(
        f"/stacks/{stack_id}/git/redeploy?endpointId={endpoint_id}",
        payload,
    )

    name = result.get("Name", f"stack {stack_id}")
    return f"Stack '{name}' redeployed successfully"


# ── Main entry point ─────────────────────────────────────────────────


def main() -> None:
    """Main entry point for the Portainer MCP server."""
    global _client

    settings = Settings()

    parser = argparse.ArgumentParser(description="Portainer MCP Server")
    parser.add_argument(
        "--transport", type=str, choices=["stdio", "http"], default=None
    )
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument("--portainer-url", type=str, default=None)
    parser.add_argument("--portainer-api-key", type=str, default=None)
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=None,
        help="Run in read-only mode (hide write tools)",
    )
    args = parser.parse_args()

    transport = args.transport or settings.portainer_transport
    log_level = args.log_level or settings.portainer_log_level

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                    "stream": "ext://sys.stderr",
                }
            },
            "root": {"level": log_level, "handlers": ["console"]},
        }
    )

    logger = logging.getLogger(__name__)

    creds = settings.load_credentials()
    url = args.portainer_url or creds.get("url", "")
    api_key = args.portainer_api_key or creds.get("api_key", "")
    default_endpoint = creds.get("default_endpoint", 1)

    if not api_key:
        logger.error("PORTAINER_API_KEY is required")
        sys.exit(1)

    logger.info("Starting Portainer MCP Server (%s)", url)
    _client = PortainerClient(url, api_key, default_endpoint)

    read_only = args.read_only if args.read_only is not None else settings.portainer_read_only
    if read_only and WRITE_TOOLS:
        for name in WRITE_TOOLS:
            mcp.remove_tool(name)
        logger.info("Read-only mode: %d write tools removed", len(WRITE_TOOLS))

    try:
        if transport == "stdio":
            mcp.run(transport="stdio")
        else:
            mcp.run(transport="http", host=args.host, port=args.port)
    except Exception as e:
        logger.error("Failed to start MCP server: %s", e)
        sys.exit(1)
    finally:
        _client.close()


if __name__ == "__main__":
    main()
