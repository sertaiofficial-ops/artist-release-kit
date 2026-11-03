#!/usr/bin/env python3
"""Extract reproducible release-oriented metrics from an audio file and optionally fill a release kit template."""
import argparse
import json
from pathlib import Path
import librosa
import numpy as np

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH = True
except ImportError:
    RICH = False

console = Console() if RICH else None


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
            score = float(chroma @ shifted)
            result.append({'key': f'{note} {mode}', 'score': score})
    ranked = sorted(result, key=lambda x: x['score'], reverse=True)
    if ranked:
        top = ranked[0]['score']
        second = ranked[1]['score'] if len(ranked) > 1 else 0
        gap = max(top - second, 0)
        confidence = min(100, max(0, int(50 + gap * 40)))
        for r in ranked:
            r['confidence_pct'] = confidence if r is ranked[0] else max(0, confidence - 15)
    return ranked


def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def fill_template(template_path: Path, output_path: Path, metrics: dict, lyrics: str | None, extras: dict):
    text = template_path.read_text(encoding='utf-8')
    top_key = metrics['key_candidates'][0] if metrics.get('key_candidates') else {}
    key_str = top_key.get('key', 'unknown')
    conf = top_key.get('confidence_pct', 0)
    replacements = {
        '{{BPM}}': f"{metrics['tempo_bpm']:.1f}",
        '{{KEY}}': f"{key_str} (est. {conf}%)",
        '{{DURATION}}': format_duration(metrics['duration_seconds']),
        '{{FORMAT}}': Path(metrics['file']).suffix.lstrip('.').upper() or 'AUDIO',
        '{{ORGANIZED_LYRICS}}': lyrics or '{{ORGANIZED_LYRICS}}',
    }
    replacements.update({f'{{{{{k}}}}}' : str(v) for k, v in extras.items()})
    for k, v in replacements.items():
        text = text.replace(k, v)
    output_path.write_text(text, encoding='utf-8')
    return output_path


def main():
    parser = argparse.ArgumentParser(description="SERTAI Release Kit — audio analysis")
    parser.add_argument('audio', type=Path, help="Audio file (wav/mp3/flac)")
    parser.add_argument('--json', type=Path, help="Write metrics JSON")
    parser.add_argument('--template', type=Path, help="Release kit template to fill")
    parser.add_argument('--output', type=Path, help="Output filled Markdown")
    parser.add_argument('--lyrics', type=Path, help="Optional lyrics text file")
    parser.add_argument('--artist', default='{{ARTIST}}')
    parser.add_argument('--title', default='{{TITLE}}')
    parser.add_argument('--track-number', default='{{TRACK_NUMBER}}')
    args = parser.parse_args()

    if RICH:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Analyzing audio…", total=None)
            y, sr = librosa.load(args.audio, sr=None, mono=True)
            progress.update(task, description="Computing features…")
            rms = float(np.mean(librosa.feature.rms(y=y)))
            centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
            tempo_value = librosa.beat.beat_track(y=y, sr=sr)[0]
            tempo = float(np.asarray(tempo_value).reshape(-1)[0])
            duration = float(librosa.get_duration(y=y, sr=sr))
            keys = key_candidates(y, sr)[:6]
            progress.update(task, description="Done")
    else:
        y, sr = librosa.load(args.audio, sr=None, mono=True)
        rms = float(np.mean(librosa.feature.rms(y=y)))
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        tempo_value = librosa.beat.beat_track(y=y, sr=sr)[0]
        tempo = float(np.asarray(tempo_value).reshape(-1)[0])
        duration = float(librosa.get_duration(y=y, sr=sr))
        keys = key_candidates(y, sr)[:6]

    output = {
        'file': str(args.audio), 'sample_rate_hz': int(sr),
        'duration_seconds': duration, 'tempo_bpm': tempo,
        'rms_energy': rms, 'spectral_centroid_hz': centroid,
        'key_candidates': keys
    }
    text = json.dumps(output, indent=2)
    if args.json:
        args.json.write_text(text + '\n', encoding='utf-8')

    if RICH:
        table = Table(title="SERTAI Release Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Duration", format_duration(duration))
        table.add_row("Tempo", f"{tempo:.1f} BPM")
        table.add_row("RMS Energy", f"{rms:.4f}")
        table.add_row("Spectral Centroid", f"{centroid:.0f} Hz")
        if keys:
            top = keys[0]
            table.add_row("Estimated Key", f"{top['key']} ({top.get('confidence_pct', 0)}%)")
        console.print(table)
    else:
        print(text)

    if args.template and args.output:
        lyrics = args.lyrics.read_text(encoding='utf-8') if args.lyrics and args.lyrics.exists() else None
        extras = {
            'ARTIST': args.artist,
            'TITLE': args.title,
            'TRACK_NUMBER': args.track_number,
        }
        filled = fill_template(args.template, args.output, output, lyrics, extras)
        msg = f"Release kit written to {filled}"
        if RICH:
            console.print(f"[green]{msg}[/green]")
        else:
            print(msg)


if __name__ == '__main__':
    main()
