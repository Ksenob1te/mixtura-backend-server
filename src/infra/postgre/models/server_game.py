"""ServerGame ORM model (junction table)."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .server import Server


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class ServerGame(Base):
    __tablename__ = 'server_game'
    __table_args__ = (
        UniqueConstraint('server_id', 'game_id', name='uq_server_game_pair'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    game_id: Mapped[UUID] = mapped_column(ForeignKey('game_table.id', ondelete='CASCADE'))

    server: Mapped[Server] = relationship(back_populates='server_games', lazy="selectin")
    game: Mapped[Game] = relationship(back_populates='server_games', lazy="selectin")
