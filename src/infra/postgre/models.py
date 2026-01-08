from enum import unique
from uuid import UUID
from datetime import datetime, time, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func, String, UniqueConstraint, DateTime
from . import Base


class GameRoleSet(Base):
    __tablename__ = 'role_set_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    is_global: Mapped[bool] = mapped_column(default=False)

    game_roles: Mapped[list['GameRole']] = relationship(
        back_populates='role_set',
        cascade='all, delete-orphan',
        lazy="selectin"
    )


class GameRole(Base):
    __tablename__ = 'game_role_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    role_set_id: Mapped[UUID] = mapped_column(ForeignKey('role_set_table.id', ondelete='CASCADE'))
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    min_in_team: Mapped[int] = mapped_column()
    max_in_team: Mapped[int] = mapped_column()
    hidden: Mapped[bool] = mapped_column(default=False)

    role_set: Mapped['GameRoleSet'] = relationship(back_populates='game_roles', lazy="selectin")
    custom_ratings: Mapped[list['CustomRating']] = relationship(back_populates='game_role', lazy="selectin")


class RatingSet(Base):
    __tablename__ = 'rating_set_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    min_rating: Mapped[int] = mapped_column()
    max_rating: Mapped[int] = mapped_column()
    is_global: Mapped[bool] = mapped_column()

    ratings: Mapped[list['Rating']] = relationship(
        back_populates='rating_set',
        cascade='all, delete-orphan',
        lazy="selectin"
    )


class Rating(Base):
    __tablename__ = 'rating_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    threshold: Mapped[int] = mapped_column()
    rating_set_id: Mapped[UUID] = mapped_column(ForeignKey('rating_set_table.id', ondelete='CASCADE'))

    rating_set: Mapped['RatingSet'] = relationship(back_populates='ratings', lazy="selectin")


class Server(Base):
    __tablename__ = 'server_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(default="")
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    banner_id: Mapped[UUID | None] = mapped_column(nullable=True)
    owner_id: Mapped[UUID] = mapped_column()
    public: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    role_set_id: Mapped[UUID] = mapped_column(ForeignKey('role_set_table.id', ondelete='RESTRICT'))
    rating_set_id: Mapped[UUID] = mapped_column(ForeignKey('rating_set_table.id', ondelete='RESTRICT'))

    role_set: Mapped['GameRoleSet'] = relationship(uselist=False, lazy="selectin", cascade="all, delete")
    rating_set: Mapped['RatingSet'] = relationship(uselist=False, lazy="selectin", cascade="all, delete")
    members: Mapped[list['Member']] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                   lazy="selectin")
    server_games: Mapped[list['ServerGame']] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                            lazy="selectin")
    server_roles: Mapped[list['ServerRole']] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                            lazy="selectin")
    invites: Mapped[list['Invite']] = relationship(back_populates='server', cascade='all, delete-orphan',
                                                   lazy="selectin")

    games: Mapped[list['Game']] = relationship(
        'Game',
        secondary='server_game',
        back_populates='servers',
        viewonly=True,
        lazy="selectin"
    )


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

    server: Mapped['Server'] = relationship(back_populates='members', lazy="selectin")
    server_role: Mapped['ServerRole'] = relationship(lazy="selectin")
    customs: Mapped[list['Custom']] = relationship(back_populates='member', foreign_keys='[Custom.member_id]',
                                                   lazy="selectin")
    restrictions: Mapped[list['MemberRestriction']] = relationship(
        back_populates='member',
        foreign_keys='[MemberRestriction.member_id]',
        cascade='all, delete-orphan',
        lazy="selectin"
    )


class Custom(Base):
    __tablename__ = 'custom_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='CASCADE'))
    creator_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)

    member: Mapped['Member'] = relationship(back_populates='customs', foreign_keys=[member_id], lazy="selectin")
    creator: Mapped['Member'] = relationship(foreign_keys=[creator_id], lazy="selectin")
    custom_ratings: Mapped[list['CustomRating']] = relationship(back_populates='custom', lazy="selectin")


