from fastapi import Request, Depends

from .infra.postgre import DatabaseSessionManager
from .infra.redis import RedisSessionManager, RedisRepository

from typing import Annotated
from redis.asyncio import Redis

import logging

logger = logging.getLogger(__name__)


async def get_db_session(request: Request):
    if not hasattr(request.app.state, "postgres_manager"):
        logger.error("postgres_manager not found in app.state")
        raise RuntimeError("Database session manager not configured")
    postgres_manager: DatabaseSessionManager = request.app.state.postgres_manager
    async with postgres_manager.session() as session:
        yield session


async def get_redis_session(request: Request):
    if not hasattr(request.app.state, "redis_manager"):
        logger.error("redis_manager not found in app.state")
        raise RuntimeError("Redis session manager not configured")
    redis_manager: RedisSessionManager = request.app.state.redis_manager
    async with redis_manager.client() as redis:
        yield redis


async def get_redis_repository(redis: Annotated[Redis, Depends(get_redis_session)]):
    return RedisRepository(redis)
