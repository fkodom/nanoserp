from datetime import datetime

from nanoserp.models import DateFilter, SearchResponse, SearchResult


class TestDateFilter:
    def test_values(self):
        assert DateFilter.DAY == "day"
        assert DateFilter.WEEK == "week"
        assert DateFilter.MONTH == "month"
        assert DateFilter.YEAR == "year"

    def test_is_string(self):
        assert isinstance(DateFilter.DAY, str)


class TestSearchResult:
    def test_basic_construction(self):
        result = SearchResult(
            title="Example",
            url="https://example.com",
            snippet="An example snippet.",
        )
        assert result.title == "Example"
        assert result.url == "https://example.com"
        assert result.snippet == "An example snippet."
        assert result.date is None

    def test_with_date(self):
        dt = datetime(2026, 2, 10, 1, 24, 0)
        result = SearchResult(
            title="Example",
            url="https://example.com",
            snippet="An example snippet.",
            date=dt,
        )
        assert result.date == dt

    def test_with_iso_date_string(self):
        result = SearchResult(
            title="Example",
            url="https://example.com",
            snippet="An example snippet.",
            date=datetime.fromisoformat("2026-02-10T01:24:00"),
        )
        assert result.date == datetime(2026, 2, 10, 1, 24, 0)


class TestSearchResponse:
    def test_basic_construction(self):
        response = SearchResponse(query="test", results=[])
        assert response.query == "test"
        assert response.results == []
        assert response.vqd is None

    def test_with_vqd(self):
        response = SearchResponse(query="test", results=[], vqd="abc-123")
        assert response.vqd == "abc-123"

    def test_with_results(self):
        results = [
            SearchResult(
                title="Example",
                url="https://example.com",
                snippet="An example snippet.",
            )
        ]
        response = SearchResponse(query="test", results=results)
        assert len(response.results) == 1
        assert response.results[0].title == "Example"
