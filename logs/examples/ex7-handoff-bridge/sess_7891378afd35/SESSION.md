# Session sess_7891378afd35

**Scenario:** ex7-handoff-bridge
**Created:** 2026-05-04T08:31:17.384969+00:00

## Your task

(The loop half reads this file on every turn. The initial task description
has been written below by the orchestrator when the session was created.
Additional per-session instructions — constraints, identity, voice — can
be added by the scenario author.)

## Task description

Book a venue for a party of 12 in Haymarket, Friday 19:30. First discover the nearby Haymarket Tap candidate and hand it to the structured half with venue_id='haymarket_tap', party_size=12, venue_capacity=8, deposit='£0'. If structured rejects it, use the rejection reason to research a larger venue, then hand off royal_oak with venue_capacity=16. Every handoff data payload must include action, venue_id, date, time, party_size, venue_capacity, and deposit.

## Constraints

- Be honest when you do not know something.
- Prefer reading memory over guessing.
- When the task is ambiguous, ask for clarification rather than inventing an answer.
