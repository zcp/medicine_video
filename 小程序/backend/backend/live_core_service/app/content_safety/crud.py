"""内容安全 CRUD 操作"""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_safety.cache import get_cached_rules, invalidate_all_rules_cache, set_cached_rules
from app.content_safety.exceptions import ContentSafetyValidationError
from app.content_safety.models import ContentSafetyLog, ContentSafetyRule
from app.content_safety.schemas import (
    ContentSafetyLogQueryParams,
    ContentSafetyRuleCreate,
    ContentSafetyRuleSnapshot,
    ContentSafetyRuleUpdate,
)


async def get_enabled_rules_by_scene(db: AsyncSession, scene: str) -> List[ContentSafetyRuleSnapshot]:
    cache_key = f"rules:{scene}"
    cached = get_cached_rules(cache_key)
    if cached is not None:
        return cached

    stmt = (
        select(ContentSafetyRule)
        .where(ContentSafetyRule.scene == scene, ContentSafetyRule.enabled.is_(True))
        .order_by(ContentSafetyRule.priority.asc())
    )
    result = await db.execute(stmt)
    rules = [ContentSafetyRuleSnapshot.from_orm(rule) for rule in result.scalars().all()]
    set_cached_rules(cache_key, rules)
    return rules


async def create_log(
    db: AsyncSession,
    *,
    scene: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID],
    target_field: str,
    user_id: Optional[uuid.UUID],
    input_value: str,
    normalized_value: str,
    decision: str,
    matched_rule_ids: Optional[list],
    matched_rule_names: Optional[list],
    reason_code: Optional[str],
    reason_message: Optional[str],
    request_id: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> ContentSafetyLog:
    log = ContentSafetyLog(
        scene=scene,
        resource_type=resource_type,
        resource_id=resource_id,
        target_field=target_field,
        user_id=user_id,
        input_excerpt=input_value[:500],
        normalized_excerpt=normalized_value[:500],
        decision=decision,
        matched_rule_ids=matched_rule_ids,
        matched_rule_names=matched_rule_names,
        reason_code=reason_code,
        reason_message=reason_message,
        request_id=request_id,
        client_ip=client_ip,
    )
    db.add(log)
    await db.flush()
    return log


async def create_rule(
    db: AsyncSession,
    obj_in: ContentSafetyRuleCreate,
    created_by: Optional[uuid.UUID] = None,
) -> ContentSafetyRule:
    rule = ContentSafetyRule(**obj_in.model_dump(), created_by=created_by)
    db.add(rule)
    await db.flush()
    invalidate_all_rules_cache()
    return rule


async def update_rule(
    db: AsyncSession,
    db_obj: ContentSafetyRule,
    obj_in: ContentSafetyRuleUpdate,
) -> ContentSafetyRule:
    update_data = obj_in.model_dump(exclude_unset=True)
    _validate_rule_update(db_obj, update_data)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.flush()
    invalidate_all_rules_cache()
    return db_obj


def _validate_rule_update(db_obj: ContentSafetyRule, update_data: dict) -> None:
    if not update_data:
        return

    binding = getattr(db_obj, "binding_level", "platform") or "platform"
    category = getattr(db_obj, "rule_category", "general") or "general"

    if binding == "statutory":
        if update_data.get("enabled") is False:
            raise ContentSafetyValidationError("statutory 规则禁止停用")
        # 分层策略 V1.1：statutory 允许 block / warn（按档位矩阵）
        if update_data.get("action") and update_data["action"] not in ("block", "warn"):
            raise ContentSafetyValidationError("statutory 规则仅允许 block 或 warn 动作")
        if "pattern" in update_data and category == "political_sensitive":
            raise ContentSafetyValidationError(
                "political_sensitive 本地兜底词表禁止通过管理端修改，请走第三方政治 API 厂商"
            )


async def get_rule(db: AsyncSession, rule_id: uuid.UUID) -> Optional[ContentSafetyRule]:
    result = await db.execute(select(ContentSafetyRule).where(ContentSafetyRule.id == rule_id))
    return result.scalar_one_or_none()


async def list_rules(
    db: AsyncSession,
    *,
    scene: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[ContentSafetyRule], int]:
    stmt = select(ContentSafetyRule)
    count_stmt = select(func.count()).select_from(ContentSafetyRule)
    if scene:
        stmt = stmt.where(ContentSafetyRule.scene == scene)
        count_stmt = count_stmt.where(ContentSafetyRule.scene == scene)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(ContentSafetyRule.priority.asc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def list_logs(
    db: AsyncSession,
    params: ContentSafetyLogQueryParams,
) -> Tuple[List[ContentSafetyLog], int]:
    stmt = select(ContentSafetyLog)
    count_stmt = select(func.count()).select_from(ContentSafetyLog)

    if params.scene:
        stmt = stmt.where(ContentSafetyLog.scene == params.scene)
        count_stmt = count_stmt.where(ContentSafetyLog.scene == params.scene)
    if params.resource_type:
        stmt = stmt.where(ContentSafetyLog.resource_type == params.resource_type)
        count_stmt = count_stmt.where(ContentSafetyLog.resource_type == params.resource_type)
    if params.user_id:
        stmt = stmt.where(ContentSafetyLog.user_id == params.user_id)
        count_stmt = count_stmt.where(ContentSafetyLog.user_id == params.user_id)
    if params.decision:
        stmt = stmt.where(ContentSafetyLog.decision == params.decision)
        count_stmt = count_stmt.where(ContentSafetyLog.decision == params.decision)
    if params.start_time:
        stmt = stmt.where(ContentSafetyLog.created_at >= params.start_time)
        count_stmt = count_stmt.where(ContentSafetyLog.created_at >= params.start_time)
    if params.end_time:
        stmt = stmt.where(ContentSafetyLog.created_at <= params.end_time)
        count_stmt = count_stmt.where(ContentSafetyLog.created_at <= params.end_time)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = (
        stmt.order_by(ContentSafetyLog.created_at.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def count_rules_by_name(db: AsyncSession, rule_name: str) -> int:
    result = await db.execute(
        select(func.count()).select_from(ContentSafetyRule).where(ContentSafetyRule.rule_name == rule_name)
    )
    return result.scalar_one()
