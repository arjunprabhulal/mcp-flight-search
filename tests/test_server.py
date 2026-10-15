from mcp.client import Client

from mcp_flight_search import flights
from mcp_flight_search.server import create_server
from tests.test_flights import SAMPLE

TRIP = {"origin": "ATL", "destination": "LAX", "outbound_date": "2026-11-02"}


async def test_tools_are_listed_with_schemas():
    async with Client(create_server()) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
    assert set(tools) == {"search_flights_tool", "server_status"}
    search = tools["search_flights_tool"]
    assert set(search.input_schema["required"]) == {"origin", "destination", "outbound_date"}
    assert search.annotations.read_only_hint is True
    assert search.output_schema is not None


async def test_search_tool_returns_structured_flights(monkeypatch):
    monkeypatch.setenv("SERP_API_KEY", "k")
    monkeypatch.setattr(flights, "_search", lambda params, key: SAMPLE)
    async with Client(create_server()) as client:
        result = await client.call_tool("search_flights_tool", TRIP)
    assert not result.is_error
    assert result.structured_content["result"][0]["airline"] == "Delta"


async def test_bad_input_and_missing_key_are_tool_errors(monkeypatch):
    monkeypatch.delenv("SERP_API_KEY", raising=False)
    async with Client(create_server()) as client:
        bad = await client.call_tool("search_flights_tool", {**TRIP, "origin": "ATLANTA"})
        no_key = await client.call_tool("search_flights_tool", TRIP)
    assert bad.is_error and no_key.is_error
    assert "SERP_API_KEY" in no_key.content[0].text
