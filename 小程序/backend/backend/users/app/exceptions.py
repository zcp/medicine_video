"""
自定义异常类定义 - 用户功能服务
为实现清晰的业务逻辑和错误处理分离而定义的异常类
"""


class BaseAppException(Exception):
    """应用程序基础异常类"""
    
    def __init__(self, message: str = "应用程序错误"):
        self.message = message
        super().__init__(self.message)


class InvalidTokenException(BaseAppException):
    """无效令牌异常"""
    
    def __init__(self, message: str = "认证令牌无效或已过期"):
        super().__init__(message)


class InvalidCredentialsException(BaseAppException):
    """无效凭证异常"""
    
    def __init__(self, message: str = "用户名或密码错误"):
        super().__init__(message)


class ValidationError(BaseAppException):
    """参数验证异常"""
    
    def __init__(self, field: str = None, message: str = "参数验证失败"):
        self.field = field
        if field:
            message = f"{field}: {message}"
        super().__init__(message)
