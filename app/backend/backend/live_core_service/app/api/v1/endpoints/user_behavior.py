"""
用户行为模块 API Endpoint 层

本模块实现所有用户行为相关的 RESTful API 接口。

职责：
- HTTP请求/响应处理
- 调用Service层
- 异常转换为HTTP响应

所有端点遵循安全异步异常处理原则。
"""

from typing import Any, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.schemas.user_behavior import (
    FavoriteCreate,
    WatchEventRequest,
    SubscriptionCreate,
    SubscriptionTargetType,
)
from app.services.user_behavior_service import UserBehaviorService
from app.core.response import success_response, error_response
from app.exceptions import (
    NotFoundException,
    InvalidParameterException,
    DatabaseIntegrityException,
)

logger = logging.getLogger(__name__)

user_behavior_router = APIRouter()

# 用于挂载到 prefix=/rooms，提供 GET /api/v1/rooms/{room_id}/is-favorited
room_favorite_router = APIRouter()

# 用于挂载到 prefix=/rooms，提供 GET /api/v1/rooms/{room_id}/is-subscribed
room_subscription_router = APIRouter()

# 用于挂载到 prefix=/sessions，提供 GET /api/v1/sessions/{session_id}/is-subscribed
session_subscription_router = APIRouter()


def _get_current_user_id(current_user: dict) -> UUID:
    """从 current_user 中提取 user_id（公开ID）。"""
    return UUID(current_user["user_id"])


# ==================== 收藏相关 ====================


