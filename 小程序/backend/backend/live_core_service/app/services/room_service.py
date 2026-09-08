"""
LiveCore Service - Room Service

This module contains the business logic layer for LiveRoom operations,
implementing all business rules and validation logic.
"""

import uuid
import logging
import re
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.crud import room as crud_room
from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate
from app.models.live_core import LiveRoom
from app.core.file_handler import FileHandler
from app.exceptions import (
    RoomNotFoundException,
    ActionForbiddenException,
    ParentRoomNotFoundException,
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
)
from app.content_safety.schemas import ContentSafetyItem
from app.content_safety.service import check_content_safety, check_scene_fields

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
        房间读可见性（文档 18）：is_private=true 为不公开（unlisted）。
        持有 room_id 即可读；发现层过滤由列表/搜索 SQL 负责。
        房间不存在仍由上层抛 404。
        """
        if room.is_private and role in ['ADMIN', 'SUPERADMIN'] and user_id and room.user_id != user_id:
            logger.info(
                f"Admin查看不公开房间: admin={user_id}, role={role}, "
                f"room_id={room.id}, owner={room.user_id}"
            )
        return

    def _check_write_permission(
        self,
        room: LiveRoom,
        user_id: uuid.UUID,
        role: str
    ) -> None:
        """
        写操作权限校验（修改/删除）
        
        Args:
            room: 直播间对象
            user_id: 当前用户的public_id
            role: 当前用户的角色
            
        Raises:
            PermissionDeniedException: 无权修改（403）
        """
        # 管理员：上帝视角通过
        if role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源创建者：通过
        if room.user_id == user_id:
            return
        
        # 其他用户：拒绝（返回403，因为已登录）
        raise PermissionDeniedException(
            "You don't have permission to modify this room"
        )

    async def create_new_room(
        self, 
        room_in: LiveRoomCreate, 
        user_id: uuid.UUID,
        role: str,  # ← 权限参数
        can_stream: bool = True,
    ) -> LiveRoom:
        """
        创建新的直播房间
        
        业务逻辑流程:
        0. 开播门禁：can_stream 为 false 时拒绝（运营禁止开播）；ADMIN 可旁路
        1. 如果指定了parent_room_id，检查父房间是否存在
        2. 如果父房间不存在，抛出ParentRoomNotFoundException
        3. 调用CRUD层创建新房间
        
        Args:
            room_in: 房间创建请求数据
            user_id: 用户ID（从JWT的user_id字段提取）
            role: 用户角色（从JWT的role字段提取）
            can_stream: 是否可开播（JWT 缺省视为 true；false=被禁止）
            
        Returns:
            创建的房间对象
            
        Raises:
            PermissionDeniedException: 开播功能已被禁用
            ParentRoomNotFoundException: 当指定的父房间不存在时
        """
        logger.info(f"开始创建新房间: user_id={user_id}, title={room_in.title}")

        from app.core.config import settings

        role_upper = (role or "").upper()
        admin_bypass = (
            settings.ADMIN_STREAM_BYPASS
            and role_upper in ("ADMIN", "SUPERADMIN")
        )
        if not admin_bypass and not can_stream:
            logger.warning(
                "创建房间被拒绝：开播功能已被禁用 user_id=%s role=%s",
                user_id,
                role_upper,
            )
            raise PermissionDeniedException("开播功能已被禁用")
        
        try:
            # 如果指定了父房间ID，检查父房间是否存在
            if room_in.parent_room_id:
                logger.info(f"检查父房间是否存在: parent_room_id={room_in.parent_room_id}")
                parent_room = await crud_room.get(db=self.db, room_id=room_in.parent_room_id)
                if not parent_room:
                    logger.warning(f"父房间不存在: parent_room_id={room_in.parent_room_id}")
                    raise ParentRoomNotFoundException()
                logger.info(f"父房间验证通过: parent_room_id={room_in.parent_room_id}")

            await check_scene_fields(
                self.db,
                scene="room_title",
                field_values={"title": room_in.title},
                resource_type="live_room",
                user_id=user_id,
            )
            if room_in.description:
                await check_scene_fields(
                    self.db,
                    scene="room_description",
                    field_values={"description": room_in.description},
                    resource_type="live_room",
                    user_id=user_id,
                )
            
            # 创建新房间
            room = await crud_room.create(db=self.db, obj_in=room_in, user_id=user_id)
            logger.info(f"成功创建新房间: room_id={room.id}, title={room.title}")
            return room
            
        except ParentRoomNotFoundException:
            # 重新抛出业务异常，不记录额外日志
            raise
        except PermissionDeniedException:
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
            # - owner_only=True：仅返回当前用户创建的房间
            # - 其他情况：沿用通用的 Public+Own / Admin All / Anonymous Public 规则
            if owner_only and user_id is not None:
                rooms, total = await crud_room.get_multi_and_total_by_owner(
                    db=self.db,
                    skip=skip,
                    limit=size,
                    owner_id=user_id,
                )
            else:
                # ← 调用通用权限过滤版本（Repository 层根据 role/user_id 进行 SQL 过滤）
                rooms, total = await crud_room.get_multi_and_total(
                    db=self.db,
                    skip=skip,
                    limit=size,
                    user_id=user_id,
                    role=role,
                )
            
            logger.info(f"成功获取房间列表: 返回{len(rooms)}条记录, 总数={total}")
            return rooms, total
            
        except Exception as e:
            logger.error(f"获取房间列表失败: page={page}, size={size}, user_id={user_id}, error={str(e)}", exc_info=True)
            raise

    async def list_admin_rooms(
        self,
        *,
        page: int = 1,
        size: int = 20,
        q: Optional[str] = None,
        owner_user_id: Optional[uuid.UUID] = None,
        is_private: Optional[bool] = None,
    ) -> Tuple[List[LiveRoom], int]:
        """管理端全站房间列表（含私密）。鉴权由 API 层完成。"""
        logger.info(
            "Admin房间列表: page=%s size=%s q=%s owner=%s is_private=%s",
            page, size, q, owner_user_id, is_private,
        )
        skip = (page - 1) * size
        rooms, total = await crud_room.list_admin_rooms(
            db=self.db,
            skip=skip,
            limit=size,
            q=q,
            owner_user_id=owner_user_id,
            is_private=is_private,
        )
        logger.info("Admin房间列表完成: 返回%s条, 总数=%s", len(rooms), total)
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

    async def ensure_test_room(
        self,
        room_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        title_suffix: Optional[str] = None,
    ) -> Tuple[LiveRoom, LiveRoom, bool]:
        """
        为正式间确保一间关联测播间（文档 18，幂等）。

        Returns:
            (source_room, test_room, created)
        """
        suffix = (title_suffix or "连接测试").strip() or "连接测试"
        if not suffix.startswith("·") and not suffix.startswith("-"):
            title_tail = f"·{suffix}"
        else:
            title_tail = suffix

        source = await crud_room.get(db=self.db, room_id=room_id)
        if not source:
            raise RoomNotFoundException()

        self._check_write_permission(source, user_id, role)

        if source.source_room_id is not None:
            raise InvalidParameterException("请对正式间调用测试连接接口")

        existing = await crud_room.get_by_source_room_id(db=self.db, source_room_id=source.id)
        if existing:
            logger.info(
                "复用测播间: source_room_id=%s test_room_id=%s",
                source.id,
                existing.id,
            )
            return source, existing, False

        # create() 会 commit；生产会话默认 expire_on_commit=True，
        # 提交后 source 属性过期，同步访问会触发 MissingGreenlet。先取出标量。
        source_id = source.id
        source_user_id = source.user_id
        source_title = source.title
        source_description = source.description
        source_cover_url = source.cover_url
        source_record_by_default = source.record_by_default
        source_category_id = source.category_id

        test_title = f"{source_title}{title_tail}"
        if len(test_title) > 100:
            # 保留后缀，截断正式标题
            max_base = 100 - len(title_tail)
            test_title = f"{source_title[:max(0, max_base)]}{title_tail}"

        await check_scene_fields(
            self.db,
            scene="room_title",
            field_values={"title": test_title},
            resource_type="live_room",
            user_id=user_id,
        )

        test_room = await crud_room.create(
            db=self.db,
            obj_in={
                "title": test_title,
                "description": source_description,
                "cover_url": source_cover_url,
                "is_private": True,
                "record_by_default": source_record_by_default,
                "category_id": source_category_id,
                "source_room_id": source_id,
            },
            user_id=source_user_id,
        )
        await self.db.refresh(source)
        logger.info(
            "创建测播间: source_room_id=%s test_room_id=%s",
            source_id,
            test_room.id,
        )
        return source, test_room, True

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

            update_data = room_update.model_dump(exclude_unset=True)
            if update_data.get("title"):
                await check_scene_fields(
                    self.db,
                    scene="room_title",
                    field_values={"title": update_data["title"]},
                    resource_type="live_room",
                    resource_id=room_id,
                    user_id=user_id,
                )
            if update_data.get("description"):
                await check_scene_fields(
                    self.db,
                    scene="room_description",
                    field_values={"description": update_data["description"]},
                    resource_type="live_room",
                    resource_id=room_id,
                    user_id=user_id,
                )
            
            # 检查房间是否正在直播
            #logger.info(f"检查房间直播状态: room_id={room_id}")
            #is_live = await crud_room.is_live(db=self.db, room_id=room_id)
            #if is_live:
            #    logger.warning(f"房间正在直播，无法修改: room_id={room_id}")
            #    raise ActionForbiddenException("无法修改正在直播的房间")
            
            # 执行更新
            updated_room = await crud_room.update(db=self.db, db_obj=room, obj_in=room_update)
            logger.info(f"成功更新房间信息: room_id={room_id}, title={updated_room.title}")
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
        role: str  # ← 新增：权限参数
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
            #is_live = await crud_room.is_live(db=self.db, room_id=room_id)
            #if is_live:
            #    logger.warning(f"房间正在直播，无法删除: room_id={room_id}")
            #    raise ActionForbiddenException("无法删除正在直播的房间")
            
            # 先删除所有关联数据（场次专家/品牌/专题等），再删房间，避免 IntegrityError
            await crud_room.delete_room_related(db=self.db, room_id=room_id)
            # 执行删除
            deleted_room = await crud_room.remove(db=self.db, db_obj=room)
            logger.info(f"成功删除房间: room_id={room_id}, title={deleted_room.title}")
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
        owner_only: bool = False,
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
            owner_only=owner_only,
        )
        
        logger.info(
            f"搜索直播间完成：q={q}, user_id={public_id}, role={role}, total={result['total']}, "
            f"found={len(result['items'])}"
        )
        
        return result
