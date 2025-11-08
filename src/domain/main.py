from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

import src.domain.api as api
from src.env_config import env
from src.infra.postgre import DatabaseSessionManager
from src.infra.redis import RedisSessionManager
from src.infra.smtp import SMTPManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_manager = DatabaseSessionManager(env.postgres.url)
    redis_engine = RedisSessionManager(env.redis.url)
    smtp_engine = SMTPManager(env.smtp.host, env.smtp.port, env.smtp.user, env.smtp.password)

    # Expose managers for DI functions in src.dependency
    app.state.postgres_manager = session_manager
    app.state.redis_manager = redis_engine
    app.state.smtp_manager = smtp_engine
    yield
    if await session_manager.opened:
        await session_manager.close()
    if await redis_engine.opened:
        await redis_engine.close()

app = FastAPI(
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    title='Mixtura',
    version="2.0",
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["localhost"], allow_methods=["*"])
    ],
    lifespan=lifespan)

app.include_router(api.router)
