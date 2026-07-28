"""Custom ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .custom_rating import CustomRating
    from .member import Member


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Custom(Base):
    __tablename__ = 'custom_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='CASCADE'))
    creator_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)

    member: Mapped[Member] = relationship(back_populates='customs', foreign_keys=[member_id], lazy="selectin")
    creator: Mapped[Member] = relationship(foreign_keys=[creator_id], lazy="selectin")
    custom_ratings: Mapped[list[CustomRating]] = relationship(back_populates='custom', lazy="selectin")
