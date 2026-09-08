# 分类系统国家医学标准重构 — Phase B 代码生成提示词

**版本**: V1.1
**创建日期**: 2026-07-28
**更新记录**: V1.1 — 修正提示词中 CATEGORIES_SEED_DATA 条目数计数错误（26→27，14/15→16）; 新增 `migration_expert_category.py` 排除说明
**基于设计文档**: [分类系统国家医学标准重构方案设计 V1.2.md](./分类系统国家医学标准重构方案设计.md) §4.3-§4.4, §6.4
**前置依赖**:
- Phase 0（ORM 模型 + Schema 的 `parent_id` 补齐）已完成
- Phase A（V10 SQL 数据迁移——INSERT 内科+外科 + UPDATE 16 条 parent_id）已完成
**目标文件**: 重构 1 个 + 修改 2 个 + 同步 1 个
**工时**: ~3.5h（B1: 1.5h + B2: 1h + B3: 0.5h + B4: 0.5h）

---

## 1. 角色定义 (Role Definition)

你是一名精通 Python 3.9+ 数据处理和 SQLAlchemy 2.0 应用层架构的后端工程师，同时具备**系统架构治理**的敏感度——你理解"单一真相源（Single Source of Truth）"原则，擅长将分散在多个文件中的常量定义收敛到一个共享模块中，并通过列表推导式自动派生衍生数据。

你对本项目 `app/core/category_constants.py` 的设计模式有深入认知——该文件是项目中所有"分类列表"的唯一定义位置，`seed.py` 和 `expert_service.py` 均通过导入引用其常量。

你的本次任务是**对分类系统执行国家医学标准层级重构**：将当前 25 条平铺的根分类重构为符合卫生部《医疗机构诊疗科目名录》的 11 个一级科目 + 16 个二级科目的层级结构，同时保持匹配算法和 seed 逻辑的正确性。

**五个必须**：
- 必须将 `CATEGORIES_SEED_DATA` 从 25 条平铺 dict 改写为 27 条含 `parent_name` 字段的层级结构
- 必须保持派生常量的自动派生关系（`ROOT_CATEGORIES` 从 `CATEGORIES_SEED_DATA` 派生）
- 必须将 `DEPARTMENT_CATEGORY_MAP` 的 41 条别名**完整迁移**到 `category_constants.py`，并将映射目标值从二级分类名改为一级分类名
- 必须确保 `_match_broad_category` 的遍历源改为按深度排序（二级优先），匹配到二级时通过 `CATEGORY_PARENT_MAP` 自动解析为一级名
- 必须同步更新所有引用方，不留"僵尸引用"

**四个不允许**：
- 不允许修改 `DEPARTMENT_CATEGORY_MAP` 的**键**（41 个别名条目不增删改）
- 不允许修改 `_match_broad_category` 的匹配优先级顺序（别名表优先 → 子串兜底，这是 Sprint 1 已修复的正确顺序）
- 不允许修改 `app/models/` 下的任何文件（Phase 0 已完成）
- 不允许修改 `app/schemas/` 下的任何文件（Phase 0 已完成）
- 不允许修改 `app/api/` 下的任何文件
- 不允许修改 `app/crud/` 下的任何文件
- 不允许新增 SQL 迁移文件（V10 已在 Phase A 执行）

---

## 2. 任务目标 (Task Objective)

### 2.1 重构文件（1 个）

| 文件 | 内容 | 说明 |
|:-----|:-----|:-----|
| `app/core/category_constants.py` | `CATEGORIES_SEED_DATA`（27 条含 `parent_name`）+ `ROOT_CATEGORIES`（11 个一级名，自动派生）+ **新增** `CATEGORY_PARENT_MAP`（16 条子→父映射）+ **新增** `ALL_CATEGORY_NAMES_SORTED`（二级在前 16 + 一级在后 11 = 27 个）+ **新增** `DEPARTMENT_CATEGORY_MAP`（41 条，从 expert_service.py 迁入，值统一为一级名） | 本次重构的核心——从"25 平铺"到"11+16 层级" |

### 2.2 修改文件（3 个）

| 文件 | 修改内容 | 行数 |
|:-----|:---------|:---:|
| `app/services/expert_service.py` | ① 删除模块级 `DEPARTMENT_CATEGORY_MAP`（第 53-74 行，22 行）② 导入语句改为从 `category_constants` 导入 4 个常量 ③ `_match_broad_category` 算法改造——遍历源从 `ROOT_CATEGORIES` 改为 `ALL_CATEGORY_NAMES_SORTED`，匹配到二级时通过 `CATEGORY_PARENT_MAP` 解析为一级名 | ~25 |
| `app/seed.py` | `seed_categories()` 单遍平铺 → 两遍插入：Phase 1 只插 `parent_name=None`（一级），Phase 2 插 `parent_name!=None`（二级）并查表填 `parent_id` | ~25 |
| `scripts/migrate_expert_departments.py` | `STANDARD_ROOT_CATEGORIES` 硬编码列表（第 45-49 行）→ 从 `category_constants` 导入；`DEPARTMENT_CATEGORY_MAP` 硬编码字典（第 51-72 行）→ 从 `category_constants` 导入 | ~15 |

> **注**：`migration_expert_category.py`（设计文档 §5.1 #7）不在本次修改范围内。该文件为已执行完毕的旧版一次性迁移脚本，其内联映射值指向二级分类名（如 `"乳腺外科": "普通外科"`），若改为从 `category_constants` 导入一级分类名（如 `"乳腺外科": "外科"`），将改变其重复执行时的行为——而此脚本不应重复执行。保留其原有内联映射，确保历史可追溯性。

### 2.3 禁止事项

- ❌ 不修改 `app/models/` 下的任何文件（Phase 0 已完成）
- ❌ 不修改 `app/schemas/` 下的任何文件（Phase 0 已完成）
- ❌ 不修改 `app/api/` 下的任何文件
- ❌ 不修改 `app/crud/` 下的任何文件
- ❌ 不修改 `app/core/` 下除 `category_constants.py` 以外的任何文件
- ❌ 不新增 SQL 迁移文件（Phase A 的 V10 SQL 已执行）
- ❌ 不修改 `seed.py` 中 `seed_categories` 以外的任何函数（`seed_experts`、`_resolve_dept_for_seed` 等不做修改）
- ❌ 不修改 `expert_service.py` 中 `_match_broad_category` 以外的任何函数
- ❌ 不修改 `_match_broad_category` 的匹配优先级顺序（别名表→子串）
- ❌ 不修改 `DEPARTMENT_CATEGORY_MAP` 的键（别名条目）

---

## 3. 核心上下文 (Core Context)

