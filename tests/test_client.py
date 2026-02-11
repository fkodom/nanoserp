import pytest

from nanoserp.client import AsyncClient


@pytest.mark.asyncio
async def test_is_healthy(mock_client: AsyncClient):
    is_healthy = await mock_client.is_healthy()
    assert isinstance(is_healthy, bool)
    assert is_healthy is True
