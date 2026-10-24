#!/usr/bin/env python3
"""Render a filled card or cauldron page to a PNG for sharing.

Usage:
  python scripts/render_png.py <page.html> <out.png> [--width 420] [--dark]

Needs Playwright with Chromium. If it is missing, try:
  pip install playwright --break-system-packages && python -m playwright install chromium
If that cannot run (no network for the browser download), skip the PNG and
share the page itself instead.
"""
import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=420)
    ap.add_argument("--dark", action="store_true", help="render with a dark color scheme")
    ap.add_argument("--wait", type=int, default=600, help="ms to wait for scripts and fonts")
    a = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("error: playwright is not installed (see the usage note)")
        return 1

    html = Path(a.page).read_text(encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": a.width, "height": 800},
            device_scale_factor=2,
            color_scheme="dark" if a.dark else "light",
            reduced_motion="reduce",
        )
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_content(html)
        page.wait_for_timeout(a.wait)
        target = page.query_selector(".rc") or page.query_selector(".cx") or page.query_selector("body")
        target.screenshot(path=a.out)
        browser.close()
    for e in errors:
        print(f"page error: {e}")
    print(f"wrote {a.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
