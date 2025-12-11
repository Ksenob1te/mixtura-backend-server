class DomainException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)

class NotAuthorizedException(DomainException):
    def __init__(self):
        super().__init__(
            status_code=401,
            message="Not authorized"
        )


class ExceedRetryLimitException(DomainException):
    def __init__(self):
        super().__init__(
            status_code=409,
            message="Exceed retry limit"
        )


class MigrationException(DomainException):
    def __init__(self):
        super().__init__(
            status_code=409,
            message="Unable to perform migration"
        )


class NotFoundException(DomainException):
    def __init__(self, message: str):
        super().__init__(
            status_code=404,
            message=message
        )


class InternalLogicException(DomainException):
    def __init__(self, message: str):
        super().__init__(
            status_code=500,
            message=message
        )


class ForbiddenException(DomainException):
    def __init__(self, message: str):
        super().__init__(
            status_code=403,
            message=message
        )
