# SERTAI Release Kit

**SERTAI LAB — Audio analysis + release kit generator for independent artists.**

Extract BPM, estimated key, energy and brightness from a track, then fill a complete distributor-ready release kit (metadata, pitches, captions, lyrics structure).

## What’s included

- `analyze_audio_release.py` — measures duration, sample rate, tempo, RMS energy, spectral centroid and key candidates from any audio file.
- `templates/release_kit_template.md` — single-file Markdown template for a full release kit.

## Quick start

```bash
pip install -r requirements.txt
python analyze_audio_release.py your-track.wav --json metrics.json
```

Use the JSON output + your lyrics to fill the template. Key detection is an estimate — confirm in a DAW when it matters.

## Notes

- Key candidates are algorithmic estimates, not guarantees.
- Designed for independent artists who want clean, consistent release metadata.
- No cloud services required. Everything runs locally.

**SERTAI LAB**  
Independent music & cinematic storytelling.
