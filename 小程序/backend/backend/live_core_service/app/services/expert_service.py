"""
专家模块 Service 层

本模块封装所有专家相关的业务逻辑，保持框架无关性。

职责：
- 业务逻辑验证（权限检查、状态检查等）
- 复杂查询的组装
- 事务管理

所有方法遵循安全异步异常处理原则。
"""

# 标准库导入
import csv
import io
import time
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

# 第三方库导入
from fastapi import UploadFile
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# 项目内导入
from app.crud import experts as crud
from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus
from app.schemas.experts import (
    ExpertCreate, ExpertUpdate, ExpertItem, FeaturedExpertItem,
    FollowedExpertItem, SessionExpertItem
)
from app.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    InvalidParameterException,
    DatabaseIntegrityException
)

# 配置日志
logger = logging.getLogger(__name__)

from app.core.category_constants import (
    ROOT_CATEGORIES,
    ALL_CATEGORY_NAMES_SORTED,
    DEPARTMENT_CATEGORY_MAP,
    OTHER_CATEGORY_NAME,
)


def _normalize_department_text(text_val: str) -> str:
    """清洗科室文本：去除末尾斜杠和首尾空白"""
    return text_val.rstrip("/.。、, ").strip()


def _match_broad_category(department_text: str) -> Optional[Tuple[str, str]]:
    """启发式匹配科室文本 → (matched_dept_name, matched_category_name)。

    优先级：
    1. DEPARTMENT_CATEGORY_MAP 精确别名
    2. ALL_CATEGORY_NAMES_SORTED 子串匹配（二级优先）
    """
    normalized = _normalize_department_text(department_text)
    if not normalized:
        return None

    mapped = DEPARTMENT_CATEGORY_MAP.get(normalized)
    if mapped:
        return (normalized, mapped)

    for cat_name in ALL_CATEGORY_NAMES_SORTED:
        if cat_name in normalized:
            return (normalized, cat_name)

    return None


def _normalize_csv_content_and_delimiter(content_str: str) -> tuple[str, str]:
    """
    去除 BOM、检测分隔符（逗号或制表符），返回 (归一化后的内容, 分隔符)。
    若首行用逗号拆只有一列且含制表符，则按制表符解析；否则按逗号。
    """
    text = content_str.lstrip("\ufeff")
    first_line = text.split("\n")[0] if text else ""
    if not first_line:
        return text, ","
    parts_comma = next(csv.reader(io.StringIO(first_line), delimiter=","), [])
    if len(parts_comma) == 1 and "\t" in first_line:
        return text, "\t"
    return text, ","


