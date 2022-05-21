class RetryExceptionError(Exception):
    """Exception triggers function retry."""

    def __init__(self, messsage) -> None:
        self.messsage = messsage
        super().__init__(self.messsage)
