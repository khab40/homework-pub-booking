# Ex5 — Edinburgh research loop scenario

## Your answer

Ex5 is implemented as a complete loop-half research scenario. The loop half uses
the planner and executor to call the four required tools: venue search, weather
lookup, cost calculation, and flyer generation. The useful successful run I
checked is `sess_52a2eb9fa955`. In that run, the trace shows the executor called
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
Memory in this exercise is deliberately small and auditable: tool outputs are
kept in the in-process `_TOOL_CALL_LOG` during the run, then the verifier can
fall back to the durable session trace when checking evidence after the process
has exited.

The real LLM runs show why this guardrail matters. In `make ex5-real` session
`sess_0d401050d62b`, Qwen drifted away from the required Haymarket booking and
repeatedly called `venue_search` with impossible constraints such as party size
50 and 30 in broad Edinburgh areas. Those searches returned zero results, and
the live loop handed off as blocked instead of producing the required flyer. The
runner then executed the deterministic recovery sequence in the same persisted
trace: `get_weather`, `calculate_cost`, `generate_flyer`, and `complete_task`.
That is a concrete non-completion caused by the LLM inventing workflow state,
and it demonstrates why the deterministic required sequence and dataflow check
are useful.

## Citations

- Session: `logs/examples/ex5-edinburgh-research/sess_52a2eb9fa955`.
- Flyer artifact: `logs/examples/ex5-edinburgh-research/sess_52a2eb9fa955/workspace/flyer.md`.
- Trace: `logs/examples/ex5-edinburgh-research/sess_52a2eb9fa955/logs/trace.jsonl`, lines with `calculate_cost(...): total £556, deposit £111` and `generate_flyer: wrote workspace/flyer.md`.
- Real-mode loop and deterministic recovery: `logs/examples/ex5-edinburgh-research/sess_0d401050d62b/logs/trace.jsonl`.
- Implementation: `starter/edinburgh_research/tools.py`, `starter/edinburgh_research/integrity.py`.
