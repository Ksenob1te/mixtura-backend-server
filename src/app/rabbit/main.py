import logging
from contextlib import asynccontextmanager

from faststream import ContextRepo, ExceptionMiddleware, FastStream
from faststream.rabbit import Channel, RabbitBroker

from src.app.rabbit.api import router
from src.app.rabbit.models.base import ErrorResponse, ResponseMessage
from src.core.exceptions import DomainException
from src.dependency import DatabaseSession
from src.env_config import env
from src.infra.postgre import DatabaseSessionManager
from src.infra.redis import RedisSessionManager

exc_middleware = ExceptionMiddleware()
logger = logging.getLogger(__name__)


@exc_middleware.add_handler(DomainException, publish=True)
async def error_handler(
    exc: DomainException, session: DatabaseSession
) -> ResponseMessage[ErrorResponse]:
    try:
        await session.rollback()
    except Exception:  # noqa: BLE001
        logger.error("Session rollback error")
    return ResponseMessage(
        status=exc.status_code, message=ErrorResponse(message=exc.message)
    )


broker = RabbitBroker(
    env.rabbit.url,
    middlewares=[exc_middleware],
    default_channel=Channel(prefetch_count=10),
)

broker.include_router(router)


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
