"""
LiveCore Service - Room API Endpoints

This module contains all API endpoints for LiveRoom resource,
providing REST API interface for room operations.
"""

import uuid
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.schemas.live_core import (
    LiveRoomCreate,
    LiveRoomUpdate,
    LiveRoomResponse,
    ScheduledSessionCreate,
    LiveSessionCreate,
    TestRoomEnsureRequest,
)
from app.services.room_service import RoomService
from app.services.session_service import SessionService
from app.models.live_core import LiveSessionStatus
from app.crud import room as crud_room
from app.exceptions import (
    RoomNotFoundException,
    ActionForbiddenException,
    ParentRoomNotFoundException,
    NotFoundException,
    PermissionDeniedException,
    DatabaseIntegrityException,
    InvalidParameterException,
)
from app.content_safety.exceptions import ContentSafetyBlockedException, ContentSafetyServiceException
from app.core.response import success_response, error_response

# 设置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()
users_me_rooms_router = APIRouter()


@router.post("", response_model=Dict[str, Any])
async def create_room(
    room_in: LiveRoomCreate,
    current_user: dict = Depends(get_current_user),  # 新增认证参数
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """创建直播房间"""
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理创建房间请求: user_id={current_user['user_id']}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # ← 新增：提取用户信息（在try之前）
        user_id = uuid.UUID(current_user["user_id"])  # 从JWT的user_id字段提取
        role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
        # 旧 Token 无 can_stream 字段 → 视为 true（默认可播；禁止开播会吊销后签发显式 false）
        can_stream = bool(current_user.get("can_stream", True))
        
        # ← 修改：传递权限参数与开播资格
        new_room = await service.create_new_room(
            room_in=room_in,
            user_id=user_id,
            role=role,
            can_stream=can_stream,
        )
        logger.info(f"成功创建直播房间: {new_room.id}")
        
        # 构建响应数据
        response_data = {
            "id": str(new_room.id),
            "title": new_room.title,
            "description": new_room.description,
            "stream_key": new_room.stream_key,
            "record_by_default": new_room.record_by_default,
            "created_at": new_room.created_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)

    except PermissionDeniedException:
        logger.warning(f"创建房间被拒绝：开播功能已被禁用 user_id={current_user.get('user_id')}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message="开播功能已被禁用")
        )
        
    except ParentRoomNotFoundException:
        logger.warning(f"主会场不存在: {room_in.parent_room_id}")
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=2004,
                message="主会场不存在",
                data={"parent_room_id": str(room_in.parent_room_id)}
            )
        )


