"""内容安全业务异常"""


class ContentSafetyBlockedException(Exception):
    """内容命中 block 规则，拒绝写入"""

    def __init__(self, message: str, *, code: int = 2005):
        self.message = message
        self.code = code
        super().__init__(message)


class ContentSafetyServiceException(Exception):
    """内容安全服务异常，发布型写入默认拒绝"""

    def __init__(self, message: str = "内容安全服务暂不可用", *, code: int = 2004):
        self.message = message
        self.code = code
        super().__init__(message)


class ContentSafetyValidationError(Exception):
    """管理端规则变更参数校验失败"""

    def __init__(self, message: str, *, code: int = 4001):
        self.message = message
        self.code = code
        super().__init__(message)
