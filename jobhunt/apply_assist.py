#!/usr/bin/env python3
"""Apply assistant: opens each queued job in a real browser, fills in your
details and resume, then hands over to you. You check the form, solve any
captcha and press Submit. Nothing is ever submitted for you.

Setup (once, on your own computer):
  pip install playwright && playwright install chromium
  cp jobhunt/profile.example.json jobhunt/profile.json   # then edit it
  put your resume at jobhunt/resume.pdf

Run:  python jobhunt/apply_assist.py            (all new roles)
      python jobhunt/apply_assist.py --limit 5
After each form, type  a = applied, s = skip, q = quit.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
SEEN = HERE / "seen.json"

# (profile key, label pattern, direct selectors used by Greenhouse / Lever / Ashby)
FIELDS = [
    ("first_name", r"first\s*name|given name", ["#first_name", "input[name='first_name']"]),
    ("last_name", r"last\s*name|family name|surname", ["#last_name", "input[name='last_name']"]),
    ("full_name", r"^\s*(full\s*)?name\b", ["input[name='name']", "#_systemfield_name"]),
    ("email", r"e-?mail", ["#email", "input[name='email']", "#_systemfield_email"]),
    ("phone", r"phone|mobile", ["#phone", "input[name='phone']"]),
    ("location", r"location|city", ["input[name='location']", "#candidate-location"]),
    ("linkedin", r"linkedin", ["input[name='urls[LinkedIn]']"]),
    ("github", r"github", ["input[name='urls[GitHub]']"]),
    ("website", r"website|portfolio|personal site", ["input[name='urls[Portfolio]']", "input[name='urls[Other]']"]),
]


def try_fill(page, value, label_re, selectors):
    if not value:
        return False
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() and loc.first.is_visible() and not loc.first.input_value():
            loc.first.fill(value); return True
    loc = page.get_by_label(re.compile(label_re, re.I))
    for i in range(min(loc.count(), 3)):
        el = loc.nth(i)
        try:
            if el.is_visible() and el.evaluate("e => ['INPUT','TEXTAREA'].includes(e.tagName)") and not el.input_value():
                el.fill(value); return True
        except Exception:
            pass
    return False


def fill(page, p):
    p = {**p, "full_name": f"{p.get('first_name','')} {p.get('last_name','')}".strip()}
    # Ashby and some Greenhouse pages show the description first; open the form.
    for name in ("Apply for this job", "Apply", "Application"):
        btn = page.get_by_role("tab", name=name).or_(page.get_by_role("button", name=name)).or_(page.get_by_role("link", name=name))
        if btn.count() and btn.first.is_visible():
            try: btn.first.click(timeout=3000); page.wait_for_timeout(1500); break
            except Exception: pass
    done = [key for key, rx, sels in FIELDS if try_fill(page, p.get(key, ""), rx, sels)]
    resume = Path(p.get("resume_path", ""))
    if resume.is_file():
        files = page.locator("input[type='file']")
        if files.count():
            files.first.set_input_files(str(resume)); done.append("resume")
    cover = p.get("cover_letter", "")
    if cover:
        ta = page.get_by_label(re.compile(r"cover letter|why .*(interested|join)|additional information", re.I))
        if ta.count() and ta.first.evaluate("e => e.tagName") == "TEXTAREA" and not ta.first.input_value():
            ta.first.fill(cover); done.append("cover note")
    return done


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=0); a = ap.parse_args()
    prof_path = HERE / "profile.json"
    if not prof_path.exists():
        sys.exit("Copy jobhunt/profile.example.json to jobhunt/profile.json and fill it in first.")
    profile = json.loads(prof_path.read_text())
    seen = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    queue = [j for j in seen.values() if j["status"] == "new"]
    queue.sort(key=lambda j: (j["first_seen"], j["pay"]), reverse=True)
    if a.limit: queue = queue[: a.limit]
    if not queue:
        sys.exit("Queue is empty. Pull the latest seen.json from GitHub first.")

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(str(HERE / ".browser"), headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for n, j in enumerate(queue, 1):
            print(f"\n[{n}/{len(queue)}] {j['company']} — {j['title']}  ({j['location']})\n  {j['url']}")
            try:
                page.goto(j["url"], wait_until="domcontentloaded", timeout=45000); page.wait_for_timeout(2000)
                print("  filled:", ", ".join(fill(page, profile)) or "nothing (fill it by hand)")
            except Exception as e:
                print("  could not pre-fill:", e)
            print("  Check the form, answer any extra questions, solve the captcha and press Submit.")
            ans = input("  a = applied, s = skip, q = quit > ").strip().lower()
            if ans == "q": break
            if ans in ("a", "s"):
                seen[j["url"]]["status"] = "applied" if ans == "a" else "skipped"
                SEEN.write_text(json.dumps(seen, indent=1, sort_keys=True))
        ctx.close()
    print("\nSaved. Commit jobhunt/seen.json so the daily queue drops what you've handled.")


if __name__ == "__main__":
    main()
