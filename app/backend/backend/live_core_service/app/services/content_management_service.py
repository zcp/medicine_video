"""
内容管理模块的Service层
负责业务逻辑编排、权限检查、事务控制
"""
from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime
import logging

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_management import Tag, Category
from app.core.file_handler import FileHandler
from app.schemas.content_management import (
    TagCreate, TagUpdate, TagItem, TagListResponse, TagAdminListResponse,
    TagResolveRequest, TagResolveData, TagResolveResponse,
    CategoryCreate, CategoryUpdate, CategoryItem, RoomCategoryItem, CategoryListResponse, CategoryAdminListResponse,
    SessionTagsSetRequest, SessionTagsSetResponse, SessionTagsListResponse,
    TagBriefItem, PaginatedData,
    LiveRoomCategoriesSetRequest, LiveRoomCategoriesSetResponse, LiveRoomCategoriesListResponse,
)
from app.crud import content_management as crud_content_management
from app.crud import room as crud_room
from app.crud import session as crud_session
from app.exceptions import NotFoundException, PermissionDeniedException, InvalidParameterException
from app.core.exceptions import DatabaseIntegrityException
from app.core.permissions import check_room_owner_or_admin, check_admin_permission, check_authenticated_user
from app.core.category_constants import is_test_category_name
from app.content_safety.service import check_scene_fields

logger = logging.getLogger(__name__)

# 场次标签数量上限（与 SessionTagsSetRequest.max_length 一致）
SESSION_TAGS_MAX = 5


