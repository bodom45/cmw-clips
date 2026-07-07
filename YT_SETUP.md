# YouTube Shorts automation — one-time setup (~10 min)

The poster (`yt_autopost.py` + hourly `yt-autopost` workflow) is already live in this
repo. It mirrors every schedule row whose `platforms` includes `YouTube` to the
channel, deduped in `posted_yt.json`. It fail-softs (posts nothing, stays green)
until the three secrets below exist.

## Steps (Brandon, one time)

1. **Google Cloud project** — console.cloud.google.com → New Project (name: `cmw-poster`).
2. **Enable API** — APIs & Services → Library → *YouTube Data API v3* → Enable.
3. **OAuth consent screen** — External → app name `cmw-poster`, your email → add scope
   `youtube.upload` → add yourself as a Test User → Save. (Publishing status can stay
   "Testing"; refresh tokens for test users expire after 7 days, so either click
   **Publish app** for a long-lived token, or expect to re-mint weekly. Publish is the move.)
4. **OAuth client** — Credentials → Create Credentials → OAuth client ID →
   type **Web application** → add redirect URI `http://localhost:8765/cb` → note
   CLIENT_ID + CLIENT_SECRET.
5. **Mint the refresh token** (from any folder with this repo cloned, or download the file):
   `python3 yt_get_token.py CLIENT_ID CLIENT_SECRET`
   → sign in with the Google account that owns the target channel → copy the printed token.
6. **Set the secrets:**
   ```
   gh secret set YT_CLIENT_ID     -R bodom45/cmw-clips
   gh secret set YT_CLIENT_SECRET -R bodom45/cmw-clips
   gh secret set YT_REFRESH_TOKEN -R bodom45/cmw-clips
   ```
7. Test one: Actions → yt-autopost → Run workflow (or wait for the :37 hourly run).

## Known caveats
- **Unverified-app private lock:** Google restricts uploads from unverified API
  projects to *private*. If Shorts land private, submit the **YouTube API audit form**
  (search "YouTube API Services audit form" — personal single-channel use is routinely
  approved) OR complete OAuth verification. Until then, private uploads can be flipped
  public in YT Studio in bulk (still beats manual uploading).
- **Quota:** default 10,000 units/day; one upload = 1,600 units → max ~6/day. Our cap
  is 3/run, 2/day scheduled — fine.
- **Which channel:** whatever Google account approves in step 5 owns the uploads.
  For a second channel (e.g. Area 51 Radio separate from CHACHAMAN), repeat steps 4–6
  with that account into secrets `YT2_*` and we'll add a second workflow.
