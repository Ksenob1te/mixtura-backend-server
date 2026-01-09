from uuid import UUID
from pydantic import BaseModel

class AccessDataRequest(BaseModel):
    member_id: UUID | None
    server_id: UUID 
    permission_mask: int
    restriction_mask: int

class PaginationRequest(BaseModel):
    page: int | None = None
    page_size: int = 50