import uuid
import pytest
from src.infra.postgre import IntegrityForeignException

from src.infra.postgre.repo import CustomRepository


@pytest.mark.asyncio(loop_scope="session")
class TestCustomRepository:

    async def test_create_and_get_custom(self, async_session, factory):
        repo = CustomRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = await repo.create(member_id=m.id, creator_id=m.id)
        assert c is not None
        assert c.member_id == m.id
        assert c.creator_id == m.id
        by_id = await repo.get_by_id(c.id)
        assert by_id is not None and by_id.id == c.id
        assert await repo.get_by_id(uuid.uuid4()) is None

    async def test_create_custom_unreal_member(self, async_session):
        repo = CustomRepository(async_session)
        unreal_member_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(member_id=unreal_member_id)

    async def test_create_custom_unreal_issuer(self, async_session, factory):
        repo = CustomRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)

        unreal_member_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(member_id=m.id, creator_id=unreal_member_id)

    async def test_list_for_member_empty_and_then_populated(self, async_session, factory):
        repo = CustomRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        assert await repo.list_for_member(m.id) == []
        c1 = await repo.create(m.id)
        c2 = await repo.create(m.id, creator_id=m.id)
        listed = await repo.list_for_member(m.id)
        ids = {x.id for x in listed}
        assert c1 is not None and c2 is not None
        assert ids == {c1.id, c2.id}

    async def test_set_creator_and_unassign(self, async_session, factory):
        repo = CustomRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        creator = await factory.create_member(s.id)
        c = await repo.create(m.id)
        assert c is not None and c.creator_id is None
        c = await repo.set_creator(c, creator.id)
        assert c.creator_id == creator.id
        c2 = await repo.set_creator(c, creator.id)
        assert c2.id == c.id and c2.creator_id == creator.id

    async def test_delete_custom(self, async_session, factory):
        repo = CustomRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = await repo.create(m.id)
        assert c is not None
        ok = await repo.delete(c.id)
        assert ok is True
        not_ok = await repo.delete(c.id)
        assert not_ok is False

