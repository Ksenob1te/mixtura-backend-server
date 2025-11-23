from pydantic import BaseModel


class GameRoleRatingSetRequest(BaseModel):
    rating: int
