"""Server ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .game_role_set import GameRoleSet
    from .invite import Invite
    from .member import Member
    from .rating_set import RatingSet
    from .server_game import ServerGame
    from .server_role import ServerRole


import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Server(Base):
    __tablename__ = 'server_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column(default="")
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    banner_id: Mapped[UUID | None] = mapped_column(nullable=True)
    owner_id: Mapped[UUID] = mapped_column()
    public: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role_set: Mapped[GameRoleSet] = relationship(back_populates='server', uselist=False, lazy="selectin",
                                                   cascade="all, delete-orphan")
    rating_set: Mapped[RatingSet] = relationship(back_populates='server', uselist=False, lazy="selectin",
                                                   cascade="all, delete-orphan")
    members: Mapped[list[Member]] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                   lazy="selectin")
    server_games: Mapped[list[ServerGame]] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                            lazy="selectin")
    server_roles: Mapped[list[ServerRole]] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                            lazy="selectin")
    invites: Mapped[list[Invite]] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                   lazy="selectin")

    games: Mapped[list[Game]] = relationship(
        'Game',
        secondary='server_game',
        back_populates='servers',
        viewonly=True,
        lazy="selectin"
    )
