import uuid
import pytest
import pytest_asyncio

from src.domain.service.member import MemberService
from src.domain.exceptions import NotFoundException, ForbiddenException, MigrationException
from src.domain.models.member.request import (
    VirtualMemberCreateRequest,
    MemberUpdateRequest,
    MemberMigrationRequest,
)
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre.repo import (
    MemberRepository,
    ServerRepository,
    ServerRoleRepository
)


@pytest_asyncio.fixture(loop_scope="session")
async def member_service(async_session):
    return MemberService(
        MemberRepository(async_session),
        ServerRepository(async_session),
        ServerRoleRepository(async_session)
    )


@pytest.mark.asyncio(loop_scope="session")
class TestMemberService:

    async def test_list_members_returns_active_members(self, member_service, factory):
        server = await factory.create_server()
        m1 = await factory.create_member(server.id, nickname="Active1")
        m2 = await factory.create_member(server.id, nickname="Inactive1")
        await member_service.member_repo.deactivate(m2)

        res = await member_service.list_members(server.id)
        assert isinstance(res, list)
        assert {m.id for m in res} == {m1.id}

    async def test_join_server_not_found_without_server(self, member_service):
        with pytest.raises(NotFoundException):
            await member_service.join_server(uuid.uuid4(), uuid.uuid4(), "User")

    async def test_join_server_not_found_when_server_private(self, member_service, factory):
        server = await factory.create_server(public=False)
        with pytest.raises(NotFoundException):
            await member_service.join_server(server.id, uuid.uuid4(), "User")

    async def test_join_server_not_found_when_banned(self, member_service, factory, helpers):
        server = await factory.create_server(public=True)
        with pytest.raises(NotFoundException):
            await member_service.join_server(
                server.id,
                uuid.uuid4(),
                "User",
                restriction_mask=helpers.restr_mask(RESTRICTION.SERVER_BAN),
            )

    async def test_join_server_returns_existing_member_and_reactivates(self, member_service, factory):
        server = await factory.create_server(public=True)
        user_id = uuid.uuid4()
        member = await factory.create_member(server.id, user_id=user_id, nickname="User")
        await member_service.member_repo.deactivate(member)

        joined = await member_service.join_server(server.id, user_id, "User")
        assert joined.id == member.id
        assert joined.active is True

    async def test_join_server_success_new_member(self, member_service, factory):
        server = await factory.create_server(public=True)
        user_id = uuid.uuid4()

        joined = await member_service.join_server(server.id, user_id, "NewUser")
        assert joined is not None
        assert joined.user_id == user_id
        assert joined.nickname == "NewUser"
        assert joined.active is True

    async def test_create_virtual_forbidden_without_permission(self, member_service, factory):
        server = await factory.create_server()
        with pytest.raises(ForbiddenException):
            await member_service.create_virtual(server.id, nickname="VirtualUser", permission_mask=0)

    async def test_create_virtual_not_found_without_server(self, member_service, helpers):
        with pytest.raises(NotFoundException):
            await member_service.create_virtual(
                uuid.uuid4(),
                nickname="VirtualUser",
                permission_mask=helpers.perm_mask(PERMISSION.CREATE_VIRTUAL),
            )

    async def test_create_virtual_success(self, member_service, factory, helpers):
        server = await factory.create_server()
        member = await member_service.create_virtual(
            server.id,
            nickname="VirtualUser",
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_VIRTUAL),
        )
        assert member is not None
        assert member.user_id is None
        assert member.nickname == "VirtualUser"

    async def test_get_member_and_not_found(self, member_service, factory):
        server = await factory.create_server()
        member = await factory.create_member(server.id, nickname="User")

        fetched = await member_service.get_member(member.id)
        assert fetched.id == member.id

        with pytest.raises(NotFoundException):
            await member_service.get_member(uuid.uuid4())

    async def test_update_member_name_and_role(self, member_service, factory, helpers):
        server = await factory.create_server()
        issuer_role = await factory.create_server_role(server.id, name="Admin", position=10)
        target_role = await factory.create_server_role(server.id, name="Mod", position=5)

        issuer = await factory.create_member(server.id, role_id=issuer_role.id, nickname="Issuer")
        member = await factory.create_member(server.id, nickname="Old")

        updated = await member_service.update_member(
            server_id=server.id,
            issuer_id=issuer.id,
            member_id=member.id,
            name="New",
            server_role_id=target_role.id,
            permission_mask=helpers.perm_mask(
                PERMISSION.EDIT_NAME,
                PERMISSION.EDIT_ROLES,
            ),
            restriction_mask=helpers.restr_mask(),
        )
        assert updated.nickname == "New"
        assert updated.server_role_id == target_role.id

    async def test_update_member_not_found(self, member_service, helpers):
        with pytest.raises(NotFoundException):
            await member_service.update_member(
                server_id=uuid.uuid4(),
                issuer_id=uuid.uuid4(),
                member_id=uuid.uuid4(),
                name="New",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_NAME),
                restriction_mask=helpers.restr_mask(),
            )

    async def test_update_member_role_not_found(self, member_service, factory, helpers):
        server = await factory.create_server()
        issuer_role = await factory.create_server_role(server.id, name="Admin", position=10)
        issuer = await factory.create_member(server.id, role_id=issuer_role.id, nickname="Issuer")
        member = await factory.create_member(server.id, nickname="Target")

        with pytest.raises(NotFoundException):
            await member_service.update_member(
                server_id=server.id,
                issuer_id=issuer.id,
                member_id=member.id,
                server_role_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLES),
                restriction_mask=helpers.restr_mask(),
            )

    async def test_update_member_forbidden_name(self, member_service, factory, helpers):
        server = await factory.create_server()
        issuer = await factory.create_member(server.id, nickname="Issuer")
        member = await factory.create_member(server.id, nickname="Old")

        with pytest.raises(ForbiddenException):
            await member_service.update_member(
                server_id=server.id,
                issuer_id=issuer.id,
                member_id=member.id,
                name="New",
                permission_mask=helpers.perm_mask(),
                restriction_mask=helpers.restr_mask(),
            )

    async def test_update_member_self_name(self, member_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id, nickname="Old")

        updated = await member_service.update_member(
            server_id=server.id,
            issuer_id=member.id,
            member_id=member.id,
            name="New",
            permission_mask=helpers.perm_mask(),
            restriction_mask=helpers.restr_mask(),
        )
        assert updated.nickname == "New"

    async def test_update_member_forbidden_self_name(self, member_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id, nickname="Old")

        with pytest.raises(ForbiddenException):
            await member_service.update_member(
                server_id=server.id,
                issuer_id=member.id,
                member_id=member.id,
                name="New",
                permission_mask=helpers.perm_mask(),
                restriction_mask=helpers.restr_mask(RESTRICTION.SELF_EDIT_NAME),
            )

    async def test_update_member_forbidden_assign_higher_role(self, member_service, factory, helpers):
        server = await factory.create_server()
        issuer_role = await factory.create_server_role(server.id, name="Mod", position=5)
        higher_role = await factory.create_server_role(server.id, name="Admin", position=10)

        issuer = await factory.create_member(server.id, role_id=issuer_role.id, nickname="Issuer")
        member = await factory.create_member(server.id, nickname="Target")

        with pytest.raises(ForbiddenException):
            await member_service.update_member(
                server_id=server.id,
                issuer_id=issuer.id,
                member_id=member.id,
                server_role_id=higher_role.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLES),
                restriction_mask=helpers.restr_mask(),
            )

    async def test_kick_member_flow(self, member_service, factory, helpers):
        server = await factory.create_server()
        issuer = await factory.create_member(server.id, nickname="Issuer")
        member = await factory.create_member(server.id, nickname="Kick")

        with pytest.raises(ForbiddenException):
            await member_service.kick_member(issuer.id, server.id, member.id, permission_mask=0)

        with pytest.raises(ForbiddenException):
            await member_service.kick_member(
                issuer.id,
                server.id,
                issuer.id,
                permission_mask=helpers.perm_mask(PERMISSION.KICK_MEMBERS)
            )

        with pytest.raises(NotFoundException):
            await member_service.kick_member(
                issuer.id,
                server.id,
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.KICK_MEMBERS)
            )

        await member_service.kick_member(
            issuer.id,
            server.id,
            member.id,
            permission_mask=helpers.perm_mask(PERMISSION.KICK_MEMBERS)
        )
        reloaded = await member_service.member_repo.get_by_id(member.id)
        assert reloaded is not None and reloaded.active is False

    async def test_migrate_member_forbidden(self, member_service, factory, helpers):
        server = await factory.create_server()
        current = await factory.create_member(server.id, nickname="Current")
        target = await factory.create_member(server.id, user_id=None, nickname="Target")

        with pytest.raises(ForbiddenException):
            await member_service.migrate_member(
                server.id,
                current.id,
                target.id,
                permission_mask=helpers.perm_mask()
            )

    async def test_migrate_member_success(self, member_service, factory, helpers):
        server = await factory.create_server()
        user_id = uuid.uuid4()
        current = await factory.create_member(server.id, user_id=user_id, nickname="Current")
        target = await factory.create_member(server.id, user_id=None, nickname="Target")

        migrated = await member_service.migrate_member(
            server.id,
            current.id,
            target.id,
            permission_mask=helpers.perm_mask(PERMISSION.MIGRATE_MEMBERS),
        )
        assert migrated.id == target.id
        assert migrated.user_id == user_id

        reloaded_current = await member_service.member_repo.get_by_id(current.id)
        assert reloaded_current.user_id is None
        assert reloaded_current.active is False

    async def test_migrate_member_raises_when_current_has_no_user(self, member_service, factory, helpers):
        server = await factory.create_server()
        target = await factory.create_member(server.id, user_id=None, nickname="Target")
        no_user_current = await factory.create_member(server.id, user_id=None, nickname="NoUser")

        with pytest.raises(MigrationException):
            await member_service.migrate_member(
                server.id,
                no_user_current.id,
                target.id,
                permission_mask=helpers.perm_mask(PERMISSION.MIGRATE_MEMBERS),
            )

    async def test_migrate_member_raises_when_target_has_user(self, member_service, factory, helpers):
        server = await factory.create_server()
        user_id = uuid.uuid4()
        current = await factory.create_member(server.id, user_id=user_id, nickname="Current")
        target_with_user = await factory.create_member(server.id, user_id=uuid.uuid4(), nickname="TargetWithUser")

        with pytest.raises(MigrationException):
            await member_service.migrate_member(
                server.id,
                current.id,
                target_with_user.id,
                permission_mask=helpers.perm_mask(PERMISSION.MIGRATE_MEMBERS),
            )

    async def test_migrate_member_not_found(self, member_service, factory, helpers):
        server = await factory.create_server()
        user_id = uuid.uuid4()
        current = await factory.create_member(server.id, user_id=user_id, nickname="Current")

        with pytest.raises(NotFoundException):
            await member_service.migrate_member(
                server.id,
                current.id,
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.MIGRATE_MEMBERS),
            )
