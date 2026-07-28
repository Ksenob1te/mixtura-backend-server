"""Permission ORM model."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .server_role import ServerRole


import uuid
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..engine import Base


class Permission(Base):
    __tablename__ = 'permission_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(unique=True)
    roles: Mapped[list[ServerRole]] = relationship(
        'ServerRole',
        secondary='server_role_permission',
        back_populates='permissions_list',
        viewonly=True,
        lazy="selectin"
    )
