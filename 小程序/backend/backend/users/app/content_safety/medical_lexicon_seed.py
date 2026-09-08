"""医学合规词库 seed 与 V2.2 旧规则迁移（users 库）"""

import logging
from typing import List, Tuple

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_safety.cache import invalidate_all_rules_cache
from app.content_safety.medical_lexicon_data import build_medical_rules
from app.content_safety.models import ContentSafetyRule

logger = logging.getLogger(__name__)

TEXT_FIELD_MATRIX: dict[str, List[str]] = {
    "nickname": ["nickname", "bio"],
}

MEDICAL_RULES: List[dict] = build_medical_rules(TEXT_FIELD_MATRIX)

_LEGACY_SUFFIXES = ("外链", "联系方式", "敏感词", "广告引流")

_SYNC_FIELDS = (
    "pattern",
    "action",
    "severity",
    "priority",
    "enabled",
    "remark",
    "binding_level",
    "rule_category",
    "regulation_ref",
    "match_type",
    "target_field",
    "scene",
)


async def disable_legacy_v22_rules(db: AsyncSession) -> int:
    """停用 V2.2 基线 nickname 规则及 avatar image_meta 规则"""
    suffix_conditions = [ContentSafetyRule.rule_name.like(f"%{s}") for s in _LEGACY_SUFFIXES]
    stmt = (
        update(ContentSafetyRule)
        .where(
            or_(
                *suffix_conditions,
                ContentSafetyRule.rule_name.like("avatar-avatar_url-%"),
            ),
            ContentSafetyRule.enabled.is_(True),
        )
        .values(enabled=False)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    disabled = result.rowcount or 0
    if disabled:
        logger.info("已停用 %d 条 V2.2 旧内容安全规则", disabled)
    return disabled


async def seed_medical_lexicon_rules(db: AsyncSession) -> Tuple[int, int]:
    """幂等写入/同步医学合规规则，返回 (新增数, 更新数)"""
    inserted = 0
    updated = 0
    for rule_data in MEDICAL_RULES:
        stmt = select(ContentSafetyRule).where(ContentSafetyRule.rule_name == rule_data["rule_name"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            db.add(ContentSafetyRule(**rule_data))
            inserted += 1
            continue

        changed = False
        for field in _SYNC_FIELDS:
            if field not in rule_data:
                continue
            new_val = rule_data[field]
            if getattr(existing, field) != new_val:
                setattr(existing, field, new_val)
                changed = True
        if changed:
            db.add(existing)
            updated += 1

    if inserted or updated:
        await db.flush()
        logger.info(
            "医学合规内容安全规则同步完成：新增 %d，更新 %d",
            inserted,
            updated,
        )
    return inserted, updated


async def run_medical_lexicon_seed(db: AsyncSession) -> int:
    """完整迁移：停用旧规则 → 写入/同步新规则 → 失效缓存；返回变更条数"""
    await disable_legacy_v22_rules(db)
    inserted, updated = await seed_medical_lexicon_rules(db)
    invalidate_all_rules_cache()
    return inserted + updated
