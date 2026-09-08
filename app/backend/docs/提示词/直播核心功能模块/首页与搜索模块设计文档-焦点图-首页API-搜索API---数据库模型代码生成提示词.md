# 首页与搜索模块设计文档-焦点图-首页API-搜索API---数据库模型代码生成提示词

**版本**: V1.0  
**创建日期**: 2026-01-18  
**基于设计文档**: 直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md  
**目标文件**: `backend/live_core_service/app/models/homepage_search.py`

---

## **高效 AI 提示词：生成首页与搜索模块的 SQLAlchemy 模型**

### **1. 角色定义 (Role Definition)**

你是一名精通 SQLAlchemy 2.0（异步）和 FastAPI 的资深 Python 后端工程师。你的任务是为 `LiveCore Service` 项目创建首页与搜索模块的数据库模型代码，确保与现有代码风格、架构和规范完全一致。

**🔥 增量开发模式** (非常重要):
- 这是一个 **增量开发** 任务，现有代码已经可以正常运行和测试
- **只能新增代码**，不能修改现有文件（除了追加导入）
- Base 类已经在 `database.py` 中定义，**不需要也不能修改** `database.py`
- 现有模型文件（如 `live_core.py`、`brand.py`）**不能修改**
- 只需要创建新文件 `homepage_search.py`
- 只需要在 `models/__init__.py` 中**追加**导入语句

**核心职责**:
- 严格遵循设计文档中的数据库设计规范
- 确保生成的代码与现有代码风格完全一致
- 遵循学院派架构（Clean Architecture）原则
- 遵循安全编码规范（不暴露敏感信息）

---

### **2. 任务目标 (Task Objective)**

生成 `homepage_search.py` 文件，该文件位于项目的 `backend/live_core_service/app/models/` 目录下。这个文件将包含首页与搜索模块所需的 SQLAlchemy 模型类：

1. **FeaturedContent**: 首页精选/焦点图表（featured_content）

**⚠️ 重要提示**:
- 必须创建新文件 `homepage_search.py`
- 必须确保模型类正确定义，包括字段、索引等
- **注意**：`target_id` 字段是应用层关联，**不设置数据库外键**（因为target_type可能指向不同的表：room/session/topic/brand/external等）

当模型被正确导入并注册到 SQLAlchemy 的元数据后，可以通过以下方式创建对应的数据库表：
- **方式1（推荐）**: 运行 `python app/init_db.py` - 会自动识别 `models/__init__.py` 中导出的所有模型

---

### **3. 核心上下文信息 (Core Context Information)**

这是成功生成代码所必需的背景信息：

#### **3.1. 项目文件结构 (Project File Structure)**

你的模型文件必须基于以下项目结构来正确组织代码：

```
backend/live_core_service/
├── app/
│   ├── __init__.py
│   ├── database.py                    # 定义了 Base, AsyncEngine 和 AsyncSession
│   ├── models/
│   │   ├── __init__.py                # 导入所有模型，便于统一管理
│   │   ├── live_core.py               # 现有模型：LiveRoom, LiveSession, SessionStatistics
│   │   ├── brand.py                   # 现有模型：Brand, BrandTopic, BrandRoom
│   │   └── homepage_search.py         # <-- 这是你要创建的目标文件
│   └── core/
│       └── config.py                  # 配置文件
```

**⚠️ 重要提示 - 增量开发原则**:
- ✅ **可以新建**: `homepage_search.py` 文件
- ✅ **可以追加**: 在 `models/__init__.py` 中添加导入语句
- ❌ **不要修改**: `database.py` 文件（已有代码依赖它）
- ❌ **不要修改**: `live_core.py` 文件（已有模型正在使用）
- ❌ **不要修改**: `brand.py` 文件（已有模型正在使用）
- ❌ **不要修改**: `init_db.py` 文件（它会自动识别新模型）

#### **3.2. 现有模型文件参考 (Existing Model Reference)**

**文件**: `backend/live_core_service/app/models/brand.py`

**关键观察点**（你必须遵循的风格，共12个）:

1. **Base类导入方式**: `from app.database import Base`（**注意：不是 `app.models.base`**）
2. **导入顺序和重命名**: 
   - TIMESTAMP从 `sqlalchemy` 导入（**不是** `sqlalchemy.dialects.postgresql`）
   - UUID从 `sqlalchemy.dialects.postgresql` 导入
   - **Enum必须重命名为SAEnum**，避免与Python enum模块冲突
