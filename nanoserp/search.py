"""
Search function that queries DuckDuckGo's HTML endpoint and parses results
into structured Pydantic models.
"""

import re
from datetime import datetime

import httpx
from markdownify import markdownify

from nanoserp.exceptions import NanoserpError, RateLimitError, ServiceUnavailableError
from nanoserp.models import DateFilter, SearchResponse, SearchResult

_BASE_URL = "https://html.duckduckgo.com/html"
_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/18.5 Mobile/15E148 Safari/604.1"
)
_HEADER_SEPARATOR = "Any Time\nPast Day\nPast Week\nPast Month\nPast Year"
_FOOTER_SUFFIX = (
    "\n\n[Feedback](//duckduckgo.com/feedback.html)\n\n![](//duckduckgo.com/t/sl_h)"
)

_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
_DATE_PATTERN = re.compile(r"^\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)\s*$")
_HR_PATTERN = re.compile(r"^-{3,}$", re.MULTILINE)
_VQD_PATTERN = re.compile(r'name="vqd"\s+value="([^"]+)"')

_DATE_FILTER_MAP: dict[DateFilter, str] = {
    DateFilter.DAY: "d",
    DateFilter.WEEK: "w",
    DateFilter.MONTH: "m",
    DateFilter.YEAR: "y",
}


def _parse_date(date_str: str) -> datetime:
    """Parse a DDG date string, truncating fractional seconds to 6 digits."""
    if "." in date_str:
        base, frac = date_str.split(".", 1)
        frac = frac[:6]
        date_str = f"{base}.{frac}"
    return datetime.fromisoformat(date_str)


def _extract_vqd(html: str) -> str | None:
    """Extract the vqd session token from DuckDuckGo HTML."""
    match = _VQD_PATTERN.search(html)
    return match.group(1) if match else None


def _check_status(response: httpx.Response) -> None:
    """Raise appropriate exceptions for HTTP error status codes."""
    if response.status_code == 429:
        raise RateLimitError("DuckDuckGo rate limit exceeded")
    if response.status_code == 503:
        raise ServiceUnavailableError("DuckDuckGo service unavailable")
    if response.status_code >= 400:
        raise NanoserpError(f"DuckDuckGo returned HTTP {response.status_code}")


def _extract_body(body_block: str) -> tuple[datetime | None, str]:
    """Extract date and snippet from a result body block."""
    date: datetime | None = None
    snippet_parts: list[str] = []

    for line in body_block.split("\n"):
        date_match = _DATE_PATTERN.match(line)
        if date_match:
            date = _parse_date(date_match.group(1))
            continue

        stripped = line.strip()
        if not stripped:
            continue

        link_match = _LINK_PATTERN.search(stripped)
        if link_match:
            link_text = link_match.group(1)
            # Skip icon links (empty text or image-only)
            if not link_text or link_text.startswith("!"):
                continue
            # Skip display URL links (text looks like a URL)
            if link_text.startswith("http") or "." in link_text.split("/")[0]:
                # But keep it if it's actually a snippet (long descriptive text)
                if len(link_text) > 100 or " " in link_text:
                    snippet_parts.append(link_text)
                continue
            snippet_parts.append(link_text)
        else:
            snippet_parts.append(stripped)

    return date, " ".join(snippet_parts).strip()


