# Deploying VeryChic MCP for Claude.ai / Cowork

Cloud Claude clients only talk to **remote** MCP servers over HTTPS. To use VeryChic MCP from
claude.ai or Cowork, self-host it in `streamable-http` mode and add it as a custom connector.

## Option A — Docker (anywhere)

```bash
docker build -t verychic-mcp .
docker run -p 8000:8000 verychic-mcp
# serves streamable-http on http://localhost:8000 (put it behind HTTPS for real use)
```

## Option B — Render (1-click-ish)

This repo ships a `render.yaml`. On [Render](https://render.com): New → Blueprint → point it at your
fork. It builds the `Dockerfile` and exposes the server over HTTPS. Render injects `$PORT`
automatically; the container's start command already honors it.

## Add it to Claude.ai / Cowork

1. Copy your deployment's HTTPS URL (e.g. `https://verychic-mcp.onrender.com`).
2. Claude settings → Connectors → **Add custom connector** → paste the URL.
3. The three `verychic_*` tools become available in your chats.

## Notes

- The server is **anonymous and read-only**; no secrets or environment variables are required.
- Keep it private to you / low-traffic — see the disclaimer in the README.
- Default bind host is `127.0.0.1` for local stdio use; the Docker image binds `0.0.0.0` so the
  platform can route to it.
