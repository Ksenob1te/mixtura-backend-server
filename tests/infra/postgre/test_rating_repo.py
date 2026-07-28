import uuid

import pytest

from src.core.models.rating import RatingCreate, RatingUpdate
from src.infra.postgre import IntegrityForeignException
from src.infra.postgre.repo import RatingRepository


async def _create_game(factory, session, **kwargs):
    game = await factory.create_game(**kwargs)
    await session.refresh(game, attribute_names=["role_set", "rating_set"])
    return game


@pytest.mark.asyncio(loop_scope="session")
class TestRatingRepository:

    async def test_create_and_get_rating(self, async_session, factory):
        repo = RatingRepository(async_session)
        game = await _create_game(factory, async_session)
        r = await repo.create(RatingCreate(rating_set_id=game.rating_set.id, threshold=100, icon_id=uuid.uuid4()))
        assert r is not None
        assert r.threshold == 100
        by_id = await repo.get(r.id)
        assert by_id is not None and by_id.id == r.id
        assert await repo.get(uuid.uuid4()) is None

    async def test_create_rating_unreal_set(self, async_session):
        repo = RatingRepository(async_session)
        unreal_set_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(RatingCreate(rating_set_id=unreal_set_id, threshold=100, icon_id=uuid.uuid4()))

    async def test_list_for_set(self, async_session, factory):
        repo = RatingRepository(async_session)
        game1 = await _create_game(factory, async_session, name="Game1")
        game2 = await _create_game(factory, async_session, name="Game2")
        ratings1 = [
            await repo.create(RatingCreate(rating_set_id=game1.rating_set.id, threshold=i, icon_id=uuid.uuid4()))
            for i in range(2)
        ]
        ratings2 = [
            await repo.create(RatingCreate(rating_set_id=game2.rating_set.id, threshold=i, icon_id=uuid.uuid4()))
            for i in range(3)
        ]
        listed1 = await repo.list_for_set(game1.rating_set.id)
        listed2 = await repo.list_for_set(game2.rating_set.id)
        assert {r.id for r in listed1} == {r.id for r in ratings1 if r is not None}
        assert {r.id for r in listed2} == {r.id for r in ratings2 if r is not None}

    async def test_set_icon_and_threshold(self, async_session, factory):
        repo = RatingRepository(async_session)
        game = await _create_game(factory, async_session)
        r = await repo.create(RatingCreate(rating_set_id=game.rating_set.id, threshold=50, icon_id=uuid.uuid4()))
        assert r is not None
        new_icon_id = uuid.uuid4()
        r = await repo.update(RatingUpdate(id=r.id, icon_id=new_icon_id))
        assert r.icon_id == new_icon_id
        r = await repo.update(RatingUpdate(id=r.id, threshold=60))
        assert r.threshold == 60

    async def test_delete_rating(self, async_session, factory):
        repo = RatingRepository(async_session)
        game = await _create_game(factory, async_session)
        r = await repo.create(RatingCreate(rating_set_id=game.rating_set.id, threshold=10, icon_id=uuid.uuid4()))
        assert r is not None
        ok = await repo.delete(r.id)
        assert ok is True
        not_ok = await repo.delete(r.id)
        assert not_ok is False

    async def test_list_for_set_empty(self, async_session, factory):
        repo = RatingRepository(async_session)
        game = await _create_game(factory, async_session)
        listed = await repo.list_for_set(game.rating_set.id)
        assert listed == []

    async def test_copy_rating(self, async_session, factory):
        repo = RatingRepository(async_session)
        game1 = await _create_game(factory, async_session, name="Game1")
        game2 = await _create_game(factory, async_session, name="Game2")
        r1 = await repo.create(RatingCreate(rating_set_id=game1.rating_set.id, threshold=150, icon_id=uuid.uuid4()))
        assert r1 is not None
        r2 = await repo.copy_rating(r1, game2.rating_set.id)
        assert r2 is not None
        assert r2.id != r1.id
        assert r2.threshold == r1.threshold
        assert r2.icon_id == r1.icon_id
        assert r2.rating_set_id == game2.rating_set.id
