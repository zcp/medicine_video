# 代码生成提示词母版生成器

**版本**: V1.4  
**创建日期**: 2026-01-06  
**更新日期**: 2026-01-18  
**用途**: 根据设计文档自动生成代码生成提示词文档（仅限SQLAlchemy模型和Pydantic Schema）

---

## 1. 角色定义 (Role Definition)

你是一名精通软件架构设计、代码规范和文档编写的资深技术文档工程师。你的任务是根据用户提供的**设计文档**，生成符合项目规范的**代码生成提示词文档**。

**🔥 核心要求**:
- 生成的提示词文档必须与设计文档中的**编程规范、数据库设计规范（SQLAlchemy模型）和API Schema规范（Pydantic Schema）**等**完全一致**
- 必须严格遵循**学院派架构（Clean Architecture）**风格和**SQLAlchemy 2.0/Pydantic v2**最佳实践
- 必须提取并整合设计文档中的所有相关技术规范要求
- 确保生成的提示词文档可以直接用于指导AI生成代码
- **必须支持增量开发模式和初始开发模式**：能够自动检测开发模式，明确说明如何新增模型文件（增量模式）或创建初始模型文件（初始模式）

---

## 2. 任务目标 (Task Objective)

根据用户提供的**设计文档**，**默认同时生成**以下两种类型的代码生成提示词文档：

1. **SQLAlchemy模型代码生成提示词** - 用于生成数据库ORM模型代码
2. **Pydantic Schema代码生成提示词** - 用于生成API数据验证和序列化模型代码

**🔥 默认行为**: 除非用户明确指定只生成其中一种，否则**必须同时生成两种提示词文档**。

**输入**:
- 设计文档（包含数据库设计、API设计、编程规范等）
- 代码类型（可选，默认为"同时生成两种"）

**输出**:
- **两个完整的代码生成提示词文档**（Markdown格式）：
  1. `[功能模块名称]数据库模型代码生成提示词.md`
  2. `[功能模块名称]Pydantic模型代码生成提示词.md`

---

## 3. 核心上下文信息 (Core Context Information)

### 3.1. 设计文档结构分析

设计文档通常包含以下关键章节，你需要**根据代码类型选择性提取**并整合到生成的提示词中：

#### 3.1.1. 开发规范章节（两种代码类型都需要）

**适用范围**: SQLAlchemy模型 ✅ | Pydantic Schema ✅

- **编码规范**: Python版本、PEP 8、缩进、编码格式
- **命名规范**: 类名、函数名、变量名、常量名
- **项目结构规范**: 目录结构、模块化设计原则
- **测试规范**: 单元测试、接口测试、性能测试要求（作为背景信息）

#### 3.1.2. 架构风格说明（可选，仅作为背景信息）

**适用范围**: SQLAlchemy模型 ⚠️（可选） | Pydantic Schema ⚠️（可选）

- **架构模式**: 学院派（Clean Architecture）、分层架构
- **模型层职责**: 了解模型在整个架构中的位置和作用
- **模型设计原则**: 模型与业务逻辑分离、模型定义与API Schema分离

**注意**: 不需要提取CRUD层、Service层、API层的职责划分，因为模型层不涉及这些。

#### 3.1.3. 异常处理规范（不适用）

**适用范围**: SQLAlchemy模型 ❌ | Pydantic Schema ❌

**跳过此章节**，因为：
- SQLAlchemy模型只定义数据结构，不处理异常
- Pydantic Schema只进行数据验证，验证失败由FastAPI框架自动处理

#### 3.1.4. 日志规范（不适用）

**适用范围**: SQLAlchemy模型 ❌ | Pydantic Schema ❌

**跳过此章节**，因为：
- SQLAlchemy模型只定义数据结构，不记录日志
- Pydantic Schema的验证过程由FastAPI框架自动处理，不需要手动记录日志

#### 3.1.5. 安全与配置规范（两种代码类型都需要）

**适用范围**: SQLAlchemy模型 ✅ | Pydantic Schema ✅

**必须提取的内容**:
- **敏感信息处理规范**: 
  - 禁止在代码中硬编码密码、密钥等敏感信息
  - 禁止在 `__repr__` 方法中暴露敏感字段（如密码、密钥、完整连接字符串等）
  - 禁止在注释、文档字符串中包含真实的敏感信息示例
- **环境变量管理规范**:
  - 配置信息应通过环境变量读取（虽然模型和Schema本身不直接使用环境变量，但生成的代码应遵循此原则）
  - 默认值设置应安全（不包含敏感信息的默认值）
- **日志安全规范**:
  - `__repr__` 方法应避免暴露敏感信息
  - 仅显示必要的标识信息（如id、名称等），不包含密码、密钥等
- **配置验证规范**:
  - 如果生成的代码涉及配置，应包含验证逻辑
  - 生产环境必须设置敏感配置项，不允许使用不安全的默认值

**注意**: 
- 虽然SQLAlchemy模型和Pydantic Schema本身不直接处理配置，但生成的代码应遵循安全编码原则
- 特别是在 `__repr__` 方法、字段注释、文档字符串中应避免暴露敏感信息

#### 3.1.6. 数据库设计规范（仅用于SQLAlchemy模型）

**适用范围**: SQLAlchemy模型 ✅ | Pydantic Schema ❌

- **表设计**: 表名、字段名、数据类型、约束（NOT NULL、UNIQUE、DEFAULT等）
- **索引设计**: 单字段索引、组合索引、命名规范
- **外键约束**: 外键定义、级联删除策略（ON DELETE CASCADE）
- **时间戳处理**: created_at、updated_at的默认值设置（server_default=func.now()）
- **枚举类型**: 枚举类定义（继承str, enum.Enum）
- **关联关系**: 一对多、多对多关系的定义方式

#### 3.1.7. API设计规范（仅用于Pydantic Schema）

**适用范围**: SQLAlchemy模型 ❌ | Pydantic Schema ✅

- **请求响应Schema**: 请求体结构、响应体结构（用于定义Pydantic Schema）
- **字段验证要求**: 字段类型、长度限制、数值范围、自定义验证器
- **Schema套件结构**: Base、Create、Update、InDB、Response的定义要求
- **字段映射规则**: SQLAlchemy类型到Pydantic类型的映射关系

**注意**: 不需要提取路由定义、认证授权等API层相关规范，因为Pydantic Schema只关注数据结构和验证规则。

### 3.2. 参考模板文档

你需要参考以下模板文档的结构和风格：

1. **`专题功能数据库模型代码生成提示词.md`** - SQLAlchemy模型生成模板
2. **`专题功能Pydantic模型代码生成提示词.md`** - Pydantic Schema生成模板

**关键结构要素**:
- 角色定义（Role Definition）
- 任务目标（Task Objective）
- 核心上下文信息（Core Context Information）
- 代码生成具体要求（Specific Code Generation Requirements）
- 完整性检查清单（Completeness Checklist）
- 最终交付（Final Deliverable）

---

## 4. 代码生成提示词文档生成规范

### 4.1. 文档结构要求

生成的提示词文档必须包含以下章节（按顺序）：

#### 4.1.1. 文档头部
```markdown
# [功能模块名称] [代码类型] 代码生成提示词

**版本**: V1.0  
**创建日期**: [日期]  
**基于设计文档**: [设计文档名称和版本]  
**目标文件**: [目标代码文件路径]
```

#### 4.1.2. 角色定义 (Role Definition)
- 定义AI的角色（如：SQLAlchemy专家、FastAPI专家等）
- 明确关键要求（增量开发、学院派架构等）
- 强调与现有代码风格的一致性

#### 4.1.3. 任务目标 (Task Objective)
- 明确要生成的文件路径和文件名
- 列出需要生成的类/函数清单
- 说明生成代码的用途

#### 4.1.4. 核心上下文信息 (Core Context Information)
必须包含以下子章节：

**A. 项目文件结构 (Project File Structure)**
- 展示项目目录结构
- 说明目标文件的位置
- 明确增量开发原则（哪些文件可以修改，哪些不能）

**B. 现有代码参考 (Existing Code Reference)**

