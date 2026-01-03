import logging
from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from ...dependency import CoreServiceDependency, GameServiceDependency

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
async def get_global_games(
    core_service: CoreServiceDependency,
) -> ResponseMessage[list[GameResponse]]:
    games = await core_service.get_global_games()
    ta = TypeAdapter(list[GameResponse])
    return ResponseMessage(status=200, message=ta.validate_python(games))


@router.subscriber("game.server.add")
async def add_game(
    data: GameAddRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameResponse]]:
    await game_service.add_games_to_server(
        data.access_data.server_id, data.game_ids, data.access_data.permission_mask
    )
    server_games = game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))


@router.subscriber("game.server.remove")
async def remove_game(
    data: GameRemoveRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameResponse]]:
    await game_service.remove_game_from_server(
        data.access_data.server_id, data.game_id, data.access_data.permission_mask
    )
    server_games = game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))


@router.subscriber("game.server.set")
async def set_game(
    data: GameSetRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameResponse]]:
    await game_service.set_server_games(
        data.access_data.server_id, data.game_ids, data.access_data.permission_mask
    )
    server_games = game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))


@router.subscriber("game.server.list")
async def list_server_games(
    data: GetServerGameListRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameResponse]]:
    server_games = game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))
