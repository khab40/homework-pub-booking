# Ex7 Handoff Bridge

## Goal

Ex7 demonstrates a bidirectional handoff round trip:

1. Loop half finds a candidate venue.
2. Structured half rejects it.
3. Bridge returns a focused research request to the loop half.
4. Loop half finds a better venue.
5. Structured half approves and the session completes.

The default run is deterministic. Real mode uses a live Nebius-backed loop half
first; if it fails to complete the full round trip, the runner creates a
separate recovery session with the deterministic loop while keeping the same
structured-half behavior.

## Diagram

```mermaid
sequenceDiagram
    participant Make as make ex7 or ex7-real
    participant Bridge as HandoffBridge
    participant LoopAgent as LoopHalf
    participant Tools as venue tools
    participant Store as handoff files
    participant Structured as RasaStructuredHalf

    Make->>Bridge: start "party of 12, Haymarket, Friday 19:30"
    Bridge->>LoopAgent: research booking option
    LoopAgent->>Tools: venue_search(Haymarket, 8)
    Tools-->>LoopAgent: haymarket_tap, capacity 8
    LoopAgent->>Store: write round_1_forward
    Bridge->>Structured: dispatch booking intent
    Structured-->>Bridge: reject party exceeds cap
    Bridge->>Store: write round_1_reverse
    Bridge->>LoopAgent: re-research with rejection reason
    LoopAgent->>Tools: venue_search(alternative, 12)
    Tools-->>LoopAgent: royal_oak, capacity 16
    LoopAgent->>Store: write round_2_forward
    Bridge->>Structured: dispatch revised booking intent
    Structured-->>Bridge: approve booking
    Bridge-->>Make: complete with final booking
```

## What It Demonstrates

- Handoffs are not one-way messages; the structured half can send the task back.
- The bridge is the glue layer between loop artifacts and structured decisions.
- Rejections should be actionable, for example "party exceeds cap".
- The final booking is produced only after the structured half approves.
- `ex7-real` uses a real LLM in the loop, while the default target uses a
  deterministic script and mock Rasa path.
- The first scripted search intentionally asks for 8 seats near Haymarket so the
  loop can discover `haymarket_tap`; the handoff then sends the real party size
  of 12 and venue capacity of 8 so the structured half can reject it.
- Handoff JSON is archived under `logs/handoffs/round_N_forward.json` and
  `round_N_reverse.json`, which makes the recovery path auditable.

## Primary Code

- `starter/handoff_bridge/bridge.py`
- `starter/handoff_bridge/run.py`
- `starter/rasa_half/structured_half.py`
- `starter/edinburgh_research/tools.py`