### 3.1 技术栈与架构约定

```
Python 3.9+ | SQLAlchemy 2.0 (async) | PostgreSQL 15
项目根模块: backend/live_core_service/app/
category_constants.py 设计原则: 纯数据文件，不导入数据库模块，可在模块导入阶段安全使用
派生常量规则: ROOT_CATEGORIES / CATEGORY_PARENT_MAP / ALL_CATEGORY_NAMES_SORTED 均从 CATEGORIES_SEED_DATA 通过列表推导式自动派生
```

### 3.2 设计文档依据

本次改动基于 [分类系统国家医学标准重构方案设计 V1.2.md](./分类系统国家医学标准重构方案设计.md)，核心依据为 §4.3（`category_constants.py` 目标数据结构）和 §4.4（`_match_broad_category` 算法改造）。

**目标层级结构**（11 一级 + 14 二级 = 25 个分类，有冗余名称）:

```
一级科目（parent_name=None）          二级科目（parent_name=父分类名）
═══════════════════════              ══════════════════════════
内科 (新增)                          心内科、消化科、内分泌科、呼吸内科、
                                     肾内科、血液科、风湿免疫科

外科 (新增)                          普通外科、神经外科、骨科、泌尿外科、
                                     心胸外科、血管外科、整形外科、器官移植科、
                                     烧伤与创面修复科

妇产科 (不变)                        （无子分类）
儿科   (不变)                        （无子分类）
眼科   (不变)                        （无子分类）
耳鼻喉科 (不变)                      （无子分类）
口腔科 (不变)                        （无子分类）
皮肤科 (不变)                        （无子分类）
生殖医学科 (不变)                    （无子分类）
肿瘤科 (不变)                        （无子分类）
其他   (不变)                        （无子分类）
```

### 3.3 已有代码参考

#### 参考 A：`app/core/category_constants.py` — 当前版本（完整内容）

```python
"""
全局医学分类常量 — 单一真相源

本文件是项目中所有"根分类列表"的唯一定义位置。
seed.py 的 CATEGORIES_DATA 和 expert_service.py 的 ROOT_CATEGORIES
均引用此文件，确保三处数据始终一致。

增删改分类时，只需修改本文件中的 CATEGORIES_SEED_DATA 列表。
ROOT_CATEGORIES 自动从 CATEGORIES_SEED_DATA 派生。

注意：本文件不包含数据库依赖，可在模块导入阶段安全使用。
"""

# ============================================================
# 分类种子数据（21 条根分类，用于 seed.py 初始化 categories 表）
# 格式: list[dict] — name, slug, sort_order
# 新增分类时在此列表末尾追加
# ============================================================
CATEGORIES_SEED_DATA: list[dict] = [
    {"name": "普通外科",   "slug": "general-surgery",          "sort_order": 1},
    {"name": "神经外科",   "slug": "neurosurgery",             "sort_order": 2},
    {"name": "心内科",     "slug": "cardiology",               "sort_order": 3},
    {"name": "骨科",       "slug": "orthopedics",              "sort_order": 4},
    {"name": "肿瘤科",     "slug": "oncology",                 "sort_order": 5},
    {"name": "妇产科",     "slug": "obstetrics-gynecology",    "sort_order": 6},
    {"name": "儿科",       "slug": "pediatrics",               "sort_order": 7},
    {"name": "眼科",       "slug": "ophthalmology",            "sort_order": 8},
    {"name": "耳鼻喉科",   "slug": "ent",                      "sort_order": 9},
    {"name": "消化科",     "slug": "gastroenterology",         "sort_order": 10},
    {"name": "内分泌科",   "slug": "endocrinology",            "sort_order": 11},
    {"name": "泌尿外科",   "slug": "urology",                  "sort_order": 12},
    {"name": "心胸外科",   "slug": "cardiothoracic-surgery",   "sort_order": 13},
    {"name": "血管外科",   "slug": "vascular-surgery",         "sort_order": 14},
    {"name": "皮肤科",     "slug": "dermatology",              "sort_order": 15},
    {"name": "口腔科",     "slug": "stomatology",              "sort_order": 16},
    {"name": "整形外科",   "slug": "plastic-surgery",          "sort_order": 17},
    {"name": "器官移植科", "slug": "organ-transplantation",    "sort_order": 18},
    {"name": "生殖医学科", "slug": "reproductive-medicine",    "sort_order": 19},
    {"name": "烧伤与创面修复科", "slug": "burn-wound-repair", "sort_order": 20},
    {"name": "呼吸内科",   "slug": "respiratory-medicine",       "sort_order": 21},
    {"name": "肾内科",     "slug": "nephrology",                 "sort_order": 22},
    {"name": "血液科",     "slug": "hematology",                 "sort_order": 23},
    {"name": "风湿免疫科", "slug": "rheumatology-immunology",    "sort_order": 24},
    {"name": "其他",       "slug": "other",                      "sort_order": 25},
]

# ============================================================
# 根分类名称列表（从 CATEGORIES_SEED_DATA 自动派生）
# 用于子串匹配、名称比对等纯字符串操作
# 格式: list[str] — 保持与 CATEGORIES_SEED_DATA 相同的顺序
# ============================================================
ROOT_CATEGORIES: list[str] = [item["name"] for item in CATEGORIES_SEED_DATA]
```

**关键观察点（8 个）**：

1. **数据结构**: `list[dict]`，每个 dict 当前含 `name`、`slug`、`sort_order` —— **本次重构新增 `parent_name` 字段**
2. **注释分隔线**: `# ====...====` 风格
3. **缩进风格**: `"slug"` 列对齐到最长 `name` 之后
4. **类型注解**: Python 3.9+ 内置 `list[dict]`、`list[str]`（非 `typing.List`）
5. **派生关系**: `ROOT_CATEGORIES` 通过列表推导式 `[item["name"] for item in ...]` 自动派生
6. **Docstring**: 包含文件用途、两个常量的定义关系、注意事项
7. **无 DB 依赖**: 文件不导入 `Base`/`AsyncSession`/`Category` 等数据库模块
8. **模块导入安全**: 可在应用启动的模块导入阶段安全使用

#### 参考 B：`app/services/expert_service.py` — `_match_broad_category`（当前版本，第 82-104 行）

```python
def _match_broad_category(department_text: str) -> Optional[Tuple[str, str]]:
    """启发式匹配科室文本 → (matched_dept_name, matched_category_name)。

    匹配优先级：
    1. 别名表精确匹配（DEPARTMENT_CATEGORY_MAP）— 优先于子串匹配
    2. 子串匹配（根分类名包含在科室文本中）

    Returns:
        (normalized_dept_name, matched_category_name) 或 None
    """
    normalized = _normalize_department_text(department_text)
    if not normalized:
        return None

    mapped = DEPARTMENT_CATEGORY_MAP.get(normalized)
    if mapped:
        return (normalized, mapped)

    for rc in ROOT_CATEGORIES:
        if rc in normalized:
            return (normalized, rc)

    return None
```

