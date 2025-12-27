import logging
from faststream.rabbit import RabbitRouter

from ..models.invites.response import InviteAdminResponse, InviteKeyResponse

from ..models.invites.request import GetInviteByKeyRequest, GetInviteListRequest, InviteCreateRequest, RevokeInviteRequest, UseInviteRequest

from ..models.response import ResponseMessage, StatusResponse



router = RabbitRouter()
logger = logging.getLogger(__name__)

@router.subscriber(queue="invite.get_by_key")
async def get_invite_info(data: GetInviteByKeyRequest) -> ResponseMessage[InviteKeyResponse]:
    ...

@router.subscriber(queue="invite.use")
async def use_invite(data: UseInviteRequest) -> ResponseMessage[StatusResponse]:
    ...

@router.subscriber(queue="invite.list")
async def list_invites(data: GetInviteListRequest) -> ResponseMessage[list[InviteAdminResponse]]:
    ...

@router.subscriber(queue="invite.create")
async def create_invite(data: InviteCreateRequest) -> ResponseMessage[InviteAdminResponse]:
    ...

@router.subscriber(queue="invite.revoke")
async def revoke_invite(data: RevokeInviteRequest) -> ResponseMessage[StatusResponse]:
    ...
