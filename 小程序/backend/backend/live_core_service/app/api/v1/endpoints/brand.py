"""
品牌模块的API层代码

本模块包含品牌模块所需的13个API端点：
- Brands API: 7个端点
- Brand_Topics API: 3个端点
- Brand_Rooms API: 3个端点
"""
import logging
from typing import Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, Body, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import success_response, error_response
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException,
    ConflictException
)
from app.schemas.brand import (
    BrandCreate, BrandUpdate,
    BrandTopicBindIn, BrandRoomBindIn
)
from app.services.brand_service import BrandService

logger = logging.getLogger(__name__)
router = APIRouter()  # ⚠️ 不指定prefix
brand_service = BrandService()


# ==================== Brands API端点 (7个) ====================

@router.get("/brands")
async def get_brands(
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    q: Optional[str] = Query(None, description="模糊搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> Any:
    """获取品牌列表（Public + Optional Auth）"""
    # 提取用户信息（可能为None）
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"

    # 🚨 防御性编程：过滤前端误传的 "undefined"/"null" 字符串
    if q and str(q).strip().lower() in ("undefined", "null"):
        q = None

    try:
        result = await brand_service.get_brands_list(db, limit, q, current_user_id, role)
        return result
        
    except Exception as e:
        logger.error(f"获取品牌列表异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/brands/{brand_id}/content")
async def get_brand_content(
    brand_id: UUID = Path(..., description="品牌ID"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> Any:
    """获取品牌详情及关联专题（Public + Optional Auth）"""
    # 提取用户信息（可能为None）
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"
    
    try:
        result = await brand_service.get_brand_content(db, brand_id, current_user_id, role)
        return result
        
    except NotFoundException as e:
        logger.warning(f"品牌不存在: user_id={user_id_for_logging}, brand_id={str(brand_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except Exception as e:
        logger.error(f"获取品牌详情异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.post("/admin/brands")
async def create_brand(
    brand_data: BrandCreate = Body(..., description="品牌创建数据"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """创建品牌（Strict Auth + Admin）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.create_brand(db, brand_data, current_user_id, role)
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except ConflictException as e:
        logger.warning(f"品牌名称冲突: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2002, message=str(e))
        )
    except InvalidParameterException as e:
        # ✅ 根据code判断是冲突（2003）还是参数验证失败（4001）
        if hasattr(e, 'code') and e.code == 2002:
            # code=2003表示品牌名称已存在（冲突）
            logger.warning(f"品牌名称冲突: user_id={user_id_for_logging}, error={str(e)}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=2002, message=str(e))
            )
        else:
            # code=4001表示其他参数验证失败
            logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message=str(e))
            )
    except Exception as e:
        logger.error(f"创建品牌异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/admin/brands")
async def get_brands_admin(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query("sort_order", description="排序字段"),
    name: Optional[str] = Query(None, description="品牌名称筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """获取品牌列表（Admin分页）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.get_brands_paginated(
            db, page, size, sort, name, is_active, current_user_id, role
        )
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取品牌列表异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/admin/brands/{brand_id}")
async def get_brand_admin(
    brand_id: UUID = Path(..., description="品牌ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """获取单个品牌（Admin）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.get_brand_by_id(db, brand_id, current_user_id, role)
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: user_id={user_id_for_logging}, brand_id={str(brand_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except Exception as e:
        logger.error(f"获取品牌详情异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.patch("/admin/brands/{brand_id}")
async def update_brand(
    brand_id: UUID = Path(..., description="品牌ID"),
    brand_data: BrandUpdate = Body(..., description="品牌更新数据"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """更新品牌（Admin）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.update_brand(db, brand_id, brand_data, current_user_id, role)
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: user_id={user_id_for_logging}, brand_id={str(brand_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except ConflictException as e:
        logger.warning(f"品牌名称冲突: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2002, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新品牌异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.delete("/admin/brands/{brand_id}")
async def delete_brand(
    brand_id: UUID = Path(..., description="品牌ID"),
    hard_delete: bool = Query(False, description="是否硬删除"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """删除品牌（Admin/SuperAdmin）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.delete_brand(db, brand_id, hard_delete, current_user_id, role)
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message=str(e))
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: user_id={user_id_for_logging}, brand_id={str(brand_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
        # backend/live_core_service/app/api/v1/endpoints/brand.py

    # 修改 delete_brand 端点（约第280-291行，在NotFoundException之后、ConflictException之前添加）
    except InvalidParameterException as e:
        # ✅ 根据code判断是冲突（2003）还是参数验证失败（4001）
        if hasattr(e, 'code') and e.code == 2003:
            # code=2003表示品牌被引用无法删除（冲突）
            logger.warning(f"品牌被引用: user_id={user_id_for_logging}, error={str(e)}")
            return JSONResponse(
                status_code=409,
                content=error_response(code=2003, message=str(e))
            )
        else:
            # code=4001表示其他参数验证失败
            logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message=str(e))
            )
    except ConflictException as e:
        logger.warning(f"品牌被引用: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=409,
            content=error_response(code=2003, message=str(e))
        )
    except Exception as e:
        logger.error(f"删除品牌异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.post("/admin/brands/{brand_id}/logo")
async def upload_brand_logo(
    brand_id: UUID = Path(..., description="品牌ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    为指定品牌上传Logo图片（Admin）
    
    完全复用 FileHandler 的实现逻辑：
    - 文件校验：PNG, JPG, GIF 格式，5MB 以内
    - 权限验证：仅 ADMIN/SUPERADMIN 可上传
    - 存储路径：/media/brands/{brand_id}/logo_{timestamp}.{ext}
    
    Args:
        brand_id: 品牌UUID
        file: 上传的Logo文件
        current_user: 当前登录用户信息
        db: 数据库会话
        
    Returns:
        标准成功响应，包含 brand_id 和 logo_url
        
    Raises:
        404: 品牌不存在
        403: 权限不足
        400: 文件格式或大小不符合要求
    """
    # 提取用户信息（在try之前）
    user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    
    # 提前提取用于日志的变量
    user_id_for_logging = str(user_id)[:8]
    brand_id_for_logging = str(brand_id)[:8]
    
    logger.info(f"开始上传品牌Logo: brand_id={brand_id_for_logging}, user_id={user_id_for_logging}")
    
    try:
        # 调用 Service 层上传Logo
        logo_url = await brand_service.upload_brand_logo(
            db=db,
            brand_id=brand_id,
            file=file,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(
            data={
                "brand_id": str(brand_id),
                "logo_url": logo_url
            },
            message="Logo上传成功"
        )
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: brand_id={brand_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except HTTPException as e:
        logger.warning(f"文件上传失败: brand_id={brand_id_for_logging}, error={e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(code=4001, message=e.detail)
        )
    except Exception as e:
        logger.error(f"上传品牌Logo异常: brand_id={brand_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ==================== Brand_Topics API端点 (3个) ====================

@router.post("/admin/brands/{brand_id}/topics")
async def bind_brand_topics(
    brand_id: UUID = Path(..., description="品牌ID"),
    topic_data: BrandTopicBindIn = Body(..., description="专题ID列表"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """批量关联专题到品牌（Admin）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.batch_add_brand_topics(
            db, brand_id, topic_data.topic_ids, current_user_id, role
        )
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"批量关联专题异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.delete("/admin/brands/{brand_id}/topics/{topic_id}")
async def unbind_brand_topic(
    brand_id: UUID = Path(..., description="品牌ID"),
    topic_id: UUID = Path(..., description="专题ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """解除单个品牌-专题关联（Admin）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.delete_brand_topic(db, brand_id, topic_id, current_user_id, role)
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"关联关系不存在: user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    except Exception as e:
        logger.error(f"解除关联异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/admin/brands/{brand_id}/topics")
async def get_brand_topics(
    brand_id: UUID = Path(..., description="品牌ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """获取品牌关联专题列表（Admin分页）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.get_brand_topics_paginated(
            db, brand_id, page, size, current_user_id, role
        )
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: user_id={user_id_for_logging}, brand_id={str(brand_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except Exception as e:
        logger.error(f"获取品牌专题列表异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/admin/brands/{brand_id}/rooms")
async def get_brand_rooms(
    brand_id: UUID = Path(..., description="品牌ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """获取品牌关联直播间列表（Admin分页）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.get_brand_rooms_paginated(
            db, brand_id, page, size, current_user_id, role
        )
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: user_id={user_id_for_logging}, brand_id={str(brand_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except Exception as e:
        logger.error(f"获取品牌直播间列表异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ==================== Brand_Rooms API端点 (3个) ====================

@router.post("/admin/rooms/{room_id}/brands")
async def bind_room_brands(
    room_id: UUID = Path(..., description="直播间ID"),
    brand_data: BrandRoomBindIn = Body(..., description="品牌ID列表"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """绑定直播间品牌（Admin 或房间 owner；可绑任意启用品牌）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.bind_room_brands(
            db, room_id, brand_data.brand_ids, current_user_id, role
        )
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"绑定直播间品牌异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/admin/rooms/{room_id}/brands")
async def get_room_brands_admin(
    room_id: UUID = Path(..., description="直播间ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """获取直播间绑定的品牌（Admin）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.get_room_brands_admin(db, room_id, current_user_id, role)
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"直播间不存在: user_id={user_id_for_logging}, room_id={str(room_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="直播间不存在")
        )
    except Exception as e:
        logger.error(f"获取直播间品牌异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@router.get("/rooms/{room_id}/brands")
async def get_room_brands_public(
    room_id: UUID = Path(..., description="直播间ID"),
    include_topic_brands: Optional[bool] = Query(False, description="是否包含专题品牌"),
    topic_id: Optional[UUID] = Query(None, description="专题ID（当include_topic_brands=True时必填）"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> Any:
    """获取直播间品牌Tab内容（Public + Optional Auth）"""
    # 提取用户信息（可能为None）
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"
    
    try:
        result = await brand_service.get_room_brands_for_tab(
            db, room_id, include_topic_brands, topic_id, current_user_id, role
        )
        return result
        
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"获取直播间品牌Tab异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