@router.get("", response_model=Dict[str, Any])
async def get_rooms(
    request: Request, # 2. 将 Request 对象注入到你的端点中
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    q: str = Query(None, max_length=100, description="搜索关键词"),
    sort: str = Query(None, description="排序字段，格式为 field:direction，例如 created_at:desc"),
    owner_only: bool = Query(False, description="是否仅返回当前用户创建的房间（管理后台 RoomList 视图）"),
    user_id: str = Query(None, description="可选的用户ID过滤"),
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth

    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取直播房间列表（支持搜索）"""
    # ← 新增：提取用户信息（可能为None）
    user_id_uuid = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理获取房间列表请求: user_id={user_id_uuid}, role={role}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    if q:
        # 使用搜索逻辑
        # 注意：search_rooms 不需要 user_id 过滤参数，因为它只搜索？
        # 但提示词中的 search_rooms 定义为 search_rooms(self, public_id, q, page, size, sort)
        # 并没有 user_id 参数用于过滤其他用户。
        # 提示词 Doc-API Section 5.2: "Search：所有登录用户均可访问，支持按 user_id 过滤自己的房间。"
        # Wait, the prompt for search_rooms in Service Layer (Section 5.2) does NOT have a user_id filter param.
        # It only has public_id (current user).
        # And prompt says:
        # 2. 若 q 非空：
        #    - ...
        #    - UUID 格式：...
        #    - 非 UUID 格式：...
        # 3. 调用 crud_room.list_with_search
        
        # However, the prompt Section 8.2 says "Search 权限规则：所有登录用户可搜索所有房间。支持按 user_id 过滤（仅查看自己的房间）"
        # This implies we SHOULD support filtering by user_id even in search.
        # But `list_with_search` in CRUD layer only implemented filters for 'id_or_title'.
        # It does accept `filters` dict.
        # Let's check `app/crud/room.py` `list_with_search` again. It takes `filters`.
        # If I want to support user_id filter in search, I should have added it to CRUD.
        # But I strictly followed the prompt for CRUD which only mentioned id/title search.
        
        # Wait, the prompt for `list_with_search` implementation in CRUD layer says:
        # "支持 ID 精确匹配 ... 支持标题模糊匹配 ..."
        # It did NOT ask to implement user_id filtering in `list_with_search`.
        
        # So, for `q` search, we might lose user_id filtering capability unless we add it ourselves or the prompt implied it.
        # The prompt for `list_rooms` API endpoint says:
        # 2. 调用 `room_service.search_rooms(public_id=public_id, q=q, page=page, size=size, sort=sort)`
        # It does NOT pass `user_id` filter to `search_rooms`.
        
        # So I will follow the prompt for `search_rooms` call.
        
        # However, existing `get_rooms` supports `user_id` filter.
        # If `q` is provided, we switch to `search_rooms`.
        
        result = await service.search_rooms(
            public_id=user_id_uuid,
            q=q,
            page=page,
            size=size,
            sort=sort,
            role=role  # ← 新增：传递role参数
        )
        # search_rooms returns a dict with items/total
        rooms = result['items']
        total = result['total']
        
    else:
        # ← 修改：传递权限参数与 owner_only 标志
        rooms, total = await service.get_room_list(
            page=page,
            size=size,
            user_id=user_id_uuid,
            role=role,
            owner_only=owner_only,
        )
    
    # 构建响应数据
    items = []
    base_url = str(request.base_url) # -> "http://localhost:8000/" 或 "https://yourdomain.com/"
    # 如果 base_url 结尾有斜杠，可以去掉
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    from app.crud.content_management import get_primary_category_names_map
    primary_name_map = await get_primary_category_names_map(db, [room.id for room in rooms])

    for room in rooms:
        # 【关键修改】在这里进行URL拼接
        full_cover_url = None
        if room.cover_url:
            # 检查是否 ಈಗಾಗಲೇ是完整 URL，避免重复拼接
            if not (room.cover_url.startswith("http://") or room.cover_url.startswith("https://")):
                relative_url = room.cover_url if room.cover_url.startswith('/') else f'/{room.cover_url}'
                full_cover_url = f"{base_url}{relative_url}"
            else:
                # 已经是完整 URL，直接使用
                full_cover_url = room.cover_url

        item = {
            "id": str(room.id),
            "title": room.title,
            "cover_url": full_cover_url,
            "parent_room_id": str(room.parent_room_id) if room.parent_room_id is not None else None,
            "created_at": room.created_at.isoformat() + "Z",
            "category_id": str(room.category_id) if getattr(room, "category_id", None) else None,
            "primary_category_name": primary_name_map.get(room.id),
        }
        items.append(item)
    
    paginated_data = {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }
    
    logger.info(f"成功获取房间列表: 总数={total}, 当前页={page}")
    
    return success_response(data=paginated_data)


@users_me_rooms_router.get("/rooms", response_model=Dict[str, Any])
async def get_my_rooms(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    q: str = Query(None, max_length=100, description="搜索关键词"),
    sort: str = Query(None, description="排序字段，格式为 field:direction，例如 created_at:desc"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取当前用户创建的直播房间列表"""
    user_id_uuid = uuid.UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR")

    logger.info(f"开始处理获取我的房间列表请求: user_id={user_id_uuid}, role={role}")

    service = RoomService(db=db)

    if q:
        result = await service.search_rooms(
            public_id=user_id_uuid,
            q=q,
            page=page,
            size=size,
            sort=sort,
            role=role,
            owner_only=True,
        )
        rooms = result["items"]
        total = result["total"]
    else:
        rooms, total = await service.get_room_list(
            page=page,
            size=size,
            user_id=user_id_uuid,
            role=role,
            owner_only=True,
        )

    items = []
    base_url = str(request.base_url)
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    for room in rooms:
        full_cover_url = None
        if room.cover_url:
            if not (room.cover_url.startswith("http://") or room.cover_url.startswith("https://")):
                relative_url = room.cover_url if room.cover_url.startswith('/') else f'/{room.cover_url}'
                full_cover_url = f"{base_url}{relative_url}"
            else:
                full_cover_url = room.cover_url

        items.append({
            "id": str(room.id),
            "title": room.title,
            "cover_url": full_cover_url,
            "parent_room_id": str(room.parent_room_id) if room.parent_room_id is not None else None,
            # 文档 18：区分正式间 / 测播间；前端「测试连接」依赖这两项
            "is_private": bool(room.is_private),
            "source_room_id": str(room.source_room_id) if room.source_room_id is not None else None,
            "created_at": room.created_at.isoformat() + "Z"
        })

    paginated_data = {
        "total": total,
        "page": page,
        "size": size,
        "items": items
    }

    logger.info(f"成功获取我的房间列表: 总数={total}, 当前页={page}")

    return success_response(data=paginated_data)


@router.get("/{room_id}", response_model=Dict[str, Any])
async def get_room(
    request: Request,  # 添加 Request 参数用于拼接 cover_url
    room_id: uuid.UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取单个直播房间详情"""
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理获取房间详情请求: user_id={user_id}, role={role}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # ← 修改：传递权限参数
        room = await service.get_room_details(room_id=room_id, user_id=user_id, role=role)
        logger.info(f"成功获取房间详情: {room_id}")
        
        # 获取 base_url 用于拼接完整的 cover_url
        base_url = str(request.base_url)
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        # 拼接完整的 cover_url（仅当是相对路径时）
        full_cover_url = room.cover_url
        if full_cover_url:
            if not (full_cover_url.startswith("http://") or full_cover_url.startswith("https://")):
                relative_url = full_cover_url if full_cover_url.startswith('/') else f'/{full_cover_url}'
                full_cover_url = f"{base_url}{relative_url}"
        
        # 构建响应数据
        from app.crud.content_management import get_primary_category_name
        primary_category_name = await get_primary_category_name(db, room.id)
        response_data = {
            "id": str(room.id),
            "title": room.title,
            "description": room.description,
            "cover_url": full_cover_url,
            "stream_key": room.stream_key,
            "parent_room_id": str(room.parent_room_id) if room.parent_room_id is not None else None,
            "is_private": room.is_private,
            "record_by_default": room.record_by_default,
            "category_id": str(room.category_id) if getattr(room, "category_id", None) else None,
            "primary_category_name": primary_category_name,
            "created_at": room.created_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except (RoomNotFoundException, NotFoundException):  # ← 新增：捕获NotFoundException（404伪装）
        logger.warning(f"房间不存在或无权访问: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )


@router.post("/{room_id}/test-room", response_model=Dict[str, Any])
async def ensure_test_room(
    request: Request,
    room_id: uuid.UUID,
    body: TestRoomEnsureRequest = TestRoomEnsureRequest(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    为正式间确保关联测播间（文档 18，幂等）。
    测播间 is_private=true，不进发现列表；持链可观看。
    """
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR")
    title_suffix = body.title_suffix
    logger.info(
        "测试连接 ensure_test_room: source=%s user=%s role=%s",
        room_id,
        user_id,
        role,
    )
    service = RoomService(db=db)
    try:
        source, test_room, created = await service.ensure_test_room(
            room_id=room_id,
            user_id=user_id,
            role=role,
            title_suffix=title_suffix,
        )

        base_url = str(request.base_url).rstrip("/")
        full_cover_url = test_room.cover_url
        if full_cover_url and not (
            full_cover_url.startswith("http://") or full_cover_url.startswith("https://")
        ):
            relative = full_cover_url if full_cover_url.startswith("/") else f"/{full_cover_url}"
            full_cover_url = f"{base_url}{relative}"

        return success_response(
            data={
                "source_room_id": str(source.id),
                "test_room": {
                    "id": str(test_room.id),
                    "title": test_room.title,
                    "is_private": bool(test_room.is_private),
                    "stream_key": test_room.stream_key,
                    "cover_url": full_cover_url,
                    "source_room_id": str(test_room.source_room_id)
                    if test_room.source_room_id
                    else str(source.id),
                    "created_at": test_room.created_at.isoformat() + "Z",
                },
                "created": created,
            }
        )
    except RoomNotFoundException:
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)},
            ),
        )
    except PermissionDeniedException as e:
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message="权限不足", data={"error": str(e)}),
        )
    except InvalidParameterException as e:
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message),
        )
    except ContentSafetyBlockedException as e:
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message),
        )
    except ContentSafetyServiceException as e:
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message),
        )


