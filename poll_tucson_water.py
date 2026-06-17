#!/usr/bin/env python3
"""Poll the City of Tucson Water drinking-water advisory feed and archive it.

Tucson Water publishes no advisory *history* — only the current live layer.
By polling its public ArcGIS FeatureServer on a cadence and snapshotting into
SQLite, TDB becomes the systematic record of Tucson Water service disruptions
(outages, main breaks, discolored-water / pressure events, planned maintenance).

This is the first feature of the "Responsiveness Index" Heat/Water/Power archive.
See responsiveness/UTILITY-DATA-SOURCES.md for the verified endpoint + field notes.

Design (a snapshot-and-store lifecycle model):
  * water_advisory             — one row per distinct advisory, updated in place
                                 across polls (first_seen -> last_seen_open -> lifted)
  * water_advisory_observation — append-only, one row only when a tracked field
                                 changes (NOT every poll), so a long advisory is a
                                 handful of rows, not one-per-poll
  * water_poll_run             — one row per poll (success or failure), so a fetch
                                 failure is recorded as known downtime rather than
                                 silently false-resolving every advisory

Idempotent: keyed on the ArcGIS OBJECTID (stable PK), safe to re-run.

Usage:
  python3 poll_tucson_water.py                 # one poll of current OPEN advisories
  python3 poll_tucson_water.py --backfill      # one-time: load the full existing archive
  python3 poll_tucson_water.py --no-notify     # skip Telegram
  python3 poll_tucson_water.py --db PATH        # override the SQLite location
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests

SITE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = SITE_DIR / "data" / "outages.sqlite"
SEND_TELEGRAM = Path.home() / ".openclaw" / "skills" / "tucson-daily-brief" / "scripts" / "send_telegram.py"

# Verified live 2026-06-17. The advisory/outage layer behind the Tucson Water
# Drinking Water Advisory ArcGIS Experience app. Public, no token required.
ADVISORY_LAYER = (
    "https://utility.arcgis.com/usrsvcs/servers/"
    "83923d49e2954c1588a032784fe3d4bf/rest/services/Water/DrinkingWaterAdvisory/MapServer/0"
)
QUERY_URL = ADVISORY_LAYER + "/query"
PAGE_SIZE = 2000  # layer maxRecordCount

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS water_advisory (
    objectid          INTEGER PRIMARY KEY,
    advise_id         TEXT,
    advise_type       TEXT,
    advise_type_es    TEXT,
    status            TEXT,
    advise_start_ms   INTEGER,
    advise_end_ms     INTEGER,
    advise_start_iso  TEXT,
    advise_end_iso    TEXT,
    est_start_time    TEXT,
    est_end_time      TEXT,
    est_services      INTEGER,
    description       TEXT,
    description_es    TEXT,
    contact           TEXT,
    document_number   TEXT,
    geom_json         TEXT,
    centroid_lat      REAL,
    centroid_lon      REAL,
    first_seen        TEXT NOT NULL,
    last_seen_open    TEXT,
    lifted_at         TEXT,
    last_polled       TEXT NOT NULL,
    content_hash      TEXT,
    backfilled        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS water_advisory_observation (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    objectid     INTEGER NOT NULL,
    observed_at  TEXT NOT NULL,
    status       TEXT,
    advise_type  TEXT,
    content_hash TEXT,
    note         TEXT
);
CREATE INDEX IF NOT EXISTS idx_obs_oid_time
    ON water_advisory_observation(objectid, observed_at);

CREATE TABLE IF NOT EXISTS water_poll_run (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    polled_at    TEXT NOT NULL,
    ok           INTEGER NOT NULL,
    open_count   INTEGER,
    http_status  INTEGER,
    new_count    INTEGER,
    lifted_count INTEGER,
    error        TEXT
);
"""

# Fields tracked for change-detection (drives the observation table).
HASH_FIELDS = ("status", "advise_type", "description", "advise_end_ms", "est_services")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ms_to_iso(ms):
    if ms in (None, "", 0):
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, OSError, OverflowError):
        return None


def content_hash(row: dict) -> str:
    payload = "|".join(str(row.get(f, "")) for f in HASH_FIELDS)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def centroid(geometry):
    """Rough centroid (mean of all ring vertices) from an Esri polygon."""
    if not geometry or "rings" not in geometry:
        return None, None
    xs, ys = [], []
    for ring in geometry["rings"]:
        for pt in ring:
            xs.append(pt[0])
            ys.append(pt[1])
    if not xs:
        return None, None
    return round(sum(ys) / len(ys), 6), round(sum(xs) / len(xs), 6)


