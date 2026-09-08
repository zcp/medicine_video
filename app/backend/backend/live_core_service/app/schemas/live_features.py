"""
直播间 Tab 和留言功能的 Pydantic Schema (学院派 ENUM 版)
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum


# ==================== 枚举类型定义 ====================
# 必须与 models/live_features.py 中的 ENUM 完全一致

class LiveRoomMessageUserRole(str, Enum):
    """留言用户角色枚举"""
    REGULAR = 'REGULAR'
    MODERATOR = 'MODERATOR'
    ADMIN = 'ADMIN'
    SUPERADMIN = 'SUPERADMIN'


class LiveRoomTabContentType(str, Enum):
    """Tab内容类型枚举"""
    TEXT = 'text'
    IMAGE = 'image'
    MIXED = 'mixed'


# ==================== LiveRoomTab Schema 部分 ====================

class LiveRoomTabBase(BaseModel):
    """
    Tab 基础 Schema
    
    包含 Tab 的核心业务字段
    """
    tab_key: str = Field(
        ..., 
        max_length=64, 
        description="系统级 key，用于前端逻辑判断"
    )
    title: str = Field(
        ..., 
        max_length=128, 
        description="展示名称"
    )
    
    # [学院派] 字段类型为 ENUM
    content_type: LiveRoomTabContentType = Field(
        ..., 
        description="内容类型, 'text', 'image' 或 'mixed'"
    )
    
    text_content: Optional[str] = Field(None, description="文本内容 (当 content_type 为 'text' 或 'mixed' 时)")
    image_url: Optional[str] = Field(None, description="图片 URL (当 content_type 为 'image' 或 'mixed' 时)")
    
    sort_order: int = Field(
        default=0, 
        ge=0, 
        description="排序顺序, 数值越小越靠前"
    )
    is_active: bool = Field(
        default=True, 
        description="是否激活, 是否在前端展示"
    )


class LiveRoomTabCreate(LiveRoomTabBase):
    """
    Tab 创建请求 Schema
    
    用于 POST /api/v1/admin/rooms/{room_id}/tabs
    room_id 来自路径参数，不包含在请求体中
    """
    pass


class LiveRoomTabUpdate(BaseModel):
    """
    Tab 更新请求 Schema
    
    用于 PATCH /api/v1/admin/tabs/{tab_id}
    所有字段可选，支持部分更新
    """
    tab_key: Optional[str] = Field(None, max_length=64, description="系统级 key")
    title: Optional[str] = Field(None, max_length=128, description="展示名称")
    content_type: Optional[LiveRoomTabContentType] = Field(None, description="内容类型")
    text_content: Optional[str] = Field(None, description="文本内容")
    image_url: Optional[str] = Field(None, description="图片 URL")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否激活")


class LiveRoomTabInDB(LiveRoomTabBase):
    """
    Tab 数据库完整记录 Schema
    
    用于从 ORM 对象转换
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="Tab ID")
    room_id: uuid.UUID = Field(..., description="直播间 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class LiveRoomTabResponse(LiveRoomTabInDB):
    """
    Tab API 响应 Schema
    
    用于 GET /api/v1/admin/rooms/{room_id}/tabs
    返回 Tab 完整信息
    """
    pass


# ==================== LiveRoomMessage Schema 部分 ====================

class LiveRoomMessageBase(BaseModel):
    """
    留言基础 Schema
    
    包含留言的核心业务字段
    """
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="留言内容"
    )


class LiveRoomMessageCreate(LiveRoomMessageBase):
    """
    留言创建请求 Schema
    
    用于 POST /api/v1/rooms/{room_id}/messages
    room_id 来自路径参数，user_id 和 user_role 由后端自动填充
    """
    pass


class LiveRoomMessageCreateInternal(BaseModel):
    """
    [学院派] 留言创建内部 Schema
    
    仅供 Service 层 -> CRUD 层使用
    包含 Service 层传入的所有必需字段（room_id, user_id, user_role 等）
    禁止在 API 路由中直接暴露给外部
    """
    room_id: uuid.UUID = Field(..., description="直播间 ID")
    session_id: Optional[uuid.UUID] = Field(None, description="会话 ID")
    user_id: uuid.UUID = Field(..., description="用户 ID")
    user_role: LiveRoomMessageUserRole = Field(..., description="用户角色")
    content: str = Field(..., min_length=1, max_length=500, description="留言内容")
    extra: Optional[Dict[str, Any]] = Field(
        default=None,
        description="扩展字段，例如包含 user_display_name（用户展示名称/昵称）等信息"
    )


