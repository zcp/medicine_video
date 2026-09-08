"""
分类同步一致性检查 Gate — 阶段 3 M2

对照 category_constants.py 单一真相源与数据库实际数据：
  ① 常量 35 条分类是否全部在库（name + 层级 parent_name 匹配）
  ② standard 标记是否一致（常量 false ↔ DB false；常量 true ↔ DB true）
  ③ 层级结构（root 16 / child 19）是否一致

用法（容器内）:
    cd /app && python scripts/check_consistency.py
退出码: 0=一致；1=存在漂移（供部署 CheckList / 未来 CI 使用）
"""
import sys
import logging

from sqlalchemy import text
from app.database import engine
from app.core.category_constants import CATEGORIES_SEED_DATA

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)


def check_consistency() -> list:
    """返回漂移清单（空列表 = 一致）"""
    issues = []

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, parent_id, standard FROM categories WHERE is_active = true")).fetchall()

    db_by_name = {}
    id_by_name = {}
    for cid, name, parent_id, standard in rows:
        db_by_name.setdefault(name, []).append({"parent_id": parent_id, "standard": standard})
        id_by_name.setdefault(name, []).append(cid)

    # ① 常量分类是否全部在库
    for data in CATEGORIES_SEED_DATA:
        name = data["name"]
        if name not in db_by_name:
            issues.append(f"常量分类缺失: {name}")
            continue
        # ② standard 一致性（常量 false 的必须 DB false；常量 true 的必须 DB true）
        for rec in db_by_name[name]:
            if bool(rec["standard"]) != bool(data.get("standard", True)):
                issues.append(
                    f"standard 漂移: {name} 常量={data.get('standard', True)} DB={rec['standard']}"
                )
        # ③ 层级一致性（逐条：常量的 parent_name ↔ DB parent_id）
        parent_name = data.get("parent_name")
        if parent_name is None:
            for rec in db_by_name[name]:
                if rec["parent_id"] is not None:
                    issues.append(f"层级漂移: {name} 常量=根分类 DB=子分类(parent={rec['parent_id']})")
        else:
            parent_ids = id_by_name.get(parent_name, [])
            for rec in db_by_name[name]:
                if rec["parent_id"] not in parent_ids:
                    issues.append(
                        f"层级漂移: {name} 常量父={parent_name} DB父={rec['parent_id']}"
                    )

    return issues


def main() -> int:
    print("=" * 60)
    print("分类同步一致性检查（category_constants.py vs DB）")
    print("=" * 60)
    issues = check_consistency()
    if issues:
        print(f"发现 {len(issues)} 项漂移:")
        for i in issues:
            print(f"  ❌ {i}")
        print("结论: 常量与数据库不一致，请治理后再部署。")
        return 1
    print(f"✅ 一致：{len(CATEGORIES_SEED_DATA)} 条常量分类、层级、standard 全部对齐")
    print("结论: 未发现漂移。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
