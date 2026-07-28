from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import IntegrityForeignException, IntegrityUnknownException
from src.core.interfaces.repo.permission import PermissionRepositoryProtocol
from src.core.models.permission import Permission as PermissionDTO
from src.core.models.permission import PermissionCreate

from ..models import Permission as PermissionModel
from ..models import ServerRolePermission
from .base import BaseRepository


class PermissionRepository(
    BaseRepository[PermissionModel, PermissionCreate, PermissionDTO, PermissionDTO],
    PermissionRepositoryProtocol,
):
    model = PermissionModel
    dto_model = PermissionDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_code(self, code: str) -> PermissionDTO | None:
        stmt = select(PermissionModel).where(PermissionModel.code == code).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_by_code_bulk(self, code_names: list[str]) -> Sequence[PermissionDTO]:
        stmt = select(PermissionModel).where(PermissionModel.code.in_(code_names))
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def list_all(self) -> Sequence[PermissionDTO]:
        stmt = select(PermissionModel)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def list_for_role(self, server_role_id: UUID | None) -> Sequence[PermissionDTO]:
        stmt = select(PermissionModel).join(ServerRolePermission).where(
            ServerRolePermission.server_role_id == server_role_id
        )
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def assign_to_role(self, permission_id: UUID, server_role_id: UUID) -> None:
        stmt = (
            insert(ServerRolePermission)
            .values(permission_id=permission_id, server_role_id=server_role_id)
            .on_conflict_do_nothing(
                index_elements=[ServerRolePermission.server_role_id, ServerRolePermission.permission_id]
            )
        )
        try:
            await self._session.execute(stmt)
            await self._flush()
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Permission or server role fields are not found") from exc
            raise IntegrityUnknownException("Failed to assign permission to server role")

    async def remove_from_role(self, permission_id: UUID, server_role_id: UUID) -> bool:
        stmt = delete(ServerRolePermission).where(
            ServerRolePermission.permission_id == permission_id,
            ServerRolePermission.server_role_id == server_role_id
        )
        return bool(await self._execute_dml(stmt))

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
            await self._session.execute(stmt)
            await self._flush()
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException(
                    "Some permissions or server role fields are not found"
                )
            raise IntegrityUnknownException(
                "Failed to assign permissions to server role"
            )

    async def bulk_remove_from_role(self, permission_ids: list[UUID], server_role_id: UUID) -> int:
        stmt = delete(ServerRolePermission).where(
            ServerRolePermission.server_role_id == server_role_id,
            ServerRolePermission.permission_id.in_(permission_ids)
        )
        return await self._execute_dml(stmt)

    async def bulk_set_for_role(self, permission_ids: list[UUID], server_role_id: UUID) -> None:
        existing_permissions = await self.list_for_role(server_role_id)
        existing_permission_ids = {p.id for p in existing_permissions}

        to_add = [pid for pid in permission_ids if pid not in existing_permission_ids]
        to_remove = [pid for pid in existing_permission_ids if pid not in permission_ids]

        if to_add:
            await self.bulk_assign_to_role(to_add, server_role_id)
        if to_remove:
            await self.bulk_remove_from_role(to_remove, server_role_id)
