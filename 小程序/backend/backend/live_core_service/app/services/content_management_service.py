"""
内容管理模块的Service层
负责业务逻辑编排、权限检查、事务控制
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_management import Tag, Category
from app.models.live_core import LiveRoom
from app.core.file_handler import FileHandler
from app.schemas.content_management import (
    TagCreate, TagUpdate, TagItem, TagListResponse,
    TagResolveRequest, TagResolveResponse, TagResolveData,
    CategoryCreate, CategoryUpdate, CategoryItem, CategoryListResponse, CategoryAdminListResponse,
    SessionTagsSetRequest, SessionTagsSetResponse, SessionTagsListResponse,
    TagBriefItem, PaginatedData,
    LiveRoomCategoriesSetRequest, LiveRoomCategoriesSetResponse, LiveRoomCategoriesListResponse,
)
from app.crud import content_management as crud_content_management
from app.crud import room as crud_room
from app.crud import session as crud_session
from app.exceptions import NotFoundException, PermissionDeniedException, InvalidParameterException
from app.core.exceptions import DatabaseIntegrityException
from app.content_safety.service import check_scene_fields

# 场次标签数量上限（与 SessionTagsSetRequest.max_length 一致）
SESSION_TAGS_MAX = 5

logger = logging.getLogger(__name__)


class ContentManagementService:
    """内容管理Service层"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # ========================================================================
    # 权限守卫函数
    # ========================================================================
    
    def _check_admin_permission(self, role: Optional[str]) -> None:
        """
        检查管理员权限（admin或superadmin）
        
        Args:
            role: 用户角色
            
        Raises:
            PermissionDeniedException: 如果不是管理员
        """
        if role not in ['ADMIN', 'SUPERADMIN']:
            self.logger.warning(f"权限不足: 需要管理员权限，当前角色={role}")
            raise PermissionDeniedException("需要管理员权限")
    
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

    def _check_admin_or_room_owner(
        self,
        room: LiveRoom,
        current_user_id: UUID,
        role: str,
    ) -> None:
        """
        场次标签写权限：Admin/SUPERADMIN 或房间 owner（开播者/房主）。
        """
        role_upper = (role or "").upper()
        if role_upper in ("ADMIN", "SUPERADMIN"):
            return
        if room.user_id == current_user_id:
            return
        self.logger.warning(
            f"权限不足: 需要管理员或房主，role={role}, "
            f"owner={str(room.user_id)[:8]}, current={str(current_user_id)[:8]}"
        )
        raise PermissionDeniedException("需要管理员权限或房间所有者权限")

    async def _assert_session_tag_write_access(
        self,
        db: AsyncSession,
        session_id: UUID,
        current_user_id: UUID,
        role: str,
    ) -> None:
        """校验场次存在且当前用户可写其标签（房主或 Admin）。"""
        session = await crud_session.get(db, session_id)
        if session is None:
            raise NotFoundException("场次不存在")
        room = await crud_room.get(db, session.room_id)
        if room is None:
            raise NotFoundException("直播间不存在")
        self._check_admin_or_room_owner(room, current_user_id, role)
    
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
            self._check_admin_permission(role)
            
            # 调用CRUD层（V2：运营创建标记 source=admin）
            tag = await crud_content_management.create_tag(
                db,
                tag_data,
                source="admin",
                created_by=current_user_id,
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

        已登录即可（MVP）；命中 active 复用；软删同名 400；未命中则 source=user 新建。
        """
        role_upper = (role or "").upper()
        if role_upper not in ("REGULAR", "ADMIN", "SUPERADMIN"):
            raise PermissionDeniedException("需要登录后才能执行此操作")

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
            self._check_admin_permission(role)
            
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
        role: str
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
            self._check_admin_permission(role)
            
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
        tree: bool = False,
    ) -> CategoryListResponse:
        """
        获取分类列表（公开接口，不分页）

        Args:
            db: 数据库会话
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            tree: 【V2新增】是否返回树形结构

        Returns:
            分类列表响应

        权限逻辑:
        - 无需权限检查，自动过滤is_active=True
        """
        # 调用CRUD层
        categories = await crud_content_management.get_categories(db, current_user_id, role, tree=tree)

        # 【V2】树形模式下，children 由 ORM relationship 自动填充，需过滤非活跃子分类
        if tree:
            for cat in categories:
                if cat.children:
                    cat.children = [c for c in cat.children if c.is_active]
                    cat.children.sort(key=lambda c: c.sort_order)

        # 构造响应
        response = CategoryListResponse(
            code=200,
            message="success",
            data=[CategoryItem.model_validate(category) for category in categories],
            timestamp=datetime.now()
        )

        self.logger.info(f"查询分类列表成功（公开，tree={tree}），返回{len(categories)}条记录")
        return response

    async def get_children_categories(
        self,
        db: AsyncSession,
        category_id: UUID,
    ) -> CategoryListResponse:
        """
        【V2新增】获取指定分类的子分类列表

        Args:
            db: 数据库会话
            category_id: 父分类ID

        Returns:
            子分类列表响应

        Raises:
            NotFoundException: 父分类不存在
        """
        # 验证父分类存在
        parent = await crud_content_management.get_category_by_id(db, category_id)
        if parent is None:
            raise NotFoundException("父分类不存在")

        # 查询子分类
        children = await crud_content_management.get_children_categories(db, category_id)

        response = CategoryListResponse(
            code=200,
            message="success",
            data=[CategoryItem.model_validate(c) for c in children],
            timestamp=datetime.now(),
        )
        self.logger.info(f"查询子分类列表成功: parent_id={str(category_id)[:8]}, count={len(children)}")
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
        parent_id: Optional[UUID] = None,
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
            parent_id: 【V2新增】按父分类ID过滤（可选）

        Returns:
            分类管理员列表响应

        Raises:
            PermissionDeniedException: 权限不足
        """
        # 权限检查
        self._check_admin_permission(role)

        # 调用CRUD层
        categories, total = await crud_content_management.get_categories_paginated(
            db, page, size, is_active, current_user_id, role,
            q=q, search_type=search_type, parent_id=parent_id,
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
            InvalidParameterException: 层级校验失败
            DatabaseIntegrityException: 分类名称已存在
        """
        try:
            # 权限检查
            self._check_admin_permission(role)

            # 【V2】层级校验
            if category_data.parent_id is not None:
                parent = await crud_content_management.get_category_by_id(db, category_data.parent_id)
                if parent is None:
                    raise InvalidParameterException("父分类不存在")
                if parent.parent_id is not None:
                    raise InvalidParameterException("不允许创建三级分类，父分类必须是一级分类")

            # 调用CRUD层
            category = await crud_content_management.create_category(db, category_data)
            
            # 提交事务
            await db.commit()

            # 刷新对象（会过期 ORM 属性包括 children）
            await db.refresh(category)

            # 重新查询带 selectinload 的对象，避免 model_validate 触发懒加载 MissingGreenlet
            category = await crud_content_management.get_category_by_id(db, category.id)

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
            InvalidParameterException: 层级校验失败
            DatabaseIntegrityException: 分类名称已存在
        """
        try:
            # 权限检查
            self._check_admin_permission(role)

            # 【V2】层级校验（仅当 parent_id 被显式传入时）
            update_data = category_data.model_dump(exclude_unset=True)
            if "parent_id" in update_data and update_data["parent_id"] is not None:
                new_parent_id = update_data["parent_id"]
                # 不能自引用
                if new_parent_id == category_id:
                    raise InvalidParameterException("不能将分类设为自身的子分类")
                # 父分类必须存在
                parent = await crud_content_management.get_category_by_id(db, new_parent_id)
                if parent is None:
                    raise InvalidParameterException("父分类不存在")
                # 父分类必须是一级分类（不能创建三级）
                if parent.parent_id is not None:
                    raise InvalidParameterException("不允许创建三级分类，父分类必须是一级分类")

            # 调用CRUD层
            category = await crud_content_management.update_category(db, category_id, category_data)
            
            # 404检查
            if category is None:
                raise NotFoundException("分类不存在")
            
            # 提交事务
            await db.commit()

            # 刷新对象（会过期 ORM 属性包括 children）
            await db.refresh(category)

            # 重新查询带 selectinload 的对象，避免 model_validate 触发懒加载 MissingGreenlet
            category = await crud_content_management.get_category_by_id(db, category_id)

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
        role: str
    ) -> dict:
        """
        删除分类（软删除）
        
        Args:
            db: 数据库会话
            category_id: 分类ID
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            删除结果字典
            
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 分类不存在
        """
        try:
            # 权限检查
            self._check_admin_permission(role)
            
            # 调用CRUD层
            success = await crud_content_management.delete_category(db, category_id)
            
            # 404检查
            if not success:
                raise NotFoundException("分类不存在")
            
            # 提交事务
            await db.commit()
            
            self.logger.info(f"删除分类成功: id={str(category_id)[:8]}, user_id={str(current_user_id)[:8]}")
            return {"message": "删除成功"}
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"删除分类失败: {str(e)}")
            raise

    async def upload_category_icon(
        self,
        db: AsyncSession,
        category_id: UUID,
        file: UploadFile,
        current_user_id: UUID,
        role: str,
    ) -> CategoryItem:
        """上传/覆盖科室（分类）图标；权限 Admin；返回更新后的 CategoryItem。"""
        self._check_admin_permission(role)
        category = await crud_content_management.get_category_by_id(db, category_id)
        if category is None:
            raise NotFoundException("分类不存在")
        if category.icon and category.icon.startswith("/media/"):
            FileHandler.delete_old_category_icon(category.icon)
        url = await FileHandler.save_category_icon(file, category_id)
        updated = await crud_content_management.update_category(db, category_id, CategoryUpdate(icon=url))
        await db.commit()
        await db.refresh(updated)
        # 重新查询带 selectinload 的对象，避免 model_validate 触发懒加载 MissingGreenlet
        updated = await crud_content_management.get_category_by_id(db, category_id)
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
        self._check_admin_permission(role)
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
        为场次设置标签。

        写权限：房间 owner（开播者/房主）或 ADMIN/SUPERADMIN。
        tag_ids：0～5；replace 空列表清空；append 后总数不得超过上限。
        """
        # 权限与参数校验在写库之前完成，避免误 rollback / 误记 error
        await self._assert_session_tag_write_access(
            db, session_id, current_user_id, role
        )

        if request_data.tag_ids:
            tags_query = select(Tag).where(Tag.id.in_(request_data.tag_ids))
            result = await db.execute(tags_query)
            existing_tags = result.scalars().all()
            if len(existing_tags) != len(request_data.tag_ids):
                raise InvalidParameterException("部分标签ID不存在")
            if any(not t.is_active for t in existing_tags):
                raise InvalidParameterException("部分标签不可用")

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

        try:
            tags = await crud_content_management.set_session_tags(
                db, session_id, request_data.tag_ids, request_data.mode
            )
            # commit 前序列化，避免 commit 后 ORM 过期触发懒加载
            tags_payload = [TagBriefItem.model_validate(tag) for tag in tags]
            await db.commit()

            response = SessionTagsSetResponse(
                code=200,
                message="success",
                data={
                    "session_id": str(session_id),
                    "mode": request_data.mode,
                    "tags": tags_payload,
                },
                timestamp=datetime.now(),
            )
            self.logger.info(
                f"为场次设置标签成功: session_id={str(session_id)[:8]}, "
                f"mode={request_data.mode}, tag_count={len(tags)}"
            )
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
        role: str
    ) -> dict:
        """
        删除场次与标签的关联。写权限同 set_session_tags（房主或 Admin）。
        """
        await self._assert_session_tag_write_access(
            db, session_id, current_user_id, role
        )

        try:
            await crud_content_management.remove_session_tag(db, session_id, tag_id)
            await db.commit()
            self.logger.info(
                f"删除场次标签关联成功: session_id={str(session_id)[:8]}, "
                f"tag_id={str(tag_id)[:8]}"
            )
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
        categories = await crud_content_management.get_categories_by_room_id(db, room_id)
        return LiveRoomCategoriesListResponse(
            code=200,
            message="success",
            data=[CategoryItem.model_validate(c) for c in categories],
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
        批量设置某直播间的分类（Admin）。
        房间不存在 2001；category_ids 中无效或未启用 4001。
        """
        self._check_admin_permission(role)
        room = await crud_room.get(db, room_id)
        if room is None:
            raise NotFoundException("直播间不存在")
        # 校验 category_ids 均在 categories 且 is_active=True（空列表时跳过 IN 查询，避免 PostgreSQL IN () 非法 SQL）
        requested = set(body.category_ids)
        if requested:
            result = await db.execute(select(Category).where(Category.id.in_(body.category_ids)))
            existing = result.scalars().all()
            active_ids = {c.id for c in existing if c.is_active}
            if requested - active_ids:
                raise InvalidParameterException("部分分类ID不存在或未启用")
        categories = await crud_content_management.set_live_room_categories(
            db, room_id, body.category_ids, body.mode, body.primary_category_id
        )
        # 在 commit 前序列化 ORM 为 Pydantic，避免 commit 后对象过期导致 model_validate 触发懒加载而 MissingGreenlet
        categories_payload = [CategoryItem.model_validate(c) for c in categories]
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
        """删除某直播间的单个分类关联（Admin）。关联不存在 2001。"""
        self._check_admin_permission(role)
        deleted = await crud_content_management.delete_live_room_category(db, room_id, category_id)
        if not deleted:
            raise NotFoundException("该直播间未关联此分类")
        await db.commit()
        return {"message": "删除成功"}

