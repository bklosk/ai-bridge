# ai-bridge

MCP (Model Context Protocol) server skeleton using Python and [uv](https://docs.astral.sh/uv/).

## Setup

```bash
uv sync
```

## Run

**Stdio** (default; for Cursor, CLI, and other MCP clients):

```bash
uv run server.py
```

**Streamable HTTP** (e.g. for [MCP Inspector](https://github.com/modelcontextprotocol/inspector)):

Edit `server.py` and use `mcp.run(transport="streamable-http")`, then:

```bash
uv run server.py
```

Connect the inspector to `http://localhost:8000/mcp`.

## Skeleton contents

- **Tools:** `ping` — returns `"pong"`.
- **Resources:** `ai-bridge://status` — returns server status text.
- **Prompts:** `example_prompt` — takes a `topic` and returns a prompt string.

Add more tools, resources, and prompts in `server.py` and re-run.
