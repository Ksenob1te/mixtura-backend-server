import logging
from uuid import UUID

from faststream.rabbit import RabbitRouter

from src.domain.models.core.request import ServerCreateRequest, ServerGetRequest, ServerUpdateRequest
from src.domain.models.core.response import ServerDetailResponse, ServerListResponse
from src.domain.models.game_roles.response import GameRoleSetResponse
from src.domain.models.games.response import GameResponse
from src.domain.models.member.response import RestrictionResponse
from src.domain.models.rating.response import RatingSetResponse
from ..models.request import UserIncludedRequest
from src.domain.models.response import ResponseMessage, StatusResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="server.global.role_sets")
async def get_global_role_templates() -> ResponseMessage[list[GameRoleSetResponse]]:
    ...

@router.subscriber(queue="server.global.rating_sets")
async def get_global_rating_templates() -> ResponseMessage[list[RatingSetResponse]]:
    ...

@router.subscriber(queue="server.global.permissions")
async def get_global_permissions() -> ResponseMessage[list[str]]:
    ...

@router.subscriber(queue="server.global.restrictions")
async def get_global_restrictions() -> ResponseMessage[list[RestrictionResponse]]:
    ...

@router.subscriber(queue="server.global.games")
async def get_global_games() -> ResponseMessage[list[GameResponse]]:
    ...

@router.subscriber(queue="server.public_server_list")
async def get_public_servers() -> ResponseMessage[list[ServerListResponse]]:
    ...

@router.subscriber(queue="server.user_server_list")
async def get_user_servers(data: UserIncludedRequest) -> ResponseMessage[list[ServerListResponse]]:
    ...

@router.subscriber(queue="server.create")
async def create_server(data: ServerCreateRequest) -> ResponseMessage[StatusResponse]:
    ...

@router.subscriber(queue="server.get_info")
async def get_server(data: ServerGetRequest) -> ResponseMessage[ServerDetailResponse]:
    ...
    

class ServerCoreController(Controller):
    prefix = ""
    tags = ["Server Core"]

    @post("/", status_code=201)
    def create_server(self, body: ServerCreateRequest):  # TODO : User id depend
        pass

    @get("/{server_id}", response_model=ServerDetailResponse)
    def get_server(self, server_id: UUID):  # TODO : User id depend
        pass

    @patch("/{server_id}", response_model=ServerDetailResponse)
    def update_server(self, server_id: UUID, body: ServerUpdateRequest): # TODO : User id depend
        # TODO : Member get depend
        pass

    @delete("/{server_id}", response_model=StatusResponse)
    def delete_server(self, server_id: UUID): # TODO : User id depend
        # TODO : Member get depend
        pass

    @put("/{server_id}/banner", response_model=ServerDetailResponse)
    def update_banner(self, server_id: UUID, banner: UploadFile): # TODO : User id depend
        # TODO : Member get depend
        pass

    @put("/{server_id}/icon", response_model=ServerDetailResponse)
    def update_icon(self, server_id: UUID, icon: UploadFile): # TODO : User id depend
        # TODO : Member get depend
        pass