class LiveRoomMessageUpdate(BaseModel):
    """
    留言更新请求 Schema
    
    用于后台管理功能（非 V3.3 API 必须）
    """
    content: Optional[str] = Field(None, max_length=500, description="留言内容")
    is_deleted: Optional[bool] = Field(None, description="是否删除")


class LiveRoomMessageInDB(LiveRoomMessageBase):
    """
    留言数据库完整记录 Schema
    
    用于从 ORM 对象转换
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="留言 ID")
    room_id: uuid.UUID = Field(..., description="直播间 ID")
    session_id: Optional[uuid.UUID] = Field(None, description="会话 ID")
    user_id: uuid.UUID = Field(..., description="用户 ID")
    user_role: LiveRoomMessageUserRole = Field(..., description="用户角色")
    created_at: datetime = Field(..., description="创建时间")
    is_deleted: bool = Field(..., description="是否删除")
    extra: Optional[Dict[str, Any]] = Field(None, description="扩展字段")


class MessageUserInfo(BaseModel):
    """留言用户展示信息"""
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="用户头像URL")


class LiveRoomMessagePostResponse(BaseModel):
    """
    留言创建响应 Schema
    
    用于 POST /api/v1/rooms/{room_id}/messages 响应
    严格遵循 V3.3 API 3.3.1 响应体
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="留言 ID")
    room_id: uuid.UUID = Field(..., description="直播间 ID")
    user_id: uuid.UUID = Field(..., description="用户 ID")
    user_role: LiveRoomMessageUserRole = Field(..., description="用户角色")
    content: str = Field(..., description="留言内容")
    created_at: datetime = Field(..., description="创建时间")
    user_display_name: Optional[str] = Field(
        default=None,
        description="用户展示名称（昵称），用于前端展示"
    )


class LiveRoomMessageListResponseItem(BaseModel):
    """
    留言列表单项 Schema
    
    用于 GET /api/v1/rooms/{room_id}/messages 列表中的单项
    严格遵循 V3.3 API 3.3.2 items 字段
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="留言 ID")
    user_role: LiveRoomMessageUserRole = Field(..., description="用户角色")
    content: str = Field(..., description="留言内容")
    created_at: datetime = Field(..., description="创建时间")
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")
    user_display_name: Optional[str] = Field(
        default=None,
        description="用户展示名称（昵称），用于前端展示"
    )
    user: Optional[MessageUserInfo] = Field(
        default=None,
        description="用户展示信息（昵称/头像），读时优先个人中心当前值"
    )


class PaginatedLiveRoomMessageResponse(BaseModel):
    """
    留言列表分页响应 Schema
    
    用于 GET /api/v1/rooms/{room_id}/messages 完整响应
    """
    total: int = Field(..., description="总留言数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[LiveRoomMessageListResponseItem] = Field(..., description="留言列表")


# ==================== PR 3 新增：管理端留言 Schema ====================


class AdminMessageQueryParams(BaseModel):
    """管理员留言查询参数"""
    room_id: Optional[uuid.UUID] = Field(None, description="按直播间筛选")
    user_id: Optional[str] = Field(None, description="按用户筛选")
    keyword: Optional[str] = Field(None, description="按内容关键词搜索")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    message_ids: List[uuid.UUID] = Field(..., min_length=1, description="留言ID列表")


class AdminMessageItem(BaseModel):
    """管理端留言列表单项"""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID = Field(..., description="留言ID")
    room_id: uuid.UUID = Field(..., description="直播间ID")
    user_id: uuid.UUID = Field(..., description="用户ID")
    user_role: LiveRoomMessageUserRole = Field(..., description="用户角色")
    content: str = Field(..., description="留言内容")
    created_at: datetime = Field(..., description="创建时间")
    extra: Optional[Dict[str, Any]] = Field(None, description="扩展字段")
    user_display_name: Optional[str] = Field(None, description="用户展示昵称（昵称优先，账号名兜底）")
    avatar_url: Optional[str] = Field(None, description="用户头像URL")
    room_title: Optional[str] = Field(None, description="直播间标题")


class AdminMessagePageResult(BaseModel):
    """管理端留言分页结果"""
    items: List[AdminMessageItem] = Field(..., description="留言列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    filter_summary: Dict[str, Any] = Field(default_factory=dict, description="筛选摘要")

