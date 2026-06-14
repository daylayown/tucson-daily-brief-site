# Ask Tucson Daily Brief — RAG query service (Fly.io).
# Ships the prebuilt rag/index.sqlite inside the image; the service is
# read-only at runtime, so no volume is needed. Rebuild + redeploy to
# refresh the index (a cron-driven incremental rebuild is a later step).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# Install Python deps first for layer caching.
COPY rag/requirements-server.txt ./requirements-server.txt
RUN pip install --no-cache-dir -r requirements-server.txt

# App code + the baked vector index. Only the files the service needs.
COPY rag/ask.py rag/server.py ./
COPY rag/index.sqlite ./index.sqlite

EXPOSE 8080

# Single worker: one small machine, in-process rate-limit state must be shared.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
