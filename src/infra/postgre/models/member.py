"""Member ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .custom import Custom
    from .member_restriction import MemberRestriction
    from .server import Server
    from .server_role import ServerRole


import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Member(Base):
    __tablename__ = 'member_table'
    __table_args__ = (
        UniqueConstraint('server_id', 'user_id', name='uq_member_server_user'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    nickname: Mapped[str] = mapped_column(String(128))
    server_role_id: Mapped[UUID | None] = mapped_column(ForeignKey('server_role_table.id', ondelete='SET NULL'),
                                                        nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    active: Mapped[bool] = mapped_column(default=True)

    server: Mapped[Server] = relationship(back_populates='members', lazy="selectin")
    server_role: Mapped[ServerRole] = relationship(lazy="selectin")
    customs: Mapped[list[Custom]] = relationship(back_populates='member', foreign_keys='[Custom.member_id]',
                                                   lazy="selectin")
    restrictions: Mapped[list[MemberRestriction]] = relationship(
        back_populates='member',
        foreign_keys='[MemberRestriction.member_id]',
        cascade='all, delete-orphan',
        lazy="selectin"
    )
