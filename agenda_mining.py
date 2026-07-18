#!/usr/bin/env python3
"""
Pima County Board of Supervisors — Agenda Mining Pipeline

Fetches upcoming meeting agendas from the Legistar API, extracts
substantive items, and generates a "What to Watch" markdown summary
for human review.

Usage:
    python agenda_mining.py                  # Check for upcoming meetings
    python agenda_mining.py --event-id 1797  # Analyze a specific meeting

Output saved to: agenda-watch/pima-county-YYYY-MM-DD.md
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from generate_post import (
    ANALYTICS_HTML,
    seo_head_html,
    derive_description,
    HAND_RULE_SVG,
    SCROLL_TRIGGER_JS,
    SUBSCRIBE_PANEL_HTML,
    footer_html,
    rebuild_homepage,
    section_nav_html,
    site_header_html,
)

# --- Config ---
LEGISTAR_BASE = "https://webapi.legistar.com/v1/pima"
SITE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = str(SITE_DIR / "agenda-watch")
PUBLISHED_DIR = SITE_DIR / "meeting-watch"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Item types that are substantive (skip procedural boilerplate)
SKIP_KEYWORDS = [
    "roll call",
    "pledge of allegiance",
    "moment of silence",
    "adjournment",
    "recess",
    "broadcast information",
    "agenda/addendum",
    "public participation speakers",
    "approval of minutes",
    "consent calendar",
    "personal privilege",
    "hearing room notice",
    "accessibility",
    "page break",
    "clerk's note",
    "land acknowledgement",
    "pause 4 paws",
    "current events/public acknowledgements",
    "agenda adjustments",
    "presentation/proclamation",
    "individuals wishing to address",
    "members of the pima county board",
    "the meeting can be streamed",
    "law permits that a video",
    "wheelchair and handicapped accessible",
    "call to the public",
    "pima county board of supervisors",
    "posted:",
    "date/time posted",
    "date/time reposted",
    "special event liquor license",
    "______",
    "attest:",
]


def fetch_json(url: str) -> list | dict:
    """Fetch JSON from a URL."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def get_upcoming_events(days_ahead: int = 30) -> list[dict]:
    """Fetch upcoming Board of Supervisors meetings."""
    today = datetime.now().strftime("%Y-%m-%dT00:00:00")
    future = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%dT00:00:00")

    params = urllib.parse.urlencode({
        "$filter": f"EventDate ge datetime'{today}' and EventDate le datetime'{future}'",
        "$orderby": "EventDate asc",
    })
    url = f"{LEGISTAR_BASE}/events?{params}"
    events = fetch_json(url)

    # Filter to Board of Supervisors only
    return [e for e in events if e.get("EventBodyName") == "Board of Supervisors"]


def get_event_items(event_id: int) -> list[dict]:
    """Fetch all agenda items for a meeting, including notes and attachments."""
    url = f"{LEGISTAR_BASE}/events/{event_id}/eventitems?AgendaNote=1&MinutesNote=1&Attachments=1"
    return fetch_json(url)


def is_substantive(item: dict) -> bool:
    """Filter out procedural items."""
    title = (item.get("EventItemTitle") or "").lower()
    note = (item.get("EventItemAgendaNote") or "").lower()
    combined = title + " " + note

    # Skip if title or note matches boilerplate
    if any(skip in combined for skip in SKIP_KEYWORDS):
        return False

    # Skip items with no real content (just a section header with no matter attached)
    if not item.get("EventItemMatterId") and not item.get("EventItemAgendaNote") and len(title) < 40:
        return False

    # Skip untitled items (usually orphaned procedural attachments)
    if title in ("untitled", ""):
        return False

    return True


