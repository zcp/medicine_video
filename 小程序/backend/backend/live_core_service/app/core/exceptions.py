"""
LiveCore Service - Core Exceptions

This module contains core exceptions for the LiveCore Service,
specifically for the CRUD layer and other core components.
"""

class DatabaseIntegrityException(Exception):
    """数据库完整性错误（如唯一键冲突）"""
    def __init__(self, message: str = "数据库完整性冲突"):
        self.message = message
        super().__init__(self.message)

class DatabaseOperationException(Exception):
    """数据库操作错误"""
    def __init__(self, message: str = "数据库操作失败"):
        self.message = message
        super().__init__(self.message)

