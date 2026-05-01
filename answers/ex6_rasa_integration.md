# Ex6 — Rasa structured half

## Your answer

Ex6 is implemented as the structured policy half. The Python side no longer
just makes an in-process decision; `RasaStructuredHalf.run` normalizes the
booking payload, POSTs it to the Rasa REST webhook shape, parses the Rasa-style
response, and returns a `HalfResult`. The validator is the bridge between loose
loop-side data and Rasa data: it canonicalizes venue IDs, dates, times, party
size, deposit, action names, and optional venue capacity.

The Rasa project contains the required flows: `confirm_booking`,
`resume_from_loop`, and `request_research`. The custom action reads
`tracker.latest_message.metadata.booking`, fills slots, rejects missing fields,
rejects deposit over £300, and rejects party size over 8 unless an explicit
venue capacity can seat the group. I verified the offline tier with `make ex6`.
I also verified the real Rasa path after starting Rasa serve and the action
server. Session `sess_2b93b31e19e6` completed through localhost Rasa 3.16.4 and
returned `Structured half outcome: complete` with booking reference
`BK-7D401E9E` for `haymarket_tap`, date `2026-04-25`, time `19:30`, party size
6, and deposit £200. The session trace now records `structured.session_started`
and `structured.completed`, so the real structured-half run is narratable and
has a persisted local evidence artifact.

## Citations

- Observed real run: `logs/examples/ex6-rasa-half/sess_2b93b31e19e6`, booking reference `BK-7D401E9E`.
- Trace: `logs/examples/ex6-rasa-half/sess_2b93b31e19e6/logs/trace.jsonl`, `structured.session_started` and `structured.completed`.
- Final state: `logs/examples/ex6-rasa-half/sess_2b93b31e19e6/session.json`, `state: completed`.
- Validator: `starter/rasa_half/validator.py`, `normalise_booking_payload`.
- HTTP structured half and mock Rasa policy: `starter/rasa_half/structured_half.py`.
- Rasa flows: `rasa_project/data/flows.yml`.
- Custom action: `rasa_project/actions/actions.py`, `ActionValidateBooking`.
