"""
LiveCore Service - Room Service

This module contains the business logic layer for LiveRoom operations,
implementing all business rules and validation logic.
"""

import uuid
import logging
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.crud import room as crud_room
from app.crud.content_management import set_live_room_categories as crud_set_live_room_categories
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate
from app.models.live_core import LiveRoom
from app.core.file_handler import FileHandler
from app.core.permissions import check_room_visibility, check_room_owner_or_admin
from app.exceptions import (
    RoomNotFoundException,
    ActionForbiddenException,
    ParentRoomNotFoundException,
    NotFoundException,
    PermissionDeniedException
)

# 设置日志
logger = logging.getLogger(__name__)


class RoomService:
    """
    房间业务逻辑服务类
    
    封装所有与LiveRoom相关的业务逻辑，包括业务规则验证、
    数据一致性检查等。该层不应了解HTTP请求/响应相关的内容。
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化房间服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db

    def _check_room_visibility(
        self,
        room: LiveRoom,
        user_id: Optional[uuid.UUID],
        role: Optional[str]
    ) -> None:
        """
        统一的房间可见性校验逻辑

        委托给公共函数 check_room_visibility 实现。
        保留此方法避免改动外部调用方。

        Raises:
            NotFoundException: 房间不存在或无权访问（404）
        """
        # Admin 查看 Private 资源的审计日志（仅 room_service 需要记录具体资源信息）
        if room.is_private and role in ('ADMIN', 'SUPERADMIN') and room.user_id != user_id:
            logger.info(
                f"Admin查看Private资源: admin={user_id}, role={role}, "
                f"room_id={room.id}, owner={room.user_id}"
            )
        check_room_visibility(room, user_id, role)

    def _check_write_permission(
        self,
        room: LiveRoom,
        user_id: uuid.UUID,
        role: str
    ) -> None:
        """
        写操作权限校验（修改/删除）

        委托给公共函数 check_room_owner_or_admin 实现。
        保留此方法避免改动外部调用方。

        Raises:
            PermissionDeniedException: 无权修改（403）
        """
        check_room_owner_or_admin(room, user_id, role)

    async def create_new_room(
        self, 
        room_in: LiveRoomCreate, 
        user_id: uuid.UUID,
        role: str,  # ← 新增：权限参数
        can_stream: bool = True,  # PR 1B: 开播资格（向后兼容默认 True）
    ) -> LiveRoom:
        """
        创建新的直播房间
        
        业务逻辑流程:
        1. 如果指定了parent_room_id，检查父房间是否存在
        2. 如果父房间不存在，抛出ParentRoomNotFoundException
        3. 调用CRUD层创建新房间
        
        Args:
            room_in: 房间创建请求数据
            user_id: 用户ID（从JWT的user_id字段提取）
            role: 用户角色（从JWT的role字段提取）
            
        Returns:
            创建的房间对象
            
        Raises:
            ParentRoomNotFoundException: 当指定的父房间不存在时
        """
        logger.info(f"开始创建新房间: user_id={user_id}, title={room_in.title}")
        
        try:
            # PR 1B: 开播门禁（ADMIN/SUPERADMIN 在 ADMIN_STREAM_BYPASS=true 时放行；
            # REGULAR/MODERATOR 看 can_stream；访客/未知角色一律拒绝）
            from app.core.config import settings
            role_upper = (role or "").upper()
            admin_bypass = (
                settings.ADMIN_STREAM_BYPASS
                and role_upper in ("ADMIN", "SUPERADMIN")
            )
            if admin_bypass:
                pass
            elif role_upper not in ("REGULAR", "MODERATOR"):
                raise PermissionDeniedException("无开播权限")
            elif not can_stream:
                raise PermissionDeniedException("你已被禁止开播，请联系管理员")

            # PR 2: 内容安全校验（房间标题）
            await _check_room_content_safety(self.db, title=room_in.title, description=room_in.description, user_id=user_id)

            # 如果指定了父房间ID，检查父房间是否存在
            if room_in.parent_room_id:
                logger.info(f"检查父房间是否存在: parent_room_id={room_in.parent_room_id}")
                parent_room = await crud_room.get(db=self.db, room_id=room_in.parent_room_id)
                if not parent_room:
                    logger.warning(f"父房间不存在: parent_room_id={room_in.parent_room_id}")
                    raise ParentRoomNotFoundException()
                logger.info(f"父房间验证通过: parent_room_id={room_in.parent_room_id}")
            
            # 创建新房间
            room = await crud_room.create(db=self.db, obj_in=room_in, user_id=user_id)
            logger.info(f"成功创建新房间: room_id={room.id}, title={room.title}")

            # 关联分类（若在创建时指定；P1-5: 校验分类有效性）
            if room_in.category_ids is not None:
                from app.models.content_management import Category
                from sqlalchemy import select as sa_select
                # 校验分类存在且已启用
                cat_stmt = sa_select(Category.id).where(
                    Category.id.in_(room_in.category_ids),
                    Category.is_active == True
                )
                cat_result = await self.db.execute(cat_stmt)
                valid_cat_ids = {row[0] for row in cat_result.all()}
                invalid_ids = set(room_in.category_ids) - valid_cat_ids
                if invalid_ids:
                    logger.warning(
                        f"创建房间时指定了无效/禁用的分类: room_title={room_in.title}, "
                        f"invalid_ids={[str(c)[:8] for c in invalid_ids]}"
                    )
                if not valid_cat_ids:
                    logger.info(f"创建房间时所有分类无效，跳过分类关联: room_title={room_in.title}")
                else:
                    valid_list = [c for c in room_in.category_ids if c in valid_cat_ids]
                    primary = valid_list[0] if valid_list else None
                    await crud_set_live_room_categories(
                        db=self.db,
                        room_id=room.id,
                        category_ids=valid_list,
                        mode='replace',
                        primary_category_id=primary
                    )
                    await self.db.commit()
                    await self.db.refresh(room)
                    logger.info(f"房间分类关联成功: room_id={room.id}, categories={len(valid_list)}")

            return room
            
        except ParentRoomNotFoundException:
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"创建房间失败: user_id={user_id}, title={room_in.title}, error={str(e)}", exc_info=True)
            raise

    async def get_room_list(
        self, 
        page: int, 
        size: int, 
        user_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None,  # ← 新增：权限参数
        owner_only: bool = False,
        status: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> Tuple[List[LiveRoom], int]:
        """
        获取房间列表（支持匿名访问）
        
        业务逻辑流程:
        1. 计算skip值
        2. 调用CRUD层获取分页数据（CRUD层会根据权限进行SQL过滤）
        
        Args:
            page: 页码
            size: 每页大小
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
            
        Returns:
            房间列表和总数的元组
        """
        logger.info(f"开始获取房间列表: page={page}, size={size}, user_id={user_id}, role={role}, owner_only={owner_only}")
        
        try:
            # 计算skip值
            skip = (page - 1) * size

            # 根据 owner_only 标志选择不同的查询路径：
            # - owner_only=True 且为普通用户时：仅返回当前用户创建的房间（管理后台 RoomList 视图）
            # - 其他情况：沿用通用的 Public+Own / Admin All / Anonymous Public 规则
            if owner_only and user_id is not None and role not in ["ADMIN", "SUPERADMIN"]:
                rooms, total = await crud_room.get_multi_and_total_by_owner(
                    db=self.db,
                    skip=skip,
                    limit=size,
                    owner_id=user_id,
                    status=status,
                    created_after=created_after,
                    created_before=created_before,
                )
            else:
                # ← 调用通用权限过滤版本（Repository 层根据 role/user_id 进行 SQL 过滤）
                rooms, total = await crud_room.get_multi_and_total(
                    db=self.db,
                    skip=skip,
                    limit=size,
                    user_id=user_id,
                    role=role,
                    status=status,
                    created_after=created_after,
                    created_before=created_before,
                )
            
            logger.info(f"成功获取房间列表: 返回{len(rooms)}条记录, 总数={total}")
            return rooms, total
            
        except Exception as e:
            logger.error(f"获取房间列表失败: page={page}, size={size}, user_id={user_id}, error={str(e)}", exc_info=True)
            raise

    async def list_admin_rooms(
        self,
        page: int = 1,
        size: int = 20,
        q: Optional[str] = None,
        owner_user_id: Optional[uuid.UUID] = None,
        is_private: Optional[bool] = None,
    ) -> Tuple[List[LiveRoom], int]:
        skip = (page - 1) * size
        rooms, total = await crud_room.get_multi_and_total(
            db=self.db,
            skip=skip,
            limit=size,
            role="ADMIN",
            owner_user_id=owner_user_id,
            is_private=is_private,
            q=q,
        )
        return rooms, total

    async def get_room_details(
        self, 
        room_id: uuid.UUID, 
        user_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> LiveRoom:
        """
        获取房间详情（支持匿名访问）
        
        业务逻辑流程:
        1. 调用CRUD层获取房间
        2. 如果房间不存在，抛出RoomNotFoundException
        3. 调用权限守卫函数检查可见性
        
        Args:
            room_id: 房间ID
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
            
        Returns:
            房间对象
            
        Raises:
            NotFoundException: 房间不存在或无权访问（404）
        """
        logger.info(f"开始获取房间详情: room_id={room_id}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：CRUD层不进行权限过滤，只根据ID查询
            room = await crud_room.get(db=self.db, room_id=room_id)
            if not room:
                logger.warning(f"房间不存在: room_id={room_id}")
                raise RoomNotFoundException()
            
            # ← 新增：权限校验（在业务逻辑之前）
            self._check_room_visibility(room, user_id, role)
            
            logger.info(f"成功获取房间详情: room_id={room_id}, title={room.title}")
            return room
            
        except (RoomNotFoundException, NotFoundException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"获取房间详情失败: room_id={room_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise

    async def update_room_info(
        self, 
        room_id: uuid.UUID, 
        room_update: LiveRoomUpdate, 
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> LiveRoom:
        """
        更新房间信息
        
        业务逻辑流程:
        1. 获取房间对象（包含存在性检查）
        2. 调用权限守卫函数检查写权限
        3. 检查房间是否正在直播
        4. 如果正在直播，抛出ActionForbiddenException
        5. 调用CRUD层执行更新
        
        Args:
            room_id: 房间ID
            room_update: 更新数据
            user_id: 当前用户的public_id（从JWT的user_id字段提取）
            role: 当前用户的角色
            
        Returns:
            更新后的房间对象
            
        Raises:
            RoomNotFoundException: 当房间不存在时
            PermissionDeniedException: 无权修改（403）
            ActionForbiddenException: 当房间正在直播时
        """
        logger.info(f"开始更新房间信息: room_id={room_id}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：获取房间对象（不传递权限参数，因为详情查询需要先检查可见性）
            room = await crud_room.get(db=self.db, room_id=room_id)
            if not room:
                logger.warning(f"房间不存在: room_id={room_id}")
                raise RoomNotFoundException()
            
            # ← 新增：权限校验（在业务逻辑之前）
            self._check_write_permission(room, user_id, role)

            # PR 2: 内容安全校验（房间标题/描述）
            title = room_update.title if hasattr(room_update, 'title') and room_update.title is not None else None
            description = room_update.description if hasattr(room_update, 'description') and room_update.description is not None else None
            if title or description:
                await _check_room_content_safety(self.db, title=title, description=description, user_id=user_id)

            # 执行更新
            updated_room = await crud_room.update(db=self.db, db_obj=room, obj_in=room_update)
            logger.info(f"成功更新房间信息: room_id={room_id}, title={updated_room.title}")

            # 关联分类（若在更新时指定；与创建路径一致：校验存在且启用，无效分类静默跳过）
            if room_update.category_ids is not None:
                from app.models.content_management import Category
                from sqlalchemy import select as sa_select
                cat_stmt = sa_select(Category.id).where(
                    Category.id.in_(room_update.category_ids),
                    Category.is_active == True
                )
                cat_result = await self.db.execute(cat_stmt)
                valid_cat_ids = [row[0] for row in cat_result.all()]
                invalid_ids = set(room_update.category_ids) - set(valid_cat_ids)
                if invalid_ids:
                    logger.warning(
                        f"更新房间时指定了无效/禁用的分类: room_id={room_id}, "
                        f"invalid_ids={[str(c)[:8] for c in invalid_ids]}"
                    )
                # 无条件 replace：valid 为空列表 = 清空该房间全部分类（crud 的 replace 对空列表先删后空插）
                primary = valid_cat_ids[0] if valid_cat_ids else None
                await crud_set_live_room_categories(
                    db=self.db,
                    room_id=room_id,
                    category_ids=valid_cat_ids,
                    mode='replace',
                    primary_category_id=primary
                )
                await self.db.commit()
                await self.db.refresh(updated_room)
                logger.info(f"房间分类关联成功: room_id={room_id}, categories={len(valid_cat_ids)}")

            return updated_room
            
        except (RoomNotFoundException, PermissionDeniedException, ActionForbiddenException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"更新房间信息失败: room_id={room_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise

    async def delete_room(
        self, 
        room_id: uuid.UUID, 
        user_id: uuid.UUID,
        role: str,  # ← 新增：权限参数
        force: bool = False,
    ) -> LiveRoom:
        """
        删除房间
        
        业务逻辑流程:
        1. 获取房间对象（包含存在性检查）
        2. 调用权限守卫函数检查写权限
        3. 检查房间是否正在直播
        4. 如果正在直播，抛出ActionForbiddenException
        5. 调用CRUD层执行删除
        
        Args:
            room_id: 房间ID
            user_id: 当前用户的public_id（从JWT的user_id字段提取）
            role: 当前用户的角色
            
        Returns:
            被删除的房间对象
            
        Raises:
            RoomNotFoundException: 当房间不存在时
            PermissionDeniedException: 无权删除（403）
            ActionForbiddenException: 当房间正在直播时
        """
        logger.info(f"开始删除房间: room_id={room_id}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：获取房间对象（不传递权限参数，因为详情查询需要先检查可见性）
            room = await crud_room.get(db=self.db, room_id=room_id)
            if not room:
                logger.warning(f"房间不存在: room_id={room_id}")
                raise RoomNotFoundException()
            
            # ← 新增：权限校验（在业务逻辑之前）
            self._check_write_permission(room, user_id, role)
            
            # 检查房间是否正在直播
            logger.info(f"检查房间直播状态: room_id={room_id}")
            is_live = await crud_room.is_live(db=self.db, room_id=room_id)
            if is_live and not force:
                logger.warning(f"房间正在直播，无法删除: room_id={room_id}")
                raise ActionForbiddenException("无法删除正在直播的房间")
            
            # 提前缓存 title，commit 后 ORM 属性会 expire 不可再访问
            room_title = room.title
            # 先删除所有关联数据（场次专家/品牌/专题等），再删房间，避免 IntegrityError
            await crud_room.delete_room_related(db=self.db, room_id=room_id)
            # 执行删除
            deleted_room = await crud_room.remove(db=self.db, db_obj=room)
            logger.info(f"成功删除房间: room_id={room_id}, title={room_title}")
            return deleted_room
            
        except (RoomNotFoundException, PermissionDeniedException, ActionForbiddenException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"删除房间失败: room_id={room_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise

    async def get_sub_venue_list(
        self, 
        parent_room_id: uuid.UUID, 
        page: int, 
        size: int,
        user_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取分会场列表（支持匿名访问）
        
        业务逻辑流程:
        1. 检查主会场是否存在并验证可见性
        2. 计算skip值
        3. 调用CRUD层获取分会场列表
        
        Args:
            parent_room_id: 主会场ID
            page: 页码
            size: 每页大小
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
            
        Returns:
            分会场列表和总数的元组
            
        Raises:
            NotFoundException: 当主会场不存在或无权访问时（404）
        """
        logger.info(f"开始获取分会场列表: parent_room_id={parent_room_id}, page={page}, size={size}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：检查主会场是否存在并验证可见性
            await self.get_room_details(parent_room_id, user_id=user_id, role=role)
            
            # 计算skip值
            skip = (page - 1) * size
            
            # 获取分会场列表和总数（传递 role 参数以支持 is_private 过滤）
            sub_venues, total = await crud_room.get_sub_venues_with_live_status(
                db=self.db, parent_room_id=parent_room_id, skip=skip, limit=size, 
                user_id=user_id, role=role  # ← 新增：传递 role 参数
            )
            
            logger.info(f"成功获取分会场列表: parent_room_id={parent_room_id}, 返回{len(sub_venues)}条记录, 总数={total}")
            return sub_venues, total
            
        except (RoomNotFoundException, NotFoundException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"获取分会场列表失败: parent_room_id={parent_room_id}, page={page}, size={size}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise

    async def upload_room_cover(
        self, 
        room_id: uuid.UUID, 
        file: UploadFile,
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> LiveRoom:
        """
        为指定房间上传封面图片
        
        Args:
            room_id: 房间ID
            file: 上传的文件对象
            user_id: 当前用户的public_id（从JWT的user_id字段提取）
            role: 当前用户的角色
            
        Returns:
            更新后的LiveRoom对象
            
        Raises:
            RoomNotFoundException: 房间不存在（404）
            PermissionDeniedException: 用户无权修改此房间（403）
        """
        logger.info(f"开始上传房间封面: room_id={room_id}, user_id={user_id}, role={role}")
        
        try:
            # ← 修改：验证房间存在性（不传递权限参数，因为详情查询需要先检查可见性）
            room = await crud_room.get(db=self.db, room_id=room_id)
            if not room:
                logger.warning(f"房间不存在: room_id={room_id}")
                raise RoomNotFoundException()
            
            # ← 新增：权限校验（在业务逻辑之前）
            self._check_write_permission(room, user_id, role)
            
            # 2. 如果房间已有封面，删除旧文件
            if room.cover_url:
                logger.info(f"删除旧封面文件: cover_url={room.cover_url}")
                FileHandler.delete_old_cover(room.cover_url)
            
            # 3. 保存新文件
            cover_url = await FileHandler.save_cover_file(file=file, room_id=room_id)
            logger.info(f"新封面文件保存成功: cover_url={cover_url}")
            
            # 4. 更新数据库 cover_url
            updated_room = await crud_room.update_cover_url(
                db=self.db, 
                room_id=room_id, 
                cover_url=cover_url
            )
            
            if not updated_room:
                logger.error(f"更新封面URL失败: room_id={room_id}")
                raise Exception("更新封面URL失败")
            
            logger.info(f"封面上传成功: room_id={room_id}, cover_url={cover_url}")
            
            # 5. 返回更新后的房间对象
            return updated_room
            
        except (RoomNotFoundException, PermissionDeniedException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(f"上传房间封面失败: room_id={room_id}, user_id={user_id}, role={role}, error={str(e)}", exc_info=True)
            raise

    async def search_rooms(
        self, 
        public_id: Optional[uuid.UUID] = None,  # ← 修改：改为Optional（支持匿名）
        q: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        sort: Optional[str] = None,
        role: Optional[str] = None,  # ← 新增：权限参数
        status: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        搜索直播间（业务逻辑层，支持匿名访问）
        
        职责：
        1. 构建搜索条件
        2. 调用 CRUD 层查询（CRUD层会根据权限进行SQL过滤）
        
        参数：
        - public_id: 当前用户公开标识（匿名时为None）
        - q: 搜索关键词（ID 或标题）
        - page/size: 分页参数
        - sort: 排序字段（可选），格式为 field:direction
        - role: 当前用户的角色（匿名时为None）
        
        返回：
        - {"total": int, "page": int, "size": int, "items": [Room]}
        """
        # 1. 构建搜索条件
        search_filters = {}
        
        if q:
            # 判断是否为 UUID 格式（36 个字符，包含 '-'）
            uuid_pattern = re.compile(
                r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                r'[0-9a-f]{4}-[0-9a-f]{12}$',
                re.IGNORECASE
            )
            
            if uuid_pattern.match(q):
                # UUID 精确匹配
                search_filters['id_or_title'] = ('id', q)
                logger.info(f"搜索直播间（UUID）：q={q}")
            else:
                # 标题模糊匹配
                search_filters['id_or_title'] = ('title', f'%{q}%')
                logger.info(f"搜索直播间（标题）：q={q}")
        
        # 2. ← 修改：调用 CRUD 层查询（传递权限参数）
        result = await crud_room.list_with_search(
            self.db, 
            filters=search_filters,
            page=page,
            size=size,
            sort=sort,
            user_id=public_id,  # ← 新增：传递权限参数
            role=role,          # ← 新增：传递权限参数
            status=status,
            created_after=created_after,
            created_before=created_before,
        )
        
        logger.info(
            f"搜索直播间完成：q={q}, user_id={public_id}, role={role}, total={result['total']}, "
            f"found={len(result['items'])}"
        )
        
        return result


async def _check_room_content_safety(
    db: AsyncSession,
    title: Optional[str] = None,
    description: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
) -> None:
    """PR 2: 房间标题/描述内容安全校验"""
    try:
        from app.content_safety.service import check_scene_fields, assert_content_safe_or_raise
        from app.core.config import settings
        if not getattr(settings, "CONTENT_SAFETY_ENABLED", True):
            return
        field_values = {}
        if title:
            field_values["title"] = title
        if description:
            field_values["description"] = description
        if not field_values:
            return
        result = await check_scene_fields(
            db=db,
            scene="room_title",
            field_values=field_values,
            user_id=user_id,
            resource_type="room",
        )
        assert_content_safe_or_raise(result)
    except Exception as e:
        from app.content_safety.exceptions import ContentSafetyBlockedException
        if isinstance(e, ContentSafetyBlockedException):
            raise
        logger.warning("房间内容安全校验异常，降级放行: %s", e)
