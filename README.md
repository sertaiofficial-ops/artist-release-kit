# SERTAI Release Kit

**SERTAI Release Kit**

Turn any track into a complete, distributor-ready release package in one command.

Analyze your audio for tempo, estimated key (with confidence), energy, and brightness. Then automatically fill a clean Markdown template with metadata, pitches, captions, and lyrics — ready for Spotify, YouTube, and socials.

Built for independent artists who want consistent, professional releases without the busywork.

**Local. Fast. No cloud required.**

SERTAI LAB — Music, code & cinematic storytelling.

**SERTAI LAB — Audio analysis + release kit generator for independent artists.**

Extract BPM, estimated key, energy and brightness from a track, then fill a complete distributor-ready release kit (metadata, pitches, captions, lyrics structure).

## What’s included

- `analyze_audio_release.py` — measures duration, sample rate, tempo, RMS energy, spectral centroid and key candidates from any audio file.
- `templates/release_kit_template.md` — single-file Markdown template for a full release kit.

## Quick start

```bash
pip install -r requirements.txt

# Basic analysis
python analyze_audio_release.py your-track.wav --json metrics.json

# Auto-fill release kit
python analyze_audio_release.py your-track.wav \
  --template templates/release_kit_template.md \
  --output release-kit.md \
  --lyrics lyrics.txt \
  --artist "SERTAI" \
  --title "Track Name" \
  --track-number "1"
```

Use the JSON output or the filled Markdown. Key detection includes a confidence percentage and is an estimate — confirm in a DAW when it matters.

## Notes

- Key candidates are algorithmic estimates, not guarantees.
- Designed for independent artists who want clean, consistent release metadata.
- No cloud services required. Everything runs locally.

**SERTAI LAB**  
Independent music & cinematic storytelling.
