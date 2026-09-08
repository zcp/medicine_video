#!/usr/bin/env python3
"""
种子数据脚本 - 为本地开发环境初始化测试数据

使用方式（两步）：
  # 步骤1：将专家CSV复制到容器（只需执行一次）
  docker cp "D:\\wechat\\xwechat_files\\wxid_vuwbstum7hx822_f849\\msg\\file\\2026-03\\experts_cleaned_top400.csv" live-streaming-saas-v2-main-live_core_service-1:/app/experts.csv

  # 步骤2：运行种子脚本
  docker exec live-streaming-saas-v2-main-live_core_service-1 sh -c "cd /app && python seed.py"

插入内容：
  - 15 个医学分类
  - 400 名专家（来自CSV，如已复制）
  - 5 个直播间 + 场次（含1条真实回放链接）
  - 4 条首页焦点图
"""

import csv
import uuid
import hashlib
import os
import sys
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import sessionmaker

from app.database import engine
from app.models.content_management import Category
from app.models.experts import Expert
from app.models.live_core import LiveRoom, LiveSession, LiveSessionStatus, SessionStatistics
from app.models.homepage_search import FeaturedContent
from app.models.live_features import LiveRoomTab, LiveRoomTabContentType
from app.models.brand import Brand

DBSession = sessionmaker(bind=engine)

# ============================================================
# 全局配置
# ============================================================

# 测试用户ID（AN_1 用户的 public_id，从登录日志获取）
SEED_USER_ID = uuid.UUID("bc1d319e-480f-48f9-bfd7-69b5d7bea88a")

# 专家CSV路径（复制到容器后的路径）
EXPERTS_CSV_PATH = "/app/experts.csv"

# ============================================================
# 分类种子数据（V2：两级分类体系）
# parent=None 表示一级分类，parent="父分类名" 表示二级分类
# ============================================================
CATEGORIES_DATA = [
    # ---- 一级分类（parent=None）----
    {"name": "普通外科",   "slug": "general-surgery",        "sort_order": 1,  "parent": None},
    {"name": "神经外科",   "slug": "neurosurgery",           "sort_order": 2,  "parent": None},
    {"name": "泌尿外科",   "slug": "urology",                "sort_order": 3,  "parent": None},
    {"name": "骨科",       "slug": "orthopedics",            "sort_order": 4,  "parent": None},
    {"name": "妇产科",     "slug": "obstetrics-gynecology",  "sort_order": 5,  "parent": None},
    {"name": "心内科",     "slug": "cardiology",             "sort_order": 6,  "parent": None},
    {"name": "心胸外科",   "slug": "cardiothoracic-surgery", "sort_order": 7,  "parent": None},
    {"name": "血管外科",   "slug": "vascular-surgery",       "sort_order": 8,  "parent": None},
    {"name": "器官移植科", "slug": "organ-transplant",       "sort_order": 9,  "parent": None},
    {"name": "眼科",       "slug": "ophthalmology",          "sort_order": 10, "parent": None},
    {"name": "耳鼻喉科",   "slug": "ent",                    "sort_order": 11, "parent": None},
    {"name": "消化科",     "slug": "gastroenterology",       "sort_order": 12, "parent": None},
    {"name": "内分泌科",   "slug": "endocrinology",          "sort_order": 13, "parent": None},
    {"name": "肿瘤科",     "slug": "oncology",               "sort_order": 14, "parent": None},
    {"name": "整形外科",   "slug": "plastic-surgery",        "sort_order": 15, "parent": None},
    {"name": "皮肤科",     "slug": "dermatology",            "sort_order": 16, "parent": None},
    {"name": "口腔科",     "slug": "stomatology",            "sort_order": 17, "parent": None},
    {"name": "儿科",       "slug": "pediatrics",             "sort_order": 18, "parent": None},
    {"name": "其他",       "slug": "other",                  "sort_order": 99, "parent": None},

    # ---- 二级分类（parent=父分类名）----
    # 普通外科
    {"name": "胆胰外科",         "slug": "hepatobiliary-pancreatic",   "sort_order": 1, "parent": "普通外科"},
    {"name": "肝外科",           "slug": "liver-surgery",              "sort_order": 2, "parent": "普通外科"},
    {"name": "胃肠外科",         "slug": "gastrointestinal-surgery",   "sort_order": 3, "parent": "普通外科"},
    {"name": "乳腺外科",         "slug": "breast-surgery",             "sort_order": 4, "parent": "普通外科"},
    {"name": "甲状腺外科",       "slug": "thyroid-surgery",            "sort_order": 5, "parent": "普通外科"},
    {"name": "小儿外科",         "slug": "pediatric-surgery",          "sort_order": 6, "parent": "普通外科"},
    # 骨科
    {"name": "脊柱外科",         "slug": "spine-surgery",              "sort_order": 1, "parent": "骨科"},
    {"name": "关节外科",         "slug": "joint-surgery",              "sort_order": 2, "parent": "骨科"},
    {"name": "骨肿瘤科",         "slug": "bone-tumor",                 "sort_order": 3, "parent": "骨科"},
    {"name": "运动医学科",       "slug": "sports-medicine",            "sort_order": 4, "parent": "骨科"},
    # 妇产科
    {"name": "妇科",             "slug": "gynecology",                 "sort_order": 1, "parent": "妇产科"},
    {"name": "产科",             "slug": "obstetrics",                 "sort_order": 2, "parent": "妇产科"},
    {"name": "生殖医学中心",     "slug": "reproductive-medicine",      "sort_order": 3, "parent": "妇产科"},
    # 泌尿外科
    {"name": "男科",             "slug": "andrology",                  "sort_order": 1, "parent": "泌尿外科"},
    # 耳鼻喉科
    {"name": "鼻专科",           "slug": "nasal",                      "sort_order": 1, "parent": "耳鼻喉科"},
    {"name": "耳专科",           "slug": "otology",                    "sort_order": 2, "parent": "耳鼻喉科"},
    {"name": "咽喉专科",         "slug": "laryngology",                "sort_order": 3, "parent": "耳鼻喉科"},
    # 心胸外科
    {"name": "胸外科",           "slug": "thoracic-surgery",           "sort_order": 1, "parent": "心胸外科"},
    # 整形外科
    {"name": "烧伤与创面修复科", "slug": "burn-wound-repair",          "sort_order": 1, "parent": "整形外科"},
    # 口腔科
    {"name": "口腔颌面外科",     "slug": "oral-maxillofacial",         "sort_order": 1, "parent": "口腔科"},
    {"name": "口内修复科",       "slug": "oral-restoration",           "sort_order": 2, "parent": "口腔科"},
]

