"""
专题功能相关异常类

这些异常类需要追加到现有的 app/exceptions.py 文件中。
"""


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


class RoomNotFoundException(Exception):
    """直播间不存在异常"""
    pass

