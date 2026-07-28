"""Invite ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .member import Member
    from .server import Server


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Invite(Base):
    __tablename__ = 'invite_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    inviter_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)
    key: Mapped[str] = mapped_column(unique=True)
    use_limit: Mapped[int] = mapped_column()

    server: Mapped[Server] = relationship(back_populates='invites', lazy="selectin")
    inviter: Mapped[Member] = relationship(lazy="selectin")