def parse_feature(feat: dict) -> dict:
    """Map a raw ArcGIS feature (attributes + geometry) to our row dict."""
    a = feat.get("attributes", {})
    geom = feat.get("geometry")
    lat, lon = centroid(geom)
    start_ms = a.get("ADVISESTART")
    end_ms = a.get("ADVISEEND")
    return {
        "objectid": a.get("OBJECTID"),
        "advise_id": a.get("ADVISEID"),
        "advise_type": a.get("ADVISETYPE"),
        "advise_type_es": a.get("ADVISETYPE_ES"),
        "status": (a.get("STATUS") or "").strip() or None,
        "advise_start_ms": start_ms,
        "advise_end_ms": end_ms,
        "advise_start_iso": ms_to_iso(start_ms),
        "advise_end_iso": ms_to_iso(end_ms),
        "est_start_time": a.get("ESTIMATED_START_TIME"),
        "est_end_time": a.get("ESTIMATED_END_TIME"),
        "est_services": a.get("Estimated_Number_Services"),
        "description": a.get("DESCRIPTION"),
        "description_es": a.get("DESCRIPTION_ES"),
        "contact": a.get("CONTACT"),
        "document_number": a.get("DocumentNumber"),
        "geom_json": json.dumps(geom) if geom else None,
        "centroid_lat": lat,
        "centroid_lon": lon,
    }


def fetch(where: str, geometry: bool, offset: int = 0):
    """Query the layer. Returns (features, http_status). Raises on failure."""
    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true" if geometry else "false",
        "outSR": "4326",
        "f": "json",
        "resultOffset": offset,
        "resultRecordCount": PAGE_SIZE,
    }
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                QUERY_URL, params=params, timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "TucsonDailyBrief/1.0 (+https://tucsondailybrief.com)"},
            )
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"ArcGIS error: {data['error']}")
            return data.get("features", []), resp.status_code, data.get("exceededTransferLimit", False)
        except Exception as e:  # noqa: BLE001 - retry on any transient failure
            last_exc = e
    raise last_exc


def fetch_all(where: str, geometry: bool):
    """Paged fetch for arbitrarily many rows (backfill)."""
    out, offset = [], 0
    while True:
        feats, _, exceeded = fetch(where, geometry, offset)
        out.extend(feats)
        if not exceeded or not feats:
            break
        offset += len(feats)
    return out


def send_telegram(message: str) -> None:
    if not SEND_TELEGRAM.exists():
        print(f"  (telegram helper not found, skipping notification)", file=sys.stderr)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(message)
        tmp_path = f.name
    try:
        subprocess.run(["python3", str(SEND_TELEGRAM), tmp_path],
                       capture_output=True, text=True, timeout=30)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

import sqlite3  # noqa: E402 - kept near use


def get_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


COLS = [
    "objectid", "advise_id", "advise_type", "advise_type_es", "status",
    "advise_start_ms", "advise_end_ms", "advise_start_iso", "advise_end_iso",
    "est_start_time", "est_end_time", "est_services", "description",
    "description_es", "contact", "document_number", "geom_json",
    "centroid_lat", "centroid_lon",
]


def upsert(conn, row, polled_at, *, backfilled=False):
    """Insert/update one advisory. Returns ('new'|'reopened'|'changed'|'same')."""
    h = content_hash(row)
    existing = conn.execute(
        "SELECT lifted_at, content_hash FROM water_advisory WHERE objectid=?",
        (row["objectid"],),
    ).fetchone()

    is_open = (row["status"] or "").upper() == "OPEN"
    lifted_at = None if is_open else (row["advise_end_iso"] or polled_at)

    if existing is None:
        cols = COLS + ["first_seen", "last_seen_open", "lifted_at", "last_polled",
                       "content_hash", "backfilled"]
        vals = [row[c] for c in COLS] + [
            polled_at,
            polled_at if is_open else None,
            lifted_at,
            polled_at,
            h,
            1 if backfilled else 0,
        ]
        conn.execute(
            f"INSERT INTO water_advisory ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            vals,
        )
        _observe(conn, row, polled_at, h, "first seen")
        return "new" if is_open else "archived"

    # Existing row: update mutable fields.
    reopened = existing["lifted_at"] is not None and is_open
    conn.execute(
        f"""UPDATE water_advisory SET {','.join(c + '=?' for c in COLS)},
            last_seen_open=?, lifted_at=?, last_polled=?, content_hash=?
            WHERE objectid=?""",
        [row[c] for c in COLS] + [
            polled_at if is_open else None,
            None if is_open else (existing["lifted_at"] or lifted_at),
            polled_at,
            h,
            row["objectid"],
        ],
    )
    if reopened:
        _observe(conn, row, polled_at, h, "reopened")
        return "reopened"
    if existing["content_hash"] != h:
        _observe(conn, row, polled_at, h, "changed")
        return "changed"
    return "same"


def _observe(conn, row, polled_at, h, note):
    conn.execute(
        """INSERT INTO water_advisory_observation
           (objectid, observed_at, status, advise_type, content_hash, note)
           VALUES (?,?,?,?,?,?)""",
        (row["objectid"], polled_at, row["status"], row["advise_type"], h, note),
    )


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def run_backfill(conn):
    polled_at = iso_now()
    print("Backfilling full advisory archive from ArcGIS...")
    feats = fetch_all("1=1", geometry=True)
    n = 0
    for feat in feats:
        row = parse_feature(feat)
        if row["objectid"] is None:
            continue
        upsert(conn, row, polled_at, backfilled=True)
        n += 1
    conn.commit()
    open_n = conn.execute(
        "SELECT COUNT(*) FROM water_advisory WHERE lifted_at IS NULL"
    ).fetchone()[0]
    print(f"Backfilled {n} advisories ({open_n} currently open).")


