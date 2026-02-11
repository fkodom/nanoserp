import os
from importlib import reload
from typing import Generator
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_postgresql import factories
from pytest_postgresql.executor import PostgreSQLExecutor
from pytest_postgresql.janitor import DatabaseJanitor

from {{REPO_NAME_SNAKECASE}}.api import main as api_main
from {{REPO_NAME_SNAKECASE}}.client import AsyncClient

TEST_API_KEY = "test-api-key-1234567890"


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: slow to run")


def pytest_collection_modifyitems(config, items):
    run_slow = config.getoption("--slow")
    skip_fast = pytest.mark.skip(reason="remove --slow option to run")
    skip_slow = pytest.mark.skip(reason="need --slow option to run")

    for item in items:
        if ("slow" in item.keywords) and (not run_slow):
            item.add_marker(skip_slow)
        if ("slow" not in item.keywords) and (run_slow):
            item.add_marker(skip_fast)


# NOTE: We don't explicitly use postgresql-specific dialects in the code, so we can use
# SQLite for most tests.  However, the DB migrations are written specifically for
# Postgres, so we need to run the migration test(s) against a local Postgres instance.
pg_executor = factories.postgresql_proc(
    dbname="test_db",
    port=5432,
    user="test_user",
    password="test_password",
)


@pytest.fixture(scope="function", autouse=True)
def database_url(
    pg_executor: PostgreSQLExecutor,
) -> Generator[str, None, None]:
    with DatabaseJanitor(
        user=pg_executor.user,
        host=pg_executor.host,
        port=pg_executor.port,
        dbname=pg_executor.dbname,
        version=pg_executor.version,
        password=pg_executor.password,
    ):
        yield (
            f"postgresql://"
            f"{pg_executor.user}:{pg_executor.password}@{pg_executor.host}"
            f":{pg_executor.port}/{pg_executor.dbname}"
        )


@pytest.fixture(scope="function", autouse=True)
def mock_app(database_url: str) -> Generator[TestClient, None, None]:
    """Fixture to provide the API URL for tests."""
    with patch.dict(
        os.environ,
        {
            "{{REPO_NAME_ALLCAPS}}_API_KEY": TEST_API_KEY,
            "{{REPO_NAME_ALLCAPS}}_DATABASE_URL": database_url,
        },
    ):
        reload(api_main)
        with TestClient(api_main.app) as client:
            yield client


class MockHttpxClient:
    def __init__(self, local_client: TestClient):
        self.local_client = local_client
        self.base_url = str(local_client.base_url)

    async def get(self, url: str, *args, **kwargs):
        return self.local_client.get(url.removeprefix(self.base_url), *args, **kwargs)

    async def post(self, url: str, *args, **kwargs):
        return self.local_client.post(url.removeprefix(self.base_url), *args, **kwargs)


@pytest.fixture(scope="function")
def mock_client(mock_app: TestClient) -> Generator[AsyncClient, None, None]:
    with patch.object(
        httpx, "AsyncClient", new=lambda *args, **kwargs: MockHttpxClient(mock_app)
    ):
        yield AsyncClient(base_url=str(mock_app.base_url))
