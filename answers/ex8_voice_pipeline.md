# Ex8 — Voice pipeline

## Your answer

Ex8 is implemented as both a text and voice conversation loop around the pub
manager persona. The persona uses the Nebius OpenAI-compatible client with
`meta-llama/Llama-3.3-70B-Instruct` and a system prompt for Alasdair MacLeod, a
gruff Edinburgh pub manager. The prompt encodes the booking policy: accept
parties of 8 or fewer unless deposit is above £300, decline parties of 9 or more,
and decline deposits over £300 with a specific reason.

The voice loop has the required shape: microphone audio is saved per turn,
Speechmatics transcribes it, the transcript is sent to the manager persona, and
ElevenLabs can synthesize the reply. Text mode uses the same trace event shape.
Graceful degradation is implemented: missing `SPEECHMATICS_KEY` falls back to
text mode, and missing `ELEVENLABS_API_KEY` keeps STT active but prints replies
instead of speaking them.

I observed both modes in session logs. Text session `sess_0a9ad448abc1` recorded
four user-manager turns with `voice.utterance_in` and `voice.utterance_out`.
Voice session `sess_e3d3c22af683` recorded five voice-mode turns, including a
decline for party size 20 and an acceptance after the user changed the request
to five people. I did not find an Ex8 `--real` non-completion comparable to Ex5:
the observed LLM behavior followed the persona policy rather than inventing a
reservation. The manager rejected oversize parties in the trace and completed
the conversation only after the request was changed to an acceptable party size.

## Citations

- Text trace: `logs/homework/ex8/sess_0a9ad448abc1/logs/trace.jsonl`, turns 0-3, mode `text`.
- Voice trace: `logs/homework/ex8/sess_e3d3c22af683/logs/trace.jsonl`, turns 0-4, mode `voice`.
- Persona implementation: `starter/voice_pipeline/manager_persona.py`.
- STT/TTS loop and fallback behavior: `starter/voice_pipeline/voice_loop.py`.
