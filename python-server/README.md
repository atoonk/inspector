# Python MCP Inspector Proxy

This directory contains a minimal Python implementation of the MCP Inspector proxy
server. It mirrors the basic behaviour of the original Node.js server and can
serve the existing client UI.

## Running

Before starting the Python server you must build the inspector client once with
Node.js:

```bash
npm install                # if you haven't already
npm run build-client       # produces client/dist
```

Once built, run the Python server:

```bash
python app.py
```

The server listens on `0.0.0.0:6277` by default. Override the host and port
using the `HOST` and `PORT` environment variables.

## Endpoints

- `/` – Serves the inspector client files.
- `/health` – Simple health check returning `{"status": "ok"}`.
- `/config` – Returns default configuration based on the `MCP_ENV_VARS`,
  `MCP_PROXY_COMMAND`, and `MCP_PROXY_ARGS` environment variables.
- `/sse` – Simple Server-Sent Events endpoint that clients can subscribe to.
- `/message` – Accepts posted messages and broadcasts them to connected SSE
  clients.

This implementation is intentionally lightweight and avoids external
dependencies so it can run in restricted environments.
