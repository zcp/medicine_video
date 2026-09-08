"""
专题聚合功能的 Pydantic Schema

本模块包含专题聚合功能所需的所有 Pydantic 模型：
- Topic 相关 Schema
- TopicCategory 相关 Schema
- TopicCategoryRoom 相关 Schema
- 聚合响应 Schema
"""

# 标准库导入
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid

# 第三方库导入
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ==================== 枚举定义部分 ====================

class TopicStatus(str, Enum):
    """专题状态枚举"""
    DRAFT = "draft"          # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"    # 已归档


# ==================== Topic Schema 部分 ====================

class TopicBase(BaseModel):
    """
    专题基础 Schema
    
    包含专题的核心业务字段，用于创建和更新操作的基类。
    """
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="专题标题，必填，长度 1-100 字符"
    )
    description: Optional[str] = Field(
        None, 
        description="专题描述，可选，支持 Markdown 格式"
    )
    # banner_url 已移除，通过 POST /api/v1/topics/{topic_id}/banner 接口上传

    status: TopicStatus = Field(
        default=TopicStatus.DRAFT, 
        description="专题状态，默认为草稿"
    )


class TopicCreate(TopicBase):
    """
    创建专题请求 Schema
    
    用于 POST /api/v1/topics 接口的请求体。
    user_id 从 JWT Token 中提取，不在请求体中。
    banner_url 默认为 NULL，需通过 POST /api/v1/topics/{topic_id}/banner 接口上传。
    """
    pass  # 继承 TopicBase 的所有字段


class TopicUpdate(BaseModel):
    """
    更新专题请求 Schema
    
    用于 PATCH /api/v1/topics/{topic_id} 接口的请求体。
    所有字段都是可选的，允许部分更新（PATCH 语义）。
    """
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        description="专题标题"
    )
    description: Optional[str] = Field(
        None,
        description="专题描述"
    )
    # banner_url 已移除，通过 POST /api/v1/topics/{topic_id}/banner 接口更新

    status: Optional[TopicStatus] = Field(
        None,
        description="专题状态"
    )


