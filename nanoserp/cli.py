"""
Command-line interface for nanoserp.
"""

import argparse
import sys

from nanoserp.exceptions import NanoserpError
from nanoserp.models import DateFilter
from nanoserp.scrape import scrape
from nanoserp.search import search

_DATE_FILTER_ALIASES: dict[str, DateFilter] = {
    "d": DateFilter.DAY,
    "day": DateFilter.DAY,
    "w": DateFilter.WEEK,
    "week": DateFilter.WEEK,
    "m": DateFilter.MONTH,
    "month": DateFilter.MONTH,
    "y": DateFilter.YEAR,
    "year": DateFilter.YEAR,
}


def _format_search(query: str, offset: int, date_filter: DateFilter | None) -> str:
    """Run a search and return formatted output."""
    result = search(query, offset=offset, date_filter=date_filter)
    lines: list[str] = []
    lines.append(f"Search: {result.query}")
    lines.append(f"Results: {len(result.results)}")
    lines.append("")
    for i, r in enumerate(result.results, start=1):
        lines.append(f"  {i}. {r.title}")
        lines.append(f"     {r.url}")
        if r.date:
            lines.append(f"     {r.date.strftime('%Y-%m-%d')}")
        lines.append(f"     {r.snippet}")
        lines.append("")
    return "\n".join(lines)


def _format_scrape(url: str) -> str:
    """Run a scrape and return formatted output."""
    result = scrape(url)
    lines: list[str] = []
    lines.append(f"URL: {result.url}")
    lines.append(f"Links: {len(result.links)}")
    lines.append("")
    lines.append(result.markdown.strip())
    if result.links:
        lines.append("")
        lines.append("--- Links ---")
        for link in result.links:
            lines.append(f"  [{link.text}]({link.url})")
    lines.append("")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nanoserp", description="Nano SERP CLI")
    subparsers = parser.add_subparsers(dest="command")

    # search
    sp_search = subparsers.add_parser("search", help="Search DuckDuckGo")
    sp_search.add_argument("query", help="Search query")
    sp_search.add_argument(
        "--date-filter",
        default=None,
        help="Date filter: d/day, w/week, m/month, y/year",
    )
    sp_search.add_argument(
        "--offset", type=int, default=0, help="Result offset for pagination"
    )

    # scrape
    sp_scrape = subparsers.add_parser("scrape", help="Scrape a webpage")
    sp_scrape.add_argument("url", help="URL to scrape")

    return parser


def _run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    try:
        if args.command == "search":
            date_filter: DateFilter | None = None
            if args.date_filter is not None:
                key = args.date_filter.lower()
                if key not in _DATE_FILTER_ALIASES:
                    print(
                        f"Error: unknown date filter '{args.date_filter}'. "
                        "Use d/day, w/week, m/month, or y/year.",
                        file=sys.stderr,
                    )
                    return 1
                date_filter = _DATE_FILTER_ALIASES[key]
            print(_format_search(args.query, args.offset, date_filter))
        elif args.command == "scrape":
            print(_format_scrape(args.url))
    except NanoserpError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        return 1

    return 0


def main() -> None:
    raise SystemExit(_run())


if __name__ == "__main__":
    main()
