import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from src.domain.exceptions import ForbiddenException, InternalLogicException, NotFoundException
from src.domain.service.role import RoleService
from src.infra.postgre.models import Server, GameRoleSet, RatingSet, ServerRole
from src.infra.postgre.repo import ServerRepository, ServerRoleRepository, MemberRepository
from src.infra.postgre.static import PERMISSION


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


async def _role_set(async_session, name: str = "Set") -> GameRoleSet:
    rs = GameRoleSet(name=name, is_global=False)
    async_session.add(rs)
    await async_session.flush()
    return rs


async def _server(async_session, role_set: GameRoleSet) -> Server:
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    async_session.add(rts)
    await async_session.flush()
    s = Server(
        id=uuid.uuid4(),
        name="Server",
        owner_id=uuid.uuid4(),
        public=True,
        role_set_id=role_set.id,
        rating_set_id=rts.id,
    )
    async_session.add(s)
    await async_session.flush()
    return s


async def _role(async_session, server: Server, name: str = "Role", position: int = 0) -> ServerRole:
    r = ServerRole(server_id=server.id, name=name, position=position)
    async_session.add(r)
    await async_session.flush()
    return r


@pytest.fixture
async def role_service(async_session):
    server_repo = ServerRepository(async_session)
    role_repo = ServerRoleRepository(async_session)
    member_repo = MemberRepository(async_session)
    return RoleService(server_repo, role_repo, member_repo)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_server_not_found(async_session, role_service):
    with pytest.raises(NotFoundException):
        await role_service.list_roles(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_empty_list(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)

    res = await role_service.list_roles(s.id)
    assert isinstance(res, list)
    assert res == []


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_returns_roles(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r1 = await _role(async_session, s, name="R1")
    r2 = await _role(async_session, s, name="R2")

    res = await role_service.list_roles(s.id)
    ids = {r.id for r in res}
    assert {r1.id, r2.id}.issubset(ids)


# create_role


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_forbidden_without_permission(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    with pytest.raises(ForbiddenException):
        await role_service.create_role(s.id, "Role", permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_success_default_position(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)

    role = await role_service.create_role(
        s.id,
        "Role",
        position=None,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert role is not None
    assert role.name == "Role"
    assert role.position == 0
    repo: ServerRoleRepository = role_service.role_repo
    listed = await repo.list_for_server(s.id)
    assert any(r.id == role.id for r in listed)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_success_with_position(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)

    role = await role_service.create_role(
        s.id,
        "Role",
        position=5,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert role.position == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_integrity_error_raises_internal_logic(async_session, role_service, monkeypatch):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)

    async def fake_create(*args, **kwargs):  # type: ignore[unused-argument]
        raise IntegrityError("stmt", {}, Exception("orig"))

    monkeypatch.setattr(role_service.role_repo, "create", fake_create)

    with pytest.raises(InternalLogicException):
        await role_service.create_role(
            s.id,
            "Role",
            position=None,
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_none_return_raises_internal_logic(async_session, role_service, monkeypatch):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)

    async def fake_create(*args, **kwargs):  # type: ignore[unused-argument]
        return None

    monkeypatch.setattr(role_service.role_repo, "create", fake_create)

    with pytest.raises(InternalLogicException):
        await role_service.create_role(
            s.id,
            "Role",
            position=None,
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )


# update_role


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_forbidden_without_permission(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r = await _role(async_session, s)

    with pytest.raises(ForbiddenException):
        await role_service.update_role(r.id, name="New", permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_not_found(async_session, role_service):
    with pytest.raises(NotFoundException):
        await role_service.update_role(
            uuid.uuid4(),
            name="New",
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_changes_name(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r = await _role(async_session, s, name="Old")

    updated = await role_service.update_role(
        r.id,
        name="New",
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert updated.name == "New"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_does_not_call_set_name_if_same(async_session, role_service, monkeypatch):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r = await _role(async_session, s, name="Same")

    called = False

    async def fake_set_name(role, name):  # type: ignore[unused-argument]
        nonlocal called
        called = True
        return role

    monkeypatch.setattr(role_service.role_repo, "set_name", fake_set_name)

    updated = await role_service.update_role(
        r.id,
        name="Same",
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert updated.name == "Same"
    assert called is False


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_updates_position(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r = await _role(async_session, s, position=1)

    updated = await role_service.update_role(
        r.id,
        position=10,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert updated.position == 10


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_updates_name_and_position(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r = await _role(async_session, s, name="Old", position=1)

    updated = await role_service.update_role(
        r.id,
        name="New",
        position=5,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert updated.name == "New"
    assert updated.position == 5


# delete_role


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_forbidden_without_permission(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r = await _role(async_session, s)

    with pytest.raises(ForbiddenException):
        await role_service.delete_role(r.id, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_success(async_session, role_service):
    rs = await _role_set(async_session)
    s = await _server(async_session, rs)
    r = await _role(async_session, s)

    await role_service.delete_role(
        r.id,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    repo: ServerRoleRepository = role_service.role_repo
    assert await repo.get_by_id(r.id) is None


class _Orig:
    def __init__(self, sqlstate: str | None):
        self.sqlstate = sqlstate


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_fk_violation_translates_to_not_found(async_session, role_service, monkeypatch):
    async def fake_delete(role_id):  # type: ignore[unused-argument]
        raise IntegrityError("stmt", {}, _Orig("23503"))

    monkeypatch.setattr(role_service.role_repo, "delete", fake_delete)

    with pytest.raises(NotFoundException):
        await role_service.delete_role(
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_other_integrity_error_translates_to_internal_logic(async_session, role_service, monkeypatch):
    async def fake_delete(role_id):  # type: ignore[unused-argument]
        raise IntegrityError("stmt", {}, _Orig("99999"))

    monkeypatch.setattr(role_service.role_repo, "delete", fake_delete)

    with pytest.raises(InternalLogicException):
        await role_service.delete_role(
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )

