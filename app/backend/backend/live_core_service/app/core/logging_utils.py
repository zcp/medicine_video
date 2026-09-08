"""
日志脱敏工具模块

提供日志消息脱敏功能，防止敏感信息泄露
"""

import re
import logging


def sanitize_log_message(message: str) -> str:
    """
    对日志消息进行脱敏处理
    
    Args:
        message: 原始日志消息
        
    Returns:
        脱敏后的日志消息
    """
    # 移除数据库连接URL中的密码
    message = re.sub(
        r'postgresql[+a-z]*://([^:]+):([^@]+)@',
        r'postgresql://\1:***@',
        message,
        flags=re.IGNORECASE
    )
    
    # 移除JWT Token
    message = re.sub(
        r'Bearer\s+([A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+)',
        r'Bearer ***',
        message
    )
    
    # 移除环境变量中的敏感值
    for env_key in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']:
        message = re.sub(
            rf'{env_key}["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            rf'{env_key}="***"',
            message,
            flags=re.IGNORECASE
        )
    
    # 移除Authorization头
    message = re.sub(
        r'Authorization["\']?\s*:\s*["\']?([^"\'\n]+)',
        r'Authorization: "***"',
        message,
        flags=re.IGNORECASE
    )
    
    return message


class SanitizedFormatter(logging.Formatter):
    """
    脱敏日志格式化器
    
    自动对所有日志消息进行脱敏处理
    """
    
    def format(self, record):
        """格式化日志记录，并进行脱敏"""
        # 先进行脱敏
        record.msg = sanitize_log_message(str(record.msg))
        
        # 如果有args参数，也需要脱敏
        if record.args:
            record.args = tuple(
                sanitize_log_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        # 调用父类的格式化方法
        return super().format(record)


def setup_sanitized_logging(level=logging.INFO):
    """
    配置使用脱敏格式化器的日志系统
    
    Args:
        level: 日志级别
    """
    # 创建格式化器
    formatter = SanitizedFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日志处理器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger

