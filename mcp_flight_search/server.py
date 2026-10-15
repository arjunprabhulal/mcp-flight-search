"""MCP server: flight search tools over stdio or Streamable HTTP."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date
from typing import Annotated

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_flight_search import __version__
from mcp_flight_search.flights import Flight, search_flights

AirportCode = Annotated[str, Field(pattern=r"^\s*[A-Za-z]{3}\s*$", description="IATA airport code, such as JFK or LAX")]


def create_server() -> MCPServer:
    server = MCPServer(
        "mcp-flight-search",
        title="Flight Search",
        description="Search Google Flights through SerpApi.",
        version=__version__,
        instructions="Use search_flights_tool with IATA airport codes and ISO dates (YYYY-MM-DD). Needs SERP_API_KEY.",
    )

    @server.tool(
        title="Search flights",
        annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True),
    )
    async def search_flights_tool(
        origin: AirportCode,
        destination: AirportCode,
        outbound_date: Annotated[date, Field(description="Departure date, YYYY-MM-DD")],
        return_date: Annotated[date | None, Field(description="Return date for a round trip, YYYY-MM-DD")] = None,
    ) -> list[Flight]:
        """Search Google Flights for one-way or round-trip flights between two airports."""
        return await search_flights(origin, destination, outbound_date, return_date)

    @server.tool(title="Server status", annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    def server_status() -> dict[str, str]:
        """Check that the flight search server is running."""
        return {"status": "online", "version": __version__}

    return server


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="mcp-flight-search", description="MCP server for Google Flights search (SerpApi)")
    parser.add_argument("--connection_type", choices=["stdio", "http"], default="stdio",
                        help="stdio (default) for MCP clients that start the server, or http for Streamable HTTP")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=3001, help="HTTP port (default 3001)")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()
    # Logs go to stderr: in stdio mode stdout carries the MCP messages.
    logging.basicConfig(stream=sys.stderr, level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                        format="%(levelname)s %(name)s: %(message)s")
    server = create_server()
    if args.connection_type == "http":
        server.run("streamable-http", host=args.host, port=args.port)
    else:
        server.run("stdio")


if __name__ == "__main__":
    main()
