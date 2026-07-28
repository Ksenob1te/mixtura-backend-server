"""Game ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .server import Server
    from .server_game import ServerGame


import uuid
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Game(Base):
    __tablename__ = 'game_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    icon_id: Mapped[UUID] = mapped_column()
    banner_id: Mapped[UUID] = mapped_column()

    server_games: Mapped[list[ServerGame]] = relationship(back_populates='game', lazy="selectin")

    servers: Mapped[list[Server]] = relationship(
        'Server',
        secondary='server_game',
        back_populates='games',
        viewonly=True,
        lazy="selectin"
    )
