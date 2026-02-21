"""URL validation and normalization utilities."""

from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Ensure URL has scheme, strip trailing slash, lowercase host.

    Args:
        url: Raw URL string, with or without scheme.

    Returns:
        Normalized URL with https scheme, lowercase host, no trailing slash.
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    host = parsed.hostname.lower() if parsed.hostname else ""
    path = parsed.path.rstrip("/") or ""
    return f"{parsed.scheme}://{host}{path}"


def extract_domain(url: str) -> str:
    """Extract bare domain from URL.

    Args:
        url: Any URL string.

    Returns:
        Lowercase domain without scheme or path.
    """
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    return parsed.hostname or ""
