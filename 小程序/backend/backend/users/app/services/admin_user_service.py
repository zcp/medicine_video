"""
管理员用户服务层 - AdminUserService
封装所有管理员用户管理相关的业务逻辑，包括用户查询、更新等管理功能
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis_client
from app.crud import crud_user
from app.schemas.users import (
    UserResponse, UserUpdate, UserFilterParams
)
from app.models.users import User, UserRole, EntityStatus

logger = logging.getLogger(__name__)

# ADMIN 运营主路径允许写入的 status
_ADMIN_ALLOWED_STATUSES = {EntityStatus.NORMAL, EntityStatus.BANNED}


# ============================================================================
# 业务异常定义
# ============================================================================

class AdminUserServiceException(Exception):
    """管理员用户服务基础异常"""
    pass


class TargetUserNotFoundError(AdminUserServiceException):
    """目标用户不存在异常"""
    def __init__(self, user_uuid: str, message: str = "用户不存在"):
        self.user_uuid = user_uuid
        super().__init__(f"{message}: {user_uuid}")


class PermissionDeniedError(AdminUserServiceException):
    """权限不足异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message)


class InvalidAdminUpdateError(AdminUserServiceException):
    """管理端更新参数不合法（如 ADMIN 写非运营主路径 status）"""
    def __init__(self, message: str = "参数非法"):
        super().__init__(message)


# ============================================================================
# 管理员用户服务类
# ============================================================================

