"""
品牌模块的 Pydantic Schemas

本模块包含品牌模块所需的所有 Pydantic Schema 模型，用于API数据验证和序列化。
"""
import uuid
import datetime
import re
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ==================== 品牌管理 Schemas ====================

class BrandBase(BaseModel):
    """品牌基础Schema"""
    name: str = Field(..., min_length=1, max_length=150, description="品牌名称")
    slug: Optional[str] = Field(None, max_length=150, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, max_length=512, description="品牌Logo URL")
    description: Optional[str] = Field(None, description="品牌描述")
    website_url: Optional[str] = Field(None, max_length=255, description="品牌官网")



class BrandCreate(BrandBase):
    """创建品牌请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否激活")

    @field_validator('website_url')
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式；空字符串视为未填，归一为 None"""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r'^https?://', v):
            raise ValueError('网站URL必须以http://或https://开头')
        return v
class BrandUpdate(BaseModel):
    """更新品牌请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="品牌名称")
    slug: Optional[str] = Field(None, max_length=150, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, max_length=512, description="品牌Logo URL")
    description: Optional[str] = Field(None, description="品牌描述")
    website_url: Optional[str] = Field(None, max_length=255, description="品牌官网")
    sort_order: Optional[int] = Field(None, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否激活")

    @field_validator('website_url')
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式；空字符串视为未填，归一为 None"""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r'^https?://', v):
            raise ValueError('网站URL必须以http://或https://开头')
        return v
class BrandItem(BrandBase):
    """品牌响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="品牌ID")
    sort_order: int = Field(..., description="排序权重")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime.datetime = Field(..., description="创建时间")
    updated_at: datetime.datetime = Field(..., description="更新时间")


# ==================== 品牌内容响应 Schemas ====================

class TopicBriefItem(BaseModel):
    """专题简要信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="专题ID")
    title: str = Field(..., description="专题标题")
    banner_url: Optional[str] = Field(None, description="专题横幅图URL")


class BrandContentData(BaseModel):
    """品牌内容数据Schema"""
    brand_info: BrandItem = Field(..., description="品牌信息")
    associated_topics: List[TopicBriefItem] = Field(
        default_factory=list, 
        max_length=1000, 
        description="关联的专题列表"
    )


class BrandContentResponse(BaseModel):
    """品牌内容响应Schema"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: BrandContentData = Field(..., description="响应数据")
    timestamp: datetime.datetime = Field(..., description="响应时间戳")


# ==================== 品牌-专题关联 Schemas ====================

class BrandTopicBindIn(BaseModel):
    """绑定品牌专题请求Schema"""
    topic_ids: List[uuid.UUID] = Field(
        default_factory=list, 
        max_length=100, 
        description="要绑定的专题ID列表"
    )


class TopicBrandItem(BaseModel):
    """专题品牌展示项Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="品牌ID")
    name: str = Field(..., description="品牌名称")
    slug: Optional[str] = Field(None, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, description="品牌Logo URL")
    sort_order: int = Field(0, description="排序权重")


class BrandTopicBindOut(BaseModel):
    """绑定品牌专题响应Schema"""
    brand_id: uuid.UUID = Field(..., description="品牌ID")
    topic_ids: List[uuid.UUID] = Field(
        ..., 
        max_length=100, 
        description="绑定的专题ID列表"
    )
    updated_at: datetime.datetime = Field(..., description="更新时间")


# ==================== 品牌-直播间关联 Schemas（V1.1新增）====================

class BrandRoomBindIn(BaseModel):
    """直播间绑定品牌请求Schema"""
    brand_ids: List[uuid.UUID] = Field(
        default_factory=list, 
        max_length=100, 
        description="要绑定的品牌ID列表"
    )


class RoomBrandItem(BaseModel):
    """直播间品牌Tab展示项Schema（Room Page专用）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="品牌ID")
    name: str = Field(..., description="品牌名称")
    slug: Optional[str] = Field(None, description="URL友好标识符")
    logo_url: Optional[str] = Field(None, description="品牌Logo URL")
    website_url: Optional[str] = Field(None, description="品牌官网")
    sort_order: int = Field(0, description="排序权重")


class BrandRoomBindOut(BaseModel):
    """直播间绑定品牌响应Schema"""
    room_id: uuid.UUID = Field(..., description="直播间ID")
    brand_ids: List[uuid.UUID] = Field(
        ..., 
        max_length=100, 
        description="绑定的品牌ID列表"
    )
    updated_at: datetime.datetime = Field(..., description="更新时间")