# ============================================================
# 首页焦点图种子数据
# 封面图使用 Unsplash 公开可访问图片（医疗主题）
# ============================================================
FEATURED_CONTENTS_DATA = [
    {
        "title": "腔腔三人行第36期：微创肝脏手术中转开腹视频分享",
        "subtitle": "中山大学附属第一医院普通外科 | 腹腔镜技术专场",
        "image_url": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=450&fit=crop",
        "target_type": "room",
        "target_room_title": "腔腔三人行 | 普通外科手术分享系列",
        "sort_order": 1,
    },
    {
        "title": "神经外科前沿：内镜微创颅底肿瘤手术技术交流",
        "subtitle": "中山大学附属第一医院 | 神经外科学术峰会直播",
        "image_url": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&h=450&fit=crop",
        "target_type": "room",
        "target_room_title": "神经外科技术论坛 | 内镜与显微手术专场",
        "sort_order": 2,
    },
    {
        "title": "垂体瘤手术与围手术期管理新进展",
        "subtitle": "中山一院神经外科垂体瘤专场直播",
        "image_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&h=450&fit=crop",
        "target_type": "room",
        "target_room_title": "脑血管病外科 | 动脉瘤与血管畸形手术专场",
        "sort_order": 3,
    },
    {
        "title": "胃肠外科手术技巧：腹腔镜胃癌根治术操作规范",
        "subtitle": "外科手术技巧系列 | 多中心专家直播分享",
        "image_url": "https://images.unsplash.com/photo-1551076805-e1869033e561?w=800&h=450&fit=crop",
        "target_type": "room",
        "target_room_title": "中山一院胃肠外科 | 腹腔镜手术技巧直播",
        "sort_order": 4,
    },
    {
        "title": "心内科学术直播：冠心病介入治疗与围术期管理",
        "subtitle": "胸痛中心联合会诊 | 冠心病诊疗专题",
        "image_url": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd45?w=800&h=450&fit=crop",
        "target_type": "room",
        "target_room_title": "心内科学术直播 | 冠心病与心衰管理新进展",
        "sort_order": 5,
    },
]

