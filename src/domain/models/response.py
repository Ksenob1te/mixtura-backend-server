from pydantic import BaseModel, Field


class UpdateResponse(BaseModel):
    status: str = Field(default="ok")
    updated: bool = Field(default=True)


class StatusResponse(BaseModel):
    status: str = Field(default="ok")