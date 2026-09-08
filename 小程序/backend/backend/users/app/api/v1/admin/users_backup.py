"""
后台管理API - 用户管理
提供用户查询、更新等管理功能
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.responses import success_response, error_response
from app.crud import crud_user
from app.schemas.users import (
    UserResponse, UserUpdate, UserFilterParams,
    PaginatedUsersResponse
)
from app.models.users import User, UserRole
from app.api.v1.deps import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Admin - Users"])


@router.get("", response_model=dict)
async def get_users_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: Optional[str] = Query("created_at:desc", description="排序字段"),
    username: Optional[str] = Query(None, description="按用户名模糊搜索"),
    email: Optional[str] = Query(None, description="按邮箱精确搜索"),
    role: Optional[UserRole] = Query(None, description="按角色筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    (管理员) 分页、排序、筛选获取系统中的所有用户列表
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    admin_username_for_logging = admin_user.username
    
    logger.info(f"管理员开始查询用户列表: admin_user_id={admin_user_id_for_logging}, page={page}, size={size}")
    
    try:
        # 构建筛选条件
        from app.models.users import EntityStatus
        filters = UserFilterParams(
            username=username,
            email=email,
            role=role,
            status=EntityStatus(status) if status else None
        )
        
        # 计算分页参数
        skip = (page - 1) * size
        
        # 数据查询
        total = await crud_user.count_with_filtering(db, filters=filters)
        users = await crud_user.get_multi_with_filtering(
            db, skip=skip, limit=size, filters=filters
        )
        
        # 构建响应
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        response_data = {
            "total": total,
            "page": page,
            "size": size,
            "items": user_responses
        }
        
        logger.info(f"成功查询用户列表: admin_user_id={admin_user_id_for_logging}, total={total}, count={len(users)}")
        return success_response(response_data)
        
    except Exception as e:
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
    (管理员) 更新指定用户的核心信息，如角色、状态
    """
    # 【安全日志准备】: 提取管理员信息到局部变量
    admin_user_id_for_logging = admin_user.id
    admin_role_for_logging = admin_user.role
    
    logger.info(f"管理员开始更新用户: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}")
    
    try:
        # 用户查询
        user_to_update = await crud_user.get_by_uuid(db, public_id=user_uuid)
        if not user_to_update:
            logger.warning(f"目标用户不存在: user_uuid={user_uuid}")
            return JSONResponse(
                status_code=404,
                content=error_response(code=2004, message='用户不存在')
            )
        
        # 【安全日志准备】: 提取目标用户信息到局部变量
        target_user_id_for_logging = user_to_update.id
        target_user_role_for_logging = user_to_update.role
        
        # 权限检查：ADMIN不能修改SUPERADMIN
        if (admin_user.role == UserRole.ADMIN and 
            user_to_update.role == UserRole.SUPERADMIN):
            logger.warning(f"管理员权限不足: admin_user_id={admin_user_id_for_logging}, target_user_role={target_user_role_for_logging}")
            return JSONResponse(
                status_code=403,
                content=error_response(code=3002, message='权限不足')
            )
        
        # 如果要修改角色，再次检查权限
        update_data = user_update.model_dump(exclude_unset=True)
        if "role" in update_data:
            new_role = update_data["role"]
            if (admin_user.role == UserRole.ADMIN and 
                new_role == UserRole.SUPERADMIN):
                logger.warning(f"管理员无权设置超级管理员角色: admin_user_id={admin_user_id_for_logging}")
                return JSONResponse(
                    status_code=403,
                    content=error_response(code=3002, message='权限不足')
                )
        
        # 数据更新
        updated_user = await crud_user.update(
            db, db_obj=user_to_update, obj_in=user_update
        )
        
        # 构建响应
        response_data = UserResponse.model_validate(updated_user)
        
        logger.info(f"成功更新用户: admin_user_id={admin_user_id_for_logging}, target_user_id={target_user_id_for_logging}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"更新用户失败: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid}, error={e}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message='数据库查询错误')
        ) 