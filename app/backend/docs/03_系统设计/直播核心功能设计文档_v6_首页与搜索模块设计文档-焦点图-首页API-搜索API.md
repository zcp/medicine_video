# 首页与搜索模块设计文档 - 焦点图-首页API-搜索API

**版本**: V1.0  
**日期**: 2026-01-06  
**状态**: ✅ 已完成，可直接开发  
**基于**: 《直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md》

---

## 📌 核心定位说明

### 1. 本文档的定位

本文档是《直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md》的拆分子模块，专注于**首页与搜索模块**的完整设计，包括：

**包含模块**:
- **Featured Content（首页精选/焦点图）**: 首页轮播Banner管理
- **Homepage API（首页专用API）**: 首页直播间列表展示（含实时状态、主讲专家、热度计算）
- **Search API（全局搜索API）**: 跨资源的全局搜索功能

**模块范围**:
- 1张数据表（featured_content）
- 7个API接口（Featured Content 4个、Homepage API 1个、Search API 2个）
- 完整的Pydantic Schemas定义
- 完整的数据库DDL及索引设计
- 详细的执行流程说明（8-15步，含复杂联表查询）

### 2. 本文档的核心特点

- ✅ **内容完整性**: 包含原始文档中首页与搜索模块的所有设计内容
- ✅ **独立可开发**: 可作为独立的开发文档，开发团队可直接基于本文档进行开发
- ✅ **与v6主文档保持一致**: 遵循v6主文档的所有设计规范和约定
- ✅ **增量设计**: 本文档是对v6主文档的增量扩展，不修改v6主文档的现有设计
- ✅ **支持前端V1.3**: 完全支持移动端前端设计v3的所有需求

### 3. 本文档的独立性说明

**本文档可独立开发的原因**:
1. **完整的表定义**: 包含 `featured_content` 表的完整DDL和索引设计
2. **完整的API接口**: 包含所有API的详细设计和执行流程
3. **明确的依赖关系**: 明确列出对v6主文档和其他模块的依赖

**与其他模块的关联**:
- `live_rooms` 表（v6主文档）：首页API需要查询直播间信息
- `live_sessions` 表（v6主文档）：首页API需要查询场次信息和状态
- `experts` 表（专家模块）：首页API需要展示主讲专家信息
- `categories` 表（内容管理模块）：首页API支持按分类筛选
- `tags` 表（内容管理模块）：搜索API可能涉及标签搜索
- `brands` 表（品牌模块）：搜索API支持品牌搜索

### 4. 业务价值说明

**首页精选/焦点图（Featured Content）**:
- 提供首页轮播Banner展示功能
- 支持运营配置和定时上下线
- 提升首页视觉吸引力和内容推广效果
- 灵活的目标链接配置（内部资源或外部链接）

**首页专用API（Homepage API）**:
- 提供首页直播间列表的聚合展示
- 实时展示直播状态（直播中/预告/回放）
- 智能选择主讲人（专家优先）
- 热度计算和排序功能
- 优化用户首页浏览体验

**全局搜索API（Search API）**:
- 提供跨资源的全局搜索功能
- 支持搜索直播间、专家、专题、品牌等
- 提供匹配分数和高亮显示
- 提升内容可发现性
- 增强用户体验

---

## 📚 依赖文档清单

本文档依赖以下文档，开发时需参考：

1. **《直播核心功能设计文档_v6_深度融合最终版.md》**
   - 主要依赖：`live_rooms` 表、`live_sessions` 表定义
   - 依赖理由：首页API和搜索API需要查询这些核心表
   - **注意**：`users` 表在 `user_service` 中，不在 `live_core_service` 数据库中，首页API仅使用 `live_rooms.user_id`（即 `users.public_id`），不进行跨数据库查询

2. **《直播核心功能设计文档_v6_增加权限设计版.md》**
   - 主要依赖：权限系统设计
   - 依赖理由：Admin API需要遵循权限验证规范

3. **《用户模块设计文档authing版+权限设计版.md》**
   - 主要依赖：User模型定义、JWT认证规范
   - 依赖理由：所有API需要遵循统一的认证规范

4. **《配置与安全优化方案-实施指南.md》**
   - 主要依赖：日志脱敏规范、配置验证规范
   - 依赖理由：所有业务模块需遵循安全配置规范

5. **《移动端前端设计v3.md》**
   - 主要依赖：前端V1.3对首页和搜索的需求
   - 依赖理由：API接口需完全支持前端需求

6. **《专家模块设计文档-专家信息-专家关注.md》**
   - 主要依赖：`experts` 表定义
   - 依赖理由：首页API需要展示主讲专家信息

7. **《内容管理模块设计文档-标签-分类-场次标签关联.md》**
   - 主要依赖：`categories` 表、`tags` 表定义
   - 依赖理由：首页API支持按分类筛选，搜索API可能涉及标签搜索

8. **《品牌模块设计文档-品牌管理-品牌专题关联.md》**
   - 主要依赖：`brands` 表定义
   - 依赖理由：搜索API支持品牌搜索

9. **《直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md》**
   - 主要依赖：整体设计原则和规范
   - 依赖理由：本文档是其拆分子模块，需保持一致性

---

## 🔄 增量开发说明

### 1. 本文档与v6主文档的关系

- **不修改v6主文档**: 本文档不对v6主文档中的 `live_rooms`、`live_sessions` 表进行任何修改
- **增量扩展**: 仅新增1张表（featured_content）和相关API
- **有机整合**: 通过外键和应用层关联实现与v6主文档的无缝集成
- **跨服务依赖说明**: `users` 表在 `user_service` 中，首页API仅使用 `live_rooms.user_id`（即 `users.public_id`），不进行跨数据库查询

### 2. 本文档的增量原则

- ✅ **新增为主**: 主要新增表和API，不修改现有表结构
- ✅ **最小侵入**: 对v6主文档的依赖仅限于查询和关联
- ✅ **向后兼容**: 不影响v6主文档的现有功能
- ✅ **完整性优先**: 确保新增功能的完整性和可用性

### 3. 字段扩展说明

本模块**不涉及**对v6主文档现有表的字段扩展。所有设计均为新增表和API。

---

## 📋 文档规范说明

### 1. 统一响应结构

所有API接口返回统一的响应结构：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-01-06T10:00:00Z"
}
```

### 2. 统一分页格式

所有分页接口返回格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "size": 10,
    "items": [...]
  },
  "timestamp": "2026-01-06T10:00:00Z"
}
```

### 3. 统一认证规范

- **Public Auth（公开访问）**: 无需JWT Token，任何人都可以访问
- **Optional Auth（可选认证）**: 允许匿名访问，但已登录用户可享受个性化功能
- **Admin Auth（管理员认证）**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

### 4. JWT Token格式说明

**重要：统一使用 `user_id` 字段**

本系统统一使用 `user_id` 作为JWT payload中的用户标识字段，而非JWT标准的 `sub` 字段。

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "REGULAR",
  "email": "user@example.com",
  "exp": 1698765432
}
```

### 5. 业务状态码

常用业务状态码（详见Section 6 错误码对照表）：
- `200`: 成功
- `2001`: 资源不存在
- `2002`: 资源已存在（唯一约束冲突）
- `3002`: 权限不足
- `4001`: 参数校验失败
- `4002`: 参数值无效
- `5001`: 服务器内部错误

### 6. 权限设计规范

首页与搜索模块的权限设计遵循《直播核心功能设计文档_v6_增加权限设计版(非独立版).md》中的统一权限架构。

#### 6.1 架构分层原则

权限管理的职责分层如下：

- **API 层 (Controller/Dependency)**：仅负责 **Authentication (认证)** —— 解析"你是谁"（User 还是 Anonymous）。
  - 使用 `Depends(get_current_user_optional)` 进行可选认证（读操作）
  - 使用 `Depends(get_current_user)` 进行严格认证（写操作）
  - 从JWT Token中提取 `user_id` 和 `role` 字段，传递给Service层

- **Service 层 (Domain Logic)**：全权负责 **Authorization (鉴权)** —— 判定"你能看吗/你能改吗"。
  - 实现权限守卫函数（`_check_admin_permission`等）
  - 根据用户角色和资源状态进行权限判断
  - 抛出相应的异常（`PermissionDeniedException`、`NotFoundException`等）

- **CRUD 层 (Repository/Data Access)**：负责在 **SQL 层面应用权限过滤逻辑**。
  - 根据用户身份在SQL查询中添加权限过滤条件
  - 禁止内存过滤，业务筛选条件与权限过滤条件使用 AND 关系组合
  - **注意**：首页与搜索模块的大部分资源都是公开的，不需要权限过滤

#### 6.2 双轨鉴权模式

首页与搜索模块采用双轨鉴权模式，支持匿名访问和已登录用户访问：

- **Strict Auth (强制鉴权)**：
  - 适用场景：所有写操作（创建、更新、删除焦点图）
  - 行为：无Token或Token无效时返回 `401 Unauthorized`
  - 对应依赖：`Depends(get_current_user)`

- **Optional Auth (可选鉴权)**：
  - 适用场景：公开资源的读操作（获取焦点图列表、首页API、搜索API）
  - 行为：无Token时视为匿名用户，Token无效时返回 `401 Unauthorized`
  - 对应依赖：`Depends(get_current_user_optional)`
  - 注意：首页API和搜索API是公开资源，匿名用户和已登录用户都可以访问

#### 6.3 权限守卫函数

Service层应实现以下权限守卫函数：

##### 管理员权限检查

```python
def _check_admin_permission(
    self,
    user_role: Optional[str]
) -> None:
    """
    管理员权限检查（用于系统级资源管理）
    
    Args:
        user_role: 当前用户的角色（从JWT Token提取）
        
    Raises:
        PermissionDeniedException: 非管理员用户（403）
    """
    if user_role not in ['ADMIN', 'SUPERADMIN']:
        raise PermissionDeniedException("权限不足，需要管理员权限")
```

**适用场景**：
- 创建/更新/删除焦点图（系统级资源）
- 获取焦点图列表（Admin分页接口）

**注意**：首页与搜索模块的资源都是公开的，不需要404伪装机制。所有写操作都需要管理员权限。

#### 6.4 CRUD层权限过滤

**首页与搜索模块的特殊性**：

首页与搜索模块的大部分资源都是公开的，不需要CRUD层权限过滤。所有用户（包括匿名用户）都可以访问首页API和搜索API。

**焦点图查询权限过滤**：

焦点图查询需要根据 `is_active` 字段和定时上下线时间进行过滤：

```python
async def get_featured_content(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    current_user_id: Optional[UUID] = None,
    role: Optional[str] = None
) -> Tuple[List[FeaturedContent], int]:
    """
    获取焦点图列表（带权限过滤）
    
    Args:
        db: 数据库会话
        page: 页码
        size: 每页大小
        current_user_id: 当前用户的ID（可选）
        role: 当前用户的角色（可选）
        
    Returns:
        (焦点图列表, 总数)
    """
    query = select(FeaturedContent)
    conditions = []
    
    # 权限过滤：普通用户只能看到启用的焦点图
    if role not in ['ADMIN', 'SUPERADMIN']:
        conditions.append(FeaturedContent.is_active == True)
        # 定时上下线过滤
        now = datetime.now(timezone.utc)
        conditions.append(
            or_(
                FeaturedContent.start_at.is_(None),
                FeaturedContent.start_at <= now
            )
        )
        conditions.append(
            or_(
                FeaturedContent.end_at.is_(None),
                FeaturedContent.end_at >= now
            )
        )
    
    # 组合所有条件
    if conditions:
        query = query.where(and_(*conditions))
    
    # 排序和分页
    query = query.order_by(FeaturedContent.sort_order)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    return list(result.scalars().all()), total
```

**关键原则**：
- 普通用户只能看到启用的焦点图，且必须在有效期内
- 管理员可以看到所有焦点图（包括禁用的）
- 所有过滤条件在SQL层面完成，不使用内存过滤

#### 6.5 用户身份提取规范

**重要：统一使用 `user_id` 字段**

在所有API实现中，必须从JWT Token的 `user_id` 字段提取用户身份，而非JWT标准的 `sub` 字段：

```python
# API层：提取用户身份（可选认证）
current_user: Optional[Dict] = Depends(get_current_user_optional)
user_id = UUID(current_user.get("user_id") or current_user.get("sub")) if current_user else None
user_role = current_user.get("role", "REGULAR").upper() if current_user else None

# 传递给Service层
result = await service.get_homepage_rooms(page, size, user_id, user_role)
```

**JWT Token格式**：
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "REGULAR",
  "email": "user@example.com",
  "exp": 1698765432
}
```

**注意**：
- 如果JWT Token中没有 `user_id` 字段，可以回退到 `sub` 字段（兼容性处理）
- 角色字段统一使用大写（`REGULAR`、`ADMIN`、`SUPERADMIN`）
- 匿名用户时，`user_id` 和 `role` 均为 `None`

---

## 🎯 设计要点与约定

### 1. 数据库设计规范

#### 1.1 UUID主键生成规范
- **在应用层生成**: 所有UUID主键必须在应用层通过 `uuid.uuid4()` 生成
- **不使用数据库DEFAULT**: 不使用PostgreSQL的 `gen_random_uuid()` 函数

#### 1.2 时间戳字段规范
- 统一使用 `TIMESTAMPTZ`（带时区的时间戳）
- `created_at`: 创建时间，`DEFAULT CURRENT_TIMESTAMP`
- `updated_at`: 更新时间，通过触发器自动更新
- `start_at`/`end_at`: 定时上下线时间，可为NULL表示立即生效/永久有效

#### 1.3 索引命名规范
- 格式：`idx_<表名>_<字段名>`
- 示例：`idx_featured_content_active_sort`

### 2. API设计规范

#### 2.1 HTTP方法规范
- `GET`: 查询数据（幂等）
- `POST`: 创建资源
- `PATCH`: 部分更新资源（使用PATCH而非PUT）
- `DELETE`: 删除资源

#### 2.2 URL路径规范
- 公开接口：`/api/v1/<资源名>`
- Admin接口：`/api/v1/admin/<资源名>`

