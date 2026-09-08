"""
内容管理模块的 Pydantic Schemas
定义所有API输入和输出的数据模型
"""
from typing import List, Optional, Literal, TypeVar, Generic
from uuid import UUID
from datetime import datetime
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator


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
    source: Optional[str] = Field(None, description="【V2】admin|user")


class TagListResponse(BaseModel):
    """标签列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[TagItem]
    timestamp: datetime


class TagResolveRequest(BaseModel):
    """解析或创建标签请求（用户侧）"""
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
    """分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
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
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")
    parent_id: Optional[UUID] = Field(None, description="【V2新增】父分类ID（NULL=一级分类）")


class CategoryUpdate(BaseModel):
    """更新分类请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    parent_id: Optional[UUID] = Field(None, description="【V2新增】父分类ID")


class CategoryItem(CategoryBase):
    """分类响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sort_order: int
    is_active: bool
    parent_id: Optional[UUID] = None  # 【V2新增】父分类ID
    children: Optional[List["CategoryItem"]] = None  # 【V2新增】子分类列表（仅一级分类时填充）
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    """分类列表响应Schema（公开接口，不分页）"""
    code: int = 200
    message: str = "success"
    data: List[CategoryItem]
    timestamp: datetime


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
    """为直播间设置分类请求Schema"""
    category_ids: List[UUID] = Field(..., min_length=0, max_length=50, description="分类UUID列表，可为空表示清空关联")
    mode: Literal["replace", "append"] = Field(..., description="操作模式：replace=替换，append=追加")
    primary_category_id: Optional[UUID] = Field(None, description="主分类ID；不传则默认列表首个")

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids_unique(cls, v: List[UUID]) -> List[UUID]:
        if len(v) != len(set(v)):
            raise ValueError("分类ID列表中存在重复项")
        return v


class LiveRoomCategoriesSetResponse(BaseModel):
    """直播间分类设置响应Schema"""
    code: int = 200
    message: str = "success"
    data: dict  # {"room_id": "...", "mode": "replace"|"append", "categories": [CategoryItem]}
    timestamp: datetime


class LiveRoomCategoriesListResponse(BaseModel):
    """直播间分类列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[CategoryItem]
    timestamp: datetime