@router.patch("/{room_id}", response_model=Dict[str, Any])
async def update_room(
    room_id: uuid.UUID,
    room_update: LiveRoomUpdate,
    current_user: dict = Depends(get_current_user),  # 新增认证参数
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """更新直播房间信息"""
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理更新房间请求: user_id={current_user['user_id']}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # ← 新增：提取用户信息（在try之前）
        user_id = uuid.UUID(current_user["user_id"])  # 从JWT的user_id字段提取
        role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
        
        # ← 修改：传递权限参数
        updated_room = await service.update_room_info(
            room_id=room_id, 
            room_update=room_update,
            user_id=user_id,
            role=role  # ← 新增：传递role参数
        )
        logger.info(f"成功更新房间信息: {room_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(updated_room.id),
            "title": updated_room.title,
            "description": updated_room.description,
            "updated_at": updated_room.updated_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except RoomNotFoundException:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )
    except PermissionDeniedException as e:  # ← 新增：捕获权限拒绝异常
        logger.warning(f"无权修改房间: room_id={room_id}, user_id={current_user['user_id']}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="权限不足",
                data={"error": str(e)}
            )
        )
    except ActionForbiddenException as e:
        logger.warning(f"房间正在直播，无法修改: {room_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2002,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        )
    except ContentSafetyBlockedException as e:
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message)
        )
    except ContentSafetyServiceException as e:
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message)
        )


