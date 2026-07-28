"""RatingSet ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rating import Rating
    from .server import Server


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class RatingSet(Base):
    __tablename__ = 'rating_set_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    min_rating: Mapped[int] = mapped_column()
    max_rating: Mapped[int] = mapped_column()
    is_global: Mapped[bool] = mapped_column()
    server_id: Mapped[UUID | None] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'), nullable=True)

    server: Mapped[Server] = relationship(back_populates='rating_set')

    ratings: Mapped[list[Rating]] = relationship(
        back_populates='rating_set',
        cascade='all, delete-orphan',
        lazy="selectin"
    )
