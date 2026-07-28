import logging

from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.invite import (
    GetInviteByKeyRequest,
    GetInviteListRequest,
    GetUserRestrictionRequest,
    InviteAdminResponse,
    InviteCreateRequest,
    InviteKeyResponse,
    RevokeInviteRequest,
    UseInviteRequest,
)
from src.app.rabbit.models.member import MemberResponse
from src.dependency import AccessControlServiceDependency, InviteServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="invite.get_by_key")
async def get_invite_info(
    data: GetInviteByKeyRequest, invite_service: InviteServiceDependency
) -> ResponseMessage[InviteKeyResponse]:
    invite_info = await invite_service.get_invite_info(data.key)
    return ResponseMessage(
        status=200, message=InviteKeyResponse.model_validate(invite_info)
    )

@router.subscriber(queue="invite.get_restriction")
async def get_invite_restriction(
    data: GetUserRestrictionRequest, access_control_service: AccessControlServiceDependency
) -> ResponseMessage[int]:
    restriction_mask = await access_control_service.get_restriction_mask(data.server_id, data.user_id)
    return ResponseMessage(status=200, message=restriction_mask)


@router.subscriber(queue="invite.use")
async def use_invite(
    data: UseInviteRequest, invite_service: InviteServiceDependency
) -> ResponseMessage[MemberResponse]:
    member = await invite_service.use_invite(
        data.key, data.user_id, data.nickname, data.restriction_mask
    )
    return ResponseMessage(status=200, message=MemberResponse.model_validate(member))


@router.subscriber(queue="invite.list")
async def list_invites(
    data: GetInviteListRequest, invite_service: InviteServiceDependency
) -> ResponseMessage[list[InviteAdminResponse]]:
    members = await invite_service.list_invites(
        data.access_data.server_id, data.access_data.permission_mask
    )
    ta = TypeAdapter(list[InviteAdminResponse])
    return ResponseMessage(status=200, message=ta.validate_python(members))


@router.subscriber(queue="invite.create")
async def create_invite(
    data: InviteCreateRequest, invite_service: InviteServiceDependency
) -> ResponseMessage[InviteAdminResponse]:
    invite = await invite_service.create_invite(
        data.access_data.server_id,
        data.use_limit,
        data.access_data.member_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(
        status=200, message=InviteAdminResponse.model_validate(invite)
    )


@router.subscriber(queue="invite.revoke")
async def revoke_invite(
    data: RevokeInviteRequest, invite_service: InviteServiceDependency
) -> ResponseMessage[StatusResponse]:
    await invite_service.revoke_invite(
        data.access_data.server_id, data.invite_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())
