# 专家分类与直播间分类系统 — 现状分析与 C 方案设计（受控词表）

> 编写日期：2026-06-21  
> 基于实际数据库审计（261 个分类、384 位专家、796 个直播间）  
> 涉及项目：live_core_service（后端）、saas_app-main（前端）

---

## 第一章：当前架构全貌

### 1.1 数据表关系图（现行）

```
categories（全局医学科室分类表） — 20 个真实分类 + 241 个测试分类
│  id (PK, UUID)
│  name (UNIQUE)               ← "心内科"、"普通外科"……
│  slug                        ← "cardiology"、"general-surgery"
│  icon, description, sort_order, is_active
│  created_at / updated_at
│
├──┄ experts（1:N，直接 FK）    ← 384 位专家
│   │
│   └── experts
│       ├── id (PK)
│       ├── department (VARCHAR 120, nullable)    ← 自由文本，41 个唯一值
│       ├── category_id (FK → categories.id, SET NULL, 索引)  ← 全部已赋值，0 个 NULL
│       └── ……其他字段
│
├──┄ live_room_categories（M:N） ← 54 个房间有分类，742 个无分类
│   │
│   └── live_room_categories
│       ├── room_id (PK, FK → live_rooms.id, CASCADE)
│       ├── category_id (PK, FK → categories.id, CASCADE)
│       └── is_primary

topic_categories（专题内分类——与全局分类完全独立）
│  id, topic_id, name, sort_order
│
└── topic_category_rooms（专题分类→房间 M:N）
    ├── category_id (FK → topic_categories.id)
    ├── room_id (FK → live_rooms.id)
    └── sort_order
```

### 1.2 关键数据指标（实际数据库）

| 指标 | 值 | 说明 |
|:----|:---|:------|
| **categories 总数** | **261** | 包含大量测试产生的垃圾数据 |
| 其中真实分类 | **20** | 15 个 seed + 5 个手动添加 |
| 其中测试分类 | **241** | `test_cat_*`、`分类_*`、`科室_*` 等命名模式 |
| **experts 总数** | **384** | — |
| 已有 `category_id` 的专家 | **384（100%）** | 无需补 NULL |
| 唯一 `department` 值 | **41** | 30 个高频值 + 11 个低频值 |
| 包含 `/` 分隔符的复合科室名 | **5** | 如 "肝外科/超声医学科/介入超声专科" |
| **rooms 总数** | **796** | — |
| 有分类关联的 rooms | **54** | — |
| 无分类的 rooms | **742** | 多数为测试房间，需业务确认 |

### 1.3 20 个真实分类

| 名称 | slug | sort_order | 来源 |
|:----|:-----|:---------:|:----:|
| 普通外科 | general-surgery | 1 | seed |
| 神经外科 | neurosurgery | 2 | seed |
| 心内科 | cardiology | 3 | seed |
| 骨科 | orthopedics | 4 | seed |
| 肿瘤科 | oncology | 5 | seed |
| 妇产科 | obstetrics-gynecology | 6 | seed |
| 儿科 | pediatrics | 7 | seed |
| 眼科 | ophthalmology | 8 | seed |
| 耳鼻喉科 | ent | 9 | seed |
| 消化科 | gastroenterology | 10 | seed |
| 内分泌科 | endocrinology | 11 | seed |
| 泌尿外科 | urology | 12 | seed |
| 心胸外科 | cardiothoracic-surgery | 13 | seed |
| 血管外科 | vascular-surgery | 14 | seed |
| 皮肤科 | dermatology | 15 | seed |
| 口腔科 | — | — | 手动添加 |
| 整形外科 | — | — | 手动添加 |
| 器官移植科 | — | — | 手动添加 |
| 生殖医学科 | — | — | 手动添加 |
| 烧伤与创面修复科 | — | — | 手动添加 |

### 1.4 前端使用现状（saas_app-main）

| 页面 | 文件 | 分类用途 | 当前状态 |
|:----|:-----|:---------|:--------:|
| 首页 | `CategoryTabs.vue` | 横向滚动分类 Tab，点击筛选直播间 | ✅ 动态加载 |
| 全部科室 | `AllCategories.vue` | 全部科室列表 + 星标管理（本地存储） | ✅ 动态加载 |
| 专家列表 | `FilterTabs.vue` | 横向滚动科室筛选 Tab | ✅ 动态加载 |
| 创建直播 | `CreateLiveDrawer.vue` | 分类选择器 | ✅ 动态加载 |
| 专家详情 | `ExpertProfile.vue:15` | 展示 `department` 自由文本 | ⚠️ 硬编码字段名 |
| 专家卡片 | `ExpertCard.vue:18` | 展示 `department` 自由文本 | ⚠️ 硬编码字段名 |
| 直播间详情 | `live-manage/detail.vue:70` | **硬编码**"肝胆外科" | ❌ 未接 API |
| 房间管理 | `RoomList.vue:205` | **硬编码**`category: '--'` | ❌ 未接 API |
| 搜索/首页 | `home/index.vue` | 传 `category_id` 给后端 | ✅ 已对接 |
| 搜索/专家 | `expert/index.vue` | 传 `category_id` 给后端 | ✅ 已对接 |
| Mock 数据 | `mock-data.ts` | 硬编码 `category_id: 'cat_001'` | ❌ 需要更新 |

---

## 第二章：现存问题清单

> 注：P0/P1 已修复问题与 A2 方案文档一致，此处仅列出**当前仍存在的问题**（方案 C 针对性解决）。

### 🔴 P0 — 数据模型根本问题（方案 C 从根源解决）

| # | 问题 | 影响 | 详细 |
|:--|:-----|:----|:------|
| C1 | **`department` 自由文本与 `category_id` 无一致性保证** | 数据污染 | `experts.department` 是 VARCHAR(120) 自由文本，无 FK、无 CHECK 约束。运营录入时"冠脉介入组"和"冠状动脉介入组"被视为两个不同的值，实际映射到同一个 `category_id`。没有任何数据库约束阻止这种不一致。 |
| C2 | **`category_id` 可空导致分类筛选遗漏** | 业务可见性 | 当前 384 位专家均已赋值（0 NULL），但系统设计上允许 NULL。一旦出现新科室找不到对应分类，运营只能留 NULL，该专家在分类筛选 Tab 中完全不可见。 |
| C3 | **无受控科室词典，科室名随专家数增长而膨胀** | 长期维护 | 41 个唯一 department 值中，'胃肠外科一科'、'胃肠外科二科'、'胃肠外科三科'、'胃肠外科二科/'（含末尾斜杠）本应是同一科室的不同写法。自由文本下无法归并。 |

