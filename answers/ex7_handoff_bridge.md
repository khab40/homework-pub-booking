# Ex7 — Handoff bridge

## Your answer

Ex7 is implemented as a bidirectional handoff bridge. The latest run I checked
is `sess_ff3c806b7f7b`, and it reached `completed` in two bridge rounds. Round 1
started in the loop half with the task to book 12 people in Haymarket. The trace
shows the loop called `venue_search(Haymarket, party=12)`, then handed
`haymarket_tap` to the structured half with `venue_capacity: 8`. The structured
half rejected it with `party_too_large`, and the bridge wrote a reverse handoff
back to the loop with that rejection reason.

Round 2 demonstrates the intended recovery. The planner received the rejection
context, searched Old Town for party size 12, and handed off `royal_oak` with
`venue_capacity: 16`. The structured half accepted that revised proposal, and
the session result contains `committed: true`, booking reference `BK-9B8DBC29`,
and final booking `venue_id: royal_oak`.

One caveat from the trace is worth recording: the first `venue_search` returned
zero results because the search tool filters out venues below party size. The
scripted handoff still named `haymarket_tap` to exercise the rejection path.
The bridge behavior itself is correct, but that trace detail is useful for a
future cleanup ticket.

For real-mode evidence, the persisted `ex7-real` session I found is
`sess_792b89eb08ad`. Its ticket manifests show `llm_model: fake`, so it is the
deterministic recovery path rather than a successful live-LLM trace. It still
records the same reservation loop: Haymarket search for 12 returns zero results,
the handoff nevertheless proposes `haymarket_tap`, Rasa rejects with
`party_too_large`, and the second loop proposes `royal_oak`. I therefore have
observed Ex7 completion after recovery, but not a separate live Ex7 LLM
invention spiral comparable to Ex5.

## Citations

- Latest Ex7 session: `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b`.
- Final result: `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b/session.json`, `state: completed`, `venue_id: royal_oak`, `booking_reference: BK-9B8DBC29`.
- Trace: `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b/logs/trace.jsonl`, round 1 `party_too_large`, round 2 `royal_oak`.
- Handoffs: `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b/logs/handoffs/round_1_forward.json`, `round_1_reverse.json`, and `ipc/handoff_to_structured.json`.
- Persisted real-mode/recovery session: `logs/examples/ex7-handoff-bridge/sess_792b89eb08ad`.
- Recovery ticket manifests: `logs/examples/ex7-handoff-bridge/sess_792b89eb08ad/logs/tickets/*/manifest.json`, showing planner `llm_model: fake`.
- Bridge implementation: `starter/handoff_bridge/bridge.py`.
