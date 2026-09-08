"""管理端内容安全规则与审计日志 API"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.content_safety import crud as safety_crud
from app.content_safety.schemas import (
    ContentSafetyLogItem,
    ContentSafetyLogPageResult,
    ContentSafetyLogQueryParams,
    ContentSafetyRuleCreate,
    ContentSafetyRuleItem,
    ContentSafetyRulePageResult,
    ContentSafetyRuleUpdate,
)
from app.core.response import error_response, success_response
from app.database import get_db
from app.content_safety.exceptions import ContentSafetyValidationError
from app.exceptions import PermissionDeniedException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-safety", tags=["内容安全-管理端"])


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") not in ("ADMIN", "SUPERADMIN"):
        raise PermissionDeniedException("Admin role required")


@router.get("/rules")
async def list_rules(
    scene: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        _require_admin(current_user)
        items, total = await safety_crud.list_rules(db, scene=scene, page=page, page_size=page_size)
        result = ContentSafetyRulePageResult(
            items=[ContentSafetyRuleItem.from_orm(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )
        return success_response(data=result.model_dump(mode="json"))
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3002, message=str(e)))
    except Exception as e:
        logger.error("查询内容安全规则失败: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库查询错误"))


@router.post("/rules")
async def create_rule(
    body: ContentSafetyRuleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        _require_admin(current_user)
        created_by = uuid.UUID(current_user["user_id"])
        rule = await safety_crud.create_rule(db, body, created_by=created_by)
        return success_response(data=ContentSafetyRuleItem.from_orm(rule).model_dump(mode="json"))
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3002, message=str(e)))
    except Exception as e:
        logger.error("创建内容安全规则失败: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作失败"))


@router.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: uuid.UUID,
    body: ContentSafetyRuleUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        _require_admin(current_user)
        rule = await safety_crud.get_rule(db, rule_id)
        if not rule:
            return JSONResponse(status_code=404, content=error_response(code=2001, message="规则不存在"))
        updated = await safety_crud.update_rule(db, rule, body)
        return success_response(data=ContentSafetyRuleItem.from_orm(updated).model_dump(mode="json"))
    except ContentSafetyValidationError as e:
        return JSONResponse(status_code=422, content=error_response(code=e.code, message=e.message))
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3002, message=str(e)))
    except Exception as e:
        logger.error("更新内容安全规则失败: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库操作失败"))


@router.get("/logs")
async def list_logs(
    scene: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    decision: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        _require_admin(current_user)
        params = ContentSafetyLogQueryParams(
            scene=scene,
            resource_type=resource_type,
            user_id=user_id,
            decision=decision,
            page=page,
            page_size=page_size,
        )
        items, total = await safety_crud.list_logs(db, params)
        return success_response(
            data={
                "items": [ContentSafetyLogItem.model_validate(i).model_dump(mode="json") for i in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )
    except PermissionDeniedException as e:
        return JSONResponse(status_code=403, content=error_response(code=3002, message=str(e)))
    except Exception as e:
        logger.error("查询内容安全日志失败: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1002, message="数据库查询错误"))
