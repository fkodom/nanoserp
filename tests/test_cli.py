from datetime import datetime
from unittest.mock import patch

from nanoserp.cli import _run
from nanoserp.exceptions import RateLimitError, ServiceUnavailableError
from nanoserp.models import (
    ScrapeLink,
    ScrapeResponse,
    SearchResponse,
    SearchResult,
)


class TestSearchCommand:
    @patch("nanoserp.cli.search")
    def test_basic_search(self, mock_search, capsys):
        mock_search.return_value = SearchResponse(
            query="test",
            results=[
                SearchResult(
                    title="Example",
                    url="https://example.com",
                    snippet="An example result.",
                )
            ],
        )
        code = _run(["search", "test"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Search: test" in out
        assert "Results: 1" in out
        assert "Example" in out
        assert "https://example.com" in out
        assert "An example result." in out

    @patch("nanoserp.cli.search")
    def test_search_with_date(self, mock_search, capsys):
        mock_search.return_value = SearchResponse(
            query="test",
            results=[
                SearchResult(
                    title="Dated",
                    url="https://example.com",
                    snippet="Has a date.",
                    date=datetime(2026, 2, 10),
                )
            ],
        )
        code = _run(["search", "test"])
        assert code == 0
        out = capsys.readouterr().out
        assert "2026-02-10" in out

    @patch("nanoserp.cli.search")
    def test_search_empty_results(self, mock_search, capsys):
        mock_search.return_value = SearchResponse(query="nothing", results=[])
        code = _run(["search", "nothing"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Results: 0" in out

    @patch("nanoserp.cli.search")
    def test_search_with_date_filter_short(self, mock_search):
        mock_search.return_value = SearchResponse(query="test", results=[])
        _run(["search", "test", "--date-filter", "w"])
        from nanoserp.models import DateFilter

        mock_search.assert_called_once_with(
            "test", offset=0, date_filter=DateFilter.WEEK
        )

    @patch("nanoserp.cli.search")
    def test_search_with_date_filter_long(self, mock_search):
        mock_search.return_value = SearchResponse(query="test", results=[])
        _run(["search", "test", "--date-filter", "month"])
        from nanoserp.models import DateFilter

        mock_search.assert_called_once_with(
            "test", offset=0, date_filter=DateFilter.MONTH
        )

    @patch("nanoserp.cli.search")
    def test_search_with_offset(self, mock_search):
        mock_search.return_value = SearchResponse(query="test", results=[])
        _run(["search", "test", "--offset", "10"])
        mock_search.assert_called_once_with("test", offset=10, date_filter=None)

    def test_search_invalid_date_filter(self, capsys):
        code = _run(["search", "test", "--date-filter", "invalid"])
        assert code == 1
        err = capsys.readouterr().err
        assert "unknown date filter" in err

    @patch("nanoserp.cli.search")
    def test_search_nanoserp_error(self, mock_search, capsys):
        mock_search.side_effect = RateLimitError("rate limit exceeded")
        code = _run(["search", "test"])
        assert code == 1
        err = capsys.readouterr().err
        assert "Error:" in err


class TestScrapeCommand:
    @patch("nanoserp.cli.scrape")
    def test_basic_scrape(self, mock_scrape, capsys):
        mock_scrape.return_value = ScrapeResponse(
            url="https://example.com",
            markdown="# Hello World\n\nSome content.",
            links=[ScrapeLink(text="Link", url="https://link.com")],
        )
        code = _run(["scrape", "https://example.com"])
        assert code == 0
        out = capsys.readouterr().out
        assert "URL: https://example.com" in out
        assert "Links: 1" in out
        assert "Hello World" in out
        assert "--- Links ---" in out
        assert "[Link](https://link.com)" in out

    @patch("nanoserp.cli.scrape")
    def test_scrape_no_links(self, mock_scrape, capsys):
        mock_scrape.return_value = ScrapeResponse(
            url="https://example.com",
            markdown="Plain text only.",
            links=[],
        )
        code = _run(["scrape", "https://example.com"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Links: 0" in out
        assert "--- Links ---" not in out

    @patch("nanoserp.cli.scrape")
    def test_scrape_nanoserp_error(self, mock_scrape, capsys):
        mock_scrape.side_effect = ServiceUnavailableError("timed out")
        code = _run(["scrape", "https://example.com"])
        assert code == 1
        err = capsys.readouterr().err
        assert "Error:" in err


class TestNoCommand:
    def test_no_args_prints_help(self, capsys):
        code = _run([])
        assert code == 1
        out = capsys.readouterr().out
        assert "usage:" in out.lower() or "nanoserp" in out
