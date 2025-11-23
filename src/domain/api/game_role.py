from uuid import UUID
from fastapi import UploadFile
from fastapi_controllers import Controller, get, post, put, patch, delete

class ServerGameRoleController(Controller):
    prefix = "/{server_id}/role-set"
    tags = ["Server game role"]

    @get("/")
    def get_role_set(self, server_id: UUID):
        """Получить настройки набора ролей"""
        pass

    @patch("/")
    def update_role_set(self, server_id: UUID):
        """Обновить настройки набора ролей"""
        pass


    @post("/roles")
    def create_role(self, server_id: UUID):
        pass
        
    @get("/roles/{role_id}")
    def get_role(self, server_id: UUID, role_id: UUID):
        pass

    @patch("/roles/{role_id}")
    def update_role(self, server_id: UUID, role_id: UUID):
        pass

    @delete("/roles/{role_id}")
    def delete_role(self, server_id: UUID, role_id: UUID):
        pass
        
    @put("/roles/{role_id}/icon")
    def update_role_icon(self, server_id: UUID, role_id: UUID, icon: UploadFile):
        pass