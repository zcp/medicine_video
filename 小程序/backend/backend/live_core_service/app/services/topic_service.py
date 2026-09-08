"""
专题聚合功能的 Service 层

本模块封装所有专题相关的业务逻辑，保持框架无关性。

职责：
- 业务逻辑验证（权限检查、状态检查等）
- 复杂查询的组装
- 事务管理

所有方法遵循安全异步异常处理原则。
"""

# 标准库导入
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any

from fastapi import UploadFile
# 第三方库导入
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# 项目内导入
from app.crud import topic as crud_topic
from app.core.file_handler import FileHandler
from app.models.topic import Topic, TopicCategory, TopicCategoryRoom, TopicStatus
from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    RoomAssociation
)
from app.exceptions import (
    TopicNotFoundException,
    CategoryNotFoundException,
    TopicPermissionDeniedException,
    RoomAlreadyAssociatedException,
    RoomNotFoundException,
    PermissionDeniedException
)



# 配置日志
logger = logging.getLogger(__name__)


class TopicService:
    """
    专题聚合功能的业务逻辑服务类
    
    封装所有专题相关的业务逻辑，包括权限验证和复杂查询。
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化Service，存储数据库会话
        
        Args:
            db: 数据库会话对象
        """
        self.db = db
    
    # ==================== 权限守卫函数 ====================
    
    def _check_topic_visibility(
        self,
        topic: Topic,
        user_id: Optional[uuid.UUID],
        role: Optional[str]
    ) -> None:
        """
        统一的专题可见性校验逻辑（基于status字段）
        
        Args:
            topic: 专题对象
            user_id: 当前用户的public_id（从JWT的user_id字段提取，匿名时为None）
            role: 当前用户的角色（匿名时为None）
            
        Raises:
            TopicNotFoundException: 专题不存在或无权访问（404）
        """
        # 1. 已发布专题：直接通过（相当于is_private=false）
        if topic.status == TopicStatus.PUBLISHED:
            return
        
        # 2. 草稿/已归档专题且未登录：拒绝（返回404隐藏存在性）
        if not user_id:
            raise TopicNotFoundException("Topic not found")
        
        # 3. 管理员：上帝视角通过
        if role in ['ADMIN', 'SUPERADMIN']:
            # ✅ 记录Admin查看Private资源的审计日志（INFO级别）
            if topic.user_id != user_id:
                logger.info(
                    f"Admin查看Private专题: admin={user_id}, role={role}, "
                    f"topic_id={topic.id}, owner={topic.user_id}, status={topic.status}"
                )
            return
        
        # 4. 资源创建者：通过
        # 注意：topic.user_id存储的就是创建者的public_id
        if topic.user_id == user_id:
            return
        
        # 5. 其他已登录用户：拒绝（返回404隐藏存在性）
        raise TopicNotFoundException("Topic not found")
    
    def _check_write_permission(
        self,
        topic: Topic,
        user_id: uuid.UUID,
        role: str
    ) -> None:
        """
        写操作权限校验（修改/删除）
        
        Args:
            topic: 专题对象
            user_id: 当前用户的public_id
            role: 当前用户的角色
            
        Raises:
            PermissionDeniedException: 无权修改（403）
        """
        # 管理员：上帝视角通过
        if role in ['ADMIN', 'SUPERADMIN']:
            return
        
        # 资源创建者：通过
        # 注意：topic.user_id存储的就是创建者的public_id
        if topic.user_id == user_id:
            return
        
        # 其他用户：拒绝（返回403，因为已登录）
        raise PermissionDeniedException(
            "You don't have permission to modify this topic"
        )
    
    # ==================== 专题管理方法 ====================
    
    async def create_topic(
        self,
        obj_in: TopicCreate,
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> Topic:
        """
        创建新专题（所有登录用户可创建）
        
        Args:
            obj_in: 专题创建数据
            user_id: 创建者用户ID
            role: 当前用户的角色
        
        Returns:
            Topic: 创建的专题对象
        
        Raises:
            Exception: 数据库异常
        """
        # 提前提取用于日志的变量
        user_id_for_logging = user_id
        
        try:
            topic = await crud_topic.create(self.db, obj_in, user_id)
            logger.info(
                f"创建专题成功: user_id={user_id_for_logging}, "
                f"topic_id={topic.id}, title={topic.title}, status={topic.status}"
            )
            return topic
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"创建专题失败: user_id={user_id_for_logging}, error={str(e)}"
            )
            raise


    async def get_topic_list(
        self,
        page: int,
        size: int,
        status: Optional[TopicStatus] = None,
        title: Optional[str] = None,  # ← 新增：专题标题筛选
        topic_id: Optional[uuid.UUID] = None,  # ← 新增：专题ID筛选
        user_id: Optional[uuid.UUID] = None,  # ← 保持：查询参数（用于业务筛选特定用户的专题）
        role: Optional[str] = None,  # ← 新增：权限参数（用于权限过滤）
        current_user_id: Optional[uuid.UUID] = None  # ← 新增：权限参数（当前用户的public_id，用于权限过滤）
    ) -> Tuple[List[Topic], int]:
        """
        获取专题列表（支持匿名访问）
        
        Args:
            page: 页码（从1开始）
            size: 每页条数
            status: 状态筛选条件（可选）
            title: 专题标题筛选，支持模糊匹配（可选）
            topic_id: 专题ID筛选，精确匹配（可选）
            user_id: 用户ID筛选条件（可选，用于业务筛选特定用户的专题）
            role: 当前用户的角色（匿名时为None，用于权限过滤）
            current_user_id: 当前用户的public_id（匿名时为None，用于权限过滤）
        
        Returns:
            Tuple[List[Topic], int]: (专题列表, 总数)
        """
        # 计算跳过的记录数
        skip = (page - 1) * size
        
        logger.debug(
            f"查询专题列表: page={page}, size={size}, "
            f"status={status}, title={title}, topic_id={topic_id}, user_id={user_id}, current_user_id={current_user_id}, role={role}"
        )
        
        # ← 修改：传递权限参数到CRUD层
        topics, total = await crud_topic.get_multi_and_total(
            self.db,
            skip=skip,
            limit=size,
            status=status,
            title=title,  # ← 新增：传递title参数
            topic_id=topic_id,  # ← 新增：传递topic_id参数
            user_id=user_id,  # ← 查询参数（筛选条件，用于业务筛选）
            current_user_id=current_user_id,  # ← 新增：用于权限过滤（当前用户的public_id）
            current_user_role=role  # ← 新增：用于权限过滤（当前用户的角色）
        )
        
        return topics, total
    
    async def get_topic_detail(
        self, 
        topic_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,  # ← 新增：权限参数
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> Dict[str, Any]:
        """
        获取专题详情（支持匿名访问）
        
        Args:
            topic_id: 专题唯一标识
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
        
        Returns:
            Dict: 完整的专题详情字典，包含分类和直播间的层级化数据
        
        Raises:
            TopicNotFoundException: 专题不存在或无权访问
        """
        # 提前提取用于日志的变量
        topic_id_for_logging = topic_id
        
        try:
            # 1. 获取专题和分类
            topic = await crud_topic.get_with_categories(self.db, topic_id)
            
            if not topic:
                raise TopicNotFoundException(str(topic_id))
            
            # ← 新增：权限校验（调用守卫函数）
            self._check_topic_visibility(topic, user_id, role)
            
            # 2. 构建基础专题信息
            topic_detail = {
                "id": str(topic.id),
                "user_id": str(topic.user_id),
                "title": topic.title,
                "description": topic.description,
                "banner_url": topic.banner_url,
                "status": topic.status.value if isinstance(topic.status, TopicStatus) else topic.status,
                "created_at": topic.created_at.isoformat() + "Z",
                "updated_at": topic.updated_at.isoformat() + "Z",
                "categories": []
            }
            
            # 3. 对每个分类，获取关联的直播间
            for category in sorted(topic.categories, key=lambda c: c.sort_order):
                # 获取分类下的直播间
                rooms_data, _ = await crud_topic.get_rooms_by_category(
                    self.db,
                    category.id,
                    skip=0,
                    limit=1000  # 假设一个分类下不会超过1000个直播间
                )
                
                # 构建直播间列表（包含状态和热度）
                rooms_list = []
                for room_data in rooms_data:
                    room_id = uuid.UUID(room_data['room_id'])
                    
                    # 查询最新场次状态
                    stmt = select(LiveSession).where(
                        LiveSession.room_id == room_id
                    ).order_by(LiveSession.created_at.desc()).limit(1)
                    result = await self.db.execute(stmt)
                    latest_session = result.scalar_one_or_none()
                    
                    live_status = "finished"
                    start_time = None
                    heat = 0
                    
                    if latest_session:
                        live_status = latest_session.status.value if hasattr(latest_session.status, 'value') else str(latest_session.status)
                        start_time = latest_session.start_time
                        
                        # 计算heat值：查询该直播间所有场次的统计数据
                        stats_stmt = select(
                            func.sum(SessionStatistics.total_viewer_count).label('total_viewers'),
                            func.sum(SessionStatistics.total_like_count).label('total_likes'),
                            func.max(SessionStatistics.peak_viewer_count).label('peak_viewers')
                        ).select_from(LiveSession).join(
                            SessionStatistics,
                            LiveSession.id == SessionStatistics.session_id
                        ).where(LiveSession.room_id == room_id)
                        
                        stats_result = await self.db.execute(stats_stmt)
                        stats = stats_result.one_or_none()
                        
                        if stats and stats.total_viewers:
                            heat = int(
                                (stats.total_viewers or 0) * 0.5 +
                                (stats.total_likes or 0) * 0.3 +
                                (stats.peak_viewers or 0) * 0.2
                            )
                    
                    rooms_list.append({
                        "id": room_data['room_id'],
                        "title": room_data['title'],
                        "cover_url": room_data['cover_url'],
                        "live_status": live_status,
                        "start_time": start_time.isoformat() + "Z" if start_time else None,
                        "heat": heat
                    })
                
                # 添加分类和直播间到结果
                topic_detail["categories"].append({
                    "id": str(category.id),
                    "name": category.name,
                    "sort_order": category.sort_order,
                    "rooms": rooms_list
                })
            
            logger.info(
                f"获取专题详情成功: topic_id={topic_id_for_logging}, "
                f"categories_count={len(topic_detail['categories'])}"
            )
            
            return topic_detail
            
        except TopicNotFoundException:
            # ✅ 使用局部变量记录日志
            logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"获取专题详情失败: topic_id={topic_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def update_topic(
        self,
        topic_id: uuid.UUID,
        user_id: uuid.UUID,
        obj_in: TopicUpdate,
        role: str  # ← 新增：权限参数
    ) -> Topic:
        """
        更新专题信息（Owner/Admin Only）
        
        Args:
            topic_id: 专题唯一标识
            user_id: 当前用户ID
            obj_in: 更新数据
            role: 当前用户的角色
        
        Returns:
            Topic: 更新后的专题对象
        
        Raises:
            TopicNotFoundException: 专题不存在
            PermissionDeniedException: 权限不足
        """
        # 提前提取用于日志的变量
        topic_id_for_logging = topic_id
        user_id_for_logging = user_id
        
        try:
            # 1. 获取专题对象
            topic = await crud_topic.get(self.db, topic_id)
            
            if not topic:
                raise TopicNotFoundException(str(topic_id))
            
            # ← 修改：使用权限守卫函数
            self._check_write_permission(topic, user_id, role)
            
            # 2. 更新专题
            updated_topic = await crud_topic.update(self.db, topic, obj_in)
            
            # ✅ 记录业务操作成功日志（INFO级别）
            logger.info(
                f"更新专题成功: user_id={user_id_for_logging}, "
                f"topic_id={topic_id_for_logging}"
            )
            
            return updated_topic
            
        except (TopicNotFoundException, PermissionDeniedException):
            # 业务异常直接抛出
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"更新专题失败: topic_id={topic_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def delete_topic(
        self,
        topic_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> Topic:
        """
        删除专题（Owner/Admin Only）
        
        Args:
            topic_id: 专题唯一标识
            user_id: 当前用户ID
            role: 当前用户的角色
        
        Returns:
            Topic: 被删除的专题对象
        
        Raises:
            TopicNotFoundException: 专题不存在
            PermissionDeniedException: 权限不足
        """
        # 提前提取用于日志的变量
        topic_id_for_logging = topic_id
        user_id_for_logging = user_id
        
        try:
            # 1. 获取专题对象
            topic = await crud_topic.get_with_categories(self.db, topic_id)
            
            if not topic:
                raise TopicNotFoundException(str(topic_id))
            
            # ← 修改：使用权限守卫函数
            self._check_write_permission(topic, user_id, role)
            
            # 提取分类数量用于日志
            categories_count = len(topic.categories) if hasattr(topic, 'categories') else 0
            
            # 3. 删除专题
            deleted_topic = await crud_topic.remove(self.db, topic)
            
            logger.warning(
                f"删除专题: user_id={user_id_for_logging}, "
                f"topic_id={topic_id_for_logging}, categories_count={categories_count}"
            )
            
            return deleted_topic
            
        except (TopicNotFoundException, PermissionDeniedException):
            # 业务异常直接抛出
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"删除专题失败: topic_id={topic_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}"
            )
            raise
    
    # ==================== 专题横幅管理方法 ====================
    
    async def upload_topic_banner(
        self, 
        topic_id: uuid.UUID, 
        file: UploadFile,
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> Topic:
        """
        为指定专题上传横幅图片（Owner/Admin Only）
        
        完全复用直播间封面上传的实现逻辑，只需调整：
        - 存储路径：/media/topics/ 而非 /media/rooms/
        - 文件前缀：banner_ 而非 cover_
        - 数据库字段：topic.banner_url 而非 room.cover_url
        
        Args:
            topic_id: 专题ID
            file: 上传的文件对象
            user_id: 当前用户ID
            role: 当前用户的角色
            
        Returns:
            更新后的Topic对象
            
        Raises:
            TopicNotFoundException: 专题不存在
            PermissionDeniedException: 用户无权修改此专题
        """
        # 提前提取用于日志的变量
        topic_id_for_logging = topic_id
        user_id_for_logging = user_id
        
        logger.info(f"开始上传专题横幅: topic_id={topic_id_for_logging}, user_id={user_id_for_logging}")
        
        try:
            # 1. 验证专题存在性
            topic = await crud_topic.get(self.db, topic_id)
            if not topic:
                raise TopicNotFoundException(str(topic_id))
            
            # ← 修改：使用权限守卫函数
            self._check_write_permission(topic, user_id, role)
            
            # 2. 如果专题已有横幅，删除旧文件
            if topic.banner_url:
                logger.info(f"删除旧横幅文件: banner_url={topic.banner_url}")
                FileHandler.delete_old_banner(topic.banner_url)
            
            # 3. 保存新文件（调用FileHandler的banner专用方法）
            banner_url = await FileHandler.save_banner_file(file=file, topic_id=topic_id)
            logger.info(f"新横幅文件保存成功: banner_url={banner_url}")
            
            # 4. 更新数据库 banner_url
            updated_topic = await crud_topic.update_banner_url(
                db=self.db, 
                topic_id=topic_id, 
                banner_url=banner_url
            )
            
            if not updated_topic:
                logger.error(f"更新横幅URL失败: topic_id={topic_id_for_logging}")
                raise Exception("更新横幅URL失败")
            
            logger.info(f"横幅上传成功: topic_id={topic_id_for_logging}, banner_url={banner_url}")
            
            # 5. 返回更新后的专题对象
            return updated_topic
            
        except (TopicNotFoundException, PermissionDeniedException):
            # 重新抛出业务异常，不记录额外日志
            raise
        except Exception as e:
            logger.error(
                f"上传专题横幅失败: topic_id={topic_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}", 
                exc_info=True
            )
            raise
    
    # ==================== 分类管理方法 ====================
    
    async def create_category(
        self,
        topic_id: uuid.UUID,
        user_id: uuid.UUID,
        obj_in: CategoryCreate,
        role: str  # ← 新增：权限参数
    ) -> TopicCategory:
        """
        创建分类（专题Owner/Admin Only）
        
        Args:
            topic_id: 专题唯一标识
            user_id: 当前用户ID
            obj_in: 分类创建数据
            role: 当前用户的角色
        
        Returns:
            TopicCategory: 创建的分类对象
        
        Raises:
            TopicNotFoundException: 专题不存在
            PermissionDeniedException: 权限不足
        """
        # 提前提取用于日志的变量
        topic_id_for_logging = topic_id
        user_id_for_logging = user_id
        
        try:
            # 1. 获取专题对象
            topic = await crud_topic.get(self.db, topic_id)
            
            if not topic:
                raise TopicNotFoundException(str(topic_id))
            
            # ← 修改：使用权限守卫函数（继承专题权限）
            self._check_write_permission(topic, user_id, role)
            
            # 3. 创建分类
            category = await crud_topic.create_category(self.db, obj_in, topic_id)
            
            logger.info(
                f"创建分类成功: user_id={user_id_for_logging}, "
                f"topic_id={topic_id_for_logging}, category_id={category.id}"
            )
            
            return category
            
        except (TopicNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"创建分类失败: topic_id={topic_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def get_category_list(
        self,
        topic_id: uuid.UUID,
        page: int,
        size: int,
        user_id: Optional[uuid.UUID] = None,  # ← 新增：权限参数
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> Tuple[List[TopicCategory], int]:
        """
        获取分类列表（继承专题可见性）
        
        Args:
            topic_id: 专题唯一标识
            page: 页码（从1开始）
            size: 每页条数
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
        
        Returns:
            Tuple[List[TopicCategory], int]: (分类列表, 总数)
        
        Raises:
            TopicNotFoundException: 专题不存在或无权访问
        """
        # 提前提取用于日志的变量
        topic_id_for_logging = topic_id
        
        try:
            # 1. 验证专题存在性
            topic = await crud_topic.get(self.db, topic_id)
            
            if not topic:
                raise TopicNotFoundException(str(topic_id))
            
            # ← 新增：检查专题可见性（分类继承专题权限）
            self._check_topic_visibility(topic, user_id, role)
            
            # 2. 获取分类列表
            skip = (page - 1) * size
            categories, total = await crud_topic.get_categories_by_topic(
                self.db,
                topic_id,
                skip=skip,
                limit=size
            )
            
            return categories, total
            
        except TopicNotFoundException:
            # ✅ 使用局部变量记录日志
            logger.warning(f"专题不存在: topic_id={topic_id_for_logging}")
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"获取分类列表失败: topic_id={topic_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def update_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        obj_in: CategoryUpdate,
        role: str  # ← 新增：权限参数
    ) -> TopicCategory:
        """
        更新分类（专题Owner/Admin Only）
        
        Args:
            category_id: 分类唯一标识
            user_id: 当前用户ID
            obj_in: 更新数据
            role: 当前用户的角色
        
        Returns:
            TopicCategory: 更新后的分类对象
        
        Raises:
            CategoryNotFoundException: 分类不存在
            PermissionDeniedException: 权限不足
        """
        # 提前提取用于日志的变量
        category_id_for_logging = category_id
        user_id_for_logging = user_id
        
        try:
            # 1. 获取分类及其专题
            category = await crud_topic.get_category_with_topic(self.db, category_id)
            
            if not category:
                raise CategoryNotFoundException(str(category_id))
            
            # ← 修改：使用权限守卫函数（继承专题权限）
            self._check_write_permission(category.topic, user_id, role)
            
            # 3. 更新分类
            updated_category = await crud_topic.update_category(self.db, category, obj_in)
            
            logger.info(
                f"更新分类成功: user_id={user_id_for_logging}, "
                f"category_id={category_id_for_logging}"
            )
            
            return updated_category
            
        except (CategoryNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"更新分类失败: category_id={category_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def delete_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str  # ← 新增：权限参数
    ) -> TopicCategory:
        """
        删除分类（专题Owner/Admin Only）
        
        Args:
            category_id: 分类唯一标识
            user_id: 当前用户ID
            role: 当前用户的角色
        
        Returns:
            TopicCategory: 被删除的分类对象
        
        Raises:
            CategoryNotFoundException: 分类不存在
            PermissionDeniedException: 权限不足
        """
        # 提前提取用于日志的变量
        category_id_for_logging = category_id
        user_id_for_logging = user_id
        
        try:
            # 1. 获取分类及其专题
            category = await crud_topic.get_category_with_topic(self.db, category_id)
            
            if not category:
                raise CategoryNotFoundException(str(category_id))
            
            # ← 修改：使用权限守卫函数（继承专题权限）
            self._check_write_permission(category.topic, user_id, role)
            
            # 3. 删除分类
            deleted_category = await crud_topic.remove_category(self.db, category)
            
            logger.warning(
                f"删除分类: user_id={user_id_for_logging}, "
                f"category_id={category_id_for_logging}"
            )
            
            return deleted_category
            
        except (CategoryNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"删除分类失败: category_id={category_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}"
            )
            raise
    
    # ==================== 直播间关联方法 ====================
    
    async def add_rooms_to_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        room_associations: List[RoomAssociation],
        role: str  # ← 新增：权限参数
    ) -> List[TopicCategoryRoom]:
        """
        批量添加直播间到分类（专题Owner/Admin Only）
        
        Args:
            category_id: 分类唯一标识
            user_id: 当前用户ID
            room_associations: 直播间关联列表
            role: 当前用户的角色
        
        Returns:
            List[TopicCategoryRoom]: 创建的关联对象列表
        
        Raises:
            CategoryNotFoundException: 分类不存在
            PermissionDeniedException: 权限不足
            RoomNotFoundException: 直播间不存在
            RoomAlreadyAssociatedException: 直播间已关联
        """
        # 提前提取用于日志的变量
        category_id_for_logging = category_id
        user_id_for_logging = user_id
        room_count = len(room_associations)
        
        try:
            # 1. 获取分类及其专题
            category = await crud_topic.get_category_with_topic(self.db, category_id)
            
            if not category:
                raise CategoryNotFoundException(str(category_id))
            
            # ← 修改：使用权限守卫函数（继承专题权限）
            self._check_write_permission(category.topic, user_id, role)
            
            # 2. 验证所有room_id存在
            room_ids = [assoc.room_id for assoc in room_associations]
            stmt = select(LiveRoom.id).where(LiveRoom.id.in_(room_ids))
            result = await self.db.execute(stmt)
            existing_room_ids = {row[0] for row in result.all()}
            
            missing_room_ids = set(room_ids) - existing_room_ids
            if missing_room_ids:
                raise RoomNotFoundException(str(missing_room_ids))
            
            # 3. 检查是否已存在关联
            for assoc in room_associations:
                exists = await crud_topic.check_room_association_exists(
                    self.db,
                    category_id,
                    assoc.room_id
                )
                if exists:
                    raise RoomAlreadyAssociatedException(
                        str(assoc.room_id),
                        str(category_id)
                    )
            
            # 4. 批量添加直播间
            associations = await crud_topic.batch_add_rooms(
                self.db,
                category_id,
                room_associations
            )
            
            logger.info(
                f"批量添加直播间成功: user_id={user_id_for_logging}, "
                f"category_id={category_id_for_logging}, count={room_count}"
            )
            
            return associations
            
        except (CategoryNotFoundException, PermissionDeniedException, 
                RoomNotFoundException, RoomAlreadyAssociatedException):
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"批量添加直播间失败: category_id={category_id_for_logging}, "
                f"user_id={user_id_for_logging}, count={room_count}, error={str(e)}"
            )
            raise
    
    async def get_rooms_in_category(
        self,
        category_id: uuid.UUID,
        page: int,
        size: int,
        user_id: Optional[uuid.UUID] = None,  # ← 新增：权限参数
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取分类下的直播间列表（双重权限过滤：专题权限+直播间权限）
        
        Args:
            category_id: 分类唯一标识
            page: 页码（从1开始）
            size: 每页条数
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
        
        Returns:
            Tuple[List[Dict], int]: (直播间信息列表, 总数)
        
        Raises:
            CategoryNotFoundException: 分类不存在
            TopicNotFoundException: 专题不存在或无权访问
        """
        # 提前提取用于日志的变量
        category_id_for_logging = category_id
        
        try:
            # 1. 获取分类及其专题
            category = await crud_topic.get_category_with_topic(self.db, category_id)
            
            if not category:
                raise CategoryNotFoundException(str(category_id))
            
            # 2. 获取专题并检查可见性
            topic = category.topic
            if not topic:
                raise TopicNotFoundException(f"专题 {category.topic_id} 不存在")
            
            # ← 新增：检查专题可见性（双重权限过滤的第一步）
            self._check_topic_visibility(topic, user_id, role)
            
            # 3. 查询直播间（应用Room模块的权限过滤，双重权限过滤的第二步）
            # 注意：get_rooms_by_category需要在CRUD层实现权限过滤，传递user_id和role
            skip = (page - 1) * size
            rooms, total = await crud_topic.get_rooms_by_category(
                self.db,
                category_id,
                skip=skip,
                limit=size,
                user_id=user_id,  # ← 新增：用于直播间权限过滤
                role=role  # ← 新增：用于直播间权限过滤
            )
            
            # 3. 查询每个直播间的最新live_status
            for room in rooms:
                room_id = uuid.UUID(room['room_id'])
                stmt = select(LiveSession.status).where(
                    LiveSession.room_id == room_id
                ).order_by(LiveSession.created_at.desc()).limit(1)
                result = await self.db.execute(stmt)
                latest_status = result.scalar_one_or_none()
                
                if latest_status:
                    room['live_status'] = latest_status.value if hasattr(latest_status, 'value') else str(latest_status)
                else:
                    room['live_status'] = "finished"
            
            return rooms, total
            
        except CategoryNotFoundException:
            # ✅ 使用局部变量记录日志
            logger.warning(f"分类不存在: category_id={category_id_for_logging}")
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"获取直播间列表失败: category_id={category_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def update_room_sort_order(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        room_sort_updates: List[Dict[str, Any]],
        role: str  # ← 新增：权限参数
    ) -> int:
        """
        批量更新排序（专题Owner/Admin Only）
        
        Args:
            category_id: 分类唯一标识
            user_id: 当前用户ID
            room_sort_updates: 排序更新列表
            role: 当前用户的角色
        
        Returns:
            int: 更新的记录数
        
        Raises:
            CategoryNotFoundException: 分类不存在
            PermissionDeniedException: 权限不足
        """
        # 提前提取用于日志的变量
        category_id_for_logging = category_id
        user_id_for_logging = user_id
        
        try:
            # 1. 获取分类及其专题
            category = await crud_topic.get_category_with_topic(self.db, category_id)
            
            if not category:
                raise CategoryNotFoundException(str(category_id))
            
            # ← 修改：使用权限守卫函数（继承专题权限）
            self._check_write_permission(category.topic, user_id, role)
            
            # 2. 更新排序
            updated_count = await crud_topic.update_room_sort_order(
                self.db,
                category_id,
                room_sort_updates
            )
            
            logger.info(
                f"批量更新排序成功: user_id={user_id_for_logging}, "
                f"category_id={category_id_for_logging}, updated_count={updated_count}"
            )
            
            return updated_count
            
        except (CategoryNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"批量更新排序失败: category_id={category_id_for_logging}, "
                f"user_id={user_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def remove_rooms_from_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        room_ids: List[uuid.UUID],
        role: str  # ← 新增：权限参数
    ) -> int:
        """
        批量移除直播间（专题Owner/Admin Only）
        
        Args:
            category_id: 分类唯一标识
            user_id: 当前用户ID
            room_ids: 要移除的直播间ID列表
            role: 当前用户的角色
        
        Returns:
            int: 删除的记录数
        
        Raises:
            CategoryNotFoundException: 分类不存在
            PermissionDeniedException: 权限不足
        """
        # 提前提取用于日志的变量
        category_id_for_logging = category_id
        user_id_for_logging = user_id
        room_count = len(room_ids)
        
        try:
            # 1. 获取分类及其专题
            category = await crud_topic.get_category_with_topic(self.db, category_id)
            
            if not category:
                raise CategoryNotFoundException(str(category_id))
            
            # ← 修改：使用权限守卫函数（继承专题权限）
            self._check_write_permission(category.topic, user_id, role)
            
            # 2. 批量移除直播间
            deleted_count = await crud_topic.batch_remove_rooms(
                self.db,
                category_id,
                room_ids
            )
            
            logger.info(
                f"批量移除直播间成功: user_id={user_id_for_logging}, "
                f"category_id={category_id_for_logging}, deleted_count={deleted_count}"
            )
            
            return deleted_count
            
        except (CategoryNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"批量移除直播间失败: category_id={category_id_for_logging}, "
                f"user_id={user_id_for_logging}, count={room_count}, error={str(e)}"
            )
            raise
    
    # ==================== 辅助查询方法 ====================
    
    async def get_topics_by_room(
        self, 
        room_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,  # ← 新增：权限参数
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> List[Dict[str, Any]]:
        """
        获取直播间关联的专题列表（双重权限过滤：直播间权限+专题权限）
        
        Args:
            room_id: 直播间唯一标识
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
        
        Returns:
            List[Dict]: 专题信息列表
        
        Raises:
            RoomNotFoundException: 直播间不存在或无权访问
        """
        # 提前提取用于日志的变量
        room_id_for_logging = room_id
        
        try:
            # 1. 检查直播间可见性（使用Room模块的权限守卫函数）
            stmt = select(LiveRoom).where(LiveRoom.id == room_id)
            result = await self.db.execute(stmt)
            room = result.scalar_one_or_none()
            
            if not room:
                raise RoomNotFoundException(str(room_id))
            
            # ← 新增：检查直播间可见性（需要导入RoomService的守卫函数或复用）
            # 注意：这里需要调用Room模块的权限守卫函数
            # 如果RoomService已实现，可以通过依赖注入或服务组合的方式调用
            # 例如：from app.services.room_service import RoomService
            #      room_service = RoomService(self.db)
            #      room_service._check_room_visibility(room, user_id, role)
            # 为了最小幅度修改，我们直接实现相同的逻辑
            if room.is_private:
                if not user_id:
                    raise RoomNotFoundException("Room not found")
                if role not in ['ADMIN', 'SUPERADMIN']:
                    if room.user_id != user_id:
                        raise RoomNotFoundException("Room not found")
            
            # 2. 查询关联的专题（应用Topic模块的权限过滤）
            # 注意：get_topics_by_room 方法已在CRUD层实现（参见专题功能CRUD层代码生成提示词），
            # 通过三表JOIN查询：topic_category_rooms -> topic_categories -> topics
            # 根据用户身份应用不同的WHERE条件（参见权限设计文档 § 3.1 接口3的SQL策略）：
            # - Admin：无过滤，看所有状态的专题
            # - Regular User：Published OR (Draft/Archived AND Own)
            # - Anonymous：Only Published
            # 注意：该方法在权限增补时需要增加 user_id 和 role 参数，参见CRUD层权限增补提示词文档
            topics = await crud_topic.get_topics_by_room(
                self.db,
                room_id=room_id,
                user_id=user_id,  # ← 用于专题权限过滤（权限增补新增参数）
                role=role  # ← 用于专题权限过滤（权限增补新增参数）
            )
            
            return topics
            
        except RoomNotFoundException:
            # ✅ 使用局部变量记录日志
            logger.warning(f"直播间不存在: room_id={room_id_for_logging}")
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(
                f"获取关联专题失败: room_id={room_id_for_logging}, error={str(e)}"
            )
            raise
    
    async def batch_get_room_status(
        self,
        room_ids: List[uuid.UUID],
        user_id: Optional[uuid.UUID] = None,  # ← 新增：权限参数
        role: Optional[str] = None  # ← 新增：权限参数
    ) -> List[Dict[str, Any]]:
        """
        批量获取多个直播间的实时状态（Room权限过滤）
        
        Args:
            room_ids: 直播间ID列表
            user_id: 当前用户的public_id（匿名时为None）
            role: 当前用户的角色（匿名时为None）
        
        Returns:
            List[Dict]: 直播间状态列表
        
        Raises:
            RoomNotFoundException: 部分直播间不存在
        """
        # 提前提取用于日志的变量
        room_count = len(room_ids)
        
        try:
            # 1. 参数验证
            if len(room_ids) > 100:
                raise ValueError("最多支持一次查询100个直播间")
            
            # 2. 批量查询直播间
            stmt = select(LiveRoom).where(LiveRoom.id.in_(room_ids))
            result = await self.db.execute(stmt)
            existing_rooms = result.scalars().all()
            existing_room_ids = {room.id for room in existing_rooms}
            
            missing_room_ids = set(room_ids) - existing_room_ids
            if missing_room_ids:
                raise RoomNotFoundException(str(missing_room_ids))
            
            # ← 新增：应用Room权限过滤（只返回用户有权限访问的直播间）
            filtered_rooms = []
            for room in existing_rooms:
                # 公开直播间：所有人可见
                if not room.is_private:
                    filtered_rooms.append(room)
                    continue
                
                # 私有直播间：需要检查权限
                if not user_id:
                    # 匿名用户：跳过私有直播间
                    continue
                
                if role in ['ADMIN', 'SUPERADMIN']:
                    # Admin：可以看到所有直播间
                    filtered_rooms.append(room)
                elif room.user_id == user_id:
                    # Owner：可以看到自己的直播间
                    filtered_rooms.append(room)
                # 其他用户：跳过
            
            # 3. 批量查询场次状态（只查询过滤后的直播间）
            room_status_list = []
            
            for room in filtered_rooms:
                room_id = room.id
                # 查询最新场次
                session_stmt = select(LiveSession).where(
                    LiveSession.room_id == room_id
                ).order_by(LiveSession.created_at.desc()).limit(1)
                session_result = await self.db.execute(session_stmt)
                latest_session = session_result.scalar_one_or_none()
                
                live_status = "finished"
                current_session_id = None
                viewer_count = 0
                
                if latest_session:
                    live_status = latest_session.status.value if hasattr(latest_session.status, 'value') else str(latest_session.status)
                    
                    if live_status == "live":
                        current_session_id = latest_session.id
                        
                        # 查询观看人数
                        stats_stmt = select(SessionStatistics.peak_viewer_count).where(
                            SessionStatistics.session_id == latest_session.id
                        )
                        stats_result = await self.db.execute(stats_stmt)
                        peak_count = stats_result.scalar_one_or_none()
                        viewer_count = peak_count or 0
                
                room_status_list.append({
                    "room_id": str(room_id),
                    "live_status": live_status,
                    "current_session_id": str(current_session_id) if current_session_id else None,
                    "viewer_count": viewer_count
                })
            
            logger.debug(f"批量查询直播间状态: count={len(filtered_rooms)}/{room_count}")
            
            return room_status_list
            
        except (ValueError, RoomNotFoundException):
            raise
        except Exception as e:
            # ✅ 使用局部变量记录日志
            logger.error(f"批量查询状态失败: count={room_count}, error={str(e)}")
            raise

