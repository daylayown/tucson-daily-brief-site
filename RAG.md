# RAG Knowledge Agent (Ask / `tdb-ask`)

Architecture, index stats, cost, known gotchas, usage, the shipped Phase 2 web UI + Fly.io hosting decision, and Phase 3+ eval-driven backlog.

Reference doc split out of CLAUDE.md on 2026-07-17 to keep the always-loaded context lean. Prose is preserved verbatim from CLAUDE.md; CLAUDE.md now carries a short pointer to this file.

---

## RAG Knowledge Agent

A retrieval-augmented chat agent that answers questions about Tucson using only the TDB corpus, with inline citations to source URLs. Differentiates TDB from every other local outlet — most of which can't have a meaningful conversation about their own archive. The corpus IS the moat; making it queryable is what turns it into a product.

**Status:** Phase 1 (CLI) live since 2026-05-09 (`a1d0149`). **Phase 2 backend + Ask UI shipped 2026-06-14** (`8387bd7`) — the RAG agent is deployed to Fly.io at `https://tdb-ask.fly.dev` and `ask.html` is a working Q&A interface, currently gated behind `SHOW_TOOLS=False` for an unlisted shakedown. See "Phase 2 — public web UI" below for what shipped; the daily index-refresh cron is now wired too, so what's left before launch is the shakedown pass, then flip `SHOW_TOOLS`.

### Files

- `rag/build_index.py` — walks corpus, document-type-aware chunking, embeds via Voyage, writes to sqlite-vec.
- `rag/ask.py` — CLI: question → top-K retrieval → Claude Sonnet 4.6 synthesis with citation discipline → printed answer + numbered source list.
- `rag/index.sqlite` — vector store (gitignored).
- `requirements.txt` — adds `voyageai`, `sqlite-vec`, `anthropic`.

### Architecture

- **Embeddings:** Voyage `voyage-3-lite` (512-dim, $0.02/1M tokens, Anthropic-acquired Voyage AI is the recommended pairing for Claude RAG). API key in `~/.config/environment.d/voyage.conf`.
- **Vector store:** SQLite + `sqlite-vec` v0.1.9 extension. Single file at `rag/index.sqlite`. No server, no hosted service.
- **Generation:** Claude Sonnet 4.6 with strict "answer only from these sources" system prompt; refuses to fabricate, suggests where to look when corpus doesn't cover the question.
- **Chunking:** document-type-aware. Daily brief → one chunk per story. News report → title+lede + per-`<h2>` sections. Meeting preview → per top-item. Public-record filing → whole filing. Agenda full reference → 1500-char windows with 200-char overlap.
- **Idempotency:** content hash per file in `file_state` table — re-running re-embeds only changed/new files (verified — incremental rebuild after a new daily brief takes ~0.5s).
- **Citation URLs:** every chunk carries the public TDB URL it came from; `agenda-watch/*-full.md` references map to the corresponding `meeting-watch/{slug}.html` published preview when one exists, else fall back to the meeting-watch index page.

### Index stats (as of 2026-05-10)

147 files, 1,464 chunks. Distribution: 1,105 daily-brief chunks, 207 agenda-full, 121 meeting-watch, 18 public-record, 13 news-report. Initial embed: ~262K tokens, well under Voyage's 200M-token free tier.

### Cost

- Embedding: ~$0.005 to embed entire corpus once. Daily incremental: pennies/day.
- **Per query at runtime:** ~$0.015 (Sonnet 4.6 with retrieved chunks). Hand-tests range $0.011–$0.020 depending on output length.
- 100 queries/day ≈ $1.50/day, $45/month. Realistic shakedown volume is pennies/month.

### Known gotchas (caught during build, must remember)