def run_poll(conn, notify=True, verbose=False):
    polled_at = iso_now()
    try:
        feats, http_status, _ = fetch("STATUS='OPEN'", geometry=True)
    except Exception as e:  # noqa: BLE001
        conn.execute(
            "INSERT INTO water_poll_run (polled_at, ok, error) VALUES (?,0,?)",
            (polled_at, str(e)),
        )
        conn.commit()
        print(f"Poll FAILED ({e}); recorded as downtime, no advisories touched.", file=sys.stderr)
        return 1

    current = {}
    for feat in feats:
        row = parse_feature(feat)
        if row["objectid"] is not None:
            current[row["objectid"]] = row

    # Which advisories did we think were open before this poll?
    prev_open = {r[0] for r in conn.execute(
        "SELECT objectid FROM water_advisory WHERE lifted_at IS NULL"
    ).fetchall()}

    new_items, changed_items = [], []
    for oid, row in current.items():
        result = upsert(conn, row, polled_at)
        if result == "new":
            new_items.append(row)
        elif result in ("changed", "reopened"):
            changed_items.append((result, row))

    # Resolution: anything previously open and now absent from the OPEN set is lifted.
    dropped = [oid for oid in prev_open if oid not in current]
    lifted_items = []
    if dropped:
        lifted_items = _finalize_dropped(conn, dropped, polled_at)

    conn.execute(
        """INSERT INTO water_poll_run
           (polled_at, ok, open_count, http_status, new_count, lifted_count)
           VALUES (?,1,?,?,?,?)""",
        (polled_at, len(current), http_status, len(new_items), len(lifted_items)),
    )
    conn.commit()

    print(f"Poll OK: {len(current)} open, {len(new_items)} new, "
          f"{len(changed_items)} changed, {len(lifted_items)} lifted.")
    if verbose:
        for row in new_items:
            print(f"  + NEW [{row['advise_type']}] {(row['description'] or '')[:80]}")
        for row in lifted_items:
            print(f"  - LIFTED [{row['advise_type']}] {(row['description'] or '')[:80]}")

    if notify and (new_items or lifted_items):
        send_telegram(_notify_text(new_items, lifted_items))
    return 0


def _finalize_dropped(conn, dropped, polled_at):
    """An OPEN advisory disappeared from the feed -> mark lifted; capture final status."""
    finals = {}
    # Best-effort: re-query the dropped OBJECTIDs to capture their final STATUS/end time.
    try:
        id_list = ",".join(str(int(o)) for o in dropped)
        feats, _, _ = fetch(f"OBJECTID IN ({id_list})", geometry=False)
        for feat in feats:
            row = parse_feature(feat)
            finals[row["objectid"]] = row
    except Exception:  # noqa: BLE001 - finalization is best-effort; lift anyway
        pass

    lifted = []
    for oid in dropped:
        row = finals.get(oid)
        lifted_iso = (row["advise_end_iso"] if row else None) or polled_at
        if row:
            conn.execute(
                """UPDATE water_advisory SET status=?, advise_end_ms=?, advise_end_iso=?,
                   lifted_at=?, last_polled=? WHERE objectid=?""",
                (row["status"], row["advise_end_ms"], row["advise_end_iso"],
                 lifted_iso, polled_at, oid),
            )
            _observe(conn, row, polled_at, content_hash(row), "lifted")
            lifted.append(row)
        else:
            conn.execute(
                "UPDATE water_advisory SET lifted_at=?, last_polled=? WHERE objectid=?",
                (lifted_iso, polled_at, oid),
            )
            cur = conn.execute(
                "SELECT advise_type, description FROM water_advisory WHERE objectid=?", (oid,)
            ).fetchone()
            lifted.append({"advise_type": cur["advise_type"], "description": cur["description"]})
    return lifted


def _notify_text(new_items, lifted_items):
    lines = ["💧 *Tucson Water*"]
    for row in new_items:
        desc = (row.get("description") or "").strip()
        loc = ""
        if row.get("centroid_lat"):
            loc = f" (~{row['centroid_lat']:.3f}, {row['centroid_lon']:.3f})"
        lines.append(f"\n🔴 NEW — {row.get('advise_type') or 'Advisory'}{loc}\n{desc[:240]}")
    for row in lifted_items:
        lines.append(f"\n✅ LIFTED — {row.get('advise_type') or 'Advisory'}\n{(row.get('description') or '')[:160]}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Poll + archive Tucson Water advisories.")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite path")
    ap.add_argument("--backfill", action="store_true", help="one-time: load the full archive")
    ap.add_argument("--no-notify", action="store_true", help="skip Telegram")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    conn = get_db(args.db)
    try:
        if args.backfill:
            run_backfill(conn)
            return 0
        return run_poll(conn, notify=not args.no_notify, verbose=args.verbose)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
