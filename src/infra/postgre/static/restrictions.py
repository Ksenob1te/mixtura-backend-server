from enum import StrEnum
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.postgre.repo import RestrictionRepository

from typing import Iterable

logger = logging.getLogger(__name__)


class RESTRICTION(StrEnum):
    SERVER_BAN = 'server_ban'
    MIX_BAN = 'mix_ban'
    TOURNAMENT_BAN = 'tournament_ban'
    SELF_EDIT = 'self_edit'

    @staticmethod
    def serialize_restriction_codes(restrictions: Iterable["RESTRICTION"]) -> int:
        mask = 0
        for i, member in enumerate(RESTRICTION):
            if member in restrictions:
                mask |= (1 << i)
        return mask

    @staticmethod
    def deserialize_restriction_codes(mask: int) -> set["RESTRICTION"]:
        restrictions = set()
        for i, member in enumerate(RESTRICTION):
            if mask & (1 << i):
                restrictions.add(member)
        return restrictions

    @staticmethod
    def check_restriction(mask: int, restriction: "RESTRICTION") -> bool:
        index = list(RESTRICTION).index(restriction)
        return (mask & (1 << index)) != 0


async def init_restrictions(session: AsyncSession) -> None:
    repo = RestrictionRepository(session)
    created_codes: list[str] = []
    existing_perms = await repo.get_by_code_bulk([r for r in RESTRICTION])
    existing_codes = {p.code for p in existing_perms}
    for r in RESTRICTION:
        if r.value not in existing_codes:
            await repo.create(r)
            created_codes.append(r)
    if created_codes:
        logger.info(f"Initialized restrictions: {', '.join(created_codes)}")
