import uuid

import pytest

from src.core.models.rating import RatingCreate
from src.core.models.rating_set import RatingSetCreate, RatingSetUpdate
from src.infra.postgre import IntegrityForeignException, IntegrityUniqueException
from src.infra.postgre.models import Game as GameModel
from src.infra.postgre.repo import RatingRepository, RatingSetRepository


async def _create_bare_game(async_session) -> uuid.UUID:
    game = GameModel(name=f"BareGame-{uuid.uuid4().hex[:8]}")
    async_session.add(game)
    await async_session.flush()
    return game.id


@pytest.mark.asyncio(loop_scope="session")
class TestRatingSetRepository:

    async def test_create_and_get_rating_set(self, async_session):
        repo = RatingSetRepository(async_session)
        game_id = await _create_bare_game(async_session)
        rs = await repo.create(RatingSetCreate(name="RSetA", min_rating=0, max_rating=100, game_id=game_id))
        assert rs is not None
        assert rs.name == "RSetA"
        assert rs.min_rating == 0
        assert rs.max_rating == 100
        assert rs.game_id == game_id
        by_id = await repo.get(rs.id)
        assert by_id is not None and by_id.id == rs.id
        assert await repo.get(uuid.uuid4()) is None

    async def test_create_rating_set_unreal_game_raises(self, async_session):
        repo = RatingSetRepository(async_session)
        unreal_game_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(RatingSetCreate(name="Orphan", min_rating=0, max_rating=10, game_id=unreal_game_id))

    async def test_create_rating_set_duplicate_game_raises(self, async_session, factory):
        repo = RatingSetRepository(async_session)
        game = await factory.create_game()
        with pytest.raises(IntegrityUniqueException):
            await repo.create(RatingSetCreate(name="Dup", min_rating=0, max_rating=10, game_id=game.id))

    async def test_get_by_game_id(self, async_session, factory):
        repo = RatingSetRepository(async_session)
        game = await factory.create_game()
        fetched = await repo.get_by_game_id(game.id)
        assert fetched is not None
        assert fetched.game_id == game.id
        assert await repo.get_by_game_id(uuid.uuid4()) is None

    async def test_get_detail_includes_ratings(self, async_session, factory):
        repo = RatingSetRepository(async_session)
        rating_repo = RatingRepository(async_session)
        game = await factory.create_game(min_rating=0, max_rating=50)
        rating_set = await repo.get_by_game_id(game.id)
        assert rating_set is not None
        rating_set_id = rating_set.id
        r1 = await rating_repo.create(RatingCreate(rating_set_id=rating_set_id, threshold=10))
        r2 = await rating_repo.create(RatingCreate(rating_set_id=rating_set_id, threshold=30))
        detail = await repo.get_detail(rating_set_id)
        assert detail is not None
        assert detail.id == rating_set_id
        assert detail.game_id == game.id
        assert detail.min_rating == 0
        assert detail.max_rating == 50
        assert {r.id for r in detail.ratings} == {r1.id, r2.id}

    async def test_get_detail_empty_ratings(self, async_session, factory):
        repo = RatingSetRepository(async_session)
        game = await factory.create_game()
        rating_set = await repo.get_by_game_id(game.id)
        assert rating_set is not None
        detail = await repo.get_detail(rating_set.id)
        assert detail is not None
        assert detail.ratings == []

    async def test_get_detail_returns_none_for_missing_id(self, async_session):
        repo = RatingSetRepository(async_session)
        assert await repo.get_detail(uuid.uuid4()) is None

    async def test_update_rating_set(self, async_session, factory):
        repo = RatingSetRepository(async_session)
        game = await factory.create_game(min_rating=10, max_rating=20)
        rating_set = await repo.get_by_game_id(game.id)
        assert rating_set is not None
        rating_set_id = rating_set.id
        updated = await repo.update(RatingSetUpdate(id=rating_set_id, name="Renamed"))
        assert updated.name == "Renamed"
        assert updated.min_rating == 10
        assert updated.max_rating == 20
        updated = await repo.update(RatingSetUpdate(id=rating_set_id, min_rating=15, max_rating=18))
        assert updated.min_rating == 15
        assert updated.max_rating == 18
        assert updated.name == "Renamed"

    async def test_delete_rating_set(self, async_session):
        repo = RatingSetRepository(async_session)
        game_id = await _create_bare_game(async_session)
        rs = await repo.create(RatingSetCreate(name="DelRSet", min_rating=0, max_rating=5, game_id=game_id))
        ok = await repo.delete(rs.id)
        assert ok is True
        not_ok = await repo.delete(rs.id)
        assert not_ok is False
        assert await repo.get(rs.id) is None
        assert await repo.get_by_game_id(game_id) is None