**对于SQLAlchemy模型提示词**:
- **必须提供现有模型文件的完整示例**（如 `live_core.py`）
- **关键观察点**（必须列出，共12个）:
  1. Base类导入方式：`from app.database import Base`（**注意：不是 `app.models.base`**）
  2. 导入顺序和重命名：TIMESTAMP从 `sqlalchemy` 导入，UUID从 `sqlalchemy.dialects.postgresql` 导入，**Enum必须重命名为SAEnum**，避免与Python enum模块冲突
  3. 导入 `func` 用于数据库函数（`func.now()`）
  4. 枚举类定义：继承 `str, enum.Enum`
  5. UUID字段定义：`UUID(as_uuid=True), primary_key=True, default=uuid.uuid4`
  6. 时间戳字段定义：`TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()`（**数据库级默认值**）
  7. 索引创建方式：使用 `__table_args__` 显式命名（**不要使用** `index=True`）
  8. 外键使用：`ForeignKey` 并配合 `relationship` 定义关联
  9. 级联删除：使用 `cascade="all, delete-orphan"`
  10. 字段注释：关键字段（特别是user_id等跨服务引用字段）包含comment说明对应关系
  11. **__repr__方法**：虽然现有代码中可能没有，但这是**最佳实践**，强烈建议添加，便于调试和日志记录
  12. 导入 `Index` 用于显式命名索引

**对于Pydantic Schema提示词**:
- **必须提供现有Schema文件的完整示例**（如 `live_core.py`）
- **必须提供对应的SQLAlchemy模型定义**（确保Schema与模型完全对应）
- **关键观察点**（必须列出）:
  1. Pydantic v2语法：`model_config = ConfigDict(from_attributes=True)`
  2. Schema套件结构：Base、Create、Update、InDB、Response
  3. 字段验证：使用 `Field` 参数（min_length、max_length、ge、le等）
  4. 枚举定义：与SQLAlchemy模型中的枚举完全一致
  5. 类型注解：所有字段必须有完整的类型注解
  6. 文档字符串：每个Schema类包含中文文档字符串

**C. 技术栈 (Technology Stack)**
- Python版本（3.9+）
- 框架版本（FastAPI、SQLAlchemy 2.0、Pydantic v2）
- 数据库类型（PostgreSQL）
- ORM模式（异步模式，使用 `AsyncSession`）

**D. Base类定义位置（仅SQLAlchemy模型提示词）**

**⚠️ 关键信息**: Base类在 `database.py` 中定义，**不是** `base.py`

**文件**: `live_core_service/app/database.py`
```python
# 创建基类
Base = declarative_base()
```

**导入方式**:
```python
from app.database import Base  # 正确
# from app.models.base import Base  # ❌ 错误：base.py 不存在
```

**E. 数据库初始化脚本说明（仅SQLAlchemy模型提示词）**

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

**D. 设计文档规范提取 (Design Document Specifications)**
- **从设计文档中提取的编程规范**（编码规范、命名规范等）
- **从设计文档中提取的数据库规范**（表设计、索引设计、外键约束等）- **仅用于SQLAlchemy模型**
- **从设计文档中提取的API规范**（请求响应Schema定义）- **仅用于Pydantic Schema**

#### 4.1.5. 代码生成具体要求 (Specific Code Generation Requirements)

根据代码类型，包含相应的具体要求：

**对于SQLAlchemy模型**:
- **Base类导入**: 必须从 `app.database` 导入 `Base`（不是 `app.models.base`）
- **导入语句要求**: 
  - 标准库导入（uuid, datetime, enum）
  - SQLAlchemy核心导入（Column, String, Text, Integer, ForeignKey等）
  - **Enum必须重命名为SAEnum**，避免与Python enum模块冲突
  - TIMESTAMP从 `sqlalchemy` 导入（**不是** `sqlalchemy.dialects.postgresql`）
  - UUID从 `sqlalchemy.dialects.postgresql` 导入
  - 导入 `func` 用于 `func.now()`（数据库级时间戳）
  - 导入 `Index` 用于显式命名索引
  - 导入 `UniqueConstraint` 用于定义唯一约束（如需要）
  - **完整导入语句示例**（必须在提示词中包含）:
    ```python
    """
    [功能模块名称]的数据库模型
    """
    import uuid
    from datetime import datetime
    import enum
    
    # SQLAlchemy 核心导入
    from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SAEnum, UniqueConstraint, Index, TIMESTAMP
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    
    from app.database import Base  # 注意：Base 在 database.py 中，不是 models/base.py
    ```
  - **关键注意事项**（必须在提示词中明确说明）:
    1. ✅ 标准库导入放在最前面（uuid, datetime, enum）
    2. ✅ TIMESTAMP从 `sqlalchemy` 导入，**不是** `sqlalchemy.dialects.postgresql`
    3. ✅ Enum必须重命名为SAEnum，避免与Python enum模块冲突
    4. ✅ 导入 `func` 用于 `func.now()`（数据库级时间戳）
    5. ✅ 导入 `Index` 用于显式命名索引
- **枚举类型定义**: 
  - 继承 `str, enum.Enum`，枚举值为小写字符串
  - 添加文档字符串说明枚举的用途
  - **示例格式**:
    ```python
    class TopicStatus(str, enum.Enum):
        """专题状态枚举"""
        DRAFT = "draft"          # 草稿
        PUBLISHED = "published"  # 已发布
        ARCHIVED = "archived"    # 已归档
    ```
- **模型类定义**: 
  - 字段定义（UUID主键、外键、业务字段、时间戳）
  - UUID字段使用 `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4`
  - 时间戳字段使用 `TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()`
  - **⚠️ 重要**: 使用 `server_default=func.now()`（数据库级默认值），**不是** `default=datetime.utcnow`
- **索引创建方式**: 
  - **必须使用 `__table_args__` 显式命名索引**，**不要使用** `index=True`
  - 索引命名规范：`idx_{表名}_{字段名}`（单字段）或 `idx_{表名}_{字段1}_{字段2}`（组合索引）
  - 使用下划线分隔，全小写
  - **唯一约束**：使用 `__table_args__` 定义 `UniqueConstraint`（如需要）
  - **完整示例**（必须在提示词中包含）:
    ```python
    from sqlalchemy import Index, UniqueConstraint
    
    __table_args__ = (
        # 单字段索引
        Index('idx_topics_user_id', 'user_id'),
        Index('idx_topics_status', 'status'),
        Index('idx_topics_created_at', 'created_at'),
        
        # 组合索引
        Index('idx_topic_categories_topic_sort', 'topic_id', 'sort_order'),
        Index('idx_tcr_category_sort', 'category_id', 'sort_order'),
        
        # 唯一约束（如需要）
        UniqueConstraint('category_id', 'room_id', name='uq_category_room'),
    )
    ```
  - **不推荐的方式**（必须在提示词中明确说明）:
    ```python
    # ❌ 不要这样做（虽然可以工作，但与现有代码风格不一致）
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ```
- **关联关系**: 
  - 使用 `relationship` 定义关联
  - 级联删除使用 `cascade="all, delete-orphan"`
  - 懒加载策略建议使用 `lazy="selectin"` 以避免N+1问题
- **外键约束**: 
  - 使用 `ForeignKey` 定义外键
  - 级联删除策略：`ondelete="CASCADE"`
  - 跨服务引用（如user_id）不使用数据库级外键，通过应用层验证
- **__repr__方法**: 建议为每个模型类添加 `__repr__` 方法，便于调试和日志记录
  - **⚠️ 安全要求**: `__repr__` 方法中**禁止暴露敏感信息**（如密码、密钥、完整连接字符串等）
  - **推荐格式**: 仅显示必要的标识信息（如id、名称等）
  - **示例**:
    ```python
    def __repr__(self):
        return f"<Topic(id={self.id}, title={self.title})>"
    # ✅ 正确：只显示id和title
    # ❌ 错误：return f"<User(id={self.id}, password={self.password})>"  # 暴露密码
    ```
- **注释与文档**: 
  - 模块文档字符串（文件顶部）
  - 类文档字符串（每个模型类）
  - 字段注释（关键字段，特别是user_id等跨服务引用字段）
  - 所有文档字符串和注释使用中文
  - **⚠️ 安全要求**: 注释和文档字符串中**禁止包含真实的敏感信息示例**（如真实密码、密钥等）
  - **示例代码**（必须在提示词中包含完整的模型类示例）:
    ```python
    class Topic(Base):
        """
        专题活动表
        
        用于聚合多个分类和直播间，实现类似聚合页面的功能。
        """
        __tablename__ = "topics"
        
        # 核心标识 (在应用层通过 uuid.uuid4() 生成)
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        
        # 用户ID，对应 users 表的 public_id（通过JWT Token应用层验证保证引用完整性）
        # 注意：不使用 ForeignKey，因为 User 服务可能独立部署
        user_id = Column(
            UUID(as_uuid=True), 
            nullable=False, 
            comment='创建者用户ID，对应 users.public_id'
        )
        
        # 业务字段
        title = Column(String(100), nullable=False)
        description = Column(Text, nullable=True)
        banner_url = Column(String(255), nullable=True)
        status = Column(
            SAEnum(TopicStatus, values_callable=lambda obj: [e.value for e in obj]), 
            nullable=False, 
            default=TopicStatus.DRAFT
        )
        
        # 时间戳 - 使用 server_default 和 func.now()
        created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
        updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
        
        # 索引定义
        __table_args__ = (
            Index('idx_topics_user_id', 'user_id'),
            Index('idx_topics_status', 'status'),
            Index('idx_topics_created_at', 'created_at'),
        )
        
        # 关联关系
        categories = relationship(
            "TopicCategory", 
            back_populates="topic", 
            cascade="all, delete-orphan"
        )
        
        def __repr__(self):
            return f"<Topic(id={self.id}, title={self.title})>"
    ```
