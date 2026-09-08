"""Content Safety business exceptions"""


class ContentSafetyBlockedException(Exception):

    def __init__(self, message: str, *, code: int = 2005):
        self.message = message
        self.code = code
        super().__init__(message)


class ContentSafetyServiceException(Exception):

    def __init__(self, message: str = "Service unavailable", *, code: int = 2004):
        self.message = message
        self.code = code
        super().__init__(message)


class ContentSafetyValidationError(Exception):

    def __init__(self, message: str, *, code: int = 4001):
        self.message = message
        self.code = code
        super().__init__(message)
