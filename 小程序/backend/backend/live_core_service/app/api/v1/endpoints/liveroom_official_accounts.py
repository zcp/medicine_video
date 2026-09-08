"""
直播间与公众号关联模块的 API 端点
"""
from typing import Optional
from uuid import UUID
import uuid as uuid_module
import logging

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import success_response, error_response
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.schemas.liveroom_official_accounts import (
    OfficialAccountCreate,
    OfficialAccountUpdate,
    LiveRoomOfficialAccountsSetRequest,
)
from app.services.liveroom_official_accounts_service import LiveroomOfficialAccountsService

logger = logging.getLogger(__name__)

service = LiveroomOfficialAccountsService()

# 管理端公众号 CRUD：挂载 prefix=/admin -> /admin/official-accounts, /admin/official-accounts/{account_id}
admin_official_accounts_router = APIRouter(tags=["直播间与公众号关联-管理端"])

# 公开：按房间查公众号 挂载 prefix=/rooms -> /rooms/{room_id}/official-accounts
rooms_official_accounts_router = APIRouter(tags=["直播间与公众号关联-公开"])

# 管理端：房间-公众号绑定 挂载 prefix=/admin/rooms -> /admin/rooms/{room_id}/official-accounts
admin_rooms_official_accounts_router = APIRouter(tags=["直播间与公众号关联-管理端-房间"])

# 按公众号查房间 挂载 prefix=/official-accounts -> /official-accounts/{account_id}/rooms
official_accounts_rooms_router = APIRouter(tags=["直播间与公众号关联-CSM"])


def _user_and_role(current_user: dict):
    user_id = UUID(current_user["user_id"])
    role = (current_user.get("role") or "REGULAR").upper()
    return user_id, role


# ---------- 管理端公众号 CRUD ----------

@admin_official_accounts_router.get("/official-accounts", summary="获取公众号列表（分页）")
async def get_official_accounts_admin(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(None),
    search_type: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    # 🚨 防御性编程：过滤前端误传的 "undefined"/"null" 字符串
    if q and str(q).strip().lower() in ("undefined", "null"):
        q = None
    if search_type == "id" and q and str(q).strip():
        try:
            uuid_module.UUID(str(q).strip())
        except (ValueError, TypeError):
            return JSONResponse(status_code=400, content=error_response(code=4001, message="无效的ID格式"))
    try:
        result = await service.get_official_accounts_admin(
            db, user_id, role, page=page, size=size, q=q, search_type=search_type, include_inactive=include_inactive
        )
        return JSONResponse(status_code=200, content=result)
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except Exception as e:
        logger.warning(f"获取公众号列表异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


@admin_official_accounts_router.get("/official-accounts/{account_id}", summary="获取公众号详情")
async def get_official_account_by_id(
    account_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    try:
        item = await service.get_official_account_by_id(db, user_id, role, account_id)
        return JSONResponse(status_code=200, content=success_response(data=item.model_dump(mode="json")))
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except NotFoundException:
        logger.warning(f"公众号不存在: account_id={account_id}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except Exception as e:
        logger.warning(f"获取公众号详情异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


@admin_official_accounts_router.post("/official-accounts", status_code=201, summary="创建公众号")
async def create_official_account(
    body: OfficialAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    try:
        item = await service.create_official_account(db, body, user_id, role)
        return JSONResponse(status_code=201, content=success_response(data=item.model_dump(mode="json")))
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except InvalidParameterException as e:
        code = getattr(e, "code", 4001)
        logger.warning(f"创建公众号参数错误: user_id={user_id_log}, error={e.message}")
        return JSONResponse(status_code=400, content=error_response(code=code, message=e.message))
    except Exception as e:
        logger.warning(f"创建公众号异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


@admin_official_accounts_router.patch("/official-accounts/{account_id}", summary="更新公众号")
async def update_official_account(
    account_id: UUID = Path(...),
    body: OfficialAccountUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    try:
        item = await service.update_official_account(db, account_id, body, user_id, role)
        return JSONResponse(status_code=200, content=success_response(data=item.model_dump(mode="json")))
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except NotFoundException:
        logger.warning(f"公众号不存在: account_id={account_id}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except InvalidParameterException as e:
        code = getattr(e, "code", 4001)
        logger.warning(f"更新公众号参数错误: user_id={user_id_log}, error={e.message}")
        return JSONResponse(status_code=400, content=error_response(code=code, message=e.message))
    except Exception as e:
        logger.warning(f"更新公众号异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


@admin_official_accounts_router.delete("/official-accounts/{account_id}", summary="软删除公众号")
async def soft_delete_official_account(
    account_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    try:
        result = await service.soft_delete_official_account(db, account_id, user_id, role)
        return JSONResponse(status_code=200, content=result)
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except NotFoundException:
        logger.warning(f"公众号不存在: account_id={account_id}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except Exception as e:
        logger.warning(f"软删除公众号异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


# ---------- 按房间查公众号（公开，Optional Auth）----------

@rooms_official_accounts_router.get("/{room_id}/official-accounts", summary="获取直播间关联公众号列表")
async def get_official_accounts_by_room_id(
    room_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    try:
        items = await service.get_official_accounts_by_room_id(db, room_id)
        data = [x.model_dump(mode="json") for x in items]
        return JSONResponse(status_code=200, content=success_response(data=data))
    except NotFoundException:
        logger.warning(f"房间不存在: room_id={room_id}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except Exception as e:
        logger.warning(f"获取房间公众号列表异常: room_id={room_id}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


# ---------- 管理端：房间-公众号绑定 ----------

@admin_rooms_official_accounts_router.post("/{room_id}/official-accounts", summary="批量设置直播间公众号")
async def set_room_official_accounts(
    room_id: UUID = Path(...),
    body: LiveRoomOfficialAccountsSetRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    try:
        result = await service.set_room_official_accounts(db, user_id, role, room_id, body)
        return JSONResponse(status_code=200, content=result)
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except NotFoundException:
        logger.warning(f"房间不存在: room_id={room_id}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except InvalidParameterException as e:
        code = getattr(e, "code", 4001)
        logger.warning(f"设置房间公众号参数错误: user_id={user_id_log}, error={e.message}")
        return JSONResponse(status_code=400, content=error_response(code=code, message=e.message))
    except Exception as e:
        logger.warning(f"设置房间公众号异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


@admin_rooms_official_accounts_router.delete("/{room_id}/official-accounts/{account_id}", summary="删除直播间单个公众号关联")
async def delete_room_official_account(
    room_id: UUID = Path(...),
    account_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    try:
        await service.delete_room_official_account(db, user_id, role, room_id, account_id)
        return JSONResponse(status_code=200, content=success_response())
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except NotFoundException:
        logger.warning(f"关联不存在: room_id={room_id}, account_id={account_id}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except Exception as e:
        logger.warning(f"删除房间公众号关联异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))


# ---------- 按公众号查房间（CSM）----------

@official_accounts_rooms_router.get("/{account_id}/rooms", summary="按公众号分页查直播间列表")
async def get_rooms_by_account_id(
    account_id: UUID = Path(...),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id, role = _user_and_role(current_user)
    user_id_log = str(user_id)[:8]
    try:
        result = await service.get_rooms_by_account_id(db, user_id, role, account_id, page=page, size=size)
        return JSONResponse(status_code=200, content=result)
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_log}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message="权限不足"))
    except NotFoundException:
        logger.warning(f"公众号不存在或已禁用: account_id={account_id}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message="资源不存在"))
    except Exception as e:
        logger.warning(f"按公众号查房间异常: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="内部服务器错误"))