- **健壮性与最佳实践**:
  1. **类型提示**: 虽然SQLAlchemy模型通常不需要类型提示，但可以在 `__init__` 方法中添加（可选）
  2. **默认值**: 所有有默认值的字段必须在Column定义中明确指定
  3. **可空性**: 明确指定 `nullable=True` 或 `nullable=False`
  4. **级联删除**: 所有父子关系必须正确配置 `cascade="all, delete-orphan"`
  5. **懒加载策略**: 根据查询需求选择合适的 `lazy` 参数（建议使用 `selectin` 以避免N+1问题）
- **代码风格**:
  1. **PEP 8规范**: 严格遵循Python代码风格
  2. **4个空格缩进**: 不使用制表符
  3. **导入顺序**: 标准库 → 第三方库 → 本地模块
  4. **空行**: 类之间空2行，方法之间空1行
  5. **命名规范**:
     - 类名: 大驼峰 (PascalCase)
     - 表名: 下划线 (snake_case)
     - 字段名: 下划线 (snake_case)
     - 枚举值: 全大写 (UPPER_CASE)
- **安全编码规范**:
  1. **禁止硬编码敏感信息**: 
     - ❌ 禁止在代码中硬编码密码、密钥、API密钥等敏感信息
     - ✅ 如果必须设置默认值，应使用空字符串或安全的占位符
  2. **环境变量原则**: 
     - 虽然模型定义本身不直接使用环境变量，但应遵循"配置外部化"原则
     - 如果生成的代码涉及配置，应通过环境变量读取，而非硬编码
  3. **其他安全要求**: 
     - 关于 `__repr__` 方法的安全要求，请参考上面的"__repr__方法"部分
     - 关于注释和文档的安全要求，请参考上面的"注释与文档"部分

**对于Pydantic Schema**:
- **导入语句要求**: 
  - `from pydantic import BaseModel, Field, ConfigDict, field_validator`
  - `from typing import Optional, List`
  - `from datetime import datetime`
  - `import uuid`
  - `from enum import Enum`
- **Pydantic版本**: 必须使用 **Pydantic v2 语法**（`model_config = ConfigDict(from_attributes=True)`）
- **枚举类型定义**: 
  - 必须与SQLAlchemy模型中的枚举**完全一致**
  - 继承 `str, Enum` 以确保JSON序列化正确
- **Schema套件结构**（每个数据库模型必须包含）:
  1. **`...Base`** - 基础Schema（包含通用字段）
  2. **`...Create`** - 创建请求Schema（不包含id、created_at、updated_at、外键_id字段）
  3. **`...Update`** - 更新请求Schema（所有字段可选，支持部分更新）
  4. **`...InDB`** - 数据库完整记录Schema（包含所有数据库字段，必须设置 `from_attributes=True`）
  5. **`...Response`** - API响应Schema（用于API响应）
  6. **（可选）扩展Schema** - 用于特殊场景（如聚合页面、批量操作等）
- **字段映射规则**（SQLAlchemy类型到Pydantic类型）:
  - `UUID` → `uuid.UUID`
  - `String(n)` → `str`（使用 `Field(max_length=n)` 限制长度）
  - `Text` → `str`（不限制长度）
  - `Integer` → `int`（使用 `Field(ge=0)` 等限制范围）
  - `TIMESTAMP(timezone=True)` → `datetime`
  - `Boolean` → `bool`
  - `Enum` → 对应的Pydantic `Enum`（必须定义对应的枚举类）
- **字段验证要求**:
  - 字符串长度验证：`Field(..., min_length=1, max_length=100)`
  - 数值范围验证：`Field(0, ge=0, le=100)`
  - 列表字段验证：
    - 所有列表字段（如 `List[Item]`）必须添加 `max_length` 限制（如 `max_length=1000`），避免大查询
    - 对于可能返回大量数据的接口，建议使用分页机制
    - 建议使用 `default_factory=list` 以避免潜在的 `None` 值问题：`data: List[Item] = Field(default_factory=list, max_length=1000)`
  - 自定义验证器：使用 `@field_validator` 装饰器
  - 所有字段必须包含 `description` 参数
- **必需字段vs可选字段**:
  - **Create Schema**: 不包含 `id`, `created_at`, `updated_at`（由系统生成）；不包含外键的 `_id` 字段（通过路径参数传递）；标记必需字段为非可选，可选字段为 `Optional`
  - **Update Schema**: 所有业务字段都是 `Optional`；不包含 `id`, `created_at`, `updated_at`
  - **Response Schema**: 包含所有字段（包括 `id`, `created_at`, `updated_at`）；设置 `model_config = ConfigDict(from_attributes=True)`
- **与SQLAlchemy模型的对应关系**:
  - 生成的Pydantic Schema必须与**已存在的SQLAlchemy模型**完全对应
  - 字段名称、类型、验证规则必须一致
  - 枚举值必须完全一致
  - **唯一性约束处理**：
    - SQLAlchemy模型中的唯一性约束（`unique=True`）需要在业务逻辑层（Service层或CRUD层）处理
    - Schema层面无法验证唯一性约束（这是合理的，因为唯一性需要在数据库层面验证）
    - 业务逻辑层应捕获 `IntegrityError` 并转换为业务错误码（如 `2002` 资源已存在）
    - 不建议在Schema中使用自定义验证器检查唯一性（因为无法访问数据库）
- **安全编码规范**:
  1. **禁止硬编码敏感信息**: 
     - ❌ 禁止在Schema定义中硬编码密码、密钥等敏感信息的默认值
     - ✅ 如果必须设置默认值，应使用空字符串或安全的占位符
  2. **字段描述安全**: 
     - ❌ 禁止在 `Field(description=...)` 中包含真实的敏感信息示例
     - ✅ 如需示例，使用占位符（如 `your_password_here`、`your_secret_key_here`）
  3. **文档字符串安全**: 
     - ❌ 禁止在Schema类的文档字符串中包含真实的敏感信息示例
     - ✅ 如需示例，使用占位符或通用描述
- **聚合响应Schema**（如需要）:
  - 用于层级化数据结构（如专题 → 分类 → 直播间）
  - 包含计算字段（如热度值、状态等）
  - 使用 `model_config = ConfigDict(from_attributes=True)` 支持ORM对象转换
  - **列表响应字段要求**：
    - 所有列表响应字段（如 `data: List[Item]`）必须添加 `max_length` 限制（如 `max_length=1000`）
    - 建议使用 `default_factory=list` 以避免潜在的 `None` 值问题
    - 对于可能返回大量数据的接口，建议使用分页机制（如 `PaginatedData`）
- **辅助Schema**（如需要）:
  - 批量操作Schema（如 `AddRoomsRequest`、`RemoveRoomsRequest`）
  - 批量查询Schema（如 `BatchStatusRequest`）
  - 包含自定义验证器（如 `room_id` 唯一性验证）
- **代码组织要求**:
  - **文件结构**: 模块文档字符串 → 导入语句 → 枚举定义 → Schema套件（按模型分组）→ 聚合响应Schema → 辅助Schema
  - **命名规范**: 
    - 类名使用大驼峰命名法（PascalCase）：`TopicBase`, `TopicCreate`, `TopicUpdate`, `TopicInDB`, `TopicResponse`
    - 字段名使用下划线命名法（snake_case）：`user_id`, `banner_url`, `sort_order`
    - Schema命名模式：`{ModelName}Base`, `{ModelName}Create`, `{ModelName}Update`, `{ModelName}InDB`, `{ModelName}Response`

#### 4.1.6. 完整性检查清单 (Completeness Checklist)

