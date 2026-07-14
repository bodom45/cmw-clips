#!/usr/bin/env bash
# Render the CMW pitch deck (resume/cmw-pitch.html) to a landscape 16:9 PDF
# using the pre-installed Chromium (no extra deps). Page size comes from the
# HTML's `@page { size: 1280px 720px }` rule.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="$HERE/cmw-pitch.html"
OUT="$HERE/CMW-Brandon-Pitch.pdf"

# Locate a Chromium binary (Playwright's bundled build, else system).
CHROME=""
for c in \
  /opt/pw-browsers/chromium-1194/chrome-linux/chrome \
  "${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}"/chromium-*/chrome-linux/chrome \
  "$(command -v chromium || true)" \
  "$(command -v chromium-browser || true)" \
  "$(command -v google-chrome || true)"; do
  if [ -n "$c" ] && [ -x "$c" ]; then CHROME="$c"; break; fi
done
if [ -z "$CHROME" ]; then echo "No Chromium binary found." >&2; exit 1; fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Chromium: $CHROME"
"$CHROME" \
  --headless=new \
  --no-sandbox \
  --disable-gpu \
  --hide-scrollbars \
  --force-color-profile=srgb \
  --no-pdf-header-footer \
  --user-data-dir="$TMP" \
  --print-to-pdf="$OUT" \
  "file://$HTML"

echo "Wrote: $OUT"
