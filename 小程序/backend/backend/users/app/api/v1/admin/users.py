"""
后台管理API - 用户管理 (重构版)
重构后的端点层只负责：
- 处理 FastAPI 的 Request 和 Depends
- 实例化 AdminUserService
- 调用 AdminUserService 中对应的方法
- 捕获 Service 层抛出的业务异常并转换为标准的 JSONResponse
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.schemas.users import (
    UserResponse, UserUpdate, UserFilterParams
)
from app.models.users import User, UserRole, EntityStatus
from app.api.v1.deps import get_current_admin_user
from app.services.admin_user_service import (
    AdminUserService,
    TargetUserNotFoundError,
    PermissionDeniedError,
    InvalidAdminUpdateError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Admin - Users"])


# ============================================================================
# API 端点实现
# ============================================================================

@router.get("", response_model=dict)
async def get_users_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: Optional[str] = Query("created_at:desc", description="排序字段"),
    username: Optional[str] = Query(None, description="按用户名模糊搜索"),
    email: Optional[str] = Query(None, description="按邮箱精确搜索"),
    phone_number: Optional[str] = Query(None, description="按手机号精确搜索"),
    nickname: Optional[str] = Query(None, description="按昵称模糊搜索"),
    role: Optional[UserRole] = Query(None, description="按角色筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    can_stream: Optional[bool] = Query(None, description="按开播状态筛选（false=被禁止开播）"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 分页、排序、筛选获取系统中的所有用户列表
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    admin_username_for_logging = admin_user.username
    
    logger.info(f"管理员开始查询用户列表: admin_user_id={admin_user_id_for_logging}, page={page}, size={size}")
    
    try:
        # 实例化服务层
        admin_user_service = AdminUserService(db)
        
        # 构建筛选条件
        filters = UserFilterParams(
            username=username,
            email=email,
            phone_number=phone_number,
            nickname=nickname,
            role=role,
            status=EntityStatus(status) if status else None,
            can_stream=can_stream,
        )
        
        # 调用服务层方法获取分页用户列表
        paginated_result = await admin_user_service.list_users(
            filters=filters, page=page, size=size
        )
        
        logger.info(f"成功查询用户列表: admin_user_id={admin_user_id_for_logging}, total={paginated_result.get('total', 0)}, count={len(paginated_result.get('items', []))}")
        return success_response(data=paginated_result)
        
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"查询用户列表失败: admin_user_id={admin_user_id_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )


@router.patch("/{user_uuid}", response_model=dict)
async def update_user(
    user_uuid: uuid.UUID = Path(..., description="用户UUID"),
    user_update: UserUpdate = ...,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 更新指定用户：开播权、状态；改角色仅超管
    """
    # 🔴 主动变量提取（安全红线）
    admin_user_id_for_logging = admin_user.id
    admin_role_for_logging = admin_user.role
    user_uuid_for_logging = str(user_uuid)
    
    logger.info(f"管理员开始更新用户: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}")
    
    try:
        # 实例化服务层
        admin_user_service = AdminUserService(db)
        
        # 调用服务层方法更新用户
        updated_user = await admin_user_service.update_user_by_admin(
            admin_user=admin_user, user_uuid=user_uuid, user_update=user_update
        )
        
        # 序列化响应数据
        response_data = UserResponse.model_validate(updated_user)
        
        logger.info(f"成功更新用户: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}")
        return success_response(data=response_data)
        
    except TargetUserNotFoundError as e:
        logger.warning(f"目标用户不存在: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2004, message=str(e))
        )
    except PermissionDeniedError as e:
        logger.warning(f"权限不足: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message=str(e))
        )
    except InvalidAdminUpdateError as e:
        logger.warning(
            f"管理端更新参数非法: admin_user_id={admin_user_id_for_logging}, "
            f"target_user_uuid={user_uuid_for_logging}, error={e}"
        )
        return JSONResponse(
            status_code=422,
            content=error_response(code=4001, message=str(e))
        )
    except Exception as e:
        # 使用安全的局部变量进行日志记录，避免访问可能已失效的ORM对象
        logger.error(f"更新用户失败: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        )
