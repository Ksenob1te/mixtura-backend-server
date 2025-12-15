import uuid
import pytest

from src.domain.service.game_role import GameRoleService
from src.domain.exceptions import NotFoundException, ForbiddenException
from src.domain.models.game_roles.request import (
    GameRoleItemCreateRequest,
    GameRoleItemUpdateRequest,
    GameRoleSetUpdateRequest,
)
from src.infra.postgre.static import PERMISSION
from src.infra.postgre.repo import (
    GameRoleSetRepository,
    GameRoleRepository,
    ServerRepository,
)
from src.infra.postgre.models import Server, GameRoleSet, GameRole, RatingSet


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


async def _server(session, role_set: GameRoleSet) -> Server:
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rts)
    await session.flush()
    s = Server(id=uuid.uuid4(), name="Server", owner_id=uuid.uuid4(), public=True, role_set_id=role_set.id,
               rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _role_set(session, name: str = "Set") -> GameRoleSet:
    rs = GameRoleSet(name=name, is_global=False)
    session.add(rs)
    await session.flush()
    return rs


async def _role(session, role_set: GameRoleSet | None = None, name: str = "Role") -> GameRole:
    if role_set is None:
        role_set = await _role_set(session)
    r = GameRole(name=name, role_set_id=role_set.id, min_in_team=1, max_in_team=3)
    session.add(r)
    await session.flush()
    return r


@pytest.fixture
async def game_role_service(async_session):
    server_repo = ServerRepository(async_session)
    role_set_repo = GameRoleSetRepository(async_session)
    role_repo = GameRoleRepository(async_session)
    return GameRoleService(server_repo, role_set_repo, role_repo)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_role_set_for_server_not_found(async_session, game_role_service):
    with pytest.raises(NotFoundException):
        await game_role_service.get_role_set_for_server(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_get_role_set_for_server_success(async_session, game_role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    async_session.add(s)
    await async_session.flush()

    res = await game_role_service.get_role_set_for_server(s.id)
    assert res is not None
    assert res.id == rs.id


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_set_forbidden_without_permission(async_session, game_role_service):
    rs = await _role_set(async_session)
    body = GameRoleSetUpdateRequest(name="NewName")
    with pytest.raises(ForbiddenException):
        await game_role_service.update_role_set(rs.id, body, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_set_not_found(async_session, game_role_service):
    body = GameRoleSetUpdateRequest(name="NewName")
    with pytest.raises(NotFoundException):
        await game_role_service.update_role_set(
            uuid.uuid4(),
            body,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_set_success(async_session, game_role_service):
    rs = await _role_set(async_session, name="Old")
    body = GameRoleSetUpdateRequest(name="New")
    updated = await game_role_service.update_role_set(
        rs.id,
        body,
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    assert updated.name == "New"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_forbidden_without_permission(async_session, game_role_service):
    rs = await _role_set(async_session)
    body = GameRoleItemCreateRequest(name="R", min_in_team=1, max_in_team=2, hidden=False)
    with pytest.raises(ForbiddenException):
        await game_role_service.create_role(rs.id, body, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_role_set_not_found(async_session, game_role_service):
    body = GameRoleItemCreateRequest(name="R", min_in_team=1, max_in_team=2, hidden=False)
    with pytest.raises(NotFoundException):
        await game_role_service.create_role(
            uuid.uuid4(),
            body,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_success(async_session, game_role_service):
    rs = await _role_set(async_session)
    body = GameRoleItemCreateRequest(name="Support", min_in_team=1, max_in_team=3, hidden=False)
    role = await game_role_service.create_role(
        rs.id,
        body,
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    assert role is not None
    assert role.name == "Support"
    repo = game_role_service.role_repo
    listed = await repo.list_for_set(rs.id)
    assert any(r.id == role.id for r in listed)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_forbidden_without_permission(async_session, game_role_service):
    r = await _role(async_session)
    body = GameRoleItemUpdateRequest(name="NewName")
    with pytest.raises(ForbiddenException):
        await game_role_service.update_role(r.id, body, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_not_found(async_session, game_role_service):
    body = GameRoleItemUpdateRequest(name="NewName")
    with pytest.raises(NotFoundException):
        await game_role_service.update_role(
            uuid.uuid4(),
            body,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_success(async_session, game_role_service):
    r = await _role(async_session)
    body = GameRoleItemUpdateRequest(name="NewName", min_in_team=2, max_in_team=4, hidden=True)
    updated = await game_role_service.update_role(
        r.id,
        body,
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    assert updated.name == "NewName"
    assert updated.hidden is True
    assert updated.min_in_team == 2
    assert updated.max_in_team == 4


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_not_found(async_session, game_role_service):
    with pytest.raises(NotFoundException):
        await game_role_service.delete_role(
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_forbidden_without_permission(async_session, game_role_service):
    r = await _role(async_session)
    with pytest.raises(ForbiddenException):
        await game_role_service.delete_role(r.id, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_success(async_session, game_role_service):
    r = await _role(async_session)
    await game_role_service.delete_role(
        r.id,
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    repo = game_role_service.role_repo
    assert await repo.get_by_id(r.id) is None
