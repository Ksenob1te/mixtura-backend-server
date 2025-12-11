from uuid import UUID

from src.domain.models.game_roles.request import (
    GameRoleItemCreateRequest,
    GameRoleItemUpdateRequest,
    GameRoleSetUpdateRequest,
)
from src.domain.models.game_roles.response import (
    GameRoleItemResponse,
    GameRoleSetResponse,
)
from src.domain.models.response import StatusResponse


class ServerGameRoleController(Controller):
    prefix = "/{server_id}/role-set"
    tags = ["Server game role"]

    @get("/", response_model=list[GameRoleSetResponse])
    def get_role_set(self, server_id: UUID): # TODO : User id depend
        # TODO : Member get depend
        pass

    @patch("/{role_set_id}", response_model=GameRoleSetResponse)
    def update_role_set(
        self, server_id: UUID, role_set_id: UUID, body: GameRoleSetUpdateRequest
    ): # TODO : User id depend
        # TODO : Member get depend
        pass

    @post("/{role_set_id}/role", response_model=StatusResponse)
    def create_role(self, server_id: UUID, role_set_id: UUID, body: GameRoleItemCreateRequest, icon: UploadFile): # TODO : User id depend
        # TODO : Member get depend
        pass

    @patch("/{role_set_id}/role/{role_id}", response_model=GameRoleItemResponse)
    def update_role(
        self,
        server_id: UUID,
        role_set_id: UUID,
        role_id: UUID,
        body: GameRoleItemUpdateRequest,
    ): # TODO : User id depend
        # TODO : Member get depend
        pass

    @delete("/{role_set_id}/roles/{role_id}", response_model=StatusResponse)
    def delete_role(self, server_id: UUID, role_set_id: UUID, role_id: UUID): # TODO : User id depend
        pass

    @put("/{role_set_id}/roles/{role_id}/icon", response_model=GameRoleItemResponse)
    def update_role_icon(
        self, server_id: UUID, role_id: UUID, role_set_id: UUID, icon: UploadFile
    ): # TODO : User id depend
        # TODO : Member get depend
        pass
