"""
Pydantic Schema 定义 - 用户功能服务
为 SQLAlchemy 模型提供 API 数据交互的 Schema
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ..models.users import (
    UserRole, EntityStatus, MembershipProductStatus, MembershipStatus
)


# ============================================================================
# 用户 (User) 相关 Schema
# ============================================================================

class UserBase(BaseModel):
    """用户基础 Schema - 包含通用字段"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    nickname: str = Field(..., min_length=1, max_length=50, description="昵称")
    email: Optional[str] = Field(None, max_length=255, description="邮箱地址")
    phone_number: Optional[str] = Field(None, max_length=20, description="手机号码")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    role: UserRole = Field(UserRole.REGULAR, description="用户角色")
    status: EntityStatus = Field(EntityStatus.NORMAL, description="用户状态")
    can_stream: bool = Field(True, description="是否可开播（默认 true；false=禁止开播；与 role 正交）")


class UserCreate(UserBase):
    """创建用户 Schema - 用于 POST /users"""
    password_hash: Optional[str] = Field(None, max_length=255, description="密码哈希")
    social_provider: Optional[str] = Field(None, max_length=20, description="社交登录提供商")
    social_id: Optional[str] = Field(None, max_length=255, description="社交登录ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "nickname": "John Doe",
                "email": "john@example.com",
                "phone_number": "+1234567890",
                "password_hash": "hashed_password_here",
                "role": "REGULAR",
                "status": "NORMAL"
            }
        }
    )


class UserUpdate(BaseModel):
    """更新用户 Schema - 用于 PUT/PATCH /users/{id}"""
    username: Optional[str] = Field(None, min_length=1, max_length=50, description="用户名")
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description="昵称")
    email: Optional[str] = Field(None, max_length=255, description="邮箱地址")
    phone_number: Optional[str] = Field(None, max_length=20, description="手机号码")
    password_hash: Optional[str] = Field(None, max_length=255, description="密码哈希")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    role: Optional[UserRole] = Field(None, description="用户角色（仅 SUPERADMIN 可改）")
    status: Optional[EntityStatus] = Field(None, description="用户状态")
    can_stream: Optional[bool] = Field(None, description="是否允许开播（false=禁止开播）")
    is_email_verified: Optional[bool] = Field(None, description="邮箱是否已验证")
    is_phone_verified: Optional[bool] = Field(None, description="手机是否已验证")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    last_login_ip: Optional[str] = Field(None, description="最后登录IP")
    social_provider: Optional[str] = Field(None, max_length=20, description="社交登录提供商")
    social_id: Optional[str] = Field(None, max_length=255, description="社交登录ID")


class UserResponse(UserBase):
    """用户响应 Schema - 用于 API 返回"""
    id: int = Field(..., description="内部ID")
    public_id: uuid.UUID = Field(..., description="公开UUID")
    is_email_verified: bool = Field(..., description="邮箱是否已验证")
    is_phone_verified: bool = Field(..., description="手机是否已验证")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    last_login_ip: Optional[str] = Field(None, description="最后登录IP")
    social_provider: Optional[str] = Field(None, description="社交登录提供商")
    social_id: Optional[str] = Field(None, description="社交登录ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    @field_validator('last_login_ip', mode='before')
    @classmethod
    def convert_ip_to_string(cls, v):
        """将IPv4Address/IPv6Address对象转换为字符串"""
        if v is None:
            return None
        if isinstance(v, (IPv4Address, IPv6Address)):
            return str(v)
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 会员产品 (MembershipProduct) 相关 Schema
# ============================================================================

class MembershipProductBase(BaseModel):
    """会员产品基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="产品名称")
    description: Optional[str] = Field(None, description="产品描述")
    sort_order: int = Field(0, description="排序顺序")
    price: Decimal = Field(..., gt=0, description="价格")
    level: int = Field(1, ge=1, description="产品等级")
    duration_unit: str = Field(..., max_length=10, description="时长单位")
    duration_value: int = Field(..., gt=0, description="时长数值")
    status: MembershipProductStatus = Field(MembershipProductStatus.DRAFT, description="产品状态")
    payment_gateway_price_id: Optional[str] = Field(None, max_length=255, description="支付网关价格ID")


class MembershipProductCreate(MembershipProductBase):
    """创建会员产品 Schema"""
    code: str = Field(..., min_length=1, max_length=50, description="产品编码")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VIDEO_YEARLY",
                "name": "视频年费会员",
                "description": "享受一年的视频观看权限",
                "price": "99.99",
                "level": 1,
                "duration_unit": "year",
                "duration_value": 1,
                "status": "ACTIVE"
            }
        }
    )


class MembershipProductUpdate(BaseModel):
    """更新会员产品 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="产品名称")
    description: Optional[str] = Field(None, description="产品描述")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    price: Optional[Decimal] = Field(None, gt=0, description="价格")
    level: Optional[int] = Field(None, ge=1, description="产品等级")
    duration_unit: Optional[str] = Field(None, max_length=10, description="时长单位")
    duration_value: Optional[int] = Field(None, gt=0, description="时长数值")
    status: Optional[MembershipProductStatus] = Field(None, description="产品状态")
    payment_gateway_price_id: Optional[str] = Field(None, max_length=255, description="支付网关价格ID")


class MembershipProductResponse(MembershipProductBase):
    """会员产品响应 Schema"""
    code: str = Field(..., description="产品编码")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 用户会员订阅 (UserMembership) 相关 Schema
# ============================================================================

class UserMembershipBase(BaseModel):
    """用户会员订阅基础 Schema"""
    level: int = Field(1, ge=1, description="会员等级")
    status: MembershipStatus = Field(MembershipStatus.PENDING_PAYMENT, description="订阅状态")
    is_auto_renew: bool = Field(False, description="是否自动续费")
    admin_notes: Optional[str] = Field(None, description="管理员备注")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    expires_at: datetime = Field(..., description="过期时间")


class UserMembershipCreate(UserMembershipBase):
    """创建用户会员订阅 Schema"""
    user_id: int = Field(..., description="用户ID")
    product_code: str = Field(..., max_length=50, description="产品编码")
    transaction_id: Optional[str] = Field(None, max_length=255, description="交易ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "product_code": "VIDEO_YEARLY",
                "transaction_id": "txn_123456789",
                "level": 1,
                "status": "PENDING_PAYMENT",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }
    )


class UserMembershipUpdate(BaseModel):
    """更新用户会员订阅 Schema"""
    transaction_id: Optional[str] = Field(None, max_length=255, description="交易ID")
    level: Optional[int] = Field(None, ge=1, description="会员等级")
    status: Optional[MembershipStatus] = Field(None, description="订阅状态")
    is_auto_renew: Optional[bool] = Field(None, description="是否自动续费")
    admin_notes: Optional[str] = Field(None, description="管理员备注")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class UserMembershipResponse(UserMembershipBase):
    """用户会员订阅响应 Schema"""
    id: int = Field(..., description="内部ID")
    public_id: uuid.UUID = Field(..., description="公开UUID")
    user_id: int = Field(..., description="用户ID")
    product_code: str = Field(..., description="产品编码")
    transaction_id: Optional[str] = Field(None, description="交易ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 关联响应 Schema (包含关联数据)
# ============================================================================

class UserWithMembershipsResponse(UserResponse):
    """用户响应 Schema (包含会员订阅信息)"""
    memberships: List[UserMembershipResponse] = Field(default_factory=list, description="用户的会员订阅")
    
    model_config = ConfigDict(from_attributes=True)


class UserMembershipWithDetailsResponse(UserMembershipResponse):
    """用户会员订阅响应 Schema (包含用户和产品详情)"""
    user: Optional[UserResponse] = Field(None, description="用户信息")
    product: Optional[MembershipProductResponse] = Field(None, description="产品信息")
    
    model_config = ConfigDict(from_attributes=True)


class MembershipProductWithMembershipsResponse(MembershipProductResponse):
    """会员产品响应 Schema (包含订阅信息)"""
    user_memberships: List[UserMembershipResponse] = Field(default_factory=list, description="该产品的订阅记录")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 分页和查询 Schema
# ============================================================================

class PaginationParams(BaseModel):
    """分页参数 Schema"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")


class UserFilterParams(BaseModel):
    """用户查询过滤参数 Schema"""
    username: Optional[str] = Field(None, description="用户名筛选")
    email: Optional[str] = Field(None, description="邮箱筛选")
    phone_number: Optional[str] = Field(None, description="手机号精确筛选")
    nickname: Optional[str] = Field(None, description="昵称模糊筛选")
    role: Optional[UserRole] = Field(None, description="角色筛选")
    status: Optional[EntityStatus] = Field(None, description="状态筛选")
    can_stream: Optional[bool] = Field(None, description="开播筛选（true=可播；false=被禁止开播）")
    is_email_verified: Optional[bool] = Field(None, description="邮箱验证状态筛选")
    is_phone_verified: Optional[bool] = Field(None, description="手机验证状态筛选")


class MembershipFilterParams(BaseModel):
    """会员订阅查询过滤参数 Schema"""
    user_id: Optional[int] = Field(None, description="用户ID筛选")
    product_code: Optional[str] = Field(None, description="产品编码筛选")
    status: Optional[MembershipStatus] = Field(None, description="订阅状态筛选")
    is_auto_renew: Optional[bool] = Field(None, description="自动续费筛选")
    expires_before: Optional[datetime] = Field(None, description="过期时间早于")
    expires_after: Optional[datetime] = Field(None, description="过期时间晚于")


class PaginatedResponse(BaseModel):
    """分页响应基础 Schema"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class PaginatedUsersResponse(PaginatedResponse):
    """分页用户响应 Schema"""
    items: List[UserResponse] = Field(..., description="用户列表")


class PaginatedMembershipProductsResponse(PaginatedResponse):
    """分页会员产品响应 Schema"""
    items: List[MembershipProductResponse] = Field(..., description="会员产品列表")


class PaginatedUserMembershipsResponse(PaginatedResponse):
    """分页用户会员订阅响应 Schema"""
    items: List[UserMembershipResponse] = Field(..., description="用户会员订阅列表")


# ============================================================================
# 批次四新增 Schema - 用户订阅管理
# ============================================================================

class SubscriptionCreateRequest(BaseModel):
    """用户购买订阅请求 Schema"""
    product_code: str = Field(..., max_length=50, description="产品编码")
    payment_token: str = Field(..., description="支付令牌")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_code": "VIDEO_YEARLY",
                "payment_token": "tok_visa_1234567890"
            }
        }
    )


class SubscriptionUpdateRequest(BaseModel):
    """用户更新订阅请求 Schema"""
    is_auto_renew: bool = Field(..., description="是否自动续费")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_auto_renew": False
            }
        }
    )


class PaginatedSubscriptionsResponse(BaseModel):
    """分页订阅响应 Schema"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    items: List[UserMembershipResponse] = Field(..., description="订阅列表")


# ============================================================================
# 批次五新增 Schema - 后台管理API
# ============================================================================

class UserMembershipCreateAdmin(BaseModel):
    """管理员手动为用户创建订阅请求 Schema"""
    product_code: str = Field(..., max_length=50, description="产品编码")
    transaction_id: str = Field(..., max_length=255, description="交易ID")
    start_date: datetime = Field(..., description="开始时间")
    expires_at: datetime = Field(..., description="过期时间")
    admin_notes: Optional[str] = Field(None, description="管理员备注")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_code": "VIDEO_YEARLY",
                "transaction_id": "manual_gift_by_admin_xyz_001",
                "start_date": "2025-07-23T00:00:00Z",
                "expires_at": "2026-07-23T00:00:00Z",
                "admin_notes": "用户参与夏日活动奖励"
            }
        }
    )

# 批次二新增模型
class UserUpdateSelf(BaseModel):
    """用户自我更新模型 - 仅包含用户可修改的字段（头像请走 POST /me/avatar）"""
    model_config = ConfigDict(extra="forbid")

    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description="昵称")
    bio: Optional[str] = Field(None, description="个人简介")


# 在文件末尾添加
class PhoneBindRequest(BaseModel):
    """手机号绑定请求 Schema"""
    phone_number: str = Field(..., max_length=20, description="手机号码")
    bind_ticket: str = Field(..., description="绑定票据（由 /verification-codes/verify 签发）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone_number": "+8613800138000",
                "bind_ticket": "ticket_xyz_123"
            }
        }
    )