class CustomRating(Base):
    __tablename__ = 'custom_rating_table'
    __table_args__ = (
        UniqueConstraint('custom_id', 'game_role_id', name='uq_custom_gamerole_pair'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    custom_id: Mapped[UUID] = mapped_column(ForeignKey('custom_table.id', ondelete='CASCADE'))
    game_role_id: Mapped[UUID] = mapped_column(ForeignKey('game_role_table.id', ondelete='CASCADE'))
    rating: Mapped[int] = mapped_column()

    custom: Mapped['Custom'] = relationship(back_populates='custom_ratings', lazy="selectin")
    game_role: Mapped['GameRole'] = relationship(back_populates='custom_ratings', lazy="selectin")


class ServerGame(Base):
    __tablename__ = 'server_game'
    __table_args__ = (
        UniqueConstraint('server_id', 'game_id', name='uq_server_game_pair'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    game_id: Mapped[UUID] = mapped_column(ForeignKey('game_table.id', ondelete='CASCADE'))

    server: Mapped['Server'] = relationship(back_populates='server_games', lazy="selectin")
    game: Mapped['Game'] = relationship(back_populates='server_games', lazy="selectin")


class Game(Base):
    __tablename__ = 'game_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    icon_id: Mapped[UUID] = mapped_column()
    banner_id: Mapped[UUID] = mapped_column()

    server_games: Mapped[list['ServerGame']] = relationship(back_populates='game', lazy="selectin")

    servers: Mapped[list['Server']] = relationship(
        'Server',
        secondary='server_game',
        back_populates='games',
        viewonly=True,
        lazy="selectin"
    )


class ServerRole(Base):
    __tablename__ = 'server_role_table'
    __table_args__ = (UniqueConstraint('server_id', 'name', name='uq_server_role_name_per_server'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(128))
    position: Mapped[int] = mapped_column()

    server: Mapped['Server'] = relationship(back_populates='server_roles', lazy="selectin")
    permissions: Mapped[list['ServerRolePermission']] = relationship(
        back_populates='server_role',
        cascade='all, delete-orphan',
        lazy="selectin"
    )

    permissions_list: Mapped[list['Permission']] = relationship(
        'Permission',
        secondary='server_role_permission',
        back_populates='roles',
        viewonly=True,
        lazy="selectin"
    )


class MemberRestriction(Base):
    __tablename__ = 'member_restriction_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='CASCADE'))
    restriction_id: Mapped[UUID] = mapped_column(ForeignKey('restriction_table.id', ondelete='RESTRICT'))
    creator_id: Mapped[UUID | None] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)
    reason: Mapped[str] = mapped_column()
    expiration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    member: Mapped['Member'] = relationship(back_populates='restrictions', foreign_keys=[member_id], lazy="selectin")
    restriction: Mapped['Restriction'] = relationship(back_populates='member_restrictions', lazy="selectin")
    creator: Mapped['Member'] = relationship(foreign_keys=[creator_id], lazy="selectin")


class Restriction(Base):
    __tablename__ = 'restriction_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(128), unique=True)

    member_restrictions: Mapped[list['MemberRestriction']] = relationship(back_populates='restriction', lazy="selectin")


class ServerRolePermission(Base):
    __tablename__ = 'server_role_permission'
    __table_args__ = (
        UniqueConstraint('server_role_id', 'permission_id', name='uq_role_permission_pair'),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    server_role_id: Mapped[UUID] = mapped_column(ForeignKey('server_role_table.id', ondelete='CASCADE'))
    permission_id: Mapped[UUID] = mapped_column(ForeignKey('permission_table.id', ondelete='CASCADE'))

    server_role: Mapped['ServerRole'] = relationship(back_populates='permissions', lazy="selectin")
    permission: Mapped['Permission'] = relationship(lazy="selectin")


class Permission(Base):
    __tablename__ = 'permission_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(unique=True)
    roles: Mapped[list['ServerRole']] = relationship(
        'ServerRole',
        secondary='server_role_permission',
        back_populates='permissions_list',
        viewonly=True,
        lazy="selectin"
    )


class Invite(Base):
    __tablename__ = 'invite_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    inviter_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)
    key: Mapped[str] = mapped_column(unique=True)
    use_limit: Mapped[int] = mapped_column()

    server: Mapped['Server'] = relationship(back_populates='invites', lazy="selectin")
    inviter: Mapped['Member'] = relationship(lazy="selectin")
