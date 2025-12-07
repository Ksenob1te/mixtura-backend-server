from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import Server


class ServerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, server_id: UUID) -> Server | None:
        stmt = select(Server).where(Server.id == server_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_public(self) -> Sequence[Server]:
        stmt = select(Server).where(Server.public.is_(True))
        res = await self.session.scalars(stmt)
        return res.all()

    async def list_by_owner(self, owner_id: UUID) -> Sequence[Server]:
        stmt = select(Server).where(Server.owner_id == owner_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(
        self,
        name: str,
        owner_id: UUID,
        role_set_id: UUID,
        rating_set_id: UUID,
        public: bool = False,
        description: str = "",
        icon_url: str | None = None,
        icon_id: UUID | None = None,
        banner_url: str | None = None,
        banner_id: UUID | None = None,
    ) -> Server | None:
        server = Server(
            name=name,
            owner_id=owner_id,
            role_set_id=role_set_id,
            rating_set_id=rating_set_id,
            public=public,
            description=description,
            icon_url=icon_url,
            icon_id=icon_id,
            banner_url=banner_url,
            banner_id=banner_id,
        )
        self.session.add(server)
        await self.session.flush()
        return await self.get_by_id(server.id)

    async def set_name(self, server: Server, name: str) -> Server:
        server.name = name
        self.session.add(server)
        await self.session.flush()
        return server

    async def set_description(self, server: Server, description: str) -> Server:
        server.description = description
        self.session.add(server)
        await self.session.flush()
        return server

    async def set_public(self, server: Server, public: bool) -> Server:
        server.public = public
        self.session.add(server)
        await self.session.flush()
        return server

    async def set_icon(self, server: Server, icon_url: str | None, icon_id: UUID | None) -> Server:
        server.icon_url = icon_url
        server.icon_id = icon_id
        self.session.add(server)
        await self.session.flush()
        return server

    async def set_banner(self, server: Server, banner_url: str | None, banner_id: UUID | None) -> Server:
        server.banner_url = banner_url
        server.banner_id = banner_id
        self.session.add(server)
        await self.session.flush()
        return server

    async def delete(self, server_id: UUID) -> bool:
        stmt = delete(Server).where(Server.id == server_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
