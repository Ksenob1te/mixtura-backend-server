from contextlib import asynccontextmanager

from faststream import ContextRepo, ExceptionMiddleware, FastStream
from faststream.rabbit import RabbitBroker, Channel

import src.domain.api as api
from src.env_config import env
from src.infra.postgre import DatabaseSessionManager
from src.infra.redis import RedisSessionManager

from .exceptions import DomainException
from .models.response import ErrorResponse, ResponseMessage

exc_middleware = ExceptionMiddleware()


@exc_middleware.add_handler(DomainException, publish=True)
def error_handler(exc: DomainException) -> ResponseMessage[ErrorResponse]:
    # TODO: think about what happens with database on the exception
    return ResponseMessage(
        status=exc.status_code, message=ErrorResponse(message=exc.message)
    )


broker = RabbitBroker(
    env.rabbit.url,
    middlewares=[exc_middleware],
    default_channel=Channel(prefetch_count=10),
)

broker.include_router(api.router)


@asynccontextmanager
async def lifespan(context: ContextRepo):
    session_manager = DatabaseSessionManager(env.postgres.url)
    redis_engine = RedisSessionManager(env.redis.url)

    context.set_global("session_manager", session_manager)
    context.set_global("redis_engine", redis_engine)

    yield

    if await session_manager.opened:
        await session_manager.close()
    if await redis_engine.opened:
        await redis_engine.close()


app = FastStream(broker, lifespan=lifespan)