3. **导入 `func` 用于数据库函数**: `from sqlalchemy.sql import func`（用于 `func.now()`）
4. **枚举类定义**: 继承 `str, enum.Enum`，枚举值为小写字符串
5. **UUID字段定义**: `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4`
6. **时间戳字段定义**: `TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()`（**数据库级默认值**）
7. **索引创建方式**: 使用 `__table_args__` 显式命名（**不要使用** `index=True`）
8. **外键使用**: `ForeignKey` 并配合 `relationship` 定义关联
9. **级联删除**: 使用 `cascade="all, delete-orphan"`
10. **字段注释**: 关键字段包含comment说明对应关系
11. **__repr__方法**: 这是**最佳实践**，强烈建议添加，便于调试和日志记录
12. **导入 `Index` 用于显式命名索引**: `from sqlalchemy import Index`

**完整导入语句示例**（必须在代码中包含）:

```python
"""
首页与搜索模块的数据库模型

本模块包含首页与搜索模块所需的 SQLAlchemy 模型类：
- FeaturedContent: 首页精选/焦点图表
"""
import uuid
from datetime import datetime
import enum

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Integer, Boolean, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base  # 注意：Base 在 database.py 中，不是 models/base.py
```

**⚠️ 关键注意事项**（必须在代码中遵循）:
1. ✅ 标准库导入放在最前面（uuid, datetime, enum）
2. ✅ TIMESTAMP从 `sqlalchemy` 导入，**不是** `sqlalchemy.dialects.postgresql`
3. ✅ 导入 `func` 用于 `func.now()`（数据库级时间戳）
4. ✅ 导入 `Index` 用于显式命名索引
5. ⚠️ **注意**：`target_id` 字段**不设置外键**（应用层关联，target_type可能指向不同表）

#### **3.3. 技术栈 (Technology Stack)**

- **Python版本**: 3.9+
- **SQLAlchemy版本**: 2.0（异步模式，使用 `AsyncSession`）
- **数据库**: PostgreSQL
- **ORM模式**: 异步模式
- **架构风格**: 学院派（Clean Architecture）

#### **3.4. Base类定义位置**

**⚠️ 关键信息**: Base类在 `database.py` 中定义，**不是** `base.py`

**文件**: `backend/live_core_service/app/database.py`
```python
# 创建基类
Base = declarative_base()
```

**导入方式**:
```python
from app.database import Base  # 正确
# from app.models.base import Base  # ❌ 错误：base.py 不存在
```

#### **3.5. 数据库初始化脚本说明**

**⚠️ 重要**: 项目中有两个数据库初始化脚本，必须明确说明使用哪个：

**脚本1: `app/init_db.py` (推荐使用)**
- **特点**: 通过包级导入自动识别所有模型
- **工作原理**: `import app.models` 会执行 `models/__init__.py`，所有导出的模型会自动注册到 `Base.metadata`
- **增量开发适配**: ✅ **完美适配** - 只需在 `models/__init__.py` 中追加导入，无需修改脚本本身
- **使用方式**: `python app/init_db.py`

**脚本2: `app/scripts/create_tables.py` (不推荐修改)**
- **特点**: 需要显式导入每个模型类
- **增量开发适配**: ❌ **不适配** - 需要修改脚本添加新模型的导入，违反增量开发原则
- **结论**: 不推荐使用，使用 `init_db.py` 代替

#### **3.6. 设计文档规范提取 (Design Document Specifications)**

**从设计文档中提取的数据库设计规范**（Section 2.1）:

1. **UUID主键生成**：
   - ✅ 所有表的主键UUID**必须在应用层生成**（`uuid.uuid4()`）
   - ❌ 禁止使用数据库默认值 `DEFAULT gen_random_uuid()`

2. **时间戳字段**：
   - 使用 `TIMESTAMPTZ` 类型（SQLAlchemy中为 `TIMESTAMP(timezone=True)`）
   - `created_at`: `DEFAULT CURRENT_TIMESTAMP`（`server_default=func.now()`）
   - `updated_at`: `DEFAULT CURRENT_TIMESTAMP` + 触发器自动更新（`server_default=func.now(), onupdate=func.now()`）

3. **字段注释**：
   - 所有表必须有 `COMMENT ON TABLE`（在模型类文档字符串中体现）
   - 关键字段必须有 `COMMENT ON COLUMN`（使用 `comment` 参数）

4. **索引策略**：
   - 常用查询条件添加复合索引
   - 使用 `__table_args__` 显式命名索引

5. **应用层关联**：
   - `target_id` 字段**不设置数据库外键**（因为target_type可能指向不同的表）
   - 通过应用层验证保证引用完整性

**从设计文档中提取的安全编码规范**（Section 1.4）:

1. **禁止硬编码敏感信息**：所有敏感配置（数据库密码、JWT密钥等）必须通过环境变量配置
2. **日志脱敏规范**：`__repr__` 方法应避免暴露敏感信息，仅显示必要的标识信息（如id、名称等）
3. **字段注释安全**：注释和文档字符串中**禁止包含真实的敏感信息示例**

