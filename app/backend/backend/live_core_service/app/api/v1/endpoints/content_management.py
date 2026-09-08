"""
内容管理模块的API端点
负责HTTP请求解析、依赖注入、调用Service层
"""
from typing import List, Optional
from uuid import UUID
import uuid as uuid_module
import logging

from fastapi import APIRouter, Depends, Query, Path, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import success_response, error_response
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.content_safety.exceptions import ContentSafetyBlockedException, ContentSafetyServiceException
from app.crud.content_management import get_categories_stats

logger = logging.getLogger(__name__)
from app.schemas.content_management import (
    TagCreate, TagUpdate, TagItem, TagListResponse, TagAdminListResponse,
    TagResolveRequest, TagResolveResponse,
    CategoryCreate, CategoryUpdate, CategoryItem, CategoryListResponse, CategoryAdminListResponse,
    SessionTagsSetRequest, SessionTagsSetResponse, SessionTagsListResponse,
    LiveRoomCategoriesSetRequest, LiveRoomCategoriesSetResponse, LiveRoomCategoriesListResponse,
    CategoryMigrateRequest, CategoryMergeRequest,
)
from app.services.content_management_service import ContentManagementService

# 🚨 重要：APIRouter定义严禁指定prefix，prefix必须在顶层api/v1/api.py中统一指定
content_public_router = APIRouter(tags=["Content Management - 公开"])  # ✅ 正确：不指定prefix
content_admin_router = APIRouter(tags=["Content Management - 管理"])
service = ContentManagementService()

# 直播间-分类：公开列表（挂载 prefix=/rooms -> GET /api/v1/rooms/{room_id}/categories）
live_room_categories_router = APIRouter(tags=["Content Management - 直播间分类"])
# 直播间-分类：管理端（挂载 prefix=/admin/rooms -> POST/DELETE /api/v1/admin/rooms/{room_id}/categories）
live_room_categories_admin_router = APIRouter(tags=["Content Management - 直播间分类-管理"])


# ============================================================================
# Tags端点
# ============================================================================

