import uuid
import pytest
import pytest_asyncio

from src.domain.exceptions import ForbiddenException, NotFoundException
from src.domain.service.role import RoleService
from src.infra.postgre.repo import ServerRepository, ServerRoleRepository, MemberRepository, PermissionRepository
from src.infra.postgre.static import PERMISSION


@pytest_asyncio.fixture(loop_scope="session")
async def role_service(async_session):
    return RoleService(
        ServerRepository(async_session),
        ServerRoleRepository(async_session),
        MemberRepository(async_session),
        PermissionRepository(async_session)
    )


@pytest.mark.asyncio(loop_scope="session")
class TestRoleService:

    async def test_list_roles_server_not_found(self, role_service):
        with pytest.raises(NotFoundException):
            await role_service.list_roles(uuid.uuid4())

    async def test_list_roles_empty_list(self, role_service, factory):
        s = await factory.create_server()
        res = await role_service.list_roles(s.id)
        assert isinstance(res, list)
        assert res == []

    async def test_list_roles_returns_roles(self, role_service, factory):
        s = await factory.create_server()
        r1 = await factory.create_server_role(s.id, name="R1")
        r2 = await factory.create_server_role(s.id, name="R2")

        res = await role_service.list_roles(s.id)
        ids = {r.id for r in res}
        assert {r1.id, r2.id}.issubset(ids)

    async def test_create_role_forbidden_without_permission(self, role_service, factory):
        s = await factory.create_server()
        with pytest.raises(ForbiddenException):
            await role_service.create_role(s.id, "Role", permission_mask=0)

    async def test_create_role_success_default_position(self, role_service, factory, helpers):
        s = await factory.create_server()

        role = await role_service.create_role(
            s.id,
            "Role",
            position=None,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )

        assert role is not None
        assert role.name == "Role"
        assert role.position == 0
        listed = await role_service.role_repo.list_for_server(s.id)
        assert any(r.id == role.id for r in listed)

    async def test_create_role_success_with_position(self, role_service, factory, helpers):
        s = await factory.create_server()

        role = await role_service.create_role(
            s.id,
            "Role",
            position=5,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )

        assert role.position == 5

    async def test_create_role_server_not_found(self, role_service, helpers):
        with pytest.raises(NotFoundException):
            await role_service.create_role(
                uuid.uuid4(),
                "Role",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
            )

    async def test_update_role_forbidden_without_permission(self, role_service, factory):
        s = await factory.create_server()
        r = await factory.create_server_role(s.id)

        with pytest.raises(ForbiddenException):
            await role_service.update_role(r.id, name="New", permission_mask=0)

    async def test_update_role_not_found(self, role_service, helpers):
        with pytest.raises(NotFoundException):
            await role_service.update_role(
                uuid.uuid4(),
                name="New",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
            )

    async def test_update_role_updates_name_and_position(self, role_service, factory, helpers):
        s = await factory.create_server()
        r = await factory.create_server_role(s.id, name="Old", position=1)

        updated = await role_service.update_role(
            r.id,
            name="New",
            position=5,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )

        assert updated.name == "New"
        assert updated.position == 5

    async def test_delete_role_forbidden_without_permission(self, role_service, factory):
        s = await factory.create_server()
        r = await factory.create_server_role(s.id)

        with pytest.raises(ForbiddenException):
            await role_service.delete_role(r.id, permission_mask=0)

    async def test_delete_role_success(self, role_service, factory, helpers):
        s = await factory.create_server()
        r = await factory.create_server_role(s.id)

        await role_service.delete_role(
            r.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )

        assert await role_service.role_repo.get_by_id(r.id) is None

    async def test_delete_role_not_found(self, role_service, helpers):
        with pytest.raises(NotFoundException):
            await role_service.delete_role(
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
            )

    async def test_delete_role_assigned_to_member(self, role_service, factory, helpers):
        s = await factory.create_server()
        r = await factory.create_server_role(s.id)
        member = await factory.create_member(s.id, role_id=r.id)

        await role_service.delete_role(
            r.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ROLES),
        )
        assert await role_service.role_repo.get_by_id(r.id) is None

        updated_member = await role_service.member_repo.get_by_id(member.id)
        await role_service.member_repo.session.refresh(updated_member)
        assert updated_member is not None
        assert updated_member.server_role_id is None
