from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from nanoserp.exceptions import NanoserpError, RateLimitError, ServiceUnavailableError
from nanoserp.models import DateFilter
from nanoserp.search import _extract_vqd, _parse_date, _parse_results, search

# --- Sample markdown fixtures ---

SINGLE_RESULT_WITH_DATE = """
[Example Title](https://example.com)
--------------------------------------

[![](//icon.ico)](https://example.com)
[example.com](https://example.com)
    2026-02-10T01:24:00.0000000

[This is the snippet text for the example result.](https://example.com)
"""

SINGLE_RESULT_WITHOUT_DATE = """
[No Date Title](https://nodate.com)
-------------------------------------

[![](//icon.ico)](https://nodate.com)
[nodate.com](https://nodate.com)

[Snippet without a date field present.](https://nodate.com)
"""

MULTIPLE_RESULTS = """
[First Title](https://first.com)
----------------------------------

[![](//icon.ico)](https://first.com)
[first.com](https://first.com)
    2026-02-10T01:24:00.0000000

[First snippet text here.](https://first.com)

[Second Title](https://second.com)
------------------------------------

[![](//icon.ico)](https://second.com)
[second.com](https://second.com)

[Second snippet text here.](https://second.com)
"""


class TestParseDate:
    def test_seven_digit_fractional(self):
        result = _parse_date("2026-02-10T01:24:00.0000000")
        assert result == datetime(2026, 2, 10, 1, 24, 0)

    def test_six_digit_fractional(self):
        result = _parse_date("2026-02-10T01:24:00.000000")
        assert result == datetime(2026, 2, 10, 1, 24, 0)

    def test_no_fractional(self):
        result = _parse_date("2026-02-10T01:24:00")
        assert result == datetime(2026, 2, 10, 1, 24, 0)

    def test_nonzero_fractional(self):
        result = _parse_date("2026-02-10T01:24:00.1234567")
        assert result == datetime(2026, 2, 10, 1, 24, 0, 123456)


class TestExtractVqd:
    def test_extracts_from_hidden_input(self):
        html = '<input type="hidden" name="vqd" value="4-12345678">'
        assert _extract_vqd(html) == "4-12345678"

    def test_returns_none_when_absent(self):
        html = "<html><body>No vqd here</body></html>"
        assert _extract_vqd(html) is None

    def test_extracts_from_full_page(self):
        html = (
            "<html><body><form>"
            '<input type="hidden" name="q" value="test">'
            '<input type="hidden" name="vqd" value="4-999">'
            "</form></body></html>"
        )
        assert _extract_vqd(html) == "4-999"


class TestParseResults:
    def test_single_result_with_date(self):
        results = _parse_results(SINGLE_RESULT_WITH_DATE)
        assert len(results) == 1
        assert results[0].title == "Example Title"
        assert results[0].url == "https://example.com"
        assert results[0].date == datetime(2026, 2, 10, 1, 24, 0)
        assert "snippet text" in results[0].snippet

    def test_single_result_without_date(self):
        results = _parse_results(SINGLE_RESULT_WITHOUT_DATE)
        assert len(results) == 1
        assert results[0].title == "No Date Title"
        assert results[0].url == "https://nodate.com"
        assert results[0].date is None
        assert "without a date" in results[0].snippet

    def test_multiple_results(self):
        results = _parse_results(MULTIPLE_RESULTS)
        assert len(results) == 2
        assert results[0].title == "First Title"
        assert results[0].url == "https://first.com"
        assert results[0].date == datetime(2026, 2, 10, 1, 24, 0)
        assert results[1].title == "Second Title"
        assert results[1].url == "https://second.com"
        assert results[1].date is None

    def test_empty_input(self):
        results = _parse_results("")
        assert results == []

    def test_no_horizontal_rules(self):
        results = _parse_results("[Title](https://example.com)\nSome text")
        assert results == []


