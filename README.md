# portainer-mcp-server

Portainer container/stack management

## Install

```bash
pip install portainer-mcp-server
# or
uvx portainer-mcp-server
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
portainer-mcp-server --help
```

## Development

```bash
git clone https://github.com/clearminds/portainer-mcp-server.git
cd portainer-mcp-server
uv sync
uv run portainer-mcp-server
```

## License

MIT