# ============================================================
# 品牌种子数据
# ============================================================
BRANDS_DATA = [
    {
        "name": "迈瑞医疗",
        "slug": "mindray",
        "logo_url": "https://images.unsplash.com/photo-1581093458791-9f3c3900e2f3?w=256&h=256&fit=crop",
        "description": "专注于医疗器械与生命信息与支持领域的品牌合作伙伴。",
        "website_url": "https://www.mindray.com/",
        "sort_order": 1,
    },
    {
        "name": "联影医疗",
        "slug": "united-imaging",
        "logo_url": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=256&h=256&fit=crop",
        "description": "影像设备与智慧医疗解决方案合作品牌。",
        "website_url": "https://www.united-imaging.com/",
        "sort_order": 2,
    },
    {
        "name": "西门子医疗",
        "slug": "siemens-healthineers",
        "logo_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=256&h=256&fit=crop",
        "description": "医学影像、实验室诊断与临床信息系统品牌。",
        "website_url": "https://www.siemens-healthineers.com/",
        "sort_order": 3,
    },
    {
        "name": "飞利浦医疗",
        "slug": "philips-healthcare",
        "logo_url": "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=256&h=256&fit=crop",
        "description": "超声、监护、手术室与患者管理解决方案品牌。",
        "website_url": "https://www.philips.com/healthcare",
        "sort_order": 4,
    },
    {
        "name": "东软医疗",
        "slug": "neusoft-medical",
        "logo_url": "https://images.unsplash.com/photo-1629904853716-f0bc54eea481?w=256&h=256&fit=crop",
        "description": "CT、MRI、PET-CT等影像设备及临床应用品牌。",
        "website_url": "https://medical.neusoft.com/",
        "sort_order": 5,
    },
    {
        "name": "奥林巴斯医疗",
        "slug": "olympus-medical",
        "logo_url": "https://images.unsplash.com/photo-1474511320723-9a56873867b5?w=256&h=256&fit=crop",
        "description": "消化内镜、泌尿外科与手术成像领域合作品牌。",
        "website_url": "https://www.olympus-global.com/medical/",
        "sort_order": 6,
    },
    {
        "name": "波士顿科学",
        "slug": "boston-scientific",
        "logo_url": "https://images.unsplash.com/photo-1504439468489-c8920d796a29?w=256&h=256&fit=crop",
        "description": "心血管、介入与内窥镜治疗方向合作品牌。",
        "website_url": "https://www.bostonscientific.com/",
        "sort_order": 7,
    },
    {
        "name": "美敦力",
        "slug": "medtronic",
        "logo_url": "https://images.unsplash.com/photo-1551190822-a9333d879b1f?w=256&h=256&fit=crop",
        "description": "心血管、神经科学、外科与糖尿病管理解决方案品牌。",
        "website_url": "https://www.medtronic.com/",
        "sort_order": 8,
    },
    {
        "name": "强生医疗",
        "slug": "johnson-and-johnson-medical",
        "logo_url": "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=256&h=256&fit=crop",
        "description": "外科手术器械、骨科与微创外科合作品牌。",
        "website_url": "https://www.jnjmedicaldevices.com/",
        "sort_order": 9,
    },
    {
        "name": "史赛克",
        "slug": "stryker",
        "logo_url": "https://images.unsplash.com/photo-1516542076529-1ea3854896e1?w=256&h=256&fit=crop",
        "description": "骨科、神经外科和内窥镜领域的医疗设备品牌。",
        "website_url": "https://www.stryker.com/",
        "sort_order": 10,
    },
]

# ============================================================
# 直播间 + 场次种子数据
# playback_url 使用真实可播放的 HLS 流
# ============================================================
now = datetime.now(timezone.utc)

