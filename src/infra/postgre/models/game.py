"""Game ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_role_set import GameRoleSet
    from .rating_set import RatingSet
    from .server import Server
    from .server_game import ServerGame


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Game(Base):
    __tablename__ = 'game_table'
    __table_args__ = (
        UniqueConstraint('server_id', 'name', name='uq_game_server_name'),
        Index('uq_game_global_name', 'name', unique=True, postgresql_where=text('server_id IS NULL')),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    banner_id: Mapped[UUID | None] = mapped_column(nullable=True)
    server_id: Mapped[UUID | None] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'), nullable=True)

    server: Mapped[Server | None] = relationship(back_populates='owned_games', lazy="selectin")
    role_set: Mapped[GameRoleSet] = relationship(back_populates='game', uselist=False, lazy="selectin",
                                                   cascade="all, delete-orphan")
    rating_set: Mapped[RatingSet] = relationship(back_populates='game', uselist=False, lazy="selectin",
                                                   cascade="all, delete-orphan")

    server_games: Mapped[list[ServerGame]] = relationship(back_populates='game', lazy="selectin")

    servers: Mapped[list[Server]] = relationship(
        'Server',
        secondary='server_game',
        back_populates='games',
        viewonly=True,
        lazy="selectin"
    )
