import uuid
import pytest

from src.domain.service.invite import InviteService
from src.domain.exceptions import NotFoundException, ForbiddenException
from src.domain.models.invites.request import InviteCreateRequest
from src.infra.postgre.models import Server, GameRoleSet, RatingSet
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre.repo import InviteRepository, ServerRepository, MemberRepository


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
async def invite_service(async_session) -> InviteService:
    invite_repo = InviteRepository(async_session)
    server_repo = ServerRepository(async_session)
    member_repo = MemberRepository(async_session)

    return InviteService(
        invite_repo,
        server_repo,
        member_repo,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_invite_info_success(async_session, invite_service):
    server = await _server(async_session)
    invite_repo: InviteRepository = invite_service.invite_repo

    inv = await invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)
    assert inv is not None

    fetched = await invite_service.get_invite_info(inv.key)
    assert fetched.id == inv.id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_invite_info_not_found(invite_service):
    with pytest.raises(NotFoundException):
        await invite_service.get_invite_info("non-existent")


@pytest.mark.asyncio(loop_scope="session")
async def test_use_invite_creates_member(async_session, invite_service):
    server = await _server(async_session)
    invite_repo: InviteRepository = invite_service.invite_repo
    member_repo: MemberRepository = invite_service.member_repo

    inv = await invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)
    assert inv is not None

    user_id = uuid.uuid4()
    member = await invite_service.use_invite(inv.key, user_id, "User", restriction_mask=restr_mask())
    assert member is not None
    assert member.user_id == user_id

    # ensure use_limit decremented
    reloaded = await invite_repo.get_by_id(inv.id)
    assert reloaded is not None
    assert reloaded.use_limit == 0

    # ensure member persisted
    stored = await member_repo.get_by_id(member.id)
    assert stored is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_use_invite_not_found_or_exhausted(async_session, invite_service):
    server = await _server(async_session)
    invite_repo: InviteRepository = invite_service.invite_repo

    inv = await invite_repo.create(server_id=server.id, use_limit=0, inviter_id=None)
    assert inv is not None

    with pytest.raises(NotFoundException):
        await invite_service.use_invite(inv.key, uuid.uuid4(), "User")

    with pytest.raises(NotFoundException):
        await invite_service.use_invite("non-existent", uuid.uuid4(), "User")


@pytest.mark.asyncio(loop_scope="session")
async def test_use_invite_restriction_ban(async_session, invite_service):
    server = await _server(async_session)
    invite_repo: InviteRepository = invite_service.invite_repo

    inv = await invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)
    assert inv is not None

    with pytest.raises(NotFoundException):
        await invite_service.use_invite(
            inv.key,
            uuid.uuid4(),
            "User",
            restriction_mask=restr_mask(RESTRICTION.SERVER_BAN),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_use_invite_reactivates_existing_member(async_session, invite_service):
    server = await _server(async_session)
    invite_repo: InviteRepository = invite_service.invite_repo
    member_repo: MemberRepository = invite_service.member_repo

    inv = await invite_repo.create(server_id=server.id, use_limit=2, inviter_id=None)
    assert inv is not None

    user_id = uuid.uuid4()
    member = await member_repo.create(server_id=server.id, user_id=user_id, name="User")
    assert member is not None

    await member_repo.deactivate(member)

    joined = await invite_service.use_invite(inv.key, user_id, "User")
    assert joined.id == member.id
    assert joined.active is True


@pytest.mark.asyncio(loop_scope="session")
async def test_list_invites_permission_and_success(async_session, invite_service):
    server = await _server(async_session)
    invite_repo: InviteRepository = invite_service.invite_repo

    inv1 = await invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)
    inv2 = await invite_repo.create(server_id=server.id, use_limit=2, inviter_id=None)
    assert inv1 is not None and inv2 is not None

    with pytest.raises(ForbiddenException):
        await invite_service.list_invites(server.id, permission_mask=perm_mask())

    invites = await invite_service.list_invites(
        server.id,
        permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
    )
    keys = {i.id for i in invites}
    assert {inv1.id, inv2.id}.issubset(keys)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_invites_server_not_found(invite_service):
    with pytest.raises(NotFoundException):
        await invite_service.list_invites(uuid.uuid4(), permission_mask=perm_mask(PERMISSION.EDIT_INVITES))


@pytest.mark.asyncio(loop_scope="session")
async def test_create_invite(async_session, invite_service):
    server = await _server(async_session)

    body = InviteCreateRequest(use_limit=5)
    invite = await invite_service.create_invite(
        server.id,
        body,
        inviter_id=None,
        permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
    )
    assert invite is not None
    assert invite.use_limit == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_create_invite_zero_and_negative(async_session, invite_service):
    server = await _server(async_session)

    body_none = InviteCreateRequest(use_limit=None)
    inv_none = await invite_service.create_invite(
        server.id,
        body_none,
        inviter_id=None,
        permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
    )
    assert inv_none.use_limit == 0

    body_negative = InviteCreateRequest(use_limit=-10)
    inv_negative = await invite_service.create_invite(
        server.id,
        body_negative,
        inviter_id=None,
        permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
    )
    assert inv_negative.use_limit == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_create_invite_forbidden_and_not_found(invite_service):
    with pytest.raises(NotFoundException):
        await invite_service.create_invite(
            uuid.uuid4(),
            InviteCreateRequest(use_limit=1),
            inviter_id=None,
            permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
        )
    server = await _server(invite_service.invite_repo.session)
    with pytest.raises(ForbiddenException):
        await invite_service.create_invite(
            server.id,
            InviteCreateRequest(use_limit=1),
            inviter_id=None,
            permission_mask=perm_mask()
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_invite_inviter_not_found(async_session, invite_service):
    server = await _server(async_session)

    with pytest.raises(NotFoundException):
        await invite_service.create_invite(
            server.id,
            InviteCreateRequest(use_limit=1),
            inviter_id=uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_revoke_invite(async_session, invite_service):
    server = await _server(async_session)
    invite_repo: InviteRepository = invite_service.invite_repo

    inv = await invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)
    assert inv is not None

    with pytest.raises(ForbiddenException):
        await invite_service.revoke_invite(inv.server_id, inv.id, permission_mask=perm_mask())

    await invite_service.revoke_invite(
        inv.server_id,
        inv.id,
        permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
    )
    assert await invite_repo.get_by_id(inv.id) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_revoke_invite_server_not_found(invite_service):
    with pytest.raises(NotFoundException):
        await invite_service.revoke_invite(
            uuid.uuid4(),
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_INVITES),
        )
