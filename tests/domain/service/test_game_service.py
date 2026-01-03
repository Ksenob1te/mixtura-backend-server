import uuid
import pytest

from src.domain.service.game import GameService
from src.domain.exceptions import NotFoundException, ForbiddenException, InternalLogicException
from src.infra.postgre.static import PERMISSION
from src.infra.postgre.repo import GameRepository, ServerRepository
from src.infra.postgre.models import Server, GameRoleSet, RatingSet, Game


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


async def _server(session) -> Server:
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(id=uuid.uuid4(), name="Server", owner_id=uuid.uuid4(), public=True, role_set_id=rs.id,
               rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _game(session, name: str = "Game") -> Game:
    g = Game(name=f"{name}-{uuid.uuid4()}", icon_id=uuid.uuid4(), banner_id=uuid.uuid4())
    session.add(g)
    await session.flush()
    return g


@pytest.fixture
async def game_service(async_session):
    game_repo = GameRepository(async_session)
    server_repo = ServerRepository(async_session)
    return GameService(
        game_repo=game_repo,
        server_repo=server_repo,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_list_server_games_not_found(async_session, game_service):
    with pytest.raises(NotFoundException):
        await game_service.list_server_games(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_list_server_games_returns_linked_games(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session, name="G1")
    g2 = await _game(async_session, name="G2")
    g3 = await _game(async_session, name="G3")

    repo = game_service.game_repo
    await repo.bulk_add_to_server(server.id, [g1.id, g2.id])
    await async_session.refresh(server)

    res = await game_service.list_server_games(server.id)
    ids = {g.id for g in res}
    assert ids == {g1.id, g2.id}


@pytest.mark.asyncio(loop_scope="session")
async def test_add_games_to_server_forbidden_without_permission(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session, name="G1")
    assert g1 is not None

    with pytest.raises(ForbiddenException):
        await game_service.add_games_to_server(
            server.id,
            [g1.id],
            permission_mask=perm_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_add_games_to_server_not_found_server(async_session, game_service):
    g1 = await _game(async_session, name="G1")
    assert g1 is not None

    with pytest.raises(NotFoundException):
        await game_service.add_games_to_server(
            uuid.uuid4(),
            [g1.id],
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_GAME),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_add_games_to_server_success(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session, name="G1")
    g2 = await _game(async_session, name="G2")

    await game_service.add_games_to_server(
        server.id,
        [g1.id, g2.id],
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_GAME),
    )

    await async_session.refresh(server)
    ids = {g.id for g in server.games}
    assert {g1.id, g2.id} == ids


@pytest.mark.asyncio(loop_scope="session")
async def test_add_games_to_server_raises_when_some_games_missing(async_session, game_service):
    server = await _server(async_session)
    existing = await _game(async_session, name="G1")
    missing_id = uuid.uuid4()

    with pytest.raises(NotFoundException):
        await game_service.add_games_to_server(
            server.id,
            [existing.id, missing_id],
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_GAME),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_game_from_server_forbidden_without_permission(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session, name="G1")

    repo = game_service.game_repo
    await repo.bulk_add_to_server(server.id, [g1.id])

    with pytest.raises(ForbiddenException):
        await game_service.remove_game_from_server(
            server.id,
            g1.id,
            permission_mask=perm_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_game_from_server_not_found_server(async_session, game_service):
    g1 = await _game(async_session, name="G1")
    with pytest.raises(NotFoundException):
        await game_service.remove_game_from_server(
            uuid.uuid4(),
            g1.id,
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_GAME),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_game_from_server_success(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session, name="G1")
    g2 = await _game(async_session, name="G2")

    repo = game_service.game_repo
    await repo.bulk_add_to_server(server.id, [g1.id, g2.id])

    await game_service.remove_game_from_server(
        server.id,
        g1.id,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_GAME),
    )

    await async_session.refresh(server)
    remaining_ids = {g.id for g in server.games}
    assert g1.id not in remaining_ids
    assert g2.id in remaining_ids


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_game_from_server_non_linked_raises_not_found(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session, name="G1")

    with pytest.raises(NotFoundException):
        await game_service.remove_game_from_server(
            server.id,
            g1.id,
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_GAME),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_set_server_games_forbidden(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session)

    with pytest.raises(ForbiddenException):
        await game_service.set_server_games(
            server.id,
            [g1.id],
            permission_mask=perm_mask()
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_set_server_games_success(async_session, game_service):
    server = await _server(async_session)
    g1 = await _game(async_session, name="G1")
    g2 = await _game(async_session, name="G2")
    g3 = await _game(async_session, name="G3")

    # Pre-populate with G1 and G2
    await game_service.game_repo.bulk_add_to_server(server.id, [g1.id, g2.id])

    # Set to G2 and G3 (should remove G1, keep G2, add G3)
    await game_service.set_server_games(
        server.id,
        [g2.id, g3.id],
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_GAME)
    )

    await async_session.refresh(server)
    current_ids = {g.id for g in server.games}
    assert current_ids == {g2.id, g3.id}

