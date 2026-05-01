# Architecture Docs

This directory documents the current homework system architecture for Ex5 through
Ex9. The diagrams are written in Mermaid so they can render directly in Markdown
viewers that support Mermaid.

## Files

- [System Overview](system-overview.md) - high-level components, local runtime,
  and session artifacts.
- [Architectural Ideas](architectural-ideas.md) - the reusable ideas that appear
  across multiple exercises.
- [Ex5 Edinburgh Research](ex5-edinburgh-research.md) - loop half, tools,
  flyer generation, and dataflow integrity.
- [Ex6 Rasa Structured Half](ex6-rasa-structured-half.md) - Rasa-backed
  structured half, validation, and booking policy.
- [Ex7 Handoff Bridge](ex7-handoff-bridge.md) - bidirectional handoff round
  trip between loop and structured halves.
- [Ex8 Voice Pipeline](ex8-voice-pipeline.md) - text and voice interaction with
  the pub manager persona.
- [Ex9 Reflection](ex9-reflection.md) - evidence-based answers grounded in
  session traces.

## Final Architecture Scope

The architecture reflects the implemented code in `starter/`, `rasa_project/`,
and the `Makefile` targets:

- Ex5 writes `workspace/flyer.md`, persists deterministic and real evidence
  sessions, and can replay persisted trace evidence during dataflow checks.
- Ex6 uses a Rasa-backed structured half with three runtime tiers: stdlib mock,
  manually started host-process Rasa, and auto-spawned host-process Rasa.
- Ex7 uses the same structured half behind a bidirectional handoff bridge, with
  deterministic recovery for live runs that do not complete the round trip.
- Ex8 text and voice modes share trace event shapes; voice mode uses
  Speechmatics for STT and ElevenLabs REST TTS when credentials are present.
- Ex9 is an evidence exercise: answer files cite committed example sessions and
  traces rather than describing the architecture generically.
