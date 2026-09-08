"""
首页与搜索模块的Service层

本模块负责：
- Phase1: 焦点图业务逻辑
- Phase2: 首页API业务逻辑（Host选择、热度计算、状态判断）
- Phase3: 搜索API业务逻辑（高亮、metadata填充）
"""
import uuid
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from typing import TYPE_CHECKING
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from fastapi import UploadFile

from app.crud import homepage_search as crud
from app.schemas.homepage_search import (
    FeaturedContentCreate,
    FeaturedContentUpdate,
    FeaturedContentItem,
    LiveStatusEnum,
    HomepageHostInfo,
    HomepageStatusData,
    HomepageRoomItem,
    SearchResultType,
    SearchResultItem
)
from app.exceptions import (
    PermissionDeniedException,
    NotFoundException,
    InvalidParameterException
)
from app.core.permissions import check_admin_permission
from app.services.user_profile_client import fetch_user_profiles
from app.services.room_card_service import get_room_card_map
import logging

logger = logging.getLogger(__name__)


class HomepageSearchService:
    """首页与搜索模块Service层"""

    # ==================== 目标资源验证 ====================
    
    async def _validate_target_resource(
        self,
        db: AsyncSession,
        target_type: str,
        target_id: uuid.UUID
    ) -> None:
        """
        验证目标资源是否存在
        
        Args:
            db: 数据库会话
            target_type: 目标类型（room/session/topic/brand/external）
            target_id: 目标资源ID
            
        Raises:
            InvalidParameterException: 目标资源不存在或类型不支持
        """
        if target_type == "room":
            from app.models.live_core import LiveRoom
            stmt = select(LiveRoom).where(LiveRoom.id == target_id)
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                raise InvalidParameterException(f"直播间不存在: {target_id}")
        
        elif target_type == "session":
            from app.models.live_core import LiveSession
            stmt = select(LiveSession).where(LiveSession.id == target_id)
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                raise InvalidParameterException(f"场次不存在: {target_id}")
        
        elif target_type == "topic":
            from app.models.topic import Topic
            stmt = select(Topic).where(Topic.id == target_id)
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                raise InvalidParameterException(f"专题不存在: {target_id}")
        
        elif target_type == "brand":
            from app.models.brand import Brand
            stmt = select(Brand).where(Brand.id == target_id, Brand.is_active == True)
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                raise InvalidParameterException(f"品牌不存在: {target_id}")
        
        elif target_type == "external":
            # 外部链接不需要验证target_id
            pass
        
        else:
            raise InvalidParameterException(f"不支持的目标类型: {target_type}")
    
    # ==================== Featured Content Service方法 ====================
    
    async def get_featured_content_list(
        self,
        db: AsyncSession
    ) -> dict:
        """
        获取焦点图列表（公开接口）
        
        Args:
            db: 数据库会话
            
        Returns:
            包含焦点图列表的响应字典
        """
        items = await crud.get_featured_content_list(db, include_inactive=False)
        content_items = [FeaturedContentItem.model_validate(item).model_dump(mode='json') for item in items]
        
        logger.info(f"查询焦点图列表（公开），返回{len(content_items)}条")
        
        return {
            "code": 200,
            "message": "success",
            "data": content_items,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_featured_content_list_admin(
        self,
        db: AsyncSession,
        current_user_id: uuid.UUID,
        role: str
    ) -> dict:
        """
        获取焦点图列表（管理员接口，显示所有状态）
        
        Args:
            db: 数据库会话
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            包含焦点图列表的响应字典
            
        Raises:
            PermissionDeniedException: 权限不足
        """
        # 权限检查
        check_admin_permission(role)
        
        # 调用CRUD层（包含未启用的）
        items = await crud.get_featured_content_list(db, include_inactive=True, include_scheduled=True)
        content_items = [FeaturedContentItem.model_validate(item).model_dump(mode='json') for item in items]
        
        logger.info(f"查询焦点图列表（管理员），返回{len(content_items)}条，管理员={str(current_user_id)[:8]}")
        
        return {
            "code": 200,
            "message": "success",
            "data": content_items,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_featured_content_list_admin_paginated(
        self,
        db: AsyncSession,
        page: int,
        size: int,
        current_user_id: uuid.UUID,
        role: str,
        q: Optional[str] = None,
        search_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> dict:
        """
        获取焦点图列表（管理员，分页）。
        返回统一分页格式 data: { total, page, size, items }。
        支持 q、search_type 列表搜索（与前端列表筛选与搜索规范对齐）。
        支持 is_active 按启用状态筛选（None=全部，True=已上线，False=已下线）。
        支持 status 按时间状态筛选（active=正在展示，upcoming=待上线，expired=已过期，inactive=已下线）。
        每条记录附加动态 status 字段：inactive=已下线（含到期自动下线），upcoming=待上线，expired=已过期，active=正在展示。
        """
        check_admin_permission(role)

        items, total = await crud.get_featured_content_list_paginated(
            db, page=page, size=size, q=q, search_type=search_type,
            is_active=is_active, status=status
        )
        now = datetime.now(timezone.utc)
        content_items = []
        for item in items:
            content_item = FeaturedContentItem.model_validate(item).model_dump(mode='json')
            content_item["status"] = self._compute_featured_status(item, now)
            content_items.append(content_item)

        logger.info(
            f"查询焦点图列表（管理员分页），page={page}, size={size}, total={total}, "
            f"q={q}, search_type={search_type}, is_active={is_active}, status={status}, "
            f"管理员={str(current_user_id)[:8]}"
        )

        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "size": size,
                "items": content_items
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def _compute_featured_status(content, now: datetime) -> str:
        """
        计算焦点图动态状态。

        Args:
            content: FeaturedContent ORM 对象
            now: 当前时间（aware UTC）

        Returns:
            inactive=已下线（含手动下线与到期自动下线），upcoming=待上线，
            expired=已过期（尚未被惰性下线翻转的过期记录），active=正在展示
        """
        if not content.is_active:
            return "inactive"
        if content.start_at and content.start_at > now:
            return "upcoming"
        if content.end_at and content.end_at < now:
            return "expired"
        return "active"
    
    async def create_featured_content(
        self,
        db: AsyncSession,
        content_data: FeaturedContentCreate,
        current_user_id: uuid.UUID,
        role: str
    ) -> dict:
        """
        创建焦点图（管理员功能）
        
        Args:
            db: 数据库会话
            content_data: 焦点图创建数据
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            包含创建的焦点图的响应字典
            
        Raises:
            PermissionDeniedException: 权限不足
            InvalidParameterException: 目标资源不存在
        """
        # 权限检查
        check_admin_permission(role)
        
        # 目标资源验证（如果提供了target_id）
        if content_data.target_id and content_data.target_type:
            await self._validate_target_resource(db, content_data.target_type, content_data.target_id)
        
        # 时间区间校验：下线时间不得早于上线时间
        if content_data.start_at and content_data.end_at and content_data.end_at < content_data.start_at:
            raise InvalidParameterException("下线时间不能早于上线时间")
        
        # 调用CRUD层创建
        content = await crud.create_featured_content(db, content_data)
        
        # 序列化并返回
        content_item = FeaturedContentItem.model_validate(content).model_dump(mode='json')
        
        logger.info(f"创建焦点图: {str(content.id)[:8]}, 标题={content.title}, 管理员={str(current_user_id)[:8]}")
        
        return {
            "code": 200,
            "message": "success",
            "data": content_item,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_featured_content_detail_admin(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str
    ) -> dict:
        """
        获取焦点图详情（管理员功能）

        Args:
            db: 数据库会话
            content_id: 焦点图ID
            current_user_id: 当前用户ID
            role: 用户角色

        Returns:
            包含单条焦点图的响应字典

        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 焦点图不存在
        """
        check_admin_permission(role)

        content = await crud.get_featured_content_by_id(db, content_id)
        if not content:
            raise NotFoundException(f"焦点图不存在: {content_id}")

        content_item = FeaturedContentItem.model_validate(content).model_dump(mode='json')
        logger.info(f"获取焦点图详情: {str(content_id)[:8]}, 管理员={str(current_user_id)[:8]}")

        return {
            "code": 200,
            "message": "success",
            "data": content_item,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def update_featured_content(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        content_data: FeaturedContentUpdate,
        current_user_id: uuid.UUID,
        role: str
    ) -> dict:
        """
        更新焦点图（管理员功能）
        
        Args:
            db: 数据库会话
            content_id: 焦点图ID
            content_data: 焦点图更新数据
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            包含更新后焦点图的响应字典
            
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 焦点图不存在
            InvalidParameterException: 目标资源不存在
        """
        # 权限检查
        check_admin_permission(role)
        
        # 目标资源验证（如果更新了target_id和target_type）
        update_dict = content_data.model_dump(exclude_unset=True)
        if "target_id" in update_dict and "target_type" in update_dict:
            await self._validate_target_resource(db, update_dict["target_type"], update_dict["target_id"])
        
        # 时间区间校验：部分更新时与现有值合并后校验，下线时间不得早于上线时间
        if "start_at" in update_dict or "end_at" in update_dict:
            existing = await crud.get_featured_content_by_id(db, content_id)
            if existing:
                final_start = update_dict.get("start_at", existing.start_at)
                final_end = update_dict.get("end_at", existing.end_at)
                if final_start and final_end and final_end < final_start:
                    raise InvalidParameterException("下线时间不能早于上线时间")
        
        # 调用CRUD层更新
        content = await crud.update_featured_content(db, content_id, content_data)
        
        # 404检查
        if not content:
            raise NotFoundException(f"焦点图不存在: {content_id}")
        
        # 序列化并返回
        content_item = FeaturedContentItem.model_validate(content).model_dump(mode='json')
        
        logger.info(f"更新焦点图: {str(content_id)[:8]}, 更新字段={list(update_dict.keys())}, 管理员={str(current_user_id)[:8]}")
        
        return {
            "code": 200,
            "message": "success",
            "data": content_item,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def delete_featured_content(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str
    ) -> dict:
        """
        删除焦点图（物理删除，管理员功能）

        物理删除数据库记录，并清理该焦点图本地媒体目录（若 image_url 为 /media/ 路径）。

        Args:
            db: 数据库会话
            content_id: 焦点图ID
            current_user_id: 当前用户ID
            role: 用户角色

        Returns:
            包含删除状态的响应字典

        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 焦点图不存在
        """
        # 权限检查
        check_admin_permission(role)

        # 物理删除前先读取原记录（用于媒体文件清理）
        content = await crud.get_featured_content_by_id(db, content_id)
        if not content:
            raise NotFoundException(f"焦点图不存在: {content_id}")

        # 调用CRUD层删除（物理删除）
        success = await crud.delete_featured_content(db, content_id, soft_delete=False)

        # 清理本地媒体目录（容错：失败不影响删除主流程）
        if success and content.image_url and content.image_url.startswith("/media/"):
            try:
                from app.core.file_handler import FileHandler
                FileHandler.delete_featured_content_media(content_id, content.image_url)
            except Exception as e:
                logger.warning(
                    f"删除焦点图媒体文件失败: content_id={str(content_id)[:8]}, error={str(e)}"
                )

        # 返回删除状态
        logger.warning(f"删除焦点图: {str(content_id)[:8]}, 管理员={str(current_user_id)[:8]}")
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "id": str(content_id),  # UUID转换为字符串
                "status": "deleted",
                "deleted_at": datetime.utcnow().isoformat()  # datetime转换为ISO字符串
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def upload_featured_content_image(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        file: "UploadFile",
        current_user_id: uuid.UUID,
        role: str
    ) -> dict:
        """
        上传焦点图图片（管理员功能）。覆盖本地存储的旧图（若存在），更新 image_url。

        Args:
            db: 数据库会话
            content_id: 焦点图ID
            file: 上传的文件
            current_user_id: 当前用户ID
            role: 用户角色

        Returns:
            包含更新后焦点图的响应字典

        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 焦点图不存在
        """
        from app.core.file_handler import FileHandler

        check_admin_permission(role)

        content = await crud.get_featured_content_by_id(db, content_id)
        if not content:
            raise NotFoundException(f"焦点图不存在: {content_id}")

        # 若当前为本地图片，先删除旧文件
        if content.image_url and content.image_url.startswith("/media/"):
            FileHandler.delete_old_featured_content_image(content.image_url)

        url_path = await FileHandler.save_featured_content_image(file, content_id)

        update_data = FeaturedContentUpdate(image_url=url_path)
        updated = await crud.update_featured_content(db, content_id, update_data)
        if not updated:
            raise NotFoundException(f"焦点图不存在: {content_id}")

        content_item = FeaturedContentItem.model_validate(updated).model_dump(mode='json')
        logger.info(
            f"上传焦点图图片: content_id={str(content_id)[:8]}, path={url_path}, "
            f"管理员={str(current_user_id)[:8]}"
        )
        return {
            "code": 200,
            "message": "success",
            "data": content_item,
            "timestamp": datetime.utcnow().isoformat()
        }

    # ==================== Homepage API Service方法 (Phase2) ====================
    
    def _select_host(
        self,
        room_data: Dict,
        user_profile_map: Optional[Dict[str, Dict[str, Optional[str]]]] = None,
    ) -> Optional[HomepageHostInfo]:
        """
        Host选择逻辑（私有方法）
        
        规则：
        1. 有场次关联专家时，使用关联顺序中的第一个专家
        2. 无关联专家时，fallback 到房间创建者公开资料
        
        Args:
            room_data: CRUD层返回的原始房间数据
            user_profile_map: 批量获取的用户公开资料映射，key 为用户 public_id 字符串
            
        Returns:
            HomepageHostInfo对象
        """
        if room_data.get('expert_id'):
            return HomepageHostInfo(
                expert_id=room_data['expert_id'],
                user_id=None,
                name=room_data['expert_name'],
                title=room_data.get('expert_title'),
                hospital=room_data.get('expert_hospital'),
                avatar_url=room_data.get('expert_avatar')
            )
        
        owner_id = room_data.get('room_owner_user_id')
        if not owner_id:
            return HomepageHostInfo(
                expert_id=None,
                user_id=None,
                name="用户",
                title=None,
                hospital=None,
                avatar_url=None,
            )

        profile = (user_profile_map or {}).get(str(owner_id)) or {}
        name = profile.get('nickname') or profile.get('username') or "用户"
        return HomepageHostInfo(
            expert_id=None,
            user_id=owner_id,
            name=name,
            title=None,
            hospital=None,
            avatar_url=profile.get('avatar_url'),
        )
    
    def _determine_live_status(self, session_status: Optional[str]) -> LiveStatusEnum:
        """
        确定直播状态（私有方法）
        
        映射关系：
        - session_status == 'live' → LiveStatusEnum.LIVE
        - session_status == 'scheduled' → LiveStatusEnum.SCHEDULED
        - session_status == 'ready' → LiveStatusEnum.REPLAY（回放）
        - 其他（finished/processing/error/ended/archived/None）→ LiveStatusEnum.REPLAY（默认）
        
        Args:
            session_status: 场次状态
            
        Returns:
            LiveStatusEnum枚举值
        """
        if session_status == 'live':
            return LiveStatusEnum.LIVE
        elif session_status == 'scheduled':
            return LiveStatusEnum.SCHEDULED
        elif session_status == 'ready':
            return LiveStatusEnum.REPLAY
        else:
            return LiveStatusEnum.REPLAY
    
    def _build_status_data(
        self,
        live_status: LiveStatusEnum,
        room_data: Dict
    ) -> HomepageStatusData:
        """
        构造状态数据（私有方法）
        
        规则：
        - live: 填充viewer_count（peak_viewer_count）
        - scheduled: 填充start_time（session_start_time）
        - replay: 填充duration_seconds和play_count（total_play_count）
        
        Args:
            live_status: 直播状态
            room_data: CRUD层返回的原始房间数据
            
        Returns:
            HomepageStatusData对象
        """
        if live_status == LiveStatusEnum.LIVE:
            return HomepageStatusData(
                viewer_count=room_data.get('peak_viewer_count'),
                start_time=None,
                duration_seconds=None,
                play_count=None
            )
        elif live_status == LiveStatusEnum.SCHEDULED:
            return HomepageStatusData(
                viewer_count=None,
                start_time=room_data.get('session_start_time'),
                duration_seconds=None,
                play_count=None
            )
        else:  # REPLAY
            return HomepageStatusData(
                viewer_count=None,
                start_time=None,
                duration_seconds=room_data.get('duration_seconds'),
                play_count=room_data.get('total_play_count')
            )
    
    def _calculate_heat(self, room_data: Dict) -> Optional[int]:
        """
        计算热度值（私有方法）
        
        公式（简化版）：
        heat = (
            peak_viewer_count * 10 +
            total_viewer_count * 1 +
            total_message_count * 5 +
            total_play_count * 2
        )
        
        注意：
        - 如果所有统计数据都为None，返回None
        - 如果部分数据为None，视为0
        
        Args:
            room_data: CRUD层返回的原始房间数据
            
        Returns:
            热度值或None
        """
        peak_viewer = room_data.get('peak_viewer_count') or 0
        total_viewer = room_data.get('total_viewer_count') or 0
        total_message = room_data.get('total_message_count') or 0
        total_play = room_data.get('total_play_count') or 0
        
        # 如果所有数据都是0（原始数据都是None），返回None
        if peak_viewer == 0 and total_viewer == 0 and total_message == 0 and total_play == 0:
            return None
        
        heat = (
            peak_viewer * 10 +
            total_viewer * 1 +
            total_message * 5 +
            total_play * 2
        )
        
        return heat
    
    async def get_homepage_rooms(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        sort: str = "heat:desc",
        category_id: Optional[uuid.UUID] = None
    ) -> dict:
        """
        获取首页直播间列表（公开接口）
        
        处理所有业务逻辑：
        - Host选择（场次专家优先）
        - 热度计算
        - live_status判断
        - status_data构造
        
        Args:
            db: 数据库会话
            page: 页码
            size: 每页数量
            sort: 排序规则
            category_id: 分类ID筛选
            
        Returns:
            包含分页数据的响应字典
        """
        logger.info(f"获取首页直播间列表: page={page}, size={size}, sort={sort}, category_id={category_id}")
        
        # 调用CRUD层获取原始数据
        rooms_raw, total = await crud.get_homepage_rooms_with_details(
            db, page, size, category_id, sort
        )

        owner_ids = [
            room_data['room_owner_user_id']
            for room_data in rooms_raw
            if not room_data.get('expert_id') and room_data.get('room_owner_user_id')
        ]
        user_profile_map: Dict[str, Dict[str, Optional[str]]] = {}
        if owner_ids:
            try:
                user_profile_map = await fetch_user_profiles(owner_ids)
            except Exception as e:
                logger.warning(f"首页创建者资料批量获取失败，使用降级展示: {e}")
                user_profile_map = {}
        
        # 遍历每个房间，应用业务逻辑
        room_items = []
        for room_data in rooms_raw:
            # Host选择
            host = self._select_host(room_data, user_profile_map)
            
            # live_status判断
            live_status = self._determine_live_status(room_data.get('session_status'))
            
            # status_data构造
            status_data = self._build_status_data(live_status, room_data)
            
            # 热度计算
            heat = self._calculate_heat(room_data)
            
            # 构造HomepageRoomItem
            room_item = HomepageRoomItem(
                id=room_data['room_id'],
                title=room_data['room_title'],
                cover_url=room_data['room_cover_url'],
                summary=room_data['room_summary'],
                live_status=live_status,
                host=host,
                status_data=status_data,
                heat=heat
            )
            room_items.append(room_item)
        
        # 如果sort='heat:desc'，需要在Service层按heat字段降序排序
        if sort == 'heat:desc':
            room_items.sort(key=lambda x: x.heat if x.heat is not None else 0, reverse=True)
        
        logger.info(f"获取首页直播间列表成功: 返回{len(room_items)}条")
        
        # 返回响应
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "size": size,
                "items": [item.model_dump(mode='json') for item in room_items]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ==================== Search API Service方法 (Phase3) ====================
    
    def _generate_highlight(self, text: str, keyword: str) -> str:
        """
        生成高亮文本（私有方法）
        
        将匹配的关键词用<em>标签包裹
        
        Args:
            text: 原始文本
            keyword: 搜索关键词
            
        Returns:
            高亮后的文本
        """
        if not text or not keyword:
            return text or ""
        
        # 不区分大小写的替换
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        highlighted = pattern.sub(lambda m: f"<em>{m.group()}</em>", text)
        
        return highlighted
    
    def _fill_metadata(
        self,
        result: Dict,
        room_card_map: Optional[Dict[Any, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        根据资源类型填充metadata（私有方法）

        - room: 使用 room_card_map（get_room_card_map 批量聚合）填充主展示人/状态，
                无关联专家时回退创建者（与首页/三列表同一套规则）
        - expert: 使用CRUD层返回的metadata_json
        - topic: 返回空字典{}（避免额外查询）
        - brand: 返回空字典{}

        Args:
            result: CRUD层返回的搜索结果
            room_card_map: room 卡片聚合 map（key=room_id），由调用方批量获取后传入

        Returns:
            metadata字典
        """
        result_type = result['type']

        if result_type == 'room':
            metadata_json = result.get('metadata_json') or {}
            # room_card_map 的 key 已归一化为字符串（见 search_resources），此处统一 str() 匹配
            room_id = metadata_json.get('room_id')
            card = (room_card_map or {}).get(str(room_id)) if room_id is not None else {}
            metadata = {}
            if card.get('room_live_status') is not None:
                metadata['status'] = card['room_live_status']
            for field in ('expert_name', 'expert_avatar', 'expert_title', 'expert_hospital'):
                if card.get(field) is not None:
                    metadata[field] = card[field]
            return metadata

        elif result_type == 'expert':
            # 使用CRUD层返回的metadata_json
            return result.get('metadata_json') or {}

        elif result_type == 'topic':
            # MVP阶段：返回简化的metadata
            return {}

        elif result_type == 'brand':
            return {}

        return {}
    
    async def search_resources(
        self,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        size: int = 10,
        resource_types: Optional[List[str]] = None,
        category_id: Optional[uuid.UUID] = None
    ) -> dict:
        """
        全局搜索（公开接口）
        
        处理所有业务逻辑：
        - 高亮生成
        - metadata填充
        
        Args:
            db: 数据库会话
            keyword: 搜索关键词
            page: 页码
            size: 每页数量
            resource_types: 资源类型筛选
            category_id: 分类ID筛选
            
        Returns:
            包含分页数据的响应字典
            
        Raises:
            InvalidParameterException: 参数错误
        """
        # 参数校验
        if len(keyword.strip()) < 2:
            raise InvalidParameterException("搜索关键词至少需要2个字符")
        
        logger.info(f"全局搜索: keyword={keyword}, types={resource_types}, page={page}, size={size}")
        
        # 调用CRUD层获取原始搜索结果
        results_raw, total = await crud.search_global_resources(
            db, keyword, page, size, resource_types, category_id
        )

        # 批量聚合 room 卡片字段（避免逐条 N+1；room_card_map 无专家时已回退创建者）
        # 注意：metadata_json 由 jsonb 序列化，room_id 为字符串；get_room_card_map 入参需 UUID 对象，
        # 返回 key 为 UUID 对象。此处统一归一化为字符串 key，供 _fill_metadata 精确匹配。
        room_card_map: Dict[str, Dict[str, Any]] = {}
        room_ids_raw = [
            (result.get('metadata_json') or {}).get('room_id')
            for result in results_raw
            if result['type'] == 'room' and (result.get('metadata_json') or {}).get('room_id')
        ]
        room_ids: List[uuid.UUID] = []
        for rid in room_ids_raw:
            try:
                room_ids.append(uuid.UUID(str(rid)))
            except (ValueError, TypeError):
                logger.warning(f"搜索 room id 非法，跳过聚合: {rid}")
        if room_ids:
            try:
                card_map_raw = await get_room_card_map(db, room_ids, include_owner=True)
                room_card_map = {str(k): v for k, v in card_map_raw.items()}
            except Exception as e:  # noqa: BLE001
                logger.warning(f"搜索 room 卡片聚合失败，降级为空 metadata: {e}")
                room_card_map = {}

        # 遍历每个结果，应用业务逻辑
        search_items = []
        for result in results_raw:
            # 生成高亮文本（优先高亮标题）
            highlight_text = self._generate_highlight(result['title'], keyword)

            # 填充metadata
            metadata = self._fill_metadata(result, room_card_map=room_card_map)

            # 构造SearchResultItem
            search_item = SearchResultItem(
                type=SearchResultType(result['type']),
                id=result['id'],
                title=result['title'],
                summary=result['summary'],
                cover_url=result['cover_url'],
                match_score=result['match_score'],
                highlight=highlight_text,
                metadata=metadata
            )
            search_items.append(search_item)
        
        logger.info(f"全局搜索成功: 返回{len(search_items)}条")
        
        # 返回响应
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "size": size,
                "items": [item.model_dump(mode='json') for item in search_items]
            },
            "timestamp": datetime.utcnow().isoformat()
        }