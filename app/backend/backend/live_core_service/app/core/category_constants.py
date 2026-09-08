"""
全局医学分类常量 — 单一真相源

本文件是项目中所有"分类列表"的唯一定义位置。
seed.py 的 CATEGORIES_DATA 和 expert_service.py 的 ROOT_CATEGORIES
均引用此文件，确保所有引用点数据始终一致。

分类体系以卫生部《医疗机构诊疗科目名录》为基底 + 业务扩展：
- 一级科目（parent_name=None）：名录一级科目 + 业务扩展（生殖医学科、其他）
- 二级科目（parent_name 指向父分类）：名录二级 + 业务扩展
- standard 标记：true=名录标准科目（name 受名录校验）；false=扩展科目（放行合规名）

增删改分类时，只需修改本文件中的 CATEGORIES_SEED_DATA 列表。
所有派生常量（ROOT_CATEGORIES / CATEGORY_PARENT_MAP / ALL_CATEGORY_NAMES_SORTED）
均从 CATEGORIES_SEED_DATA 通过列表推导式自动派生。

本文件不包含数据库依赖，可在模块导入阶段安全使用。
"""

# ============================================================
# 分类种子数据（36 条：16 一级 + 20 二级，阶段6B 补录）
# 格式: list[dict] — name, parent_name, slug, sort_order, standard
# parent_name=None → 一级科目（parent_id=NULL）
# parent_name="内科"/"外科" → 二级科目（seed 时查表填 parent_id）
# standard=true → 名录标准名（create/update 校验）；false → 扩展科目
# ============================================================
CATEGORIES_SEED_DATA: list[dict] = [
    # ═══════════════════════════════════════════════════════════════
    # Level 1：一级科目（parent_name=None → parent_id=NULL）
    # 以名录为基底 + 业务扩展（生殖医学科/其他 标 standard=false）
    # ═══════════════════════════════════════════════════════════════
    {"name": "内科",       "parent_name": None, "slug": "internal-medicine",         "sort_order": 1,  "standard": True},
    {"name": "外科",       "parent_name": None, "slug": "surgery",                   "sort_order": 2,  "standard": True},
    {"name": "妇产科",     "parent_name": None, "slug": "obstetrics-gynecology",     "sort_order": 3,  "standard": True},
    {"name": "儿科",       "parent_name": None, "slug": "pediatrics",                "sort_order": 4,  "standard": True},
    {"name": "眼科",       "parent_name": None, "slug": "ophthalmology",             "sort_order": 5,  "standard": True},
    {"name": "耳鼻喉科",   "parent_name": None, "slug": "ent",                       "sort_order": 6,  "standard": True},
    {"name": "口腔科",     "parent_name": None, "slug": "stomatology",               "sort_order": 7,  "standard": True},
    {"name": "皮肤科",     "parent_name": None, "slug": "dermatology",               "sort_order": 8,  "standard": True},
    {"name": "精神科",     "parent_name": None, "slug": "psychiatry",                "sort_order": 9,  "standard": True},
    {"name": "中医科",     "parent_name": None, "slug": "tcm",                       "sort_order": 10, "standard": True},
    {"name": "康复医学科", "parent_name": None, "slug": "rehabilitation",            "sort_order": 11, "standard": True},
    {"name": "麻醉科",     "parent_name": None, "slug": "anesthesiology",            "sort_order": 12, "standard": True},
    {"name": "医学影像科", "parent_name": None, "slug": "medical-imaging",           "sort_order": 13, "standard": True},
    {"name": "肿瘤科",     "parent_name": None, "slug": "oncology",                  "sort_order": 14, "standard": True},
    {"name": "生殖医学科", "parent_name": None, "slug": "reproductive-medicine",     "sort_order": 15, "standard": False},
    {"name": "其他",       "parent_name": None, "slug": "other",                     "sort_order": 99, "standard": False},

    # ═══════════════════════════════════════════════════════════════
    # Level 2：二级科目（parent_name 指向父分类，seed 时查表填 parent_id）
    # ═══════════════════════════════════════════════════════════════

    # —— 内科子类（10 个，阶段6B 补 3 个）——
    {"name": "心内科",     "parent_name": "内科", "slug": "cardiology",               "sort_order": 16, "standard": True},
    {"name": "消化科",     "parent_name": "内科", "slug": "gastroenterology",         "sort_order": 17, "standard": True},
    {"name": "内分泌科",   "parent_name": "内科", "slug": "endocrinology",            "sort_order": 18, "standard": True},
    {"name": "呼吸内科",   "parent_name": "内科", "slug": "respiratory-medicine",     "sort_order": 19, "standard": True},
    {"name": "肾内科",     "parent_name": "内科", "slug": "nephrology",               "sort_order": 20, "standard": True},
    {"name": "血液科",     "parent_name": "内科", "slug": "hematology",               "sort_order": 21, "standard": True},
    {"name": "风湿免疫科", "parent_name": "内科", "slug": "rheumatology-immunology",  "sort_order": 22, "standard": True},
    {"name": "神经内科",   "parent_name": "内科", "slug": "neurology",                "sort_order": 23, "standard": True},
    {"name": "变态反应科", "parent_name": "内科", "slug": "allergy",                  "sort_order": 24, "standard": True},
    {"name": "老年病科",   "parent_name": "内科", "slug": "geriatrics",               "sort_order": 25, "standard": True},

    # —— 外科子类（9 个）——
    {"name": "普通外科",           "parent_name": "外科", "slug": "general-surgery",        "sort_order": 26, "standard": True},
    {"name": "神经外科",           "parent_name": "外科", "slug": "neurosurgery",           "sort_order": 27, "standard": True},
    {"name": "骨科",               "parent_name": "外科", "slug": "orthopedics",            "sort_order": 28, "standard": True},
    {"name": "泌尿外科",           "parent_name": "外科", "slug": "urology",                "sort_order": 29, "standard": True},
    {"name": "心胸外科",           "parent_name": "外科", "slug": "cardiothoracic-surgery", "sort_order": 30, "standard": False},
    {"name": "血管外科",           "parent_name": "外科", "slug": "vascular-surgery",       "sort_order": 31, "standard": False},
    {"name": "整形外科",           "parent_name": "外科", "slug": "plastic-surgery",        "sort_order": 32, "standard": True},
    {"name": "器官移植科",         "parent_name": "外科", "slug": "organ-transplantation",  "sort_order": 33, "standard": False},
    {"name": "烧伤与创面修复科",   "parent_name": "外科", "slug": "burn-wound-repair",      "sort_order": 34, "standard": False},
]

