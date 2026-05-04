# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

In Ex7 run `sess_7891378afd35`, the planner itself did not directly
assign the subgoal to the structured half. The first planner ticket,
`tk_cab7cd39`, produced subgoal `sg_1` with `"description": "find nearest
Haymarket venue before structured policy check"` and `"assigned_half": "loop"`.
The handoff decision was made one step later by the loop executor in ticket
`tk_2757b8ff`, where the tool sequence was `venue_search` followed by
`handoff_to_structured`.

The signal for that handoff was that the loop had produced a booking candidate
that required deterministic policy confirmation, not more open-ended search.
The handoff tool call says the reason explicitly: "loop half identified a
candidate venue; passing to structured half for confirmation under policy
rules." Its payload proposed `haymarket_tap` for a party of 12 at 19:30 with
`venue_capacity: 8`. The bridge then moved state from loop to structured, and
the structured half rejected it with `party_too_large`. In round 2, the same
pattern repeated after the rejection: planner ticket `tk_4a6ee34d` again assigned
the retry subgoal to `loop`, then executor ticket `tk_84ec9d4c` handed
`royal_oak` to structured after finding an Old Town venue with enough capacity.

### Citation

- `logs/examples/ex7-handoff-bridge/sess_7891378afd35/logs/tickets/tk_cab7cd39/raw_output.json` shows `assigned_half: loop`.
- `logs/examples/ex7-handoff-bridge/sess_7891378afd35/logs/tickets/tk_2757b8ff/raw_output.json` shows `handoff_to_structured` and the handoff reason.
- `logs/examples/ex7-handoff-bridge/sess_7891378afd35/logs/trace.jsonl` lines 5-7 show loop to structured, then structured to loop with `party_too_large`.
- `logs/examples/ex7-handoff-bridge/sess_7891378afd35/logs/tickets/tk_84ec9d4c/raw_output.json` shows the second handoff for `royal_oak`.

---

## Q2 — Dataflow integrity catch

### Your answer

The clearest reproducible Ex5 integrity case is the flyer from
`sess_52a2eb9fa955`. The trace records the tool outputs: `get_weather`
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

- `logs/examples/ex5-edinburgh-research/sess_52a2eb9fa955/logs/trace.jsonl` records `get_weather(edinburgh, 2026-04-25): cloudy, 12C`.
- `logs/examples/ex5-edinburgh-research/sess_52a2eb9fa955/logs/trace.jsonl` records `calculate_cost(haymarket_tap, 6): total £556, deposit £111`.
- `logs/examples/ex5-edinburgh-research/sess_52a2eb9fa955/workspace/flyer.md` lines 11-17 contain `cloudy`, `12C`, `£556`, and `£111`.
- `starter/edinburgh_research/integrity.py` contains `verify_dataflow`.

---

## Q3 — Removing one framework primitive

### Your answer

The first production failure I would expect is planner output that is empty or
not parseable. I saw this in Ex7 live session `sess_0b1bfe855664`: the bridge
started the planner, but the framework rejected the planner result with
`[SA_VAL_INVALID_PLANNER_OUTPUT] planner returned empty content`. No structured
handoff should be attempted after that, because there is no valid subgoal graph
to execute.

The one sovereign-agent primitive I would keep is planner-output validation. If
that primitive were removed, an empty planner response could be treated as a
valid no-op plan or fall through into executor behavior with missing context.
Here the validation made the failure explicit: the session was marked failed
with a `bridge.failed` trace event, and the recovery run `sess_085e42123ab0`
could resume deterministically from that failure and complete the intended
two-round handoff path.

### Citation

- Real-mode failure session: `logs/examples/ex7-handoff-bridge/sess_0b1bfe855664`.
- Failure trace: `logs/examples/ex7-handoff-bridge/sess_0b1bfe855664/logs/trace.jsonl`, ending with `planner returned empty content`.
- Recovery session proving the intended path: `logs/examples/ex7-handoff-bridge/sess_085e42123ab0`, with `resumed_from: sess_0b1bfe855664`.