**关键观察点（5 个）**：

1. **匹配优先级**: 别名表优先 → 子串兜底（Sprint 1 已修复为正确顺序）
2. **遍历源**: `ROOT_CATEGORIES`（当前为 25 个全部平铺分类名）
3. **返回值**: `(dept_name, category_name)` — 当前 category_name 是**二级分类名**（如"心内科"）
4. **纯函数**: 无数据库访问、无副作用、模块级函数（非类方法）
5. **调用方**: `_resolve_department_and_category` 中使用返回值 `heuristic[1]` 作为 `category_name` 查 `Category.name`

#### 参考 C：`app/seed.py` — `seed_categories`（当前版本，第 449-469 行）

```python
def seed_categories(db) -> dict:
    print("📂 插入分类数据...")
    categories = {}
    for data in CATEGORIES_DATA:
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
            print(f"  ++ 创建: {data['name']}")
    db.flush()
    return categories
```

**关键观察点（4 个）**：

1. **单遍遍历**: 当前遍历 `CATEGORIES_DATA`（list of dict），每个 dict 创建一条 Category
2. **幂等性**: `filter_by(name=data["name"]).first()` 检查已存在则跳过
3. **Category 构造**: `Category(id=uuid.uuid4(), name=..., slug=..., sort_order=..., is_active=True)` — **未传 `parent_id`**
4. **返回值**: `dict[name → Category]`，用于 `seed_live_rooms` 中按名称查分类

#### 参考 D：`scripts/migrate_expert_departments.py` — 当前状态（第 1-72 行，重点关注 43-72）

```python
# 标准根分类名（与 seed.py CATEGORIES_DATA 一致：20 个医学分类 + "其他"）
# 用硬编码列表替代数据库查询，避免测试数据干扰
STANDARD_ROOT_CATEGORIES = [
    '普通外科', '神经外科', '心内科', '骨科', '肿瘤科', '妇产科', '儿科', '眼科',
    '耳鼻喉科', '消化科', '内分泌科', '泌尿外科', '心胸外科', '血管外科', '皮肤科',
    '口腔科', '整形外科', '器官移植科', '生殖医学科', '烧伤与创面修复科', '其他',
]

DEPARTMENT_CATEGORY_MAP = {
    '乳腺外科': '普通外科', '甲状腺外科': '普通外科',
    # ... (41 条，与 expert_service.py 中的完全一致)
    '肝外科/超声医学科/介入超声专科': '其他',
}
```

> ⚠️ **FROZEN 标记**：此文件头注释标注 `FROZEN — 此脚本为一次性数据迁移，已执行完毕，不应再修改或重新运行`。本次同步仅做**导入源统一**（硬编码 → 从 `category_constants` 导入），不改动任何函数逻辑。如果将来有人需要重新执行该脚本，导入的值将自动使用重构后的层级分类体系。

#### 参考 E：`_resolve_department_and_category` 中启发式匹配的调用方式（第 322-356 行）

```python
# 启发式匹配结果：整段代码中最多调用一次（纯函数无副作用）
_heuristic: Optional[Tuple[str, str]] = None

if not matched_dept:
    _heuristic = _match_broad_category(normalized)
    if _heuristic:
        matched_dept_name, matched_cat_name = _heuristic
        # ... 用 matched_cat_name 在 DB 中查 Category.name == matched_cat_name
```

**关键观察点**：`_match_broad_category` 返回的 `matched_cat_name`（即 `heuristic[1]`）被用于 `Category.name == matched_cat_name` 的数据库查询。因此 **`matched_cat_name` 必须是数据库中实际存在的分类名称**。

重构后，`_match_broad_category` 返回一级分类名（如 `"内科"`、`"外科"`）。这要求 Phase A 的 V10 SQL 已经执行，数据库中已存在 `name='内科'` 和 `name='外科'` 的记录。这是 Phase B 必须在 Phase A 之后执行的**硬性依赖**。

---

## 4. 架构约束 (Architecture Constraints)

### 4.1 单一真相源原则

```
✅ 正确模式（重构后）:
   category_constants.py  ← 唯一定义所有分类相关常量
      ├── CATEGORIES_SEED_DATA     ← 唯一定义（27 条含 parent_name）
     ├── ROOT_CATEGORIES          ← 派生（11 个一级名）
      ├── CATEGORY_PARENT_MAP      ← 派生（16 条子→父映射）
      ├── ALL_CATEGORY_NAMES_SORTED ← 派生（二级在前 16 + 一级在后 11）
     ├── DEPARTMENT_CATEGORY_MAP  ← 唯一定义（41 条别名，值统一为一级名）
     │
     ├─→ seed.py: seed_categories()     → 引用 CATEGORIES_SEED_DATA
     ├─→ expert_service.py: _match_broad_category() → 引用 ALL_CATEGORY_NAMES_SORTED + CATEGORY_PARENT_MAP + DEPARTMENT_CATEGORY_MAP
     └─→ migrate_expert_departments.py: match_department() → 引用 ROOT_CATEGORIES + DEPARTMENT_CATEGORY_MAP
```

### 4.2 数据派生关系（铁律）

以下 4 个常量必须通过列表推导式从 `CATEGORIES_SEED_DATA` 自动派生，**禁止手写重复列表**：

| 常量 | 派生规则 | 元素数 |
|------|---------|:---:|
| `ROOT_CATEGORIES` | `c["name"] for c in CATEGORIES_SEED_DATA if c["parent_name"] is None` | 11 |
| `CATEGORY_PARENT_MAP` | `{c["name"]: c["parent_name"] for c in CATEGORIES_SEED_DATA if c["parent_name"] is not None}` | 14 |
| `ALL_CATEGORY_NAMES_SORTED` | 二级名列表（16）+ 一级名列表（11） | 27 |

`DEPARTMENT_CATEGORY_MAP` 是**独立定义**的（41 条别名），不参与自动派生——但它是唯一在该文件中定义、其他地方通过导入引用的。

### 4.3 ALL_CATEGORY_NAMES_SORTED 排序约束（关键！）

