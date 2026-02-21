"""Base API client with shared HTTP client, retry logic, and rate limiting."""

from __future__ import annotations

import asyncio
import logging

import httpx

from retina.config import Settings

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """Base class for all API clients.

    Provides a shared httpx.AsyncClient with exponential backoff retry.
    Retries on 5xx and transport errors; fails immediately on 4xx.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-initialize the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._settings.request_timeout),
                follow_redirects=True,
            )
        return self._client

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: object,
    ) -> httpx.Response:
        """Execute HTTP request with exponential backoff retry.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL.
            **kwargs: Additional arguments passed to httpx.request().

        Returns:
            httpx.Response on success.

        Raises:
            httpx.HTTPStatusError: On non-retryable HTTP errors (4xx).
            httpx.TransportError: After all retries exhausted.
        """
        client = await self._get_client()
        last_exception: Exception | None = None

        async with self._semaphore:
            for attempt in range(self._settings.max_retries):
                try:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError as e:
                    if e.response.status_code < 500:
                        logger.error(
                            "Non-retryable HTTP %d for %s: %s",
                            e.response.status_code,
                            url,
                            e.response.text[:200],
                        )
                        raise
                    last_exception = e
                    logger.warning(
                        "HTTP %d on attempt %d/%d for %s",
                        e.response.status_code,
                        attempt + 1,
                        self._settings.max_retries,
                        url,
                    )
                except httpx.TransportError as e:
                    last_exception = e
                    logger.warning(
                        "Transport error on attempt %d/%d for %s: %s",
                        attempt + 1,
                        self._settings.max_retries,
                        url,
                        str(e),
                    )

                if attempt < self._settings.max_retries - 1:
                    delay = self._settings.retry_delay * (2**attempt)
                    logger.info("Retrying in %.1fs...", delay)
                    await asyncio.sleep(delay)

        assert last_exception is not None
        raise last_exception

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