---

### **4. 代码生成具体要求 (Specific Code Generation Requirements)**

#### **4.1. 导入语句要求**

必须使用以下导入语句：

```python
"""
首页与搜索模块的数据库模型

本模块包含首页与搜索模块所需的 SQLAlchemy 模型类：
- FeaturedContent: 首页精选/焦点图表
"""
import uuid
from datetime import datetime

# SQLAlchemy 核心导入
from sqlalchemy import Column, String, Integer, Boolean, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base  # 注意：Base 在 database.py 中，不是 models/base.py
```

**⚠️ 关键注意事项**（必须在代码中遵循）:
1. ✅ 标准库导入放在最前面（uuid, datetime）
2. ✅ TIMESTAMP从 `sqlalchemy` 导入，**不是** `sqlalchemy.dialects.postgresql`
3. ✅ 导入 `func` 用于 `func.now()`（数据库级时间戳）
4. ✅ 导入 `Index` 用于显式命名索引

#### **4.2. 模型类定义要求**

根据设计文档Section 2.1的DDL定义，必须创建以下模型类：

##### **4.2.1. FeaturedContent 模型类**

**表名**: `featured_content`

**字段要求**（根据DDL Section 2.1）:
- `id`: UUID主键，应用层生成（`default=uuid.uuid4`）
- `title`: String(255), NOT NULL
- `subtitle`: String(512), nullable
- `image_url`: String(512), NOT NULL
- `target_type`: String(50), nullable（应用层关联类型：room/session/topic/brand/external等）
- `target_id`: UUID, nullable（**不设置外键**，应用层关联）
- `target_url`: String(512), nullable（外部链接，优先级高于target_id）
- `sort_order`: Integer, default=0
- `is_active`: Boolean, default=True（软删除标识）
- `start_at`: TIMESTAMP(timezone=True), nullable（上线时间）
- `end_at`: TIMESTAMP(timezone=True), nullable（下线时间）
- `created_at`: TIMESTAMP(timezone=True), server_default=func.now()
- `updated_at`: TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()

**索引要求**:
- `idx_featured_content_active_sort` ON `is_active, sort_order`
- `idx_featured_content_schedule` ON `start_at, end_at`

**代码示例**:

```python
class FeaturedContent(Base):
    """
    首页精选/焦点图内容配置表
    
    用于首页轮播Banner展示，支持运营配置和定时上下线
    """
    __tablename__ = "featured_content"
    
    # 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 业务字段
    title = Column(String(255), nullable=False, comment='焦点图标题')
    subtitle = Column(String(512), nullable=True, comment='焦点图副标题（可选）')
    image_url = Column(String(512), nullable=False, comment='焦点图图片URL')
    target_type = Column(String(50), nullable=True, comment='目标类型：room/session/topic/brand/external等')
    target_id = Column(UUID(as_uuid=True), nullable=True, comment='目标ID，根据target_type指向对应表的id（应用层关联，不设置外键）')
    target_url = Column(String(512), nullable=True, comment='外部链接，优先级高于target_id')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序权重，数字越小越靠前')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用：true=可见，false=已下线（软删除）')
    start_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='上线时间，为空表示立即上线')
    end_at = Column(TIMESTAMP(timezone=True), nullable=True, comment='下线时间，为空表示永久有效')
    
    # 时间戳 - 使用 server_default 和 func.now()
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 索引定义
    __table_args__ = (
        Index('idx_featured_content_active_sort', 'is_active', 'sort_order'),
        Index('idx_featured_content_schedule', 'start_at', 'end_at'),
    )
    
    def __repr__(self):
        return f"<FeaturedContent(id={self.id}, title={self.title})>"
```

**⚠️ 重要注意事项**:
1. **target_id字段不设置外键**：因为target_type可能指向不同的表（room/session/topic/brand/external等），无法在数据库层面设置外键约束，需要通过应用层验证保证引用完整性
2. **索引命名规范**：使用 `idx_` 前缀，下划线分隔，全小写
3. **时间戳字段**：使用 `server_default=func.now()` 和 `onupdate=func.now()`

#### **4.3. 代码风格要求**

1. **PEP 8规范**: 严格遵循Python代码风格
2. **4个空格缩进**: 不使用制表符
3. **导入顺序**: 标准库 → 第三方库 → 本地模块
4. **空行**: 类之间空2行，方法之间空1行
5. **命名规范**:
   - 类名: 大驼峰 (PascalCase): `FeaturedContent`
   - 表名: 下划线 (snake_case): `featured_content`
   - 字段名: 下划线 (snake_case): `target_id`, `sort_order`, `is_active`