class ContentManagementService:
    """内容管理Service层"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    
    def _check_write_permission(self, role: Optional[str]) -> None:
        """
        检查写权限（REGULAR、admin或superadmin）
        
        Args:
            role: 用户角色
            
        Raises:
            PermissionDeniedException: 如果无写权限
        """
        if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写，使用REGULAR而非USER
            self.logger.warning(f"权限不足: 需要写权限，当前角色={role}")
            raise PermissionDeniedException("需要登录后才能执行此操作")

    async def _assert_session_tag_write_access(
        self,
        db: AsyncSession,
        session_id: UUID,
        current_user_id: UUID,
        role: str,
    ) -> None:
        """
        校验场次存在且当前用户可写其标签（房主或 Admin）。

        写权限 = 场次所属房间 owner（live_rooms.user_id）或 ADMIN/SUPERADMIN。

        Args:
            db: 数据库会话
            session_id: 场次ID
            current_user_id: 当前用户ID
            role: 用户角色

        Raises:
            NotFoundException: 场次或直播间不存在
            PermissionDeniedException: 非房主且非 Admin
        """
        session = await crud_session.get(db, session_id)
        if session is None:
            raise NotFoundException("场次不存在")
        room = await crud_room.get(db, session.room_id)
        if room is None:
            raise NotFoundException("直播间不存在")
        check_room_owner_or_admin(room, current_user_id, role)
    
    def _check_tag_visibility(
        self,
        tag: Tag,
        current_user_id: Optional[UUID],
        role: Optional[str]
    ) -> None:
        """
        检查标签可见性
        
        如果标签is_active=False且用户不是管理员，抛出NotFoundException（404伪装）
        
        Args:
            tag: 标签对象
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            
        Raises:
            NotFoundException: 如果标签不可见
        """
        if not tag.is_active and role not in ['ADMIN', 'SUPERADMIN']:
            self.logger.warning(f"标签不可见: id={str(tag.id)[:8]}, is_active=False")
            raise NotFoundException("标签不存在")

    async def _validate_category_hierarchy(
        self,
        db: AsyncSession,
        data: Any,
        existing_category_id: Optional[UUID] = None,
    ) -> None:
        """
        P1-6: 分类树治理校验（阶段2 加固：子孙循环检测 + 有子分类禁改层级）。

        校验规则:
        1. 深度限制: 最多 2 层 (parent_id → 一级 → 二级)，禁止三级及以上
        2. 循环检测: parent_id 不能等于自身或自身任意子孙（阶段2 扩展）
        3. 父分类状态: 不能挂到已禁用的分类下
        4. 有 active 子分类的分类禁止调整层级（提升为一级 parent_id=None 不受限）（阶段2 新增）

        Raises:
            InvalidParameterException: 校验不通过时抛出
        """
        from app.models.content_management import Category as CatModel

        parent_id = getattr(data, 'parent_id', None)
        if parent_id is None:
            return

        # 规则 3: 父分类必须存在且已启用
        parent_stmt = select(CatModel).where(CatModel.id == parent_id)
        parent_result = await db.execute(parent_stmt)
        parent_cat = parent_result.scalar_one_or_none()
        if not parent_cat:
            raise InvalidParameterException(f"父分类不存在: {parent_id}", code=4001)
        if not parent_cat.is_active:
            raise InvalidParameterException(f"无法挂到已禁用的父分类下: {parent_cat.name}", code=4001)

        # 规则 1: 深度限制 — 父分类不能是二级分类（即 parent_cat.parent_id 不能非空）
        if parent_cat.parent_id is not None:
            raise InvalidParameterException(
                f"分类树最深为 2 层，不能挂到二级分类 '{parent_cat.name}' 下再形成三级",
                code=4001
            )

        # 规则 2: 循环检测 — 自身 + 全部启用子孙（inactive 子孙作为父已被规则 3 拒绝）
        if existing_category_id:
            if parent_id == existing_category_id:
                raise InvalidParameterException("分类不能将自己设为父分类", code=4001)
            subtree_ids = await crud_content_management.get_category_descendant_ids(db, existing_category_id)
            if parent_id in subtree_ids:
                raise InvalidParameterException(
                    "分类不能挂到其子孙分类下（会形成循环）", code=4001
                )

            # 规则 4: 有 active 子分类的分类禁止调整层级（防降级三层/树重组）
            # 仅当 parent_id 实际变更时校验；提升为一级（parent_id=None 已提前 return）不受限
            existing_stmt = select(CatModel).where(CatModel.id == existing_category_id)
            existing_cat = (await db.execute(existing_stmt)).scalar_one_or_none()
            if existing_cat is not None and existing_cat.parent_id != parent_id:
                child_count = (
                    await db.execute(
                        select(func.count())
                        .select_from(CatModel)
                        .where(
                            CatModel.parent_id == existing_category_id,
                            CatModel.is_active == True,
                        )
                    )
                ).scalar_one()
                if child_count > 0:
                    raise InvalidParameterException(
                        f"该分类下有 {child_count} 个启用子分类，请先迁移或停用子分类后再调整层级",
                        code=4001,
                    )
    
    # ========================================================================
    # Tags Service方法
    # ========================================================================
    
    async def get_tags_list(
        self,
        db: AsyncSession,
        current_user_id: Optional[UUID],
        role: Optional[str],
        q: Optional[str] = None,
        search_type: Optional[str] = None,
        include_inactive: bool = False,
    ) -> TagListResponse:
        """
        获取标签列表
        
        Args:
            db: 数据库会话
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            q: 关键词或主键 ID（可选）
            search_type: id | keyword（可选）
            include_inactive: 是否包含禁用标签（True 时需管理员权限）
            
        Returns:
            标签列表响应
            
        权限逻辑:
        - include_inactive=True 且非管理员/未登录时抛出 PermissionDeniedException（3002）
        - 管理员且 include_inactive=True 时查询全部；否则仅 is_active=True
        - 普通用户只能查询 is_active=True 的标签
        """
        if include_inactive and (current_user_id is None or role not in ['ADMIN', 'SUPERADMIN']):
            raise PermissionDeniedException("查询禁用标签需管理员权限")
        if role not in ['ADMIN', 'SUPERADMIN']:
            is_active = True
        else:
            is_active = None if include_inactive else True
        
        # 调用CRUD层
        tags = await crud_content_management.get_tags(db, is_active, current_user_id, role, q=q, search_type=search_type)
        
        # 构造响应
        response = TagListResponse(
            code=200,
            message="success",
            data=[TagItem.model_validate(tag) for tag in tags],
            timestamp=datetime.now()
        )
        
        self.logger.info(f"查询标签列表成功，返回{len(tags)}条记录")
        return response

    async def get_tags_paginated(
        self,
        db: AsyncSession,
        page: int,
        size: int,
        is_active: Optional[bool],
        current_user_id: UUID,
        role: str,
        q: Optional[str] = None,
        search_type: Optional[str] = None,
    ) -> TagAdminListResponse:
        """
        获取标签列表（管理员接口，分页）

        Args:
            db: 数据库会话
            page: 页码（从1开始）
            size: 每页数量
            is_active: 是否启用（可选）
            current_user_id: 当前用户ID
            role: 用户角色
            q: 关键词或主键 ID（可选）
            search_type: id | keyword（可选）

        Returns:
            标签管理员列表响应

        Raises:
            PermissionDeniedException: 权限不足
        """
        # 权限检查
        check_admin_permission(role)

        # 调用CRUD层
        tags, total = await crud_content_management.get_tags_paginated(
            db, page, size, is_active, current_user_id, role,
            q=q, search_type=search_type,
        )

        # 构造响应（沿用分类管理端的 PaginatedData 结构：{items,total,page,size}）
        response = TagAdminListResponse(
            code=200,
            message="success",
            data=PaginatedData[TagItem](
                total=total,
                page=page,
                size=size,
                items=[TagItem.model_validate(tag) for tag in tags]
            ),
            timestamp=datetime.now()
        )

        self.logger.info(f"查询标签列表成功（Admin），page={page}, size={size}, total={total}")
        return response

    async def create_tag(
        self,
        db: AsyncSession,
        tag_data: TagCreate,
        current_user_id: UUID,
        role: str
    ) -> TagItem:
        """
        创建标签
        
        Args:
            db: 数据库会话
            tag_data: 标签创建数据
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            创建的标签项
            
        Raises:
            PermissionDeniedException: 权限不足
            DatabaseIntegrityException: 标签名称已存在
        """
        try:
            # 权限检查
            check_admin_permission(role)
            
            # 调用CRUD层（V2：运营创建落 source=admin、created_by=current_user_id 溯源）
            tag = await crud_content_management.create_tag(
                db, tag_data, source="admin", created_by=current_user_id
            )
            
            # 提交事务
            await db.commit()
            
            # 刷新对象
            await db.refresh(tag)
            
            self.logger.info(f"创建标签成功: id={str(tag.id)[:8]}, user_id={str(current_user_id)[:8]}")
            return TagItem.model_validate(tag)
            
        except DatabaseIntegrityException as e:
            await db.rollback()
            raise  # 重新抛出，由Endpoint层处理
        except Exception as e:
            await db.rollback()
            self.logger.error(f"创建标签失败: {str(e)}")
            raise

    async def resolve_tag(
        self,
        db: AsyncSession,
        request_data: TagResolveRequest,
        current_user_id: UUID,
        role: str,
    ) -> TagResolveResponse:
        """
        解析或创建标签（V2 阶段 2）。

        已登录即可（MVP）；命中 active 复用（created=False）；软删同名 400 不复活；
        未命中则 source=user 新建（created=True）；并发唯一冲突回滚再查（幂等）。
        """
        check_authenticated_user(role)

        name = request_data.name  # Schema 已 strip

        # 内容安全（scene=tag_name / field=name）；block 抛 ContentSafetyBlockedException
        await check_scene_fields(
            db,
            scene="tag_name",
            field_values={"name": name},
            resource_type="tag",
            user_id=current_user_id,
        )

        existing = await crud_content_management.get_tag_by_name(db, name)
        if existing is not None:
            if not existing.is_active:
                raise InvalidParameterException("标签不可用")
            return TagResolveResponse(
                code=200,
                message="success",
                data=TagResolveData(
                    id=existing.id,
                    name=existing.name,
                    created=False,
                    source=getattr(existing, "source", None),
                ),
                timestamp=datetime.now(),
            )

        try:
            tag = await crud_content_management.create_tag(
                db,
                TagCreate(name=name, is_active=True),
                source="user",
                created_by=current_user_id,
            )
            await db.commit()
            await db.refresh(tag)
            self.logger.info(
                f"resolve 新建标签: id={str(tag.id)[:8]}, name={tag.name}, "
                f"user={str(current_user_id)[:8]}"
            )
            return TagResolveResponse(
                code=200,
                message="success",
                data=TagResolveData(
                    id=tag.id,
                    name=tag.name,
                    created=True,
                    source=tag.source,
                ),
                timestamp=datetime.now(),
            )
        except DatabaseIntegrityException:
            # 并发唯一冲突：再查一次返回已有（幂等）
            await db.rollback()
            raced = await crud_content_management.get_tag_by_name(db, name)
            if raced is not None and raced.is_active:
                return TagResolveResponse(
                    code=200,
                    message="success",
                    data=TagResolveData(
                        id=raced.id,
                        name=raced.name,
                        created=False,
                        source=getattr(raced, "source", None),
                    ),
                    timestamp=datetime.now(),
                )
            if raced is not None and not raced.is_active:
                raise InvalidParameterException("标签不可用")
            raise
        except Exception as e:
            await db.rollback()
            self.logger.error(f"resolve 标签失败: {str(e)}")
            raise
    
    async def update_tag(
        self,
        db: AsyncSession,
        tag_id: UUID,
        tag_data: TagUpdate,
        current_user_id: UUID,
        role: str
    ) -> TagItem:
        """
        更新标签
        
        Args:
            db: 数据库会话
            tag_id: 标签ID
            tag_data: 更新数据
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            更新后的标签项
            
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 标签不存在
            DatabaseIntegrityException: 标签名称已存在
        """
        try:
            # 权限检查
            check_admin_permission(role)
            
            # 调用CRUD层
            tag = await crud_content_management.update_tag(db, tag_id, tag_data)
            
            # 404检查
            if tag is None:
                raise NotFoundException("标签不存在")
            
            # 提交事务
            await db.commit()
            
            # 刷新对象
            await db.refresh(tag)
            
            self.logger.info(f"更新标签成功: id={str(tag_id)[:8]}, user_id={str(current_user_id)[:8]}")
            return TagItem.model_validate(tag)
            
        except DatabaseIntegrityException as e:
            await db.rollback()
            raise  # 重新抛出，由Endpoint层处理
        except Exception as e:
            await db.rollback()
            self.logger.error(f"更新标签失败: {str(e)}")
            raise
    
    async def delete_tag(
        self,
        db: AsyncSession,
        tag_id: UUID,
        current_user_id: UUID,
        role: str,
        force: bool = False,
    ) -> dict:
        """
        删除标签（软删除）
        
        Args:
            db: 数据库会话
            tag_id: 标签ID
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            删除结果字典
            
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 标签不存在
        """
        try:
            # 权限检查
            check_admin_permission(role)
            
            # 调用CRUD层
            success = await crud_content_management.delete_tag(db, tag_id)
            
            # 404检查
            if not success:
                raise NotFoundException("标签不存在")
            
            # 提交事务
            await db.commit()
            
            self.logger.info(f"删除标签成功: id={str(tag_id)[:8]}, user_id={str(current_user_id)[:8]}")
            return {"message": "删除成功"}
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"删除标签失败: {str(e)}")
            raise
    
    # ========================================================================
    # Categories Service方法
    # ========================================================================
    
    async def get_categories_list(
        self,
        db: AsyncSession,
        current_user_id: Optional[UUID],
        role: Optional[str],
        include_counts: bool = False,
    ) -> CategoryListResponse:
        """
        获取分类列表（公开接口，不分页）
        
        Args:
            db: 数据库会话
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            include_counts: 是否附加 expert_count 和 room_count
            
        Returns:
            分类列表响应
            
        权限逻辑:
        - 无需权限检查，自动过滤is_active=True
        """
        # 调用CRUD层
        categories = await crud_content_management.get_categories(
            db, current_user_id, role, include_counts=include_counts
        )
        
        # 构造响应
        response = CategoryListResponse(
            code=200,
            message="success",
            data=[CategoryItem.model_validate(category) for category in categories],
            timestamp=datetime.now()
        )
        
        self.logger.info(f"查询分类列表成功（公开），返回{len(categories)}条记录")
        return response
    
    async def get_categories_paginated(
        self,
        db: AsyncSession,
        page: int,
        size: int,
        is_active: Optional[bool],
        current_user_id: UUID,
        role: str,
        q: Optional[str] = None,
        search_type: Optional[str] = None,
        include_counts: bool = False,
    ) -> CategoryAdminListResponse:
        """
        获取分类列表（管理员接口，分页）
        
        Args:
            db: 数据库会话
            page: 页码（从1开始）
            size: 每页数量
            is_active: 是否启用（可选）
            current_user_id: 当前用户ID
            role: 用户角色
            q: 关键词或主键 ID（可选）
            search_type: id | keyword（可选）
            
        Returns:
            分类管理员列表响应
            
        Raises:
            PermissionDeniedException: 权限不足
        """
        # 权限检查
        check_admin_permission(role)
        
        # 调用CRUD层
        categories, total = await crud_content_management.get_categories_paginated(
            db, page, size, is_active, current_user_id, role,
            q=q, search_type=search_type, include_counts=include_counts
        )
        
        # 构造响应
        response = CategoryAdminListResponse(
            code=200,
            message="success",
            data=PaginatedData[CategoryItem](
                total=total,
                page=page,
                size=size,
                items=[CategoryItem.model_validate(category) for category in categories]
            ),
            timestamp=datetime.now()
        )
        
        self.logger.info(f"查询分类列表成功（Admin），page={page}, size={size}, total={total}")
        return response
    
    async def create_category(
        self,
        db: AsyncSession,
        category_data: CategoryCreate,
        current_user_id: UUID,
        role: str
    ) -> CategoryItem:
        """
        创建分类
        
        Args:
            db: 数据库会话
            category_data: 分类创建数据
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            创建的分类项
            
        Raises:
            PermissionDeniedException: 权限不足
            DatabaseIntegrityException: 分类名称已存在
        """
        try:
            # 权限检查
            check_admin_permission(role)

            # P1-6: 分类树治理校验
            await self._validate_category_hierarchy(db, category_data)

            # 阶段6B：标准名校验（standard=true 时 name 必须命中名录清单）
            self._validate_standard_category_name(category_data.name, category_data.standard)

            # K3: 测试前缀警告（仅提示，不阻断——避免打断并行开发）
            if is_test_category_name(category_data.name):
                self.logger.warning(
                    f"创建疑似测试分类: name={category_data.name}, "
                    f"user_id={str(current_user_id)[:8]}（仅提示，不阻断）"
                )

            # 调用CRUD层
            category = await crud_content_management.create_category(db, category_data)
            
            # 提交事务
            await db.commit()
            
            # 刷新对象
            await db.refresh(category)
            
            self.logger.info(f"创建分类成功: id={str(category.id)[:8]}, user_id={str(current_user_id)[:8]}")
            return CategoryItem.model_validate(category)
            
        except DatabaseIntegrityException as e:
            await db.rollback()
            raise  # 重新抛出，由Endpoint层处理
        except Exception as e:
            await db.rollback()
            self.logger.error(f"创建分类失败: {str(e)}")
            raise
    
    async def update_category(
        self,
        db: AsyncSession,
        category_id: UUID,
        category_data: CategoryUpdate,
        current_user_id: UUID,
        role: str
    ) -> CategoryItem:
        """
        更新分类
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            category_data: 更新数据
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            更新后的分类项
            
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 分类不存在
            DatabaseIntegrityException: 分类名称已存在
        """
        try:
            # 权限检查
            check_admin_permission(role)

            # P1-6: 分类树治理校验
            await self._validate_category_hierarchy(db, category_data, existing_category_id=category_id)

            # 阶段6B：标准名校验（改 name 时：请求显式 standard 优先，否则 DB 现有值）
            if category_data.name is not None:
                existing_cat = await crud_content_management.get_category_by_id(db, category_id)
                if existing_cat is not None:
                    effective_standard = (
                        category_data.standard
                        if category_data.standard is not None
                        else existing_cat.standard
                    )
                    self._validate_standard_category_name(category_data.name, effective_standard)

            # 调用CRUD层
            category = await crud_content_management.update_category(db, category_id, category_data)
            
            # 404检查
            if category is None:
                raise NotFoundException("分类不存在")
            
            # 提交事务
            await db.commit()
            
            # 刷新对象
            await db.refresh(category)
            
            self.logger.info(f"更新分类成功: id={str(category_id)[:8]}, user_id={str(current_user_id)[:8]}")
            return CategoryItem.model_validate(category)
            
        except DatabaseIntegrityException as e:
            await db.rollback()
            raise  # 重新抛出，由Endpoint层处理
        except Exception as e:
            await db.rollback()
            self.logger.error(f"更新分类失败: {str(e)}")
            raise
    
    async def delete_category(
        self,
        db: AsyncSession,
        category_id: UUID,
        current_user_id: UUID,
        role: str,
        force: bool = False,
        target_category_id: Optional[UUID] = None,
    ) -> dict:
        """
        删除分类（软删除；阶段1：删除闭环——引用安顿 + 级联停用子树）

        - 禁删规则：slug=="other" 的兜底分类禁止删除
        - 非 force + 有引用 → 409（结构化 references，阶段0 口径）
        - force = 确认级联（单事务）：专家/科室迁移到 target 或"其他"、
          房间关联迁移（去重）/解除、级联软删子树，返回迁移统计

        Args:
            db: 数据库会话
            category_id: 分类ID
            current_user_id: 当前用户ID
            role: 用户角色
            force: 确认级联（不跳过任何安顿步骤）
            target_category_id: 引用迁移目标（缺省用"其他"兜底分类）

        Returns:
            删除结果字典（force 时含 migrated 统计）

        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 分类不存在
            InvalidParameterException: 禁删兜底分类 / 迁移目标非法
        """
        try:
            # 权限检查
            check_admin_permission(role)

            # 1. 查询分类（404 + 禁删规则）
            category = await crud_content_management.get_category_by_id(db, category_id)
            if category is None:
                raise NotFoundException("分类不存在")
            if category.slug == "other":
                raise InvalidParameterException("兜底分类'其他'禁止删除，请迁移其引用后再处理", code=4001)

            # 2. 统一引用统计（阶段0 五类口径）
            refs = await crud_content_management.count_category_references(db, category_id)

            # 3. 非 force + 有引用 → 409（结构化 references）
            if refs.total > 0 and not force:
                warnings_msgs = []
                if refs.expert_all > 0:
                    warnings_msgs.append(
                        f"该分类下有 {refs.expert_all} 位专家引用（其中 {refs.expert_active} 位启用），"
                        f"停用后这些专家在前台按分类筛选时将无法命中"
                    )
                if refs.department_count > 0:
                    warnings_msgs.append(f"该分类下有 {refs.department_count} 个科室引用")
                if refs.room_count > 0:
                    warnings_msgs.append(f"该分类下有 {refs.room_count} 个直播间关联（live_room_categories），停用后这些关联在前台不可见")
                if refs.active_child_count > 0:
                    warnings_msgs.append(f"该分类下有 {refs.active_child_count} 个启用子分类，停用后将级联下线")
                self.logger.warning(
                    f"删除分类被阻止（有引用）: category_id={str(category_id)[:8]}, "
                    f"expert_all={refs.expert_all}, department={refs.department_count}, "
                    f"room={refs.room_count}, child={refs.active_child_count}"
                )
                return {
                    "blocked": True,
                    "message": "分类存在引用，默认禁止停用。请先迁移引用或使用 force=true 强制删除",
                    "references": {
                        "expert_all": refs.expert_all,
                        "expert_active": refs.expert_active,
                        "department_count": refs.department_count,
                        "room_count": refs.room_count,
                        "active_child_count": refs.active_child_count,
                    },
                    "warnings": warnings_msgs,
                }

            # 4. 无引用 → 单分类软删（原路径）
            if refs.total == 0:
                success = await crud_content_management.delete_category(db, category_id)
                if not success:
                    raise NotFoundException("分类不存在")
                await db.commit()
                self.logger.info(f"删除分类成功（无引用）: id={str(category_id)[:8]}")
                return {"message": "删除成功"}

            # 5. force = 确认级联：引用安顿 + 级联停用子树（单事务）
            # 5.1 解析迁移目标
            target_id = target_category_id
            if target_id is None:
                other_cat = await crud_content_management.get_category_by_slug(db, "other")
                if other_cat is None:
                    raise InvalidParameterException(
                        "兜底分类'其他'不存在，无法迁移引用——请先执行 seed 分类初始化", code=4001
                    )
                target_id = other_cat.id
            elif target_id == category_id:
                raise InvalidParameterException("迁移目标不能是分类自身", code=4001)
            else:
                target_cat = await crud_content_management.get_category_by_id(db, target_id)
                if target_cat is None or not target_cat.is_active:
                    raise InvalidParameterException("迁移目标分类不存在或已停用", code=4001)

            # 5.2 子树（含自身）
            subtree_ids = await crud_content_management.get_category_descendant_ids(db, category_id)

            # 5.3 迁移引用（专家/科室/房间，含去重）
            migrate_stats = await crud_content_management.migrate_category_references(
                db, subtree_ids, target_id
            )

            # 5.4 级联软删子树
            disabled_count = await crud_content_management.cascade_disable_category_tree(db, subtree_ids)

            # 5.5 提交
            await db.commit()

            self.logger.info(
                f"强制删除分类（引用已安顿）: id={str(category_id)[:8]}, "
                f"expert={migrate_stats['expert_count']}, department={migrate_stats['department_count']}, "
                f"room={migrate_stats['room_count']}, disabled={disabled_count}, target={str(target_id)[:8]}"
            )
            return {
                "message": "删除成功（引用已迁移）",
                "migrated": {
                    "expert_count": migrate_stats["expert_count"],
                    "department_count": migrate_stats["department_count"],
                    "room_count": migrate_stats["room_count"],
                },
                "disabled_category_count": disabled_count,
            }

        except Exception as e:
            await db.rollback()
            self.logger.error(f"删除分类失败: {str(e)}")
            raise

    def _validate_standard_category_name(self, name: str, standard: bool) -> None:
        """
        阶段6B：标准名校验。

        规则：
        - standard=true 时，name 必须命中名录标准名清单
          （category_constants.STANDARD_CATEGORY_NAMES）
        - standard=false（扩展科目）放行任意合规名

        Args:
            name: 分类名称（create/update 中实际生效的名称）
            standard: 生效的 standard 标记（请求显式值或 DB 现有值）

        Raises:
            InvalidParameterException: 标准科目名称不在名录清单中
        """
        if not standard:
            return
        from app.core.category_constants import STANDARD_CATEGORY_NAMES
        if name not in STANDARD_CATEGORY_NAMES:
            raise InvalidParameterException(
                f"标准分类名称 '{name}' 不在《医疗机构诊疗科目名录》标准清单中；"
                f"如为扩展科目请设置 standard=false",
                code=4001,
            )

    async def migrate_category(
        self,
        db: AsyncSession,
        category_id: UUID,
        target_category_id: UUID,
        scope: str = "all",
        current_user_id: UUID = None,
        role: str = None,
    ) -> dict:
        """
        迁移分类引用到目标分类（阶段3 独立工具端点；与删除闭环复用同一 crud 函数）。

        Args:
            db: 数据库会话
            category_id: 源分类ID（仅迁移其自身引用，不含子分类）
            target_category_id: 迁移目标分类ID
            scope: 迁移范围（experts/departments/rooms/all）
            current_user_id: 当前用户ID（审计日志）
            role: 用户角色（审计日志）

        Returns:
            {"expert_count", "department_count", "room_count"} 迁移统计

        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 分类不存在
            InvalidParameterException: 迁移目标非法（自身/不存在/停用/在子树内）
        """
        check_admin_permission(role)

        source = await crud_content_management.get_category_by_id(db, category_id)
        if source is None:
            raise NotFoundException("分类不存在")

        # target 校验：≠ source、存在且启用、∉ source 子树（防循环中间态）
        if target_category_id == category_id:
            raise InvalidParameterException("迁移目标不能是源分类自身", code=4001)
        target = await crud_content_management.get_category_by_id(db, target_category_id)
        if target is None or not target.is_active:
            raise InvalidParameterException("迁移目标分类不存在或已停用", code=4001)
        subtree_ids = await crud_content_management.get_category_descendant_ids(db, category_id)
        if target_category_id in subtree_ids:
            raise InvalidParameterException("迁移目标不能位于源分类子树内（会形成循环）", code=4001)

        stats = await crud_content_management.migrate_category_references(
            db, [category_id], target_category_id, scope=scope
        )
        await db.commit()

        self.logger.info(
            f"分类引用迁移: source={str(category_id)[:8]}, target={str(target_category_id)[:8]}, "
            f"scope={scope}, expert={stats['expert_count']}, department={stats['department_count']}, "
            f"room={stats['room_count']}"
        )
        return stats

    async def merge_categories(
        self,
        db: AsyncSession,
        source_id: UUID,
        target_id: UUID,
        attach_children: bool = False,
        dry_run: bool = False,
        current_user_id: UUID = None,
        role: str = None,
    ) -> dict:
        """
        合并分类（阶段4）：source 引用迁入 target 后软删 source，单事务。

        5 类数据处理（V1.1/V1.2 语义）：
        - 子分类：attach_children=false 挂到 target 下 / true 提升为一级
        - 专家：仅 category_id = source_id（源分类自身，不含子分类下的专家）→ target
        - 科室：category_id = source_id → target
        - 房间关联：source 行 → target（target 已关联去重，is_primary 保留 target 行）
        - 软删 source（引用清空后单行软删）
        问题 15 联动：统计"专家 category_id 与所属科室 category_id 不一致"数量提示运营
        （合并后专家/科室均迁至 target，不一致自然消除）

        Args:
            db: 数据库会话
            source_id: 源分类ID（合并后软删）
            target_id: 目标分类ID
            attach_children: 子分类处置（false=挂 target 下 / true=提升一级）
            dry_run: 预览模式（只统计不落库）
            current_user_id: 当前用户ID（审计日志）
            role: 用户角色

        Returns:
            {"dry_run", "expert_count", "department_count", "room_count",
             "child_count", "inconsistent_expert_count", "message"}

        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 分类不存在
            InvalidParameterException: 合并参数非法
        """
        check_admin_permission(role)

        source = await crud_content_management.get_category_by_id(db, source_id)
        if source is None:
            raise NotFoundException("源分类不存在")
        target = await crud_content_management.get_category_by_id(db, target_id)
        if target is None:
            raise NotFoundException("目标分类不存在")

        # 校验：≠自身、均启用、target≠"其他"、target ∉ source 子树
        if source_id == target_id:
            raise InvalidParameterException("源分类与目标分类不能相同", code=4001)
        if not source.is_active:
            raise InvalidParameterException("源分类已停用，无法合并", code=4001)
        if not target.is_active:
            raise InvalidParameterException("目标分类已停用", code=4001)
        if target.slug == "other":
            raise InvalidParameterException("不能合并到兜底分类'其他'", code=4001)
        subtree_ids = await crud_content_management.get_category_descendant_ids(db, source_id)
        if target_id in subtree_ids:
            raise InvalidParameterException("目标分类不能位于源分类子树内（会形成循环）", code=4001)
        # 目标为二级分类时，子分类挂载会形成三层 → 拒绝（attach_children=true 提升不受限）
        if not attach_children and target.parent_id is not None:
            raise InvalidParameterException(
                "目标分类为二级分类，子分类无法挂载（会形成三层）；请用 attach_children=true 提升为一级", code=4001
            )

        from app.models.content_management import LiveRoomCategory
        from app.models.experts import Expert
        from app.models.expert_departments import ExpertDepartment

        # ---- 统计（dry_run 与真实执行共用）----
        expert_stmt = (
            select(func.count()).select_from(Expert).where(Expert.category_id == source_id)
        )
        dept_stmt = (
            select(func.count()).select_from(ExpertDepartment)
            .where(ExpertDepartment.category_id == source_id)
        )
        room_stmt = (
            select(func.count()).select_from(LiveRoomCategory)
            .where(LiveRoomCategory.category_id == source_id)
        )
        child_stmt = (
            select(func.count()).select_from(Category)
            .where(Category.parent_id == source_id)
        )
        # 问题15：专家 category_id 与所属科室 category_id 不一致（源分类下）
        inconsistent_stmt = (
            select(func.count())
            .select_from(Expert)
            .join(ExpertDepartment, Expert.department_id == ExpertDepartment.id)
            .where(Expert.category_id == source_id, ExpertDepartment.category_id != source_id)
        )

        expert_count = (await db.execute(expert_stmt)).scalar_one()
        department_count = (await db.execute(dept_stmt)).scalar_one()
        room_count = (await db.execute(room_stmt)).scalar_one()
        child_count = (await db.execute(child_stmt)).scalar_one()
        inconsistent_expert_count = (await db.execute(inconsistent_stmt)).scalar_one()

        if dry_run:
            self.logger.info(
                f"分类合并预览: source={str(source_id)[:8]} → target={str(target_id)[:8]}, "
                f"expert={expert_count}, department={department_count}, room={room_count}, "
                f"child={child_count}, inconsistent={inconsistent_expert_count}"
            )
            return {
                "dry_run": True,
                "expert_count": expert_count,
                "department_count": department_count,
                "room_count": room_count,
                "child_count": child_count,
                "inconsistent_expert_count": inconsistent_expert_count,
                "message": f"预览：将合并 {expert_count} 位专家、{department_count} 个科室、"
                          f"{room_count} 个房间关联、{child_count} 个子分类"
                          + (f"，另有 {inconsistent_expert_count} 位专家科室分类不一致将被校正" if inconsistent_expert_count else ""),
            }

        # ---- 真实执行（单事务）----
        # 1. 子分类挂载/提升
        if child_count > 0:
            from sqlalchemy import update as sa_update
            await db.execute(
                sa_update(Category)
                .where(Category.parent_id == source_id)
                .values(parent_id=None if attach_children else target_id)
                .execution_options(synchronize_session=False)
            )
        # 2. 引用迁移（科室→专家→房间去重；复用阶段1/3 函数）
        migrate_stats = await crud_content_management.migrate_category_references(
            db, [source_id], target_id, scope="all"
        )
        # 3. 软删 source（引用已清空）
        await crud_content_management.delete_category(db, source_id)
        # 4. 提交
        await db.commit()

        self.logger.info(
            f"分类合并完成: source={str(source_id)[:8]} → target={str(target_id)[:8]}, "
            f"expert={expert_count}, department={department_count}, room={room_count}, "
            f"child={child_count}, inconsistent={inconsistent_expert_count}"
        )
        return {
            "dry_run": False,
            "expert_count": migrate_stats["expert_count"],
            "department_count": migrate_stats["department_count"],
            "room_count": migrate_stats["room_count"],
            "child_count": child_count,
            "inconsistent_expert_count": inconsistent_expert_count,
            "message": f"合并成功：{migrate_stats['expert_count']} 位专家、"
                      f"{migrate_stats['department_count']} 个科室、"
                      f"{migrate_stats['room_count']} 个房间关联已迁移，"
                      f"{child_count} 个子分类已{'提升为一级' if attach_children else '挂到目标分类下'}",
        }

    async def upload_category_icon(
        self,
        db: AsyncSession,
        category_id: UUID,
        file: UploadFile,
        current_user_id: UUID,
        role: str,
    ) -> CategoryItem:
        """上传/覆盖科室（分类）图标；权限 Admin；返回更新后的 CategoryItem。"""
        check_admin_permission(role)
        category = await crud_content_management.get_category_by_id(db, category_id)
        if category is None:
            raise NotFoundException("分类不存在")
        if category.icon and category.icon.startswith("/media/"):
            FileHandler.delete_old_category_icon(category.icon)
        url = await FileHandler.save_category_icon(file, category_id)
        updated = await crud_content_management.update_category(db, category_id, CategoryUpdate(icon=url))
        await db.commit()
        await db.refresh(updated)
        self.logger.info(f"上传科室图标成功: id={str(category_id)[:8]}, user_id={str(current_user_id)[:8]}")
        return CategoryItem.model_validate(updated)

    async def delete_category_icon(
        self,
        db: AsyncSession,
        category_id: UUID,
        current_user_id: UUID,
        role: str,
    ) -> dict:
        """删除科室（分类）图标（物理文件 + 将 icon 置为 NULL）；权限 Admin；无图片时也成功（幂等）。"""
        check_admin_permission(role)
        category = await crud_content_management.get_category_by_id(db, category_id)
        if category is None:
            raise NotFoundException("分类不存在")
        if category.icon and category.icon.startswith("/media/"):
            FileHandler.delete_old_category_icon(category.icon)
        await crud_content_management.update_category(db, category_id, CategoryUpdate(icon=None))
        await db.commit()
        self.logger.info(f"删除科室图标成功: id={str(category_id)[:8]}, user_id={str(current_user_id)[:8]}")
        return {"message": "删除成功"}

    async def get_category_by_id(
        self,
        db: AsyncSession,
        category_id: UUID,
        current_user_id: Optional[UUID],
        role: Optional[str]
    ) -> CategoryItem:
        """
        根据ID获取分类详情
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            
        Returns:
            分类项
            
        Raises:
            NotFoundException: 分类不存在
        """
        # 调用CRUD层
        category = await crud_content_management.get_category_by_id(db, category_id)
        
        # 404检查
        if category is None:
            raise NotFoundException("分类不存在")
        
        # 权限检查：如果分类is_active=False且用户不是管理员，返回404（404伪装）
        if not category.is_active and role not in ['ADMIN', 'SUPERADMIN']:
            raise NotFoundException("分类不存在")
        
        self.logger.info(f"获取分类详情成功: id={str(category_id)[:8]}")
        return CategoryItem.model_validate(category)
    
    # ========================================================================
    # Session_Tags Service方法
    # ========================================================================
    
    async def set_session_tags(
        self,
        db: AsyncSession,
        session_id: UUID,
        request_data: SessionTagsSetRequest,
        current_user_id: UUID,
        role: str
    ) -> SessionTagsSetResponse:
        """
        为场次设置标签
        
        Args:
            db: 数据库会话
            session_id: 场次ID
            request_data: 设置标签请求数据
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            设置标签响应
            
        Raises:
            PermissionDeniedException: 权限不足
            InvalidParameterException: 部分标签ID不存在
        """
        # 权限：场次标签写权限 = 房主（开播者）或 Admin（写库前断言，避免误 rollback / 误记 error）
        await self._assert_session_tag_write_access(db, session_id, current_user_id, role)
        try:
            # 业务验证（V2：tag_ids 0~5，空列表=清空语义，跳过校验避免 IN () 非法 SQL）
            existing_tags = []
            if request_data.tag_ids:
                # 数据关联治理（P1-2）：仅允许启用状态的标签关联场次
                # （与 set_session_experts "仅允许启用状态的专家关联场次" 语义对齐，
                #   消除"能设置但看不见"的体验断裂——软删标签前台不展示）
                tags_query = select(Tag).where(
                    Tag.id.in_(request_data.tag_ids),
                    Tag.is_active == True,
                )
                result = await db.execute(tags_query)
                existing_tags = result.scalars().all()

                if len(existing_tags) != len(request_data.tag_ids):
                    raise InvalidParameterException("部分标签ID不存在或已停用")
            
            # append 数量上限校验（V2）：与现有关联去重后 ≤ SESSION_TAGS_MAX
            if request_data.mode == "append" and request_data.tag_ids:
                existing_links = await crud_content_management.get_tags_by_session_id(
                    db, session_id
                )
                final_count = len(
                    {t.id for t in existing_links} | set(request_data.tag_ids)
                )
                if final_count > SESSION_TAGS_MAX:
                    raise InvalidParameterException(
                        f"场次标签最多 {SESSION_TAGS_MAX} 个"
                    )

            # 调用CRUD层
            tags = await crud_content_management.set_session_tags(
                db, session_id, request_data.tag_ids, request_data.mode
            )

            # commit 前序列化，避免 commit 后 ORM 过期触发懒加载（MissingGreenlet）
            tags_payload = [TagBriefItem.model_validate(tag) for tag in tags]

            # 提交事务
            await db.commit()
            
            # 构造响应
            response = SessionTagsSetResponse(
                code=200,
                message="success",
                data={
                    "session_id": str(session_id),
                    "mode": request_data.mode,
                    "tags": tags_payload
                },
                timestamp=datetime.now()
            )
            
            self.logger.info(f"为场次设置标签成功: session_id={str(session_id)[:8]}, mode={request_data.mode}, tag_count={len(tags)}")
            return response
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"为场次设置标签失败: {str(e)}")
            raise
    
    async def get_session_tags(
        self,
        db: AsyncSession,
        session_id: UUID,
        current_user_id: Optional[UUID],
        role: Optional[str]
    ) -> SessionTagsListResponse:
        """
        获取场次标签列表
        
        Args:
            db: 数据库会话
            session_id: 场次ID
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            
        Returns:
            场次标签列表响应
            
        权限逻辑:
        - 无需权限检查（公开接口）
        """
        # 调用CRUD层
        tags = await crud_content_management.get_tags_by_session_id(db, session_id)
        
        # 构造响应
        response = SessionTagsListResponse(
            code=200,
            message="success",
            data=[TagItem.model_validate(tag) for tag in tags],
            timestamp=datetime.now()
        )
        
        self.logger.info(f"获取场次标签列表成功: session_id={str(session_id)[:8]}, tag_count={len(tags)}")
        return response
    
    async def get_sessions_by_tags(
        self,
        db: AsyncSession,
        tag_ids: List[UUID],
        match_all: bool,
        current_user_id: Optional[UUID],
        role: Optional[str]
    ) -> List[UUID]:
        """
        根据标签查询场次ID列表
        
        Args:
            db: 数据库会话
            tag_ids: 标签ID列表
            match_all: 匹配模式（True=AND逻辑，False=OR逻辑）
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            
        Returns:
            场次ID列表
            
        权限逻辑:
        - 无需权限检查（公开接口）
        """
        # 调用CRUD层
        session_ids = await crud_content_management.get_sessions_by_tags(
            db, tag_ids, match_all
        )
        
        self.logger.info(f"根据标签查询场次成功: tag_count={len(tag_ids)}, match_all={match_all}, session_count={len(session_ids)}")
        return session_ids
    
    async def remove_session_tag(
        self,
        db: AsyncSession,
        session_id: UUID,
        tag_id: UUID,
        current_user_id: UUID,
        role: str,
        force: bool = False,
    ) -> dict:
        """
        删除场次与标签的关联
        
        Args:
            db: 数据库会话
            session_id: 场次ID
            tag_id: 标签ID
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            删除结果字典
            
        Raises:
            PermissionDeniedException: 权限不足
        """
        # 权限：场次标签写权限 = 房主（开播者）或 Admin（写库前断言，避免误 rollback / 误记 error）
        await self._assert_session_tag_write_access(db, session_id, current_user_id, role)
        try:
            # 调用CRUD层
            success = await crud_content_management.remove_session_tag(db, session_id, tag_id)
            
            # 提交事务
            await db.commit()
            
            self.logger.info(f"删除场次标签关联成功: session_id={str(session_id)[:8]}, tag_id={str(tag_id)[:8]}")
            return {"message": "删除成功"}
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"删除场次标签关联失败: {str(e)}")
            raise

    # ========================================================================
    # Live_Room_Categories Service方法
    # ========================================================================

    async def get_live_room_categories_list(
        self,
        db: AsyncSession,
        room_id: UUID,
        current_user_id: Optional[UUID],
        role: Optional[str],
    ) -> LiveRoomCategoriesListResponse:
        """
        获取某直播间的分类列表（公开）。
        若房间不存在则抛出 NotFoundException（2001）。
        """
        room = await crud_room.get(db, room_id)
        if room is None:
            raise NotFoundException("直播间不存在")
        lrcs = await crud_content_management.get_categories_by_room_id(db, room_id)
        return LiveRoomCategoriesListResponse(
            code=200,
            message="success",
            data=[
                RoomCategoryItem(**CategoryItem.model_validate(lrc.category).model_dump(), is_primary=lrc.is_primary)
                for lrc in lrcs
            ],
            timestamp=datetime.now(),
        )

    async def set_live_room_categories(
        self,
        db: AsyncSession,
        room_id: UUID,
        body: LiveRoomCategoriesSetRequest,
        current_user_id: UUID,
        role: str,
    ) -> LiveRoomCategoriesSetResponse:
        """
        批量设置某直播间的分类（仅 ADMIN 或 SUPERADMIN——分类为全局受控词汇）。
        房间不存在 2001；category_ids 中无效或未启用 4001。
        """
        # 权限检查：仅 ADMIN 或 SUPERADMIN（分类为全局受控词汇）
        room = await crud_room.get(db, room_id)
        if room is None:
            raise NotFoundException("直播间不存在")
        check_admin_permission(role)
        # 校验 category_ids 均在 categories 且 is_active=True（空列表时跳过 IN 查询，避免 PostgreSQL IN () 非法 SQL）
        requested = set(body.category_ids)
        if requested:
            result = await db.execute(select(Category).where(Category.id.in_(body.category_ids)))
            existing = result.scalars().all()
            active_ids = {c.id for c in existing if c.is_active}
            if requested - active_ids:
                raise InvalidParameterException("部分分类ID不存在或未启用")
        lrcs = await crud_content_management.set_live_room_categories(
            db, room_id, body.category_ids, body.mode, body.primary_category_id
        )
        # 在 commit 前序列化 ORM 为 Pydantic，避免 commit 后对象过期导致 model_validate 触发懒加载而 MissingGreenlet
        categories_payload = [
            RoomCategoryItem(**CategoryItem.model_validate(lrc.category).model_dump(), is_primary=lrc.is_primary)
            for lrc in lrcs
        ]
        await db.commit()
        return LiveRoomCategoriesSetResponse(
            code=200,
            message="success",
            data={
                "room_id": str(room_id),
                "mode": body.mode,
                "categories": categories_payload,
            },
            timestamp=datetime.now(),
        )

    async def delete_live_room_category(
        self,
        db: AsyncSession,
        room_id: UUID,
        category_id: UUID,
        current_user_id: UUID,
        role: str,
    ) -> dict:
        """删除某直播间的单个分类关联（仅 ADMIN 或 SUPERADMIN）。关联不存在 2001。P1-4: 删除主分类后自动递补。"""
        room = await crud_room.get(db, room_id)
        if room is None:
            raise NotFoundException("直播间不存在")
        check_admin_permission(role)

        # 删除前检查是否为主分类
        from app.models.content_management import LiveRoomCategory
        deleted_cat = await db.execute(
            select(LiveRoomCategory).where(
                LiveRoomCategory.room_id == room_id,
                LiveRoomCategory.category_id == category_id
            )
        )
        was_primary = deleted_cat.scalar_one_or_none()

        deleted = await crud_content_management.delete_live_room_category(db, room_id, category_id)
        if not deleted:
            raise NotFoundException("该直播间未关联此分类")

        # P1-4: 删除的是主分类 → 自动递补 created_at 最早的剩余分类
        if was_primary and was_primary.is_primary:
            next_primary = await db.execute(
                select(LiveRoomCategory).where(
                    LiveRoomCategory.room_id == room_id
                ).order_by(LiveRoomCategory.created_at.asc()).limit(1)
            )
            next_cat = next_primary.scalar_one_or_none()
            if next_cat:
                next_cat.is_primary = True
                await db.flush()
                self.logger.info(
                    f"自动递补主分类: room_id={str(room_id)[:8]}, "
                    f"new_primary={str(next_cat.category_id)[:8]}"
                )

        await db.commit()
        return {"message": "删除成功"}

    async def batch_set_live_room_categories(
        self,
        db: AsyncSession,
        room_ids: List[UUID],
        category_ids: List[UUID],
        mode: str,
        current_user_id: UUID,
        role: str,
    ) -> dict:
        """批量设置直播间分类（独立事务，部分成功语义）

        注意：当前为死代码——全项目无任何端点/调用方引用（2026-08-06 审查确认）。
        保留备用（未来批量运营场景），新增入口前需先补测试。
        """
        check_admin_permission(role)

        if category_ids:
            result = await db.execute(
                select(Category).where(Category.id.in_(category_ids), Category.is_active == True)
            )
            existing_ids = {c.id for c in result.scalars().all()}
            if set(category_ids) - existing_ids:
                raise InvalidParameterException("部分分类ID不存在或未启用")

        results = []
        success_count = 0
        failed_count = 0

        for room_id in room_ids:
            try:
                body = LiveRoomCategoriesSetRequest(
                    category_ids=category_ids,
                    primary_category_id=category_ids[0] if category_ids else None,
                    mode=mode,
                )
                await self.set_live_room_categories(
                    db=db, room_id=room_id, body=body,
                    current_user_id=current_user_id, role=role,
                )
                results.append({"room_id": str(room_id), "status": "success"})
                success_count += 1
            except Exception as e:
                await db.rollback()
                results.append({
                    "room_id": str(room_id),
                    "status": "failed",
                    "reason": str(e),
                })
                failed_count += 1

        return {
            "total_requested": len(room_ids),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        }