### 🟡 P1 — 架构设计问题

| # | 问题 | 影响 | 详细 |
|:--|:-----|:----|:------|
| C4 | **分类没有层次结构** | 扩展性 | 现有 20 个分类平铺，无法表达父子关系（心内科→冠脉介入组）。新增细分方向只能作为独立大类存在。 |
| C5 | **`categories.name` 全局唯一约束** | 命名灵活度 | `UNIQUE CONSTRAINT (name)` 阻止了不同根分类下出现同名子分类。例如"介入组"不能在"心内科"和"神经外科"下同时存在。 |
| C6 | **`is_primary` 字段名存疑** | 业务语义 | `live_room_categories.is_primary` 注释写明"规则尚未启用"。一个设计好但未实际使用的字段。 |
| C7 | **分类验证路径不统一** | 维护成本 | `create_expert` 中校验 `category_id`；`get_experts_public_list` 中查 `Category.name` 再做筛选；`homepage_search` 中写 `_validate_active_category_or_raise`。三套路径，散落三处。 |

### 🟡 P2 — 业务运营问题

| # | 问题 | 场景 | 详细 |
|:--|:-----|:-----|:------|
| C8 | **新科室出现无法映射** | 日常运营 | 管理者新增一个"心内科-结构性心脏病组"的专家，系统中没有对应分类。`_resolve_active_category_id` 匹配不到直接报错，导入中断。 |
| C9 | **批量导入时科室名无法落地** | CSV 导入 | 一次导入 100 个专家包含 20 种科室名，当前没有可用的兜底机制，匹配不到就报错一行中断一次。 |
| C10 | **映射不可靠** | 长期维护 | 现有 `migration_expert_category.py` 的 MAPPING 字典约 40 条硬编码在 Python 代码中，新映射需要修改代码部署。 |
| C11 | **管理员无法查看未映射科室** | 数据治理 | 没有 API 可以查询"哪些专家的 department 尚未映射到受控词表"。运营无法主动发现需要处理的数据。 |
| C12 | **241 个测试分类未清理** | 运维 | 数据库中 261 个分类中 241 个是测试遗留数据，不清理会在 `GET /categories` 接口中返回（虽然前端用了"主页"组件固定的分类列表展示而不会被干扰，但 API 响应数据庞大）。 |
| C13 | **742 个房间无分类** | 业务 | 796 个房间中仅 54 个有关联分类。需业务团队确认哪些是真实房间并按标题/描述关键词匹配分类。 |

---

## 第三章：C 方案详细设计（受控词表 + 分层分类）

### 3.1 设计原则

```
1. 科室受控词表：department 从自由文本提升为 FK → expert_departments 表，录入即受控
2. 单一真相源：category_id 由 department_id 推导，不独立存在
3. 只读匹配：导入时精确匹配受控词表，匹配不到归"其他"（绝不自动创建）
4. 分层分类：categories 加 parent_id 支持父子关系，预置常用子分类
5. 可审计映射：所有科室→分类的映射在数据库表中，SQL 可查、可修改、可追溯
6. 渐进实施：7 步迁移，每步可独立验证和回滚
```

### 3.2 数据库改动

#### 新增表：`expert_departments`（受控词表）

```python
class ExpertDepartment(Base):
    """
    专家科室受控词表。

    将 department 从自由文本变为受控词表，确保每个科室名全局唯一。
    科室→分类的映射存储在 category_id 中，是唯一的真相源。
    synonyms 用于导入时的同义词容错匹配。
    """
    __tablename__ = "expert_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False, unique=True,
                  comment='标准科室名称，全局唯一。如"乳腺外科"、"冠脉介入组"')
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        comment='科室所属的主分类 ID。RESTRICT 防止误删关联的根分类'
    )
    synonyms = Column(JSONB, nullable=False, default=list,
                      comment='同义词列表，JSON 数组。导入时用于容错匹配')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", lazy="select")

    __table_args__ = (
        Index('idx_expert_departments_name', 'name'),
        Index('idx_expert_departments_category_id', 'category_id'),
    )
```

**数据示例**：

| id | name | category_id | synonyms | is_active |
|:---|:-----|:-----------|:---------|:--------:|
| ... | 乳腺外科 | (普通外科.ID) | `["乳腺科", "乳房外科"]` | true |
| ... | 冠脉介入组 | (心内科.ID) | `["冠脉支架组", "冠心病介入组"]` | true |
| ... | 脊柱外科 | (骨科.ID) | `[]` | true |
| ... | 器官移植科/肾移植专科 | (器官移植科.ID) | `["肾移植专科"]` | true |
| ... | 其他-科室 | (其他.ID) | `[]` | true |

#### `experts` 表改造

```python
class Expert(Base):
    __tablename__ = "experts"

    # ... 其他字段不变 ...

    # ❌ 移除 department（自由文本）
    # department = Column(String(120), ...)   ← 删除此字段

    # ✅ 新增 department_id（受控词表 FK）
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("expert_departments.id", ondelete="SET NULL"),
        nullable=True,
        comment='科室 ID，关联 expert_departments 表。NULL 表示尚未映射标准科室'
    )

    # ✅ category_id 保持 NOT NULL（由 department_id 推导，应用层保证）
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=False,    # ← 从 True 改为 False
        comment='专家主分类，由 department_id 推导，应用层保证一致性'
    )

    # 新增关系
    expert_department = relationship("ExpertDepartment", lazy="select")

    __table_args__ = (
        Index('idx_experts_is_featured', 'is_featured', 'sort_order'),
        Index('idx_experts_is_active', 'is_active'),
        Index('idx_experts_user_id', 'user_id'),
        Index('idx_experts_category_id', 'category_id'),
        Index('idx_experts_department_id', 'department_id'),  # ← 新增索引
    )
```

