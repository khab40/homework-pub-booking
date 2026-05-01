# Ex5 Edinburgh Research

## Goal

Ex5 demonstrates a complete loop-half scenario. The agent researches venues,
checks weather, calculates catering cost, writes `workspace/flyer.md`, and
verifies that concrete flyer facts came from tool outputs or replayable
persisted trace evidence.

## Diagram

```mermaid
sequenceDiagram
    participant Make as make ex5 or ex5-real
    participant Run as starter.edinburgh_research.run
    participant LoopAgent as LoopHalf
    participant Tools as Ex5 tools
    participant Data as sample_data JSON
    participant Workspace as session/workspace
    participant Log as _TOOL_CALL_LOG
    participant Check as verify_dataflow

    Make->>Run: start scenario
    Run->>LoopAgent: research Edinburgh venue and write flyer
    LoopAgent->>Tools: venue_search(near, party_size, budget)
    Tools->>Data: read venues.json
    Tools->>Log: record venue result
    LoopAgent->>Tools: get_weather(city, date)
    Tools->>Data: read weather.json
    Tools->>Log: record weather result
    LoopAgent->>Tools: calculate_cost(venue_id, party_size, duration)
    Tools->>Data: read catering.json
    Tools->>Log: record cost result
    LoopAgent->>Tools: generate_flyer(event_details)
    Tools->>Workspace: write flyer.md
    Run->>Check: verify_dataflow(session, flyer.md)
    Check->>Log: compare flyer facts to in-process tool outputs
    alt fresh process or committed evidence session
        Check->>Workspace: match persisted flyer.md
        Check->>Data: replay read/calculation tool outputs from trace arguments
    end
    Check-->>Run: dataflow OK or FAIL
```

## What It Demonstrates

- Session-scoped tools can do real work while keeping side effects local.
- Read tools are parallel safe; `generate_flyer` is not parallel safe because it
  writes `workspace/flyer.md`.
- LLM-written final content is not trusted by default.
- The integrity check catches fabricated venue names, weather conditions,
  temperatures, and prices.
- Offline and real runs are persisted because their traces are part of the
  homework evidence used by Ex9.

## Primary Code

- `starter/edinburgh_research/tools.py`
- `starter/edinburgh_research/integrity.py`
- `starter/edinburgh_research/run.py`
- `sample_data/venues.json`
- `sample_data/weather.json`
- `sample_data/catering.json`
