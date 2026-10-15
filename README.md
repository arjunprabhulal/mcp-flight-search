# MCP Flight Search

<!-- mcp-name: io.github.arjunprabhulal/mcp-flight-search -->

An MCP server that searches Google Flights through [SerpApi](https://serpapi.com/google-flights-api), for Claude, Cursor and other MCP clients. One-way and round-trip searches by IATA airport code, with prices, durations, stops and times.

[![CI](https://github.com/arjunprabhulal/mcp-flight-search/actions/workflows/ci.yml/badge.svg)](https://github.com/arjunprabhulal/mcp-flight-search/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mcp-flight-search)](https://pypi.org/project/mcp-flight-search/)

## Requirements

- Python 3.10 or later (or [uv](https://docs.astral.sh/uv/))
- A SerpApi key in `SERP_API_KEY` (serpapi.com has a free tier)

## Use it from an MCP client

Add it to your client's MCP configuration (Claude Desktop, Claude Code, Cursor, ...):

```json
{
  "mcpServers": {
    "flight-search": {
      "command": "uvx",
      "args": ["mcp-flight-search"],
      "env": { "SERP_API_KEY": "your-serpapi-key" }
    }
  }
}
```

Or install it with `pip install mcp-flight-search` and use `"command": "mcp-flight-search"`.

## Run it yourself

```bash
export SERP_API_KEY="your-serpapi-key"
mcp-flight-search                                    # stdio (default)
mcp-flight-search --connection_type http --port 3001 # Streamable HTTP at http://127.0.0.1:3001/mcp
```

`LOG_LEVEL=DEBUG` shows more detail on stderr. The API key is never logged.

With Docker:

```bash
docker build -t mcp-flight-search .
docker run -i --rm -e SERP_API_KEY=your-serpapi-key mcp-flight-search
```

## Tools

| Tool | What it does |
| --- | --- |
| `search_flights_tool` | Flights between two airports. `origin`, `destination`: IATA codes such as `ATL`, `LAX`. `outbound_date`: `YYYY-MM-DD`. `return_date` (optional): `YYYY-MM-DD` for a round trip. Returns structured results: airline, price (USD), duration, stops, departure, arrival, cabin class. |
| `server_status` | Checks the server is running and reports its version. |

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
```

## License

MIT
