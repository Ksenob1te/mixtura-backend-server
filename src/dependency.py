from faststream import Context, Depends

from .infra.postgre import DatabaseSessionManager
from .infra.redis import RedisSessionManager, RedisRepository
from .infra.postgre.repo import *

from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

import logging

from .domain.service.core import CoreService
from .domain.service.game import GameService
from .domain.service.game_role import GameRoleService
from .domain.service.invite import InviteService
from .domain.service.rating import RatingService

logger = logging.getLogger(__name__)


async def get_db_session(session_manager: Annotated[DatabaseSessionManager, Context()]):
    async with session_manager.session() as session:
        yield session


async def get_redis_session(redis_engine: Annotated[RedisSessionManager, Context()]):
    async with redis_engine.client() as redis:
        yield redis


async def get_redis_repository(redis: Annotated[Redis, Depends(get_redis_session)]):
    return RedisRepository(redis)


async def get_custom_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return CustomRepository(session)


async def get_custom_rating_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return CustomRatingRepository(session)


async def get_game_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return GameRepository(session)


async def get_game_role_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return GameRoleRepository(session)


async def get_game_role_set_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return GameRoleSetRepository(session)


async def get_invite_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return InviteRepository(session)


async def get_member_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return MemberRepository(session)


async def get_member_restriction_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return MemberRestrictionRepository(session)


async def get_permission_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return PermissionRepository(session)


async def get_rating_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return RatingRepository(session)


async def get_rating_set_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return RatingSetRepository(session)


async def get_restriction_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return RestrictionRepository(session)


async def get_server_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return ServerRepository(session)


async def get_server_role_repository(session: Annotated[AsyncSession, Depends(get_db_session)]):
    return ServerRoleRepository(session)


async def get_game_service(
        game_repo: Annotated[GameRepository, Depends(get_game_repository)],
        server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
) -> GameService:
    return GameService(
        game_repo=game_repo,
        server_repo=server_repo,
    )


async def get_core_service(
        server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
        game_repo: Annotated[GameRepository, Depends(get_game_repository)],
        game_role_repo: Annotated[GameRoleRepository, Depends(get_game_role_repository)],
        game_role_set_repo: Annotated[GameRoleSetRepository, Depends(get_game_role_set_repository)],
        rating_repo: Annotated[RatingRepository, Depends(get_rating_repository)],
        rating_set_repo: Annotated[RatingSetRepository, Depends(get_rating_set_repository)],
        permission_repo: Annotated[PermissionRepository, Depends(get_permission_repository)],
        restriction_repo: Annotated[RestrictionRepository, Depends(get_restriction_repository)],
        member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
) -> CoreService:
    return CoreService(
        server_repo=server_repo,
        game_repo=game_repo,
        game_role_repo=game_role_repo,
        game_role_set_repo=game_role_set_repo,
        rating_repo=rating_repo,
        rating_set_repo=rating_set_repo,
        permission_repo=permission_repo,
        restriction_repo=restriction_repo,
        member_repo=member_repo
    )


async def get_game_role_service(
        server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
        game_role_set_repo: Annotated[GameRoleSetRepository, Depends(get_game_role_set_repository)],
        game_role_repo: Annotated[GameRoleRepository, Depends(get_game_role_repository)],
) -> GameRoleService:
    return GameRoleService(
        server_repo=server_repo,
        role_set_repo=game_role_set_repo,
        role_repo=game_role_repo,
    )


async def get_invite_service(
        invite_repo: Annotated[InviteRepository, Depends(get_invite_repository)],
        server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
        member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
) -> InviteService:
    return InviteService(
        invite_repo=invite_repo,
        server_repo=server_repo,
        member_repo=member_repo,
    )


async def get_rating_service(
        rating_repo: Annotated[RatingRepository, Depends(get_rating_repository)],
        rating_set_repo: Annotated[RatingSetRepository, Depends(get_rating_set_repository)],
        server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
) -> RatingService:
    return RatingService(
        rating_repo=rating_repo,
        rating_set_repo=rating_set_repo,
        server_repo=server_repo
    )
# TODO: all services and repositories into dependency injection functions
