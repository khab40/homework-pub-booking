"""Ex5 tools. Four tools the agent uses to research an Edinburgh booking.

Each tool:
  1. Reads its fixture from sample_data/ (DO NOT modify the fixtures).
  2. Logs its arguments and output into _TOOL_CALL_LOG (see integrity.py).
  3. Returns a ToolResult with success=True/False, output=dict, summary=str.

The grader checks for:
  * Correct parallel_safe flags (reads True, generate_flyer False).
  * Every tool's results appear in _TOOL_CALL_LOG.
  * Tools fail gracefully on missing fixtures or bad inputs (ToolError,
    not RuntimeError).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sovereign_agent.errors import ToolError
from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolRegistry, ToolResult, _RegisteredTool

from starter.edinburgh_research.integrity import _TOOL_CALL_LOG, record_tool_call

_SAMPLE_DATA = Path(__file__).parent / "sample_data"


def _load_json_fixture(filename: str) -> Any:
    path = _SAMPLE_DATA / filename
    if not path.exists():
        raise ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"required fixture missing: {filename}",
            context={"path": str(path)},
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"fixture is not valid JSON: {filename}",
            context={"path": str(path)},
            cause=exc,
        ) from exc


def _invalid_result(tool_name: str, arguments: dict, message: str) -> ToolResult:
    err = ToolError(
        code="SA_TOOL_INVALID_INPUT",
        message=message,
        context={"tool": tool_name, "arguments": arguments},
    )
    output = {"error": message}
    record_tool_call(tool_name, arguments, output)
    return ToolResult(success=False, output=output, summary=f"{tool_name}: {message}", error=err)


# ---------------------------------------------------------------------------
# TODO 1 — venue_search
# ---------------------------------------------------------------------------
def venue_search(near: str, party_size: int, budget_max_gbp: int = 1000) -> ToolResult:
    """Search for Edinburgh venues near <near> that can seat the party.

    Reads sample_data/venues.json. Filters by:
      * open_now == True
      * area contains <near> (case-insensitive substring match)
      * seats_available_evening >= party_size
      * hire_fee_gbp + min_spend_gbp <= budget_max_gbp

    Returns a ToolResult with:
      output: {"near": ..., "party_size": ..., "results": [<venue dicts>], "count": int}
      summary: "venue_search(<near>, party=<N>): <count> result(s)"

    MUST call record_tool_call(...) before returning so the integrity
    check can see what data was produced.
    """
    arguments = {
        "near": near,
        "party_size": party_size,
        "budget_max_gbp": budget_max_gbp,
    }
    search_count = sum(1 for record in _TOOL_CALL_LOG if record.tool_name == "venue_search")
    if search_count >= 3:
        output = {"error": "too_many_searches", "count": search_count}
        record_tool_call("venue_search", arguments, output)
        return ToolResult(
            success=False,
            output=output,
            summary="STOP calling venue_search; use the results you already have.",
        )

    if not isinstance(near, str) or not near.strip():
        return _invalid_result("venue_search", arguments, "near must be a non-empty string")
    if not isinstance(party_size, int) or party_size <= 0:
        return _invalid_result("venue_search", arguments, "party_size must be a positive integer")
    if not isinstance(budget_max_gbp, int) or budget_max_gbp < 0:
        return _invalid_result(
            "venue_search", arguments, "budget_max_gbp must be a non-negative integer"
        )

    venues = _load_json_fixture("venues.json")
    needle = near.casefold()
    results = [
        venue
        for venue in venues
        if venue.get("open_now") is True
        and needle in str(venue.get("area", "")).casefold()
        and int(venue.get("seats_available_evening", 0)) >= party_size
        and int(venue.get("hire_fee_gbp", 0)) + int(venue.get("min_spend_gbp", 0)) <= budget_max_gbp
    ]
    output = {
        "near": near,
        "party_size": party_size,
        "results": results,
        "count": len(results),
    }
    record_tool_call("venue_search", arguments, output)
    return ToolResult(
        success=True,
        output=output,
        summary=f"venue_search({near}, party={party_size}): {len(results)} result(s)",
    )


# ---------------------------------------------------------------------------
# TODO 2 — get_weather
# ---------------------------------------------------------------------------
def get_weather(city: str, date: str) -> ToolResult:
    """Look up the scripted weather for <city> on <date> (YYYY-MM-DD).

    Reads sample_data/weather.json. Returns:
      output: {"city": str, "date": str, "condition": str, "temperature_c": int, ...}
      summary: "get_weather(<city>, <date>): <condition>, <temp>C"

    If the city or date is not in the fixture, return success=False with
    a clear ToolError (SA_TOOL_INVALID_INPUT). Do NOT raise.

    MUST call record_tool_call(...) before returning.
    """
    arguments = {"city": city, "date": date}
    if not isinstance(city, str) or not city.strip():
        return _invalid_result("get_weather", arguments, "city must be a non-empty string")
    if not isinstance(date, str) or not date.strip():
        return _invalid_result("get_weather", arguments, "date must be a non-empty string")

    weather = _load_json_fixture("weather.json")
    city_key = city.casefold()
    if city_key not in weather:
        return _invalid_result("get_weather", arguments, f"no scripted weather for city {city!r}")
    if date not in weather[city_key]:
        return _invalid_result(
            "get_weather", arguments, f"no scripted weather for {city_key} on {date}"
        )

    output = {"city": city_key, "date": date, **weather[city_key][date]}
    record_tool_call("get_weather", arguments, output)
    return ToolResult(
        success=True,
        output=output,
        summary=(
            f"get_weather({city_key}, {date}): {output['condition']}, {output['temperature_c']}C"
        ),
    )


# ---------------------------------------------------------------------------
# TODO 3 — calculate_cost
# ---------------------------------------------------------------------------
def calculate_cost(
    venue_id: str,
    party_size: int,
    duration_hours: int,
    catering_tier: str = "bar_snacks",
) -> ToolResult:
    """Compute the total cost for a booking.

    Formula:
      base_per_head = base_rates_gbp_per_head[catering_tier]
      venue_mult    = venue_modifiers[venue_id]
      subtotal      = base_per_head * venue_mult * party_size * max(1, duration_hours)
      service       = subtotal * service_charge_percent / 100
      total         = subtotal + service + <venue's hire_fee_gbp + min_spend_gbp>
      deposit_rule  = per deposit_policy thresholds

    Returns:
      output: {
        "venue_id": str,
        "party_size": int,
        "duration_hours": int,
        "catering_tier": str,
        "subtotal_gbp": int,
        "service_gbp": int,
        "total_gbp": int,
        "deposit_required_gbp": int,
      }
      summary: "calculate_cost(<venue>, <party>): total £<N>, deposit £<M>"

    MUST call record_tool_call(...) before returning.
    """
    arguments = {
        "venue_id": venue_id,
        "party_size": party_size,
        "duration_hours": duration_hours,
        "catering_tier": catering_tier,
    }
    if not isinstance(venue_id, str) or not venue_id.strip():
        return _invalid_result("calculate_cost", arguments, "venue_id must be a non-empty string")
    if not isinstance(party_size, int) or party_size <= 0:
        return _invalid_result("calculate_cost", arguments, "party_size must be a positive integer")
    if not isinstance(duration_hours, int):
        return _invalid_result("calculate_cost", arguments, "duration_hours must be an integer")

    catering = _load_json_fixture("catering.json")
    venues = _load_json_fixture("venues.json")
    base_rates = catering["base_rates_gbp_per_head"]
    venue_modifiers = catering["venue_modifiers"]

    if catering_tier not in base_rates:
        return _invalid_result(
            "calculate_cost", arguments, f"unknown catering_tier {catering_tier!r}"
        )
    if venue_id not in venue_modifiers:
        return _invalid_result("calculate_cost", arguments, f"unknown venue_id {venue_id!r}")

    venue = next((v for v in venues if v.get("id") == venue_id), None)
    if venue is None:
        return _invalid_result(
            "calculate_cost", arguments, f"venue_id {venue_id!r} is not in venues fixture"
        )

    billable_hours = max(1, duration_hours)
    subtotal = base_rates[catering_tier] * venue_modifiers[venue_id] * party_size * billable_hours
    service = subtotal * catering["service_charge_percent"] / 100
    venue_cost = int(venue.get("hire_fee_gbp", 0)) + int(venue.get("min_spend_gbp", 0))
    total = subtotal + service + venue_cost

    subtotal_gbp = round(subtotal)
    service_gbp = round(service)
    total_gbp = round(total)
    if total_gbp < 300:
        deposit_required_gbp = 0
    elif total_gbp <= 1000:
        deposit_required_gbp = round(total_gbp * 0.2)
    else:
        deposit_required_gbp = round(total_gbp * 0.3)

    output = {
        "venue_id": venue_id,
        "party_size": party_size,
        "duration_hours": duration_hours,
        "catering_tier": catering_tier,
        "subtotal_gbp": subtotal_gbp,
        "service_gbp": service_gbp,
        "total_gbp": total_gbp,
        "deposit_required_gbp": deposit_required_gbp,
    }
    record_tool_call("calculate_cost", arguments, output)
    return ToolResult(
        success=True,
        output=output,
        summary=(
            f"calculate_cost({venue_id}, {party_size}): "
            f"total £{total_gbp}, deposit £{deposit_required_gbp}"
        ),
    )


# ---------------------------------------------------------------------------
# TODO 4 — generate_flyer
# ---------------------------------------------------------------------------
def generate_flyer(session: Session, event_details: dict) -> ToolResult:
    """Produce a markdown flyer and write it to workspace/flyer.md.

    event_details is expected to contain at least:
      venue_name, venue_address, date, time, party_size, condition,
      temperature_c, total_gbp, deposit_required_gbp

    Write a formatted markdown flyer with a title, event facts, weather
    summary, and cost breakdown.

    Returns:
      output: {"path": "workspace/flyer.md", "bytes_written": int}
      summary: "generate_flyer: wrote <path> (<N> chars)"

    MUST call record_tool_call(...) before returning — the integrity
    check compares the flyer's contents against earlier tool outputs.

    IMPORTANT: this tool MUST be registered with parallel_safe=False
    because it writes a file.
    """
    arguments = {"event_details": event_details}
    if not isinstance(event_details, dict):
        return _invalid_result("generate_flyer", arguments, "event_details must be a dict")

    required = [
        "venue_name",
        "venue_address",
        "date",
        "time",
        "party_size",
        "condition",
        "temperature_c",
        "total_gbp",
        "deposit_required_gbp",
    ]
    missing = [key for key in required if key not in event_details]
    if missing:
        return _invalid_result(
            "generate_flyer", arguments, f"event_details missing required keys: {missing}"
        )

    flyer = f"""# {event_details["venue_name"]} private booking