**关键设计决策**：
- `category_id` 是**反范式缓存列**，从 `department_id → expert_departments.category_id` 推导
- 如果 `department_id=NULL`，则 `category_id` 指向"其他"分类
- **不需要触发器**——应用层的 service 方法保证一致性

#### `categories` 表加 `parent_id`

与 A2 方案相同，支持分层结构：

```python
class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        comment='父分类ID。NULL=根分类（一级分类）；非NULL=子分类（具体专业方向）'
    )
    # name 不再设全局 unique=True（改用部分索引）
    name = Column(String(100), nullable=False, comment='分类名称')
    slug = Column(String(120), nullable=True)
    icon = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

**唯一约束**（使用 PostgreSQL 部分索引替代 `UNIQUE`）：

```sql
-- 必须先删除旧约束
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key;

-- 根分类（parent_id IS NULL）：name 全局唯一
CREATE UNIQUE INDEX uq_root_category_name
ON categories (name)
WHERE parent_id IS NULL;

-- 子分类（parent_id IS NOT NULL）：同父类下 name 唯一
CREATE UNIQUE INDEX uq_sub_category_name
ON categories (parent_id, name)
WHERE parent_id IS NOT NULL;
```

#### `live_room_categories.is_primary` 启用规则

```sql
-- 启用 is_primary 的业务语义
-- 规则：一个房间最多有一个 is_primary=true 的分类
-- 规则：在直播间卡片/列表中展示 is_primary=true 的分类名
-- 规则：is_primary=true 的分类变更时自动取消其他分类的 is_primary
```

#### 新建迁移 SQL 清单

```sql
-- V4_create_expert_departments.sql
-- V5_add_category_parent_id.sql
-- V6_migrate_expert_departments.sql
-- V7_drop_experts_department.sql
```

参见 3.8 节（迁移计划）的完整 SQL。

### 3.3 受控词表设计方案

#### 初始种子数据（41 条标准科室 + 1 条兜底）

从现有 384 位专家的 41 个 `department` 值提取。高频 30 条可直接入库，低频 11 条需人工审核。

**高频值（直接入库，30 条）**：

```
# 普通外科 (4条): 乳腺外科, 甲状腺外科, 肝胆外科, 胃肠外科三科
# 神经外科 (2条): 神经外科, 显微创伤外手科
# 心内科   (0条): 无精确匹配—等待专家补充
# 骨科     (3条): 脊柱外科, 关节外科, 骨肿瘤科
# 妇产科   (2条): 妇科, 产科
# 耳鼻喉科 (3条): 鼻专科, 耳专科, 咽喉专科
# 泌尿外科 (2条): 泌尿外科, 泌尿外科/男科
# 心胸外科 (1条): 胸外科
# 血管外科 (1条): 血管外科
# 器官移植科(2条): 器官移植科, 器官移植科/肾移植专科
# 生殖医学科(2条): 生殖医学中心, 生殖男科专科
# 口腔科   (2条): 口腔科, 口内修复科
# 烧伤与创面修复科(1条): 烧伤与创面修复科
# 眼科     (1条): 眼科
# 消化科   (0条): 无精确匹配
# 内分泌科  (0条): 无精确匹配
# 整形外科  (1条): 整形外科
```

**低频值（需人工审核，11 条）**：

| department | 频次 | 可能的映射 |
|:-----------|:----:|:----------|
| 器官移植科/肾移植专科 | 2 | → 器官移植科 |
| 器官移植科/肝移植专科 | 1 | → 器官移植科 |
| 外科门诊 | 2 | 无精确匹配→需确认 |
| 肝外科/超声医学科/介入超声专科 | 1 | 复合科室→需人工拆分 |
| 胃肠外科一科 | 9 | → 普通外科 |
| 胃肠外科二科 | 8 | → 普通外科 |
| 胃肠外科二科/ | 1 | 含末尾斜杠，清洗后同↑ |
| 肾移植专科 | 1 | → 器官移植科 |
| 男科/生殖医学中心 | 1 | 复合写法→需确认 |
| 运动医学科 | 1 | → 骨科 |
| 变态反应专科 | 1 | 无分类→归"其他-科室" |

**兜底记录**：

```sql
-- "其他-科室" 兜底科室
INSERT INTO expert_departments (name, category_id, synonyms)
VALUES ('其他-科室', (SELECT id FROM categories WHERE name = '其他' AND parent_id IS NULL), '[]');
```

#### 字符串规范化辅助函数

```python
def _normalize_department_name(raw: str) -> str:
    """
    规范化科室名称：去零宽字符、统一全半角、繁简体归一、去首尾空白。

    与 A2 方案的 _normalize_category_name 逻辑一致。
    所有导入路径（CSV / API 创建 / 迁移脚本）应统一调用此函数。
    """
    if not raw:
        return ""

    # 1. 移除零宽字符及不可见控制字符
    cleaned = re.sub(
        r'[\u200b\u200c\u200d\ufeff\u00ad\u2060\u200e\u200f\u202a-\u202e]',
        '', raw
    )

    # 2. 全半角及兼容性字符归一（NFKC）
    cleaned = unicodedata.normalize('NFKC', cleaned)

    # 3. 移除末尾特殊字符（斜杠、空格、点号等）
    cleaned = cleaned.rstrip('/.。、，, ')

    # 4. 繁简体统一（库可用时执行）
    try:
        import zhconv
        cleaned = zhconv.convert(cleaned, 'zh-hans')
    except ImportError:
        pass

    return cleaned.strip()
