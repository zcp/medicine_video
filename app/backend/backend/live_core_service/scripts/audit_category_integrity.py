"""
分类数据完整性体检脚本（阶段7 前置，V1.1 补充）

体检 6 项（只报告，不自动修复）：
  1. 孤儿分类：is_active=True 且父分类不存在或已停用
  2. 悬空 category_id：experts / expert_departments 指向不存在或已停用的分类
  3. 多主分类：同一直播间存在多个 is_primary=true
  4. 无主分类：直播间有分类关联但 is_primary 全 false
  5. 科室-专家不一致：专家 category_id 与其科室 category_id 不一致

执行方式（容器内）：
  cd /app && python scripts/audit_category_integrity.py

执行方式（docker exec）：
  docker exec live-streaming-saas-v2-main-live_core_service-1 sh -c "cd /app && python scripts/audit_category_integrity.py"

退出码：0=无问题；1=发现问题（供 CI/运维判断）。
"""
import logging
import sys
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.database import engine
from app.models.content_management import Category, LiveRoomCategory
from app.models.experts import Expert
from app.models.expert_departments import ExpertDepartment

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

DBSession = sessionmaker(bind=engine)

MAX_DETAIL_ROWS = 10


def _fmt_issues(rows, header):
    """格式化问题明细（最多 MAX_DETAIL_ROWS 条）"""
    lines = [header]
    if not rows:
        lines.append("  无")
        return "\n".join(lines)
    for row in rows[:MAX_DETAIL_ROWS]:
        lines.append(f"  {row}")
    if len(rows) > MAX_DETAIL_ROWS:
        lines.append(f"  ... 共 {len(rows)} 条（仅显示前 {MAX_DETAIL_ROWS} 条）")
    return "\n".join(lines)


def audit_orphan_categories(session) -> list:
    """① 孤儿分类：active 子分类挂 inactive/不存在父"""
    active_cats = session.execute(
        select(Category.id, Category.parent_id, Category.name).where(
            Category.is_active == True,  # noqa: E712
            Category.parent_id.isnot(None),
        )
    ).all()
    if not active_cats:
        return []
    parent_ids = {c.parent_id for c in active_cats}
    parents = set(
        session.execute(
            select(Category.id).where(
                Category.id.in_(parent_ids),
                Category.is_active == True,  # noqa: E712
            )
        ).scalars().all()
    )
    issues = []
    for c in active_cats:
        if c.parent_id not in parents:
            issues.append(f"id={c.id} name={c.name} parent={c.parent_id}（父不存在或已停用）")
    return issues


def audit_dangling_category_refs(session) -> dict:
    """② 悬空 category_id：专家/科室指向不存在或停用分类"""
    valid_ids = set(
        session.execute(
            select(Category.id).where(Category.is_active == True)  # noqa: E712
        ).scalars().all()
    )
    expert_rows = session.execute(
        select(Expert.id, Expert.name, Expert.category_id).where(
            Expert.category_id.isnot(None),
            Expert.is_active == True,  # noqa: E712 仅检查活跃专家（停用数据不参与体检）
        )
    ).all()
    expert_issues = [
        f"expert_id={e.id} name={e.name} category={e.category_id}（分类不存在或已停用）"
        for e in expert_rows if e.category_id not in valid_ids
    ]
    dept_rows = session.execute(
        select(ExpertDepartment.id, ExpertDepartment.name, ExpertDepartment.category_id).where(
            ExpertDepartment.category_id.isnot(None),
            ExpertDepartment.is_active == True,  # noqa: E712 仅检查活跃科室
        )
    ).all()
    dept_issues = [
        f"department_id={d.id} name={d.name} category={d.category_id}（分类不存在或已停用）"
        for d in dept_rows if d.category_id not in valid_ids
    ]
    return {"experts": expert_issues, "departments": dept_issues}


def audit_multi_primary(session) -> list:
    """③ 多主分类：同一直播间多个 is_primary=true"""
    rows = session.execute(
        select(
            LiveRoomCategory.room_id,
            func.count().filter(LiveRoomCategory.is_primary == True),  # noqa: E712
        )
        .group_by(LiveRoomCategory.room_id)
        .having(func.count().filter(LiveRoomCategory.is_primary == True) > 1)  # noqa: E712
    ).all()
    return [f"room_id={room_id} primary_count={cnt}" for room_id, cnt in rows]


