import logging
from faststream.rabbit import RabbitRouter

from ..models.games.request import (
    GameAddRequest,
    GameRemoveRequest,
    GameSetRequest,
    GetServerGameListRequest,
)

from ..models.response import ResponseMessage

from ..models.games.response import GameResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="server.global.games")
async def get_global_games() -> ResponseMessage[list[GameResponse]]: ...


@router.subscriber("game.server.add")
def add_game(data: GameAddRequest) -> ResponseMessage[list[GameResponse]]: ...


@router.subscriber("game.server.remove")
def remove_game(data: GameRemoveRequest) -> ResponseMessage[list[GameResponse]]: ...


@router.subscriber("game.server.set")
def set_game(data: GameSetRequest) -> ResponseMessage[list[GameResponse]]: ...


@router.subscriber("game.server.list")
def list_server_games(
    data: GetServerGameListRequest,
) -> ResponseMessage[list[GameResponse]]: ...
