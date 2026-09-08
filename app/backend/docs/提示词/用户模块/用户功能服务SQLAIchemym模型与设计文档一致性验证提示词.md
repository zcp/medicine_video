
-----

### **高效 AI 代码审计提示词 (针对 `users.py` 的一致性审查)**

#### **1. 角色定义 (Role Definition)**

你是一名资深的 Python 后端技术审计员和 SQLAlchemy 专家。你的核心任务是进行代码审查，
以确保下文中提供的 SQLAlchemy ORM 模型代码**百分之百**地、**严格地**遵循了给定的数据库设计规范 (DDL)。
你必须以挑剔和精确的态度找出任何细微的偏差。

#### **2. 任务目标 (Task Objective)**

你的目标是：

1.  **比较**下面提供的【数据库设计规范 (DDL)】和【待审查的 SQLAlchemy 模型代码】。
2.  **验证**代码是否完全实现了 DDL 中定义的所有表、字段、类型、约束和关系。
3.  **生成**一份详细的审查报告，明确指出所有一致、不一致或缺失的实现，并提供修正建议。

#### **3. 核心输入 (Core Inputs)**

**3.1. 权威的数据库设计规范 (Authoritative Database Schema - DDL)**
这是唯一的设计标准，所有代码实现都必须与此对齐。

```sql
-- 用户角色
CREATE TYPE user_role AS ENUM (
    'REGULAR', 
    'MODERATOR', 
    'ADMIN', 
    'SUPERADMIN'
);

-- 通用实体状态 (用于用户账户、内容等)
CREATE TYPE entity_status AS ENUM (
    'NORMAL', 
    'BANNED', 
    'DELETED', 
    'PENDING_REVIEW', 
    'REJECTED'
);

-- 会员产品状态
CREATE TYPE membership_product_status AS ENUM (
    'DRAFT', 
    'PENDING', 
    'ACTIVE', 
    'INACTIVE', 
    'ARCHIVED'
);

-- 用户会员订阅状态
CREATE TYPE membership_status AS ENUM (
    'PENDING_PAYMENT', 
    'ACTIVE', 
    'PAST_DUE', 
    'EXPIRED', 
    'UPGRADED', 
    'REFUNDED'
);
```

### 4.2. 核心表结构 (DDL)

```sql
-- 公用函数：用于自动更新 updated_at 时间戳
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- users 表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255),
    nickname VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(512),
    bio TEXT,
    role user_role NOT NULL DEFAULT 'REGULAR',
    status entity_status NOT NULL DEFAULT 'NORMAL',
    is_email_verified BOOLEAN NOT NULL DEFAULT false,
    is_phone_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ NULL,
    last_login_ip INET,
    social_provider VARCHAR(20),
    social_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_login_method_check
        CHECK (password_hash IS NOT NULL OR (social_provider IS NOT NULL AND social_id IS NOT NULL))
);
CREATE UNIQUE INDEX idx_users_social_login ON users (social_provider, social_id);
COMMENT ON TABLE users IS '用户核心表';
COMMENT ON COLUMN users.id IS '【内部ID】主键，仅用于数据库内部关联';
COMMENT ON COLUMN users.public_id IS '【公开ID】对外暴露的唯一标识符，用于API等';
COMMENT ON COLUMN users.role IS '用户角色: REGULAR, MODERATOR, ADMIN, SUPERADMIN';
COMMENT ON COLUMN users.status IS '用户状态: NORMAL, BANNED, DELETED, PENDING_REVIEW, REJECTED';
CREATE TRIGGER set_timestamp_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- membership_products 表
CREATE TABLE membership_products (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INT NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL,
    level SMALLINT NOT NULL DEFAULT 1,
    duration_unit VARCHAR(10) NOT NULL,
    duration_value INT NOT NULL,
    status membership_product_status NOT NULL DEFAULT 'DRAFT',
    payment_gateway_price_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
               
COMMENT ON TABLE membership_products IS '可供售卖的会员产品目录表';
COMMENT ON COLUMN membership_products.code IS '产品唯一编码 (e.g., VIDEO_YEARLY), 也是外键';

        
CREATE TRIGGER set_timestamp_membership_products BEFORE UPDATE ON membership_products FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- user_memberships 表
CREATE TABLE user_memberships (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    transaction_id VARCHAR(255) UNIQUE,
    product_code VARCHAR(50) NOT NULL,
    level SMALLINT NOT NULL DEFAULT 1,
    status membership_status NOT NULL DEFAULT 'PENDING_PAYMENT',
    is_auto_renew BOOLEAN NOT NULL DEFAULT false,
    admin_notes TEXT,
    start_date TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_memberships_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_memberships_product_code FOREIGN KEY (product_code) REFERENCES membership_products(code) ON DELETE RESTRICT
);
CREATE INDEX idx_user_memberships_user_id ON user_memberships(user_id);
CREATE INDEX idx_user_memberships_expires_at ON user_memberships(expires_at);
CREATE UNIQUE INDEX idx_user_memberships_one_active_per_product ON user_memberships (user_id, product_code) WHERE (status IN ('ACTIVE', 'PAST_DUE'));
COMMENT ON TABLE user_memberships IS '用户会员状态与历史表';
COMMENT ON COLUMN user_memberships.level IS '购买时产品的等级快照，用于历史数据不变性';
COMMENT ON COLUMN user_memberships.admin_notes IS '管理员手动操作备注，用于审计';
COMMENT ON COLUMN user_memberships.public_id IS '【公开ID】对外暴露的唯一标识符，用于API等';
        
CREATE TRIGGER set_timestamp_user_memberships BEFORE UPDATE ON user_memberships FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
```

