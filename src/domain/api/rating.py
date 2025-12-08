from uuid import UUID
from fastapi import UploadFile
from fastapi_controllers import Controller, get, post, put, patch, delete

from src.domain.models.rating.request import (
    RatingItemCreateRequest,
    RatingItemUpdateRequest,
    RatingSetUpdateRequest,
)
from src.domain.models.rating.response import RatingItemResponse, RatingSetResponse
from src.domain.models.response import StatusResponse


class ServerRatingController(Controller):
    prefix = "/{server_id}/rating-set"
    tags = ["Server rating"]

    @get("/", response_model=list[RatingSetResponse])
    def get_rating_set(self, server_id: UUID):  # TODO : User id depend
        # TODO : Member get depend
        pass

    @patch("/{rating_set_id}", response_model=RatingSetResponse)
    def update_rating_set(
        self, server_id: UUID, rating_set_id: UUID, body: RatingSetUpdateRequest
    ):  # TODO : User id depend
        # TODO : Member get depend
        pass

    @post("/{rating_set_id}/ratings", response_model=RatingItemResponse)
    def create_rating(
        self,
        server_id: UUID,
        rating_set_id: UUID,
        body: RatingItemCreateRequest,
        icon: UploadFile,
    ):  # TODO : User id depend
        # TODO : Member get depend
        pass

    @patch("/{rating_set_id}/ratings/{rating_id}", response_model=RatingItemResponse)
    def update_rating(
        self,
        server_id: UUID,
        rating_set_id: UUID,
        rating_id: UUID,
        body: RatingItemUpdateRequest,
    ):  # TODO : User id depend
        # TODO : Member get depend
        pass

    @delete("/{rating_set_id}/ratings/{rating_id}", response_model=StatusResponse)
    def delete_rating(
        self, server_id: UUID, rating_set_id: UUID, rating_id: UUID
    ):  # TODO : User id depend
        # TODO : Member get depend
        pass

    @put(
        "/{rating_set_id}/ratings/{rating_id}/icon", response_model=RatingItemResponse
    )
    def update_rating_icon(
        self, server_id: UUID, rating_set_id: UUID, rating_id: UUID, icon: UploadFile
    ):  # TODO : User id depend
        # TODO : Member get depend
        pass

