import uuid
import pytest

from src.domain.service.game_role import GameRoleService
from src.domain.exceptions import NotFoundException, ForbiddenException
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
    server = await _server(async_session, rs)
    with pytest.raises(ForbiddenException):
        await game_role_service.update_role_set(rs.id, server.id, name="NewName", permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_set_mismatch_raises_not_found(async_session, game_role_service):
    # Renamed from test_update_role_set_not_found because implementation raises Forbidden for mismatch
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    with pytest.raises(NotFoundException):
        await game_role_service.update_role_set(
            uuid.uuid4(),
            server.id,
            name="NewName",
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_set_success(async_session, game_role_service):
    rs = await _role_set(async_session, name="Old")
    server = await _server(async_session, rs)
    updated = await game_role_service.update_role_set(
        rs.id,
        server.id,
        name="New",
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    assert updated.name == "New"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_forbidden_without_permission(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    with pytest.raises(ForbiddenException):
        await game_role_service.create_role(
            rs.id,
            server.id,
            name="R",
            min_in_team=1,
            max_in_team=2,
            hidden=False,
            permission_mask=0
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_role_set_not_found(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    with pytest.raises(NotFoundException):
        await game_role_service.create_role(
            uuid.uuid4(),
            server.id,
            name="R",
            min_in_team=1,
            max_in_team=2,
            hidden=False,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_wrong_server(async_session, game_role_service):
    rs1 = await _role_set(async_session)
    s1 = await _server(async_session, rs1)
    rs2 = await _role_set(async_session)
    s2 = await _server(async_session, rs2)

    with pytest.raises(NotFoundException):
        await game_role_service.create_role(
            rs1.id,
            s2.id,  # Wrong server
            name="R",
            min_in_team=1,
            max_in_team=2,
            hidden=False,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_success(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    role = await game_role_service.create_role(
        rs.id,
        server.id,
        name="Support",
        min_in_team=1,
        max_in_team=3,
        hidden=False,
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    assert role is not None
    assert role.name == "Support"
    repo = game_role_service.role_repo
    listed = await repo.list_for_set(rs.id)
    assert any(r.id == role.id for r in listed)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_forbidden_without_permission(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    r = await _role(async_session, role_set=rs)
    with pytest.raises(ForbiddenException):
        await game_role_service.update_role(r.id, server.id, name="NewName", permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_not_found(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    with pytest.raises(NotFoundException):
        await game_role_service.update_role(
            uuid.uuid4(),
            server.id,
            name="NewName",
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_wrong_server(async_session, game_role_service):
    rs1 = await _role_set(async_session)
    s1 = await _server(async_session, rs1)
    r1 = await _role(async_session, role_set=rs1)

    rs2 = await _role_set(async_session)
    s2 = await _server(async_session, rs2)

    with pytest.raises(NotFoundException):
        await game_role_service.update_role(
            r1.id,
            s2.id,  # Wrong server
            name="NewName",
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_success(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    r = await _role(async_session, role_set=rs)
    updated = await game_role_service.update_role(
        r.id,
        server.id,
        name="NewName",
        min_in_team=2,
        max_in_team=4,
        hidden=True,
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    assert updated.name == "NewName"
    assert updated.hidden is True
    assert updated.min_in_team == 2
    assert updated.max_in_team == 4


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_not_found(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    with pytest.raises(NotFoundException):
        await game_role_service.delete_role(
            uuid.uuid4(),
            server.id,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_forbidden_without_permission(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    r = await _role(async_session, role_set=rs)
    with pytest.raises(ForbiddenException):
        await game_role_service.delete_role(r.id, server.id, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_success(async_session, game_role_service):
    rs = await _role_set(async_session)
    server = await _server(async_session, rs)
    r = await _role(async_session, role_set=rs)
    await game_role_service.delete_role(
        r.id,
        server.id,
        permission_mask=perm_mask(PERMISSION.EDIT_ROLE_SET),
    )
    repo = game_role_service.role_repo
    assert await repo.get_by_id(r.id) is None
