# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

In my Ex7 run `sess_ff3c806b7f7b`, the planner itself did not directly assign
the subgoal to the structured half. The first planner ticket, `tk_2d0a6564`,
produced subgoal `sg_1` with `"description": "find venue near haymarket for 12"`
and `"assigned_half": "loop"`. The handoff decision was made one step later by
the loop executor in ticket `tk_7e079914`, where the tool sequence was
`venue_search` followed by `handoff_to_structured`.

The signal for that handoff was that the loop had produced a booking candidate
that required deterministic policy confirmation, not more open-ended search.
The handoff tool call says the reason explicitly: "loop half identified a
candidate venue; passing to structured half for confirmation under policy
rules." Its payload proposed `haymarket_tap` for a party of 12 at 19:30 with
`venue_capacity: 8`. The bridge then moved state from loop to structured, and
the structured half rejected it with `party_too_large`. In round 2, the same
pattern repeated after the rejection: planner ticket `tk_ac6d1b3a` again assigned
the retry subgoal to `loop`, then executor ticket `tk_f476dbdf` handed
`royal_oak` to structured after finding an Old Town venue with enough capacity.

### Citation

- `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b/logs/tickets/tk_2d0a6564/raw_output.json` shows `assigned_half: loop`.
- `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b/logs/tickets/tk_7e079914/raw_output.json` shows `handoff_to_structured` and the handoff reason.
- `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b/logs/trace.jsonl` lines 5-7 show loop to structured, then structured to loop with `party_too_large`.
- `logs/examples/ex7-handoff-bridge/sess_ff3c806b7f7b/logs/tickets/tk_f476dbdf/raw_output.json` shows the second handoff for `royal_oak`.

---

## Q2 — Dataflow integrity catch

### Your answer

The clearest reproducible Ex5 integrity case is the flyer from
`sess_4ac7ff81cf4c`. The trace records the real tool outputs: `get_weather`
returned `cloudy, 12C`, and `calculate_cost(haymarket_tap, 6)` returned `total
£556, deposit £111`. The generated flyer then repeats those exact facts:
Haymarket Tap, cloudy, 12C, Total £556, Deposit £111.

A failure that manual inspection could miss is a small but plausible price edit.
For example, if someone changes only the flyer line `Total: £556` to
`Total: £9999` or even to a less absurd `Total: £540`, the flyer would still look
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

If this agent were shipping to a real pub-booking business next week, the first
production failure I would expect is premature completion after a partial
workflow. I saw exactly that pattern in Ex5 real-mode session
`sess_8af1faeccf2c`: the LLM found The Royal Oak and called `complete_task`
after venue selection, but before the required weather lookup, cost calculation,
and flyer generation. In a business setting, the same failure mode would look
like a reservation being reported as "done" when the quote, deposit, or customer
artifact was never produced.

The one sovereign-agent primitive I would keep is manifest discipline. If that
primitive were removed, the system would still have a final answer, but no
reliable record of which operations produced it. The ticket manifest and ticket
summary expose the exact operation and outputs. In the bad ticket, the summary
says the executor made only `venue_search, venue_search, venue_search,
complete_task`; there is no `get_weather`, `calculate_cost`, or `generate_flyer`
in that ticket. That makes the failure auditable after the fact and enforceable
in CI: a production gate can reject any "completed" booking ticket whose
manifest does not include the required tool sequence and expected workspace
artifact.

### Citation

- Real-mode failure session: `logs/examples/ex5-edinburgh-research/sess_8af1faeccf2c`.
- Premature completion trace: `logs/examples/ex5-edinburgh-research/sess_8af1faeccf2c/logs/trace.jsonl`, lines with three `venue_search` calls followed by `complete_task`.
- Ticket summary: `logs/examples/ex5-edinburgh-research/sess_8af1faeccf2c/logs/tickets/tk_5953fcf5/summary.md`, which lists `venue_search, venue_search, venue_search, complete_task`.
- Ticket manifest: `logs/examples/ex5-edinburgh-research/sess_8af1faeccf2c/logs/tickets/tk_5953fcf5/manifest.json`.
