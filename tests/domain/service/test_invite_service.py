import uuid
import pytest
import pytest_asyncio

from src.domain.service.invite import InviteService
from src.domain.exceptions import NotFoundException, ForbiddenException
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre.repo import InviteRepository, ServerRepository, MemberRepository


@pytest_asyncio.fixture(loop_scope="session")
async def invite_service(async_session) -> InviteService:
    return InviteService(
        InviteRepository(async_session),
        ServerRepository(async_session),
        MemberRepository(async_session),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestInviteService:

    async def test_get_invite_info_success(self, invite_service, factory):
        server = await factory.create_server()
        inv = await invite_service.invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)

        fetched = await invite_service.get_invite_info(inv.key)
        assert fetched.id == inv.id

    async def test_get_invite_info_not_found(self, invite_service):
        with pytest.raises(NotFoundException):
            await invite_service.get_invite_info("non-existent")

    async def test_use_invite_creates_member(self, invite_service, factory, helpers):
        server = await factory.create_server()
        inv = await invite_service.invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)

        user_id = uuid.uuid4()
        member = await invite_service.use_invite(inv.key, user_id, "User", restriction_mask=helpers.restr_mask())
        assert member is not None
        assert member.user_id == user_id

        reloaded = await invite_service.invite_repo.get_by_id(inv.id)
        assert reloaded.use_limit == 0

    async def test_use_invite_not_found_or_exhausted(self, invite_service, factory):
        server = await factory.create_server()
        inv = await invite_service.invite_repo.create(server_id=server.id, use_limit=0, inviter_id=None)

        with pytest.raises(NotFoundException):
            await invite_service.use_invite(inv.key, uuid.uuid4(), "User")

        with pytest.raises(NotFoundException):
            await invite_service.use_invite("non-existent", uuid.uuid4(), "User")

    async def test_use_invite_restriction_ban(self, invite_service, factory, helpers):
        server = await factory.create_server()
        inv = await invite_service.invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)

        with pytest.raises(NotFoundException):
            await invite_service.use_invite(
                inv.key,
                uuid.uuid4(),
                "User",
                restriction_mask=helpers.restr_mask(RESTRICTION.SERVER_BAN),
            )

    async def test_use_invite_reactivates_existing_member(self, invite_service, factory):
        server = await factory.create_server()
        inv = await invite_service.invite_repo.create(server_id=server.id, use_limit=2, inviter_id=None)

        user_id = uuid.uuid4()
        member = await factory.create_member(server.id, user_id=user_id, nickname="User")
        await invite_service.member_repo.deactivate(member)

        joined = await invite_service.use_invite(inv.key, user_id, "User")
        assert joined.id == member.id
        assert joined.active is True

    async def test_list_invites_permission_and_success(self, invite_service, factory, helpers):
        server = await factory.create_server()
        inv1 = await invite_service.invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)
        inv2 = await invite_service.invite_repo.create(server_id=server.id, use_limit=2, inviter_id=None)

        with pytest.raises(ForbiddenException):
            await invite_service.list_invites(server.id, permission_mask=helpers.perm_mask())

        invites = await invite_service.list_invites(
            server.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
        )
        keys = {i.id for i in invites}
        assert {inv1.id, inv2.id}.issubset(keys)

    async def test_list_invites_server_not_found(self, invite_service, helpers):
        with pytest.raises(NotFoundException):
            await invite_service.list_invites(uuid.uuid4(), permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES))

    async def test_create_invite(self, invite_service, factory, helpers):
        server = await factory.create_server()

        invite = await invite_service.create_invite(
            server.id,
            5,
            inviter_id=None,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
        )
        assert invite is not None
        assert invite.use_limit == 5

    async def test_create_invite_zero_and_negative(self, invite_service, factory, helpers):
        server = await factory.create_server()

        inv_none = await invite_service.create_invite(
            server.id,
            None,
            inviter_id=None,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
        )
        assert inv_none.use_limit == 0

        inv_negative = await invite_service.create_invite(
            server.id,
            -10,
            inviter_id=None,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
        )
        assert inv_negative.use_limit == 0

    async def test_create_invite_not_found(self, invite_service, helpers):
        with pytest.raises(NotFoundException):
            await invite_service.create_invite(
                uuid.uuid4(),
                1,
                inviter_id=None,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
            )

    async def test_create_invite_forbidden(self, invite_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(ForbiddenException):
            await invite_service.create_invite(
                server.id,
                1,
                inviter_id=None,
                permission_mask=helpers.perm_mask()
            )

    async def test_create_invite_inviter_not_found(self, invite_service, factory, helpers):
        server = await factory.create_server()

        with pytest.raises(NotFoundException):
            await invite_service.create_invite(
                server.id,
                1,
                inviter_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
            )

    async def test_revoke_invite(self, invite_service, factory, helpers):
        server = await factory.create_server()
        inv = await invite_service.invite_repo.create(server_id=server.id, use_limit=1, inviter_id=None)

        with pytest.raises(ForbiddenException):
            await invite_service.revoke_invite(server.id, inv.id, permission_mask=helpers.perm_mask())

        await invite_service.revoke_invite(
            server.id,
            inv.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
        )
        assert await invite_service.invite_repo.get_by_id(inv.id) is None

    async def test_revoke_invite_server_not_found(self, invite_service, helpers):
        with pytest.raises(NotFoundException):
            await invite_service.revoke_invite(
                uuid.uuid4(),
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
            )

    async def test_revoke_invite_wrong_server(self, invite_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        inv = await invite_service.invite_repo.create(server_id=server1.id, use_limit=1, inviter_id=None)

        with pytest.raises(NotFoundException):
            await invite_service.revoke_invite(
                server2.id,
                inv.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_INVITES),
            )