# ============================================================
# 派生数据（从 CATEGORIES_SEED_DATA 自动派生，确保单一真相源）
# ============================================================

# 一级科目名列表（11 个，parent_name=None）
ROOT_CATEGORIES: list[str] = [
    c["name"] for c in CATEGORIES_SEED_DATA if c["parent_name"] is None
]

# 子→父映射表（16 条，用于匹配算法：匹配到二级时返回一级名）
CATEGORY_PARENT_MAP: dict[str, str] = {
    c["name"]: c["parent_name"]
    for c in CATEGORIES_SEED_DATA if c["parent_name"] is not None
}

# 按深度排序的全分类名列表（二级优先，避免"内科"先匹配"心内科"）
# 排序策略：二级(first, 20个) + 一级(second, 16个) = 总共 36 个
ALL_CATEGORY_NAMES_SORTED: list[str] = (
    [c["name"] for c in CATEGORIES_SEED_DATA if c["parent_name"] is not None] +
    [c["name"] for c in CATEGORIES_SEED_DATA if c["parent_name"] is None]
)

# 名录标准名清单（standard=true 的分类 name 必须命中，阶段6B 校验用）
# 从 CATEGORIES_SEED_DATA 派生，确保与种子数据单一真相源一致
STANDARD_CATEGORY_NAMES: set[str] = {
    c["name"] for c in CATEGORIES_SEED_DATA if c.get("standard", True)
}

# ============================================================
# 科室→分类别名映射表（41 条，统一从此处导出）
# 键: 科室别名（来自历史数据清洗和人工审核）
# 值: 目标分类名（一级或二级均可；_match_broad_category 直接透传此值）
# P0-3 修订: 此表入口优先于子串匹配，值可以是任何 categories 表中的 name
# ============================================================
DEPARTMENT_CATEGORY_MAP: dict[str, str] = {
    # —— 外科学类 ——
    '乳腺外科': '普通外科', '甲状腺外科': '普通外科',
    '甲乳外科': '普通外科',
    '肝胆外科': '普通外科', '胃肠外科一科': '普通外科',
    '胃肠外科二科': '普通外科', '胃肠外科三科': '普通外科',
    '胆胰外科': '普通外科', '肝外科': '普通外科',
    '脊柱外科': '骨科', '关节外科': '骨科',
    '骨肿瘤科': '骨科', '运动医学科': '骨科',
    '显微创伤外手科': '骨科',
    '肾移植专科': '器官移植科',
    '器官移植科/肾移植专科': '器官移植科',
    '器官移植科/肝移植专科': '器官移植科',
    '泌尿外科/男科': '泌尿外科', '男科': '泌尿外科',
    '胸外科': '心胸外科',

    # —— 妇产科学类 ——
    '妇科': '妇产科', '产科': '妇产科',

    # —— 耳鼻喉科学类 ——
    '鼻专科': '耳鼻喉科', '耳专科': '耳鼻喉科', '咽喉专科': '耳鼻喉科',

    # —— 口腔科学类 ——
    '口内修复科': '口腔科', '口腔颌面外科': '口腔科',

    # —— 儿科学类 ——
    '小儿外科': '儿科',

    # —— 生殖医学类 ——
    '生殖医学中心': '生殖医学科', '生殖男科专科': '生殖医学科',
    '男科/生殖医学中心': '生殖医学科',

    # —— 变态反应类 ——
    '变态反应专科': '变态反应科',

    # —— 其他 ——
    '外科门诊': '其他',
    '肝外科/超声医学科/介入超声专科': '其他',
}

# ============================================================
# 测试分类前缀模式（K3 警告日志 / K5 audit 第 6 项共用）
# 基于 2026-08-12 实测的测试分类命名模式（含并行开发历史模式）
# ============================================================
TEST_CATEGORY_PATTERNS: tuple = (
    "分类_", "分类1_", "分类2_", "分类3_",
    "test_", "TEST", "科室_", "源_", "一级_", "目标_",
    "二级", "子_", "父_", "根_", "活跃", "空分类_",
    "重复分类_", "新分类_", "唯一名_", "停用", "禁用",
    "神经内科_", "D_", "测试",
)


def is_test_category_name(name: str) -> bool:
    """判断分类名是否为测试前缀模式（K3/K5 共用，避免两处定义漂移）"""
    if not name:
        return False
    return any(name.startswith(p) for p in TEST_CATEGORY_PATTERNS) or "测试" in name
