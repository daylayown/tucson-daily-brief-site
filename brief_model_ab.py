#!/usr/bin/env python3
"""brief_model_ab.py — run a challenger model on the same prompt the published
brief was built from, so the two can be read side by side.

WHY PAIRED, NOT ALTERNATING
Alternating days measures the news, not the model: brief quality swings far more
with what happened yesterday than with which model wrote it. Running both over
byte-identical input removes that variance entirely. The extra cost is one API
call a day.

WHAT IT DOES NOT DO
Publishes nothing, writes nothing to the canonical brief path, and never touches
brief-inputs/shadow.jsonl (the provenance gate's own log, which is mid-review).
Challenger output and metrics go to model-ab/.

HOW THE PROMPT IS OBTAINED
generate_brief.main() is run with call_claude monkeypatched to capture its
argument and return None. main() then exits on "synthesis failed" and we keep
the prompt. This is deliberately not a re-implementation of the assembly: a
parallel copy would drift from production and quietly invalidate the comparison.

READ THE OUTPUT, NOT THE METRICS
Tokens, cost and latency are logged because they are free to capture, but they
are not the question. The question is which brief you would rather have
published — which stories each picked, which it missed, and whether either
asserted something the sources do not support. n=7 over a week has no
statistical power; this is a structured side-by-side, not a measurement.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))
OUT_DIR = SITE / "model-ab"
SEND_TELEGRAM = Path.home() / ".openclaw/skills/tucson-daily-brief/scripts/send_telegram.py"

CHALLENGER = "gpt-5.6-sol"
CHALLENGER_URL = "https://api.openai.com/v1/chat/completions"
# $/MTok in, out — update if pricing moves.
PRICING = {"gpt-5.6-sol": (5.0, 30.0), "gpt-5.6-terra": (2.5, 15.0),
           "claude-opus-5": (5.0, 25.0), "claude-sonnet-5": (3.0, 15.0)}
MAX_TOKENS = 16000


def capture_prompt():
    import generate_brief as gb
    captured = {}

    def spy(prompt, api_key, max_tokens=None):
        captured["prompt"] = prompt
        return None

    real, gb.call_claude = gb.call_claude, spy
    argv, sys.argv = sys.argv, ["generate_brief.py"]
    try:
        gb.main()
    except SystemExit:
        pass
    finally:
        gb.call_claude, sys.argv = real, argv
    if not captured.get("prompt"):
        raise RuntimeError("could not capture the synthesis prompt")
    return captured["prompt"]


def run_challenger(prompt, api_key):
    body = json.dumps({
        "model": CHALLENGER,
        "max_completion_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        CHALLENGER_URL, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return None, {"error": f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}",
                      "secs": round(time.time() - t0, 1)}
    except Exception as e:
        return None, {"error": f"{type(e).__name__}: {e}",
                      "secs": round(time.time() - t0, 1)}

    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content")
    u = data.get("usage", {}) or {}
    pin, pout = PRICING.get(CHALLENGER, (0, 0))
    return text, {
        "secs": round(time.time() - t0, 1),
        "in": u.get("prompt_tokens"),
        "out": u.get("completion_tokens"),
        "thinking": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
        "finish": choice.get("finish_reason"),
        "usd": round((u.get("prompt_tokens", 0) * pin
                      + u.get("completion_tokens", 0) * pout) / 1e6, 4),
    }


def send_to_telegram(text, meta):
    """Deliver the challenger brief for side-by-side reading.

    This does NOT breach the "brief goes out once" rule in PIPELINE.md. That rule
    exists so the *published* brief is not sent twice; this is a different
    artifact that was never published. It still arrives minutes after the real
    one, so the header has to make confusing the two impossible.
    """
    if not SEND_TELEGRAM.exists():
        print("  WARN: send_telegram.py not found; skipping", file=sys.stderr)
        return
    head = (f"🧪 A/B CHALLENGER — NOT PUBLISHED\n"
            f"{meta.get('model')} · {meta.get('words')} words · "
            f"{meta.get('secs')}s · ${meta.get('usd')}\n"
            f"thinking {meta.get('thinking')} tok · gate: {meta.get('gate','n/a')}\n"
            f"Compare against today's published brief (Opus 5).\n"
            f"{'─' * 28}\n\n")
    # send_telegram.py takes a FILE PATH (sys.argv[1] -> md_path), not message
    # text. Passing the text directly makes it try to open a 5,000-character
    # string as a filename; it fails and, because we were not checking the exit
    # code, we reported success anyway. Match the house pattern in
    # generate_brief.send_provenance_alert(): temp file, pass the path, unlink.
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(head + text)
        tmp = fh.name
    try:
        sys.stdout.flush()
        r = subprocess.run([sys.executable, str(SEND_TELEGRAM), tmp],
                           check=False, timeout=120)
        if r.returncode == 0:
            print("  Telegram: challenger brief sent", file=sys.stderr)
        else:
            print(f"  WARN: telegram send exited {r.returncode} — NOT delivered",
                  file=sys.stderr)
    except (subprocess.SubprocessError, OSError) as e:
        print(f"  WARN: telegram send failed: {e}", file=sys.stderr)
    finally:
        os.unlink(tmp)


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set. Cron does not read ~/.bashrc — the key "
              "must live in ~/.config/environment.d/openai.conf.", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = capture_prompt()
    text, meta = run_challenger(prompt, api_key)
    meta.update(model=CHALLENGER, date=today, prompt_chars=len(prompt))

    if text:
        (OUT_DIR / f"{today}-{CHALLENGER}.md").write_text(text)
        meta["words"] = len(text.split())
        meta["headlines"] = sum(1 for ln in text.splitlines() if ln.startswith("**"))
        try:
            import provenance_gate as pg
            res = pg.check(text, prompt, mode=pg.Mode.SHADOW)
            meta["gate"] = res.summary()
        except Exception as e:
            meta["gate"] = f"unavailable: {e}"

    with open(OUT_DIR / "ab.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(meta) + "\n")

    print(json.dumps(meta, indent=2), file=sys.stderr)
    if not text:
        sys.exit(1)
    send_to_telegram(text, meta)
    print(f"\nWrote {OUT_DIR / f'{today}-{CHALLENGER}.md'}", file=sys.stderr)


if __name__ == "__main__":
    main()