@router.delete("/{room_id}", response_model=Dict[str, Any])
async def delete_room(
    room_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),  # 新增认证参数
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """删除直播房间"""
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理删除房间请求: user_id={current_user['user_id']}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # ← 新增：提取用户信息（在try之前）
        user_id = uuid.UUID(current_user["user_id"])  # 从JWT的user_id字段提取
        role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
        
        # ← 修改：传递权限参数
        deleted_room = await service.delete_room(room_id=room_id, user_id=user_id, role=role)
        logger.info(f"成功删除房间: {room_id}")
        
        # 构建响应数据
        response_data = {
            "id": str(deleted_room.id),
            "status": "deleted"
        }
        
        return success_response(data=response_data)
        
    except RoomNotFoundException:
        logger.warning(f"房间不存在: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )
    except PermissionDeniedException as e:  # ← 新增：捕获权限拒绝异常
        logger.warning(f"无权删除房间: room_id={room_id}, user_id={current_user['user_id']}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="权限不足",
                data={"error": str(e)}
            )
        )
    except ActionForbiddenException as e:
        logger.warning(f"房间正在直播，无法删除: {room_id}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=2003,
                message="业务逻辑错误",
                data={"error": str(e)}
            )
        )
    except DatabaseIntegrityException as e:
        logger.warning(f"删除房间失败（关联约束）: room_id={room_id}, error={e}")
        return JSONResponse(
            status_code=409,
            content=error_response(
                code=2005,
                message="无法删除：存在关联数据，请先解除品牌/专家等关联或联系管理员",
                data={"resource": "Room", "id": str(room_id), "error": str(e)}
            )
        )


