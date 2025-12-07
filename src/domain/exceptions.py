from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT, HTTP_400_BAD_REQUEST, \
    HTTP_500_INTERNAL_SERVER_ERROR, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND


class NotAuthorizedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Not authorized"
            }
        )


class ExceedRetryLimitException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "message": "Exceed retry limit"
            }
        )


class MigrationException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "message": "Unable to perform migration"
            }
        )


class NotFoundException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": message
            }
        )


class InternalLogicException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": message
            }
        )


class ForbiddenException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "message": message
            }
        )
