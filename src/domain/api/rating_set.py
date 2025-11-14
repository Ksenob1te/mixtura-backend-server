from uuid import UUID
from fastapi import Depends, UploadFile
from fastapi_controllers import Controller, delete, get, patch, post, put

class RatingSetController(Controller):
    prefix = "/"
    tags = ["rating_set"]

    @get("ratingset")
    async def get_public_rating_sets(self, server_id: UUID):
        pass

    @get("{server_id}/rating-set")
    async def get_rating_set(self, server_id: UUID):
        pass

    @patch("{server_id}/rating-set")
    async def update_rating_set(self, server_id: UUID):
        pass

    @post("{server_id}/rating-set/ratings")
    async def create_rating(self, server_id: UUID):
        pass

    @get("{server_id}/rating-set/ratings/{rating_id}")
    async def get_rating(self, server_id: UUID, rating_id: UUID):
        pass

    @patch("{server_id}/rating-set/ratings/{rating_id}")
    async def update_rating(self, server_id: UUID, rating_id: UUID):
        pass

    @put("{server_id}/rating-set/ratings/{rating_id}/icon")
    async def set_rating_icon(self, server_id: UUID, rating_id: UUID, icon: UploadFile):
        pass

    @delete("{server_id}/rating-set/ratings/{rating_id}")
    async def delete_rating(self, server_id: UUID, rating_id: UUID):
        pass

