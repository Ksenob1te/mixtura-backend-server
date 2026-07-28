"""GameRoleSet ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_role import GameRole
    from .server import Server


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class GameRoleSet(Base):
    __tablename__ = 'role_set_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    is_global: Mapped[bool] = mapped_column(default=False)
    server_id: Mapped[UUID | None] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'), nullable=True)

    server: Mapped[Server] = relationship(back_populates='role_set')

    game_roles: Mapped[list[GameRole]] = relationship(
        back_populates='role_set',
        cascade='all, delete-orphan',
        lazy="selectin"
    )
