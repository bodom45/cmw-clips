#!/usr/bin/env python3
"""Tailored resumes: one source of truth for the resume, re-ordered per job.

Every bullet and skill here is real. Tailoring never adds claims; it reads the
job description, works out what the role cares about most (GTM, agents,
customer deployments, transformation, content), then picks the matching
headline and summary, puts the most relevant bullets first and bolds the tools
the posting names.

  python jobhunt/tailor.py --base                 rebuild portfolio/resume.html + PDF
  python jobhunt/tailor.py --all --min-fit 70     one PDF per queued job -> jobhunt/resumes/
  python jobhunt/tailor.py --url <apply url>      one job
"""
from __future__ import annotations
import argparse, glob, html, json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
FILE_NAME = "Brandon_Odom_Resume.pdf"  # what recruiters see when the file is uploaded

CONTACT = {
    "name": "Brandon Odom",
    "line": ["Dallas, TX", "brandon.niles.odom@gmail.com", "github.com/bodom45", "area51hq.vercel.app"],
}

THEMES = {
    "gtm": r"\bgtm\b|go-to-market|sales|\bsdrs?\b|\bbdrs?\b|revenue|crm|salesforce|hubspot|\bclay\b|outbound|prospect|account[- ]based|\babm\b|revops|\bleads?\b",
    "agents": r"\bagents?\b|agentic|\bllms?\b|large language|claude|\bgpt|openai|anthropic|prompt|\brag\b|retrieval|conversational|chatbot|voice|tool use|function calling|\bevals?\b",
    "deploy": r"forward deployed|customers?\b|implementation|deploy|onboard|enterprise|stakeholder|solutions?\b|integrat|consult|post-sales|pre-sales",
    "data": r"\bdata\b|\bsql\b|analytics|metrics|dashboard|scoring|insights?|reporting|attribution|\betl\b",
    "platform": r"\bapis?\b|backend|typescript|python|node|react|next\.?js|postgres|serverless|infrastructure|scalab|reliab|architect|production",
    "automation": r"automat|workflows?|zapier|\bn8n\b|orchestrat|schedul|\bcron\b|pipelines?",
    "content": r"content|media|creators?|social|video|brand|campaigns?|youtube|instagram|tiktok",
    "transform": r"transformation|enablement|adoption|change management|training|workshops?|strategy|roadmap|champions?|upskill",
}
LEADS = ["gtm", "agents", "deploy", "transform", "content"]  # themes that pick the headline + summary

HEADLINES = {
    "gtm": "AI Automation Engineer · GTM Systems · Agentic AI",
    "agents": "AI Engineer · Agentic Systems · LLM Applications",
    "deploy": "Applied AI Engineer · Deployments · Integrations",
    "transform": "AI Transformation · Automation · Enablement",
    "content": "AI Automation Engineer · Content & Growth Systems",
}
SUMMARIES = {
    "gtm": "I build the AI systems GTM teams run on: lead sourcing and enrichment, outreach sequencing, AI agents that handle replies, and pipeline visibility. I design, ship and operate them end to end, from data model and API integrations to deploys, cost limits and failure recovery, and they run real revenue work every day at Creative Music Television and Area 51 Radio.",
    "agents": "I build production LLM systems: Claude agents with tool use, streaming and prompt caching, model fallback between Claude and GPT, usage limits, and tests that guard them. I take them from prototype to always-on, and they handle real work every day at Creative Music Television and Area 51 Radio.",
    "deploy": "I turn business problems into working AI systems quickly: scope the workflow, integrate the APIs, ship, and stay with it in production. My systems span AI outreach with a reply agent, an AI operations console, a multi-tenant SaaS app and unattended content pipelines, all used every day at Creative Music Television and Area 51 Radio.",
    "transform": "I lead AI adoption by building it: find the manual work, automate it, and get the team using it. At Creative Music Television and Area 51 Radio that meant AI outreach and reply agents, an AI console the business runs on, unattended publishing pipelines and explainable scoring tools, while leading the production team and an internship program.",
    "content": "I build the systems behind content and growth, from unattended publishing pipelines that have shipped 260+ videos to AI-written outreach and a self-serve marketing platform, and I lead the production team that makes the content. Everything runs in production every day at Creative Music Television and Area 51 Radio.",
}

