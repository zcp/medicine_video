"""
LiveCore Service - Custom Business Exceptions

This module contains all custom exceptions for the LiveCore Service,
used for business logic validation and error handling.
"""


class NotFoundException(Exception):
    """通用资源不存在异常（用于权限检查时返回404，隐藏资源存在性）"""
    pass


class RoomNotFoundException(Exception):
    """Raised when a room is not found in the database."""
    pass


class ActionForbiddenException(Exception):
    """Raised when an action is not permitted due to business logic."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ParentRoomNotFoundException(Exception):
    """Raised when the specified parent room does not exist."""
    pass


class SessionNotFoundException(Exception):
    """Raised when a session is not found in the database."""
    pass


class SessionActionForbiddenException(Exception):
    """Raised when an action on a session is not permitted."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# ==================== 专题功能相关异常 ====================

class TopicNotFoundException(Exception):
    """专题不存在异常"""
    pass


class CategoryNotFoundException(Exception):
    """分类不存在异常"""
    pass


class TopicPermissionDeniedException(Exception):
    """专题权限不足异常"""
    def __init__(self, action: str = "操作"):
        self.message = f"您没有权限进行此{action}"
        super().__init__(self.message)


class RoomAlreadyAssociatedException(Exception):
    """直播间已关联异常"""
    def __init__(self, room_id: str, category_id: str):
        self.message = "该直播间已关联到此分类"
        self.room_id = room_id
        self.category_id = category_id
        super().__init__(self.message)


# ==================== Tab 和留言功能相关异常（学院派）====================

class TabNotFoundException(Exception):
    """Tab 不存在"""
    pass


class MessageNotFoundException(Exception):
    """留言不存在"""
    pass


class PermissionDeniedException(Exception):
    """权限不足（由 Service 层检查并抛出）"""
    pass


class InvalidParameterException(Exception):
    """
    业务参数无效（由 Service 层检查并抛出）
    例如：内容包含非法 URL, content_type 与 content 不匹配
    """
    def __init__(self, message: str, code: int = 4001):
        self.message = message
        self.code = code  # 允许携带业务码
        super().__init__(self.message)


# ==================== CRUD 层异常（CRUD 层抛出, API 层捕获）====================

class DatabaseIntegrityException(Exception):
    """数据库完整性异常（如唯一键冲突）"""
    pass


class DatabaseOperationException(Exception):
    """数据库操作异常（通用）"""
    pass


# ==================== 内容管理模块相关异常 (Service 层抛出) ====================

class TagNotFoundException(Exception):
    """标签不存在"""
    pass


class CategoryNotFoundException(Exception):
    """分类不存在"""
    pass


class TagAlreadyExistsException(Exception):
    """标签名称已存在"""
    pass


class CategoryAlreadyExistsException(Exception):
    """分类名称已存在"""
    pass


class TagReferencedException(Exception):
    """标签被引用，无法删除"""
    def __init__(self, message: str, referenced_count: int):
        self.message = message
        self.referenced_count = referenced_count
        super().__init__(self.message)


class SessionTagNotFoundException(Exception):
    """场次-标签关联不存在"""
    pass


class InvalidTagSearchModeException(Exception):
    """无效的标签搜索模式"""
    pass

# app/exceptions.py
# 在文件末尾添加（约第150行后）

class ConflictException(Exception):
    """
    资源冲突异常（由 Service 层或 CRUD 层抛出）
    例如：品牌名称已存在、资源被引用无法删除
    """
    def __init__(self, message: str, code: int = 2003):
        self.message = message
        self.code = code  # 允许携带业务码
        super().__init__(self.message)