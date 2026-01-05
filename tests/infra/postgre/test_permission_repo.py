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

    async def test_bulk_assign_foreign_key_error(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)

        p1 = await repo.create("p.valid")
        bad_id = uuid.uuid4()

        with pytest.raises(IntegrityForeignException):
            await repo.bulk_assign_to_role([p1.id, bad_id], role.id)

    async def test_get_by_code_bulk(self, async_session):
        repo = PermissionRepository(async_session)
        codes = ["perm.bulk.1", "perm.bulk.2", "perm.bulk.3"]
        for c in codes:
            await repo.create(c)

        found = await repo.get_by_code_bulk(["perm.bulk.1", "perm.bulk.3", "perm.missing"])
        assert len(found) == 2
        found_codes = {p.code for p in found}
        assert "perm.bulk.1" in found_codes
        assert "perm.bulk.3" in found_codes

    async def test_bulk_remove_from_role(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)
        perms = [await repo.create(f"perm.rem.{i}") for i in range(3)]
        perm_ids = [p.id for p in perms if p]

        await repo.bulk_assign_to_role(perm_ids, role.id)

        count = await repo.bulk_remove_from_role(perm_ids[:2], role.id)
        assert count == 2

        remaining = await repo.list_for_role(role.id)
        assert len(remaining) == 1
        assert remaining[0].id == perm_ids[2]

    async def test_bulk_set_for_role(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)

        p1 = await repo.create("p1")
        p2 = await repo.create("p2")
        p3 = await repo.create("p3")

        await repo.assign_to_role(p1.id, role.id)

        # Set state: p2, p3 (should remove p1, add p2, p3)
        await repo.bulk_set_for_role([p2.id, p3.id], role.id)

        current = await repo.list_for_role(role.id)
        current_ids = {p.id for p in current}
        assert p1.id not in current_ids
        assert p2.id in current_ids
        assert p3.id in current_ids

        # Set state: empty (should remove all)
        await repo.bulk_set_for_role([], role.id)
        current = await repo.list_for_role(role.id)
        assert len(current) == 0

    async def test_list_for_role_empty_when_none_assigned(self, async_session, factory):
        repo = PermissionRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)
        listed = await repo.list_for_role(role.id)
        assert listed == []
