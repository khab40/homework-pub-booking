# System Overview

The project demonstrates a "two half" agent architecture. The loop half handles
open-ended planning and tool use. The structured half handles deterministic
dialog and policy decisions. Session directories provide the durable boundary
for traces, workspace files, and handoff payloads.

## Component View

```mermaid
flowchart LR
    User[User or Make target] --> Runner[Exercise runner]

    Runner --> Session[Session directory]
    Session --> Workspace[workspace/ artifacts]
    Session --> Trace[trace events]
    Session --> Handoffs[handoff files]

    Runner --> Loop[LoopHalf]
    Loop --> Planner[DefaultPlanner]
    Loop --> Executor[DefaultExecutor]
    Loop --> Tools[Session-scoped tools]
    Planner --> LLM[FakeLLMClient or Nebius LLM]
    Executor --> LLM

    Tools --> Data[sample_data JSON]
    Tools --> Workspace
    Tools --> IntegrityLog[_TOOL_CALL_LOG]

    Runner --> Structured[RasaStructuredHalf]
    Structured --> Validator[Booking validator]
    Structured --> Rasa[Rasa REST server :5005]
    Rasa --> Actions[Rasa action server :5055]
    Actions --> Policy[Booking policy]

    Runner --> Voice[Voice pipeline]
    Voice --> Speechmatics[Speechmatics STT]
    Voice --> Persona[ManagerPersona on Nebius]
    Voice --> ElevenLabs[ElevenLabs TTS]
    Voice --> Trace
```

## Local Runtime

```mermaid
flowchart TB
    Make[Makefile target] --> Python[uv run python -m starter...]

    subgraph Offline
        FakeLLM[FakeLLMClient]
        MockRasa[stdlib mock Rasa]
    end

    subgraph Real_Mode
        Nebius[Nebius OpenAI-compatible endpoint]
        RasaServer[Rasa server :5005]
        RasaActions[Rasa actions :5055]
        Speechmatics[Speechmatics]
        ElevenLabs[ElevenLabs]
    end

    Python --> FakeLLM
    Python --> MockRasa
    Python --> Nebius
    Python --> RasaServer
    RasaServer --> RasaActions
    Python --> Speechmatics
    Python --> ElevenLabs
```

## Session Artifact Model

```mermaid
classDiagram
    class Session {
        +id
        +workspace_dir
        +logs_dir
        +trace_events
    }

    class Workspace {
        +flyer.md
        +exercise_outputs
    }

    class Trace {
        +planner_events
        +tool_events
        +voice.utterance_in
        +voice.utterance_out
    }

    class HandoffStore {
        +outgoing_handoff
        +return_handoff
        +archived_rounds
    }

    Session *-- Workspace
    Session *-- Trace
    Session *-- HandoffStore
```

The important design point is that every exercise leaves evidence in the
session. Ex5 produces a flyer and tool log. Ex7 archives the handoff round
trip. Ex8 logs each utterance. Ex9 should cite those traces instead of relying
on generic conclusions.
