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
from datetime import datetime

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
    REJECTED_IMAGE_URL_PATTERNS,
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
from app.content_safety.schemas import ContentSafetyItem
from app.content_safety.service import check_content_safety
import logging

logger = logging.getLogger(__name__)


class HomepageSearchService:
    """首页与搜索模块Service层"""
    
    # ==================== 权限守卫函数 ====================
    
    def _check_admin_permission(self, user_role: str) -> None:
        """
        管理员权限检查
        
        Args:
            user_role: 用户角色（必须是大写）
            
        Raises:
            PermissionDeniedException: 权限不足
        """
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            raise PermissionDeniedException("权限不足，需要管理员权限")
    
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
        content_items = []
        for item in items:
            item_dict = FeaturedContentItem.model_validate(item).model_dump(mode='json')
            # 防御性过滤：排除 image_url 为本地临时路径的脏数据
            image_url = item_dict.get('image_url', '')
            if any(p.match(image_url) for p in REJECTED_IMAGE_URL_PATTERNS):
                logger.warning(f"公开列表过滤脏数据: id={item_dict.get('id')}, image_url={image_url}")
                continue
            content_items.append(item_dict)

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
        self._check_admin_permission(role)
        
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
        search_type: Optional[str] = None
    ) -> dict:
        """
        获取焦点图列表（管理员，分页）。
        返回统一分页格式 data: { total, page, size, items }。
        支持 q、search_type 列表搜索（与前端列表筛选与搜索规范对齐）。
        """
        self._check_admin_permission(role)

        items, total = await crud.get_featured_content_list_paginated(
            db, page=page, size=size, q=q, search_type=search_type
        )
        content_items = [FeaturedContentItem.model_validate(item).model_dump(mode='json') for item in items]

        logger.info(
            f"查询焦点图列表（管理员分页），page={page}, size={size}, total={total}, "
            f"q={q}, search_type={search_type}, 管理员={str(current_user_id)[:8]}"
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
        self._check_admin_permission(role)
        
        # 目标资源验证（如果提供了target_id）
        if content_data.target_id and content_data.target_type:
            await self._validate_target_resource(db, content_data.target_type, content_data.target_id)
        
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
        self._check_admin_permission(role)

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
        self._check_admin_permission(role)
        
        # 目标资源验证（如果更新了target_id和target_type）
        update_dict = content_data.model_dump(exclude_unset=True)
        if "target_id" in update_dict and "target_type" in update_dict:
            await self._validate_target_resource(db, update_dict["target_type"], update_dict["target_id"])
        
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
        删除焦点图（软删除，管理员功能）
        
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
        self._check_admin_permission(role)
        
        # 调用CRUD层删除（软删除）
        success = await crud.delete_featured_content(db, content_id, soft_delete=True)
        
        # 404检查
        if not success:
            raise NotFoundException(f"焦点图不存在: {content_id}")
        
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

        self._check_admin_permission(role)

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

        logger.info(
            f"上传焦点图图片: content_id={str(content_id)[:8]}, path={url_path}, "
            f"管理员={str(current_user_id)[:8]}"
        )
        return {
            "code": 200,
            "message": "图片上传成功",
            "data": {
                "image_url": url_path
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    # ==================== Homepage API Service方法 (Phase2) ====================
    
    def _select_host(self, room_data: Dict) -> Optional[HomepageHostInfo]:
        """
        Host选择逻辑（私有方法）
        
        优先级：
        1. 场次主讲专家（session_expert_role == '主讲'）
        2. 场次其他专家（session_expert_role in ['主持', '嘉宾']）
        3. null（场次没有关联专家）
        
        注意：不再使用房主专家或房主用户ID
        
        Args:
            room_data: CRUD层返回的原始房间数据
            
        Returns:
            HomepageHostInfo对象或None
        """
        # 如果场次有关联启用专家（CRUD 已过滤 is_active=false）
        if room_data.get('expert_id'):
            return HomepageHostInfo(
                expert_id=room_data['expert_id'],
                user_id=None,  # 专家情况下user_id为None
                name=room_data['expert_name'],
                title=room_data.get('expert_title'),
                hospital=room_data.get('expert_hospital'),
                avatar_url=room_data.get('expert_avatar_url'),
            )
        
        # 场次没有关联专家，返回null
        return None
    
    def _determine_live_status(self, session_status: Optional[str]) -> LiveStatusEnum:
        """
        确定直播状态（私有方法）
        
        映射关系：
        - session_status == 'live' → LiveStatusEnum.LIVE
        - session_status in ['ready', 'scheduled'] → LiveStatusEnum.SCHEDULED
        - session_status in ['ended', 'archived'] → LiveStatusEnum.REPLAY
        - session_status is None → LiveStatusEnum.REPLAY（默认）
        
        Args:
            session_status: 场次状态
            
        Returns:
            LiveStatusEnum枚举值
        """
        if session_status == 'live':
            return LiveStatusEnum.LIVE
        elif session_status in ['ready', 'scheduled']:
            return LiveStatusEnum.SCHEDULED
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
        
        # 遍历每个房间，应用业务逻辑
        room_items = []
        for room_data in rooms_raw:
            # Host选择
            host = self._select_host(room_data)
            
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
                heat=heat,
                primary_category_name=room_data.get('primary_category_name'),
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
    
    def _fill_metadata(self, result: Dict) -> Dict[str, Any]:
        """
        根据资源类型填充metadata（私有方法）
        
        MVP阶段简化实现：
        - room: 返回空字典{}（避免额外查询）
        - expert: 使用CRUD层返回的metadata_json
        - topic: 返回空字典{}（避免额外查询）
        - brand: 返回空字典{}
        
        Args:
            result: CRUD层返回的搜索结果
            
        Returns:
            metadata字典
        """
        result_type = result['type']
        
        if result_type == 'room':
            # MVP阶段：返回简化的metadata
            return {}
        
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

        # 搜索关键词内容安全校验（block 时不执行搜索、不落历史）
        await check_content_safety(
            db,
            scene="search_query",
            items=[ContentSafetyItem(field_name="keyword", value=keyword.strip())],
            resource_type="search",
            user_id=None,
            fail_open=False,
        )
        
        logger.info(f"全局搜索: keyword={keyword}, types={resource_types}, page={page}, size={size}")
        
        # 调用CRUD层获取原始搜索结果
        results_raw, total = await crud.search_global_resources(
            db, keyword, page, size, resource_types, category_id
        )
        
        # 遍历每个结果，应用业务逻辑
        search_items = []
        for result in results_raw:
            # 生成高亮文本（优先高亮标题）
            highlight_text = self._generate_highlight(result['title'], keyword)
            
            # 填充metadata
            metadata = self._fill_metadata(result)
            
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