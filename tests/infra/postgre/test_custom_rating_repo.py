import uuid

import pytest

from src.core.models.custom_rating import CustomRatingCreate, CustomRatingUpdate
from src.infra.postgre import IntegrityForeignException, IntegrityUniqueException
from src.infra.postgre.models import Custom
from src.infra.postgre.repo import CustomRatingRepository


async def _create_game(factory, session, **kwargs):
    game = await factory.create_game(**kwargs)
    await session.refresh(game, attribute_names=["role_set", "rating_set"])
    return game


@pytest.mark.asyncio(loop_scope="session")
class TestCustomRatingRepository:

    async def test_create_get_and_list(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        game = await _create_game(factory, async_session)
        r = await factory.create_game_role(game.role_set.id)

        cr = await repo.create(CustomRatingCreate(custom_id=c.id, game_role_id=r.id, rating=12))
        assert cr is not None and cr.rating == 12

        by_id = await repo.get(cr.id)
        assert by_id is not None and by_id.id == cr.id

        by_pair = await repo.get_by_custom_role(c.id, r.id)
        assert by_pair is not None and by_pair.id == cr.id

        list_c = await repo.list_for_custom(c.id)
        assert cr.id in {x.id for x in list_c}

    async def test_create_unreal_custom(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        game = await _create_game(factory, async_session)
        r = await factory.create_game_role(game.role_set.id)

        unreal_custom_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(CustomRatingCreate(custom_id=unreal_custom_id, game_role_id=r.id, rating=5))

    async def test_create_unreal_role(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        unreal_role_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(CustomRatingCreate(custom_id=c.id, game_role_id=unreal_role_id, rating=5))

    async def test_unique_pair_constraint(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        game = await _create_game(factory, async_session)
        r = await factory.create_game_role(game.role_set.id, name="PairRole")

        await repo.create(CustomRatingCreate(custom_id=c.id, game_role_id=r.id, rating=1))
        with pytest.raises(IntegrityUniqueException):
            await repo.create(CustomRatingCreate(custom_id=c.id, game_role_id=r.id, rating=2))

    async def test_set_rating_and_delete(self, async_session, factory):
        repo = CustomRatingRepository(async_session)
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        c = Custom(member_id=m.id, creator_id=m.id)
        async_session.add(c)
        await async_session.flush()

        game = await _create_game(factory, async_session)
        r = await factory.create_game_role(game.role_set.id)

        cr = await repo.create(CustomRatingCreate(custom_id=c.id, game_role_id=r.id, rating=5))
        assert cr is not None

        cr = await repo.update(CustomRatingUpdate(id=cr.id, rating=7))
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

        game = await _create_game(factory, async_session)
        r = await factory.create_game_role(game.role_set.id)

        cr = await repo.create(CustomRatingCreate(custom_id=c.id, game_role_id=r.id, rating=3))
        assert cr is not None

        ok = await repo.delete_by_custom_rating(c.id, r.id)
        assert ok is True
        not_ok = await repo.delete_by_custom_rating(c.id, r.id)
        assert not_ok is False
