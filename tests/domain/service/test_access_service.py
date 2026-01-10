import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, UTC

from src.domain.service import AccessControlService
from src.domain.exceptions import NotFoundException, ForbiddenException
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre.repo import (
    MemberRepository,
    MemberRestrictionRepository,
    ServerRepository,
    RestrictionRepository,
    PermissionRepository,
)


@pytest_asyncio.fixture(loop_scope="session")
async def access_control_service(async_session):
    return AccessControlService(
        MemberRepository(async_session),
        MemberRestrictionRepository(async_session),
        ServerRepository(async_session),
        RestrictionRepository(async_session),
        PermissionRepository(async_session),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestAccessControlService:

    async def test_get_restrictions_empty(self, access_control_service, factory):
        server = await factory.create_server()
        user_id = uuid.uuid4()
        await factory.create_member(server.id, user_id=user_id, nickname="Restricted")
        await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        assert await access_control_service.get_restrictions(server.id, user_id) == []

    async def test_add_restriction(self, access_control_service, factory, helpers):
        server = await factory.create_server()
        role_issuer = await factory.create_server_role(server.id, name="Admin", position=100)
        role_member = await factory.create_server_role(server.id, name="User", position=1)

        member = await factory.create_member(server.id, role_id=role_member.id, nickname="Restricted")
        issuer = await factory.create_member(server.id, role_id=role_issuer.id, nickname="Issuer")
        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        # Fail case: Empty permissions
        with pytest.raises(ForbiddenException):
            await access_control_service.add_restriction(
                member_id=member.id,
                issuer_id=issuer.id,
                server_id=server.id,
                permission_mask=helpers.perm_mask(),
                reason="Bad behavior",
                expiration_date=datetime.now(UTC) + timedelta(days=1),
                restriction_id=restriction.id
            )

        # Success case
        mr = await access_control_service.add_restriction(
            member_id=member.id,
            issuer_id=issuer.id,
            server_id=server.id,
            permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
            reason="Bad behavior",
            expiration_date=datetime.now(UTC) + timedelta(days=1),
            restriction_id=restriction.id
        )
        assert mr is not None and mr.member_id == member.id
        assert len(await access_control_service.get_restrictions(server.id, member.user_id)) == 1

    async def test_add_restriction_hierarchy_fail(self, access_control_service, factory, helpers):
        server = await factory.create_server()
        role_1 = await factory.create_server_role(server.id, name="Role1", position=10)
        role_2 = await factory.create_server_role(server.id, name="Role2", position=10)

        member = await factory.create_member(server.id, role_id=role_1.id, nickname="Target")
        issuer = await factory.create_member(server.id, role_id=role_2.id, nickname="Issuer")
        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        with pytest.raises(ForbiddenException):
            await access_control_service.add_restriction(
                member_id=member.id,
                issuer_id=issuer.id,
                server_id=server.id,
                permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
                reason="Bad behavior",
                expiration_date=datetime.now(UTC) + timedelta(days=1),
                restriction_id=restriction.id
            )

    async def test_remove_restriction(self, access_control_service, factory, helpers):
        server = await factory.create_server()
        role_issuer = await factory.create_server_role(server.id, name="Admin", position=100)
        member = await factory.create_member(server.id, nickname="Restricted")
        issuer = await factory.create_member(server.id, role_id=role_issuer.id, nickname="Issuer")
        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        mr = await access_control_service.add_restriction(
            member_id=member.id,
            issuer_id=issuer.id,
            server_id=server.id,
            permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
            reason="Bad behavior",
            expiration_date=datetime.now(UTC) + timedelta(days=1),
            restriction_id=restriction.id
        )

        # Fail: Wrong ID
        with pytest.raises(NotFoundException):
            await access_control_service.remove_restriction(
                member_id=uuid.uuid4(),
                issuer_id=issuer.id,
                server_id=server.id,
                member_restriction_id=mr.id,
                permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
            )

        # Fail: No permission
        with pytest.raises(ForbiddenException):
            await access_control_service.remove_restriction(
                member_id=member.id,
                issuer_id=issuer.id,
                server_id=server.id,
                member_restriction_id=mr.id,
                permission_mask=helpers.perm_mask(),
            )

        # Success
        await access_control_service.remove_restriction(
            member_id=member.id,
            issuer_id=issuer.id,
            server_id=server.id,
            member_restriction_id=mr.id,
            permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
        )
        assert await access_control_service.get_restrictions(server.id, member.user_id) == []

    async def test_remove_restriction_hierarchy_fail(self, access_control_service, factory, helpers):
        server = await factory.create_server()
        role_1 = await factory.create_server_role(server.id, name="Role1", position=10)
        role_2 = await factory.create_server_role(server.id, name="Role2", position=10)

        member = await factory.create_member(server.id, role_id=role_1.id, nickname="Target")
        issuer = await factory.create_member(server.id, role_id=role_2.id, nickname="Issuer")
        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        mr = await access_control_service.member_restriction_repo.create(
            member_id=member.id,
            restriction_id=restriction.id,
            reason="Test",
            expiration_date=datetime.now(UTC) + timedelta(days=1),
            creator_id=issuer.id
        )

        with pytest.raises(ForbiddenException):
            await access_control_service.remove_restriction(
                member_id=member.id,
                issuer_id=issuer.id,
                server_id=server.id,
                member_restriction_id=mr.id,
                permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
            )

    @pytest.mark.parametrize("role_name, role_perms, expected_perms", [
        ("User", [PERMISSION.KICK_MEMBERS], [PERMISSION.KICK_MEMBERS]),
        ("Admin", [PERMISSION.ADMINISTRATOR], [PERMISSION.ADMINISTRATOR, PERMISSION.KICK_MEMBERS]),
    ])
    async def test_get_permissions(self, access_control_service, factory, role_name, role_perms, expected_perms):
        server = await factory.create_server()
        role = await factory.create_server_role(server.id, name=role_name, position=50)

        for p_code in PERMISSION:
            perm = await factory.create_permission(code=p_code)
            if p_code in role_perms:
                await access_control_service.permission_repo.assign_to_role(perm.id, role.id)

        member = await factory.create_member(server.id, role_id=role.id, nickname=role_name)

        perms = await access_control_service.get_permissions(server.id, member.user_id)

        for p in expected_perms:
            assert p in [perm.code for perm in perms]

        if PERMISSION.ADMINISTRATOR in role_perms:
            assert len(perms) == len(PERMISSION)

    async def test_get_permissions_owner(self, access_control_service, factory):
        owner_id = uuid.uuid4()
        server = await factory.create_server(owner_id=owner_id)

        for p_code in PERMISSION:
            await factory.create_permission(code=p_code)

        # Role with no permissions
        role = await factory.create_server_role(server.id, name="Empty", position=50)
        member = await factory.create_member(server.id, user_id=owner_id, role_id=role.id, nickname="Owner")

        perms = await access_control_service.get_permissions(server.id, member.user_id)

        # Owner gets all permissions regardless of role
        assert len(perms) == len(PERMISSION)
        assert PERMISSION.ADMINISTRATOR in [perm.code for perm in perms]
        assert PERMISSION.RESTRICT_SERVER_BAN in [perm.code for perm in perms]

    async def test_get_permission_mask_admin_override(self, access_control_service, factory):
        server = await factory.create_server()

        # Normal role
        role = await factory.create_server_role(server.id, name="Role", position=1)
        perm = await factory.create_permission(PERMISSION.KICK_MEMBERS)
        await access_control_service.permission_repo.assign_to_role(perm.id, role.id)

        member = await factory.create_member(server.id, role_id=role.id, nickname="User")

        mask = await access_control_service.get_permission_mask(server.id, member.user_id)
        assert PERMISSION.check_permission(mask, PERMISSION.KICK_MEMBERS)
        assert not PERMISSION.check_permission(mask, PERMISSION.RESTRICT_SERVER_BAN)

        # Admin role
        admin_role = await factory.create_server_role(server.id, name="Admin", position=10)
        admin_perm = await factory.create_permission(PERMISSION.ADMINISTRATOR)
        await access_control_service.permission_repo.assign_to_role(admin_perm.id, admin_role.id)

        admin = await factory.create_member(server.id, role_id=admin_role.id, nickname="Admin")

        admin_mask = await access_control_service.get_permission_mask(server.id, admin.user_id)
        assert PERMISSION.check_permission(admin_mask, PERMISSION.RESTRICT_SERVER_BAN)
        assert PERMISSION.check_permission(admin_mask, PERMISSION.KICK_MEMBERS)

    async def test_get_permission_mask_owner_override(self, access_control_service, factory):
        owner_id = uuid.uuid4()
        server = await factory.create_server(owner_id=owner_id)

        # Role with strictly limited permissions
        role = await factory.create_server_role(server.id, name="Limited", position=1)
        # Assign one random permission just to ensure it's not empty by default logic but overridden
        perm = await factory.create_permission(PERMISSION.EDIT_INVITES)
        await access_control_service.permission_repo.assign_to_role(perm.id, role.id)

        member = await factory.create_member(server.id, user_id=owner_id, role_id=role.id, nickname="Owner")

        mask = await access_control_service.get_permission_mask(server.id, member.user_id)

        # Should be full mask
        assert mask == (1 << len(PERMISSION)) - 1
        assert PERMISSION.check_permission(mask, PERMISSION.ADMINISTRATOR)
        assert PERMISSION.check_permission(mask, PERMISSION.RESTRICT_SERVER_BAN)

    async def test_get_restriction_mask_success(self, access_control_service, factory):
        server = await factory.create_server()
        member = await factory.create_member(server.id, nickname="Restricted")
        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        await access_control_service.member_restriction_repo.create(
            member_id=member.id,
            restriction_id=restriction.id,
            reason="Test",
            expiration_date=datetime.now(UTC) + timedelta(days=1),
            creator_id=member.id
        )

        mask = await access_control_service.get_restriction_mask(server.id, member.user_id)
        assert RESTRICTION.check_restriction(mask, RESTRICTION.SERVER_BAN)

    async def test_add_restriction_not_found(self, access_control_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id, nickname="User")

        with pytest.raises(NotFoundException):
            await access_control_service.add_restriction(
                member_id=member.id,
                issuer_id=member.id,
                server_id=server.id,
                permission_mask=helpers.perm_mask(),
                reason="Reason",
                expiration_date=datetime.now(UTC) + timedelta(days=1),
                restriction_id=uuid.uuid4()
            )

    async def test_add_restriction_owner_can_restrict_anyone(self, access_control_service, factory, helpers):
        owner_id = uuid.uuid4()
        server = await factory.create_server(owner_id=owner_id)

        # Owner role (позиция не имеет значения)
        owner_role = await factory.create_server_role(server.id, name="OwnerRole", position=0)
        user_role = await factory.create_server_role(server.id, name="User", position=100)

        owner = await factory.create_member(
            server.id, user_id=owner_id, role_id=owner_role.id, nickname="Owner"
        )
        target = await factory.create_member(
            server.id, role_id=user_role.id, nickname="Target"
        )

        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        mr = await access_control_service.add_restriction(
            member_id=target.id,
            issuer_id=owner.id,
            server_id=server.id,
            permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
            reason="Owner restriction",
            expiration_date=datetime.now(UTC) + timedelta(days=1),
            restriction_id=restriction.id,
        )

        assert mr.member_id == target.id

    async def test_add_restriction_target_is_owner_forbidden(self, access_control_service, factory, helpers):
        owner_id = uuid.uuid4()
        server = await factory.create_server(owner_id=owner_id)

        admin_role = await factory.create_server_role(server.id, name="Admin", position=100)
        owner_role = await factory.create_server_role(server.id, name="OwnerRole", position=0)

        owner = await factory.create_member(
            server.id, user_id=owner_id, role_id=owner_role.id, nickname="Owner"
        )
        admin = await factory.create_member(
            server.id, role_id=admin_role.id, nickname="Admin"
        )

        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        with pytest.raises(ForbiddenException, match="Unable to add restriction"):
            await access_control_service.add_restriction(
                member_id=owner.id,
                issuer_id=admin.id,
                server_id=server.id,
                permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
                reason="Try restrict owner",
                expiration_date=datetime.now(UTC) + timedelta(days=1),
                restriction_id=restriction.id,
            )

    async def test_remove_restriction_owner_can_remove_any(self, access_control_service, factory, helpers):
        owner_id = uuid.uuid4()
        server = await factory.create_server(owner_id=owner_id)

        owner_role = await factory.create_server_role(server.id, name="OwnerRole", position=0)
        user_role = await factory.create_server_role(server.id, name="User", position=1)

        owner = await factory.create_member(
            server.id, user_id=owner_id, role_id=owner_role.id, nickname="Owner"
        )
        user = await factory.create_member(
            server.id, role_id=user_role.id, nickname="User"
        )

        restriction = await factory.create_restriction(code=RESTRICTION.SERVER_BAN)

        mr = await access_control_service.member_restriction_repo.create(
            member_id=user.id,
            restriction_id=restriction.id,
            reason="Test",
            expiration_date=datetime.now(UTC) + timedelta(days=1),
            creator_id=owner.id,
        )

        await access_control_service.remove_restriction(
            member_id=user.id,
            issuer_id=owner.id,
            server_id=server.id,
            member_restriction_id=mr.id,
            permission_mask=helpers.perm_mask(PERMISSION.RESTRICT_SERVER_BAN),
        )

        restrictions = await access_control_service.get_restrictions(server.id, user.user_id)
        assert restrictions == []
