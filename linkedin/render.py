#!/usr/bin/env python3
"""Render the LinkedIn series: one 1080x1350 diagram image per post, plus an
animated dashboard MP4 for posts whose visual is a dashboard.

  python linkedin/render.py            # everything -> linkedin/media/
  python linkedin/render.py 02-gtm-loop
Needs: pip install playwright (+ chromium), ffmpeg on PATH.
"""
from __future__ import annotations
import glob, html, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "media"
W, H, FPS, SECONDS = 1080, 1350, 30, 7

CSS = """
:root{--paper:#f6f7f9;--card:#ffffff;--ink:#0f1b2d;--muted:#5b6678;--line:#dde2ea;--accent:#ff5a1f;--soft:#fff0e9;--live:#12a37a;
 --display:"Archivo",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace}
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1350px;background:var(--paper);color:var(--ink);font-family:var(--display)}
.frame{width:1080px;height:1350px;padding:64px 68px 56px;display:flex;flex-direction:column;gap:30px}
.top{display:flex;justify-content:space-between;font:500 20px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.top b{color:var(--accent);font-weight:500}
h1{margin:0;font-size:62px;line-height:1.04;font-weight:800;letter-spacing:-.02em;text-wrap:balance}
.sub{font-size:28px;line-height:1.3;color:var(--muted);margin-top:-12px}
.body{flex:1;display:flex;flex-direction:column;gap:16px;justify-content:center;min-height:0}
.proof{background:var(--soft);border:1.5px solid color-mix(in srgb,var(--accent) 35%,transparent);border-radius:14px;padding:18px 24px;font:500 22px/1.35 var(--mono);color:var(--ink)}
.proof::before{content:"IN PRODUCTION  ";color:var(--accent);font-weight:600;letter-spacing:.08em}
.foot{display:flex;justify-content:space-between;align-items:center;font-size:21px;color:var(--muted);border-top:1.5px solid var(--line);padding-top:18px}
.foot b{color:var(--ink);font-weight:800;font-size:23px}
/* stack */
.row{display:grid;grid-template-columns:250px 1fr;align-items:center;gap:20px;background:var(--card);border:1.5px solid var(--line);border-radius:16px;padding:20px 24px}
.row .n{font-weight:800;font-size:30px;display:flex;gap:14px;align-items:baseline}
.row .n i{font:500 20px var(--mono);color:var(--muted);font-style:normal}
.chips{display:flex;flex-wrap:wrap;gap:10px}
.chip{font:500 21px var(--mono);padding:8px 14px;border-radius:999px;border:1.5px solid var(--line);background:var(--paper)}
.hot{border-color:var(--accent);background:var(--soft)}
.hot .n,.hot .n i{color:var(--accent)}
.hot .chip{border-color:color-mix(in srgb,var(--accent) 45%,transparent);background:#fff}
/* flow */
.step{display:grid;grid-template-columns:84px 1fr;gap:24px;align-items:center;position:relative}
.dot{width:84px;height:84px;border-radius:50%;background:var(--ink);color:#fff;display:grid;place-items:center;font:600 26px var(--mono);z-index:1}
.step:not(:last-child)::after{content:"";position:absolute;left:41px;top:84px;height:calc(100% - 56px);width:2px;background:var(--line)}
.step .t{font-weight:800;font-size:36px}
.step .d{font-size:25px;color:var(--muted);margin-top:2px}
.step.hot .dot{background:var(--accent)}
.step.hot .t{color:var(--accent)}
.loop{align-self:flex-end;font:500 21px var(--mono);color:var(--accent)}
/* lanes */
.lanes{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;max-height:780px}
.lane{background:var(--card);border:1.5px solid var(--line);border-radius:18px;padding:26px 22px;display:flex;flex-direction:column;gap:16px}
.lane h3{margin:0;font-size:40px;font-weight:800}
.lane .r{font-size:23px;color:var(--muted);line-height:1.3;min-height:92px}
.lane ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:10px}
.lane li{font:500 22px var(--mono);padding:16px 14px;border-radius:10px;background:var(--paper);border:1.5px solid var(--line)}
.lane.hot{border-color:var(--accent);background:var(--soft)}
.lane.hot h3{color:var(--accent)}
.lane.hot li{background:#fff}
/* timeline */
.ph{display:grid;grid-template-columns:150px 1fr;gap:22px;background:var(--card);border:1.5px solid var(--line);border-radius:16px;padding:20px 24px;align-items:start}
.ph .days{font:600 24px var(--mono);color:var(--muted)}
.ph .days span{display:block;font:500 16px var(--mono);letter-spacing:.1em;margin-top:4px}
.ph h3{margin:0 0 10px;font-size:32px;font-weight:800}
.ph.hot{border-color:var(--accent);background:var(--soft)}
.ph.hot h3,.ph.hot .days{color:var(--accent)}
/* dashboard */
.dash{background:var(--card);border:1.5px solid var(--line);border-radius:22px;overflow:hidden;display:flex;flex-direction:column;flex:1}
.dhead{background:var(--accent);color:#fff;padding:22px 28px;display:flex;justify-content:space-between;align-items:center}
.dhead h2{margin:0;font-size:36px;font-weight:800}
.badge{font:600 18px var(--mono);letter-spacing:.12em;background:rgba(255,255,255,.18);padding:8px 14px;border-radius:999px;display:flex;gap:10px;align-items:center}
.pulse{width:12px;height:12px;border-radius:50%;background:#fff}
.dbody{padding:32px 30px;display:flex;flex-direction:column;justify-content:space-between;gap:26px;flex:1}
.big{display:flex;flex-direction:column;gap:6px}
.big .lab{font:500 20px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.big .num{font-size:176px;line-height:.95;font-weight:800;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.big .note{font-size:22px;color:var(--muted)}
.bars{display:flex;flex-direction:column;gap:20px}
.bar{display:grid;grid-template-columns:250px 1fr 130px;gap:16px;align-items:center;font:500 23px var(--mono)}
.track{height:46px;background:var(--paper);border-radius:8px;overflow:hidden}
.fill{height:100%;background:var(--accent);border-radius:8px;width:0}
.bar .v{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.tile{border:1.5px solid var(--line);border-radius:14px;padding:16px 18px;background:var(--paper)}
.tile .tv{font-size:58px;font-weight:800;color:var(--accent);font-variant-numeric:tabular-nums;line-height:1}
.tile .tl{font:500 17px var(--mono);color:var(--muted);margin-top:8px}
.cta{background:var(--ink);color:#fff;font:500 23px var(--mono);padding:20px 28px;text-align:center;letter-spacing:.02em}
"""
FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;800&family=IBM+Plex+Mono:wght@500;600&display=swap">'
e = html.escape