LIVE_ROOMS_DATA = [
    {
        "title": "腔腔三人行 | 普通外科手术分享系列",
        "description": "中山大学附属第一医院普通外科医生联合直播，分享肝胆胰外科、胃肠外科手术视频和临床经验。每期邀请不同专科专家参与讨论。",
        "cover_url": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&h=300&fit=crop",
        "category_name": "普通外科",
        "sessions": [
            {
                "status": "finished",
                "start_time": datetime(2023, 12, 9, 10, 0, tzinfo=timezone.utc),
                "end_time": datetime(2023, 12, 9, 12, 0, tzinfo=timezone.utc),
                "playback_url": "https://mp2.dayilive.com/clip/7539795878.m3u8",
                "viewer_count": 1280,
            }
        ],
        "tabs": [
            {
                "tab_key": "intro",
                "title": "直播简介",
                "content_type": "text",
                "text_content": "本系列由中山大学附属第一医院普通外科团队主理，每期围绕肝胆胰外科、胃肠外科手术视频展开，邀请不同专科专家进行实战点评与经验分享。适合外科住院医、进修医师及有兴趣的外科同道观看学习。",
                "sort_order": 0,
            },
            {
                "tab_key": "agenda",
                "title": "本期议程",
                "content_type": "text",
                "text_content": "18:00 - 18:10  开场介绍\n18:10 - 19:00  微创肝脏手术视频回放（腹腔镜左肝外叶切除术）\n19:00 - 19:30  术中关键步骤解析\n19:30 - 20:00  专家点评与Q&A\n20:00 - 20:30  延伸讨论：中转开腹指征",
                "sort_order": 1,
            },
            {
                "tab_key": "poster",
                "title": "会议海报",
                "content_type": "image",
                "image_url": "https://images.unsplash.com/photo-1504439468489-c8920d796a29?w=600&h=800&fit=crop",
                "sort_order": 2,
            },
        ],
    },
    {
        "title": "神经外科技术论坛 | 内镜与显微手术专场",
        "description": "聚焦神经外科内镜技术、垂体瘤微创手术、颅底肿瘤处理等前沿话题，定期邀请国内顶尖专家分享经验和最新进展。",
        "cover_url": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=400&h=300&fit=crop",
        "category_name": "神经外科",
        "sessions": [
            {
                "status": "finished",
                "start_time": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 11, 30, tzinfo=timezone.utc),
                "playback_url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8",
                "viewer_count": 860,
            }
        ],
        "tabs": [
            {
                "tab_key": "intro",
                "title": "论坛介绍",
                "content_type": "mixed",
                "text_content": "神经外科技术论坛聚焦内镜与显微手术前沿技术，每期邀请国内知名神经外科专家就垂体瘤、颅底肿瘤、脑血管病等复杂病例展开深度讨论。",
                "image_url": "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=600&h=300&fit=crop",
                "sort_order": 0,
            },
            {
                "tab_key": "speakers",
                "title": "主讲专家",
                "content_type": "text",
                "text_content": "▶ 张教授（中山一院神经外科主任）\n  专长：颅底肿瘤显微手术、经鼻内镜垂体瘤\n\n▶ 李教授（南方医科大学附属医院）\n  专长：脑血管病外科，颅内动脉瘤夹闭\n\n▶ 王副教授（广州医科大学附属第一医院）\n  专长：神经内镜技术推广与培训",
                "sort_order": 1,
            },
        ],
    },
    {
        "title": "脑血管病外科 | 动脉瘤与血管畸形手术专场",
        "description": "脑血管病显微手术与介入治疗专场，涵盖颅内动脉瘤、脑动静脉畸形等复杂疾病的手术视频和术前术后分析。",
        "cover_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=400&h=300&fit=crop",
        "category_name": "神经外科",
        "sessions": [
            {
                "status": "scheduled",
                "start_time": now + timedelta(days=3),
                "end_time": None,
                "playback_url": None,
                "viewer_count": 0,
            }
        ],
    },
    {
        "title": "中山一院胃肠外科 | 腹腔镜手术技巧直播",
        "description": "胃肠胰腺肿瘤外科手术技巧系列，腹腔镜与开腹手术操作规范及难点解析，定期更新。",
        "cover_url": "https://images.unsplash.com/photo-1551076805-e1869033e561?w=400&h=300&fit=crop",
        "category_name": "普通外科",
        "sessions": [
            {
                "status": "live",
                "start_time": now - timedelta(hours=1),
                "end_time": None,
                "playback_url": None,
                "viewer_count": 342,
            }
        ],
    },
    {
        "title": "心内科学术直播 | 冠心病与心衰管理新进展",
        "description": "心脏内科专家系列直播，分享冠心病介入治疗、心衰规范化管理、心律失常诊治等最新指南解读和临床经验。",
        "cover_url": "https://images.unsplash.com/photo-1628348068343-c6a848d2b6dd?w=400&h=300&fit=crop",
        "category_name": "心内科",
        "sessions": [
            {
                "status": "finished",
                "start_time": datetime(2024, 2, 20, 8, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 2, 20, 10, 0, tzinfo=timezone.utc),
                "playback_url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8",
                "viewer_count": 2100,
            }
        ],
        "tabs": [
            {
                "tab_key": "intro",
                "title": "课程简介",
                "content_type": "text",
                "text_content": "本次学术直播聚焦冠心病与心衰领域最新进展，结合2024年AHA/ESC指南更新，由心内科专家深入解析临床诊疗策略变化及实战经验。",
                "sort_order": 0,
            },
            {
                "tab_key": "outline",
                "title": "课程大纲",
                "content_type": "text",
                "text_content": "第一讲：冠心病介入治疗新进展\n  · PCI技术演进与器械选择\n  · IVUS/OCT在复杂病变中的应用\n\n第二讲：心衰规范化管理\n  · HFrEF四联药物治疗策略\n  · 心脏再同步化治疗适应证\n\n第三讲：心律失常诊治\n  · 房颤导管消融最新进展\n  · 室性心律失常的风险分层",
                "sort_order": 1,
            },
            {
                "tab_key": "references",
                "title": "参考资料",
                "content_type": "mixed",
                "text_content": "📄 2023 ACC/AHA慢性冠心病管理指南\n📄 2023 ESC急慢性心力衰竭诊断和治疗指南\n📄 2023中国心房颤动诊断和治疗指南\n\n扫描下方二维码下载PPT：",
                "image_url": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=300&h=300&fit=crop",
                "sort_order": 2,
            },
        ],
    },
    {
        "title": "妇产科围手术期管理 | 剖宫产与宫腔镜专场",
        "description": "围绕妇产科常见手术与围手术期管理展开，适合临床教学与病例讨论。",
        "cover_url": "https://images.unsplash.com/photo-1542884748-2b87b9f5b4d2?w=400&h=300&fit=crop",
        "category_name": "妇产科",
        "sessions": [
            {
                "status": "scheduled",
                "start_time": now + timedelta(days=2),
                "end_time": None,
                "playback_url": None,
                "viewer_count": 0,
            }
        ],
    },
    {
        "title": "儿科疑难病例讨论 | 新生儿重症管理",
        "description": "面向儿科与新生儿科的病例讨论直播，聚焦危重新生儿与早产儿管理。",
        "cover_url": "https://images.unsplash.com/photo-1511174511562-5f97f4f4a9f0?w=400&h=300&fit=crop",
        "category_name": "儿科",
        "sessions": [
            {
                "status": "live",
                "start_time": now - timedelta(minutes=30),
                "end_time": None,
                "playback_url": None,
                "viewer_count": 186,
            }
        ],
    },
    {
        "title": "眼科显微手术技巧 | 白内障与玻璃体切除",
        "description": "眼科显微手术演示与术后管理专题，适合眼科规培与进修学习。",
        "cover_url": "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=400&h=300&fit=crop",
        "category_name": "眼科",
        "sessions": [
            {
                "status": "finished",
                "start_time": datetime(2024, 3, 8, 14, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 3, 8, 16, 0, tzinfo=timezone.utc),
                "playback_url": "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8",
                "viewer_count": 620,
            }
        ],
    },
]


