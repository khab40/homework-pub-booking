"""Ex5 — reference solution for integrity.py.

verify_dataflow's job: for every concrete fact in the flyer, confirm
that some tool call in the session actually produced that value. If
a fact exists in the flyer but not in any tool output, it's fabrication.

Two competing failure modes to balance:
  - Too lenient → misses fabrications (grader plants £9999; must catch it)
  - Too strict → rejects legitimate flyers (fails the "accepts real flyer" test)

This implementation leans slightly strict but uses the scalar-matching
`fact_appears_in_log` helper provided in the starter to tolerate common
variations (leading £, trailing C, case differences).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from html import unescape
from pathlib import Path
from typing import Any


@dataclass
class ToolCallRecord:
    tool_name: str
    arguments: dict
    output: dict
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


_TOOL_CALL_LOG: list[ToolCallRecord] = []


def record_tool_call(tool_name: str, arguments: dict, output: dict) -> None:
    _TOOL_CALL_LOG.append(
        ToolCallRecord(tool_name=tool_name, arguments=dict(arguments), output=dict(output))
    )


def clear_log() -> None:
    _TOOL_CALL_LOG.clear()


@dataclass
class IntegrityResult:
    ok: bool
    unverified_facts: list[str] = field(default_factory=list)
    verified_facts: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "unverified_facts": self.unverified_facts,
            "verified_facts": self.verified_facts,
            "summary": self.summary,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def extract_money_facts(text: str) -> list[str]:
    """Find all pound-denominated amounts, HTML tags stripped or not."""
    # Strip HTML tags first so e.g. <dd>£540</dd> matches cleanly.
    stripped = re.sub(r"<[^>]+>", " ", text)
    facts: list[str] = []
    for match in re.finditer(r"£\s*\d[\d,\s]*(?:\.\d+)?", stripped):
        amount = re.sub(r"[\s,]", "", match.group(0))
        facts.append(amount)
    return facts


def extract_temperature_facts(text: str) -> list[str]:
    """Find temperature mentions (number followed by °C or C)."""
    stripped = re.sub(r"<[^>]+>", " ", text)
    return list({m.group(1) for m in re.finditer(r"(\d+)\s*°?\s*[Cc]\b", stripped)})


def extract_condition_facts(text: str) -> list[str]:
    """Find weather condition keywords."""
    stripped = re.sub(r"<[^>]+>", " ", text)
    tl = stripped.lower()
    known = ("sunny", "rainy", "cloudy", "partly_cloudy", "partly cloudy")
    return [c for c in known if c in tl]


def extract_testid_facts(text: str) -> dict[str, str]:
    """For HTML flyers that use data-testid, extract {testid: value} pairs.

    This is the preferred path for HTML — it gives us structured facts
    (e.g. {'total': '£540', 'deposit': '£0'}) instead of loose regex
    matches. The solution flyer ships with data-testid on every fact.
    """
    pattern = re.compile(
        r'<[^>]+data-testid="([^"]+)"[^>]*>([^<]+)</[^>]+>',
        re.IGNORECASE,
    )
    return {m.group(1): m.group(2).strip() for m in pattern.finditer(text)}


def extract_labelled_facts(text: str) -> list[str]:
    """Extract explicit flyer facts from simple labelled prose.

    This catches markdown/plain-text flyers used by the grader probe, including
    non-money values accidentally placed in a cost field.
    """
    stripped = unescape(re.sub(r"<[^>]+>", " ", text))
    facts: list[str] = []
    for label in ("Venue", "Condition", "Temperature", "Total", "Deposit"):
        for match in re.finditer(rf"(?im)^\s*{label}\s*:\s*([^\n.]+)", stripped):
            value = match.group(1).strip()
            if value:
                facts.append(value)
    return facts


def fact_appears_in_log(fact: Any, log: list[ToolCallRecord] | None = None) -> bool:
    records = log if log is not None else _TOOL_CALL_LOG
    target = _normalise_scalar_fact(fact)

    def _scan(obj: Any) -> bool:
        if isinstance(obj, (str, int, float)):
            return _normalise_scalar_fact(obj) == target
        if isinstance(obj, dict):
            return any(_scan(v) for v in obj.values())
        if isinstance(obj, (list, tuple, set)):
            return any(_scan(v) for v in obj)
        return False

    return any(_scan(r.output) for r in records if r.tool_name != "generate_flyer")


def _normalise_scalar_fact(value: Any) -> str:
    text = str(value).casefold().strip()
    text = re.sub(r"^\s*£\s*", "", text)
    text = text.replace(",", "")
    text = re.sub(r"\s*°?\s*c\s*$", "", text)
    text = text.strip()
    try:
        number = Decimal(text)
    except InvalidOperation:
        return text
    return format(number.normalize(), "f")


def _trace_path_from_session(session: Any) -> Path | None:
    if session is None:
        return None
    if isinstance(session, (str, Path)):
        base = Path(session)
    else:
        directory = getattr(session, "directory", None)
        if directory is None:
            return None
        base = Path(directory)
    if base.name == "trace.jsonl":
        return base
    trace_path = base / "logs" / "trace.jsonl"
    return trace_path if trace_path.exists() else None


def _matching_trace_for_flyer(flyer_content: str) -> Path | None:
    candidates: list[Path] = []
    local_root = Path("logs") / "examples" / "ex5-edinburgh-research"
    if local_root.exists():
        candidates.extend(local_root.glob("sess_*"))
    if Path("sessions").exists():
        candidates.extend(Path("sessions").glob("sess_*"))

    session_dirs = [p for p in candidates if p.is_dir()]
    session_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for session_dir in session_dirs:
        flyer_path = session_dir / "workspace" / "flyer.md"
        trace_path = session_dir / "logs" / "trace.jsonl"
        if not flyer_path.exists() or not trace_path.exists():
            continue
        try:
            if flyer_path.read_text(encoding="utf-8") == flyer_content:
                return trace_path
        except OSError:
            continue
    return None


def _records_from_trace(trace_path: Path) -> list[ToolCallRecord]:
    sample_data = Path(__file__).parent / "sample_data"

    def _load_fixture(filename: str) -> Any:
        return json.loads((sample_data / filename).read_text(encoding="utf-8"))

    def _replay_output(tool_name: str, arguments: dict) -> dict | None:
        if tool_name == "venue_search":
            venues = _load_fixture("venues.json")
            near = str(arguments["near"])
            party_size = int(arguments["party_size"])
            budget_max_gbp = int(arguments.get("budget_max_gbp", 1000))
            needle = near.casefold()
            results = [
                venue
                for venue in venues
                if venue.get("open_now") is True
                and needle in str(venue.get("area", "")).casefold()
                and int(venue.get("seats_available_evening", 0)) >= party_size
                and int(venue.get("hire_fee_gbp", 0)) + int(venue.get("min_spend_gbp", 0))
                <= budget_max_gbp
            ]
            return {
                "near": near,
                "party_size": party_size,
                "results": results,
                "count": len(results),
            }
        if tool_name == "get_weather":
            weather = _load_fixture("weather.json")
            city_key = str(arguments["city"]).casefold()
            date = str(arguments["date"])
            return {"city": city_key, "date": date, **weather[city_key][date]}
        if tool_name == "calculate_cost":
            catering = _load_fixture("catering.json")
            venues = _load_fixture("venues.json")
            venue_id = str(arguments["venue_id"])
            party_size = int(arguments["party_size"])
            duration_hours = int(arguments["duration_hours"])
            catering_tier = str(arguments.get("catering_tier", "bar_snacks"))
            venue = next(v for v in venues if v.get("id") == venue_id)
            billable_hours = max(1, duration_hours)
            subtotal = (
                catering["base_rates_gbp_per_head"][catering_tier]
                * catering["venue_modifiers"][venue_id]
                * party_size
                * billable_hours
            )
            service = subtotal * catering["service_charge_percent"] / 100
            venue_cost = int(venue.get("hire_fee_gbp", 0)) + int(venue.get("min_spend_gbp", 0))
            total_gbp = round(subtotal + service + venue_cost)
            deposit_required_gbp = 0
            if total_gbp >= 300:
                deposit_required_gbp = round(total_gbp * (0.2 if total_gbp <= 1000 else 0.3))
            return {
                "venue_id": venue_id,
                "party_size": party_size,
                "duration_hours": duration_hours,
                "catering_tier": catering_tier,
                "subtotal_gbp": round(subtotal),
                "service_gbp": round(service),
                "total_gbp": total_gbp,
                "deposit_required_gbp": deposit_required_gbp,
            }
        return None

    records: list[ToolCallRecord] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = event.get("payload", {})
        tool_name = payload.get("tool")
        if event.get("event_type") != "executor.tool_called":
            continue
        arguments = dict(payload.get("arguments") or {})
        output = _replay_output(tool_name, arguments)
        if output is None:
            continue
        records.append(
            ToolCallRecord(
                tool_name=tool_name,
                arguments=arguments,
                output=output,
            )
        )
    return records


# ---------------------------------------------------------------------------
# verify_dataflow — the main check
# ---------------------------------------------------------------------------
def verify_dataflow(*args: Any) -> IntegrityResult:
    """Verify that flyer facts came from previous tool outputs.

    Assignment.md specifies verify_dataflow(session, flyer_content). Public
    scaffold tests historically called verify_dataflow(flyer_content), so this
    accepts both forms. If called after a completed run in a fresh process, it
    can reload matching persisted Ex5 trace evidence.
    """
    session = None
    if len(args) == 1:
        flyer_content = args[0]
    elif len(args) == 2:
        session, flyer_content = args
    else:
        raise TypeError("verify_dataflow expects flyer_content or session, flyer_content")

    flyer_content = str(flyer_content)
    if not flyer_content or not flyer_content.strip():
        return IntegrityResult(ok=True, summary="no facts to verify (empty flyer)")

    facts_to_check: list[str] = []
    facts_to_check.extend(extract_testid_facts(flyer_content).values())
    facts_to_check.extend(extract_labelled_facts(flyer_content))
    facts_to_check.extend(extract_money_facts(flyer_content))
    facts_to_check.extend(extract_temperature_facts(flyer_content))
    facts_to_check.extend(extract_condition_facts(flyer_content))

    # De-dupe while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for f in facts_to_check:
        key = f.lower().strip()
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    if not deduped:
        return IntegrityResult(
            ok=True, summary="no extractable facts in flyer (verified vacuously)"
        )

    records = _TOOL_CALL_LOG
    if not records:
        trace_path = _trace_path_from_session(session) or _matching_trace_for_flyer(flyer_content)
        if trace_path:
            records = _records_from_trace(trace_path)

    verified: list[str] = []
    unverified: list[str] = []
    for fact in deduped:
        if fact_appears_in_log(fact, records):
            verified.append(fact)
        else:
            unverified.append(fact)

    if unverified:
        return IntegrityResult(
            ok=False,
            unverified_facts=unverified,
            verified_facts=verified,
            summary=(
                f"dataflow FAIL: {len(unverified)} unverified fact(s): "
                f"{unverified[:5]}" + ("..." if len(unverified) > 5 else "")
            ),
        )

    return IntegrityResult(
        ok=True,
        verified_facts=verified,
        summary=f"dataflow OK: verified {len(verified)} fact(s) against tool outputs",
    )


__all__ = [
    "IntegrityResult",
    "ToolCallRecord",
    "_TOOL_CALL_LOG",
    "clear_log",
    "extract_condition_facts",
    "extract_money_facts",
    "extract_labelled_facts",
    "extract_temperature_facts",
    "extract_testid_facts",
    "fact_appears_in_log",
    "record_tool_call",
    "verify_dataflow",
]
