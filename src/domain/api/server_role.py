from uuid import UUID

from fastapi_controllers import Controller, get, post, patch, delete

from src.domain.models.member.response import ServerRoleResponse
from src.domain.models.response import StatusResponse
from src.domain.models.roles.request import (
    ServerRoleCreateRequest,
    ServerRoleUpdateRequest,
)


class ServerRoleController(Controller):
    prefix = "/{server_id}/roles"
    tags = ["Server roles"]

    @get("/", response_model=list[ServerRoleResponse])
    def list_roles(self, server_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @post("/", response_model=StatusResponse)
    def create_role(self, server_id: UUID, body: ServerRoleCreateRequest):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @patch("/{role_id}", response_model=ServerRoleResponse)
    def update_role(
        self,
        server_id: UUID,
        role_id: UUID,
        body: ServerRoleUpdateRequest,
    ):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @delete("/{role_id}", response_model=StatusResponse)
    def delete_role(self, server_id: UUID, role_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

