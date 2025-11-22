from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Permission, ServerRolePermission


class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, permission_id: UUID) -> Permission | None:
        stmt = select(Permission).where(Permission.id == permission_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_code_name(self, code_name: str) -> Permission | None:
        stmt = select(Permission).where(Permission.code_name == code_name).limit(1)
        return await self.session.scalar(stmt)

    async def list_all(self) -> Sequence[Permission]:
        stmt = select(Permission)
        res = await self.session.scalars(stmt)
        return res.all()

    async def list_for_role(self, server_role_id: UUID) -> Sequence[Permission]:
        stmt = select(Permission).join(ServerRolePermission).where(
            ServerRolePermission.server_role_id == server_role_id
        )
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, code_name: str) -> Permission | None:
        perm = Permission(code_name=code_name)
        self.session.add(perm)
        await self.session.flush()
        return await self.get_by_id(perm.id)

    async def delete(self, permission_id: UUID) -> bool:
        stmt = delete(Permission).where(Permission.id == permission_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def assign_to_role(self, permission_id: UUID, server_role_id: UUID) -> None:
        stmt = select(ServerRolePermission).where(
            ServerRolePermission.permission_id == permission_id,
            ServerRolePermission.server_role_id == server_role_id
        ).limit(1)
        existing = await self.session.scalar(stmt)
        if existing:
            return
        link = ServerRolePermission(permission_id=permission_id, server_role_id=server_role_id)
        self.session.add(link)
        await self.session.flush()

    async def remove_from_role(self, permission_id: UUID, server_role_id: UUID) -> bool:
        stmt = delete(ServerRolePermission).where(
            ServerRolePermission.permission_id == permission_id,
            ServerRolePermission.server_role_id == server_role_id
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def bulk_assign_to_role(self, server_role_id: UUID, permission_ids: list[UUID]) -> None:
        for pid in permission_ids:
            await self.assign_to_role(pid, server_role_id)

