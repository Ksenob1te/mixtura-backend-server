"""GameRole ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .custom_rating import CustomRating
    from .game_role_set import GameRoleSet


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class GameRole(Base):
    __tablename__ = 'game_role_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    role_set_id: Mapped[UUID] = mapped_column(ForeignKey('role_set_table.id', ondelete='CASCADE'))
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    min_in_team: Mapped[int] = mapped_column()
    max_in_team: Mapped[int] = mapped_column()
    hidden: Mapped[bool] = mapped_column(default=False)

    role_set: Mapped[GameRoleSet] = relationship(back_populates='game_roles', lazy="selectin")
    custom_ratings: Mapped[list[CustomRating]] = relationship(back_populates='game_role', lazy="selectin")