@content_public_router.get(
    "/tags",
    response_model=TagListResponse,
    summary="获取标签列表",
    description="获取所有标签列表，管理员可查询所有标签，普通用户只能查询启用的标签；支持 q、search_type（id/keyword）、include_inactive（需管理员）"
)
async def get_tags(
    q: Optional[str] = Query(None, description="关键词或主键ID"),
    search_type: Optional[str] = Query(None, description="id=按ID精确查询，keyword或未传=按字符串模糊查询"),
    include_inactive: Optional[bool] = Query(False, description="是否包含禁用标签（需管理员权限）"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> TagListResponse:
    """获取标签列表（Public + Optional Auth）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"

    if search_type == "id" and q and str(q).strip():
        try:
            uuid_module.UUID(str(q).strip())
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="无效的ID格式")
            )
    try:
        return await service.get_tags_list(
            db, current_user_id, role, q=q, search_type=search_type, include_inactive=include_inactive or False
        )
    except PermissionDeniedException:
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取标签列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_public_router.post(
    "/tags/resolve",
    response_model=TagResolveResponse,
    summary="解析或创建标签",
    description="按名称确保标签存在：命中返回已有；未命中则创建（source=user）。需登录。",
)
async def resolve_tag(
    request_data: TagResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TagResolveResponse:
    """解析或创建标签（Strict Auth；REGULAR/Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.resolve_tag(db, request_data, current_user_id, role)
    except PermissionDeniedException:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足"),
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e)),
        )
    except ContentSafetyBlockedException as e:
        # 内容安全拦截：显式 catch 返回 422/2005（与 live_features 留言端点风格一致，避免被兜底吞成 500）
        logger.warning(f"内容安全拦截: user_id={user_id_for_logging}, error={e.message}")
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message),
        )
    except ContentSafetyServiceException as e:
        logger.error(f"内容安全服务异常: user_id={user_id_for_logging}, error={e.message}")
        return JSONResponse(
            status_code=422,
            content=error_response(code=e.code, message=e.message),
        )
    except Exception as e:
        logger.error(f"resolve 标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )


@content_admin_router.get(
    "/tags",
    response_model=TagAdminListResponse,
    summary="获取标签列表（管理员接口）",
    description="获取标签列表，支持分页、按is_active过滤及 q/search_type 搜索，需要管理员权限"
)
async def get_tags_admin(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否启用（true/false/null）"),
    q: Optional[str] = Query(None, description="关键词或主键ID"),
    search_type: Optional[str] = Query(None, description="id=按ID精确查询，keyword或未传=按字符串模糊查询"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TagAdminListResponse:
    """获取标签列表（Admin接口，分页）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    if search_type == "id" and q and str(q).strip():
        try:
            uuid_module.UUID(str(q).strip())
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="无效的ID格式")
            )
    try:
        return await service.get_tags_paginated(db, page, size, is_active, current_user_id, role, q=q, search_type=search_type)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取标签列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.post(
    "/tags",
    response_model=TagItem,
    status_code=201,
    summary="创建标签",
    description="创建新标签，需要管理员权限"
)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TagItem:
    """创建标签（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.create_tag(db, tag_data, current_user_id, role)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.put(
    "/tags/{tag_id}",
    response_model=TagItem,
    summary="更新标签",
    description="更新标签信息，需要管理员权限"
)
async def update_tag(
    tag_id: UUID = Path(..., description="标签ID"),
    tag_data: TagUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TagItem:
    """更新标签（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.update_tag(db, tag_id, tag_data, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# PATCH 路由：兼容 App 端与小程序的 request.patch 调用（两端均已上线依赖 PATCH）
# 与 PUT 完全同构（同一 service.update_tag + 同一套异常捕获），仅 HTTP 方法不同
@content_admin_router.patch(
    "/tags/{tag_id}",
    response_model=TagItem,
    summary="更新标签（PATCH 别名）",
    description="更新标签信息（部分更新），需要管理员权限；与 PUT 等价，兼容前端 PATCH 调用"
)
async def update_tag_patch(
    tag_id: UUID = Path(..., description="标签ID"),
    tag_data: TagUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TagItem:
    """更新标签（PATCH 别名，Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.update_tag(db, tag_id, tag_data, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.delete(
    "/tags/{tag_id}",
    summary="删除标签",
    description="删除标签（软删除），需要管理员权限"
)
async def delete_tag(
    tag_id: UUID = Path(..., description="标签ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """删除标签（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.delete_tag(db, tag_id, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"删除标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ============================================================================
# Categories端点
# ============================================================================

@content_public_router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="获取分类列表（公开接口）",
    description="获取所有启用的分类列表，按sort_order排序"
)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> CategoryListResponse:
    """获取分类列表（Public + Optional Auth）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"

    try:
        return await service.get_categories_list(db, current_user_id, role)
    except Exception as e:
        logger.error(f"获取分类列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.get(
    "/categories",
    response_model=CategoryAdminListResponse,
    summary="获取分类列表（管理员接口）",
    description="获取分类列表，支持分页、按is_active过滤及 q/search_type 搜索，需要管理员权限"
)
async def get_categories_admin(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否启用（true/false/null）"),
    q: Optional[str] = Query(None, description="关键词或主键ID"),
    search_type: Optional[str] = Query(None, description="id=按ID精确查询，keyword或未传=按字符串模糊查询"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CategoryAdminListResponse:
    """获取分类列表（Admin接口，分页）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    if search_type == "id" and q and str(q).strip():
        try:
            uuid_module.UUID(str(q).strip())
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="无效的ID格式")
            )
    try:
        return await service.get_categories_paginated(db, page, size, is_active, current_user_id, role, q=q, search_type=search_type, include_counts=True)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取分类列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.post(
    "/categories",
    response_model=CategoryItem,
    status_code=201,
    summary="创建分类",
    description="创建新分类，需要管理员权限"
)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CategoryItem:
    """创建分类（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.create_category(db, category_data, current_user_id, role)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建分类异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.put(
    "/categories/{category_id}",
    response_model=CategoryItem,
    summary="更新分类",
    description="更新分类信息，需要管理员权限"
)
async def update_category(
    category_id: UUID = Path(..., description="分类ID"),
    category_data: CategoryUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CategoryItem:
    """更新分类（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.update_category(db, category_id, category_data, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新分类异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.delete(
    "/categories/{category_id}",
    summary="删除分类",
    description="删除分类（软删除），需要管理员权限。force=true 时引用安顿（专家/科室迁移到 target_category_id 或'其他'、房间关联迁移/解除）并级联停用子树"
)
async def delete_category(
    category_id: UUID = Path(..., description="分类ID"),
    force: bool = Query(False, description="确认级联：安顿引用并级联停用子树（不再跳过检查）"),
    target_category_id: Optional[UUID] = Query(None, description="引用迁移目标分类ID（缺省用'其他'兜底分类）"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """删除分类（Strict Auth + Admin）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        result = await service.delete_category(
            db, category_id, current_user_id, role,
            force=force, target_category_id=target_category_id,
        )
        # force=False 且有引用时返回 blocked 状态，用 409 Conflict 告知调用方
        if isinstance(result, dict) and result.get("blocked"):
            return JSONResponse(
                status_code=409,
                content=error_response(code=4001, message=result["message"], data=result)
            )
        return result
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数校验失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    except Exception as e:
        logger.error(f"删除分类异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.post(
    "/categories/{category_id}/migrate",
    summary="迁移分类引用",
    description="将分类的专家/科室/房间关联迁移到目标分类（治理工具，与删除闭环共用迁移函数）。需要管理员权限"
)
async def migrate_category(
    category_id: UUID = Path(..., description="源分类ID"),
    body: CategoryMigrateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """迁移分类引用（Strict Auth + Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        result = await service.migrate_category(
            db, category_id, body.target_category_id, scope=body.scope,
            current_user_id=current_user_id, role=role,
        )
        return success_response(
            message="分类引用迁移成功",
            data={"migrated": result},
        )
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数校验失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    except Exception as e:
        logger.error(f"迁移分类引用异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.post(
    "/categories/merge",
    summary="合并分类",
    description="将源分类的专家/科室/房间关联迁入目标分类并软删源分类（dry_run 预览；子分类可挂载或提升）。需要管理员权限"
)
async def merge_categories(
    body: CategoryMergeRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """合并分类（Strict Auth + Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        result = await service.merge_categories(
            db, body.source_id, body.target_id,
            attach_children=body.attach_children, dry_run=body.dry_run,
            current_user_id=current_user_id, role=role,
        )
        return success_response(message=result["message"], data=result)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数校验失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    except Exception as e:
        logger.error(f"合并分类异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.post(
    "/categories/{category_id}/icon",
    response_model=CategoryItem,
    summary="上传/更新科室图片",
    description="上传科室（分类）图标，覆盖旧图；需要管理员权限"
)
async def upload_category_icon(
    category_id: UUID = Path(..., description="分类ID"),
    file: UploadFile = File(..., description="科室图标图片文件"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CategoryItem:
    """上传/覆盖科室图标（Strict Auth + Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    try:
        return await service.upload_category_icon(db, category_id, file, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content=error_response(code=4001, message=str(e.detail)))
    except Exception as e:
        logger.error(f"上传科室图标异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.delete(
    "/categories/{category_id}/icon",
    summary="删除科室图片",
    description="删除科室（分类）图标；需要管理员权限；无图片时也返回成功"
)
async def delete_category_icon(
    category_id: UUID = Path(..., description="分类ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """删除科室图标（Strict Auth + Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    try:
        return await service.delete_category_icon(db, category_id, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"删除科室图标异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_admin_router.get(
    "/categories/stats",
    summary="获取分类系统统计数据",
    description="获取分类系统的聚合统计数据（分类数、科室数、审核状态等）；需要管理员权限"
)
async def categories_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取分类系统统计数据（Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        service._check_admin_permission(role)
        stats = await get_categories_stats(db)
        logger.info(f"查询分类统计数据成功: user_id={user_id_for_logging}")
        return success_response(data=stats)
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message=str(e))
        )
    except Exception as e:
        logger.error(f"查询分类统计数据异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_public_router.get(
    "/categories/{category_id}",
    response_model=CategoryItem,
    summary="获取分类详情",
    description="根据ID获取分类详情"
)
async def get_category_by_id(
    category_id: UUID = Path(..., description="分类ID"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> CategoryItem:
    """获取分类详情（Public + Optional Auth）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"

    try:
        return await service.get_category_by_id(db, category_id, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"获取分类详情异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ============================================================================
# Session_Tags端点
# ============================================================================

@content_public_router.post(
    "/sessions/{session_id}/tags",
    response_model=SessionTagsSetResponse,
    summary="为场次设置标签",
    description="为指定场次设置标签，支持替换或追加模式，需要写权限"
)
async def set_session_tags(
    session_id: UUID = Path(..., description="场次ID"),
    request_data: SessionTagsSetRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SessionTagsSetResponse:
    """为场次设置标签（Strict Auth + Write）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.set_session_tags(db, session_id, request_data, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"为场次设置标签异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_public_router.get(
    "/sessions/{session_id}/tags",
    response_model=SessionTagsListResponse,
    summary="获取场次标签列表",
    description="获取指定场次的所有启用标签"
)
async def get_session_tags(
    session_id: UUID = Path(..., description="场次ID"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> SessionTagsListResponse:
    """获取场次标签列表（Public + Optional Auth）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"

    try:
        return await service.get_session_tags(db, session_id, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"获取场次标签列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_public_router.get(
    "/tags/search/sessions",
    summary="根据标签查询场次",
    description="根据标签ID列表查询场次ID列表，支持AND/OR匹配模式"
)
async def get_sessions_by_tags(
    tag_ids: List[UUID] = Query(..., description="标签ID列表"),
    match_all: bool = Query(False, description="匹配模式：true=AND逻辑，false=OR逻辑"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> dict:
    """根据标签查询场次（Public + Optional Auth）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"

    try:
        session_ids = await service.get_sessions_by_tags(db, tag_ids, match_all, current_user_id, role)

        return success_response(data={
            "tag_ids": [str(tag_id) for tag_id in tag_ids],
            "match_all": match_all,
            "session_ids": [str(session_id) for session_id in session_ids]
        })
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except Exception as e:
        logger.error(f"根据标签查询场次异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


@content_public_router.delete(
    "/sessions/{session_id}/tags/{tag_id}",
    summary="删除场次标签关联",
    description="删除场次与标签的关联，需要写权限"
)
async def remove_session_tag(
    session_id: UUID = Path(..., description="场次ID"),
    tag_id: UUID = Path(..., description="标签ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """删除场次标签关联（Strict Auth + Write）"""
    # 🚨 必须：在try块之前提取并转换role
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()  # ✅ 必须调用.upper()
    user_id_for_logging = str(current_user_id)[:8]

    try:
        return await service.remove_session_tag(db, session_id, tag_id, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在")
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"删除场次标签关联异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ============================================================================
# Live_Room_Categories 端点（公开 GET 挂载于 /rooms，管理 POST/DELETE 挂载于 /admin/rooms）
# ============================================================================

@live_room_categories_router.get(
    "/{room_id}/categories",
    response_model=LiveRoomCategoriesListResponse,
    summary="获取直播间分类列表",
    description="获取指定直播间通过 live_room_categories 关联的已启用全局医学分类列表（公开）",
)
async def get_live_room_categories(
    room_id: UUID = Path(..., description="直播间ID"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
) -> LiveRoomCategoriesListResponse:
    """获取直播间分类列表（Optional Auth）"""
    current_user_id = UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role", "REGULAR").upper() if current_user else None
    user_id_for_logging = str(current_user_id)[:8] if current_user_id else "anonymous"
    try:
        return await service.get_live_room_categories_list(db, room_id, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except Exception as e:
        logger.error(f"获取直播间分类列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )


@live_room_categories_admin_router.post(
    "/{room_id}/categories",
    response_model=LiveRoomCategoriesSetResponse,
    status_code=200,
    summary="设置直播间分类",
    description="为指定直播间批量设置全局医学分类（replace/append），写入 live_room_categories，需要管理员权限",
)
async def set_live_room_categories(
    room_id: UUID = Path(..., description="直播间ID"),
    body: LiveRoomCategoriesSetRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> LiveRoomCategoriesSetResponse:
    """设置直播间分类（Strict Auth + Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]

    # ← 新增：Admin 专用端点，仅 ADMIN/SUPERADMIN 可调用
    if role not in ('ADMIN', 'SUPERADMIN'):
        logger.warning(f"非管理员尝试设置直播间分类: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="需要管理员权限"),
        )

    try:
        return await service.set_live_room_categories(db, room_id, body, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足"),
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message=str(e)),
        )
    except Exception as e:
        logger.error(f"设置直播间分类异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )


@live_room_categories_admin_router.delete(
    "/{room_id}/categories/{category_id}",
    summary="删除直播间分类关联",
    description="删除直播间与指定全局医学分类的关联，需要管理员权限",
)
async def delete_live_room_category(
    room_id: UUID = Path(..., description="直播间ID"),
    category_id: UUID = Path(..., description="分类ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """删除直播间分类关联（Strict Auth + Admin）"""
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]

    # ← 新增：Admin 专用端点，仅 ADMIN/SUPERADMIN 可调用
    if role not in ('ADMIN', 'SUPERADMIN'):
        logger.warning(f"非管理员尝试删除直播间分类: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="需要管理员权限"),
        )

    try:
        return await service.delete_live_room_category(db, room_id, category_id, current_user_id, role)
    except NotFoundException as e:
        logger.warning(f"资源不存在: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在"),
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足"),
        )
    except Exception as e:
        logger.error(f"删除直播间分类关联异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误"),
        )
