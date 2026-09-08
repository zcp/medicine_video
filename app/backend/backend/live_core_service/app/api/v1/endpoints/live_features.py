"""
直播间 Tab 和留言功能的 API Endpoint 层（学院派）

职责：
- 参数绑定和依赖注入
- 调用 Service 层
- 捕获自定义异常并转换为 HTTP 响应
- URL 拼接处理
- 严禁包含业务逻辑
"""

import uuid
import logging
from typing import List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body, Request, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.deps import get_current_user, get_current_user_optional, verify_admin_role  # [关键] 导入依赖注入函数
from app.core.response import success_response, error_response
from app.core.file_handler import FileHandler
from app.core.permissions import check_room_visibility
from app.core.redis_cache import get_cached_messages, set_cached_messages, invalidate_message_cache
from app.core.deactivated_users import filter_deactivated_user_ids
from app.models.live_features import LiveRoomMessageUserRole

from app.services.live_features_service import TabService, MessageService
from app.services.message_push import message_push_manager
from app.services.user_profile_client import fetch_user_profiles
from app.crud import live_features as crud_live_features
from app.schemas.live_features import (
    LiveRoomTabCreate,
    LiveRoomTabUpdate,
    LiveRoomTabResponse,
    LiveRoomMessageCreate,
    LiveRoomMessagePostResponse,
    LiveRoomMessageListResponseItem,
    PaginatedLiveRoomMessageResponse,
    AdminMessageQueryParams,
    AdminMessageItem,
    AdminMessagePageResult,
    BatchDeleteRequest,
)

# [关键] 导入所有需要捕获的异常
from app.exceptions import (
    TabNotFoundException,
    RoomNotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException,
    DatabaseOperationException,
    NotFoundException,
    MessageNotFoundException,
)
from app.content_safety.exceptions import ContentSafetyBlockedException

logger = logging.getLogger(__name__)


# ==================== 路由器定义（学院派规范 5.3.C）====================
# 严禁在此处使用 prefix，prefix 由顶层 api_router 统一管理

admin_tab_router = APIRouter(tags=["Admin - Tabs"])

public_message_router = APIRouter(tags=["Public - Messages"])

# PR 3: 管理端留言路由 + WebSocket
admin_message_router = APIRouter(tags=["Admin - Messages"])
message_ws_router = APIRouter(tags=["WebSocket - Messages"])


# ==================== Admin Tab 管理端点 ====================

