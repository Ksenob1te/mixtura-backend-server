import uuid
import pytest
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException

from src.infra.postgre.repo import MemberRepository


@pytest.mark.asyncio(loop_scope="session")
class TestMemberRepository:

    async def test_create_and_get_member(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), nickname="Alice")
        assert m is not None and m.nickname == "Alice"
        by_id = await repo.get_by_id(m.id)
        assert by_id is not None and by_id.id == m.id
        assert await repo.get_by_id(uuid.uuid4()) is None

    async def test_create_member_unreal_server(self, async_session):
        repo = MemberRepository(async_session)
        unreal_server_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(server_id=unreal_server_id, user_id=uuid.uuid4(), nickname="Bob")

    async def test_create_member_unreal_role(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        unreal_role_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(server_id=s.id, user_id=uuid.uuid4(), nickname="Charlie", server_role_id=unreal_role_id)

    async def test_duplicate_user_membership_raises(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        user_id = uuid.uuid4()
        _ = await repo.create(server_id=s.id, user_id=user_id, nickname="UserOne")
        with pytest.raises(IntegrityUniqueException):
            await repo.create(server_id=s.id, user_id=user_id, nickname="UserOneDup")

    async def test_list_and_list_active(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        members = [await repo.create(server_id=s.id, user_id=uuid.uuid4(), nickname=f"U{i}") for i in range(3)]
        listed = await repo.list_for_server(s.id)
        assert {m.id for m in listed} == {m.id for m in members if m is not None}
        active_listed = await repo.list_active_for_server(s.id)
        assert {m.id for m in active_listed} == {m.id for m in members if m is not None}

    async def test_activation_and_deactivation(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), nickname="ActUser")
        assert m is not None and m.active is True
        m = await repo.deactivate(m)
        assert m.active is False
        m2 = await repo.deactivate(m)
        assert m2.id == m.id and m2.active is False
        m = await repo.activate(m)
        assert m.active is True
        m2 = await repo.activate(m)
        assert m2.id == m.id and m2.active is True

    async def test_set_role(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        role = await factory.create_server_role(s.id)
        m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), nickname="RoleUser")
        assert m is not None
        m = await repo.set_role(m, role.id)
        assert m.server_role_id == role.id
        m2 = await repo.set_role(m, role.id)
        assert m2.id == m.id and m2.server_role_id == role.id
        m = await repo.set_role(m, None)
        assert m.server_role_id is None

    async def test_set_name(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), nickname="OldName")
        assert m is not None and m.nickname == "OldName"
        m = await repo.set_nickname(m, "NewName")
        assert m.nickname == "NewName"
        m2 = await repo.set_nickname(m, "NewName")
        assert m2.id == m.id and m2.nickname == "NewName"

    async def test_delete_member(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        m = await repo.create(server_id=s.id, user_id=uuid.uuid4(), nickname="DelUser")
        assert m is not None
        ok = await repo.delete(m.id)
        assert ok is True
        not_ok = await repo.delete(m.id)
        assert not_ok is False

    async def test_multiple_anonymous_members_allowed(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        anon_members = [await repo.create(server_id=s.id, user_id=None, nickname=f"Anon{i}") for i in range(5)]
        assert all(m is not None for m in anon_members)
        assert all(m.user_id is None for m in anon_members if m is not None)
        ids = {m.id for m in anon_members if m is not None}
        assert len(ids) == len(anon_members)
        listed = await repo.list_for_server(s.id)
        assert ids.issubset({m.id for m in listed})

    async def test_set_user_if_none_success(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        virtual = await repo.create(server_id=s.id, user_id=None, nickname="Virtual")
        assert virtual is not None and virtual.user_id is None
        new_user_id = uuid.uuid4()
        ok = await repo.set_user_if_none(virtual, new_user_id)
        assert ok is True
        assert virtual.user_id == new_user_id

    async def test_set_user_if_none_conflict_existing_user(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        user_id = uuid.uuid4()
        existing = await repo.create(server_id=s.id, user_id=user_id, nickname="Existing")
        virtual = await repo.create(server_id=s.id, user_id=None, nickname="Virtual2")
        assert existing is not None and virtual is not None
        ok = await repo.set_user_if_none(virtual, user_id)
        assert ok is False
        assert virtual.user_id is None

    async def test_set_user_if_none_already_has_user(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        user_id = uuid.uuid4()
        member = await repo.create(server_id=s.id, user_id=user_id, nickname="HasUser")
        assert member is not None and member.user_id == user_id
        new_user_id = uuid.uuid4()
        ok = await repo.set_user_if_none(member, new_user_id)
        assert ok is False
        assert member.user_id == user_id

    async def test_remove_user(self, async_session, factory):
        repo = MemberRepository(async_session)
        s = await factory.create_server()
        user_id = uuid.uuid4()
        member = await repo.create(server_id=s.id, user_id=user_id, nickname="Removable")
        assert member is not None and member.user_id == user_id

        updated = await repo.remove_user(member)
        assert updated.id == member.id
        assert updated.user_id is None

        reloaded = await repo.get_by_id(member.id)
        assert reloaded is not None
        assert reloaded.user_id is None

