#!/usr/bin/env python3
"""
一次性数据迁移脚本：将现有专家的 department 文本映射到 category_id

使用方式：
  docker cp migration_expert_category.py live-streaming-saas-v2-main-live_core_service-1:/app/
  docker exec live-streaming-saas-v2-main-live_core_service-1 python /app/migration_expert_category.py

功能：
  1. 读取所有 categories 和 experts
  2. 根据 department 文本精确匹配 + 模糊匹配 categories.name
  3. 更新 expert.category_id
  4. 输出统计报告
"""

import os
import sys
sys.path.insert(0, '/app')

from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import engine
from app.models.content_management import Category
from app.models.experts import Expert

DBSession = sessionmaker(bind=engine)

# ============================================================
# 映射表：department 文本 → categories 大类名
# ============================================================
MAPPING = {
    # 普通外科
    "普通外科": "普通外科",
    "普外科": "普通外科",
    "胃肠外科": "普通外科",
    "肝胆外科": "普通外科",
    "肝胆胰外科": "普通外科",
    "甲乳外科": "普通外科",
    "血管外科": "血管外科",

    # 神经外科
    "神经外科": "神经外科",
    "神经外科-颅底肿瘤组": "神经外科",
    "神经外科-内镜组": "神经外科",
    "神经外科-血管病组": "神经外科",
    "神经外科-功能神经外科": "神经外科",

    # 心内科
    "心内科": "心内科",
    "心血管内科": "心内科",
    "心内科-冠脉介入组": "心内科",
    "心内科-心律失常组": "心内科",
    "心内科-心衰组": "心内科",

    # 心胸外科
    "心胸外科": "心胸外科",
    "心脏外科": "心胸外科",
    "胸外科": "心胸外科",

    # 骨科
    "骨科": "骨科",
    "骨科-关节外科组": "骨科",
    "骨科-脊柱外科组": "骨科",
    "骨科-创伤组": "骨科",

    # 肿瘤科
    "肿瘤科": "肿瘤科",
    "肿瘤外科": "肿瘤科",
    "肿瘤内科": "肿瘤科",

    # 妇产科
    "妇产科": "妇产科",
    "妇科": "妇产科",
    "产科": "妇产科",

    # 儿科
    "儿科": "儿科",
    "新生儿科": "儿科",

    # 眼科
    "眼科": "眼科",

    # 耳鼻喉科
    "耳鼻喉科": "耳鼻喉科",
    "耳鼻咽喉科": "耳鼻喉科",

    # 消化科
    "消化科": "消化科",
    "消化内科": "消化科",

    # 内分泌科
    "内分泌科": "内分泌科",

    # 泌尿外科
    "泌尿外科": "泌尿外科",

    # 皮肤科
    "皮肤科": "皮肤科",
}


def main():
    print("=" * 60)
    print("  专家分类数据迁移脚本")
    print("=" * 60)

    with DBSession() as db:
        # 1. 读取所有 categories，建立 {name: id} 字典
        categories = {}
        cats = db.query(Category).filter(Category.is_active == True).all()
        for cat in cats:
            categories[cat.name] = cat.id
        print(f"\n📂 已加载 {len(categories)} 个活跃分类: {list(categories.keys())}")

        # 2. 读取所有专家
        experts = db.query(Expert).all()
        print(f"👨‍⚕️ 共 {len(experts)} 位专家待处理\n")

        # 3. 遍历映射
        matched = 0
        unmatched = []
        skipped = 0

        for expert in experts:
            if not expert.department:
                skipped += 1
                continue

            dept = expert.department.strip()

            # 精确匹配
            cat_name = MAPPING.get(dept)

            # 模糊匹配：department 包含映射 key
            if not cat_name:
                for key, val in MAPPING.items():
                    if key in dept or dept in key:
                        cat_name = val
                        break

            # 模糊匹配：直接匹配 categories.name
            if not cat_name:
                for cat_n in categories:
                    if cat_n in dept:
                        cat_name = cat_n
                        break

            if cat_name and cat_name in categories:
                expert.category_id = categories[cat_name]
                matched += 1
                print(f"  ✅ {expert.name[:10]:10s} | {dept[:25]:25s} → {cat_name}")
            else:
                unmatched.append((expert.name, dept))
                print(f"  ❌ {expert.name[:10]:10s} | {dept[:25]:25s} → 未匹配")

        db.commit()

        # 4. 统计报告
        print("\n" + "=" * 60)
        print("  迁移结果统计")
        print("=" * 60)
        print(f"  总专家数:     {len(experts)}")
        print(f"  成功匹配:     {matched}")
        print(f"  跳过(无科室): {skipped}")
        print(f"  未匹配:       {len(unmatched)}")

        if unmatched:
            print("\n  ⚠️ 以下 department 未能匹配到任何分类，请人工确认：")
            for name, dept in unmatched:
                print(f"    - {name} | {dept}")

        print("\n  迁移完成！")


if __name__ == "__main__":
    main()
