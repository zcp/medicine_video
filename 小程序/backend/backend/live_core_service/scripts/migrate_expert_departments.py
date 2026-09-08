#!/usr/bin/env python3
"""
融合方案：专家 department → expert_departments 数据迁移脚本（wechat-v1）

功能：
  --dry-run: 输出匹配报告 CSV（只读不写）
  正式模式: 遍历 experts 表，将 department 文本匹配到 expert_departments 表
            并设置 department_id 和 category_id

使用方式：
  cd /app
  python scripts/migrate_expert_departments.py --dry-run > migration_report.csv
  python scripts/migrate_expert_departments.py

前置条件：
  - migrations/20260812_create_expert_departments.sql 已执行
  - categories 含「其他」
  - 不执行 V7 删列
"""

import asyncio
import csv
import os
import sys
from typing import List, Optional, Tuple

# 保证以 scripts/xxx.py 直接运行时可导入 app
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVICE_ROOT = os.path.dirname(_SCRIPT_DIR)
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    try:
        from app.core.config import settings
        DATABASE_URL = settings.DATABASE_URL
    except Exception:
        DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/live_core_test"

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

from app.core.category_constants import ROOT_CATEGORIES, DEPARTMENT_CATEGORY_MAP, OTHER_CATEGORY_NAME


def normalize(text_val: str) -> str:
    """清洗科室文本：去除末尾斜杠和首尾空白"""
    return text_val.rstrip('/.。、, ').strip()


def match_department(normalized: str, root_categories: List[str]) -> Optional[Tuple[str, str]]:
    """匹配科室文本 → (matched_dept_name, matched_category_name)。"""
    mapped = DEPARTMENT_CATEGORY_MAP.get(normalized)
    if mapped:
        return (normalized, mapped)

    for rc in root_categories:
        if rc in normalized:
            return (normalized, rc)

    return None


async def run_dry_run(session: AsyncSession):
    """Dry-Run：只读不写，输出 CSV 报告到 stdout"""
    root_categories = ROOT_CATEGORIES
    print(f"# 使用 {len(root_categories)} 个标准根分类", file=sys.stderr)

    writer = csv.writer(sys.stdout)
    writer.writerow(["expert_id", "name", "original_department", "matched_dept", "matched_category", "status"])

    result = await session.execute(
        text("SELECT id, name, department FROM experts WHERE department IS NOT NULL ORDER BY created_at")
    )
    rows = result.fetchall()
    print(f"# 共 {len(rows)} 位专家需要迁移", file=sys.stderr)

    matched_count = 0
    unmatched_count = 0

    for row in rows:
        expert_id = str(row[0])
        expert_name = row[1]
        original = row[2]
        normalized = normalize(original)

        match_result = match_department(normalized, root_categories)
        if match_result:
            matched_dept, matched_cat = match_result
            writer.writerow([expert_id, expert_name, original, matched_dept, matched_cat, "auto"])
            matched_count += 1
        else:
            writer.writerow([expert_id, expert_name, original, "", OTHER_CATEGORY_NAME, "manual_review"])
            unmatched_count += 1

    print(
        f"\n# Dry-Run 完成：{matched_count} 条可自动匹配，{unmatched_count} 条需人工审核",
        file=sys.stderr,
    )


async def run_migrate(session: AsyncSession):
    """正式迁移：写数据库"""
    result = await session.execute(
        text("SELECT id, name, department FROM experts WHERE department IS NOT NULL")
    )
    rows = result.fetchall()
    print(f"# 共 {len(rows)} 位专家需要迁移", file=sys.stderr)

    dept_result = await session.execute(
        text("SELECT id, name, category_id FROM expert_departments WHERE is_active = true")
    )
    dept_lookup = {row[1]: (row[0], row[2]) for row in dept_result.fetchall()}
    print(f"# 已加载 {len(dept_lookup)} 个科室", file=sys.stderr)

    root_categories = ROOT_CATEGORIES
    print(f"# 使用 {len(root_categories)} 个标准根分类", file=sys.stderr)

    other_result = await session.execute(
        text("SELECT id FROM categories WHERE name = :n AND is_active = true LIMIT 1"),
        {"n": OTHER_CATEGORY_NAME},
    )
    other_cat_id = other_result.scalar_one_or_none()
    if not other_cat_id:
        raise RuntimeError(f"兜底分类「{OTHER_CATEGORY_NAME}」不存在，请先执行 seed.py")

    migrated = 0
    skipped = 0

    for row in rows:
        expert_id = row[0]
        original = row[2]
        normalized = normalize(original)

        if normalized in dept_lookup:
            dept_id, cat_id = dept_lookup[normalized]
        else:
            match_result = match_department(normalized, root_categories)
            if match_result:
                matched_dept_name, matched_cat_name = match_result
                if matched_dept_name in dept_lookup:
                    dept_id, cat_id = dept_lookup[matched_dept_name]
                else:
                    cat_result = await session.execute(
                        text("SELECT id FROM categories WHERE name = :cn AND is_active = true LIMIT 1"),
                        {"cn": matched_cat_name},
                    )
                    cat_row = cat_result.one_or_none()
                    dept_id, cat_id = None, cat_row[0] if cat_row else other_cat_id
            else:
                dept_id, cat_id = None, other_cat_id

        if dept_id:
            await session.execute(
                text(
                    "UPDATE experts SET department_id = :dept_id, category_id = :cat_id WHERE id = :eid"
                ),
                {"dept_id": dept_id, "cat_id": cat_id, "eid": expert_id},
            )
            migrated += 1
        else:
            await session.execute(
                text("UPDATE experts SET category_id = :cat_id WHERE id = :eid"),
                {"cat_id": cat_id, "eid": expert_id},
            )
            skipped += 1

        if migrated % 50 == 0 and migrated:
            print(f"  已迁移 {migrated} 条...", file=sys.stderr)

    await session.commit()
    print(
        f"\n# 迁移完成：{migrated} 条成功迁移，{skipped} 条未匹配（归入'{OTHER_CATEGORY_NAME}'）",
        file=sys.stderr,
    )


async def main():
    dry_run = "--dry-run" in sys.argv

    engine = create_async_engine(DATABASE_URL)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        if dry_run:
            print("# 迁移脚本 Dry-Run 报告", file=sys.stderr)
            await run_dry_run(session)
        else:
            print("# 正式迁移开始...", file=sys.stderr)
            await run_migrate(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
