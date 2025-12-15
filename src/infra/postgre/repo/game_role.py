from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..models import GameRole

from ..exceptions import IntegrityUnknownException, IntegrityForeignException, IntegrityUniqueException


class GameRoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, role_id: UUID) -> GameRole | None:
        stmt = select(GameRole).where(GameRole.id == role_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_set(self, role_set_id: UUID) -> Sequence[GameRole]:
        stmt = select(GameRole).where(GameRole.role_set_id == role_set_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, name: str, role_set_id: UUID, min_in_team: int, max_in_team: int,
                     icon_url: str | None = None, icon_id: UUID | None = None, hidden: bool = False) -> GameRole:
        role = GameRole(
            name=name,
            role_set_id=role_set_id,
            min_in_team=min_in_team,
            max_in_team=max_in_team,
            icon_url=icon_url,
            icon_id=icon_id,
            hidden=hidden
        )
        try:
            self.session.add(role)
            await self.session.flush()
            game_role_field = await self.get_by_id(role.id)
            if game_role_field is None:
                raise IntegrityUnknownException("Failed to create game role")
            return game_role_field
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Role set field is not found")
            raise IntegrityUnknownException("Failed to create game role")

    async def set_name(self, role: GameRole, name: str) -> GameRole:
        role.name = name
        self.session.add(role)
        await self.session.flush()
        return role

    async def set_icon(self, role: GameRole, icon_url: str | None, icon_id: UUID | None) -> GameRole:
        role.icon_url = icon_url
        role.icon_id = icon_id
        self.session.add(role)
        await self.session.flush()
        return role

    async def set_hidden(self, role: GameRole, hidden: bool) -> GameRole:
        role.hidden = hidden
        self.session.add(role)
        await self.session.flush()
        return role

    async def set_min(self, role: GameRole, min_in_team: int) -> GameRole:
        role.min_in_team = min_in_team
        if role.max_in_team < min_in_team:
            role.min_in_team = role.max_in_team
        self.session.add(role)
        await self.session.flush()
        return role

    async def set_max(self, role: GameRole, max_in_team: int) -> GameRole:
        role.max_in_team = max_in_team
        if role.min_in_team > max_in_team:
            role.max_in_team = role.min_in_team
        self.session.add(role)
        await self.session.flush()
        return role

    async def delete(self, role_id: UUID) -> bool:
        stmt = delete(GameRole).where(GameRole.id == role_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def copy_role(self, template_role: GameRole, new_role_set_id: UUID) -> GameRole | None:
        # TODO: add tests for this method
        # TODO: add error handling here as well
        role = GameRole(
            name=template_role.name,
            role_set_id=new_role_set_id,
            min_in_team=template_role.min_in_team,
            max_in_team=template_role.max_in_team,
            icon_url=template_role.icon_url,
            icon_id=template_role.icon_id,
            hidden=template_role.hidden
        )
        self.session.add(role)
        await self.session.flush()
        return await self.get_by_id(role.id)

