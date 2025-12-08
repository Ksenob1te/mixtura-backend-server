from src.infra.redis import RedisRepository
from uuid import UUID

from ..exceptions import NotAuthorizedException


class UserService:
    def __init__(self, redis_repo: RedisRepository):
        self.redis_repo = redis_repo

    async def validate_user_token(self, token: str | None) -> bool: # 123
        if not token:
            return False
        session_data = await self.redis_repo.get_user_by_cookie(token)
        return session_data is not None
    
    async def get_user_id(self, token: str | None) -> UUID:
        if not token:
            raise NotAuthorizedException()
        session_data = await self.redis_repo.get_user_by_cookie(token)
        if not session_data:
            raise NotAuthorizedException()
        return UUID(session_data)
