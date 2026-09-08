"""
LiveCore Service - API Router

聚合所有v1版本的API路由
"""

from fastapi import APIRouter

from app.api.v1.endpoints import room, session, topic, live_features
from app.api.v1.endpoints import batch_import, session_import
from app.api.v1.endpoints import internal, internal_users, health, experts, user_behavior, user_preference_notification, brand, homepage_search
from app.api.v1.endpoints import liveroom_official_accounts
from app.api.v1.endpoints import search_extra
from app.api.v1.endpoints import content_safety_admin
from app.api.v1.endpoints import admin_rooms
from app.api.v1.endpoints import expert_departments

api_router = APIRouter()


# 注册各个模块的路由
api_router.include_router(room.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(room.users_me_rooms_router, prefix="/users/me", tags=["rooms"])
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])

# 注册 Import 和 Batch Import 路由
api_router.include_router(
    batch_import.router,
    prefix="/rooms",  # 路径：/api/v1/rooms/import/batch
    tags=["Batch Import"]
)
api_router.include_router(
    session_import.router,
    prefix="/rooms",  # 路径：/api/v1/rooms/{room_id}/sessions/import
    tags=["Session Import"]
)


# --- 新增：注册新的内部回调API路由 ---
# 我们为它指定一个清晰、隔离的路径前缀
api_router.include_router(
    internal.router,
    prefix="/internal/srs",
    tags=["Internal SRS Callbacks"]
)

# 16-D2：账号注销清私货（/api/v1/internal/users/{public_id}/deactivate-cleanup）
api_router.include_router(internal_users.router, tags=["Internal - Users Cleanup"])

# 1. 主专题路由器 - 必须明确指定 prefix 和 tags
api_router.include_router(
    topic.router,
    prefix="/topics",
    tags=["topics"]
)

# 2. 分类路由器
api_router.include_router(
    topic.category_router,
    prefix="/topic-categories",
    tags=["topic-categories"]
)

# 3. 直播间-专题关系路由器
api_router.include_router(
    topic.room_router,
    prefix="/rooms",
    tags=["room-topic-relations"]
)

# 3.9 管理端全站房间列表（17 Admin Room Content Ops MVP）
api_router.include_router(
    admin_rooms.router,
    prefix="/admin",
    tags=["admin-rooms"]
)

# 4. Tab管理路由器（管理员）
api_router.include_router(
    live_features.admin_tab_router,
    prefix="/admin",
    tags=["admin-tabs"]
)

# 4.1 Tab公开路由器（普通用户/匿名，继承 Room is_private 可见性）
api_router.include_router(
    live_features.public_tab_router,
    prefix="",
    tags=["public-tabs"]
)

# 5. 留言路由器（公开）
api_router.include_router(
    live_features.public_message_router,
    prefix="",
    tags=["room-messages"]
)

# 5.1 留言管理端路由器
api_router.include_router(
    live_features.admin_message_router,
    prefix="/admin",
    tags=["admin-messages"]
)

# 5.2 留言 WebSocket 路由器
api_router.include_router(
    live_features.message_ws_router,
    prefix="",
    tags=["room-messages-ws"]
)

# 6. 健康检查路由器
api_router.include_router(
    health.router,
    tags=["health"]
)




# 9. 专家模块路由器
# 专家相关API（公开、管理员、用户）
# 注意：prefix 不要包含 /api/v1，因为 main.py 中已经添加了 prefix=settings.API_V1_STR
# 9.1 推荐专家接口：/api/v1/featured-experts（注册到空前缀）
api_router.include_router(
    experts.experts_featured_router,
    prefix="",
    tags=["专家管理-公开"]
)
# 9.2 公开接口：/api/v1/experts/*
api_router.include_router(
    experts.experts_public_router,
    prefix="/experts",
    tags=["专家管理-公开"]
)
# 9.3 用户接口：/api/v1/users/me/followed-experts（注册到空前缀）
# 注意：必须在 user_preference_notification 之前注册，避免路由冲突
api_router.include_router(
    experts.experts_user_router,
    prefix="",
    tags=["专家管理-用户"]
)
# 9.4 管理员接口：/api/v1/admin/experts
api_router.include_router(
    experts.experts_admin_router,
    prefix="/admin",
    tags=["专家管理-管理员"]
)
# 9.5 科室管理（管理员）：/api/v1/admin/expert-departments
api_router.include_router(
    expert_departments.expert_dept_admin_router,
    prefix="/admin",
    tags=["科室管理-管理员"]
)

