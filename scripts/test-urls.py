#!/usr/bin/env python3
"""Test each captive portal check URL and validate against expected responses."""

import json
import urllib.request
import urllib.error
import ssl
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
JSON_PATH = ROOT / "captive_portal_check_urls.json"
TIMEOUT = 10


def is_ssl_error(exc):
    """Check if an exception is caused by an SSL certificate error."""
    if isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, ssl.SSLCertVerificationError):
        return True
    return False


def test_url(url, expected, expect_ssl_error=False):
    """Fetch a URL and check the response against the expected value. Returns (pass, detail)."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "CaptivePortalCheck/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace").strip()

            # Check if expected is an HTTP status pattern
            if expected.startswith("HTTP "):
                if "204" in expected and status == 204:
                    return True, f"{status} No Content"
                if "200" in expected and status == 200:
                    return True, f"{status} OK"
                return False, f"Got {status}, expected {expected}"

            # Otherwise match body content
            if expected in body:
                return True, f"{status}, body matches"
            return False, f"{status}, body mismatch (got {len(body)} chars: {body[:80]!r})"

    except urllib.error.HTTPError as e:
        if "204" in expected and e.code == 204:
            return True, f"{e.code} No Content"
        return False, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        if expect_ssl_error and url.startswith("https") and is_ssl_error(e):
            return True, f"SSL error (expected): {e.reason}"
        return False, f"URL error: {e.reason}"
    except TimeoutError:
        return False, "Timeout"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    entries = data["captive_portal_check_urls"]

    total = 0
    passed = 0
    failed = 0
    failures = []

    for entry in entries:
        vendor = entry["vendor"]
        expected = entry["expected_response"]
        expect_ssl_error = entry.get("expect_ssl_error", False)
        print(f"\n{'─' * 60}")
        print(f"  {vendor}  ({entry['os']})")
        print(f"  Expected: {expected}")
        if expect_ssl_error:
            print(f"  Note: SSL errors expected on HTTPS URLs")
        print(f"{'─' * 60}")

        for url in entry["urls"]:
            total += 1
            ok, detail = test_url(url, expected, expect_ssl_error)
            status = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
                print(f"  ✓  {url}")
                print(f"     {detail}")
            else:
                failed += 1
                failures.append((vendor, url, detail))
                print(f"  ✗  {url}")
                print(f"     {detail}")

    print(f"\n{'═' * 60}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'═' * 60}")

    if failures:
        print(f"\n  Failed URLs:")
        for vendor, url, detail in failures:
            print(f"    [{vendor}] {url}")
            print(f"      {detail}")


if __name__ == "__main__":
    main()
