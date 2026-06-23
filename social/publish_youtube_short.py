#!/usr/bin/env python3
"""
Publish a TDB short-form vertical video to YouTube (as a Short).

Reuses the existing YouTube OAuth token/secrets from the podcast pipeline
(~/.config/youtube-token.json). A vertical (<=3min) video auto-classifies as a
Short; #Shorts in the description reinforces it. The Cloud project is audited,
so uploads publish public.

Usage:
    python3 publish_youtube_short.py <video.mp4> [--privacy public|unlisted|private]

Title/description/tags are set in the CONFIG block (per-clip for now; the real
pipeline will pass these from the generator).
"""
import os, sys, json, argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401 (parity w/ podcast)
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

TOKEN_FILE = os.path.expanduser("~/.config/youtube-token.json")
CATEGORY_NEWS = "25"  # News & Politics (matches the channel)

# --- per-clip metadata (the generator will supply these later) ---
TITLE = "Tucson kids named two rescued mountain lion cubs 🦁 #Shorts"
DESCRIPTION = (
    "Tucson, meet Moonbead and Pretzel. 🦁\n\n"
    "Two orphaned mountain lion brothers — rescued in April, found in the wild "
    "without their mother — finally have names. The naming was given to kids "
    "from Beads of Courage, a nonprofit for children facing serious illness, who "
    "named them at the Arizona-Sonora Desert Museum.\n\n"
    "A little good desert news for your day. 🌵\n\n"
    "More Tucson news every morning at tucsondailybrief.com\n\n"
    "#Shorts #Tucson #TucsonAZ #DesertMuseum #MountainLion #SonoranDesert "
    "#OnlyInTucson #LocalNews"
)
TAGS = ["Tucson", "Tucson news", "Arizona", "Desert Museum", "mountain lion",
        "Moonbead", "Pretzel", "Sonoran Desert", "Only in Tucson", "local news"]


def get_credentials():
    if not os.path.exists(TOKEN_FILE):
        sys.exit(f"ERROR: no YouTube token at {TOKEN_FILE}")
    d = json.loads(Path(TOKEN_FILE).read_text())
    creds = Credentials(
        token=d["token"], refresh_token=d["refresh_token"],
        token_uri=d["token_uri"], client_id=d["client_id"],
        client_secret=d["client_secret"],
    )
    if creds.expired or not creds.valid:
        creds.refresh(Request())
        d["token"] = creds.token
        Path(TOKEN_FILE).write_text(json.dumps(d, indent=2))
    return creds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    args = ap.parse_args()
    if not os.path.exists(args.video):
        sys.exit(f"ERROR: video not found: {args.video}")

    yt = build("youtube", "v3", credentials=get_credentials())
    body = {
        "snippet": {"title": TITLE, "description": DESCRIPTION,
                    "tags": TAGS, "categoryId": CATEGORY_NEWS},
        "status": {"privacyStatus": args.privacy,
                   "selfDeclaredMadeForKids": False},
    }
    size_mb = os.path.getsize(args.video) / (1024 * 1024)
    print(f"Uploading Short ({size_mb:.1f} MB, {args.privacy})\n  {TITLE}")
    media = MediaFileUpload(args.video, mimetype="video/mp4", resumable=True,
                            chunksize=4 * 1024 * 1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  {int(status.progress()*100)}%")
    vid = resp["id"]
    print(f"\n=== PUBLISHED ===\nhttps://www.youtube.com/watch?v={vid}\n"
          f"Shorts: https://www.youtube.com/shorts/{vid}")


if __name__ == "__main__":
    main()
