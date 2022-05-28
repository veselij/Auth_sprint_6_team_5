class RetryExceptionError(Exception):
    """Exception triggers function retry."""

    def __init__(self, messsage) -> None:
        self.messsage = messsage
        super().__init__(self.messsage)


class ObjectDoesNotExistError(Exception):
    "Exception triggered when object doesn not exist in database."


class LoginPasswordError(Exception):
    "Exception triggered when user login or password wrong."


class ConflictError(Exception):
    "Integrety conflict in database."


class InvalidTokenError(Exception):
    "Invalid token error."


class TotpNotSyncError(Exception):
    "Totp not ready for use, sync first."