def format_item(item: dict) -> str:
    """Format a single agenda item as markdown."""
    number = item.get("EventItemAgendaNumber") or ""
    title = item.get("EventItemTitle") or "Untitled"
    matter_name = item.get("EventItemMatterName") or ""
    matter_type = item.get("EventItemMatterType") or ""
    note = item.get("EventItemAgendaNote") or ""
    matter_file = item.get("EventItemMatterFile") or ""
    consent = item.get("EventItemConsent")

    # Build attachments list
    attachments = item.get("EventItemMatterAttachments") or []
    attachment_names = [a.get("MatterAttachmentName", "") for a in attachments if a.get("MatterAttachmentName")]

    lines = []

    # Item header
    header = f"**{number}** " if number else ""
    header += title
    if matter_type:
        header += f" _{matter_type}_"
    lines.append(f"### {header}")

    if consent:
        lines.append("*(Consent calendar — typically approved without discussion)*")

    if matter_name and matter_name != title:
        lines.append(f"\n{matter_name}")

    # Agenda note (truncate if very long)
    if note:
        # Clean up HTML tags that sometimes appear
        clean_note = note.replace("<br>", "\n").replace("<br/>", "\n")
        clean_note = clean_note.replace("<p>", "\n").replace("</p>", "")
        clean_note = clean_note.replace("&amp;", "&").replace("&nbsp;", " ")
        # Remove other HTML tags
        import re
        clean_note = re.sub(r"<[^>]+>", "", clean_note)
        clean_note = clean_note.strip()
        if len(clean_note) > 1000:
            clean_note = clean_note[:1000] + "..."
        if clean_note:
            lines.append(f"\n{clean_note}")

    # Attachments
    if attachment_names:
        lines.append(f"\nAttachments ({len(attachment_names)}):")
        for name in attachment_names[:10]:  # Cap at 10
            lines.append(f"- {name}")

    # Legistar link
    if matter_file:
        lines.append(f"\n[View in Legistar](https://pima.legistar.com/LegislationDetail.aspx?ID={item.get('EventItemMatterId')}&GUID={item.get('EventItemMatterGuid')})")

    return "\n".join(lines)


_CANCEL_WORD = r"cancell?ed|cancellation"

# The cancel word next to "meeting"/"session" — not merely present. An agenda
# item about a canceled *contract* must not read as a canceled *meeting*.
_CANCEL_NEAR_MEETING_RE = re.compile(
    rf"(?:meeting|session)s?[^.]{{0,80}}\b(?:{_CANCEL_WORD})\b"
    rf"|\b(?:{_CANCEL_WORD})\b[^.]{{0,80}}(?:meeting|session)s?",
    re.IGNORECASE,
)


def is_canceled_meeting(meeting_label: str, agenda_text: str = "") -> bool:
    """True when the posted meeting is canceled and there is nothing to preview.

    Both signals are needed because the portals disagree on where they say it:
    Marana and Oro Valley put it in the meeting label itself ("Council Regular
    Meeting - CANCELED"), while Tucson leaves the label reading "Mayor & Council
    - Regular" and buries the notice in the PDF body ("Due to an anticipated
    lack of quorum, the ... meetings of JULY 7, 2026, are CANCELLED"). Checking
    only the label misses every Tucson cancellation.

    The body check is confined to the notice header, where a cancellation is
    announced, so an ordinary agenda that happens to cancel a contract 200 lines
    down doesn't trip it.
    """
    if re.search(_CANCEL_WORD, meeting_label or "", re.IGNORECASE):
        return True
    head = " ".join((agenda_text or "").split("\n")[:40])
    return bool(_CANCEL_NEAR_MEETING_RE.search(head))


def canceled_analysis_md(body_name: str, meeting_date: datetime) -> str:
    """Stand-in for the editorial analysis when a meeting is canceled.

    Deliberately a flat statement of fact with no "what to watch" framing: there
    is no agenda, so there is nothing to analyze, and asking a model to write a
    preview anyway invites it to manufacture significance. It did exactly that
    on 2026-07-21, filing a full preview — headline, "Reporter's Note",
    follow-up questions — about a meeting that was not happening.

    Still published rather than skipped, because "is there a meeting Tuesday?"
    is a real reader question and the answer is worth a page.
    """
    date_str = meeting_date.strftime("%B %-d, %Y")
    return "\n".join([
        f"**The {date_str} {body_name} meeting has been canceled.** "
        "No agenda items will be heard and no public business will be conducted.",
        "",
        "This page exists to record the cancellation. There is no agenda to preview.",
    ])


def analyze_with_claude(event: dict, substantive_items: list[dict]) -> str | None:
    """Send agenda items to Claude for editorial analysis."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  WARNING: ANTHROPIC_API_KEY not set, skipping LLM analysis")
        return None

    event_date = datetime.strptime(event["EventDate"][:10], "%Y-%m-%d")
    date_str = event_date.strftime("%A, %B %d, %Y")

    # Build a compact representation of items for the prompt
    items_text = []
    for item in substantive_items:
        number = item.get("EventItemAgendaNumber") or ""
        title = item.get("EventItemTitle") or ""
        matter_name = item.get("EventItemMatterName") or ""
        matter_type = item.get("EventItemMatterType") or ""
        note = item.get("EventItemAgendaNote") or ""
        consent = item.get("EventItemConsent")

        # Clean HTML from note
        clean_note = re.sub(r"<[^>]+>", "", note).strip()
        if len(clean_note) > 500:
            clean_note = clean_note[:500] + "..."

        attachments = item.get("EventItemMatterAttachments") or []
        attachment_names = [a.get("MatterAttachmentName", "") for a in attachments if a.get("MatterAttachmentName")]

        entry = f"Item {number}: {title}"
        if matter_name and matter_name != title:
            entry += f"\n  Matter: {matter_name}"
        if matter_type:
            entry += f"\n  Type: {matter_type}"
        if consent:
            entry += "\n  [CONSENT CALENDAR]"
        if clean_note:
            entry += f"\n  Note: {clean_note}"
        if attachment_names:
            entry += f"\n  Attachments: {', '.join(attachment_names[:5])}"
        items_text.append(entry)

    agenda_dump = "\n\n".join(items_text)

    prompt = f"""You are a local government reporter covering Pima County, Arizona for the Tucson Daily Brief. Analyze the following Board of Supervisors meeting agenda for {date_str}.

Your job: identify the 5-8 most newsworthy items and explain WHY they matter to Tucson/Pima County residents. Think like a beat reporter — what would your editor want you to cover? What affects people's lives, money, safety, or rights?

Prioritize:
1. Policy changes that affect residents (ordinances, zoning, regulations)
2. Large spending decisions or contracts (especially $500K+)
3. Public hearings where community input is sought
4. Items with political tension or controversy
5. Land use, development, and infrastructure decisions
6. Items that connect to ongoing stories (immigration, water, budget deficit, etc.)

De-prioritize:
- Proclamations and ceremonial items (unless politically significant)
- Routine contract renewals under $100K
- Administrative appointments (unless controversial)
- Precinct committeemen and minor board vacancies

For each item you highlight, write:
- A clear, specific headline (not the bureaucratic title from the agenda)
- 2-3 sentences explaining what it is and why it matters
- Note if it's on the consent calendar (which means it could pass without any discussion)

Format as markdown. Start with a brief 2-sentence overview of the meeting, then list your picks.

AGENDA ITEMS:

