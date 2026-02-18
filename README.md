# clr-portainer-mcp

Portainer container/stack management

## Install

```bash
pip install clr-portainer-mcp
# or
uvx clr-portainer-mcp
```

## Configuration

**Preferred:** Configuration file at `~/.config/portainer/credentials.json` (chmod 600):

```json
{
  "url": "https://portainer.example.com",
  "token": "your-api-token",
  "username": "admin",
  "password": "your-password"
}
```

**Note:** Either token OR username/password is required.

**Alternative:** Environment variables are also supported:

| Variable | Description | Example |
|----------|-------------|---------|
| `PORTAINER_URL` | Portainer URL | `https://portainer.example.com` |
| `PORTAINER_TOKEN` | API token | `your-api-token` |
| `PORTAINER_USERNAME` | Username (if not using token) | `admin` |
| `PORTAINER_PASSWORD` | Password (if not using token) | `your-password` |

See `--help` for additional options:

```bash
clr-portainer-mcp --help
```

## Development

```bash
git clone https://github.com/clearminds/clr-portainer-mcp.git
cd clr-portainer-mcp
uv sync
uv run clr-portainer-mcp
```

## License

MIT
