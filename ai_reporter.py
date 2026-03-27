#!/usr/bin/env python3
"""
AI Reporter — Downstream Pipeline

Takes a transcript JSON file and generates an AP-style news report via
Claude Sonnet, sends to Telegram for human review, and publishes approved
reports to the site.

Usage:
    python3 ai_reporter.py transcripts/pentagon-2026-03-26.json
    python3 ai_reporter.py --approve transcripts/pentagon-2026-03-26-draft.md
    python3 ai_reporter.py --publish transcripts/pentagon-2026-03-26-approved.md

Requires:
    ANTHROPIC_API_KEY environment variable.
    TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID for review notifications.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# --- Config ---
SITE_DIR = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = SITE_DIR / "transcripts"
REPORTS_DIR = SITE_DIR / "news-reports"
SEND_TELEGRAM = Path.home() / ".openclaw/skills/tucson-daily-brief/scripts/send_telegram.py"

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Transcript handling
# ---------------------------------------------------------------------------

def load_transcript(json_path: str) -> dict:
    """Load and validate a transcript JSON file."""
    with open(json_path, "r") as f:
        data = json.load(f)

    if "meta" not in data or "segments" not in data:
        print(f"ERROR: Invalid transcript format — missing 'meta' or 'segments' in {json_path}",
              file=sys.stderr)
        sys.exit(1)

    return data


def format_transcript_for_prompt(data: dict) -> str:
    """Convert transcript segments to readable text for the Claude prompt.

    Merges consecutive segments from the same speaker and adds timestamp
    markers every few minutes for reference.
    """
    segments = data["segments"]
    if not segments:
        return "(empty transcript)"

    lines = []
    current_speaker = None
    current_text_parts = []
    last_timestamp_min = -1

    for seg in segments:
        speaker = seg.get("speaker")
        text = seg.get("text", "").strip()
        start = seg.get("start", 0)

        if not text:
            continue

        # Add timestamp marker roughly every 5 minutes
        current_min = int(start // 60)
        if current_min >= last_timestamp_min + 5:
            if current_text_parts and current_speaker is not None:
                lines.append(f"Speaker {current_speaker}: {' '.join(current_text_parts)}")
                current_text_parts = []
            minutes = int(start // 60)
            seconds = int(start % 60)
            lines.append(f"\n[{minutes:02d}:{seconds:02d}]")
            last_timestamp_min = current_min

        # Same speaker — accumulate
        if speaker == current_speaker:
            current_text_parts.append(text)
        else:
            # Flush previous speaker
            if current_text_parts and current_speaker is not None:
                lines.append(f"Speaker {current_speaker}: {' '.join(current_text_parts)}")
            current_speaker = speaker
            current_text_parts = [text]

    # Flush last speaker
    if current_text_parts and current_speaker is not None:
        lines.append(f"Speaker {current_speaker}: {' '.join(current_text_parts)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude API
# ---------------------------------------------------------------------------

def generate_news_report(data: dict, force: bool = False) -> str | None:
    """Send transcript to Claude and get an AP-style news report back."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return None

    meta = data["meta"]
    title = meta.get("title", "Government Meeting")
    slug = meta.get("slug", "unknown")
    duration_sec = meta.get("duration_seconds", 0)
    duration_str = f"{duration_sec // 3600}h {(duration_sec % 3600) // 60}m" if duration_sec else "unknown"
    meeting_date = meta.get("started_at", "")[:10] or "unknown"
    has_diarization = meta.get("diarization", False)

    formatted_transcript = format_transcript_for_prompt(data)

    speaker_note = ""
    if has_diarization:
        # Count unique speakers
        speakers = set(s.get("speaker") for s in data["segments"] if s.get("speaker") is not None)
        speaker_note = f"The transcript includes speaker diarization with {len(speakers)} identified speaker(s). Attribute statements using 'Speaker N said' where possible — these can be replaced with real names during editorial review."
    else:
        speaker_note = "No speaker diarization is available. Attribute statements generically (e.g., 'a spokesperson said', 'one official noted')."

    prompt = f"""You are a local government reporter writing in AP style for the Tucson Daily Brief.

You have just monitored a meeting/briefing. Below is the full transcript. Write a news report covering the most significant actions, decisions, and statements.

Guidelines:
1. Lead with the single most newsworthy action, decision, or announcement
2. Use inverted pyramid structure — most important information first
3. Attribute all statements to speakers
4. Include specific numbers: vote counts, dollar amounts, dates, statistics
5. Cover 3-5 major items, with 2-3 paragraphs each
6. Note any contentious items with disagreement or heated discussion
7. Do NOT editorialize — report what happened factually
8. Use past tense throughout (this already happened)
9. Keep it concise — a reader should get the key takeaways in under 3 minutes

{speaker_note}

Format as markdown:
- H1 headline (newsy, specific, not bureaucratic)
- A dateline paragraph in bold that opens with the key news
- Subsequent paragraphs for each major item
- End with "**Also discussed:**" bullet list for minor items (if any)

Do NOT include any metadata, disclaimers, or notes about the transcript quality.

Meeting info:
- Event: {title}
- Date: {meeting_date}
- Duration: {duration_str}

TRANSCRIPT:

{formatted_transcript}"""

    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        CLAUDE_API_URL,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0]["text"]
            return None
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Draft management
# ---------------------------------------------------------------------------

