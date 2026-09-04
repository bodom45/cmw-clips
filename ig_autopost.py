#!/usr/bin/env python3.14
"""Instagram Reels auto-poster — publishes scheduled clips via the Graph API.

You provide (one-time): IG_USER_ID + IG_ACCESS_TOKEN (long-lived) and a public
BASE_URL where the clips are hosted. This reads POSTING_SCHEDULE.csv and, for
each row whose time has arrived, creates a Reels container, waits for it to
finish processing, and publishes it — with the cover as the thumbnail.

Modes:
  --list           show what's scheduled and what's due now
  --test ROW       publish a single row NOW (1-based), ignoring its date — for a first test
  --due            publish everything due up to now (what a cron runs every ~15 min)

Env: IG_USER_ID, IG_ACCESS_TOKEN, BASE_URL, GRAPH_VERSION(optional), STATE_FILE(optional)
"""
from __future__ import annotations
import csv, json, os, sys, time, urllib.parse, urllib.request, datetime as dt
from pathlib import Path

CSV = Path(os.environ.get("SCHEDULE_CSV", Path.home()/"Desktop/Orbit-Music-Clips/POSTING_SCHEDULE.csv"))
GRAPH = os.environ.get("GRAPH_VERSION", "v21.0")
STATE = Path(os.environ.get("STATE_FILE", Path.home()/"Downloads/sf_work/poster/posted.json"))


def _api(method, path, params):
    url = f"https://graph.facebook.com/{GRAPH}/{path}"
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        url += "?" + data.decode(); data = None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Graph {method} {path} -> {e.code}: {e.read().decode()[:400]}")


def post_reel(ig_user, token, video_url, caption, cover_url=None):
    p = {"media_type": "REELS", "video_url": video_url, "caption": caption,
         "share_to_feed": "false", "access_token": token}
    if cover_url:
        p["cover_url"] = cover_url
    container = _api("POST", f"{ig_user}/media", p)["id"]
    # poll processing (Reels need encoding time). IG can flicker through a
    # transient ERROR before settling on FINISHED, so tolerate a few errors
    # and keep waiting rather than bailing immediately.
    errors = 0
    for _ in range(75):  # up to ~10 min
        st = _api("GET", container, {"fields": "status_code", "access_token": token})
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            errors += 1
            if errors >= 6:  # persistent failure
                raise RuntimeError(f"container {container} failed: {st}")
        time.sleep(8)
    pub = _api("POST", f"{ig_user}/media_publish",
               {"creation_id": container, "access_token": token})
    return pub.get("id")


def post_trial_reel(ig_user, token, video_url, caption):
    """Publish the SAME reel as a Trial Reel (non-followers only, ~72h;
    winners auto-graduate via SS_PERFORMANCE). Never raises — a trial
    failure must not affect the regular post."""
    try:
        p = {"media_type": "REELS", "video_url": video_url, "caption": caption,
             "trial_params": json.dumps({"graduation_strategy": "SS_PERFORMANCE"}),
             "access_token": token}
        container = _api("POST", f"{ig_user}/media", p)["id"]
        errors = 0
        for _ in range(75):
            st = _api("GET", container, {"fields": "status_code", "access_token": token})
            code = st.get("status_code")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                errors += 1
                if errors >= 6:
                    print(f"  trial-twin container failed: {st}")
                    return None
            time.sleep(8)
        pub = _api("POST", f"{ig_user}/media_publish",
                   {"creation_id": container, "access_token": token})
        return pub.get("id")
    except Exception as e:
        print(f"  trial-twin failed (regular post unaffected): {e}")
        return None


def load_rows():
    with open(CSV) as f:
        return list(csv.DictReader(f))


def _name(s):
    # accept old "dateTtime|path/clip.mp4" keys OR new "clip.mp4" basenames
    return s.split("|", 1)[-1].split("/")[-1]


def load_state():
    # state is a SET OF CLIP BASENAMES — a clip posts once, ever, regardless of
    # what date/time slot it sits in. This makes re-dating the schedule safe:
    # moving a posted clip to a new slot can never cause a duplicate post.
    if not STATE.exists():
        return set()
    return {_name(x) for x in json.loads(STATE.read_text())}


def save_state(done):
    STATE.write_text(json.dumps(sorted(done)))


def key(r):
    return f"{r['post_date']}T{r['post_time']}|{r['clip_file']}"


def clipname(r):
    return Path(r['clip_file']).name


def env():
    ig, tok, base = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN"), os.environ.get("BASE_URL")
    if not (ig and tok and base):
        sys.exit("Set IG_USER_ID, IG_ACCESS_TOKEN, BASE_URL first.")
    return ig, tok, base.rstrip("/")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "--list"
    rows = load_rows()
    if arg == "--list":
        done = load_state()
        now = dt.datetime.now()
        for i, r in enumerate(rows, 1):
            when = dt.datetime.fromisoformat(f"{r['post_date']}T{r['post_time']}")
            mark = "✅posted" if clipname(r) in done else ("⏰due" if when <= now else "  queued")
            print(f"{i:>2}. {mark}  {r['post_date']} {r['post_time']}  {r['clip_file']}")
        return
    ig, tok, base = env()
    if arg == "--test":
        r = rows[int(sys.argv[2]) - 1]
        vid = f"{base}/{urllib.parse.quote(Path(r['clip_file']).name)}"
        cov = f"{base}/{urllib.parse.quote(Path(r['cover_file']).name)}"
        print("posting NOW:", r['clip_file'])
        print("media id:", post_reel(ig, tok, vid, r['caption'], cov))
        return
    if arg == "--due":
        done = load_state(); now = dt.datetime.now()
        cap = int(os.environ.get("DUE_CAP", "4")); posted = 0
        for r in rows:
            if posted >= cap:
                break
            when = dt.datetime.fromisoformat(f"{r['post_date']}T{r['post_time']}")
            if when <= now and clipname(r) not in done:
                vid = f"{base}/{urllib.parse.quote(Path(r['clip_file']).name)}"
                cov = f"{base}/{urllib.parse.quote(Path(r['cover_file']).name)}" if r.get('cover_file') else None
                try:
                    # DJ TRIAL-ONLY (Brandon 2026-09-02): DJ clips publish ONLY as
                    # Trial Reels (non-followers, ~72h) until he says otherwise.
                    # AI clips keep normal behaviour. DJ_TRIAL_ONLY=0 reverts.
                    dj_trial = (os.environ.get("DJ_TRIAL_ONLY", "1") == "1"
                                and clipname(r).startswith("DJ_"))
                    if dj_trial:
                        mid = post_trial_reel(ig, tok, vid, r['caption'])
                        if not mid:
                            raise RuntimeError("trial-only publish failed; retry next run")
                        posted += 1
                        done.add(clipname(r)); save_state(done)
                        print(f"🧪 {r['clip_file']} -> TRIAL-ONLY {mid}")
                        continue
                    mid = post_reel(ig, tok, vid, r['caption'], cov)
                    posted += 1
                    done.add(clipname(r)); save_state(done)
                    print(f"✅ {r['clip_file']} -> {mid}")
                    if os.environ.get("TRIAL_DUPLICATE", "1") == "1":
                        tid = post_trial_reel(ig, tok, vid, r['caption'])
                        if tid:
                            print(f"🧪 trial twin -> {tid}")
                except Exception as e:
                    print(f"❌ {r['clip_file']}: {e}")
        return

if __name__ == "__main__":
    main()