```
二级分类名（16 个，按 sort_order 排序）在前
一级分类名（11 个，按 sort_order 排序）在后

原因：子串匹配时，必须让更具体的"心内科"先于更宽泛的"内科"被遍历。
如果顺序反了，"内科"会子串匹配"心内科"（"内科" in "心内科" == True），
导致"心内科-冠脉组"被错误归类为"内科"而非"心内科→内科"。

正确的排序保证：
  "心内科" in "心内科-冠脉组" → True → return ("心内科-冠脉组", "内科") ✅
  （如果"内科"先被遍历：)
  "内科" in "心内科-冠脉组" → True → return ("心内科-冠脉组", "内科") ← 结果碰巧相同
  但更精确的匹配（通过心内科→CATEGORY_PARENT_MAP）语义更清晰

对于"消化科门诊"：
  "消化科" in "消化科门诊" → True → CATEGORY_PARENT_MAP["消化科"] = "内科"
  return ("消化科门诊", "内科") ✅

对于"眼科门诊"（一级科目，无子分类）：
  "眼科" in "眼科门诊" → True → CATEGORY_PARENT_MAP.get("眼科", "眼科") = "眼科"
  return ("眼科门诊", "眼科") ✅
```

### 4.4 匹配算法返回值语义变化

```
重构前: _match_broad_category("心内科-冠脉组") → ("心内科-冠脉组", "心内科")
                                                      matched_cat_name = "心内科"（二级）

重构后: _match_broad_category("心内科-冠脉组") → ("心内科-冠脉组", "内科")
                                                      matched_cat_name = "内科"（一级）

影响:
  - 存量数据: experts.category_id 仍指向二级分类 UUID——不受影响
  - 新创建/导入: 自动创建的科室绑定到一级分类——更安全（宽泛归类比猜测具体二级更稳妥）
  - 统计: category 维度的 expert_count 需要递归统计才能按一级聚合（不在 Phase B 范围内）
```

### 4.5 行为等价性约束

```
以下行为必须保持一致:
  ✅ 41 条已知科室值的匹配结果与 §5.3 验证表一致（覆盖率 ≥ 95%）
   ✅ seed_categories() 生成 27 条 Category（11 一级 + 16 二级，含"内科""外科"新增）
  ✅ 现有数据库中的分类名称集合不变（只是 parent_id 从 NULL 变为有值）
```

### 4.6 循环导入风险排除

```
category_constants.py:
  imports: 无（纯数据文件）

seed.py:
  imports: app.core.category_constants
  imported by: 无（独立脚本）

expert_service.py:
  imports: app.core.category_constants
  imported by: app.api.v1.endpoints.experts, ...

结论: 不存在循环导入 ✅
```

### 4.7 禁止引入的内容

- ❌ 禁止在 `category_constants.py` 中导入数据库会话
- ❌ 禁止在 `category_constants.py` 中定义 Class 或函数（纯数据常量文件）
- ❌ 禁止新增 `__init__.py` 注册
- ❌ 禁止修改 `app/models/content_management.py`（Phase 0 已完成）

---

## 5. 代码生成要求 (Specific Code Generation Requirements)

### 5.1 重构 `app/core/category_constants.py`

**修改范围**：整个文件以重构方式重写（从 25 条平铺 → 27 条层级结构 + 4 个派生常量 + 1 个别名表）。

#### 5.1.1 CATEGORIES_SEED_DATA（27 条，含 `parent_name`）

**修改前**（当前 25 条平铺，无 `parent_name`）：

```python
CATEGORIES_SEED_DATA: list[dict] = [
    {"name": "普通外科",   "slug": "general-surgery",          "sort_order": 1},
    {"name": "神经外科",   "slug": "neurosurgery",             "sort_order": 2},
    {"name": "心内科",     "slug": "cardiology",               "sort_order": 3},
    {"name": "骨科",       "slug": "orthopedics",              "sort_order": 4},
    {"name": "肿瘤科",     "slug": "oncology",                 "sort_order": 5},
    {"name": "妇产科",     "slug": "obstetrics-gynecology",    "sort_order": 6},
    {"name": "儿科",       "slug": "pediatrics",               "sort_order": 7},
    {"name": "眼科",       "slug": "ophthalmology",            "sort_order": 8},
    {"name": "耳鼻喉科",   "slug": "ent",                      "sort_order": 9},
    {"name": "消化科",     "slug": "gastroenterology",         "sort_order": 10},
    {"name": "内分泌科",   "slug": "endocrinology",            "sort_order": 11},
    {"name": "泌尿外科",   "slug": "urology",                  "sort_order": 12},
    {"name": "心胸外科",   "slug": "cardiothoracic-surgery",   "sort_order": 13},
    {"name": "血管外科",   "slug": "vascular-surgery",         "sort_order": 14},
    {"name": "皮肤科",     "slug": "dermatology",              "sort_order": 15},
    {"name": "口腔科",     "slug": "stomatology",              "sort_order": 16},
    {"name": "整形外科",   "slug": "plastic-surgery",          "sort_order": 17},
    {"name": "器官移植科", "slug": "organ-transplantation",    "sort_order": 18},
    {"name": "生殖医学科", "slug": "reproductive-medicine",    "sort_order": 19},
    {"name": "烧伤与创面修复科", "slug": "burn-wound-repair", "sort_order": 20},
    {"name": "呼吸内科",   "slug": "respiratory-medicine",       "sort_order": 21},
    {"name": "肾内科",     "slug": "nephrology",                 "sort_order": 22},
    {"name": "血液科",     "slug": "hematology",                 "sort_order": 23},
    {"name": "风湿免疫科", "slug": "rheumatology-immunology",    "sort_order": 24},
    {"name": "其他",       "slug": "other",                      "sort_order": 25},
]
```

**修改后**（27 条，含 `parent_name`）：

```python
CATEGORIES_SEED_DATA: list[dict] = [
    # ═══════════════════════════════════════════════════════════════
    # Level 1：一级科目（parent_name=None → parent_id=NULL）
    # 严格遵循卫生部《医疗机构诊疗科目名录》
    # ═══════════════════════════════════════════════════════════════
    {"name": "内科",       "parent_name": None, "slug": "internal-medicine",         "sort_order": 1},
    {"name": "外科",       "parent_name": None, "slug": "surgery",                   "sort_order": 2},
    {"name": "妇产科",     "parent_name": None, "slug": "obstetrics-gynecology",     "sort_order": 3},
    {"name": "儿科",       "parent_name": None, "slug": "pediatrics",                "sort_order": 4},
    {"name": "眼科",       "parent_name": None, "slug": "ophthalmology",             "sort_order": 5},
    {"name": "耳鼻喉科",   "parent_name": None, "slug": "ent",                       "sort_order": 6},
    {"name": "口腔科",     "parent_name": None, "slug": "stomatology",               "sort_order": 7},
    {"name": "皮肤科",     "parent_name": None, "slug": "dermatology",               "sort_order": 8},
    {"name": "生殖医学科", "parent_name": None, "slug": "reproductive-medicine",     "sort_order": 9},
    {"name": "肿瘤科",     "parent_name": None, "slug": "oncology",                  "sort_order": 10},
    {"name": "其他",       "parent_name": None, "slug": "other",                     "sort_order": 99},

    # ═══════════════════════════════════════════════════════════════
    # Level 2：二级科目（parent_name 指向父分类，seed 时查表填 parent_id）
    # ═══════════════════════════════════════════════════════════════

    # —— 内科子类（7 个）——
    {"name": "心内科",     "parent_name": "内科", "slug": "cardiology",               "sort_order": 11},
    {"name": "消化科",     "parent_name": "内科", "slug": "gastroenterology",         "sort_order": 12},
    {"name": "内分泌科",   "parent_name": "内科", "slug": "endocrinology",            "sort_order": 13},
    {"name": "呼吸内科",   "parent_name": "内科", "slug": "respiratory-medicine",     "sort_order": 14},
    {"name": "肾内科",     "parent_name": "内科", "slug": "nephrology",               "sort_order": 15},
    {"name": "血液科",     "parent_name": "内科", "slug": "hematology",               "sort_order": 16},
    {"name": "风湿免疫科", "parent_name": "内科", "slug": "rheumatology-immunology",  "sort_order": 17},

    # —— 外科子类（9 个）——
    {"name": "普通外科",           "parent_name": "外科", "slug": "general-surgery",        "sort_order": 18},
    {"name": "神经外科",           "parent_name": "外科", "slug": "neurosurgery",           "sort_order": 19},
    {"name": "骨科",               "parent_name": "外科", "slug": "orthopedics",            "sort_order": 20},
    {"name": "泌尿外科",           "parent_name": "外科", "slug": "urology",                "sort_order": 21},
    {"name": "心胸外科",           "parent_name": "外科", "slug": "cardiothoracic-surgery", "sort_order": 22},
    {"name": "血管外科",           "parent_name": "外科", "slug": "vascular-surgery",       "sort_order": 23},
    {"name": "整形外科",           "parent_name": "外科", "slug": "plastic-surgery",        "sort_order": 24},
    {"name": "器官移植科",         "parent_name": "外科", "slug": "organ-transplantation",  "sort_order": 25},
    {"name": "烧伤与创面修复科",   "parent_name": "外科", "slug": "burn-wound-repair",      "sort_order": 26},
]
```

> ⚠️ **关键验证点**：`"内科"` 和 `"外科"` 的 `parent_name` 是 `None`（它们是一级科目）。`"妇产科"`~`"其他"` 的 `parent_name` 也是 `None`。只有 `"心内科"`~`"烧伤与创面修复科"` 的 `parent_name` 不为 `None`。

#### 5.1.2 派生常量

在 `CATEGORIES_SEED_DATA` 定义之后，替换原来的 `ROOT_CATEGORIES` 段落，改为以下 4 个派生常量：

```python
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
# 排序策略：二级(first, 16个) + 一级(second, 11个) = 总共 27 个
ALL_CATEGORY_NAMES_SORTED: list[str] = (
    [c["name"] for c in CATEGORIES_SEED_DATA if c["parent_name"] is not None] +
    [c["name"] for c in CATEGORIES_SEED_DATA if c["parent_name"] is None]
)
```

**关键确保项（7 个）**：

1. ✅ `ROOT_CATEGORIES` 长度为 11（不是当前 25）
2. ✅ `CATEGORY_PARENT_MAP` 长度为 16（16 个二级的 name → parent_name 映射）
3. ✅ `ALL_CATEGORY_NAMES_SORTED` 长度为 27（16 个二级在前 + 11 个一级在后）
4. ✅ `ALL_CATEGORY_NAMES_SORTED` 中 `"心内科"` 在 `"内科"` 之前（关键排序约束）
5. ✅ `ALL_CATEGORY_NAMES_SORTED` 中 `"普通外科"` 在 `"外科"` 之前
6. ✅ 所有派生常量使用列表推导式，不手写重复列表
7. ✅ 类型注解使用 Python 3.9+ 内置 `list[str]` 和 `dict[str, str]`

#### 5.1.3 DEPARTMENT_CATEGORY_MAP（41 条，从 expert_service.py 迁入）

在派生常量之后，新增 `DEPARTMENT_CATEGORY_MAP` 定义。**这是从 `expert_service.py` 迁入的 41 条别名表，值全部从二级名改为一级名。**

```python
# ============================================================
# 科室→一级分类别名映射表（41 条，统一从此处导出）
# 键: 科室别名（来自历史数据清洗和人工审核）
# 值: 一级分类名（严格遵循卫生部《医疗机构诊疗科目名录》）
#
# 此表原分散在 expert_service.py / migrate_expert_departments.py 两处独立维护，
# 现收敛到 category_constants.py 作为单一真相源。
# ============================================================
DEPARTMENT_CATEGORY_MAP: dict[str, str] = {
    # —— 外科学类 ——
    '乳腺外科': '外科', '甲状腺外科': '外科',
    '肝胆外科': '外科', '胃肠外科一科': '外科',
    '胃肠外科二科': '外科', '胃肠外科三科': '外科',
    '胆胰外科': '外科', '肝外科': '外科',
    '脊柱外科': '外科', '关节外科': '外科',
    '骨肿瘤科': '外科', '运动医学科': '外科',
    '显微创伤外手科': '外科',
    '肾移植专科': '外科',
    '器官移植科/肾移植专科': '外科',
    '器官移植科/肝移植专科': '外科',
    '泌尿外科/男科': '外科',
    '胸外科': '外科',

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

    # —— 其他 ——
    '变态反应专科': '其他', '外科门诊': '其他',
    '肝外科/超声医学科/介入超声专科': '其他',
}
```

> ⚠️ **值迁移核对清单**（逐个验证，不要遗漏）：
>
> 从旧值（二级名）→ 新值（一级名）的映射关系：
> ```
> '普通外科' → '外科'    (乳腺外科、甲状腺外科、肝胆外科、胃肠外科一科/二科/三科、胆胰外科、肝外科)
> '骨科'     → '外科'    (脊柱外科、关节外科、骨肿瘤科、运动医学科、显微创伤外手科)
> '器官移植科' → '外科'  (肾移植专科、器官移植科/肾移植专科、器官移植科/肝移植专科)
> '泌尿外科' → '外科'    (泌尿外科/男科)
> '心胸外科' → '外科'    (胸外科)
> '妇产科'   → '妇产科'  (不变 — 妇产科已是一级科目)
> '耳鼻喉科' → '耳鼻喉科' (不变)
> '口腔科'   → '口腔科'  (不变)
> '儿科'     → '儿科'    (不变)
> '生殖医学科' → '生殖医学科' (不变)
> '其他'     → '其他'    (不变)
> ```