def audit_no_primary(session) -> list:
    """④ 无主分类：有分类关联但 is_primary 全 false"""
    rows = session.execute(
        select(
            LiveRoomCategory.room_id,
            func.count(LiveRoomCategory.category_id),
            func.count().filter(LiveRoomCategory.is_primary == True),  # noqa: E712
        )
        .group_by(LiveRoomCategory.room_id)
    ).all()
    return [
        f"room_id={room_id} category_count={total}（无主分类）"
        for room_id, total, primary_cnt in rows if total > 0 and primary_cnt == 0
    ]


def audit_dept_expert_inconsistent(session) -> list:
    """⑤ 科室-专家不一致：专家 category_id 与其科室 category_id 不同"""
    issues = []
    rows = session.execute(
        select(Expert.id, Expert.name, Expert.category_id, ExpertDepartment.category_id)
        .join(ExpertDepartment, Expert.department_id == ExpertDepartment.id)
        .where(Expert.department_id.isnot(None))
    ).all()
    for expert_id, name, expert_cat, dept_cat in rows:
        if expert_cat != dept_cat:
            issues.append(
                f"expert_id={expert_id} name={name} expert_category={expert_cat} dept_category={dept_cat}（不一致）"
            )
    return issues


def audit_test_category_leaks(session) -> list:
    """⑥ 测试前缀分类 + 层级断链（K5，防测试数据污染生产 + 防树断裂）"""
    from app.core.category_constants import is_test_category_name

    issues = []
    rows = session.execute(
        select(Category.id, Category.name, Category.parent_id).where(Category.is_active == True)  # noqa: E712
    ).all()
    active_ids = {r.id for r in rows}
    for cat_id, name, parent_id in rows:
        if is_test_category_name(name):
            issues.append(f"id={cat_id} name={name}（测试前缀模式，疑似测试数据出网）")
        if parent_id is not None and parent_id not in active_ids:
            issues.append(f"id={cat_id} name={name} parent={parent_id}（层级断链：父分类不存在或已停用）")
    return issues


def main() -> int:
    session = DBSession()
    try:
        print("=" * 60)
        print("分类数据完整性体检报告")
        print(f"数据库: {engine.url.database}")
        print(f"检查时间: {datetime.now().isoformat(timespec='seconds')}")
        print("=" * 60)
        print()

        found_any = False

        # ① 孤儿分类
        orphans = audit_orphan_categories(session)
        found_any = found_any or bool(orphans)
        print(f"[1/6] 孤儿分类（active 子分类挂 inactive/不存在父）— 发现 {len(orphans)} 个")
        print(_fmt_issues(orphans, f"  明细（前 {MAX_DETAIL_ROWS} 条）:"))
        print()

        # ② 悬空 category_id
        dangling = audit_dangling_category_refs(session)
        expert_dangling = dangling["experts"]
        dept_dangling = dangling["departments"]
        found_any = found_any or bool(expert_dangling) or bool(dept_dangling)
        print(f"[2/6] 悬空 category_id — 专家 {len(expert_dangling)} 个 / 科室 {len(dept_dangling)} 个")
        print(_fmt_issues(expert_dangling, "  专家明细:"))
        print(_fmt_issues(dept_dangling, "  科室明细:"))
        print()

        # ③ 多主分类
        multi_primary = audit_multi_primary(session)
        found_any = found_any or bool(multi_primary)
        print(f"[3/6] 多主分类（同直播间多个 is_primary=true）— 发现 {len(multi_primary)} 个直播间")
        print(_fmt_issues(multi_primary, "  明细:"))
        print()

        # ④ 无主分类
        no_primary = audit_no_primary(session)
        found_any = found_any or bool(no_primary)
        print(f"[4/6] 无主分类（有分类关联但无 is_primary）— 发现 {len(no_primary)} 个直播间")
        print(_fmt_issues(no_primary, "  明细:"))
        print()

        # ⑤ 科室-专家不一致
        inconsistent = audit_dept_expert_inconsistent(session)
        found_any = found_any or bool(inconsistent)
        print(f"[5/6] 科室-专家分类不一致 — 发现 {len(inconsistent)} 位专家")
        print(_fmt_issues(inconsistent, "  明细:"))
        print()

        # ⑥ 测试前缀分类 + 层级断链
        test_leaks = audit_test_category_leaks(session)
        found_any = found_any or bool(test_leaks)
        print(f"[6/6] 测试前缀分类 + 层级断链 — 发现 {len(test_leaks)} 个")
        print(_fmt_issues(test_leaks, "  明细:"))

        print("=" * 60)
        if found_any:
            print("结论: 发现数据完整性问题（详见上表），建议治理后再上线强校验。")
            return 1
        print("结论: 未发现数据完整性问题。")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
