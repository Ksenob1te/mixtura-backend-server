import logging
from faststream.rabbit import RabbitRouter

from ..models.response import ResponseMessage, StatusResponse

from ..models.member.request import GetMemberByUserRequest, GetMemberListRequest, GetMemberRestrictionsRequest, JoinServerRequest, KickMemberRequest, MemberGetInfoRequest, AddMemberRestrictionRequest, MemberUpdateRequest, MemberMigrationRequest, RemoveMemberRestrictionRequest, VirtualMemberCreateRequest

from ..models.member.response import AccessResponse, MemberResponse, MemberRestrictionResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="member.by_user")
async def get_member_by_user(data: GetMemberByUserRequest) -> ResponseMessage[AccessResponse]:
    ...

@router.subscriber(queue="member.list")
async def list_members(data: GetMemberListRequest) -> ResponseMessage[list[MemberResponse]]:
    ...

@router.subscriber(queue="member.join")
async def join_server(data: JoinServerRequest) -> ResponseMessage[MemberResponse]:
    ...

@router.subscriber(queue="member.virtual.create")
async def create_virtual(data: VirtualMemberCreateRequest) -> ResponseMessage[MemberResponse]:
    ...

@router.subscriber(queue="member.get")
async def get_member(data: MemberGetInfoRequest) -> ResponseMessage[MemberResponse]:
    ...

@router.subscriber(queue="member.update")
async def update_member(data: MemberUpdateRequest) -> ResponseMessage[MemberResponse]:
    ...

@router.subscriber(queue="member.kick")
async def delete_member(data: KickMemberRequest) -> ResponseMessage[StatusResponse]:
    ...

@router.subscriber(queue="member.virtual.migrate")
async def migrate_member(data: MemberMigrationRequest) -> ResponseMessage[MemberResponse]:
    ...

@router.subscriber(queue="member.restriction.list")
async def list_restrictions(data: GetMemberRestrictionsRequest) -> ResponseMessage[list[MemberRestrictionResponse]]:
    ...

@router.subscriber(queue="member.restriction.add")
async def add_restriction(data: AddMemberRestrictionRequest) -> ResponseMessage[MemberRestrictionResponse]:
    ...

@router.subscriber(queue="member.restriction.remove")
async def remove_restriction(data: RemoveMemberRestrictionRequest) -> ResponseMessage[StatusResponse]:
    ...
