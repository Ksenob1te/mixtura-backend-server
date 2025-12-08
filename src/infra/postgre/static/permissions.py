from enum import StrEnum
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.postgre.repo.permission import PermissionRepository

from typing import Iterable, Callable

logger = logging.getLogger(__name__)


class PERMISSION(StrEnum):
    # overwrite permission
    ADMINISTRATOR = 'administrator'

    # base permission
    SELF_EDIT_NAME = 'self_edit_name'
    # TODO: think if we need self_edit right if its base permission that cannot be removed and we have edit restriction
    EDIT_NAME = 'edit_name'
    EDIT_ROLES = 'edit_roles'
    CREATE_VIRTUAL = 'create_virtual'
    MIGRATE_MEMBERS = 'migrate_members'
    KICK_MEMBERS = 'kick_members'
    CREATE_CUSTOM = 'create_custom'
    DELETE_CUSTOM = 'delete_custom'
    EDIT_ALL_CUSTOMS = 'edit_all_customs'

    # server settings
    EDIT_SERVER_PUBLIC = 'edit_server_public'
    EDIT_SERVER_NAME = 'edit_server_name'
    EDIT_SERVER_DESCRIPTION = 'edit_server_description'
    EDIT_SERVER_GAME = 'edit_server_game'
    DELETE_SERVER = 'delete_server'
    EDIT_ROLE_SET = 'edit_role_set'
    EDIT_RATING_SET = 'edit_rating_set'
    EDIT_INVITES = 'edit_invites'

    # apply restrictions
    RESTRICT_SERVER_BAN = 'restrict_server_ban'
    RESTRICT_MIX_BAN = 'restrict_mix_ban'
    RESTRICT_TOURNAMENT_BAN = 'restrict_tournament_ban'
    RESTRICT_SELF_EDIT_NAME = 'restrict_self_edit_name'

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
    def check_permission(mask: int, permission: "PERMISSION | str") -> bool:
        if isinstance(permission, str):
            permission = PERMISSION(permission)
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