#### 2.3 查询参数规范
- 分页：`page`（页码）、`size`（每页数量）
- 搜索：`q`（查询关键词）
- 筛选：`<字段名>`（如：`category_id`、`type`）
- 排序：`sort`（排序规则，如：`heat:desc`、`created_at:desc`）

### 3. 软删除策略

#### 3.1 焦点图表（featured_content）
- 使用 `is_active` 字段实现软删除
- `is_active=false` 表示已删除/禁用
- 保留数据用于历史记录和审计

### 4. 安全与配置规范

本节内容基于《直播核心功能设计文档----配置与安全优化方案.md》，定义API设计中的安全要求。

#### 4.1 环境变量与配置管理

##### 环境变量管理原则

- **禁止硬编码敏感信息**：所有敏感配置（数据库密码、JWT密钥等）必须通过环境变量配置
- **使用 `.env.example` 模板**：提供环境变量模板文件，明确所有必需和可选的配置项
- **配置验证机制**：应用启动时必须验证所有关键配置项，缺失或不安全时拒绝启动
- **生产环境强制要求**：生产环境必须设置所有敏感变量，不允许使用默认值

##### 必需环境变量清单

首页与搜索模块依赖以下环境变量：

**数据库配置**：
- `POSTGRES_SERVER`: 数据库服务器地址（默认：`localhost`）
- `POSTGRES_PORT`: 数据库端口（默认：`5432`）
- `POSTGRES_DB`: 数据库名称（默认：`live_core_test`）
- `POSTGRES_USER`: 数据库用户名（默认：`postgres`）
- `POSTGRES_PASSWORD`: 数据库密码（**生产环境必须设置，不允许默认值**）

**JWT配置**：
- `JWT_SECRET_KEY`: JWT签名密钥（**生产环境必须设置，长度至少32字符**）
- `JWT_ALGORITHM`: JWT算法（默认：`HS256`）

**CORS配置**：
- `CORS_ORIGINS`: 允许的跨域来源（格式：`http://localhost:5175,https://example.com`，默认：`*`）
- **生产环境必须设置为具体域名，禁止使用 `*`**

##### 配置验证规范

应用启动时必须执行以下验证：

```python
# app/core/config.py
class Settings:
    def __init__(self):
        """初始化配置并验证"""
        self._validate_database_config()
        self._validate_jwt_config()
        self._validate_cors_config()
    
    def _validate_database_config(self):
        """验证数据库配置"""
        if not self.POSTGRES_PASSWORD:
            raise ValueError(
                "POSTGRES_PASSWORD 环境变量未设置。"
                "生产环境必须设置此变量。"
            )
    
    def _validate_jwt_config(self):
        """验证JWT配置"""
        if not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY 环境变量未设置。"
                "生产环境必须设置此变量，且长度应至少32个字符。"
            )
        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY 长度不足32个字符，存在安全风险。"
            )
    
    def _validate_cors_config(self):
        """验证CORS配置"""
        if self.DEBUG is False and "*" in self.BACKEND_CORS_ORIGINS:
            import warnings
            warnings.warn(
                "生产环境（DEBUG=False）检测到CORS配置为 '*'，存在安全风险。"
                "请通过 CORS_ORIGINS 环境变量设置具体的允许域名。"
            )
```

##### 环境变量文件管理

- **`.env.example` 模板文件**：提供所有环境变量的模板和说明
- **`.gitignore` 配置**：确保 `.env` 文件不被提交到版本控制系统
- **文件权限控制**：生产环境 `.env` 文件权限设置为 `600`（仅所有者可读写）

#### 4.2 敏感信息防护

##### 禁止硬编码敏感信息

**禁止在代码中硬编码**：
- 数据库密码
- JWT密钥
- API密钥
- 其他敏感配置

**正确做法**：
```python
# ❌ 错误：硬编码密码
POSTGRES_PASSWORD = "CHANGE_ME"

# ✅ 正确：从环境变量读取
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
```

##### 密钥管理服务（生产环境推荐）

生产环境推荐使用密钥管理服务：
- **AWS**: AWS Secrets Manager / Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Secret Manager
- **HashiCorp**: Vault

##### 数据库连接URL日志脱敏

**禁止在日志中打印完整的数据库连接URL**（包含密码）：

```python
# ❌ 错误：日志泄露密码
logger.info(f"尝试连接数据库: {DATABASE_URL}")

# ✅ 正确：仅打印非敏感信息
logger.info(
    f"尝试连接数据库: "
    f"server={settings.POSTGRES_SERVER}, "
    f"port={settings.POSTGRES_PORT}, "
    f"database={settings.POSTGRES_DB}, "
    f"user={settings.POSTGRES_USER}"
    # 不打印密码
)
```

#### 4.3 日志脱敏规范

##### 日志脱敏实现载体要求

所有日志输出必须经过脱敏处理，禁止直接输出敏感信息：

**需要脱敏的信息**：
- 数据库连接URL（包含密码）
- JWT Token完整内容
- 用户密码（即使已加密）
- API密钥
- 搜索关键词（如果涉及敏感信息）
- 其他敏感配置信息

**日志脱敏工具函数**：

```python
# app/core/logging_utils.py
import re
import logging

def sanitize_log_message(message: str) -> str:
    """对日志消息进行脱敏处理"""
    # 移除数据库连接URL中的密码
    message = re.sub(
        r'postgresql[+a-z]*://[^:]+:([^@]+)@',
        r'postgresql://***:***@',
        message,
        flags=re.IGNORECASE
    )
    
    # 移除JWT密钥（如果意外出现在日志中）
    message = re.sub(
        r'JWT_SECRET_KEY["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'JWT_SECRET_KEY="***"',
        message,
        flags=re.IGNORECASE
    )
    
    # 移除JWT Token完整字符串（仅保留前8个字符）
    message = re.sub(
        r'Bearer\s+([A-Za-z0-9_-]{8})([A-Za-z0-9_-]+)',
        r'Bearer \1...',
        message
    )
    
    return message

class SanitizedFormatter(logging.Formatter):
    """脱敏日志格式化器"""
    def format(self, record):
        record.msg = sanitize_log_message(str(record.msg))
        return super().format(record)
```

##### 日志级别使用规范

- **INFO级别**：记录正常业务操作（不包含敏感信息）
- **WARNING级别**：记录权限拒绝和业务异常（不包含敏感信息）
- **ERROR级别**：记录系统异常（不包含敏感信息，仅记录错误类型和位置）
- **DEBUG级别**：记录搜索关键词和执行时间（不包含敏感信息）

**示例**：
```python
# ✅ 正确：不包含敏感信息
logger.info(f"用户 {user_id} 执行了搜索，关键词长度: {len(query)}")
logger.warning(f"用户 {user_id} 尝试访问无权限的资源 {resource_id}")
logger.error(f"数据库操作失败: {type(e).__name__}")
logger.debug(f"搜索执行时间: {execution_time}ms")

# ❌ 错误：包含敏感信息
logger.info(f"数据库连接: {DATABASE_URL}")  # 包含密码
logger.debug(f"搜索关键词: {query}")  # 可能包含敏感信息
logger.error(f"异常详情: {str(e)}")  # 可能包含敏感信息
```

#### 4.4 错误消息脱敏

##### 异常处理中的脱敏