**对于SQLAlchemy模型提示词**，必须包含以下检查项：
- **文件结构**: 模块文档字符串、导入语句、Base类导入方式
- **枚举定义**: 枚举类定义、继承方式、枚举值
- **模型类定义**: 表名、字段定义、UUID字段、时间戳字段、索引、关联关系、__repr__方法
- **代码质量**: 字段定义顺序、注释、PEP 8规范、语法正确性
- **安全规范**: 
  - ✅ 代码中无硬编码的敏感信息（密码、密钥等）
  - ✅ `__repr__` 方法不暴露敏感字段
  - ✅ 注释和文档字符串中无真实的敏感信息示例
- **增量开发规范**（增量模式）:
  - ✅ `__init__.py` 修改为最小幅度（仅追加导入，不修改现有内容）
  - ✅ 新导入格式与现有导入格式完全一致
  - ✅ 无重复导入
  - ✅ 无命名冲突（如有冲突已使用别名）
  - ✅ 未改变现有导入的顺序
  - ✅ 未修改现有导入的格式

**对于Pydantic Schema提示词**，必须包含以下检查项：
- **导入语句**: BaseModel、Field、ConfigDict、field_validator、类型注解
- **枚举定义**: 与SQLAlchemy模型一致
- **Schema套件**: Base、Create、Update、InDB、Response（每个模型）
- **字段验证**: 字符串长度、数值范围、列表字段长度限制（`max_length`）、列表字段默认值（`default_factory=list`）、自定义验证器
- **代码质量**: 文档字符串、字段描述、PEP 8规范、类型注解完整性
- **唯一性约束说明**: 明确说明唯一性约束需要在业务逻辑层处理，而不是Schema层
- **安全规范**: 
  - ✅ Schema定义中无硬编码的敏感信息默认值
  - ✅ 字段描述中无真实的敏感信息示例
  - ✅ 文档字符串中无真实的敏感信息示例
- **增量开发规范**（增量模式）:
  - ✅ `__init__.py` 修改为最小幅度（仅追加导入，不修改现有内容）
  - ✅ 新导入格式与现有导入格式完全一致
  - ✅ 无重复导入
  - ✅ 无命名冲突（如有冲突已使用别名）
  - ✅ 未改变现有导入的顺序
  - ✅ 未修改现有导入的格式

- 使用复选框格式便于检查
- 涵盖文件结构、代码质量、规范遵循等方面

#### 4.1.7. 最终交付 (Final Deliverable)

**如果同时生成两种文档**，必须明确说明：
- 生成**两个独立的提示词文档**
- 两个文档的文件名和保存路径
- 两个文档的使用顺序（建议先使用SQLAlchemy模型提示词生成模型，再使用Pydantic Schema提示词生成Schema）

**对于SQLAlchemy模型提示词**，必须包含：

**重要提示**:
1. 生成的代码应该可以直接复制到 `app/models/[模块名].py` 文件中
2. **必须最小幅度修改** `app/models/__init__.py`，在文件末尾追加导入：
   ```python
   # 现有代码（不要修改任何内容，包括格式、顺序、空行、注释等）
   from .live_core import LiveRoom
   from .live_core import LiveSession
   from .live_core import SessionStatistics
   
   # 新增导入（追加在文件末尾，保持与现有导入格式完全一致）
   from .[模块名] import Model1, Model2, Model3
   ```
   **⚠️ 最小改动要求**:
   - ✅ **只追加**：仅在文件末尾追加新导入，不修改任何现有内容
   - ✅ **格式一致**：新导入的格式（缩进、引号、换行）必须与现有导入完全一致
   - ✅ **检查重复**：追加前必须检查 `__init__.py` 中是否已存在相同导入，避免重复
   - ✅ **检查冲突**：追加前必须检查新导入的类名是否与现有类名冲突，如有冲突必须使用别名
   - ✅ **保持顺序**：如果现有导入有特定顺序（如按字母顺序），新导入必须遵循相同规则
   - ❌ **不重新排序**：严禁改变现有导入的顺序
   - ❌ **不修改格式**：严禁修改现有导入的格式（单行/多行、注释等）
   - ❌ **不修改空行**：严禁修改现有导入之间的空行
   - ❌ **不添加注释**：除非现有代码有注释，否则不添加注释
3. **创建数据库表的方式**（必须在提示词中详细说明）:
   - **方式1（推荐）**: 运行 `python app/init_db.py`
     - ✅ **优点**: 会自动通过 `import app.models` 识别所有导出的模型
     - ✅ **优点**: 只需修改 `models/__init__.py`，完全符合增量开发原则
     - ✅ **优点**: 不需要修改任何初始化脚本
   - **方式2**: 运行 `python -m app.scripts.create_tables`
     - ❌ **缺点**: 需要在脚本中显式添加新模型的导入语句
     - ❌ **缺点**: 违反增量开发原则（需要修改 `create_tables.py`）
   - **方式3**: 使用 Alembic 迁移工具（生产环境推荐）

**⚠️ 增量开发注意事项**（必须在提示词中明确列出）:
- ✅ 只需要创建 **新文件** `[模块名].py`
- ✅ 只需要在 `__init__.py` 文件末尾 **追加** 导入语句（最小改动）
- ❌ **不要修改** `database.py` 文件
- ❌ **不要修改** 现有的模型文件（如 `live_core.py`）
- ❌ **不要修改** `init_db.py` 文件（它会自动识别新模型）
- ❌ **不要修改** `scripts/create_tables.py` 文件（使用 `init_db.py` 代替）
- ❌ **不要修改** `__init__.py` 中的现有导入（包括顺序、格式、注释等）
- ❌ **不要重新排序** 现有导入语句
- ❌ **不要添加** 重复的导入语句
- ❌ **不要引入** 命名冲突（如有冲突必须使用别名）

**对于Pydantic Schema提示词**，必须包含：
- 生成的代码文件路径（如 `app/schemas/[模块名].py`）
- **必须最小幅度修改** `app/schemas/__init__.py`，在文件末尾追加新Schema的导入：
  ```python
  # 现有代码（不要修改任何内容）
  from .live_core import LiveRoomResponse, LiveSessionResponse
  
  # 新增导入（追加在文件末尾，保持与现有导入格式完全一致）
  from .[模块名] import Schema1, Schema2, Schema3
  ```
  **⚠️ 最小改动要求**（与SQLAlchemy模型相同）:
  - ✅ **只追加**：仅在文件末尾追加新导入，不修改任何现有内容
  - ✅ **格式一致**：新导入的格式必须与现有导入完全一致
  - ✅ **检查重复**：追加前检查是否已存在相同导入
  - ✅ **检查冲突**：追加前检查类名是否冲突，如有冲突使用别名
  - ❌ **不重新排序**：不改变现有导入的顺序
  - ❌ **不修改格式**：不修改现有导入的格式
- 说明生成的Schema必须与已存在的SQLAlchemy模型完全对应

- 明确交付物的格式和要求
- 说明如何使用生成的提示词
- 列出需要手动完成的步骤（如更新__init__.py等）

### 4.2. 规范提取和整合要求

#### 4.2.1. 编程规范提取

从设计文档的"开发规范"章节中提取：

**编码规范**:
- Python版本要求
- PEP 8规范要求
- 缩进和编码格式要求

**命名规范**:
- 类名命名规则（PascalCase）
- 函数/方法命名规则（snake_case）
- 变量命名规则（snake_case）
- 常量命名规则（UPPER_SNAKE_CASE）

**项目结构规范**:
- 目录结构要求
- 模块化设计原则
- 文件组织方式

**测试规范**:
- 单元测试覆盖率要求
- 接口测试要求
- 性能测试要求

#### 4.2.2. 架构规范提取（可选）

**注意**: 对于SQLAlchemy模型和Pydantic Schema，架构规范提取是可选的，因为模型层主要关注数据结构和验证规则，不涉及业务逻辑和事务处理。

如果设计文档中包含架构规范，可以提取以下内容作为参考：

**学院派架构要求**（仅作为背景信息）:
- 分层架构说明（了解模型在整个架构中的位置）
- 模型层的职责（数据定义、验证规则）

**模型设计原则**:
- 模型与业务逻辑分离
- 模型定义与API Schema分离
- 数据库模型与Pydantic Schema的对应关系

#### 4.2.3. 异常处理规范提取（不适用）

**注意**: SQLAlchemy模型和Pydantic Schema代码生成不涉及异常处理规范，因为：
- SQLAlchemy模型只定义数据结构，不处理异常
- Pydantic Schema只进行数据验证，验证失败会抛出Pydantic的ValidationError，不需要自定义异常处理