Venue: {event_details["venue_name"]}
Address: {event_details["venue_address"]}
Date: {event_details["date"]}
Time: {event_details["time"]}
Party size: {event_details["party_size"]}

## Weather

Condition: {event_details["condition"]}
Temperature: {event_details["temperature_c"]}C

## Cost

Total: £{event_details["total_gbp"]}
Deposit: £{event_details["deposit_required_gbp"]}

Deposit requirements are shown in the booking facts above.
"""
    flyer_path = session.workspace_dir / "flyer.md"
    flyer_path.parent.mkdir(parents=True, exist_ok=True)
    flyer_path.write_text(flyer, encoding="utf-8")
    output = {"path": "workspace/flyer.md", "bytes_written": len(flyer)}
    record_tool_call("generate_flyer", arguments, output)
    return ToolResult(
        success=True,
        output=output,
        summary=f"generate_flyer: wrote workspace/flyer.md ({len(flyer)} chars)",
    )


# ---------------------------------------------------------------------------
# Registry builder — DO NOT MODIFY the name, signature, or registration calls.
# The grader imports and calls this to pick up your tools.
# ---------------------------------------------------------------------------
def build_tool_registry(session: Session) -> ToolRegistry:
    """Build a session-scoped tool registry with all four Ex5 tools plus
    the sovereign-agent builtins (read_file, write_file, list_files,
    handoff_to_structured, complete_task).

    DO NOT change the tool names — the tests and grader call them by name.
    """
    from sovereign_agent.tools.builtin import make_builtin_registry

    reg = make_builtin_registry(session)

    # venue_search
    reg.register(
        _RegisteredTool(
            name="venue_search",
            description="Search Edinburgh venues by area, party size, and max budget.",
            fn=venue_search,
            parameters_schema={
                "type": "object",
                "properties": {
                    "near": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "budget_max_gbp": {"type": "integer", "default": 1000},
                },
                "required": ["near", "party_size"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"near": "Haymarket", "party_size": 6, "budget_max_gbp": 800},
                    "output": {"count": 1, "results": [{"id": "haymarket_tap"}]},
                }
            ],
        )
    )

    # get_weather
    reg.register(
        _RegisteredTool(
            name="get_weather",
            description="Get scripted weather for a city on a YYYY-MM-DD date.",
            fn=get_weather,
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["city", "date"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"city": "Edinburgh", "date": "2026-04-25"},
                    "output": {"condition": "cloudy", "temperature_c": 12},
                }
            ],
        )
    )

    # calculate_cost
    reg.register(
        _RegisteredTool(
            name="calculate_cost",
            description="Compute total cost and deposit for a booking.",
            fn=calculate_cost,
            parameters_schema={
                "type": "object",
                "properties": {
                    "venue_id": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "duration_hours": {"type": "integer"},
                    "catering_tier": {
                        "type": "string",
                        "enum": ["drinks_only", "bar_snacks", "sit_down_meal", "three_course_meal"],
                        "default": "bar_snacks",
                    },
                },
                "required": ["venue_id", "party_size", "duration_hours"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # pure compute, no shared state
            examples=[
                {
                    "input": {
                        "venue_id": "haymarket_tap",
                        "party_size": 6,
                        "duration_hours": 3,
                    },
                    "output": {"total_gbp": 556, "deposit_required_gbp": 111},
                }
            ],
        )
    )

    # generate_flyer — parallel_safe=False because it writes a file
    def _flyer_adapter(event_details: dict) -> ToolResult:
        return generate_flyer(session, event_details)

    reg.register(
        _RegisteredTool(
            name="generate_flyer",
            description="Write a markdown flyer for the event to workspace/flyer.md.",
            fn=_flyer_adapter,
            parameters_schema={
                "type": "object",
                "properties": {"event_details": {"type": "object"}},
                "required": ["event_details"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=False,  # writes a file — MUST be False
            examples=[
                {
                    "input": {
                        "event_details": {
                            "venue_name": "Haymarket Tap",
                            "date": "2026-04-25",
                            "party_size": 6,
                        }
                    },
                    "output": {"path": "workspace/flyer.md"},
                }
            ],
        )
    )

    return reg


__all__ = [
    "build_tool_registry",
    "venue_search",
    "get_weather",
    "calculate_cost",
    "generate_flyer",
]
