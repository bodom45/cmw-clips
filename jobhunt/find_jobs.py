#!/usr/bin/env python3
"""Daily job finder: pulls open roles from public Greenhouse, Lever and Ashby
job-board APIs, keeps senior AI/automation roles in Dallas/Texas or US-remote
that pay at least MIN_SALARY (or don't list pay), and writes QUEUE.md with
direct apply links. New roles are tracked in seen.json so each shows up once.
"""
from __future__ import annotations
import json, os, re, sys, urllib.request, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
MIN_SALARY = int(os.environ.get("MIN_SALARY", "80000"))
SEEN = HERE / "seen.json"
QUEUE = HERE / "QUEUE.md"

TITLE_YES = re.compile(r"\b(ai|a\.i\.|ml|llm|genai|generative|agent|agentic|automation|machine learning|applied ai|solutions? architect|forward deployed)\b", re.I)
TITLE_NO = re.compile(r"\b(intern|internship|new grad|junior|jr\.?|associate|recruiter|sales development|account executive|counsel|paralegal)\b", re.I)
SENIOR = re.compile(r"\b(senior|sr\.?|staff|principal|lead|head|director|manager|architect|founding|forward deployed)\b", re.I)
LOC_YES = re.compile(r"(dallas|fort worth|dfw|plano|irving|frisco|addison|richardson|austin|texas|\btx\b|remote)", re.I)
LOC_NO = re.compile(r"remote.{0,20}\b(uk|emea|europe|canada|india|apac|latam|germany|france|poland|brazil|australia)\b", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "jobhunt/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def money(text):
    """Largest $ figure in text, in dollars/year (handles 150k and 150,000)."""
    best = 0
    for m in re.finditer(r"\$\s?(\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d)?\s?[kK])", text or ""):
        v = m.group(1).replace(",", "").replace(" ", "")
        n = float(v[:-1]) * 1000 if v[-1] in "kK" else float(v)
        best = max(best, int(n))
    return best


def greenhouse(co):
    for j in get(f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs?content=true")["jobs"]:
        yield dict(company=co, title=j["title"], location=(j.get("location") or {}).get("name", ""),
                   url=j["absolute_url"], pay=money(j.get("content", "")), ats="greenhouse",
                   posted=j.get("updated_at", "")[:10])


def lever(co):
    for j in get(f"https://api.lever.co/v0/postings/{co}?mode=json"):
        cats = j.get("categories") or {}
        sr = j.get("salaryRange") or {}
        pay = int(sr.get("max") or 0) or money(j.get("descriptionPlain", "") + j.get("additionalPlain", ""))
        posted = dt.datetime.fromtimestamp(j.get("createdAt", 0) / 1000).date().isoformat()
        yield dict(company=co, title=j["text"], location=cats.get("location", "") + (" remote" if j.get("workplaceType") == "remote" else ""),
                   url=j.get("applyUrl") or j["hostedUrl"], pay=pay, ats="lever", posted=posted)


def ashby(co):
    for j in get(f"https://api.ashbyhq.com/posting-api/job-board/{co}?includeCompensation=true")["jobs"]:
        loc = " ".join(filter(None, [j.get("location", ""), "remote" if j.get("isRemote") else "",
                                     " ".join(s.get("location", "") for s in j.get("secondaryLocations") or [])]))
        comp = (j.get("compensation") or {}).get("compensationTierSummary", "")
        yield dict(company=co, title=j["title"], location=loc, url=j.get("applyUrl") or j["jobUrl"],
                   pay=money(comp) or money(j.get("descriptionPlain", "")), ats="ashby",
                   posted=(j.get("publishedAt") or "")[:10])


def keep(j):
    t, loc = j["title"], j["location"]
    if not TITLE_YES.search(t) or TITLE_NO.search(t) or not SENIOR.search(t):
        return False
    if not LOC_YES.search(loc) or LOC_NO.search(loc):
        return False
    return j["pay"] == 0 or j["pay"] >= MIN_SALARY


def main():
    cos = json.loads((HERE / "companies.json").read_text())
    found, errors = [], []
    for ats, fn in (("greenhouse", greenhouse), ("lever", lever), ("ashby", ashby)):
        for co in cos.get(ats, []):
            try:
                found += [j for j in fn(co) if keep(j)]
            except Exception as e:
                errors.append(f"{ats}/{co}: {e}")
    seen = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    today = dt.date.today().isoformat()
    for j in found:
        seen.setdefault(j["url"], {**j, "first_seen": today, "status": "new"})
    SEEN.write_text(json.dumps(seen, indent=1, sort_keys=True))

    open_ = [j for j in seen.values() if j["status"] == "new"]
    open_.sort(key=lambda j: (j["first_seen"], j["pay"]), reverse=True)
    lines = [f"# Job queue — updated {today}", "",
             f"{len(open_)} roles waiting. Run `python jobhunt/apply_assist.py` to open and pre-fill them, "
             "then solve the captcha and press Submit yourself.", "",
             "| New | Company | Role | Location | Top pay | Apply |", "|---|---|---|---|---|---|"]
    for j in open_:
        pay = f"${j['pay']:,}" if j["pay"] else "not listed"
        new = "🆕" if j["first_seen"] == today else ""
        lines.append(f"| {new} | {j['company']} | {j['title']} | {j['location'][:40]} | {pay} | [apply]({j['url']}) |")
    if errors:
        lines += ["", "<details><summary>Boards that failed this run</summary>", ""] + [f"- {e}" for e in errors] + ["", "</details>"]
    QUEUE.write_text("\n".join(lines) + "\n")
    print(f"{len(found)} matches, {sum(j['first_seen']==today for j in open_)} new, {len(errors)} board errors")


if __name__ == "__main__":
    main()