---

### 5.2 修改 `app/services/expert_service.py`

#### 5.2.1 导入语句变更

**修改前**（第 50-51 行）：
```python
# 标准根分类名（从单一真相源引用，与 seed.py 共享同一份数据）
from app.core.category_constants import ROOT_CATEGORIES
```

**修改后**（扩展为 4 个常量的导入）：
```python
# 分类常量（从单一真相源引用，与 seed.py 共享同一份数据）
from app.core.category_constants import (
    ROOT_CATEGORIES,
    ALL_CATEGORY_NAMES_SORTED,
    CATEGORY_PARENT_MAP,
    DEPARTMENT_CATEGORY_MAP,
)
```

#### 5.2.2 删除模块级 DEPARTMENT_CATEGORY_MAP 定义（第 53-74 行）

**删除**：整个 `DEPARTMENT_CATEGORY_MAP = { ... }` 块（第 53-74 行，共 22 行）。现在该常量从 `category_constants` 导入。

**注意**：`_normalize_department_text` 函数（第 77-79 行）保留不变——它不是本次重构的改动目标。

#### 5.2.3 _match_broad_category 算法改造（第 82-104 行）

**修改前**：
```python
def _match_broad_category(department_text: str) -> Optional[Tuple[str, str]]:
    """启发式匹配科室文本 → (matched_dept_name, matched_category_name)。

    匹配优先级：
    1. 别名表精确匹配（DEPARTMENT_CATEGORY_MAP）— 优先于子串匹配
    2. 子串匹配（根分类名包含在科室文本中）

    Returns:
        (normalized_dept_name, matched_category_name) 或 None
    """
    normalized = _normalize_department_text(department_text)
    if not normalized:
        return None

    mapped = DEPARTMENT_CATEGORY_MAP.get(normalized)
    if mapped:
        return (normalized, mapped)

    for rc in ROOT_CATEGORIES:
        if rc in normalized:
            return (normalized, rc)

    return None
```

**修改后**：
```python
def _match_broad_category(department_text: str) -> Optional[Tuple[str, str]]:
    """启发式匹配科室文本 → (matched_dept_name, matched_category_name)。

    匹配优先级：
    1. 别名表精确匹配（DEPARTMENT_CATEGORY_MAP）— 优先于子串匹配
    2. 子串匹配（二级优先，一级兜底——ALL_CATEGORY_NAMES_SORTED 中二级在前）

    匹配到 Level 2 分类时，通过 CATEGORY_PARENT_MAP 自动解析为一级科目名。

    Returns:
        (normalized_dept_name, level1_category_name) 或 None
    """
    normalized = _normalize_department_text(department_text)
    if not normalized:
        return None

    # P1: 别名表（值已是 Level 1 名）
    mapped = DEPARTMENT_CATEGORY_MAP.get(normalized)
    if mapped:
        return (normalized, mapped)

    # P2: 子串匹配（Level 2 优先——ALL_CATEGORY_NAMES_SORTED 中二级在前）
    for cat_name in ALL_CATEGORY_NAMES_SORTED:
        if cat_name in normalized:
            parent = CATEGORY_PARENT_MAP.get(cat_name, cat_name)
            return (normalized, parent)

    return None
```

**改动点说明**：
1. 遍历源：`ROOT_CATEGORIES`（25 个全平铺） → `ALL_CATEGORY_NAMES_SORTED`（14 二级 + 11 一级）
2. 返回值：匹配到二级时通过 `CATEGORY_PARENT_MAP.get(cat_name, cat_name)` 解析为一级名
3. Docstring 更新：说明新增的二级优先策略和一级解析逻辑
4. 别名表优先级和 Docstring 中"P1/P2"标注**保持不变**（Sprint 1 已修复的正确顺序）

---

### 5.3 修改 `app/seed.py` — `seed_categories` 两遍插入

**修改前**（第 449-469 行）：
```python
def seed_categories(db) -> dict:
    print("📂 插入分类数据...")
    categories = {}
    for data in CATEGORIES_DATA:
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
            print(f"  ++ 创建: {data['name']}")
    db.flush()
    return categories
```

**修改后**（两遍插入：先父后子）：
```python
def seed_categories(db) -> dict:
    print("📂 插入分类数据...")
    categories = {}

    # Phase 1: 插入一级科目（parent_name=None → parent_id=NULL）
    for data in CATEGORIES_DATA:
        if data.get("parent_name") is not None:
            continue  # 二级暂时跳过
        existing = db.query(Category).filter_by(
            name=data["name"], parent_id=None
        ).first()
        if existing:
            categories[data["name"]] = existing
            print(f"  -- 已存在: {data['name']} (一级)")
        else:
            cat = Category(
                id=uuid.uuid4(),
                name=data["name"],
                slug=data["slug"],
                sort_order=data["sort_order"],
                parent_id=None,
                is_active=True,
            )
            db.add(cat)
            categories[data["name"]] = cat
            print(f"  ++ 创建: {data['name']} (一级)")
    db.flush()

    # Phase 2: 插入二级科目（parent_name 指向已存在的一级）
    for data in CATEGORIES_DATA:
        if data.get("parent_name") is None:
            continue
        parent = categories.get(data["parent_name"])
        if not parent:
            raise ValueError(
                f"父分类 '{data['parent_name']}' 未找到——"
                f"请检查 CATEGORIES_SEED_DATA 中 '{data['name']}' 的 parent_name 是否正确"
            )
        existing = db.query(Category).filter_by(
            name=data["name"], parent_id=parent.id
        ).first()
        if existing:
            key = f"{data['parent_name']}→{data['name']}"
            categories[key] = existing
            print(f"  -- 已存在: {data['parent_name']}→{data['name']}")
        else:
            cat = Category(
                id=uuid.uuid4(),
                name=data["name"],
                slug=data["slug"],
                sort_order=data["sort_order"],
                parent_id=parent.id,
                is_active=True,
            )
            db.add(cat)
            key = f"{data['parent_name']}→{data['name']}"
            categories[key] = cat
            print(f"  ++ 创建: {data['parent_name']}→{data['name']}")
    db.flush()
    return categories
```

**关键确保项（5 个）**：

1. ✅ Phase 1 用 `filter_by(name=..., parent_id=None)` 查重——确保不创建重复的一级分类
2. ✅ Phase 1 创建一级时显式传 `parent_id=None`
3. ✅ Phase 1 和 Phase 2 之间有 `db.flush()` —— 确保二级插入时一级 UUID 已生成
4. ✅ Phase 2 用 `parent_id=parent.id` 显式设置 FK
5. ✅ 二级的 key 用 `"内科→心内科"` 格式存入 `categories` dict——与旧代码的简单 `"心内科"` key 不同。需要检查下游调用方（`seed_live_rooms`）的 key 查找方式

> ⚠️ **下游兼容性注意**：`seed_live_rooms(db, categories)` 中通过 `categories.get(room_data["category_name"])` 查找分类。重构后，"普通外科"的 key 不再是 `"普通外科"` 而是 `"外科→普通外科"`。但 `seed_live_rooms` 在 seed 流程中始终在 `seed_categories` 之后执行——且当前 `LIVE_ROOMS_DATA` 中引用的分类名（如 `"普通外科"`、`"神经外科"`、`"心内科"`、`"妇产科"`、`"儿科"`、`"眼科"`）都是二级分类名或叶子一级分类名。
>
> 对于二级分类（如 `"普通外科"`）：`categories.get("普通外科")` 将返回 `None`（因为 key 变成了 `"外科→普通外科"`）。
>
> **解决方案**：在 `seed_categories` 函数末尾，为二级分类建立额外的简单名称映射，确保向后兼容：
>
> ```python
> # 向后兼容：为二级分类建立简单名称映射（seed_live_rooms 按名称查找）
> for data in CATEGORIES_DATA:
>     if data.get("parent_name") is not None:
>         key = f"{data['parent_name']}→{data['name']}"
>         if key in categories:
>             categories[data["name"]] = categories[key]
> ```
>
> 将此段插入到 `seed_categories` 函数末尾、`return categories` 之前。

---

### 5.4 同步 `scripts/migrate_expert_departments.py`

> ⚠️ 此文件头注释标注 `FROZEN — 此脚本为一次性数据迁移，已执行完毕`。本次同步为**导入源统一**（硬编码 → 从 `category_constants` 导入），不改动任何函数逻辑。

#### 5.4.1 删除硬编码的 STANDARD_ROOT_CATEGORIES（第 44-49 行）

**删除**：
```python
# 标准根分类名（与 seed.py CATEGORIES_DATA 一致：20 个医学分类 + "其他"）
# 用硬编码列表替代数据库查询，避免测试数据干扰
STANDARD_ROOT_CATEGORIES = [
    '普通外科', '神经外科', '心内科', '骨科', '肿瘤科', '妇产科', '儿科', '眼科',
    '耳鼻喉科', '消化科', '内分泌科', '泌尿外科', '心胸外科', '血管外科', '皮肤科',
    '口腔科', '整形外科', '器官移植科', '生殖医学科', '烧伤与创面修复科', '其他',
]
```

#### 5.4.2 删除硬编码的 DEPARTMENT_CATEGORY_MAP（第 51-72 行）

**删除**整个 `DEPARTMENT_CATEGORY_MAP = { ... }` 块。

#### 5.4.3 新增导入语句

在文件头部项目内导入区域（`from sqlalchemy.orm import sessionmaker` 之后），新增：

```python
# 分类常量（从单一真相源导入，替代原有的硬编码列表）
from app.core.category_constants import ROOT_CATEGORIES, DEPARTMENT_CATEGORY_MAP
```

> **注意**：`match_department` 函数（第 80-99 行）中 `for rc in root_categories:` 的参数名 `root_categories` 是小写——这是通过函数参数传入的，调用处 `match_department(normalized, root_categories)` 中 `root_categories` 现在是导入的 `ROOT_CATEGORIES`。确保函数调用处使用**大写**的 `ROOT_CATEGORIES`。

#### 5.4.4 更新 `run_dry_run` 和 `run_migrate` 中的变量引用

将 `run_dry_run` 中：
```python
root_categories = STANDARD_ROOT_CATEGORIES
```
改为：
```python
root_categories = ROOT_CATEGORIES
```

将 `run_migrate` 中：
```python
root_categories = STANDARD_ROOT_CATEGORIES
```
改为：
```python
root_categories = ROOT_CATEGORIES
```

---

## 6. 完整性检查清单 (Completeness Checklist)

### 6.1 `category_constants.py` 验证

- ✅ `CATEGORIES_SEED_DATA` 共 27 条（11 个 `parent_name=None` + 16 个 `parent_name!=None`）
- ✅ `"内科"` 的 `parent_name` 是 `None`（一级科目）
- ✅ `"外科"` 的 `parent_name` 是 `None`（一级科目）
- ✅ `"心内科"` 的 `parent_name` 是 `"内科"`（不是 `"外科"`，不是 `None`）
- ✅ `"普通外科"` 的 `parent_name` 是 `"外科"`（不是 `"内科"`，不是 `None`）
- ✅ `"妇产科"`~`"其他"` 共 9 个的 `parent_name` 是 `None`
- ✅ `ROOT_CATEGORIES` 长度为 11（通过列表推导式派生）
- ✅ `CATEGORY_PARENT_MAP` 长度为 16（通过字典推导式派生）
- ✅ `ALL_CATEGORY_NAMES_SORTED` 长度为 27，二级在前
- ✅ `ALL_CATEGORY_NAMES_SORTED` 中 `"心内科"` 在 `"内科"` 之前（通过列表推导式中的 `if c["parent_name"] is not None` 先于 `is None` 保证）
- ✅ `DEPARTMENT_CATEGORY_MAP` 长度为 41
- ✅ `DEPARTMENT_CATEGORY_MAP` 的所有值均为一级分类名（"外科"/"妇产科"/"耳鼻喉科"/"口腔科"/"儿科"/"生殖医学科"/"其他"）
- ✅ 文件 Docstring 已更新为反映层级结构
- ✅ 类型注解使用 Python 3.9+ 内置 `list[dict]`/`list[str]`/`dict[str, str]`

### 6.2 `expert_service.py` 验证

- ✅ 模块级 `DEPARTMENT_CATEGORY_MAP = {...}`（第 53-74 行）已删除
- ✅ 导入语句扩展为 `from app.core.category_constants import ROOT_CATEGORIES, ALL_CATEGORY_NAMES_SORTED, CATEGORY_PARENT_MAP, DEPARTMENT_CATEGORY_MAP`
- ✅ `_match_broad_category` 遍历源改为 `ALL_CATEGORY_NAMES_SORTED`
- ✅ `_match_broad_category` 中 `for rc in ROOT_CATEGORIES:` → `for cat_name in ALL_CATEGORY_NAMES_SORTED:`
- ✅ `_match_broad_category` 中匹配到分类时通过 `CATEGORY_PARENT_MAP.get(cat_name, cat_name)` 解析
- ✅ `_match_broad_category` 的 Docstring 已更新
- ✅ 别名表优先级 **保持不变**（MAP 在前，循环在后——Sprint 1 的正确顺序）
- ✅ `_normalize_department_text` 函数未做任何修改

