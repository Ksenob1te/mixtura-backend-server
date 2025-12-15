from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Permission, ServerRolePermission
from sqlalchemy.dialects.postgresql import insert

from sqlalchemy.exc import IntegrityError
from ..exceptions import IntegrityUnknownException, IntegrityForeignException, IntegrityUniqueException


class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, permission_id: UUID) -> Permission | None:
        stmt = select(Permission).where(Permission.id == permission_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_code_name(self, code_name: str) -> Permission | None:
        stmt = select(Permission).where(Permission.code_name == code_name).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_code_name_bulk(self, code_names: list[str]) -> Sequence[Permission]:
        stmt = select(Permission).where(Permission.code_name.in_(code_names))
        res = await self.session.scalars(stmt)
        return res.all()

    async def list_all(self) -> Sequence[Permission]:
        stmt = select(Permission)
        res = await self.session.scalars(stmt)
        return res.all()

    async def list_for_role(self, server_role_id: UUID | None) -> Sequence[Permission]:
        stmt = select(Permission).join(ServerRolePermission).where(
            ServerRolePermission.server_role_id == server_role_id
        )
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, code_name: str) -> Permission | None:
        perm = Permission(code_name=code_name)
        # TODO: handle integrity errors
        self.session.add(perm)
        await self.session.flush()
        return await self.get_by_id(perm.id)

    async def delete(self, permission_id: UUID) -> bool:
        stmt = delete(Permission).where(Permission.id == permission_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def assign_to_role(self, permission_id: UUID, server_role_id: UUID) -> None:
        link = ServerRolePermission(permission_id=permission_id, server_role_id=server_role_id)
        try:
            self.session.add(link)
            await self.session.flush()
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Permission or server role fields are not found")
            # SQLSTATE_UNIQUE_VIOLATION - duplicate entry
            elif sql_state == "23505":
                raise IntegrityUniqueException("Permission is already assigned to server role")
            raise IntegrityUnknownException("Failed to assign permission to server role")

    async def remove_from_role(self, permission_id: UUID, server_role_id: UUID) -> bool:
        stmt = delete(ServerRolePermission).where(
            ServerRolePermission.permission_id == permission_id,
            ServerRolePermission.server_role_id == server_role_id
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def bulk_assign_to_role(self, permission_ids: list[UUID], server_role_id: UUID) -> None:
        stmt = (
            insert(ServerRolePermission)
            .values(
                [
                    {
                        "server_role_id": server_role_id,
                        "permission_id": pid,
                    }
                    for pid in permission_ids
                ]
            )
            .on_conflict_do_nothing(
                index_elements=[
                    ServerRolePermission.server_role_id,
                    ServerRolePermission.permission_id,
                ]
            )
        )

        try:
            await self.session.execute(stmt)
            await self.session.flush()
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException(
                    "Some permissions or server role fields are not found"
                )
            raise IntegrityUnknownException(
                "Failed to assign permissions to server role"
            )

