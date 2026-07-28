"""CustomRating ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .custom import Custom
    from .game_role import GameRole


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class CustomRating(Base):
    __tablename__ = 'custom_rating_table'
    __table_args__ = (
        UniqueConstraint('custom_id', 'game_role_id', name='uq_custom_gamerole_pair'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    custom_id: Mapped[UUID] = mapped_column(ForeignKey('custom_table.id', ondelete='CASCADE'))
    game_role_id: Mapped[UUID] = mapped_column(ForeignKey('game_role_table.id', ondelete='CASCADE'))
    rating: Mapped[int] = mapped_column()

    custom: Mapped[Custom] = relationship(back_populates='custom_ratings', lazy="selectin")
    game_role: Mapped[GameRole] = relationship(back_populates='custom_ratings', lazy="selectin")