# 11. 内容管理模块路由器
# 内容管理相关API（tags, categories, session-tags）
# 注意：prefix 不要包含 /api/v1，因为 main.py 中已经添加了 prefix=settings.API_V1_STR
from app.api.v1.endpoints import content_management
# 内容管理-公开：GET /api/v1/content/categories, /api/v1/content/tags 等
api_router.include_router(
    content_management.content_public_router,
    prefix="/content",
    tags=["内容管理-公开"]
)
# 内容管理-管理：POST/PATCH/DELETE /api/v1/admin/categories, /api/v1/admin/tags 等
api_router.include_router(
    content_management.content_admin_router,
    prefix="/admin",
    tags=["内容管理-管理"]
)
# 11.1 直播间-分类：公开 GET /api/v1/rooms/{room_id}/categories
api_router.include_router(
    content_management.live_room_categories_router,
    prefix="/rooms",
    tags=["内容管理-直播间分类"]
)
# 11.2 直播间-分类：管理 POST/DELETE /api/v1/admin/rooms/{room_id}/categories
api_router.include_router(
    content_management.live_room_categories_admin_router,
    prefix="/admin/rooms",
    tags=["内容管理-直播间分类-管理"]
)

# 12. 用户行为模块路由器
# 注意：prefix 不包含 /api/v1，主路由中统一添加
api_router.include_router(
    user_behavior.router,
    prefix="",
    tags=["用户行为"]
)
# 12.1 用户行为 - 检查是否已收藏（路径为 /api/v1/rooms/{room_id}/is-favorited）
api_router.include_router(
    user_behavior.room_favorite_router,
    prefix="/rooms",
    tags=["用户行为"]
)

# 13. 用户偏好与通知模块路由器
# 包含：/users/me/preferences、/users/me/notifications、/admin/notifications
# 注意：prefix 不包含 /api/v1，主路由中统一添加
# 注意：experts_user_router 已在此前注册，确保 /users/me/followed-experts 路由优先匹配
api_router.include_router(
    user_preference_notification.router,
    prefix="",
    tags=["用户偏好与通知"]
)

# 14. 品牌模块路由器
# 包含：/brands、/admin/brands、/rooms/{room_id}/brands、/admin/rooms/{room_id}/brands
# 注意：prefix 不包含 /api/v1，主路由中统一添加
api_router.include_router(
    brand.router,
    prefix="",
    tags=["品牌管理"]
)
# 焦点图公开路由
api_router.include_router(
    homepage_search.featured_content_public_router,
    prefix="/featured-content",
    tags=["焦点图"]
)
# 焦点图管理员路由（/api/v1/admin/featured-content/*）
api_router.include_router(
    homepage_search.featured_content_admin_router,
    prefix="/admin",
    tags=["焦点图-管理员"]
)

# 首页API路由
api_router.include_router(
    homepage_search.homepage_router,
    prefix="/homepage",
    tags=["首页API"]
)

# 搜索API路由
api_router.include_router(
    homepage_search.search_router,
    prefix="/search",
    tags=["搜索API"]
)

# 直播间与公众号关联模块
api_router.include_router(
    liveroom_official_accounts.admin_official_accounts_router,
    prefix="/admin",
    tags=["直播间与公众号关联-管理端"]
)
api_router.include_router(
    liveroom_official_accounts.rooms_official_accounts_router,
    prefix="/rooms",
    tags=["直播间与公众号关联-公开"]
)
api_router.include_router(
    liveroom_official_accounts.admin_rooms_official_accounts_router,
    prefix="/admin/rooms",
    tags=["直播间与公众号关联-管理端-房间"]
)
api_router.include_router(
    liveroom_official_accounts.official_accounts_rooms_router,
    prefix="/official-accounts",
    tags=["直播间与公众号关联-CSM"]
)

# 搜索模块补充路由
# 用户搜索历史：/api/v1/users/me/search-history
api_router.include_router(
    search_extra.search_history_router,
    prefix="/users/me",
    tags=["搜索历史"]
)

# 热门搜索和搜索建议：/api/v1/search/hot-keywords, /api/v1/search/suggestions
api_router.include_router(
    search_extra.search_extra_router,
    prefix="/search",
    tags=["搜索扩展"]
)

# 内容安全管理端路由
api_router.include_router(
    content_safety_admin.router,
    prefix="/admin",
    tags=["内容安全-管理端"]
)