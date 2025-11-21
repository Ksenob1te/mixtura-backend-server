from uuid import UUID
from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func, String, UniqueConstraint, null
from . import Base


class GameRoleSet(Base):
    __tablename__ = 'role_set_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    is_global: Mapped[bool] = mapped_column(default=False)

    game_roles: Mapped[list['GameRole']] = relationship(
        back_populates='role_set',
        cascade='all, delete-orphan'
    )


class GameRole(Base):
    __tablename__ = 'game_role_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    role_set_id: Mapped[UUID] = mapped_column(ForeignKey('role_set_table.id', ondelete='CASCADE'))
    icon_url: Mapped[str | None] = mapped_column(nullable=True)
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    min_in_team: Mapped[int] = mapped_column()
    max_in_team: Mapped[int] = mapped_column()
    hidden: Mapped[bool] = mapped_column(default=False)

    role_set: Mapped['GameRoleSet'] = relationship(back_populates='game_roles')
    custom_ratings: Mapped[list['CustomRating']] = relationship(back_populates='game_role')


class RatingSet(Base):
    __tablename__ = 'rating_set_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    min_rating: Mapped[int] = mapped_column()
    max_rating: Mapped[int] = mapped_column()
    is_global: Mapped[bool] = mapped_column()

    ratings: Mapped[list['Rating']] = relationship(
        back_populates='rating_set',
        cascade='all, delete-orphan'
    )


class Rating(Base):
    __tablename__ = 'rating_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    icon_url: Mapped[str] = mapped_column()
    icon_id: Mapped[UUID] = mapped_column()
    threshold: Mapped[int] = mapped_column()
    rating_set_id: Mapped[UUID] = mapped_column(ForeignKey('rating_set_table.id', ondelete='CASCADE'))

    rating_set: Mapped['RatingSet'] = relationship(back_populates='ratings')


class Server(Base):
    __tablename__ = 'server_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(default="")
    icon_url: Mapped[str | None] = mapped_column(nullable=True)
    icon_id: Mapped[UUID | None] = mapped_column(nullable=True)
    banner_url: Mapped[str | None] = mapped_column(nullable=True)
    banner_id: Mapped[UUID | None] = mapped_column(nullable=True)
    owner_id: Mapped[UUID] = mapped_column()
    rating_set_id: Mapped[UUID | None] = mapped_column(ForeignKey('rating_set_table.id', ondelete='SET NULL'),
                                                       nullable=True)
    role_set_id: Mapped[UUID | None] = mapped_column(ForeignKey('role_set_table.id', ondelete='SET NULL'),
                                                     nullable=True)
    public: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    rating_set: Mapped['RatingSet'] = relationship(back_populates='servers')
    role_set: Mapped['GameRoleSet'] = relationship()
    members: Mapped[list['Member']] = relationship(back_populates='server', cascade='all, delete-orphan')
    server_games: Mapped[list['ServerGame']] = relationship(back_populates='server', cascade='all, delete-orphan')
    server_roles: Mapped[list['ServerRole']] = relationship(back_populates='server', cascade='all, delete-orphan')
    invites: Mapped[list['Invite']] = relationship(back_populates='server', cascade='all, delete-orphan')

    games: Mapped[list['Game']] = relationship(
        'Game',
        secondary='server_game',
        back_populates='servers',
        viewonly=True
    )


class Member(Base):
    __tablename__ = 'member_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    server_role_id: Mapped[UUID] = mapped_column(ForeignKey('server_role_table.id', ondelete='SET NULL'), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())
    active: Mapped[bool] = mapped_column(default=True)

    server: Mapped['Server'] = relationship(back_populates='members')
    server_role: Mapped['ServerRole'] = relationship()
    customs: Mapped[list['Custom']] = relationship(back_populates='member')
    restrictions: Mapped[list['Restriction']] = relationship(
        back_populates='member',
        cascade='all, delete-orphan'
    )


class Custom(Base):
    __tablename__ = 'custom_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='CASCADE'))
    creator_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)

    member: Mapped['Member'] = relationship(
        back_populates='customs', foreign_keys=[member_id])
    creator: Mapped['Member'] = relationship(foreign_keys=[creator_id])
    custom_ratings: Mapped[list['CustomRating']] = relationship(back_populates='custom')


class CustomRating(Base):
    __tablename__ = 'custom_rating_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    custom_id: Mapped[UUID] = mapped_column(ForeignKey('custom_table.id'))
    game_role_id: Mapped[UUID] = mapped_column(ForeignKey('game_role_table.id'))
    rating: Mapped[int] = mapped_column()

    custom: Mapped['Custom'] = relationship(back_populates='custom_ratings')
    game_role: Mapped['GameRole'] = relationship(back_populates='custom_ratings')


class ServerGame(Base):
    __tablename__ = 'server_game'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    game_id: Mapped[UUID] = mapped_column(ForeignKey('game_table.id', ondelete='CASCADE'))

    server: Mapped['Server'] = relationship(back_populates='server_game')
    game: Mapped['Game'] = relationship(back_populates='server_game')


class Game(Base):
    __tablename__ = 'game_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    icon_url: Mapped[str] = mapped_column()
    banner_url: Mapped[str] = mapped_column()

    server_games: Mapped[list['ServerGame']] = relationship(back_populates='game')

    servers: Mapped[list['Server']] = relationship(
        'Server',
        secondary='server_game',
        back_populates='games',
        viewonly=True
    )


class ServerRole(Base):
    __tablename__ = 'server_role_table'
    __table_args__ = (UniqueConstraint('server_id', 'name', name='uq_server_role_name_per_server'),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(128))
    position: Mapped[int] = mapped_column()

    server: Mapped['Server'] = relationship(back_populates='server_roles')
    permissions: Mapped[list['ServerRolePermission']] = relationship(
        back_populates='server_role',
        cascade='all, delete-orphan'
    )

    permissions_list: Mapped[list['Permission']] = relationship(
        'Permission',
        secondary='server_role_permission',
        back_populates='roles',
        viewonly=True
    )


class Restriction(Base):
    __tablename__ = 'restriction_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='CASCADE'))
    reason: Mapped[str] = mapped_column()
    expiration_date: Mapped[datetime] = mapped_column()
    type_code: Mapped[str] = mapped_column()

    member: Mapped['Member'] = relationship(back_populates='restrictions')


class ServerRolePermission(Base):
    __tablename__ = 'server_role_permission'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    server_role_id: Mapped[UUID] = mapped_column(ForeignKey('server_role_table.id', ondelete='CASCADE'))
    permission_id: Mapped[UUID] = mapped_column(ForeignKey('permission_table.id', ondelete='CASCADE'))

    server_role: Mapped['ServerRole'] = relationship(back_populates='permissions')
    permission: Mapped['Permission'] = relationship()


class Permission(Base):
    __tablename__ = 'permission_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code_name: Mapped[str] = mapped_column(unique=True)
    roles: Mapped[list['ServerRole']] = relationship(
        'ServerRole',
        secondary='server_role_permission',
        back_populates='permissions_list',
        viewonly=True
    )


class Invite(Base):
    __tablename__ = 'invite_table'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('server_table.id', ondelete='CASCADE'))
    inviter_id: Mapped[UUID] = mapped_column(ForeignKey('member_table.id', ondelete='SET NULL'), nullable=True)
    key: Mapped[str] = mapped_column(unique=True)
    use_limit: Mapped[int] = mapped_column()

    server: Mapped['Server'] = relationship(back_populates='invites')
    inviter: Mapped['Member'] = relationship()
