from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import Server

from ..exceptions import IntegrityUnknownException, IntegrityForeignException


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
        public: bool = False,
        description: str = "",
        icon_id: UUID | None = None,
        banner_id: UUID | None = None,
    ) -> Server:
        server = Server(
            name=name,
            owner_id=owner_id,
            public=public,
            description=description,
            icon_id=icon_id,
            banner_id=banner_id,
        )
        try:
            self.session.add(server)
            await self.session.flush()
            server_field = await self.get_by_id(server.id)
            if server_field is None:
                raise IntegrityUnknownException("Failed to create server")
            return server_field
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Owner field is not found")
            raise IntegrityUnknownException("Failed to create server")

    async def set_name(self, server: Server, name: str) -> Server:
        server.name = name
        await self.session.flush()
        return server

    async def set_description(self, server: Server, description: str) -> Server:
        server.description = description
        await self.session.flush()
        return server

    async def set_public(self, server: Server, public: bool) -> Server:
        server.public = public
        await self.session.flush()
        return server

    async def set_icon(self, server: Server, icon_id: UUID | None) -> Server:
        server.icon_id = icon_id
        await self.session.flush()
        return server

    async def set_banner(self, server: Server, banner_id: UUID | None) -> Server:
        server.banner_id = banner_id
        await self.session.flush()
        return server

    async def delete(self, server_id: UUID) -> bool:
        stmt = delete(Server).where(Server.id == server_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
