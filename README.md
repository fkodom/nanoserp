# nanoserp

A tiny, free Python library and CLI for web search and page scraping. No API keys, no accounts, no rate limit tiers -- just search and scrape.

Built on top of DuckDuckGo's HTML endpoint and [markdownify](https://github.com/matthewwithanm/python-markdownify), nanoserp is designed for small-scale coding agents and agentic Python applications that need lightweight, zero-config access to web search and content extraction.

## Install

```bash
pip install nanoserp
```

Requires Python 3.11+.

## CLI

### Search

```bash
nanoserp search "python web scraping"
```

Filter results by time range (`d`/`w`/`m`/`y`):

```bash
nanoserp search "python web scraping" --date-filter w
```

Paginate through results with `--offset`:

```bash
nanoserp search "python web scraping" --offset 10
```

### Scrape

```bash
nanoserp scrape "https://example.com"
```

Prints the page content as markdown, followed by an aggregated list of all links found on the page.

## Python API

### Search

```python
from nanoserp import search, DateFilter

# Basic search
result = search("python web scraping")

for r in result.results:
    print(r.title, r.url, r.snippet)

# Filter by time range
result = search("python web scraping", date_filter=DateFilter.WEEK)

# Pagination
page1 = search("python web scraping")
page2 = search("python web scraping", offset=len(page1.results), vqd=page1.vqd)
```

The `search` function returns a `SearchResponse`:

| Field | Type | Description |
| --- | --- | --- |
| `query` | `str` | The original query string |
| `results` | `list[SearchResult]` | Parsed search results |
| `vqd` | `str \| None` | Session token for pagination |

Each `SearchResult` contains:

| Field | Type | Description |
| --- | --- | --- |
| `title` | `str` | Result title |
| `url` | `str` | Result URL |
| `snippet` | `str` | Text snippet |
| `date` | `datetime \| None` | Publish date, if available |

### Scrape

```python
from nanoserp import scrape

result = scrape("https://example.com")

print(result.markdown)     # Full page content as markdown
for link in result.links:
    print(link.text, link.url)
```

The `scrape` function returns a `ScrapeResponse`:

| Field | Type | Description |
| --- | --- | --- |
| `url` | `str` | The scraped URL |
| `markdown` | `str` | Page content converted to markdown |
| `links` | `list[ScrapeLink]` | All links found on the page |

### Error Handling

All errors inherit from `NanoserpError`:

```python
from nanoserp import search
from nanoserp.exceptions import NanoserpError, RateLimitError

try:
    result = search("test")
except RateLimitError:
    # DuckDuckGo returned HTTP 429
    ...
except NanoserpError as e:
    # Any other HTTP or parsing error
    print(e.message)
```

## Limitations

- Search results come from DuckDuckGo's HTML endpoint, which is not an official API. The response format may change without notice.
- DuckDuckGo may rate-limit or block requests under heavy use. This tool is intended for small-scale, low-frequency usage.
- Scraping respects the target server's response but does not check `robots.txt`.

## For Developers

### Setup

This project uses [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management, but any virtual environment or package manager (`pip`, `venv`, `poetry`, `conda`) will work.

```bash
# Create and activate a virtual environment
uv venv --python 3.12
source .venv/bin/activate

# Install development dependencies and pre-commit hooks
uv sync --extra dev
pre-commit install
```

### Verification

Before committing, make sure all checks pass:

```bash
# Lint and format
uv run ruff check --fix . && uv run ruff format .

# Type check
uv run ty check .

# Unit tests
uv run pytest

# Include integration tests (makes real HTTP requests)
uv run pytest --slow
```

### Tooling

| Tool | Description |
| --- | --- |
| [ruff](https://github.com/astral-sh/ruff) | Linting and formatting |
| [ty](https://docs.astral.sh/ty/) | Static type checking |
| [pytest](https://github.com/pytest-dev/pytest) | Unit and integration testing |
| [pre-commit](https://pre-commit.com/) | Git hook management |

### Publishing

To publish to PyPI, move `.github/disabled-workflows/publish.yaml.disabled` to `.github/workflows/publish.yaml` and set `PYPI_API_TOKEN` in the repo secrets. Then tag a new release, and GitHub Actions will build and publish the package automatically.
