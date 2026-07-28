import uuid

import pytest
import pytest_asyncio

from src.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from src.core.services import MemberCustomService
from src.infra.postgre.repo import (
    CustomRatingRepository,
    CustomRepository,
    GameRepository,
    GameRoleRepository,
    GameRoleSetRepository,
    MemberRepository,
    RatingSetRepository,
    ServerRepository,
)
from src.infra.postgre.static import PERMISSION


@pytest_asyncio.fixture(loop_scope="session")
async def member_custom_service(async_session):
    return MemberCustomService(
        CustomRepository(async_session),
        CustomRatingRepository(async_session),
        MemberRepository(async_session),
        GameRoleRepository(async_session),
        ServerRepository(async_session),
        RatingSetRepository(async_session),
        GameRoleSetRepository(async_session),
        GameRepository(async_session),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestMemberCustomService:

    async def test_list_customs_for_member(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)

        c1 = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM)
        )
        c2 = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM)
        )

        res = await member_custom_service.list_customs(server.id, member.id)
        ids = {c.id for c in res}
        assert c1.id in ids and c2.id in ids

    async def test_list_customs_member_not_found(self, member_custom_service, factory):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await member_custom_service.list_customs(server.id, uuid.uuid4())

    async def test_list_customs_wrong_server(self, member_custom_service, factory):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        member = await factory.create_member(server1.id)

        with pytest.raises(NotFoundException):
            await member_custom_service.list_customs(server2.id, member.id)

    async def test_create_custom_forbidden_without_permission(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)

        with pytest.raises(ForbiddenException):
            await member_custom_service.create_custom(
                issuer_id=member.id, server_id=server.id, member_id=member.id,
                permission_mask=helpers.perm_mask()
            )

    async def test_create_custom_member_not_found(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)
        with pytest.raises(NotFoundException):
            await member_custom_service.create_custom(
                issuer_id=member.id, server_id=server.id, member_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM)
            )

    async def test_create_custom_wrong_server(self, member_custom_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        member = await factory.create_member(server1.id)

        with pytest.raises(NotFoundException):
            await member_custom_service.create_custom(
                issuer_id=member.id, server_id=server2.id, member_id=member.id,
                permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM)
            )

    async def test_create_custom_issuer_not_found(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)

        with pytest.raises(NotFoundException, match="Issuer field not found"):
            await member_custom_service.create_custom(
                issuer_id=uuid.uuid4(), server_id=server.id, member_id=member.id,
                permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM)
            )

    async def test_get_custom_not_found(self, member_custom_service, factory):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await member_custom_service.get_custom(server.id, uuid.uuid4())

    async def test_create_and_get_custom(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)

        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )
        assert created is not None
        assert created.member_id == member.id

        fetched = await member_custom_service.get_custom(server.id, created.id)
        assert fetched.id == created.id

    async def test_get_custom_wrong_server(self, member_custom_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        member = await factory.create_member(server1.id)

        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server1.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )

        with pytest.raises(NotFoundException):
            await member_custom_service.get_custom(server2.id, created.id)

    async def test_delete_custom_permissions(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)

        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )

        with pytest.raises(ForbiddenException):
            await member_custom_service.delete_custom(server.id, created.id, permission_mask=helpers.perm_mask())

        await member_custom_service.delete_custom(server.id, created.id,
                                                  permission_mask=helpers.perm_mask(PERMISSION.DELETE_CUSTOM))

        with pytest.raises(NotFoundException):
            await member_custom_service.get_custom(server.id, created.id)

    async def test_delete_not_existent_custom(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await member_custom_service.delete_custom(server.id, uuid.uuid4(),
                                                      permission_mask=helpers.perm_mask(PERMISSION.DELETE_CUSTOM))

    async def test_delete_custom_wrong_server(self, member_custom_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        member = await factory.create_member(server1.id)
        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server1.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )

        with pytest.raises(NotFoundException):
            await member_custom_service.delete_custom(
                server_id=server2.id, custom_id=created.id,
                permission_mask=helpers.perm_mask(PERMISSION.DELETE_CUSTOM)
            )

    async def test_set_rating_create_and_update(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)
        game = await factory.create_game(server_id=server.id)
        await factory.attach_game(server.id, game.id)
        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )

        role_set = await member_custom_service.game_role_set_repo.get_by_game_id(game.id)
        role = await factory.create_game_role(role_set.id)

        # Creator can change rating without extra permission
        updated = await member_custom_service.set_rating_value(
            issuer_id=member.id,
            server_id=server.id,
            custom_id=created.id,
            game_role_id=role.id,
            rating=10,
            permission_mask=helpers.perm_mask(),
        )
        assert updated.id == created.id
        stored = await member_custom_service.custom_rating_repo.get_by_custom_role(created.id, role.id)
        assert stored is not None and stored.rating == 10

        # Creator updates rating again
        updated2 = await member_custom_service.set_rating_value(
            issuer_id=member.id,
            server_id=server.id,
            custom_id=created.id,
            game_role_id=role.id,
            rating=15,
            permission_mask=helpers.perm_mask(),
        )
        assert updated2.id == created.id
        stored2 = await member_custom_service.custom_rating_repo.get_by_custom_role(created.id, role.id)
        assert stored2 is not None and stored2.rating == 15

    async def test_set_rating_forbidden_for_non_creator_without_permission(self, member_custom_service, factory,
                                                                           helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)
        other_member = await factory.create_member(server.id)
        game = await factory.create_game(server_id=server.id)
        await factory.attach_game(server.id, game.id)

        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )
        role_set = await member_custom_service.game_role_set_repo.get_by_game_id(game.id)
        role = await factory.create_game_role(role_set.id)

        with pytest.raises(ForbiddenException):
            await member_custom_service.set_rating_value(
                issuer_id=other_member.id,
                server_id=server.id,
                custom_id=created.id,
                game_role_id=role.id,
                rating=5,
                permission_mask=helpers.perm_mask(),
            )

    async def test_set_rating_allowed_for_non_creator_with_permission(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)
        other_member = await factory.create_member(server.id)
        game = await factory.create_game(server_id=server.id)
        await factory.attach_game(server.id, game.id)

        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )
        role_set = await member_custom_service.game_role_set_repo.get_by_game_id(game.id)
        role = await factory.create_game_role(role_set.id)

        updated = await member_custom_service.set_rating_value(
            issuer_id=other_member.id,
            server_id=server.id,
            custom_id=created.id,
            game_role_id=role.id,
            rating=7,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ALL_CUSTOMS),
        )
        assert updated.id == created.id
        stored = await member_custom_service.custom_rating_repo.get_by_custom_role(created.id, role.id)
        assert stored is not None and stored.rating == 7

    async def test_set_rating_foreign_key_error(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        # Use random IDs to trigger FK violation
        with pytest.raises(NotFoundException):
            await member_custom_service.set_rating_value(
                issuer_id=uuid.uuid4(),
                server_id=server.id,
                custom_id=uuid.uuid4(),
                game_role_id=uuid.uuid4(),
                rating=5,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ALL_CUSTOMS),
            )

    async def test_set_rating_wrong_server(self, member_custom_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        member = await factory.create_member(server1.id)
        game = await factory.create_game(server_id=server1.id)
        await factory.attach_game(server1.id, game.id)
        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server1.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )
        role_set = await member_custom_service.game_role_set_repo.get_by_game_id(game.id)
        role = await factory.create_game_role(role_set.id)

        with pytest.raises(NotFoundException):
            await member_custom_service.set_rating_value(
                issuer_id=member.id,
                server_id=server2.id,
                custom_id=created.id,
                game_role_id=role.id,
                rating=10,
                permission_mask=helpers.perm_mask(),
            )

    async def test_set_rating_out_of_bounds(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)
        game = await factory.create_game(server_id=server.id)
        await factory.attach_game(server.id, game.id)
        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )
        role_set = await member_custom_service.game_role_set_repo.get_by_game_id(game.id)
        role = await factory.create_game_role(role_set.id)

        # Get bounds from the game's rating set
        rating_set = await member_custom_service.rating_set_repo.get_by_game_id(game.id)
        min_rating = rating_set.min_rating
        max_rating = rating_set.max_rating

        # Test value below minimum
        with pytest.raises(BadRequestException, match="Rating value is out of bounds"):
            await member_custom_service.set_rating_value(
                issuer_id=member.id,
                server_id=server.id,
                custom_id=created.id,
                game_role_id=role.id,
                rating=min_rating - 1,
                permission_mask=helpers.perm_mask(),
            )

        # Test value above maximum
        with pytest.raises(BadRequestException, match="Rating value is out of bounds"):
            await member_custom_service.set_rating_value(
                issuer_id=member.id,
                server_id=server.id,
                custom_id=created.id,
                game_role_id=role.id,
                rating=max_rating + 1,
                permission_mask=helpers.perm_mask(),
            )

    async def test_set_rating_game_not_enabled_on_server(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)
        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )

        # Game exists but is never attached to the member's server
        game = await factory.create_game(server_id=None)
        role_set = await member_custom_service.game_role_set_repo.get_by_game_id(game.id)
        role = await factory.create_game_role(role_set.id)

        with pytest.raises(NotFoundException, match="Game is not enabled on server"):
            await member_custom_service.set_rating_value(
                issuer_id=member.id,
                server_id=server.id,
                custom_id=created.id,
                game_role_id=role.id,
                rating=5,
                permission_mask=helpers.perm_mask(),
            )

    async def test_set_rating_game_belongs_to_another_server(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        other_server = await factory.create_server()
        member = await factory.create_member(server.id)
        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )

        # Local game owned by a different server
        foreign_game = await factory.create_game(server_id=other_server.id)
        await factory.attach_game(other_server.id, foreign_game.id)
        role_set = await member_custom_service.game_role_set_repo.get_by_game_id(foreign_game.id)
        role = await factory.create_game_role(role_set.id)

        with pytest.raises(NotFoundException, match="Game is not enabled on server"):
            await member_custom_service.set_rating_value(
                issuer_id=member.id,
                server_id=server.id,
                custom_id=created.id,
                game_role_id=role.id,
                rating=5,
                permission_mask=helpers.perm_mask(),
            )

    async def test_set_rating_bounds_sourced_per_game(self, member_custom_service, factory, helpers):
        server = await factory.create_server()
        member = await factory.create_member(server.id)
        created = await member_custom_service.create_custom(
            issuer_id=member.id, server_id=server.id, member_id=member.id,
            permission_mask=helpers.perm_mask(PERMISSION.CREATE_CUSTOM),
        )

        narrow_game = await factory.create_game(server_id=server.id, min_rating=0, max_rating=10)
        wide_game = await factory.create_game(server_id=server.id, min_rating=0, max_rating=1000)
        await factory.attach_game(server.id, narrow_game.id)
        await factory.attach_game(server.id, wide_game.id)

        narrow_role_set = await member_custom_service.game_role_set_repo.get_by_game_id(narrow_game.id)
        wide_role_set = await member_custom_service.game_role_set_repo.get_by_game_id(wide_game.id)
        narrow_role = await factory.create_game_role(narrow_role_set.id)
        wide_role = await factory.create_game_role(wide_role_set.id)

        # 500 is out of bounds for the narrow game...
        with pytest.raises(BadRequestException, match="Rating value is out of bounds"):
            await member_custom_service.set_rating_value(
                issuer_id=member.id,
                server_id=server.id,
                custom_id=created.id,
                game_role_id=narrow_role.id,
                rating=500,
                permission_mask=helpers.perm_mask(),
            )

        # ...but valid for the wide game, proving bounds are sourced per-game
        updated = await member_custom_service.set_rating_value(
            issuer_id=member.id,
            server_id=server.id,
            custom_id=created.id,
            game_role_id=wide_role.id,
            rating=500,
            permission_mask=helpers.perm_mask(),
        )
        assert updated.id == created.id
        stored = await member_custom_service.custom_rating_repo.get_by_custom_role(created.id, wide_role.id)
        assert stored is not None and stored.rating == 500
