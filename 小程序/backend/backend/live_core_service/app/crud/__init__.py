# CRUD package initialization

# 健康检查模块（新增）
from .health import check_database_connection

# 首页与搜索模块 CRUD（新增）
from . import homepage_search

# 用户偏好与通知模块 CRUD
# TODO: 待实现
# from app.crud.user_preferences_notifications import (
#     get_user_preferences,
#     create_or_update_user_preferences,
#     get_notifications,
#     get_unread_count,
#     get_notification_by_id,
#     create_notification,
#     create_bulk_notifications,
#     update_notification,
#     delete_notification,
#     delete_bulk_notifications
# ) 