{agenda_dump}"""

    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 2000,
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0]["text"]
            return None
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}")
        return None


def generate_preview(event: dict, items: list[dict], analysis: str,
                     canceled: bool = False) -> str:
    """Generate the publishable preview — just the editorial analysis.

    canceled=True swaps the title (nothing to "watch"), drops the item counts,
    and swaps the disclosure — a cancellation notice is written by
    canceled_analysis_md(), not by a model, so crediting CLAUDE_MODEL for it
    would be a false disclosure.
    """
    event_date = datetime.strptime(event["EventDate"][:10], "%Y-%m-%d")
    date_str = event_date.strftime("%B %d, %Y")
    day_of_week = event_date.strftime("%A")
    time_str = event.get("EventTime") or ""
    location = event.get("EventLocation") or ""

    substantive = [i for i in items if is_substantive(i)]
    consent_items = [i for i in substantive if i.get("EventItemConsent")]
    discussion_items = [i for i in substantive if not i.get("EventItemConsent")]

    lines = []
    lines.append(f"# Pima County Board of Supervisors — {'Meeting Canceled' if canceled else 'What to Watch'}")
    lines.append(f"## {day_of_week}, {date_str} at {time_str}")
    if location:
        lines.append(f"\n{location}")
    lines.append("")
    if not canceled:
        lines.append(f"**{len(substantive)} substantive items** on the agenda ({len(discussion_items)} for discussion, {len(consent_items)} on consent calendar)")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(analysis)
    lines.append("")
    lines.append("---")
    if canceled:
        lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline.*")
        lines.append(f"*No agenda was posted for this meeting — this notice records the cancellation and is not AI-generated.*")
    else:
        lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline using {CLAUDE_MODEL}.*")
        lines.append(f"*AI-assisted journalism — reviewed by a human editor before publication.*")
    lines.append(f"*Source: [Pima County Legistar](https://pima.legistar.com/Calendar.aspx)*")

    return "\n".join(lines)


def generate_full_report(event: dict, items: list[dict]) -> str:
    """Generate the full itemized agenda — reporter's reference, not for publication."""
    event_date = datetime.strptime(event["EventDate"][:10], "%Y-%m-%d")
    date_str = event_date.strftime("%B %d, %Y")
    day_of_week = event_date.strftime("%A")
    time_str = event.get("EventTime") or ""
    location = event.get("EventLocation") or ""
    comment = event.get("EventComment") or ""

    lines = []
    lines.append(f"# Pima County Board of Supervisors — Full Agenda Reference")
    lines.append(f"## {day_of_week}, {date_str} at {time_str}")
    if comment:
        lines.append(f"*{comment}*")
    if location:
        lines.append(f"\nLocation: {location}")
    lines.append("")

    substantive = [i for i in items if is_substantive(i)]
    consent_items = [i for i in substantive if i.get("EventItemConsent")]
    discussion_items = [i for i in substantive if not i.get("EventItemConsent")]

    lines.append(f"**{len(substantive)} substantive items** ({len(discussion_items)} for discussion, {len(consent_items)} on consent calendar)")
    lines.append("")

    # Public hearings first
    public_hearings = [i for i in discussion_items if "public hearing" in (i.get("EventItemMatterType") or "").lower() or "public hearing" in (i.get("EventItemTitle") or "").lower()]
    other_discussion = [i for i in discussion_items if i not in public_hearings]

    if public_hearings:
        lines.append("---")
        lines.append("## Public Hearings")
        lines.append("")
        for item in public_hearings:
            lines.append(format_item(item))
            lines.append("")

    if other_discussion:
        lines.append("---")
        lines.append("## Discussion Items")
        lines.append("")
        for item in other_discussion:
            lines.append(format_item(item))
            lines.append("")

    if consent_items:
        lines.append("---")
        lines.append("## Consent Calendar")
        lines.append("*(Typically approved as a block without discussion. Any supervisor can pull an item for separate discussion.)*")
        lines.append("")
        for item in consent_items:
            lines.append(format_item(item))
            lines.append("")

    lines.append("---")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline*")
    lines.append(f"*Source: [Pima County Legistar](https://pima.legistar.com/Calendar.aspx)*")

    return "\n".join(lines)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def preview_md_to_html(md_text: str) -> str:
    """Convert preview markdown to HTML body content."""
    lines = md_text.strip().split("\n")
    html_parts = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$", stripped) or stripped == "---":
            html_parts.append("<hr>")
            i += 1
            continue

        # H1
        if stripped.startswith("# ") and not stripped.startswith("## "):
            html_parts.append(f"<h1>{_heading_text(stripped[2:])}</h1>")
            i += 1
            continue

        # H2
        if stripped.startswith("## "):
            html_parts.append(f"<h2>{_heading_text(stripped[3:])}</h2>")
            i += 1
            continue

        # H3
        if stripped.startswith("### "):
            html_parts.append(f"<h3>{_heading_text(stripped[4:])}</h3>")
            i += 1
            continue

        # Blockquote
        if stripped.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            quote_text = " ".join(quote_lines)
            # Apply inline formatting
            quote_text = _inline_format(quote_text)
            html_parts.append(f"<blockquote><p>{quote_text}</p></blockquote>")
            continue

        # Italic line (standalone *text*) — every preview's source-attribution
        # footer takes this branch, and it carries a markdown link, so it needs
        # inline formatting rather than a bare escape.
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            inner = stripped[1:-1]
            html_parts.append(f"<p><em>{_inline_format(inner)}</em></p>")
            i += 1
            continue

        # Regular paragraph — collect continuation lines
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if (not next_line or
                    next_line.startswith("#") or
                    next_line.startswith("> ") or
                    next_line == "---" or
                    re.match(r"^-{3,}$", next_line)):
                break
            para_lines.append(next_line)
            i += 1

        para_text = " ".join(para_lines)
        para_html = _inline_format(para_text)
        html_parts.append(f"<p>{para_html}</p>")

    return "\n".join(html_parts)


