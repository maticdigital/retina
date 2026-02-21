"""Google PageSpeed Insights API v5 client."""

from __future__ import annotations

import asyncio
import logging

from retina.clients.base import BaseAPIClient
from retina.config import Settings
from retina.models.normalized import DeviceStrategy

logger = logging.getLogger(__name__)

# Lighthouse categories to request
CATEGORIES = ["PERFORMANCE", "ACCESSIBILITY", "BEST_PRACTICES", "SEO"]


class PageSpeedClient(BaseAPIClient):
    """Client for Google PageSpeed Insights API v5.

    Analyzes URLs for performance, accessibility, best practices, and SEO
    using Google's Lighthouse engine.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._base_url = settings.pagespeed_base_url
        self._api_key = settings.pagespeed_api_key

    async def analyze(
        self,
        url: str,
        strategy: DeviceStrategy = DeviceStrategy.MOBILE,
    ) -> dict:
        """Run PageSpeed analysis for a single strategy.

        Args:
            url: The URL to analyze.
            strategy: Device strategy (mobile or desktop).

        Returns:
            Raw JSON response from the PageSpeed API.
        """
        params: list[tuple[str, str]] = [
            ("url", url),
            ("key", self._api_key),
            ("strategy", strategy.value.upper()),
        ]
        for category in CATEGORIES:
            params.append(("category", category))

        logger.info("Analyzing %s (%s)...", url, strategy.value)
        response = await self._request_with_retry("GET", self._base_url, params=params)
        logger.info("Completed %s (%s)", url, strategy.value)
        return response.json()

    async def analyze_both_strategies(self, url: str) -> dict[str, dict]:
        """Run analysis for both mobile and desktop in parallel.

        Args:
            url: The URL to analyze.

        Returns:
            Dict keyed by strategy name ("mobile", "desktop") with raw responses.
        """
        mobile, desktop = await asyncio.gather(
            self.analyze(url, DeviceStrategy.MOBILE),
            self.analyze(url, DeviceStrategy.DESKTOP),
        )
        return {"mobile": mobile, "desktop": desktop}
