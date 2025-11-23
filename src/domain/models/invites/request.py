from pydantic import BaseModel


class InviteCreateRequest(BaseModel):
    use_limit: int | None = None