在异常处理中，不要向用户暴露敏感信息：

```python
# ✅ 正确：不暴露敏感信息
try:
    # 数据库操作
    result = await db.execute(query)
except Exception as e:
    logger.error(f"数据库操作失败: {type(e).__name__}")
    # 不打印完整的异常信息（可能包含连接字符串）
    raise HTTPException(
        status_code=500,
        detail="内部服务器错误"
    )

# ❌ 错误：暴露敏感信息
try:
    result = await db.execute(query)
except Exception as e:
    logger.error(f"数据库操作失败: {str(e)}")  # 可能包含连接字符串
    raise HTTPException(status_code=500, detail=str(e))  # 暴露给用户
```

##### 错误消息规范

- **用户可见错误**：仅返回通用的错误消息，不暴露系统内部细节
- **日志记录**：在日志中记录详细的错误信息（已脱敏），用于调试
- **错误码使用**：使用统一的错误码（如 `3002` 权限不足），而非详细的错误描述

### 5. 首页与搜索模块特殊设计说明

#### 5.1 焦点图设计

**目标链接类型**:
- `target_type`: 目标资源类型（room/session/topic/brand/external等）
- `target_id`: 目标资源ID（UUID）
- `target_url`: 外部链接（优先级高于target_id）

**定时上下线**:
- `start_at`: 上线时间，为NULL表示立即上线
- `end_at`: 下线时间，为NULL表示永久有效
- 查询时需检查当前时间是否在有效期内

#### 5.2 首页API设计

**Host选择逻辑**（展示 live_session 关联的 expert 信息）:
1. 场次的主讲专家（通过 `live_session_experts` 表，`session_id = live_sessions.id AND role = '主讲'`）
   - 如果有多个主讲专家，选择 `sort_order` 最小的（或第一个）
2. 如果场次没有主讲专家，显示其他角色的专家（`role = '主持'` 或 `role = '嘉宾'`）
   - 按角色优先级：主讲 > 主持 > 嘉宾
   - 同一角色内按 `sort_order` 排序
3. 如果场次没有关联任何专家，`host` 为 `null`

**注意**：
- `host` 仅展示与 `live_session` 关联的 `expert` 信息
- 不展示房主信息（`live_room.user_id`）
- 目前一个 `live_room` 只包含一个 `live_session`，所以每个房间对应一个场次

**直播状态判断**:
- `live`: 场次状态为 `live`
- `scheduled`: 场次状态为 `scheduled`
- `replay`: 场次状态为 `ready` 或 `ended`

**热度计算**（示例公式）:
```
heat = current_viewer_count * 10 + peak_viewer_count * 5 + play_count
```

#### 5.3 搜索API设计

**搜索范围**:
- `room`: 搜索 `live_rooms` 表的 `title` 和 `summary` 字段
- `expert`: 搜索 `experts` 表的 `name`, `bio`, `expertise_areas` 字段
- `topic`: 搜索 `topics` 表的 `title` 和 `description` 字段
- `brand`: 搜索 `brands` 表的 `name` 和 `description` 字段

**匹配分数计算**:
- 标题完全匹配：1.0
- 标题包含关键词：0.8-0.9
- 内容包含关键词：0.5-0.7
- 其他字段匹配：0.3-0.5

**高亮显示**:
- 将匹配的关键词用 `<em>` 标签包裹
- 前端可根据标签进行样式渲染

---

## 2. 数据库Schema设计（DDL）

### 2.0 前置准备：触发器函数

```sql
-- 公用函数：用于自动更新 updated_at 时间戳
-- (如果已存在则跳过此步骤)
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION trigger_set_timestamp() IS '触发器函数：自动更新updated_at字段';
```

### 2.1 featured_content（首页精选/焦点图表）

```sql
CREATE TABLE featured_content (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(512) NULL,
    image_url VARCHAR(512) NOT NULL,
    target_type VARCHAR(50) NULL,
    target_id UUID NULL,
    target_url VARCHAR(512) NULL,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    start_at TIMESTAMPTZ NULL,
    end_at TIMESTAMPTZ NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_featured_content_active_sort ON featured_content(is_active, sort_order);
CREATE INDEX idx_featured_content_schedule ON featured_content(start_at, end_at);

-- 触发器
CREATE TRIGGER set_timestamp_featured_content 
BEFORE UPDATE ON featured_content 
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- 注释
COMMENT ON TABLE featured_content IS '首页精选/焦点图内容配置表';
COMMENT ON COLUMN featured_content.title IS '焦点图标题';
COMMENT ON COLUMN featured_content.subtitle IS '焦点图副标题（可选）';
COMMENT ON COLUMN featured_content.image_url IS '焦点图图片URL';
COMMENT ON COLUMN featured_content.target_type IS '目标类型：room/session/topic/brand/external等';
COMMENT ON COLUMN featured_content.target_id IS '目标ID，根据target_type指向对应表的id';
COMMENT ON COLUMN featured_content.target_url IS '外部链接，优先级高于target_id';
COMMENT ON COLUMN featured_content.sort_order IS '排序权重，数字越小越靠前';
COMMENT ON COLUMN featured_content.is_active IS '是否启用：true=可见，false=已下线（软删除）';
COMMENT ON COLUMN featured_content.start_at IS '上线时间，为空表示立即上线';
COMMENT ON COLUMN featured_content.end_at IS '下线时间，为空表示永久有效';
```

---

## 3. Pydantic Schemas定义

### 3.1 Featured Content Schemas

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal
import uuid
import datetime
import re

class FeaturedContentBase(BaseModel):
    """焦点图基础Schema"""
    title: str = Field(..., min_length=1, max_length=255, description="焦点图标题")
    subtitle: Optional[str] = Field(None, max_length=512, description="焦点图副标题")
    image_url: str = Field(..., max_length=512, description="焦点图图片URL")
    target_type: Optional[str] = Field(None, max_length=50, description="目标类型")
    target_id: Optional[uuid.UUID] = Field(None, description="目标资源ID")
    target_url: Optional[str] = Field(None, max_length=512, description="外部链接")
    
    @field_validator('image_url', 'target_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式"""
        if v is not None:
            v = v.strip()
            if not re.match(r'^https?://', v) and not v.startswith('/'):
                raise ValueError('URL必须以http://、https://或/开头')
        return v

class FeaturedContentCreate(FeaturedContentBase):
    """创建焦点图请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")
    start_at: Optional[datetime.datetime] = Field(None, description="上线时间")
    end_at: Optional[datetime.datetime] = Field(None, description="下线时间")

class FeaturedContentUpdate(BaseModel):
    """更新焦点图请求Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    target_url: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None

class FeaturedContentItem(FeaturedContentBase):
    """焦点图响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    sort_order: int
    is_active: bool
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
```

### 3.2 Homepage Schemas

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
import uuid
import datetime

class LiveStatusEnum(str, Enum):
    """直播状态枚举"""
    LIVE = 'live'
    SCHEDULED = 'scheduled'
    REPLAY = 'replay'

class HomepageHostInfo(BaseModel):
    """首页主讲人信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    expert_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None

class HomepageStatusData(BaseModel):
    """首页状态数据Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    viewer_count: Optional[int] = None  # 正在直播的观看人数
    start_time: Optional[datetime.datetime] = None  # 计划开始时间
    duration_seconds: Optional[int] = None  # 回放时长（秒）
    play_count: Optional[int] = None  # 回放播放次数

class HomepageRoomItem(BaseModel):
    """首页直播间信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    live_status: LiveStatusEnum
    host: Optional[HomepageHostInfo] = None
    status_data: HomepageStatusData
    heat: Optional[int] = None

class HomepageRoomsResponse(BaseModel):
    """首页直播间列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[HomepageRoomItem]
    timestamp: datetime.datetime
```

### 3.3 Search Schemas

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
import uuid

class SearchResultType(str, Enum):
    """搜索结果类型枚举"""
    ROOM = 'room'
    EXPERT = 'expert'
    TOPIC = 'topic'
    BRAND = 'brand'

class SearchResultItem(BaseModel):
    """搜索结果项Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    type: SearchResultType
    id: uuid.UUID
    title: str
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="匹配分数（0-1）")
    highlight: Optional[str] = Field(None, description="高亮后的文本片段")
    metadata: Optional[Dict[str, Any]] = Field(None, description="类型特定的元数据")

