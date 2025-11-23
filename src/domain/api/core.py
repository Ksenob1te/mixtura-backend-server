from uuid import UUID
from fastapi import UploadFile
from fastapi_controllers import Controller, get, post, put, patch, delete

from src.domain.models.core.request import ServerCreateRequest, ServerUpdateRequest
from src.domain.models.core.response import ServerDetailResponse, ServerListResponse
from src.domain.models.game_roles.response import GameRoleSetResponse
from src.domain.models.games.response import GameResponse
from src.domain.models.member.response import RestrictionResponse
from src.domain.models.rating.response import RatingSetResponse
from src.domain.models.response import StatusResponse

class ServerCoreController(Controller):
    prefix = ""
    tags = ["Server Core"]

    @get("/role-set", response_model=list[GameRoleSetResponse])
    def get_global_role_templates(self):
        pass

    @get("/rating-set", response_model=list[RatingSetResponse])
    def get_global_rating_templates(self):
        pass

    @get("/restrictions", response_model=list[RestrictionResponse])
    def get_global_restrictions(self):
        pass
    
    @get("/games", response_model=list[GameResponse])
    def get_global_games(self):
        pass

    # --- Server CRUD ---
    @get("/", response_model=list[ServerListResponse])
    def list_servers(self):
        pass

    @get("/", response_model=list[ServerListResponse])
    def list_user_servers(self): # TODO : User id depend
        pass

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