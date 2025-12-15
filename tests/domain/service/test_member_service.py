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
    MemberRestrictionRepository,
    ServerRepository,
    ServerRoleRepository,
    RestrictionRepository,
    PermissionRepository,
)
from src.infra.postgre.models import Server, GameRoleSet, RatingSet


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
    member_restriction_repo = MemberRestrictionRepository(async_session)
    server_repo = ServerRepository(async_session)
    server_role_repo = ServerRoleRepository(async_session)
    restriction_repo = RestrictionRepository(async_session)
    permission_repo = PermissionRepository(async_session)

    return MemberService(
        member_repo,
        member_restriction_repo,
        server_repo,
        server_role_repo,
        restriction_repo,
        permission_repo
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_list_members_returns_active_members(async_session, member_service):
    server = await _server(async_session)
    member_repo = member_service.member_repo

    m1 = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Active1")
    m2 = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Inactive1")
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
    member = await member_repo.create(server_id=server.id, user_id=user_id, name="User")
    assert member is not None
    await member_repo.deactivate(member)

    joined = await member_service.join_server(server.id, user_id, "User")
    assert joined.id == member.id
    assert joined.active is True


@pytest.mark.asyncio(loop_scope="session")
async def test_create_virtual_forbidden_without_permission(async_session, member_service):
    server = await _server(async_session)
    body = VirtualMemberCreateRequest(name="VirtualUser")
    with pytest.raises(ForbiddenException):
        await member_service.create_virtual(server.id, body, permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_virtual_success(async_session, member_service):
    server = await _server(async_session)
    body = VirtualMemberCreateRequest(name="VirtualUser")
    member = await member_service.create_virtual(
        server.id,
        body,
        permission_mask=perm_mask(PERMISSION.CREATE_VIRTUAL),
    )
    assert member is not None
    assert member.user_id is None
    assert member.name == "VirtualUser"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_member_permission_and_not_found(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="User")
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

    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Issuer")
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Old")
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
            PERMISSION.SELF_EDIT_NAME,
            PERMISSION.EDIT_NAME,
            PERMISSION.EDIT_ROLES,
        ),
        restriction_mask=restr_mask(),
    )
    assert updated.name == "New"
    assert updated.server_role_id == target_role.id


@pytest.mark.asyncio(loop_scope="session")
async def test_update_member_forbidden_on_name_and_role(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)

    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Issuer")
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Old")
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
async def test_update_member_forbidden_assign_higher_role(async_session, member_service):
    member_repo = member_service.member_repo
    server_role_repo = member_service.server_role_repo
    server = await _server(async_session)

    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Issuer")
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Target")
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
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Kick")
    assert member is not None

    with pytest.raises(ForbiddenException):
        await member_service.kick_member(member.id, permission_mask=0)

    with pytest.raises(NotFoundException):
        await member_service.kick_member(uuid.uuid4(), permission_mask=perm_mask(PERMISSION.KICK_MEMBERS))

    await member_service.kick_member(member.id, permission_mask=perm_mask(PERMISSION.KICK_MEMBERS))
    reloaded = await member_repo.get_by_id(member.id)
    assert reloaded is not None and reloaded.active is False


@pytest.mark.asyncio(loop_scope="session")
async def test_migrate_member_forbidden_without_permission(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    user_id = uuid.uuid4()
    current = await member_repo.create(server_id=server.id, user_id=user_id, name="Current")
    target = await member_repo.create(server_id=server.id, user_id=None, name="Target")
    assert current is not None and target is not None

    body = MigrationRequest(target_member_id=target.id)

    with pytest.raises(ForbiddenException):
        await member_service.migrate_member(current.id, body, permission_mask=perm_mask())


@pytest.mark.asyncio(loop_scope="session")
async def test_migrate_member_success(async_session, member_service):
    member_repo = member_service.member_repo
    server = await _server(async_session)
    user_id = uuid.uuid4()
    current = await member_repo.create(server_id=server.id, user_id=user_id, name="Current")
    target = await member_repo.create(server_id=server.id, user_id=None, name="Target")
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
    target = await member_repo.create(server_id=server.id, user_id=None, name="Target")
    no_user_current = await member_repo.create(server_id=server.id, user_id=None, name="NoUser")
    assert target is not None and no_user_current is not None

    with pytest.raises(MigrationException):
        await member_service.migrate_member(
            no_user_current.id,
            MigrationRequest(target_member_id=target.id),
            permission_mask=perm_mask(PERMISSION.MIGRATE_MEMBERS),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_restrictions_permissions_and_empty(async_session, member_service):
    member_repo = member_service.member_repo
    restriction_repo = member_service.restriction_repo

    server = await _server(async_session)
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Restricted")
    assert member is not None

    await restriction_repo.create(code=RESTRICTION.SERVER_BAN)
    assert await member_service.get_restrictions(member.id) == []


@pytest.mark.asyncio(loop_scope="session")
async def test_add_restriction_permission_and_success(async_session, member_service):
    member_repo = member_service.member_repo
    restriction_repo = member_service.restriction_repo

    server = await _server(async_session)
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Restricted")
    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Issuer")
    assert member is not None
    assert issuer is not None

    restriction = await restriction_repo.create(code=RESTRICTION.SERVER_BAN)

    create_body = MemberRestrictionCreateRequest(
        restriction_id=restriction.id,      # type: ignore
        reason="Bad behavior",
        expiration_date=datetime.now(UTC) + timedelta(days=1),
    )

    with pytest.raises(ForbiddenException):
        await member_service.add_restriction(
            member.id,
            issuer_id=issuer.id,
            body=create_body,
            permission_mask=perm_mask(),
        )

    mr = await member_service.add_restriction(
        member.id,
        issuer_id=issuer.id,
        body=create_body,
        permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
    )
    assert mr is not None and mr.member_id == member.id

    restrictions = await member_service.get_restrictions(member.id)
    assert len(restrictions) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_restriction_permission_and_success(async_session, member_service):
    member_repo = member_service.member_repo
    restriction_repo = member_service.restriction_repo

    server = await _server(async_session)
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Restricted")
    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), name="Issuer")
    assert member is not None
    assert issuer is not None

    restriction = await restriction_repo.create(code=RESTRICTION.SERVER_BAN)

    create_body = MemberRestrictionCreateRequest(
        restriction_id=restriction.id,      # type: ignore
        reason="Bad behavior",
        expiration_date=datetime.now(UTC) + timedelta(days=1),
    )

    mr = await member_service.add_restriction(
        member.id,
        issuer_id=issuer.id,
        body=create_body,
        permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
    )
    assert mr is not None

    with pytest.raises(NotFoundException):
        await member_service.remove_restriction(
            uuid.uuid4(),
            member_restriction_id=mr.id,
            permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
        )

    with pytest.raises(ForbiddenException):
        await member_service.remove_restriction(
            member.id,
            member_restriction_id=mr.id,
            permission_mask=perm_mask(),
        )

    await member_service.remove_restriction(
        member.id,
        member_restriction_id=mr.id,
        permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
    )
    restrictions_after = await member_service.get_restrictions(member.id)
    assert restrictions_after == []