@user_behavior_router.post("/users/me/favorites")
async def add_favorite(
    favorite_in: FavoriteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建收藏"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserBehaviorService(db)
        item = await service.add_favorite(user_id, favorite_in.room_id)
        return success_response(data=item)
    except InvalidParameterException as e:
        logger.warning(f"创建收藏失败（参数错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建收藏失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@user_behavior_router.get("/users/me/favorites")
async def get_favorites(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取收藏列表（分页）"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserBehaviorService(db)
        result = await service.get_favorites(user_id, page=page, size=size)
        return success_response(data=result.model_dump())
    except Exception as e:
        logger.error(f"获取收藏列表失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@room_favorite_router.get("/{room_id}/is-favorited")
async def check_is_favorited(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """检查当前用户是否已收藏指定直播间（Strict Auth）"""
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    try:
        service = UserBehaviorService(db)
        result = await service.check_is_favorited(room_id=room_id, current_user_id=user_id)
        return success_response(data=result)
    except NotFoundException:
        logger.warning(
            "检查收藏状态失败（直播间不存在）: user_id=%s, room_id=%s",
            user_id_for_logging,
            str(room_id)[:8],
        )
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except Exception as e:
        logger.error(
            "检查收藏状态异常: user_id=%s, room_id=%s, error=%s",
            user_id_for_logging,
            str(room_id)[:8],
            str(e),
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )


@user_behavior_router.delete("/users/me/favorites/{room_id}")
async def remove_favorite(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """取消收藏"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserBehaviorService(db)
        await service.remove_favorite(user_id, room_id)
        return success_response()
    except NotFoundException as e:
        logger.warning(f"取消收藏失败（资源不存在）: user_id={user_id_for_logging}, room_id={str(room_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"取消收藏失败: user_id={user_id_for_logging}, room_id={str(room_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ==================== 观看历史相关 ====================


@user_behavior_router.post("/users/me/watch-history")
async def record_watch_event(
    body: WatchEventRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """记录观看历史"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserBehaviorService(db)
        item = await service.record_watch_event(user_id, body)
        return success_response(data=item)
    except InvalidParameterException as e:
        logger.warning(f"记录观看历史失败（参数错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"记录观看历史失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@user_behavior_router.get("/users/me/watch-history")
async def get_watch_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取观看历史列表（分页）"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserBehaviorService(db)
        result = await service.get_watch_history(user_id, page=page, size=size)
        return success_response(data=result.model_dump())
    except Exception as e:
        logger.error(f"获取观看历史列表失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@user_behavior_router.delete("/users/me/watch-history/{history_id}")
async def delete_watch_history(
    history_id: UUID = Path(..., description="观看历史记录ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """删除单条观看历史"""
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    try:
        service = UserBehaviorService(db)
        await service.delete_watch_history(user_id, history_id)
        return success_response(data={"id": str(history_id), "status": "deleted"})
    except NotFoundException:
        logger.warning(
            "删除观看历史失败（记录不存在或无权）: user_id=%s, history_id=%s",
            user_id_for_logging,
            str(history_id)[:8],
        )
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except Exception as e:
        logger.error(
            "删除观看历史失败: user_id=%s, history_id=%s, error=%s",
            user_id_for_logging,
            str(history_id)[:8],
            str(e),
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )


# ==================== 订阅提醒相关 ====================


@user_behavior_router.post("/users/me/subscriptions")
async def create_subscription(
        sub_in: SubscriptionCreate,
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
) -> Any:
    """创建订阅"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]

    try:
        service = UserBehaviorService(db)
        item = await service.create_subscription(user_id, sub_in)
        return success_response(data=item)
    except NotFoundException as e:
        logger.warning(
            f"创建订阅失败（资源不存在）: user_id={user_id_for_logging}, target_id={str(sub_in.target_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except InvalidParameterException as e:
        logger.warning(f"创建订阅失败（参数错误）: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建订阅失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@user_behavior_router.get("/users/me/subscriptions")
async def get_subscriptions(
    target_type: Optional[SubscriptionTargetType] = Query(None, description="订阅目标类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取订阅列表（分页）"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserBehaviorService(db)
        result = await service.get_subscriptions(
            user_id, target_type=target_type, page=page, size=size
        )
        return success_response(data=result.model_dump())
    except Exception as e:
        logger.error(f"获取订阅列表失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@user_behavior_router.delete("/users/me/subscriptions")
async def cancel_subscription(
    target_type: SubscriptionTargetType = Query(..., description="订阅目标类型"),
    target_id: UUID = Query(..., description="订阅目标ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """取消订阅"""
    # 🚨 必须在 try 之前提取 user_id
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = UserBehaviorService(db)
        await service.cancel_subscription(
            current_user_id=user_id,
            target_type=target_type,
            target_id=target_id,
        )
        return success_response()
    except Exception as e:
        logger.error(f"取消订阅失败: user_id={user_id_for_logging}, target_id={str(target_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ==================== 订阅状态查询（对标 is-favorited） ====================


@room_subscription_router.get("/{room_id}/is-subscribed")
async def check_room_is_subscribed(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """检查当前用户是否已订阅指定房间（用于预告页面按钮状态）"""
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    try:
        service = UserBehaviorService(db)
        result = await service.check_is_subscribed(
            target_type=SubscriptionTargetType.ROOM,
            target_id=room_id,
            current_user_id=user_id,
        )
        return success_response(data=result)
    except NotFoundException:
        logger.warning(
            "检查订阅状态失败（房间不存在）: user_id=%s, room_id=%s",
            user_id_for_logging,
            str(room_id)[:8],
        )
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except Exception as e:
        logger.error(
            "检查订阅状态异常: user_id=%s, room_id=%s, error=%s",
            user_id_for_logging,
            str(room_id)[:8],
            str(e),
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )


@session_subscription_router.get("/{session_id}/is-subscribed")
async def check_session_is_subscribed(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """检查当前用户是否已订阅指定场次（用于预告页面按钮状态）"""
    user_id = _get_current_user_id(current_user)
    user_id_for_logging = str(user_id)[:8]
    try:
        service = UserBehaviorService(db)
        result = await service.check_is_subscribed(
            target_type=SubscriptionTargetType.SESSION,
            target_id=session_id,
            current_user_id=user_id,
        )
        return success_response(data=result)
    except NotFoundException:
        logger.warning(
            "检查订阅状态失败（场次不存在）: user_id=%s, session_id=%s",
            user_id_for_logging,
            str(session_id)[:8],
        )
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except Exception as e:
        logger.error(
            "检查订阅状态异常: user_id=%s, session_id=%s, error=%s",
            user_id_for_logging,
            str(session_id)[:8],
            str(e),
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )
