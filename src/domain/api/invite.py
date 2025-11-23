from uuid import UUID
from fastapi_controllers import Controller, get, post, delete

from src.domain.models.invites.request import InviteCreateRequest
from src.domain.models.invites.response import InviteAdminResponse, InviteKeyResponse
from src.domain.models.member.response import MemberResponse
from src.domain.models.response import StatusResponse

class ServerInviteController(Controller):
    prefix = "" 
    tags = ["Server invite"]

    @get("/invites/{key}", response_model=InviteKeyResponse)
    def get_invite_info(self, key: str): # TODO : User id depend
        pass

    @post("/invites/{key}", response_model=MemberResponse)
    def use_invite(self, key: str): # TODO : User id depend
        pass
    
    @get("/{server_id}/invites", response_model=list[InviteAdminResponse])
    def list_invites(self, server_id: UUID): # TODO : User id depend
        # TODO : Member get depend
        pass

    @post("/{server_id}/invites", response_model=StatusResponse)
    def create_invite(self, server_id: UUID, body: InviteCreateRequest): # TODO : User id depend
        # TODO : Member get depend
        pass

    @delete("/{server_id}/invites/{invite_id}", response_model=StatusResponse)
    def revoke_invite(self, server_id: UUID, invite_id: UUID): # TODO : User id depend
        # TODO : Member get depend
        pass