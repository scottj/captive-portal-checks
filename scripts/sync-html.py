#!/usr/bin/env python3
"""Sync captive_portal_check_urls.json into the embedded DATA object in index.html."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "captive_portal_check_urls.json"
HTML_PATH = ROOT / "index.html"

def main():
    data = JSON_PATH.read_text(encoding="utf-8")
    # Validate JSON
    json.loads(data)

    html = HTML_PATH.read_text(encoding="utf-8")

    # Match the DATA = { ... }; block
    pattern = re.compile(r"const DATA = \{.*?\n\};", re.DOTALL)
    match = pattern.search(html)
    if not match:
        print("ERROR: Could not find 'const DATA = { ... };' in index.html", file=sys.stderr)
        sys.exit(1)

    replacement = f"const DATA = {data.rstrip()};"
    updated = html[:match.start()] + replacement + html[match.end():]

    HTML_PATH.write_text(updated, encoding="utf-8")
    print(f"Synced {JSON_PATH.name} -> {HTML_PATH.name}")

if __name__ == "__main__":
    main()