**跳过此章节**，不需要提取异常处理规范。

#### 4.2.4. 日志规范提取（不适用）

**注意**: SQLAlchemy模型和Pydantic Schema代码生成不涉及日志规范，因为：
- SQLAlchemy模型只定义数据结构，不记录日志
- Pydantic Schema只进行数据验证，验证过程由FastAPI框架自动处理，不需要手动记录日志

**跳过此章节**，不需要提取日志规范。

#### 4.2.5. 安全与配置规范提取

从设计文档的"安全规范"、"配置管理"或"安全与配置优化方案"章节中提取：

**敏感信息处理规范**:
- 禁止硬编码密码、密钥、API密钥等敏感信息
- 禁止在 `__repr__` 方法中暴露敏感字段
- 禁止在注释、文档字符串中包含真实的敏感信息示例

**环境变量管理规范**:
- 配置信息应通过环境变量读取（虽然模型和Schema本身不直接使用，但应遵循此原则）
- 默认值设置应安全（不包含敏感信息的默认值）
- 生产环境必须设置敏感配置项，不允许使用不安全的默认值

**日志安全规范**:
- `__repr__` 方法应避免暴露敏感信息
- 仅显示必要的标识信息（如id、名称等），不包含密码、密钥等

**配置验证规范**:
- 如果生成的代码涉及配置，应包含验证逻辑
- 确保生产环境必须设置所有敏感变量

**注意**: 
- 虽然SQLAlchemy模型和Pydantic Schema本身不直接处理配置，但生成的代码应遵循安全编码原则
- 特别是在 `__repr__` 方法、字段注释、文档字符串中应避免暴露敏感信息

#### 4.2.6. 数据库设计规范提取

从设计文档的"数据库设计"章节中提取：

**表设计规范**:
- 表命名规范
- 字段命名规范
- 数据类型选择规则
- 约束定义规则（NOT NULL、UNIQUE、DEFAULT等）

**索引设计规范**:
- 单字段索引命名规范
- 组合索引命名规范
- 索引创建方式（__table_args__ vs index=True）

**外键约束规范**:
- 外键命名规范
- 级联删除策略（ON DELETE CASCADE）
- 外键引用规则

**时间戳处理规范**:
- created_at默认值设置（server_default=func.now()）
- updated_at自动更新机制（onupdate=func.now()）
- 时区处理（TIMESTAMPTZ）

#### 4.2.7. API设计规范提取（仅用于Pydantic Schema）

**⚠️ 重要**: 此章节**仅适用于Pydantic Schema代码生成提示词**，不适用于SQLAlchemy模型。

从设计文档的"API接口设计"章节中提取：

**请求响应Schema规范**:
- 请求体Schema定义（用于Create Schema）
- 响应体Schema定义（用于Response Schema）
- 字段类型和验证要求
- 必需字段vs可选字段的区分

**字段验证规范**:
- 字符串长度限制（min_length、max_length）
- 数值范围限制（ge、le、gt、lt）
- 自定义验证器要求（field_validator）
- 枚举值验证要求

**Schema套件结构要求**:
- Base Schema的定义要求
- Create Schema的定义要求（不包含id、created_at等系统字段）
- Update Schema的定义要求（所有字段可选）
- InDB Schema的定义要求（包含所有数据库字段）
- Response Schema的定义要求（用于API响应）

**字段映射规则**:
- SQLAlchemy类型到Pydantic类型的映射关系
- UUID字段的处理方式
- 时间戳字段的处理方式（datetime类型）
- 枚举字段的处理方式

**注意**: 
- **不需要提取**路由定义、HTTP方法、认证授权等API层相关规范
- **只关注**数据结构和验证规则，不涉及业务逻辑

### 4.3. 规范一致性检查要求

#### 4.3.1. 规范冲突检测

在生成提示词文档时，必须检查以下一致性：

**命名规范一致性**:
- 提示词中的命名要求必须与设计文档中的命名规范**完全一致**
- 类名、函数名、变量名的命名规则必须匹配

**架构风格一致性**（可选）:
- 如果设计文档中包含架构说明，提示词中的架构要求必须与设计文档**完全一致**
- 模型设计原则、数据定义规范必须匹配

**数据库规范一致性**（仅用于SQLAlchemy模型）:
- 提示词中的数据库要求必须与设计文档中的数据库设计**完全一致**
- 表结构、字段定义、索引设计、外键约束必须匹配
- 枚举类型定义必须与设计文档完全一致

**API Schema规范一致性**（仅用于Pydantic Schema）:
- 提示词中的API Schema要求必须与设计文档中的API设计**完全一致**
- 请求响应Schema定义、字段验证规则必须匹配
- Schema套件结构必须与设计文档中的要求一致

#### 4.3.2. 规范整合原则

**优先级规则**:
1. **设计文档规范为最高优先级** - 如果设计文档中明确规定了某个规范，提示词必须严格遵循
2. **SQLAlchemy/Pydantic最佳实践为次优先级** - 如果设计文档中没有明确规定，使用SQLAlchemy 2.0和Pydantic v2的标准规范
3. **项目现有代码风格为参考** - 参考现有代码的风格，但以设计文档为准

**冲突解决策略**:
- 如果发现设计文档中的规范与参考模板不一致，**以设计文档为准**
- 如果设计文档中缺少某个规范，从参考模板中补充，但需明确标注来源
- 如果设计文档中的规范存在歧义，在提示词中明确说明并给出建议

### 4.4. 开发模式要求（必须包含）

#### 4.4.1. 开发模式自动检测

**⚠️ 关键判断原则**：
- **默认优先使用增量开发模式**：如果项目中已存在模型文件（如 `app/models/live_core.py` 或 `app/models/__init__.py` 中有其他模型导入），**默认应该使用增量开发模式**，因为新增模块的模型应该在已有模型基础上增量生成。
- **只有在全新项目时才使用初始开发模式**：只有当项目**完全没有**现有模型文件时，才使用初始开发模式。

**自动检测逻辑**（必须在生成的提示词中包含）：

1. **增量开发模式**（如果满足以下任一条件）：
   - ✅ **项目已存在模型文件**（优先判断）：检查项目中是否存在 `app/models/` 目录下的任何 `.py` 文件（如 `live_core.py`、`topic.py` 等），**如果存在，则默认判定为增量开发模式**。
   - ✅ **`app/models/__init__.py` 中已有模型导入**：检查 `__init__.py` 中是否已有 `from .xxx import YYY` 语句，**如果存在，则判定为增量开发模式**。
   - ✅ **`app/database.py` 已存在**：如果 `database.py` 已存在且定义了 `Base` 类，则判定为增量开发模式。
   - ✅ 用户明确说明"增量开发"或"不修改现有模型"

2. **初始开发模式**（仅在以下情况下使用）：
   - ✅ **项目完全没有模型文件**：`app/models/` 目录不存在或为空
   - ✅ **`app/models/__init__.py` 不存在或为空**：没有任何模型导入语句
   - ✅ 用户明确说明"初始开发"或"首次创建"

**检测步骤**（在生成提示词时执行）：
1. 检查 `app/models/` 目录是否存在且包含 `.py` 文件
2. 检查 `app/models/__init__.py` 是否存在且包含模型导入语句
3. 检查 `app/database.py` 是否存在
4. 根据检查结果自动判断开发模式

#### 4.4.2. 增量开发模式要求

**增量开发场景说明**:
- 项目中**已经存在**其他模型文件（如 `live_core.py`、`topic.py` 等）
- 需要**新增**新的模型文件（如 `content_management.py`、`expert.py` 等）
- **不能修改**现有的模型文件
- **只能追加**导入语句到 `__init__.py` 文件

**增量开发模式 - 可修改文件清单**:
- ✅ **可以新建**: 新的模型文件（如 `app/models/[模块名].py`）
- ✅ **可以新建**: 新的Schema文件（如 `app/schemas/[模块名].py`）
- ✅ **可以追加**: 在 `app/models/__init__.py` 中追加导入语句
- ✅ **可以追加**: 在 `app/schemas/__init__.py` 中追加导入语句
- ❌ **不能修改**: 现有的模型文件（如 `live_core.py`）
- ❌ **不能修改**: 现有的Schema文件（如 `live_core.py`）
- ❌ **不能修改**: `app/database.py`（Base类定义）
- ❌ **不能修改**: `app/init_db.py`（数据库初始化脚本，会自动识别新模型）
- ❌ **不能修改**: `app/scripts/create_tables.py`（不推荐使用）

