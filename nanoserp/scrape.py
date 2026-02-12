"""
Scrape a webpage and return its content as markdown with extracted links.
"""

import re

import httpx
from markdownify import markdownify

from nanoserp.exceptions import NanoserpError, RateLimitError, ServiceUnavailableError
from nanoserp.models import ScrapeLink, ScrapeResponse

_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/18.5 Mobile/15E148 Safari/604.1"
)

_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def _extract_links(markdown: str) -> list[ScrapeLink]:
    """Extract all markdown links, skipping image-only links."""
    links: list[ScrapeLink] = []
    seen: set[tuple[str, str]] = set()

    for text, url in _LINK_PATTERN.findall(markdown):
        # Skip image-only links like [![](img)](url)
        if not text or text.startswith("!"):
            continue
        key = (text, url)
        if key in seen:
            continue
        seen.add(key)
        links.append(ScrapeLink(text=text, url=url))

    return links


def scrape(url: str, *, timeout: float = 10.0) -> ScrapeResponse:
    """Fetch a webpage and return its content as markdown with extracted links.

    Args:
        url: The URL to scrape.
        timeout: HTTP request timeout in seconds.

    Returns:
        A ScrapeResponse containing the markdown content and all links found.

    Raises:
        RateLimitError: If the server returns a 429 status.
        ServiceUnavailableError: If the server returns 503 or the request times out.
        NanoserpError: For other HTTP errors.
    """
    headers = {"User-Agent": _USER_AGENT}

    try:
        response = httpx.get(
            url, headers=headers, timeout=timeout, follow_redirects=True
        )
    except httpx.TimeoutException as e:
        raise ServiceUnavailableError(f"Request timed out: {e}") from e

    if response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    if response.status_code == 503:
        raise ServiceUnavailableError("Service unavailable")
    if response.status_code >= 400:
        raise NanoserpError(f"HTTP {response.status_code}")

    md: str = markdownify(response.text)
    links = _extract_links(md)

    return ScrapeResponse(url=url, markdown=md, links=links)
