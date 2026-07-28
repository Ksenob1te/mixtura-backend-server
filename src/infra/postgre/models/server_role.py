"""ServerRole ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .permission import Permission
    from .server import Server
    from .server_role_permission import ServerRolePermission


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class ServerRole(Base):
    __tablename__ = 'server_role_table'
    __table_args__ = (UniqueConstraint('server_id', 'name', name='uq_server_role_name_per_server'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(128))
    position: Mapped[int] = mapped_column()

    server: Mapped[Server] = relationship(back_populates='server_roles', lazy="selectin")
    permissions: Mapped[list[ServerRolePermission]] = relationship(
        back_populates='server_role',
        cascade='all, delete-orphan',
        lazy="selectin"
    )

    permissions_list: Mapped[list[Permission]] = relationship(
        'Permission',
        secondary='server_role_permission',
        back_populates='roles',
        viewonly=True,
        lazy="selectin"
    )
