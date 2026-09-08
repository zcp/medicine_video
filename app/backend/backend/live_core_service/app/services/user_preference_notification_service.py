"""
用户偏好与通知模块 - Service层

职责：业务逻辑层，负责业务编排、权限检查、事务管理
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user_preference_notification as crud
from app.schemas.user_preference_notification import (
    UserPreferencesUpdate,
    UserPreferencesItem,
    NotificationItem,
    NotificationCreateRequest,
    NotificationBatchCreateResponse,
    NotificationUpdateRequest,
    NotificationBatchDeleteRequest,
    NotificationListResponse,
)
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
)
from app.core.permissions import check_admin_permission

logger = logging.getLogger(__name__)


class UserPreferenceNotificationService:
    """用户偏好与通知Service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def _check_user_preferences_ownership(
        self,
        resource_owner_id: UUID,
        current_user_id: UUID,
        user_role: str
    ) -> None:
        """
        检查用户资源所有权
        
        Args:
            resource_owner_id: 资源所有者ID
            current_user_id: 当前用户ID
            user_role: 当前用户角色
            
        Raises:
            PermissionDeniedException: 无权操作
            NotFoundException: 资源不存在或无权访问
        """
        # 管理员：可以操作所有用户的资源
        if user_role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源所有者：可以操作自己的资源
        if resource_owner_id == current_user_id:
            return
        
        # 其他用户：返回404隐藏存在性
        raise NotFoundException("Resource not found")
    
    # ==================== User Preferences Service ====================
    
    async def get_preferences(
        self,
        user_id: UUID,
        role: str
    ) -> UserPreferencesItem:
        """
        获取用户偏好设置
        
        Args:
            user_id: 用户ID
            role: 用户角色
            
        Returns:
            UserPreferencesItem对象
            
        Raises:
            NotFoundException: 用户不存在
        """
        try:
            prefs = await crud.get_preferences(self.db, user_id)
            
            if not prefs:
                # 首次访问，返回默认偏好
                import uuid
                from datetime import datetime, timezone
                from app.models.user_preference_notification import UserPreferences
                prefs = UserPreferences(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    theme_mode="auto",  # ✅ 新增：第114行后插入
                    homepage_view_mode="double",  # ✅ 新增：第115行后插入
                    created_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
                    updated_at=datetime.now(timezone.utc),  # ✅ 修复：添加必需字段
                )
                # 不保存到数据库，只返回默认值
            
            return UserPreferencesItem.model_validate(prefs)
        except Exception as e:
            self.logger.error(f"获取用户偏好失败: user_id={str(user_id)[:8]}, error={str(e)}")
            raise
    
    async def update_preferences(
        self,
        user_id: UUID,
        prefs_update: UserPreferencesUpdate,
        role: str
    ) -> UserPreferencesItem:
        """
        更新用户偏好设置
        
        Args:
            user_id: 用户ID
            prefs_update: 偏好更新数据
            role: 用户角色
            
        Returns:
            更新后的UserPreferencesItem对象
            
        Raises:
            InvalidParameterException: 参数错误
        """
        try:
            # 创建或更新偏好
            prefs = await crud.create_or_update_preferences(
                self.db,
                user_id,
                prefs_update
            )
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(prefs)
            
            self.logger.info(f"更新用户偏好成功: user_id={str(user_id)[:8]}")
            return UserPreferencesItem.model_validate(prefs)
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"更新用户偏好失败: user_id={str(user_id)[:8]}, error={str(e)}")
            raise
    
    # ==================== Notifications Service ====================
    
    async def get_notifications_list(
        self,
        user_id: UUID,
        page: int,
        size: int,
        is_read: Optional[bool],
        notification_type: Optional[str],
        role: str
    ) -> NotificationListResponse:
        """
        获取用户通知列表
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 每页大小
            is_read: 是否已读筛选
            notification_type: 通知类型筛选
            role: 用户角色
            
        Returns:
            NotificationListResponse对象
        """
        try:
            items, total = await crud.get_notifications(
                self.db,
                user_id=user_id,
                page=page,
                size=size,
                is_read=is_read,
                notification_type=notification_type,
                current_user_id=user_id,
                role=role
            )
            
            # 转换为Schema
            notification_items = [NotificationItem.model_validate(item) for item in items]
            
            return NotificationListResponse(
                items=notification_items,
                total=total,
                page=page,
                size=size,
                has_more=(page * size) < total
            )
        except Exception as e:
            self.logger.error(f"获取通知列表失败: user_id={str(user_id)[:8]}, error={str(e)}")
            raise

    async def get_notification_detail(
        self,
        notification_id: UUID,
        user_id: UUID,
        role: str
    ) -> NotificationItem:
        """
        获取通知详情

        Args:
            notification_id: 通知ID
            user_id: 用户ID
            role: 用户角色

        Returns:
            NotificationItem对象

        Raises:
            NotFoundException: 通知不存在或不属于当前用户
        """
        try:
            notification = await crud.get_notification(self.db, notification_id, user_id)

            if not notification:
                raise NotFoundException("通知不存在或不属于当前用户")

            return NotificationItem.model_validate(notification)
        except NotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"获取通知详情失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
            raise
    
    async def get_unread_count(self, user_id: UUID) -> Dict[str, int]:
        """
        获取未读通知数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            {"unread_count": int}
        """
        try:
            count = await crud.get_unread_count(self.db, user_id)
            return {"unread_count": count}
        except Exception as e:
            self.logger.error(f"获取未读数量失败: user_id={str(user_id)[:8]}, error={str(e)}")
            raise
    
    async def mark_notification_as_read(
        self,
        notification_id: UUID,
        user_id: UUID,
        role: str
    ) -> None:
        """
        标记通知为已读
        
        Args:
            notification_id: 通知ID
            user_id: 用户ID
            role: 用户角色
            
        Raises:
            NotFoundException: 通知不存在或不属于当前用户
        """
        try:
            notification = await crud.mark_as_read(self.db, notification_id, user_id)
            
            if not notification:
                raise NotFoundException("通知不存在或不属于当前用户")
            
            await self.db.commit()
            self.logger.info(f"标记通知为已读: notification_id={str(notification_id)[:8]}")
        except NotFoundException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"标记通知为已读失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
            raise
    
    async def mark_all_notifications_as_read(self, user_id: UUID) -> Dict[str, int]:
        """
        标记所有通知为已读
        
        Args:
            user_id: 用户ID
            
        Returns:
            {"updated_count": int}
        """
        try:
            count = await crud.mark_all_as_read(self.db, user_id)
            await self.db.commit()
            self.logger.info(f"标记所有通知为已读: user_id={str(user_id)[:8]}, count={count}")
            return {"updated_count": count}
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"标记所有通知为已读失败: user_id={str(user_id)[:8]}, error={str(e)}")
            raise
    
    async def create_notifications_batch(
        self,
        user_ids: List[UUID],
        notification_data: NotificationCreateRequest,
        admin_role: str
    ) -> NotificationBatchCreateResponse:
        """
        批量创建通知（管理员）
        
        Args:
            user_ids: 用户ID列表（空列表表示全部用户）
            notification_data: 通知数据
            admin_role: 管理员角色
            
        Returns:
            NotificationBatchCreateResponse对象
            
        Raises:
            PermissionDeniedException: 非管理员
            InvalidParameterException: 参数错误
        """
        # 权限检查
        check_admin_permission(admin_role)
        
        try:
            # 处理user_ids
            if not user_ids:
                # 空列表表示全部用户，需要查询所有用户ID
                #from app.models.user_core import User
                #from sqlalchemy import select
                #query = select(User.public_id)
                #result = await self.db.execute(query)
                #user_ids = [row[0] for row in result.all()]
                # 注意：user表在user_service数据库中，live_core_service无法直接访问
                # 因此不支持"全部用户"功能，必须明确指定user_ids
                raise InvalidParameterException(
                    "user_ids不能为空，请明确指定要通知的用户ID列表（user表在user_service数据库中，live_core_service无法直接访问）"
                )
            
            # 构建通知列表
            notifications_list = [
                {
                    "user_id": uid,
                    "title": notification_data.title,
                    "content": notification_data.content,
                    "notification_type": notification_data.notification_type,
                    "related_id": notification_data.related_id,
                    "related_type": notification_data.related_type,
                }
                for uid in user_ids
            ]
            
            # 批量创建
            count = await crud.bulk_create_notifications(self.db, notifications_list)
            await self.db.commit()
            
            self.logger.info(f"批量创建通知: count={count}")
            return NotificationBatchCreateResponse(
                total_created=count,
                user_ids=user_ids
            )
        except PermissionDeniedException:
            raise
        except InvalidParameterException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"批量创建通知失败: error={str(e)}")
            raise
    
    async def get_notifications_list_admin(
        self,
        page: int,
        size: int,
        user_id_filter: Optional[UUID],
        notification_type: Optional[str],
        is_read: Optional[bool],
        admin_role: str
    ) -> NotificationListResponse:
        """
        管理员获取通知列表
        
        Args:
            page: 页码
            size: 每页大小
            user_id_filter: 用户ID筛选
            notification_type: 通知类型筛选
            is_read: 是否已读筛选
            admin_role: 管理员角色
            
        Returns:
            NotificationListResponse对象
            
        Raises:
            PermissionDeniedException: 非管理员
        """
        # 权限检查
        check_admin_permission(admin_role)
        
        try:
            items, total = await crud.get_notifications_admin(
                self.db,
                page=page,
                size=size,
                user_id=user_id_filter,
                notification_type=notification_type,
                is_read=is_read
            )
            
            notification_items = [NotificationItem.model_validate(item) for item in items]
            
            return NotificationListResponse(
                items=notification_items,
                total=total,
                page=page,
                size=size,
                has_more=(page * size) < total
            )
        except PermissionDeniedException:
            raise
        except Exception as e:
            self.logger.error(f"管理员获取通知列表失败: error={str(e)}")
            raise
    
    async def update_notification(
        self,
        notification_id: UUID,
        update_data: NotificationUpdateRequest,
        admin_role: str
    ) -> NotificationItem:
        """
        更新通知（管理员）
        
        Args:
            notification_id: 通知ID
            update_data: 更新数据
            admin_role: 管理员角色
            
        Returns:
            NotificationItem对象
            
        Raises:
            PermissionDeniedException: 非管理员
            NotFoundException: 通知不存在
        """
        # 权限检查
        check_admin_permission(admin_role)
        
        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            notification = await crud.update_notification(
                self.db,
                notification_id,
                update_dict
            )
            
            if not notification:
                raise NotFoundException("通知不存在")
            
            await self.db.commit()
            await self.db.refresh(notification)
            
            self.logger.info(f"更新通知: notification_id={str(notification_id)[:8]}")
            return NotificationItem.model_validate(notification)
        except PermissionDeniedException:
            raise
        except NotFoundException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"更新通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
            raise
    
    async def delete_notification(
        self,
        notification_id: UUID,
        admin_role: str
    ) -> None:
        """
        删除通知（管理员）
        
        Args:
            notification_id: 通知ID
            admin_role: 管理员角色
            
        Raises:
            PermissionDeniedException: 非管理员
            NotFoundException: 通知不存在
        """
        # 权限检查
        check_admin_permission(admin_role)
        
        try:
            deleted = await crud.delete_notification(self.db, notification_id)
            
            if not deleted:
                raise NotFoundException("通知不存在")
            
            await self.db.commit()
            self.logger.info(f"删除通知: notification_id={str(notification_id)[:8]}")
        except PermissionDeniedException:
            raise
        except NotFoundException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"删除通知失败: notification_id={str(notification_id)[:8]}, error={str(e)}")
            raise
    
    async def batch_delete_notifications(
        self,
        delete_request: NotificationBatchDeleteRequest,
        admin_role: str
    ) -> Dict[str, int]:
        """
        批量删除通知（管理员）
        
        Args:
            delete_request: 删除请求
            admin_role: 管理员角色
            
        Returns:
            {"deleted_count": int}
            
        Raises:
            PermissionDeniedException: 非管理员
        """
        # 权限检查
        check_admin_permission(admin_role)
        
        try:
            count = await crud.batch_delete_notifications(
                self.db,
                notification_ids=delete_request.notification_ids,
                delete_before=delete_request.delete_before,
                notification_type=delete_request.notification_type,
                is_read=delete_request.is_read
            )
            
            await self.db.commit()
            self.logger.info(f"批量删除通知: count={count}")
            return {"deleted_count": count}
        except PermissionDeniedException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"批量删除通知失败: error={str(e)}")
            raise