```

#### 前置映射表（Static Mapping Dict，约 20 条）

用于处理科室名中不包含根分类子串的映射（如"乳腺外科"不含"普通外科"文本）：

```python
DEPARTMENT_CATEGORY_MAP = {
    # 普通外科相关
    '乳腺外科': '普通外科',
    '甲状腺外科': '普通外科',
    '肝胆外科': '普通外科',
    '胃肠外科一科': '普通外科',
    '胃肠外科二科': '普通外科',
    '胃肠外科三科': '普通外科',
    # 骨科相关
    '脊柱外科': '骨科',
    '关节外科': '骨科',
    '骨肿瘤科': '骨科',
    '运动医学科': '骨科',
    # 妇产科相关
    '妇科': '妇产科',
    '产科': '妇产科',
    # 耳鼻喉科
    '鼻专科': '耳鼻喉科',
    '耳专科': '耳鼻喉科',
    '咽喉专科': '耳鼻喉科',
    # 器官移植相关
    '肾移植专科': '器官移植科',
    '器官移植科/肾移植专科': '器官移植科',
    '器官移植科/肝移植专科': '器官移植科',
    # 泌尿外科
    '泌尿外科/男科': '泌尿外科',
    # 生殖医学科
    '生殖医学中心': '生殖医学科',
    '生殖男科专科': '生殖医学科',
    '男科/生殖医学中心': '生殖医学科',
}
```

**为什么只需要 20 条**：另外 ~20 条科室名直接包含根分类名（如"神经外科"→神经外科、"心胸外科"→心胸外科），子串匹配即可覆盖，不需要在映射表中显式列出。

### 3.4 核心逻辑改动

#### 3.4.1 科室解析函数（只读匹配，永不创建）

```python
from app.models.content_management import ExpertDepartment, Category

# 在 ExpertService.__init__ 中初始化的常量
OTHER_DEPT_ID: Optional[uuid.UUID] = None    # "其他-科室" 的 ID
OTHER_CATEGORY_ID: Optional[uuid.UUID] = None  # "其他" 根分类的 ID

async def _resolve_department_and_category(
    self,
    department_name: Optional[str],
    category_id: Optional[uuid.UUID],
) -> Tuple[Optional[uuid.UUID], uuid.UUID]:
    """
    解析专家科室和分类。

    规则（按优先级）：
    1. 传了 category_id → 直接使用，不查 department（管理员明确指定）
    2. 传了 department_name → 匹配 expert_departments 表
       a. 精确匹配 name → 返回 (department_id, category_id)
       b. 同义词匹配 synonyms → 返回 (department_id, category_id)
       c. 子串匹配大类 + 别名表 → 归入对应大类的"其他-{大类}"子分类
       d. 完全匹配不到 → 归入"其他-科室"，department_id=NULL
    3. 都没传 → (NULL, "其他"分类)

    永远不返回 None 作为 category_id。
    永远不写数据库（只读匹配）。
    """
    # 1. 管理员明确指定了分类
    if category_id is not None:
        cat = await self.db.get(Category, category_id)
        if cat and cat.is_active:
            return (None, category_id)
        raise InvalidParameterException("分类不存在或已禁用")

    # 2. 传了科室名称
    if department_name:
        normalized = self._normalize_department_name(department_name)

        # 2a. 精确匹配标准名称
        result = await self.db.execute(
            select(ExpertDepartment).where(
                ExpertDepartment.name == normalized,
                ExpertDepartment.is_active == True
            )
        )
        if dept := result.scalar_one_or_none():
            return (dept.id, dept.category_id)

        # 2b. 同义词匹配（synonyms JSONB 数组）
        result = await self.db.execute(
            text("""
                SELECT id, category_id FROM expert_departments
                WHERE :name = ANY(synonyms) AND is_active = true
            """),
            {"name": normalized}
        )
        if row := result.one_or_none():
            return (row[0], row[1])

        # 2c. 子串匹配大类 + 别名表
        category = await self._match_broad_category(normalized)
        if category:
            # 归入该大类下的"其他-{大类}"子分类
            fallback = await self.db.execute(
                select(ExpertDepartment.id).where(
                    ExpertDepartment.name == f"其他-{category.name}",
                    ExpertDepartment.is_active == True
                )
            )
            if fallback_id := fallback.scalar_one_or_none():
                return (fallback_id, category.id)
            # 如果没有"其他-{大类}"子分类，直接归到大类
            return (None, category.id)

        # 2d. 完全匹配不到 → "其他-科室"
        return (self.OTHER_DEPT_ID, self.OTHER_CATEGORY_ID)

    # 3. 都没传
    return (self.OTHER_DEPT_ID, self.OTHER_CATEGORY_ID)
```

#### 3.4.2 父类匹配算法（增强版，无正则回退）

```python
# 预置别名表（仅 20 条，覆盖名字中不含根分类名的科室）
DEPARTMENT_CATEGORY_MAP = { ... }  # 见 3.3 节

async def _match_broad_category(self, name: str) -> Optional[Category]:
    """
    从科室文本中提取根分类。

    策略（按顺序）：
    1. 子串匹配：根分类名包含在输入文本中（如"神经外科-重症组"→"神经外科"）
    2. 别名表匹配：在 DEPARTMENT_CATEGORY_MAP 中查找
    
    无正则回退。无模糊匹配。匹配不到返回 None（归"其他"）。
    """
    # 加载所有根分类（会话级缓存，一次会话只查一次）
    if not hasattr(self, '_root_categories'):
        result = await self.db.execute(
            select(Category).where(
                Category.parent_id == None,
                Category.is_active == True
            ).order_by(Category.sort_order)
        )
        self._root_categories = result.scalars().all()

    # 1. 子串匹配：根分类名是否在输入文本中
    for bc in self._root_categories:
        if bc.name in name:
            return bc

    # 2. 别名表匹配
    mapped_name = DEPARTMENT_CATEGORY_MAP.get(name)
    if mapped_name:
        for bc in self._root_categories:
            if bc.name == mapped_name:
                return bc

    return None
```

#### 3.4.3 创建专家的 Service 方法

```python
async def create_expert(self, expert_data: ExpertCreate, ...) -> ExpertItem:
    self._check_admin_permission(role)
    
    # ... user_id 唯一性检查 ...

    # 解析科室和分类（替换原来的 category_id 校验）
    dept_id, cat_id = await self._resolve_department_and_category(
        department_name=expert_data.department_name,
        category_id=expert_data.category_id,
    )

    # 构造创建数据
    create_dict = expert_data.model_dump(exclude={'department_name', 'category_id'})
    create_dict['department_id'] = dept_id
    create_dict['category_id'] = cat_id

    try:
        expert = await crud.create_expert_raw(self.db, create_dict)
        await self.db.commit()
        await self.db.refresh(expert)

        result = await self._build_expert_item(expert)
        return result
    except Exception as e:
        await self.db.rollback()
        raise
