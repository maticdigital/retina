"""BuiltWith Domain API v21 client."""

from __future__ import annotations

import logging

from retina.clients.base import BaseAPIClient
from retina.config import Settings
from retina.utils.url import extract_domain

logger = logging.getLogger(__name__)


class BuiltWithClient(BaseAPIClient):
    """Client for BuiltWith Domain API v21.

    Detects technology stacks, frameworks, analytics tools, CDNs,
    and other technologies used by a website.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._base_url = settings.builtwith_base_url
        self._api_key = settings.builtwith_api_key

    async def lookup(self, url: str) -> dict:
        """Look up the technology profile for a domain.

        Args:
            url: The URL or domain to look up.

        Returns:
            Raw JSON response from the BuiltWith API.
        """
        domain = extract_domain(url)
        params = {
            "KEY": self._api_key,
            "LOOKUP": domain,
            "NOMETA": "no",
            "NOATTR": "no",
            "HIDETEXT": "no",
            "HIDEDL": "no",
        }

        logger.info("Looking up tech stack for %s...", domain)
        response = await self._request_with_retry("GET", self._base_url, params=params)
        logger.info("Completed tech stack lookup for %s", domain)
        return response.json()