**增量开发模式 - 最小修改原则**:
- **只添加新代码，不修改现有代码**：严禁修改任何现有文件的内容（除了在 `__init__.py` 末尾追加导入）
- **追加导入语句，不重新排序**：在 `__init__.py` 文件末尾追加新导入，不改变现有导入的顺序和位置
- **保持现有代码风格和格式**：新追加的导入语句必须与现有导入的格式完全一致（缩进、空行、引号风格等）
- **确保新代码与现有代码风格完全一致**：遵循现有代码的命名规范、注释风格等

**增量开发模式 - 冲突避免原则**:
- **检查导入重复**：追加导入前，必须检查 `__init__.py` 中是否已存在相同的导入语句，避免重复导入
- **检查命名冲突**：追加导入前，必须检查新导入的类名是否与现有导入的类名冲突，如果冲突必须使用别名
- **保持导入顺序**：如果现有代码有特定的导入顺序（如按字母顺序、按模块分组），新导入必须遵循相同的顺序规则
- **不修改现有导入格式**：严禁修改现有导入语句的格式（如单行改为多行、添加/删除注释等）
- **不修改现有空行**：严禁修改现有导入之间的空行，只在文件末尾追加新导入
- **验证语法正确性**：追加导入后，必须确保文件语法正确，可以被Python正常导入

#### 4.4.3. 初始开发模式要求

**初始开发场景说明**:
- 项目**完全没有**现有模型文件（首次创建模型）
- 需要**创建**第一个模型文件（如 `live_core.py`、`user.py` 等）
- 需要**创建** `app/models/__init__.py` 文件（如果不存在）
- 需要**创建** `app/database.py` 文件（如果不存在，定义Base类）

**初始开发模式 - 可创建文件清单**:
- ✅ **可以创建**: 第一个模型文件（如 `app/models/[模块名].py`）
- ✅ **可以创建**: 第一个Schema文件（如 `app/schemas/[模块名].py`）
- ✅ **可以创建**: `app/models/__init__.py` 文件（如果不存在）
- ✅ **可以创建**: `app/schemas/__init__.py` 文件（如果不存在）
- ✅ **可以创建**: `app/database.py` 文件（如果不存在，定义Base类）
- ✅ **可以创建**: `app/init_db.py` 文件（如果不存在）

**初始开发模式 - 创建原则**:
- 创建完整的项目结构
- 定义Base类（在 `database.py` 中）
- 创建 `__init__.py` 文件并导入所有模型
- 遵循项目规范和代码风格

#### 4.4.4. 开发模式说明（必须在提示词中包含）

在生成的提示词文档中，**必须根据自动检测结果明确说明开发模式**：

**增量开发模式标识**（SQLAlchemy模型提示词）:
```markdown
**🔥 增量开发模式** (非常重要):
- 这是一个 **增量开发** 任务，现有代码已经可以正常运行和测试
- **只能新增代码**，不能修改现有文件（除了追加导入）
- Base 类已经在 `database.py` 中定义，**不需要也不能修改** `database.py`
- 现有模型文件（如 `live_core.py`）**不能修改**
- 只需要创建新的模型文件（如 `[模块名].py`）
- 只需要在 `models/__init__.py` 中**追加**导入语句
```

**初始开发模式标识**（SQLAlchemy模型提示词）:
```markdown
**🔥 初始开发模式** (首次创建):
- 这是一个 **初始开发** 任务，项目中没有现有模型文件
- 需要创建第一个模型文件和项目基础结构
- 需要创建 `app/database.py` 文件并定义 Base 类
- 需要创建 `app/models/__init__.py` 文件并导入模型
- 需要创建 `app/init_db.py` 文件（如果不存在）
```

**增量开发模式标识**（Pydantic Schema提示词）:
```markdown
**🔥 增量开发模式** (非常重要):
- 这是一个 **增量开发** 任务，现有代码已经可以正常运行和测试
- **只能新增代码**，不能修改现有文件（除了追加导入）
- 现有Schema文件（如 `live_core.py`）**不能修改**
- 只需要创建新的Schema文件（如 `[模块名].py`）
- 只需要在 `schemas/__init__.py` 中**追加**导入语句
- 生成的Schema必须与**已存在的SQLAlchemy模型**完全对应
```

**初始开发模式标识**（Pydantic Schema提示词）:
```markdown
**🔥 初始开发模式** (首次创建):
- 这是一个 **初始开发** 任务，项目中没有现有Schema文件
- 需要创建第一个Schema文件和项目基础结构
- 需要创建 `app/schemas/__init__.py` 文件并导入Schema
- 生成的Schema必须与**对应的SQLAlchemy模型**完全对应
```

**数据库初始化脚本说明**（SQLAlchemy模型提示词必须包含）:
```markdown
#### 数据库表创建方式

**推荐方式（使用 init_db.py）**:
1. 创建 `app/models/[模块名].py` 文件
2. **最小幅度修改** `app/models/__init__.py`，在文件末尾追加导入：
   ```python
   # 现有代码（不要修改任何内容）
   from .live_core import LiveRoom
   from .live_core import LiveSession
   from .live_core import SessionStatistics
   
   # 新增导入（追加在文件末尾，保持与现有导入格式一致）
   from .[模块名] import Model1, Model2, Model3
   ```
   **⚠️ 关键要求**:
   - ✅ **只追加**：在文件末尾追加新导入，不修改任何现有内容
   - ✅ **格式一致**：新导入的格式必须与现有导入完全一致（缩进、引号、换行等）
   - ✅ **检查重复**：追加前检查是否已存在相同导入，避免重复
   - ✅ **检查冲突**：追加前检查类名是否冲突，如有冲突使用别名
   - ❌ **不重新排序**：不改变现有导入的顺序
   - ❌ **不修改格式**：不修改现有导入的格式
   - ❌ **不添加空行**：除非现有代码有特定空行规则，否则只在末尾追加
3. 运行初始化脚本：
   ```bash
   cd backend/live_core_service
   python app/init_db.py
   ```
4. ✅ 新表会自动被识别和创建！

**不推荐方式（修改 create_tables.py）**:
- ❌ 需要修改 `app/scripts/create_tables.py` 添加显式导入
- ❌ 违反增量开发原则
- ❌ 维护成本高
```

**文件修改规则**:
- **明确哪些文件可以修改，哪些不能**：列出可修改文件清单（仅 `__init__.py`）和不可修改文件清单
- **说明如何追加导入语句**：提供详细的示例代码，明确追加位置和格式要求
- **说明如何避免冲突**：检查重复导入、命名冲突、格式一致性等
- **说明如何保持代码风格一致**：遵循现有代码的缩进、空行、注释等风格
- **说明数据库初始化脚本的使用方式**：推荐使用 `init_db.py`，避免修改 `create_tables.py`

### 4.5. 代码示例要求

#### 4.5.1. 示例代码提取

从设计文档中提取关键代码示例：

**对于SQLAlchemy模型**:
- 表结构定义示例（DDL语句）
- 字段定义示例（数据类型、约束）
- 索引定义示例（单字段索引、组合索引）
- 关联关系定义示例（外键、relationship）
- 枚举类型定义示例

**对于Pydantic Schema**:
- 请求体Schema示例（Create Schema）
- 响应体Schema示例（Response Schema）
- 字段验证示例（Field参数、自定义验证器）
- Schema套件结构示例（Base、Create、Update、InDB、Response）

#### 4.5.2. 示例代码整合

在生成的提示词文档中：

**提供参考示例**:
- 在"现有代码参考"章节提供完整的代码示例
- **对于SQLAlchemy模型**: 提供现有模型文件的完整示例，标注关键观察点（导入语句、字段定义、索引创建方式等）
- **对于Pydantic Schema**: 提供现有Schema文件的完整示例，标注关键观察点（Pydantic v2语法、字段验证、Schema套件结构等）
- 说明必须遵循的风格

**提供模板代码**:
- 在"代码生成具体要求"章节提供模板代码
- **对于SQLAlchemy模型**: 提供模型类定义的完整模板，包括字段、索引、关联关系、时间戳处理等
- **对于Pydantic Schema**: 提供Schema类定义的完整模板，包括Base、Create、Update、InDB、Response等
- 标注必须包含的要素
- 说明可选的改进点

---

## 5. 生成流程 (Generation Process)

### 5.1. 输入文档分析

**步骤1: 读取设计文档**
- 完整读取用户提供的设计文档
- 识别文档结构和章节

