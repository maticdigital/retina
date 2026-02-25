"""Standalone screenshot worker script.

Launched as a fully independent process by ScreenshotClient.
Reads args from a JSON file, captures screenshots, writes results to another JSON file.
"""

import json
import os
import sys
import time
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: _screenshot_worker.py <config.json>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    with open(config_path) as f:
        config = json.load(f)

    url = config["url"]
    full_path = config["full_path"]
    viewport_path = config["viewport_path"]
    timeout_s = config.get("timeout", 30)
    result_path = config["result_path"]
    result = {"full_page": None, "viewport": None}

    def attempt_capture(p, attempt_num=1):
        """Single capture attempt with fresh browser."""
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-extensions",
                "--disable-background-networking",
            ],
        )
        try:
            ctx = browser.new_context(viewport={"width": 1280, "height": 720})
            page = ctx.new_page()
            timeout_ms = timeout_s * 1000

            # Navigate with fallback strategies
            loaded = False
            for strategy in ["load", "domcontentloaded"]:
                try:
                    page.goto(url, wait_until=strategy, timeout=timeout_ms)
                    loaded = True
                    break
                except Exception as e:
                    print(f"Attempt {attempt_num}: {strategy} failed: {e}", file=sys.stderr)
                    try:
                        page.close()
                    except Exception:
                        pass
                    try:
                        ctx.close()
                    except Exception:
                        pass
                    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
                    page = ctx.new_page()

            if not loaded:
                print(f"Attempt {attempt_num}: navigation failed", file=sys.stderr)
                return False

            Path(full_path).parent.mkdir(parents=True, exist_ok=True)

            # Wait for page to render
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass  # Best-effort

            try:
                page.wait_for_timeout(2000)
            except Exception:
                pass

            # Dismiss overlays
            try:
                page.evaluate("""() => {
                    const sels = [
                        '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]',
                        '[class*="cookie"]', '[class*="consent"]', '[class*="banner"]',
                        '[id*="modal"]', '[id*="popup"]', '[id*="overlay"]',
                        '[id*="cookie"]', '[id*="consent"]',
                        '[role="dialog"]', '[aria-modal="true"]',
                    ];
                    for (const sel of sels) {
                        document.querySelectorAll(sel).forEach(el => {
                            const s = window.getComputedStyle(el);
                            if (s.position === 'fixed' || s.position === 'absolute') el.remove();
                        });
                    }
                    document.querySelectorAll('*').forEach(el => {
                        const s = window.getComputedStyle(el);
                        if (s.position === 'fixed' && parseInt(s.zIndex) > 999) el.remove();
                    });
                }""")
            except Exception:
                pass

            # Viewport screenshot
            try:
                page.screenshot(
                    path=viewport_path,
                    full_page=False,
                    animations="disabled",
                    timeout=10000,
                )
                result["viewport"] = viewport_path
            except Exception as e:
                print(f"Attempt {attempt_num}: viewport screenshot failed: {e}", file=sys.stderr)

            # Full-page screenshot (only if viewport succeeded)
            if result["viewport"]:
                try:
                    page.screenshot(
                        path=full_path,
                        full_page=True,
                        animations="disabled",
                        timeout=15000,
                    )
                    result["full_page"] = full_path
                except Exception:
                    pass  # Viewport is enough

            try:
                ctx.close()
            except Exception:
                pass
            return result["viewport"] is not None
        finally:
            try:
                browser.close()
            except Exception:
                pass

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            for i in range(3):
                if attempt_capture(p, i + 1):
                    break
                time.sleep(2)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)

    # Write result to file
    with open(result_path, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