#### **4.4. 安全编码规范**

1. **禁止硬编码敏感信息**: 
   - ❌ 禁止在代码中硬编码密码、密钥、API密钥等敏感信息
   - ✅ 如果必须设置默认值，应使用空字符串或安全的占位符

2. **__repr__方法安全**: 
   - `__repr__` 方法中**禁止暴露敏感信息**
   - **推荐格式**: 仅显示必要的标识信息（如id、标题等）
   - **示例**: `return f"<FeaturedContent(id={self.id}, title={self.title})>"`
   - ❌ **错误**: 如果字段包含敏感信息，不要在 `__repr__` 中暴露

3. **注释和文档安全**: 
   - 注释和文档字符串中**禁止包含真实的敏感信息示例**
   - 如需示例，使用占位符（如 `your_url_here`）

---

### **5. 完整性检查清单 (Completeness Checklist)**

生成代码后，请检查以下所有项：

**文件结构**:
- ✅ 模块文档字符串（文件顶部）
- ✅ 导入语句完整且正确
- ✅ Base类导入方式正确（`from app.database import Base`）

**模型类定义**:
- ✅ FeaturedContent模型类定义完整（所有字段、索引）
- ✅ 模型类有文档字符串
- ✅ 模型类有 `__repr__` 方法

**字段定义**:
- ✅ 所有字段类型正确（UUID, String, Integer, Boolean, TIMESTAMP）
- ✅ 所有字段约束正确（nullable, default等）
- ✅ 时间戳字段使用 `server_default=func.now()`
- ✅ UUID主键使用 `default=uuid.uuid4`
- ⚠️ **target_id字段不设置外键**（应用层关联）

**索引定义**:
- ✅ 所有索引都使用 `__table_args__` 显式命名
- ✅ 索引命名规范正确（`idx_` 前缀，下划线分隔）

**代码质量**:
- ✅ 代码遵循PEP 8规范
- ✅ 字段定义顺序合理（主键 → 业务字段 → 时间戳）
- ✅ 注释完整（关键字段有comment参数）
- ✅ 文档字符串使用中文

**安全规范**:
- ✅ 代码中无硬编码的敏感信息
- ✅ `__repr__` 方法不暴露敏感字段
- ✅ 注释和文档字符串中无真实的敏感信息示例

**增量开发规范**:
- ✅ 新文件创建在 `app/models/homepage_search.py`
- ✅ 需要在 `models/__init__.py` 中追加导入：`from .homepage_search import FeaturedContent`
- ✅ `__init__.py` 修改为最小幅度（仅追加导入，不修改现有内容）
- ✅ 新导入格式与现有导入格式完全一致
- ✅ 无重复导入
- ✅ 无命名冲突

---

### **6. 最终交付 (Final Deliverable)**

**生成的文件**:
- `backend/live_core_service/app/models/homepage_search.py` - 包含FeaturedContent模型类

**需要手动完成的步骤**:

1. **更新 `models/__init__.py`**：
   在文件末尾追加导入语句：

   ```python
   # 现有代码（不要修改任何内容，包括格式、顺序、空行、注释等）
   from .live_core import LiveRoom
   from .live_core import LiveSession
   from .live_core import SessionStatistics
   # ... 其他现有导入 ...
   from .brand import Brand, BrandTopic, BrandRoom
   
   # 新增导入（追加在文件末尾，保持与现有导入格式完全一致）
   from .homepage_search import FeaturedContent
   ```

   **⚠️ 最小改动要求**:
   - ✅ **只追加**：仅在文件末尾追加新导入，不修改任何现有内容
   - ✅ **格式一致**：新导入的格式（缩进、引号、换行）必须与现有导入完全一致
   - ✅ **检查重复**：追加前必须检查 `__init__.py` 中是否已存在相同导入，避免重复
   - ✅ **检查冲突**：追加前必须检查新导入的类名是否与现有类名冲突，如有冲突必须使用别名
   - ❌ **不重新排序**：严禁改变现有导入的顺序
   - ❌ **不修改格式**：严禁修改现有导入的格式（单行/多行、注释等）
   - ❌ **不修改空行**：严禁修改现有导入之间的空行

2. **创建数据库表**：
   运行数据库初始化脚本（推荐使用 `init_db.py`）：
   
   ```bash
   cd backend/live_core_service
   python app/init_db.py
   ```
   
   ✅ 新表会自动被识别和创建！

**验证步骤**:
1. 检查生成的代码语法正确（无linter错误）
2. 检查 `__init__.py` 导入语句正确
3. 运行 `python app/init_db.py` 创建表
4. 验证表结构是否正确（字段、索引）

---

**版本历史**:
- V1.0 (2026-01-18): 初始版本
