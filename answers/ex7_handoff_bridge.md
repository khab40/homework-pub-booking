# Ex7 — Handoff bridge

## Your answer

Ex7 is implemented as a bidirectional handoff bridge. The latest run I checked
is `sess_e9f1561758cd`, and it reached `completed` in two bridge rounds. Round 1
started in the loop half with the task to book 12 people in Haymarket. The trace
shows the loop called `venue_search(Haymarket, party=8)`, which found the nearby
8-seat Haymarket Tap candidate. The handoff then sent the real booking request
to the structured half with `venue_id: haymarket_tap`, `party_size: 12`,
`venue_capacity: 8`, and deposit `£0`. The structured half rejected it with
`party_too_large`, and the bridge wrote a reverse handoff back to the loop with
that rejection reason.

Round 2 demonstrates the intended recovery. The planner received the rejection
context, searched Old Town for party size 12, and handed off `royal_oak` with
`venue_capacity: 16`. The structured half accepted that revised proposal, and
the session result contains `committed: true`, booking reference `BK-9B8DBC29`,
and final booking `venue_id: royal_oak`.

For real-mode evidence, live session `sess_806f69c91167` failed after three
rounds because the LLM repeatedly handed incomplete data to structured Rasa:
empty payloads, missing `venue_id`, and a workspace lookup instead of a valid
booking proposal. The successful recovery session `sess_e9f1561758cd` resumed
from that failed session and completed against the real Rasa structured half.
Its final `session.json` records `fallback_from_action: resume_from_loop`,
because live Rasa did not route `resume_from_loop` directly and the structured
half retried through `confirm_booking`. The same validation policy still ran,
and the accepted booking is `royal_oak` for 12 people.

## Citations

- Successful recovery session: `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd`.
- Final result: `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/session.json`, `state: completed`, `venue_id: royal_oak`, `booking_reference: BK-9B8DBC29`, `resumed_from: sess_806f69c91167`.
- Trace: `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/logs/trace.jsonl`, round 1 `party_too_large`, round 2 `royal_oak`.
- Handoffs: `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/logs/handoffs/round_1_forward.json` and `round_1_reverse.json`.
- Live failed session: `logs/examples/ex7-handoff-bridge/sess_806f69c91167/logs/trace.jsonl`, three rounds ending with `normalisation failed: missing venue_id`.
- Ticket evidence: `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/logs/tickets/tk_cac7a4e6/raw_output.json` and `tk_3ce0a069/raw_output.json`.
- Bridge implementation: `starter/handoff_bridge/bridge.py`.
