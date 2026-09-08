#!/usr/bin/env python3
"""
标签种子数据脚本 - 为本地开发环境初始化测试标签

使用方式：
  docker cp "d:\live-streaming-saas-v2-main\backend\live_core_service\app\seed_tags.py" live-streaming-saas-v2-main-live_core_service-1:/app/seed_tags.py
  docker exec live-streaming-saas-v2-main-live_core_service-1 sh -c "cd /app && python seed_tags.py"

插入内容：
  - 20 个医学直播常用标签
  - 8 个场次-标签关联（对应 seed.py 中已有的 sessions）
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.database import engine
from app.models.content_management import Tag, SessionTag
from app.models.live_core import LiveSession, LiveRoom

DBSession = sessionmaker(bind=engine)

# ============================================================
# TEST USER ID (matching seed.py)
# ============================================================
SEED_USER_ID = uuid.UUID("bc1d319e-480f-48f9-bfd7-69b5d7bea88a")

# ============================================================
# Tag Data: 20 tags across 4 categories
# ============================================================
# Tags grouped by purpose:
#   A) Format tags (直播形式): 手术直播, 病例讨论, 学术讲座, 指南解读, MDT讨论
#   B) Technique tags (技术/术式): 腹腔镜, 微创手术, 内镜技术, 介入治疗, 显微手术
#   C) Disease tags (疾病/领域): 冠心病, 心衰, 动脉瘤, 新生儿, 白内障, 肿瘤
#   D) Audience tags (受众): 住院医, 进修学习, 专家访谈, 手术演示

TAGS_DATA = [
    # ---- 格式标签 ----
    {"name": "手术直播",     "slug": "surgery-live",     "description": "实时手术演示与讲解"},
    {"name": "病例讨论",     "slug": "case-discussion",  "description": "疑难病例多角度讨论分析"},
    {"name": "学术讲座",     "slug": "academic-lecture", "description": "专题学术报告与知识更新"},
    {"name": "指南解读",     "slug": "guideline-review", "description": "最新临床指南解读与实践"},
    {"name": "MDT讨论",      "slug": "mdt-discussion",   "description": "多学科团队协作诊疗讨论"},

    # ---- 技术/术式标签 ----
    {"name": "腹腔镜",       "slug": "laparoscopy",      "description": "腹腔镜微创手术技术"},
    {"name": "微创手术",     "slug": "minimally-invasive","description": "各类微创手术技术"},
    {"name": "内镜技术",     "slug": "endoscopy",         "description": "消化内镜/神经内镜等"},
    {"name": "介入治疗",     "slug": "interventional",    "description": "血管介入与导管治疗"},
    {"name": "显微手术",     "slug": "microsurgery",      "description": "显微外科精细操作技术"},

    # ---- 疾病/领域标签 ----
    {"name": "冠心病",       "slug": "coronary-disease",  "description": "冠状动脉粥样硬化性心脏病"},
    {"name": "心衰",         "slug": "heart-failure",     "description": "心力衰竭诊治与管理"},
    {"name": "动脉瘤",       "slug": "aneurysm",          "description": "颅内及外周动脉瘤"},
    {"name": "新生儿",       "slug": "neonatology",       "description": "新生儿疾病与重症管理"},
    {"name": "白内障",       "slug": "cataract",          "description": "白内障手术与术后管理"},
    {"name": "颅底肿瘤",     "slug": "skull-base-tumor",  "description": "颅底肿瘤手术与综合治疗"},
    {"name": "胃癌",         "slug": "gastric-cancer",    "description": "胃癌手术与综合治疗"},
    {"name": "心律失常",     "slug": "arrhythmia",        "description": "心律失常诊断与治疗"},

    # ---- 受众/场景标签 ----
    {"name": "住院医培训",   "slug": "resident-training", "description": "面向住院医师规范化培训"},
    {"name": "手术演示",     "slug": "surgical-demo",     "description": "手术操作步骤演示与讲解"},
]

# ============================================================
# Session-Tag mappings
# Maps seed session titles (from seed.py) to tag names
# ============================================================
SESSION_TAG_MAP = [
    # 腔腔三人行 | 普通外科手术分享系列 (finished)
    # → 术式分享，腹腔镜肝脏手术
    {
        "session_title_match": "%腔腔三人行%",
        "tags": ["手术直播", "腹腔镜", "微创手术", "胃癌", "住院医培训"],
    },
    # 神经外科技术论坛 | 内镜与显微手术专场 (finished)
    {
        "session_title_match": "%内镜与显微手术%",
        "tags": ["内镜技术", "显微手术", "颅底肿瘤", "学术讲座"],
    },
    # 脑血管病外科 | 动脉瘤与血管畸形 (scheduled)
    {
        "session_title_match": "%动脉瘤%血管畸形%",
        "tags": ["动脉瘤", "介入治疗", "显微手术", "病例讨论"],
    },
    # 中山一院胃肠外科 | 腹腔镜手术技巧直播 (live)
    {
        "session_title_match": "%腹腔镜手术技巧直播%",
        "tags": ["手术直播", "腹腔镜", "微创手术", "胃癌", "手术演示"],
    },
    # 心内科学术直播 | 冠心病与心衰管理 (finished)
    {
        "session_title_match": "%冠心病%心衰管理%",
        "tags": ["冠心病", "心衰", "心律失常", "指南解读", "学术讲座"],
    },
    # 妇产科围手术期管理 (scheduled)
    {
        "session_title_match": "%剖宫产%宫腔镜%",
        "tags": ["微创手术", "病例讨论", "住院医培训"],
    },
    # 儿科疑难病例讨论 | 新生儿重症管理 (live)
    {
        "session_title_match": "%新生儿重症管理%",
        "tags": ["新生儿", "病例讨论", "MDT讨论"],
    },
    # 眼科显微手术技巧 | 白内障与玻璃体切除 (finished)
    {
        "session_title_match": "%白内障%玻璃体切除%",
        "tags": ["显微手术", "白内障", "手术演示", "学术讲座"],
    },
]


def seed_tags(db):
    """幂等插入标签"""
    print("=" * 60)
    print("🏷️  插入标签种子数据...")
    print("=" * 60)

    tag_map: dict[str, Tag] = {}  # name -> Tag
    created = 0
    skipped = 0

    for tag_data in TAGS_DATA:
        existing = db.query(Tag).filter_by(name=tag_data["name"]).first()
        if existing:
            tag_map[tag_data["name"]] = existing
            skipped += 1
            print(f"  ⏭️  跳过（已存在）: {tag_data['name']}")
        else:
            tag = Tag(
                id=uuid.uuid4(),
                name=tag_data["name"],
                slug=tag_data["slug"],
                description=tag_data["description"],
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(tag)
            tag_map[tag_data["name"]] = tag
            created += 1
            print(f"  ✅ 创建: {tag_data['name']}")

    db.flush()
    print(f"\n📊 标签统计: 新建 {created}, 跳过 {skipped}, 总计 {len(tag_map)}")

    return tag_map


def seed_session_tags(db, tag_map: dict[str, Tag]):
    """为已有场次关联标签（幂等，按 session+tag 去重）"""
    print("\n" + "=" * 60)
    print("🔗 为场次关联标签...")
    print("=" * 60)

    linked = 0
    skipped = 0
    not_found = 0

    for mapping in SESSION_TAG_MAP:
        # LiveSession 没有 title 字段，通过关联 LiveRoom 的 title 匹配
        session = db.query(LiveSession).join(LiveRoom).filter(
            LiveRoom.title.ilike(mapping["session_title_match"])
        ).first()

        if not session:
            not_found += 1
            print(f"  ⚠️  未找到场次: {mapping['session_title_match']}")
            continue

        session_title_short = session.room.title[:40]
        for tag_name in mapping["tags"]:
            tag = tag_map.get(tag_name)
            if not tag:
                print(f"  ⚠️  标签不存在: {tag_name}")
                continue

            # 幂等检查
            existing_link = db.query(SessionTag).filter_by(
                session_id=session.id, tag_id=tag.id
            ).first()
            if existing_link:
                skipped += 1
            else:
                session_tag = SessionTag(
                    session_id=session.id,
                    tag_id=tag.id,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(session_tag)
                linked += 1
                print(f"  🔗 [{session_title_short}] ← #{tag_name}")

    db.flush()
    print(f"\n📊 关联统计: 新建 {linked}, 跳过 {skipped}, 场次未找到 {not_found}")


def main():
    db = DBSession()
    try:
        tag_map = seed_tags(db)
        seed_session_tags(db, tag_map)
        db.commit()
        print("\n✅ 标签种子数据插入完成！")
    except Exception as e:
        db.rollback()
        print(f"\n❌ 失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
