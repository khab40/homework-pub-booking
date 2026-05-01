# Changelog

All notable changes to the homework are documented here. The repository version
is pinned in `pyproject.toml`; cohort tags use the same `vYYYY.MM.N` shape.

## [2026.04.0] - 2026-05-01

Final homework version for Nebius Academy Module 1 Week 5.

### Delivered

- Implemented the full Ex5-Ex9 homework path: loop-half Edinburgh research,
  Rasa structured-half validation, bidirectional handoff recovery, text/voice
  pub-manager interaction, and trace-grounded reflection answers.
- Pinned `sovereign-agent == 0.2.0` for reproducible cohort grading.
- Added a repository preview image at
  `img/homework-pub-booking-social.png` and linked it from `README.md`.
- Updated answer files with committed evidence from example session logs.

### Runtime Architecture

- Ex5 writes `workspace/flyer.md`, records tool calls, and verifies venue,
  weather, temperature, and price facts against tool evidence.
- Ex5 integrity checks can replay persisted trace evidence when they run after
  the original process has exited.
- Ex6 supports three structured-half tiers: stdlib mock Rasa, manually started
  host-process Rasa, and auto-spawned host-process Rasa.
- Ex6 now persists mock and real sessions, writes structured trace events, and
  marks session state complete or failed.
- Ex7 uses a bidirectional handoff bridge with archived forward and reverse
  handoff JSON for each round.
- Ex7 real mode can fall back to a deterministic recovery session if the live
  loop half does not complete the required round trip.
- Ex8 text and voice modes emit the same `voice.utterance_in` and
  `voice.utterance_out` trace events. Voice mode uses Speechmatics STT and
  ElevenLabs REST TTS when credentials and optional dependencies are present.
- Ex9 reflection answers cite concrete committed sessions and trace artifacts.

### Documentation

- Added and finalized the architecture documentation in `docs/architecture/`.
- Updated all architecture diagrams and descriptions to match the current code:
  markdown flyer output, persisted evidence sessions, Rasa runtime tiers,
  fallback action routing, handoff archives, deterministic Ex7 recovery, and
  ElevenLabs-based voice output.
- Kept the architecture docs focused on implementation behavior rather than
  earlier design experiments.

### Tooling and Setup

- `make help` provides the student-facing workflow, and `make next` gives
  state-aware guidance.
- `.env.example` can be regenerated with `make env-bootstrap` via the bundled
  fallback in `scripts/write_env_example.py`.
- `make narrate` and `make narrate-latest` render persisted sessions into a
  readable play-by-play.
- The local grader remains advisory; CI is authoritative for the 30-point
  reasoning layer.

### Validation State

- Local completion evidence was previously committed in `d2b72e7` with
  Mechanical 27/27, Behavioural 19/19, and public tests at 27 passed,
  0 skipped.
- This finalization updates documentation and committed evidence metadata for
  the current working tree.
