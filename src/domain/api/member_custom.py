from uuid import UUID
from fastapi_controllers import Controller, get, post, put, delete

from src.domain.models.custom.request import GameRoleRatingSetRequest
from src.domain.models.custom.response import CustomResponse
from src.domain.models.response import StatusResponse


class MemberCustomController(Controller):
    prefix = "/{server_id}/members/{member_id}/customs"
    tags = ["Member custom"]

    @get("/", response_model=list[CustomResponse])
    def list_customs(self, server_id: UUID, member_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @post("/", response_model=CustomResponse)
    def create_custom(self, server_id: UUID, member_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @get("/{custom_id}", response_model=CustomResponse)
    def get_custom(self, server_id: UUID, member_id: UUID, custom_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @delete("/{custom_id}", response_model=StatusResponse)
    def delete_custom(self, server_id: UUID, member_id: UUID, custom_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @put("/{custom_id}/ratings/{game_role_id}", response_model=CustomResponse)
    def update_rating_value(self, server_id: UUID, member_id: UUID, custom_id: UUID, game_role_id: UUID,
                            body: GameRoleRatingSetRequest):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass
