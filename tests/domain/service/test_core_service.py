import uuid
import pytest

from src.domain.service.core import CoreService
from src.domain.exceptions import NotFoundException, InternalLogicException, ForbiddenException
from src.infra.postgre.static import PERMISSION
from src.infra.postgre.repo import (
    MemberRepository,
    ServerRepository,
    GameRoleRepository,
    GameRoleSetRepository,
    RatingRepository,
    RatingSetRepository,
    PermissionRepository,
    RestrictionRepository,
    GameRepository
)
from src.infra.postgre.models import Server, GameRoleSet, RatingSet, Restriction, Game, Permission


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


async def _server(session, public: bool = False) -> Server:
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(id=uuid.uuid4(), name="Server", owner_id=uuid.uuid4(), public=public, role_set_id=rs.id,
               rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _role_set(session, is_global: bool = True) -> GameRoleSet:
    rs = GameRoleSet(name="GlobalRS", is_global=is_global)
    session.add(rs)
    await session.flush()
    return rs


async def _rating_set(session, is_global: bool = True) -> RatingSet:
    rts = RatingSet(name="GlobalRT", min_rating=0, max_rating=100, is_global=is_global)
    session.add(rts)
    await session.flush()
    return rts


async def _permission(session, code: str = "SOME_PERMISSION") -> None:
    p = Permission(code=code)
    session.add(p)
    await session.flush()


async def _restriction(session, code: str = "SOME_RESTRICTION") -> Restriction:
    r = Restriction(code=code)
    session.add(r)
    await session.flush()
    return r


async def _game(session, name: str = "Game") -> Game:
    g = Game(name=f"{name}-{uuid.uuid4()}", icon_id=uuid.uuid4(), banner_id=uuid.uuid4())
    session.add(g)
    await session.flush()
    return g


@pytest.fixture
async def core_service(async_session):
    server_repo = ServerRepository(async_session)
    game_repo = GameRepository(async_session)
    game_role_repo = GameRoleRepository(async_session)
    game_role_set_repo = GameRoleSetRepository(async_session)
    rating_repo = RatingRepository(async_session)
    rating_set_repo = RatingSetRepository(async_session)
    permission_repo = PermissionRepository(async_session)
    restriction_repo = RestrictionRepository(async_session)
    member_repo = MemberRepository(async_session)

    return CoreService(
        server_repo=server_repo,
        game_repo=game_repo,
        game_role_repo=game_role_repo,
        game_role_set_repo=game_role_set_repo,
        rating_repo=rating_repo,
        rating_set_repo=rating_set_repo,
        permission_repo=permission_repo,
        restriction_repo=restriction_repo,
        member_repo=member_repo,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_global_role_templates(async_session, core_service):
    await _role_set(async_session, is_global=True)
    await _role_set(async_session, is_global=False)

    res = await core_service.get_global_role_templates()
    assert len(res) == 1
    assert all(rs.is_global for rs in res)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_global_rating_templates(async_session, core_service):
    await _rating_set(async_session, is_global=True)
    await _rating_set(async_session, is_global=False)

    res = await core_service.get_global_rating_templates()
    assert len(res) == 1
    assert all(rts.is_global for rts in res)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_global_permissions(async_session, core_service):
    await _permission(async_session, code="P1")
    await _permission(async_session, code="P2")

    res = await core_service.get_global_permissions()
    assert {r.code for r in res} == {"P1", "P2"}


@pytest.mark.asyncio(loop_scope="session")
async def test_get_global_restrictions(async_session, core_service):
    await _restriction(async_session, code="R1")
    await _restriction(async_session, code="R2")

    res = await core_service.get_global_restrictions()
    assert {r.code for r in res} == {"R1", "R2"}


@pytest.mark.asyncio(loop_scope="session")
async def test_get_global_games(async_session, core_service):
    g1 = await _game(async_session, name="G1")
    g2 = await _game(async_session, name="G2")

    res = await core_service.get_global_games()
    ids = {g.id for g in res}
    assert {g1.id, g2.id}.issubset(ids)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_servers_returns_only_public(async_session, core_service):
    await _server(async_session, public=True)
    await _server(async_session, public=False)

    res = await core_service.list_servers()
    assert all(s.public for s in res)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_user_servers_filters_by_owner(async_session, core_service):
    owner_id = uuid.uuid4()
    other_owner_id = uuid.uuid4()

    rs = await _role_set(async_session)
    rts = await _rating_set(async_session)

    s1 = Server(name="S1", owner_id=owner_id, public=True, role_set_id=rs.id, rating_set_id=rts.id)
    s2 = Server(name="S2", owner_id=other_owner_id, public=True, role_set_id=rs.id, rating_set_id=rts.id)
    async_session.add_all([s1, s2])
    await async_session.flush()

    res = await core_service.list_user_servers(owner_id)
    assert len(res) == 1
    assert res[0].owner_id == owner_id


@pytest.mark.asyncio(loop_scope="session")
async def test_create_server_raises_when_role_set_not_found(async_session, core_service):
    rating = await _rating_set(async_session)

    with pytest.raises(NotFoundException):
        await core_service.create_server(
            owner_id=uuid.uuid4(),
            name="NewServer",
            description="Desc",
            public=True,
            role_set_id=uuid.uuid4(),
            rating_set_id=rating.id
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_server_raises_when_rating_set_not_found(async_session, core_service):
    role_set = await _role_set(async_session)

    with pytest.raises(NotFoundException):
        await core_service.create_server(
            owner_id=uuid.uuid4(),
            name="NewServer",
            description="Desc",
            public=True,
            role_set_id=role_set.id,
            rating_set_id=uuid.uuid4()
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_server_raises_when_template_is_not_global(async_session, core_service):
    owner_id = uuid.uuid4()
    global_role_set = await _role_set(async_session, is_global=True)
    local_role_set = await _role_set(async_session, is_global=False)
    global_rating_set = await _rating_set(async_session, is_global=True)
    local_rating_set = await _rating_set(async_session, is_global=False)

    with pytest.raises(NotFoundException):
        await core_service.create_server(
            owner_id=owner_id,
            name="BadRole",
            description="Desc",
            public=True,
            role_set_id=local_role_set.id,
            rating_set_id=global_rating_set.id
        )

    with pytest.raises(NotFoundException):
        await core_service.create_server(
            owner_id=owner_id,
            name="BadRating",
            description="Desc",
            public=True,
            role_set_id=global_role_set.id,
            rating_set_id=local_rating_set.id
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_server_success_persists(async_session, core_service):
    owner_id = uuid.uuid4()
    global_role_set = await _role_set(async_session, is_global=True)
    global_rating_set = await _rating_set(async_session, is_global=True)

    server = await core_service.create_server(
        owner_id=owner_id,
        name="ServerName",
        description="Desc",
        public=True,
        role_set_id=global_role_set.id,
        rating_set_id=global_rating_set.id
    )
    assert server is not None
    assert server.name == "ServerName"
    assert server.owner_id == owner_id

    assert server.role_set_id != global_role_set.id
    assert server.rating_set_id != global_rating_set.id

    new_role_set = await core_service.game_role_set_repo.get_by_id(server.role_set_id)
    new_rating_set = await core_service.rating_set_repo.get_by_id(server.rating_set_id)

    assert new_role_set is not None
    assert new_role_set.is_global is False
    assert new_rating_set is not None
    assert new_rating_set.is_global is False

    repo = core_service.server_repo
    reloaded = await repo.get_by_id(server.id)
    assert reloaded is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_server_permission(async_session, core_service):
    public_server = await _server(async_session, public=True)
    fetched_public = await core_service.get_server(public_server.id)
    assert fetched_public.id == public_server.id

    private_server = await _server(async_session, public=False)

    fetched_private = await core_service.get_server(private_server.id)
    assert fetched_private.id == private_server.id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_server_not_found(async_session, core_service):
    with pytest.raises(NotFoundException):
        await core_service.get_server(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_update_server_not_found(async_session, core_service):
    with pytest.raises(NotFoundException):
        await core_service.update_server(uuid.uuid4(), name="NewName", permission_mask=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_server_updates_fields_with_permissions(async_session, core_service):
    server = await _server(async_session, public=False)

    updated = await core_service.update_server(
        server.id,
        name="NewName",
        description="NewDesc",
        public=True,
        permission_mask=perm_mask(
            PERMISSION.EDIT_SERVER_NAME,
            PERMISSION.EDIT_SERVER_DESCRIPTION,
            PERMISSION.EDIT_SERVER_PUBLIC,
        ),
    )

    assert updated.name == "NewName"
    assert updated.description == "NewDesc"
    assert updated.public is True


@pytest.mark.asyncio(loop_scope="session")
async def test_update_server_without_permissions(async_session, core_service):
    server = await _server(async_session, public=False)

    with pytest.raises(ForbiddenException):
        await core_service.update_server(
            server.id,
            name="AnotherName",
            description="AnotherDesc",
            public=True,
            permission_mask=perm_mask(),
        )

    with pytest.raises(NotFoundException):
        await core_service.update_server(
            uuid.uuid4(),
            name="AnotherName",
            description="AnotherDesc",
            public=True,
            permission_mask=perm_mask(
                PERMISSION.EDIT_SERVER_NAME,
                PERMISSION.EDIT_SERVER_DESCRIPTION,
                PERMISSION.EDIT_SERVER_PUBLIC,
            ),
        )

    with pytest.raises(NotFoundException):
        await core_service.update_server(
            uuid.uuid4(),
            name="AnotherName",
            description="AnotherDesc",
            public=True,
            permission_mask=perm_mask(
                PERMISSION.EDIT_SERVER_NAME,
                PERMISSION.EDIT_SERVER_DESCRIPTION,
                PERMISSION.EDIT_SERVER_PUBLIC
            ),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_server_permission_and_flow(async_session, core_service):
    server = await _server(async_session, public=True)

    with pytest.raises(ForbiddenException):
        await core_service.delete_server(server.id, permission_mask=perm_mask())

    with pytest.raises(NotFoundException):
        await core_service.delete_server(uuid.uuid4(), permission_mask=perm_mask(PERMISSION.DELETE_SERVER))

    await core_service.delete_server(server.id, permission_mask=perm_mask(PERMISSION.DELETE_SERVER))
    repo = core_service.server_repo
    assert await repo.get_by_id(server.id) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_server_banner(async_session, core_service):
    server = await _server(async_session)
    server.banner_id = uuid.uuid4()
    async_session.add(server)
    await async_session.flush()

    with pytest.raises(ForbiddenException):
        await core_service.delete_server_banner(server.id, permission_mask=0)

    updated = await core_service.delete_server_banner(
        server.id,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_BANNER)
    )
    assert updated.banner_id is None

    reloaded = await core_service.server_repo.get_by_id(server.id)
    assert reloaded.banner_id is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_server_icon(async_session, core_service):
    server = await _server(async_session)
    server.icon_id = uuid.uuid4()
    async_session.add(server)
    await async_session.flush()

    with pytest.raises(ForbiddenException):
        await core_service.delete_server_icon(server.id, permission_mask=0)

    updated = await core_service.delete_server_icon(
        server.id,
        permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ICON)
    )
    assert updated.icon_id is None

    reloaded = await core_service.server_repo.get_by_id(server.id)
    assert reloaded.icon_id is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_server_assets_not_found(async_session, core_service):
    with pytest.raises(NotFoundException):
        await core_service.delete_server_banner(
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_BANNER)
        )

    with pytest.raises(NotFoundException):
        await core_service.delete_server_icon(
            uuid.uuid4(),
            permission_mask=perm_mask(PERMISSION.EDIT_SERVER_ICON)
        )
