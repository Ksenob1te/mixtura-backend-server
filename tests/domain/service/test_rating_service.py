import uuid
import pytest

from src.domain.service.rating import RatingService
from src.domain.exceptions import NotFoundException, ForbiddenException
from src.domain.models.rating.request import (
    RatingItemCreateRequest,
    RatingItemUpdateRequest,
    RatingSetUpdateRequest,
)
from src.infra.postgre.repo import RatingRepository, RatingSetRepository, ServerRepository
from src.infra.postgre.models import Server, GameRoleSet, RatingSet
from src.infra.postgre.static import PERMISSION


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


async def _server(session) -> Server:
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(
        id=uuid.uuid4(),
        name="Server",
        owner_id=uuid.uuid4(),
        public=True,
        role_set_id=rs.id,
        rating_set_id=rts.id,
    )
    session.add(s)
    await session.flush()
    return s


@pytest.fixture
async def rating_service(async_session):
    rating_repo = RatingRepository(async_session)
    rating_set_repo = RatingSetRepository(async_session)
    server_repo = ServerRepository(async_session)

    return RatingService(
        rating_repo=rating_repo,
        rating_set_repo=rating_set_repo,
        server_repo=server_repo,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_rating_set_not_found(async_session, rating_service):
    with pytest.raises(NotFoundException):
        await rating_service.get_rating_set(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_get_rating_set_success(async_session, rating_service):
    server = await _server(async_session)
    rs = await rating_service.get_rating_set(server.id)
    assert rs.id == server.rating_set_id


@pytest.mark.asyncio(loop_scope="session")
async def test_update_rating_set_forbidden(async_session, rating_service):
    server = await _server(async_session)
    body = RatingSetUpdateRequest(name="NewName", min_rating=10, max_rating=100)
    with pytest.raises(ForbiddenException):
        await rating_service.update_rating_set(server.rating_set_id, body, permission_mask=perm_mask())


@pytest.mark.asyncio(loop_scope="session")
async def test_update_rating_set_not_found(async_session, rating_service):
    body = RatingSetUpdateRequest(name="NewName", min_rating=10, max_rating=100)
    with pytest.raises(NotFoundException):
        await rating_service.update_rating_set(
            uuid.uuid4(),
            body,
            permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_rating_set_success(async_session, rating_service):
    server = await _server(async_session)
    body = RatingSetUpdateRequest(name="NewName", min_rating=10, max_rating=100)

    updated = await rating_service.update_rating_set(
        server.rating_set_id,
        body,
        permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
    )

    assert updated.name == "NewName"
    assert updated.min_rating == 10
    assert updated.max_rating == 100


@pytest.mark.asyncio(loop_scope="session")
async def test_create_rating_forbidden_without_permission(async_session, rating_service):
    server = await _server(async_session)
    body = RatingItemCreateRequest(threshold=10)

    with pytest.raises(ForbiddenException):
        await rating_service.create_rating(
            server.rating_set_id,
            body,
            icon_id=uuid.uuid4(),
            permission_mask=perm_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_rating_not_found_rating_set(async_session, rating_service):
    body = RatingItemCreateRequest(threshold=10)

    with pytest.raises(NotFoundException):
        await rating_service.create_rating(
            uuid.uuid4(),
            body,
            icon_id=uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_update_and_delete_rating(async_session, rating_service):
    server = await _server(async_session)
    body_create = RatingItemCreateRequest(threshold=10)

    created = await rating_service.create_rating(
        server.rating_set_id,
        body_create,
        icon_id=uuid.uuid4(),
        permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
    )

    assert created.threshold == 10
    assert created.rating_set_id == server.rating_set_id

    body_update = RatingItemUpdateRequest(threshold=20)

    updated = await rating_service.update_rating(
        created.id,
        body_update,
        permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
    )

    assert updated.threshold == 20

    await rating_service.delete_rating(
        created.id,
        permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
    )

    with pytest.raises(NotFoundException):
        await rating_service.update_rating(
            created.id,
            body_update,
            permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_rating_forbidden_without_permission(async_session, rating_service):
    server = await _server(async_session)
    body_create = RatingItemCreateRequest(threshold=10)

    created = await rating_service.create_rating(
        server.rating_set_id,
        body_create,
        icon_id=uuid.uuid4(),
        permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
    )

    body_update = RatingItemUpdateRequest(threshold=20)

    with pytest.raises(ForbiddenException):
        await rating_service.update_rating(
            created.id,
            body_update,
            permission_mask=perm_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_rating_forbidden_without_permission(async_session, rating_service):
    server = await _server(async_session)
    body_create = RatingItemCreateRequest(threshold=10)

    created = await rating_service.create_rating(
        server.rating_set_id,
        body_create,
        icon_id=uuid.uuid4(),
        permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
    )

    with pytest.raises(ForbiddenException):
        await rating_service.delete_rating(
            created.id,
            permission_mask=perm_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_rating_not_found(async_session, rating_service):
    with pytest.raises(NotFoundException):
        await rating_service.delete_rating(
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_RATING_SET),
        )