### 6.3 `seed.py` 验证

- ✅ `seed_categories` 改为两遍插入（Phase 1: parent_name=None → Phase 2: parent_name!=None）
- ✅ Phase 1 创建 Category 时显式传 `parent_id=None`
- ✅ Phase 2 创建 Category 时传 `parent_id=parent.id`
- ✅ Phase 1 和 Phase 2 之间有 `db.flush()`
- ✅ 向后兼容映射：`categories[data["name"]] = categories[key]`（简单名称 → 二级对象）
- ✅ 其他函数（`seed_experts`、`_resolve_dept_for_seed`、`seed_live_rooms`、`seed_tabs` 等）未做任何修改
- ✅ 文件头部的导入语句未改变（`CATEGORIES_DATA` 别名仍指向 `CATEGORIES_SEED_DATA`）

### 6.4 `migrate_expert_departments.py` 验证

- ✅ `STANDARD_ROOT_CATEGORIES` 硬编码列表已删除
- ✅ `DEPARTMENT_CATEGORY_MAP` 硬编码字典已删除
- ✅ 新增 `from app.core.category_constants import ROOT_CATEGORIES, DEPARTMENT_CATEGORY_MAP`
- ✅ `run_dry_run` 中 `root_categories = STANDARD_ROOT_CATEGORIES` → `root_categories = ROOT_CATEGORIES`
- ✅ `run_migrate` 中 `root_categories = STANDARD_ROOT_CATEGORIES` → `root_categories = ROOT_CATEGORIES`
- ✅ `match_department` 函数逻辑未做任何修改

### 6.5 行为等价性 / 回归验证（Phase C 执行）

- ✅ `_match_broad_category("心内科-冠脉组")` → `("心内科-冠脉组", "内科")`（二级优先 + CATEGORY_PARENT_MAP 解析）
- ✅ `_match_broad_category("骨科-脊柱组")` → `("骨科-脊柱组", "外科")`（同上）
- ✅ `_match_broad_category("消化科门诊")` → `("消化科门诊", "内科")`（同上）
- ✅ `_match_broad_category("乳腺外科")` → `("乳腺外科", "外科")`（别名表命中，值已是一级名）
- ✅ `_match_broad_category("骨肿瘤科")` → `("骨肿瘤科", "外科")`（别名表命中，值已从"骨科"改为"外科"）
- ✅ `_match_broad_category("妇产科-产科")` → `("妇产科-产科", "妇产科")`（一级分类，无 parent_name，CATEGORY_PARENT_MAP.get("妇产科", "妇产科") = "妇产科"）
- ✅ `_match_broad_category("眼科门诊")` → `("眼科门诊", "眼科")`（同上）
- ✅ `_match_broad_category("变态反应专科")` → `("变态反应专科", "其他")`（别名表命中）
- ✅ `_match_broad_category("外科门诊")` → `("外科门诊", "其他")`（别名表命中）
- ✅ 41 条已知科室值逐个验证，覆盖率 ≥ 95%（≥39/41）

### 6.6 不会引入的问题

- ✅ 不修改 `app/models/__init__.py` → 不存在模型注册缺失
- ✅ 不修改 `app/schemas/__init__.py` → 不存在 Schema 注册缺失
- ✅ 不修改 `app/api/v1/api.py` → 不存在路由注册缺失
- ✅ 不修改 `app/crud/` → 不存在 CRUD 层行为变化
- ✅ 不新增 Python 依赖 → 不需要修改 `requirements.txt`
- ✅ 不新增 SQL 迁移文件（V10 已在 Phase A 执行）
- ✅ `category_constants.py` 是纯数据文件 → 无循环导入风险
- ✅ `_match_broad_category` 的匹配顺序未改变 → 别名表仍优先于子串

### 6.7 部署约束验证

- ✅ Phase A (V10 SQL) 已执行 → 数据库中 `"内科"` 和 `"外科"` 已存在
- ✅ `_resolve_department_and_category` 中 `Category.name == matched_cat_name` 能查到 `"内科"`/`"外科"`
- ✅ Phase B 全部代码与 Phase A 同批次部署（避免 B2 先于 A 导致的匹配退化）

---

## 7. 最终交付 (Final Deliverable)

### 7.1 重构文件

| # | 文件 | 内容 |
|---|------|------|
| 1 | `backend/live_core_service/app/core/category_constants.py` | 完整替换：27 条层级种子数据 + 4 个派生常量 + 41 条别名表 |

### 7.2 修改文件

| # | 文件 | 改动行数 | 改动内容 |
|---|------|:---:|---------|
| 2 | `backend/live_core_service/app/services/expert_service.py` | ~25 行 | 删除模块级 `DEPARTMENT_CATEGORY_MAP`；导入 4 个新常量；`_match_broad_category` 算法改造 |
| 3 | `backend/live_core_service/app/seed.py` | ~35 行 | `seed_categories()` 单遍平铺 → 两遍插入 + 向后兼容映射 |
| 4 | `backend/live_core_service/scripts/migrate_expert_departments.py` | ~15 行 | 硬编码列表 → 从 `category_constants` 导入 |

### 7.3 验证顺序

```
1. 执行 category_constants.py 重构 → python -c "from app.core.category_constants import *; print(len(CATEGORIES_SEED_DATA), len(ROOT_CATEGORIES), len(CATEGORY_PARENT_MAP), len(ALL_CATEGORY_NAMES_SORTED), len(DEPARTMENT_CATEGORY_MAP))"
   预期输出: 27 11 16 27 41

2. 执行 expert_service.py 修改 → python -c "from app.services.expert_service import _match_broad_category; print(_match_broad_category('心内科-冠脉组')); print(_match_broad_category('骨肿瘤科'))"
   预期输出: ('心内科-冠脉组', '内科') 和 ('骨肿瘤科', '外科')

3. 执行 seed.py 修改 → docker exec ... python seed.py → 验证 categories 表含 27 条记录（含"内科""外科"）

4. 验证 migrate_expert_departments.py 语法 → python -c "import scripts.migrate_expert_departments"（仅验证导入不报错，不执行）

5. 41 条全量回归测试（Phase C1）

6. 端到端 CSV 导入测试（Phase C2）

7. API 回归测试（Phase C3）
```

---

> **最后更新**: 2026-07-28 | **状态**: 🟢 待执行
