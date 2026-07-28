"""MemberRestriction ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .member import Member
    from .restriction import Restriction


import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class MemberRestriction(Base):
    __tablename__ = 'member_restriction_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='CASCADE'))
    restriction_id: Mapped[UUID] = mapped_column(ForeignKey('restriction_table.id', ondelete='RESTRICT'))
    creator_id: Mapped[UUID | None] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)
    reason: Mapped[str] = mapped_column()
    expiration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    member: Mapped[Member] = relationship(back_populates='restrictions', foreign_keys=[member_id], lazy="selectin")
    restriction: Mapped[Restriction] = relationship(back_populates='member_restrictions', lazy="selectin")
    creator: Mapped[Member] = relationship(foreign_keys=[creator_id], lazy="selectin")