def _heading_text(raw: str) -> str:
    """Inline-format a heading, unwrapping a fully-bolded line.

    Previews routinely arrive as "### **Headline**". A heading renders bold
    already, so the wrapping pair is redundant — but running it through
    escape_html alone published the asterisks as literal visible text
    (meeting-watch/marana-council-2026-07-21.html). Unwrap the outer pair, then
    inline-format the rest so partial bold inside a heading still works.
    """
    text = raw.strip()
    m = re.fullmatch(r"\*\*(.+)\*\*", text, re.DOTALL)
    if m and "**" not in m.group(1):
        text = m.group(1)
    return _inline_format(text)


def _inline_format(text: str) -> str:
    """Handle bold, links, and inline formatting."""
    text = escape_html(text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Markdown links. Without this every preview published its own source
    # attribution as dead text — "Source: [Town of Marana Agendas](https://...)"
    # rendered literally on all 39 pages, so the provenance link never worked.
    # Runs after escape_html, so & and " in the URL are already entity-safe;
    # the scheme is pinned to http(s) so nothing else can reach an href.
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    # Emoji indicators
    text = text.replace("&amp;#x26A0;", "&#x26A0;")
    return text


def extract_preview_lede(md_text: str) -> str:
    """Extract the first line of the overview for the index listing."""
    lines = md_text.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        # Skip headers, rules, metadata lines
        if (stripped.startswith("#") or stripped == "---" or
                stripped.startswith("*") or not stripped or
                "substantive items" in stripped):
            continue
        # First real paragraph text
        clean = stripped.replace("**", "")
        if len(clean) > 120:
            clean = clean[:117] + "..."
        return clean
    return ""


def render_meeting_post(title: str, date: datetime, body_html: str, page_slug: str = "") -> str:
    """Render a full meeting watch HTML page. `page_slug` is the output
    filename stem (e.g. "pima-county-bos-2026-03-03") for canonical/OG URLs."""
    from generate_post import ARROW_LEFT_SVG, post_header_html
    slug = date.strftime("%Y-%m-%d")
    seo = ""
    if page_slug:
        seo = seo_head_html(
            title=f"{title} — Tucson Daily Brief",
            description=derive_description(body_html) or f"What to watch at the {title} meeting.",
            path=f"meeting-watch/{page_slug}.html",
            og_type="article", published=date) + "\n"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape_html(title)} &mdash; Tucson Daily Brief</title>
{seo}<link rel="stylesheet" href="../style.css">
{ANALYTICS_HTML}
</head>
<body>

{post_header_html()}

<div class="container">
{section_nav_html(active="meetings", path_prefix="../")}
</div>

<main>
<div class="container container--reading">
<a class="back-link" href="../meeting-watch.html">{ARROW_LEFT_SVG} All Local Meeting Previews</a>

<article id="meeting-{slug}" class="post-page">
<p class="post-meta">{title}</p>
{body_html}
</article>
</div>
</main>

<div class="container">
<div style="margin-bottom:var(--gap-xl)">{SUBSCRIBE_PANEL_HTML}</div>
{footer_html(path_prefix="../")}
</div>

