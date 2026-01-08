import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infra.postgre import Base
from src.infra.postgre.models import (
    Server, GameRoleSet, RatingSet, Member, Game, Permission, Restriction,
    ServerRole, GameRole, Invite
)
from src.infra.postgre.static import PERMISSION, RESTRICTION


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


class Helpers:
    @staticmethod
    def perm_mask(*perms: PERMISSION) -> int:
        return PERMISSION.serialize_permission_codes(perms)

    @staticmethod
    def restr_mask(*restrs: RESTRICTION) -> int:
        return RESTRICTION.serialize_restriction_codes(restrs)


@pytest.fixture(scope="session")
def helpers():
    return Helpers


class ServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_role_set(self, name: str = "RS", is_global: bool = False,
                              server_id: uuid.UUID | None = None) -> GameRoleSet:
        uid = uuid.uuid4().hex[:8]
        rs = GameRoleSet(name=f"{name}-{uid}", is_global=is_global, server_id=server_id)
        self.session.add(rs)
        await self.session.flush()
        return rs

    async def create_rating_set(self, name: str = "RT", is_global: bool = False,
                                server_id: uuid.UUID | None = None) -> RatingSet:
        uid = uuid.uuid4().hex[:8]
        rts = RatingSet(name=f"{name}-{uid}", min_rating=0, max_rating=50, is_global=is_global, server_id=server_id)
        self.session.add(rts)
        await self.session.flush()
        return rts

    async def create_server(self, public: bool = False, owner_id: uuid.UUID | None = None,
                            role_set: GameRoleSet | None = None, rating_set: RatingSet | None = None) -> Server:

        uid = uuid.uuid4().hex[:8]
        s = Server(
            id=uuid.uuid4(),
            name=f"Server-{uid}",
            owner_id=owner_id or uuid.uuid4(),
            public=public
        )
        self.session.add(s)
        if role_set:
            s.role_set = role_set
        if rating_set:
            s.rating_set = rating_set
        await self.session.flush()

        if not role_set:
            role_set = await self.create_role_set(server_id=s.id)
            s.role_set = role_set
        if not rating_set:
            rating_set = await self.create_rating_set(server_id=s.id)
            s.rating_set = rating_set

        return s

    async def create_member(self, server_id: uuid.UUID, user_id: uuid.UUID | int | None = 0,
                            nickname: str = "Member", role_id: uuid.UUID | None = None) -> Member:
        if user_id == 0:
            user_id = uuid.uuid4()
        m = Member(
            server_id=server_id,
            user_id=user_id,
            nickname=nickname,
            server_role_id=role_id
        )
        self.session.add(m)
        await self.session.flush()
        return m

    async def create_server_role(self, server_id: uuid.UUID, name: str = "Role", position: int = 0) -> ServerRole:
        r = ServerRole(server_id=server_id, name=name, position=position)
        self.session.add(r)
        await self.session.flush()
        return r

    async def create_game_role(self, role_set_id: uuid.UUID, name: str = "GRole") -> GameRole:
        r = GameRole(name=name, role_set_id=role_set_id, min_in_team=1, max_in_team=5)
        self.session.add(r)
        await self.session.flush()
        return r

    async def create_game(self, name: str = "Game") -> Game:
        g = Game(name=f"{name}-{uuid.uuid4()}", icon_id=uuid.uuid4(), banner_id=uuid.uuid4())
        self.session.add(g)
        await self.session.flush()
        return g

    async def create_permission(self, code: PERMISSION) -> Permission:
        # Check if exists first to avoid unique constraint errors in tests
        # In a real DB this would be static data
        from sqlalchemy import select
        stmt = select(Permission).where(Permission.code == code)
        existing = await self.session.scalar(stmt)
        if existing:
            return existing

        p = Permission(code=code)
        self.session.add(p)
        await self.session.flush()
        return p

    async def create_restriction(self, code: RESTRICTION) -> Restriction:
        from sqlalchemy import select
        stmt = select(Restriction).where(Restriction.code == code)
        existing = await self.session.scalar(stmt)
        if existing:
            return existing

        r = Restriction(code=code)
        self.session.add(r)
        await self.session.flush()
        return r


@pytest_asyncio.fixture(loop_scope="session")
async def factory(async_session):
    return ServiceFactory(async_session)
