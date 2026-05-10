#!/usr/bin/env python3
"""
ai_reporter_vod.py — VOD transcription via Deepgram batch (pre-recorded) API.

For meetings where the live capture failed or processing happens after the fact.
ffmpeg extracts/transcodes audio from any URL/file → opus → Deepgram batch →
transcript JSON in the schema ai_reporter.py expects → invokes ai_reporter.py
to generate the news-report draft.

Usage:
    python3 ai_reporter_vod.py <audio_url_or_path> --slug <slug> [options]

Options:
    --title "..."          Human-readable meeting title (default: derived from slug)
    --started-at DATE      Meeting date YYYY-MM-DD (default: today)
    --keep-audio           Don't delete the intermediate audio file
    --force                Overwrite existing transcript JSON
    --no-draft             Skip the ai_reporter.py draft generation step
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.resolve()
TRANSCRIPTS_DIR = REPO_ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"
DEEPGRAM_PARAMS = {
    "model": "nova-2",
    "smart_format": "true",
    "diarize": "true",
    "punctuate": "true",
    "utterances": "true",
    "language": "en-US",
}


def fetch_audio_to_opus(source: str, out_path: Path) -> None:
    """Use ffmpeg to extract mono opus audio from any source (URL or local file)."""
    print(f"  Extracting audio with ffmpeg → {out_path.name}")
    cmd = [
        "ffmpeg",
        "-y",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "30",
        "-err_detect", "ignore_err",
        "-fflags", "+discardcorrupt",
        "-i", source,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "libopus",
        "-b:a", "24k",
        "-loglevel", "error",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: ffmpeg failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    size_mb = out_path.stat().st_size / 1_000_000
    print(f"  Audio: {size_mb:.1f} MB")


def transcribe(audio_path: Path) -> dict:
    """POST audio bytes to Deepgram's pre-recorded API and return the parsed JSON."""
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        print("ERROR: DEEPGRAM_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print("  Uploading to Deepgram batch API (nova-2, diarized, utterance-segmented)...")
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/ogg",
    }
    with open(audio_path, "rb") as f:
        resp = requests.post(
            DEEPGRAM_URL,
            params=DEEPGRAM_PARAMS,
            headers=headers,
            data=f,
            timeout=600,
        )
    if resp.status_code != 200:
        print(f"ERROR: Deepgram returned {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def deepgram_to_segments(dg: dict) -> list[dict]:
    """Convert Deepgram utterances into our segment schema."""
    utterances = dg.get("results", {}).get("utterances") or []
    segments = []
    for u in utterances:
        text = (u.get("transcript") or "").strip()
        if not text:
            continue
        segments.append({
            "start": float(u.get("start", 0.0)),
            "end": float(u.get("end", 0.0)),
            "speaker": float(u.get("speaker", 0)),
            "text": text,
            "confidence": float(u.get("confidence", 0.0)),
        })
    return segments


def write_transcript(
    slug: str,
    source: str,
    title: str,
    started_at: str,
    segments: list[dict],
    dg_duration: float,
) -> Path:
    """Write our transcript JSON in the schema ai_reporter.py expects."""
    duration_seconds = int(dg_duration or (segments[-1]["end"] if segments else 0))
    started_dt = datetime.fromisoformat(started_at).replace(tzinfo=timezone.utc) if started_at else datetime.now(timezone.utc)
    ended_dt = started_dt
    data = {
        "meta": {
            "source_url": source,
            "slug": slug,
            "title": title,
            "started_at": started_dt.isoformat(),
            "ended_at": ended_dt.isoformat(),
            "duration_seconds": duration_seconds,
            "provider": "deepgram",
            "model": "nova-2",
            "diarization": True,
            "ingest": "batch-vod",
        },
        "segments": segments,
    }
    out_path = TRANSCRIPTS_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"  Transcript: {out_path}")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="Audio/video URL or local file path")
    ap.add_argument("--slug", required=True, help="Unique slug for this meeting")
    ap.add_argument("--title", default=None, help="Human-readable meeting title")
    ap.add_argument("--started-at", default=None, help="Meeting date YYYY-MM-DD (default: today)")
    ap.add_argument("--keep-audio", action="store_true", help="Don't delete intermediate audio")
    ap.add_argument("--force", action="store_true", help="Overwrite existing transcript JSON")
    ap.add_argument("--no-draft", action="store_true", help="Skip downstream ai_reporter.py invocation")
    args = ap.parse_args()

    slug = args.slug
    title = args.title or slug.replace("-", " ").title()
    started_at = args.started_at or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    transcript_path = TRANSCRIPTS_DIR / f"{slug}.json"
    if transcript_path.exists() and not args.force:
        print(f"Transcript already exists: {transcript_path}")
        print("Use --force to overwrite.")
        sys.exit(1)

    audio_path = TRANSCRIPTS_DIR / f"{slug}.opus"

    print(f"VOD transcription: {slug}")
    print(f"  Source: {args.source}")

    fetch_audio_to_opus(args.source, audio_path)
    dg = transcribe(audio_path)
    segments = deepgram_to_segments(dg)
    if not segments:
        print("ERROR: Deepgram returned no utterances", file=sys.stderr)
        sys.exit(1)
    duration = dg.get("metadata", {}).get("duration", 0.0)
    print(f"  Segments: {len(segments)} | Duration: {duration/60:.1f} min")

    write_transcript(slug, args.source, title, started_at, segments, duration)

    if not args.keep_audio:
        audio_path.unlink(missing_ok=True)

    if args.no_draft:
        print("Skipping draft generation (--no-draft).")
        return

    print("\nHanding off to ai_reporter.py for draft generation...")
    py = sys.executable
    cmd = [py, str(REPO_ROOT / "ai_reporter.py"), str(transcript_path)]
    if args.force:
        cmd.append("--force")
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