**3.2. 待审查的 SQLAlchemy 模型代码 (`users.py`)**
* **已存在的代码**:
    * `@app/models/users.py` 
    * `@app/schemas/users.py` 

#### **4. 审查清单与验证规则 (Audit Checklist & Validation Rules)**

请根据以下清单逐项进行严格审查：

1.  **表与模型映射 (Table-to-Model Mapping):**
    * `users`, `membership_products`, `user_memberships` 三个表是否都已正确映射为 SQLAlchemy 模型类 `User`, `MembershipProduct`, `UserMembership`？
    * 每个模型类的 `__tablename__` 是否与 DDL 表名完全对应？

2.  **字段与列的完全对应 (Field-to-Column Correspondence):**
    * 每个模型中的字段是否与 DDL 中对应表的列一一对应，不多不少？
    * 字段命名是否遵循 PEP 8 的 `snake_case` 风格？

3.  **数据类型精确性 (Data Type Accuracy):**
    * **`BIGSERIAL` / `BigInteger`**: `users.id` 和 `user_memberships.id` 是否正确映射为 `BigInteger`？
    * **`UUID`**: `users.public_id` 和 `user_memberships.public_id` 是否使用了 `from sqlalchemy.dialects.postgresql import UUID` 并定义为 `Column(UUID(as_uuid=True), ...)`？
    * **`VARCHAR(n)`**: 是否映射为 `String(n)`？ (例如 `String(50)`, `String(255)`)
    * **`TEXT`**: `users.bio`, `membership_products.description`, `user_memberships.admin_notes` 是否映射为 `Text`？
    * **`BOOLEAN`**: `users.is_email_verified` 和 `user_memberships.is_auto_renew` 等字段是否映射为 `Boolean`？
    * **`TIMESTAMPTZ`**: 所有 `created_at`, `updated_at`, `last_login_at`, `start_date`, `expires_at` 字段是否都正确映射为带时区信息的 `DateTime(timezone=True)`？
    * **`INET`**: `users.last_login_ip` 是否使用了 `from sqlalchemy.dialects.postgresql import INET` 并定义为 `Column(INET)`?
    * **`DECIMAL(10, 2)`**: `membership_products.price` 是否映射为 `Numeric(10, 2)`？
    * **`SMALLINT`**: `membership_products.level` 和 `user_memberships.level` 是否映射为 `SmallInteger`？
    * **自定义 `ENUM` 类型**:
        * 是否为 `user_role`, `entity_status`, `membership_product_status`, `membership_status` 分别创建了对应的 Python `enum.Enum` 类？
        * 模型中的 `role`, `status` 字段是否使用了 `from sqlalchemy.dialects.postgresql import ENUM` 并正确关联了 Python 枚举类，例如 `Column(ENUM(UserRole, name="user_role"), ...)`？

