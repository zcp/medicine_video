"""
内容管理模块的 Pydantic Schemas
定义所有API输入和输出的数据模型
"""
from typing import List, Optional, Literal, TypeVar, Generic
from uuid import UUID
from datetime import datetime
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ============================================================================
# Tags Schemas
# ============================================================================

class TagBase(BaseModel):
    """标签基础Schema"""
    name: str = Field(..., min_length=1, max_length=80, description="标签名称")
    slug: Optional[str] = Field(None, max_length=100, description="URL友好标识符")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证标签名称"""
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError('标签名称不能包含特殊字符')
        return v

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """验证slug格式"""
        if v is not None:
            v = v.strip().lower()
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('slug只能包含小写字母、数字和连字符')
        return v


class TagCreate(TagBase):
    """创建标签请求Schema"""
    is_active: Optional[bool] = Field(True, description="是否启用")


class TagUpdate(BaseModel):
    """更新标签请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=80)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class TagItem(TagBase):
    """标签响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = Field(None, description="【V2】创建者 public_id")
    source: Optional[str] = Field(None, description="【V2】来源：admin=运营创建；user=用户 resolve 创建")


class TagListResponse(BaseModel):
    """标签列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[TagItem]
    timestamp: datetime


class TagResolveRequest(BaseModel):
    """解析或创建标签请求Schema（用户侧）"""
    name: str = Field(..., min_length=1, max_length=80, description="标签名（将 strip）")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("标签名称不能为空")
        if re.search(r'[<>\'";]', v):
            raise ValueError("标签名称不能包含特殊字符")
        return v


class TagResolveData(BaseModel):
    """解析或创建标签结果"""
    id: UUID
    name: str
    created: bool = Field(..., description="true=本次新建；false=命中已有")
    source: Optional[str] = Field(None, description="admin|user")


class TagResolveResponse(BaseModel):
    """解析或创建标签响应"""
    code: int = 200
    message: str = "success"
    data: TagResolveData
    timestamp: datetime


# ============================================================================
# Categories Schemas
# ============================================================================

class CategoryBase(BaseModel):
    """全局医学科室/专业方向分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="全局医学科室/专业方向分类名称")
    display_name: Optional[str] = Field(None, max_length=100, description="口语名（C端展示用）；NULL 回退 name")
    standard: bool = Field(True, description="标准科目标记：true=name 须命中名录标准名清单；false=扩展科目（如'其他'）")
    slug: Optional[str] = Field(None, max_length=120)
    icon: Optional[str] = Field(None, max_length=255, description="图标名称或URL")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError('分类名称不能包含特殊字符')
        return v


class CategoryCreate(CategoryBase):
    """创建分类请求Schema"""
    parent_id: Optional[UUID] = Field(None, description="父分类ID。NULL=一级分类，非NULL=二级分类")
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")


class CategoryUpdate(BaseModel):
    """更新分类请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    standard: Optional[bool] = None
    slug: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = Field(None, description="父分类ID。NULL=提升为一级分类")
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryItem(CategoryBase):
    """分类响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: Optional[UUID] = Field(None, description="父分类ID。NULL=一级分类")
    sort_order: int
    is_active: bool
    expert_count: int = Field(0, alias="expert_count", description="关联的专家数（管理端填充）")
    room_count: int = Field(0, alias="room_count", description="关联的直播间数（管理端填充）")
    created_at: datetime
    updated_at: datetime


class RoomCategoryItem(CategoryItem):
    """直播间分类响应Schema（含 is_primary 标记）"""
    is_primary: bool = Field(False, description="是否为主分类")


class CategoryListResponse(BaseModel):
    """分类列表响应Schema（公开接口，不分页）"""
    code: int = 200
    message: str = "success"
    data: List[CategoryItem]
    timestamp: datetime


class CategoryMigrateRequest(BaseModel):
    """分类引用迁移请求（阶段3 治理工具）"""
    target_category_id: UUID = Field(..., description="迁移目标分类ID（须存在且启用，且不在源分类子树内）")
    scope: Literal["experts", "departments", "rooms", "all"] = Field(
        "all", description="迁移范围：experts=仅专家 / departments=仅科室 / rooms=仅房间关联 / all=全部"
    )


class CategoryMergeRequest(BaseModel):
    """分类合并请求（阶段4 治理工具）"""
    source_id: UUID = Field(..., description="源分类ID（合并后软删）")
    target_id: UUID = Field(..., description="目标分类ID（须存在且启用，非'其他'，不在源子树内）")
    attach_children: bool = Field(False, description="子分类处置：false=挂到 target 下（默认）；true=提升为一级")
    dry_run: bool = Field(False, description="预览模式：只统计不落库")


# 通用分页数据Schema
T = TypeVar('T')


class PaginatedData(BaseModel, Generic[T]):
    """分页数据通用Schema"""
    total: int
    page: int
    size: int
    items: List[T]


class CategoryAdminListResponse(BaseModel):
    """分类列表响应Schema（Admin接口，分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[CategoryItem]
    timestamp: datetime