{SCROLL_TRIGGER_JS}
</body>
</html>
"""


def render_meeting_index(posts: list[dict]) -> str:
    """Render the meeting watch index page."""
    items = []
    for p in posts:
        items.append(f"""<li>
<span class="post-date">{p["date"].strftime("%b %-d, %Y")}</span>
<a href="meeting-watch/{p["slug"]}.html">{escape_html(p["title"])}</a>
<p class="post-lede">{escape_html(p["lede"])}</p>
</li>""")

    post_list = "\n".join(items) if items else '<li class="empty">No meeting previews yet.</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Local Meeting Previews &mdash; Tucson Daily Brief</title>
{seo_head_html(
    title="Local Meeting Previews — Tucson Daily Brief",
    description="AI-assisted previews of what's on the agenda for local government meetings across Tucson, Pima County, Marana, and Oro Valley — published the morning agendas drop.",
    path="meeting-watch.html")}
<link rel="stylesheet" href="style.css">
{ANALYTICS_HTML}
</head>
<body>

{site_header_html()}

<div class="container">
{section_nav_html(active="meetings")}
</div>

<main>
<div class="container container--editorial">
<div style="padding-top:var(--gap-xl);margin-bottom:var(--gap-l)">
<h1 class="section-head">Local Meeting Previews</h1>
<p class="section-intro">Before each meeting: AI-assisted previews of what&rsquo;s on the agenda for local government bodies across Tucson, Pima County, Marana, and Oro Valley. Auto-published the morning agendas drop.</p>
</div>

<div style="margin-bottom:var(--gap-xl)">{SUBSCRIBE_PANEL_HTML}</div>

<ul class="post-list">
{post_list}
</ul>
</div>
</main>

<div class="container">
{footer_html()}
</div>

{SCROLL_TRIGGER_JS}
</body>
</html>
"""


