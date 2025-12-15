class RepositoryException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class IntegrityForeignException(RepositoryException):
    def __init__(self, message: str = "SQLSTATE_FK_VIOLATION"):
        super().__init__(
            message=message
        )


class IntegrityUniqueException(RepositoryException):
    def __init__(self, message: str = "SQLSTATE_UNIQUE_VIOLATION"):
        super().__init__(
            message=message
        )


class IntegrityUnknownException(RepositoryException):
    def __init__(self, message: str = "Unable to perform task due to integrity error"):
        super().__init__(
            message=message
        )


class InviteUniqueException(RepositoryException):
    def __init__(self, message: str = "Unable to generate unique invite code"):
        super().__init__(
            message=message
        )
