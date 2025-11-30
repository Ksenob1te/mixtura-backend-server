from enum import StrEnum
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.postgre.repo.permission import PermissionRepository

logger = logging.getLogger(__name__)


class PERMISSION(StrEnum):
    SELF_EDIT = 'self_edit'
    MANAGE_MEMBERS = 'manage_members'
    MANAGE_ROLES = 'manage_roles'
    MANAGE_CHANNELS = 'manage_channels'
    MANAGE_SERVER = 'manage_server'


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
