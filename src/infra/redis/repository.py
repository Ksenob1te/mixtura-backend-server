from redis.asyncio import Redis


class RedisRepository:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def _get_dict_by_key(self, key: str) -> dict | None:
        response = await self.redis.hgetall(key)  # type: ignore
        if not response:
            return None
        return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in
                response.items()}

    async def _get_element_by_key(self, key: str) -> str | None:
        response = await self.redis.get(key)
        if not response:
            return None
        return response.decode() if isinstance(response, bytes) else response

    async def get_user_by_cookie(self, cookie: str) -> str | None:
        hash_value = f"cookie::{cookie}"
        return await self._get_element_by_key(hash_value)
