"""Rating ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rating_set import RatingSet


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Rating(Base):
    __tablename__ = 'rating_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    threshold: Mapped[int] = mapped_column()
    rating_set_id: Mapped[UUID] = mapped_column(ForeignKey('rating_set_table.id', ondelete='CASCADE'))

    rating_set: Mapped[RatingSet] = relationship(back_populates='ratings', lazy="selectin")