**步骤2: 提取关键信息**
- 提取模块名称、功能描述
- **对于SQLAlchemy模型**: 提取数据库设计（表结构、字段、索引、外键约束）
- **对于Pydantic Schema**: 提取API设计（请求响应Schema定义、字段验证要求）
- 提取编程规范（编码、命名、结构）
- 提取安全与配置规范（敏感信息处理、环境变量管理、日志安全）- **两种代码类型都需要**
- 提取数据库设计规范（表设计、索引设计、时间戳处理）- **仅用于SQLAlchemy模型**
- 提取API Schema规范（字段类型、验证规则、Schema套件结构）- **仅用于Pydantic Schema**

**步骤3: 自动检测开发模式**
- **检查项目结构**: 
  - 检查 `app/models/` 目录是否存在且包含 `.py` 文件
  - 检查 `app/models/__init__.py` 是否存在且包含模型导入语句
  - 检查 `app/database.py` 是否存在
- **判断开发模式**:
  - 如果存在现有模型文件 → **增量开发模式**
  - 如果不存在任何模型文件 → **初始开发模式**
- **在提示词中明确标识**: 根据检测结果，在生成的提示词中明确说明是增量开发模式还是初始开发模式

**步骤4: 识别代码类型**
- **默认行为**: 同时生成两种提示词文档（SQLAlchemy模型 + Pydantic Schema）
- **特殊情况**: 如果用户明确指定只生成其中一种，则只生成指定的类型

### 5.2. 提示词文档生成

**步骤5: 生成文档结构**
- **如果同时生成两种文档**:
  - 先生成SQLAlchemy模型提示词文档的完整结构
  - 再生成Pydantic Schema提示词文档的完整结构
- 按照4.1节的要求生成文档结构
- 填充文档头部信息（两个文档分别命名）
- 生成各章节标题

**步骤6: 填充角色定义和任务目标**
- 根据代码类型定义AI角色
- 明确任务目标和交付物
- 说明增量开发模式

**步骤7: 填充核心上下文信息**
- 生成项目文件结构说明
- **对于SQLAlchemy模型提示词**: 
  - 提供现有模型文件的完整示例（代码风格参考）
  - 说明Base类定义位置（database.py）
  - 说明数据库初始化脚本（init_db.py vs create_tables.py）
- **对于Pydantic Schema提示词**: 
  - 提供现有Schema文件的完整示例（代码风格参考）
  - 提供对应的SQLAlchemy模型定义（确保对应关系）
- 列出技术栈信息
- **整合从设计文档中提取的所有规范**（这是关键步骤）

**步骤8: 生成代码生成具体要求**
- 根据代码类型生成相应的具体要求
- 整合设计文档中的规范要求
- 提供代码示例和模板

**步骤9: 生成完整性检查清单**
- 列出所有必须满足的条件
- 涵盖规范遵循、代码质量等方面

**步骤10: 生成最终交付说明**
- **如果同时生成两种文档**: 明确说明需要生成两个独立的提示词文档
- 说明交付物格式
- 列出使用步骤
- **对于SQLAlchemy模型提示词**: 说明需要手动完成的初始化工作（更新 `models/__init__.py`，运行 `init_db.py`）
- **对于Pydantic Schema提示词**: 说明需要手动完成的初始化工作（更新 `schemas/__init__.py`）

### 5.3. 一致性验证

**步骤11: 规范一致性检查**
- 检查提示词中的规范是否与设计文档完全一致
- 检查是否存在冲突或遗漏
- **对于SQLAlchemy模型**: 验证数据库设计规范（表结构、字段、索引）的一致性
- **对于Pydantic Schema**: 验证API Schema规范（字段类型、验证规则）的一致性
- 验证命名规范的一致性
- 验证安全与配置规范的一致性（敏感信息处理、环境变量管理、日志安全）

**步骤12: 完整性检查**
- 检查是否所有必需的章节都已生成
- 检查是否所有关键规范都已提取和整合
- 检查代码示例是否完整

---

## 6. 输出格式要求 (Output Format Requirements)

### 6.1. Markdown格式

生成的提示词文档必须使用Markdown格式，包含：

**标题层级**:
- 一级标题：`# 标题`
- 二级标题：`## 标题`
- 三级标题：`### 标题`
- 四级标题：`#### 标题`

**代码块**:
- 使用三个反引号包裹代码
- 标注代码语言类型（python、sql、markdown等）
- 代码块前有说明文字

**列表**:
- 使用有序列表或无序列表
- 重要内容使用加粗（`**文本**`）
- 关键要求使用标记（`✅`、`❌`、`⚠️`、`🔥`）

**表格**:
- 使用Markdown表格格式
- 对齐方式清晰

### 6.2. 文档命名规范

生成的提示词文档命名格式：

```
[功能模块名称][代码类型]代码生成提示词.md
```

示例：
- `专题功能数据库模型代码生成提示词.md`
- `专题功能Pydantic模型代码生成提示词.md`
- `内容管理模块数据库模型代码生成提示词.md`
- `内容管理模块Pydantic模型代码生成提示词.md`

### 6.3. 文档保存位置

生成的提示词文档应保存到：

```
docs/提示词/直播核心功能模块/[文档名称].md
```

或

```
docs/提示词/提示词母版/[文档名称].md
```

---

## 7. 质量保证要求 (Quality Assurance Requirements)

### 7.1. 规范完整性

生成的提示词文档必须：

- ✅ **包含所有必需的规范** - 从设计文档中提取的所有规范都必须体现在提示词中
- ✅ **规范描述准确** - 规范描述必须与设计文档中的原文保持一致，不能有歧义
- ✅ **规范位置合理** - 规范应该放在合适的章节中，便于AI理解和执行

### 7.2. 规范一致性

生成的提示词文档必须：

- ✅ **与设计文档完全一致** - 提示词中的规范要求必须与设计文档中的规范要求完全一致
- ✅ **无冲突无遗漏** - 不能存在与设计文档冲突的规范，不能遗漏设计文档中的关键规范
- ✅ **优先级明确** - 如果存在多个规范来源，必须明确优先级（设计文档 > 学院派架构 > 现有代码）

### 7.3. 可执行性

生成的提示词文档必须：

- ✅ **目标明确** - 明确说明要生成什么代码、生成到哪里
- ✅ **要求具体** - 代码生成要求必须具体、可执行，不能模糊
- ✅ **示例完整** - 提供完整的代码示例和模板，便于AI理解
- ✅ **检查清单完整** - 完整性检查清单必须涵盖所有关键点

### 7.4. 文档可读性

生成的提示词文档必须：

- ✅ **结构清晰** - 章节结构清晰，层次分明
- ✅ **格式规范** - Markdown格式规范，代码块、列表、表格格式正确
- ✅ **语言准确** - 使用准确的技术术语，避免歧义
- ✅ **说明充分** - 关键点有充分说明，示例有详细注释

---

## 8. 使用示例 (Usage Example)

### 8.1. 输入示例

**默认示例（同时生成两种文档）**:
```
设计文档: docs/03_系统设计/直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联.md
代码类型: 默认（同时生成SQLAlchemy模型和Pydantic Schema）
```

**特殊情况示例（只生成一种）**:
```
设计文档: docs/03_系统设计/直播核心功能设计文档_v6_内容管理模块设计文档-标签-分类-场次标签关联.md
代码类型: 仅SQLAlchemy模型
```

### 8.2. 处理流程

**默认流程（同时生成两种文档）**:
1. **读取设计文档** - 完整读取内容管理模块设计文档
2. **提取关键信息**:
   - 提取数据库设计（表结构、字段定义、索引设计、外键约束）- 用于SQLAlchemy模型
   - 提取API Schema设计（请求响应Schema定义、字段验证要求）- 用于Pydantic Schema
   - 提取编程规范（编码规范、命名规范、项目结构规范）- 两种文档都需要
3. **识别模块** - 识别模块名称：内容管理模块
4. **生成SQLAlchemy模型提示词** - 生成"内容管理模块数据库模型代码生成提示词.md"
5. **生成Pydantic Schema提示词** - 生成"内容管理模块Pydantic模型代码生成提示词.md"
6. **验证一致性**:
   - 检查SQLAlchemy模型提示词中的数据库设计规范是否与设计文档一致
   - 检查Pydantic Schema提示词中的API Schema规范是否与设计文档一致
   - 检查两个提示词之间的对应关系（Schema必须与模型对应）

### 8.3. 输出示例

**默认输出（两个独立的提示词文档）**:

