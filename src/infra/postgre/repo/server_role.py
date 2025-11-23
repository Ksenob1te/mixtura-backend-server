from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ServerRole


class ServerRoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, role_id: UUID) -> ServerRole | None:
        stmt = select(ServerRole).where(ServerRole.id == role_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_server(self, server_id: UUID) -> Sequence[ServerRole]:
        stmt = select(ServerRole).where(ServerRole.server_id == server_id).order_by(ServerRole.position.asc())
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, server_id: UUID, name: str, position: int) -> ServerRole | None:
        role = ServerRole(server_id=server_id, name=name, position=position)
        self.session.add(role)
        await self.session.flush()
        return await self.get_by_id(role.id)

    async def set_name(self, role: ServerRole, name: str) -> ServerRole:
        if role.name == name:
            return role
        role.name = name
        self.session.add(role)
        await self.session.flush()
        return role

    async def set_position(self, role: ServerRole, position: int) -> ServerRole:
        if position < 0:
            position = 0
        role.position = position
        self.session.add(role)
        await self.session.flush()
        return role

    async def delete(self, role_id: UUID) -> bool:
        stmt = delete(ServerRole).where(ServerRole.id == role_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

