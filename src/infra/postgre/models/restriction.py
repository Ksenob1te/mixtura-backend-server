"""Restriction ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .member_restriction import MemberRestriction


import uuid
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Restriction(Base):
    __tablename__ = 'restriction_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(128), unique=True)

    member_restrictions: Mapped[list[MemberRestriction]] = relationship(back_populates='restriction', lazy="selectin")
