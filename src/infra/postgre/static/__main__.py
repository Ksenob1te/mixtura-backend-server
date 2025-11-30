from . import *
import asyncio
from src.env_config import env
from src.infra.postgre import DatabaseSessionManager


async def init_constants():

    session_manager = DatabaseSessionManager(env.postgres.url)
    async with session_manager.session() as session:
        await init_permissions(session)

if __name__ == "__main__":
    asyncio.run(init_constants())
