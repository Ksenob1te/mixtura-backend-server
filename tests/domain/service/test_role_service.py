import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from src.domain.exceptions import ForbiddenException, InternalLogicException, NotFoundException
from src.domain.service.role import RoleService
from src.infra.postgre.models import Server, GameRoleSet, RatingSet, ServerRole
from src.infra.postgre.repo import ServerRepository, ServerRoleRepository, MemberRepository, PermissionRepository
from src.infra.postgre.static import PERMISSION


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


async def _server(session, public: bool = False) -> Server:
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(id=uuid.uuid4(), name="Server", owner_id=uuid.uuid4(), public=public, role_set_id=rs.id,
               rating_set_id=rts.id)
    session.add(s)
    await session.flush()
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
    permission_repo = PermissionRepository(async_session)
    return RoleService(server_repo, role_repo, member_repo, permission_repo)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_server_not_found(async_session, role_service):
    with pytest.raises(NotFoundException):
        await role_service.list_roles(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_empty_list(async_session, role_service):
    s = await _server(async_session)

    res = await role_service.list_roles(s.id)
    assert isinstance(res, list)
    assert res == []


@pytest.mark.asyncio(loop_scope="session")
async def test_list_roles_returns_roles(async_session, role_service):
    s = await _server(async_session)
    r1 = await _role(async_session, s, name="R1")
    r2 = await _role(async_session, s, name="R2")

    res = await role_service.list_roles(s.id)
    ids = {r.id for r in res}
    assert {r1.id, r2.id}.issubset(ids)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_forbidden_without_permission(async_session, role_service):
    s = await _server(async_session)
    with pytest.raises(ForbiddenException):
        await role_service.create_role(s.id, "Role", permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_success_default_position(async_session, role_service):
    s = await _server(async_session)

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
    s = await _server(async_session)

    role = await role_service.create_role(
        s.id,
        "Role",
        position=5,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert role.position == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_create_role_server_not_found(async_session, role_service):
    with pytest.raises(NotFoundException):
        await role_service.create_role(
            uuid.uuid4(),
            "Role",
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_role_forbidden_without_permission(async_session, role_service):
    s = await _server(async_session)
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
async def test_update_role_updates_name_and_position(async_session, role_service):
    s = await _server(async_session)
    r = await _role(async_session, s, name="Old", position=1)

    updated = await role_service.update_role(
        r.id,
        name="New",
        position=5,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    assert updated.name == "New"
    assert updated.position == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_forbidden_without_permission(async_session, role_service):
    s = await _server(async_session)
    r = await _role(async_session, s)

    with pytest.raises(ForbiddenException):
        await role_service.delete_role(r.id, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_success(async_session, role_service):
    s = await _server(async_session)
    r = await _role(async_session, s)

    await role_service.delete_role(
        r.id,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )

    repo: ServerRoleRepository = role_service.role_repo
    assert await repo.get_by_id(r.id) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_not_found(async_session, role_service):
    with pytest.raises(NotFoundException):
        await role_service.delete_role(
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_assigned_to_member(async_session, role_service):
    s = await _server(async_session)
    r = await _role(async_session, s)
    member = await role_service.member_repo.create(
        server_id=s.id,
        user_id=uuid.uuid4(),
        nickname="Name",
        server_role_id=r.id,
    )

    await role_service.delete_role(
        r.id,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ROLES),
    )
    repo: ServerRoleRepository = role_service.role_repo
    assert await repo.get_by_id(r.id) is None

    member_repo: MemberRepository = role_service.member_repo
    updated_member = await member_repo.get_by_id(member.id)     # type: ignore
    await async_session.refresh(updated_member)
    assert updated_member is not None
    assert updated_member.server_role_id is None