1. **sqlite-vec KNN syntax:** use `WHERE embedding MATCH ? AND k = ?` inside the WHERE clause, NOT a regular SQL `LIMIT`. Plain `LIMIT` raises `OperationalError: A LIMIT or 'k = ?' constraint is required on vec0 knn queries`.
2. **Voyage `input_type`:** use `"document"` when embedding for the index, `"query"` when embedding the user's question. They're tuned differently.
3. **Vector serialization:** sqlite-vec accepts `sqlite_vec.serialize_float32(vec)` for storage. Do not pass Python lists directly.
4. **Boolean params on SDKs:** Voyage 0.2.x is fine, but the Deepgram pattern of "pass booleans as strings" is a precedent worth remembering when integrating other vector/SDK libraries.

### Usage

```bash
.venv/bin/python3 rag/build_index.py              # incremental — only re-embeds changed files
.venv/bin/python3 rag/build_index.py --rebuild    # drop everything and re-embed all
.venv/bin/python3 rag/build_index.py --dry-run    # walk + chunk only, no API calls

.venv/bin/python3 rag/ask.py "your question here"
.venv/bin/python3 rag/ask.py --k 15 "..."         # retrieve more chunks
.venv/bin/python3 rag/ask.py --json "..."         # machine-readable output
```

### Phase 2 — public web UI (next, ~2-3 days of focused work)

The chat agent ships publicly as the **launch event** of the project's marketing push. Status of the plan (✅ = shipped 2026-06-14, `8387bd7`):

1. ✅ **`ask.html` rebuilt** — was a coming-soon stub; now a working Q&A interface (vanilla JS, scoped `<style>` on the locked desert palette): question box + example-question chips + answer card + citation list. The answer's `[N]` markers render as links that jump to the numbered source list; each source links out to its TDB page. Carries a beta disclaimer. POSTs to the Fly service (no Cloudflare Worker — that plan was dropped, see hosting decision below). **Still gated behind `SHOW_TOOLS=False`** — do NOT flip until shakedown is clean.
2. ✅ **Fly.io service** (`rag/server.py`) — FastAPI wrapper around the existing `ask()` function. Holds Voyage + Anthropic keys as Fly secrets (`fly secrets set`, reused from `environment.d`). `POST /ask` → `{question, k?}` → `{answer, sources}`; `GET /health` for the Fly health check. App name **`tdb-ask`**, deployed via `fly deploy --remote-only`; the prebuilt `index.sqlite` is **baked into the image** (`Dockerfile` copies it in — service is read-only at runtime, no volume). `fly.toml`: `shared-cpu-1x`/512mb, scale-to-zero (`min_machines_running = 0`), HTTPS forced. Image ~107MB.
3. ✅ **Per-IP rate limiting** in the FastAPI app — in-process sliding window, 20 req/hour (env-tunable via `RATE_LIMIT_*`). CORS locked to `tucsondailybrief.com` (+ localhost for dev); other origins blocked. Input validation: question 1–500 chars, `k` clamped 1–20.
4. ⏳ **Unlisted shakedown (~1 week)** — in progress. `ask.html` is pushed but unlinked (`SHOW_TOOLS=False`, not in any nav/sitemap), so it's effectively unlisted. After clean shakedown: flip `SHOW_TOOLS=True` in `generate_post.py` (surfaces Ask + Responsiveness in the homepage Tools row and Tools nav site-wide), then public launch (r/Tucson + LinkedIn + local press).
5. ✅ **Cron the index refresh — DONE 2026-06-14.** `refresh_ask_index.sh` rebuilds the index (`build_index.py`) then `fly deploy --remote-only --app tdb-ask` to reship it, since the baked `index.sqlite` otherwise freezes live answers at deploy-time. Runs daily at **8:45 AM MST** (cron, after `check_agendas.sh` at 8:00 so both the morning brief and freshly mined agendas/filings are indexed) → `/tmp/ask-index-refresh.log`. Non-interactive deploy auth uses a **scoped Fly deploy token** in `~/.config/environment.d/fly.conf` (`FLY_API_TOKEN`, created via `fly tokens create deploy -a tdb-ask`, 1-yr expiry — regenerate before it lapses). The script sources `environment.d/*.conf` (Voyage key + Fly token) like the other cron wrappers. Skips the deploy if the rebuild fails. Future optimization: a Fly volume + pushing just the `.sqlite` instead of a full image rebuild each day; current daily redeploy is cheap (~107MB image) and fine at this scale.

