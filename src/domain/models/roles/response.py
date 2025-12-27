from pydantic import BaseModel, ConfigDict


class ServerRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    position: int
    permission_mask: int