# ============================================================
# Tab 种子数据插入（幂等，支持对已有直播间补充Tab）
# ============================================================
def seed_tabs(db):
    print("📑 插入直播间 Tab 数据...")
    for room_data in LIVE_ROOMS_DATA:
        if not room_data.get("tabs"):
            continue
        room = db.query(LiveRoom).filter_by(title=room_data["title"]).first()
        if not room:
            print(f"  [!] 未找到直播间: {room_data['title'][:30]}，跳过 Tab 插入")
            continue
        for tab_data in room_data["tabs"]:
            existing = db.query(LiveRoomTab).filter_by(
                room_id=room.id, tab_key=tab_data["tab_key"]
            ).first()
            if existing:
                print(f"  -- 已存在: [{room_data['title'][:20]}] {tab_data['title']}")
                continue
            db.add(LiveRoomTab(
                id=uuid.uuid4(),
                room_id=room.id,
                tab_key=tab_data["tab_key"],
                title=tab_data["title"],
                content_type=LiveRoomTabContentType(tab_data["content_type"]),
                text_content=tab_data.get("text_content"),
                image_url=tab_data.get("image_url"),
                sort_order=tab_data.get("sort_order", 0),
                is_active=True,
            ))
            print(f"  ++ 创建: [{room_data['title'][:20]}] {tab_data['title']} ({tab_data['content_type']})")
    db.flush()


