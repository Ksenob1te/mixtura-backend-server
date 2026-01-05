import uuid
from datetime import datetime, timedelta, timezone
import pytest

from src.infra.postgre.repo import RestrictionRepository, MemberRestrictionRepository
from src.infra.postgre import IntegrityForeignException


@pytest.mark.asyncio(loop_scope="session")
class TestMemberRestrictionRepository:

    async def test_create_and_get_member_restriction(self, async_session, factory):
        code_repo = RestrictionRepository(async_session)
        mr_repo = MemberRestrictionRepository(async_session)
        code = await code_repo.create("BAN")
        assert code is not None and code.code == "BAN"
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        creator = await factory.create_member(s.id, nickname="Creator")
        exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        mr = await mr_repo.create(m.id, code.id, "Rule violation", exp, creator_id=creator.id)
        assert mr is not None and mr.reason == "Rule violation"
        assert mr.creator_id == creator.id
        assert mr.creator is not None and mr.creator.id == creator.id
        fetched = await mr_repo.get_by_id(mr.id)
        assert fetched is not None and fetched.id == mr.id
        assert fetched.creator_id == creator.id

    async def test_create_member_restriction_unreal_member(self, async_session, factory):
        code_repo = RestrictionRepository(async_session)
        mr_repo = MemberRestrictionRepository(async_session)
        code = await code_repo.create("SUSPEND")
        assert code is not None and code.code == "SUSPEND"
        unreal_member_id = uuid.uuid4()
        s = await factory.create_server()
        creator = await factory.create_member(s.id, nickname="CreatorUnreal")
        with pytest.raises(IntegrityForeignException):
            await mr_repo.create(unreal_member_id,
                                 code.id, "No such member", datetime.now(timezone.utc) + timedelta(minutes=10),
                                 creator_id=creator.id)

    async def test_list_and_active(self, async_session, factory):
        code_repo = RestrictionRepository(async_session)
        mr_repo = MemberRestrictionRepository(async_session)
        code = await code_repo.create("MUTE")
        assert code is not None and code.code == "MUTE"
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        creator = await factory.create_member(s.id, nickname="Creator2")
        active = await mr_repo.create(m.id, code.id, "Spam", datetime.now(timezone.utc) + timedelta(minutes=20),
                                      creator_id=creator.id)
        expired = await mr_repo.create(m.id, code.id, "Old", datetime.now(timezone.utc) - timedelta(minutes=5),
                                       creator_id=creator.id)
        assert active is not None and expired is not None
        assert active.creator_id == creator.id and expired.creator_id == creator.id
        listed = await mr_repo.list_for_member(m.id)
        assert {r.id for r in listed} == {active.id, expired.id}
        active_list = await mr_repo.list_active_for_member(m.id)
        assert {r.id for r in active_list} == {active.id}

    async def test_setters(self, async_session, factory):
        code_repo = RestrictionRepository(async_session)
        mr_repo = MemberRestrictionRepository(async_session)
        c1 = await code_repo.create("CODE1")
        c2 = await code_repo.create("CODE2")
        s = await factory.create_server()
        m = await factory.create_member(s.id)
        creator = await factory.create_member(s.id, nickname="Creator3")
        assert c1 is not None and c2 is not None
        mr = await mr_repo.create(m.id, c1.id, "Initial", datetime.now(timezone.utc) + timedelta(minutes=5),
                                  creator_id=creator.id)
        assert mr is not None and mr.creator_id == creator.id
        mr = await mr_repo.set_reason(mr, "Updated")
        assert mr.reason == "Updated"
        new_exp = datetime.now(timezone.utc) + timedelta(hours=1)
        mr = await mr_repo.set_expiration(mr, new_exp)
        assert mr.expiration_date == new_exp
        mr = await mr_repo.set_code(mr, c2.id)
        assert mr.restriction_id == c2.id