@admin_tab_router.get("/rooms/{room_id}/tabs")
async def list_room_tabs(
    room_id: uuid.UUID,
    request: Request,  # [关键] 注入 Request 用于 URL 拼接
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user)  # [关键] JWT token 字典
):
    """
    获取房间的所有 Tab（Room Owner 或管理员用）

    权限：ADMIN/SUPERADMIN 或 Room Owner（Service 层 `_check_tab_management_permission` 放行）
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user.get("user_id"))
    role = current_user.get("role")  # ← 使用.get()方法，字符串格式
    role_str = role.upper() if role else "REGULAR"

    try:
        user_role = LiveRoomMessageUserRole[role_str]
    except KeyError:
        user_role = LiveRoomMessageUserRole.REGULAR

    # 从当前用户信息中提取一个可用于展示的昵称/名称
    user_display_name = (
        current_user.get("nickname")
        or current_user.get("username")
        or current_user.get("email")
    )

    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    operator_user_id_log = str(user_id)
    room_id_log = str(room_id)
    
    logger.info(f"管理端 {operator_user_id_log} listing tabs for room {room_id_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        # ← 修改：传递role参数（字符串格式）
        tabs, total = await service.list_tabs_for_admin(
            user_id=user_id, 
            user_role=user_role, 
            room_id=room_id,
            role=role_str  # ← 使用已做 .upper() 的 role_str，避免大小写不一致导致 ADMIN 被拒
        )
        
        # 按《图片上传与显示规范》：image_url 原样返回（相对或完整），由前端用 getImageSrc 转完整 URL
        tabs_with_urls = [LiveRoomTabResponse.model_validate(tab).model_dump() for tab in tabs]
        
        return success_response(data={"items": tabs_with_urls, "total": total})
    
    except PermissionDeniedException as e:
        # [学院派规范 5.3.C] 权限异常 -> 403
        logger.warning(f"权限不足: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except RoomNotFoundException as e:
        # [学院派规范 5.1] 资源不存在 -> 404
        logger.warning(f"Room not found: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except Exception as e:
        # [学院派规范 5.1] 未捕获异常 -> 500
        logger.error(f"Error listing tabs: user_id={operator_user_id_log}, room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@admin_tab_router.post("/rooms/{room_id}/tabs/image")
async def upload_tab_image(
    room_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user)
):
    """
     Tab 图片上传（与房间封面上传独立，多 Tab 多图互不覆盖）。
     权限：Room Owner 或 ADMIN/SUPERADMIN。返回相对路径，由前端用 getImageSrc 转完整 URL。
    """
    user_id = uuid.UUID(current_user.get("user_id"))
    role = (current_user.get("role") or "REGULAR").upper()
    room_id_log = str(room_id)

    try:
        service = TabService(db)
        room = await service._check_room_exists(room_id)
        service._check_tab_management_permission(room, user_id, role)
    except RoomNotFoundException:
        return JSONResponse(status_code=404, content=error_response(code=2001, message="房间不存在"))
    except PermissionDeniedException:
        return JSONResponse(status_code=403, content=error_response(code=3002, message="无权操作该房间"))
    try:
        image_url = await FileHandler.save_tab_image_file(file=file, room_id=room_id)
        return success_response(data={"image_url": image_url})
    except HTTPException as e:
        logger.warning(f"Tab 图片上传失败(文件验证): room_id={room_id_log}, detail={e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(code=4001, message=e.detail if isinstance(e.detail, str) else str(e.detail))
        )
    except Exception as e:
        logger.error(f"Tab 图片上传失败: room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message="文件保存失败")
        )


@admin_tab_router.post("/rooms/{room_id}/tabs")
async def create_room_tab(
    room_id: uuid.UUID,
    obj_in: LiveRoomTabCreate = Body(...),
    request: Request = None,  # [关键] 注入 Request
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user)  # JWT token 字典
):
    """
    创建房间 Tab（管理端——Room Owner 或管理员均可操作）

     权限：Room Owner 或 ADMIN/SUPERADMIN
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user.get("user_id"))
    role = current_user.get("role")  # ← 使用.get()方法，字符串格式
    role_str = role.upper() if role else "REGULAR"

    try:
        user_role = LiveRoomMessageUserRole[role_str]
    except KeyError:
        user_role = LiveRoomMessageUserRole.REGULAR
    
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    operator_user_id_log = str(user_id)
    room_id_log = str(room_id)
    tab_key_log = obj_in.tab_key
    
    logger.info(f"管理端 {operator_user_id_log} creating tab for room {room_id_log}, tab_key={tab_key_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        # ← 修改：传递role参数（字符串格式）
        new_tab = await service.create_tab(
            user_id=user_id, 
            user_role=user_role, 
            room_id=room_id, 
            obj_in=obj_in,
            role=role_str  # ← 使用已做 .upper() 的 role_str，避免大小写不一致导致 ADMIN 被拒
        )
        
        # 按《图片上传与显示规范》：image_url 原样返回，由前端用 getImageSrc 转完整 URL
        tab_response = LiveRoomTabResponse.model_validate(new_tab)
        return success_response(data=tab_response.model_dump())
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except RoomNotFoundException as e:
        logger.warning(f"Room not found: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except InvalidParameterException as e:
        # [学院派规范] 业务参数错误 -> 400
        logger.warning(f"Invalid parameter: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except (DatabaseIntegrityException, DatabaseOperationException) as e:
        # [学院派规范] 数据库错误（来自 CRUD 层）-> 400
        logger.error(f"Database error creating tab: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=f"数据库操作失败: {str(e)}")
        )
    
    except Exception as e:
        logger.error(f"Error creating tab: user_id={operator_user_id_log}, room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@admin_tab_router.patch("/tabs/{tab_id}")
async def update_room_tab(
    tab_id: uuid.UUID,
    obj_in: LiveRoomTabUpdate = Body(...),
    request: Request = None,  # [关键] 注入 Request
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user)  # JWT token 字典
):
    """
    更新房间 Tab（管理端——Room Owner 或管理员均可操作）

     权限：Room Owner 或 ADMIN/SUPERADMIN
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user.get("user_id"))
    role = current_user.get("role")  # ← 使用.get()方法，字符串格式
    role_str = role.upper() if role else "REGULAR"

    try:
        user_role = LiveRoomMessageUserRole[role_str]
    except KeyError:
        user_role = LiveRoomMessageUserRole.REGULAR
    
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    operator_user_id_log = str(user_id)
    tab_id_log = str(tab_id)
    
    logger.info(f"管理端 {operator_user_id_log} updating tab {tab_id_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        # ← 修改：传递role参数（字符串格式）
        updated_tab = await service.update_tab(
            user_id=user_id, 
            user_role=user_role, 
            tab_id=tab_id, 
            obj_in=obj_in,
            role=role_str  # ← 使用已做 .upper() 的 role_str，避免大小写不一致导致 ADMIN 被拒
        )
        
        # 按《图片上传与显示规范》：image_url 原样返回，由前端用 getImageSrc 转完整 URL
        tab_response = LiveRoomTabResponse.model_validate(updated_tab)
        return success_response(data=tab_response.model_dump())
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except TabNotFoundException as e:
        logger.warning(f"Tab not found: tab_id={tab_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2002, message=str(e))
        )
    
    except InvalidParameterException as e:
        logger.warning(f"Invalid parameter: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except (DatabaseIntegrityException, DatabaseOperationException) as e:
        logger.error(f"Database error updating tab: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=f"数据库操作失败: {str(e)}")
        )
    
    except Exception as e:
        logger.error(f"Error updating tab: user_id={operator_user_id_log}, tab_id={tab_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@admin_tab_router.delete("/tabs/{tab_id}")
async def delete_room_tab(
    tab_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user)  # JWT token 字典
):
    """
    删除房间 Tab（管理端——Room Owner 或管理员均可操作）

     权限：Room Owner 或 ADMIN/SUPERADMIN
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user.get("user_id"))
    role = current_user.get("role")  # ← 使用.get()方法，字符串格式
    role_str = role.upper() if role else "REGULAR"

    try:
        user_role = LiveRoomMessageUserRole[role_str]
    except KeyError:
        user_role = LiveRoomMessageUserRole.REGULAR
    
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    operator_user_id_log = str(user_id)
    tab_id_log = str(tab_id)
    
    logger.info(f"管理端 {operator_user_id_log} deleting tab {tab_id_log}")
    
    try:
        # 调用 Service 层
        service = TabService(db)
        # ← 修改：传递role参数（字符串格式）
        deleted_tab = await service.delete_tab(
            user_id=user_id, 
            user_role=user_role, 
            tab_id=tab_id,
            role=role_str  # ← 使用已做 .upper() 的 role_str，避免大小写不一致导致 ADMIN 被拒
        )
        
        return success_response(data={"message": "Tab 删除成功", "tab_id": str(deleted_tab.id)})
    
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={operator_user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    
    except TabNotFoundException as e:
        logger.warning(f"Tab not found: tab_id={tab_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2002, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"Error deleting tab: user_id={operator_user_id_log}, tab_id={tab_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )




# ==================== Public 留言端点 ====================

@public_message_router.post("/rooms/{room_id}/messages")
async def send_message(
    room_id: uuid.UUID,
    obj_in: LiveRoomMessageCreate = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user)  # JWT token 字典
):
    """
    发送留言
    
    权限：所有登录用户
    限制：普通用户不能发送包含 URL 的留言
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user.get("user_id"))
    role = current_user.get("role")  # ← 使用.get()方法，字符串格式
    role_str = role.upper() if role else "REGULAR"
    try:
        user_role = LiveRoomMessageUserRole[role_str]
    except KeyError:
        user_role = LiveRoomMessageUserRole.REGULAR
    
    # 从当前用户信息中提取一个可用于展示的昵称/名称
    user_display_name = (
        current_user.get("nickname")
        or current_user.get("username")
        or current_user.get("email")
    )
    user_avatar_url = current_user.get("avatar_url")
    
    # [学院派规范 5.1] 安全异步异常处理：提前提取日志变量
    user_id_log = str(user_id)
    user_role_log = str(user_role.value) if hasattr(user_role, 'value') else str(user_role)
    room_id_log = str(room_id)
    
    logger.info(f"User {user_id_log} (role={user_role_log}) sending message to room {room_id_log}")
    
    try:
        # 调用 Service 层
        service = MessageService(db)
        # ← 修改：传递role参数（字符串格式），并附带用户展示名称/头像快照
        new_msg = await service.create_message(
            user_id=user_id, 
            user_role=user_role, 
            room_id=room_id, 
            obj_in=obj_in,
            role=role,  # ← 新增：字符串格式的role
            user_display_name=user_display_name,
            user_avatar_url=user_avatar_url,
        )
        
        # [关键] 响应规范（学院派 5.2）：使用 LiveRoomMessagePostResponse
        response_data = LiveRoomMessagePostResponse.model_validate(new_msg)
        # 如果 ORM 对象中包含 extra.user_display_name，则同步到响应模型中
        extra = getattr(new_msg, "extra", None)
        if isinstance(extra, dict):
            display_name = extra.get("user_display_name")
            if display_name:
                response_data = response_data.model_copy(update={"user_display_name": display_name})

        # PR 3: WebSocket 广播 + 缓存失效
        response_dict = response_data.model_dump()
        await message_push_manager.broadcast_new_message(room_id, response_dict)
        await invalidate_message_cache(room_id)

        return success_response(data=response_dict)
    
    except (RoomNotFoundException, NotFoundException) as e:  # ← 新增：捕获NotFoundException（404伪装）
        # ← 新增：返回404（隐藏Private房间存在性）
        logger.warning(f"Room not found or access denied: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    
    except ContentSafetyBlockedException as e:
        # ← 新增：内容违规拦截 → 422/2005（避免被下方 except Exception 吞成 500，与全局 handler 语义一致）
        logger.warning(f"Content safety blocked: user_id={user_id_log}, room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message)
        )
    
    except InvalidParameterException as e:
        # [关键] 捕获 URL 过滤异常（code=4004）
        logger.warning(f"Invalid parameter: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except (DatabaseIntegrityException, DatabaseOperationException) as e:
        logger.error(f"Database error creating message: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=f"数据库操作失败: {str(e)}")
        )
    
    except Exception as e:
        logger.error(f"Error sending message: user_id={user_id_log}, room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@public_message_router.get("/rooms/{room_id}/messages")
async def get_room_messages(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    size: int = Query(20, ge=1, le=100, description="每页大小，最大 100"),
    since: Optional[datetime] = Query(None, description="获取该时间之后的留言"),
    current_user: Optional[Dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取房间留言列表（分页）
    
    权限：所有用户（包括未登录），但需要检查Room可见性
    """
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    room_id_log = str(room_id)
    
    logger.info(f"Getting messages for room {room_id_log}, page={page}, size={size}, user_id={user_id}, role={role}")
    
    try:
        # PR 3: 尝试从缓存读取
        if since is None:
            cached = await get_cached_messages(room_id, page, size)
            if cached is not None:
                cached_items, cached_total = cached
                uid_list = []
                for item in cached_items:
                    try:
                        uid_list.append(uuid.UUID(str(item.get("user_id", ""))))
                    except (ValueError, TypeError):
                        pass
                profiles = await fetch_user_profiles(uid_list) if uid_list else {}
                deactivated_ids_cached = await filter_deactivated_user_ids(uid_list) if uid_list else set()
                items_rebuilt = []
                for item in cached_items:
                    try:
                        uid = uuid.UUID(str(item.get("user_id", "")))
                    except (ValueError, TypeError):
                        uid = None
                    profile = profiles.get(str(uid)) if uid else None
                    payload = dict(item)
                    if profile and profile.get("nickname"):
                        payload["user_display_name"] = profile["nickname"]
                    if uid and uid in deactivated_ids_cached:
                        payload["user_display_name"] = "账号已注销"
                        payload["user"] = {"nickname": "账号已注销", "avatar_url": None}
                    elif profile is not None:
                        payload["user"] = {
                            "nickname": payload.get("user_display_name"),
                            "avatar_url": profile.get("avatar_url"),
                        }
                    items_rebuilt.append(LiveRoomMessageListResponseItem(**payload))
                paginated = PaginatedLiveRoomMessageResponse(
                    total=cached_total, page=page, size=size, items=items_rebuilt
                )
                return success_response(data=paginated.model_dump())

        service = MessageService(db)
        messages, total = await service.get_messages(room_id, page, size, since, user_id=user_id, role=role)

        message_items = []
        for msg in messages:
            item = LiveRoomMessageListResponseItem.model_validate(msg)
            extra = getattr(msg, "extra", None)
            if isinstance(extra, dict):
                display_name = extra.get("user_display_name")
                if display_name:
                    item = item.model_copy(update={"user_display_name": display_name})
            message_items.append(item)

        # PR 3: 用户资料同步（拿到的 profiles 覆盖到对应消息项，含头像）
        uid_list = [msg.user_id for msg in messages]
        profiles = await fetch_user_profiles(uid_list) if uid_list else {}
        if profiles:
            for i, msg in enumerate(messages):
                uid = str(msg.user_id)
                profile = profiles.get(uid)
                if profile and profile.get("nickname"):
                    message_items[i] = message_items[i].model_copy(
                        update={"user_display_name": profile["nickname"]}
                    )
                # 头像回填：batch 命中则头像以个人中心为准（可为 null）
                if profile is not None:
                    from app.schemas.live_features import MessageUserInfo
                    cur = message_items[i]
                    user_info = MessageUserInfo(
                        nickname=cur.user_display_name,
                        avatar_url=profile.get("avatar_url"),
                    )
                    message_items[i] = cur.model_copy(update={"user": user_info})

        # PR 4 (D3): 注销作者占位覆盖
        deactivated_ids = await filter_deactivated_user_ids(uid_list) if uid_list else set()
        if deactivated_ids:
            for i, msg in enumerate(messages):
                if msg.user_id in deactivated_ids:
                    from app.schemas.live_features import MessageUserInfo
                    message_items[i] = message_items[i].model_copy(
                        update={
                            "user_display_name": "账号已注销",
                            "user": MessageUserInfo(nickname="账号已注销", avatar_url=None),
                        }
                    )

        paginated_data = PaginatedLiveRoomMessageResponse(
            total=total, page=page, size=size, items=message_items
        )

        # PR 3: 写入缓存
        if since is None:
            await set_cached_messages(
                room_id, page, size,
                [item.model_dump(mode="json") for item in message_items],
                total,
            )

        return success_response(data=paginated_data.model_dump())
    
    except (RoomNotFoundException, NotFoundException) as e:  # ← 新增：捕获NotFoundException（404伪装）
        logger.warning(f"Room not found or access denied: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    
    except Exception as e:
        logger.error(f"Error getting messages: room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )


@public_message_router.delete("/rooms/{room_id}/messages/{message_id}")
async def delete_room_message(
    room_id: uuid.UUID,
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: Dict = Depends(get_current_user),
):
    """删除留言（管理员可删任意；普通用户只可删自己的）"""
    user_id = uuid.UUID(current_user.get("user_id"))
    role = current_user.get("role")
    try:
        service = MessageService(db)
        await service.delete_message(room_id, message_id, user_id, role)
        return success_response(message="留言删除成功", data=None)
    except PermissionDeniedException as e:
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e)),
        )
    except MessageNotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e)),
        )
    except RoomNotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e)),
        )
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message=f"内部错误: {str(e)}"),
        )


# ==================== PR 3: 管理端留言端点 ====================

@admin_message_router.get("/messages")
async def admin_get_messages(
    query: AdminMessageQueryParams = Depends(),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role")
    try:
        service = MessageService(db)
        result = await service.admin_list_messages(query, role)
        return success_response(data=result.model_dump(mode="json"))
    except PermissionDeniedException:
        return JSONResponse(status_code=403, content=error_response(code=3003, message="权限不足：仅管理员可执行此操作"))
    except Exception as e:
        logger.error(f"Admin list messages error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库查询错误"))


@admin_message_router.post("/messages/batch-delete")
async def admin_batch_delete_messages(
    body: BatchDeleteRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role")
    try:
        service = MessageService(db)
        # P1-2: 删除前先查 room_id，用于精准失效缓存
        affected_room_ids = set()
        if body.message_ids:
            from sqlalchemy import select
            from app.models.live_features import LiveRoomMessage
            room_ids_result = await db.execute(
                select(LiveRoomMessage.room_id).where(
                    LiveRoomMessage.id.in_(body.message_ids)
                )
            )
            affected_room_ids = set(row[0] for row in room_ids_result if row[0])
        deleted, failed = await service.admin_batch_delete(body.message_ids, role)
        for rid in affected_room_ids:
            await invalidate_message_cache(rid)
        return success_response(message=f"成功删除{deleted}条留言", data={"deleted_count": deleted, "failed_count": failed})
    except PermissionDeniedException:
        return JSONResponse(status_code=403, content=error_response(code=3003, message="权限不足"))
    except Exception as e:
        logger.error(f"Admin batch delete error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作失败"))


