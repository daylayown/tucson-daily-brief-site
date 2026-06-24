#!/usr/bin/env python3
"""
Build the RAG search index for Tucson Daily Brief.

Walks the published corpus (daily briefs, news reports, meeting previews,
public-record filings) and the unpublished agenda-watch full references,
chunks each document by its native structure, embeds chunks via Voyage AI,
and writes the result to a sqlite-vec database at rag/index.sqlite.

Idempotent: re-running only re-embeds files whose contents have changed.

Usage:
    python rag/build_index.py              # incremental — embeds new/changed
    python rag/build_index.py --rebuild    # drop everything and re-embed all
    python rag/build_index.py --dry-run    # walk + chunk, no API calls or DB writes
"""

import argparse
import hashlib
import html as html_mod
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec
import voyageai

SITE_DIR = Path(__file__).resolve().parent.parent
RAG_DIR = Path(__file__).resolve().parent
DB_PATH = RAG_DIR / "index.sqlite"
BASE_URL = "https://tucsondailybrief.com"
EMBEDDING_MODEL = "voyage-3-lite"
EMBEDDING_DIM = 512
BATCH_SIZE = 128
AGENDA_WINDOW_CHARS = 1500
AGENDA_OVERLAP_CHARS = 200


# --- DB ---------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    source_file TEXT NOT NULL,
    source_url TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    date TEXT,
    section_title TEXT,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embed_input TEXT NOT NULL,
    UNIQUE(source_file, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_file);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_type ON chunks(doc_type);
CREATE INDEX IF NOT EXISTS idx_chunks_date ON chunks(date);

