"""
直播间与公众号关联模块的 Pydantic Schemas
定义公众号管理、直播间-公众号关联及按公众号查房间等 API 的请求/响应模型
"""
from typing import List, Optional, Literal
from uuid import UUID
from datetime import datetime
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.content_management import PaginatedData


# ============================================================================
# Official_Accounts Schemas
# ============================================================================

class OfficialAccountBase(BaseModel):
    """公众号基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="公众号名称")
    slug: Optional[str] = Field(None, max_length=120)
    app_id: Optional[str] = Field(None, max_length=255, description="预留：外部 app_id")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError("公众号名称不能包含特殊字符")
        return v


class OfficialAccountCreate(OfficialAccountBase):
    """创建公众号请求 Schema"""
    is_active: Optional[bool] = Field(True, description="是否启用")


class OfficialAccountUpdate(BaseModel):
    """更新公众号请求 Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    app_id: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class OfficialAccountItem(OfficialAccountBase):
    """公众号响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OfficialAccountAdminListResponse(BaseModel):
    """公众号管理端列表响应（分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[OfficialAccountItem]
    timestamp: datetime


# ============================================================================
# Live_Room_Official_Accounts Schemas
# ============================================================================

class LiveRoomOfficialAccountsSetRequest(BaseModel):
    """直播间公众号批量设置请求 Schema"""
    account_ids: List[UUID] = Field(..., min_length=0, max_length=50, description="公众号 ID 列表，可为空表示清空关联")
    mode: Literal["replace", "append"] = Field("replace", description="replace=覆盖，append=追加")

    @field_validator("account_ids")
    @classmethod
    def account_ids_unique(cls, v: List[UUID]) -> List[UUID]:
        if len(v) != len(set(v)):
            raise ValueError("account_ids 不能重复")
        return v


class LiveRoomOfficialAccountsSetResponse(BaseModel):
    """直播间公众号设置响应 Schema"""
    code: int = 200
    message: str = "success"
    data: dict  # room_id, mode, accounts: List[OfficialAccountItem]
    timestamp: datetime


class LiveRoomOfficialAccountsListResponse(BaseModel):
    """直播间关联公众号列表响应 Schema"""
    code: int = 200
    message: str = "success"
    data: List[OfficialAccountItem]
    timestamp: datetime


# ============================================================================
# 按公众号查直播间列表（CSM）Schemas
# ============================================================================

class RoomBriefItem(BaseModel):
    """直播间简要信息（与 v6 主文档一致，用于按公众号查房间分页；对应 live_rooms 的 id/title 等）"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: Optional[str] = Field(None, max_length=100, description="房间标题")
    slug: Optional[str] = Field(None, description="URL 友好标识")


class OfficialAccountRoomsListResponse(BaseModel):
    """按公众号查直播间列表响应（分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[RoomBriefItem]
    timestamp: datetime
