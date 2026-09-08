"""
直播间 Tab 和留言功能的 Pydantic Schema (学院派 ENUM 版)
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Tuple
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
        description="扩展字段，例如包含 user_display_name / avatar_url（用户展示快照）等信息"
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
    """留言关联的用户展示信息（读时优先个人中心当前值；extra 快照仅兜底）。"""
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="用户头像 URL")


def build_message_user_snapshot(
    extra: Optional[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[MessageUserInfo]]:
    """从 extra 组装 user_display_name 与嵌套 user（写时快照 / 降级兜底）。"""
    if not isinstance(extra, dict):
        return None, None
    display_name = extra.get("user_display_name")
    avatar_url = extra.get("avatar_url")
    if not display_name and not avatar_url:
        return None, None
    return display_name, MessageUserInfo(nickname=display_name, avatar_url=avatar_url)


def apply_live_user_profile(
    display_name: Optional[str],
    user_info: Optional[MessageUserInfo],
    profile: Optional[Dict[str, Optional[str]]],
) -> Tuple[Optional[str], Optional[MessageUserInfo]]:
    """用 users.batch 当前资料覆盖展示；无 profile 时保持原值（快照兜底）。"""
    if not profile:
        return display_name, user_info
    nickname = profile.get("nickname") or profile.get("username") or display_name
    # batch 命中则头像以个人中心为准（可为 null）
    avatar_url = profile.get("avatar_url")
    if not nickname and avatar_url is None:
        return display_name, user_info
    return nickname, MessageUserInfo(nickname=nickname, avatar_url=avatar_url)


DEACTIVATED_DISPLAY_NAME = "账号已注销"


def apply_deactivated_display(
    display_name: Optional[str],
    user_info: Optional[MessageUserInfo],
    is_deactivated: bool,
) -> Tuple[Optional[str], Optional[MessageUserInfo]]:
    """16-D3：作者已注销时覆盖展示名与头像；正文/extra 不改。"""
    if not is_deactivated:
        return display_name, user_info
    return DEACTIVATED_DISPLAY_NAME, MessageUserInfo(
        nickname=DEACTIVATED_DISPLAY_NAME,
        avatar_url=None,
    )


def resolve_message_user_display(
    extra: Optional[Dict[str, Any]],
    profile: Optional[Dict[str, Optional[str]]],
    is_deactivated: bool,
) -> Tuple[Optional[str], Optional[MessageUserInfo]]:
    """组装顺序：extra 快照 → 个人中心当前资料 → 注销占位。"""
    display_name, user_info = build_message_user_snapshot(extra)
    display_name, user_info = apply_live_user_profile(display_name, user_info, profile)
    return apply_deactivated_display(display_name, user_info, is_deactivated)


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
        description="用户展示名称（昵称），用于前端展示（兼容旧字段）"
    )
    user: Optional[MessageUserInfo] = Field(
        default=None,
        description="用户展示信息（昵称、头像），对齐设计文档"
    )


class LiveRoomMessageListResponseItem(BaseModel):
    """
    留言列表单项 Schema
    
    用于 GET /api/v1/rooms/{room_id}/messages 列表中的单项
    严格遵循 V3.3 API 3.3.2 items 字段
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="留言 ID")
    # 16-D3：缓存命中后仍需按 user_id 查已注销标记；C 端「我的留言」也依赖此字段
    user_id: uuid.UUID = Field(..., description="作者 public_id")
    user_role: LiveRoomMessageUserRole = Field(..., description="用户角色")
    content: str = Field(..., description="留言内容")
    created_at: datetime = Field(..., description="创建时间")
    user_display_name: Optional[str] = Field(
        default=None,
        description="用户展示名称（昵称），用于前端展示（兼容旧字段）"
    )
    user: Optional[MessageUserInfo] = Field(
        default=None,
        description="用户展示信息（昵称、头像），对齐设计文档"
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


# ==================== Admin 管理端留言 Schema ====================

class AdminMessageQueryParams(BaseModel):
    """管理员全局留言查询参数"""
    room_id: Optional[uuid.UUID] = Field(None, description="按直播间筛选")
    user_id: Optional[uuid.UUID] = Field(None, description="按用户筛选")
    keyword: Optional[str] = Field(None, max_length=100, description="留言内容关键词模糊搜索")
    start_time: Optional[datetime] = Field(None, description="起始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class BatchDeleteRequest(BaseModel):
    """批量删除留言请求"""
    message_ids: List[uuid.UUID] = Field(
        ..., min_length=1, max_length=200, description="待删除留言ID列表"
    )


class AdminMessageItem(LiveRoomMessageListResponseItem):
    """管理端留言条目"""
    room_id: uuid.UUID = Field(..., description="直播间 ID")
    user_id: uuid.UUID = Field(..., description="用户 ID")
    room_title: Optional[str] = Field(None, description="直播间标题")
    user_nickname: Optional[str] = Field(None, description="用户昵称")
    user_role_snapshot: Optional[str] = Field(None, description="留言时的用户角色快照")


class AdminMessagePageResult(BaseModel):
    """管理端留言分页响应"""
    items: List[AdminMessageItem]
    total: int
    page: int
    page_size: int
    filter_summary: Optional[Dict[str, Any]] = Field(None, description="筛选条件摘要")

