# Ex7 — Handoff bridge

## Your answer

Ex7 is implemented as a bidirectional handoff bridge. The latest run I checked
is `sess_7891378afd35`, and it reached `completed` in two bridge rounds. Round 1
started in the loop half with the task to book 12 people in Haymarket. The trace
shows the loop called `venue_search(Haymarket, party=8)`, which found the nearby
8-seat Haymarket Tap candidate. The handoff then sent the real booking request
to the structured half with `venue_id: haymarket_tap`, `party_size: 12`,
`venue_capacity: 8`, and deposit `£0`. The structured half rejected it with
`party_too_large`, and the bridge wrote a reverse handoff back to the loop with
that rejection reason.
Observability for this bridge is the session artifact model: trace JSONL,
archived handoff files, and ticket manifests with SHA-256 checksums make the
round trip inspectable after the run.

Round 2 demonstrates the intended recovery. The planner received the rejection
context, searched Old Town for party size 12, and handed off `royal_oak` with
`venue_capacity: 16`. The structured half accepted that revised proposal, and
the session result contains `committed: true`, booking reference `BK-9B8DBC29`,
and final booking `venue_id: royal_oak`.

For real-mode evidence, live session `sess_0b1bfe855664` failed immediately
because the planner returned empty content. The successful recovery session
`sess_085e42123ab0` resumed from that failed session and completed the same
two-round path against the real Rasa structured half. Its final `session.json`
records `fallback_from_action: resume_from_loop`, because live Rasa did not route
`resume_from_loop` directly and the structured half retried through
`confirm_booking`. The same validation policy still ran, and the accepted
booking is `royal_oak` for 12 people.
The bridge uses the session directory as durable memory between halves: the
current retry context is carried in the reverse handoff file, while prior
handoffs are preserved under `logs/handoffs/` for audit instead of being kept
only in process memory.

## Citations

- Successful deterministic session: `logs/examples/ex7-handoff-bridge/sess_7891378afd35`.
- Final result: `logs/examples/ex7-handoff-bridge/sess_7891378afd35/session.json`, `state: completed`, `venue_id: royal_oak`, `booking_reference: BK-9B8DBC29`.
- Trace: `logs/examples/ex7-handoff-bridge/sess_7891378afd35/logs/trace.jsonl`, round 1 `party_too_large`, round 2 `royal_oak`.
- Handoffs: `logs/examples/ex7-handoff-bridge/sess_7891378afd35/logs/handoffs/round_1_forward.json` and `round_1_reverse.json`.
- Live failed session: `logs/examples/ex7-handoff-bridge/sess_0b1bfe855664/logs/trace.jsonl`, ending with `planner returned empty content`.
- Recovery session: `logs/examples/ex7-handoff-bridge/sess_085e42123ab0`, with `resumed_from: sess_0b1bfe855664`.
- Ticket evidence: `logs/examples/ex7-handoff-bridge/sess_7891378afd35/logs/tickets/tk_2757b8ff/raw_output.json` and `tk_84ec9d4c/raw_output.json`.
- Bridge implementation: `starter/handoff_bridge/bridge.py`.
