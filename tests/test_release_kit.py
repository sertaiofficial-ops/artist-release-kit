"""Tests for analyze_audio_release.py using synthetic audio generated at test time."""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analyze_audio_release as ark  # noqa: E402

SR = 22050


def write_wav(path: Path, y: np.ndarray, sr: int = SR) -> Path:
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path


def a_minor_chord(seconds=4.0, sr=SR):
    t = np.arange(int(seconds * sr)) / sr
    freqs = [220.0, 261.63, 329.63]  # A3, C4, E4
    return 0.3 * sum(np.sin(2 * np.pi * f * t) for f in freqs)


def click_track(bpm=120, seconds=6.0, sr=SR):
    y = np.zeros(int(seconds * sr))
    step = int(sr * 60 / bpm)
    burst = np.hanning(400) * np.sin(2 * np.pi * 1000 * np.arange(400) / sr)
    for i in range(0, len(y) - 400, step):
        y[i:i + 400] += burst
    # A faint deterministic noise floor keeps onset detection stable.
    return y + 0.01 * np.random.default_rng(0).standard_normal(len(y))


def test_format_duration():
    assert ark.format_duration(0) == "0:00"
    assert ark.format_duration(65.9) == "1:05"
    assert ark.format_duration(600) == "10:00"


def test_key_candidates_ranking_and_confidence():
    keys = ark.key_candidates(a_minor_chord(), SR)
    assert len(keys) == 24
    scores = [k["score"] for k in keys]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= k["confidence_pct"] <= 100 for k in keys)
    assert keys[0]["confidence_pct"] >= keys[1]["confidence_pct"]
    # A minor triad should rank A minor (or its relative C major) at the top.
    assert keys[0]["key"] in {"A minor", "C major"}


def test_fill_template(tmp_path):
    tpl = tmp_path / "tpl.md"
    tpl.write_text("{{ARTIST}} - {{TITLE}} #{{TRACK_NUMBER}}\n{{BPM}} | {{KEY}} | {{DURATION}} | {{FORMAT}}\n{{ORGANIZED_LYRICS}}\n{{UNTOUCHED}}", encoding="utf-8")
    out = tmp_path / "out.md"
    metrics = {"file": "song.wav", "tempo_bpm": 120.04, "duration_seconds": 125.0,
               "key_candidates": [{"key": "A minor", "score": 1.0, "confidence_pct": 72}]}
    ark.fill_template(tpl, out, metrics, "line one", {"ARTIST": "Artist", "TITLE": "Song", "TRACK_NUMBER": "3"})
    text = out.read_text(encoding="utf-8")
    assert "Artist - Song #3" in text
    assert "120.0 | A minor (est. 72%) | 2:05 | WAV" in text
    assert "line one" in text
    assert "{{UNTOUCHED}}" in text


def test_fill_template_without_lyrics_keeps_placeholder(tmp_path):
    tpl = tmp_path / "tpl.md"
    tpl.write_text("{{ORGANIZED_LYRICS}}", encoding="utf-8")
    out = tmp_path / "out.md"
    ark.fill_template(tpl, out, {"file": "x.mp3", "tempo_bpm": 90, "duration_seconds": 1, "key_candidates": []}, None, {})
    assert out.read_text(encoding="utf-8") == "{{ORGANIZED_LYRICS}}"


def test_cli_help():
    r = subprocess.run([sys.executable, str(ROOT / "analyze_audio_release.py"), "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "--template" in r.stdout


def test_cli_end_to_end(tmp_path):
    audio = write_wav(tmp_path / "click.wav", click_track())
    metrics_path = tmp_path / "metrics.json"
    out_md = tmp_path / "kit.md"
    lyrics = tmp_path / "lyrics.txt"
    lyrics.write_text("hello world", encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "analyze_audio_release.py"), str(audio),
                        "--json", str(metrics_path),
                        "--template", str(ROOT / "templates" / "release_kit_template.md"),
                        "--output", str(out_md), "--lyrics", str(lyrics),
                        "--artist", "Test Artist", "--title", "Test Title"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    m = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert m["sample_rate_hz"] == SR
    assert m["duration_seconds"] == pytest.approx(6.0, abs=0.05)
    # 120 BPM click; allow common half/double-time readings.
    assert any(abs(m["tempo_bpm"] - b) <= 8 for b in (60, 120, 240)), m["tempo_bpm"]
    assert m["rms_energy"] > 0
    assert len(m["key_candidates"]) == 6
    assert out_md.exists() and out_md.stat().st_size > 0
    text = out_md.read_text(encoding="utf-8")
    assert "Test Artist" in text and "Test Title" in text and "hello world" in text
    for placeholder in ("{{BPM}}", "{{KEY}}", "{{DURATION}}", "{{ARTIST}}", "{{TITLE}}"):
        assert placeholder not in text
