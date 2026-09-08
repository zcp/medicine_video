"""内容安全统一校验服务"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.content_safety import crud as safety_crud
from app.content_safety.engine import evaluate_field, normalize_text
from app.content_safety.exceptions import ContentSafetyBlockedException, ContentSafetyServiceException
from app.content_safety.messages import build_political_block_message
from app.content_safety.political_text.client import PoliticalTextServiceError, check_political_text
from app.content_safety.schemas import (
    ContentSafetyCheckResult,
    ContentSafetyFieldResult,
    ContentSafetyItem,
)

logger = logging.getLogger(__name__)


async def _check_political_for_text(text: str) -> bool:
    """政治敏感 API 检测；故障向上抛 ContentSafetyServiceException"""
    try:
        return await check_political_text(text)
    except PoliticalTextServiceError as exc:
        raise ContentSafetyServiceException(str(exc)) from exc


async def check_content_safety(
    db: AsyncSession,
    scene: str,
    items: List[ContentSafetyItem],
    *,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    client_ip: Optional[str] = None,
    request_id: Optional[str] = None,
    fail_open: bool = False,
) -> ContentSafetyCheckResult:
    """
    统一内容安全校验入口。

    block -> 抛出 ContentSafetyBlockedException (code=2005)
    服务异常 -> 抛出 ContentSafetyServiceException (code=2004)，除非 fail_open=True
    """
    try:
        rules = await safety_crud.get_enabled_rules_by_scene(db, scene)
    except Exception as exc:
        logger.error("加载内容安全规则失败: scene=%s, error=%s", scene, exc, exc_info=True)
        if fail_open:
            return ContentSafetyCheckResult(
                passed=True,
                decision="allow",
                results=[
                    ContentSafetyFieldResult(field_name=item.field_name, decision="allow")
                    for item in items
                ],
            )
        raise ContentSafetyServiceException() from exc

    field_results: List[ContentSafetyFieldResult] = []
    overall_decision = "allow"
    last_log_id: Optional[uuid.UUID] = None

    for item in items:
        normalized = normalize_text(item.value)

        try:
            political_hit = await _check_political_for_text(item.value)
        except ContentSafetyServiceException:
            if fail_open:
                political_hit = False
            else:
                raise

        decision, matched_rules, message = evaluate_field(rules, item.field_name, item.value)

        if political_hit:
            decision = "block"
            message = build_political_block_message(item.field_name)
            matched_rules = list(matched_rules)
            matched_rule_ids = None
            matched_rule_names = ["political-api"]
        else:
            matched_rule_ids = [str(r.rule_id) for r in matched_rules] if matched_rules else None
            matched_rule_names = [r.rule_name for r in matched_rules] if matched_rules else None
            if matched_rules and not message:
                top = matched_rules[0]
                regulation = getattr(
                    next((r for r in rules if r.id == top.rule_id), None),
                    "regulation_ref",
                    None,
                )
                if regulation:
                    message = f"命中[{getattr(next((r for r in rules if r.id == top.rule_id), None), 'rule_category', '')}]：{regulation}"

        field_result = ContentSafetyFieldResult(
            field_name=item.field_name,
            decision=decision,
            message=message,
            matched_rules=matched_rules if not political_hit else [],
        )
        field_results.append(field_result)

        if decision in ("warn", "block") or matched_rules or political_hit:
            reason_code = "2005" if decision == "block" else ("2006" if decision == "warn" else None)
            log = await safety_crud.create_log(
                db,
                scene=scene,
                resource_type=resource_type,
                resource_id=resource_id,
                target_field=item.field_name,
                user_id=user_id,
                input_value=item.value,
                normalized_value=normalized,
                decision=decision,
                matched_rule_ids=matched_rule_ids,
                matched_rule_names=matched_rule_names,
                reason_code=reason_code,
                reason_message=message,
                request_id=request_id,
                client_ip=client_ip,
            )
            last_log_id = log.id

        if decision == "block":
            overall_decision = "block"
        elif decision == "warn" and overall_decision != "block":
            overall_decision = "warn"

    passed = overall_decision != "block"
    result = ContentSafetyCheckResult(
        passed=passed,
        decision=overall_decision,
        results=field_results,
        log_id=last_log_id,
    )

    if overall_decision == "block":
        block_messages = [r.message for r in field_results if r.decision == "block" and r.message]
        raise ContentSafetyBlockedException(
            block_messages[0] if block_messages else "内容违规",
        )

    return result


async def check_scene_fields(
    db: AsyncSession,
    scene: str,
    field_values: dict,
    **kwargs,
) -> ContentSafetyCheckResult:
    """同一场景下多字段批量校验（逐字段匹配对应规则集）"""
    items = [
        ContentSafetyItem(field_name=name, value=str(value))
        for name, value in field_values.items()
        if value is not None and str(value).strip()
    ]
    if not items:
        return ContentSafetyCheckResult(passed=True, decision="allow", results=[])
    return await check_content_safety(db, scene, items, **kwargs)


async def check_single_field(
    db: AsyncSession,
    scene: str,
    field_name: str,
    value: str,
    **kwargs,
) -> ContentSafetyCheckResult:
    """便捷方法：单字段校验"""
    return await check_content_safety(
        db,
        scene,
        [ContentSafetyItem(field_name=field_name, value=value)],
        **kwargs,
    )


def assert_content_safe_or_raise(result: ContentSafetyCheckResult) -> None:
    if not result.passed:
        raise ContentSafetyBlockedException("内容违规")
