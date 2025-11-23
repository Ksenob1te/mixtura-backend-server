from uuid import UUID
from fastapi_controllers import Controller, get, post, put, delete


class MemberController(Controller):
    prefix = "/{server_id}/members"
    tags = ['Member']

    @get("/")
    def list_members(self, server_id: UUID):
        pass


    @post("/")
    def create_member(self, server_id: UUID): # Only for public servers
        pass

    @post("/virtual") 
    def create_virtual(self, server_id: UUID):
        pass

    @get("/{member_id}")
    def get_member(self, server_id: UUID, member_id: UUID):
        pass

    @put("/{member_id}")
    def update_member(self, server_id: UUID, member_id: UUID):
        pass
        
    @delete("/{member_id}")
    def kick_member(self, server_id: UUID, member_id: UUID):
        pass

    @post("/{member_id}/migrate")
    def migrate_member(self, server_id: UUID, member_id: UUID):
        pass

    @get("/{member_id}/restrictions")
    def get_restrictions(self, server_id: UUID, member_id: UUID):
        pass
        
    @post("/{member_id}/restrictions")
    def add_restriction(self, server_id: UUID, member_id: UUID):
        pass
        
    @delete("/{member_id}/restrictions/{restriction_id}")
    def remove_restriction(self, server_id: UUID, member_id: UUID, restriction_id: UUID):
        pass