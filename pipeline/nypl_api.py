#!/usr/bin/env python3
"""Minimal client for the NYPL Digital Collections API (api.repo.nypl.org).

The API needs a personal token (free; sign up at https://api.repo.nypl.org/sign_up,
the token arrives by email). It is read from, in order:

  1. the NYPL_API_TOKEN environment variable
  2. pipeline/.nypl_token (one line; gitignored, never commit it)

Check that the token works (prints counts only, never the token):

    python nypl_api.py --check

Limits: 10,000 requests a day per token. This client pauses between requests.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.repo.nypl.org/api/v2"
TOKEN_FILE = Path(__file__).resolve().parent / ".nypl_token"
USER_AGENT = "chicago-menu-time-machine-pipeline/0.1 (historical menu research script)"
PAUSE = 1.0


def token() -> str:
    value = os.environ.get("NYPL_API_TOKEN", "").strip()
    if not value and TOKEN_FILE.exists():
        value = TOKEN_FILE.read_text().strip()
    if not value:
        raise SystemExit(
            "No NYPL API token. Sign up at https://api.repo.nypl.org/sign_up, then put the emailed token in "
            f"{TOKEN_FILE} (one line) or the NYPL_API_TOKEN environment variable."
        )
    return value


def get(path: str, **params) -> dict:
    """GET an API path (e.g. "items/search") and return the decoded 'nyplAPI' response."""
    time.sleep(PAUSE)
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "Authorization": f'Token token="{token()}"',
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)["nyplAPI"]
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise SystemExit("NYPL API refused the token (HTTP 401). Check it was copied in full.") from None
        raise


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true", help="make one search to confirm the token works")
    args = p.parse_args()
    if not args.check:
        p.print_help()
        return 0
    data = get("items/search", q="chicago menu", publicDomainOnly="true", per_page=5)
    total = data.get("response", {}).get("numResults", "?")
    source = "NYPL_API_TOKEN" if os.environ.get("NYPL_API_TOKEN") else TOKEN_FILE.name
    print(f"Token OK (from {source}). Public-domain items matching 'chicago menu': {total}")
    results = data.get("response", {}).get("result") or []
    for item in (results if isinstance(results, list) else [results])[:5]:
        print(f"  {item.get('title', '')[:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