class AdminUserService:
    """管理员用户服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化管理员用户服务
        
        Args:
            db: 数据库会话
        """
        self.db = db

    async def _revoke_user_sessions(self, user_public_id: str) -> None:
        """写入与 AuthService 相同语义的会话吊销 Key"""
        try:
            redis_client = get_redis_client()
            revocation_key = f"user_sessions_revoked:{user_public_id}"
            await redis_client.set(
                revocation_key,
                datetime.utcnow().isoformat(),
                ex=86400 * 7,
            )
            logger.info(f"已吊销用户所有会话: public_id={user_public_id}")
        except Exception as e:
            logger.error(f"吊销用户会话失败: public_id={user_public_id}, error={e}")
            raise
    
    async def list_users(self, filters: UserFilterParams, page: int, size: int) -> Dict[str, Any]:
        """
        分页、排序、筛选获取系统中的所有用户列表
        
        Args:
            filters: 筛选条件
            page: 页码
            size: 每页数量
            
        Returns:
            包含分页信息的用户列表字典
        """
        logger.info(f"开始查询用户列表: page={page}, size={size}, filters={filters}")
        
        try:
            # 1. 计算分页参数
            skip = (page - 1) * size
            
            # 2. 数据查询
            # a. 获取筛选后的用户总数
            total = await crud_user.count_with_filtering(self.db, filters=filters)
            
            # b. 获取当页的用户列表
            users = await crud_user.get_multi_with_filtering(
                self.db, skip=skip, limit=size, filters=filters
            )
            
            # 3. 序列化 - 将SQLAlchemy对象列表转换为Pydantic模型
            user_responses = []
            for user in users:
                try:
                    user_response = UserResponse.model_validate(user)
                    user_responses.append(user_response)
                except Exception as e:
                    user_id = getattr(user, 'id', 'unknown')
                    logger.warning(f"序列化用户失败: user_id={user_id}, error={e}")
                    # 跳过失败的用户，继续处理其他用户
                    continue
            
            # 4. 构建分页响应数据
            paginated_result = {
                "total": total,
                "page": page,
                "size": size,
                "items": user_responses
            }
            
            logger.info(f"成功查询用户列表: total={total}, count={len(user_responses)}")
            return paginated_result
            
        except Exception as e:
            logger.error(f"查询用户列表失败: page={page}, size={size}, error={e}")
            raise
    
    async def update_user_by_admin(self, admin_user: User, user_uuid: uuid.UUID, user_update: UserUpdate) -> User:
        """
        管理员更新指定用户的核心信息，如禁止/恢复开播、状态；改角色仅超管
        
        Args:
            admin_user: 管理员用户对象
            user_uuid: 目标用户UUID
            user_update: 用户更新数据
            
        Returns:
            更新后的用户对象
            
        Raises:
            TargetUserNotFoundError: 目标用户不存在
            PermissionDeniedError: 权限不足
            InvalidAdminUpdateError: 参数非法
        """
        # 🔴 主动变量提取（安全红线）
        admin_user_id_for_logging = admin_user.id
        admin_role_for_logging = admin_user.role
        user_uuid_for_logging = str(user_uuid)
        
        logger.info(f"开始更新用户: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}")
        
        try:
            # 1. 用户查询 - 根据UUID获取目标用户
            user_to_update = await crud_user.get_by_uuid(self.db, public_id=user_uuid)
            if not user_to_update:
                logger.warning(f"目标用户不存在: user_uuid={user_uuid_for_logging}")
                raise TargetUserNotFoundError(user_uuid_for_logging)

            # 1.1 禁止管理员改自己（防自封/自降权锁死后台）
            if user_to_update.public_id == admin_user.public_id:
                logger.warning(
                    f"禁止修改自己的账号: admin_user_id={admin_user_id_for_logging}"
                )
                raise PermissionDeniedError("禁止修改自己的账号")
            
            # 🔴 提取目标用户安全变量
            target_user_id_for_logging = user_to_update.id
            target_user_role_for_logging = user_to_update.role
            old_role = user_to_update.role
            old_can_stream = bool(getattr(user_to_update, "can_stream", True))
            old_status = user_to_update.status
            
            # 2. 权限检查 (静态) - ADMIN不能修改SUPERADMIN
            if (admin_user.role == UserRole.ADMIN and 
                user_to_update.role == UserRole.SUPERADMIN):
                logger.warning(f"管理员权限不足: admin_user_id={admin_user_id_for_logging}, target_user_role={target_user_role_for_logging}")
                raise PermissionDeniedError("管理员无权修改超级管理员")
            
            update_data = user_update.model_dump(exclude_unset=True)

            # 3. V2：仅 SUPERADMIN 可修改 role
            if "role" in update_data and admin_user.role != UserRole.SUPERADMIN:
                logger.warning(
                    f"非超管尝试修改角色: admin_user_id={admin_user_id_for_logging}, "
                    f"admin_role={admin_role_for_logging}"
                )
                raise PermissionDeniedError("仅超级管理员可修改用户角色")

            # 4. ADMIN 日常 status 仅 NORMAL ↔ BANNED
            if "status" in update_data and admin_user.role == UserRole.ADMIN:
                new_status = update_data["status"]
                if isinstance(new_status, str):
                    new_status = EntityStatus(new_status)
                if new_status not in _ADMIN_ALLOWED_STATUSES:
                    raise InvalidAdminUpdateError(
                        "管理员仅可将状态设为 NORMAL 或 BANNED"
                    )
            
            # 5. 数据更新 - 更新用户信息
            updated_user = await crud_user.update(
                self.db, db_obj=user_to_update, obj_in=user_update
            )

            # 6. 封禁 / 禁止开播 / 降权 → 吊销会话（使旧 access 立刻失效）
            new_status = updated_user.status
            new_can_stream = bool(getattr(updated_user, "can_stream", True))
            new_role = updated_user.role
            should_revoke = False
            if new_status in (EntityStatus.BANNED, EntityStatus.DELETED) and new_status != old_status:
                should_revoke = True
            if old_can_stream and not new_can_stream:
                should_revoke = True
            # 降权：目标角色权限级别下降（简化：原为 ADMIN/SUPERADMIN 且新角色更低）
            _role_rank = {
                UserRole.REGULAR: 0,
                UserRole.MODERATOR: 1,
                UserRole.ADMIN: 2,
                UserRole.SUPERADMIN: 3,
            }
            if _role_rank.get(new_role, 0) < _role_rank.get(old_role, 0):
                should_revoke = True

            if should_revoke:
                await self._revoke_user_sessions(str(updated_user.public_id))
            
            logger.info(f"成功更新用户: admin_user_id={admin_user_id_for_logging}, target_user_id={target_user_id_for_logging}")
            return updated_user
            
        except (TargetUserNotFoundError, PermissionDeniedError, InvalidAdminUpdateError):
            raise
        except Exception as e:
            logger.error(f"更新用户失败: admin_user_id={admin_user_id_for_logging}, target_user_uuid={user_uuid_for_logging}, error={e}")
            raise
