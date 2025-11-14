from uuid import UUID
from fastapi import Depends, UploadFile
from fastapi_controllers import Controller, delete, get, patch, post, put

class RoleSetController(Controller):
    prefix = "/"
    tags = ["role_set"]

    @get("roleset")
    async def get_public_role_sets(self, server_id: UUID):
        pass

    @get("{server_id}/roleset")
    async def get_role_set(self, server_id: UUID):
        pass

    @patch("{server_id}/roleset")
    async def update_role_set(self, server_id: UUID):
        pass

    @post("{server_id}/roleset/roles")
    async def create_role(self, server_id: UUID):
        pass

    @get("{server_id}/roleset/roles/{role_id}")
    async def get_role(self, server_id: UUID, role_id: UUID):
        pass

    @patch("{server_id}/roleset/roles/{role_id}")
    async def update_role(self, server_id: UUID, role_id: UUID):
        pass

    @put("{server_id}/roleset/roles/{role_id}/icon")
    async def set_role_icon(self, server_id: UUID, role_id: UUID, icon: UploadFile):
        pass

    @delete("{server_id}/roleset/roles/{role_id}")
    async def delete_role(self, server_id: UUID, role_id: UUID):
        pass