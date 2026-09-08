"""
专家科室受控词表 — Pydantic Schemas 定义
"""
import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ExpertDepartmentCreate(BaseModel):
    """管理员创建科室"""
    name: str = Field(..., min_length=1, max_length=120, description="标准科室名称")
    category_id: uuid.UUID = Field(..., description="所属主分类ID")
    synonyms: List[str] = Field(default_factory=list, description="同义词列表")
    is_verified: Optional[bool] = Field(False, description="是否已审核")
    source: str = Field("admin_api", description="创建来源，管理员API创建默认为admin_api")


class ExpertDepartmentUpdate(BaseModel):
    """管理员更新科室（全部字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=120, description="标准科室名称")
    category_id: Optional[uuid.UUID] = Field(None, description="所属主分类ID")
    synonyms: Optional[List[str]] = Field(None, description="同义词列表")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_verified: Optional[bool] = Field(None, description="是否已审核")


class ExpertDepartmentItem(BaseModel):
    """科室列表/详情响应"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category_id: uuid.UUID
    category_name: Optional[str] = Field(None, description="分类名称（JOIN填充）")
    synonyms: List[str] = Field(default_factory=list, description="同义词列表")
    is_active: bool
    is_verified: bool
    source: Optional[str] = Field(None, description="创建来源")
    created_by: Optional[uuid.UUID] = Field(None, description="创建人 user_id")
    expert_count: int = Field(0, description="关联的专家数")
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ExpertDepartmentBriefItem(BaseModel):
    """科室简要信息（用于下拉选择器）"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category_id: uuid.UUID
    category_name: Optional[str] = None


class BatchVerifyRequest(BaseModel):
    """批量审核科室请求"""
    department_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=200, description="待审核的科室ID列表")
    verified: bool = Field(True, description="审核状态：true=通过，false=驳回")


class ExpertDepartmentListResponse(BaseModel):
    """科室分页列表响应"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: dict = Field(..., description="{ items: [...], total: N, page: N, size: N }")
    timestamp: datetime.datetime
