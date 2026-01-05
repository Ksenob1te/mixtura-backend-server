import uuid
import pytest
from sqlalchemy import select
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException

from src.infra.postgre.models import ServerRolePermission
from src.infra.postgre.repo import PermissionRepository


@pytest.mark.asyncio(loop_scope="session")
class TestPermissionRepository:

    async def test_create_and_get_permission(self, async_session):
        repo = PermissionRepository(async_session)
        p = await repo.create("perm.view")
        assert p is not None
        assert p.code == "perm.view"
        by_id = await repo.get_by_id(p.id)
        assert by_id is not None and by_id.id == p.id
        by_code = await repo.get_by_code("perm.view")
        assert by_code is not None and by_code.id == p.id
        assert await repo.get_by_code("missing") is None

    async def test_unique_code_name_enforced(self, async_session):
        repo = PermissionRepository(async_session)
        await repo.create("perm.unique")
        with pytest.raises(IntegrityUniqueException):
            await repo.create("perm.unique")

    async def test_list_all_permissions(self, async_session):
        repo = PermissionRepository(async_session)
        codes = [f"perm.list.{i}" for i in range(3)]
        for c in codes:
            await repo.create(c)
        all_perms = await repo.list_all()
        present_codes = {p.code for p in all_perms}
        for c in codes:
            assert c in present_codes

    async def test_delete_permission(self, async_session):
        repo = PermissionRepository(async_session)
        p = await repo.create("perm.delete")
        assert p is not None
        ok = await repo.delete(p.id)
        assert ok is True
        not_ok = await repo.delete(p.id)
        assert not_ok is False

    async def test_assign_and_list_for_role(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id, name="R1")
        perms = [await repo.create(f"perm.role.{i}") for i in range(2)]
        for perm in perms:
            assert perm is not None
            await repo.assign_to_role(perm.id, role.id)

        stmt = select(ServerRolePermission).where(ServerRolePermission.server_role_id == role.id)
        res = await async_session.execute(stmt)
        assert len(res.scalars().all()) == 2

    async def test_assign_to_role_twice(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id, name="R2")
        perm = await repo.create("perm.role.twice")
        assert perm is not None
        await repo.assign_to_role(perm.id, role.id)
        # Assigning again should not raise an error or create duplicate entries
        await repo.assign_to_role(perm.id, role.id)
        listed = await repo.list_for_role(role.id)
        assert len(listed) == 1
        assert listed[0].id == perm.id

    async def test_assign_to_role_non_existing_role(self, async_session):
        repo = PermissionRepository(async_session)
        perm = await repo.create("perm.nonexist.role")
        assert perm is not None
        non_existing_role_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.assign_to_role(perm.id, non_existing_role_id)

    async def test_remove_from_role(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)
        perm = await repo.create("perm.remove")
        assert perm is not None
        await repo.assign_to_role(perm.id, role.id)
        removed = await repo.remove_from_role(perm.id, role.id)
        assert removed is True
        removed_again = await repo.remove_from_role(perm.id, role.id)
        assert removed_again is False

    async def test_bulk_assign_to_role(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)
        perms = [await repo.create(f"perm.bulk.{i}") for i in range(3)]
        for p in perms:
            assert p is not None
        await repo.bulk_assign_to_role([p.id for p in perms if p is not None], role.id)
        listed = await repo.list_for_role(role.id)
        assert {p.id for p in listed} == {p.id for p in perms if p is not None}

    async def test_list_for_role_empty_when_none_assigned(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)
        listed = await repo.list_for_role(role.id)
        assert listed == []

