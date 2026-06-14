#!/usr/bin/env bash
#
# Rebuild the RAG vector index and redeploy the Ask service (Fly app tdb-ask)
# so the live agent at https://tdb-ask.fly.dev stays current with newly
# published TDB content. The index.sqlite is baked into the Fly image, so a
# redeploy is what actually refreshes the deployed answers — rebuilding the
# index locally alone does nothing to the live site.
#
# Runs daily via cron after check_agendas.sh (8 AM) so both the morning daily
# brief and the freshly mined agendas/filings are in the index. Manual:
#   ./refresh_ask_index.sh
#
# Cron (8:30 AM MST, after the agenda check):
#   30 8 * * * ~/claude-code-projects/tucson-daily-brief-site/refresh_ask_index.sh >> /tmp/ask-index-refresh.log 2>&1

set -uo pipefail

# --- Load env (VOYAGE_API_KEY for embedding, FLY_API_TOKEN for the deploy) ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

export PATH="$HOME/.fly/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python3"
cd "$SCRIPT_DIR"

echo "===================="
echo "$(date): Ask index refresh starting."

# --- 1. Rebuild the vector index (incremental — only re-embeds new/changed files) ---
if ! "$PYTHON" rag/build_index.py; then
    echo "$(date): ERROR — index rebuild failed; skipping deploy." >&2
    exit 1
fi

# --- 2. Redeploy so the updated index.sqlite ships inside the Fly image ---
if [ -z "${FLY_API_TOKEN:-}" ]; then
    echo "$(date): ERROR — FLY_API_TOKEN not set (expected in ~/.config/environment.d/fly.conf); skipping deploy." >&2
    exit 1
fi

if ! fly deploy --remote-only --app tdb-ask; then
    echo "$(date): ERROR — fly deploy failed. The index was rebuilt locally but the live service is unchanged." >&2
    exit 1
fi

echo "$(date): Done — Ask service redeployed with the refreshed index."
