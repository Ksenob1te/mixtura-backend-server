from faststream.rabbit import RabbitRouter

from .core import router as CoreController
from .custom import router as CustomController
from .game import router as GameController
from .game_role import router as GameRoleController
from .invite import router as InviteController
from .member import router as MemberController
from .rating import router as RatingController
from .server_role import router as ServerRoleController

router = RabbitRouter()

router.include_router(CoreController)
router.include_router(CustomController)
router.include_router(GameController)
router.include_router(GameRoleController)
router.include_router(InviteController)
router.include_router(MemberController)
router.include_router(RatingController)
router.include_router(ServerRoleController)
