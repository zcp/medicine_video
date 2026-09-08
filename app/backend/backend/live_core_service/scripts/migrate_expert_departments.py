#!/usr/bin/env python3
"""
FROZEN — 此脚本为一次性数据迁移，已执行完毕，不应再修改或重新运行。

融合方案 V6：专家 department → expert_departments 数据迁移脚本

功能：
  --dry-run: 输出匹配报告 CSV（只读不写）
  正式模式: 遍历 experts 表，将 department 文本匹配到 expert_departments 表
            并设置 department_id 和 category_id

使用方式：
  cd /app
  python scripts/migrate_expert_departments.py --dry-run > migration_report.csv
  python scripts/migrate_expert_departments.py           # 正式执行

前置条件：
  - V4（expert_departments 表）已执行
  - V5（categories.parent_id）已执行
  - expert_departments 中已预置种子科室数据
"""

import asyncio
import csv
import io
import os
import sys
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# —— 配置 ——
# 使用独立的 MIGRATION_DATABASE_URL，避免与项目的同步 DATABASE_URL 冲突
# 回退到 Docker 容器间通信的 asyncpg 默认值
DATABASE_URL = os.getenv(
    "MIGRATION_DATABASE_URL",
    "postgresql+asyncpg://postgres:CHANGE_ME@postgres:5432/live_core_test"
)

# 分类常量（从单一真相源导入，替代原有的硬编码列表）
from app.core.category_constants import ROOT_CATEGORIES, DEPARTMENT_CATEGORY_MAP


def normalize(text_val: str) -> str:
    """清洗科室文本：去除末尾斜杠和首尾空白"""
    return text_val.rstrip('/.。、, ').strip()


def match_department(normalized: str, root_categories: List[str]) -> Optional[Tuple[str, str]]:
    """
    匹配科室文本 → (matched_dept_name, matched_category_name)。
    返回 None 表示需要人工确认。

    匹配优先级：
    1. 子串匹配（根分类名包含在科室文本中）
    2. 别名表匹配
    """
    # 1. 子串匹配
    for rc in root_categories:
        if rc in normalized:
            return (normalized, rc)

    # 2. 别名表匹配
    mapped = DEPARTMENT_CATEGORY_MAP.get(normalized)
    if mapped:
        return (normalized, mapped)

    return None


async def run_dry_run(session: AsyncSession):
    """Dry-Run：只读不写，输出 CSV 报告到 stdout"""
    # 加载根分类列表（从数据库动态加载，避免硬编码同步问题）
    root_categories = ROOT_CATEGORIES
    print(f"# 使用 {len(root_categories)} 个标准根分类（硬编码，避免测试数据干扰）", file=sys.stderr)
    print(f"# 已加载 {len(root_categories)} 个根分类: {root_categories}", file=sys.stderr)

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
            writer.writerow([expert_id, expert_name, original, "", "其他", "manual_review"])
            unmatched_count += 1

    print(f"\n# Dry-Run 完成：{matched_count} 条可自动匹配，{unmatched_count} 条需人工审核",
          file=sys.stderr)


async def run_migrate(session: AsyncSession):
    """正式迁移：写数据库"""
    # 1. 查询所有有 department 的专家
    result = await session.execute(
        text("SELECT id, name, department FROM experts WHERE department IS NOT NULL")
    )
    rows = result.fetchall()
    print(f"# 共 {len(rows)} 位专家需要迁移", file=sys.stderr)

    # 2. 加载 expert_departments 查找表
    dept_result = await session.execute(
        text("SELECT id, name, category_id FROM expert_departments WHERE is_active = true")
    )
    dept_lookup = {row[1]: (row[0], row[2]) for row in dept_result.fetchall()}
    print(f"# 已加载 {len(dept_lookup)} 个科室", file=sys.stderr)

    # 3. 加载根分类列表
    root_categories = ROOT_CATEGORIES
    print(f"# 使用 {len(root_categories)} 个标准根分类（硬编码，避免测试数据干扰）", file=sys.stderr)

    # 4. 加载"其他"分类 ID
    other_result = await session.execute(
        text("SELECT id FROM categories WHERE name = '其他' AND parent_id IS NULL AND is_active = true")
    )
    other_cat_id = other_result.scalar_one()

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
                    # 匹配到了根分类但科室表中没有独立条目
                    # （如"泌尿外科"→在 dept_lookup 中有"泌尿外科/男科"但没有"泌尿外科"自己）
                    # → 不关联具体科室但设置正确的 category_id
                    cat_result = await session.execute(
                        text("SELECT id FROM categories WHERE name = :cn AND parent_id IS NULL AND is_active = true"),
                        {"cn": matched_cat_name}
                    )
                    cat_row = cat_result.one_or_none()
                    dept_id, cat_id = None, cat_row[0] if cat_row else other_cat_id
            else:
                dept_id, cat_id = None, other_cat_id

        if dept_id:
            await session.execute(
                text("UPDATE experts SET department_id = :dept_id, category_id = :cat_id WHERE id = :eid"),
                {"dept_id": dept_id, "cat_id": cat_id, "eid": expert_id}
            )
            migrated += 1
        else:
            await session.execute(
                text("UPDATE experts SET category_id = :cat_id WHERE id = :eid"),
                {"cat_id": cat_id, "eid": expert_id}
            )
            skipped += 1

        if migrated % 50 == 0:
            print(f"  已迁移 {migrated} 条...", file=sys.stderr)

    await session.commit()
    print(f"\n# 迁移完成：{migrated} 条成功迁移，{skipped} 条未匹配（归入'其他'）", file=sys.stderr)


async def main():
    dry_run = "--dry-run" in sys.argv

    engine = create_async_engine(DATABASE_URL)
    # SQLAlchemy 1.4 兼容：使用 sessionmaker + AsyncSession
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
