"""ServerRolePermission ORM model (junction table)."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .permission import Permission
    from .server_role import ServerRole


import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class ServerRolePermission(Base):
    __tablename__ = 'server_role_permission'
    __table_args__ = (
        UniqueConstraint('server_role_id', 'permission_id', name='uq_role_permission_pair'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_role_id: Mapped[UUID] = mapped_column(ForeignKey('server_role_table.id', ondelete='CASCADE'))
    permission_id: Mapped[UUID] = mapped_column(ForeignKey('permission_table.id', ondelete='CASCADE'))

    server_role: Mapped[ServerRole] = relationship(back_populates='permissions', lazy="selectin")
    permission: Mapped[Permission] = relationship(lazy="selectin")
