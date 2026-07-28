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


class BadRequestException(DomainException):
    def __init__(self, message: str):
        super().__init__(
            status_code=400,
            message=message
        )


class RepositoryException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class IntegrityForeignException(RepositoryException):
    def __init__(self, message: str = "SQLSTATE_FK_VIOLATION"):
        super().__init__(message=message)


class IntegrityUniqueException(RepositoryException):
    def __init__(self, message: str = "SQLSTATE_UNIQUE_VIOLATION"):
        super().__init__(message=message)


class IntegrityUnknownException(RepositoryException):
    def __init__(self, message: str = "Unable to perform task due to integrity error"):
        super().__init__(message=message)


class InviteUniqueException(RepositoryException):
    def __init__(self, message: str = "Unable to generate unique invite code"):
        super().__init__(message=message)
