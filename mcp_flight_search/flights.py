"""Flight search through the SerpApi Google Flights engine."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import date
from typing import Any

import serpapi
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

logger = logging.getLogger("mcp_flight_search")

API_KEY_ENV = "SERP_API_KEY"


class Flight(BaseModel):
    """One itinerary from Google Flights' best results."""

    airline: str = Field(description="Airline of the first leg")
    price: str = Field(description="Total price in USD, or N/A")
    duration: str = Field(description="Total duration, such as '345 min'")
    stops: str = Field(description="'Nonstop' or the number of stops")
    layovers: list[str] = Field(default_factory=list, description="Layover airports and durations for connecting flights")
    departure: str = Field(description="First departure airport and time")
    arrival: str = Field(description="First leg's arrival airport and time")
    travel_class: str = Field(description="Cabin class, such as Economy")
    airline_logo: str | None = Field(default=None, description="URL of the airline's logo")


class FlightSearchError(ToolError):
    """The search couldn't run or SerpApi refused it: reported to the model as a tool error with this message."""


def api_key() -> str:
    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        raise FlightSearchError(f"Set {API_KEY_ENV} to your SerpApi key (serpapi.com) to search flights.")
    return key


def search_params(origin: str, destination: str, outbound_date: date, return_date: date | None = None) -> dict[str, Any]:
    """SerpApi Google Flights parameters: one-way (type 2), or round trip (type 1) with a return date."""
    params: dict[str, Any] = {
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "currency": "USD",
        "departure_id": origin.strip().upper(),
        "arrival_id": destination.strip().upper(),
        "outbound_date": outbound_date.isoformat(),
        "type": "2",
    }
    if return_date:
        params["return_date"] = return_date.isoformat()
        params["type"] = "1"
    return params


def _airport(leg: dict[str, Any], key: str) -> str:
    airport = leg.get(key) or {}
    if not isinstance(airport, dict):
        return str(airport) or "Unknown"
    return f"{airport.get('name', 'Unknown')} ({airport.get('id', '???')}) at {airport.get('time', 'N/A')}"


def _layover_duration(minutes: Any) -> str | None:
    if not isinstance(minutes, int) or minutes <= 0:
        return None
    return f"{minutes // 60}h {minutes % 60}m" if minutes >= 60 else f"{minutes}m"


def _layovers(itinerary: dict[str, Any], legs: list[dict[str, Any]]) -> list[str]:
    layovers = itinerary.get("layovers") or []
    if layovers:
        details = []
        for lo in layovers:
            if not isinstance(lo, dict):
                continue
            name = lo.get("name", "Unknown")
            code = lo.get("id")
            airport = f"{name} ({code})" if code else name
            meta = [m for m in (_layover_duration(lo.get("duration")), "overnight" if lo.get("overnight") else None) if m]
            details.append(f"{airport} - {', '.join(meta)}" if meta else airport)
        return details
    stops = []
    for leg in legs[:-1]:
        airport = leg.get("arrival_airport")
        if isinstance(airport, dict) and (airport.get("name") or airport.get("id")):
            name = airport.get("name", "Unknown")
            code = airport.get("id")
            stops.append(f"{name} ({code})" if code else name)
    return stops


def format_flights(results: dict[str, Any]) -> list[Flight]:
    """Every itinerary in a SerpApi response, the best ones first, with the first leg's details for each.
    Some flights (often regional carriers) appear only under other_flights."""
    flights = []
    for itinerary in [*(results.get("best_flights") or []), *(results.get("other_flights") or [])]:
        legs = itinerary.get("flights") or []
        if not legs:
            continue
        first = legs[0]
        duration = itinerary.get("total_duration")
        flights.append(Flight(
            airline=first.get("airline", "Unknown airline"),
            price=str(itinerary.get("price", "N/A")),
            duration=f"{duration} min" if duration is not None else "N/A",
            stops="Nonstop" if len(legs) == 1 else f"{len(legs) - 1} stop(s)",
            layovers=_layovers(itinerary, legs),
            departure=_airport(first, "departure_airport"),
            arrival=_airport(first, "arrival_airport"),
            travel_class=first.get("travel_class", "Economy"),
            airline_logo=first.get("airline_logo") or None,
        ))
    return flights


def _search(params: dict[str, Any], key: str) -> dict[str, Any]:
    try:
        return dict(serpapi.Client(api_key=key).search(params))
    except serpapi.SerpApiError as error:
        raise FlightSearchError(f"SerpApi: {error}") from error


async def search_flights(origin: str, destination: str, outbound_date: date, return_date: date | None = None) -> list[Flight]:
    """Search Google Flights. The API key is never logged."""
    key = api_key()
    params = search_params(origin, destination, outbound_date, return_date)
    logger.info("Searching flights %s -> %s on %s", params["departure_id"], params["arrival_id"], params["outbound_date"])
    results = await asyncio.to_thread(_search, params, key)
    if results.get("error"):
        raise FlightSearchError(f"SerpApi: {results['error']}")
    return format_flights(results)
