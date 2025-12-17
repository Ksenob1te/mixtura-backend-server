import uuid
import pytest
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException

from src.infra.postgre.models import Server, Member, ServerRole, GameRoleSet, RatingSet
from src.infra.postgre.repo import MemberRepository


async def _server(session, name="Srv"):
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(name=name, owner_id=uuid.uuid4(), public=True, role_set_id=rs.id, rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _role(session, server: Server, name="Role", position=0):
    r = ServerRole(server_id=server.id, name=name, position=position)
    session.add(r)
    await session.flush()
    return r


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_member(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), name="Alice")
    assert m is not None and m.name == "Alice"
    by_id = await repo.get_by_id(m.id)
    assert by_id is not None and by_id.id == m.id
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_member_unreal_server(async_session):
    repo = MemberRepository(async_session)
    unreal_server_id = uuid.uuid4()
    with pytest.raises(IntegrityForeignException):
        await repo.create(server_id=unreal_server_id, user_id=uuid.uuid4(), name="Bob")


@pytest.mark.asyncio(loop_scope="session")
async def test_create_member_unreal_role(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    unreal_role_id = uuid.uuid4()
    with pytest.raises(IntegrityForeignException):
        await repo.create(server_id=s.id, user_id=uuid.uuid4(), name="Charlie", server_role_id=unreal_role_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_duplicate_user_membership_raises(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    user_id = uuid.uuid4()
    _ = await repo.create(server_id=s.id, user_id=user_id, name="UserOne")
    with pytest.raises(IntegrityUniqueException):
        await repo.create(server_id=s.id, user_id=user_id, name="UserOneDup")


@pytest.mark.asyncio(loop_scope="session")
async def test_list_and_list_active(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    members = [await repo.create(server_id=s.id, user_id=uuid.uuid4(), name=f"U{i}") for i in range(3)]
    listed = await repo.list_for_server(s.id)
    assert {m.id for m in listed} == {m.id for m in members if m is not None}
    active_listed = await repo.list_active_for_server(s.id)
    assert {m.id for m in active_listed} == {m.id for m in members if m is not None}


@pytest.mark.asyncio(loop_scope="session")
async def test_activation_and_deactivation(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), name="ActUser")
    assert m is not None and m.active is True
    m = await repo.deactivate(m)
    assert m.active is False
    m2 = await repo.deactivate(m)
    assert m2.id == m.id and m2.active is False
    m = await repo.activate(m)
    assert m.active is True
    m2 = await repo.activate(m)
    assert m2.id == m.id and m2.active is True


@pytest.mark.asyncio(loop_scope="session")
async def test_set_role(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    role = await _role(async_session, s)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), name="RoleUser")
    assert m is not None
    m = await repo.set_role(m, role.id)
    assert m.server_role_id == role.id
    m2 = await repo.set_role(m, role.id)
    assert m2.id == m.id and m2.server_role_id == role.id
    m = await repo.set_role(m, None)
    assert m.server_role_id is None


@pytest.mark.asyncio(loop_scope="session")
async def test_set_name(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), name="OldName")
    assert m is not None and m.name == "OldName"
    m = await repo.set_name(m, "NewName")
    assert m.name == "NewName"
    m2 = await repo.set_name(m, "NewName")
    assert m2.id == m.id and m2.name == "NewName"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_member(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), name="DelUser")
    assert m is not None
    ok = await repo.delete(m.id)
    assert ok is True
    not_ok = await repo.delete(m.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_multiple_anonymous_members_allowed(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    anon_members = [await repo.create(server_id=s.id, user_id=None, name=f"Anon{i}") for i in range(5)]
    assert all(m is not None for m in anon_members)
    assert all(m.user_id is None for m in anon_members if m is not None)
    ids = {m.id for m in anon_members if m is not None}
    assert len(ids) == len(anon_members)
    listed = await repo.list_for_server(s.id)
    assert ids.issubset({m.id for m in listed})


@pytest.mark.asyncio(loop_scope="session")
async def test_set_user_if_none_success(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    virtual = await repo.create(server_id=s.id, user_id=None, name="Virtual")
    assert virtual is not None and virtual.user_id is None
    new_user_id = uuid.uuid4()
    ok = await repo.set_user_if_none(virtual, new_user_id)
    assert ok is True
    assert virtual.user_id == new_user_id


@pytest.mark.asyncio(loop_scope="session")
async def test_set_user_if_none_conflict_existing_user(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    user_id = uuid.uuid4()
    existing = await repo.create(server_id=s.id, user_id=user_id, name="Existing")
    virtual = await repo.create(server_id=s.id, user_id=None, name="Virtual2")
    assert existing is not None and virtual is not None
    ok = await repo.set_user_if_none(virtual, user_id)
    assert ok is False
    assert virtual.user_id is None


@pytest.mark.asyncio(loop_scope="session")
async def test_set_user_if_none_already_has_user(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    user_id = uuid.uuid4()
    member = await repo.create(server_id=s.id, user_id=user_id, name="HasUser")
    assert member is not None and member.user_id == user_id
    new_user_id = uuid.uuid4()
    ok = await repo.set_user_if_none(member, new_user_id)
    assert ok is False
    assert member.user_id == user_id


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_user(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    user_id = uuid.uuid4()
    member = await repo.create(server_id=s.id, user_id=user_id, name="Removable")
    assert member is not None and member.user_id == user_id

    updated = await repo.remove_user(member)
    assert updated.id == member.id
    assert updated.user_id is None

    reloaded = await repo.get_by_id(member.id)
    assert reloaded is not None
    assert reloaded.user_id is None
