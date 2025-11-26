from uuid import UUID
from fastapi_controllers import Controller, get, patch, post, delete

from src.domain.models.member.request import MemberRestrictionCreateRequest, MemberUpdateRequest, MigrationRequest, \
    VirtualMemberCreateRequest
from src.domain.models.member.response import MemberResponse, MemberRestrictionResponse
from src.domain.models.response import StatusResponse


class MemberController(Controller):
    prefix = "/{server_id}/members"
    tags = ['Member']

    @get("/", response_model=list[MemberResponse])
    def list_members(self, server_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @post("/", response_model=StatusResponse)
    def join_server(self, server_id: UUID):  # Only for public servers  # TODO : User id depend
        pass

    @post("/virtual", response_model=StatusResponse)
    def create_virtual(self, server_id: UUID, body: VirtualMemberCreateRequest):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @get("/{member_id}", response_model=MemberResponse)
    def get_member(self, server_id: UUID, member_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @patch("/{member_id}", response_model=MemberResponse)
    def update_member(self, server_id: UUID, member_id: UUID, body: MemberUpdateRequest):  # TODO : User id depend
        pass

    @delete("/{member_id}", response_model=StatusResponse)
    def kick_member(self, server_id: UUID, member_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @post("/{member_id}/migrate", response_model=MemberResponse)
    def migrate_member(self, server_id: UUID, member_id: UUID, body: MigrationRequest):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @get("/{member_id}/restrictions", response_model=list[MemberRestrictionResponse])
    def get_restrictions(self, server_id: UUID, member_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @post("/{member_id}/restrictions", response_model=MemberRestrictionResponse)
    def add_restriction(self, server_id: UUID, member_id: UUID,
                        body: MemberRestrictionCreateRequest):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass

    @delete("/{member_id}/restrictions/{member_restriction_id}", response_model=StatusResponse)
    def remove_restriction(self, server_id: UUID, member_id: UUID,
                           member_restriction_id: UUID):  # TODO : User id depend
        # TODO : Issuer Member get depend
        pass
