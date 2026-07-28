import logging
from typing import Annotated

from faststream import Context, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from .core.services.access_control import AccessControlService
from .core.services.core import CoreService
from .core.services.game import GameService
from .core.services.game_role import GameRoleService
from .core.services.invite import InviteService
from .core.services.member import MemberService
from .core.services.member_custom import MemberCustomService
from .core.services.rating import RatingService
from .core.services.role import RoleService
from .infra.postgre import DatabaseSessionManager
from .infra.postgre.repo import *
from .infra.redis import RedisRepository, RedisSessionManager

logger = logging.getLogger(__name__)


async def get_db_session(session_manager: Annotated[DatabaseSessionManager, Context()]):
    async with session_manager.session() as session:
        yield session


async def get_redis_session(redis_engine: Annotated[RedisSessionManager, Context()]):
    async with redis_engine.client() as redis:
        yield redis


async def get_redis_repository(redis: Annotated[Redis, Depends(get_redis_session)]):
    return RedisRepository(redis)


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_custom_repository(
    session: DatabaseSession,
):
    return CustomRepository(session)


async def get_custom_rating_repository(
    session: DatabaseSession,
):
    return CustomRatingRepository(session)


async def get_game_repository(
    session: DatabaseSession,
):
    return GameRepository(session)


async def get_game_role_repository(
    session: DatabaseSession,
):
    return GameRoleRepository(session)


async def get_game_role_set_repository(
    session: DatabaseSession,
):
    return GameRoleSetRepository(session)


async def get_invite_repository(
    session: DatabaseSession,
):
    return InviteRepository(session)


async def get_member_repository(
    session: DatabaseSession,
):
    return MemberRepository(session)


async def get_member_restriction_repository(
    session: DatabaseSession,
):
    return MemberRestrictionRepository(session)


async def get_permission_repository(
    session: DatabaseSession,
):
    return PermissionRepository(session)


async def get_rating_repository(
    session: DatabaseSession,
):
    return RatingRepository(session)


async def get_rating_set_repository(
    session: DatabaseSession,
):
    return RatingSetRepository(session)


async def get_restriction_repository(
    session: DatabaseSession,
):
    return RestrictionRepository(session)


async def get_server_repository(
    session: DatabaseSession,
):
    return ServerRepository(session)


async def get_server_role_repository(
    session: DatabaseSession,
):
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
    game_role_set_repo: Annotated[
        GameRoleSetRepository, Depends(get_game_role_set_repository)
    ],
    rating_repo: Annotated[RatingRepository, Depends(get_rating_repository)],
    rating_set_repo: Annotated[RatingSetRepository, Depends(get_rating_set_repository)],
    permission_repo: Annotated[
        PermissionRepository, Depends(get_permission_repository)
    ],
    restriction_repo: Annotated[
        RestrictionRepository, Depends(get_restriction_repository)
    ],
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
        member_repo=member_repo,
    )


async def get_game_role_service(
    server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
    game_role_set_repo: Annotated[
        GameRoleSetRepository, Depends(get_game_role_set_repository)
    ],
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
        server_repo=server_repo,
    )


async def get_member_service(
    server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    server_role_repo: Annotated[
        ServerRoleRepository, Depends(get_server_role_repository)
    ],
) -> MemberService:
    return MemberService(
        server_repo=server_repo,
        member_repo=member_repo,
        server_role_repo=server_role_repo,
    )


async def get_member_custom_service(
    custom_repo: Annotated[CustomRepository, Depends(get_custom_repository)],
    custom_rating_repo: Annotated[
        CustomRatingRepository, Depends(get_custom_rating_repository)
    ],
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    game_role_repo: Annotated[GameRoleRepository, Depends(get_game_role_repository)],
    server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
    rating_set_repo: Annotated[
        RatingSetRepository, Depends(get_rating_set_repository)
    ],
) -> MemberCustomService:
    return MemberCustomService(
        custom_repo=custom_repo,
        custom_rating_repo=custom_rating_repo,
        member_repo=member_repo,
        game_role_repo=game_role_repo,
        server_repo=server_repo,
        rating_set_repo=rating_set_repo,
    )


async def get_access_control_service(
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    member_restriction_repo: Annotated[
        MemberRestrictionRepository, Depends(get_member_restriction_repository)
    ],
    server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
    restriction_repo: Annotated[
        RestrictionRepository, Depends(get_restriction_repository)
    ],
    permission_repo: Annotated[
        PermissionRepository, Depends(get_permission_repository)
    ],
    server_role_repo: Annotated[
        ServerRoleRepository, Depends(get_server_role_repository)
    ],
) -> AccessControlService:
    return AccessControlService(
        member_repo=member_repo,
        member_restriction_repo=member_restriction_repo,
        server_repo=server_repo,
        restriction_repo=restriction_repo,
        permission_repo=permission_repo,
        server_role_repo=server_role_repo,
    )


async def get_role_service(
    server_repo: Annotated[ServerRepository, Depends(get_server_repository)],
    role_repo: Annotated[ServerRoleRepository, Depends(get_server_role_repository)],
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    permission_repo: Annotated[
        PermissionRepository, Depends(get_permission_repository)
    ],
) -> RoleService:
    return RoleService(
        server_repo=server_repo,
        role_repo=role_repo,
        member_repo=member_repo,
        permission_repo=permission_repo,
    )


CoreServiceDependency = Annotated[CoreService, Depends(get_core_service)]
GameServiceDependency = Annotated[GameService, Depends(get_game_service)]
GameRoleServiceDependency = Annotated[GameRoleService, Depends(get_game_role_service)]
InviteServiceDependency = Annotated[InviteService, Depends(get_invite_service)]
RatingServiceDependency = Annotated[RatingService, Depends(get_rating_service)]
MemberServiceDependency = Annotated[MemberService, Depends(get_member_service)]
MemberCustomServiceDependency = Annotated[
    MemberCustomService, Depends(get_member_custom_service)
]
AccessControlServiceDependency = Annotated[
    AccessControlService, Depends(get_access_control_service)
]
RoleServiceDependency = Annotated[RoleService, Depends(get_role_service)]
