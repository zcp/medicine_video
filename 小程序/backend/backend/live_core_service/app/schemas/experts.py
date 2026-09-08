"""
专家模块 Pydantic Schemas 定义
包含专家信息、专家关注、场次专家关联的 Schema
"""

from pydantic import BaseModel, ConfigDict, Field
import uuid
import datetime
from typing import Optional, List
from enum import Enum


# ============== 枚举定义 ==============

class SessionExpertRole(str, Enum):
    """专家角色枚举"""
    MAIN_SPEAKER = "主讲"
    HOST = "主持"
    GUEST = "嘉宾"


# ============== 专家信息 Schemas ==============

class ExpertBase(BaseModel):
    """专家基础Schema"""
    name: str = Field(..., min_length=1, max_length=120, description="专家姓名")
    title: Optional[str] = Field(None, max_length=120, description="职称")
    hospital: Optional[str] = Field(None, max_length=200, description="所属医院")
    department: Optional[str] = Field(None, max_length=120, description="科室（过渡兼容；优先词表回填）")
    department_id: Optional[uuid.UUID] = Field(None, description="标准化科室ID（expert_departments）")
    category_id: Optional[uuid.UUID] = Field(None, description="专家主专业分类ID（categories）")
    expertise_areas: Optional[str] = Field(None, description="擅长领域")
    bio: Optional[str] = Field(None, max_length=10000, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")


class ExpertCreate(ExpertBase):
    """创建专家请求Schema"""
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID（可选）")
    is_featured: Optional[bool] = Field(False, description="是否首页推荐")
    is_active: Optional[bool] = Field(True, description="是否启用（false 表示软删除/下架）")
    sort_order: Optional[int] = Field(0, ge=0, description="排序顺序")
    contact_info: Optional[dict] = Field(None, description="联系方式JSONB")


class ExpertUpdate(BaseModel):
    """更新专家请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID（可选）")
    name: Optional[str] = Field(None, min_length=1, max_length=120, description="专家姓名")
    title: Optional[str] = Field(None, max_length=120, description="职称")
    hospital: Optional[str] = Field(None, max_length=200, description="所属医院")
    department: Optional[str] = Field(None, max_length=120, description="科室（过渡兼容）")
    department_id: Optional[uuid.UUID] = Field(None, description="标准化科室ID")
    category_id: Optional[uuid.UUID] = Field(None, description="专家主专业分类ID")
    expertise_areas: Optional[str] = Field(None, description="擅长领域")
    bio: Optional[str] = Field(None, max_length=1000, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")
    is_featured: Optional[bool] = Field(None, description="是否首页推荐")
    is_active: Optional[bool] = Field(None, description="是否启用（false 表示软删除/下架）")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")


class ExpertItem(ExpertBase):
    """专家响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = Field(None, description="科室名称（词表）")
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = Field(None, description="分类名称")
    is_featured: bool
    is_active: bool
    sort_order: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class FeaturedExpertItem(BaseModel):
    """首页推荐专家简要Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True


# ============== 专家关注 Schemas ==============

class ExpertFollowRequest(BaseModel):
    """关注专家请求Schema"""
    expert_id: uuid.UUID = Field(..., description="专家ID")


class ExpertFollowResponse(BaseModel):
    """关注专家响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("关注成功", description="响应消息")
    data: dict
    timestamp: datetime.datetime


class FollowedExpertItem(BaseModel):
    """关注的专家响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    expert_id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
    subscribed_at: datetime.datetime
    live_status: Optional[dict] = Field(None, description="直播状态信息")


class FollowedExpertsResponse(BaseModel):
    """关注列表响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: List[FollowedExpertItem] = Field(default_factory=list, max_length=1000, description="关注的专家列表")
    timestamp: datetime.datetime


# ============== 批量导入 Schemas ==============

class BatchImportFailedRow(BaseModel):
    """批量导入失败行"""
    row: int = Field(..., description="行号")
    data: dict = Field(default_factory=dict, description="行数据摘要")
    error: str = Field(..., description="错误信息")


class BatchImportSkippedRow(BaseModel):
    """批量导入跳过行"""
    row: int = Field(..., description="行号")
    data: dict = Field(default_factory=dict, description="行数据摘要")
    reason: str = Field(..., description="跳过原因")


class BatchImportExpertsResult(BaseModel):
    """批量导入专家结果"""
    total: int = Field(..., description="总行数")
    success: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    skipped: int = Field(..., description="跳过数")
    created_expert_ids: List[uuid.UUID] = Field(default_factory=list, description="创建的专家ID列表")
    failed_rows: List[BatchImportFailedRow] = Field(default_factory=list, description="失败行详情")
    skipped_rows: List[BatchImportSkippedRow] = Field(default_factory=list, description="跳过行详情")
    processing_time: float = Field(..., description="处理耗时（秒）")


# ============== 场次专家关联 Schemas ==============

class SessionExpertItem(BaseModel):
    """场次专家关联信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = Field(None, description="是否启用")
    role: Optional[str] = Field(None, description="专家角色（主讲、主持、嘉宾）")
    sort_order: Optional[int] = Field(None, description="显示顺序")
    expertise_areas: Optional[str] = Field(None, description="擅长领域，逗号分隔或JSON")
    bio: Optional[str] = Field(None, description="个人简介")

