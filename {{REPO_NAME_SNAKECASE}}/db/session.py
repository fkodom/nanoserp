from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from {{REPO_NAME_SNAKECASE}}.settings import DatabaseSettings


class SessionManager:
    """Singleton class to manage connections to the SQL DB with SQLAlchemy / SQLModel

    We use a singleton class and cache the async engine, so that:
      - every new DB request does not need to initialize the engine
      - the engine doesn't have to be defined in global scope
    """

    _instance: SessionManager | None = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.settings = DatabaseSettings()  # type: ignore[call-arg]
        self._async_engine: AsyncEngine | None = None
        self._semaphore = asyncio.Semaphore(self.settings.MAX_CONNECTIONS)

    @property
    def async_engine(self) -> AsyncEngine:
        """Get the async engine for the global database connection."""
        if self._async_engine is None:
            url = self.settings.URL.replace(
                "postgresql://", "postgresql+asyncpg://"
            ).replace("sqlite://", "sqlite+aiosqlite://")
            # NOTE: Use an unlimited pool size (pool_size=0) for async connections, and
            # limit the number of concurrent connections using a semaphore instead.
            self._async_engine = create_async_engine(url, pool_size=0, echo=True)
        return self._async_engine

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._semaphore:
            async with AsyncSession(self.async_engine) as session:
                yield session


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """A convenience function to get an async session more compactly."""
    async with SessionManager().get_async_session() as session:
        yield session
