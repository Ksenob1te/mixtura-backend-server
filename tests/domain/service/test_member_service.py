import uuid
import pytest
from datetime import datetime, timedelta, UTC

from src.domain.service.member import MemberService
from src.domain.exceptions import NotFoundException, ForbiddenException, MigrationException
from src.domain.models.member.request import (
    VirtualMemberCreateRequest,
    MemberUpdateRequest,
    MigrationRequest,
    MemberRestrictionCreateRequest,
)
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre.repo import (
    MemberRepository,
    ServerRepository,
    ServerRoleRepository
)
from src.infra.postgre.models import Server, GameRoleSet, RatingSet

# TODO: refactor tests into classes, setups and fixtures


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


def restr_mask(*restrs: RESTRICTION) -> int:
    return RESTRICTION.serialize_restriction_codes(restrs)


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


@pytest.fixture
async def member_service(async_session):
    member_repo = MemberRepository(async_session)
    server_repo = ServerRepository(async_session)
    server_role_repo = ServerRoleRepository(async_session)

    return MemberService(
        member_repo,
        server_repo,
        server_role_repo
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_list_members_returns_active_members(async_session, member_service):
    server = await _server(async_session)
    member_repo = member_service.member_repo

    m1 = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Active1")
    m2 = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Inactive1")
    assert m1 is not None and m2 is not None
    await member_repo.deactivate(m2)

    res = await member_service.list_members(
        server.id,
    )
    assert isinstance(res, list)
    assert {m.id for m in res} == {m1.id}


@pytest.mark.asyncio(loop_scope="session")
async def test_join_server_not_found_without_server(async_session, member_service):
    with pytest.raises(NotFoundException):
        await member_service.join_server(uuid.uuid4(), uuid.uuid4(), "User")


@pytest.mark.asyncio(loop_scope="session")
async def test_join_server_not_found_when_server_private(async_session, member_service):
    server = await _server(async_session)
    with pytest.raises(NotFoundException):
        await member_service.join_server(server.id, uuid.uuid4(), "User")


@pytest.mark.asyncio(loop_scope="session")
async def test_join_server_not_found_when_banned(async_session, member_service):
    server = await _server(async_session, public=True)
    with pytest.raises(NotFoundException):
        await member_service.join_server(
            server.id,
            uuid.uuid4(),
            "User",
            restriction_mask=restr_mask(RESTRICTION.SERVER_BAN),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_join_server_returns_existing_member_and_reactivates(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session, public=True)
    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, nickname="User")
    assert member is not None
    await member_repo.deactivate(member)

    joined = await member_service.join_server(server.id, user_id, "User")
    assert joined.id == member.id
    assert joined.active is True


@pytest.mark.asyncio(loop_scope="session")
async def test_join_server_success_new_member(async_session, member_service):
    server = await _server(async_session, public=True)
    user_id = uuid.uuid4()

    joined = await member_service.join_server(server.id, user_id, "NewUser")
    assert joined is not None
    assert joined.user_id == user_id
    assert joined.nickname == "NewUser"
    assert joined.active is True


@pytest.mark.asyncio(loop_scope="session")
async def test_create_virtual_forbidden_without_permission(async_session, member_service):
    server = await _server(async_session)
    body = VirtualMemberCreateRequest(nickname="VirtualUser")
    with pytest.raises(ForbiddenException):
        await member_service.create_virtual(server.id, body, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_virtual_not_found_without_server(async_session, member_service):
    body = VirtualMemberCreateRequest(nickname="VirtualUser")
    with pytest.raises(NotFoundException):
        await member_service.create_virtual(
            uuid.uuid4(),
            body,
            permission_mask=perm_mask(PERMISSION.CREATE_VIRTUAL),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_virtual_success(async_session, member_service):
    server = await _server(async_session)
    body = VirtualMemberCreateRequest(nickname="VirtualUser")
    member = await member_service.create_virtual(
        server.id,
        body,
        permission_mask=perm_mask(PERMISSION.CREATE_VIRTUAL),
    )
    assert member is not None
    assert member.user_id is None
    assert member.nickname == "VirtualUser"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_member_and_not_found(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="User")
    assert member is not None

    fetched = await member_service.get_member(member.id)
    assert fetched.id == member.id

    with pytest.raises(NotFoundException):
        await member_service.get_member(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_name_and_role(async_session, member_service):
    member_repo = member_service.member_repo
    server_role_repo = member_service.server_role_repo
    server = await _server(async_session)

    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Issuer")
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Old")
    assert issuer is not None and member is not None

    issuer_role = await server_role_repo.create(server_id=server.id, name="Admin", position=10)
    target_role = await server_role_repo.create(server_id=server.id, name="Mod", position=5)

    issuer.server_role_id = issuer_role.id
    issuer.server_role = issuer_role
    await async_session.flush()

    body = MemberUpdateRequest(name="New", server_role_id=target_role.id)  # type: ignore
    updated = await member_service.update_member(
        issuer_id=issuer.id,
        member_id=member.id,
        body=body,
        permission_mask=perm_mask(
            PERMISSION.EDIT_NAME,
            PERMISSION.EDIT_ROLES,
        ),
        restriction_mask=restr_mask(),
    )
    assert updated.nickname == "New"
    assert updated.server_role_id == target_role.id


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_not_found(async_session, member_service):
    body = MemberUpdateRequest(name="New")
    with pytest.raises(NotFoundException):
        await member_service.update_member(
            issuer_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            body=body,
            permission_mask=perm_mask(PERMISSION.EDIT_NAME),
            restriction_mask=restr_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_role_not_found(async_session, member_service):
    member_repo = member_service.member_repo
    server_role_repo = member_service.server_role_repo
    server = await _server(async_session)

    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Issuer")
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Target")

    issuer_role = await server_role_repo.create(server_id=server.id, name="Admin", position=10)
    issuer.server_role_id = issuer_role.id
    issuer.server_role = issuer_role
    await async_session.flush()

    body = MemberUpdateRequest(server_role_id=uuid.uuid4())  # Random UUID

    with pytest.raises(NotFoundException):
        await member_service.update_member(
            issuer_id=issuer.id,
            member_id=member.id,
            body=body,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLES),
            restriction_mask=restr_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_forbidden_name(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)

    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Issuer")
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Old")
    assert issuer is not None and member is not None

    body = MemberUpdateRequest(name="New", server_role_id=None)

    with pytest.raises(ForbiddenException):
        await member_service.update_member(
            issuer_id=issuer.id,
            member_id=member.id,
            body=body,
            permission_mask=perm_mask(),
            restriction_mask=restr_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_self_name(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)

    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Old")
    assert member is not None

    body = MemberUpdateRequest(name="New", server_role_id=None)
    updated = await member_service.update_member(
        issuer_id=member.id,
        member_id=member.id,
        body=body,
        permission_mask=perm_mask(),
        restriction_mask=restr_mask(),
    )
    assert updated.nickname == "New"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_forbidden_self_name(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)

    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Old")
    assert member is not None

    body = MemberUpdateRequest(name="New", server_role_id=None)

    with pytest.raises(ForbiddenException):
        await member_service.update_member(
            issuer_id=member.id,
            member_id=member.id,
            body=body,
            permission_mask=perm_mask(),
            restriction_mask=restr_mask(RESTRICTION.SELF_EDIT_NAME),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_forbidden_assign_higher_role(async_session, member_service):
    member_repo = member_service.member_repo
    server_role_repo = member_service.server_role_repo
    server = await _server(async_session)

    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Issuer")
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Target")
    assert issuer is not None and member is not None

    issuer_role = await server_role_repo.create(server_id=server.id, name="Mod", position=5)
    higher_role = await server_role_repo.create(server_id=server.id, name="Admin", position=10)

    issuer.server_role_id = issuer_role.id
    issuer.server_role = issuer_role
    await async_session.flush()

    body = MemberUpdateRequest(name=None, server_role_id=higher_role.id)  # type: ignore

    with pytest.raises(ForbiddenException):
        await member_service.update_member(
            issuer_id=issuer.id,
            member_id=member.id,
            body=body,
            permission_mask=perm_mask(PERMISSION.EDIT_ROLES),
            restriction_mask=restr_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_kick_member_flow(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Kick")
    assert member is not None

    with pytest.raises(ForbiddenException):
        await member_service.kick_member(member.id, permission_mask=0)

    with pytest.raises(NotFoundException):
        await member_service.kick_member(uuid.uuid4(), permission_mask=perm_mask(PERMISSION.KICK_MEMBERS))

    await member_service.kick_member(member.id, permission_mask=perm_mask(PERMISSION.KICK_MEMBERS))
    reloaded = await member_repo.get_by_id(member.id)
    assert reloaded is not None and reloaded.active is False


@pytest.mark.asyncio(loop_scope="session")
async def test_migrate_member_forbidden(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    user_id = uuid.uuid4()
    current = await member_repo.create(server_id=server.id, user_id=user_id, nickname="Current")
    target = await member_repo.create(server_id=server.id, user_id=None, nickname="Target")
    assert current is not None and target is not None

    body = MigrationRequest(target_member_id=target.id)

    with pytest.raises(ForbiddenException):
        await member_service.migrate_member(current.id, body, permission_mask=perm_mask())


@pytest.mark.asyncio(loop_scope="session")
async def test_migrate_member_success(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    user_id = uuid.uuid4()
    current = await member_repo.create(server_id=server.id, user_id=user_id, nickname="Current")
    target = await member_repo.create(server_id=server.id, user_id=None, nickname="Target")
    assert current is not None and target is not None

    body = MigrationRequest(target_member_id=target.id)

    migrated = await member_service.migrate_member(
        current.id,
        body,
        permission_mask=perm_mask(PERMISSION.MIGRATE_MEMBERS),
    )
    assert migrated.id == target.id
    assert migrated.user_id == user_id

    reloaded_current = await member_repo.get_by_id(current.id)
    assert reloaded_current is not None
    assert reloaded_current.user_id is None
    assert reloaded_current.active is False


@pytest.mark.asyncio(loop_scope="session")
async def test_migrate_member_raises_when_current_has_no_user(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    target = await member_repo.create(server_id=server.id, user_id=None, nickname="Target")
    no_user_current = await member_repo.create(server_id=server.id, user_id=None, nickname="NoUser")
    assert target is not None and no_user_current is not None

    with pytest.raises(MigrationException):
        await member_service.migrate_member(
            no_user_current.id,
            MigrationRequest(target_member_id=target.id),
            permission_mask=perm_mask(PERMISSION.MIGRATE_MEMBERS),
        )
