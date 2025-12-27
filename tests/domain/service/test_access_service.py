import uuid
import pytest
from datetime import datetime, timedelta, UTC

from src.domain.service import AccessControlService
from src.domain.exceptions import NotFoundException, ForbiddenException, MigrationException
from src.domain.models.member.request import AddMemberRestrictionRequest
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre.repo import (
    MemberRepository,
    ServerRepository,
    MemberRestrictionRepository,
    RestrictionRepository,
    PermissionRepository,
    ServerRoleRepository

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
async def access_control_service(async_session):
    member_repo = MemberRepository(async_session)
    member_restriction_repo = MemberRestrictionRepository(async_session)
    server_repo = ServerRepository(async_session)
    restriction_repo = RestrictionRepository(async_session)
    permission_repo = PermissionRepository(async_session)

    return AccessControlService(
        member_repo,
        member_restriction_repo,
        server_repo,
        restriction_repo,
        permission_repo,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_restrictions_empty(async_session, access_control_service):
    member_repo = access_control_service.member_repo
    restriction_repo = access_control_service.restriction_repo

    server = await _server(async_session)
    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, nickname="Restricted")
    assert member is not None

    await restriction_repo.create(code=RESTRICTION.SERVER_BAN)
    assert await access_control_service.get_restrictions(server.id, user_id) == []


@pytest.mark.asyncio(loop_scope="session")
async def test_add_restriction(async_session, access_control_service):
    member_repo = access_control_service.member_repo
    restriction_repo = access_control_service.restriction_repo

    server = await _server(async_session)
    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, nickname="Restricted")
    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Issuer")
    assert member is not None
    assert issuer is not None

    restriction = await restriction_repo.create(code=RESTRICTION.SERVER_BAN)

    create_body = AddMemberRestrictionRequest(
        restriction_id=restriction.id,  # type: ignore
        reason="Bad behavior",
        expiration_date=datetime.now(UTC) + timedelta(days=1),
    )

    with pytest.raises(ForbiddenException):
        await access_control_service.add_restriction(
            member.id,
            issuer_id=issuer.id,
            body=create_body,
            permission_mask=perm_mask(),
        )

    mr = await access_control_service.add_restriction(
        member.id,
        issuer_id=issuer.id,
        body=create_body,
        permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
    )
    assert mr is not None and mr.member_id == member.id

    restrictions = await access_control_service.get_restrictions(server.id, user_id)
    assert len(restrictions) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_restriction(async_session, access_control_service):
    member_repo = access_control_service.member_repo
    restriction_repo = access_control_service.restriction_repo

    server = await _server(async_session)
    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, nickname="Restricted")
    issuer = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="Issuer")
    assert member is not None
    assert issuer is not None

    restriction = await restriction_repo.create(code=RESTRICTION.SERVER_BAN)

    create_body = AddMemberRestrictionRequest(
        restriction_id=restriction.id,  # type: ignore
        reason="Bad behavior",
        expiration_date=datetime.now(UTC) + timedelta(days=1),
    )

    mr = await access_control_service.add_restriction(
        member.id,
        issuer_id=issuer.id,
        body=create_body,
        permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
    )

    with pytest.raises(NotFoundException):
        await access_control_service.remove_restriction(
            uuid.uuid4(),
            member_restriction_id=mr.id,
            permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
        )

    with pytest.raises(ForbiddenException):
        await access_control_service.remove_restriction(
            member.id,
            member_restriction_id=mr.id,
            permission_mask=perm_mask(),
        )

    await access_control_service.remove_restriction(
        member.id,
        member_restriction_id=mr.id,
        permission_mask=perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
    )
    restrictions_after = await access_control_service.get_restrictions(server.id, user_id)
    assert restrictions_after == []


@pytest.mark.asyncio(loop_scope="session")
async def test_get_permissions_success(async_session, access_control_service):
    member_repo = access_control_service.member_repo
    server_role_repo = ServerRoleRepository(async_session)
    permission_repo = access_control_service.permission_repo
    server = await _server(async_session)

    role = await server_role_repo.create(server_id=server.id, name="Role", position=1)
    permission = await permission_repo.create(code=PERMISSION.KICK_MEMBERS)
    await permission_repo.assign_to_role(permission.id, role.id)

    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, nickname="User",
                                      server_role_id=role.id)

    perms = await access_control_service.get_permissions(server.id, user_id)
    assert PERMISSION.KICK_MEMBERS in perms


@pytest.mark.asyncio(loop_scope="session")
async def test_get_permission_mask_success_and_admin_override(async_session, access_control_service):
    member_repo = access_control_service.member_repo
    server_role_repo = ServerRoleRepository(async_session)
    permission_repo = access_control_service.permission_repo
    server = await _server(async_session)

    # Normal role
    role = await server_role_repo.create(server_id=server.id, name="Role", position=1)
    permission = await permission_repo.create(code=PERMISSION.KICK_MEMBERS)
    await permission_repo.assign_to_role(permission.id, role.id)
    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, nickname="User",
                                      server_role_id=role.id)

    mask = await access_control_service.get_permission_mask(server.id, user_id)
    assert PERMISSION.check_permission(mask, PERMISSION.KICK_MEMBERS)
    assert not PERMISSION.check_permission(mask, PERMISSION.RESTRICT_SERVER_BAN)

    # Admin role
    admin_role = await server_role_repo.create(server_id=server.id, name="Admin", position=10)
    admin_permission = await permission_repo.create(code=PERMISSION.ADMINISTRATOR)
    await permission_repo.assign_to_role(admin_permission.id, admin_role.id)
    admin_user_id = uuid.uuid4()
    admin = await member_repo.create(server_id=server.id, user_id=admin_user_id, nickname="Admin",
                                     server_role_id=admin_role.id)

    admin_mask = await access_control_service.get_permission_mask(server.id, admin_user_id)
    # Should have everything
    assert PERMISSION.check_permission(admin_mask, PERMISSION.RESTRICT_SERVER_BAN)
    assert PERMISSION.check_permission(admin_mask, PERMISSION.KICK_MEMBERS)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_restriction_mask_success(async_session, access_control_service):
    member_repo = access_control_service.member_repo
    restriction_repo = access_control_service.restriction_repo
    member_restriction_repo = access_control_service.member_restriction_repo
    server = await _server(async_session)

    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, nickname="Restricted")
    restriction = await restriction_repo.create(code=RESTRICTION.SERVER_BAN)

    await member_restriction_repo.create(
        member_id=member.id,
        restriction_id=restriction.id,
        reason="Test",
        expiration_date=datetime.now(UTC) + timedelta(days=1),
        creator_id=member.id
    )

    mask = await access_control_service.get_restriction_mask(server.id, user_id)
    assert RESTRICTION.check_restriction(mask, RESTRICTION.SERVER_BAN)


@pytest.mark.asyncio(loop_scope="session")
async def test_add_restriction_not_found(async_session, access_control_service):
    member_repo = access_control_service.member_repo
    server = await _server(async_session)
    member = await member_repo.create(server_id=server.id, user_id=uuid.uuid4(), nickname="User")

    body = AddMemberRestrictionRequest(
        restriction_id=uuid.uuid4(),
        reason="Reason",
        expiration_date=datetime.now(UTC) + timedelta(days=1)
    )

    with pytest.raises(NotFoundException):
        await access_control_service.add_restriction(
            member.id,
            issuer_id=member.id,
            body=body,
            permission_mask=perm_mask()
        )
