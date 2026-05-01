# Observed Real-Mode Failures

This file maps the real-mode failure catalogue in `docs/real-mode-failures.md`
to the failures actually observed in this repository's committed evidence, plus
the code paths that catch or mitigate each one.

## Summary

| Catalogue item | Observed here? | Current handling |
| --- | --- | --- |
| Ex5 Qwen `venue_search` spiral | Yes | `venue_search` caps repeated calls and returns `too_many_searches`; Ex5 runner prints tool-call diagnostics and can run deterministic recovery. |
| Ex6 `action_validate_booking` internal error | No final evidence | Action reads `latest_message.metadata.booking` first, fills slots explicitly, and structured runner records `structured.failed` on exceptions. |
| Ex6 action-server cache | No final evidence | Operational mitigation: restart `make rasa-actions`; symptoms are surfaced through structured-half failure traces. |
| Ex6 embeddings 401 | No | `rasa_project/config.yml` nests embeddings under `flow_retrieval`, avoiding OpenAI fallback. |
| Ex7 real mode secretly using `FakeLLMClient` | No longer applicable | Current `--real` path uses `OpenAICompatibleClient`; offline mode is the only scripted path. |
| Ex7 live LLM bad handoff / incomplete data | Yes | Real-mode bridge records failure, marks the session failed, and creates a deterministic recovery session. |
| Ex7 `FakeLLMClient` scripted responses exhausted | No | Prevented mainly by the `sovereign-agent == 0.2.0` pin; otherwise it fails loudly. |
| Ex8 Speechmatics 401/403 | No final evidence | Voice mode catches STT exceptions and prints key/quota guidance; diagnostics probes Speechmatics auth. |
| Ex8 Rime invalid voice | Not applicable | Current code uses ElevenLabs, not Rime; TTS failures are caught and the conversation continues. |
| Ex8 mic/audio playback failure | No final evidence | Mic capture errors print platform guidance; TTS playback errors are non-fatal. |
| General offline works, real breaks | Yes | Ex5 spiral and Ex7 incomplete handoff are examples; traces, narration, and recovery sessions expose the failure. |

## Observed Failures

### Ex5 Qwen `venue_search` Spiral

Observed in the committed Ex5 evidence. `answers/ex5_loop_scenario.md` cites
`logs/examples/ex5-edinburgh-research/sess_10a5d8ccaffb`, where the live LLM
called `venue_search` repeatedly instead of following the required sequence.

Current catch:

- `starter/edinburgh_research/tools.py` counts previous `venue_search` calls in
  `_TOOL_CALL_LOG`.
- The fourth and later calls return `success=False` with
  `{"error": "too_many_searches", "count": <N>}` and the summary
  `STOP calling venue_search; use the results you already have.`
- The blocked call is still recorded with `record_tool_call`, so the trace
  explains what happened.
- `starter/edinburgh_research/run.py` prints the tools that did run when no
  flyer is produced, and real mode can run a deterministic recovery pass.

### Ex7 Live LLM Bad Handoff

Observed in the committed Ex7 evidence. `answers/ex7_handoff_bridge.md` cites
`logs/examples/ex7-handoff-bridge/sess_806f69c91167`, where the live loop handed
incomplete data to structured Rasa, including empty payloads and missing
`venue_id`.

Current catch:

- `starter/handoff_bridge/run.py` catches live bridge exceptions, appends a
  `bridge.failed` trace event, and marks the original session failed.
- If real mode does not complete, the runner creates a separate deterministic
  recovery session using the same structured half.
- The successful recovery evidence is
  `logs/examples/ex7-handoff-bridge/sess_e9f1561758cd`.
- That recovery session records `fallback_from_action: resume_from_loop`
  because live Rasa did not route `resume_from_loop` directly; the structured
  half retried as `confirm_booking`.

## Not Observed, But Covered

### Ex6 `action_validate_booking` Internal Error

No final committed evidence shows the internal-error failure. The code prevents
the common metadata-vs-slots bug by reading `tracker.latest_message.metadata`
first in `rasa_project/actions/actions.py`, then filling Rasa slots explicitly.

If an exception still occurs in the structured runner,
`starter/rasa_half/run.py` records `structured.failed` and marks the session
failed.

### Ex6 Action-Server Cache

No final committed evidence shows this failure. It is primarily operational:
Rasa action servers keep Python modules in memory. The mitigation remains to
restart `make rasa-actions` after editing `rasa_project/actions/*.py`, and to
restart or clean/train Rasa after changing flows, domain, or config.

The code catches the symptom, not the stale-process cause: unexpected Rasa
responses become failed `HalfResult` objects or structured failure traces.

### Ex6 Embeddings 401

No final committed evidence shows this failure. It is prevented by
`rasa_project/config.yml`, where embeddings are nested under
`flow_retrieval.embeddings`. That prevents Rasa from falling back to default
OpenAI embeddings with a Nebius key.

### Ex7 `FakeLLMClient` Script Exhaustion

No final committed evidence shows this failure. The main protection is the exact
framework pin, `sovereign-agent == 0.2.0`, so the scripted planner/executor call
sequence stays stable. If it occurs, offline mode should fail loudly rather than
silently pass.

### Ex8 Speechmatics 401/403

No final committed evidence shows a bad Speechmatics key or quota exhaustion.
`starter/voice_pipeline/voice_loop.py` catches STT exceptions and prints
guidance to check `SPEECHMATICS_KEY` and the free-tier quota. The diagnostics
script also probes Speechmatics auth.

### Ex8 Mic Or Playback Failure

No final committed evidence shows this failure. Mic capture exceptions are
caught with macOS microphone-permission guidance. TTS playback exceptions are
non-fatal, so the conversation can continue with printed manager replies.

## Stale Catalogue Items

`docs/real-mode-failures.md` still contains two stale references:

- Ex5 examples mention `workspace/flyer.html`, while current code writes
  `workspace/flyer.md`.
- Ex8 documents Rime TTS, while current code uses ElevenLabs REST TTS.

The current ElevenLabs path reads `ELEVENLABS_API_KEY`,
`ELEVENLABS_VOICE_ID`, and `ELEVENLABS_MODEL_ID`. TTS failures are caught per
turn and do not stop the voice conversation.
