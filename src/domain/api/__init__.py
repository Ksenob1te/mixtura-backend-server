from fastapi import APIRouter

from src.domain.api.member_custom import MemberCustomController
from src.domain.api.member import MemberController
from src.domain.api.core import ServerCoreController
from src.domain.api.game_role import ServerGameRoleController
from src.domain.api.game import ServerGameController
from src.domain.api.invite import ServerInviteController
from src.domain.api.rating import ServerRatingController

router = APIRouter(
    prefix="/api/servers",
)

router.include_router(ServerInviteController.create_router())
router.include_router(ServerGameController.create_router())
router.include_router(ServerGameRoleController.create_router())
router.include_router(ServerRatingController.create_router())
router.include_router(MemberCustomController.create_router())
router.include_router(MemberController.create_router())
router.include_router(ServerCoreController.create_router())
