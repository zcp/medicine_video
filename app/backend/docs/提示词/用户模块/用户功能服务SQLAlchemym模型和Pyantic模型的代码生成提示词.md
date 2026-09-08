
-----

### **高效 AI 代码生成提示词 (针对 LiveCore Service)**

#### **1. 角色定义 (Role Definition)**

你是一名精通 FastAPI 和异步 SQLAlchemy 的资深 Python 后端工程师。你的任务是根据我提供的数据库设计规范，为 `users` 生成结构清晰、类型精确且符合最佳实践的 SQLAlchemy ORM 模型和 Pydantic Schema。

#### **2. 任务目标 (Task Objective)**

你的目标是生成以下两个 Python 文件的完整代码：

1.  `users/app/models/users.py`: 包含所有与数据库表对应的 SQLAlchemy 模型。
2.  `users/app/schemas/users.py`: 包含所有用于 API 数据交互的 Pydantic 模型。

#### **3. 核心上下文信息 (Core Context Information)**

**3.1. 技术栈 (Technology Stack)**

  * **框架**: FastAPI
  * **ORM**: SQLAlchemy (异步模式, 使用 `AsyncSession`)
  * **数据库**: PostgreSQL
  * **数据模型**: Pydantic
  * **Python 版本**: 3.8+

**3.2. 数据库 Schema (Database Schema - DDL)**
这是项目最终的数据库表结构定义，请严格根据它来创建 SQLAlchemy 模型：

```sql

### 3.2.1. 枚举类型 (ENUM Types)

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

### 3.2.2. 核心表结构 (DDL)

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

#### **4. 期望的项目文件结构 (新增部分)
请将生成的代码放入以下结构中：
```
users/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── users.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── users.py
│   └── ...
│
└── ...
```
-----

#### **5. 代码生成具体要求 (Specific Code Generation Requirements)**
**5.1 代码风格必须严格遵循 PEP 8 规范

**5.2.  Pydantic字段约束最佳实践

    **5.2.1. 支持的约束类型
  - **字符串**: `min_length`, `max_length`, `regex`
  - **数值**: `gt`, `ge`, `lt`, `le`
  - **通用**: `description`, `default`, `alias`

**5.2.2 禁用的约束类型（Pydantic v2不兼容）
- ❌ `max_digits` - 改用数据库层约束
- ❌ `decimal_places` - 改用数据库层约束  
- ❌ `multiple_of` - 可能不稳定，谨慎使用

**5.2.3  Decimal字段最佳实践
    ```python
    # ✅ 推荐写法
    price: Decimal = Field(..., gt=0, description="价格")
    
    # ❌ 避免写法  
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="价格")
    ```

 ** 5.2.4 约束分层原则
1. **数据库层**: 使用SQLAlchemy确保数据完整性 (`Numeric(10, 2)`)
2. **API层**: 使用Pydantic进行基础验证 (`gt=0`)
3. **业务层**: 复杂的业务规则验证在Service层处理


**5.3. SQLAlchemy 模型 (`users/app/models/users.py`)**

* 必须使用 SQLAlchemy 的声明式基类 (`declarative_base`)。
* 对于 **`BIGSERIAL`** 类型的主键（如 `users.id`），模型定义应为 `id = Column(BigInteger, primary_key=True)`。这会告知 SQLAlchemy 该值由数据库在插入时自动生成。
* 对于所有 **`UUID`** 类型的字段（如 `users.public_id`），必须使用 `from sqlalchemy.dialects.postgresql import UUID`，并在 `Column` 中定义为 `UUID(as_uuid=True)`。对于需要在应用层默认生成的 `uuid` 字段，应添加 `default=uuid.uuid4`。请确保导入 `uuid` 库。
* 对于所有 PostgreSQL 的 **`ENUM`** 类型字段（如 `users.role`），必须首先在代码中定义 Python 的 `enum.Enum`，然后使用 `sqlalchemy.dialects.postgresql.ENUM` 将其关联到模型字段。
* 必须精确定义所有表之间的 `relationship()`，并使用 `back_populates` 来建立双向关系。
* 外键的 `ondelete` 行为必须与 DDL 中的定义（如 `ON DELETE CASCADE`）保持一致。
* 为每个模型类添加注释，说明它对应哪个数据库表。

**5.4. Pydantic 模型 (`users/app/schemas/users.py`)**

  * 为每个 SQLAlchemy 模型创建一组对应的 Pydantic Schema，至少包含：
      * **`...Base`**: 包含通用的、可被继承的字段。
      * **`...Create`**: 用于 API 创建资源时接收的请求体。
      * **`...Update`**: 用于 API 更新资源时接收的请求体，所有字段应为可选（`Optional`）。
      * **`...Response`**: 用于 API 返回给客户端的响应数据。
  * 所有用于从数据库对象转换的 Schema，必须配置 `from_attributes=True` (对于 Pydantic v2) 或 `orm_mode = True` (对于 Pydantic v1)。
  * 所有 `UUID` 字段的类型应为 `uuid.UUID`，所有 `TIMESTAMPTZ` 字段的类型应为 `datetime.datetime`。

#### **6. 最终交付 (Final Deliverable)**

请根据以上所有要求，为我生成以下两个文件的完整 Python 代码。请将每个文件的代码放在独立的、有明确标记的代码块中。

1.  **`users/app/models/users.py`**
2.  **`users/app/schemas/users.py`**

-----