ROLES = [
    {"title": "AI Automation Engineer &amp; Technical Lead", "place": "Dallas, TX", "org": "Creative Music Television (CTV)", "bullets": [
        (["gtm", "agents", "platform", "automation", "data"], "<b>Orbit, AI prospecting and outreach:</b> built a system that can serve several client organizations, each seeing only its own data, on Supabase (24 tables, 19 edge functions). It finds and fills in lead details, runs outreach sequences from a queue that blocks duplicates and retries failures, and uses a Claude agent to read and answer replies. A model rewrites the outreach copy every week. It manages 2,584 leads and 31k+ industry contacts."),
        (["agents", "platform", "data", "transform"], "<b>The Captain's HQ, Claude operations console:</b> the Next.js console the business runs on. Claude looks up live pipeline data, streams its answers and uses prompt caching under usage limits. It rebuilds its context, runs 77 tests and redeploys every morning."),
        (["automation", "content", "platform"], "<b>CMW Autopost:</b> a scheduled GitHub Actions pipeline that has published 260+ Instagram Reels and YouTube Shorts unattended, with retries and duplicate protection."),
        (["data", "transform", "gtm"], "<b>Grant Radar:</b> scores funding opportunities across 8 weighted criteria, explains each score and drafts the start of each application."),
    ]},
    {"title": "Product Engineer", "place": "Dallas, TX", "org": "Area 51 Radio", "bullets": [
        (["platform", "deploy", "data"], "Built The Motion Hub, a self-serve marketing platform for independent creators (Next.js, Prisma, 28 data models, 53 API routes), with Stripe credit packs and subscriptions."),
        (["agents", "automation", "content", "deploy"], "Connected OpenAI, HeyGen, Spotify, TikTok and Meta, and added scheduled jobs that sync opportunities daily and tune ad campaigns every 6 hours."),
    ]},
    {"title": "Content Systems &amp; Production Lead", "place": "Dallas–Fort Worth", "org": "CTV Motion Media", "bullets": [
        (["content", "gtm", "deploy", "automation"], "Deliver done-for-you content systems for DFW service businesses, from scripting and shoots to automated posting. Client and company content has reached 1M+ organic views."),
        (["transform"], "Lead the production team and run a paid media internship program."),
    ]},
]

SKILLS = [
    ("AI &amp; Agents", [
        (["agents"], "Claude API: tool use, streaming, prompt caching"),
        (["agents", "platform"], "Switching between Claude and GPT models"),
        (["agents", "gtm"], "AI agents that answer messages"),
        (["agents", "content"], "Automated prompt and copy improvement"),
    ]),
    ("Engineering", [
        (["platform"], "TypeScript, React, Next.js"),
        (["platform", "data"], "Python, Node.js"),
        (["platform", "data"], "Supabase, Postgres, Prisma"),
        (["platform", "automation"], "Edge functions, queues, retries"),
        (["automation", "platform"], "GitHub Actions, Vercel, scheduled jobs"),
    ]),
    ("Integrations", [
        (["gtm"], "Salesforce, Clay (GTM)"),
        (["content", "gtm"], "Meta Graph and Instagram APIs"),
        (["content", "platform"], "YouTube Data API, Google sign-in (OAuth)"),
        (["platform", "content"], "Stripe, Spotify, TikTok"),
        (["gtm", "automation"], "Apify, Resend, HeyGen"),
    ]),
]
LIVE = ["dmoutreachtool.vercel.app", "area51hq.vercel.app", "area51radio-artist-hub.vercel.app", "cmt-grant-radar.vercel.app"]
TOOLS = ["Salesforce", "Clay", "Claude", "GPT", "OpenAI", "TypeScript", "React", "Next.js", "Python", "Node.js", "Supabase",
         "Postgres", "Prisma", "GitHub Actions", "Vercel", "Stripe", "Spotify", "TikTok", "Instagram", "YouTube", "OAuth",
         "Apify", "Resend", "HeyGen", "Meta"]

CSS = """
:root{--bg:#ffffff;--fg:#14181f;--muted:#566070;--line:#dfe3e8;--accent:#c8321c;
  --display:"Archivo",system-ui,sans-serif;--body:"Source Serif 4",Georgia,serif;color-scheme:light}
@page{size:letter;margin:0.5in}
body{background:var(--bg);color:var(--fg);font:10pt/1.42 var(--body);margin:0}
.page{max-width:7.5in;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px;display:grid;gap:14px}
@media print{.page{padding:0}}
h1,h2,h3{font-family:var(--display);margin:0;line-height:1.15}
h1{font-size:24pt;font-weight:800;letter-spacing:-.01em}
.role{font:600 11pt var(--display);color:var(--accent)}
.contact{font:9pt var(--display);color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 14px}
p{margin:0}
h2{font-size:8.5pt;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:3px;margin-bottom:6px}
.cols{display:grid;grid-template-columns:1fr 2.1in;gap:22px}
.cols>*{min-width:0;display:grid;gap:12px;align-content:start}
.job{display:grid;gap:3px}
.job+.job{margin-top:12px}
.job h3{font-size:10.5pt;font-weight:700;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.job h3 span{font-weight:500;color:var(--muted);font-size:9pt}
.sub{font:9pt var(--display);color:var(--muted)}
ul{margin:0;padding-left:1.05em;display:grid;gap:2px}
.side ul{list-style:none;padding:0}
.side li{font-size:9.3pt}
@media(max-width:620px){.cols{grid-template-columns:1fr}}
"""
FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">'