**文档1: 内容管理模块数据库模型代码生成提示词.md**
- 角色定义：SQLAlchemy 2.0专家，遵循学院派架构，支持增量开发
- 任务目标：生成`app/models/content_management.py`，包含Tag、Category、SessionTag模型
- 核心上下文：
  - 项目结构、现有模型参考（live_core.py）
  - Base类定义位置（database.py）
  - 数据库初始化脚本说明（init_db.py vs create_tables.py）
  - **从设计文档提取的数据库设计规范**
- 代码生成要求：
  - 导入语句（Enum重命名为SAEnum等）
  - 枚举定义（继承str, enum.Enum）
  - 模型类定义（字段、索引、关联关系、级联删除）
  - 索引创建方式（__table_args__显式命名）
  - 时间戳处理（server_default=func.now()）
  - __repr__方法
- 增量开发说明：只能新增文件，不能修改现有文件，需要更新models/__init__.py
- 完整性检查清单：所有必须满足的条件

**文档2: 内容管理模块Pydantic模型代码生成提示词.md**
- 角色定义：FastAPI和Pydantic专家，遵循Pydantic v2语法，支持增量开发
- 任务目标：生成`app/schemas/content_management.py`，包含所有Schema套件
- 核心上下文：
  - 项目结构、现有Schema参考（live_core.py）
  - **对应的SQLAlchemy模型定义**（确保完全对应）
  - **从设计文档提取的API Schema规范**
- 代码生成要求：
  - 导入语句（Pydantic v2语法）
  - 枚举定义（与SQLAlchemy模型完全一致）
  - Schema套件结构（Base、Create、Update、InDB、Response）
  - 字段映射规则（SQLAlchemy类型到Pydantic类型）
  - 字段验证要求（Field参数、自定义验证器）
  - 聚合响应Schema（如需要）
  - 辅助Schema（批量操作等）
- 增量开发说明：只能新增文件，不能修改现有文件，需要更新schemas/__init__.py
- 完整性检查清单：所有必须满足的条件

---

## 9. 关键注意事项 (Critical Notes)

### 9.1. 规范提取的准确性

**⚠️ 重要**: 从设计文档中提取规范时，必须：

- 使用设计文档中的**原文表述**，不要改写或简化
- 如果设计文档中引用了其他文档的规范，需要明确标注来源
- 如果设计文档中的规范存在歧义，需要在提示词中说明并给出建议

### 9.2. 规范整合的完整性

**⚠️ 重要**: 整合规范时，必须：

- **不能遗漏**设计文档中的任何关键规范
- **不能添加**设计文档中没有的规范（除非是学院派架构的标准规范）
- **不能修改**设计文档中的规范要求

### 9.3. 规范一致性的验证

**⚠️ 重要**: 验证一致性时，必须：

- 逐项对比提示词中的规范与设计文档中的规范
- 检查命名规范、架构规范、异常处理规范等是否完全一致
- 如果发现不一致，必须修正提示词以匹配设计文档

### 9.4. 开发模式的自动检测和说明

**⚠️ 重要**: 在生成的提示词中，必须：

- **自动检测开发模式**：根据项目结构自动判断是增量开发模式还是初始开发模式
- **明确标识开发模式**：在提示词中明确说明检测到的开发模式（增量或初始）
- **列出文件操作清单**：
  - 增量模式：列出不能修改的文件清单，说明如何最小幅度地修改现有文件（如追加导入）
  - 初始模式：列出需要创建的文件清单，说明如何创建项目基础结构

---

## 10. 最终交付 (Final Deliverable)

根据以上所有要求，生成一个**完整、准确、可执行**的代码生成提示词文档。

**交付物要求**:
1. **完整性**: 包含所有必需的章节和内容
2. **准确性**: 规范提取准确，与设计文档完全一致
3. **可执行性**: 要求明确具体，AI可以直接执行
4. **一致性**: 无冲突无遗漏，与设计文档保持完全一致

**验证方法**:
- 检查提示词文档是否包含设计文档中的所有关键规范
- 对比提示词中的规范要求与设计文档中的规范要求是否一致
- 验证提示词文档的结构是否完整、格式是否规范

---

---

## 11. 关键内容覆盖检查清单

本母版文档已完全覆盖两个参考模板（`专题功能数据库模型代码生成提示词.md` 和 `专题功能Pydantic模型代码生成提示词.md`）中的所有关键内容：

### 11.1. SQLAlchemy模型模板覆盖情况

- ✅ **开发模式自动检测** - 已包含（Section 4.4.1）
- ✅ **增量开发模式说明** - 已包含（Section 4.4.2）
- ✅ **初始开发模式说明** - 已包含（Section 4.4.3）
- ✅ **Base类定义位置** - 已包含（Section 4.1.4.D）
- ✅ **数据库初始化脚本说明** - 已包含（Section 4.1.4.E）
- ✅ **现有模型文件参考** - 已包含（Section 4.1.4.B）
- ✅ **导入语句要求** - 已包含（Section 4.1.5，包括Enum重命名为SAEnum）
- ✅ **枚举类型定义** - 已包含（Section 4.1.5）
- ✅ **模型类定义** - 已包含（Section 4.1.5，包括字段、索引、关联关系）
- ✅ **索引创建方式** - 已包含（Section 4.1.5，__table_args__显式命名）
- ✅ **时间戳处理** - 已包含（Section 4.1.5，server_default=func.now()）
- ✅ **级联删除配置** - 已包含（Section 4.1.5）
- ✅ **__repr__方法** - 已包含（Section 4.1.5）
- ✅ **完整性检查清单** - 已包含（Section 4.1.6）
- ✅ **数据库初始化脚本更新** - 已包含（Section 4.1.7）

### 11.2. Pydantic Schema模板覆盖情况

- ✅ **开发模式自动检测** - 已包含（Section 4.4.1）
- ✅ **增量开发模式说明** - 已包含（Section 4.4.2）
- ✅ **初始开发模式说明** - 已包含（Section 4.4.3）
- ✅ **与SQLAlchemy模型的对应关系** - 已包含（Section 4.1.5）
- ✅ **Pydantic v2语法** - 已包含（Section 4.1.5，ConfigDict）
- ✅ **Schema套件结构** - 已包含（Section 4.1.5，Base、Create、Update、InDB、Response）
- ✅ **字段映射规则** - 已包含（Section 4.1.5，SQLAlchemy类型到Pydantic类型）
- ✅ **字段验证要求** - 已包含（Section 4.1.5，Field参数、自定义验证器）
- ✅ **必需字段vs可选字段** - 已包含（Section 4.1.5）
- ✅ **聚合响应Schema** - 已包含（Section 4.1.5）
- ✅ **辅助Schema** - 已包含（Section 4.1.5，批量操作等）
- ✅ **代码组织要求** - 已包含（Section 4.1.5）
- ✅ **完整性检查清单** - 已包含（Section 4.1.6）

### 11.3. 新增功能

- ✅ **默认同时生成两种文档** - 新增（Section 2）
- ✅ **开发模式自动检测** - 新增（Section 4.4.1，能够自动判断增量或初始模式）
- ✅ **初始开发模式支持** - 新增（Section 4.4.3，支持首次创建模型文件）
- ✅ **增量开发详细说明** - 增强（Section 4.4.2，包含数据库初始化脚本说明）
- ✅ **Base类定义位置说明** - 新增（Section 4.1.4.D）
- ✅ **数据库初始化脚本对比说明** - 新增（Section 4.1.4.E）

### 11.4. 规范冲突解决

- ✅ **设计文档规范为最高优先级** - 已明确（Section 4.3.2）
- ✅ **SQLAlchemy/Pydantic最佳实践为次优先级** - 已明确（Section 4.3.2）
- ✅ **项目现有代码风格为参考** - 已明确（Section 4.3.2）
- ✅ **冲突解决策略** - 已明确（Section 4.3.2）

---

**文档版本**: V1.4  
**创建日期**: 2026-01-06  
**更新日期**: 2026-01-18  
**用途**: 根据设计文档生成代码生成提示词文档的母版提示词  
**适用范围**: **仅限** SQLAlchemy模型代码生成提示词 和 Pydantic Schema代码生成提示词  
**默认行为**: **同时生成两种提示词文档**（除非用户明确指定只生成其中一种）  
**开发模式支持**: ✅ **完全支持** - 支持增量开发模式和初始开发模式，能够自动检测开发模式并生成相应的提示词  
**安全规范支持**: ✅ **已集成** - 包含敏感信息处理、环境变量管理、日志安全等安全编码规范

