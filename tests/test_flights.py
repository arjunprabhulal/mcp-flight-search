from datetime import date

import pytest

from mcp_flight_search import flights
from mcp_flight_search.flights import FlightSearchError, format_flights, search_params

SAMPLE = {"best_flights": [
    {"price": 289, "total_duration": 330, "flights": [{
        "airline": "Delta", "travel_class": "Economy", "airline_logo": "https://example.com/dl.png",
        "departure_airport": {"name": "Hartsfield-Jackson", "id": "ATL", "time": "2026-11-02 08:00"},
        "arrival_airport": {"name": "Los Angeles", "id": "LAX", "time": "2026-11-02 10:30"}}]},
    {"price": 199, "total_duration": 410, "flights": [{"airline": "United"}, {"airline": "United"}]},
    {"price": 1, "flights": []},
]}


def test_one_way_and_round_trip_params():
    one_way = search_params(" atl ", "lax", date(2026, 11, 2))
    assert one_way["departure_id"] == "ATL" and one_way["arrival_id"] == "LAX"
    assert one_way["type"] == "2" and "return_date" not in one_way and "api_key" not in one_way
    round_trip = search_params("ATL", "LAX", date(2026, 11, 2), date(2026, 11, 9))
    assert round_trip["type"] == "1" and round_trip["return_date"] == "2026-11-09"


def test_format_flights():
    result = format_flights(SAMPLE)
    assert len(result) == 2
    assert result[0].airline == "Delta" and result[0].stops == "Nonstop" and result[0].duration == "330 min"
    assert result[0].departure == "Hartsfield-Jackson (ATL) at 2026-11-02 08:00"
    assert result[1].stops == "1 stop(s)"
    assert format_flights({}) == []


async def test_missing_key(monkeypatch):
    monkeypatch.delenv("SERP_API_KEY", raising=False)
    with pytest.raises(FlightSearchError, match="SERP_API_KEY"):
        await flights.search_flights("ATL", "LAX", date(2026, 11, 2))


async def test_search_uses_serpapi_and_never_logs_the_key(monkeypatch, caplog):
    monkeypatch.setenv("SERP_API_KEY", "secret-key")
    seen = {}

    def fake(params, key):
        seen.update(params=params, key=key)
        return SAMPLE

    monkeypatch.setattr(flights, "_search", fake)
    caplog.set_level("DEBUG")
    result = await flights.search_flights("ATL", "LAX", date(2026, 11, 2))
    assert len(result) == 2 and seen["key"] == "secret-key" and seen["params"]["engine"] == "google_flights"
    assert "secret-key" not in caplog.text


async def test_serpapi_error(monkeypatch):
    monkeypatch.setenv("SERP_API_KEY", "k")
    monkeypatch.setattr(flights, "_search", lambda params, key: {"error": "Invalid API key."})
    with pytest.raises(FlightSearchError, match="Invalid API key"):
        await flights.search_flights("ATL", "LAX", date(2026, 11, 2))
