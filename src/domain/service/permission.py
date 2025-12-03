from typing import Iterable

from src.infra.postgre.static import PERMISSION
from src.infra.postgre.repo.server_role import ServerRoleRepository
from src.infra.postgre.models import Member


class PermissionService:
    def __init__(self, server_role_repo: ServerRoleRepository):
        self.server_role_repo = server_role_repo

    @staticmethod
    def _serialize_permission_codes(permissions: Iterable[PERMISSION]) -> int:
        mask = 0
        for i, member in enumerate(PERMISSION):
            if member in permissions:
                mask |= (1 << i)
        return mask

    @staticmethod
    def _deserialize_permission_codes(mask: int) -> set[PERMISSION]:
        permissions = set()
        for i, member in enumerate(PERMISSION):
            if mask & (1 << i):
                permissions.add(member)
        return permissions

    @staticmethod
    def _check_permission(mask: int, permission: PERMISSION) -> bool:
        index = list(PERMISSION).index(permission)
        return (mask & (1 << index)) != 0


    # def get_permissions_for_member(self, member: Member) -> int:
    #     if member.server_role is None:
    #         return 0
        # member.server_role.permissions

