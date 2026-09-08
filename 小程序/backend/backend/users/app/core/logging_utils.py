"""
日志脱敏工具模块

提供日志中敏感信息的脱敏功能，防止数据库密码、JWT密钥、Authing密钥等敏感信息泄漏。
"""
import logging
import re
from typing import Union


def sanitize_log_message(message: Union[str, Exception]) -> str:
    """
    脱敏日志消息，移除或掩码敏感信息
    
    Args:
        message: 原始日志消息（字符串或异常对象）
    
    Returns:
        脱敏后的日志消息
    """
    if isinstance(message, Exception):
        message = str(message)
    elif not isinstance(message, str):
        message = str(message)
    
    # 1. 数据库连接URL脱敏
    # 匹配 postgres://user:password@host:port/db 或 postgresql+asyncpg://user:password@host:port/db
    message = re.sub(
        r"(postgres(?:ql)?(?:\+asyncpg)?://[^:]+:)([^@]+)(@[^\s]+)",
        r"\1***REDACTED***\3",
        message,
        flags=re.IGNORECASE
    )
    
    # 2. JWT密钥脱敏
    # 匹配 JWT_SECRET_KEY=xxxx 或 "JWT_SECRET_KEY": "xxxx"
    message = re.sub(
        r'(JWT_SECRET_KEY["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)',
        r'\1***REDACTED***',
        message,
        flags=re.IGNORECASE
    )
    
    # 3. Authing相关密钥脱敏
    # 匹配 USER_POOL_SECRET=xxxx 或 "USER_POOL_SECRET": "xxxx"
    message = re.sub(
        r'(USER_POOL_SECRET["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)',
        r'\1***REDACTED***',
        message,
        flags=re.IGNORECASE
    )
    
    # 匹配 VITE_CLIENT_ID=xxxx（通常不算敏感，但为了一致性也脱敏）
    message = re.sub(
        r'(VITE_CLIENT_ID["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)',
        r'\1***REDACTED***',
        message,
        flags=re.IGNORECASE
    )
    
    # 4. 通用密码字段脱敏
    # 匹配 password=xxxx 或 "password": "xxxx" 或 POSTGRES_PASSWORD=xxxx
    message = re.sub(
        r'(\b(?:password|passwd|pwd|POSTGRES_PASSWORD)["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)',
        r'\1***REDACTED***',
        message,
        flags=re.IGNORECASE
    )
    
    # 5. Redis密码脱敏（如果有）
    message = re.sub(
        r'(REDIS_PASSWORD["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)',
        r'\1***REDACTED***',
        message,
        flags=re.IGNORECASE
    )
    
    return message


class SanitizedFormatter(logging.Formatter):
    """
    自定义日志格式化器，自动脱敏敏感信息
    
    使用此格式化器替代默认的 logging.Formatter，可确保所有日志输出都经过脱敏处理。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录，并对消息内容进行脱敏
        
        Args:
            record: 日志记录对象
        
        Returns:
            格式化且脱敏后的日志消息
        """
        # 脱敏消息主体
        if record.msg:
            record.msg = sanitize_log_message(record.msg)
        
        # 脱敏参数（如果有）
        if record.args:
            sanitized_args = tuple(
                sanitize_log_message(arg) if isinstance(arg, (str, Exception)) else arg
                for arg in record.args
            )
            record.args = sanitized_args
        
        # 脱敏异常信息
        if record.exc_info:
            # exc_info是一个元组 (type, value, traceback)
            # 我们主要关注value（异常实例）
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_value:
                # 创建一个新的异常实例，消息已脱敏
                sanitized_message = sanitize_log_message(exc_value)
                # 注意：我们不能直接修改异常对象，但可以在格式化时替换消息
                # 这里我们通过修改record的exc_text来实现
                record.exc_text = sanitized_message
        
        # 调用父类的format方法完成最终格式化
        return super().format(record)


def setup_sanitized_logging(
    level: int = logging.INFO,
    format_string: str = "%(levelname)s:%(name)s:%(filename)s:%(lineno)d %(message)s"
) -> None:
    """
    配置全局日志系统使用脱敏格式化器
    
    Args:
        level: 日志级别（默认INFO）
        format_string: 日志格式字符串
    
    示例:
        >>> setup_sanitized_logging()
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("数据库连接: postgresql://user:secret_password@localhost/db")
        # 输出: INFO:__main__:example.py:10 数据库连接: postgresql://user:***REDACTED***@localhost/db
    """
    # 创建脱敏格式化器
    formatter = SanitizedFormatter(format_string)
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 移除现有的handlers（避免重复）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建并配置新的控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # 添加handler到根日志器
    root_logger.addHandler(console_handler)
    
    # 禁用uvicorn的访问日志（可选，避免重复）
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True


# 如果直接运行此模块，执行测试
if __name__ == "__main__":
    # 配置脱敏日志
    setup_sanitized_logging()
    
    # 测试用例
    logger = logging.getLogger(__name__)
    
    print("=" * 80)
    print("测试日志脱敏功能")
    print("=" * 80)
    
    # 测试1: 数据库URL脱敏
    logger.info("测试1 - 数据库连接: postgresql://user:secret_password@localhost:5432/db")
    
    # 测试2: JWT密钥脱敏
    logger.info("测试2 - JWT配置: JWT_SECRET_KEY=my-super-secret-jwt-key-123456")
    
    # 测试3: Authing密钥脱敏
    logger.info('测试3 - Authing配置: {"USER_POOL_SECRET": "authing-secret-key-789"}')
    
    # 测试4: 通用密码脱敏
    logger.info("测试4 - 用户密码: password=user123456")
    
    # 测试5: 异常消息脱敏
    try:
        raise Exception("连接失败: postgresql://admin:admin123@db.example.com/prod")
    except Exception as e:
        logger.error("测试5 - 异常处理", exc_info=True)
    
    print("=" * 80)
    print("脱敏测试完成")
    print("=" * 80)

