#!/usr/bin/env python3
"""Extract reproducible release-oriented metrics from an audio file."""
import argparse
import json
from pathlib import Path
import librosa
import numpy as np


def key_candidates(y, sr):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    major = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    chroma = (chroma - chroma.mean()) / (chroma.std() + 1e-9)
    result = []
    for i, note in enumerate(notes):
        for profile, mode in ((major, 'major'), (minor, 'minor')):
            shifted = np.roll(profile, i)
            shifted = (shifted - shifted.mean()) / (shifted.std() + 1e-9)
            result.append({'key': f'{note} {mode}', 'score': float(chroma @ shifted)})
    return sorted(result, key=lambda x: x['score'], reverse=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('audio', type=Path)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    y, sr = librosa.load(args.audio, sr=None, mono=True)
    rms = float(np.mean(librosa.feature.rms(y=y)))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    tempo_value = librosa.beat.beat_track(y=y, sr=sr)[0]
    tempo = float(np.asarray(tempo_value).reshape(-1)[0])
    duration = float(librosa.get_duration(y=y, sr=sr))
    output = {
        'file': str(args.audio), 'sample_rate_hz': int(sr),
        'duration_seconds': duration, 'tempo_bpm': tempo,
        'rms_energy': rms, 'spectral_centroid_hz': centroid,
        'key_candidates': key_candidates(y, sr)[:6]
    }
    text = json.dumps(output, indent=2)
    if args.json:
        args.json.write_text(text + '\n', encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