def publish_preview(preview_path: str) -> None:
    """Convert a preview markdown file to HTML and publish to the site."""
    md_text = Path(preview_path).read_text()

    # Extract date from filename (pima-county-2026-03-03-preview.md)
    match = re.search(r"(\d{4}-\d{2}-\d{2})", Path(preview_path).stem)
    if not match:
        print(f"  ERROR: Could not extract date from {preview_path}")
        return
    date = datetime.strptime(match.group(1), "%Y-%m-%d")
    slug = f"pima-county-bos-{date.strftime('%Y-%m-%d')}"

    # Extract title from first H1/H2
    title = "Pima County BOS — What to Watch"
    for line in md_text.split("\n"):
        if line.startswith("## "):
            title = line[3:].strip()
            break

    # Convert and write
    PUBLISHED_DIR.mkdir(exist_ok=True)
    body_html = preview_md_to_html(md_text)
    html_path = PUBLISHED_DIR / f"{slug}.html"
    html_path.write_text(render_meeting_post(title, date, body_html, page_slug=html_path.stem))
    print(f"  Published: {html_path}")

    # Rebuild meeting watch index
    posts = []
    for f in PUBLISHED_DIR.glob("*.html"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not m:
            continue
        dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        content = f.read_text()

        # Extract title from post-meta
        title_match = re.search(r'<p class="post-meta">(.+?)</p>', content)
        post_title = title_match.group(1) if title_match else f.stem

        # Extract lede from first paragraph after post-meta
        lede_match = re.search(r'</p>\s*<(?:p|h[12])>(.+?)</(?:p|h[12])>', content)
        lede = ""
        if lede_match:
            lede = re.sub(r"<[^>]+>", "", lede_match.group(1))
            # Unescape HTML entities so escape_html() doesn't double-encode
            lede = lede.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            if len(lede) > 120:
                lede = lede[:117] + "..."

        posts.append({"date": dt, "slug": f.stem, "title": post_title, "lede": lede})

    posts.sort(key=lambda p: p["date"], reverse=True)
    index_path = SITE_DIR / "meeting-watch.html"
    index_path.write_text(render_meeting_index(posts))
    print(f"  Updated index: {index_path} ({len(posts)} preview(s))")

    # Refresh the homepage so the new meeting surfaces in the cross-section card
    rebuild_homepage()


def main():
    parser = argparse.ArgumentParser(description="Pima County agenda mining pipeline")
    parser.add_argument("--event-id", type=int, help="Analyze a specific Legistar event ID")
    parser.add_argument("--days", type=int, default=30, help="Look ahead N days for upcoming meetings (default: 30)")
    parser.add_argument("--list", action="store_true", help="List upcoming meetings without generating reports")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM editorial analysis")
    parser.add_argument("--publish", type=str, metavar="PREVIEW_FILE", help="Publish a preview markdown file to the site as HTML")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.publish:
        if not os.path.isfile(args.publish):
            print(f"Error: file not found: {args.publish}", file=sys.stderr)
            sys.exit(1)
        print(f"Publishing: {args.publish}")
        publish_preview(args.publish)
        return

    if args.event_id:
        # Fetch specific event
        event = fetch_json(f"{LEGISTAR_BASE}/events/{args.event_id}")
        events = [event]
    else:
        # Fetch upcoming events
        print(f"Checking for upcoming Pima County BOS meetings (next {args.days} days)...")
        events = get_upcoming_events(args.days)

    if not events:
        print("No upcoming Board of Supervisors meetings found.")
        return

    for event in events:
        event_date = event["EventDate"][:10]
        event_time = event.get("EventTime", "")
        event_id = event["EventId"]
        comment = event.get("EventComment") or ""
        label = f" ({comment})" if comment else ""

        if args.list:
            agenda_status = event.get("EventAgendaStatusName", "Unknown")
            print(f"  {event_date} {event_time}{label} — Event ID: {event_id} — Agenda: {agenda_status}")
            continue

        print(f"\nProcessing: {event_date} {event_time}{label} (Event ID: {event_id})")

        # Fetch agenda items
        items = get_event_items(event_id)
        if not items:
            print(f"  No agenda items found (agenda may not be published yet)")
            continue

        substantive = [i for i in items if is_substantive(i)]
        print(f"  Found {len(items)} total items, {len(substantive)} substantive")

        # Build filename base
        suffix = ""
        if comment:
            suffix = f"-{comment.lower().replace(' ', '-')}"
        base = f"pima-county-{event_date}{suffix}"

        # Check if preview already exists (idempotency guard)
        preview_path = os.path.join(OUTPUT_DIR, f"{base}-preview.md")
        if os.path.exists(preview_path):
            print(f"  Preview already exists: {preview_path}")
            continue

        # Always save the full reference report
        full_report = generate_full_report(event, items)
        full_path = os.path.join(OUTPUT_DIR, f"{base}-full.md")
        with open(full_path, "w") as f:
            f.write(full_report)
        print(f"  Saved full reference: {full_path}")

        # LLM analysis → publishable preview
        if not args.no_llm:
            # Legistar signals a cancellation in EventComment and/or the agenda
            # status, not in the body text — so pass those as the label.
            event_label = " ".join(filter(None, [
                event.get("EventComment") or "",
                event.get("EventAgendaStatusName") or "",
            ]))
            canceled = is_canceled_meeting(event_label)
            if canceled:
                print("  Meeting is CANCELED — writing stub preview, skipping Claude")
                analysis = canceled_analysis_md(
                    "Pima County Board of Supervisors",
                    datetime.strptime(event["EventDate"][:10], "%Y-%m-%d"),
                )
            else:
                print("  Running editorial analysis with Claude...")
                analysis = analyze_with_claude(event, substantive)
            if analysis:
                print("  Editorial analysis complete")
                preview = generate_preview(event, items, analysis, canceled=canceled)
                with open(preview_path, "w") as f:
                    f.write(preview)
                print(f"  Saved publishable preview: {preview_path}")

    if args.list:
        print(f"\nFound {len(events)} upcoming meeting(s). Run without --list to generate reports.")


if __name__ == "__main__":
    main()
