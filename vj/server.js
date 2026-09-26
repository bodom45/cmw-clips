#!/usr/bin/env node
// CMW Beat VJ — local server. No dependencies, just Node 18+.
//
//   node vj/server.js            -> http://localhost:8080
//
// - Serves the VJ page (vj/index.html) and every .mp4 in the repo root.
// - If Carabiner (Ableton Link bridge) is running, relays Serato's Link
//   tempo + beat to the page over Server-Sent Events at /link.

const http = require("http");
const net = require("net");
const fs = require("fs");
const path = require("path");

const PORT = Number(process.env.PORT) || 8080;
const CLIPS_DIR = path.resolve(process.env.CLIPS_DIR || path.join(__dirname, ".."));
const CARABINER_HOST = process.env.CARABINER_HOST || "127.0.0.1";
const CARABINER_PORT = Number(process.env.CARABINER_PORT) || 17000;

// ---------- Ableton Link via Carabiner ----------
// Carabiner speaks a line protocol on TCP 17000. We poll "status" and get
// back e.g.  status { :peers 1 :bpm 124.000000 :start 7374373 :beat 597.7375 }
let link = { connected: false, peers: 0, bpm: 0, beat: 0, t: 0 };
const listeners = new Set();

function broadcast() {
  const msg = `data: ${JSON.stringify(link)}\n\n`;
  for (const res of listeners) res.write(msg);
}

function connectCarabiner() {
  const sock = net.connect(CARABINER_PORT, CARABINER_HOST);
  let buf = "";
  let poll;
  sock.on("connect", () => {
    console.log(`[link] connected to Carabiner on ${CARABINER_HOST}:${CARABINER_PORT}`);
    poll = setInterval(() => sock.write("status\n"), 200);
  });
  sock.on("data", (chunk) => {
    buf += chunk.toString();
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line.startsWith("status")) continue;
      const num = (k) => {
        const m = line.match(new RegExp(`:${k}\\s+(-?[\\d.]+)`));
        return m ? Number(m[1]) : undefined;
      };
      link = {
        connected: true,
        peers: num("peers") ?? 0,
        bpm: num("bpm") ?? link.bpm,
        beat: num("beat") ?? link.beat,
        t: Date.now(),
      };
      broadcast();
    }
  });
  const retry = () => {
    clearInterval(poll);
    if (link.connected) console.log("[link] Carabiner disconnected");
    link = { ...link, connected: false, peers: 0 };
    broadcast();
    setTimeout(connectCarabiner, 3000);
  };
  sock.on("error", () => {});
  sock.on("close", retry);
}
connectCarabiner();

// ---------- HTTP ----------
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".mp4": "video/mp4",
  ".mov": "video/quicktime",
  ".webm": "video/webm",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
};

function listClips() {
  return fs
    .readdirSync(CLIPS_DIR)
    .filter((f) => /\.(mp4|mov|webm)$/i.test(f))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}

// Streams a file, honouring Range requests so <video> can seek.
function sendFile(req, res, file) {
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) {
      res.writeHead(404).end("not found");
      return;
    }
    const type = TYPES[path.extname(file).toLowerCase()] || "application/octet-stream";
    const range = req.headers.range && /bytes=(\d*)-(\d*)/.exec(req.headers.range);
    if (range) {
      const start = range[1] ? Number(range[1]) : 0;
      const end = range[2] ? Math.min(Number(range[2]), st.size - 1) : st.size - 1;
      res.writeHead(206, {
        "Content-Type": type,
        "Content-Range": `bytes ${start}-${end}/${st.size}`,
        "Accept-Ranges": "bytes",
        "Content-Length": end - start + 1,
      });
      fs.createReadStream(file, { start, end }).pipe(res);
    } else {
      res.writeHead(200, { "Content-Type": type, "Content-Length": st.size, "Accept-Ranges": "bytes" });
      fs.createReadStream(file).pipe(res);
    }
  });
}

http
  .createServer((req, res) => {
    const url = decodeURIComponent(new URL(req.url, "http://x").pathname);

    if (url === "/" || url === "/index.html") return sendFile(req, res, path.join(__dirname, "index.html"));

    if (url === "/clips.json") {
      res.writeHead(200, { "Content-Type": "application/json" });
      return res.end(JSON.stringify(listClips()));
    }

    if (url === "/link") {
      res.writeHead(200, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      });
      res.write(`data: ${JSON.stringify(link)}\n\n`);
      listeners.add(res);
      req.on("close", () => listeners.delete(res));
      return;
    }

    if (url.startsWith("/clips/")) {
      const name = path.basename(url.slice(7)); // basename blocks ../ traversal
      return sendFile(req, res, path.join(CLIPS_DIR, name));
    }

    res.writeHead(404).end("not found");
  })
  .listen(PORT, () => {
    console.log(`CMW Beat VJ  ->  http://localhost:${PORT}`);
    console.log(`Clips from   ->  ${CLIPS_DIR} (${listClips().length} found)`);
    console.log(`Link         ->  waiting for Carabiner on ${CARABINER_HOST}:${CARABINER_PORT} (optional)`);
  });
