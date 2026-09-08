from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, membership_products, subscriptions, health
from app.api.v1.admin import users as admin_users
from app.api.v1.admin import products as admin_products
from app.api.v1.admin import subscriptions as admin_subscriptions
from app.api.v1.internal import users as internal_users

api_router = APIRouter()

# 注册健康检查路由
api_router.include_router(
    health.health_router,
    prefix="/health",
    tags=["健康检查"]
)

# 注册认证相关路由
api_router.include_router(
    auth.auth_router,
    prefix="/auth",
    tags=["认证"]
)

# 注册用户管理路由
api_router.include_router(
    users.users_router,
    prefix="/users",
    tags=["用户管理"]
)

# 注册会员产品路由
api_router.include_router(
    membership_products.membership_products_router,
    prefix="/membership-products",
    tags=["会员产品"]
)

# 注册订阅管理路由
api_router.include_router(
    subscriptions.subscriptions_router,
    prefix="/users/me/memberships",
    tags=["订阅管理"]
)

# PR 1B: 管理端路由
api_router.include_router(
    admin_users.router,
    prefix="/admin",
    tags=["管理端-用户"]
)
api_router.include_router(
    admin_products.router,
    prefix="/admin",
    tags=["管理端-产品"]
)
api_router.include_router(
    admin_subscriptions.router,
    prefix="/admin",
    tags=["管理端-订阅"]
)

# PR 1B: 内部服务路由
api_router.include_router(
    internal_users.router,
    tags=["Internal - Users"]
) 