def save_draft(data: dict, report_text: str) -> Path:
    """Save the Claude-generated report as a draft markdown file."""
    meta = data["meta"]
    slug = meta.get("slug", "unknown")
    title = meta.get("title", "Meeting")
    meeting_date = meta.get("started_at", "")[:10] or "unknown"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    header = f"""*Draft generated {now} by Tucson Daily Brief AI Reporter using {CLAUDE_MODEL}.*
*Source: Transcript of {title}, {meeting_date}.*
*This draft requires human editorial review before publication.*

---

"""

    draft_path = TRANSCRIPTS_DIR / f"{slug}-draft.md"
    draft_path.write_text(header + report_text)
    print(f"  Draft saved: {draft_path}")
    return draft_path


def send_telegram_review(draft_path: Path, data: dict) -> None:
    """Send the draft to Telegram for human review."""
    if not SEND_TELEGRAM.exists():
        print("  WARNING: send_telegram.py not found, skipping Telegram notification")
        return

    meta = data["meta"]
    slug = meta.get("slug", "unknown")
    title = meta.get("title", "Meeting")
    duration_sec = meta.get("duration_seconds", 0)
    duration_str = f"{duration_sec // 60} minutes" if duration_sec else "unknown"

    draft_text = draft_path.read_text()

    # Build the review message
    msg = f"""📝 AI REPORTER DRAFT — Requires Review

{title}
Duration: {duration_str}

---

{draft_text}

---

To approve and publish:
python3 ai_reporter.py --approve {draft_path}"""

    # Write to temp file and send via send_telegram.py
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, dir="/tmp") as f:
        f.write(msg)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python3", str(SEND_TELEGRAM), tmp_path],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            print("  Telegram review notification sent.")
        else:
            print(f"  WARNING: Telegram notification failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"  WARNING: Telegram notification failed: {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# HTML generation and publishing
# ---------------------------------------------------------------------------

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _inline_format(text: str) -> str:
    """Handle bold and inline formatting."""
    text = escape_html(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


def report_md_to_html(md_text: str) -> str:
    """Convert report markdown to HTML body content.

    Strips the metadata header (lines starting with * before the first ---)
    and converts the rest.
    """
    lines = md_text.strip().split("\n")
    html_parts = []

    # Skip metadata header (italic lines + --- at the top)
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            i += 1
            continue
        if stripped == "---" or re.match(r"^-{3,}$", stripped):
            i += 1
            break
        if not stripped:
            i += 1
            continue
        break  # Hit real content before finding ---

    # Convert remaining markdown to HTML (same logic as preview_md_to_html)
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if re.match(r"^-{3,}$", stripped) or stripped == "---":
            html_parts.append("<hr>")
            i += 1
            continue

        if stripped.startswith("# ") and not stripped.startswith("## "):
            html_parts.append(f"<h1>{_inline_format(stripped[2:])}</h1>")
            i += 1
            continue

        if stripped.startswith("## "):
            html_parts.append(f"<h2>{_inline_format(stripped[3:])}</h2>")
            i += 1
            continue

        if stripped.startswith("### "):
            html_parts.append(f"<h3>{_inline_format(stripped[4:])}</h3>")
            i += 1
            continue

        # Bullet list items
        if stripped.startswith("- ") or stripped.startswith("* "):
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                item_text = lines[i].strip()[2:]
                list_items.append(f"<li>{_inline_format(item_text)}</li>")
                i += 1
            html_parts.append("<ul>\n" + "\n".join(list_items) + "\n</ul>")
            continue

        # Blockquote
        if stripped.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            quote_text = " ".join(quote_lines)
            html_parts.append(f"<blockquote><p>{_inline_format(quote_text)}</p></blockquote>")
            continue

        # Regular paragraph
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if (not next_line or
                    next_line.startswith("#") or
                    next_line.startswith("> ") or
                    next_line.startswith("- ") or
                    next_line.startswith("* ") or
                    next_line == "---" or
                    re.match(r"^-{3,}$", next_line)):
                break
            para_lines.append(next_line)
            i += 1

        para_text = " ".join(para_lines)
        html_parts.append(f"<p>{_inline_format(para_text)}</p>")

    return "\n".join(html_parts)


def render_report_post(title: str, date: datetime, body_html: str) -> str:
    """Render a full news report HTML page."""
    slug = date.strftime("%Y-%m-%d")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape_html(title)}</title>
<link rel="stylesheet" href="../style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MEYSB9GYF2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-MEYSB9GYF2');
</script>
</head>
<body>
<div class="container">

<header>
<h1><a href="../">Tucson Daily Brief</a></h1>
<p class="tagline">An AI-powered local news pipeline by Nicholas De Leon</p>
</header>

<a class="back-link" href="../news-reports.html">&larr; All news reports</a>

<article id="report-{slug}">
<p class="post-meta">{escape_html(title)}</p>
{body_html}
</article>

<footer>
<p>By Nicholas De Leon</p>
<p class="footer-links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1878173070">Apple Podcasts</a> &middot;
<a href="https://www.youtube.com/@tucsondailybrief">YouTube</a> &middot;
<a href="https://www.linkedin.com/in/nicholas-de-leon-3b5b6a9">LinkedIn</a> &middot;
<a href="https://www.instagram.com/daylayownphoto">Instagram</a> &middot;
<a href="mailto:nicholas@daylayown.org">Email</a>
</p>
</footer>

</div>
</body>
</html>
"""


def render_report_index(posts: list[dict]) -> str:
    """Render the news reports index page."""
    items = []
    for p in posts:
        items.append(f"""<li>
<span class="post-date">{p["date"].strftime("%b %-d, %Y")}</span>
<a href="news-reports/{p["slug"]}.html">{escape_html(p["title"])}</a>
<p class="post-lede">{escape_html(p["lede"])}</p>
</li>""")

    post_list = "\n".join(items) if items else '<li class="empty">No news reports yet.</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>News Reports &mdash; Tucson Daily Brief</title>
<link rel="stylesheet" href="style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MEYSB9GYF2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-MEYSB9GYF2');
</script>
</head>
<body>
<div class="container">

<header>
<h1><a href="./">Tucson Daily Brief</a></h1>
<p class="tagline">News Reports &mdash; AI-drafted, human-reviewed coverage</p>
</header>

<p><a class="back-link" href="./">&larr; Daily briefings</a></p>

<ul class="post-list">
{post_list}
</ul>

<footer>
<p>By Nicholas De Leon</p>
<p class="footer-links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1878173070">Apple Podcasts</a> &middot;
<a href="https://www.youtube.com/@tucsondailybrief">YouTube</a> &middot;
<a href="https://www.linkedin.com/in/nicholas-de-leon-3b5b6a9">LinkedIn</a> &middot;
<a href="https://www.instagram.com/daylayownphoto">Instagram</a> &middot;
<a href="mailto:nicholas@daylayown.org">Email</a>
</p>
</footer>

</div>
</body>
</html>
"""


def extract_report_lede(md_text: str) -> str:
    """Extract the first substantive line for the index listing."""
    lines = md_text.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        # Skip headers, rules, metadata, empty
        if (stripped.startswith("#") or stripped == "---" or
                re.match(r"^-{3,}$", stripped) or
                stripped.startswith("*") or not stripped or
                stripped.startswith("- ") or stripped.startswith("> ")):
            continue
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
        if len(clean) > 120:
            clean = clean[:117] + "..."
        return clean
    return ""


def publish_report(md_path: str) -> None:
    """Convert an approved markdown report to HTML and publish to the site."""
    md_text = Path(md_path).read_text()

    # Extract slug from filename (e.g., pentagon-2026-03-26-approved.md → pentagon-2026-03-26)
    stem = Path(md_path).stem
    slug = re.sub(r"-(approved|draft)$", "", stem)

    # Extract date from slug
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", slug)
    if not date_match:
        print(f"  ERROR: Could not extract date from {md_path}", file=sys.stderr)
        return
    date = datetime.strptime(date_match.group(1), "%Y-%m-%d")

    # Extract title from first H1
    title = slug
    for line in md_text.split("\n"):
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            break

    # Convert and write
    REPORTS_DIR.mkdir(exist_ok=True)
    body_html = report_md_to_html(md_text)
    html_path = REPORTS_DIR / f"{slug}.html"
    html_path.write_text(render_report_post(title, date, body_html))
    print(f"  Published: {html_path}")

    # Rebuild news reports index
    rebuild_report_index()


def rebuild_report_index() -> None:
    """Scan all published reports and rebuild the index page."""
    if not REPORTS_DIR.exists():
        return

    posts = []
    for f in REPORTS_DIR.glob("*.html"):
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not date_match:
            continue
        dt = datetime.strptime(date_match.group(1), "%Y-%m-%d")
        content = f.read_text()

        # Extract title from post-meta
        title_match = re.search(r'<p class="post-meta">(.+?)</p>', content)
        post_title = title_match.group(1) if title_match else f.stem

        # Extract lede from first paragraph after post-meta
        lede_match = re.search(r'</p>\s*<(?:p|h[12])>(.+?)</(?:p|h[12])>', content)
        lede = ""
        if lede_match:
            lede = re.sub(r"<[^>]+>", "", lede_match.group(1))
            lede = lede.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            if len(lede) > 120:
                lede = lede[:117] + "..."

        posts.append({"date": dt, "slug": f.stem, "title": post_title, "lede": lede})

    posts.sort(key=lambda p: p["date"], reverse=True)
    index_path = SITE_DIR / "news-reports.html"
    index_path.write_text(render_report_index(posts))
    print(f"  Updated index: {index_path} ({len(posts)} report(s))")


# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------

def cmd_generate(args):
    """Generate a news report from a transcript JSON file."""
    json_path = args.transcript
    if not os.path.isfile(json_path):
        print(f"ERROR: File not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    data = load_transcript(json_path)
    meta = data["meta"]
    slug = meta.get("slug", "unknown")

    # Idempotency check
    draft_path = TRANSCRIPTS_DIR / f"{slug}-draft.md"
    if draft_path.exists() and not args.force:
        print(f"  Draft already exists: {draft_path}")
        print(f"  Use --force to regenerate.")
        return

    print(f"  Generating news report for: {meta.get('title', slug)}")
    report_text = generate_news_report(data)
    if not report_text:
        print("  ERROR: Failed to generate news report", file=sys.stderr)
        sys.exit(1)

    draft_path = save_draft(data, report_text)
    send_telegram_review(draft_path, data)


def cmd_approve(args):
    """Approve a draft and publish it."""
    draft_path = Path(args.approve)
    if not draft_path.exists():
        print(f"ERROR: File not found: {draft_path}", file=sys.stderr)
        sys.exit(1)

    # Copy draft to approved
    slug = re.sub(r"-(draft|approved)$", "", draft_path.stem)
    approved_path = TRANSCRIPTS_DIR / f"{slug}-approved.md"
    approved_path.write_text(draft_path.read_text())
    print(f"  Approved: {approved_path}")

    # Publish
    publish_report(str(approved_path))


def cmd_publish(args):
    """Publish an already-approved markdown file."""
    publish_report(args.publish)


def main():
    parser = argparse.ArgumentParser(
        description="AI Reporter — generate and publish news reports from transcripts"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("transcript", nargs="?",
                       help="Path to transcript JSON file (generate mode)")
    group.add_argument("--approve",
                       help="Approve a draft and publish it")
    group.add_argument("--publish",
                       help="Publish an already-approved markdown file")

    parser.add_argument("--force", action="store_true",
                        help="Regenerate even if draft already exists")

    args = parser.parse_args()

    TRANSCRIPTS_DIR.mkdir(exist_ok=True)

    if args.approve:
        cmd_approve(args)
    elif args.publish:
        cmd_publish(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
