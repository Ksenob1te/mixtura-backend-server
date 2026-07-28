"""GameRoleSet ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .game_role import GameRole


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class GameRoleSet(Base):
    __tablename__ = 'role_set_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    game_id: Mapped[UUID] = mapped_column(ForeignKey('game_table.id', ondelete='CASCADE'), unique=True)

    game: Mapped[Game] = relationship(back_populates='role_set', lazy="selectin")

    game_roles: Mapped[list[GameRole]] = relationship(
        back_populates='role_set',
        cascade='all, delete-orphan',
        lazy="selectin"
    )
