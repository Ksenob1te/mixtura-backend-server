import asyncio
import logging
from src.app.rabbit.main import app
from src.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    asyncio.run(app.run())