class TagAdminListResponse(BaseModel):
    """标签列表响应Schema（Admin接口，分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[TagItem]
    timestamp: datetime


# ============================================================================
# Session_Tags Schemas
# ============================================================================

class SessionTagsSetRequest(BaseModel):
    """为场次设置标签请求Schema"""
    tag_ids: List[UUID] = Field(
        ...,
        min_length=0,
        max_length=5,
        description="标签UUID列表（0～5；replace 传空列表表示清空）",
    )
    mode: Literal["replace", "append"] = Field(..., description="操作模式：replace=替换，append=追加")

    @field_validator('tag_ids')
    @classmethod
    def validate_tag_ids_unique(cls, v: List[UUID]) -> List[UUID]:
        """验证标签ID列表唯一性"""
        if len(v) != len(set(v)):
            raise ValueError('标签ID列表中存在重复项')
        return v


class TagBriefItem(BaseModel):
    """标签简要信息Schema（用于关联响应）"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class SessionTagsSetResponse(BaseModel):
    """场次标签设置响应Schema"""
    code: int = 200
    message: str = "success"
    data: dict  # {"session_id": "...", "mode": "replace", "tags": [...]}
    timestamp: datetime


class SessionTagsListResponse(BaseModel):
    """场次标签列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[TagItem]  # 使用 TagItem 而非 TagBriefItem
    timestamp: datetime


# ============================================================================
# Live_Room_Categories Schemas
# ============================================================================

class LiveRoomCategoriesSetRequest(BaseModel):
    """为直播间设置医学方向分类请求Schema；直播间分类以 live_room_categories 为唯一业务来源。"""
    category_ids: List[UUID] = Field(..., min_length=0, max_length=50, description="全局分类UUID列表；写入 live_room_categories，可为空表示清空关联")
    primary_category_id: Optional[UUID] = Field(None, description="主分类ID，必须在 category_ids 列表中。如果 category_ids 不为空，则此字段必填。")
    mode: Literal["replace", "append"] = Field(..., description="操作模式：replace=替换，append=追加")

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids_unique(cls, v: List[UUID]) -> List[UUID]:
        if len(v) != len(set(v)):
            raise ValueError("分类ID列表中存在重复项")
        return v

    @model_validator(mode='after')
    def validate_primary_category(self) -> 'LiveRoomCategoriesSetRequest':
        if self.category_ids and not self.primary_category_id:
            raise ValueError("当 category_ids 不为空时，必须指定 primary_category_id")
        if self.primary_category_id and self.primary_category_id not in self.category_ids:
            raise ValueError("primary_category_id 必须包含在 category_ids 列表中")
        return self


class LiveRoomCategoriesSetResponse(BaseModel):
    """直播间分类设置响应Schema"""
    code: int = 200
    message: str = "success"
    data: dict  # {"room_id": "...", "mode": "replace"|"append", "categories": [RoomCategoryItem]}
    timestamp: datetime


class LiveRoomCategoriesListResponse(BaseModel):
    """直播间分类列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[RoomCategoryItem]
    timestamp: datetime
