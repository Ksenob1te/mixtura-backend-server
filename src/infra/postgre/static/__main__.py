from . import *
import asyncio
from src.env_config import env
from src.infra.postgre import DatabaseSessionManager
from src.logging_setup import setup_logging


async def init_constants():

    session_manager = DatabaseSessionManager(env.postgres.url)
    async with session_manager.session() as session:
        await init_permissions(session)
        await init_restrictions(session)

if __name__ == "__main__":
    setup_logging()
    asyncio.run(init_constants())
