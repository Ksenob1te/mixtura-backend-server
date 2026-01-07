from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ServerRole
from sqlalchemy.exc import IntegrityError

from ..exceptions import IntegrityUnknownException, IntegrityForeignException, IntegrityUniqueException


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

    async def create(self, server_id: UUID, name: str, position: int) -> ServerRole:
        stmt = (
            update(ServerRole)
            .where(ServerRole.server_id == server_id)
            .where(ServerRole.position >= position)
            .values(position=ServerRole.position + 1)
        )
        await self.session.execute(stmt)

        role = ServerRole(server_id=server_id, name=name, position=position)
        try:
            self.session.add(role)
            await self.session.flush()
            role_field = await self.get_by_id(role.id)
            if role_field is None:
                raise IntegrityUnknownException("Failed to create server role")
            return role_field
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Server field is not found")
            # SQLSTATE_UNIQUE_VIOLATION - duplicate name in the same server
            if sql_state == "23505":
                raise IntegrityUniqueException("Server role with this name already exists in the server") from exc
            raise IntegrityUnknownException("Failed to create server role")

    async def set_name(self, role: ServerRole, name: str) -> ServerRole:
        if role.name == name:
            return role
        role.name = name
        await self.session.flush()
        return role

    async def set_position(self, role: ServerRole, new_position: int) -> ServerRole:
        if new_position < 0:
            new_position = 0
        old_position = role.position

        if new_position > old_position:
            stmt = (
                update(ServerRole)
                .where(ServerRole.server_id == role.server_id)
                .where(ServerRole.position > old_position)
                .where(ServerRole.position <= new_position)
                .values(position=ServerRole.position - 1)
            )
        else:
            stmt = (
                update(ServerRole)
                .where(ServerRole.server_id == role.server_id)
                .where(ServerRole.position >= new_position)
                .where(ServerRole.position < old_position)
                .values(position=ServerRole.position + 1)
            )
        await self.session.execute(stmt)
        role.position = new_position
        await self.session.flush()
        return role

    async def delete(self, role_id: UUID) -> bool:
        stmt = delete(ServerRole).where(ServerRole.id == role_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