```

#### 3.4.4 批量导入的改动

```python
# 在 batch_import_experts_from_csv_optimized 中
# CSV 的 "department" 列（兼容旧列名）通过精确匹配转换为 department_id

dept_text = row_data.get("department_name") or row_data.get("department")
dept_id, cat_id = await self._resolve_department_and_category(
    department_name=dept_text,
    category_id=None,  # 导入时一般不传分类ID
)

# 不再调用原来的 _resolve_active_category_id
```

#### 3.4.5 响应构造辅助函数

```python
async def _build_expert_item(self, expert: Expert) -> ExpertItem:
    """构造专家响应，填充 department_name 和 category_name。"""
    # 预加载关系（如果尚未加载）
    if not hasattr(expert, 'expert_department') or expert.expert_department is None:
        if expert.department_id:
            result = await self.db.execute(
                select(ExpertDepartment).where(
                    ExpertDepartment.id == expert.department_id
                )
            )
            expert.expert_department = result.scalar_one_or_none()

    if not hasattr(expert, 'category') or expert.category is None:
        if expert.category_id:
            result = await self.db.execute(
                select(Category).where(Category.id == expert.category_id)
            )
            expert.category = result.scalar_one_or_none()

    item = ExpertItem.model_validate(expert)
    item.department_name = expert.expert_department.name if expert.expert_department else None
    item.category_name = expert.category.name if expert.category else None
    return item
```

#### 3.4.6 搜索/筛选中展开子分类（平铺查询）

与 A2 方案 §3.4.6 一致。不需要递归 CTE，2 层结构使用 `or_` 平铺查询：

```python
async def _expand_category_ids(db, category_id: UUID) -> List[UUID]:
    """获取当前分类ID及其直接子分类的ID列表（仅2层）。"""
    result = await db.execute(
        select(Category.id).where(
            or_(
                Category.id == category_id,
                Category.parent_id == category_id
            ),
            Category.is_active == True
        )
    )
    return result.scalars().all()
```

#### 3.4.7 CRUD 层 keyword 搜索改动

```python
# app/crud/experts.py — get_experts_public_list

# department 字段已移除，改为通过 expert_departments 表搜索
if keyword and keyword.strip():
    kw = f"%{keyword.strip()}%"
    conditions.append(
        or_(
            Expert.name.ilike(kw),
            Expert.hospital.ilike(kw),
            # 关联搜索受控词表
            Expert.department_id.in_(
                select(ExpertDepartment.id).where(
                    ExpertDepartment.name.ilike(kw)
                )
            ),
            Expert.expertise_areas.ilike(kw),
            Expert.bio.ilike(kw),
        )
    )
```

### 3.5 前端改动清单

| 文件 | 改动 | 影响范围 |
|:----|:-----|:---------|
| `ExpertProfile.vue:15` | `department` → `department_name`（受控词表名） | 专家详情页展示 |
| `ExpertCard.vue:18` | `department` → `department_name` | 专家列表卡片 |
| `expert/detail.vue:11` | 传参从 `detail.department` → `detail.department_name` | 专家详情页 |
| `live-manage/detail.vue:70` | 硬编码"肝胆外科" → 调 `getRoomCategories()` API | 直播间详情 |
| `RoomList.vue:205` | 硬编码 `'--'` → `room.primary_category_name` | 房间管理列表 |
| **新增**：科室管理页 | 调用 `GET/POST/PATCH /admin/expert-departments` | 运营后台 |
| **新增**：未映射科室看板 | 调用 `GET /admin/expert-departments/unmapped` | 运营后台 |
| **无需改动**：`CategoryTabs.vue`、`FilterTabs.vue`、`AllCategories.vue`、`CreateLiveDrawer.vue`、`home/index.vue`、`expert/index.vue`（只传 `category_id`） | | |

**前端兼容性**：
- 旧代码读 `expert.department` → 改为 `expert.department_name`
- 旧代码读 `expert.category_id` → 不变
- 新增字段：`expert.department_name`、`expert.department_id`、`expert.category_name`

### 3.6 API 接口变更

| 接口 | 改动 | 是否兼容 |
|:----|:-----|:--------:|
| `GET /categories` | 新增 `parent_id` 字段 | ✅ 向前兼容 |
| `GET /experts` | 新增响应字段 `department_name`、`department_id`、`category_name`；请求参数 `department` → `department_name` | 🟡 请求字段名变化，旧 `department` 参数保留兼容 |
| `GET /experts?category_id=` | 加入子分类展开（`= ANY`） | ✅ 参数不变，结果更全 |
| `POST /experts` | `department` → `department_name`；`category_id` 可选 | 🟡 请求字段名变化 |
| `PATCH /experts/{id}` | 同上 | 🟡 请求字段名变化 |
| `GET /admin/expert-departments` | **新增** | ✅ 全新接口 |
| `POST /admin/expert-departments` | **新增** | ✅ 全新接口 |
| `PATCH /admin/expert-departments/{id}` | **新增** | ✅ 全新接口 |
| `GET /admin/expert-departments/unmapped` | **新增**（列出 `department_id=NULL` 的专家） | ✅ 全新接口 |

### 3.7 Admin API 设计（科室管理端点）

```python
# app/api/v1/endpoints/expert_departments.py（新增）

expert_dept_admin_router = APIRouter(tags=["科室管理-管理员"])

