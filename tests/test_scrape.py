from unittest.mock import MagicMock, patch

import httpx
import pytest

from nanoserp.exceptions import NanoserpError, RateLimitError, ServiceUnavailableError
from nanoserp.models import ScrapeLink
from nanoserp.scrape import _extract_links, scrape


class TestExtractLinks:
    def test_basic_links(self):
        md = "[Example](https://example.com) and [Other](https://other.com)"
        links = _extract_links(md)
        assert len(links) == 2
        assert links[0] == ScrapeLink(text="Example", url="https://example.com")
        assert links[1] == ScrapeLink(text="Other", url="https://other.com")

    def test_skips_image_only_links(self):
        md = "[![alt](img.png)](https://example.com)"
        links = _extract_links(md)
        assert len(links) == 0

    def test_skips_empty_text_links(self):
        md = "[](https://example.com)"
        links = _extract_links(md)
        assert len(links) == 0

    def test_deduplicates(self):
        md = "[Same](https://example.com) [Same](https://example.com)"
        links = _extract_links(md)
        assert len(links) == 1

    def test_keeps_same_text_different_urls(self):
        md = "[Click](https://a.com) [Click](https://b.com)"
        links = _extract_links(md)
        assert len(links) == 2

    def test_empty_input(self):
        links = _extract_links("")
        assert links == []

    def test_no_links(self):
        links = _extract_links("Just plain text, no links here.")
        assert links == []


class TestScrape:
    @patch("nanoserp.scrape.httpx.get")
    def test_timeout_raises_service_unavailable(self, mock_get):
        mock_get.side_effect = httpx.TimeoutException("timed out")
        with pytest.raises(ServiceUnavailableError, match="timed out"):
            scrape("https://example.com")

    @patch("nanoserp.scrape.httpx.get")
    def test_429_raises_rate_limit_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        with pytest.raises(RateLimitError):
            scrape("https://example.com")

    @patch("nanoserp.scrape.httpx.get")
    def test_503_raises_service_unavailable(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        with pytest.raises(ServiceUnavailableError):
            scrape("https://example.com")

    @patch("nanoserp.scrape.httpx.get")
    def test_generic_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        with pytest.raises(NanoserpError, match="404"):
            scrape("https://example.com")

    @patch("nanoserp.scrape.httpx.get")
    def test_successful_scrape(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            "<html><body>"
            "<h1>Hello World</h1>"
            '<p>Visit <a href="https://example.com">Example</a></p>'
            "</body></html>"
        )
        mock_get.return_value = mock_response

        result = scrape("https://example.com")
        assert result.url == "https://example.com"
        assert "Hello World" in result.markdown
        assert len(result.links) == 1
        assert result.links[0].text == "Example"
        assert result.links[0].url == "https://example.com"

    @patch("nanoserp.scrape.httpx.get")
    def test_multiple_links(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            "<html><body>"
            '<a href="https://a.com">Link A</a>'
            '<a href="https://b.com">Link B</a>'
            '<a href="https://c.com">Link C</a>'
            "</body></html>"
        )
        mock_get.return_value = mock_response

        result = scrape("https://example.com")
        assert len(result.links) == 3

    @patch("nanoserp.scrape.httpx.get")
    def test_no_links(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>No links here</p></body></html>"
        mock_get.return_value = mock_response

        result = scrape("https://example.com")
        assert result.links == []
        assert "No links here" in result.markdown

    @patch("nanoserp.scrape.httpx.get")
    def test_follow_redirects_enabled(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Redirected</body></html>"
        mock_get.return_value = mock_response

        scrape("https://example.com")
        _, kwargs = mock_get.call_args
        assert kwargs["follow_redirects"] is True


class TestScrapeIntegration:
    @pytest.mark.slow
    def test_real_scrape(self):
        result = scrape("https://example.com")
        assert result.url == "https://example.com"
        assert len(result.markdown) > 0
        assert "Example Domain" in result.markdown
