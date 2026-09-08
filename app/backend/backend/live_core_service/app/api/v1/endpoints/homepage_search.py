"""
首页与搜索模块的API端点

本模块包含：
- Phase1: 焦点图CRUD（管理员功能）
- Phase2: 首页API（公开接口）
- Phase3: 搜索API（公开接口）
"""
from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.services.homepage_search_service import HomepageSearchService
from app.schemas.homepage_search import (
    FeaturedContentCreate,
    FeaturedContentUpdate
)
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException
)
from app.core.response import error_response
from app.crud.search import record_search
import logging

logger = logging.getLogger(__name__)

featured_content_public_router = APIRouter()

# 管理员焦点图路由（GET /api/v1/admin/featured-content 分页列表）
featured_content_admin_router = APIRouter()


@featured_content_admin_router.get("/featured-content", response_model=None, tags=["Featured Content Admin"])
async def get_featured_content_list_admin_paginated_endpoint(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    q: Optional[str] = Query(None, description="搜索关键词（ID 或 标题/副标题）"),
    search_type: Optional[str] = Query(None, description="搜索类型：id=按ID精确，不传或非id=按标题/副标题模糊"),
    is_active: Optional[bool] = Query(None, description="启用状态筛选：不传=全部，true=已上线，false=已下线"),
    status: Optional[str] = Query(None, description="时间状态筛选：active=正在展示，upcoming=待上线，expired=已过期，inactive=已下线（含到期自动下线）"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取焦点图列表（管理员，分页）。
    返回全部焦点图（含已禁用、未上线、已过期），需 ADMIN 或 SUPERADMIN 权限。
    支持 q、search_type 列表搜索、is_active 启用状态筛选、status 时间状态筛选（active/upcoming/expired/inactive）。
    查询时会对已过下线时间的焦点图执行惰性下线（is_active 翻转为 false），实现到期自动下线。
    路径：GET /api/v1/admin/featured-content
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()

    if q is not None and (q := q.strip()) == "":
        q = None
    if search_type == "id" and q is not None:
        try:
            UUID(q)
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="search_type 为 id 时，q 必须为有效 UUID")
            )

    try:
        service = HomepageSearchService()
        result = await service.get_featured_content_list_admin_paginated(
            db, page, size, user_id, role, q=q, search_type=search_type, is_active=is_active, status=status
        )
        return JSONResponse(status_code=200, content=result)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    except Exception as e:
        logger.error(f"获取焦点图列表（分页）失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@featured_content_admin_router.post("/featured-content/{content_id}/image", response_model=None, tags=["Featured Content Admin"])
async def upload_featured_content_image_endpoint(
    content_id: UUID,
    image: UploadFile = File(..., description="焦点图图片文件"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传焦点图图片（管理员）。覆盖该焦点图本地图片并更新 image_url。
    路径：POST /api/v1/admin/featured-content/{content_id}/image
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()

    try:
        service = HomepageSearchService()
        result = await service.upload_featured_content_image(db, content_id, image, user_id, role)
        return JSONResponse(status_code=200, content=result)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(status_code=403, content=error_response(code=3002, message=str(e)))
    except NotFoundException as e:
        logger.warning(f"资源不存在: {str(e)}")
        return JSONResponse(status_code=404, content=error_response(code=2001, message=str(e)))
    except HTTPException as e:
        if e.status_code == 400:
            msg = e.detail if isinstance(e.detail, str) else (e.detail.get("detail", "参数错误") if isinstance(e.detail, dict) else "参数错误")
            return JSONResponse(status_code=400, content=error_response(code=4001, message=msg))
        raise
    except Exception as e:
        logger.error(f"上传焦点图图片失败: {str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=5001, message="服务器内部错误"))


@featured_content_admin_router.post("/featured-content", response_model=None, tags=["Featured Content Admin"])
async def create_featured_content_endpoint(
    content_data: FeaturedContentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建焦点图（管理员功能）

    - 需要ADMIN或SUPERADMIN权限
    - 自动生成UUID
    - 支持定时上下线
    - 路径：POST /api/v1/admin/featured-content
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()

    try:
        service = HomepageSearchService()
        result = await service.create_featured_content(db, content_data, user_id, role)

        return JSONResponse(
            status_code=200,
            content=result
        )

    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )

    except InvalidParameterException as e:
        logger.warning(f"参数错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )

    except Exception as e:
        logger.error(f"创建焦点图失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@featured_content_admin_router.get("/featured-content/{content_id}", response_model=None, tags=["Featured Content Admin"])
async def get_featured_content_detail_admin_endpoint(
    content_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取焦点图详情（管理员功能）

    - 需要ADMIN或SUPERADMIN权限
    - 根据 content_id 返回单条焦点图完整信息，用于详情页
    - 路径：GET /api/v1/admin/featured-content/{content_id}
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()

    try:
        service = HomepageSearchService()
        result = await service.get_featured_content_detail_admin(db, content_id, user_id, role)
        return JSONResponse(status_code=200, content=result)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: {str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    except Exception as e:
        logger.error(f"获取焦点图详情失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@featured_content_admin_router.patch("/featured-content/{content_id}", response_model=None, tags=["Featured Content Admin"])
async def update_featured_content_endpoint(
    content_id: UUID,
    content_data: FeaturedContentUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新焦点图（管理员功能）

    - 需要ADMIN或SUPERADMIN权限
    - 支持部分更新
    - 自动更新updated_at字段
    - 路径：PATCH /api/v1/admin/featured-content/{content_id}
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()

    try:
        service = HomepageSearchService()
        result = await service.update_featured_content(db, content_id, content_data, user_id, role)

        return JSONResponse(
            status_code=200,
            content=result
        )

    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )

    except NotFoundException as e:
        logger.warning(f"资源不存在: {str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )

    except InvalidParameterException as e:
        logger.warning(f"参数错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )

    except Exception as e:
        logger.error(f"更新焦点图失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


@featured_content_admin_router.delete("/featured-content/{content_id}", response_model=None, tags=["Featured Content Admin"])
async def delete_featured_content_endpoint(
    content_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除焦点图（管理员功能）

    - 需要ADMIN或SUPERADMIN权限
    - 物理删除（记录与本地媒体目录一并清理，不可恢复）
    - 路径：DELETE /api/v1/admin/featured-content/{content_id}
    """
    user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
    role = (current_user.get("role") or "REGULAR").upper()

    try:
        service = HomepageSearchService()
        result = await service.delete_featured_content(db, content_id, user_id, role)

        return JSONResponse(
            status_code=200,
            content=result
        )

    except PermissionDeniedException as e:
        logger.warning(f"权限不足: {str(e)}, 用户={str(user_id)[:8]}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )

    except NotFoundException as e:
        logger.warning(f"资源不存在: {str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )

    except Exception as e:
        logger.error(f"删除焦点图失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


# 首页API路由（Phase2）
homepage_router = APIRouter()

# 搜索API路由（Phase3）
search_router = APIRouter()
# ==================== 公开端点 ====================

@featured_content_public_router.get("", response_model=None, tags=["Featured Content"])
async def get_featured_content_list_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页焦点图列表（公开接口）

    - 仅返回已启用且在有效期内的焦点图
    - 按排序权重升序排列
    - 最多返回10条
    """
    try:
        service = HomepageSearchService()
        result = await service.get_featured_content_list(db)

        return JSONResponse(
            status_code=200,
            content=result
        )

    except Exception as e:
        logger.error(f"获取焦点图列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


# ==================== Homepage API端点 (Phase2) ====================

@homepage_router.get("/rooms", response_model=None, tags=["Homepage API"])
async def get_homepage_rooms_endpoint(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: str = Query("heat:desc", pattern="^(heat:desc|start_time:asc|created_at:desc)$", description="排序规则"),
    category_id: Optional[UUID] = Query(None, description="全局医学分类ID筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页直播间列表（公开接口）

    - 无需认证
    - 支持分页
    - 支持排序（热度、开始时间、创建时间）
    - 支持分类筛选
    - 包含实时状态、主讲专家、热度等信息
    """
    try:
        service = HomepageSearchService()
        result = await service.get_homepage_rooms(
            db, page, size, sort, category_id
        )

        return JSONResponse(
            status_code=200,
            content=result
        )

    except InvalidParameterException as e:
        logger.warning(f"首页直播间参数错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )

    except Exception as e:
        logger.error(f"获取首页直播间列表失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )


# ==================== Search API端点 (Phase3) ====================

@search_router.get("", response_model=None, tags=["Search API"])
async def search_resources_endpoint(
    q: str = Query(..., min_length=2, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    type: Optional[str] = Query(None, description="资源类型筛选（逗号分隔）"),
    category_id: Optional[UUID] = Query(None, description="全局医学分类ID筛选（room 走 live_room_categories，expert 走 experts.category_id）"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    全局搜索接口

    - 可选认证（登录用户自动记录搜索历史）
    - 支持跨直播间、专家、专题、品牌的模糊搜索
    - 支持分页
    - 支持资源类型筛选
    - 返回匹配分数和高亮文本
    """
    try:
        # 解析type参数（逗号分隔）
        resource_types = None
        if type:
            resource_types = [t.strip() for t in type.split(',')]

        service = HomepageSearchService()
        result = await service.search_resources(
            db, q, page, size, resource_types, category_id
        )

        # 搜索成功后记录搜索行为（不影响搜索结果返回）
        try:
            user_id = None
            if current_user:
                user_id = UUID(current_user.get("user_id") or current_user.get("sub"))
            await record_search(db, user_id, q)
        except Exception as e:
            logger.warning(f"记录搜索行为失败（不影响搜索结果）: {e}")

        return JSONResponse(
            status_code=200,
            content=result
        )

    except InvalidParameterException as e:
        logger.warning(f"搜索参数错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )

    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=5001, message="服务器内部错误")
        )