CREATE TABLE IF NOT EXISTS file_state (
    source_file TEXT PRIMARY KEY,
    file_hash TEXT NOT NULL,
    indexed_at TEXT NOT NULL
);
"""


def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.executescript(SCHEMA)
    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[{EMBEDDING_DIM}])"
    )
    return conn


def drop_all(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM chunks")
    conn.execute("DELETE FROM vec_chunks")
    conn.execute("DELETE FROM file_state")
    conn.commit()


# --- HTML helpers -----------------------------------------------------------

def strip_tags(s: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def extract_article(html: str) -> str:
    m = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
    return m.group(1) if m else ""


# --- Chunkers ---------------------------------------------------------------
# Each chunker returns a list of dicts: {section_title, chunk_index, content}.
# `content` is the user-facing text shown in citations.
# `embed_input` is constructed later (prepends doc context for the embedding model).


def chunk_daily_brief(html: str, date_iso: str) -> list[dict]:
    """One chunk per story: section header + bold headline + body + source line."""
    article = extract_article(html)
    chunks: list[dict] = []
    current_section = None
    pending: dict | None = None
    chunk_idx = 0

    # Walk h2 / p.source / p / hr in order
    for m in re.finditer(
        r'<h2>(?P<h2>.+?)</h2>'
        r'|<p class="source">(?P<src>.+?)</p>'
        r'|<p class="post-meta">(?P<meta>.+?)</p>'
        r'|<p>(?P<body>.+?)</p>'
        r'|(?P<hr><hr>)',
        article,
        re.DOTALL,
    ):
        if m.group("h2") is not None:
            current_section = strip_tags(m.group("h2"))
            if pending:
                chunks.append({"section_title": pending["section"], "chunk_index": chunk_idx, "content": pending["text"]})
                chunk_idx += 1
                pending = None
        elif m.group("src") is not None:
            if pending:
                pending["text"] += "\n\nSources: " + strip_tags(m.group("src"))
                chunks.append({"section_title": pending["section"], "chunk_index": chunk_idx, "content": pending["text"]})
                chunk_idx += 1
                pending = None
        elif m.group("meta") is not None:
            continue  # date metadata, already in chunk metadata
        elif m.group("body") is not None:
            text = strip_tags(m.group("body"))
            if not text or len(text) < 20:
                continue
            if pending:
                chunks.append({"section_title": pending["section"], "chunk_index": chunk_idx, "content": pending["text"]})
                chunk_idx += 1
            pending = {"section": current_section or "Untitled", "text": text}

    if pending:
        chunks.append({"section_title": pending["section"], "chunk_index": chunk_idx, "content": pending["text"]})

    return chunks


def chunk_news_report(html: str, date_iso: str) -> list[dict]:
    """News report: title+lede as one chunk, then one chunk per <h2> section."""
    article = extract_article(html)
    chunks: list[dict] = []
    chunk_idx = 0

    # Title: <h1>...</h1>
    title_m = re.search(r"<h1>(.+?)</h1>", article, re.DOTALL)
    title = strip_tags(title_m.group(1)) if title_m else ""

    # Lede: first <p><strong>...</strong></p> after title
    lede_m = re.search(r"<p><strong>(.+?)</strong></p>", article, re.DOTALL)
    lede = strip_tags(lede_m.group(1)) if lede_m else ""

    if title or lede:
        body = title
        if lede:
            body += ("\n\n" if body else "") + lede
        chunks.append({"section_title": title or "Lede", "chunk_index": chunk_idx, "content": body})
        chunk_idx += 1

    # Sections: split on <h2>
    sections = re.split(r"<h2>(.+?)</h2>", article)
    # split returns [pre, h2_1, body_1, h2_2, body_2, ...]
    for i in range(1, len(sections), 2):
        heading = strip_tags(sections[i])
        body_html = sections[i + 1] if i + 1 < len(sections) else ""

        # Collect <p>, <ul><li>, <blockquote> text in document order
        parts: list[str] = []
        for m in re.finditer(
            r"<p>(?P<p>.+?)</p>|<ul>(?P<ul>.+?)</ul>|<blockquote>(?P<bq>.+?)</blockquote>",
            body_html,
            re.DOTALL,
        ):
            if m.group("p"):
                parts.append(strip_tags(m.group("p")))
            elif m.group("ul"):
                items = re.findall(r"<li>(.+?)</li>", m.group("ul"), re.DOTALL)
                for it in items:
                    parts.append("• " + strip_tags(it))
            elif m.group("bq"):
                parts.append(strip_tags(m.group("bq")))
        body_text = "\n\n".join(p for p in parts if p)
        if not body_text:
            continue
        chunks.append(
            {"section_title": heading, "chunk_index": chunk_idx, "content": f"{heading}\n\n{body_text}"}
        )
        chunk_idx += 1

    return chunks


def chunk_meeting_watch(html: str, date_iso: str) -> list[dict]:
    """Meeting preview: one chunk per <h3> 'Top Item' (with its surrounding paragraphs)."""
    article = extract_article(html)
    chunks: list[dict] = []
    chunk_idx = 0

    # Capture the top analysis paragraph (between "Reporter's Agenda Analysis" h3 and the next hr/h2)
    intro_m = re.search(
        r"<h3>Reporter's Agenda Analysis</h3>(.*?)(?=<hr>|<h2>|<h3>)",
        article,
        re.DOTALL,
    )
    if intro_m:
        intro_text = "\n\n".join(strip_tags(p) for p in re.findall(r"<p>(.+?)</p>", intro_m.group(1), re.DOTALL))
        if intro_text.strip():
            chunks.append({"section_title": "Reporter's Agenda Analysis", "chunk_index": chunk_idx, "content": intro_text})
            chunk_idx += 1

    # One chunk per top-item heading. New format uses <h3>; the earliest few
    # files used numbered <h2> items (e.g., "1. 🚨 ..."). Try <h3> first; if
    # we found no items, fall back to numbered <h2>.
    h3_pattern = (
        r"<h3>(?P<h>(?!Reporter's Agenda).+?)</h3>"
        r"(?P<body>.*?)(?=<h3>|<hr>\s*<p><em>Generated|<hr>\s*<p><em>Source|</article>)"
    )
    h2_numbered_pattern = (
        r"<h2>(?P<h>\d+\.\s.+?)</h2>"
        r"(?P<body>.*?)(?=<h2>\d+\.\s|<hr>\s*<p><em>Generated|<hr>\s*<p><em>Source|</article>)"
    )

    items_added_before = chunk_idx
    for pattern in (h3_pattern, h2_numbered_pattern):
        for m in re.finditer(pattern, article, re.DOTALL):
            heading = strip_tags(m.group("h"))
            body_html = m.group("body")
            parts: list[str] = []
            for pm in re.finditer(
                r"<p>(?P<p>.+?)</p>|<blockquote>(?P<bq>.+?)</blockquote>",
                body_html,
                re.DOTALL,
            ):
                if pm.group("p"):
                    parts.append(strip_tags(pm.group("p")))
                elif pm.group("bq"):
                    parts.append(strip_tags(pm.group("bq")))
            body_text = "\n\n".join(p for p in parts if p)
            if not body_text:
                continue
            chunks.append(
                {"section_title": heading, "chunk_index": chunk_idx, "content": f"{heading}\n\n{body_text}"}
            )
            chunk_idx += 1
        if chunk_idx > items_added_before:
            break  # found items with this pattern; don't try the fallback

    # Final fallback: if neither pattern produced items (e.g., a degraded
    # preview where the analysis failed), emit a single chunk from the
    # article's <p> content so the file is still queryable.
    if chunk_idx == items_added_before:
        body_html = re.sub(
            r"<hr>\s*<p><em>(?:Generated|AI-assisted|Source).*?</article>",
            "",
            article,
            flags=re.DOTALL,
        )
        parts = [strip_tags(p) for p in re.findall(r"<p>(.+?)</p>", body_html, re.DOTALL)]
        body_text = "\n\n".join(p for p in parts if p)
        if body_text:
            chunks.append(
                {"section_title": "Meeting Preview", "chunk_index": chunk_idx, "content": body_text}
            )

    return chunks


def chunk_public_record(html: str, date_iso: str) -> list[dict]:
    """Public-record filing: extract title, fact list, and summary into one chunk."""
    article = extract_article(html)

    title_m = re.search(r"<h1>(.+?)</h1>", article, re.DOTALL)
    title = strip_tags(title_m.group(1)) if title_m else ""

    sub_m = re.search(r'<p class="filing-subtitle">(.+?)</p>', article, re.DOTALL)
    subtitle = strip_tags(sub_m.group(1)) if sub_m else ""

    facts: list[str] = []
    for dt, dd in re.findall(r"<dt>(.+?)</dt>\s*<dd>(.+?)</dd>", article, re.DOTALL):
        facts.append(f"{strip_tags(dt)}: {strip_tags(dd)}")

    # Summary = first <p> after </dl>
    summary_m = re.search(r"</dl>\s*<p>(.+?)</p>", article, re.DOTALL)
    summary = strip_tags(summary_m.group(1)) if summary_m else ""

    body = title
    if subtitle:
        body += f" — {subtitle}"
    if facts:
        body += "\n\n" + "\n".join(facts)
    if summary:
        body += "\n\n" + summary

    return [{"section_title": title, "chunk_index": 0, "content": body}]


def chunk_around_town_dev(html: str, date_iso: str) -> list[dict]:
    """Around Town development case: title, subtitle, fact list, AI summary, and
    the 'From the case record' description — all into one chunk. Same filing
    markup as public-record, plus the case-record paragraph; excludes the
    disclosure/meta footer after the <hr>."""
    article = extract_article(html)

    title_m = re.search(r"<h1>(.+?)</h1>", article, re.DOTALL)
    title = strip_tags(title_m.group(1)) if title_m else ""

    sub_m = re.search(r'<p class="filing-subtitle">(.+?)</p>', article, re.DOTALL)
    subtitle = strip_tags(sub_m.group(1)) if sub_m else ""

    facts: list[str] = []
    for dt, dd in re.findall(r"<dt>(.+?)</dt>\s*<dd>(.+?)</dd>", article, re.DOTALL):
        facts.append(f"{strip_tags(dt)}: {strip_tags(dd)}")

    # Body = every <p> between </dl> and the <hr> (AI summary + case-record line)
    body_parts: list[str] = []
    mid = re.search(r"</dl>(.*?)<hr>", article, re.DOTALL)
    if mid:
        for p in re.findall(r"<p[^>]*>(.+?)</p>", mid.group(1), re.DOTALL):
            t = strip_tags(p)
            if t:
                body_parts.append(t)

    body = title
    if subtitle:
        body += f" — {subtitle}"
    if facts:
        body += "\n\n" + "\n".join(facts)
    if body_parts:
        body += "\n\n" + "\n\n".join(body_parts)

    return [{"section_title": title, "chunk_index": 0, "content": body}]


def chunk_agenda_full(md: str, date_iso: str) -> list[dict]:
    """Full agenda reference: skip the procedural preamble, then fixed-window chunks
    over the substantive content."""
    # Drop the trailing "Generated by..." / "Source:" footer
    md = re.split(r"\n---\s*\n\*Generated", md, maxsplit=1)[0]

    # Find first numbered item (C1, A1, P1, D1, etc.) and start from there.
    # Falls back to the start of file if no marker is found.
    body_start_m = re.search(r"^[\s ]*(?:C1|A1|P1|D1|E1|R1|I1)\b", md, re.MULTILINE)
    body = md[body_start_m.start():] if body_start_m else md

    # Normalize whitespace
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = body.strip()

    if not body:
        return []

    chunks: list[dict] = []
    step = AGENDA_WINDOW_CHARS - AGENDA_OVERLAP_CHARS
    for i, start in enumerate(range(0, len(body), step)):
        window = body[start:start + AGENDA_WINDOW_CHARS]
        if not window.strip():
            continue
        chunks.append({"section_title": f"Window {i + 1}", "chunk_index": i, "content": window})
        if start + AGENDA_WINDOW_CHARS >= len(body):
            break

    return chunks


# --- Corpus walking ---------------------------------------------------------

def file_date(name: str) -> str | None:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else None


def meeting_watch_url_for_agenda_full(filename: str) -> str:
    """Map agenda-watch/{slug}-full.md → meeting-watch/{published-slug}.html
    (or fall back to the meeting-watch index page)."""
    stem = filename.replace("-full.md", "")
    date = file_date(stem)
    if not date:
        return f"{BASE_URL}/meeting-watch.html"
    if stem.startswith("pima-county-"):
        slug = f"pima-county-bos-{date}"
    elif stem.startswith("marana-"):
        slug = f"marana-council-{date}"
    elif stem.startswith("orovalley-"):
        slug = f"orovalley-council-{date}"
    elif stem.startswith("tucson-"):
        slug = f"tucson-council-{date}"
    else:
        return f"{BASE_URL}/meeting-watch.html"
    candidate = SITE_DIR / "meeting-watch" / f"{slug}.html"
    if candidate.exists():
        return f"{BASE_URL}/meeting-watch/{slug}.html"
    return f"{BASE_URL}/meeting-watch.html"


def walk_corpus():
    """Yield (path, doc_type, source_url, date_iso, chunker) for every indexable file."""
    posts = SITE_DIR / "posts"
    for p in sorted(posts.glob("*.html")):
        date = file_date(p.name)
        yield p, "daily_brief", f"{BASE_URL}/posts/{p.name}", date, chunk_daily_brief

    nr = SITE_DIR / "news-reports"
    if nr.exists():
        for p in sorted(nr.glob("*.html")):
            date = file_date(p.name)
            yield p, "news_report", f"{BASE_URL}/news-reports/{p.name}", date, chunk_news_report

    mw = SITE_DIR / "meeting-watch"
    if mw.exists():
        for p in sorted(mw.glob("*.html")):
            date = file_date(p.name)
            yield p, "meeting_watch", f"{BASE_URL}/meeting-watch/{p.name}", date, chunk_meeting_watch

    pr = SITE_DIR / "public-record"
    if pr.exists():
        for p in sorted(pr.glob("liquor-*.html")):
            date = file_date(p.name)
            yield p, "public_record", f"{BASE_URL}/public-record/{p.name}", date, chunk_public_record

    at = SITE_DIR / "around-town"
    if at.exists():
        for p in sorted(at.glob("*.html")):
            date = file_date(p.name)
            yield p, "around_town_dev", f"{BASE_URL}/around-town/{p.name}", date, chunk_around_town_dev

    aw = SITE_DIR / "agenda-watch"
    if aw.exists():
        for p in sorted(aw.glob("*-full.md")):
            date = file_date(p.name)
            url = meeting_watch_url_for_agenda_full(p.name)
            yield p, "agenda_full", url, date, chunk_agenda_full


# --- Embedding context ------------------------------------------------------

DOC_TYPE_LABELS = {
    "daily_brief": "Daily brief",
    "news_report": "News report",
    "meeting_watch": "Meeting preview",
    "agenda_full": "Full agenda reference",
    "public_record": "Around Town filing (new business)",
    "around_town_dev": "Around Town development case",
}


def build_embed_input(doc_type: str, date_iso: str | None, section_title: str | None, content: str) -> str:
    """Prepend lightweight context so the embedding model sees the doc type, date, section."""
    label = DOC_TYPE_LABELS.get(doc_type, doc_type)
    parts = [label]
    if date_iso:
        parts.append(date_iso)
    if section_title:
        parts.append(section_title)
    header = " — ".join(parts) + ":\n"
    return header + content


# --- Main -------------------------------------------------------------------

def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_voyage_key() -> None:
    """Load VOYAGE_API_KEY from ~/.config/environment.d/voyage.conf if not already set."""
    if os.environ.get("VOYAGE_API_KEY"):
        return
    conf = Path.home() / ".config" / "environment.d" / "voyage.conf"
    if not conf.exists():
        print(f"ERROR: {conf} not found and VOYAGE_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    for line in conf.read_text().splitlines():
        line = line.strip()
        if line.startswith("VOYAGE_API_KEY="):
            os.environ["VOYAGE_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    print(f"ERROR: VOYAGE_API_KEY not found in {conf}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the TDB RAG search index")
    parser.add_argument("--rebuild", action="store_true", help="Drop existing index and re-embed everything")
    parser.add_argument("--dry-run", action="store_true", help="Walk + chunk; skip embeddings and DB writes")
    args = parser.parse_args()

    if not args.dry_run:
        load_voyage_key()

    RAG_DIR.mkdir(exist_ok=True)
    conn = open_db()

    if args.rebuild:
        print("Rebuild requested — dropping existing index.")
        drop_all(conn)

    # Pass 1: walk corpus, collect chunks for changed/new files
    pending_files: list[tuple[Path, str, str, str | None, list[dict]]] = []
    skipped = 0
    type_counts: dict[str, int] = {}

    for path, doc_type, source_url, date_iso, chunker in walk_corpus():
        text = path.read_text(encoding="utf-8")
        h = hash_str(text)

        if not args.rebuild:
            row = conn.execute("SELECT file_hash FROM file_state WHERE source_file = ?", (str(path.relative_to(SITE_DIR)),)).fetchone()
            if row and row[0] == h:
                skipped += 1
                continue

        chunks = chunker(text, date_iso or "")
        if not chunks:
            print(f"  WARN: 0 chunks from {path.relative_to(SITE_DIR)}")
            continue
        type_counts[doc_type] = type_counts.get(doc_type, 0) + len(chunks)
        pending_files.append((path, doc_type, source_url, date_iso, chunks))

    total_chunks = sum(len(c) for _, _, _, _, c in pending_files)
    print(f"Files to (re)index: {len(pending_files)} ({total_chunks} chunks)")
    print(f"Files unchanged (skipped): {skipped}")
    if type_counts:
        for t, n in sorted(type_counts.items()):
            print(f"  {t}: {n} chunks")

    if args.dry_run or total_chunks == 0:
        if args.dry_run:
            print("(dry-run: stopping before embedding)")
        return 0

    # Pass 2: batch-embed all pending chunks
    client = voyageai.Client()
    flat: list[tuple[Path, str, str, str | None, dict, str]] = []  # (path, doc_type, url, date, chunk, embed_input)
    for path, doc_type, source_url, date_iso, chunks in pending_files:
        for ch in chunks:
            embed_input = build_embed_input(doc_type, date_iso, ch["section_title"], ch["content"])
            flat.append((path, doc_type, source_url, date_iso, ch, embed_input))

    print(f"Embedding {len(flat)} chunks via {EMBEDDING_MODEL}…")
    embeddings: list[list[float]] = []
    t0 = time.time()
    for i in range(0, len(flat), BATCH_SIZE):
        batch_inputs = [item[5] for item in flat[i:i + BATCH_SIZE]]
        result = client.embed(batch_inputs, model=EMBEDDING_MODEL, input_type="document")
        embeddings.extend(result.embeddings)
        print(f"  batch {i // BATCH_SIZE + 1}/{(len(flat) + BATCH_SIZE - 1) // BATCH_SIZE}: {len(batch_inputs)} chunks, {result.total_tokens} tokens")
    print(f"Embedded {len(embeddings)} chunks in {time.time() - t0:.1f}s")

    # Pass 3: write to DB (per-file transaction, replacing any existing chunks for that file)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    files_done: set[Path] = set()
    embed_idx = 0
    files_in_pass = {item[0] for item in flat}

    with conn:
        for path in files_in_pass:
            rel = str(path.relative_to(SITE_DIR))
            # Remove old rows for this file (chunks + vec_chunks)
            old_ids = [r[0] for r in conn.execute("SELECT id FROM chunks WHERE source_file = ?", (rel,)).fetchall()]
            if old_ids:
                conn.executemany("DELETE FROM vec_chunks WHERE rowid = ?", [(i,) for i in old_ids])
                conn.execute("DELETE FROM chunks WHERE source_file = ?", (rel,))

        for path, doc_type, source_url, date_iso, ch, embed_input in flat:
            rel = str(path.relative_to(SITE_DIR))
            cur = conn.execute(
                """INSERT INTO chunks(source_file, source_url, doc_type, date, section_title, chunk_index, content, embed_input)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (rel, source_url, doc_type, date_iso, ch["section_title"], ch["chunk_index"], ch["content"], embed_input),
            )
            chunk_id = cur.lastrowid
            conn.execute(
                "INSERT INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
                (chunk_id, sqlite_vec.serialize_float32(embeddings[embed_idx])),
            )
            embed_idx += 1

        # Update file_state
        for path, _, _, _, _ in pending_files:
            rel = str(path.relative_to(SITE_DIR))
            text = path.read_text(encoding="utf-8")
            conn.execute(
                """INSERT INTO file_state(source_file, file_hash, indexed_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(source_file) DO UPDATE SET file_hash=excluded.file_hash, indexed_at=excluded.indexed_at""",
                (rel, hash_str(text), now),
            )
            files_done.add(rel)

    print(f"Wrote {len(flat)} chunks to {DB_PATH} (across {len(files_done)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