def themes(title: str, desc: str) -> dict[str, float]:
    """How much the posting cares about each theme. Title words count 5x."""
    t, d = title.lower(), desc.lower()
    return {k: 5 * len(re.findall(rx, t)) + len(re.findall(rx, d)) for k, rx in THEMES.items()}


def build(job: dict | None = None) -> tuple[str, dict]:
    """Resume HTML, tailored to `job` (title + desc) when given."""
    score = themes(job.get("title", ""), job.get("desc", "")) if job else {}
    lead = max(LEADS, key=lambda k: (score.get(k, 0), -LEADS.index(k))) if any(score.values()) else "gtm"
    text = (job.get("title", "") + " " + job.get("desc", "")).lower() if job else ""
    named = [t for t in TOOLS if text and re.search(r"(?<![a-z])" + re.escape(t.lower()) + r"(?![a-z])", text)]

    def rank(items):
        return sorted(items, key=lambda it: -sum(score.get(tag, 0) for tag in it[0])) if score else items

    def mark(s):
        for t in named:
            s = re.sub(r"(?<![\w>])(" + re.escape(t) + r")(?![\w<])", r"<b>\1</b>", s, count=1)
        return s

    jobs_html = "".join(
        f'<div class="job"><h3>{r["title"]} <span>{r["place"]}</span></h3><div class="sub">{r["org"]}</div><ul>'
        + "".join(f"<li>{b}</li>" for _, b in rank(r["bullets"])) + "</ul></div>" for r in ROLES)
    side_html = "".join(f"<section><h2>{name}</h2><ul>" + "".join(f"<li>{mark(s)}</li>" for _, s in rank(items)) + "</ul></section>"
                        for name, items in SKILLS)
    side_html += "<section><h2>Live work</h2><ul>" + "".join(f"<li>{u}</li>" for u in LIVE) + "</ul></section>"
    page = f"""<title>{CONTACT['name']} Resume</title>
<meta name="claude:viewport-fit-sides" content="cover">
{FONTS}
<style>{CSS}</style>
<div class="page">
<header>
  <h1>{CONTACT['name']}</h1>
  <div class="role">{HEADLINES[lead]}</div>
  <div class="contact">{''.join(f'<span>{html.escape(c)}</span>' for c in CONTACT['line'])}</div>
</header>
<section><h2>Summary</h2><p>{SUMMARIES[lead]}</p></section>
<div class="cols">
<div><section><h2>Experience</h2>{jobs_html}</section></div>
<aside class="side">{side_html}</aside>
</div>
</div>
"""
    return page, {"lead": lead, "themes": score, "named": named}


def render_pdf(page_html: str, out: Path, pw=None):
    """Print the HTML to a one-page letter PDF with headless Chromium."""
    from playwright.sync_api import sync_playwright

    def go(p):
        try:
            browser = p.chromium.launch()
        except Exception:
            exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome") or [None])[0]
            browser = p.chromium.launch(executable_path=exe)
        tab = browser.new_page()
        tab.set_content("<!doctype html><meta charset=utf-8>" + page_html, wait_until="networkidle")
        out.parent.mkdir(parents=True, exist_ok=True)
        tab.pdf(path=str(out), format="Letter", print_background=True,
                margin=dict(top="0.5in", bottom="0.5in", left="0.5in", right="0.5in"))
        browser.close()

    if pw is not None:
        go(pw)
    else:
        with sync_playwright() as p:
            go(p)
    return out


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def for_job(job: dict, out_dir: Path = HERE / "resumes", pw=None) -> tuple[Path, dict]:
    page, info = build(job)
    out = out_dir / f"{slug(job['company'])}-{slug(job['title'])}" / FILE_NAME
    return render_pdf(page, out, pw), info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--url")
    ap.add_argument("--min-fit", type=int, default=70)
    a = ap.parse_args()
    if a.base:
        page, _ = build(None)
        root = HERE.parent / "portfolio"
        (root / "resume.html").write_text(page)
        render_pdf(page, root / FILE_NAME)
        print("rebuilt portfolio/resume.html and", FILE_NAME)
        return
    seen = json.loads((HERE / "seen.json").read_text())
    jobs = [j for j in seen.values() if j.get("status") == "new" and j.get("desc")]
    if a.url:
        jobs = [j for j in jobs if j["url"] == a.url]
    elif a.all:
        jobs = [j for j in jobs if j.get("fit", 0) >= a.min_fit]
    else:
        sys.exit(__doc__)
    if not jobs:
        sys.exit("No matching jobs with descriptions yet. They appear after the next daily search.")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        for j in sorted(jobs, key=lambda j: -j.get("fit", 0)):
            out, info = for_job(j, pw=p)
            print(f"{j['company']:<12} {j['title'][:48]:<48} lead={info['lead']:<9} tools={','.join(info['named']) or '-'}")
    print(f"\n{len(jobs)} resumes in {HERE / 'resumes'}")


if __name__ == "__main__":
    main()
