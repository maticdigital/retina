"""Playwright-based screenshot capture client.

Captures full-page and viewport-only (above-the-fold) screenshots for
analyzed URLs. Runs independently of HTTP-based API clients since
Playwright manages its own browser instance.
"""

from __future__ import annotations

import logging
from pathlib import Path

from retina.config import Settings
from retina.models.normalized import ScreenshotData

logger = logging.getLogger(__name__)

# Default viewport dimensions (standard desktop)
DEFAULT_VIEWPORT = {"width": 1280, "height": 720}


class ScreenshotClient:
    """Captures full-page and viewport screenshots using Playwright.

    Unlike the HTTP-based API clients, this uses a headless Chromium browser.
    The browser is lazily initialized on first use and shared across captures.

    Usage:
        client = ScreenshotClient(settings)
        data = await client.capture("https://example.com", "example.com")
        await client.close()
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._output_dir = Path(settings.screenshots_dir)
        self._playwright: object | None = None
        self._browser: object | None = None

    async def _ensure_browser(self) -> None:
        """Lazy-initialize Playwright and launch Chromium.

        Imports Playwright only when actually needed, so the rest of Retina
        works even if Playwright browsers aren't installed.
        """
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

        result = ScreenshotData()

        try:
            await self._ensure_browser()
        except Exception:
            return result  # Browser failed to launch; return empty

        try:
            page = await self._browser.new_page(viewport=DEFAULT_VIEWPORT)

            # Navigate with networkidle, fall back to load event
            loaded = await self._navigate_with_fallback(page, url)
            if not loaded:
                await page.close()
                return result

            # Best-effort popup/overlay dismissal
            await self._dismiss_overlays(page)

            # Small pause for animations to settle
            try:
                await page.wait_for_timeout(1000)
            except Exception:
                pass

            # Full-page screenshot
            try:
                await page.screenshot(path=str(full_path), full_page=True)
                result.full_page = str(full_path)
                logger.info("Full-page screenshot: %s", full_path)
            except Exception as e:
                logger.warning("Full-page screenshot failed for %s: %s", url, e)

            # Viewport-only (above the fold) screenshot
            try:
                await page.screenshot(path=str(viewport_path), full_page=False)
                result.viewport = str(viewport_path)
                logger.info("Viewport screenshot: %s", viewport_path)
            except Exception as e:
                logger.warning("Viewport screenshot failed for %s: %s", url, e)

            await page.close()

        except Exception as e:
            logger.warning("Screenshot capture failed for %s: %s", url, e)

        return result

    async def _navigate_with_fallback(self, page: object, url: str) -> bool:
        """Navigate to URL, trying networkidle first, then load event.

        Returns True if navigation succeeded, False otherwise.
        """
        timeout_ms = self._settings.screenshot_timeout * 1000

        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            return True
        except Exception as e:
            logger.warning("networkidle timeout for %s, trying load event: %s", url, e)

        try:
            await page.goto(url, wait_until="load", timeout=timeout_ms)
            return True
        except Exception as e:
            logger.warning("Page load failed for %s: %s", url, e)
            return False

    @staticmethod
    async def _dismiss_overlays(page: object) -> None:
        """Best-effort removal of common popups, cookie banners, and overlays."""
        try:
            await page.evaluate("""
                () => {
                    // Remove elements matching common overlay patterns
                    const selectors = [
                        '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]',
                        '[class*="cookie"]', '[class*="consent"]', '[class*="banner"]',
                        '[id*="modal"]', '[id*="popup"]', '[id*="overlay"]',
                        '[id*="cookie"]', '[id*="consent"]',
                        '[role="dialog"]', '[aria-modal="true"]',
                    ];
                    for (const sel of selectors) {
                        document.querySelectorAll(sel).forEach(el => {
                            // Only remove if it looks like a floating overlay
                            const style = window.getComputedStyle(el);
                            if (style.position === 'fixed' || style.position === 'absolute') {
                                el.remove();
                            }
                        });
                    }
                    // Also remove any fixed-position elements that cover the viewport
                    document.querySelectorAll('*').forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.position === 'fixed' && style.zIndex > 999) {
                            el.remove();
                        }
                    });
                }
            """)
        except Exception:
            pass  # Non-critical — some sites may block JS evaluation

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
