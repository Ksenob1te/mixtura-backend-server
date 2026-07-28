import logging

from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.member import (
    AccessResponse,
    AddMemberRestrictionRequest,
    GetMemberByUserRequest,
    GetMemberListRequest,
    GetMemberRestrictionsRequest,
    JoinServerRequest,
    KickMemberRequest,
    MemberGetInfoRequest,
    MemberMigrationRequest,
    MemberPermissionRequest,
    MemberPermissionResponse,
    MemberResponse,
    MemberRestrictionResponse,
    MemberUpdateRequest,
    RemoveMemberRestrictionRequest,
    RestrictionResponse,
    VirtualMemberCreateRequest,
)
from src.app.rabbit.models.role import PermissionResponse
from src.core.exceptions import NotFoundException
from src.dependency import (
    AccessControlServiceDependency,
    CoreServiceDependency,
    MemberServiceDependency,
)

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="member.by_user")
async def get_member_by_user(
    data: GetMemberByUserRequest, access_service: AccessControlServiceDependency
) -> ResponseMessage[AccessResponse]:
    member = await access_service.get_member(data.server_id, data.user_id)
    if member is None:
        permission_mask: int = 0
        restriction_mask = 0
    else:
        permission_mask = await access_service.get_permission_mask(
            data.server_id, data.user_id
        )
        restriction_mask = await access_service.get_restriction_mask(
            data.server_id, data.user_id
        )

    member_model = MemberResponse.model_validate(member) if member else None
    return ResponseMessage(
        status=200,
        message=AccessResponse(
            member=member_model,
            permission_mask=permission_mask,
            restriction_mask=restriction_mask,
        ),
    )


@router.subscriber(queue="member.list")
async def list_members(
    data: GetMemberListRequest, member_service: MemberServiceDependency
) -> ResponseMessage[list[MemberResponse]]:
    members = await member_service.list_members(
        data.access_data.server_id, data.pagination.page, data.nickname_filter, data.pagination.page_size
    )
    ta = TypeAdapter(list[MemberResponse])
    return ResponseMessage(status=200, message=ta.validate_python(members))


@router.subscriber(queue="member.join")
async def join_server(
    data: JoinServerRequest, member_service: MemberServiceDependency
) -> ResponseMessage[MemberResponse]:
    member = await member_service.join_server(
        data.server_id, data.user_id, data.nickname, data.restriction_mask
    )
    return ResponseMessage(status=200, message=MemberResponse.model_validate(member))


@router.subscriber(queue="member.virtual.create")
async def create_virtual(
    data: VirtualMemberCreateRequest, member_service: MemberServiceDependency
) -> ResponseMessage[MemberResponse]:
    member = await member_service.create_virtual(
        data.access_data.server_id, data.nickname, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=MemberResponse.model_validate(member))


@router.subscriber(queue="member.get")
async def get_member(
    data: MemberGetInfoRequest, member_service: MemberServiceDependency
) -> ResponseMessage[MemberResponse]:
    member = await member_service.get_member(data.target_member_id)
    return ResponseMessage(status=200, message=MemberResponse.model_validate(member))


@router.subscriber(queue="member.permissions.get")
async def get_member_permissions(
    data: MemberPermissionRequest, access_service: AccessControlServiceDependency
) -> ResponseMessage[MemberPermissionResponse]:
    if data.access_data.member_id is None:
        raise NotFoundException("Member not found")
    permissions = await access_service.get_permissions(
        data.access_data.server_id, data.access_data.member_id
    )
    restrictions = await access_service.get_restrictions(
        data.access_data.server_id, data.access_data.member_id
    )
    return ResponseMessage(
        status=200,
        message=MemberPermissionResponse(
            permissions=[PermissionResponse.model_validate(p) for p in permissions],
            restrictions=[MemberRestrictionResponse.model_validate(r) for r in restrictions],
        ),
    )


@router.subscriber(queue="member.update")
async def update_member(
    data: MemberUpdateRequest, member_service: MemberServiceDependency
) -> ResponseMessage[MemberResponse]:
    if data.access_data.member_id is None:
        raise NotFoundException("Member not found")
    member = await member_service.update_member(
        data.access_data.server_id,
        data.access_data.member_id,
        data.access_data.permission_mask,
        data.access_data.restriction_mask,
        data.target_member_id,
        data.name,
        data.server_role_id,
    )
    return ResponseMessage(status=200, message=MemberResponse.model_validate(member))


@router.subscriber(queue="member.kick")
async def delete_member(
    data: KickMemberRequest, member_service: MemberServiceDependency
) -> ResponseMessage[StatusResponse]:
    if data.access_data.member_id is None:
        raise NotFoundException("Member not found")
    await member_service.kick_member(
        data.access_data.member_id,
        data.access_data.server_id,
        data.target_member_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber(queue="member.virtual.migrate")
async def migrate_member(
    data: MemberMigrationRequest, member_service: MemberServiceDependency
) -> ResponseMessage[MemberResponse]:
    member = await member_service.migrate_member(
        data.access_data.server_id,
        data.origin_member_id,
        data.target_member_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=MemberResponse.model_validate(member))


@router.subscriber(queue="server.global.restrictions")
async def get_global_restrictions(
    core_service: CoreServiceDependency,
) -> ResponseMessage[list[RestrictionResponse]]:
    restrictions = await core_service.get_global_restrictions()
    ta = TypeAdapter(list[RestrictionResponse])
    return ResponseMessage(status=200, message=ta.validate_python(restrictions))


@router.subscriber(queue="member.restriction.list")
async def list_restrictions(
    data: GetMemberRestrictionsRequest, access_service: AccessControlServiceDependency, member_service: MemberServiceDependency
) -> ResponseMessage[list[MemberRestrictionResponse]]:
    member = await member_service.get_member(data.target_member_id)
    if member is None or member.user_id is None:
        return ResponseMessage(status=200, message=[])
    restrictions = await access_service.get_restrictions(
        data.access_data.server_id, member.user_id
    )
    ta = TypeAdapter(list[MemberRestrictionResponse])
    return ResponseMessage(status=200, message=ta.validate_python(restrictions))


@router.subscriber(queue="member.restriction.add")
async def add_restriction(
    data: AddMemberRestrictionRequest, access_service: AccessControlServiceDependency
) -> ResponseMessage[MemberRestrictionResponse]:
    if data.access_data.member_id is None:
        raise NotFoundException("Member not found")
    restriction = await access_service.add_restriction(
        data.target_member_id,
        data.access_data.member_id,
        data.access_data.server_id,
        data.access_data.permission_mask,
        data.reason,
        data.expiration_date,
        data.restriction_id,
    )
    return ResponseMessage(status=200, message=MemberRestrictionResponse.model_validate(restriction))


@router.subscriber(queue="member.restriction.remove")
async def remove_restriction(
    data: RemoveMemberRestrictionRequest, access_service: AccessControlServiceDependency
) -> ResponseMessage[StatusResponse]:
    if data.access_data.member_id is None:
        raise NotFoundException("Member not found")
    await access_service.remove_restriction(
        data.target_member_id,
        data.access_data.member_id,
        data.access_data.server_id,
        data.member_restriction_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=StatusResponse())