@admin_message_router.delete("/rooms/{room_id}/messages")
async def admin_clear_room_messages(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role")
    try:
        service = MessageService(db)
        deleted = await service.admin_clear_room_messages(room_id, role)
        await invalidate_message_cache(room_id)
        return success_response(message="已清空该直播间所有留言", data={"deleted_count": deleted})
    except PermissionDeniedException:
        return JSONResponse(status_code=403, content=error_response(code=3003, message="权限不足"))
    except NotFoundException:
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except Exception as e:
        logger.error(f"Admin clear room messages error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作失败"))


# ==================== PR 3: WebSocket 留言推送 ====================

@message_ws_router.websocket("/ws/rooms/{room_id}/messages")
async def room_messages_websocket(
    websocket: WebSocket,
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """留言实时推送 WebSocket（H3 修复：鉴权 + 房间可见性校验）

    - 匿名（无 token）：仅可订阅公开房间
    - 登录（?token=<access_token>）：订阅可见房间（公开/本人私有/管理员）
    - 校验失败：关闭连接（4401=未认证，4403=无权，4404=房间不存在）
    """
    # 1. 可选鉴权：query 参数 token（WebSocket 无法携带自定义 Header）
    from app.core.auth import JWTAuth
    from app.core.deps import _ensure_session_not_revoked
    from app.crud import room as crud_room
    from app.exceptions import NotFoundException

    user = None
    token = websocket.query_params.get("token")
    if token:
        try:
            user = JWTAuth.verify_token(token)
            user["role"] = user.get("role", "REGULAR").upper()
            await _ensure_session_not_revoked(user)
        except HTTPException:
            await websocket.close(code=4401)
            return

    # 2. 房间可见性校验（方案 B：公开房间匿名可订阅；私有房间仅创建者/管理员可订阅 WS，其余 close 4403。
    #    REST 读路径为 unlisted 放行（check_room_visibility），WS 保持保守语义，保护 H3 鉴权成果）
    try:
        room = await crud_room.get(db, room_id)
        if room is None:
            await websocket.close(code=4404)
            return
        user_id = uuid.UUID(user["user_id"]) if user else None
        role = user.get("role") if user else None
        if room.is_private:
            is_owner_or_admin = (
                user is not None
                and (
                    role in ('ADMIN', 'SUPERADMIN')
                    or room.user_id == user_id
                )
            )
            if not is_owner_or_admin:
                await websocket.close(code=4403)
                return
    except (NotFoundException, PermissionDeniedException, ValueError):
        await websocket.close(code=4403)
        return

    await message_push_manager.connect(room_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        message_push_manager.disconnect(room_id, websocket)


# ==================== Public Tab 端点 ====================

public_tab_router = APIRouter(tags=["Public - Tabs"])


@public_tab_router.get("/rooms/{room_id}/tabs")
async def list_room_tabs_public(
    room_id: uuid.UUID,
    current_user: Optional[Dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db),
):
    """
    获取房间 Tab 列表（公开端点）

    权限（继承 Room 的 is_private 可见性，2026-08-11 unlisted 语义）：
    - 公开房间（is_private=False）：所有用户可访问，含未登录匿名用户
    - 私有房间（is_private=True）：任何人持 room_id 可读（unlisted，不进发现层）；写操作仍限创建者/管理员
    """
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    room_id_log = str(room_id)

    try:
        service = TabService(db)

        # 1. 检查房间是否存在
        room = await service._check_room_exists(room_id)

        # 2. 私有房间可见性校验（继承 Room 的 is_private 规则）
        # 使用公共权限函数统一校验
        check_room_visibility(room, user_id, role)

        # 3. 获取激活的 Tab
        tabs = await crud_live_features.get_active_by_room_id(db, room_id)
        tabs_data = [LiveRoomTabResponse.model_validate(tab).model_dump() for tab in tabs]

        return success_response(data={"items": tabs_data, "total": len(tabs_data)})

    except (RoomNotFoundException, NotFoundException):
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )

    except Exception as e:
        logger.error(f"Error listing public tabs: room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message="内部错误")
        )
