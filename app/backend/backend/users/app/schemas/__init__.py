"""
Schemas package - 导出所有 Pydantic Schema
"""
from .users import (
    # 用户相关 Schema
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithMembershipsResponse,
    
    # 会员产品相关 Schema
    MembershipProductBase,
    MembershipProductCreate,
    MembershipProductUpdate,
    MembershipProductResponse,
    MembershipProductWithMembershipsResponse,
    
    # 用户会员订阅相关 Schema
    UserMembershipBase,
    UserMembershipCreate,
    UserMembershipUpdate,
    UserMembershipResponse,
    UserMembershipWithDetailsResponse,
    
    # 分页和查询 Schema
    PaginationParams,
    UserFilterParams,
    MembershipFilterParams,
    PaginatedResponse,
    PaginatedUsersResponse,
    PaginatedMembershipProductsResponse,
    PaginatedUserMembershipsResponse,
)

from .auth import (
    # 认证相关 Schema
    VerificationCodeRequest,
    VerifyCodeRequest,
    LoginRequest,
    PhoneLoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    PhoneRegisterRequest,
    OneTapLoginRequest,
)

__all__ = [
    # 用户相关 Schema
    "UserBase",
    "UserCreate", 
    "UserUpdate",
    "UserResponse",
    "UserWithMembershipsResponse",
    
    # 会员产品相关 Schema
    "MembershipProductBase",
    "MembershipProductCreate",
    "MembershipProductUpdate", 
    "MembershipProductResponse",
    "MembershipProductWithMembershipsResponse",
    
    # 用户会员订阅相关 Schema
    "UserMembershipBase",
    "UserMembershipCreate",
    "UserMembershipUpdate",
    "UserMembershipResponse", 
    "UserMembershipWithDetailsResponse",
    
    # 分页和查询 Schema
    "PaginationParams",
    "UserFilterParams",
    "MembershipFilterParams",
    "PaginatedResponse",
    "PaginatedUsersResponse",
    "PaginatedMembershipProductsResponse",
    "PaginatedUserMembershipsResponse",
    
    # 认证相关 Schema
    "VerificationCodeRequest",
    "VerifyCodeRequest",
    "LoginRequest",
    "PhoneLoginRequest",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "PhoneRegisterRequest",
    "OneTapLoginRequest",
] 