def _parse_results(markdown: str) -> list[SearchResult]:
    """Parse cleaned DuckDuckGo markdown into SearchResult objects.

    The markdown structure for each result is:
        [Title](url)
        ---+
        body (icon, display URL, optional date, snippet)

    When split on HR lines, we get:
        parts[0] = Title 1
        parts[1] = Body 1 ... Title 2
        parts[2] = Body 2 ... Title 3
        ...
        parts[N] = Body N (no trailing title)

    We extract the title from the end of each part (last link), and the body
    from the beginning of the next part (everything before the last link line).
    """
    parts = _HR_PATTERN.split(markdown)

    if len(parts) < 2:
        return []

    titles: list[tuple[str, str]] = []
    bodies: list[str] = []

    # Extract title from parts[0]
    first_links = _LINK_PATTERN.findall(parts[0].strip())
    if first_links:
        title_text, title_url = first_links[-1]
        if title_text and title_url:
            titles.append((title_text, title_url))

    # For parts[1..N-1], split into body (top) + next title (bottom)
    for i in range(1, len(parts)):
        block = parts[i].strip()
        lines = block.split("\n")

        if i < len(parts) - 1:
            # Find the last link line to use as the next title
            title_line_idx = None
            for j in range(len(lines) - 1, -1, -1):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                link_match = _LINK_PATTERN.search(stripped)
                if link_match:
                    link_text = link_match.group(1)
                    if link_text and " " in link_text:
                        title_line_idx = j
                    break

            if title_line_idx is not None:
                body_text = "\n".join(lines[:title_line_idx])
                title_link = _LINK_PATTERN.search(lines[title_line_idx].strip())
                if title_link:
                    titles.append((title_link.group(1), title_link.group(2)))
            else:
                body_text = block
        else:
            body_text = block

        bodies.append(body_text)

    results: list[SearchResult] = []
    for idx in range(min(len(titles), len(bodies))):
        title, url = titles[idx]
        date, snippet = _extract_body(bodies[idx])
        if not snippet:
            continue
        results.append(SearchResult(title=title, url=url, snippet=snippet, date=date))

    return results


def _parse_response(query: str, html: str, vqd: str | None) -> SearchResponse:
    """Convert raw HTML response into a SearchResponse."""
    response_vqd = _extract_vqd(html) or vqd
    response_md: str = markdownify(html)

    if _HEADER_SEPARATOR not in response_md:
        return SearchResponse(query=query, results=[], vqd=response_vqd)
    _, response_md = response_md.split(_HEADER_SEPARATOR, 1)

    if _FOOTER_SUFFIX in response_md:
        response_md = response_md[: response_md.index(_FOOTER_SUFFIX)]

    results = _parse_results(response_md)
    return SearchResponse(query=query, results=results, vqd=response_vqd)


def search(
    query: str,
    *,
    offset: int = 0,
    date_filter: DateFilter | None = None,
    vqd: str | None = None,
    timeout: float = 10.0,
) -> SearchResponse:
    """Search DuckDuckGo and return parsed results.

    Args:
        query: The search query string.
        offset: Result offset for pagination (maps to DDG's ``s`` parameter).
            Use ``SearchResponse.vqd`` from a previous call to avoid an extra
            request when paginating.
        date_filter: Restrict results to a time range (day, week, month, year).
        vqd: DuckDuckGo session token for pagination. Extracted automatically
            from the first-page response and returned in ``SearchResponse.vqd``.
            Pass it back when using ``offset`` to avoid a redundant request.
        timeout: HTTP request timeout in seconds.

    Returns:
        A SearchResponse containing the query, parsed results, and a ``vqd``
        token for pagination.

    Raises:
        RateLimitError: If DuckDuckGo returns a 429 status.
        ServiceUnavailableError: If DuckDuckGo returns 503 or the request times out.
        NanoserpError: For other HTTP errors.
    """
    headers = {"User-Agent": _USER_AGENT}
    df = _DATE_FILTER_MAP[date_filter] if date_filter else ""

    try:
        if offset > 0 and vqd is None:
            # Pagination requires a vqd token.  Fetch one if not provided.
            initial_data: dict[str, str] = {"q": query}
            if df:
                initial_data["df"] = df
            initial_response = httpx.post(
                _BASE_URL, data=initial_data, headers=headers, timeout=timeout
            )
            _check_status(initial_response)
            vqd = _extract_vqd(initial_response.text)
            if vqd is None:
                return SearchResponse(query=query, results=[])

        form_data: dict[str, str] = {"q": query}
        if df:
            form_data["df"] = df
        if offset > 0 and vqd is not None:
            form_data["s"] = str(offset)
            form_data["dc"] = str(offset + 1)
            form_data["vqd"] = vqd

        response = httpx.post(
            _BASE_URL, data=form_data, headers=headers, timeout=timeout
        )
    except httpx.TimeoutException as e:
        raise ServiceUnavailableError(f"DuckDuckGo request timed out: {e}") from e

    _check_status(response)
    return _parse_response(query, response.text, vqd)
