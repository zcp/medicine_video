from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, membership_products, subscriptions, health
from app.api.v1.admin.users import router as admin_users_router
from app.api.v1.admin.products import router as admin_products_router
from app.api.v1.admin.subscriptions import router as admin_subscriptions_router
from app.api.v1.internal.users import router as internal_users_router

api_router = APIRouter()

# 注册健康检查路由
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["健康检查"]
)

# 注册认证相关路由
api_router.include_router(
    auth.router,
    tags=["认证"]
)

# 注册用户管理路由
api_router.include_router(
    users.router,
    tags=["用户管理"]
)

# 服务间内部路由（专家头像同步 users.avatar_url 等）
api_router.include_router(internal_users_router, tags=["Internal - Users"])

# 注册会员产品路由
api_router.include_router(
    membership_products.router,
    tags=["会员产品"]
)

# 注册订阅管理路由
api_router.include_router(
    subscriptions.router,
    tags=["订阅管理"]
)

# 注册后台管理路由
api_router.include_router(admin_users_router, prefix="/admin", tags=["Admin - Users"])
api_router.include_router(admin_products_router, prefix="/admin", tags=["Admin - Products"])
api_router.include_router(admin_subscriptions_router, prefix="/admin", tags=["Admin - Subscriptions"])
