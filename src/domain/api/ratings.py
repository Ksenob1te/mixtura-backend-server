from uuid import UUID
from fastapi_controllers import Controller, get, post, put, patch, delete

class ServerRatingsController(Controller):
    prefix = "/{server_id}/rating-set"
    tags = ["Server ratings"]

    @get("/")
    def get_rating_set(self, server_id: UUID):
        """Получить текущий набор рейтингов"""
        pass

    @put("/")
    def replace_rating_set(self, server_id: UUID):
        """Полное обновление/замена набора рейтингов"""
        pass

    @post("/ratings")
    def create_rating(self, server_id: UUID):
        pass

    @get("/ratings/{rating_id}")
    def get_rating(self, server_id: UUID, rating_id: UUID):
        pass

    @patch("/ratings/{rating_id}")
    def update_rating(self, server_id: UUID, rating_id: UUID):
        pass

    @delete("/ratings/{rating_id}")
    def delete_rating(self, server_id: UUID, rating_id: UUID):
        pass
        
    @put("/ratings/{rating_id}/icon") # Добавил иконку, как было в списке
    def update_rating_icon(self, server_id: UUID, rating_id: UUID):
        pass