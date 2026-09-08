"""
专家科室受控词表 — Admin API 端点

提供科室的 CRUD 管理和未映射专家查询。
所有端点需要管理员权限。
"""
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, error_response
from app.services.expert_service import ExpertService
from app.schemas.expert_departments import ExpertDepartmentCreate, ExpertDepartmentUpdate, ExpertDepartmentItem, BatchVerifyRequest
from app.exceptions import PermissionDeniedException, NotFoundException, InvalidParameterException
from app.models.content_management import Category


def check_admin_permission(role) -> None:
    """本地无 app.core.permissions，沿用专家模块大写角色约定。"""
    if (role or "").upper() not in ("ADMIN", "SUPERADMIN"):
        raise PermissionDeniedException("需要管理员权限")

logger = logging.getLogger(__name__)

expert_dept_admin_router = APIRouter(tags=["科室管理-管理员"])


@expert_dept_admin_router.get("/expert-departments")
async def list_departments(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    is_active: Optional[bool] = Query(default=None),
    is_verified: Optional[bool] = Query(default=None),
    category_id: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员查询科室列表（分页）"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    user_id_log = str(user_id)[:8]

    cat_uuid = None
    if category_id:
        try:
            cat_uuid = uuid.UUID(category_id)
        except (ValueError, TypeError):
            return JSONResponse(status_code=400, content=error_response(code=4001, message="无效的分类ID格式"))

    try:
        check_admin_permission(role)
        from app.crud import expert_departments as crud_dept
        items, total = await crud_dept.get_departments_paginated(
            db, page=page, size=size, is_active=is_active,
            is_verified=is_verified, category_id=cat_uuid, q=q,
        )
        items_data = [ExpertDepartmentItem.model_validate(d, from_attributes=True) for d in items]
        return success_response(data={"items": items_data, "total": total, "page": page, "size": size})
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except Exception as e:
        logger.error(f"查询科室列表失败: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.post("/expert-departments")
async def create_department(
    department_data: ExpertDepartmentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员创建科室"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")
    user_id_log = str(user_id)[:8]

    try:
        check_admin_permission(role)

        cat = await db.get(Category, department_data.category_id)
        if not cat or not cat.is_active:
            return JSONResponse(status_code=400, content=error_response(code=4001, message="分类不存在或已禁用"))

        from app.crud import expert_departments as crud_dept
        dept = await crud_dept.create_department(db, department_data, created_by=user_id)
        await db.commit()
        await db.refresh(dept)
        return success_response(data={"id": str(dept.id), "name": dept.name, "category_id": str(dept.category_id)})
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except InvalidParameterException as e:
        return JSONResponse(status_code=400, content=error_response(code=e.code if hasattr(e,'code') else 4001, message=str(e)))
    except Exception as e:
        logger.error(f"创建科室失败: user_id={user_id_log}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.patch("/expert-departments/{department_id}")
async def update_department(
    department_id: uuid.UUID = Path(...),
    department_data: ExpertDepartmentUpdate = ...,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新科室信息（部分更新）"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        check_admin_permission(role)
        from app.crud import expert_departments as crud_dept
        # 记录更新前的 category_id，用于判断是否需要同步专家
        old_dept = await crud_dept.get_department_by_id(db, department_id)
        old_category_id = old_dept.category_id if old_dept else None
        dept = await crud_dept.update_department(db, department_id, department_data)
        if dept is None:
            return JSONResponse(status_code=404, content=error_response(code=2001, message="科室不存在"))
        # 如果 category_id 变更了，同步关联专家
        if department_data.category_id is not None and old_category_id != department_data.category_id:
            from app.crud.expert_departments import update_experts_category_by_department
            synced = await update_experts_category_by_department(db, department_id, department_data.category_id)
            logger.info(f"科室分类变更同步专家: dept_id={str(department_id)[:8]}, old_cat={str(old_category_id)[:8] if old_category_id else 'None'}, synced={synced}")
        await db.commit()
        await db.refresh(dept)
        return success_response(data={"id": str(dept.id), "name": dept.name, "is_verified": dept.is_verified})
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except InvalidParameterException as e:
        return JSONResponse(status_code=400, content=error_response(code=e.code if hasattr(e,'code') else 4001, message=str(e)))
    except Exception as e:
        logger.error(f"更新科室失败: error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.delete("/expert-departments/{department_id}")
async def delete_department(
    department_id: uuid.UUID = Path(...),
    hard_delete: bool = Query(False, description="是否物理删除（默认软删/停用）"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除科室：默认软删（is_active=false），hard_delete=true 时物理删除"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        check_admin_permission(role)
        from app.crud import expert_departments as crud_dept
        if hard_delete:
            dept = await crud_dept.get_department_by_id(db, department_id)
            if not dept:
                return JSONResponse(status_code=404, content=error_response(code=2001, message="科室不存在"))
            expert_count = await crud_dept.count_experts_by_department(db, department_id)
            if expert_count > 0:
                return JSONResponse(
                    status_code=409,
                    content=error_response(
                        code=2004,
                        message=f"科室仍有 {expert_count} 位专家关联，请先合并到其他科室后再删除",
                    ),
                )
            deleted = await crud_dept.hard_delete_department(db, department_id)
            if not deleted:
                return JSONResponse(status_code=404, content=error_response(code=2001, message="科室不存在"))
            await db.commit()
            return success_response(data={"message": "科室已物理删除", "hard_delete": True})
        deleted = await crud_dept.soft_delete_department(db, department_id)
        if deleted is False:
            return JSONResponse(status_code=404, content=error_response(code=2001, message="科室不存在"))
        await db.commit()
        return success_response(data={"message": "科室已软删除", "hard_delete": False})
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except Exception as e:
        logger.error(f"删除科室失败: error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.get("/expert-departments/unmapped")
async def list_unmapped_experts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有 department_id IS NULL 的专家（未映射科室）"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        check_admin_permission(role)
        from app.crud import expert_departments as crud_dept
        experts, total = await crud_dept.get_unmapped_experts(db, page=page, size=size)
        return success_response(data={
            "items": [
                {
                    "id": str(e.id),
                    "name": e.name,
                    "title": e.title,
                    "hospital": e.hospital,
                    "avatar_url": e.avatar_url,
                    "category_id": str(e.category_id) if e.category_id else None,
                    "category_name": e.category.name if e.category else None,
                    "expertise_areas": e.expertise_areas or [],
                    "is_active": e.is_active,
                    "department": e.department,
                }
                for e in experts
            ],
            "total": total,
            "page": page,
            "size": size
        })
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except Exception as e:
        logger.error(f"查询未映射专家失败: error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.post("/expert-departments/merge")
async def merge_departments(
    source_id: uuid.UUID = Body(..., description="源科室 ID（将被合并并删除）"),
    target_id: uuid.UUID = Body(..., description="目标科室 ID（保留）"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员合并科室：源科室 → 目标科室，同义词自学习 + 专家转移 + 物理删除源科室"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        service = ExpertService(db)
        result = await service.merge_departments(source_id, target_id, user_id, role)
        await db.commit()
        return success_response(data=result)
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except NotFoundException as e:
        return JSONResponse(status_code=404, content=error_response(code=2001, message=str(e)))
    except InvalidParameterException as e:
        return JSONResponse(status_code=400, content=error_response(code=4001, message=str(e)))
    except Exception as e:
        logger.error(f"合并科室失败: source_id={str(source_id)[:8]}, target_id={str(target_id)[:8]}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.patch("/expert-departments/{department_id}/category")
async def update_department_category(
    department_id: uuid.UUID = Path(...),
    category_id: uuid.UUID = Body(..., description="新的分类 ID", embed=True),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员修改科室分类，并同步所有关联专家的 category_id"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        service = ExpertService(db)
        result = await service.update_department_category(department_id, category_id, user_id, role)
        await db.commit()
        return success_response(data=result)
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except NotFoundException as e:
        return JSONResponse(status_code=404, content=error_response(code=2001, message=str(e)))
    except InvalidParameterException as e:
        return JSONResponse(status_code=400, content=error_response(code=4001, message=str(e)))
    except Exception as e:
        logger.error(f"更新科室分类失败: dept_id={str(department_id)[:8]}, error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.post("/expert-departments/batch-verify")
async def batch_verify_departments(
    req: BatchVerifyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员批量审核科室（通过/驳回）"""
    role = current_user.get("role")

    try:
        check_admin_permission(role)

        from app.crud import expert_departments as crud_dept

        affected = await crud_dept.batch_verify_departments(
            db, req.department_ids, verified=req.verified
        )
        await db.commit()
        return success_response(data={"affected": affected})
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3003, message=str(e)))
    except Exception as e:
        logger.error(f"批量审核科室失败: error={str(e)}")
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作错误"))


@expert_dept_admin_router.get("/expert-departments/{department_id}")
async def get_department_detail(
    department_id: uuid.UUID = Path(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员查看单个科室详情（含 expert_count）"""
    user_id = uuid.UUID(current_user["user_id"])
    role = current_user.get("role")

    try:
        check_admin_permission(role)
        from app.crud import expert_departments as crud_dept
        from app.models.experts import Expert
        from sqlalchemy import select as sa_select, func as sa_func

        dept = await crud_dept.get_department_by_id(db, department_id)
        if dept is None:
            return JSONResponse(
                status_code=404,
                content=error_response(code=2001, message="科室不存在"),
            )

        count_q = sa_select(sa_func.count(Expert.id)).where(
            Expert.department_id == department_id
        )
        count_res = await db.execute(count_q)
        dept.expert_count = count_res.scalar() or 0

        if dept.category is not None:
            dept.category_name = dept.category.name

        result = ExpertDepartmentItem.model_validate(dept)
        return success_response(data=result)
    except PermissionDeniedException as e:
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message=str(e)),
        )
    except Exception as e:
        logger.error(f"查询科室详情失败: dept_id={str(department_id)[:8]}, error={str(e)}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="数据库操作错误"),
        )
