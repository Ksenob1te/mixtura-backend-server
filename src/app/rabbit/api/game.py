import logging

from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.game import (
    GameAddRequest,
    GameDetailResponse,
    GameRemoveRequest,
    GameSetRequest,
    GetOwnedGameListRequest,
    GetServerGameListRequest,
    GlobalGameCreateRequest,
    GlobalGameDeleteRequest,
    GlobalGameUpdateRequest,
    LocalGameCopyRequest,
    LocalGameCreateRequest,
    LocalGameDeleteRequest,
    LocalGameUpdateRequest,
)
from src.dependency import GameServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber("game.global.list")
async def list_global_games(
    game_service: GameServiceDependency,
) -> ResponseMessage[list[GameDetailResponse]]:
    games = await game_service.list_global_games()
    ta = TypeAdapter(list[GameDetailResponse])
    return ResponseMessage(status=200, message=ta.validate_python(games))


@router.subscriber("game.global.create")
async def create_global_game(
    data: GlobalGameCreateRequest, game_service: GameServiceDependency
) -> ResponseMessage[GameDetailResponse]:
    game = await game_service.create_global_game(
        data.name, data.min_rating, data.max_rating, data.icon_id, data.banner_id
    )
    return ResponseMessage(status=200, message=GameDetailResponse.model_validate(game))


@router.subscriber("game.global.update")
async def update_global_game(
    data: GlobalGameUpdateRequest, game_service: GameServiceDependency
) -> ResponseMessage[GameDetailResponse]:
    game = await game_service.update_global_game(
        data.game_id, data.name, data.icon_id, data.banner_id
    )
    return ResponseMessage(status=200, message=GameDetailResponse.model_validate(game))


@router.subscriber("game.global.delete")
async def delete_global_game(
    data: GlobalGameDeleteRequest, game_service: GameServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_service.delete_global_game(data.game_id)
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("game.server.list")
async def list_server_games(
    data: GetServerGameListRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameDetailResponse]]:
    server_games = await game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameDetailResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))


@router.subscriber("game.server.owned")
async def list_owned_games(
    data: GetOwnedGameListRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameDetailResponse]]:
    owned_games = await game_service.list_owned_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameDetailResponse])
    return ResponseMessage(status=200, message=ta.validate_python(owned_games))


@router.subscriber("game.server.create")
async def create_local_game(
    data: LocalGameCreateRequest, game_service: GameServiceDependency
) -> ResponseMessage[GameDetailResponse]:
    game = await game_service.create_local_game(
        data.access_data.server_id, data.name, data.min_rating, data.max_rating,
        data.icon_id, data.banner_id, data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=GameDetailResponse.model_validate(game))


@router.subscriber("game.server.copy")
async def copy_global_game(
    data: LocalGameCopyRequest, game_service: GameServiceDependency
) -> ResponseMessage[GameDetailResponse]:
    game = await game_service.copy_global_game(
        data.access_data.server_id, data.game_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=GameDetailResponse.model_validate(game))


@router.subscriber("game.server.update")
async def update_local_game(
    data: LocalGameUpdateRequest, game_service: GameServiceDependency
) -> ResponseMessage[GameDetailResponse]:
    game = await game_service.update_local_game(
        data.access_data.server_id, data.game_id, data.name, data.icon_id, data.banner_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=GameDetailResponse.model_validate(game))


@router.subscriber("game.server.delete")
async def delete_local_game(
    data: LocalGameDeleteRequest, game_service: GameServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_service.delete_local_game(
        data.access_data.server_id, data.game_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("game.server.add")
async def add_game(
    data: GameAddRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameDetailResponse]]:
    await game_service.add_games_to_server(
        data.access_data.server_id, data.game_ids, data.access_data.permission_mask
    )
    server_games = await game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameDetailResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))


@router.subscriber("game.server.remove")
async def remove_game(
    data: GameRemoveRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameDetailResponse]]:
    await game_service.remove_game_from_server(
        data.access_data.server_id, data.game_id, data.access_data.permission_mask
    )
    server_games = await game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameDetailResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))


@router.subscriber("game.server.set")
async def set_game(
    data: GameSetRequest, game_service: GameServiceDependency
) -> ResponseMessage[list[GameDetailResponse]]:
    await game_service.set_server_games(
        data.access_data.server_id, data.game_ids, data.access_data.permission_mask
    )
    server_games = await game_service.list_server_games(data.access_data.server_id)
    ta = TypeAdapter(list[GameDetailResponse])
    return ResponseMessage(status=200, message=ta.validate_python(server_games))