def chrome(n, total, title, sub, body, proof, author, tagline):
    return f"""<!doctype html><meta charset=utf-8>{FONTS}<style>{CSS}</style>
<div class="frame">
 <div class="top"><span>{e(author)} · <b>Systems I build</b></span><span>{n:02d} / {total:02d}</span></div>
 <h1>{e(title)}</h1>
 {f'<div class="sub">{e(sub)}</div>' if sub else ''}
 <div class="body">{body}</div>
 {f'<div class="proof">{e(proof)}</div>' if proof else ''}
 <div class="foot"><b>{e(author)}</b><span>{e(tagline)}</span></div>
</div>"""


def body_for(v):
    k = v["kind"]
    if k == "stack":
        return "".join(
            f'<div class="row{" hot" if r.get("accent") else ""}"><div class="n"><i>{i:02d}</i>{e(r["name"])}</div>'
            f'<div class="chips">{"".join(f"<span class=chip>{e(c)}</span>" for c in r["chips"])}</div></div>'
            for i, r in enumerate(v["rows"], 1))
    if k == "flow":
        s = "".join(
            f'<div class="step{" hot" if st.get("accent") else ""}"><div class="dot">{i:02d}</div>'
            f'<div><div class="t">{e(st["name"])}</div><div class="d">{e(st["note"])}</div></div></div>'
            for i, st in enumerate(v["steps"], 1))
        return s + (f'<div class="loop">↺ {e(v["loop"])}</div>' if v.get("loop") else "")
    if k == "lanes":
        return '<div class="lanes">' + "".join(
            f'<div class="lane{" hot" if l.get("accent") else ""}"><h3>{e(l["name"])}</h3><div class="r">{e(l["rule"])}</div>'
            f'<ul>{"".join(f"<li>{e(x)}</li>" for x in l["items"])}</ul></div>' for l in v["lanes"]) + "</div>"
    if k == "timeline":
        return "".join(
            f'<div class="ph{" hot" if p.get("accent") else ""}"><div class="days">{e(p["days"])}<span>DAYS</span></div>'
            f'<div><h3>{e(p["name"])}</h3><div class="chips">{"".join(f"<span class=chip>{e(x)}</span>" for x in p["items"])}</div></div></div>'
            for p in v["phases"])
    raise ValueError(k)


