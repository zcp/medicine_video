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
from app.crud import session as crud_session
from app.crud import room as crud_room
from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert
from app.models.live_core import LiveSession, LiveSessionStatus
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
from app.core.permissions import check_room_owner_or_admin, check_admin_permission

# 配置日志
logger = logging.getLogger(__name__)

# 分类常量（从单一真相源引用，与 seed.py 共享同一份数据）
from app.core.category_constants import (
    ROOT_CATEGORIES,
    ALL_CATEGORY_NAMES_SORTED,
    CATEGORY_PARENT_MAP,
    DEPARTMENT_CATEGORY_MAP,
)

def _normalize_department_text(text_val: str) -> str:
    """清洗科室文本：去除末尾斜杠和首尾空白"""
    return text_val.rstrip('/.。、, ').strip()


def _match_broad_category(department_text: str) -> Optional[Tuple[str, str]]:
    """启发式匹配科室文本 → (matched_dept_name, matched_category_name)。

    匹配优先级：
    1. 别名表精确匹配（DEPARTMENT_CATEGORY_MAP）— 优先于子串匹配
    2. 子串匹配（二级优先，一级兜底——ALL_CATEGORY_NAMES_SORTED 中二级在前）

    返回值:
        (normalized_dept_name, matched_category_name) — category_name 是实际匹配到的
        分类名（二级优先），用于查找数据库中的具体 Category 行。
        返回 None 表示无法匹配。

    设计意图（P0-3 修订）:
        - 匹配到任何分类名都直接返回，不做一级/二级转换
        - 让调用方在 DB 中查找该名称对应的 Category 行，确保所有专家落在同一层级
        - UPDATE: 别名表中的值已有二级分类映射，保持原值不变
    """
    normalized = _normalize_department_text(department_text)
    if not normalized:
        return None

    # P1: 别名表（值已是分类名，直接返回）
    mapped = DEPARTMENT_CATEGORY_MAP.get(normalized)
    if mapped:
        return (normalized, mapped)

    # P2: 子串匹配（二级优先——ALL_CATEGORY_NAMES_SORTED 中二级在前）
    # 直接返回匹配到的分类名本身，不做层级转换
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
        # 会话级科室缓存（避免 batch import 时每行 CSV 全表扫描 expert_departments）
        self._dept_cache: Optional[List] = None
    
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

    # ==================== [DEPRECATED] 旧分类解析方法 ====================
    # 以下方法仅保留向后兼容，新代码请使用 _resolve_department_and_category
    # 该方法在 batch import 中已不再调用（已迁移到 _resolve_department_and_category）

    async def _resolve_active_category_id(
        self,
        category_id_raw: Optional[str],
        category_name_raw: Optional[str],
    ) -> Optional[uuid.UUID]:
        """
        解析 CSV 导入中的专家主分类。

        category_id 和 category_name 都必须指向启用的全局分类，避免批量导入绕过
        create/update 接口中对专家主专业分类的有效性校验。
        """
        from app.models.content_management import Category

        if category_id_raw:
            try:
                category_id = uuid.UUID(category_id_raw)
            except (ValueError, TypeError):
                raise ValueError(f"无效的 category_id 格式: {category_id_raw}")

            cat_stmt = select(Category.id).where(
                Category.id == category_id,
                Category.is_active == True,
            )
            cat_result = await self.db.execute(cat_stmt)
            if cat_result.scalar_one_or_none():
                return category_id
            raise ValueError(f"分类不存在或已禁用: {category_id_raw}")

        if category_name_raw:
            # 阶段6A：统一按名查询 helper（同名歧义二级优先）
            from app.crud.content_management import get_category_id_by_name
            cat_id = await get_category_id_by_name(self.db, category_name_raw)
            if cat_id:
                return cat_id
            raise ValueError(f"分类不存在或已禁用: {category_name_raw}")

        return None

    async def _resolve_department_and_category(
        self,
        department_text: Optional[str],
        category_id_raw: Optional[str] = None,
        category_name_raw: Optional[str] = None,
        source: str = "auto_match",
    ) -> Tuple[Optional[uuid.UUID], Optional[uuid.UUID]]:
        """自适应匹配科室 + 分类。

        这是融合方案的核心匹配逻辑，按以下优先级解析：
        1. 显式 category_id 或 category_name → 直接验证使用
        2. department_text 精确匹配 ExpertDepartment.name → 使用其 category_id
        3. department_text 精确匹配 ExpertDepartment.synonyms → 使用其 category_id
        4. department_text 启发式匹配（_match_broad_category）→ 使用其 category_id
        5. 无匹配 → 自动创建科室（is_verified=False），category 回退到"其他"或启发式结果

        Args:
            department_text: CSV 中的科室文本（可选）
            category_id_raw: 显式分类 ID（可选）
            category_name_raw: 显式分类名称（可选）

        Returns:
            (department_id, category_id) — department_id 可能为 None
        """
        from app.crud import expert_departments as crud_dept
        from app.models.content_management import Category

        resolved_category_id: Optional[uuid.UUID] = None
        resolved_department_id: Optional[uuid.UUID] = None

        # 1. 显式分类解析（优先级最高）
        if category_id_raw:
            try:
                explicit_cat_id = uuid.UUID(category_id_raw)
            except (ValueError, TypeError):
                raise ValueError(f"无效的 category_id 格式: {category_id_raw}")
            cat_stmt = select(Category.id).where(
                Category.id == explicit_cat_id,
                Category.is_active == True
            )
            cat_result = await self.db.execute(cat_stmt)
            if cat_result.scalar_one_or_none():
                resolved_category_id = explicit_cat_id
            else:
                raise ValueError(f"分类不存在或已禁用: {category_id_raw}")
        elif category_name_raw:
            # 阶段6A：统一按名查询 helper（同名歧义二级优先）
            from app.crud.content_management import get_category_id_by_name
            found = await get_category_id_by_name(self.db, category_name_raw)
            if found:
                resolved_category_id = found
            else:
                raise ValueError(f"分类名称不存在或已禁用: {category_name_raw}")

        # 如果显式分类已确定且无科室文本，直接返回
        if resolved_category_id and not department_text:
            return (None, resolved_category_id)

        # 2. 科室匹配
        if department_text:
            normalized = _normalize_department_text(department_text)
            if normalized:
                # 会话级缓存：一次 Service 实例生命周期内只加载一次全部科室
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

                # 启发式匹配结果：整段代码中最多调用一次（纯函数无副作用）
                _heuristic: Optional[Tuple[str, str]] = None

                if not matched_dept:
                    _heuristic = _match_broad_category(normalized)
                    if _heuristic:
                        matched_dept_name, matched_cat_name = _heuristic
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
                            self.logger.info(
                                f"启发式匹配科室: '{normalized}' → '{matched_dept.name}'"
                            )

                if matched_dept:
                    resolved_department_id = matched_dept.id
                    if not resolved_category_id:
                        resolved_category_id = matched_dept.category_id
                else:
                    # 自动创建科室：_heuristic[1] 现在是实际分类名（二级优先），直接查 DB
                    from app.crud.content_management import get_category_id_by_name
                    heuristic_cat_name = _heuristic[1] if _heuristic else None
                    fallback_cat_id = await get_category_id_by_name(self.db, heuristic_cat_name or '其他')

                    # 兼容旧逻辑：若按 heuristic_cat_name（可能有多个同名一级分类）查不到，
                    # 尝试按"其他"兜底
                    if not fallback_cat_id and heuristic_cat_name and heuristic_cat_name != '其他':
                        fallback_cat_id = await get_category_id_by_name(self.db, '其他')
                        self.logger.warning(
                            f"启发式分类名 '{heuristic_cat_name}' 在 DB 中不存在，回退到'其他': "
                            f"department_text={department_text}"
                        )

                    from app.schemas.expert_departments import ExpertDepartmentCreate
                    new_dept_data = ExpertDepartmentCreate(
                        name=normalized,
                        category_id=fallback_cat_id if not resolved_category_id else resolved_category_id,
                        synonyms=[],
                        is_verified=False,
                        source=source,
                    )
                    try:
                        new_dept = await crud_dept.create_department(self.db, new_dept_data)
                        await self.db.flush()
                        resolved_department_id = new_dept.id
                        if not resolved_category_id:
                            resolved_category_id = new_dept.category_id
                        self.logger.info(
                            f"自动创建新科室: '{normalized}' (id={str(new_dept.id)[:8]}, "
                            f"category={heuristic_cat_name or '其他'})"
                        )
                    except DatabaseIntegrityException:
                        # 并发冲突：另一请求已创建同名科室，回滚当前写入并重查
                        await self.db.rollback()
                        existing = await crud_dept.get_department_by_name(self.db, normalized)
                        if existing:
                            resolved_department_id = existing.id
                            resolved_category_id = resolved_category_id or existing.category_id
                            self.logger.info(
                                f"并发冲突后复用已有科室: '{normalized}' → id={str(existing.id)[:8]}"
                            )
                        else:
                            # 极低概率：事务回滚后查不到 → 向上传播让调用方重试
                            raise

        # 3. 兜底：确保绝不返回 None category_id（DB 已 NOT NULL）
        if not resolved_category_id:
            from app.crud.content_management import get_category_id_by_name
            other_cat_id = await get_category_id_by_name(self.db, '其他')
            if not other_cat_id:
                raise ValueError("无法解析分类，且'其他'兜底分类不存在——请先执行 seed.py")
            resolved_category_id = other_cat_id
            self.logger.warning(
                f"科室文本为空或无匹配，回退到'其他'分类: "
                f"department_text={department_text}, category_id_raw={category_id_raw}"
            )

        return (resolved_department_id, resolved_category_id)

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

    async def get_experts_public_list(
        self,
        page: int = 1,
        size: int = 20,
        category_id: Optional[uuid.UUID] = None,
        keyword: Optional[str] = None,
        department: Optional[str] = None,
        hospital: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取公开专家列表（分页，默认仅已启用专家）

        Args:
            page: 页码（从1开始）
            size: 每页数量
            category_id: 分类ID筛选（可选）
            keyword: 关键词（姓名/医院/科室/简介，可选）
            department: 科室筛选（可选）
            hospital: 医院筛选（可选）
            is_active: 启用状态筛选（可选，默认仅启用）
            sort: 排序规则（可选）

        Returns:
            {"total": int, "page": int, "size": int, "items": [ExpertItem]}
        """
        experts, total = await crud.get_experts_public_list(
            self.db, page=page, size=size, category_id=category_id,
            keyword=keyword, department=department, hospital=hospital,
            is_active=is_active, sort=sort,
        )
        items = [ExpertItem.model_validate(expert) for expert in experts]
        result = {
            "total": total,
            "page": page,
            "size": size,
            "items": items,
        }
        self.logger.info(f"查询公开专家列表成功: page={page}, size={size}, total={total}, returned={len(items)}")
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
        check_admin_permission(role)

        # 子任务 4.1：显式同时传 category_id + department_id 且不一致 → 400
        # （科室优先原则：不一致时提示只传科室或保持一致；department 文本分支仍走自适应解析）
        if expert_data.category_id and expert_data.department_id:
            from app.models.expert_departments import ExpertDepartment as EDModel
            dept_stmt = select(EDModel).where(EDModel.id == expert_data.department_id)
            dept = (await self.db.execute(dept_stmt)).scalar_one_or_none()
            if dept is None:
                raise InvalidParameterException("科室不存在", code=4001)
            if dept.category_id != expert_data.category_id:
                raise InvalidParameterException(
                    "分类与科室不一致：专家分类应与所属科室分类一致，请只传科室或保持一致", code=4001
                )

        # 业务验证：如果提供了user_id，检查是否已被绑定
        if expert_data.user_id:
            existing_expert = await crud.get_expert_by_user_id(self.db, expert_data.user_id)
            if existing_expert:
                raise InvalidParameterException("该用户已绑定到其他专家档案", code=2004)

        # 融合方案：如果传了 department 文本（非 None 非空），自适应匹配科室+分类
        dept_text = getattr(expert_data, 'department', None)
        if dept_text and dept_text.strip():
            resolved_dept_id, resolved_cat_id = await self._resolve_department_and_category(
                department_text=dept_text.strip(),
                category_id_raw=str(expert_data.category_id) if expert_data.category_id else None,
                source="manual_create",
            )
            expert_data.department_id = resolved_dept_id
            expert_data.category_id = resolved_cat_id
        elif expert_data.category_id:
            # 没传 department 文本，但传了 category_id → 精确校验
            from app.models.content_management import Category
            cat_stmt = select(Category).where(
                Category.id == expert_data.category_id,
                Category.is_active == True
            )
            cat_result = await self.db.execute(cat_stmt)
            category = cat_result.scalar_one_or_none()
            if not category:
                raise InvalidParameterException("分类不存在或已禁用", code=4001)
        else:
            # 既没传 department 也没传 category_id → 兜底"其他"（阶段6A：统一按名 helper）
            from app.crud.content_management import get_category_id_by_name
            other_cat_id = await get_category_id_by_name(self.db, '其他')
            if not other_cat_id:
                raise InvalidParameterException("无法解析分类，且'其他'兜底分类不存在——请先执行 seed.py")
            expert_data.category_id = other_cat_id

        try:
            # 调用CRUD层
            expert = await crud.create_expert(self.db, expert_data)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(expert)
            
            result = ExpertItem.model_validate(expert)
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
        is_verified: Optional[bool] = None,
        hospital: Optional[str] = None,
        sort: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
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
            is_verified: 审核状态筛选
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
        check_admin_permission(role)
        
        # 计算分页
        skip = (page - 1) * size
        
        # 调用CRUD层
        experts, total = await crud.get_experts_multi_and_total(
            self.db, skip, size, name, is_featured, is_active, is_verified, hospital, sort,
            category_id, department_id
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
        check_admin_permission(role)
        
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
        
        optional_cols = ["title", "hospital", "department", "expertise_areas", "bio", "avatar_url", "is_featured", "sort_order", "is_active", "category_id", "category_name"]
        
        for row_num, row in enumerate(reader, start=2):
            total += 1
            row_data = {k: v.strip() if isinstance(v, str) else v for k, v in row.items() if v}
            row_summary = {k: v for k, v in row_data.items() if k in fieldnames}
            
            try:
                name = row_data.get("name", "").strip()
                if not name:
                    raise ValueError("name 为必填列")

                # 融合方案：自适应匹配科室 + 分类（替代旧 _resolve_active_category_id）
                resolved_dept_id, resolved_cat_id = await self._resolve_department_and_category(
                    department_text=row_data.get("department"),
                    category_id_raw=row_data.get("category_id"),
                    category_name_raw=row_data.get("category_name"),
                )

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
                    department=row_data.get("department") or None,  # 保留兼容旧 Schema 字段
                    department_id=resolved_dept_id,  # 融合方案：自适应匹配的科室 ID
                    expertise_areas=row_data.get("expertise_areas") or None,
                    bio=row_data.get("bio") or None,
                    avatar_url=row_data.get("avatar_url") or None,
                    is_featured=row_data.get("is_featured", "false").lower() in ("true", "1"),
                    sort_order=int(row_data["sort_order"]) if row_data.get("sort_order") else 0,
                    is_active=row_data.get("is_active", "true").lower() not in ("false", "0"),
                    category_id=resolved_cat_id,  # 融合方案：自适应匹配的分类 ID（绝不为 None）
                )
                
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
        check_admin_permission(role)

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

                # 融合方案：自适应匹配科室 + 分类（替代旧 _resolve_active_category_id）
                resolved_dept_id, resolved_cat_id = await self._resolve_department_and_category(
                    department_text=row_data.get("department"),
                    category_id_raw=row_data.get("category_id"),
                    category_name_raw=row_data.get("category_name"),
                )

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
                    department=row_data.get("department") or None,  # 保留兼容旧 Schema 字段
                    department_id=resolved_dept_id,  # 融合方案：自适应匹配的科室 ID
                    expertise_areas=row_data.get("expertise_areas") or None,
                    bio=row_data.get("bio") or None,
                    avatar_url=row_data.get("avatar_url") or None,
                    is_featured=row_data.get("is_featured", "false").lower() in ("true", "1"),
                    sort_order=int(row_data["sort_order"]) if row_data.get("sort_order") else 0,
                    is_active=row_data.get("is_active", "true").lower() not in ("false", "0"),
                    category_id=resolved_cat_id,  # 融合方案：自适应匹配的分类 ID（绝不为 None）
                )

                nested = await self.db.begin_nested()
                try:
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
        check_admin_permission(role)

        # 子任务 4.1：科室↔分类一致性校验（V1.2 闭环：合并端点的校正不被日常操作打回）
        # 先查专家现状（404 提前，语义与 crud.update 后一致）
        existing_expert = await crud.get_expert(self.db, expert_id)
        if existing_expert is None:
            raise NotFoundException("专家不存在")
        from app.models.expert_departments import ExpertDepartment as EDModel

        new_dept_id = expert_data.department_id if expert_data.department_id is not None else existing_expert.department_id
        if expert_data.category_id is not None and new_dept_id is not None:
            # 规则 a：传 category_id 且专家有科室 → 必须与科室分类一致
            dept_stmt = select(EDModel).where(EDModel.id == new_dept_id)
            dept = (await self.db.execute(dept_stmt)).scalar_one_or_none()
            if dept is not None and dept.category_id != expert_data.category_id:
                raise InvalidParameterException(
                    "分类与科室不一致：分类变更请通过科室变更完成（科室分类跟随）", code=4001
                )
        if expert_data.department_id is not None:
            # 规则 b/c：传 department_id → category_id 自动跟随新科室（同时传两者以科室为准）
            dept_stmt = select(EDModel).where(EDModel.id == expert_data.department_id)
            dept = (await self.db.execute(dept_stmt)).scalar_one_or_none()
            if dept is None:
                raise InvalidParameterException("科室不存在", code=4001)
            if expert_data.category_id is None or expert_data.category_id != dept.category_id:
                expert_data.category_id = dept.category_id

        # 业务验证：如果更新了category_id，检查分类是否存在且启用
        if expert_data.category_id is not None:
            from app.models.content_management import Category
            cat_stmt = select(Category).where(
                Category.id == expert_data.category_id,
                Category.is_active == True
            )
            cat_result = await self.db.execute(cat_stmt)
            category = cat_result.scalar_one_or_none()
            if not category:
                raise InvalidParameterException("分类不存在或已禁用", code=4001)

        try:
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
            
            result = ExpertItem.model_validate(expert)
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
        check_admin_permission(role)
        
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
        为场次设置专家列表
        
        Args:
            session_id: 直播场次ID
            expert_data_list: 专家数据列表，格式: [{"expert_id": UUID, "role": str, "sort_order": int}, ...]
            current_user_id: 当前用户ID
            role: 用户角色
        
        Returns:
            Dict[str, Any]: 设置结果
        
        Raises:
            PermissionDeniedException: 如果无管理员权限
            InvalidParameterException: 如果专家不存在或角色无效
        """
        # 权限检查：Admin 或房间创建者可操作
        session = await crud_session.get(self.db, session_id)
        if session is None:
            raise NotFoundException("场次不存在")
        room = await crud_room.get(self.db, room_id=session.room_id)
        if room is None:
            raise NotFoundException("场次关联的直播间不存在")
        check_room_owner_or_admin(room, current_user_id, role)
        
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
        # 调用CRUD层（数据关联治理 P1-1：透传查看者角色，CRUD 层过滤已停用专家）
        session_experts = await crud.get_session_experts(
            self.db, session_id, role, viewer_role=role_user
        )
        
        # 构造响应
        result = [
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
                bio=se.expert.bio
            )
            for se in session_experts
        ]
        
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
        check_admin_permission(role)
        
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
        check_admin_permission(role)
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

        # 跨分类合并时同步专家的 category_id
        if source.category_id != target.category_id:
            synced = await crud_dept.update_experts_category_by_department(self.db, source_id, target.category_id)
            self.logger.info(
                f"合并科室跨分类同步: source_cat={str(source.category_id)[:8]}, "
                f"target_cat={str(target.category_id)[:8]}, synced={synced}"
            )

        old_synonyms = target.synonyms or []
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
        check_admin_permission(role)
        user_id_log = str(current_user_id)[:8]

        from app.crud import expert_departments as crud_dept
        from app.models.content_management import Category

        dept = await crud_dept.get_department_by_id(self.db, department_id)
        if not dept:
            raise NotFoundException("科室不存在")

        cat_stmt = select(Category).where(
            Category.id == new_category_id,
            Category.is_active == True
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

    async def get_my_expert(self, current_user_id: uuid.UUID) -> Optional[Any]:
        """PR 5: 获取当前用户绑定的专家"""
        from app.crud import experts as crud_experts
        expert = await crud_experts.get_expert_by_user_id(self.db, current_user_id)
        return expert

    async def update_my_expert(
        self,
        current_user_id: uuid.UUID,
        expert_data: Any,
    ) -> None:
        """PR 5: 创建或更新当前用户的专家绑定"""
        from app.crud import experts as crud_experts
        from app.schemas.experts import ExpertCreate

        existing = await crud_experts.get_expert_by_user_id(self.db, current_user_id)

        if existing:
            update_dict = {}
            for field in ("name", "title", "hospital", "expertise_areas", "bio"):
                val = getattr(expert_data, field, None)
                if val is not None:
                    update_dict[field] = val
            if hasattr(expert_data, "department_name") and expert_data.department_name:
                dept_id, cat_id = await self._resolve_department_and_category(
                    department_text=expert_data.department_name,
                    source="self_claim",
                )
                if dept_id:
                    update_dict["department_id"] = dept_id
                if cat_id:
                    update_dict["category_id"] = cat_id
            if update_dict:
                await crud_experts.update_expert(self.db, existing.id, update_dict)
                await self.db.commit()
        else:
            create_data = {
                "name": getattr(expert_data, "name", ""),
                "user_id": current_user_id,
            }
            dept_id, cat_id = None, None
            if hasattr(expert_data, "department_name") and expert_data.department_name:
                dept_id, cat_id = await self._resolve_department_and_category(
                    department_text=expert_data.department_name,
                    source="self_claim",
                )
            if dept_id:
                create_data["department_id"] = dept_id
            if cat_id:
                create_data["category_id"] = cat_id
            await crud_experts.create_expert(self.db, ExpertCreate(**create_data))
            await self.db.commit()
