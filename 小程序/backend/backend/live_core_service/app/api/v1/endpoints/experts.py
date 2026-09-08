"""
专家模块 API Endpoint 层

本模块实现所有专家相关的 RESTful API 接口。

职责：
- HTTP请求/响应处理
- 调用Service层
- 异常转换为HTTP响应

所有端点遵循安全异步异常处理原则。
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Dict, Any

# 第三方库导入
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Body, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# 项目内导入
from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import success_response, error_response
from app.services.expert_service import ExpertService
from app.schemas.experts import (
    ExpertCreate, ExpertUpdate, ExpertItem, FeaturedExpertItem,
    ExpertFollowRequest, ExpertFollowResponse, FollowedExpertItem,
    FollowedExpertsResponse, SessionExpertItem
)
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException
)

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 主路由器：专家管理 ====================
# 拆分为4个router以符合设计文档的URL规范：
# 1. experts_featured_router: /featured-experts（注册到空前缀）
# 2. experts_public_router: 公开接口 /experts/*（注册到 /experts prefix）
# 3. experts_user_router: 用户接口 /users/me/followed-experts（注册到空前缀）
# 4. experts_admin_router: 管理员接口 /admin/experts（注册到 /admin prefix）

# 推荐专家router（注册到空前缀，路径为 /featured-experts）
experts_featured_router = APIRouter(tags=["专家管理-公开"])

# 公开接口router（注册到 /experts prefix）
experts_public_router = APIRouter(tags=["专家管理-公开"])

# 用户接口router（注册到空前缀，路径已包含 /users/me）
experts_user_router = APIRouter(tags=["专家管理-用户"])

# 管理员接口router（注册到 /admin prefix）
experts_admin_router = APIRouter(tags=["专家管理-管理员"])

# 保持向后兼容（用于未拆分的路由）
router = experts_public_router


# ==================== 响应格式化函数 ====================

def format_expert_response(expert, request: Request = None) -> dict:
    """格式化专家响应数据"""
    data = {
        "id": str(expert.id),
        "user_id": str(expert.user_id) if expert.user_id else None,
        "name": expert.name,
        "title": expert.title,
        "hospital": expert.hospital,
        "department": expert.department,
        "department_id": str(expert.department_id) if getattr(expert, "department_id", None) else None,
        "department_name": getattr(expert, "department_name", None) or expert.department,
        "category_id": str(expert.category_id) if getattr(expert, "category_id", None) else None,
        "category_name": getattr(expert, "category_name", None),
        "expertise_areas": expert.expertise_areas,
        "bio": expert.bio,
        "avatar_url": expert.avatar_url,
        "is_featured": expert.is_featured,
        "is_active": expert.is_active,
        "sort_order": expert.sort_order,
        "created_at": expert.created_at.isoformat() + "Z",
        "updated_at": expert.updated_at.isoformat() + "Z"
    }
    
    # URL拼接（如果需要）
    if request and data["avatar_url"]:
        base_url = str(request.base_url).rstrip('/')
        if not data["avatar_url"].startswith('http'):
            data["avatar_url"] = f"{base_url}{data['avatar_url']}"
    
    return data


def format_avatar_url(avatar_url: Optional[str], request: Request = None) -> Optional[str]:
    """格式化头像URL"""
    if not avatar_url:
        return None
    
    if request and not avatar_url.startswith('http'):
        base_url = str(request.base_url).rstrip('/')
        return f"{base_url}{avatar_url}"
    
    return avatar_url


# ==================== 专家信息管理API端点 ====================

@experts_featured_router.get("/featured-experts")
async def get_featured_experts(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页推荐专家列表（公开）
    """
    try:
        service = ExpertService(db)
        experts = await service.get_featured_experts(limit=limit)
        
        # 格式化响应（URL拼接，含 is_active）
        experts_data = [
            {
                "id": str(expert.id),
                "name": expert.name,
                "title": expert.title,
                "hospital": expert.hospital,
                "avatar_url": format_avatar_url(expert.avatar_url, request) if expert.avatar_url else None,
                "is_active": expert.is_active
            }
            for expert in experts
        ]
        
        return success_response(data=experts_data)
        
    except Exception as e:
        logger.error(f"获取推荐专家列表异常: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_public_router.get("")
async def get_public_experts_list(
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=50, description="每页数量，最大100"),
    keyword: Optional[str] = Query(default=None, description="关键词（姓名/医院/科室/简介）"),
    department: Optional[str] = Query(default=None, description="按科室筛选"),
    hospital: Optional[str] = Query(default=None, description="按医院筛选"),
    is_active: Optional[bool] = Query(default=True, description="按启用状态筛选，默认仅启用专家"),
    sort: Optional[str] = Query(default=None, description="排序规则，默认 sort_order:asc,created_at:desc,id:asc"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公共专家列表（分页，专家页全量接口）
    """
    try:
        service = ExpertService(db)
        result = await service.get_public_experts_list(
            page=page,
            size=size,
            keyword=keyword,
            department=department,
            hospital=hospital,
            is_active=is_active,
            sort=sort,
        )

        result["items"] = [format_expert_response(expert, request) for expert in result["items"]]
        return success_response(data=result)

    except InvalidParameterException as e:
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code if hasattr(e, "code") else 4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"获取公共专家列表异常: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_public_router.get("/{expert_id}")
async def get_expert_detail(
    expert_id: str,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取专家详情（公开）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    user_id_for_logging = str(user_id)[:8] if user_id else "anonymous"
    
    try:
        service = ExpertService(db)
        expert = await service.get_expert_detail(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(data=format_expert_response(expert, request))
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
        )
    except Exception as e:
        logger.error(f"获取专家详情异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_public_router.get("/{expert_id}/sessions")
async def get_expert_sessions(
    expert_id: str,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(default=None, description="专家角色筛选"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取专家详情及其参与的所有直播场次（分页，公开）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role_user = current_user.get("role") if current_user else None
    
    user_id_for_logging = str(user_id)[:8] if user_id else "anonymous"
    
    try:
        service = ExpertService(db)
        result = await service.get_expert_sessions(
            expert_id=expert_uuid,
            page=page,
            size=size,
            role=role,
            current_user_id=user_id,
            role_user=role_user
        )
        
        return success_response(data=result)
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
        )
    except Exception as e:
        logger.error(f"获取专家场次列表异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_admin_router.post("/experts/batch-import")
async def batch_import_experts(
    file: UploadFile = File(..., description="CSV 文件"),
    skip_duplicates: bool = Form(default=False, description="是否跳过已存在记录"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量导入专家（需要管理员权限）
    
    - 文件校验：.csv、最大 10MB、最大 1000 行、UTF-8 编码
    - 201 全成功；207 部分成功；400 格式错误；413 文件过大；403 非 Admin
    """
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(user_id)[:8]
    file_name_for_logging = file.filename or "unknown"
    
    MAX_FILE_SIZE = 10 * 1024 * 1024
    MAX_ROWS = 1000
    
    try:
        if not file.filename or not file.filename.lower().endswith(".csv"):
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="文件格式错误，仅支持 .csv 格式", data={"expected": "csv"})
            )
        
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content=error_response(code=4001, message="文件过大", data={"max_size": MAX_FILE_SIZE, "file_size": len(content)})
            )
        if len(content) == 0:
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="文件为空")
            )
        
        row_count = content.decode("utf-8", errors="replace").count("\n") + 1
        if row_count > MAX_ROWS + 1:
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="行数超过限制", data={"max_rows": MAX_ROWS, "rows": row_count})
            )
        
        service = ExpertService(db)
        result = await service.batch_import_experts_from_csv_optimized(
            file_content=content,
            skip_duplicates=skip_duplicates,
            role=role
        )
        
        total, success, failed = result["total"], result["success"], result["failed"]
        if failed == total:
            return JSONResponse(
                status_code=400,
                content=error_response(code=4001, message="全部导入失败", data=result)
            )
        if failed > 0:
            return JSONResponse(status_code=207, content=success_response(data=result, message="部分导入成功"))
        return JSONResponse(status_code=201, content=success_response(data=result, message="导入成功"))
        
    except PermissionDeniedException:
        logger.warning(f"批量导入权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(status_code=403, content=error_response(code=3003, message="权限不足"))
    except InvalidParameterException as e:
        logger.warning(f"批量导入参数错误: user_id={user_id_for_logging}, file={file_name_for_logging}, error={str(e)}")
        return JSONResponse(status_code=400, content=error_response(code=e.code if hasattr(e, "code") else 4001, message=str(e)))
    except Exception as e:
        logger.error(f"批量导入异常: user_id={user_id_for_logging}, file={file_name_for_logging}, error={type(e).__name__}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@experts_admin_router.post("/experts")
async def create_expert(
    expert_create: ExpertCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建专家（需要管理员权限）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        expert = await service.create_expert(
            expert_data=expert_create,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"专家创建成功: expert_id={expert.id}, user_id={user_id_for_logging}")
        
        return success_response(data=format_expert_response(expert))
        
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
            content=error_response(code=e.code if hasattr(e, 'code') else 4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"创建专家异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_admin_router.get("/experts")
async def get_experts_list(
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(default=None, description="按姓名模糊搜索"),
    is_featured: Optional[bool] = Query(default=None, description="筛选推荐状态"),
    is_active: Optional[bool] = Query(default=None, description="按启用状态筛选"),
    hospital: Optional[str] = Query(default=None, description="按医院筛选"),
    sort: Optional[str] = Query(default=None, description="排序规则"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取专家列表（需要管理员权限，分页）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.get_experts_list(
            page=page,
            size=size,
            name=name,
            is_featured=is_featured,
            is_active=is_active,
            hospital=hospital,
            sort=sort,
            current_user_id=user_id,
            role=role
        )
        
        # 格式化响应（URL拼接，含 is_active）
        result["items"] = [format_expert_response(expert, request) for expert in result["items"]]
        
        return success_response(data=result)
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取专家列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_admin_router.patch("/experts/{expert_id}")
async def update_expert(
    expert_id: str,
    expert_update: ExpertUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新专家信息（需要管理员权限）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        expert = await service.update_expert(
            expert_id=expert_uuid,
            expert_data=expert_update,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"专家更新成功: expert_id={expert_id}, user_id={user_id_for_logging}")
        
        return success_response(data=format_expert_response(expert))
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
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
            content=error_response(code=e.code if hasattr(e, 'code') else 4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"更新专家异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_admin_router.delete("/experts/{expert_id}")
async def delete_expert(
    expert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除专家（需要管理员权限，软删除）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.delete_expert(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        logger.warning(f"专家删除成功（软删除）: expert_id={expert_id}, user_id={user_id_for_logging}")
        
        return success_response(data=result)
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"删除专家异常: expert_id={expert_id}, user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_admin_router.post("/experts/{expert_id}/avatar")
async def upload_expert_avatar(
    expert_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    为指定专家上传头像图片（Admin）
    
    完全复用 FileHandler 的实现逻辑：
    - 文件校验：PNG, JPG, GIF 格式，5MB 以内
    - 权限验证：仅 ADMIN/SUPERADMIN 可上传
    - 存储路径：/media/experts/{expert_id}/avatar_{timestamp}.{ext}
    
    Args:
        expert_id: 专家UUID
        file: 上传的头像文件
        current_user: 当前登录用户信息
        db: 数据库会话
        
    Returns:
        标准成功响应，包含 expert_id 和 avatar_url
        
    Raises:
        404: 专家不存在
        403: 权限不足
        400: 文件格式或大小不符合要求
    """
    # 提取用户信息
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    
    # 提前提取用于日志的变量
    user_id_for_logging = str(user_id)[:8]
    
    try:
        expert_id_uuid = uuid.UUID(expert_id)
        expert_id_for_logging = str(expert_id_uuid)[:8]
    except ValueError:
        logger.warning(f"无效的专家ID格式: expert_id={expert_id}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID格式")
        )
    
    logger.info(f"开始上传专家头像: expert_id={expert_id_for_logging}, user_id={user_id_for_logging}")
    
    try:
        # 实例化Service层
        service = ExpertService(db)
        
        # 调用 Service 层上传头像
        avatar_url = await service.upload_expert_avatar(
            expert_id=expert_id_uuid,
            file=file,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(
            data={
                "expert_id": expert_id,
                "avatar_url": avatar_url
            },
            message="头像上传成功"
        )
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="专家不存在")
        )
    except HTTPException as e:
        logger.warning(f"文件上传失败: expert_id={expert_id_for_logging}, error={e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(code=4001, message=e.detail)
        )
    except Exception as e:
        logger.error(f"上传专家头像异常: expert_id={expert_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )


# ==================== 专家关注API端点 ====================

@experts_user_router.post("/users/me/followed-experts")
async def follow_expert(
    follow_request: ExpertFollowRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    关注专家（需要登录）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.follow_expert(
            expert_id=follow_request.expert_id,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"关注专家成功: user_id={user_id_for_logging}, expert_id={follow_request.expert_id}")
        
        return success_response(data=result, message="关注成功")
        
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={follow_request.expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": str(follow_request.expert_id)})
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
            status_code=409,
            content=error_response(code=e.code if hasattr(e, 'code') else 2002, message=str(e))
        )
    except Exception as e:
        logger.error(f"关注专家异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_user_router.delete("/users/me/followed-experts/{expert_id}")
async def unfollow_expert(
    expert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消关注专家（需要登录）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.unfollow_expert(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"取消关注专家成功: user_id={user_id_for_logging}, expert_id={expert_id}")
        
        return success_response(data=result, message="取消关注成功")
        
    except NotFoundException as e:
        logger.warning(f"未关注该专家: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"reason": "未关注该专家"})
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"取消关注专家异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_user_router.get("/users/me/followed-experts")
async def get_followed_experts(
    request: Request,
    include_live_status: bool = Query(default=True, description="是否包含直播状态"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取关注的专家列表（需要登录）
    """
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        experts = await service.get_followed_experts(
            current_user_id=user_id,
            role=role,
            include_live_status=include_live_status
        )
        
        # 格式化响应（URL拼接）
        experts_data = [
            {
                "expert_id": str(expert.expert_id),
                "name": expert.name,
                "title": expert.title,
                "hospital": expert.hospital,
                "avatar_url": format_avatar_url(expert.avatar_url, request) if expert.avatar_url else None,
                "subscribed_at": expert.subscribed_at.isoformat() + "Z",
                "live_status": expert.live_status
            }
            for expert in experts
        ]
        
        return success_response(data=experts_data)
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"获取关注列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_public_router.get("/{expert_id}/is-followed")
async def check_is_followed(
    expert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查是否已关注专家（需要登录）
    """
    try:
        expert_uuid = uuid.UUID(expert_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.check_is_followed(
            expert_id=expert_uuid,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(data=result)
        
    except NotFoundException as e:
        logger.warning(f"专家不存在或已下架: expert_id={expert_id}, user_id={user_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="资源不存在", data={"resource": "Expert", "id": expert_id})
        )
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except Exception as e:
        logger.error(f"检查关注状态异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


# ==================== 场次专家关联API端点 ====================

@experts_public_router.post("/sessions/{session_id}/experts")
async def set_session_experts(
    session_id: str,
    expert_data_list: List[Dict[str, Any]] = Body(..., description="专家列表"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为场次设置专家列表（Admin 或场次所属房间 owner）
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的场次ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    
    user_id_for_logging = str(user_id)[:8]
    
    try:
        service = ExpertService(db)
        result = await service.set_session_experts(
            session_id=session_uuid,
            expert_data_list=expert_data_list,
            current_user_id=user_id,
            role=role
        )
        
        logger.info(f"设置场次专家列表成功: session_id={session_id}, user_id={user_id_for_logging}")
        
        return success_response(data=result)
        
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
            content=error_response(code=2004, message=str(e))
        )
    except InvalidParameterException as e:
        logger.warning(f"参数验证失败: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code if hasattr(e, 'code') else 4001, message=str(e))
        )
    except Exception as e:
        logger.error(f"设置场次专家列表异常: user_id={user_id_for_logging}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@experts_public_router.get("/sessions/{session_id}/experts")
async def get_session_experts(
    session_id: str,
    request: Request,
    role: Optional[str] = Query(default=None, description="专家角色筛选"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取场次的专家列表（公开）
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的场次ID")
        )
    
    # 提前提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role_user = current_user.get("role") if current_user else None
    
    try:
        service = ExpertService(db)
        experts = await service.get_session_experts(
            session_id=session_uuid,
            role=role,
            current_user_id=user_id,
            role_user=role_user
        )
        
        # 格式化响应（URL拼接，含 is_active）
        experts_data = [
            {
                "id": str(expert.id),
                "name": expert.name,
                "title": expert.title,
                "hospital": expert.hospital,
                "avatar_url": format_avatar_url(expert.avatar_url, request) if expert.avatar_url else None,
                "is_active": getattr(expert, "is_active", True),
                "role": expert.role,
                "sort_order": expert.sort_order,
                "expertise_areas": expert.expertise_areas,
                "bio": expert.bio
            }
            for expert in experts
        ]
        
        return success_response(data=experts_data)
        
    except Exception as e:
        logger.error(f"获取场次专家列表异常: session_id={session_id}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )

