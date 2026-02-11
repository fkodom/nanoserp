from urllib.parse import urlparse

import pytest

from {{REPO_NAME_SNAKECASE}}.db.session import get_async_session
from {{REPO_NAME_SNAKECASE}}.settings import DatabaseSettings


@pytest.mark.asyncio
async def test_get_async_session():
    async with get_async_session() as session:
        assert session is not None
        assert session.bind is not None

        settings = DatabaseSettings()  # type: ignore[call-arg]
        url = urlparse(settings.URL)
        assert session.bind.engine.url.host == url.hostname
        assert session.bind.engine.url.port == url.port
