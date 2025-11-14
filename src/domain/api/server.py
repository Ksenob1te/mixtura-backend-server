from uuid import UUID
from fastapi import Depends, UploadFile
from fastapi_controllers import Controller, delete, get, patch, post, put

class ServerController(Controller):
    prefix = "/"
    tags = ["server"]

    @post("")
    async def create_server(self):
        pass

    @get("")
    async def get_public_servers(self):
        pass

    @get("{server_id}")
    async def get_server(self, server_id: UUID):
        pass

    @patch("{server_id}")
    async def update_server(self, server_id: UUID):
        pass

    @put("{server_id}/banner")
    async def set_server_banner(self, server_id: UUID, banner: UploadFile):
        pass

    @put("{server_id}/icon")
    async def set_server_icon(self, server_id: UUID, icon: UploadFile):
        pass

    @delete("{server_id}")
    async def delete_server(self, server_id: UUID):
        pass
    

