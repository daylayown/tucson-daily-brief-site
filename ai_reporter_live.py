#!/usr/bin/env python3
"""
AI Reporter — Live Input Pipeline

Captures a live audio stream, transcribes in real-time using Deepgram's WebSocket
API, and saves the transcript as JSON. On completion, hands off to ai_reporter.py
for news report generation.

Supports two input modes:
  - Default: streamlink → ffmpeg → Deepgram (for YouTube and other streamlink-supported sites)
  - Direct:  ffmpeg reads URL directly → Deepgram (for HLS/RTMP/etc. URLs not supported by streamlink)

Usage:
    python3 ai_reporter_live.py "https://youtube.com/watch?v=XXX" --slug pentagon-2026-03-26
    python3 ai_reporter_live.py "https://stream.swagit.com/.../playlist.m3u8" --slug ov-2026-04-08 --direct
    python3 ai_reporter_live.py "https://youtube.com/watch?v=XXX" --transcribe-only

Requires:
    DEEPGRAM_API_KEY environment variable.
    ffmpeg, deepgram-sdk installed. streamlink required unless --direct is used.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from deepgram import DeepgramClient
    from deepgram.core.events import EventType
    from deepgram.listen.v1.types import ListenV1Results
except ImportError:
    print("ERROR: deepgram-sdk not installed. Run: .venv/bin/pip install deepgram-sdk", file=sys.stderr)
    sys.exit(1)

# --- Config ---
SITE_DIR = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = SITE_DIR / "transcripts"
AUDIO_CHUNK_SIZE = 4096  # ~128ms at 16kHz/16bit/mono
PERIODIC_SAVE_INTERVAL = 60  # seconds
DEAD_AIR_TIMEOUT = 900  # 15 minutes of no speech → auto-stop
MAX_DURATION = 6 * 3600  # 6 hour safety cap
MIN_RECORDING_TIME = 4 * 3600  # 4 hours before dead air timeout activates


class LiveTranscriber:
    """Manages the live transcription pipeline: [streamlink →] ffmpeg → Deepgram."""

    def __init__(self, url: str, slug: str, max_duration: int = None,
                 dead_air_timeout: int = None, direct: bool = False,
                 min_recording_time: int = None):
        self.url = url
        self.slug = slug
        self.max_duration = max_duration or MAX_DURATION
        self.dead_air_timeout = dead_air_timeout or DEAD_AIR_TIMEOUT
        self.min_recording_time = min_recording_time if min_recording_time is not None else MIN_RECORDING_TIME
        self.direct = direct  # Skip streamlink, feed URL directly to ffmpeg
        self.segments: list[dict] = []
        self.started_at: str = ""
        self.ended_at: str = ""
        self.streamlink_proc = None
        self.ffmpeg_proc = None
        self.dg_connection = None
        self.shutting_down = False
        self.last_save_time = 0
        self.last_speech_time = 0  # Updated on each final transcript segment
        self.speech_detected = False  # Dead air timeout only activates after first speech
        self.pipeline_start_time = 0
        self.current_interim = ""  # For terminal display

    def start(self) -> Path:
        """Run the full pipeline. Returns path to saved transcript JSON."""
        TRANSCRIPTS_DIR.mkdir(exist_ok=True)

        # Check for existing transcript
        final_path = TRANSCRIPTS_DIR / f"{self.slug}.json"
        if final_path.exists():
            print(f"Transcript already exists: {final_path}")
            print("Delete it to re-transcribe, or run ai_reporter.py directly.")
            return final_path

        self.started_at = datetime.now(timezone.utc).isoformat()
        print(f"Starting live transcription: {self.slug}")
        print(f"Source: {self.url}")
        print(f"Press Ctrl+C to stop and save transcript.\n")

        # Set up signal handler for graceful shutdown
        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_sigint)

        try:
            self._run_pipeline()
        except Exception as e:
            print(f"\nERROR: Pipeline failed: {e}", file=sys.stderr)
        finally:
            signal.signal(signal.SIGINT, original_sigint)
            self._cleanup_processes()

        self.ended_at = datetime.now(timezone.utc).isoformat()

        # Save final transcript
        if self.segments:
            transcript_path = self._save_transcript(final=True)
            print(f"\nTranscript saved: {transcript_path}")
            print(f"Segments: {len(self.segments)}")
            duration = self.segments[-1].get("end", 0) - self.segments[0].get("start", 0)
            print(f"Duration: {int(duration // 60)}m {int(duration % 60)}s")
            return transcript_path
        else:
            print("\nNo transcript segments captured.")
            return None

    def _handle_sigint(self, signum, frame):
        """Graceful shutdown on Ctrl+C."""
        if self.shutting_down:
            print("\nForce quit.")
            sys.exit(1)
        self.shutting_down = True
        print("\n\nShutting down gracefully... (press Ctrl+C again to force quit)")

        # Close Deepgram connection to flush final results
        if self.dg_connection:
            try:
                self.dg_connection.send_close_stream()
            except Exception:
                pass

    def _run_pipeline(self):
        """Set up and run [streamlink →] ffmpeg → Deepgram."""
        ffmpeg_input_args = []
        ffmpeg_stdin = None

        if self.direct:
            # Direct mode: ffmpeg reads URL directly (HLS, RTMP, etc.)
            # If stream isn't live yet, ffmpeg fails fast — retry until it works
            print(f"Direct mode: connecting to {self.url}")
            ffmpeg_input_args = [
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "30",
                "-err_detect", "ignore_err",
                "-fflags", "+discardcorrupt",
                "-i", self.url,
            ]
            ffmpeg_stdin = None

            wait_interval = 60
            wait_max = 1800  # 30 minutes
            elapsed = 0
            while True:
                probe = subprocess.run(
                    ["ffmpeg", "-i", self.url, "-t", "1", "-f", "null", "-"],
                    capture_output=True, timeout=30,
                )
                if probe.returncode == 0:
                    break
                if elapsed >= wait_max:
                    print(f"ERROR: Stream not available after {wait_max}s, giving up.", file=sys.stderr)
                    return
                print(f"Stream not live yet, retrying in {wait_interval}s... ({elapsed}s elapsed)")
                time.sleep(wait_interval)
                elapsed += wait_interval
        else:
            # Streamlink mode: streamlink pipes audio to ffmpeg
            print("Starting streamlink...")
            try:
                self.streamlink_proc = subprocess.Popen(
                    ["streamlink", "--stdout", self.url, "audio_only,audio,worst"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except FileNotFoundError:
                print("ERROR: streamlink not found. Run: pip install streamlink", file=sys.stderr)
                return

            # Give streamlink a moment to connect
            time.sleep(2)
            if self.streamlink_proc.poll() is not None:
                stderr = self.streamlink_proc.stderr.read().decode().strip()
                print(f"ERROR: streamlink failed to connect: {stderr}", file=sys.stderr)
                return

            ffmpeg_input_args = ["-i", "pipe:0"]
            ffmpeg_stdin = self.streamlink_proc.stdout

        # Start ffmpeg to convert to PCM
        print("Starting ffmpeg (converting to PCM 16kHz mono)...")
        try:
            self.ffmpeg_proc = subprocess.Popen(
                [
                    "ffmpeg",
                    *ffmpeg_input_args,
                    "-f", "s16le",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    "-loglevel", "quiet",
                    "pipe:1",
                ],
                stdin=ffmpeg_stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            print("ERROR: ffmpeg not found. Install ffmpeg.", file=sys.stderr)
            return

        # 3. Connect to Deepgram
        print("Connecting to Deepgram...")
        api_key = os.environ.get("DEEPGRAM_API_KEY")
        if not api_key:
            print("ERROR: DEEPGRAM_API_KEY not set", file=sys.stderr)
            return

        deepgram = DeepgramClient(api_key=api_key)

        with deepgram.listen.v1.connect(
            model="nova-2",
            language="en-US",
            smart_format="true",
            diarize="true",
            interim_results="true",
            endpointing="300",
            encoding="linear16",
            sample_rate="16000",
            channels="1",
        ) as connection:
            self.dg_connection = connection

            # Set up event handlers
            connection.on(EventType.MESSAGE, self._on_message)
            connection.on(EventType.ERROR, self._on_error)
            connection.on(EventType.CLOSE, self._on_close)

            # Start listener thread (processes incoming events)
            listener_thread = threading.Thread(
                target=connection.start_listening, daemon=True
            )
            listener_thread.start()

            now = time.time()
            self.last_speech_time = now
            self.pipeline_start_time = now

            print("Connected. Listening...\n")
            if self.min_recording_time > 0:
                hours = self.min_recording_time // 3600
                minutes = (self.min_recording_time % 3600) // 60
                if hours:
                    print(f"  [Dead air timeout suppressed for first {hours}h{minutes}m]")
                else:
                    print(f"  [Dead air timeout suppressed for first {minutes}m]")

            # 4. Read audio chunks and send to Deepgram
            self._stream_audio()

            # Wait for listener to finish processing
            listener_thread.join(timeout=5)

    def _stream_audio(self):
        """Read PCM chunks from ffmpeg and send to Deepgram.

        Uses non-blocking reads with select() so that if ffmpeg stalls
        (e.g., corrupt HLS packets), we send silence to Deepgram to keep
        the WebSocket alive and avoid 1011 timeout errors.
        """
        import select
        SILENCE_CHUNK = b'\x00' * AUDIO_CHUNK_SIZE
        FFMPEG_READ_TIMEOUT = 5  # seconds before sending silence
        ffmpeg_fd = self.ffmpeg_proc.stdout.fileno()

        while not self.shutting_down:
            # Check if ffmpeg/streamlink died
            if self.ffmpeg_proc.poll() is not None:
                print("\nStream ended (ffmpeg process exited).")
                break
            if self.streamlink_proc and self.streamlink_proc.poll() is not None:
                print("\nStream ended (streamlink process exited).")
                break

            try:
                ready, _, _ = select.select([ffmpeg_fd], [], [], FFMPEG_READ_TIMEOUT)
                if ready:
                    chunk = os.read(ffmpeg_fd, AUDIO_CHUNK_SIZE)
                    if not chunk:
                        print("\nStream ended (no more audio data).")
                        break
                    self.dg_connection.send_media(chunk)
                else:
                    # ffmpeg stalled — send silence to keep Deepgram alive
                    self.dg_connection.send_media(SILENCE_CHUNK)
            except Exception as e:
                if not self.shutting_down:
                    print(f"\nERROR reading/sending audio: {e}", file=sys.stderr)
                break

            now = time.time()

            # Dead air timeout: only activates after first speech detected
            # AND after min_recording_time has elapsed
            elapsed = now - self.pipeline_start_time
            if self.speech_detected and elapsed >= self.min_recording_time:
                silence_duration = now - self.last_speech_time
                if silence_duration >= self.dead_air_timeout:
                    minutes = int(silence_duration // 60)
                    seconds = int(silence_duration % 60)
                    print(f"\nAuto-stopping: no speech for {minutes}m{seconds}s.")
                    break

            # Max duration safety cap
            if elapsed >= self.max_duration:
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                print(f"\nAuto-stopping: max duration reached ({hours}h{minutes}m).")
                break

            # Periodic save
            if now - self.last_save_time >= PERIODIC_SAVE_INTERVAL and self.segments:
                self._save_transcript(final=False)
                self.last_save_time = now

        # Signal Deepgram we're done
        if self.dg_connection:
            try:
                self.dg_connection.send_close_stream()
            except Exception:
                pass

        # Wait briefly for final results to arrive
        time.sleep(2)

    def _on_message(self, message, **kwargs):
        """Handle incoming messages from Deepgram."""
        if not isinstance(message, ListenV1Results):
            return
        try:
            channel = message.channel
            alt = channel.alternatives[0] if channel.alternatives else None
            if not alt or not alt.transcript.strip():
                return

            text = alt.transcript.strip()
            is_final = message.is_final

            if is_final:
                self.last_speech_time = time.time()
                if not self.speech_detected:
                    self.speech_detected = True
                    print("  [Speech detected — dead air timeout now active]")

                # Extract speaker and timing from words
                speaker = None
                start_time = 0
                end_time = 0

                if alt.words:
                    start_time = alt.words[0].start
                    end_time = alt.words[-1].end
                    # Use the most common speaker in this segment
                    speakers = [w.speaker for w in alt.words if hasattr(w, 'speaker') and w.speaker is not None]
                    if speakers:
                        speaker = max(set(speakers), key=speakers.count)

                self.segments.append({
                    "start": start_time,
                    "end": end_time,
                    "speaker": speaker,
                    "text": text,
                    "confidence": alt.confidence if hasattr(alt, 'confidence') else 0.0,
                })

                # Print final result
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                speaker_label = f"Speaker {speaker}" if speaker is not None else "Speaker ?"
                # Clear interim line and print final
                print(f"\r\033[K[{minutes:02d}:{seconds:02d}] {speaker_label}: {text}")

            else:
                # Show interim result (overwrite in place)
                print(f"\r\033[K  ... {text}", end="", flush=True)

        except Exception as e:
            print(f"\nWARNING: Error processing transcript result: {e}", file=sys.stderr)

    def _on_error(self, error, **kwargs):
        """Handle Deepgram errors."""
        print(f"\nDeepgram error: {error}", file=sys.stderr)

    def _on_close(self, close, **kwargs):
        """Handle Deepgram connection close."""
        if not self.shutting_down:
            print("\nDeepgram connection closed.")

    def _save_transcript(self, final: bool = False) -> Path:
        """Save transcript to disk."""
        duration = 0
        if self.segments:
            duration = self.segments[-1].get("end", 0) - self.segments[0].get("start", 0)

        data = {
            "meta": {
                "source_url": self.url,
                "slug": self.slug,
                "title": self.slug.replace("-", " ").title(),
                "started_at": self.started_at,
                "ended_at": self.ended_at if final else "",
                "duration_seconds": int(duration),
                "provider": "deepgram",
                "model": "nova-2",
                "diarization": True,
            },
            "segments": self.segments,
        }

        if final:
            path = TRANSCRIPTS_DIR / f"{self.slug}.json"
        else:
            path = TRANSCRIPTS_DIR / f"{self.slug}-partial.json"

        path.write_text(json.dumps(data, indent=2))

        if not final:
            print(f"\r\033[K  [periodic save: {len(self.segments)} segments, {int(duration // 60)}m]",
                  end="", flush=True)

        return path

    def _cleanup_processes(self):
        """Terminate subprocesses."""
        for proc, name in [(self.ffmpeg_proc, "ffmpeg"), (self.streamlink_proc, "streamlink")]:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                except Exception:
                    pass

        # Clean up partial file if final exists
        partial = TRANSCRIPTS_DIR / f"{self.slug}-partial.json"
        final = TRANSCRIPTS_DIR / f"{self.slug}.json"
        if final.exists() and partial.exists():
            try:
                partial.unlink()
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="AI Reporter — capture and transcribe live streams"
    )
    parser.add_argument("url", help="Live stream URL (YouTube, HLS .m3u8, RTMP, etc.)")
    parser.add_argument("--slug", required=True,
                        help="Identifier for this transcript (e.g., pentagon-2026-03-26)")
    parser.add_argument("--direct", action="store_true",
                        help="Skip streamlink — feed URL directly to ffmpeg (for HLS, RTMP, etc.)")
    parser.add_argument("--transcribe-only", action="store_true",
                        help="Only transcribe — don't generate a news report")
    parser.add_argument("--max-duration", type=int, default=None,
                        help="Max recording duration in seconds (default: 6 hours)")
    parser.add_argument("--dead-air-timeout", type=int, default=None,
                        help="Stop after N seconds of no speech (default: 900)")
    parser.add_argument("--min-recording-time", type=int, default=None,
                        help="Don't activate dead air timeout until this many seconds have elapsed (default: 4 hours)")

    args = parser.parse_args()

    transcriber = LiveTranscriber(args.url, args.slug,
                                  max_duration=args.max_duration,
                                  dead_air_timeout=args.dead_air_timeout,
                                  direct=args.direct,
                                  min_recording_time=args.min_recording_time)
    transcript_path = transcriber.start()

    if transcript_path and transcript_path.exists() and not args.transcribe_only:
        print(f"\nGenerating news report...")
        result = subprocess.run(
            [sys.executable, str(SITE_DIR / "ai_reporter.py"), str(transcript_path)],
            cwd=str(SITE_DIR),
        )
        if result.returncode != 0:
            print("WARNING: News report generation failed (non-fatal)", file=sys.stderr)
    elif transcript_path and args.transcribe_only:
        print(f"\nTranscribe-only mode. To generate a report, run:")
        print(f"  python3 ai_reporter.py {transcript_path}")


if __name__ == "__main__":
    main()
