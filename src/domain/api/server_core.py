from uuid import UUID
from fastapi_controllers import Controller, get, post, put, patch, delete

class ServerCoreController(Controller):
    prefix = ""  # Базовый путь будет /servers/
    tags = ["Server Core"]

    # --- Global Lists (Metadata) ---
    @get("/role-set") # Старый: /server/role-set
    def get_global_role_templates(self):
        pass

    @get("/rating-set") # Старый: /server/rating-set
    def get_global_rating_templates(self):
        pass
    
    @get("/games") # Старый: /server/games
    def get_global_games(self):
        pass

    # --- Server CRUD ---
    @get("/")
    def list_servers(self):
        pass

    @post("/")
    def create_server(self):
        pass

    @get("/{server_id}")
    def get_server(self, server_id: UUID):
        pass

    @patch("/{server_id}")
    def update_server(self, server_id: UUID):
        pass

    @delete("/{server_id}")
    def delete_server(self, server_id: UUID):
        pass

    # --- Media ---
    @put("/{server_id}/banner")
    def update_banner(self, server_id: UUID):
        pass

    @put("/{server_id}/icon")
    def update_icon(self, server_id: UUID):
        pass