# ============================================================
# 品牌插入
# ============================================================
def seed_brands(db):
    print("🏷️ 插入品牌数据...")
    count = 0
    skip = 0
    for data in BRANDS_DATA:
        existing = db.query(Brand).filter_by(name=data["name"]).first()
        if existing:
            skip += 1
            print(f"  -- 已存在: {data['name']}")
            continue
        db.add(Brand(
            id=uuid.uuid4(),
            name=data["name"],
            slug=data.get("slug"),
            logo_url=data.get("logo_url"),
            description=data.get("description"),
            website_url=data.get("website_url"),
            sort_order=data.get("sort_order", 0),
            is_active=True,
        ))
        count += 1
        print(f"  ++ 创建: {data['name']}")
    db.flush()
    print(f"  ++ 新增品牌: {count} 条 | 跳过已存在: {skip} 条")


# ============================================================
# 分类插入（V2：支持两级分类，先插一级再插二级）
# ============================================================
def seed_categories(db) -> dict:
    print("📂 插入分类数据（V2 两级体系）...")
    categories = {}

    # 第一轮：插入一级分类（parent=None）
    for data in CATEGORIES_DATA:
        if data.get("parent") is not None:
            continue  # 跳过二级分类，第二轮处理
        existing = db.query(Category).filter_by(name=data["name"]).first()
        if existing:
            categories[data["name"]] = existing
            print(f"  -- 已存在: {data['name']}")
        else:
            cat = Category(
                id=uuid.uuid4(),
                name=data["name"],
                slug=data["slug"],
                sort_order=data["sort_order"],
                is_active=True,
            )
            db.add(cat)
            categories[data["name"]] = cat
            print(f"  ++ 创建一级: {data['name']}")

    db.flush()  # flush 以获取一级分类的 id

    # 第二轮：插入二级分类并关联 parent_id
    for data in CATEGORIES_DATA:
        if data.get("parent") is None:
            continue  # 跳过一级分类
        existing = db.query(Category).filter_by(name=data["name"]).first()
        if existing:
            categories[data["name"]] = existing
            print(f"  -- 已存在: {data['name']}")
        else:
            parent_cat = categories.get(data["parent"])
            if not parent_cat:
                print(f"  [!] 未找到父分类: {data['parent']}，跳过: {data['name']}")
                continue
            cat = Category(
                id=uuid.uuid4(),
                name=data["name"],
                slug=data["slug"],
                sort_order=data["sort_order"],
                is_active=True,
                parent_id=parent_cat.id,
            )
            db.add(cat)
            categories[data["name"]] = cat
            print(f"  ++ 创建二级: {data['name']} -> {data['parent']}")

    db.flush()
    return categories


