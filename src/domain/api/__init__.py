from fastapi import APIRouter

from src.domain.api.member_customs import MemberCustomsController
from src.domain.api.members import MembersController
from src.domain.api.server_core import ServerCoreController
from src.domain.api.server_game_roles import ServerGameRolesController
from src.domain.api.server_games import ServerGamesController
from src.domain.api.server_invites import ServerInvitesController
from src.domain.api.server_ratings import ServerRatingsController

router = APIRouter(
    prefix="/api/servers",
)

router.include_router(ServerInvitesController.create_router())
router.include_router(ServerGamesController.create_router())
router.include_router(ServerGameRolesController.create_router())
router.include_router(ServerRatingsController.create_router())
router.include_router(MemberCustomsController.create_router())
router.include_router(MembersController.create_router())
router.include_router(ServerCoreController.create_router())
