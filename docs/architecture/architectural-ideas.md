# Architectural Ideas

This page shows the reusable ideas behind the exercises. Each idea has its own
Mermaid diagram and a short explanation of why it exists.

## Loop Half Tool Execution

```mermaid
sequenceDiagram
    participant Runner
    participant LoopHalf
    participant Planner
    participant Executor
    participant ToolRegistry
    participant Tool
    participant Session

    Runner->>LoopHalf: run(session, task)
    LoopHalf->>Planner: plan task
    Planner-->>LoopHalf: subgoals
    LoopHalf->>Executor: execute subgoal
    Executor->>ToolRegistry: resolve tool call
    ToolRegistry->>Tool: invoke with arguments
    Tool->>Session: write trace or workspace artifact
    Tool-->>Executor: ToolResult
    Executor-->>LoopHalf: execution result
    LoopHalf-->>Runner: HalfResult
```

The loop half is allowed to plan, call tools, recover, and produce artifacts.
It is intentionally flexible, so it must be constrained by tool schemas,
session-scoped side effects, and post-run checks.

## Dataflow Integrity

```mermaid
sequenceDiagram
    participant VenueTool as venue_search
    participant WeatherTool as get_weather
    participant CostTool as calculate_cost
    participant FlyerTool as generate_flyer
    participant Log as _TOOL_CALL_LOG
    participant Verifier as verify_dataflow

    VenueTool->>Log: record venue output
    WeatherTool->>Log: record weather output
    CostTool->>Log: record cost output
    FlyerTool->>Log: record flyer write only
    FlyerTool-->>Verifier: flyer.md content
    Verifier->>Log: read previous in-process tool outputs
    Verifier->>Session: optionally locate matching persisted trace
    Verifier->>Verifier: replay deterministic tool outputs from trace args
    Verifier->>Verifier: extract venue, weather, price facts
    Verifier-->>Verifier: pass only if exact facts are traceable
```

The verifier protects against LLM fabrication. A fact in `flyer.md` must have
appeared in an earlier read or calculation tool result. The flyer write itself
does not verify its own content. When the check runs outside the original
process, it can reload persisted Ex5 evidence by matching the flyer and
replaying deterministic tool outputs from `trace.jsonl`.

## Structured Half Policy Boundary

```mermaid
sequenceDiagram
    participant LoopSide as Loop half or runner
    participant Validator as normalise_booking_payload
    participant Structured as RasaStructuredHalf
    participant Rasa as Rasa REST webhook
    participant Action as ActionValidateBooking

    LoopSide->>Structured: booking intent dict
    Structured->>Validator: normalize values and action
    Validator-->>Structured: Rasa REST message
    Structured->>Rasa: POST /webhooks/rest/webhook
    Rasa->>Action: validate latest_message.metadata.booking
    Action-->>Rasa: slots and rejection reason
    Rasa-->>Structured: response messages
    Structured-->>LoopSide: HalfResult complete or escalate
```

The structured half is the policy boundary. It receives normalized booking data,
lets Rasa flows and actions decide, and returns a typed `HalfResult` instead of
free-form chat.

## Bidirectional Handoff

```mermaid
stateDiagram-v2
    [*] --> LoopResearch
    LoopResearch --> ForwardHandoff: candidate venue found
    ForwardHandoff --> StructuredReview: bridge dispatches
    StructuredReview --> ReturnHandoff: rejected
    ReturnHandoff --> LoopResearch: re-research requested
    StructuredReview --> Completed: approved
    Completed --> [*]
```

The Ex7 bridge demonstrates that a rejection is not a terminal failure. The
structured half can send a focused request back to the loop half, and the loop
half can produce a better candidate.

## Real and Offline Modes

```mermaid
flowchart LR
    MakeTarget[make target] --> Runner

    Runner --> Mode{mode}
    Mode -->|offline| Fake[FakeLLMClient scripts]
    Mode -->|offline| Mock[Mock Rasa server]
    Mode -->|real| Nebius[Nebius LLM]
    Mode -->|real| Rasa[Rasa localhost services]
    Mode -->|voice| STT[Speechmatics]
    Mode -->|voice| TTS[ElevenLabs REST TTS]

    Fake --> Deterministic[deterministic expected path]
    Mock --> Deterministic
    Nebius --> Recovery[deterministic recovery if LLM misses required artifact]
    Rasa --> Recovery
```

Offline mode is for deterministic development and public tests. Real mode shows
the integration path but still needs guardrails because live LLMs can miss
required tool sequences.

## Trace-Grounded Reflection

```mermaid
flowchart TB
    Session[Session logs] --> Evidence[Specific trace events]
    Evidence --> Answers[answers/*.md]
    Answers --> Validator[Ex9 answer validator]
    Validator --> Review[Reasoning review]
```

Ex9 is not only essay writing. The intended architecture is evidence first:
answers should refer to observed session behavior, handoffs, tool calls, and
integrity failures.
