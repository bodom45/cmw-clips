#!/bin/bash
# Double-click to start. Opens each new job pre-filled; you solve the captcha and press Submit.
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is needed. Install it from https://www.python.org/downloads/ then double-click this again."
  read -p "Press Enter to close."; exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "First-time setup. This takes a few minutes, once."
  python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip playwright && .venv/bin/python -m playwright install chromium \
    || { echo "Setup failed. Send me the message above."; read -p "Press Enter to close."; exit 1; }
fi
echo "Getting today's job list..."
curl -fsSL https://raw.githubusercontent.com/bodom45/cmw-clips/main/jobhunt/seen.json -o seen.json.new && mv seen.json.new seen.json \
  || echo "Couldn't download today's list, using the last one."
.venv/bin/python apply_assist.py --min-fit 55 "$@"
read -p "All done. Press Enter to close."
