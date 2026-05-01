# Ex6 Rasa Structured Half

## Goal

Ex6 replaces a minimal in-process structured half with a Rasa-backed dialog
manager. Python normalizes booking data, Rasa owns the dialog flow, and a custom
action enforces booking policy. The same runner supports mock, manually started
Rasa, and auto-spawned Rasa modes while persisting trace evidence for all tiers.

## Diagram

```mermaid
sequenceDiagram
    participant Make as make ex6 or ex6-real
    participant Run as starter.rasa_half.run
    participant Half as RasaStructuredHalf
    participant Validator as normalise_booking_payload
    participant Rasa as Rasa REST webhook
    participant Flow as flows.yml
    participant Action as ActionValidateBooking

    Make->>Run: start booking confirmation
    Run->>Run: create persisted session
    Run->>Run: append structured.session_started
    Run->>Half: run(session, booking dict)
    Half->>Validator: parse party, deposit, date, action
    Validator-->>Half: sender, message, metadata.booking
    Half->>Rasa: POST booking message
    Rasa->>Flow: confirm_booking, resume_from_loop, or request_research
    Flow->>Action: action_validate_booking
    Action->>Action: reject deposit > 300
    Action->>Action: reject party > 8 unless venue_capacity allows
    Action-->>Flow: slots and validation_error
    Flow-->>Rasa: approve or reject response
    Rasa-->>Half: REST messages
    alt Rasa does not route non-confirm action cleanly
        Half->>Half: retry as confirm_booking and preserve fallback metadata
    end
    Half-->>Run: HalfResult complete or escalate
    Run->>Run: append structured.completed or structured.rejected
```

## What It Demonstrates

- Rasa is the deterministic half for policy-heavy decisions.
- The Python validator is the boundary between loose LLM data and Rasa's REST
  message shape.
- The custom action reads `latest_message.metadata.booking` and sets slots.
- Flows cover the happy path, resumed handoff, and request-for-research path.
- Offline mock mode validates Python wiring without requiring a Rasa license.
- Session state is marked complete or failed so committed example logs can be
  used as direct evidence.
- If a live Rasa run does not route `resume_from_loop` or `request_research`
  directly, `RasaStructuredHalf` retries as `confirm_booking` and records the
  original action in the result.

## Primary Code

- `starter/rasa_half/validator.py`
- `starter/rasa_half/structured_half.py`
- `starter/rasa_half/run.py`
- `rasa_project/data/flows.yml`
- `rasa_project/actions/actions.py`
- `rasa_project/domain.yml`
