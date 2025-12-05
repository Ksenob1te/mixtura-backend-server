from enum import StrEnum
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.postgre.repo.permission import PermissionRepository

from typing import Iterable, Callable

logger = logging.getLogger(__name__)


class PERMISSION(StrEnum):
    SELF_EDIT = 'self_edit'
    LIST_MEMBERS = 'list_members'
    CREATE_VIRTUAL = 'create_virtual'
    EDIT_MEMBERS = 'edit_members'
    KICK_MEMBERS = 'kick_members'
    MIGRATE_MEMBERS = 'migrate_members'

    # MANAGE_ROLES = 'manage_roles'
    # MANAGE_CHANNELS = 'manage_channels'
    # MANAGE_SERVER = 'manage_server'

    @staticmethod
    def serialize_permission_codes(permissions: Iterable["PERMISSION"]) -> int:
        mask = 0
        for i, member in enumerate(PERMISSION):
            if member in permissions:
                mask |= (1 << i)
        return mask

    @staticmethod
    def deserialize_permission_codes(mask: int) -> set["PERMISSION"]:
        permissions = set()
        for i, member in enumerate(PERMISSION):
            if mask & (1 << i):
                permissions.add(member)
        return permissions

    @staticmethod
    def check_permission(mask: int, permission: "PERMISSION") -> bool:
        index = list(PERMISSION).index(permission)
        return (mask & (1 << index)) != 0

    @staticmethod
    def check_permission_bulk(mask: int, permissions: Iterable["PERMISSION"],
                              method: Callable[[Iterable[object]], bool]) -> bool:
        return method(
            PERMISSION.check_permission(mask, permission)
            for permission in permissions
        )


async def init_permissions(session: AsyncSession) -> None:
    repo = PermissionRepository(session)
    created_codes: list[str] = []
    existing_perms = await repo.get_by_code_name_bulk([p for p in PERMISSION])
    existing_codes = {p.code_name for p in existing_perms}
    for perm in PERMISSION:
        if perm not in existing_codes:
            await repo.create(perm)
            created_codes.append(perm)
    if created_codes:
        logger.info(f"Initialized permissions: {', '.join(created_codes)}")
