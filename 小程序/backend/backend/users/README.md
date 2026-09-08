# 用户功能服务 - SQLAlchemy 模型和 Pydantic Schema

## 📁 目录结构

```
users/
├── __init__.py                    # 顶级包初始化
├── README.md                      # 本文档
├── test_imports.py               # 导入测试脚本
└── app/
    ├── __init__.py               # 应用包初始化
    ├── models/
    │   ├── __init__.py           # 模型包初始化和导出
    │   └── users.py              # SQLAlchemy 模型定义
    └── schemas/
        ├── __init__.py           # Schema 包初始化和导出
        └── users.py              # Pydantic Schema 定义
```

## 🎯 生成内容概览

### SQLAlchemy 模型 (`app/models/users.py`)

**枚举类型:**
- `UserRole`: 用户角色 (REGULAR, MODERATOR, ADMIN, SUPERADMIN)
- `EntityStatus`: 实体状态 (NORMAL, BANNED, DELETED, PENDING_REVIEW, REJECTED)
- `MembershipProductStatus`: 会员产品状态 (DRAFT, PENDING, ACTIVE, INACTIVE, ARCHIVED)
- `MembershipStatus`: 会员订阅状态 (PENDING_PAYMENT, ACTIVE, PAST_DUE, EXPIRED, UPGRADED, REFUNDED)

**数据模型:**
- `User`: 用户核心表，包含用户基本信息、角色权限、社交登录等
- `MembershipProduct`: 会员产品目录表，定义可售卖的会员产品
- `UserMembership`: 用户会员订阅表，记录用户的会员购买和状态历史

**关键特性:**
- ✅ 完整的外键关系和级联删除配置
- ✅ PostgreSQL UUID 字段支持
- ✅ 自动时间戳更新
- ✅ 数据库约束和索引定义
- ✅ 枚举类型映射

### Pydantic Schema (`app/schemas/users.py`)

**为每个模型提供完整的 CRUD Schema:**

**用户相关:**
- `UserBase` / `UserCreate` / `UserUpdate` / `UserResponse`
- `UserWithMembershipsResponse` (包含会员订阅信息)

**会员产品相关:**
- `MembershipProductBase` / `MembershipProductCreate` / `MembershipProductUpdate` / `MembershipProductResponse`
- `MembershipProductWithMembershipsResponse` (包含订阅记录)

**用户会员订阅相关:**
- `UserMembershipBase` / `UserMembershipCreate` / `UserMembershipUpdate` / `UserMembershipResponse`
- `UserMembershipWithDetailsResponse` (包含用户和产品详情)

**分页和查询支持:**
- `PaginationParams`: 分页参数
- `UserFilterParams` / `MembershipFilterParams`: 查询过滤参数
- `PaginatedUsersResponse` / `PaginatedMembershipProductsResponse` / `PaginatedUserMembershipsResponse`: 分页响应

**关键特性:**
- ✅ 完整的数据验证和类型注解
- ✅ Pydantic v2 兼容 (`from_attributes=True`)
- ✅ UUID 和 datetime 类型正确映射
- ✅ 详细的字段描述和示例
- ✅ 灵活的查询和分页支持

## 🚀 使用方法

### 1. 导入模型

```python
# 导入 SQLAlchemy 模型
from app.models import User, MembershipProduct, UserMembership
from app.models import UserRole, EntityStatus, MembershipStatus

# 导入 Pydantic Schema
from app.schemas import (
    UserCreate, UserResponse, UserUpdate,
    MembershipProductCreate, MembershipProductResponse,
    UserMembershipCreate, UserMembershipResponse
)
```

### 2. 创建用户示例

```python
from app.schemas import UserCreate
from app.models import User

# API 层：接收创建用户请求
user_data = UserCreate(
    username="john_doe",
    nickname="John Doe", 
    email="john@example.com",
    password_hash="hashed_password",
    role="REGULAR"
)

# 数据库层：创建用户记录
new_user = User(
    username=user_data.username,
    nickname=user_data.nickname,
    email=user_data.email,
    password_hash=user_data.password_hash,
    role=user_data.role
)
```

### 3. 查询响应示例

```python
from app.schemas import UserResponse

# 从数据库查询用户
user = session.query(User).filter(User.id == 1).first()

# 转换为 API 响应格式
user_response = UserResponse.from_orm(user)  # Pydantic v1
# 或
user_response = UserResponse.model_validate(user)  # Pydantic v2
```

## 🏗️ 数据库设置

### 快速开始

1. **初始化数据库表**：
   ```bash
   cd users/
   python -m app.scripts.create_tables
   ```

2. **运行演示（可选）**：
   ```bash
   python demo_database_setup.py
   ```

详细设置指南请参考 [DATABASE_SETUP.md](DATABASE_SETUP.md)

## 🧪 测试

运行导入测试脚本验证代码生成是否成功：

```bash
cd users/
python test_imports.py
```

期望输出：
```
🚀 开始测试用户功能服务的模型和 Schema 导入...
============================================================
✅ SQLAlchemy 模型导入成功
   - 用户模型: User
   - 会员产品模型: MembershipProduct
   - 用户会员订阅模型: UserMembership
   - 用户角色枚举: UserRole

✅ Pydantic Schema 导入成功
   - 用户创建 Schema: UserCreate
   - 用户响应 Schema: UserResponse
   - 会员产品创建 Schema: MembershipProductCreate
   - 用户会员订阅响应 Schema: UserMembershipResponse

✅ 枚举值测试:
   - 用户角色: ['REGULAR', 'MODERATOR', 'ADMIN', 'SUPERADMIN']
   - 实体状态: ['NORMAL', 'BANNED', 'DELETED', 'PENDING_REVIEW', 'REJECTED']
   - 会员状态: ['PENDING_PAYMENT', 'ACTIVE', 'PAST_DUE', 'EXPIRED', 'UPGRADED', 'REFUNDED']

============================================================
📊 测试结果: 3/3 通过
🎉 所有导入测试通过！代码生成成功。
```

## 📝 注意事项

1. **数据库依赖**: 确保已安装 PostgreSQL 相关依赖 (`psycopg2` 或 `asyncpg`)
2. **Pydantic 版本**: 代码基于 Pydantic v2，如使用 v1 请调整配置语法
3. **异步支持**: SQLAlchemy 模型支持异步操作，配合 `AsyncSession` 使用
4. **枚举验证**: 所有枚举字段在 API 层会自动验证有效值

## 🔗 相关链接

- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)

---

> 此代码严格按照 `用户功能服务SQLAlchemym模型和Pyantic模型的代码生成提示词.md` 文档规范生成 