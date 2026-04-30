# Ex7 Handoff Bridge

## Goal

Ex7 demonstrates a bidirectional handoff round trip:

1. Loop half finds a candidate venue.
2. Structured half rejects it.
3. Bridge returns a focused research request to the loop half.
4. Loop half finds a better venue.
5. Structured half approves and the session completes.

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
    LoopAgent->>Tools: venue_search(Haymarket, 12)
    Tools-->>LoopAgent: haymarket_tap, capacity 8
    LoopAgent->>Store: write forward handoff
    Bridge->>Structured: dispatch booking intent
    Structured-->>Bridge: reject party exceeds cap
    Bridge->>Store: write return handoff
    Bridge->>LoopAgent: re-research with rejection reason
    LoopAgent->>Tools: venue_search(alternative, 12)
    Tools-->>LoopAgent: royal_oak, capacity 16
    LoopAgent->>Store: write second forward handoff
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

## Primary Code

- `starter/handoff_bridge/bridge.py`
- `starter/handoff_bridge/run.py`
- `starter/rasa_half/structured_half.py`
- `starter/edinburgh_research/tools.py`
