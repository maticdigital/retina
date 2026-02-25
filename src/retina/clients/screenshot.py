"""Playwright-based screenshot capture client.

Captures full-page and viewport-only (above-the-fold) screenshots for
analyzed URLs. Runs independently of HTTP-based API clients since
Playwright manages its own browser instance.

When running inside a background thread (e.g., FastAPI BackgroundTasks),
Playwright's browser process can crash due to event loop issues. In that
case, the client falls back to running capture in a subprocess.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from retina.config import Settings
from retina.models.normalized import ScreenshotData

logger = logging.getLogger(__name__)

# Default viewport dimensions (standard desktop)
DEFAULT_VIEWPORT = {"width": 1280, "height": 720}


class ScreenshotClient:
    """Captures full-page and viewport screenshots using Playwright.

    Unlike the HTTP-based API clients, this uses a headless Chromium browser.
    A fresh browser context is created per capture for isolation.

    If in-process capture fails with a page crash (common in background
    threads), automatically falls back to subprocess-based capture.

    Usage:
        client = ScreenshotClient(settings)
        data = await client.capture("https://example.com", "example.com")
        await client.close()
    """

    def __init__(self, settings: Settings, *, use_subprocess: bool = False) -> None:
        self._settings = settings
        self._output_dir = Path(settings.screenshots_dir)
        self._playwright: object | None = None
        self._browser: object | None = None
        self._use_subprocess = use_subprocess  # True for background thread usage

    async def _ensure_browser(self) -> None:
        """Lazy-initialize Playwright and launch Chromium."""
        if self._browser is not None:
            return

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            logger.info("Playwright browser launched")
        except Exception as e:
            logger.warning(
                "Could not launch Playwright browser: %s. "
                "Run 'playwright install chromium' to enable screenshots.",
                e,
            )
            raise

    async def capture(self, url: str, domain: str) -> ScreenshotData:
        """Capture full-page and viewport screenshots for a URL.

        Args:
            url: The URL to screenshot.
            domain: Domain name used for file naming.

        Returns:
            ScreenshotData with paths to both screenshots.
            Paths may be None if capture failed for that type.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Clean domain for filename (remove port, special chars)
        safe_domain = domain.replace(":", "_").replace("/", "_")
        full_path = self._output_dir / f"{safe_domain}_full.png"
        viewport_path = self._output_dir / f"{safe_domain}_viewport.png"

        # Subprocess mode: run capture in a separate process (crash-proof)
        if self._use_subprocess:
            return await self._capture_subprocess_async(url, domain, full_path, viewport_path)

        # In-process mode (for CLI usage)
        try:
            result = await self._capture_in_process(url, full_path, viewport_path)
            if result.viewport or result.full_page:
                return result
            logger.info("In-process capture returned empty for %s, trying subprocess", url)
            return await asyncio.get_event_loop().run_in_executor(
                None, self._capture_subprocess, url, domain, full_path, viewport_path,
            )
        except _PageCrashedError:
            logger.warning(
                "Page crashed in-process for %s, switching to subprocess mode", url
            )
            self._use_subprocess = True
            return await asyncio.get_event_loop().run_in_executor(
                None, self._capture_subprocess, url, domain, full_path, viewport_path,
            )
        except Exception as e:
            logger.warning("In-process capture failed for %s: %s, trying subprocess", url, e)
            return await asyncio.get_event_loop().run_in_executor(
                None, self._capture_subprocess, url, domain, full_path, viewport_path,
            )

    async def _capture_in_process(
        self, url: str, full_path: Path, viewport_path: Path,
    ) -> ScreenshotData:
        """Attempt capture using in-process Playwright."""
        result = ScreenshotData()

        try:
            await self._ensure_browser()
        except Exception:
            raise

        # Use a fresh context per capture for memory isolation
        context = await self._browser.new_context(viewport=DEFAULT_VIEWPORT)
        page = await context.new_page()

        try:
            loaded = await self._navigate_with_fallback(page, url)
            if not loaded:
                await context.close()
                return result

            await self._dismiss_overlays(page)

            try:
                await page.wait_for_timeout(1500)
            except Exception:
                pass

            # Full-page screenshot
            try:
                await page.screenshot(path=str(full_path), full_page=True)
                result.full_page = str(full_path)
                logger.info("Full-page screenshot: %s", full_path)
            except Exception as e:
                if "crash" in str(e).lower():
                    raise _PageCrashedError(str(e)) from e
                logger.warning("Full-page screenshot failed for %s: %s", url, e)

            # Viewport screenshot
            try:
                await page.screenshot(path=str(viewport_path), full_page=False)
                result.viewport = str(viewport_path)
                logger.info("Viewport screenshot: %s", viewport_path)
            except Exception as e:
                if "crash" in str(e).lower():
                    raise _PageCrashedError(str(e)) from e
                logger.warning("Viewport screenshot failed for %s: %s", url, e)

            await context.close()

        except _PageCrashedError:
            try:
                await context.close()
            except Exception:
                pass
            raise
        except Exception as e:
            try:
                await context.close()
            except Exception:
                pass
            if "crash" in str(e).lower():
                raise _PageCrashedError(str(e)) from e
            raise

        return result

    async def _capture_subprocess_async(
        self, url: str, domain: str, full_path: Path, viewport_path: Path,
    ) -> ScreenshotData:
        """Run screenshot capture using a standalone worker script.

        Uses a permanent worker script file and communicates via JSON config/result
        files, with Popen + async polling. This approach is more reliable than
        inline script templates when launched from within a server process.
        """
        import tempfile
        import time

        result = ScreenshotData()
        worker_script = Path(__file__).parent / "_screenshot_worker.py"

        if not worker_script.exists():
            logger.error("Screenshot worker script not found: %s", worker_script)
            return result

        # Create config file for the worker
        config = {
            "url": url,
            "full_path": str(full_path),
            "viewport_path": str(viewport_path),
            "timeout": self._settings.screenshot_timeout,
            "result_path": None,  # Will be set below
        }

        try:
            # Create temp files for config and result
            config_fd, config_path = tempfile.mkstemp(suffix=".json", prefix="ss_config_")
            result_fd, result_path = tempfile.mkstemp(suffix=".json", prefix="ss_result_")
            os.close(config_fd)
            os.close(result_fd)

            config["result_path"] = result_path
            with open(config_path, "w") as f:
                json.dump(config, f)

            timeout_secs = self._settings.screenshot_timeout * 2 + 30

            proc = subprocess.Popen(
                [sys.executable, str(worker_script), config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path.cwd()),
                start_new_session=True,
            )

            start = time.monotonic()
            while proc.poll() is None:
                if time.monotonic() - start > timeout_secs:
                    proc.kill()
                    proc.wait()
                    logger.warning("Screenshot worker timed out for %s", url)
                    self._cleanup_temps(config_path, result_path)
                    return result
                await asyncio.sleep(0.5)

            stderr_bytes = proc.stderr.read() if proc.stderr else b""
            stderr_text = stderr_bytes.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                logger.warning(
                    "Screenshot worker failed for %s (exit %d): %s",
                    url, proc.returncode, stderr_text[-500:] if stderr_text else "",
                )
                self._cleanup_temps(config_path, result_path)
                return result

            # Read result from file
            try:
                with open(result_path) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning("Screenshot worker result invalid for %s: %s", url, e)
                self._cleanup_temps(config_path, result_path)
                return result

            if data.get("full_page"):
                result.full_page = data["full_page"]
            if data.get("viewport"):
                result.viewport = data["viewport"]

            if not result.full_page and not result.viewport:
                logger.warning(
                    "Screenshot worker returned no screenshots for %s. stderr=%s",
                    url, stderr_text[:500] if stderr_text else "(empty)",
                )
            else:
                logger.info(
                    "Screenshot worker for %s: full=%s viewport=%s",
                    url, result.full_page, result.viewport,
                )

            self._cleanup_temps(config_path, result_path)

        except Exception as e:
            logger.warning("Screenshot worker error for %s: %s", url, e)

        return result

    @staticmethod
    def _cleanup_temps(*paths: str) -> None:
        for p in paths:
            try:
                os.unlink(p)
            except OSError:
                pass

    def _capture_subprocess(
        self, url: str, domain: str, full_path: Path, viewport_path: Path,
    ) -> ScreenshotData:
        """Synchronous subprocess capture (legacy, used by run_in_executor)."""
        result = ScreenshotData()

        script = _SUBPROCESS_SCRIPT.format(
            url=url,
            full_path=str(full_path),
            viewport_path=str(viewport_path),
            timeout=self._settings.screenshot_timeout,
        )

        try:
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, dir=str(Path.cwd()),
            ) as tmp:
                tmp.write(script)
                script_path = tmp.name

            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=self._settings.screenshot_timeout * 2 + 30,
                cwd=str(Path.cwd()),
                start_new_session=True,
            )

            try:
                os.unlink(script_path)
            except OSError:
                pass

            if proc.returncode == 0:
                try:
                    data = json.loads(proc.stdout.strip())
                except json.JSONDecodeError:
                    logger.warning("Subprocess returned invalid JSON for %s: %s", url, proc.stdout[:200])
                    return result

                if data.get("full_page"):
                    result.full_page = data["full_page"]
                if data.get("viewport"):
                    result.viewport = data["viewport"]

                if not result.full_page and not result.viewport:
                    logger.warning(
                        "Subprocess returned no screenshots for %s. stderr=%s",
                        url, proc.stderr[:500] if proc.stderr else "(empty)",
                    )
                else:
                    logger.info(
                        "Subprocess screenshot for %s: full=%s viewport=%s",
                        url, result.full_page, result.viewport,
                    )
            else:
                logger.warning(
                    "Subprocess screenshot failed for %s (exit %d): %s",
                    url, proc.returncode, proc.stderr[-500:] if proc.stderr else "",
                )
        except subprocess.TimeoutExpired:
            logger.warning("Subprocess screenshot timed out for %s", url)
        except Exception as e:
            logger.warning("Subprocess screenshot error for %s: %s", url, e)

        return result

    async def _navigate_with_fallback(self, page: object, url: str) -> bool:
        """Navigate to URL, trying multiple strategies."""
        timeout_ms = self._settings.screenshot_timeout * 1000

        strategies = ["networkidle", "load", "domcontentloaded"]
        for i, strategy in enumerate(strategies):
            try:
                await page.goto(url, wait_until=strategy, timeout=timeout_ms)
                if i > 0:
                    logger.info("Navigation succeeded with '%s' for %s", strategy, url)
                return True
            except Exception as e:
                err_str = str(e)
                if "crash" in err_str.lower():
                    raise _PageCrashedError(err_str) from e
                if i < len(strategies) - 1:
                    logger.warning(
                        "%s strategy failed for %s, trying %s: %s",
                        strategy, url, strategies[i + 1], e,
                    )
                else:
                    logger.warning("All navigation strategies failed for %s: %s", url, e)

        return False

    @staticmethod
    async def _dismiss_overlays(page: object) -> None:
        """Best-effort removal of common popups, cookie banners, and overlays."""
        try:
            await page.evaluate("""
                () => {
                    const selectors = [
                        '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]',
                        '[class*="cookie"]', '[class*="consent"]', '[class*="banner"]',
                        '[id*="modal"]', '[id*="popup"]', '[id*="overlay"]',
                        '[id*="cookie"]', '[id*="consent"]',
                        '[role="dialog"]', '[aria-modal="true"]',
                    ];
                    for (const sel of selectors) {
                        document.querySelectorAll(sel).forEach(el => {
                            const style = window.getComputedStyle(el);
                            if (style.position === 'fixed' || style.position === 'absolute') {
                                el.remove();
                            }
                        });
                    }
                    document.querySelectorAll('*').forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.position === 'fixed' && style.zIndex > 999) {
                            el.remove();
                        }
                    });
                }
            """)
        except Exception:
            pass

    async def close(self) -> None:
        """Shut down the Playwright browser and instance."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None


class _PageCrashedError(Exception):
    """Internal signal that a Playwright page/context crashed."""


# Script run in a subprocess for crash-proof screenshot capture.
# Uses sync Playwright API for simplicity in a standalone process.
_SUBPROCESS_SCRIPT = '''
import json, sys, time
from pathlib import Path

url = "{url}"
full_path = "{full_path}"
viewport_path = "{viewport_path}"
timeout_s = {timeout}
result = {{"full_page": None, "viewport": None}}

def attempt_capture(p, attempt_num=1):
    """Single attempt: launch browser, navigate, screenshot, close."""
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
        ctx = browser.new_context(viewport={{"width": 1280, "height": 720}})
        page = ctx.new_page()
        timeout_ms = timeout_s * 1000

        # Navigate
        loaded = False
        for strategy in ["load", "domcontentloaded"]:
            try:
                page.goto(url, wait_until=strategy, timeout=timeout_ms)
                loaded = True
                break
            except Exception:
                try:
                    page.close()
                except Exception:
                    pass
                try:
                    ctx.close()
                except Exception:
                    pass
                ctx = browser.new_context(viewport={{"width": 1280, "height": 720}})
                page = ctx.new_page()

        if not loaded:
            print(f"Attempt {{attempt_num}}: navigation failed", file=sys.stderr)
            return False

        Path(full_path).parent.mkdir(parents=True, exist_ok=True)

        # Wait for page to actually render content before screenshotting.
        # networkidle may timeout on heavy sites — that's fine, we still proceed.
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass  # Best-effort; page may still be loading assets

        # Brief pause for paint/render after load
        try:
            page.wait_for_timeout(2000)
        except Exception:
            pass

        # Dismiss common overlays (cookie banners, modals) before capture
        try:
            page.evaluate("""() => {{
                const sels = [
                    '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]',
                    '[class*="cookie"]', '[class*="consent"]', '[class*="banner"]',
                    '[id*="modal"]', '[id*="popup"]', '[id*="overlay"]',
                    '[id*="cookie"]', '[id*="consent"]',
                    '[role="dialog"]', '[aria-modal="true"]',
                ];
                for (const sel of sels) {{
                    document.querySelectorAll(sel).forEach(el => {{
                        const s = window.getComputedStyle(el);
                        if (s.position === 'fixed' || s.position === 'absolute') el.remove();
                    }});
                }}
                document.querySelectorAll('*').forEach(el => {{
                    const s = window.getComputedStyle(el);
                    if (s.position === 'fixed' && parseInt(s.zIndex) > 999) el.remove();
                }});
            }}""")
        except Exception:
            pass

        try:
            page.screenshot(
                path=viewport_path,
                full_page=False,
                animations="disabled",
                timeout=10000,
            )
            result["viewport"] = viewport_path
        except Exception as e:
            print(f"Attempt {{attempt_num}}: viewport screenshot failed: {{e}}", file=sys.stderr)

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
        # Up to 3 attempts with completely fresh browsers
        for i in range(3):
            if attempt_capture(p, i + 1):
                break
            time.sleep(2)  # Brief pause between retries
except Exception as e:
    print(f"Fatal error: {{e}}", file=sys.stderr)

print(json.dumps(result))
'''
