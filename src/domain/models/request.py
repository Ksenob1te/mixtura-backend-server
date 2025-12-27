from uuid import UUID
from pydantic import BaseModel

class AccessDataRequest(BaseModel):
    member_id: UUID
    server_id: UUID
    permission_mask: int
    restriction_mask: int