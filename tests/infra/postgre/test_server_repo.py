import uuid
import pytest

from src.infra.postgre.repo import ServerRepository
from src.infra.postgre import IntegrityForeignException


@pytest.mark.asyncio(loop_scope="session")
class TestServerRepository:
    async def test_create_and_get_server(self, async_session, factory):
        repo = ServerRepository(async_session)
        rs = await factory.create_role_set()
        rts = await factory.create_rating_set()
        icon_id = uuid.uuid4()
        banner_id = uuid.uuid4()
        s = await repo.create(name="Srv1", owner_id=uuid.uuid4(), public=False,
                              description="desc", icon_id=icon_id, banner_id=banner_id)
        assert s is not None
        assert s.name == "Srv1"
        assert s.public is False
        assert s.description == "desc"
        assert s.icon_id == icon_id
        assert s.banner_id == banner_id
        by_id = await repo.get(s.id)
        assert by_id is not None and by_id.id == s.id

    async def test_setters_update_fields(self, async_session, factory):
        repo = ServerRepository(async_session)
        s = await factory.create_server()
        assert s is not None
        s = await repo.set_name(s, "Srv2-Updated")
        assert s.name == "Srv2-Updated"
        s = await repo.set_description(s, "NewDesc")
        assert s.description == "NewDesc"
        s = await repo.set_public(s, True)
        assert s.public is True
        new_icon_id = uuid.uuid4()
        s = await repo.set_icon(s, new_icon_id)
        assert s.icon_id == new_icon_id
        new_banner_id = uuid.uuid4()
        s = await repo.set_banner(s, new_banner_id)
        assert s.banner_id == new_banner_id

    async def test_list_and_delete_server(self, async_session, factory):
        repo = ServerRepository(async_session)
        owner = uuid.uuid4()
        s1 = await factory.create_server(owner_id=owner, public=True)
        s2 = await factory.create_server(owner_id=owner, public=False)
        assert s1 is not None and s2 is not None

        by_owner = await repo.list_by_owner(owner)
        assert {s.id for s in by_owner} == {s1.id, s2.id}

        public_list = await repo.list_public()
        assert s1.id in {s.id for s in public_list}

        ok = await repo.delete(s2.id)
        assert ok is True
        not_ok = await repo.delete(s2.id)
        assert not_ok is False

    async def test_list_by_user_returns_active_servers(self, async_session, factory):
        repo = ServerRepository(async_session)
        user_id = uuid.uuid4()

        active_server = await factory.create_server(name="ActiveServer")
        inactive_server = await factory.create_server(name="InactiveServer")

        await factory.create_member(active_server.id, user_id=user_id)
        inactive_member = await factory.create_member(inactive_server.id, user_id=user_id)

        inactive_member.active = False
        await repo._session.flush()

        res = await repo.list_by_user(user_id)

        assert len(res) == 1
        assert res[0].id == active_server.id
