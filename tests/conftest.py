import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infra.postgre import Base


@pytest_asyncio.fixture(scope="session")
async def postgres_container() -> AsyncGenerator[str, None]:
    with PostgresContainer("postgres:15") as container:
        container.start()
        sync_url = container.get_connection_url()
        sync_url = "postgresql://" + sync_url.split("://")[1]
        async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://")

        yield async_url


@pytest_asyncio.fixture(scope="session")
async def async_engine(postgres_container):
    engine = create_async_engine(
        postgres_container,
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def async_session(async_engine):
    async with async_engine.connect() as connection:
        async with connection.begin() as transaction:
            session_factory = async_sessionmaker(
                bind=connection,
                expire_on_commit=False,
            )
            async with session_factory() as session:
                yield session

            await transaction.rollback()