4.  **主键 (Primary Keys):**
    * `users.id`, `user_memberships.id` 和 `membership_products.code` 字段是否都被正确定义为 `primary_key=True`？

5.  **外键与级联规则 (Foreign Keys & Cascade Rules):**
    * `user_memberships.user_id`: `ForeignKey` 是否正确指向 `users.id`？`ondelete` 是否设置为 `'CASCADE'`？
    * `user_memberships.product_code`: `ForeignKey` 是否正确指向 `membership_products.code`？`ondelete` 是否设置为 `'RESTRICT'`？

6.  **关系完整性 (Relationship Integrity):**
    * 所有外键是否都定义了对应的 `relationship()`？
    * 是否使用了 `back_populates` 来确保所有关系都是双向的？
        * `User` (memberships) \<-\> `UserMembership` (user)
        * `MembershipProduct` (user_memberships) \<-\> `UserMembership` (product)
    * `User.memberships` 的 `cascade` 规则是否设置为 `'all, delete-orphan'` 以匹配 `ondelete="CASCADE"` 的行为？

7.  **约束、索引和默认值 (Constraints, Indexes, and Defaults):**
    * **`NOT NULL`**: 是否正确转换为 `nullable=False`？
    * **`UNIQUE`**: `users.public_id`, `users.username`, `users.email` 等字段是否设置了 `unique=True`？
    * **`DEFAULT ...`**:
        * DDL 中的 `DEFAULT 'REGULAR'` / `DEFAULT 'NORMAL'` 等枚举默认值，是否在模型中也通过 `default=...` 正确设置了对应的 Python 枚举成员？
        * `DEFAULT NOW()` 是否使用了 `server_default=func.now()`？
    * **`CHECK` 约束**: `users` 模型中是否通过 `__table_args__` 定义了与DDL完全一致的 `CheckConstraint`？
    * **独立索引**: `users` 和 `user_memberships` 模型中是否通过 `__table_args__` 定义了与DDL完全一致的 `Index`？
    * **部分唯一索引**: `user_memberships` 中是否正确定义了 `Index`，包含 `unique=True` 和 `postgresql_where` 条件 `(status.in_(['ACTIVE', 'PAST_DUE']))`？

---

#### **5. 最终交付 (Final Deliverable)**

请生成一份 Markdown 格式的审查报告。报告应包含以下部分：

1.  **总体结论 (Overall Conclusion):**

      * 一句话总结代码与设计规范的符合程度（例如：“完全一致”、“基本一致，但存在小问题”、“存在严重偏差”）。

2.  **详细分析报告 (Detailed Analysis Report):**

      * 使用表格形式，逐项列出【第 4 部分】中的所有审查规则。
      * 表格应包含三列：`审查项`、`审查结果 (通过/失败)`、`备注与修改建议`。
      * 如果审查结果为“失败”，必须在备注中清晰地解释问题所在，并**提供修正后的正确代码片段**。

**示例报告格式:**

| 审查项 | 审查结果 | 备注与修改建议 |
| :--- | :--- | :--- |
| **表与模型映射** | 通过 | `live_rooms`, `live_sessions`, `session_statistics` 均已正确映射。 |
| **数据类型: `TIMESTAMPTZ`** | \<span style="color:red;"\>失败\</span\> | `live_rooms.created_at` 被错误地定义为 `DateTime`，缺少时区信息。应使用 `TIMESTAMP(timezone=True)`。\<br\>**修正建议:**\<br\>`python<br>created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())<br>` |
| **...** | ... | ... |  