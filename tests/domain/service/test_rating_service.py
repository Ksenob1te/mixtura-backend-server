import uuid
import pytest
import pytest_asyncio

from src.domain.service.rating import RatingService
from src.domain.exceptions import NotFoundException, ForbiddenException
from src.domain.models.rating.request import (
    RatingItemCreateRequest,
    RatingItemUpdateRequest,
    RatingSetUpdateRequest,
)
from src.infra.postgre.repo import RatingRepository, RatingSetRepository, ServerRepository
from src.infra.postgre.static import PERMISSION


@pytest_asyncio.fixture(loop_scope="session")
async def rating_service(async_session):
    return RatingService(
        rating_repo=RatingRepository(async_session),
        rating_set_repo=RatingSetRepository(async_session),
        server_repo=ServerRepository(async_session),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestRatingService:

    async def test_get_rating_set_not_found(self, rating_service):
        with pytest.raises(NotFoundException):
            await rating_service.get_rating_set(uuid.uuid4())

    async def test_get_rating_set_success(self, rating_service, factory):
        server = await factory.create_server()
        rs = await rating_service.get_rating_set(server.id)
        assert rs.id == server.rating_set.id

    async def test_update_rating_set_forbidden(self, rating_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(ForbiddenException):
            await rating_service.update_rating_set(
                server.id,
                server.rating_set.id,
                name="NewName",
                min_rating=10,
                max_rating=100,
                permission_mask=helpers.perm_mask()
            )

    async def test_update_rating_set_not_found(self, rating_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await rating_service.update_rating_set(
                server.id,
                uuid.uuid4(),
                name="NewName",
                min_rating=10,
                max_rating=100,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_set_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        with pytest.raises(NotFoundException):
            await rating_service.update_rating_set(
                server2.id,
                server1.rating_set.id,
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_set_success(self, rating_service, factory, helpers):
        server = await factory.create_server()

        updated = await rating_service.update_rating_set(
            server.id,
            server.rating_set.id,
            name="NewName",
            min_rating=10,
            max_rating=100,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        assert updated.name == "NewName"
        assert updated.min_rating == 10
        assert updated.max_rating == 100

    async def test_create_rating_forbidden_without_permission(self, rating_service, factory, helpers):
        server = await factory.create_server()

        with pytest.raises(ForbiddenException):
            await rating_service.create_rating(
                server.id,
                server.rating_set.id,
                threshold=10,
                icon_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(),
            )

    async def test_create_rating_not_found_rating_set(self, rating_service, factory, helpers):
        server = await factory.create_server()

        with pytest.raises(NotFoundException):
            await rating_service.create_rating(
                server.id,
                uuid.uuid4(),
                threshold=10,
                icon_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_create_rating_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()

        with pytest.raises(NotFoundException):
            await rating_service.create_rating(
                server2.id,
                server1.rating_set.id,
                threshold=10,
                icon_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_create_and_update_and_delete_rating(self, rating_service, factory, helpers):
        server = await factory.create_server()

        created = await rating_service.create_rating(
            server.id,
            server.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        assert created.threshold == 10
        assert created.rating_set.id == server.rating_set.id

        updated = await rating_service.update_rating(
            server.id,
            created.id,
            threshold=20,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        assert updated.threshold == 20

        await rating_service.delete_rating(
            server.id,
            created.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(NotFoundException):
            await rating_service.update_rating(
                server.id,
                created.id,
                threshold=20,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_forbidden_without_permission(self, rating_service, factory, helpers):
        server = await factory.create_server()

        created = await rating_service.create_rating(
            server.id,
            server.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(ForbiddenException):
            await rating_service.update_rating(
                server.id,
                created.id,
                threshold=20,
                permission_mask=helpers.perm_mask(),
            )

    async def test_update_rating_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()

        created = await rating_service.create_rating(
            server1.id,
            server1.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(NotFoundException):
            await rating_service.update_rating(
                server2.id,
                created.id,
                threshold=20,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_delete_rating_forbidden_without_permission(self, rating_service, factory, helpers):
        server = await factory.create_server()

        created = await rating_service.create_rating(
            server.id,
            server.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(ForbiddenException):
            await rating_service.delete_rating(
                server.id,
                created.id,
                permission_mask=helpers.perm_mask(),
            )

    async def test_delete_rating_not_found(self, rating_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await rating_service.delete_rating(
                server.id,
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_delete_rating_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()

        created = await rating_service.create_rating(
            server1.id,
            server1.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(NotFoundException):
            await rating_service.delete_rating(
                server2.id,
                created.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_delete_rating_icon(self, rating_service, factory, helpers):
        server = await factory.create_server()
        icon_id = uuid.uuid4()
        created = await rating_service.create_rating(
            server.id,
            server.rating_set.id,
            threshold=10,
            icon_id=icon_id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        assert created.icon_id == icon_id

        updated = await rating_service.delete_rating_icon(
            server.id,
            created.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        assert updated.icon_id is None
