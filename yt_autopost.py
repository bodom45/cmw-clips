#!/usr/bin/env python3
"""YouTube Shorts auto-poster — mirrors scheduled clips to YouTube.

Same pattern as ig_autopost.py: reads POSTING_SCHEDULE.csv, posts every row
whose time has arrived AND whose `platforms` column includes "YouTube",
deduped by clip basename in posted_yt.json (a clip uploads once, ever).

Clips are fetched from BASE_URL (jsDelivr) and uploaded via the YouTube Data
API v3 resumable upload. Title = first caption line + #Shorts; description =
full caption. Stdlib only — no pip deps.

Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, BASE_URL,
     DUE_CAP (default 3), SCHEDULE_CSV, STATE_FILE (default posted_yt.json)

Modes:  --list | --test ROW | --due
"""
from __future__ import annotations
import csv, json, os, sys, time, urllib.parse, urllib.request, datetime as dt
from pathlib import Path

CSV = Path(os.environ.get("SCHEDULE_CSV", "POSTING_SCHEDULE.csv"))
STATE = Path(os.environ.get("STATE_FILE", "posted_yt.json"))
UPLOAD_URL = ("https://www.googleapis.com/upload/youtube/v3/videos"
              "?uploadType=resumable&part=snippet,status")


def access_token():
    cid = os.environ.get("YT_CLIENT_ID")
    sec = os.environ.get("YT_CLIENT_SECRET")
    ref = os.environ.get("YT_REFRESH_TOKEN")
    if not (cid and sec and ref):
        print("YT secrets not set (YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN) — skipping.")
        sys.exit(0)  # fail-soft so the cron stays green until Brandon finishes setup
    data = urllib.parse.urlencode({
        "client_id": cid, "client_secret": sec,
        "refresh_token": ref, "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["access_token"]


def fetch_clip(base, name):
    url = f"{base}/{urllib.parse.quote(name)}"
    with urllib.request.urlopen(url, timeout=300) as r:
        return r.read()


def upload_short(token, video_bytes, title, description):
    meta = {"snippet": {"title": title[:100], "description": description[:4900],
                        "categoryId": "10"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    req = urllib.request.Request(UPLOAD_URL, data=json.dumps(meta).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json; charset=UTF-8",
                                          "X-Upload-Content-Length": str(len(video_bytes)),
                                          "X-Upload-Content-Type": "video/mp4"})
    with urllib.request.urlopen(req, timeout=120) as r:
        session = r.headers["Location"]
    put = urllib.request.Request(session, data=video_bytes, method="PUT",
                                 headers={"Content-Type": "video/mp4"})
    with urllib.request.urlopen(put, timeout=600) as r:
        return json.loads(r.read()).get("id")


def yt_title(caption):
    first = (caption or "").strip().splitlines()[0].strip()
    first = first if first else "New mix"
    if "#shorts" not in first.lower():
        first = (first[:90].rstrip() + " #Shorts")
    return first


def load_rows():
    with open(CSV) as f:
        return [r for r in csv.DictReader(f)
                if "youtube" in (r.get("platforms", "") or "").lower()]


def clipname(r):
    return Path(r["clip_file"]).name


def load_state():
    if not STATE.exists():
        return set()
    return set(json.loads(STATE.read_text()))


def save_state(done):
    STATE.write_text(json.dumps(sorted(done)))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "--list"
    rows = load_rows()
    if arg == "--list":
        done = load_state(); now = dt.datetime.now()
        for i, r in enumerate(rows, 1):
            when = dt.datetime.fromisoformat(f"{r['post_date']}T{r['post_time']}")
            mark = "✅posted" if clipname(r) in done else ("⏰due" if when <= now else "  queued")
            print(f"{i:>2}. {mark}  {r['post_date']} {r['post_time']}  {r['clip_file']}")
        return
    base = os.environ.get("BASE_URL", "").rstrip("/")
    if not base:
        sys.exit("Set BASE_URL first.")
    token = access_token()
    if arg == "--test":
        r = rows[int(sys.argv[2]) - 1]
        vid = upload_short(token, fetch_clip(base, clipname(r)),
                           yt_title(r["caption"]), r["caption"])
        print("uploaded:", f"https://youtube.com/shorts/{vid}")
        return
    if arg == "--due":
        done = load_state(); now = dt.datetime.now()
        cap = int(os.environ.get("DUE_CAP", "3")); posted = 0
        for r in rows:
            if posted >= cap:
                break
            when = dt.datetime.fromisoformat(f"{r['post_date']}T{r['post_time']}")
            if when <= now and clipname(r) not in done:
                try:
                    vid = upload_short(token, fetch_clip(base, clipname(r)),
                                       yt_title(r["caption"]), r["caption"])
                    posted += 1
                    done.add(clipname(r)); save_state(done)
                    print(f"✅ {r['clip_file']} -> https://youtube.com/shorts/{vid}")
                except Exception as e:
                    print(f"❌ {r['clip_file']}: {e}")
        return


if __name__ == "__main__":
    main()
