from uuid import UUID
from fastapi_controllers import Controller, get, post, put, delete

class MemberCustomsController(Controller):
    # Очень глубокий путь
    prefix = "/{server_id}/members/{member_id}/customs"
    tags = ["Members customs"]

    @get("/")
    def list_customs(self, server_id: UUID, member_id: UUID):
        pass

    @post("/")
    def create_custom(self, server_id: UUID, member_id: UUID):
        pass

    @get("/{custom_id}")
    def get_custom(self, server_id: UUID, member_id: UUID, custom_id: UUID):
        pass

    @delete("/{custom_id}")
    def delete_custom(self, server_id: UUID, member_id: UUID, custom_id: UUID):
        pass

    # --- Ratings внутри Customs ---
    # Путь: .../customs/{custom_id}/ratings/{rating_id}
    
    @post("/{custom_id}/ratings")
    def add_rating_to_custom(self, server_id: UUID, member_id: UUID, custom_id: UUID):
        pass

    @put("/{custom_id}/ratings/{rating_id}")
    def update_rating_value(self, server_id: UUID, member_id: UUID, custom_id: UUID, rating_id: UUID):
        pass

    @delete("/{custom_id}/ratings/{rating_id}")
    def remove_rating_from_custom(self, server_id: UUID, member_id: UUID, custom_id: UUID, rating_id: UUID):
        pass