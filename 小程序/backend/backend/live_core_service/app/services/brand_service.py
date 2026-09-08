"""
品牌模块的Service层代码

本模块包含品牌模块所需的14个Service方法：
- Brands Service: 7个方法
- Brand_Topics Service: 3个方法
- Brand_Rooms Service: 3个方法
- 权限守卫: 1个方法
"""
import logging
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import brand as crud
from app.models.brand import Brand
from app.models.topic import Topic  # 专题模型
from app.models.live_core import LiveRoom  # 直播间模型
from app.schemas.brand import (
    BrandCreate, BrandUpdate, BrandItem,
    TopicBriefItem, RoomBrandItem
)
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException
)

logger = logging.getLogger(__name__)


class BrandService:
    """品牌服务类"""
    
    def _check_admin_permission(self, user_role: str) -> None:
        """
        管理员权限检查
        
        Args:
            user_role: 用户角色（必须是大写：ADMIN/SUPERADMIN/REGULAR）
        
        Raises:
            PermissionDeniedException: 权限不足
        """
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            raise PermissionDeniedException("权限不足，需要管理员权限")

    def _check_admin_or_room_owner(
        self,
        room: LiveRoom,
        current_user_id: UUID,
        role: str,
    ) -> None:
        """
        直播间品牌绑定写权限：Admin/SUPERADMIN 或房间 owner。
        可绑任意启用品牌（支持品牌联动）；不限制 brand_members。
        """
        role_upper = (role or "").upper()
        if role_upper in ("ADMIN", "SUPERADMIN"):
            return
        if room.user_id == current_user_id:
            return
        raise PermissionDeniedException("需要管理员权限或房间所有者权限")
    
    # ==================== Brands Service方法 (7个) ====================
    
    async def get_brands_list(
        self,
        db: AsyncSession,
        limit: int,
        q: Optional[str],
        current_user_id: Optional[UUID],
        role: Optional[str]
    ) -> dict:
        """
        获取品牌列表（公开接口）
        
        Args:
            db: 数据库会话
            limit: 返回数量限制
            q: 模糊搜索关键词
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
        
        Returns:
            标准响应字典
        """
        brands = await crud.get_brands(db, limit, q)
        brand_items = [BrandItem.model_validate(b) for b in brands]
        
        return {
            "code": 200,
            "message": "success",
            "data": brand_items,
            "timestamp": datetime.utcnow()
        }
    
    async def get_brand_content(
        self,
        db: AsyncSession,
        brand_id: UUID,
        current_user_id: Optional[UUID],
        role: Optional[str]
    ) -> dict:
        """
        获取品牌详情及关联专题
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
        
        Returns:
            标准响应字典
        
        Raises:
            NotFoundException: 品牌不存在
        """
        brand, topics = await crud.get_brand_with_topics(db, brand_id)
        
        if not brand:
            raise NotFoundException("品牌不存在")
        
        # 序列化品牌和专题
        brand_info = BrandItem.model_validate(brand)
        associated_topics = [
            TopicBriefItem(
                id=t.id,
                title=t.title,
                banner_url=t.banner_url if hasattr(t, 'banner_url') else None
            )
            for t in topics
        ]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_info": brand_info,
                "associated_topics": associated_topics
            },
            "timestamp": datetime.utcnow()
        }
    
    async def create_brand(
        self,
        db: AsyncSession,
        brand_in: BrandCreate,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        创建品牌（需管理员权限）
        
        Args:
            db: 数据库会话
            brand_in: 品牌创建数据
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            InvalidParameterException: 品牌名称已存在
        """
        # 权限检查
        self._check_admin_permission(role)

        try:
            # 创建品牌
            brand = await crud.create_brand(db, brand_in)
            brand_item = BrandItem.model_validate(brand)

            return {
                "code": 200,
                "message": "success",
                "data": brand_item,
                "timestamp": datetime.utcnow()
            }
        except DatabaseIntegrityException as e:
            # 转换为业务异常
            error_msg = str(e).lower()
            if "品牌名称已存在" in str(e) or "unique constraint" in error_msg or "brands_name_key" in error_msg:
                raise InvalidParameterException("品牌名称已存在", code=2002)
            raise

    async def get_brands_paginated(
        self,
        db: AsyncSession,
        page: int,
        size: int,
        sort: str,
        name: Optional[str],
        is_active: Optional[bool],
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        获取品牌列表（管理员分页）
        
        Args:
            db: 数据库会话
            page: 页码
            size: 每页数量
            sort: 排序字段
            name: 品牌名称筛选
            is_active: 是否激活筛选
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 查询品牌
        brands, total = await crud.get_brands_paginated(db, page, size, name, is_active)
        brand_items = [BrandItem.model_validate(b) for b in brands]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": brand_items,
                "total": total,
                "page": page,
                "size": size
            },
            "timestamp": datetime.utcnow()
        }
    
    async def get_brand_by_id(
        self,
        db: AsyncSession,
        brand_id: UUID,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        获取单个品牌（管理员）
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 品牌不存在
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 查询品牌
        brand = await crud.get_brand_by_id(db, brand_id)
        if not brand:
            raise NotFoundException("品牌不存在")
        
        brand_item = BrandItem.model_validate(brand)
        
        return {
            "code": 200,
            "message": "success",
            "data": brand_item,
            "timestamp": datetime.utcnow()
        }
    
    async def update_brand(
        self,
        db: AsyncSession,
        brand_id: UUID,
        brand_in: BrandUpdate,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        更新品牌（需管理员权限）
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            brand_in: 品牌更新数据
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 品牌不存在
            ConflictException: 品牌名称已存在
        """
        # 权限检查
        self._check_admin_permission(role)

        try:
            # 更新品牌
            brand = await crud.update_brand(db, brand_id, brand_in)
            brand_item = BrandItem.model_validate(brand)
        
            return {
                "code": 200,
                "message": "success",
                "data": brand_item,
                "timestamp": datetime.utcnow()
            }
        except DatabaseIntegrityException as e:
            # 转换为业务异常
            error_msg = str(e).lower()
            if "品牌名称已存在" in str(e) or "unique constraint" in error_msg or "brands_name_key" in error_msg:
                raise InvalidParameterException("品牌名称已存在", code=2002)
            raise

    async def delete_brand(
        self,
        db: AsyncSession,
        brand_id: UUID,
        hard_delete: bool,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        删除品牌（软删除需ADMIN，硬删除需SUPERADMIN）
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            hard_delete: 是否硬删除
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 品牌不存在
            InvalidParameterException: 品牌被引用无法删除
        """
        # 权限检查
        # 权限检查：统一使用_check_admin_permission（ADMIN和SUPERADMIN都可以）
        self._check_admin_permission(role)  # ✅ 移除hard_delete的特殊检查
        
        # 硬删除前检查引用关系
        if hard_delete:
            topic_count, room_count = await crud.check_brand_references(db, brand_id)
            if topic_count > 0 or room_count > 0:
                raise InvalidParameterException(
                    f"品牌被引用无法删除，专题引用数：{topic_count}，直播间引用数：{room_count}",
                    code=2003
                )
        
        # 删除品牌
        brand = await crud.delete_brand(db, brand_id, hard_delete)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": str(brand_id),
                "deleted": True,
                "hard_delete": hard_delete
            },
            "timestamp": datetime.utcnow()
        }
    
    async def upload_brand_logo(
        self,
        db: AsyncSession,
        brand_id: UUID,
        file: UploadFile,
        current_user_id: UUID,
        role: str
    ) -> str:
        """
        上传品牌Logo
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            file: 上传的文件
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            Logo的URL路径
            
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 品牌不存在
            HTTPException: 文件上传失败
        """
        # 1. 权限检查
        if role not in ["ADMIN", "SUPERADMIN"]:
            logger.warning(f"权限不足: user_id={str(current_user_id)[:8]}, role={role}")
            raise PermissionDeniedException("需要管理员权限")
        
        # 2. 验证品牌是否存在
        brand = await db.get(Brand, brand_id)
        if not brand:
            logger.warning(f"品牌不存在: brand_id={str(brand_id)[:8]}")
            raise NotFoundException("品牌不存在")
        
        # 3. 保存Logo文件
        from app.core.file_handler import FileHandler
        logo_url = await FileHandler.save_brand_logo(file, brand_id)
        
        # 4. 更新数据库中的logo_url
        brand.logo_url = logo_url
        await db.commit()
        await db.refresh(brand)
        
        logger.info(f"品牌Logo上传成功: brand_id={str(brand_id)[:8]}, logo_url={logo_url}")
        
        return logo_url
    
    # ==================== Brand_Topics Service方法 (3个) ====================
    
    async def batch_add_brand_topics(
        self,
        db: AsyncSession,
        brand_id: UUID,
        topic_ids: List[UUID],
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        批量关联专题到品牌
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            topic_ids: 专题ID列表
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 品牌不存在
            InvalidParameterException: 部分专题ID不存在
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 验证品牌存在
        brand = await crud.get_brand_by_id(db, brand_id)
        if not brand or not brand.is_active:
            raise NotFoundException("品牌不存在")
        
        # 批量验证专题ID
        if topic_ids:
            stmt = select(Topic.id).where(Topic.id.in_(topic_ids))
            result = await db.execute(stmt)
            existing_ids = set(result.scalars().all())
            invalid_ids = set(topic_ids) - existing_ids
            
            if invalid_ids:
                raise InvalidParameterException(
                    f"部分专题ID不存在: {[str(id) for id in invalid_ids]}"
                )
        
        # 执行批量关联
        added_count = await crud.batch_add_brand_topics(db, brand_id, topic_ids)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": str(brand_id),
                "added_count": added_count,
                "topic_ids": [str(id) for id in topic_ids]
            },
            "timestamp": datetime.utcnow()
        }
    
    async def delete_brand_topic(
        self,
        db: AsyncSession,
        brand_id: UUID,
        topic_id: UUID,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        解除单个品牌-专题关联
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            topic_id: 专题ID
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 关联关系不存在
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 删除关联
        success = await crud.delete_brand_topic(db, brand_id, topic_id)
        if not success:
            raise NotFoundException("品牌-专题关联关系不存在")
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": str(brand_id),
                "topic_id": str(topic_id),
                "deleted": True
            },
            "timestamp": datetime.utcnow()
        }
    
    async def get_brand_topics_paginated(
        self,
        db: AsyncSession,
        brand_id: UUID,
        page: int,
        size: int,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        获取品牌关联专题列表（管理员分页）
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            page: 页码
            size: 每页数量
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 品牌不存在
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 验证品牌存在
        brand = await crud.get_brand_by_id(db, brand_id)
        if not brand:
            raise NotFoundException("品牌不存在")
        
        # 查询关联专题
        topics, total = await crud.get_brand_topics_paginated(db, brand_id, page, size)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": topics,
                "total": total,
                "page": page,
                "size": size
            },
            "timestamp": datetime.utcnow()
        }
    
    async def get_brand_rooms_paginated(
        self,
        db: AsyncSession,
        brand_id: UUID,
        page: int,
        size: int,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        获取品牌关联直播间列表（管理员分页）
        
        Args:
            db: 数据库会话
            brand_id: 品牌ID
            page: 页码
            size: 每页数量
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 品牌不存在
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 验证品牌存在
        brand = await crud.get_brand_by_id(db, brand_id)
        if not brand:
            raise NotFoundException("品牌不存在")
        
        # 查询关联直播间
        rooms, total = await crud.get_brand_rooms_paginated(db, brand_id, page, size)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": rooms,
                "total": total,
                "page": page,
                "size": size
            },
            "timestamp": datetime.utcnow()
        }
    
    # ==================== Brand_Rooms Service方法 (3个) ====================
    
    async def bind_room_brands(
        self,
        db: AsyncSession,
        room_id: UUID,
        brand_ids: List[UUID],
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        为直播间绑定品牌（全量替换策略）

        权限：ADMIN/SUPERADMIN，或该房间 owner。
        可绑任意 is_active 品牌（支持品牌联动）。
        
        Args:
            db: 数据库会话
            room_id: 直播间ID
            brand_ids: 品牌ID列表（允许为空，表示清空绑定）
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 非管理员且非房主
            NotFoundException: 直播间不存在
            InvalidParameterException: 部分品牌ID不存在或已禁用
        """
        # 验证直播间存在
        stmt = select(LiveRoom).where(LiveRoom.id == room_id)
        result = await db.execute(stmt)
        room = result.scalar_one_or_none()
        if not room:
            raise NotFoundException("直播间不存在")

        self._check_admin_or_room_owner(room, current_user_id, role)
        
        # 批量验证品牌ID（is_active=True）
        if brand_ids:
            stmt = select(Brand.id).where(
                Brand.id.in_(brand_ids),
                Brand.is_active == True
            )
            result = await db.execute(stmt)
            existing_ids = set(result.scalars().all())
            invalid_ids = set(brand_ids) - existing_ids
            
            if invalid_ids:
                raise InvalidParameterException(
                    f"部分品牌ID不存在或已禁用: {[str(id) for id in invalid_ids]}"
                )
        
        # 执行绑定（全量替换）
        bound_ids = await crud.bind_room_brands(db, room_id, brand_ids)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "room_id": str(room_id),
                "brand_ids": [str(id) for id in bound_ids],
                "updated_at": datetime.utcnow()
            },
            "timestamp": datetime.utcnow()
        }
    
    async def get_room_brands_admin(
        self,
        db: AsyncSession,
        room_id: UUID,
        current_user_id: UUID,
        role: str
    ) -> dict:
        """
        获取直播间绑定的品牌（管理员）
        
        Args:
            db: 数据库会话
            room_id: 直播间ID
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            标准响应字典
        
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 直播间不存在
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 验证直播间存在
        stmt = select(LiveRoom).where(LiveRoom.id == room_id)
        result = await db.execute(stmt)
        room = result.scalar_one_or_none()
        if not room:
            raise NotFoundException("直播间不存在")
        
        # 查询品牌
        brands = await crud.get_room_brands(db, room_id)
        brand_items = [RoomBrandItem.model_validate(b) for b in brands]
        
        return {
            "code": 200,
            "message": "success",
            "data": brand_items,
            "timestamp": datetime.utcnow()
        }
    
    async def get_room_brands_for_tab(
        self,
        db: AsyncSession,
        room_id: UUID,
        include_topic_brands: bool,
        topic_id: Optional[UUID],
        current_user_id: Optional[UUID],
        role: Optional[str]
    ) -> dict:
        """
        获取直播间品牌Tab内容（公开）
        
        Args:
            db: 数据库会话
            room_id: 直播间ID
            include_topic_brands: 是否包含专题品牌
            topic_id: 专题ID（当include_topic_brands=True时必填）
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
        
        Returns:
            标准响应字典
        
        Raises:
            NotFoundException: 直播间不存在
            InvalidParameterException: 参数验证失败
        """
        # 验证直播间存在
        stmt = select(LiveRoom).where(LiveRoom.id == room_id)
        result = await db.execute(stmt)
        room = result.scalar_one_or_none()
        if not room:
            raise NotFoundException("直播间不存在")
        
        # 查询直播间品牌
        room_brands = await crud.get_room_brands_for_tab(db, room_id)
        room_brand_items = [RoomBrandItem.model_validate(b) for b in room_brands]
        
        # 如果需要包含专题品牌
        if include_topic_brands:
            if not topic_id:
                raise InvalidParameterException("include_topic_brands=True时，topic_id参数必填")
            
            # 验证专题存在
            stmt = select(Topic).where(Topic.id == topic_id)
            result = await db.execute(stmt)
            topic = result.scalar_one_or_none()
            if not topic:
                raise InvalidParameterException("专题不存在")
            
            # 查询专题关联的启用品牌（16-D5：过滤 is_active；勿误用 get_brand_with_topics(brand_id)）
            topic_brands = await crud.get_brands_by_topic(db, topic_id)
            topic_brand_items = [RoomBrandItem.model_validate(b) for b in topic_brands]
            
            # 返回结构化数据
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "room_brands": room_brand_items,
                    "topic_brands": topic_brand_items
                },
                "timestamp": datetime.utcnow()
            }
        
        # 默认只返回直播间品牌
        return {
            "code": 200,
            "message": "success",
            "data": room_brand_items,
            "timestamp": datetime.utcnow()
        }