class TestSearch:
    @patch("nanoserp.search.httpx.post")
    def test_timeout_raises_service_unavailable(self, mock_post):
        mock_post.side_effect = httpx.TimeoutException("timed out")
        with pytest.raises(ServiceUnavailableError, match="timed out"):
            search("test query")

    @patch("nanoserp.search.httpx.post")
    def test_429_raises_rate_limit_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        with pytest.raises(RateLimitError, match="rate limit"):
            search("test query")

    @patch("nanoserp.search.httpx.post")
    def test_503_raises_service_unavailable(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_post.return_value = mock_response
        with pytest.raises(ServiceUnavailableError, match="unavailable"):
            search("test query")

    @patch("nanoserp.search.httpx.post")
    def test_generic_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        with pytest.raises(NanoserpError, match="500"):
            search("test query")

    @patch("nanoserp.search.httpx.post")
    def test_missing_header_separator_returns_empty(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No DDG content here</body></html>"
        mock_post.return_value = mock_response
        result = search("test query")
        assert result.query == "test query"
        assert result.results == []

    @patch("nanoserp.search.httpx.post")
    def test_successful_parse(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            "<html><body>"
            "Any Time\nPast Day\nPast Week\nPast Month\nPast Year"
            '<a href="https://example.com">Example Title</a>'
            "<hr/>"
            '<a href="https://example.com"><img src="//icon.ico"/></a>'
            '<a href="https://example.com">example.com</a>'
            "<br/>    2026-02-10T01:24:00.0000000<br/>"
            '<a href="https://example.com">'
            "This is the snippet text for the search result."
            "</a>"
            '<a href="//duckduckgo.com/feedback.html">Feedback</a>'
            '<img src="//duckduckgo.com/t/sl_h"/>'
            "</body></html>"
        )
        mock_post.return_value = mock_response
        result = search("test query")
        assert result.query == "test query"
        assert isinstance(result.results, list)

    @patch("nanoserp.search.httpx.post")
    def test_basic_post_form_data(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No DDG content</body></html>"
        mock_post.return_value = mock_response

        search("test query")
        mock_post.assert_called_once()
        form_data = mock_post.call_args[1]["data"]
        assert form_data["q"] == "test query"
        assert "s" not in form_data
        assert "dc" not in form_data

    @patch("nanoserp.search.httpx.post")
    def test_date_filter_in_form_data(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No DDG content</body></html>"
        mock_post.return_value = mock_response

        search("test query", date_filter=DateFilter.WEEK)
        form_data = mock_post.call_args[1]["data"]
        assert form_data["df"] == "w"

    @patch("nanoserp.search.httpx.post")
    def test_date_filter_day(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No DDG content</body></html>"
        mock_post.return_value = mock_response

        search("test query", date_filter=DateFilter.DAY)
        form_data = mock_post.call_args[1]["data"]
        assert form_data["df"] == "d"

    @patch("nanoserp.search.httpx.post")
    def test_offset_with_vqd_includes_pagination_params(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No DDG content</body></html>"
        mock_post.return_value = mock_response

        search("test query", offset=10, vqd="4-token")
        mock_post.assert_called_once()
        form_data = mock_post.call_args[1]["data"]
        assert form_data["q"] == "test query"
        assert form_data["s"] == "10"
        assert form_data["dc"] == "11"
        assert form_data["vqd"] == "4-token"

    @patch("nanoserp.search.httpx.post")
    def test_offset_with_date_filter_includes_df(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No DDG content</body></html>"
        mock_post.return_value = mock_response

        search("test query", offset=10, date_filter=DateFilter.MONTH, vqd="4-token")
        form_data = mock_post.call_args[1]["data"]
        assert form_data["df"] == "m"

    @patch("nanoserp.search.httpx.post")
    def test_offset_without_vqd_fetches_it(self, mock_post):
        # First call: initial POST to get vqd
        initial_response = MagicMock()
        initial_response.status_code = 200
        initial_response.text = (
            '<html><input type="hidden" name="vqd" value="4-auto"></html>'
        )

        # Second call: paginated POST
        paginated_response = MagicMock()
        paginated_response.status_code = 200
        paginated_response.text = "<html><body>No DDG content</body></html>"

        mock_post.side_effect = [initial_response, paginated_response]

        result = search("test query", offset=10)
        assert mock_post.call_count == 2
        # Second call should include vqd from first response
        form_data = mock_post.call_args_list[1][1]["data"]
        assert form_data["vqd"] == "4-auto"
        assert result.query == "test query"

    @patch("nanoserp.search.httpx.post")
    def test_offset_without_vqd_missing_returns_empty(self, mock_post):
        # Initial POST returns page without vqd
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No vqd here</body></html>"
        mock_post.return_value = mock_response

        result = search("test query", offset=10)
        assert result.results == []

    @patch("nanoserp.search.httpx.post")
    def test_offset_timeout_raises_service_unavailable(self, mock_post):
        mock_post.side_effect = httpx.TimeoutException("timed out")
        with pytest.raises(ServiceUnavailableError, match="timed out"):
            search("test query", offset=10, vqd="4-token")

    @patch("nanoserp.search.httpx.post")
    def test_vqd_extracted_from_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            "<html><body>"
            '<input type="hidden" name="vqd" value="4-resp-token">'
            "No DDG content</body></html>"
        )
        mock_post.return_value = mock_response
        result = search("test query")
        assert result.vqd == "4-resp-token"


class TestSearchIntegration:
    @pytest.mark.slow
    def test_real_search(self):
        result = search("python programming language")
        assert result.query == "python programming language"
        assert len(result.results) > 0
        for r in result.results:
            assert r.title
            assert r.url
            assert r.snippet
        assert result.vqd is not None

    @pytest.mark.slow
    def test_real_search_with_date_filter(self):
        result = search("python programming", date_filter=DateFilter.WEEK)
        assert result.query == "python programming"
        assert len(result.results) > 0

    @pytest.mark.slow
    def test_real_search_pagination(self):
        page1 = search("python programming language")
        assert page1.vqd is not None
        assert len(page1.results) > 0

        page2 = search(
            "python programming language",
            offset=len(page1.results),
            vqd=page1.vqd,
        )
        assert len(page2.results) > 0
        # Results should differ between pages
        page1_urls = {r.url for r in page1.results}
        page2_urls = {r.url for r in page2.results}
        assert page1_urls != page2_urls