class ExpertService:
    """专家模块Service层"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化Service，存储数据库会话
        
        Args:
            db: 数据库会话对象
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        # 会话级科室缓存（避免 batch import 时每行全表扫描）
        self._dept_cache: Optional[List] = None
    
    # ==================== 权限守卫函数 ====================
    
    def _check_admin_permission(self, role: Optional[str]) -> None:
        """
        检查管理员权限（admin或superadmin）
        
        Args:
            role: 用户角色
            
        Raises:
            PermissionDeniedException: 如果不是管理员
        """
        if role not in ['ADMIN', 'SUPERADMIN']:  # 🚨 必须使用大写
            self.logger.warning(f"权限不足: 需要管理员权限，当前角色={role}")
            raise PermissionDeniedException("需要管理员权限")

    async def _check_admin_or_session_room_owner(
        self,
        session_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: Optional[str],
    ) -> None:
        """
        场次专家关联写权限：Admin/SUPERADMIN 或场次所属房间的 owner。
        可绑任意启用专家（支持多专家联动）；不限制 experts.user_id == me。
        """
        role_upper = (role or "").upper()
        if role_upper in ("ADMIN", "SUPERADMIN"):
            return

        stmt = (
            select(LiveRoom)
            .join(LiveSession, LiveSession.room_id == LiveRoom.id)
            .where(LiveSession.id == session_id)
        )
        result = await self.db.execute(stmt)
        room = result.scalar_one_or_none()
        if room is None:
            raise NotFoundException("场次不存在")
        if room.user_id == current_user_id:
            return

        self.logger.warning(
            f"权限不足: 非管理员且非房主, session_id={str(session_id)[:8]}, "
            f"user={str(current_user_id)[:8]}, owner={str(room.user_id)[:8]}"
        )
        raise PermissionDeniedException("需要管理员权限或房间所有者权限")
    
    def _check_user_resource_permission(
        self,
        resource_owner_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: Optional[str]
    ) -> None:
        """
        检查用户专属资源操作权限（关注/取消关注等，非专家写权限）
        
        Args:
            resource_owner_id: 资源所有者ID
            current_user_id: 当前用户ID
            role: 用户角色
            
        Raises:
            PermissionDeniedException: 如果无用户资源操作权限
        """
        if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:
            self.logger.warning(f"权限不足: 需要用户资源操作权限，当前角色={role}")
            raise PermissionDeniedException("需要登录后才能执行此操作")
        if role in ['ADMIN', 'SUPERADMIN']:
            return
        if resource_owner_id == current_user_id:
            return
        self.logger.warning(f"权限不足: 无权操作该资源，resource_owner={str(resource_owner_id)[:8]}, current_user={str(current_user_id)[:8]}")
        raise PermissionDeniedException("无权操作该资源")
    
    def _check_expert_visibility(
        self, 
        expert: Expert, 
        current_user_id: Optional[uuid.UUID], 
        role: Optional[str]
    ) -> None:
        """
        检查专家可见性
        
        如果专家不存在或已软删除，抛出NotFoundException（404伪装）
        
        Args:
            expert: 专家对象（可能为None）
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
            
        Raises:
            NotFoundException: 如果专家不存在或不可见
        """
        if expert is None:
            raise NotFoundException("专家不存在")
        
        # 软删除检查：is_active=False 表示已下架
        if not expert.is_active and role not in ['ADMIN', 'SUPERADMIN']:
            self.logger.warning(f"专家不可见: id={str(expert.id)[:8]}, is_active=False")
            raise NotFoundException("专家不存在")
    
    async def _resolve_department_and_category(
        self,
        department_text: Optional[str],
        category_id_raw: Optional[str] = None,
        category_name_raw: Optional[str] = None,
        source: str = "auto_match",
        department_id: Optional[uuid.UUID] = None,
    ) -> Tuple[Optional[uuid.UUID], Optional[uuid.UUID], Optional[str]]:
        """自适应匹配科室 + 分类。

        优先级：
        1. 显式 department_id
        2. 显式 category_id / category_name
        3. department_text 精确匹配 ExpertDepartment.name
        4. synonyms 匹配
        5. _match_broad_category 启发式
        6. UPSERT is_verified=false；失败归「其他」

        Returns:
            (department_id, category_id, department_display_name)
        """
        from app.crud import expert_departments as crud_dept
        from app.models.content_management import Category

        resolved_category_id: Optional[uuid.UUID] = None
        resolved_department_id: Optional[uuid.UUID] = None
        display_name: Optional[str] = None

        if department_id:
            dept = await crud_dept.get_department_by_id(self.db, department_id)
            if not dept or not dept.is_active:
                raise InvalidParameterException("科室不存在或已禁用", code=4001)
            resolved_department_id = dept.id
            resolved_category_id = dept.category_id
            display_name = dept.name
            if category_id_raw:
                try:
                    explicit_cat_id = uuid.UUID(category_id_raw)
                except (ValueError, TypeError):
                    raise InvalidParameterException(f"无效的 category_id 格式: {category_id_raw}", code=4001)
                cat_stmt = select(Category.id).where(
                    Category.id == explicit_cat_id,
                    Category.is_active == True,
                )
                cat_result = await self.db.execute(cat_stmt)
                if not cat_result.scalar_one_or_none():
                    raise InvalidParameterException(f"分类不存在或已禁用: {category_id_raw}", code=4001)
                resolved_category_id = explicit_cat_id
            return (resolved_department_id, resolved_category_id, display_name)

        if category_id_raw:
            try:
                explicit_cat_id = uuid.UUID(category_id_raw)
            except (ValueError, TypeError):
                raise InvalidParameterException(f"无效的 category_id 格式: {category_id_raw}", code=4001)
            cat_stmt = select(Category.id).where(
                Category.id == explicit_cat_id,
                Category.is_active == True,
            )
            cat_result = await self.db.execute(cat_stmt)
            if cat_result.scalar_one_or_none():
                resolved_category_id = explicit_cat_id
            else:
                raise InvalidParameterException(f"分类不存在或已禁用: {category_id_raw}", code=4001)
        elif category_name_raw:
            cat_stmt = select(Category.id).where(
                Category.name == category_name_raw,
                Category.is_active == True,
            )
            cat_result = await self.db.execute(cat_stmt)
            found = cat_result.scalar_one_or_none()
            if found:
                resolved_category_id = found
            else:
                raise InvalidParameterException(f"分类名称不存在或已禁用: {category_name_raw}", code=4001)

        if resolved_category_id and not department_text:
            return (None, resolved_category_id, None)

        if department_text:
            normalized = _normalize_department_text(department_text)
            if normalized:
                if self._dept_cache is None:
                    dept_list = await crud_dept.get_departments_paginated(
                        self.db, page=1, size=300, is_active=True
                    )
                    self._dept_cache, _ = dept_list
                all_depts = self._dept_cache

                matched_dept = None
                for dept in all_depts:
                    if dept.name == normalized:
                        matched_dept = dept
                        break

                if not matched_dept:
                    for dept in all_depts:
                        synonyms = dept.synonyms or []
                        if normalized in synonyms:
                            matched_dept = dept
                            break

                _heuristic: Optional[Tuple[str, str]] = None
                if not matched_dept:
                    _heuristic = _match_broad_category(normalized)
                    if _heuristic:
                        matched_dept_name, _matched_cat_name = _heuristic
                        for dept in all_depts:
                            if dept.name == matched_dept_name:
                                matched_dept = dept
                                break
                        if not matched_dept:
                            for dept in all_depts:
                                synonyms = dept.synonyms or []
                                if matched_dept_name in synonyms:
                                    matched_dept = dept
                                    break

                if matched_dept:
                    resolved_department_id = matched_dept.id
                    display_name = matched_dept.name
                    if not resolved_category_id:
                        resolved_category_id = matched_dept.category_id
                else:
                    heuristic_cat_name = _heuristic[1] if _heuristic else None
                    cat_stmt = select(Category.id).where(
                        Category.name == (heuristic_cat_name or OTHER_CATEGORY_NAME),
                        Category.is_active == True,
                    )
                    cat_result = await self.db.execute(cat_stmt)
                    fallback_cat_id = cat_result.scalar_one_or_none()

                    if not fallback_cat_id and heuristic_cat_name and heuristic_cat_name != OTHER_CATEGORY_NAME:
                        cat_stmt = select(Category.id).where(
                            Category.name == OTHER_CATEGORY_NAME,
                            Category.is_active == True,
                        )
                        cat_result = await self.db.execute(cat_stmt)
                        fallback_cat_id = cat_result.scalar_one_or_none()
                        self.logger.warning(
                            f"启发式分类名 '{heuristic_cat_name}' 不存在，回退到'{OTHER_CATEGORY_NAME}': "
                            f"department_text={department_text}"
                        )

                    if not fallback_cat_id and not resolved_category_id:
                        raise InvalidParameterException(
                            f"无法解析分类，且'{OTHER_CATEGORY_NAME}'兜底分类不存在——请先执行 seed.py",
                            code=4001,
                        )

                    from app.schemas.expert_departments import ExpertDepartmentCreate
                    new_dept_data = ExpertDepartmentCreate(
                        name=normalized,
                        category_id=resolved_category_id or fallback_cat_id,
                        synonyms=[],
                        is_verified=False,
                        source=source,
                    )
                    try:
                        new_dept = await crud_dept.create_department(self.db, new_dept_data)
                        await self.db.flush()
                        # 失效缓存
                        self._dept_cache = None
                        resolved_department_id = new_dept.id
                        display_name = new_dept.name
                        if not resolved_category_id:
                            resolved_category_id = new_dept.category_id
                        self.logger.info(
                            f"自动创建新科室: '{normalized}' (id={str(new_dept.id)[:8]}, "
                            f"category={heuristic_cat_name or OTHER_CATEGORY_NAME})"
                        )
                    except DatabaseIntegrityException:
                        await self.db.rollback()
                        existing = await crud_dept.get_department_by_name(self.db, normalized)
                        if existing:
                            resolved_department_id = existing.id
                            display_name = existing.name
                            resolved_category_id = resolved_category_id or existing.category_id
                        else:
                            raise

        if not resolved_category_id:
            cat_stmt = select(Category.id).where(
                Category.name == OTHER_CATEGORY_NAME,
                Category.is_active == True,
            )
            cat_result = await self.db.execute(cat_stmt)
            other_cat_id = cat_result.scalar_one_or_none()
            if not other_cat_id:
                raise InvalidParameterException(
                    f"无法解析分类，且'{OTHER_CATEGORY_NAME}'兜底分类不存在——请先执行 seed.py",
                    code=4001,
                )
            resolved_category_id = other_cat_id
            self.logger.warning(
                f"科室文本为空或无匹配，回退到'{OTHER_CATEGORY_NAME}': "
                f"department_text={department_text}, category_id_raw={category_id_raw}"
            )

        return (resolved_department_id, resolved_category_id, display_name)

    def _to_expert_item(self, expert: Expert) -> ExpertItem:
        """组装响应：含 department_name/category_name；过渡期回填 department。"""
        dept_name = None
        if getattr(expert, "department_ref", None) is not None:
            dept_name = expert.department_ref.name
        elif expert.department:
            dept_name = expert.department
        cat_name = expert.category.name if getattr(expert, "category", None) is not None else None
        item = ExpertItem.model_validate(expert)
        payload = item.model_dump()
        payload["department"] = dept_name or expert.department
        payload["department_name"] = dept_name
        payload["department_id"] = expert.department_id
        payload["category_id"] = expert.category_id
        payload["category_name"] = cat_name
        return ExpertItem.model_validate(payload)

    # ==================== 专家信息管理Service方法 ====================
    
    async def get_featured_experts(
        self,
        limit: int = 10
    ) -> List[FeaturedExpertItem]:
        """
        获取首页推荐专家列表
        
        Args:
            limit: 返回记录数限制（默认10，最大50）
        
        Returns:
            List[FeaturedExpertItem]: 推荐专家列表
        """
        if limit > 50:
            limit = 50
        
        experts = await crud.get_featured_experts(self.db, limit)
        result = [FeaturedExpertItem.model_validate(expert) for expert in experts]
        self.logger.info(f"查询推荐专家列表成功，返回{len(result)}条记录")
        return result
    
    async def get_expert_detail(
        self,
        expert_id: uuid.UUID,
        current_user_id: Optional[uuid.UUID],
        role: Optional[str]
    ) -> ExpertItem:
        """
        获取专家详情
        
        Args:
            expert_id: 专家唯一标识
            current_user_id: 当前用户ID（可选）
            role: 用户角色（可选）
        
        Returns:
            ExpertItem: 专家详情
        
        Raises:
            NotFoundException: 如果专家不存在或不可见
        """
        expert = await crud.get_expert(self.db, expert_id)
        self._check_expert_visibility(expert, current_user_id, role)
        
        result = ExpertItem.model_validate(expert)
        self.logger.info(f"查询专家详情成功: expert_id={str(expert_id)[:8]}")
        return result

    async def get_public_experts_list(
        self,
        page: int = 1,
        size: int = 50,
        keyword: Optional[str] = None,
        department: Optional[str] = None,
        hospital: Optional[str] = None,
        is_active: Optional[bool] = True,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取公共专家列表（分页，专家页）

        Args:
            page: 页码（从1开始）
            size: 每页记录数
            keyword: 关键词（姓名/医院/科室/简介）
            department: 科室筛选
            hospital: 医院筛选
            is_active: 启用状态筛选，默认仅返回启用专家
            sort: 排序参数

        Returns:
            Dict[str, Any]: 包含分页信息与专家列表

        Raises:
            InvalidParameterException: 如果分页参数非法
        """
        if page < 1:
            raise InvalidParameterException("page 必须大于等于 1", code=4001)
        if size < 1:
            raise InvalidParameterException("size 必须大于等于 1", code=4001)
        if size > 100:
            raise InvalidParameterException("size 超过最大值 100", code=4001)

        skip = (page - 1) * size
        experts, total = await crud.get_public_experts_multi_and_total(
            self.db,
            skip=skip,
            limit=size,
            keyword=keyword,
            department=department,
            hospital=hospital,
            is_active=is_active,
            sort=sort,
        )

        items = [ExpertItem.model_validate(expert) for expert in experts]
        result = {
            "total": total,
            "page": page,
            "size": size,
            "has_more": (skip + len(items)) < total,
            "items": items,
        }

        self.logger.info(
            "查询公共专家列表成功，page=%s, size=%s, total=%s",
            page,
            size,
            total,
        )
        return result
    
    async def get_expert_sessions(
        self,
        expert_id: uuid.UUID,
        page: int = 1,
        size: int = 10,
        role: Optional[str] = None,
        current_user_id: Optional[uuid.UUID] = None,
        role_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取专家详情及其参与的所有直播场次（分页）
        
        Args:
            expert_id: 专家唯一标识
            page: 页码（从1开始）
            size: 每页记录数
            role: 专家角色筛选（可选）
            current_user_id: 当前用户ID（可选）
            role_user: 用户角色（可选）
        
        Returns:
            Dict[str, Any]: 包含专家信息和场次列表的响应
        
        Raises:
            NotFoundException: 如果专家不存在或不可见
        """
        # 查询专家
        expert = await crud.get_expert(self.db, expert_id)
        self._check_expert_visibility(expert, current_user_id, role_user)
        
        # 计算分页
        skip = (page - 1) * size
        
        # 查询场次
        session_experts, total = await crud.get_expert_sessions(
            self.db, expert_id, role, skip, size
        )
        
        # 构造响应
        sessions_items = []
        for se in session_experts:
            session = se.session
            room = session.room if hasattr(session, 'room') else None
            
            session_item = {
                "id": str(session.id),
                "room_title": room.title if room else None,
                "role": se.role,
                "sort_order": se.sort_order,
                "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
                "start_time": session.start_time.isoformat() + "Z" if session.start_time else None,
                "cover_url": room.cover_url if room else None
            }
            sessions_items.append(session_item)
        
        result = {
            "expert_info": ExpertItem.model_validate(expert),
            "sessions": {
                "total": total,
                "page": page,
                "size": size,
                "items": sessions_items
            }
        }
        
        self.logger.info(f"查询专家场次列表成功: expert_id={str(expert_id)[:8]}, total={total}")
        return result
    
    async def create_expert(
        self,
        expert_data: ExpertCreate,
        current_user_id: uuid.UUID,
        role: str
    ) -> ExpertItem:
        """
        创建专家
        
        Args:
            expert_data: 专家创建数据
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            ExpertItem: 创建的专家对象
        
        Raises:
            PermissionDeniedException: 如果无管理员权限
            InvalidParameterException: 如果user_id已绑定到其他专家档案
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 业务验证：如果提供了user_id，检查是否已被绑定
        if expert_data.user_id:
            existing_expert = await crud.get_expert_by_user_id(self.db, expert_data.user_id)
            if existing_expert:
                raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)

        # 融合方案：department 文本或 department_id → 自适应解析
        dept_text = getattr(expert_data, "department", None)
        dept_id = getattr(expert_data, "department_id", None)
        cat_id = getattr(expert_data, "category_id", None)
        if (dept_text and str(dept_text).strip()) or dept_id or cat_id:
            resolved_dept_id, resolved_cat_id, display_name = await self._resolve_department_and_category(
                department_text=(dept_text.strip() if dept_text else None),
                category_id_raw=str(cat_id) if cat_id else None,
                source="manual_create",
                department_id=dept_id,
            )
            expert_data.department_id = resolved_dept_id
            expert_data.category_id = resolved_cat_id
            if display_name:
                expert_data.department = display_name
        else:
            from app.models.content_management import Category
            cat_stmt = select(Category.id).where(
                Category.name == OTHER_CATEGORY_NAME,
                Category.is_active == True,
            )
            cat_result = await self.db.execute(cat_stmt)
            other_cat_id = cat_result.scalar_one_or_none()
            if other_cat_id:
                expert_data.category_id = other_cat_id
        
        try:
            # 调用CRUD层
            expert = await crud.create_expert(self.db, expert_data)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(expert)
            
            result = self._to_expert_item(expert)
            self.logger.info(f"创建专家成功: id={str(expert.id)[:8]}, user_id={str(current_user_id)[:8]}")
            return result
        except DatabaseIntegrityException as e:
            await self.db.rollback()
            raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"创建专家失败: {str(e)}")
            raise
    
    async def get_experts_list(
        self,
        page: int = 1,
        size: int = 10,
        name: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_active: Optional[bool] = None,
        hospital: Optional[str] = None,
        sort: Optional[str] = None,
        current_user_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取专家列表（分页，管理员接口）
        
        Args:
            page: 页码（从1开始）
            size: 每页记录数
            name: 专家姓名筛选（模糊匹配）
            is_featured: 是否推荐筛选
            is_active: 是否启用筛选（用于 Admin 列表按启用状态过滤）
            hospital: 医院筛选（模糊匹配）
            sort: 排序参数
            current_user_id: 当前用户ID（可选）
            role: 用户角色
        
        Returns:
            Dict[str, Any]: 包含专家列表和分页信息的响应
        
        Raises:
            PermissionDeniedException: 如果无管理员权限
        """
        # 权限检查
        self._check_admin_permission(role)
        
        # 计算分页
        skip = (page - 1) * size
        
        # 调用CRUD层
        experts, total = await crud.get_experts_multi_and_total(
            self.db, skip, size, name, is_featured, is_active, hospital, sort
        )
        
        # 构造响应
        result = {
            "total": total,
            "page": page,
            "size": size,
            "items": [ExpertItem.model_validate(expert) for expert in experts]
        }
        
        self.logger.info(f"查询专家列表成功（Admin），page={page}, size={size}, total={total}")
        return result
    
    async def batch_import_experts_from_csv(
        self,
        file_content: bytes,
        skip_duplicates: bool = False,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从 CSV 文件批量创建专家；错误隔离、可选去重、结果统计
        
        Args:
            file_content: CSV 文件内容（字节）
            skip_duplicates: 是否跳过已存在记录（按 name+hospital 去重）
            role: 用户角色（用于权限检查）
            
        Returns:
            Dict: 与 BatchImportExpertsResult 结构一致
        """
        self._check_admin_permission(role)
        
        start_time = time.time()
        total = success = failed = skipped = 0
        created_expert_ids: List[uuid.UUID] = []
        failed_rows: List[Dict[str, Any]] = []
        skipped_rows: List[Dict[str, Any]] = []
        
        try:
            content_str = file_content.decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidParameterException("文件必须为 UTF-8 编码", code=4001)
        
        content_str, delimiter = _normalize_csv_content_and_delimiter(content_str)
        reader = csv.DictReader(io.StringIO(content_str), delimiter=delimiter)
        raw_fieldnames = reader.fieldnames or []
        fieldnames = [f.strip() for f in raw_fieldnames]
        reader.fieldnames = fieldnames
        if "name" not in fieldnames:
            raise InvalidParameterException("CSV 表头至少需含 name 列", code=4001)
        
        optional_cols = ["title", "hospital", "department", "expertise_areas", "bio", "avatar_url", "is_featured", "sort_order", "is_active"]
        
        for row_num, row in enumerate(reader, start=2):
            total += 1
            row_data = {k: v.strip() if isinstance(v, str) else v for k, v in row.items() if v}
            row_summary = {k: v for k, v in row_data.items() if k in fieldnames}
            
            try:
                name = row_data.get("name", "").strip()
                if not name:
                    raise ValueError("name 为必填列")
                
                if skip_duplicates:
                    hospital_val = row_data.get("hospital", "") or None
                    existing, _ = await crud.get_experts_multi_and_total(
                        self.db, skip=0, limit=1,
                        name=name, hospital=hospital_val
                    )
                    if existing:
                        skipped += 1
                        skipped_rows.append({"row": row_num, "data": row_summary, "reason": "已存在"})
                        continue
                
                expert_data = ExpertCreate(
                    name=name,
                    title=row_data.get("title") or None,
                    hospital=row_data.get("hospital") or None,
                    department=row_data.get("department") or None,
                    expertise_areas=row_data.get("expertise_areas") or None,
                    bio=row_data.get("bio") or None,
                    avatar_url=row_data.get("avatar_url") or None,
                    is_featured=row_data.get("is_featured", "false").lower() in ("true", "1"),
                    sort_order=int(row_data["sort_order"]) if row_data.get("sort_order") else 0,
                    is_active=row_data.get("is_active", "true").lower() not in ("false", "0")
                )

                resolved_dept_id, resolved_cat_id, display_name = await self._resolve_department_and_category(
                    department_text=expert_data.department,
                    category_id_raw=row_data.get("category_id") or None,
                    category_name_raw=row_data.get("category_name") or None,
                    source="csv_import",
                )
                expert_data.department_id = resolved_dept_id
                expert_data.category_id = resolved_cat_id
                if display_name:
                    expert_data.department = display_name
                
                expert = await crud.create_expert(self.db, expert_data)
                await self.db.commit()
                success += 1
                if len(created_expert_ids) < 100:
                    created_expert_ids.append(str(expert.id))
                    
            except Exception as e:
                failed += 1
                failed_rows.append({"row": row_num, "data": row_summary, "error": str(e)})
                await self.db.rollback()
                continue
        
        processing_time = round(time.time() - start_time, 2)
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "created_expert_ids": created_expert_ids,
            "failed_rows": failed_rows,
            "skipped_rows": skipped_rows,
            "processing_time": processing_time
        }

    async def batch_import_experts_from_csv_optimized(
        self,
        file_content: bytes,
        skip_duplicates: bool = False,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从 CSV 文件批量创建专家（优化实现）：单事务 + 每行 savepoint，一次 commit。
        错误隔离、可选去重、结果统计；与 batch_import_experts_from_csv 返回结构一致。
        """
        self._check_admin_permission(role)

        start_time = time.time()
        total = success = failed = skipped = 0
        created_expert_ids: List[str] = []
        failed_rows: List[Dict[str, Any]] = []
        skipped_rows: List[Dict[str, Any]] = []

        try:
            content_str = file_content.decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidParameterException("文件必须为 UTF-8 编码", code=4001)

        content_str, delimiter = _normalize_csv_content_and_delimiter(content_str)
        reader = csv.DictReader(io.StringIO(content_str), delimiter=delimiter)
        raw_fieldnames = reader.fieldnames or []
        fieldnames = [f.strip() for f in raw_fieldnames]
        reader.fieldnames = fieldnames
        if "name" not in fieldnames:
            raise InvalidParameterException("CSV 表头至少需含 name 列", code=4001)

        for row_num, row in enumerate(reader, start=2):
            total += 1
            row_data = {k: v.strip() if isinstance(v, str) else v for k, v in row.items() if v}
            row_summary = {k: v for k, v in row_data.items() if k in fieldnames}

            try:
                name = row_data.get("name", "").strip()
                if not name:
                    raise ValueError("name 为必填列")

                if skip_duplicates:
                    hospital_val = row_data.get("hospital", "") or None
                    existing, _ = await crud.get_experts_multi_and_total(
                        self.db, skip=0, limit=1,
                        name=name, hospital=hospital_val
                    )
                    if existing:
                        skipped += 1
                        skipped_rows.append({"row": row_num, "data": row_summary, "reason": "已存在"})
                        continue

                expert_data = ExpertCreate(
                    name=name,
                    title=row_data.get("title") or None,
                    hospital=row_data.get("hospital") or None,
                    department=row_data.get("department") or None,
                    expertise_areas=row_data.get("expertise_areas") or None,
                    bio=row_data.get("bio") or None,
                    avatar_url=row_data.get("avatar_url") or None,
                    is_featured=row_data.get("is_featured", "false").lower() in ("true", "1"),
                    sort_order=int(row_data["sort_order"]) if row_data.get("sort_order") else 0,
                    is_active=row_data.get("is_active", "true").lower() not in ("false", "0")
                )

                nested = await self.db.begin_nested()
                try:
                    resolved_dept_id, resolved_cat_id, display_name = await self._resolve_department_and_category(
                        department_text=expert_data.department,
                        category_id_raw=row_data.get("category_id") or None,
                        category_name_raw=row_data.get("category_name") or None,
                        source="csv_import",
                    )
                    expert_data.department_id = resolved_dept_id
                    expert_data.category_id = resolved_cat_id
                    if display_name:
                        expert_data.department = display_name
                    expert = await crud.create_expert(self.db, expert_data)
                    expert_id_str = str(expert.id)
                    success += 1
                    if len(created_expert_ids) < 100:
                        created_expert_ids.append(expert_id_str)
                except Exception:
                    await nested.rollback()
                    raise

            except Exception as e:
                failed += 1
                failed_rows.append({"row": row_num, "data": row_summary, "error": str(e)})
                continue

        await self.db.commit()

        processing_time = round(time.time() - start_time, 2)
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "created_expert_ids": created_expert_ids,
            "failed_rows": failed_rows,
            "skipped_rows": skipped_rows,
            "processing_time": processing_time
        }

    async def update_expert(
        self,
        expert_id: uuid.UUID,
        expert_data: ExpertUpdate,
        current_user_id: uuid.UUID,
        role: str
    ) -> ExpertItem:
        """
        更新专家信息
        
        Args:
            expert_id: 专家唯一标识
            expert_data: 专家更新数据（部分更新）
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            ExpertItem: 更新后的专家对象
        
        Raises:
            PermissionDeniedException: 如果无管理员权限
            NotFoundException: 如果专家不存在
            InvalidParameterException: 如果user_id已绑定到其他专家档案
        """
        # 权限检查
        self._check_admin_permission(role)
        
        try:
            update_fields = expert_data.model_dump(exclude_unset=True)
            if any(k in update_fields for k in ("department", "department_id", "category_id")):
                resolved_dept_id, resolved_cat_id, display_name = await self._resolve_department_and_category(
                    department_text=update_fields.get("department"),
                    category_id_raw=str(update_fields["category_id"]) if update_fields.get("category_id") else None,
                    source="manual_update",
                    department_id=update_fields.get("department_id"),
                )
                expert_data.department_id = resolved_dept_id
                expert_data.category_id = resolved_cat_id
                if display_name:
                    expert_data.department = display_name

            # 调用CRUD层
            expert = await crud.update_expert(self.db, expert_id, expert_data)
            
            # 404检查
            if expert is None:
                raise NotFoundException("专家不存在")
            
            # 业务验证：如果更新了user_id，检查是否已被其他专家绑定
            if expert_data.user_id and expert_data.user_id != expert.user_id:
                existing_expert = await crud.get_expert_by_user_id(self.db, expert_data.user_id)
                if existing_expert and existing_expert.id != expert_id:
                    raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(expert)
            
            result = self._to_expert_item(expert)
            self.logger.info(f"更新专家成功: id={str(expert_id)[:8]}")
            return result
        except DatabaseIntegrityException as e:
            await self.db.rollback()
            raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"更新专家失败: {str(e)}")
            raise
    
    async def delete_expert(
        self,
        expert_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str
    ) -> Dict[str, Any]:
        """
        删除专家（软删除）
        
        Args:
            expert_id: 专家唯一标识
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            Dict[str, Any]: 删除结果
        
        Raises:
            PermissionDeniedException: 如果无管理员权限
            NotFoundException: 如果专家不存在
        """
        # 权限检查
        self._check_admin_permission(role)
        
        try:
            # 调用CRUD层
            success = await crud.delete_expert(self.db, expert_id)
            
            # 404检查
            if not success:
                raise NotFoundException("专家不存在")
            
            # 提交事务
            await self.db.commit()
            
            result = {"id": str(expert_id), "status": "deleted"}
            self.logger.warning(f"删除专家成功（软删除）: id={str(expert_id)[:8]}, user_id={str(current_user_id)[:8]}")
            return result
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"删除专家失败: {str(e)}")
            raise
    
    # ==================== 专家关注Service方法 ====================
    
    async def follow_expert(
        self,
        expert_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str
    ) -> Dict[str, Any]:
        """
        关注专家
        
        Args:
            expert_id: 专家唯一标识
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            Dict[str, Any]: 关注结果
        
        Raises:
            PermissionDeniedException: 如果无用户资源操作权限
            NotFoundException: 如果专家不存在
            InvalidParameterException: 如果已关注该专家
        """
        # 权限检查
        self._check_user_resource_permission(current_user_id, current_user_id, role)
        
        try:
            # 检查专家是否存在且可见
            expert = await crud.get_expert(self.db, expert_id)
            self._check_expert_visibility(expert, current_user_id, role)
            
            # 检查是否已关注
            existing_subscription = await crud.get_subscription(self.db, current_user_id, expert_id)
            if existing_subscription:
                raise InvalidParameterException("您已关注该专家", code=2002)
            
            # 调用CRUD层
            subscription = await crud.create_subscription(self.db, current_user_id, expert_id)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(subscription)
            
            result = {
                "user_id": str(current_user_id),
                "expert_id": str(expert_id),
                "subscribed_at": subscription.created_at.isoformat() + "Z"
            }
            self.logger.info(f"关注专家成功: user_id={str(current_user_id)[:8]}, expert_id={str(expert_id)[:8]}")
            return result
        except DatabaseIntegrityException as e:
            await self.db.rollback()
            raise InvalidParameterException("您已关注该专家", code=2002)
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"关注专家失败: {str(e)}")
            raise
    
    async def unfollow_expert(
        self,
        expert_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str
    ) -> Dict[str, Any]:
        """
        取消关注专家
        
        Args:
            expert_id: 专家唯一标识
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            Dict[str, Any]: 取消关注结果
        
        Raises:
            PermissionDeniedException: 如果无用户资源操作权限
            NotFoundException: 如果未关注该专家
        """
        # 权限检查
        self._check_user_resource_permission(current_user_id, current_user_id, role)
        
        try:
            # 调用CRUD层
            success = await crud.delete_subscription(self.db, current_user_id, expert_id)
            
            # 404检查
            if not success:
                raise NotFoundException("未关注该专家")
            
            # 提交事务
            await self.db.commit()
            
            result = {"message": "取消关注成功"}
            self.logger.info(f"取消关注专家成功: user_id={str(current_user_id)[:8]}, expert_id={str(expert_id)[:8]}")
            return result
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"取消关注专家失败: {str(e)}")
            raise
    
    async def get_followed_experts(
        self,
        current_user_id: uuid.UUID,
        role: str,
        include_live_status: bool = True
    ) -> List[FollowedExpertItem]:
        """
        获取关注的专家列表（包含直播状态）
        
        Args:
            current_user_id: 当前用户ID
            role: 用户角色
            include_live_status: 是否包含直播状态（默认True）
        
        Returns:
            List[FollowedExpertItem]: 关注的专家列表
        
        Raises:
            PermissionDeniedException: 如果无用户资源操作权限
        """
        # 权限检查
        self._check_user_resource_permission(current_user_id, current_user_id, role)
        
        # 调用CRUD层
        subscriptions = await crud.get_user_subscriptions(self.db, current_user_id)
        
        # 提取专家ID列表
        expert_ids = [sub.expert_id for sub in subscriptions]
        
        # 查询直播状态（如果include_live_status=True）
        live_status_map = {}
        if include_live_status and expert_ids:
            # 批量查询专家参与的正在直播的场次
            for expert_id in expert_ids:
                # 查询专家参与的正在直播的场次
                session_experts, _ = await crud.get_expert_sessions(
                    self.db, expert_id, None, 0, 1
                )
                
                if session_experts:
                    se = session_experts[0]
                    session = se.session
                    if session and session.status == LiveSessionStatus.LIVE:
                        live_status_map[expert_id] = {
                            "session_id": str(session.id),
                            "status": session.status.value,
                            "start_time": session.start_time.isoformat() + "Z" if session.start_time else None
                        }
        
        # 构造响应（仅展示启用专家，过滤 is_active=False）
        result = [
            FollowedExpertItem(
                expert_id=sub.expert_id,
                name=sub.expert.name,
                title=sub.expert.title,
                hospital=sub.expert.hospital,
                avatar_url=sub.expert.avatar_url,
                subscribed_at=sub.created_at,
                live_status=live_status_map.get(sub.expert_id)
            )
            for sub in subscriptions
            if sub.expert.is_active
        ]
        
        self.logger.info(f"查询关注列表成功: user_id={str(current_user_id)[:8]}, 返回{len(result)}条记录")
        return result
    
    async def check_is_followed(
        self,
        expert_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str
    ) -> Dict[str, bool]:
        """
        检查是否已关注专家
        
        Args:
            expert_id: 专家唯一标识
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            Dict[str, bool]: 是否已关注
        
        Raises:
            PermissionDeniedException: 如果无用户资源操作权限
        """
        # 权限检查
        self._check_user_resource_permission(current_user_id, current_user_id, role)
        
        # 专家可见性校验（专家不存在或 is_active=False 且非 Admin 则 404）
        expert = await crud.get_expert(self.db, expert_id)
        self._check_expert_visibility(expert, current_user_id, role)
        
        # 调用CRUD层
        subscription = await crud.get_subscription(self.db, current_user_id, expert_id)
        
        result = {"is_followed": subscription is not None}
        self.logger.debug(f"检查关注状态: user_id={str(current_user_id)[:8]}, expert_id={str(expert_id)[:8]}, is_followed={result['is_followed']}")
        return result
    
    # ==================== 场次专家关联Service方法 ====================
    
    async def set_session_experts(
        self,
        session_id: uuid.UUID,
        expert_data_list: List[Dict[str, Any]],
        current_user_id: uuid.UUID,
        role: str
    ) -> Dict[str, Any]:
        """
        为场次设置专家列表（全量替换）

        权限：ADMIN/SUPERADMIN，或该场次所属房间的 owner。
        可绑任意 is_active 专家（支持多专家联动）。

        Args:
            session_id: 直播场次ID
            expert_data_list: 专家数据列表，格式: [{"expert_id": UUID, "role": str, "sort_order": int}, ...]
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            Dict[str, Any]: 设置结果
        
        Raises:
            PermissionDeniedException: 非管理员且非房主
            NotFoundException: 场次不存在
            InvalidParameterException: 如果专家不存在或角色无效
        """
        await self._check_admin_or_session_room_owner(session_id, current_user_id, role)
        
        # 业务验证：检查列表长度
        if len(expert_data_list) > 100:
            raise InvalidParameterException("专家数量不能超过100个", code=4001)
        
        valid_roles = ["主讲", "主持", "嘉宾"]
        normalized = []
        for data in expert_data_list:
            eid = data.get("expert_id")
            if eid is None:
                raise InvalidParameterException("专家列表项缺少 expert_id", code=4001)
            try:
                eid_uuid = uuid.UUID(str(eid))
            except (ValueError, TypeError):
                raise InvalidParameterException(f"无效的 expert_id: {eid}", code=4001)
            r = data.get("role")
            if not r or r not in valid_roles:
                raise InvalidParameterException("专家列表项缺少或无效的 role", code=4001)
            so = data.get("sort_order", 0)
            try:
                so = int(so) if so is not None else 0
            except (TypeError, ValueError):
                so = 0
            normalized.append({"expert_id": eid_uuid, "role": r, "sort_order": so})
        
        for item in normalized:
            expert = await crud.get_expert(self.db, item["expert_id"])
            if expert is None:
                raise InvalidParameterException(f"专家不存在: {item['expert_id']}", code=2001)
            if not expert.is_active:
                raise InvalidParameterException("仅允许启用状态的专家关联场次", code=4001)
        
        try:
            session_experts = await crud.set_session_experts(self.db, session_id, normalized)
            await self.db.commit()
            
            result = {
                "session_id": str(session_id),
                "experts": [
                    {"expert_id": str(item["expert_id"]), "role": item["role"], "sort_order": item["sort_order"]}
                    for item in normalized
                ]
            }
            self.logger.info(f"设置场次专家列表成功: session_id={str(session_id)[:8]}, 专家数量={len(normalized)}")
            return result
        except DatabaseIntegrityException as e:
            await self.db.rollback()
            raise InvalidParameterException("场次专家关联已存在", code=2004)
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"设置场次专家列表失败: {str(e)}")
            raise
    
    async def get_session_experts(
        self,
        session_id: uuid.UUID,
        role: Optional[str] = None,
        current_user_id: Optional[uuid.UUID] = None,
        role_user: Optional[str] = None
    ) -> List[SessionExpertItem]:
        """
        获取场次的专家列表
        
        Args:
            session_id: 直播场次ID
            role: 专家角色筛选（可选）
            current_user_id: 当前用户ID（可选）
            role_user: 用户角色（可选）
        
        Returns:
            List[SessionExpertItem]: 场次专家列表
        """
        # 调用CRUD层
        session_experts = await crud.get_session_experts(self.db, session_id, role)

        # 《16》P44：C 端隐藏已下架专家；Admin 可见全量便于恢复挂靠
        is_admin = role_user in ("ADMIN", "SUPERADMIN")

        # 构造响应
        result = []
        for se in session_experts:
            if not se.expert:
                continue
            if not se.expert.is_active and not is_admin:
                continue
            result.append(
                SessionExpertItem(
                    id=se.expert.id,
                    name=se.expert.name,
                    title=se.expert.title,
                    hospital=se.expert.hospital,
                    avatar_url=se.expert.avatar_url,
                    is_active=se.expert.is_active,
                    role=se.role,
                    sort_order=se.sort_order,
                    expertise_areas=se.expert.expertise_areas,
                    bio=se.expert.bio,
                )
            )

        self.logger.info(f"查询场次专家列表成功: session_id={str(session_id)[:8]}, 返回{len(result)}条记录")
        return result
    
    async def upload_expert_avatar(
        self,
        expert_id: UUID,
        file: UploadFile,
        current_user_id: UUID,
        role: str
    ) -> str:
        """
        上传专家头像
        
        Args:
            expert_id: 专家ID
            file: 上传的文件
            current_user_id: 当前用户ID
            role: 用户角色
            
        Returns:
            头像的URL路径
            
        Raises:
            PermissionDeniedException: 权限不足
            NotFoundException: 专家不存在
            HTTPException: 文件上传失败
        """
        # 1. 权限检查
        if role not in ["ADMIN", "SUPERADMIN"]:
            self.logger.warning(f"权限不足: user_id={str(current_user_id)[:8]}, role={role}")
            raise PermissionDeniedException("需要管理员权限")
        
        # 2. 验证专家是否存在
        expert = await self.db.get(Expert, expert_id)
        if not expert:
            self.logger.warning(f"专家不存在: expert_id={str(expert_id)[:8]}")
            raise NotFoundException("专家不存在")
        
        # 3. 保存头像文件
        from app.core.file_handler import FileHandler
        avatar_url = await FileHandler.save_expert_avatar(file, expert_id)
        
        # 4. 更新数据库中的avatar_url
        expert.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(expert)
        
        self.logger.info(f"专家头像上传成功: expert_id={str(expert_id)[:8]}, avatar_url={avatar_url}")
        
        return avatar_url

    async def merge_departments(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str,
    ) -> dict:
        """合并科室：源科室 → 目标科室"""
        self._check_admin_permission(role)
        user_id_log = str(current_user_id)[:8]

        if source_id == target_id:
            raise InvalidParameterException("源科室和目标科室不能相同", code=4001)

        from app.crud import expert_departments as crud_dept

        source = await crud_dept.get_department_by_id(self.db, source_id)
        if not source:
            raise NotFoundException("源科室不存在")

        target = await crud_dept.get_department_by_id(self.db, target_id)
        if not target:
            raise NotFoundException("目标科室不存在")

        expert_count = await crud_dept.transfer_experts_to_department(self.db, source_id, target_id)

        if source.category_id != target.category_id:
            synced = await crud_dept.update_experts_category_by_department(
                self.db, target_id, target.category_id
            )
            self.logger.info(
                f"合并科室跨分类同步: source_cat={str(source.category_id)[:8]}, "
                f"target_cat={str(target.category_id)[:8]}, synced={synced}"
            )

        old_synonyms = list(target.synonyms or [])
        if source.name not in old_synonyms:
            new_synonyms = old_synonyms + [source.name]
            if len(new_synonyms) > 20:
                new_synonyms = new_synonyms[-20:]
            target.synonyms = new_synonyms

        if source.is_verified and not target.is_verified:
            target.is_verified = True

        deleted = await crud_dept.hard_delete_department(self.db, source_id)
        if not deleted:
            raise DatabaseIntegrityException("物理删除源科室失败")

        self.logger.info(
            f"合并科室成功: source_id={str(source_id)[:8]}({source.name}), "
            f"target_id={str(target_id)[:8]}({target.name}), "
            f"transferred={expert_count}, user_id={user_id_log}"
        )
        return {
            "source_name": source.name,
            "target_name": target.name,
            "transferred_experts": expert_count,
        }

    async def update_department_category(
        self,
        department_id: uuid.UUID,
        new_category_id: uuid.UUID,
        current_user_id: uuid.UUID,
        role: str,
    ) -> dict:
        """修改科室分类，并同步所有关联专家的 category_id"""
        self._check_admin_permission(role)
        user_id_log = str(current_user_id)[:8]

        from app.crud import expert_departments as crud_dept
        from app.models.content_management import Category

        dept = await crud_dept.get_department_by_id(self.db, department_id)
        if not dept:
            raise NotFoundException("科室不存在")

        cat_stmt = select(Category).where(
            Category.id == new_category_id,
            Category.is_active == True,
        )
        cat_result = await self.db.execute(cat_stmt)
        category = cat_result.scalar_one_or_none()
        if not category:
            raise InvalidParameterException("新分类不存在或已禁用", code=4001)

        old_category_id = dept.category_id
        dept.category_id = new_category_id
        await self.db.flush()

        expert_count = await crud_dept.update_experts_category_by_department(
            self.db, department_id, new_category_id
        )

        self.logger.info(
            f"更新科室分类成功: dept_id={str(department_id)[:8]}({dept.name}), "
            f"old_category={str(old_category_id)[:8]}, "
            f"new_category={str(new_category_id)[:8]}, "
            f"synced_experts={expert_count}, user_id={user_id_log}"
        )
        return {
            "department_name": dept.name,
            "old_category_id": str(old_category_id),
            "new_category_id": str(new_category_id),
            "synced_experts": expert_count,
        }

