from uuid import UUID
from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from . import Base

class GameRoleSet(Base):
    __tablename__ = 'role_sets'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    is_global: Mapped[bool] = mapped_column()

    game_roles: Mapped[list['GameRole']] = relationship(
        back_populates='role_set')


class GameRole(Base):
    __tablename__ = 'game_roles'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    role_set_id: Mapped[UUID] = mapped_column(ForeignKey('role_sets.id'))
    icon_url: Mapped[str] = mapped_column()
    min_in_team: Mapped[int] = mapped_column()
    max_in_team: Mapped[int] = mapped_column()
    hidden: Mapped[bool] = mapped_column()

    role_set: Mapped['GameRoleSet'] = relationship(back_populates='game_roles')
    custom_ratings: Mapped[list['CustomRating']
                           ] = relationship(back_populates='game_role')


class RatingSet(Base):
    __tablename__ = 'rating_sets'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    min_rating: Mapped[int] = mapped_column()
    max_rating: Mapped[int] = mapped_column()
    is_global: Mapped[bool] = mapped_column()

    ratings: Mapped[list['Rating']] = relationship(back_populates='rating_set')
    servers: Mapped[list['Server']] = relationship(back_populates='rating_set')


class Rating(Base):
    __tablename__ = 'ratings'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    icon_url: Mapped[str] = mapped_column()
    threshold: Mapped[int] = mapped_column()
    rating_set_id: Mapped[UUID] = mapped_column(ForeignKey('rating_sets.id'))

    rating_set: Mapped['RatingSet'] = relationship(back_populates='ratings')


class Server(Base):
    __tablename__ = 'servers'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    icon_url: Mapped[str] = mapped_column()
    banner_url: Mapped[str] = mapped_column()
    owner_id: Mapped[UUID] = mapped_column()
    rating_set_id: Mapped[UUID] = mapped_column(ForeignKey('rating_sets.id'))
    role_set_id: Mapped[UUID] = mapped_column(ForeignKey('role_sets.id'))
    public: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    rating_set: Mapped['RatingSet'] = relationship(back_populates='servers')
    role_set: Mapped['GameRoleSet'] = relationship()
    members: Mapped[list['Member']] = relationship(back_populates='server')
    server_games: Mapped[list['ServerGame']
                         ] = relationship(back_populates='server')
    server_roles: Mapped[list['ServerRole']
                         ] = relationship(back_populates='server')
    invites: Mapped[list['Invite']] = relationship(back_populates='server')


class Member(Base):
    __tablename__ = 'members'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('servers.id'))
    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    server_role_id: Mapped[UUID] = mapped_column(ForeignKey('server_roles.id'))
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())

    server: Mapped['Server'] = relationship(back_populates='members')
    server_role: Mapped['ServerRole'] = relationship()
    customs: Mapped[list['Custom']] = relationship(back_populates='member')
    restrictions: Mapped[list['Restriction']
                         ] = relationship(back_populates='member')


class Custom(Base):
    __tablename__ = 'customs'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('members.id'))
    creator_id: Mapped[UUID] = mapped_column(ForeignKey('members.id'))

    member: Mapped['Member'] = relationship(
        back_populates='customs', foreign_keys=[member_id])
    creator: Mapped['Member'] = relationship(foreign_keys=[creator_id])
    custom_ratings: Mapped[list['CustomRating']
                           ] = relationship(back_populates='custom')


class CustomRating(Base):
    __tablename__ = 'custom_ratings'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    custom_id: Mapped[UUID] = mapped_column(ForeignKey('customs.id'))
    game_role_id: Mapped[UUID] = mapped_column(ForeignKey('game_roles.id'))
    rating: Mapped[int] = mapped_column()

    custom: Mapped['Custom'] = relationship(back_populates='custom_ratings')
    game_role: Mapped['GameRole'] = relationship(
        back_populates='custom_ratings')


class ServerGame(Base):
    __tablename__ = 'server_games'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('servers.id'))
    game_id: Mapped[UUID] = mapped_column(ForeignKey('games.id'))

    server: Mapped['Server'] = relationship(back_populates='server_games')
    game: Mapped['Game'] = relationship(back_populates='server_games')


class Game(Base):
    __tablename__ = 'games'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    icon_url: Mapped[str] = mapped_column()
    banner_url: Mapped[str] = mapped_column()

    server_games: Mapped[list['ServerGame']
                         ] = relationship(back_populates='game')


class ServerRole(Base):
    __tablename__ = 'server_roles'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('servers.id'))
    name: Mapped[str] = mapped_column()
    position: Mapped[int] = mapped_column()

    server: Mapped['Server'] = relationship(back_populates='server_roles')
    permissions: Mapped[list['ServerRolePermission']
                        ] = relationship(back_populates='server_role')


class Restriction(Base):
    __tablename__ = 'restrictions'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    member_id: Mapped[UUID] = mapped_column(ForeignKey('members.id'))
    reason: Mapped[str] = mapped_column()
    expiration_date: Mapped[datetime] = mapped_column()
    type_code: Mapped[str] = mapped_column()

    member: Mapped['Member'] = relationship(back_populates='restrictions')


class ServerRolePermission(Base):
    __tablename__ = 'server_role_permissions'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    admin_role_id: Mapped[UUID] = mapped_column(ForeignKey('server_roles.id'))
    permission_id: Mapped[UUID] = mapped_column(ForeignKey('permissions.id'))

    server_role: Mapped['ServerRole'] = relationship(
        back_populates='permissions')
    permission: Mapped['Permission'] = relationship()


class Permission(Base):
    __tablename__ = 'permissions'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code_name: Mapped[str] = mapped_column()


class Invite(Base):
    __tablename__ = 'invites'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(ForeignKey('servers.id'))
    inviter_id: Mapped[UUID] = mapped_column(ForeignKey('members.id'))
    key: Mapped[str] = mapped_column()
    use_limit: Mapped[int] = mapped_column()

    server: Mapped['Server'] = relationship(back_populates='invites')
    inviter: Mapped['Member'] = relationship()
