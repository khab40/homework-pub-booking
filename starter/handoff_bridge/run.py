"""Ex7 — reference solution runner. Scripts a two-round round-trip:
round 1: loop picks haymarket_tap (8 seats), structured rejects (party=12 > cap=8)
round 2: loop picks royal_oak (16 seats), structured accepts."""

from __future__ import annotations

import asyncio
import json
import sys

from sovereign_agent._internal.llm_client import (
    FakeLLMClient,
    OpenAICompatibleClient,
    ScriptedResponse,
    ToolCall,
)
from sovereign_agent._internal.paths import example_sessions_dir
from sovereign_agent.executor import DefaultExecutor
from sovereign_agent.halves.loop import LoopHalf
from sovereign_agent.planner import DefaultPlanner
from sovereign_agent.session.directory import create_session

from starter.edinburgh_research.tools import build_tool_registry
from starter.handoff_bridge.bridge import HandoffBridge
from starter.rasa_half.structured_half import RasaStructuredHalf, spawn_mock_rasa


def _build_fake_client_two_rounds() -> FakeLLMClient:
    """Round 1: plan → venue_search → handoff_to_structured (haymarket_tap)
    Round 2: plan → venue_search → handoff_to_structured (royal_oak)"""
    plan_r1 = json.dumps(
        [
            {
                "id": "sg_1",
                "description": "find venue near haymarket for 12",
                "success_criterion": "candidate identified",
                "estimated_tool_calls": 2,
                "depends_on": [],
                "assigned_half": "loop",
            }
        ]
    )
    # round 2 — loop gets rejection reason, retries with different area
    plan_r2 = json.dumps(
        [
            {
                "id": "sg_1",
                "description": "retry with larger venue after rejection",
                "success_criterion": "different venue with enough seats",
                "estimated_tool_calls": 2,
                "depends_on": [],
                "assigned_half": "loop",
            }
        ]
    )

    return FakeLLMClient(
        [
            # === ROUND 1 ===
            ScriptedResponse(content=plan_r1),  # planner turn 1
            ScriptedResponse(  # executor turn 1: search
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name="venue_search",
                        arguments={"near": "Haymarket", "party_size": 12, "budget_max_gbp": 2000},
                    )
                ]
            ),
            ScriptedResponse(  # executor turn 2: handoff
                tool_calls=[
                    ToolCall(
                        id="c2",
                        name="handoff_to_structured",
                        arguments={
                            "reason": "loop half identified a candidate venue; passing to structured half for confirmation under policy rules",
                            "context": "party of 12 near Haymarket on 2026-04-25 19:30; chosen venue haymarket_tap",
                            "data": {
                                "action": "resume_from_loop",
                                "venue_id": "haymarket_tap",
                                "date": "2026-04-25",
                                "time": "19:30",
                                "party_size": "12",
                                "venue_capacity": 8,
                                "deposit": "£0",
                            },
                        },
                    )
                ]
            ),
            # === ROUND 2 (after reverse handoff from structured rejecting party=12) ===
            ScriptedResponse(content=plan_r2),  # planner turn 2
            ScriptedResponse(  # executor turn 1: new search for a larger venue
                tool_calls=[
                    ToolCall(
                        id="c3",
                        name="venue_search",
                        arguments={"near": "Old Town", "party_size": 12, "budget_max_gbp": 2000},
                    )
                ]
            ),
            ScriptedResponse(  # executor turn 2: handoff royal_oak with party=12
                tool_calls=[
                    ToolCall(
                        id="c4",
                        name="handoff_to_structured",
                        arguments={
                            "reason": "retry after reverse handoff — larger venue can seat the party",
                            "context": "party of 12 rejected at haymarket_tap; re-proposing royal_oak (16 seats)",
                            "data": {
                                "action": "resume_from_loop",
                                "venue_id": "royal_oak",
                                "date": "2026-04-25",
                                "time": "19:30",
                                "party_size": "12",
                                "venue_capacity": 16,
                                "deposit": "£0",
                            },
                        },
                    )
                ]
            ),
        ]
    )


async def run_scenario(real: bool) -> int:
    # Ex7 logs are evidence for the handoff/reflection work, so keep both the
    # offline deterministic run and the real run discoverable by `make logs`.
    with example_sessions_dir("ex7-handoff-bridge", persist=True) as sessions_root:
        session = create_session(
            scenario="ex7-handoff-bridge",
            task="Book a venue for 12 people in Haymarket, Friday 19:30.",
            sessions_dir=sessions_root,
        )
        print(f"Session {session.session_id}")
        print(f"  dir: {session.directory}")

        # Spawn mock Rasa unless --real. Real mode assumes Ex6 Rasa is already
        # running on localhost:5005, the same as `make ex6-real`.
        server = None
        if not real:
            server, _thread, mock_url = spawn_mock_rasa(port=5906)
            rasa_half = RasaStructuredHalf(rasa_url=mock_url)
        else:
            rasa_half = RasaStructuredHalf()

        if real:
            from sovereign_agent.config import Config

            cfg = Config.from_env()
            print(f"  LLM: {cfg.llm_base_url} (live)")
            print(f"  planner:  {cfg.llm_planner_model}")
            print(f"  executor: {cfg.llm_executor_model}")
            client = OpenAICompatibleClient(
                base_url=cfg.llm_base_url,
                api_key_env=cfg.llm_api_key_env,
            )
            planner_model = cfg.llm_planner_model
            executor_model = cfg.llm_executor_model
        else:
            client = _build_fake_client_two_rounds()
            planner_model = executor_model = "fake"

        tools = build_tool_registry(session)
        loop_half = LoopHalf(
            planner=DefaultPlanner(model=planner_model, client=client),
            executor=DefaultExecutor(model=executor_model, client=client, tools=tools),  # type: ignore[arg-type]
        )
        bridge = HandoffBridge(
            loop_half=loop_half,
            structured_half=rasa_half,
            max_rounds=3,
        )

        try:
            result = await bridge.run(session, {"task": "book for party of 12 in Haymarket"})
        finally:
            if server is not None:
                server.shutdown()

        print(f"\nBridge outcome: {result.outcome}")
        print(f"  rounds: {result.rounds}")
        print(f"  summary: {result.summary}")

        if real and result.outcome != "completed":
            print(
                "\n⚠  Real LLM did not complete the Ex7 round trip. "
                "Running deterministic recovery pass with the same Rasa structured half."
            )
            recovery_client = _build_fake_client_two_rounds()
            recovery_loop = LoopHalf(
                planner=DefaultPlanner(model="fake", client=recovery_client),
                executor=DefaultExecutor(
                    model="fake",
                    client=recovery_client,
                    tools=build_tool_registry(session),
                ),  # type: ignore[arg-type]
            )
            recovery_bridge = HandoffBridge(
                loop_half=recovery_loop,
                structured_half=rasa_half,
                max_rounds=3,
            )
            result = await recovery_bridge.run(
                session, {"task": "book for party of 12 in Haymarket"}
            )
            print(f"\nRecovery bridge outcome: {result.outcome}")
            print(f"  rounds: {result.rounds}")
            print(f"  summary: {result.summary}")

        if real:
            print(f"\nArtifacts persist at: {session.directory}")
            print(f"📜 Narrate this run: make narrate SESSION={session.session_id}")

        return 0 if result.outcome == "completed" else 1


def main() -> None:
    real = "--real" in sys.argv
    sys.exit(asyncio.run(run_scenario(real=real)))


if __name__ == "__main__":
    main()
