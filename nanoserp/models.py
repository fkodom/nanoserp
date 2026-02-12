"""
Common data models used throughout the 'nanoserp' library.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class DateFilter(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    date: datetime | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    vqd: str | None = None


class ScrapeLink(BaseModel):
    text: str
    url: str


class ScrapeResponse(BaseModel):
    url: str
    markdown: str
    links: list[ScrapeLink]
