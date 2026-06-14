#!/usr/bin/env python3
"""
Ask Tucson Daily Brief — HTTP service wrapping the RAG agent (rag/ask.py).

A thin FastAPI app for Phase 2 of the RAG agent: it exposes the existing
`ask()` function over HTTP so the public `ask.html` page can POST questions
and render answers + citations. Designed to run as a single small Fly.io
machine with the `index.sqlite` file baked into the image.

Endpoints:
    GET  /health   — liveness probe (used by Fly health checks); not rate-limited
    POST /ask       — {"question": str, "k": int?} -> {"answer", "sources", ...}

Rate limiting: in-process per-IP sliding window (default 20 requests/hour).
Good enough for a single-machine deploy; revisit if we scale horizontally.

Run locally:
    .venv/bin/uvicorn server:app --reload --port 8080   # from the rag/ dir
"""

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ask.py lives alongside this file; DB_PATH inside it is resolved relative to
# __file__, so imports work no matter what the process CWD is.
from ask import DEFAULT_K, ask

# --- Configuration (overridable via env on Fly) --------------------------------

MAX_QUESTION_CHARS = int(os.environ.get("MAX_QUESTION_CHARS", "500"))
MAX_K = int(os.environ.get("MAX_K", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "3600"))
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "20"))

# Origins allowed to call the API from a browser. The production site plus
# localhost for development. Update if the domain ever changes.
ALLOWED_ORIGINS = [
    "https://tucsondailybrief.com",
    "https://www.tucsondailybrief.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# --- App -----------------------------------------------------------------------

app = FastAPI(title="Ask Tucson Daily Brief", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_CHARS)
    k: int = Field(default=DEFAULT_K, ge=1, le=MAX_K)


# --- Rate limiting (in-process, per-IP sliding window) -------------------------

_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()


def _client_ip(request: Request) -> str:
    # Behind Fly's proxy the real client IP arrives in Fly-Client-IP; fall back
    # to the first X-Forwarded-For hop, then the socket peer for local runs.
    fly_ip = request.headers.get("Fly-Client-IP")
    if fly_ip:
        return fly_ip
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    with _hits_lock:
        q = _hits[ip]
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= RATE_LIMIT_MAX_REQUESTS:
            retry_after = int(q[0] + RATE_LIMIT_WINDOW_SECONDS - now) + 1
            raise HTTPException(
                status_code=429,
                detail="Rate limit reached. Please try again later.",
                headers={"Retry-After": str(max(retry_after, 1))},
            )
        q.append(now)


# --- Routes --------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask_endpoint(body: AskRequest, request: Request) -> dict:
    _check_rate_limit(_client_ip(request))

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    try:
        # ask() makes blocking Voyage + Anthropic calls. Declaring this route as
        # a sync `def` lets FastAPI run it in a worker thread, so concurrent
        # requests don't block the event loop.
        result = ask(question, k=body.k)
    except Exception:
        # Don't leak internals (API errors, keys) to the client.
        raise HTTPException(status_code=502, detail="Upstream error answering the question.")

    # Trim token/debug fields the public UI doesn't need.
    return {
        "question": result["question"],
        "answer": result["answer"],
        "sources": result["sources"],
    }
