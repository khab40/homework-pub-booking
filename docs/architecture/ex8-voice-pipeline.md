# Ex8 Voice Pipeline

## Goal

Ex8 demonstrates a voice or text interaction with a Llama-3.3-70B pub manager
persona. The manager speaks in character and accepts or declines bookings based
on party size and deposit policy. Text mode and voice mode write the same trace
event types so the downstream evidence model does not depend on the I/O mode.

## Diagram

```mermaid
sequenceDiagram
    participant User
    participant CLI as voice_pipeline.run
    participant Voice as voice_loop
    participant STT as Speechmatics
    participant Persona as ManagerPersona
    participant Nebius as Nebius Llama-3.3-70B
    participant TTS as ElevenLabs REST TTS
    participant Trace as session trace

    User->>CLI: --text or --voice
    CLI->>Voice: start interaction loop
    alt text mode
        User->>Voice: stdin text
    else voice mode
        User->>Voice: microphone audio
        Voice->>STT: transcribe audio
        STT-->>Voice: utterance text
    end
    Voice->>Trace: voice.utterance_in
    Voice->>Persona: manager input
    Persona->>Nebius: chat completion
    Nebius-->>Persona: in-character response
    Persona-->>Voice: manager response
    Voice->>Trace: voice.utterance_out
    alt text mode or no TTS key
        Voice-->>User: print response
    else voice mode with TTS
        Voice->>TTS: synthesize response
        TTS-->>Voice: audio
        Voice-->>User: play audio
    end
```

## What It Demonstrates

- Text mode exercises the conversation logic without audio credentials.
- Voice mode adds Speechmatics STT and ElevenLabs REST TTS.
- Missing `SPEECHMATICS_KEY` degrades to text mode with a visible warning.
- Missing `ELEVENLABS_API_KEY` still allows STT and printed responses.
- Each turn is logged with `voice.utterance_in` and `voice.utterance_out`.
- Captured microphone input is written to `workspace/turn_<N>_input.wav` for
  debugging before transcription.

## Primary Code

- `starter/voice_pipeline/manager_persona.py`
- `starter/voice_pipeline/voice_loop.py`
- `starter/voice_pipeline/run.py`
- `starter/voice_pipeline/requirements-voice.txt`