def live_numbers(v):
    """Fill the job-engine dashboard from the latest daily search."""
    if v.get("live") != "jobhunt":
        return v
    stats = json.loads((ROOT / "jobhunt/stats.json").read_text()) if (ROOT / "jobhunt/stats.json").exists() else {}
    seen = json.loads((ROOT / "jobhunt/seen.json").read_text())
    fits = [j.get("fit", 0) for j in seen.values() if j.get("status") == "new"]
    v = json.loads(json.dumps(v))
    v["counter"]["value"] = stats.get("roles_screened", v["counter"]["value"])
    v["counter"]["note"] = f"{stats.get('boards', 61)} company job boards · Greenhouse, Lever, Ashby APIs"
    v["bars"] = [["Fit 80+", sum(f >= 80 for f in fits)], ["Fit 70-79", sum(70 <= f < 80 for f in fits)], ["Fit 55-69", sum(55 <= f < 70 for f in fits)]]
    v["tiles"] = [["Job boards", stats.get("boards", 0)], ["Matched", stats.get("matched", len(fits))],
                  ["Strong fits", stats.get("strong_fits", sum(f >= 70 for f in fits))]]
    return v


def dashboard_page(v, n, total, author, tagline):
    v = live_numbers(v)
    bars = "".join(f'<div class="bar"><span>{e(l)}</span><div class="track"><div class="fill" id="b{i}"></div></div><span class="v" id="bv{i}">0</span></div>'
                   for i, (l, _) in enumerate(v["bars"]))
    tiles = "".join(f'<div class="tile"><div class="tv" id="t{i}">0</div><div class="tl">{e(l)}</div></div>' for i, (l, _) in enumerate(v["tiles"]))
    body = f"""<div class="dash">
 <div class="dhead"><h2>{e(v['title'])}</h2><span class="badge"><i class="pulse" id="pulse"></i>{e(v['badge'])}</span></div>
 <div class="dbody">
  <div class="big"><span class="lab">{e(v['counter']['label'])}</span><span class="num" id="num">0</span><span class="note">{e(v['counter'].get('note',''))}</span></div>
  <div class="bars">{bars}</div>
  <div class="tiles">{tiles}</div>
 </div>
 <div class="cta">{e(v['cta'])}</div>
</div>"""
    data = json.dumps({"num": v["counter"]["value"], "bars": [b[1] for b in v["bars"]], "tiles": [t[1] for t in v["tiles"]]})
    script = f"""<script>(() => {{
const D={data}, mx=Math.max(1,...D.bars);
const ease=x=>1-Math.pow(1-Math.min(1,Math.max(0,x)),3);
const fmt=n=>Math.round(n).toLocaleString('en-US');
window.frame=t=>{{
  document.getElementById('num').textContent=fmt(D.num*ease((t-.3)/2.9));
  D.bars.forEach((b,i)=>{{const p=ease((t-.6-i*.25)/1.6);document.getElementById('b'+i).style.width=(b/mx*100*p)+'%';document.getElementById('bv'+i).textContent=fmt(b*p)}});
  D.tiles.forEach((v,i)=>{{document.getElementById('t'+i).textContent=fmt(v*ease((t-1.2-i*.2)/2.2))}});
  document.getElementById('pulse').style.opacity=.45+.55*Math.abs(Math.cos(t*Math.PI));
}};
window.frame(99);
}})();</script>"""
    return chrome(n, total, v.get("headline", v["title"]), None, body, None, author, tagline).replace("<h1>", "<h1 style='display:none'>") + script


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(executable_path=glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0])


def main(only=None):
    from playwright.sync_api import sync_playwright
    d = json.loads((HERE / "series.json").read_text())
    posts, author, tagline = d["posts"], d["author"], d["tagline"]
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = launch(p)
        tab = b.new_page(viewport={"width": W, "height": H})
        for n, post in enumerate(posts, 1):
            if only and post["id"] not in only:
                continue
            v = post["visual"]
            still = post.get("diagram") if v["kind"] == "dashboard" else v
            tab.set_content(chrome(n, len(posts), still["title"], still.get("subtitle"), body_for(still), still.get("proof"), author, tagline), wait_until="networkidle")
            tab.screenshot(path=str(OUT / f"{post['id']}.png"))
            made = [f"{post['id']}.png"]
            if v["kind"] == "dashboard":
                tab.set_content(dashboard_page(v, n, len(posts), author, tagline), wait_until="networkidle")
                tab.evaluate("window.frame(99)")
                tab.screenshot(path=str(OUT / f"{post['id']}-final.png"))
                ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart",
                                       str(OUT / f"{post['id']}.mp4")], stdin=subprocess.PIPE)
                for f in range(FPS * SECONDS):
                    tab.evaluate(f"window.frame({f / FPS})")
                    ff.stdin.write(tab.screenshot(type="jpeg", quality=92))
                ff.stdin.close(); ff.wait()
                made += [f"{post['id']}.mp4", f"{post['id']}-final.png"]
            print(post["id"], "->", ", ".join(made))
        b.close()


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