class SearchResponse(BaseModel):
    """搜索响应Schema"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[SearchResultItem]
    timestamp: datetime.datetime
```

---

## 4. API接口设计（完整CRUD）

### 4.1 Featured Content 模块API（焦点图管理）

#### 4.1.1 获取焦点图列表（公开）

**Endpoint**: `GET /api/v1/featured-content`

**描述**: 获取首页焦点图轮播列表，按排序权重展示（用于首页Banner）

**认证**: 公开访问，无需JWT Token

**请求参数**: 无

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "featured_uuid_1",
      "title": "全国骨科学术研讨会",
      "subtitle": "2026年1月10-12日",
      "image_url": "/media/featured/banner1.jpg",
      "target_type": "session",
      "target_id": "session_uuid_123",
      "target_url": null,
      "sort_order": 0
    },
    {
      "id": "featured_uuid_2",
      "title": "肝胆外科最新进展",
      "subtitle": "名医讲堂系列",
      "image_url": "/media/featured/banner2.jpg",
      "target_type": "topic",
      "target_id": "topic_uuid_456",
      "target_url": null,
      "sort_order": 1
    },
    {
      "id": "featured_uuid_3",
      "title": "合作伙伴推广",
      "subtitle": null,
      "image_url": "/media/featured/banner3.jpg",
      "target_type": "external",
      "target_id": null,
      "target_url": "https://external-site.com/promo",
      "sort_order": 2
    }
  ],
  "timestamp": "2025-10-23T14:00:00Z"
}
```

**执行流程**:

1. **构建查询**: `SELECT * FROM featured_content WHERE is_active = true`
2. **时间范围筛选**: 添加条件 `(start_at IS NULL OR start_at <= NOW()) AND (end_at IS NULL OR end_at >= NOW())`
3. **排序**: 按 `sort_order` 升序排序
4. **限制**: 最多返回10条焦点图
5. **执行查询**: 执行数据库查询获取焦点图列表
6. **序列化**: 将结果序列化为 `FeaturedContentItem` 列表（仅返回前端需要的字段）
7. **返回响应**: 构建统一响应结构并返回

---

#### 4.1.2 创建焦点图（Admin）

**Endpoint**: `POST /api/v1/admin/featured-content`

**描述**: 管理员创建焦点图配置

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "title": "年度医学峰会",
  "subtitle": "2026年医学教育盛会",
  "image_url": "/media/featured/summit2025.jpg",
  "target_type": "session",
  "target_id": "session_uuid_789",
  "target_url": null,
  "sort_order": 0,
  "start_at": "2025-10-25T00:00:00Z",
  "end_at": "2025-11-25T23:59:59Z"
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "featured_uuid_new",
    "title": "年度医学峰会",
    "subtitle": "2026年医学教育盛会",
    "image_url": "/media/featured/summit2025.jpg",
    "target_type": "session",
    "target_id": "session_uuid_789",
    "target_url": null,
    "sort_order": 0,
    "is_active": true,
    "start_at": "2025-10-25T00:00:00Z",
    "end_at": "2025-11-25T23:59:59Z",
    "created_at": "2025-10-23T14:05:00Z",
    "updated_at": "2025-10-23T14:05:00Z"
  },
  "timestamp": "2025-10-23T14:05:00Z"
}
```

**执行流程**:

1. **JWT验证与权限检查**: 验证JWT Token并检查管理员权限
2. **Pydantic校验**: 校验 `FeaturedContentCreate` 模型（URL格式、字段验证等）
3. **UUID生成**: 在应用层调用 `uuid.uuid4()` 生成焦点图ID
4. **目标资源验证**: 若提供了 `target_id`，根据 `target_type` 验证目标资源是否存在（如：room/session/topic等）
5. **创建对象**: 创建 `FeaturedContent` 模型实例并填充所有字段
6. **保存到数据库**: 调用 `db.add()` 和 `db.commit()`
7. **日志记录**: 记录INFO级别日志（焦点图ID、标题、管理员ID）
8. **刷新对象**: 调用 `db.refresh()` 刷新对象以获取数据库生成的时间戳
9. **序列化**: 将创建的焦点图对象序列化为 `FeaturedContentItem`
10. **返回响应**: 构建统一响应结构并返回

---

#### 4.1.3 更新焦点图（Admin）

**Endpoint**: `PATCH /api/v1/admin/featured-content/{content_id}`

**描述**: 管理员更新焦点图配置

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体** (所有字段可选):
```json
{
  "title": "年度医学峰会（更新）",
  "sort_order": 1,
  "is_active": true,
  "end_at": "2025-12-25T23:59:59Z"
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "featured_uuid_new",
    "title": "年度医学峰会（更新）",
    "sort_order": 1,
    "is_active": true,
    "end_at": "2025-12-25T23:59:59Z",
    "updated_at": "2025-10-23T14:10:00Z"
  },
  "timestamp": "2025-10-23T14:10:00Z"
}
```

**执行流程**:

1. **JWT验证与权限检查**: 验证JWT Token并检查管理员权限
2. **查询焦点图**: 根据 `content_id` 查询焦点图对象，若不存在返回 `2001` 错误
3. **Pydantic解析**: 解析 `FeaturedContentUpdate` 模型，提取要更新的字段（使用 `exclude_unset=True`）
4. **目标资源验证**: 若更新 `target_id` 和 `target_type`，验证目标资源有效性
5. **更新对象**: 遍历更新数据，逐个设置焦点图对象的属性值
6. **自动更新时间戳**: 数据库触发器自动更新 `updated_at` 字段
7. **提交事务**: 调用 `db.commit()` 和 `db.refresh()`
8. **日志记录**: 记录INFO级别日志（焦点图ID、更新的字段列表）
9. **序列化**: 将更新后的焦点图对象序列化为 `FeaturedContentItem`
10. **返回响应**: 构建统一响应结构并返回

---

#### 4.1.4 删除焦点图（Admin）

**Endpoint**: `DELETE /api/v1/admin/featured-content/{content_id}`

**描述**: 管理员删除焦点图（软删除）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "featured_uuid_new",
    "status": "soft_deleted",
    "deleted_at": "2025-10-23T14:15:00Z"
  },
  "timestamp": "2025-10-23T14:15:00Z"
}
```

**执行流程**:

1. **JWT验证与权限检查**: 验证JWT Token并检查管理员权限
2. **查询焦点图**: 根据 `content_id` 查询焦点图对象，若不存在返回 `2001` 错误
3. **软删除**: 设置 `is_active=false`
4. **提交事务**: 调用 `db.commit()`
5. **日志记录**: 记录WARNING级别日志（焦点图ID、标题、管理员ID）
6. **返回响应**: 构建删除状态响应并返回

---

### 4.2 Homepage 模块API（首页专用）

#### 4.2.1 获取首页直播间列表

**Endpoint**: `GET /api/v1/homepage/rooms`

**描述**: 获取首页展示的直播间列表，包含实时状态、主讲专家、热度等信息（分页）

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10, 最大100): 每页数量
- `sort` (string, 可选, 默认`heat:desc`): 排序规则（`heat:desc`, `start_time:asc`, `created_at:desc`）
- `category_id` (UUID, 可选): 按分类筛选

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 15,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "room_uuid_1",
        "title": "肝胆胰外科手术直播演示",
        "cover_url": "/media/rooms/.../cover1.jpg",
        "summary": "演示最新的微创技术...",
        "live_status": "live",
        "host": {
          "expert_id": "expert_uuid_doc_B",
          "user_id": null,
          "name": "李四 教授",
          "title": "主任医师",
          "hospital": "XX 医院"
        },
        "status_data": {
          "viewer_count": 1250,
          "start_time": null,
          "duration_seconds": null,
          "play_count": null
        },
        "heat": 8500
      },
      {
        "id": "room_uuid_2",
        "title": "骨科病例讨论会 (预告)",
        "cover_url": "/media/rooms/.../cover2.jpg",
        "summary": "讨论罕见病例...",
        "live_status": "scheduled",
        "host": {
          "expert_id": "expert_uuid_doc_C",
          "user_id": null,
          "name": "王五 主任",
          "title": "骨科主任",
          "hospital": "YY 医院"
        },
        "status_data": {
          "viewer_count": null,
          "start_time": "2025-10-25T19:30:00Z",
          "duration_seconds": null,
          "play_count": null
        },
        "heat": null
      },
      {
        "id": "room_uuid_3",
        "title": "基础操作演示 (回放)",
        "cover_url": "/media/rooms/.../cover3.jpg",
        "summary": "适合新手学习...",
        "live_status": "replay",
        "host": null,
        "status_data": {
          "viewer_count": null,
          "start_time": null,
          "duration_seconds": 3650,
          "play_count": 500
        },
        "heat": 1500
      }
    ]
  },
  "timestamp": "2025-10-23T16:00:00Z"
}
```

**执行流程**（复杂联表查询，详细15步）:

1. **参数解析与校验**: 解析并验证查询参数（page、size、sort、category_id）
2. **构建基础查询**: 从 `live_rooms lr` 表开始
3. **分类筛选**: 若提供 `category_id`，添加筛选条件：`WHERE lr.category_id = :category_id`
4. **查找相关场次**: 使用子查询或窗口函数找到每个房间的"相关场次"（relevant_session）
   - 优先级：live > scheduled > latest replay
   - 使用 `DISTINCT ON` 或 `ROW_NUMBER()` 窗口函数
   - 注意：目前一个 `live_room` 只包含一个 `live_session`，但保留此逻辑以支持未来扩展
5. **LEFT JOIN live_session_experts（场次专家关联）**: 获取场次关联的专家信息
   - 查询条件：`session_id = ls.id AND role = '主讲'`
   - 按 `sort_order` 排序，取第一个
   - 如果没有主讲专家，降级查找其他角色（主持、嘉宾）
6. **LEFT JOIN experts（场次专家）**: 获取专家的详细信息（name、title、hospital等）
7. **LEFT JOIN session_statistics**: 获取统计数据（观看人数、播放次数等）
8. **Service层Host选择**: 应用Host选择逻辑（从 live_session_experts 获取专家信息）
   - 如果找到主讲专家，使用主讲专家信息
   - 如果没有主讲专家，使用其他角色专家信息（主持、嘉宾）
   - 如果场次没有关联任何专家，`host` 为 `null`
9. **确定live_status**: 根据 `relevant_session` 的status确定直播状态（live/scheduled/replay）
10. **计算热度**: 使用 `session_statistics` 数据和预定义公式计算热度
11. **构造status_data**: 根据 `live_status` 填充相应字段（live填充viewer_count，scheduled填充start_time，replay填充duration和play_count）
12. **COUNT查询**: 执行COUNT查询获取筛选后的总房间数
13. **排序**: 解析 `sort` 参数并应用排序（热度、开始时间、创建时间等）
14. **分页**: 应用 `LIMIT :size OFFSET :offset`
15. **执行查询**: 执行主查询获取当前页的房间列表，将结果映射到 `HomepageRoomItem` Schema，构建分页响应并返回

**核心SQL示例**（PostgreSQL）:
```sql
SELECT DISTINCT ON (lr.id)
    lr.*,
    ls.id AS session_id,
    ls.status AS session_status,
    -- 场次专家信息（通过 live_session_experts 表）
    lse.expert_id AS session_expert_id,
    lse.role AS expert_role,
    e.id AS expert_id,
    e.name AS expert_name,
    e.title AS expert_title,
    e.hospital AS expert_hospital,
    -- session_statistics 统计信息
    ss.peak_viewer_count,
    ss.total_viewer_count,
    ...
FROM live_rooms lr
LEFT JOIN live_sessions ls ON ls.room_id = lr.id
-- 通过 live_session_experts 表查找场次关联的专家（优先主讲，按sort_order排序）
LEFT JOIN LATERAL (
    SELECT expert_id, role
    FROM live_session_experts
    WHERE session_id = ls.id
    ORDER BY 
        CASE role
            WHEN '主讲' THEN 1
            WHEN '主持' THEN 2
            WHEN '嘉宾' THEN 3
        END,
        sort_order ASC
    LIMIT 1
) lse ON TRUE
LEFT JOIN experts e ON lse.expert_id = e.id
LEFT JOIN session_statistics ss ON ls.id = ss.session_id
WHERE lr.category_id = :category_id (如果提供)
ORDER BY lr.id,
    CASE ls.status
        WHEN 'live' THEN 1
        WHEN 'scheduled' THEN 2
        WHEN 'ready' THEN 3
        ELSE 4
    END,
    ls.start_time DESC;
```

**注意**：
- 不再 JOIN `users` 表（`users` 表在 `user_service` 中，不同数据库）
- `live_rooms.user_id` 即为 `users.public_id`，直接使用，无需查询 `users` 表
- 通过 `live_session_experts` 表查询场次关联的专家信息

---

### 4.3 Search 模块API（全局搜索）

#### 4.3.1 全局搜索

**Endpoint**: `GET /api/v1/search`

**描述**: 全局搜索接口，支持跨直播间、专家、专题等资源的模糊搜索（分页）

**认证**: 公开访问，无需JWT Token（可选：登录后返回更个性化的结果）

**请求参数 (Query)**:
- `q` (string, 必需): 搜索关键词（最少2个字符）
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10, 最大50): 每页数量
- `type` (string, 可选): 资源类型筛选（`room`, `expert`, `topic`, `brand`，多选用逗号分隔）
- `category_id` (UUID, 可选): 按分类筛选（仅对room有效）

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 25,
    "page": 1,
    "size": 10,
    "query": "肝胆外科",
    "items": [
      {
        "type": "room",
        "id": "room_uuid_1",
        "title": "肝胆胰外科手术直播演示",
        "summary": "演示最新的微创技术...",
        "cover_url": "/media/rooms/.../cover1.jpg",
        "match_score": 0.95,
        "highlight": "肝胆胰<em>外科</em>手术直播演示",
        "metadata": {
          "live_status": "live",
          "viewer_count": 1250
        }
      },
      {
        "type": "expert",
        "id": "expert_uuid_doc_B",
        "title": "李四 教授",
        "summary": "主任医师，擅长微创肝胆手术",
        "cover_url": "/media/experts/.../avatar.jpg",
        "match_score": 0.88,
        "highlight": "擅长微创<em>肝胆</em>手术",
        "metadata": {
          "hospital": "XX 医院",
          "title": "主任医师"
        }
      },
      {
        "type": "topic",
        "id": "topic_uuid_123",
        "title": "肝胆外科精品课程",
        "summary": "系统学习肝胆外科知识",
        "cover_url": "/media/topics/.../banner.jpg",
        "match_score": 0.82,
        "highlight": "<em>肝胆外科</em>精品课程",
        "metadata": {
          "room_count": 15
        }
      }
    ]
  },
  "timestamp": "2025-10-23T17:00:00Z"
}
```

**失败响应** (`4001 Parameter Error`):
```json
{
  "code": 4001,
  "message": "参数错误",
  "data": {
    "field": "q",
    "error": "搜索关键词至少需要2个字符"
  },
  "timestamp": "2025-10-23T17:00:00Z"
}
```

**执行流程**（15步，含复杂搜索逻辑）:

1. **参数解析与校验**: 解析并验证查询参数（q、page、size、type等）
2. **搜索关键词验证**: 验证搜索关键词长度（至少2个字符，中文1个字符当2个）
3. **解析type参数**: 确定搜索范围（默认搜索所有类型）
4. **构建搜索查询**: 使用PostgreSQL全文搜索或Elasticsearch
5. **按资源类型搜索**: 
   - **room**: 搜索 `live_rooms` 表的 `title` 和 `summary` 字段
   - **expert**: 搜索 `experts` 表的 `name`, `bio`, `expertise_areas` 字段
   - **topic**: 搜索 `topics` 表的 `title` 和 `description` 字段
   - **brand**: 搜索 `brands` 表的 `name` 和 `description` 字段
6. **合并结果**: 使用 `UNION ALL` 合并各类型的搜索结果
7. **计算匹配分数**: 基于关键词在标题/内容中的位置和频率计算分数
8. **生成高亮文本**: 将匹配的关键词用 `<em>` 标签包裹
9. **填充metadata**: 填充类型特定的元数据（room: live_status/viewer_count，expert: hospital/title，topic: room_count）
10. **排序**: 按匹配分数降序排序
11. **COUNT查询**: 执行COUNT查询获取总结果数
12. **分页**: 应用 `LIMIT :size OFFSET :offset`
13. **执行查询**: 获取当前页的搜索结果
14. **序列化**: 将结果映射到 `SearchResultItem` 列表
15. **日志记录**: 记录DEBUG级别日志（搜索关键词、结果数量、执行时间），构建分页响应并返回

**实现建议**:

**阶段1（MVP）**: 使用PostgreSQL的 `ILIKE` 实现基础搜索

```sql
-- 示例SQL（简化版）
SELECT 
    'room' AS type,
    id,
    title,
    summary,
    cover_url,
    (CASE 
        WHEN title ILIKE '%肝胆%' THEN 1.0
        WHEN summary ILIKE '%肝胆%' THEN 0.7
        ELSE 0.5
    END) AS match_score
FROM live_rooms
WHERE title ILIKE '%肝胆%' OR summary ILIKE '%肝胆%'

UNION ALL

SELECT 
    'expert' AS type,
    id,
    name AS title,
    bio AS summary,
    avatar_url AS cover_url,
    (CASE 
        WHEN name ILIKE '%肝胆%' THEN 1.0
        WHEN bio ILIKE '%肝胆%' THEN 0.8
        ELSE 0.6
    END) AS match_score
FROM experts
WHERE name ILIKE '%肝胆%' OR bio ILIKE '%肝胆%'

ORDER BY match_score DESC
LIMIT :size OFFSET :offset;
```

**阶段2（优化）**: 使用PostgreSQL全文搜索（tsvector）

```sql
-- 为表添加全文搜索列和索引
ALTER TABLE live_rooms ADD COLUMN search_vector tsvector;
CREATE INDEX idx_live_rooms_search ON live_rooms USING gin(search_vector);

-- 更新触发器自动维护search_vector
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
ON live_rooms FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.simple', title, summary);

-- 搜索查询
SELECT *, ts_rank(search_vector, query) AS rank
FROM live_rooms, to_tsquery('肝胆 & 外科') query
WHERE search_vector @@ query
ORDER BY rank DESC;
```

**阶段3（高级）**: 集成Elasticsearch
- 支持中文分词
- 支持同义词搜索
- 支持拼音搜索
- 更精确的相关性评分

---

#### 4.3.2 搜索建议（自动补全）

**Endpoint**: `GET /api/v1/search/suggestions`

**描述**: 提供搜索关键词建议（自动补全）

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `q` (string, 必需): 搜索前缀（最少1个字符）
- `limit` (int, 可选, 默认5, 最大10): 返回建议数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "suggestions": [
      "肝胆外科",
      "肝胆外科微创手术",
      "肝胆外科专家",
      "肝胆外科直播",
      "肝胆外科病例"
    ]
  },
  "timestamp": "2025-10-23T17:05:00Z"
}
```

**执行流程**:

1. **参数解析与校验**: 验证搜索前缀长度
2. **查询热门搜索**: 从搜索历史表或Redis缓存中查询热门搜索词
3. **前缀匹配**: 筛选以 `q` 为前缀的搜索词
4. **排序**: 按搜索频率降序排序
5. **限制**: 应用 `limit` 参数
6. **返回响应**: 构建建议列表并返回

---

## 5. 执行流程详细说明

### 5.1 Featured Content 模块执行流程

#### 创建焦点图完整流程：
1. API路由接收请求 → 2. JWT验证与权限检查 → 3. Pydantic校验 → 4. UUID生成 → 5. 目标资源验证 → 6. 创建对象 → 7. 保存到数据库 → 8. 日志记录 → 9. 刷新对象 → 10. 序列化 → 11. 返回响应

#### 删除焦点图完整流程：
1. API路由接收请求 → 2. JWT验证与权限检查 → 3. 查询焦点图 → 4. 软删除 → 5. 提交事务 → 6. 日志记录 → 7. 返回响应

### 5.2 Homepage 模块执行流程

#### 获取首页直播间列表完整流程（复杂）：
1. 参数解析与校验 → 2. 构建基础查询 → 3. 分类筛选 → 4. 查找相关场次（子查询/窗口函数） → 5. LEFT JOIN live_session_experts（场次专家关联） → 6. LEFT JOIN experts（场次专家） → 7. LEFT JOIN session_statistics → 8. Service层Host选择（从live_session_experts获取） → 9. 确定live_status → 10. 计算热度 → 11. 构造status_data → 12. COUNT查询 → 13. 排序 → 14. 分页 → 15. 执行查询并返回

### 5.3 Search 模块执行流程

#### 全局搜索完整流程：
1. 参数解析与校验 → 2. 搜索关键词验证 → 3. 解析type参数 → 4. 构建搜索查询 → 5. 按资源类型搜索 → 6. 合并结果 → 7. 计算匹配分数 → 8. 生成高亮文本 → 9. 填充metadata → 10. 排序 → 11. COUNT查询 → 12. 分页 → 13. 执行查询 → 14. 序列化 → 15. 日志记录并返回

---

## 6. 错误处理与事务管理

### 6.1 错误处理策略

**业务异常**:
- 使用业务状态码（2xxx、3xxx、4xxx）
- 提供详细的错误信息和字段说明
- 记录WARNING级别日志

**系统异常**:
- 捕获所有未预期的异常
- 转换为统一的系统错误响应（5001）
- 记录ERROR级别日志

**搜索异常**:
- 搜索引擎不可用时降级为简单模糊搜索
- 记录ERROR级别日志并告警

### 6.2 事务管理规范

**单表操作**:
- 使用FastAPI的依赖注入获取数据库会话
- 操作完成后调用 `db.commit()`
- 异常时自动回滚

---

## 7. 性能优化建议

### 7.1 数据库优化

**索引优化**:
- 焦点图表已添加复合索引（is_active, sort_order）
- 为搜索字段添加全文索引（tsvector）

**查询优化**:
- 首页API使用窗口函数或子查询优化相关场次查找
- 搜索API使用 `UNION ALL` 而非 `UNION`（避免去重开销）

### 7.2 缓存策略

**焦点图缓存**:
- 使用Redis缓存焦点图列表
- 缓存时间：3600秒（1小时）
- 更新/删除时清除对应缓存

**首页列表缓存**:
- 缓存首页直播间列表（按分类和排序分别缓存）
- 缓存时间：60秒（1分钟）
- 直播状态变化时更新缓存

**搜索结果缓存**:
- 缓存热门搜索结果
- 缓存时间：300秒（5分钟）
- 使用LRU策略淘汰

### 7.3 应用层优化

**批量查询优化**:
- 使用 `joinedload` 预加载关联数据，避免N+1问题
- 首页API使用一次复杂查询而非多次简单查询

**异步处理**:
- 搜索索引更新可使用异步任务
- 避免阻塞主业务流程

---

## 8. 测试建议

### 8.1 单元测试

**Featured Content模块测试**:
- 测试焦点图CRUD操作
- 测试定时上下线逻辑（start_at/end_at）
- 测试目标资源验证
- 测试排序功能

**Homepage模块测试**:
- 测试Host选择逻辑（从live_session_experts获取专家信息，优先级：主讲 > 主持 > 嘉宾，或无专家时为null）
- 测试live_status判断逻辑
- 测试热度计算公式
- 测试分类筛选和排序

**Search模块测试**:
- 测试搜索关键词验证
- 测试跨资源搜索
- 测试匹配分数计算
- 测试高亮显示功能

### 8.2 集成测试

**API集成测试**:
- 测试完整的API调用流程
- 测试JWT认证和权限验证
- 测试复杂联表查询性能

### 8.3 性能测试

**负载测试**:
- 模拟高并发查询首页列表
- 模拟高并发搜索请求
- 测试数据库连接池性能

**压力测试**:
- 测试大数据量场景（10万+直播间）
- 测试复杂查询性能
- 识别性能瓶颈

---

## 9. 错误码对照表

| 错误码 | 说明 | 使用场景 |
|--------|------|----------|
| `200` | 成功 | 所有成功响应 |
| `2001` | 资源不存在 | 焦点图不存在、目标资源不存在 |
| `2002` | 资源已存在 | 唯一约束冲突 |
| `3002` | 权限不足 | 非管理员访问管理接口 |
| `4001` | 参数校验失败 | 请求体格式错误、字段验证失败 |
| `4002` | 参数值无效 | 资源类型无效、分类ID无效 |
| `5001` | 服务器内部错误 | 数据库查询失败、搜索引擎不可用 |

---

## 10. 部署与监控建议

### 10.1 部署检查清单

- [ ] 数据库迁移脚本已执行（创建1张表）
- [ ] 触发器函数已创建（trigger_set_timestamp）
- [ ] 索引已创建（所有idx_*索引）
- [ ] 全文搜索索引已创建（如果使用PostgreSQL全文搜索）
- [ ] API接口已部署并可访问
- [ ] JWT认证配置已验证
- [ ] 权限系统已配置（ADMIN/SUPERADMIN角色）
- [ ] Redis缓存已配置
- [ ] Elasticsearch已配置（如果使用）

### 10.2 监控指标

**API监控**:
- 请求成功率（目标：>99.9%）
- 平均响应时间（目标：<200ms）
- P95响应时间（目标：<500ms）
- 错误率（目标：<0.1%）

**搜索性能监控**:
- 搜索查询延迟（目标：<300ms）
- 搜索引擎可用性（目标：>99%）
- 搜索结果相关性（人工评估）

### 10.3 告警规则

**严重告警**:
- API可用性<95%（立即通知）
- 搜索引擎不可用（立即通知）
- 首页API响应时间>2s（立即通知）

**警告告警**:
- API响应时间>1s（1分钟内持续）
- 错误率>1%（5分钟内持续）
- 搜索查询延迟>1s（5分钟内持续）

---

## 11. 后续开发建议

### 11.1 优先级P0（必须完成）

1. **实现核心API接口**:
   - Featured Content模块：4个API
   - Homepage模块：1个API
   - Search模块：2个API

2. **数据库迁移**:
   - 创建1张表
   - 创建所有索引
   - 创建触发器

3. **基础搜索实现**:
   - 使用PostgreSQL ILIKE实现基础搜索
   - 实现匹配分数计算
   - 实现高亮显示

### 11.2 优先级P1（重要功能）

1. **缓存实现**:
   - 焦点图列表缓存
   - 首页列表缓存
   - 搜索结果缓存

2. **性能优化**:
   - 首页API复杂查询优化
   - 搜索API索引优化
   - 批量查询优化

3. **监控告警**:
   - API监控接入
   - 搜索性能监控
   - 告警规则配置

### 11.3 优先级P2（增强功能）

1. **搜索增强**:
   - 集成Elasticsearch
   - 支持中文分词
   - 支持同义词搜索
   - 支持拼音搜索

2. **首页增强**:
   - 个性化推荐算法
   - 用户行为分析
   - A/B测试支持

3. **焦点图增强**:
   - 点击统计
   - 转化率分析
   - 智能排序

---

**文档结束** ✅