@expert_dept_admin_router.get("/admin/expert-departments")
async def list_departments(
    page: int = 1, size: int = 50,
    is_active: Optional[bool] = None,
    category_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """列出所有科室（分页，支持按分类筛选）。"""

@expert_dept_admin_router.post("/admin/expert-departments")
async def create_department(
    data: ExpertDepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建新科室（name + category_id + 可选 synonyms）。"""

@expert_dept_admin_router.patch("/admin/expert-departments/{id}")
async def update_department(
    id: uuid.UUID,
    data: ExpertDepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新科室名称/分类/同义词。"""

@expert_dept_admin_router.delete("/admin/expert-departments/{id}")
async def soft_delete_department(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """软删除科室（is_active=false）。"""

@expert_dept_admin_router.get("/admin/expert-departments/unmapped")
async def list_unmapped_experts(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    列出所有 department_id=NULL 的专家。
    这是运营的核心工具——查看有哪些专家还未映射标准科室。
    结果按专家姓名排序，包含 id、name、hospital、created_at。
    """
```

**Schema 定义**：

```python
class ExpertDepartmentCreate(BaseModel):
    name: str = Field(..., max_length=120, description="标准科室名称")
    category_id: uuid.UUID = Field(..., description="所属主分类ID")
    synonyms: list[str] = Field(default_factory=list, description="同义词列表")

class ExpertDepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    category_id: Optional[uuid.UUID] = None
    synonyms: Optional[list[str]] = None
    is_active: Optional[bool] = None

class ExpertDepartmentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    category_id: uuid.UUID
    category_name: Optional[str] = None
    synonyms: list[str]
    is_active: bool
    expert_count: int = Field(0, description="关联的专家数")
```

### 3.8 迁移计划（7 步）

```
Step 1（安全，新增表）：创建 expert_departments 表
  │  ├── 执行 V4_create_expert_departments.sql
  │  └── 入库 42 条种子数据（41 条标准科室 + "其他-科室"兜底）
  │
Step 2（安全，NULLABLE FK）：experts 加 department_id 列
  │  ├── ALTER TABLE experts ADD COLUMN department_id UUID;
  │  └── CREATE INDEX idx_experts_department_id;
  │
Step 3（中等风险，需指定顺序）：categories 加 parent_id
  │  ├── 执行 V5_add_category_parent_id.sql
  │  │   ├── ALTER TABLE categories DROP CONSTRAINT categories_name_key;
  │  │   ├── CREATE UNIQUE INDEX uq_root_category_name …;
  │  │   ├── CREATE UNIQUE INDEX uq_sub_category_name …;
  │  │   └── ALTER TABLE categories ADD COLUMN parent_id UUID …;
  │  └── 20 个真实分类保持 parent_id=NULL（根分类）
  │      241 个测试分类保持 parent_id=NULL（不受影响）
  │
Step 4（Dry-Run 先出报告）：迁移已有 department 数据
  │  ├── 执行 V6_migrate_expert_departments.py（Python 迁移脚本）
  │  │   ├── 遍历 384 个专家
  │  │   ├── _normalize_department_name() 清洗
  │  │   ├── 精确匹配 expert_departments.name
  │  │   ├── 同义词匹配
  │  │   ├── 子串匹配 + 别名表 → 归"其他-{大类}"
  │  │   └── 完全匹配不到 → department_id=NULL, category_id="其他"
  │  ├── 输出 migration_report.csv
  │  │   └── [专家ID, 姓名, 原department, 映射到的科室名, 映射到的分类名]
  │  └── 人工审核 11 条低频值，修正映射表
  │
Step 5（不可逆，最后执行）：删除 department 列 + NOT NULL
  │  ├── 执行 V7_drop_experts_department.sql
  │  │   ├── ALTER TABLE experts DROP COLUMN department;
  │  │   └── ALTER TABLE experts ALTER COLUMN category_id SET NOT NULL;
  │  └── 注意：执行前必须确认 Step 4 迁移报告已审核通过
  │
Step 6（低风险）：部署新代码
  │  ├── 新 Model / Schema / Service / CRUD
  │  ├── 新 Admin API（科室管理端点）
  │  └── 前端接入 department_name / category_name
  │
Step 7（独立，分批进行）：清理 241 个测试分类
  │  ├── 逐一确认是否有真实业务依赖
  │  ├── 对有房间关联的测试分类先解除关联
  │  └── DELETE FROM categories WHERE name LIKE 'test_cat_%' …;
```

### 3.9 历史数据迁移空跑流程

```
┌──────────────────────────────────────────────────────────┐
│  步骤 A：帕累托分析（已完成）                              │
│                                                          │
│  SELECT department, COUNT(*) FROM experts                │
│  GROUP BY department ORDER BY COUNT(*) DESC;             │
│                                                          │
│  → 41 个唯一值，前 30 条覆盖 373/384 = 97% 数据          │
│  → 30 条高频值可直接自动化映射                              │
│  → 11 条低频值需人工审核（见 3.3 节）                      │
├──────────────────────────────────────────────────────────┤
│  步骤 B：Dry-Run 迁移脚本                                 │
│                                                          │
│  输出 migration_report.csv:                              │
│  [专家ID, 姓名, 原department, 拟匹配科室, 拟匹配分类]      │
│                                                          │
│  → 检查复合写法是否有误（"肝外科/超声医学科"拆解）          │
│  → 检查末尾斜杠是否已清洗（"胃肠外科二科/"）               │
│  → 检查"外科门诊"等无匹配项是否归入"其他"                  │
│  → 基于报表修正 MAPPING 字典                               │
├──────────────────────────────────────────────────────────┤
│  步骤 C：正式迁移（带降级兜底）                            │
│                                                          │
│  匹配成功 → SET department_id, category_id 不变           │
│  匹配失败 → SET department_id=NULL, category_id="其他"     │
│  原始 department 文本 → 写入 expert_departments.description │
│  或存储到 ExpertDepartment 的追加字段中                     │
└──────────────────────────────────────────────────────────┘
```

---

## 第四章：风险与缓解

### 4.1 迁移步骤顺序错误

**风险**：Step 3 中 `DROP CONSTRAINT` 和 `CREATE INDEX` 的顺序不可逆。如果先部署代码再执行迁移，旧 UNIQUE 约束会导致子分类插入失败。

**缓解**：
- Runbook 明确标注：Step 3 必须在 Step 6（代码部署）之前完成
- `DROP CONSTRAINT IF EXISTS` 确保幂等
- 迁移 SQL 使用事务包裹，失败时整体回滚

### 4.2 低频 department 值映射错误

**风险**：11 条低频值中有复合写法（"肝外科/超声医学科/介入超声专科"），映射到单一分类可能不合理。

**缓解**：
- Dry-Run 先输出完整报告，人工审核后再执行正式迁移
- 无法确认的映射暂时归入"其他-{大类}"，不阻塞迁移
- 运营后续可通过 `GET /admin/expert-departments/unmapped` 查看并调整

### 4.3 241 个测试分类影响迁移

**风险**：`ADD COLUMN parent_id` 后测试分类的 `parent_id=NULL` 保持不变。但如果后续要插入子分类，子分类名可能与测试分类名冲突（测试分类名带随机后缀，冲突概率极低）。

**缓解**：不影响。测试类名带 `_xxx` 随机后缀，不与标准名冲突。Step 7 单独清理。

### 4.4 `category_id` 改为 NOT NULL 时的约束违反

**风险**：如果某个专家的 `category_id` 在迁移后仍为 NULL（理论上不会发生，因为 Step 4 全部归入"其他"），ALTER 语句会失败。

**缓解**：
- Step 4 中确保每个专家都设置 `category_id`（匹配不到的统一设"其他"）
- Step 5 之前运行验证 SQL：
  ```sql
  SELECT COUNT(*) FROM experts WHERE category_id IS NULL;
  ```
- 如果有 NULL，先补全再执行 ALTER

### 4.5 `ON DELETE RESTRICT` 阻止父分类删除

**风险**：`expert_departments.category_id` 和 `categories.parent_id` 都使用 `RESTRICT`。误删根分类时会被阻止。

**缓解**：这是安全设计，不是 bug。分类使用 `is_active` 软删除，不物理 DELETE。

### 4.6 `department` 列删除后无法恢复

**风险**：Step 5 `DROP COLUMN department` 不可逆。如果迁移后发现映射错误，原始数据丢失。

**缓解**：
- Step 4 运行 Dry-Run，人工确认后再执行 Step 5
- 在 `expert_departments` 表中用 `description` 或 `original_departments`（JSONB）字段保留原始文本：
  ```json
  {
    "张医生": "原科室: 肝外科/超声医学科/介入超声专科",
    "李医生": "原科室: 胃肠外科二科/"
  }
  ```
- 保留 migration_report.csv 作为离线备份

### 4.7 `synonyms` JSONB 数组查询性能

**风险**：`WHERE :name = ANY(synonyms)` 在 JSONB 数组上使用索引？PostgreSQL 的 `ANY()` 操作 JSONB 数组默认不走 GIN 索引。

**缓解**：
- 当前数据量（384 专家，42 科室）下全表扫描也无压力
- 未来如果扩展到 >10000 科室，可以为 `synonyms` 列创建 GIN 索引：
  ```sql
  CREATE INDEX idx_expert_departments_synonyms ON expert_departments USING GIN (synonyms jsonb_path_ops);
  ```

### 4.8 新建科室的运营延迟

**风险**：运营在 UI 上创建新科室，但创建前导入的专家全部归入"其他-科室"，需要手动调整。

**缓解**：
- `GET /admin/expert-departments/unmapped` 直接列出所有待处理的专家
- 运营可在科室创建后批量更新：
  ```sql
  UPDATE experts SET department_id = :new_dept_id, category_id = :new_cat_id
  WHERE id IN (:unmapped_ids);
  ```

### 4.9 `_resolve_department_and_category` 的只读路径不需要事务

**风险**：当前 `batch_import_experts_from_csv` 中使用 `begin_nested()` 做每行 savepoint。`_resolve_department_and_category` 是只读查询，不应在嵌套事务中执行。

**缓解**：已经在当前的 batch_import 流程中，`_resolve_active_category_id` 在 savepoint 之前调用（第 611-614 行），方案 C 保持相同的调用顺序——先解析（只读），再创建（写）。不改变事务边界。

### 4.10 前端字段名变化兼容性

**风险**：旧前端代码读 `expert.department`，方案 C 改为 `expert.department_name`。如果前端未同步更新，展示为空。

**缓解**：
- API 响应中同时返回 `department`（兼容，值与 `department_name` 相同）和 `department_name`
- **仅在前端代码完全更新后，再移除 `department` 兼容字段**
- 过渡期（2 周）同时返回两个字段，给前端留足更新时间

---

## 第五章：与 A2 方案的最终对比

| 维度 | A2（层次FK + 自动创建） | C（受控词表 + 只读匹配） |
|:----|:----------------------|:------------------------|
| **department 处理** | ❌ 保留为自由文本，前端不用 | ✅ **提升为 FK，受控词表保证一致性** |
| **运行时行为** | 🟡 非确定性：UPSERT + 模糊匹配，相同输入可能因并发产生不同结果 | 🟢 **确定性：只读精确匹配，相同输入永远映射到相同科室** |
| **新科室处理** | ✅ 自动创建子分类（`is_public=false`） | ⚠️ 匹配不到归"其他-科室"，运营通过 unmapped API 可见 |
| **脏数据控制** | 🔴 `is_public=false` 机制复杂，有 UX 矛盾 | 🟢 不可能产生脏数据（不自动创建） |
| **并发安全** | 🟡 UPSERT + `on_conflict_do_nothing` + 二次查询，有 3 个 Bug（见审计） | 🟢 **无并发问题（只读查询）** |
| **查询性能** | 🟢 无额外 JOIN | 🟢 无额外 JOIN（category_id 反范式缓存） |
| **运营工具** | 🟡 需"待审核分类看板" + 合并 API + 孤儿清理 | 🟢 unmapped API + 科室管理 CRUD，更简单 |
| **实现复杂度** | 🟡 ~15 个文件，2 周 | 🟢 ~10 个文件，1 周 |
| **生产风险** | 🟡 11 个隐患（含 3 个 P0） | 🟢 **7 个风险全部在 Dry-Run 阶段可发现，线上风险集中于 Step 5** |
| **数据可追溯** | 🟡 映射在 Python 字典中，不可被 SQL 查询 | ✅ **映射在数据库表中，SQL 可直接查、改、审核** |
| **适合场景** | 数据量大、科室名变化频繁、有专职运营团队审核 | **数据量中等、需要数据纯净度、希望最小化运行时风险** |

---

## 第六章：附录

### 附录 A：评审决策记录

| 编号 | 提议 | 决策 | 优先级 |
|:----|:-----|:----|:------|
| R1 | `expert_departments.category_id` 用 `RESTRICT` 而非 `SET NULL` | ✅ 采纳 | P0 |
| R2 | 迁移前必须 Dry-Run 出报告 | ✅ 采纳 | P0 |
| R3 | `department` 兼容字段保留 2 周过渡 | ✅ 采纳 | P1 |
| R4 | `synonyms` JSONB 字段需记录匹配命中次数，帮助运营优化 | ⏸️ 暂缓 | P3 |
| R5 | 241 个测试分类是否自动清理 | ⏸️ 暂缓，需业务确认 | P2 |

### 附录 B：V4_create_expert_departments.sql（完整）

```sql
CREATE TABLE IF NOT EXISTS expert_departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) UNIQUE NOT NULL,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    synonyms JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_expert_departments_name ON expert_departments(name);
CREATE INDEX idx_expert_departments_category_id ON expert_departments(category_id);

COMMENT ON TABLE expert_departments IS '专家科室受控词表。将 department 从自由文本变为受控词表';
COMMENT ON COLUMN expert_departments.name IS '标准科室名称，全局唯一';
COMMENT ON COLUMN expert_departments.synonyms IS '同义词列表 JSON 数组，如 ["乳腺科", "乳房外科"]';
COMMENT ON COLUMN expert_departments.category_id IS '科室所属主分类 ID。ON DELETE RESTRICT 防止误删';
```

### 附录 C：V5_add_category_parent_id.sql（完整）

```sql
-- 1. 先删除旧唯一约束（不可逆，但幂等）
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key;

-- 2. 根分类名称全局唯一（部分索引）
CREATE UNIQUE INDEX IF NOT EXISTS uq_root_category_name
ON categories (name)
WHERE parent_id IS NULL;

-- 3. 子分类在同父类下唯一（部分索引）
CREATE UNIQUE INDEX IF NOT EXISTS uq_sub_category_name
ON categories (parent_id, name)
WHERE parent_id IS NOT NULL;

-- 4. 添加 parent_id 自引用外键（RESTRICT 防止误删父分类）
ALTER TABLE categories ADD COLUMN IF NOT EXISTS parent_id UUID
REFERENCES categories(id) ON DELETE RESTRICT;

-- 5. 创建索引
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);
```

### 附录 D：V7_drop_experts_department.sql（完整）

```sql
-- 请先执行 V6_migrate_expert_departments.py 并确认迁移报告
-- 先验证
DO $$
DECLARE
    null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count FROM experts WHERE category_id IS NULL;
    IF null_count > 0 THEN
        RAISE EXCEPTION '仍有 % 个专家的 category_id 为 NULL，不能删除 department 列', null_count;
    END IF;
END $$;

-- 再执行
ALTER TABLE experts DROP COLUMN IF EXISTS department;
ALTER TABLE experts ALTER COLUMN category_id SET NOT NULL;
```

### 附录 E：41 条种子数据映射表（完整）

```sql
-- 插入前需要先获取各分类的 ID（为简洁，此处用 slug 标识）
-- 实际迁移脚本中通过子查询获取 ID

INSERT INTO expert_departments (name, category_id, synonyms) VALUES
('普通外科',     (SELECT id FROM categories WHERE name = '普通外科'), '[]'),
('神经外科',     (SELECT id FROM categories WHERE name = '神经外科'), '[]'),
('泌尿外科',     (SELECT id FROM categories WHERE name = '泌尿外科'), '["泌尿外科/男科"]'),
('胸外科',       (SELECT id FROM categories WHERE name = '心胸外科'), '[]'),
('血管外科',     (SELECT id FROM categories WHERE name = '血管外科'), '[]'),
('眼科',         (SELECT id FROM categories WHERE name = '眼科'), '[]'),
('口腔科',       (SELECT id FROM categories WHERE name = '口腔科'), '[]'),
('器官移植科',   (SELECT id FROM categories WHERE name = '器官移植科'), '["器官移植科/肾移植专科","器官移植科/肝移植专科","肾移植专科"]'),
('整形外科',     (SELECT id FROM categories WHERE name = '整形外科'), '[]'),
('烧伤与创面修复科', (SELECT id FROM categories WHERE name = '烧伤与创面修复科'), '[]'),
('乳腺外科',     (SELECT id FROM categories WHERE name = '普通外科'), '["乳腺科","乳房外科"]'),
('甲状腺外科',   (SELECT id FROM categories WHERE name = '普通外科'), '[]'),
('肝胆外科',     (SELECT id FROM categories WHERE name = '普通外科'), '[]'),
('胃肠外科一科', (SELECT id FROM categories WHERE name = '普通外科'), '["胃肠外科一科/"]'),
('胃肠外科二科', (SELECT id FROM categories WHERE name = '普通外科'), '["胃肠外科二科/"]'),
('胃肠外科三科', (SELECT id FROM categories WHERE name = '普通外科'), '[]'),
('脊柱外科',     (SELECT id FROM categories WHERE name = '骨科'), '[]'),
('关节外科',     (SELECT id FROM categories WHERE name = '骨科'), '[]'),
('骨肿瘤科',     (SELECT id FROM categories WHERE name = '骨科'), '[]'),
('妇科',         (SELECT id FROM categories WHERE name = '妇产科'), '[]'),
('产科',         (SELECT id FROM categories WHERE name = '妇产科'), '[]'),
('鼻专科',       (SELECT id FROM categories WHERE name = '耳鼻喉科'), '[]'),
('耳专科',       (SELECT id FROM categories WHERE name = '耳鼻喉科'), '[]'),
('咽喉专科',     (SELECT id FROM categories WHERE name = '耳鼻喉科'), '[]'),
('生殖医学中心', (SELECT id FROM categories WHERE name = '生殖医学科'), '["生殖男科专科","男科/生殖医学中心"]'),
('显微创伤外手科', (SELECT id FROM categories WHERE name = '神经外科'), '[]'),
('口内修复科',   (SELECT id FROM categories WHERE name = '口腔科'), '[]'),
('运动医学科',   (SELECT id FROM categories WHERE name = '骨科'), '[]'),
('变态反应专科', (SELECT id FROM categories WHERE name = '其他' AND parent_id IS NULL), '[]'),
('外科门诊',     (SELECT id FROM categories WHERE name = '其他' AND parent_id IS NULL), '[]'),
-- 复合写法（需要清洗后人工确认）
('肝外科/超声医学科/介入超声专科', (SELECT id FROM categories WHERE name = '其他' AND parent_id IS NULL), '[]'),
-- 兜底
('其他-科室', (SELECT id FROM categories WHERE name = '其他' AND parent_id IS NULL), '[]');
```