# ============================================================
# 专家插入（从CSV）
# ============================================================
def seed_experts(db):
    if not os.path.exists(EXPERTS_CSV_PATH):
        print(f"[!] 未找到CSV文件: {EXPERTS_CSV_PATH}")
        print("    请先执行：")
        print('    docker cp "<csv路径>" live-streaming-saas-v2-main-live_core_service-1:/app/experts.csv')
        print("    然后重新运行此脚本")
        return 0

    print(f"👨‍⚕️ 从CSV插入专家数据...")
    count = 0
    skip = 0
    with open(EXPERTS_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_id = row.get("id", "").strip()
            expert_id = uuid.UUID(raw_id) if raw_id else uuid.uuid4()

            # 按ID去重
            if db.query(Expert).filter_by(id=expert_id).first():
                skip += 1
                continue
            # 按姓名去重（防止重复执行种子脚本产生同名专家）
            if db.query(Expert).filter_by(name=row["name"]).first():
                skip += 1
                continue

            is_featured = str(row.get("is_featured", "")).strip().upper() in ("TRUE", "1", "YES")
            sort_order_val = row.get("sort_order", "0") or "0"
            sort_order = int(sort_order_val) if str(sort_order_val).strip().isdigit() else 0
            avatar_url = row.get("avatar_url", "").strip() or None

            # 优先使用简短版字段，回退到 full 版
            expertise = (row.get("expertise_areas") or row.get("expertise_areas_full") or "").strip() or None
            bio = (row.get("bio") or row.get("bio_full") or "").strip() or None

            db.add(Expert(
                id=expert_id,
                name=row["name"],
                title=(row.get("title") or "").strip() or None,
                hospital=(row.get("hospital") or "").strip() or None,
                department=(row.get("department") or "").strip() or None,
                expertise_areas=expertise,
                bio=bio,
                avatar_url=avatar_url,
                is_featured=is_featured,
                is_active=True,
                sort_order=sort_order,
            ))
            count += 1
            if count % 50 == 0:
                db.flush()
                print(f"  进度: {count} 条...")

    db.flush()
    print(f"  ++ 新增专家: {count} 条 | 跳过已存在: {skip} 条")
    return count


# ============================================================
# 直播间 + 场次插入
# ============================================================
def seed_live_rooms(db, categories: dict):
    print("🎬 插入直播间 + 场次数据...")
    status_map = {
        "scheduled": LiveSessionStatus.SCHEDULED,
        "live":      LiveSessionStatus.LIVE,
        "finished":  LiveSessionStatus.FINISHED,
    }

    for room_data in LIVE_ROOMS_DATA:
        existing = db.query(LiveRoom).filter_by(title=room_data["title"]).first()
        if existing:
            print(f"  -- 已存在: {room_data['title'][:40]}")
            continue

        cat = categories.get(room_data["category_name"])
        stream_key = "seed_" + hashlib.md5(room_data["title"].encode()).hexdigest()[:16]

        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=SEED_USER_ID,
            title=room_data["title"],
            description=room_data.get("description"),
            cover_url=room_data.get("cover_url"),
            stream_key=stream_key,
            is_private=False,
            record_by_default=True,
            category_id=cat.id if cat else None,
        )
        db.add(room)
        db.flush()

        for sess_data in room_data.get("sessions", []):
            playback_url = sess_data.get("playback_url")
            playback_url_hash = None
            if playback_url:
                playback_url_hash = hashlib.sha256(playback_url.strip().encode()).hexdigest()

            session_id = uuid.uuid4()
            db.add(LiveSession(
                id=session_id,
                room_id=room.id,
                status=status_map.get(sess_data["status"], LiveSessionStatus.FINISHED),
                start_time=sess_data["start_time"],
                end_time=sess_data.get("end_time"),
                playback_url=playback_url,
                playback_url_hash=playback_url_hash,
            ))
            db.flush()
            db.add(SessionStatistics(
                id=uuid.uuid4(),
                session_id=session_id,
                peak_viewer_count=sess_data.get("viewer_count", 0),
                total_viewer_count=sess_data.get("viewer_count", 0),
                total_like_count=0,
                total_share_count=0,
            ))

        print(f"  ++ 创建: {room_data['title'][:40]}")


# ============================================================
# 首页焦点图插入
# ============================================================
def seed_featured_content(db):
    print("🖼️  插入首页焦点图...")
    room_map = {room["title"]: db.query(LiveRoom).filter_by(title=room["title"]).first() for room in LIVE_ROOMS_DATA}
    for data in FEATURED_CONTENTS_DATA:
        existing = db.query(FeaturedContent).filter_by(title=data["title"]).first()
        if existing:
            print(f"  -- 已存在: {data['title'][:40]}")
            continue

        target_type = data.get("target_type")
        target_id = None
        target_url = data.get("target_url")
        if target_type == "room":
            room = room_map.get(data.get("target_room_title") or data["title"])
            if room:
                target_id = room.id
                target_url = None
            else:
                print(f"  [!] 未找到目标直播间: {data.get('target_room_title') or data['title']}")

        db.add(FeaturedContent(
            id=uuid.uuid4(),
            title=data["title"],
            subtitle=data.get("subtitle"),
            image_url=data["image_url"],
            target_type=target_type,
            target_id=target_id,
            target_url=target_url,
            sort_order=data.get("sort_order", 0),
            is_active=True,
        ))
        print(f"  ++ 创建: {data['title'][:40]}")


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("  开始初始化种子数据")
    print("=" * 60)

    with DBSession() as db:
        try:
            seed_brands(db)
            categories = seed_categories(db)
            seed_experts(db)
            seed_live_rooms(db, categories)
            seed_tabs(db)
            seed_featured_content(db)
            db.commit()
            print("\n" + "=" * 60)
            print("  种子数据初始化完成")
            print("=" * 60)
        except Exception as e:
            db.rollback()
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