class TopicInDB(TopicBase):
    """
    数据库中的专题 Schema
    
    包含所有数据库字段，包括系统生成的 id 和时间戳。
    支持从 SQLAlchemy ORM 对象转换。
    """
    id: uuid.UUID = Field(..., description="专题唯一标识")
    user_id: uuid.UUID = Field(..., description="创建者用户ID")
    banner_url: Optional[str] = Field(  # ✅ 新增：数据库字段，默认为null
        None,
        description="横幅图URL，通过上传接口设置，默认为null"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class TopicResponse(TopicInDB):
    """
    专题响应 Schema
    
    用于 API 响应，返回专题的完整信息。
    继承 TopicInDB 的所有字段。
    """
    pass


# ==================== TopicCategory Schema 部分 ====================

class CategoryBase(BaseModel):
    """
    分类基础 Schema
    
    包含分类的核心业务字段。
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="分类名称，必填，长度 1-50 字符"
    )
    sort_order: int = Field(
        default=0, 
        ge=0, 
        description="排序顺序，默认 0，数值越小越靠前"
    )


class CategoryCreate(CategoryBase):
    """
    创建分类请求 Schema
    
    用于 POST /api/v1/topics/{topic_id}/categories 接口的请求体。
    topic_id 从路径参数获取，不在请求体中。
    """
    pass


class CategoryUpdate(BaseModel):
    """
    更新分类请求 Schema
    
    用于 PATCH /api/v1/topic-categories/{category_id} 接口的请求体。
    所有字段都是可选的，允许部分更新。
    """
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="分类名称"
    )
    sort_order: Optional[int] = Field(
        None, 
        ge=0,
        description="排序顺序"
    )


class CategoryInDB(CategoryBase):
    """
    数据库中的分类 Schema
    
    包含所有数据库字段，包括外键和时间戳。
    支持从 SQLAlchemy ORM 对象转换。
    """
    id: uuid.UUID = Field(..., description="分类唯一标识")
    topic_id: uuid.UUID = Field(..., description="所属专题ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(CategoryInDB):
    """
    分类响应 Schema
    
    用于 API 响应，返回分类的完整信息。
    """
    pass


# ==================== TopicCategoryRoom 关联管理 Schema 部分 ====================

class RoomAssociation(BaseModel):
    """
    单个直播间关联 Schema
    
    用于批量添加直播间到分类时的单个直播间数据结构。
    """
    room_id: uuid.UUID = Field(..., description="直播间唯一标识")
    sort_order: int = Field(
        default=0, 
        ge=0, 
        description="在分类下的排序顺序，默认 0"
    )


class AddRoomsRequest(BaseModel):
    """
    添加直播间到分类请求 Schema
    
    用于 POST /api/v1/topic-categories/{category_id}/rooms 接口的请求体。
    支持批量添加 1-50 个直播间，自动验证 room_id 唯一性。
    """
    rooms: List[RoomAssociation] = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="要添加的直播间列表，最少 1 个，最多 50 个"
    )
    
    @field_validator('rooms')
    @classmethod
    def validate_unique_room_ids(cls, v):
        """
        验证 room_id 唯一性
        
        确保同一个请求中的 room_id 不重复。
        """
        room_ids = [r.room_id for r in v]
        if len(room_ids) != len(set(room_ids)):
            raise ValueError("room_id 不能重复")
        return v


class UpdateRoomSortRequest(BaseModel):
    """
    更新直播间排序请求 Schema
    
    用于 PATCH /api/v1/topic-categories/{category_id}/rooms/sort 接口的请求体。
    支持批量更新 1-100 个直播间的排序顺序。
    """
    rooms: List[RoomAssociation] = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="要更新排序的直播间列表"
    )


class RemoveRoomsRequest(BaseModel):
    """
    移除直播间请求 Schema
    
    用于 DELETE /api/v1/topic-categories/{category_id}/rooms 接口的请求体。
    支持批量移除 1-50 个直播间。
    """
    room_ids: List[uuid.UUID] = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="要移除的直播间ID列表，最少 1 个，最多 50 个"
    )


# ==================== 聚合响应 Schema 部分 ====================

class RoomInCategory(BaseModel):
    """
    分类下的直播间 Schema（用于聚合页面）
    
    用于专题详情页的直播间展示，包含直播状态和热度信息。
    """
    id: uuid.UUID = Field(..., description="直播间唯一标识")
    title: str = Field(..., description="直播间标题")
    cover_url: Optional[str] = Field(None, description="直播间封面图 URL")
    live_status: str = Field(
        ..., 
        description='直播状态: "scheduled"(预约), "live"(直播中), "finished"(已结束)'
    )
    start_time: Optional[datetime] = Field(None, description="最新场次开始时间")
    heat: int = Field(
        default=0, 
        ge=0, 
        description="热度值，根据观看、点赞等数据计算"
    )
    
    model_config = ConfigDict(from_attributes=True)


class CategoryWithRooms(BaseModel):
    """
    包含直播间列表的分类 Schema
    
    用于专题详情页的分类展示，包含该分类下的所有直播间。
    """
    id: uuid.UUID = Field(..., description="分类唯一标识")
    name: str = Field(..., description="分类名称")
    sort_order: int = Field(..., description="分类排序顺序")
    rooms: List[RoomInCategory] = Field(
        default_factory=list,
        description="该分类下的直播间列表"
    )
    
    model_config = ConfigDict(from_attributes=True)


class TopicDetailResponse(TopicInDB):
    """
    专题详情响应 Schema（包含层级化数据）
    
    用于 GET /api/v1/topics/{topic_id} 接口的响应。
    返回完整的层级化数据结构：专题 → 分类 → 直播间。
    """
    categories: List[CategoryWithRooms] = Field(
        default_factory=list,
        description="专题下的所有分类及其直播间"
    )


# ==================== 辅助 Schema 部分 ====================

class BatchStatusRequest(BaseModel):
    """
    批量查询状态请求 Schema
    
    用于批量查询多个直播间的状态信息。
    """
    room_ids: List[uuid.UUID] = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="要查询的直播间ID列表，最少 1 个，最多 100 个"
    )


class RoomStatusResponse(BaseModel):
    """
    直播间状态响应 Schema
    
    用于返回单个直播间的实时状态信息。
    """
    room_id: uuid.UUID = Field(..., description="直播间唯一标识")
    live_status: str = Field(
        ..., 
        description='直播状态: "scheduled", "live", "finished"'
    )
    current_session_id: Optional[uuid.UUID] = Field(
        None, 
        description="当前场次ID，如果没有进行中的场次则为 null"
    )
    viewer_count: int = Field(
        default=0, 
        ge=0, 
        description="当前观看人数，仅在直播中时有效"
    )

