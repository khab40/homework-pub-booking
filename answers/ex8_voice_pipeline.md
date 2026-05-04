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

I observed both modes in the persisted example session logs. The text example
records four user-manager turns with matching `voice.utterance_in` and
`voice.utterance_out` events, ending after the manager collected party size,
date/time, and contact number. The voice example records five voice-mode turns:
the user asks to book, gives a party size of five, supplies "today, 6 p.m.",
provides a contact number, and then says goodbye. In both modes, the trace
captures the transcript text and `mode` field for every turn, so the grading
evidence does not depend on replaying microphone audio.

I did not observe an Ex8 real-mode non-completion comparable to Ex5. The
manager persona stayed within the booking policy and asked for missing booking
details before confirming. The main operational risk I observed was not policy
drift but pipeline fragility around optional voice dependencies, which is why
voice mode degrades to text output when TTS is unavailable and now requests raw
PCM from ElevenLabs instead of decoding MP3 locally.

## Citations

- Text trace: `logs/examples/ex8-voice-pipeline/sess_68a359c439e8/logs/trace.jsonl`, turns 0-3, mode `text`.
- Voice trace: `logs/examples/ex8-voice-pipeline/sess_6f68d9bd9f2f/logs/trace.jsonl`, turns 0-4, mode `voice`.
- Persona implementation: `starter/voice_pipeline/manager_persona.py`.
- STT/TTS loop and fallback behavior: `starter/voice_pipeline/voice_loop.py`.
