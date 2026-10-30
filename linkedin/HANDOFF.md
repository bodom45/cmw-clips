# Handoff: queue the "Systems I Build" series on the LinkedIn autoposter

For the Claude session that runs Brandon's LinkedIn autoposter in `~/area51poster` on his Mac
(launchd job `com.ctv.linkedin`, weekdays 8:20am and 12:35pm). Brandon asked for this series to post
automatically so he doesn't have to copy and paste anything.

## Source (public repo, no login needed)

- Posts: https://raw.githubusercontent.com/bodom45/cmw-clips/main/linkedin/series.json
  Each item in `posts` has `id` and `text` (final copy, post it exactly as written).
- Media: `https://raw.githubusercontent.com/bodom45/cmw-clips/main/linkedin/media/<file>`
  - Every post has an image: `<id>.png` (1080x1350).
  - Posts `02-gtm-loop`, `04-serverless-pipeline` and `05-explainable-scoring` also have a video: `<id>.mp4`
    (H.264, 1080x1350, 7 s). Use the video for those three; use the image for the rest.
- Review page Brandon has seen: https://claude.ai/artifact/3uT85nb95JjM4nNE5ikrJN

## Steps

1. **Token first.** Run `/opt/homebrew/bin/python3 linkedin_post.py --check`. The token was due to expire on
   2026-10-23. If it has expired or has 10 days or less, stop here and send a macOS notification telling Brandon to run
   `/opt/homebrew/bin/python3 linkedin_auth.py` from `~/area51poster` (it needs his browser login). Do not run it yourself.
2. **Download** `series.json` and the 14 media files into `~/area51poster/series/systems-i-build/`.
3. **Queue the 11 posts** in the poster's own queue format, in order `01` → `11`, *ahead* of the existing
   queue, so they go out next at the normal 2-per-weekday pace. Keep every existing queued post after them.
   Never post more than one per scheduled slot and never post them all at once.
4. **Media support.** If `linkedin_post.py` can't attach media yet, add it:
   - Images: Images API `initializeUpload` → `PUT` the bytes → put the image URN in the post's `content.media`.
   - Videos: Videos API `initializeUpload` (with `fileSizeBytes`) → upload each part → `finalizeUpload` →
     post with the video URN. Wait for the video to finish processing before publishing.
   - If media fails at post time, post the text alone rather than skipping the slot, and log it.
   - Don't publish a test post. Upload-only checks are fine.
5. **Report back** in this chat: what was queued, the date and time of the first new post, and any change
   made to `linkedin_post.py`.

Never edit or print the token, and never run `linkedin_auth.py` yourself.
