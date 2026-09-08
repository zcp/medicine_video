"""
专题聚合功能的 API Endpoint 层

本模块实现所有专题相关的 RESTful API 接口。

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
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# 项目内导入
from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional  # ← 新增：Optional Auth依赖
from app.core.response import success_response, error_response
from app.services.topic_service import TopicService
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicResponse,
    TopicCategoryCreate, TopicCategoryUpdate, TopicCategoryResponse,
    AddRoomsRequest, UpdateRoomSortRequest, RemoveRoomsRequest,
    BatchStatusRequest
)
from app.models.topic import TopicStatus
from app.exceptions import (
    TopicNotFoundException,
    TopicCategoryNotFoundException,
    RoomAlreadyAssociatedException,
    RoomNotFoundException,
    PermissionDeniedException,  # ← 修改：使用PermissionDeniedException替代TopicPermissionDeniedException
    NotFoundException  # ← 新增：用于404伪装
)

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 主路由器：专题管理 ====================

topic_router = APIRouter(tags=["Topics"])  # prefix 在 api.py 中指定


def format_topic_response(topic) -> dict:
    """格式化专题响应数据"""
    return {
        "id": str(topic.id),
        "user_id": str(topic.user_id),
        "title": topic.title,
        "description": topic.description,
        "banner_url": topic.banner_url,
        "status": topic.status.value if hasattr(topic.status, 'value') else str(topic.status),
        "created_at": topic.created_at.isoformat() + "Z",
        "updated_at": topic.updated_at.isoformat() + "Z"
    }


def format_category_response(category) -> dict:
    """格式化分类响应数据"""
    return {
        "id": str(category.id),
        "topic_id": str(category.topic_id),
        "name": category.name,
        "sort_order": category.sort_order,
        "created_at": category.created_at.isoformat() + "Z",
        "updated_at": category.updated_at.isoformat() + "Z"
    }


@topic_router.post("")
async def create_topic(
    topic_create: TopicCreate,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    创建专题（需要登录）
    
    Args:
        topic_create: 专题创建数据
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：创建的专题信息
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    
    try:
        logger.info(f"API调用: POST /topics, user_id={user_id_for_logging}")
        
        service = TopicService(db)
        # ← 修改：传递权限参数
        topic = await service.create_topic(
            obj_in=topic_create,
            user_id=user_id,
            role=role  # ← 新增
        )
        
        # ✅ 记录业务操作成功日志（INFO级别）
        logger.info(
            f"专题创建成功: topic_id={topic.id}, user={user_id_for_logging}, "
            f"status={topic.status}, title={topic.title}"
        )
        
        return success_response(data=format_topic_response(topic))
        
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"创建专题异常: user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@topic_router.get("")
async def get_topic_list(
    request: Request,  # 添加 Request 参数
    page: int = Query(default=1, ge=1, description="页码，从1开始"),
    size: int = Query(default=10, ge=1, le=100, description="每页条数"),
    title: Optional[str] = Query(default=None, description="专题标题筛选，支持模糊匹配"),  # ← 新增
    topic_id: Optional[str] = Query(default=None, description="专题ID筛选，精确匹配"),  # ← 新增
    status: Optional[str] = Query(default=None, description="状态筛选"),
    user_id: Optional[str] = Query(default=None, description="用户ID筛选"),
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
):
    """
    获取专题列表（支持匿名访问）
    
    Args:
        page: 页码
        size: 每页条数
        title: 专题标题筛选，支持模糊匹配（可选）
        topic_id: 专题ID筛选，精确匹配（可选）
        status: 状态筛选
        user_id: 用户ID筛选（查询参数，用于业务筛选特定用户的专题）
        current_user: 当前用户信息（可选，用于权限过滤）
        db: 数据库会话
    
    Returns:
        JSON响应：专题列表（分页）
    """
    # ← 新增：提取用户信息（可能为None）
    current_user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    current_user_role = current_user.get("role") if current_user else None
    
    try:
        logger.debug(f"API调用: GET /topics, page={page}, size={size}")
        
        service = TopicService(db)
        
        # 转换status参数
        status_enum = None
        if status:
            try:
                status_enum = TopicStatus(status)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content=error_response(
                        code=4001,
                        message="参数校验失败",
                        data={"error": f"无效的status值: {status}"}
                    )
                )
        
        # ← 新增：转换topic_id参数（title参数直接传递字符串，无需转换）
        topic_id_uuid = None
        if topic_id:
            try:
                topic_id_uuid = uuid.UUID(topic_id)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content=error_response(
                        code=4001,
                        message="参数校验失败",
                        data={"error": "无效的topic_id格式"}
                    )
                )
        
        # 转换user_id参数（查询参数，用于业务筛选）
        user_id_uuid = None
        if user_id:
            try:
                user_id_uuid = uuid.UUID(user_id)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content=error_response(
                        code=4001,
                        message="参数校验失败",
                        data={"error": "无效的user_id格式"}
                    )
                )
        
        # ← 修改：传递权限参数（用于权限过滤）
        # 注意：user_id_uuid是查询参数（用于业务筛选特定用户的专题），
        # current_user_id是权限参数（用于权限过滤，当前用户的public_id）
        topics, total = await service.get_topic_list(
            page=page,
            size=size,
            status=status_enum,
            title=title,  # ← 新增：传递title参数（字符串）
            topic_id=topic_id_uuid,  # ← 新增：传递topic_id参数（UUID）
            user_id=user_id_uuid,  # ← 查询参数（筛选条件，用于业务筛选）
            role=current_user_role,  # ← 新增：权限参数（用于权限过滤）
            current_user_id=current_user_id  # ← 新增：权限参数（用于权限过滤）
        )
        # 获取 base_url 用于拼接完整的 banner_url
        base_url = str(request.base_url)
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        # 构建分页响应，拼接 banner_url
        items = []
        for topic in topics:
            topic_data = format_topic_response(topic)
            # 拼接完整的 banner_url
            if topic_data["banner_url"]:
                banner_url = topic_data["banner_url"]
                if not (banner_url.startswith("http://") or banner_url.startswith("https://")):
                    relative_url = topic_data["banner_url"] if topic_data["banner_url"].startswith(
                    '/') else f'/{topic_data["banner_url"]}'
                    topic_data["banner_url"] = f"{base_url}{relative_url}"
            items.append(topic_data)

        # 构建分页响应
        paginated_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": [format_topic_response(topic) for topic in topics]
        }
        
        return success_response(data=paginated_data)
        
    except Exception as e:
        logger.error(f"获取专题列表异常: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@topic_router.get("/{topic_id}")
async def get_topic_detail(
    request: Request,  # 添加 Request 参数
    topic_id: uuid.UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
):
    """
    获取专题详情（支持匿名访问）
    
    Args:
        topic_id: 专题唯一标识
        current_user: 当前用户信息（可选）
        db: 数据库会话
    
    Returns:
        JSON响应：专题详情（包含分类和直播间）
    """
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # ✅ 提前提取用于日志的变量
    topic_id_for_logging = topic_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        topic_detail = await service.get_topic_detail(
            topic_id,
            user_id=user_id,  # ← 新增
            role=role  # ← 新增
        )

        # 获取 base_url 用于拼接完整的 banner_url
        base_url = str(request.base_url)
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        # 拼接完整的 banner_url
        if topic_detail.get("banner_url"):
            banner_url = topic_detail["banner_url"]
            if not (banner_url.startswith("http://") or banner_url.startswith("https://")):
                relative_url = topic_detail["banner_url"] if topic_detail["banner_url"].startswith(
                    '/') else f'/{topic_detail["banner_url"]}'
                topic_detail["banner_url"] = f"{base_url}{relative_url}"

        return success_response(data=topic_detail)
        
    except (TopicNotFoundException, NotFoundException) as e:  # ← 新增：捕获NotFoundException（404伪装）
        # ← 新增：返回404（隐藏Draft/Archived专题存在性）
        logger.warning(f"专题不存在或无权访问: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="Topic not found"
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"获取专题详情异常: topic_id={topic_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@topic_router.patch("/{topic_id}")
async def update_topic(
    request: Request,  # 添加 Request 参数
    topic_id: uuid.UUID,
    topic_update: TopicUpdate,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    更新专题（需要登录）
    
    Args:
        topic_id: 专题唯一标识
        topic_update: 更新数据
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：更新后的专题信息
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    topic_id_for_logging = topic_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        updated_topic = await service.update_topic(
            topic_id=topic_id,
            user_id=user_id,
            obj_in=topic_update,
            role=role  # ← 新增
        )

        # ✅ 记录业务操作成功日志（INFO级别）
        logger.info(
            f"专题更新成功: topic_id={topic_id_for_logging}, user={user_id_for_logging}"
        )
        
        return success_response(data=format_topic_response(updated_topic))
        
    except TopicNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Topic", "id": str(topic_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"更新专题异常: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@topic_router.delete("/{topic_id}")
async def delete_topic(
    topic_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    删除专题（需要登录）
    
    Args:
        topic_id: 专题唯一标识
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：删除结果
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    topic_id_for_logging = topic_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        await service.delete_topic(
            topic_id=topic_id,
            user_id=user_id,
            role=role  # ← 新增
        )
        
        return success_response(
            data={"id": str(topic_id_for_logging), "status": "deleted"}
        )
        
    except TopicNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Topic", "id": str(topic_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"删除专题异常: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@topic_router.post("/{topic_id}/banner", response_model=Dict[str, Any])
async def upload_topic_banner(
    request: Request,  # 添加 Request 参数
    topic_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    为指定专题上传横幅图片（需要登录）
    
    完全复用直播间封面上传的实现逻辑：
    - 文件校验：PNG, JPG 格式，10MB 以内
    - 权限验证：仅创建者可上传
    - 存储路径：/media/topics/{topic_id}/banner_{timestamp}.{ext}
    
    Args:
        topic_id: 专题UUID
        file: 上传的图片文件
        current_user: 当前登录用户信息
        db: 数据库会话
        
    Returns:
        标准成功响应，包含 topic_id 和 banner_url
        
    Raises:
        404: 专题不存在
        403: 权限不足
        400: 文件格式或大小不符合要求
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    topic_id_for_logging = topic_id
    
    logger.info(f"开始上传横幅: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}")
    
    # 实例化服务层
    service = TopicService(db=db)
    
    try:
        # ← 修改：传递权限参数
        updated_topic = await service.upload_topic_banner(
            topic_id=topic_id,
            file=file,
            user_id=user_id,
            role=role  # ← 新增
        )
        
        logger.info(f"横幅上传成功: topic_id={topic_id_for_logging}")

        # 获取 base_url 用于拼接完整的 banner_url
        base_url = str(request.base_url)
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        # 拼接完整的 banner_url
        full_banner_url = updated_topic.banner_url
        if full_banner_url:
            if not (full_banner_url.startswith("http://") or full_banner_url.startswith("https://")):
                relative_url = full_banner_url if full_banner_url.startswith('/') else f'/{full_banner_url}'
                full_banner_url = f"{base_url}{relative_url}"

        # 构建响应数据
        response_data = {
            "topic_id": str(updated_topic.id),
            "banner_url": updated_topic.banner_url
        }
        
        return success_response(data=response_data)
        
    except TopicNotFoundException:
        logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Topic", "id": str(topic_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        logger.warning(
            f"无权上传横幅: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={
                    "error": "权限不足", 
                    "reason": "只有创建者可以上传横幅"
                }
            )
        )
    except HTTPException as e:
        logger.warning(f"文件验证失败: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(
                code=4002,
                message="参数校验失败",
                data={"file": e.detail}
            )
        )
    except Exception as e:
        logger.error(
            f"横幅上传失败: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}", 
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=1002,
                message="数据库操作错误",
                data={"error": "服务器内部错误"}
            )
        )


@topic_router.post("/{topic_id}/categories")
async def create_category(
    topic_id: uuid.UUID,
    category_create: TopicCategoryCreate,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    创建分类（需要登录）
    
    Args:
        topic_id: 专题唯一标识
        category_create: 分类创建数据
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：创建的分类信息
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    topic_id_for_logging = topic_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        category = await service.create_category(
            topic_id=topic_id,
            user_id=user_id,
            obj_in=category_create,
            role=role  # ← 新增
        )
        
        return success_response(data=format_category_response(category))
        
    except TopicNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Topic", "id": str(topic_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"创建分类异常: topic_id={topic_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@topic_router.get("/{topic_id}/categories")
async def get_category_list(
    topic_id: uuid.UUID,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=100, ge=1, le=1000, description="每页条数"),
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类列表（继承专题可见性）
    
    Args:
        topic_id: 专题唯一标识
        page: 页码
        size: 每页条数
        current_user: 当前用户信息（可选）
        db: 数据库会话
    
    Returns:
        JSON响应：分类列表（分页）
    """
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # ✅ 提前提取用于日志的变量
    topic_id_for_logging = topic_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        categories, total = await service.get_category_list(
            topic_id=topic_id,
            page=page,
            size=size,
            user_id=user_id,  # ← 新增
            role=role  # ← 新增
        )
        
        # 构建分页响应
        paginated_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": [format_category_response(cat) for cat in categories]
        }
        
        return success_response(data=paginated_data)
        
    except (TopicNotFoundException, NotFoundException) as e:  # ← 新增：捕获NotFoundException（404伪装）
        # ← 新增：返回404（隐藏Draft/Archived专题存在性）
        logger.warning(f"专题不存在或无权访问: topic_id={topic_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="Topic not found"
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"获取分类列表异常: topic_id={topic_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


# ==================== 子路由器：分类管理 ====================

category_router = APIRouter(tags=["Topic Categories"])


@category_router.patch("/{category_id}")
async def update_category(
    category_id: uuid.UUID,
    category_update: TopicCategoryUpdate,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    更新分类（需要登录）
    
    Args:
        category_id: 分类唯一标识
        category_update: 更新数据
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：更新后的分类信息
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    category_id_for_logging = category_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        updated_category = await service.update_category(
            category_id=category_id,
            user_id=user_id,
            obj_in=category_update,
            role=role  # ← 新增
        )
        
        return success_response(data=format_category_response(updated_category))
        
    except TopicCategoryNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"分类不存在: category_id={category_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Category", "id": str(category_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: category_id={category_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"更新分类异常: category_id={category_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@category_router.delete("/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    删除分类（需要登录）
    
    Args:
        category_id: 分类唯一标识
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：删除结果
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    category_id_for_logging = category_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        await service.delete_category(
            category_id=category_id,
            user_id=user_id,
            role=role  # ← 新增
        )
        
        return success_response(
            data={"id": str(category_id_for_logging), "status": "deleted"}
        )
        
    except TopicCategoryNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"分类不存在: category_id={category_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Category", "id": str(category_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: category_id={category_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"删除分类异常: category_id={category_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@category_router.post("/{category_id}/rooms")
async def add_rooms_to_category(
    category_id: uuid.UUID,
    request: AddRoomsRequest,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    添加直播间到分类（需要登录）
    
    Args:
        category_id: 分类唯一标识
        request: 添加直播间请求
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：添加成功的记录数
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    category_id_for_logging = category_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        associations = await service.add_rooms_to_category(
            category_id=category_id,
            user_id=user_id,
            room_associations=request.rooms,
            role=role  # ← 新增
        )
        
        return success_response(
            data={"added_count": len(associations)}
        )
        
    except TopicCategoryNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"分类不存在: category_id={category_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Category", "id": str(category_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: category_id={category_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except RoomNotFoundException as e:
        logger.warning(f"直播间不存在: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4001,
                message="参数校验失败",
                data={"error": "部分直播间不存在"}
            )
        )
    except RoomAlreadyAssociatedException as e:
        logger.warning(
            f"直播间已关联: room_id={e.room_id}, category_id={e.category_id}"
        )
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4001,
                message="参数校验失败",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"添加直播间异常: category_id={category_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@category_router.get("/{category_id}/rooms")
async def get_rooms_in_category(
    category_id: uuid.UUID,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=100, ge=1, le=1000, description="每页条数"),
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
):
    """
    获取分类下的直播间列表（双重权限过滤：专题权限+直播间权限）
    
    Args:
        category_id: 分类唯一标识
        page: 页码
        size: 每页条数
        current_user: 当前用户信息（可选）
        db: 数据库会话
    
    Returns:
        JSON响应：直播间列表（分页）
    """
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # ✅ 提前提取用于日志的变量
    category_id_for_logging = category_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        rooms, total = await service.get_rooms_in_category(
            category_id=category_id,
            page=page,
            size=size,
            user_id=user_id,  # ← 新增
            role=role  # ← 新增
        )
        
        # 构建分页响应
        paginated_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": rooms
        }
        
        return success_response(data=paginated_data)
        
    except (TopicCategoryNotFoundException, TopicNotFoundException, NotFoundException) as e:  # ← 新增：捕获NotFoundException（404伪装）
        # ← 新增：返回404（隐藏Draft/Archived专题存在性）
        logger.warning(f"分类或专题不存在或无权访问: category_id={category_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在"
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"获取直播间列表异常: category_id={category_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@category_router.patch("/{category_id}/rooms/sort-order")
async def update_room_sort_order(
    category_id: uuid.UUID,
    request: UpdateRoomSortRequest,
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    更新直播间排序（需要登录）
    
    Args:
        category_id: 分类唯一标识
        request: 更新排序请求
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：更新的记录数
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    category_id_for_logging = category_id
    
    try:
        service = TopicService(db)
        
        # 转换RoomAssociation列表为字典列表
        room_sort_updates = [
            {"room_id": assoc.room_id, "sort_order": assoc.sort_order}
            for assoc in request.rooms
        ]
        
        # ← 修改：传递权限参数
        updated_count = await service.update_room_sort_order(
            category_id=category_id,
            user_id=user_id,
            room_sort_updates=room_sort_updates,
            role=role  # ← 新增
        )
        
        return success_response(
            data={"updated_count": updated_count}
        )
        
    except TopicCategoryNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"分类不存在: category_id={category_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Category", "id": str(category_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: category_id={category_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"更新排序异常: category_id={category_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@category_router.delete("/{category_id}/rooms")
async def remove_rooms_from_category(
    category_id: uuid.UUID,
    request: RemoveRoomsRequest = Body(...),
    current_user: dict = Depends(get_current_user),  # ← 保持不变：Strict Auth
    db: AsyncSession = Depends(get_db)
):
    """
    移除直播间（需要登录）
    
    Args:
        category_id: 分类唯一标识
        request: 移除直播间请求
        current_user: 当前用户信息
        db: 数据库会话
    
    Returns:
        JSON响应：删除的记录数
    """
    # ← 新增：提取用户信息（在try之前）
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")  # ← 使用.get()方法
    
    # ✅ 提前提取用于日志的变量
    user_id_for_logging = str(user_id)
    category_id_for_logging = category_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        deleted_count = await service.remove_rooms_from_category(
            category_id=category_id,
            user_id=user_id,
            room_ids=request.room_ids,
            role=role  # ← 新增
        )
        
        return success_response(
            data={"deleted_count": deleted_count}
        )
        
    except TopicCategoryNotFoundException:
        # ✅ 使用局部变量记录日志
        logger.warning(f"分类不存在: category_id={category_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在",
                data={"resource": "Category", "id": str(category_id_for_logging)}
            )
        )
    except PermissionDeniedException as e:  # ← 修改：使用PermissionDeniedException
        # ✅ 使用局部变量记录日志
        logger.warning(
            f"权限不足: category_id={category_id_for_logging}, user_id={user_id_for_logging}"
        )
        return JSONResponse(
            status_code=403,
            content=error_response(
                code=3002,
                message="操作被禁止",
                data={"error": str(e)}
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"移除直播间异常: category_id={category_id_for_logging}, "
            f"user_id={user_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


# ==================== 子路由器：直播间与专题关系 ====================

#room_router = APIRouter(prefix="/rooms", tags=["Room-Topic Relations"])
room_router = APIRouter(tags=["Room-Topic Relations"])

@room_router.get("/{room_id}/topics")
async def get_topics_by_room(
    room_id: uuid.UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
):
    """
    获取直播间关联的专题列表（双重权限过滤：直播间权限+专题权限）
    
    Args:
        room_id: 直播间唯一标识
        current_user: 当前用户信息（可选）
        db: 数据库会话
    
    Returns:
        JSON响应：专题列表
    """
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    # ✅ 提前提取用于日志的变量
    room_id_for_logging = room_id
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        topics = await service.get_topics_by_room(
            room_id,
            user_id=user_id,  # ← 新增
            role=role  # ← 新增
        )
        
        return success_response(data=topics)
        
    except (RoomNotFoundException, NotFoundException) as e:  # ← 新增：捕获NotFoundException（404伪装）
        # ← 新增：返回404（隐藏Private房间或Draft/Archived专题存在性）
        logger.warning(f"直播间或专题不存在或无权访问: room_id={room_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(
                code=2001,
                message="资源不存在"
            )
        )
    except Exception as e:
        # ✅ 使用局部变量记录未知错误
        logger.error(
            f"获取关联专题异常: room_id={room_id_for_logging}, error={str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )


@room_router.post("/batch-status")
async def batch_get_room_status(
    request: BatchStatusRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),  # ← 修改：Optional Auth
    db: AsyncSession = Depends(get_db)
):
    """
    批量获取直播间状态（Room权限过滤）
    
    Args:
        request: 批量查询请求（包含room_ids列表）
        current_user: 当前用户信息（可选）
        db: 数据库会话
    
    Returns:
        JSON响应：直播间状态列表
    """
    # ← 新增：提取用户信息（可能为None）
    user_id = uuid.UUID(current_user["user_id"]) if current_user else None
    role = current_user.get("role") if current_user else None
    
    try:
        service = TopicService(db)
        # ← 修改：传递权限参数
        room_status_list = await service.batch_get_room_status(
            request.room_ids,
            user_id=user_id,  # ← 新增
            role=role  # ← 新增
        )
        
        return success_response(data=room_status_list)
        
    except ValueError as e:
        logger.warning(f"参数校验失败: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4001,
                message="最多支持一次查询100个直播间"
            )
        )
    except RoomNotFoundException:
        logger.warning("部分直播间不存在")
        return JSONResponse(
            status_code=400,
            content=error_response(
                code=4001,
                message="部分直播间不存在"
            )
        )
    except Exception as e:
        logger.error(f"批量查询状态异常: error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误")
        )

