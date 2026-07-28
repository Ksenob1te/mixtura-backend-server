from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.core.models.member_restriction import (
    MemberRestriction,
    MemberRestrictionCreate,
)


class MemberRestrictionRepositoryProtocol(Protocol):
    async def get(self, restriction_id: UUID, /) -> MemberRestriction | None: ...
    async def list_for_member(self, member_id: UUID) -> Sequence[MemberRestriction]: ...
    async def create(self, dto: MemberRestrictionCreate) -> MemberRestriction: ...
    async def delete(self, restriction_id: UUID, /) -> bool: ...
