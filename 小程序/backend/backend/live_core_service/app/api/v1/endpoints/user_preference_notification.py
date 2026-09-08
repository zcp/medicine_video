"""
用户偏好与通知模块 - API层

职责：HTTP端点层，处理请求/响应，调用Service层
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.response import success_response, error_response
from app.schemas.user_preference_notification import (
    UserPreferencesUpdate,
    NotificationCreateRequest,
    NotificationUpdateRequest,
    NotificationBatchDeleteRequest,
    NotificationItem,
)
from app.services.user_preference_notification_service import UserPreferenceNotificationService
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["User Preferences & Notifications"])


# ==================== User Preferences API ====================

@router.get("/users/me/preferences")
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户偏好设置"""
    # 🚨 必须在try之前提取user_id
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_preferences(user_id, role)
        logger.info(f"获取用户偏好成功: user_id={user_id_for_logging}")
        return success_response(data=result)
    except NotFoundException as e:
        logger.warning(f"获取用户偏好失败（资源不存在）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"获取用户偏好失败（系统错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.patch("/users/me/preferences")
async def update_user_preferences(
    prefs_update: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户偏好设置"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.update_preferences(user_id, prefs_update, role)
        logger.info(f"更新用户偏好成功: user_id={user_id_for_logging}")
        return success_response(data=result)
    except InvalidParameterException as e:
        logger.warning(f"更新用户偏好失败（参数错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新用户偏好失败（系统错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ==================== Notifications API (User) ====================

@router.get("/users/me/notifications")
async def get_user_notifications(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    notification_type: Optional[str] = Query(None, description="通知类型筛选"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取通知列表"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_notifications_list(
            user_id, page, size, is_read, notification_type, role
        )
        logger.info(f"获取通知列表成功: user_id={user_id_for_logging}, page={page}, size={size}")
        return success_response(data=result)
    except Exception as e:
        logger.error(f"获取通知列表失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# 静态路径必须注册在 {notification_id} 动态路由之前，否则会被 UUID 参数路由抢走并 422
@router.get("/users/me/notifications/unread-count")
async def get_unread_notifications_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取未读通知数量"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_unread_count(user_id)
        logger.info(f"获取未读数量成功: user_id={user_id_for_logging}, count={result['unread_count']}")
        return success_response(data=result)
    except Exception as e:
        logger.error(f"获取未读数量失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/users/me/notifications/{notification_id}")
async def get_user_notification_detail(
    notification_id: UUID = Path(..., description="通知ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取通知详情"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()

    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_notification_detail(notification_id, user_id, role)
        logger.info(f"获取通知详情成功: user_id={user_id_for_logging}, notification_id={str(notification_id)[:8]}")
        return success_response(data=result)
    except NotFoundException as e:
        logger.warning(f"获取通知详情失败（资源不存在）: user_id={user_id_for_logging}, notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"获取通知详情失败: user_id={user_id_for_logging}, notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.post("/users/me/notifications/read-all")
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记所有通知为已读"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.mark_all_notifications_as_read(user_id)
        logger.info(f"标记所有通知为已读成功: user_id={user_id_for_logging}, count={result['updated_count']}")
        return success_response(data=result)
    except Exception as e:
        logger.error(f"标记所有通知为已读失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.post("/users/me/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: UUID = Path(..., description="通知ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记通知为已读"""
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    user_id_for_logging = str(user_id)[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        await service.mark_notification_as_read(notification_id, user_id, role)
        logger.info(f"标记通知为已读成功: notification_id={str(notification_id)[:8]}")
        return success_response(data=None)
    except NotFoundException as e:
        logger.warning(f"标记通知为已读失败（资源不存在）: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"标记通知为已读失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ==================== Notifications API (Admin) ====================

@router.post("/admin/notifications")
async def create_notifications_batch(
    notification_data: NotificationCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量创建通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.create_notifications_batch(
            notification_data.user_ids,
            notification_data,
            role
        )
        logger.info(f"批量创建通知成功: admin={user_id_for_logging}, count={result.total_created}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"批量创建通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"批量创建通知失败（参数错误）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"批量创建通知失败: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/admin/notifications")
async def get_notifications_admin(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    user_id: Optional[UUID] = Query(None, description="用户ID筛选"),
    notification_type: Optional[str] = Query(None, description="通知类型筛选"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取通知列表（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.get_notifications_list_admin(
            page, size, user_id, notification_type, is_read, role
        )
        logger.info(f"管理员获取通知列表成功: admin={user_id_for_logging}, page={page}, size={size}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"管理员获取通知列表失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except Exception as e:
        logger.error(f"管理员获取通知列表失败: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.patch("/admin/notifications/{notification_id}")
async def update_notification(
    notification_id: UUID = Path(..., description="通知ID"),
    update_data: NotificationUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.update_notification(notification_id, update_data, role)
        logger.info(f"更新通知成功: admin={user_id_for_logging}, notification_id={str(notification_id)[:8]}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"更新通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except NotFoundException as e:
        logger.warning(f"更新通知失败（资源不存在）: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"更新通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.delete("/admin/notifications/{notification_id}")
async def delete_notification(
    notification_id: UUID = Path(..., description="通知ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        await service.delete_notification(notification_id, role)
        logger.info(f"删除通知成功: admin={user_id_for_logging}, notification_id={str(notification_id)[:8]}")
        return success_response(data=None)
    except PermissionDeniedException as e:
        logger.warning(f"删除通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except NotFoundException as e:
        logger.warning(f"删除通知失败（资源不存在）: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"删除通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.post("/admin/notifications/batch-delete")
async def batch_delete_notifications(
    delete_request: NotificationBatchDeleteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除通知（管理员）"""
    user_id_for_logging = str(UUID(current_user.get("user_id") or current_user.get("sub")))[:8]
    role = current_user.get("role", "REGULAR").upper()
    
    try:
        service = UserPreferenceNotificationService(db)
        result = await service.batch_delete_notifications(delete_request, role)
        logger.info(f"批量删除通知成功: admin={user_id_for_logging}, count={result['deleted_count']}")
        return success_response(data=result)
    except PermissionDeniedException as e:
        logger.warning(f"批量删除通知失败（权限不足）: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=4003, message=str(e))
        )
    except Exception as e:
        logger.error(f"批量删除通知失败: admin={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
