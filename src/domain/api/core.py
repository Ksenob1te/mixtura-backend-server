from uuid import UUID
from fastapi import UploadFile
from fastapi_controllers import Controller, get, post, put, patch, delete

class ServerCoreController(Controller):
    prefix = ""
    tags = ["Server Core"]

    @get("/role-set", response_model=None)
    def get_global_role_templates(self):
        pass

    @get("/rating-set", response_model=None)
    def get_global_rating_templates(self):
        pass
    
    @get("/games", response_model=None)
    def get_global_games(self):
        pass

    # --- Server CRUD ---
    @get("/", response_model=None)
    def list_servers(self):
        pass

    @post("/", response_model=None)
    def create_server(self):
        pass

    @get("/{server_id}", response_model=None)
    def get_server(self, server_id: UUID):
        pass

    @patch("/{server_id}", response_model=None)
    def update_server(self, server_id: UUID):
        pass

    @delete("/{server_id}", response_model=None)
    def delete_server(self, server_id: UUID):
        pass

    # --- Media ---
    @put("/{server_id}/banner")
    def update_banner(self, server_id: UUID, banner: UploadFile):
        pass

    @put("/{server_id}/icon")
    def update_icon(self, server_id: UUID, icon: UploadFile):
        pass