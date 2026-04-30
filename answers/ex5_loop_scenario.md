# Ex5 — Edinburgh research loop scenario

## Your answer

Ex5 is implemented as a complete loop-half research scenario. The loop half uses
the planner and executor to call the four required tools: venue search, weather
lookup, cost calculation, and flyer generation. The useful successful run I
checked is `sess_4ac7ff81cf4c`. In that run, the trace shows the executor called
`calculate_cost` for `haymarket_tap`, party size 6, duration 3 hours, and got
`total £556, deposit £111`. Immediately after that, `generate_flyer` wrote
`workspace/flyer.md`.

The produced flyer is markdown and contains the same concrete facts: Haymarket
Tap, 12 Dalry Rd, 2026-04-25 at 19:30, party size 6, cloudy weather, 12C, total
£556, and deposit £111. That is the intended dataflow: the final user-facing
artifact is only valid if each specific fact can be traced to a previous tool
result. The implementation also keeps `generate_flyer` non-parallel-safe because
it writes to the session workspace. The important lesson from Ex5 is that the
LLM can assemble the artifact, but the verifier is the control that prevents the
artifact from silently inventing prices, venue names, or weather.

The real LLM runs show why this guardrail matters. In `make ex5-real` session
`sess_10a5d8ccaffb`, Qwen repeatedly called `venue_search` five times with
invented or drifting constraints: Old Town party 10 at £200 and £300, Edinburgh
City Centre party 12 at £400, Edinburgh party 15 at £500, and Edinburgh,
Scotland party 8 at £300. Every search returned zero results, and the run handed
off instead of producing a flyer. In `sess_8af1faeccf2c`, the LLM found The
Royal Oak and called `complete_task` after only venue selection, before weather,
cost calculation, or flyer generation; recovery then ran the required sequence.
In `sess_bcac073a9a76`, the LLM called `generate_flyer` with a nested `venue`
object and missing required keys, so the tool rejected it. Those are concrete
non-completions caused by the LLM inventing workflow state or payload structure.

## Citations

- Session: `logs/examples/ex5-edinburgh-research/sess_4ac7ff81cf4c`.
- Flyer artifact: `logs/examples/ex5-edinburgh-research/sess_4ac7ff81cf4c/workspace/flyer.md`.
- Trace: `logs/examples/ex5-edinburgh-research/sess_4ac7ff81cf4c/logs/trace.jsonl`, lines with `calculate_cost(...): total £556, deposit £111` and `generate_flyer: wrote workspace/flyer.md`.
- Real-mode loop: `logs/examples/ex5-edinburgh-research/sess_10a5d8ccaffb/logs/trace.jsonl`.
- Real-mode early completion and recovery: `logs/examples/ex5-edinburgh-research/sess_8af1faeccf2c/logs/trace.jsonl`.
- Real-mode malformed flyer payload: `logs/examples/ex5-edinburgh-research/sess_bcac073a9a76/logs/trace.jsonl`.
- Implementation: `starter/edinburgh_research/tools.py`, `starter/edinburgh_research/integrity.py`.