@router.get("/{room_id}/sub-venues", response_model=Dict[str, Any])
async def get_sub_venues(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取分会场列表"""
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理获取分会场列表请求: user_id={user_id}, role={role}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # ← 修改：传递权限参数
        sub_venues, total = await service.get_sub_venue_list(
            parent_room_id=room_id,
            page=page,
            size=size,
            user_id=user_id,
            role=role  # ← 新增：传递role参数
        )
        
        # 构建响应数据
        items = []
        for venue in sub_venues:
            item = {
                "id": str(venue['id']),
                "title": venue['title'],
                "live_status": venue['live_status'],
                "current_session_id": str(venue['current_session_id']) if venue['current_session_id'] else None
            }
            items.append(item)
        
        paginated_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": items
        }
        
        logger.info(f"成功获取分会场列表: 总数={total}, 当前页={page}")
        
        return success_response(data=paginated_data)
        
    except (RoomNotFoundException, NotFoundException):  # ← 新增：捕获NotFoundException（404伪装）
        logger.warning(f"主会场不存在或无权访问: {room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )


@router.post("/{room_id}/sessions", response_model=Dict[str, Any])
async def create_scheduled_session(
    room_id: uuid.UUID,
    scheduled_session_in: ScheduledSessionCreate,
    current_user: dict = Depends(get_current_user),  # 新增认证参数
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """为指定房间创建一个计划中的直播场次"""
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理创建计划场次请求: user_id={current_user['user_id']}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # ← 新增：提取用户信息（在try之前）
        user_id = uuid.UUID(current_user["user_id"])  # 从JWT的user_id字段提取
        role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
        
        # ← 修改：传递权限参数
        new_session = await service.create_scheduled_session(
            room_id=room_id,
            session_in=scheduled_session_in,
            user_id=user_id,
            role=role  # ← 新增：传递role参数
        )
        logger.info(f"成功创建计划场次: session_id={new_session.id}")
        
        # 构建响应数据
        response_data = {
            "id": str(new_session.id),
            "room_id": str(new_session.room_id),
            "status": new_session.status.value,
            "start_time": new_session.start_time.isoformat() + "Z",
            "end_time": None,
            "video_id": None,
            "created_at": new_session.created_at.isoformat() + "Z",
            "updated_at": new_session.updated_at.isoformat() + "Z"
        }
        
        return success_response(data=response_data)
        
    except (RoomNotFoundException, NotFoundException):  # ← 新增：捕获NotFoundException（404伪装）
        logger.warning(f"房间不存在或无权访问: room_id={room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )
    except PermissionDeniedException as e:  # ← 新增：捕获权限拒绝异常
        logger.warning(f"无权创建场次: room_id={room_id}, user_id={current_user['user_id']}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="权限不足",
                data={"error": str(e)}
            )
        )


@router.get("/{room_id}/sessions", response_model=Dict[str, Any])
async def get_room_sessions(
    room_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取指定房间的直播场次列表"""
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # 在业务逻辑开始前记录日志
    logger.info(f"开始处理获取房间场次列表请求: user_id={user_id}, role={role}")
    
    # 实例化服务层
    service = SessionService(db=db)
    
    try:
        # ← 修改：传递权限参数
        sessions, total = await service.get_sessions_by_room(
            room_id=room_id,
            page=page,
            size=size,
            user_id=user_id,
            role=role  # ← 新增：传递role参数
        )
        
        # 构建响应数据
        items = []
        for session in sessions:
            item = {
                "id": str(session.id),
                "room_id": str(session.room_id),
                "status": session.status.value,
                "start_time": session.start_time.isoformat() + "Z",
                "end_time": session.end_time.isoformat() + "Z" if session.end_time else None,
                "video_id": str(session.video_id) if session.video_id else None,
                "created_at": session.created_at.isoformat() + "Z",
                "updated_at": session.updated_at.isoformat() + "Z"
            }
            items.append(item)
        
        paginated_data = {
            "total": total,
            "page": page,
            "size": len(items),
            "items": items
        }
        
        logger.info(f"成功获取房间场次列表: room_id={room_id}, 返回{len(items)}条记录")
        
        return success_response(data=paginated_data)
        
    except (RoomNotFoundException, NotFoundException):  # ← 新增：捕获NotFoundException（404伪装）
        logger.warning(f"房间不存在或无权访问: room_id={room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )


@router.post("/{room_id}/cover", response_model=Dict[str, Any])
async def upload_room_cover(
    request: Request,
    room_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """为指定房间上传封面图片"""
    logger.info(f"开始上传封面: room_id={room_id}, user_id={current_user['user_id']}")
    
    # 实例化服务层
    service = RoomService(db=db)
    
    try:
        # ← 新增：提取用户信息（在try之前）
        user_id = uuid.UUID(current_user["user_id"])  # 从JWT的user_id字段提取
        role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
        
        # ← 修改：传递权限参数
        updated_room = await service.upload_room_cover(
            room_id=room_id,
            file=file,
            user_id=user_id,
            role=role  # ← 新增：传递role参数
        )
        
        logger.info(f"封面上传成功: room_id={room_id}")

        # 按《图片上传与显示规范》：返回相对路径，由前端用 BASE_API_URL 转完整 URL
        response_data = {
            "room_id": str(updated_room.id),
            "cover_url": updated_room.cover_url
        }
        
        return success_response(data=response_data)
        
    except RoomNotFoundException:
        logger.warning(f"房间不存在: room_id={room_id}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Room", "id": str(room_id)}
            )
        )
    except PermissionDeniedException as e:  # ← 新增：捕获权限拒绝异常
        logger.warning(f"无权上传封面: room_id={room_id}, user_id={current_user['user_id']}")
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="权限不足",
                data={"error": str(e)}
            )
        )
    except HTTPException as e:
        logger.warning(f"文件验证失败: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(
                code=2001,
                message="文件验证失败",
                data={"error": e.detail}
            )
        )
    except Exception as e:
        logger.error(f"封面上传失败: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=5001,
                message="文件上传失败",
                data={"error": "服务器内部错误"}
            )
        ) 