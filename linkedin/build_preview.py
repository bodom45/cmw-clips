#!/usr/bin/env python3
"""Build linkedin/preview.html: every post with its image or video and a copy button."""
import html, json
from pathlib import Path

HERE = Path(__file__).parent
d = json.loads((HERE / "series.json").read_text())
e = html.escape

cards = []
for n, p in enumerate(d["posts"], 1):
    vid = p["visual"]["kind"] == "dashboard"
    media = (f'<video src="media/{p["id"]}.mp4" poster="media/{p["id"]}-final.png" controls muted loop playsinline preload="none"></video>'
             if vid else f'<img src="media/{p["id"]}.png" alt="{e(p["visual"]["title"])}" loading="lazy">')
    alt = f'<a class="alt" href="media/{p["id"]}.png" target="_blank" rel="noopener">Diagram version</a>' if vid else ""
    title = (p.get("diagram") or p["visual"])["title"]
    cards.append(f"""<article class="post" id="p{n}">
  <div class="media">{media}{alt}</div>
  <div class="copy">
    <div class="meta"><span class="num">{n:02d}</span><span class="kind{' v' if vid else ''}">{'Video' if vid else 'Image'}</span><span class="len">{len(p['text']):,} characters</span></div>
    <h2>{e(title)}</h2>
    <pre id="t{n}">{e(p['text'])}</pre>
    <button type="button" data-copy="t{n}" id="c{n}">Copy post text</button>
  </div>
</article>""")

page = f"""<title>Systems I Build</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;800&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: a review board; one row per post, media left at feed size, copy right */
:root{{--bg:#f6f7f9;--card:#ffffff;--fg:#0f1b2d;--muted:#5b6678;--line:#dde2ea;--accent:#e2470f;--soft:#fff0e9;
 --display:"Archivo",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0d131c;--card:#151d29;--fg:#e8edf4;--muted:#9aa6b8;--line:#263142;--accent:#ff7a45;--soft:#2a1c16;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#0d131c;--card:#151d29;--fg:#e8edf4;--muted:#9aa6b8;--line:#263142;--accent:#ff7a45;--soft:#2a1c16;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:16px/1.5 var(--display)}}
.wrap{{max-width:1080px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:40px 80px;display:grid;gap:28px}}
header{{display:grid;gap:10px}}
.eyebrow{{font:500 .78rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}}
h1{{margin:0;font-size:clamp(2rem,5vw,2.8rem);font-weight:800;letter-spacing:-.02em;text-wrap:balance}}
header p{{margin:0;color:var(--muted);max-width:65ch}}
.post{{display:grid;grid-template-columns:minmax(0,380px) minmax(0,1fr);gap:28px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px}}
.media{{display:grid;gap:8px;align-content:start}}
.media img,.media video{{width:100%;max-width:100%;aspect-ratio:4/5;border-radius:10px;border:1px solid var(--line);background:var(--bg);display:block}}
.alt{{font:500 .8rem var(--mono);color:var(--accent)}}
.copy{{min-width:0;display:grid;gap:12px;align-content:start}}
.meta{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font:500 .78rem var(--mono);color:var(--muted)}}
.num{{color:var(--fg);font-weight:600}}
.kind{{border:1px solid var(--line);padding:2px 8px;border-radius:999px}}
.kind.v{{border-color:var(--accent);color:var(--accent);background:var(--soft)}}
h2{{margin:0;font-size:1.35rem;font-weight:800;text-wrap:balance}}
pre{{margin:0;white-space:pre-wrap;font:15px/1.55 var(--display);max-height:420px;overflow:auto;border-top:1px solid var(--line);padding-top:12px}}
button{{justify-self:start;font:600 .9rem var(--display);background:var(--fg);color:var(--bg);border:0;border-radius:8px;padding:10px 16px;cursor:pointer}}
button:focus-visible,a:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
@media (max-width:720px){{.post{{grid-template-columns:1fr}}}}
</style>
<div class="wrap">
<header>
  <div class="eyebrow">LinkedIn series · {len(d['posts'])} posts</div>
  <h1>{e(d['series'])}</h1>
  <p>Senior-level posts on the kinds of systems you build: agents, GTM pipelines, reliability, multi-tenant SaaS, cost controls, scoring and rollout strategy. Each has a diagram, and three have animated dashboard videos built from your real numbers.</p>
</header>
{''.join(cards)}
</div>
<script>
document.addEventListener('click', async ev => {{
  const b = ev.target.closest('[data-copy]'); if (!b) return;
  const pre = document.getElementById(b.dataset.copy);
  try {{ await navigator.clipboard.writeText(pre.textContent); b.textContent = 'Copied'; }}
  catch (e) {{ const r = document.createRange(); r.selectNodeContents(pre); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Selected, press copy'; }}
  setTimeout(() => b.textContent = 'Copy post text', 2000);
}});
</script>
"""
(HERE / "preview.html").write_text(page)
print("wrote", HERE / "preview.html")
