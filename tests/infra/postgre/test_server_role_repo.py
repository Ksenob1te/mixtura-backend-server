import uuid
import pytest

from src.infra.postgre.repo import ServerRoleRepository
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException


@pytest.mark.asyncio(loop_scope="session")
class TestServerRoleRepository:

    async def test_create_and_get_server_role(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()
        r = await repo.create(s.id, "RoleA", position=1)
        assert r is not None and r.name == "RoleA" and r.position == 1
        by_id = await repo.get_by_id(r.id)
        assert by_id is not None and by_id.id == r.id
        assert await repo.get_by_id(uuid.uuid4()) is None

    async def test_create_shifts_positions(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()

        # Create roles at specific positions
        r1 = await repo.create(s.id, "R1", 1)  # R1 at 1
        r2 = await repo.create(s.id, "R2", 2)  # R2 at 2 (1 < 2, so R1 stays)

        assert r1.position == 1
        assert r2.position == 2

        # Insert R_Mid at position 2. Should shift R2 to 3. R1 stays at 1.
        r_mid = await repo.create(s.id, "R_Mid", 2)
        assert r_mid.position == 2

        # Verify shifts
        r1_fresh = await repo.get_by_id(r1.id)
        r2_fresh = await repo.get_by_id(r2.id)

        assert r1_fresh and r1_fresh.position == 1
        assert r2_fresh and r2_fresh.position == 3

    async def test_create_server_role_unreal_server(self, async_session):
        repo = ServerRoleRepository(async_session)
        unreal_server_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(unreal_server_id, "RoleX", position=0)

    async def test_unique_name_per_server(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()
        _ = await repo.create(s.id, "Dup", 0)
        with pytest.raises(IntegrityUniqueException):
            await repo.create(s.id, "Dup", 1)

    async def test_list_for_server_sorted_by_position(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()
        r3 = await repo.create(s.id, "R3", 3)
        r1 = await repo.create(s.id, "R1", 1)
        r2 = await repo.create(s.id, "R2", 2)
        listed = await repo.list_for_server(s.id)
        # Order implies positions: R1(1), R2(2), R3(5 due to shifts)
        assert [r.name for r in listed] == ["R1", "R2", "R3"]

    async def test_set_name_and_position(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()
        r = await repo.create(s.id, "Orig", 5)
        assert r is not None
        r = await repo.set_name(r, "NewName")
        assert r.name == "NewName"
        r2 = await repo.set_name(r, "NewName")
        assert r2.id == r.id and r2.name == "NewName"
        r = await repo.set_position(r, -10)
        assert r.position == 0
        r = await repo.set_position(r, 7)
        assert r.position == 7

    async def test_set_position_shifts_others(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()

        # Initial: R1(1), R2(2), R3(3)
        r1 = await repo.create(s.id, "R1", 1)
        r2 = await repo.create(s.id, "R2", 2)
        r3 = await repo.create(s.id, "R3", 3)

        # Move R1 from 1 to 3.
        # Logic: R1 moves down (idx increases). Roles between (1, 3] should shift -1.
        # R2(2) -> 1, R3(3) -> 2. R1 -> 3.
        await repo.set_position(r1, 3)

        # Expire session to ensure we fetch fresh data from DB after raw SQL updates
        # async_session.refresh(r1)
        async_session.refresh(r2)
        async_session.refresh(r3)

        assert r1 and r1.position == 3
        assert r2 and r2.position == 1
        assert r3 and r3.position == 2

        # Move R1 from 3 back to 1.
        # Logic: R1 moves up (idx decreases). Roles between [1, 3) should shift +1.
        # R2(1) -> 2, R3(2) -> 3. R1 -> 1.
        await repo.set_position(r1, 1)

        # async_session.refresh(r1)
        async_session.refresh(r2)
        async_session.refresh(r3)

        assert r1 and r1.position == 1
        assert r2 and r2.position == 2
        assert r3 and r3.position == 3

    async def test_delete_server_role(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()
        r = await repo.create(s.id, "Del", 0)
        assert r is not None
        ok = await repo.delete(r.id)
        assert ok is True
        not_ok = await repo.delete(r.id)
        assert not_ok is False

    async def test_list_for_server_empty(self, async_session, factory):
        repo = ServerRoleRepository(async_session)
        s = await factory.create_server()
        listed = await repo.list_for_server(s.id)
        assert listed == []
