#!/usr/bin/env python3
"""One-time helper: mint a YouTube refresh token for yt_autopost.

Run locally:  python3 yt_get_token.py CLIENT_ID CLIENT_SECRET
Opens the Google consent page; sign in with the Google account that owns the
target YouTube channel and approve. Prints the refresh token to store as the
YT_REFRESH_TOKEN repo secret. Stdlib only.
"""
import http.server, json, sys, threading, urllib.parse, urllib.request, webbrowser

CID, SEC = sys.argv[1], sys.argv[2]
PORT = 8765
REDIRECT = f"http://localhost:{PORT}/cb"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
code_holder = {}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_holder["code"] = q.get("code", [""])[0]
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Done - you can close this tab and return to the terminal.")

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("localhost", PORT), H)
threading.Thread(target=srv.handle_request, daemon=True).start()

auth = ("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": CID, "redirect_uri": REDIRECT, "response_type": "code",
    "scope": SCOPE, "access_type": "offline", "prompt": "consent"}))
print("Opening browser for consent...\n", auth)
webbrowser.open(auth)
while "code" not in code_holder:
    pass

data = urllib.parse.urlencode({
    "code": code_holder["code"], "client_id": CID, "client_secret": SEC,
    "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
with urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data) as r:
    tok = json.loads(r.read())
print("\nYT_REFRESH_TOKEN =", tok.get("refresh_token"))
print("\nStore it:  gh secret set YT_REFRESH_TOKEN -R bodom45/cmw-clips")
