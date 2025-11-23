from uuid import UUID
from fastapi_controllers import Controller, get, post, delete

class ServerInvitesController(Controller):
    prefix = "" 
    tags = ["Server invites"]

    @get("/invites/{key}")
    def get_invite_info(self, key: str):
        """Публичный: Проверить, куда ведет инвайт"""
        pass

    @post("/invites/{key}")
    def use_invite(self, key: str):
        """Публичный: Принять инвайт"""
        pass
    
    @get("/{server_id}/invites")
    def list_invites(self, server_id: UUID):
        """Админ: Список активных инвайтов сервера"""
        pass

    @post("/{server_id}/invites")
    def create_invite(self, server_id: UUID):
        """Админ: Создать новый инвайт"""
        pass

    @delete("/{server_id}/invites/{invite_id}")
    def revoke_invite(self, server_id: UUID, invite_id: UUID):
        """Админ: Удалить/Отозвать инвайт"""
        pass