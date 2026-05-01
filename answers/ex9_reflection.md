# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

In Ex7 recovery run `sess_e9f1561758cd`, the planner itself did not directly
assign the subgoal to the structured half. The first planner ticket,
`tk_96097e09`, produced subgoal `sg_1` with `"description": "find nearest
Haymarket venue before structured policy check"` and `"assigned_half": "loop"`.
The handoff decision was made one step later by the loop executor in ticket
`tk_cac7a4e6`, where the tool sequence was `venue_search` followed by
`handoff_to_structured`.

The signal for that handoff was that the loop had produced a booking candidate
that required deterministic policy confirmation, not more open-ended search.
The handoff tool call says the reason explicitly: "loop half identified a
candidate venue; passing to structured half for confirmation under policy
rules." Its payload proposed `haymarket_tap` for a party of 12 at 19:30 with
`venue_capacity: 8`. The bridge then moved state from loop to structured, and
the structured half rejected it with `party_too_large`. In round 2, the same
pattern repeated after the rejection: planner ticket `tk_7c6ba9b4` again assigned
the retry subgoal to `loop`, then executor ticket `tk_3ce0a069` handed
`royal_oak` to structured after finding an Old Town venue with enough capacity.

### Citation

- `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/logs/tickets/tk_96097e09/raw_output.json` shows `assigned_half: loop`.
- `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/logs/tickets/tk_cac7a4e6/raw_output.json` shows `handoff_to_structured` and the handoff reason.
- `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/logs/trace.jsonl` lines 5-7 show loop to structured, then structured to loop with `party_too_large`.
- `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd/logs/tickets/tk_3ce0a069/raw_output.json` shows the second handoff for `royal_oak`.

---

## Q2 — Dataflow integrity catch

### Your answer

The clearest reproducible Ex5 integrity case is the flyer from
`sess_4ac7ff81cf4c`. The trace records the real tool outputs: `get_weather`
returned `cloudy, 12C`, and `calculate_cost(haymarket_tap, 6)` returned `total
£556, deposit £111`. The generated flyer then repeats those exact facts:
Haymarket Tap, cloudy, 12C, Total £556, Deposit £111.

A failure that manual inspection could miss is a small price edit.
For example, if someone changes only the flyer line `Total: £556` to
`Total: £9999` or even to `Total: £540`, the flyer would still look
like a normal markdown booking artifact. A human reviewer might scan the venue,
date, weather, and deposit and miss the mismatch. The dataflow verifier should
not miss it, because it extracts concrete facts from the flyer and checks that
each value appears in an earlier tool output. In this run, `£556` and `£111` are
traceable to `calculate_cost`; `£9999` is not. The same logic applies if the
weather condition is changed from `cloudy` to `sunny`, because the only observed
weather output for that date was `cloudy, 12C`.

### Citation

- `logs/examples/ex5-edinburgh-research/sess_4ac7ff81cf4c/logs/trace.jsonl` line 14 records `get_weather(edinburgh, 2026-04-25): cloudy, 12C`.
- `logs/examples/ex5-edinburgh-research/sess_4ac7ff81cf4c/logs/trace.jsonl` line 15 records `calculate_cost(haymarket_tap, 6): total £556, deposit £111`.
- `logs/examples/ex5-edinburgh-research/sess_4ac7ff81cf4c/workspace/flyer.md` lines 11-17 contain `cloudy`, `12C`, `£556`, and `£111`.
- `starter/edinburgh_research/integrity.py` contains `verify_dataflow`.

---

## Q3 — Removing one framework primitive

### Your answer

The first production failure I would expect is malformed handoff payloads from the LLM.
I saw this in Ex7 live session `sess_806f69c91167`: the loop half handed
structured Rasa empty or irrelevant data instead of a booking dict. Round 1
failed with `normalisation failed: missing venue_id`; round 2 handed off another
empty payload while claiming there was no venue name-to-ID lookup; round 3
listed the empty workspace and handed off `{ "error": "Missing venue details
file" }`. The bridge exhausted three rounds and marked the session failed.

The one sovereign-agent primitive I would keep is IPC atomic rename. If that
primitive were removed, malformed handoff files could be read while only partly
written, or several stale handoffs could remain visible at once. Here the
problem was the payload content, not a partial file, but the same primitive made
the failure auditable and bounded: each complete bad handoff was archived as
`round_1_forward.json`, `round_2_forward.json`, and `round_3_forward.json`, and
only one current IPC file was visible. That gives production monitoring a crisp
failure mode: reject or alert on complete handoff files missing required booking
fields, instead of debugging ambiguous filesystem state.

### Citation

- Real-mode failure session: `logs/examples/ex7-handoff-bridge/sess_806f69c91167`.
- Failure trace: `logs/examples/ex7-handoff-bridge/sess_806f69c91167/logs/trace.jsonl`, rounds 1-3 ending with `normalisation failed: missing venue_id`.
- Archived bad handoffs: `logs/examples/ex7-handoff-bridge/sess_806f69c91167/logs/handoffs/round_1_forward.json`, `round_2_forward.json`, and `round_3_forward.json`.
- Recovery session proving the intended path: `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd`, with `resumed_from: sess_806f69c91167`.
