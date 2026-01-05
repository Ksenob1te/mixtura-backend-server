import uuid
import pytest
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException

from src.infra.postgre.repo import InviteRepository


@pytest.mark.asyncio(loop_scope="session")
class TestInviteRepository:

    async def test_create_and_get_invite(self, async_session, factory):
        repo = InviteRepository(async_session)
        s = await factory.create_server()
        inviter = await factory.create_member(s.id)
        inv = await repo.create(server_id=s.id, use_limit=5, inviter_id=inviter.id)
        assert inv is not None
        by_id = await repo.get_by_id(inv.id)
        assert by_id is not None and by_id.id == inv.id
        by_key = await repo.get_by_key(inv.key)
        assert by_key is not None and by_key.id == inv.id
        assert await repo.get_by_key("missing-key") is None
        assert await repo.get_by_id(uuid.uuid4()) is None

    async def test_create_invite_unreal_server(self, async_session):
        repo = InviteRepository(async_session)
        unreal_server_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(server_id=unreal_server_id, use_limit=5)

    async def test_create_with_custom_key_and_uniqueness(self, async_session, factory):
        repo = InviteRepository(async_session)
        s = await factory.create_server()
        inv1 = await repo.create(server_id=s.id, use_limit=1, key="CUSTOMKEY")
        assert inv1 is not None and inv1.key == "CUSTOMKEY"
        with pytest.raises(IntegrityUniqueException):
            await repo.create(server_id=s.id, use_limit=2, key="CUSTOMKEY")

    async def test_list_for_server(self, async_session, factory):
        repo = InviteRepository(async_session)
        s = await factory.create_server()
        invites = [await repo.create(server_id=s.id, use_limit=i + 1) for i in range(3)]
        listed = await repo.list_for_server(s.id)
        assert {i.id for i in listed} == {i.id for i in invites if i is not None}

    async def test_delete_invite(self, async_session, factory):
        repo = InviteRepository(async_session)
        s = await factory.create_server()
        inv = await repo.create(server_id=s.id, use_limit=10)
        assert inv is not None
        ok = await repo.delete(inv.id)
        assert ok is True
        not_ok = await repo.delete(inv.id)
        assert not_ok is False

    async def test_generate_unique_keys(self, async_session, factory):
        repo = InviteRepository(async_session)
        s = await factory.create_server()
        keys = set()
        for _ in range(1000):
            inv = await repo.create(server_id=s.id, use_limit=1)
            assert inv is not None
            assert inv.key not in keys
            keys.add(inv.key)

    async def test_set_use_limit_and_decrement(self, async_session, factory):
        repo = InviteRepository(async_session)
        s = await factory.create_server()
        inv = await repo.create(server_id=s.id, use_limit=3)
        assert inv is not None and inv.use_limit == 3
        inv = await repo.decrement_use_limit(inv)
        assert inv.use_limit == 2

