#!/usr/bin/env python3
"""
Ask Tucson Daily Brief — RAG query CLI.

Embeds the user's question via Voyage, retrieves top-K relevant chunks
from rag/index.sqlite via sqlite-vec, sends them to Claude Sonnet 4.6
with strict "answer only from these sources" instructions, and prints
the answer with inline citations and a numbered source list.

Usage:
    python rag/ask.py "What's happening with the Vanderbilt Farms development?"
    python rag/ask.py --k 15 "How is Tucson preparing for monsoon season?"
    python rag/ask.py --json "..."     # machine-readable output
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

import anthropic
import sqlite_vec
import voyageai

RAG_DIR = Path(__file__).resolve().parent
DB_PATH = RAG_DIR / "index.sqlite"
EMBEDDING_MODEL = "voyage-3-lite"
ANSWER_MODEL = "claude-sonnet-4-6"
DEFAULT_K = 10
MAX_TOKENS = 1024

DOC_TYPE_LABELS = {
    "daily_brief": "Daily brief",
    "news_report": "News report",
    "meeting_watch": "Meeting preview",
    "agenda_full": "Full agenda reference",
    "public_record": "Public record filing",
}

SYSTEM_PROMPT = """You are an assistant for Tucson Daily Brief, a local news site covering the Tucson, Arizona metro area — the City of Tucson, Pima County, Marana, Oro Valley, Green Valley, and surrounding communities.

Answer the user's question using ONLY the sources provided below. Do not draw on outside knowledge, and do not fabricate facts, dates, names, or figures. If the sources don't contain enough information to answer the question, say so clearly and briefly.

Cite sources inline using bracketed numbers, like [1] or [2][4]. Every factual claim should be tied to at least one source.

Tone: warm, plain-language, the voice of a local news editor — not a chatbot, not a press release. Be concise but substantive. When sources are recent, lead with the most current information.

If the user's question implies a "what's happening now" framing, weight more recent sources higher than older ones. If the user is asking about a historical thread (a development project, a council decision over time), pull the relevant sources together into a brief narrative.

Never refer to "the sources" or "the documents" generically — write as if speaking to a Tucson reader. Cite with [N] markers, not phrases like "according to source 1"."""


def load_env_file(path: Path, varname: str) -> None:
    """Load VARNAME=value from a key=value conf file into os.environ if not already set."""
    if os.environ.get(varname):
        return
    if not path.exists():
        print(f"ERROR: {path} not found and {varname} not set", file=sys.stderr)
        sys.exit(1)
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{varname}="):
            os.environ[varname] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    print(f"ERROR: {varname} not found in {path}", file=sys.stderr)
    sys.exit(1)


def open_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        print(f"ERROR: index not built yet. Run: python rag/build_index.py", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    return conn


def retrieve(conn: sqlite3.Connection, query_vec: list[float], k: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT chunks.id, chunks.doc_type, chunks.source_url, chunks.date,
               chunks.section_title, chunks.content, vec_chunks.distance
        FROM vec_chunks
        JOIN chunks ON chunks.id = vec_chunks.rowid
        WHERE embedding MATCH ? AND k = ?
        ORDER BY distance
        """,
        (sqlite_vec.serialize_float32(query_vec), k),
    ).fetchall()
    return [
        {
            "id": r[0],
            "doc_type": r[1],
            "source_url": r[2],
            "date": r[3],
            "section_title": r[4],
            "content": r[5],
            "distance": r[6],
        }
        for r in rows
    ]


def build_user_prompt(question: str, hits: list[dict]) -> str:
    lines = ["Sources:\n"]
    for i, h in enumerate(hits, 1):
        label = DOC_TYPE_LABELS.get(h["doc_type"], h["doc_type"])
        header = f"[{i}] {label}"
        if h["date"]:
            header += f" — {h['date']}"
        if h["section_title"]:
            header += f" ({h['section_title']})"
        header += f"\nURL: {h['source_url']}\n"
        lines.append(header + h["content"].strip() + "\n")
    lines.append(f"\nQuestion: {question}")
    return "\n".join(lines)


def ask(question: str, k: int = DEFAULT_K) -> dict:
    load_env_file(Path.home() / ".config/environment.d/voyage.conf", "VOYAGE_API_KEY")
    load_env_file(Path.home() / ".config/environment.d/anthropic.conf", "ANTHROPIC_API_KEY")

    voyage = voyageai.Client()
    qv = voyage.embed([question], model=EMBEDDING_MODEL, input_type="query").embeddings[0]

    conn = open_db()
    hits = retrieve(conn, qv, k)
    conn.close()

    if not hits:
        return {"question": question, "answer": "I don't have any indexed content yet to answer from.", "sources": []}

    user_prompt = build_user_prompt(question, hits)

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=ANSWER_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    answer = "".join(block.text for block in msg.content if block.type == "text").strip()

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "n": i,
                "doc_type": h["doc_type"],
                "date": h["date"],
                "section_title": h["section_title"],
                "url": h["source_url"],
                "distance": h["distance"],
            }
            for i, h in enumerate(hits, 1)
        ],
        "model": ANSWER_MODEL,
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
    }


def render_human(result: dict) -> str:
    out = [f"Q: {result['question']}", "", result["answer"], "", "Sources:"]
    for s in result["sources"]:
        label = DOC_TYPE_LABELS.get(s["doc_type"], s["doc_type"])
        line = f"  [{s['n']}] {label}"
        if s["date"]:
            line += f", {s['date']}"
        if s["section_title"]:
            line += f" — {s['section_title']}"
        line += f"\n      {s['url']}"
        out.append(line)
    out.append("")
    out.append(f"({result['input_tokens']} input + {result['output_tokens']} output tokens, {result['model']})")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the Tucson Daily Brief RAG agent")
    parser.add_argument("question", nargs="*", help="The question to ask (or read from stdin)")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help=f"Number of chunks to retrieve (default {DEFAULT_K})")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable")
    args = parser.parse_args()

    if args.question:
        question = " ".join(args.question).strip()
    elif not sys.stdin.isatty():
        question = sys.stdin.read().strip()
    else:
        print("Question: ", end="", flush=True)
        question = sys.stdin.readline().strip()

    if not question:
        print("ERROR: empty question", file=sys.stderr)
        return 1

    result = ask(question, k=args.k)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
