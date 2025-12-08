import uuid
import pytest

from src.domain.service import MemberCustomService
from src.domain.exceptions import NotFoundException, ForbiddenException, InternalLogicException
from src.infra.postgre.repo import (
    CustomRepository,
    CustomRatingRepository,
    MemberRepository,
    GameRoleRepository,
)
from src.infra.postgre.models import Server, GameRoleSet, RatingSet, Member, GameRole
from src.infra.postgre.static import PERMISSION


def perm_mask(*perms: PERMISSION) -> int:
    return PERMISSION.serialize_permission_codes(perms)


async def _server(session) -> Server:
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(id=uuid.uuid4(), name="Server", owner_id=uuid.uuid4(), public=True, role_set_id=rs.id,
               rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _member(session, server: Server) -> Member:
    m = Member(server_id=server.id, user_id=uuid.uuid4(), name="Member")
    session.add(m)
    await session.flush()
    return m


async def _role(session, role_set: GameRoleSet) -> GameRole:
    r = GameRole(name="Role", role_set_id=role_set.id, min_in_team=0, max_in_team=1)
    session.add(r)
    await session.flush()
    return r


@pytest.fixture
async def member_custom_service(async_session):
    custom_repo = CustomRepository(async_session)
    custom_rating_repo = CustomRatingRepository(async_session)
    member_repo = MemberRepository(async_session)
    game_role_repo = GameRoleRepository(async_session)

    return MemberCustomService(
        custom_repo,
        custom_rating_repo,
        member_repo,
        game_role_repo,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_list_customs_for_member(async_session, member_custom_service):
    server = await _server(async_session)
    member = await _member(async_session, server)

    c1 = await member_custom_service.create_custom(
        member.id, creator_id=member.id,
        permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM)
    )
    c2 = await member_custom_service.create_custom(
        member.id, creator_id=None,
        permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM)
    )

    res = await member_custom_service.list_customs(member.id)
    ids = {c.id for c in res}
    assert c1.id in ids and c2.id in ids

    res_empty = await member_custom_service.list_customs(uuid.uuid4())
    assert res_empty == []


@pytest.mark.asyncio(loop_scope="session")
async def test_create_custom_forbidden_without_permission(async_session, member_custom_service):
    server = await _server(async_session)
    member = await _member(async_session, server)

    with pytest.raises(ForbiddenException):
        await member_custom_service.create_custom(member.id, creator_id=member.id, permission_mask=perm_mask())


@pytest.mark.asyncio(loop_scope="session")
async def test_create_custom_foreign_key_error(async_session, member_custom_service):
    with pytest.raises(NotFoundException):
        await member_custom_service.create_custom(
            uuid.uuid4(), creator_id=None,
            permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM)
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_get_custom_not_found(async_session, member_custom_service):
    with pytest.raises(NotFoundException):
        await member_custom_service.get_custom(uuid.uuid4())


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_custom(async_session, member_custom_service):
    server = await _server(async_session)
    member = await _member(async_session, server)

    created = await member_custom_service.create_custom(
        member.id,
        creator_id=member.id,
        permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM),
    )
    assert created is not None
    assert created.member_id == member.id

    fetched = await member_custom_service.get_custom(created.id)
    assert fetched.id == created.id


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_custom_permissions(async_session, member_custom_service):
    server = await _server(async_session)
    member = await _member(async_session, server)

    created = await member_custom_service.create_custom(
        member.id,
        creator_id=member.id,
        permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM),
    )

    with pytest.raises(ForbiddenException):
        await member_custom_service.delete_custom(created.id, permission_mask=perm_mask())

    await member_custom_service.delete_custom(created.id, permission_mask=perm_mask(PERMISSION.DELETE_CUSTOM))

    with pytest.raises(NotFoundException):
        await member_custom_service.get_custom(created.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_not_existent_custom(async_session, member_custom_service):
    with pytest.raises(NotFoundException):
        await member_custom_service.delete_custom(uuid.uuid4(), permission_mask=perm_mask(PERMISSION.DELETE_CUSTOM))


@pytest.mark.asyncio(loop_scope="session")
async def test_set_rating_create_and_update(async_session, member_custom_service):
    server = await _server(async_session)
    member = await _member(async_session, server)
    created = await member_custom_service.create_custom(
        member.id,
        creator_id=member.id,
        permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM),
    )

    role = await _role(async_session, server.role_set)

    # Creator can change rating without extra permission
    updated = await member_custom_service.set_rating_value(
        issuer_id=member.id,
        custom_id=created.id,
        game_role_id=role.id,
        rating=10,
        permission_mask=perm_mask(),
    )
    assert any(cr.game_role_id == role.id and cr.rating == 10 for cr in updated.custom_ratings)

    # Creator updates rating again
    updated2 = await member_custom_service.set_rating_value(
        issuer_id=member.id,
        custom_id=created.id,
        game_role_id=role.id,
        rating=15,
        permission_mask=perm_mask(),
    )
    assert any(cr.game_role_id == role.id and cr.rating == 15 for cr in updated2.custom_ratings)


@pytest.mark.asyncio(loop_scope="session")
async def test_set_rating_forbidden_for_non_creator_without_permission(async_session, member_custom_service):
    server = await _server(async_session)
    member = await _member(async_session, server)
    other_member = await _member(async_session, server)

    created = await member_custom_service.create_custom(
        member.id,
        creator_id=member.id,
        permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM),
    )
    role = await _role(async_session, server.role_set)

    with pytest.raises(ForbiddenException):
        await member_custom_service.set_rating_value(
            issuer_id=other_member.id,
            custom_id=created.id,
            game_role_id=role.id,
            rating=5,
            permission_mask=perm_mask(),
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_set_rating_allowed_for_non_creator_with_permission(async_session, member_custom_service):
    server = await _server(async_session)
    member = await _member(async_session, server)
    other_member = await _member(async_session, server)

    created = await member_custom_service.create_custom(
        member.id,
        creator_id=member.id,
        permission_mask=perm_mask(PERMISSION.CREATE_CUSTOM),
    )
    role = await _role(async_session, server.role_set)

    updated = await member_custom_service.set_rating_value(
        issuer_id=other_member.id,
        custom_id=created.id,
        game_role_id=role.id,
        rating=7,
        permission_mask=perm_mask(PERMISSION.EDIT_ALL_CUSTOMS),
    )
    assert any(cr.game_role_id == role.id and cr.rating == 7 for cr in updated.custom_ratings)


@pytest.mark.asyncio(loop_scope="session")
async def test_set_rating_foreign_key_error(async_session, member_custom_service):
    # Use random IDs to trigger FK violation
    with pytest.raises(NotFoundException):
        await member_custom_service.set_rating_value(
            issuer_id=uuid.uuid4(),
            custom_id=uuid.uuid4(),
            game_role_id=uuid.uuid4(),
            rating=5,
            permission_mask=perm_mask(PERMISSION.EDIT_ALL_CUSTOMS),
        )