**Local dev / redeploy quickref:**
```bash
# Test the server locally against the real index (from rag/):
../.venv/bin/uvicorn server:app --reload --port 8080
# Refresh the deployed index after new content lands:
.venv/bin/python3 rag/build_index.py && fly deploy --remote-only --app tdb-ask
# Logs / status:
fly logs --app tdb-ask ; fly status --app tdb-ask
```
Note: `fastapi` + `uvicorn[standard]` are in both the repo-root `requirements.txt` (laptop `.venv`) and `rag/requirements-server.txt` (the lean Fly image).

**Shakedown + date-awareness fix (2026-06-14):** A 13-question adversarial pass found grounding strong — clean refusals on out-of-corpus questions (Phoenix mayor, Wildcats football) and false premises (a fictional streetcar derailment, a made-up Romero car-ban plan), a corrected loaded premise on the Nanos "corruption charges" question, and a gracefully-declined prompt injection. The one real failure: no sense of "now" — it served a months-old weather brief as "tomorrow's forecast." **Fixed** by injecting the current Tucson date (`America/Phoenix`, no DST) plus a real-time/staleness instruction into the system prompt at request time (`current_date_note()` in `ask.py`, appended to `SYSTEM_PROMPT`). Verified: the weather question now flags its newest source as stale and points to NWS, "this week" questions lead with the most recent source and admit gaps, and well-covered topics still answer confidently. **Two structural follow-ups deliberately deferred** (discuss before building): (a) exclude ephemeral weather sections from the index — they only generate stale-data traps; (b) recency weighting in retrieval (Phase 3) — retrieval still surfaces mostly older chunks for "latest/this week" questions, so the prompt fix makes the model degrade honestly but doesn't fix ranking. **Also flagged for pre-launch:** the in-process per-IP rate limit resets on every deploy and is per-machine (2 machines) — soft against real abuse; revisit before flipping `SHOW_TOOLS`.

**Phase 2 hosting decision (2026-05-25): Fly.io with local SQLite (option C from the original evaluation).** One small Python service wraps `ask.py`; the `index.sqlite` file ships with the deploy. Reasons: zero rewrite of existing `build_index.py` / `ask.py` code; one system to maintain (vs. Worker + VPS); avoids re-implementing the chunk store in Cloudflare Vectorize for a problem (scale, edge latency) TDB doesn't have at expected traffic. Rate limiting lives in the FastAPI app (per-IP bucket, ~20 lines) instead of at the Worker edge. Replaces the earlier Cloudflare Worker plan throughout this section — `ask.html` will POST to the Fly.io app directly, no Worker hop. This is also **Stage 1 of the broader "Move TDB off the laptop" roadmap** (see section below) — chosen as the low-stakes first migration to prove out the cloud-deploy workflow before tackling the heavier cron + live-recording migration.

### Phase 3+ (eval-driven, defer until Phase 2 has run for a few weeks)

- **Eval set** — 30–50 hand-graded real Tucson questions, automated regression-tested on every change. Build before any of the items below; without it, "improvements" are guesses.
- **Hybrid search** — BM25 + vector, then rerank top-30 → top-10 via Voyage Rerank or Cohere Rerank. Highest-leverage quality lever in most RAG systems.
- **Recency weighting** — explicit time-decay scoring if Sonnet isn't picking up "what's happening lately" framing from prompt instructions alone.
- **Agentic multi-hop retrieval** — for cross-document questions ("Who funded the council member who voted yes on Bloom Tea's liquor license?"). Let the model issue multiple retrieval queries iteratively.
- **Operational RAG extension** — once the Responsiveness Index ships, extend the agent to query its live SQLite store alongside the text corpus (covered in detail in `responsiveness/PLANNING.md` under "Function 3 — Access").
