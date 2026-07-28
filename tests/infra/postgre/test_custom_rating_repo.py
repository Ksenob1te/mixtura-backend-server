import uuid
import pytest
from src.infra.postgre.models import Custom
from src.infra.postgre.repo import CustomRatingRepository

from src.core.models.custom_rating import CustomRatingCreate, CustomRatingUpdate
from src.infra.postgre import IntegrityForeignException, IntegrityUniqueException


@pytest.mark.asyncio(loop_scope="session")
class TestCustomRatingRepository:

    async def test_create_get_and_list(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        rs = await factory.create_role_set()
        r = await factory.create_game_role(rs.id)

        cr = await repo.create(c.id, r.id, 12)
        assert cr is not None and cr.rating == 12

        by_id = await repo.get(cr.id)
        assert by_id is not None and by_id.id == cr.id

        by_pair = await repo.get_by_custom_role(c.id, r.id)
        assert by_pair is not None and by_pair.id == cr.id

        list_c = await repo.list_for_custom(c.id)
        assert cr.id in {x.id for x in list_c}

    async def test_create_unreal_custom(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        rs = await factory.create_role_set()
        r = await factory.create_game_role(rs.id)

        unreal_custom_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(unreal_custom_id, r.id, 5)

    async def test_create_unreal_role(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        unreal_role_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(c.id, unreal_role_id, 5)

    async def test_unique_pair_constraint(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        rs = await factory.create_role_set()
        r = await factory.create_game_role(rs.id, name="PairRole")

        await repo.create(c.id, r.id, 1)
        with pytest.raises(IntegrityUniqueException):
            await repo.create(c.id, r.id, 2)

    async def test_set_rating_and_delete(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        rs = await factory.create_role_set()
        r = await factory.create_game_role(rs.id)

        cr = await repo.create(c.id, r.id, 5)
        assert cr is not None

        cr = await repo.set_rating(cr, 7)
        assert cr.rating == 7

        ok = await repo.delete(cr.id)
        assert ok is True
        not_ok = await repo.delete(cr.id)
        assert not_ok is False

    async def test_delete_by_pair(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        rs = await factory.create_role_set()
        r = await factory.create_game_role(rs.id)

        cr = await repo.create(c.id, r.id, 3)
        assert cr is not None

        ok = await repo.delete_by_custom_rating(c.id, r.id)
        assert ok is True
        not_ok = await repo.delete_by_custom_rating(c.id, r.id)
        assert not_ok is False

