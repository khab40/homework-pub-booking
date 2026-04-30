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
That run created session `sess_c6a0799b06b3`, used the stdlib mock Rasa server
on port 5905, and returned `Structured half outcome: complete` with booking
reference `BK-7D401E9E` for `haymarket_tap`, date `2026-04-25`, time `19:30`,
party size 6, and deposit £200. Real Rasa still requires the three-process setup,
but the implemented code path matches the assignment contract.

## Citations

- Observed run: `make ex6`, session `sess_c6a0799b06b3`, mock URL `http://127.0.0.1:5905/webhooks/rest/webhook`, booking reference `BK-7D401E9E`.
- Persisted Ex6 session shell: `logs/examples/ex6-rasa-half/sess_2f8bd5ca2b6e/session.json`.
- Validator: `starter/rasa_half/validator.py`, `normalise_booking_payload`.
- HTTP structured half and mock Rasa policy: `starter/rasa_half/structured_half.py`.
- Rasa flows: `rasa_project/data/flows.yml`.
- Custom action: `rasa_project/actions/actions.py`, `ActionValidateBooking`.
