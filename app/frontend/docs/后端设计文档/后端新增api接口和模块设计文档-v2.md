# 新增模块设计：Tags、Categories、Brands、Experts、Session_Tags等（修订版 V2.0）

**版本**: V2.0 (规范修订版)  
**修订日期**: 2025-10-23  
**状态**: 设计定稿  
**基于**: 审查报告全面修订

---

## 📋 修订说明

本文档是对 V1.0 的全面修订，已修复审查报告中的所有问题：

### ✅ 已修复的关键问题（23项）

**P0级严重问题（7项）**：
- ✅ 新增 `session_tags` 关联表
- ✅ 新增 `live_sessions.featured_expert_id` 字段DDL
- ✅ 修正UUID主键生成方式（应用层生成，非数据库默认值）
- ✅ 为所有表添加 `updated_at` 触发器
- ✅ 统一HTTP方法为 `PATCH`（删除所有 `PUT`）
- ✅ 修正错误码体系（2xxx业务/3xxx权限/4xxx参数）
- ✅ Pydantic改为V2语法（`model_config = ConfigDict(from_attributes=True)`）

**P1级重要问题（10项）**：
- ✅ 新增 `live_sessions.summary` 字段
- ✅ 补充完整的字段注释
- ✅ 添加外键命名约束
- ✅ 统一认证权限描述
- ✅ 补充JWT Token格式说明
- ✅ 详细化所有API执行流程（8-10步详细说明）
- ✅ 完善 `live_rooms.category_id` 关联方案
- ✅ 定义完整的响应Schema
- ✅ 统一软删除策略
- ✅ 补充输入验证规则

**P2级建议优化（6项）**：
- ✅ 优化索引策略
- ✅ 新增批量操作接口
- ✅ 完善错误码对照表
- ✅ 增加性能优化说明

---

## 📖 文档规范说明

### 统一响应结构

所有API接口的响应都遵循以下统一结构：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... } | null,
  "timestamp": "2025-10-23T10:00:00Z"
}
```

### 分页响应格式

```json
{
  "total": 100,
  "page": 1,
  "size": 10,
  "items": [ ... ]
}
```

### 认证规范

- **公开接口**: 无需JWT Token
- **用户接口**: 需要JWT Token（`Authorization: Bearer <token>`）
- **Admin接口**: 需要JWT Token + `ADMIN` 或 `SUPERADMIN` 角色

### JWT Token格式说明

**Access Token Payload**:
```json
{
  "sub": "user_uuid",           // 用户ID (users.public_id)
  "role": "ADMIN",               // 用户角色
  "type": "access",              // Token类型
  "exp": 1757364000,             // 过期时间
  "iat": 1757363100,             // 签发时间
  "jti": "token_unique_id"       // Token唯一ID
}
```

**详见**: 《用户模块设计文档》Section 7.1.3

### 业务状态码体系

| 业务状态码 | 含义 | 使用场景 |
|:---------|:-----|:---------|
| `200` | 成功 | 操作成功完成 |
| `2001` | 资源不存在 | 查询的资源不存在 |
| `2002` | 资源已存在 | 创建时名称/唯一键冲突 |
| `2003` | 操作被禁止 | 删除被引用的资源等 |
| `2004` | 业务逻辑错误 | 其他业务规则违反 |
| `3001` | 未认证 | Token缺失或无效 |
| `3002` | 权限不足 | 用户角色权限不足 |
| `4001` | 参数校验失败 | 请求参数格式/类型错误 |
| `1002` | 数据库错误 | 系统级数据库异常 |

---

## 目录

1. 设计要点与约定
2. 数据库Schema设计（DDL）
   - tags（内容标签表）
   - categories（全局分类表）
   - brands（品牌/合作伙伴表）
   - brand_topics（品牌-专题关联表）
   - experts（专家信息表）
   - session_tags（场次-标签关联表）
   - user_favorites（用户收藏表）
   - watch_history（观看历史表）
   - user_subscriptions（订阅提醒表）
   - featured_content（首页精选表）
   - live_sessions字段扩展（featured_expert_id, summary）
   - live_rooms字段确认（category_id）
3. Pydantic Schemas定义
4. API接口设计（完整CRUD）
5. 执行流程详细说明
6. 错误处理与事务管理
7. 性能优化建议
8. 迁移实施计划

---

## 1. 设计要点与约定

### 1.1 数据库设计规范

**遵循《直播核心功能设计文档V3.2》Section 7.1规范**：

1. **UUID主键生成**：
   - ✅ 所有表的主键UUID**必须在应用层生成**（`uuid.uuid4()`）
   - ❌ 禁止使用数据库默认值 `DEFAULT gen_random_uuid()`
   - 原因：便于日志记录、批量插入优化、避免数据库特定依赖

2. **时间戳字段**：
   - 使用 `TIMESTAMPTZ` 类型，以UTC存储
   - `created_at`: `DEFAULT CURRENT_TIMESTAMP`
   - `updated_at`: `DEFAULT CURRENT_TIMESTAMP` + 触发器自动更新

3. **外键约束**：
   - 必须命名外键约束（`CONSTRAINT fk_<table>_<column>`）
   - 微服务架构下，跨服务引用（如user_id）在应用层验证，不添加数据库外键

4. **用户ID引用规范（重要！）**：

   **⚠️ 特别说明：本系统用户表采用双ID设计**
   
   根据《用户模块设计文档authing版+权限设计版.md》Section 3.1，用户表（users）采用**双ID架构**：
   
   | 字段名 | 类型 | 用途 | 暴露范围 |
   |--------|------|------|----------|
   | `user_id` | BIGINT | 数据库内部主键，自增 | ❌ 不对外暴露 |
   | `public_id` | UUID | 对外公开标识符 | ✅ 对外暴露（API、JWT） |
   
   **📌 本文档的命名约定**：
   - **本文档中所有表的 `user_id` 字段，实际上引用的是 `users.public_id`（UUID类型）**
   - 字段命名为 `user_id` 而非 `public_id` 是为了保持代码可读性（更符合直觉）
   - 但本质上存储和引用的是用户的公开UUID，不是内部自增ID
   
   **设计原因**：
   - **微服务架构隔离**：LiveCore Service 不直接访问 User Service 的数据库，仅通过 public_id 引用用户
   - **安全性**：避免暴露内部自增ID，防止用户信息遍历攻击
   - **JWT集成**：JWT Token的 `sub` 字段存储的是 `public_id`，LiveCore Service 通过Token验证用户身份
   
   **实现要点**：
   - 数据库定义：`user_id UUID NOT NULL`（注意是UUID类型，不是BIGINT）
   - 外键处理：由于跨服务，不添加数据库外键约束，在应用层验证
   - JWT验证：`Depends(get_current_user)` 会从JWT Token的 `sub` 字段提取 `public_id`，赋值给 `user_id` 变量
   - 数据库注释：`COMMENT ON COLUMN xxx.user_id IS '用户公开ID（users.public_id），应用层验证，JWT Token的sub字段值'`
   
   **代码示例**：
   ```python
   # JWT Token验证依赖函数
   async def get_current_user(token: str = Depends(oauth2_scheme)):
       payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
       user_id: str = payload.get("sub")  # 这是 users.public_id (UUID字符串)
       # 验证user_id有效性（调用User Service API）
       return {"user_id": UUID(user_id), "role": payload.get("role")}
   
   # API接口使用
   @app.post("/api/v1/users/me/favorites")
   async def add_favorite(
       room_id: UUID,
       current_user: dict = Depends(get_current_user)
   ):
       user_id = current_user["user_id"]  # 这是 users.public_id (UUID对象)
       # 创建收藏记录
       favorite = UserFavorite(
           id=uuid.uuid4(),
           user_id=user_id,  # 存储的是 public_id
           room_id=room_id
       )
   ```
   
   **涉及的表**：
   - `experts.user_id` → `users.public_id`（可选，外部专家可为NULL）
   - `user_favorites.user_id` → `users.public_id`
   - `watch_history.user_id` → `users.public_id`
   - `user_subscriptions.user_id` → `users.public_id`

5. **字段注释**：
   - 所有表必须有 `COMMENT ON TABLE`
   - 关键字段必须有 `COMMENT ON COLUMN`

6. **索引策略**：
   - 外键字段必须添加索引
   - 常用查询条件添加复合索引
   - 唯一约束自动创建唯一索引

### 1.2 API设计规范

**遵循《直播核心功能设计文档V3.2》Section 4规范**：

1. **HTTP方法**：
   - `GET`: 查询（幂等）
   - `POST`: 创建
   - `PATCH`: 部分更新（推荐）
   - `DELETE`: 删除

2. **路径设计**：
   - 公开接口: `/api/v1/<resource>`
   - 用户接口: `/api/v1/users/me/<resource>`
   - Admin接口: `/api/v1/admin/<resource>`

3. **认证要求**：
   - 使用 `Depends(get_current_user)` 提取JWT Token
   - 从Token的 `sub` 字段提取 `user_id`
   - 从Token的 `role` 字段验证权限

4. **执行流程规范**：
   - 必须包含8-10步详细说明
   - 包含权限验证、参数校验、业务逻辑、异常处理、日志记录

### 1.3 软删除策略

**统一策略**：

1. **基础数据表**（tags, categories, brands, experts, featured_content）：
   - 默认：软删除（`is_active=false`）
   - 原因：可能被历史数据引用
   - 硬删除：需要 `SUPERADMIN` 权限 + 引用检查

2. **关联表**（session_tags, brand_topics, user_favorites, user_subscriptions）：
   - 用户相关：软删除（保留审计）
   - 纯关联：硬删除（ON DELETE CASCADE）

3. **历史记录表**（watch_history）：
   - 用户可删除单条（硬删除）
   - 建议提供批量清空功能（保留30天）

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

### 2.1 tags（内容标签表）

```sql
CREATE TABLE tags (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    name VARCHAR(80) NOT NULL UNIQUE,
    slug VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_is_active ON tags(is_active);

-- 触发器
CREATE TRIGGER set_timestamp_tags 
BEFORE UPDATE ON tags 
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- 注释
COMMENT ON TABLE tags IS '内容标签表（多对多关联 live_sessions 等）';
COMMENT ON COLUMN tags.id IS '主键UUID，在应用层通过uuid.uuid4()生成';
COMMENT ON COLUMN tags.name IS '标签名称，全局唯一';
COMMENT ON COLUMN tags.slug IS 'URL友好的标识符，用于前端路由';
COMMENT ON COLUMN tags.is_active IS '是否启用：true=可用，false=已隐藏（软删除）';
```

### 2.2 categories（全局分类表）

```sql
CREATE TABLE categories (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(120),
    icon VARCHAR(255),
    description TEXT,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_categories_sort_order ON categories(sort_order);
CREATE INDEX idx_categories_is_active ON categories(is_active);
CREATE INDEX idx_categories_active_sort ON categories(is_active, sort_order) 
WHERE is_active = true;

-- 触发器
CREATE TRIGGER set_timestamp_categories 
BEFORE UPDATE ON categories 
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- 注释
COMMENT ON TABLE categories IS '全局医学内容分类表（如：肝胆胰外科、胃肠外科等）';
COMMENT ON COLUMN categories.id IS '主键UUID，在应用层通过uuid.uuid4()生成';
COMMENT ON COLUMN categories.sort_order IS '排序权重，数字越小越靠前，用于前端展示顺序';
COMMENT ON COLUMN categories.icon IS '分类图标名称或URL';
COMMENT ON COLUMN categories.is_active IS '是否启用：true=前端可见，false=已下线';
```

### 2.3 brands（品牌/合作伙伴表）

```sql
CREATE TABLE brands (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    name VARCHAR(150) NOT NULL UNIQUE,
    slug VARCHAR(150),
    logo_url VARCHAR(512),
    description TEXT,
    website_url VARCHAR(255),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_brands_sort_order ON brands(sort_order);
CREATE INDEX idx_brands_is_active ON brands(is_active);
CREATE INDEX idx_brands_active_sort ON brands(is_active, sort_order) 
WHERE is_active = true;

-- 触发器
CREATE TRIGGER set_timestamp_brands 
BEFORE UPDATE ON brands 
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- 注释
COMMENT ON TABLE brands IS '品牌/合作伙伴信息表（如：迈瑞医疗、威克·微课等）';
COMMENT ON COLUMN brands.id IS '主键UUID，在应用层通过uuid.uuid4()生成';
COMMENT ON COLUMN brands.logo_url IS '品牌Logo图片URL';
COMMENT ON COLUMN brands.website_url IS '品牌官网链接';
COMMENT ON COLUMN brands.sort_order IS '排序权重，用于品牌栏展示顺序';
```

### 2.4 brand_topics（品牌-专题关联表）

```sql
CREATE TABLE brand_topics (
    brand_id UUID NOT NULL,
    topic_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (brand_id, topic_id),
    
    -- 命名的外键约束
    CONSTRAINT fk_brand_topics_brand_id 
        FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    CONSTRAINT fk_brand_topics_topic_id 
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_brand_topics_brand_id ON brand_topics(brand_id);
CREATE INDEX idx_brand_topics_topic_id ON brand_topics(topic_id);

-- 注释
COMMENT ON TABLE brand_topics IS '品牌与专题的多对多关联表';
COMMENT ON COLUMN brand_topics.brand_id IS '品牌ID，关联brands表';
COMMENT ON COLUMN brand_topics.topic_id IS '专题ID，关联topics表';
```

### 2.5 experts（专家信息表）

```sql
CREATE TABLE experts (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    -- user_id为可选关联，关联平台用户
    user_id UUID UNIQUE NULL,
    
    name VARCHAR(120) NOT NULL,
    title VARCHAR(120),
    hospital VARCHAR(200),
    department VARCHAR(120),
    expertise_areas TEXT,
    bio TEXT,
    avatar_url VARCHAR(512),
    is_featured BOOLEAN DEFAULT false,
    sort_order INT DEFAULT 0,
    contact_info JSONB NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 命名的外键约束（应用层验证，不添加数据库外键）
    -- CONSTRAINT fk_experts_user_id 
    --     FOREIGN KEY (user_id) REFERENCES users(public_id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_experts_is_featured ON experts(is_featured, sort_order);
CREATE INDEX idx_experts_user_id ON experts(user_id);

-- 触发器
CREATE TRIGGER set_timestamp_experts 
BEFORE UPDATE ON experts 
FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();

-- 注释
COMMENT ON TABLE experts IS '平台专家信息表（外部专家+内部用户专家）';
COMMENT ON COLUMN experts.id IS '主键UUID，在应用层通过uuid.uuid4()生成';
COMMENT ON COLUMN experts.user_id IS '关联平台用户公开ID（users.public_id），可为空表示外部专家（未绑定平台账号），应用层验证';
COMMENT ON COLUMN experts.title IS '职称（如：主任医师、教授）';
COMMENT ON COLUMN experts.expertise_areas IS '擅长领域，逗号分隔或JSON字符串';
COMMENT ON COLUMN experts.is_featured IS '是否为首页推荐专家';
COMMENT ON COLUMN experts.contact_info IS 'JSONB格式存储联系方式：{phone, email, office}';
```

### 2.6 session_tags（场次-标签关联表）

```sql
CREATE TABLE session_tags (
    session_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (session_id, tag_id),
    
    -- 命名的外键约束
    CONSTRAINT fk_session_tags_session_id 
        FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_tags_tag_id 
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_session_tags_session_id ON session_tags(session_id);
CREATE INDEX idx_session_tags_tag_id ON session_tags(tag_id);

-- 注释
COMMENT ON TABLE session_tags IS '直播场次与标签的多对多关联表';
COMMENT ON COLUMN session_tags.session_id IS '场次ID，关联live_sessions表';
COMMENT ON COLUMN session_tags.tag_id IS '标签ID，关联tags表';
```

### 2.7 user_favorites（用户收藏表）

```sql
CREATE TABLE user_favorites (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    user_id UUID NOT NULL,
    room_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：同一用户不能重复收藏同一房间
    CONSTRAINT uq_user_favorites_user_room UNIQUE(user_id, room_id),
    
    -- 命名的外键约束（应用层验证user_id）
    CONSTRAINT fk_user_favorites_room_id 
        FOREIGN KEY (room_id) REFERENCES live_rooms(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_room_id ON user_favorites(room_id);
CREATE INDEX idx_user_favorites_user_active ON user_favorites(user_id, is_active) 
WHERE is_active = true;

-- 注释
COMMENT ON TABLE user_favorites IS '用户收藏直播间关联表';
COMMENT ON COLUMN user_favorites.user_id IS '用户公开ID（users.public_id），应用层验证，JWT Token的sub字段值';
COMMENT ON COLUMN user_favorites.is_active IS '是否有效：true=已收藏，false=已取消（软删除）';
```

### 2.8 watch_history（观看历史表）

**设计说明**：

#### 2.8.1 核心设计决策：为什么仅关联session_id？

本表采用**仅关联 `session_id`（直播场次）** 的设计，不直接关联 `room_id`（直播间），也不同时关联两者。这个设计决策基于以下深入分析：

**业务场景分析**：

1. **用户观看的本质是视频内容，而非直播间容器**：
   - 用户点击直播间后，实际观看的是**具体的视频内容（live_session）**
   - 直播间（live_room）是内容的组织容器，一个直播间可能包含：
     - **单场次**：一个直播间只有一次直播（最常见）
     - **系列讲座**：一个直播间有多个场次（如："肝胆外科系列讲座"，包含5场不同主题的直播）
     - **历史回放**：直播结束后，场次转为回放状态
   
2. **观看进度（progress字段）的语义要求**：
   - `progress` 记录的是"观看到第X秒"，这个进度必须对应**具体的视频内容（session）**
   - 如果关联room_id，当直播间有多个场次时，无法区分是哪个视频的进度
   - 如果同时关联room_id和session_id，则room_id是冗余数据（违反第三范式）

**设计方案对比**：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **方案A：仅关联session_id**<br>（本设计采用） | ✅ progress语义清晰<br>✅ 支持系列讲座<br>✅ 符合数据库范式<br>✅ 避免数据冗余 | ⚠️ 查询直播间维度需JOIN | ✅ 推荐（通用场景） |
| 方案B：仅关联room_id | ✅ 查询直播间维度简单 | ❌ 无法区分具体场次<br>❌ progress语义不清<br>❌ 不支持系列讲座 | ❌ 不推荐 |
| 方案C：同时关联两者 | ✅ 查询灵活 | ❌ 数据冗余<br>❌ 维护复杂<br>❌ 违反数据库范式<br>❌ 一致性风险 | ❌ 不推荐 |

**技术实现考量**：

3. **数据冗余与一致性**：
   - 如果同时存储room_id和session_id，每次记录观看历史时需保证：
     ```
     room_id == (SELECT room_id FROM live_sessions WHERE id = session_id)
     ```
   - 如果live_sessions的room_id发生变更（虽然罕见），会导致历史数据不一致
   - 仅关联session_id，通过外键的 `ON DELETE CASCADE` 自然维护数据完整性

4. **查询性能**：
   - 通过JOIN查询直播间维度的性能完全可接受：
     ```sql
     -- 使用索引 idx_watch_history_user_session 和 live_sessions的主键索引
     SELECT DISTINCT lr.id, lr.title, MAX(wh.watched_at) as last_watched
     FROM watch_history wh
     JOIN live_sessions ls ON wh.session_id = ls.id
     JOIN live_rooms lr ON ls.room_id = lr.id
     WHERE wh.user_id = :user_id AND wh.is_latest = true
     GROUP BY lr.id, lr.title
     ORDER BY last_watched DESC;
     ```
   - PostgreSQL的查询优化器会使用索引，性能瓶颈不在这里
   - 如果真有性能问题，可以通过物化视图或缓存解决，而不是破坏数据设计

#### 2.8.2 查询直播间维度的观看历史

若前端需要展示"用户观看过的直播间列表"，使用以下查询：

```sql
-- 查询用户观看过的直播间（按最后观看时间倒序）
SELECT 
    lr.id AS room_id,
    lr.title AS room_title,
    lr.cover_url,
    MAX(wh.watched_at) AS last_watched_at,
    COUNT(DISTINCT wh.session_id) AS watched_sessions_count
FROM watch_history wh
JOIN live_sessions ls ON wh.session_id = ls.id
JOIN live_rooms lr ON ls.room_id = lr.id
WHERE wh.user_id = :user_id AND wh.is_latest = true
GROUP BY lr.id, lr.title, lr.cover_url
ORDER BY last_watched_at DESC
LIMIT 20;
```

**查询说明**：
- 使用 `is_latest = true` 筛选每个场次的最新观看记录，避免重复统计
- `COUNT(DISTINCT wh.session_id)` 可以统计用户观看了该直播间的多少个场次
- 索引支持：`idx_watch_history_user_session` 和 `idx_watch_history_is_latest`

#### 2.8.3 进度跟踪机制

- `is_latest=true` 标记每个用户对每个场次的最新观看记录
- 前端可据此实现"继续观看"功能（恢复到上次进度）
- 每次用户观看时，将旧记录的 `is_latest` 设为 `false`，新记录设为 `true`

#### 2.8.4 数据库定义

```sql
CREATE TABLE watch_history (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    watched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    progress INT DEFAULT 0,
    extra JSONB NULL,
    is_latest BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 命名的外键约束
    CONSTRAINT fk_watch_history_session_id 
        FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_watch_history_user_session ON watch_history(user_id, session_id);
CREATE INDEX idx_watch_history_watched_at ON watch_history(user_id, watched_at DESC);
CREATE INDEX idx_watch_history_is_latest ON watch_history(user_id, is_latest) 
WHERE is_latest = true;

-- 注释
COMMENT ON TABLE watch_history IS '用户观看历史记录表（记录用户观看的具体直播场次）';
COMMENT ON COLUMN watch_history.user_id IS '用户公开ID（users.public_id），应用层验证';
COMMENT ON COLUMN watch_history.session_id IS '直播场次ID，关联live_sessions表。注：不直接关联room_id，可通过live_sessions.room_id反向查询';
COMMENT ON COLUMN watch_history.progress IS '观看进度（秒），用于实现"继续观看"功能';
COMMENT ON COLUMN watch_history.extra IS 'JSONB格式存储元数据：{device, ip, quality}';
COMMENT ON COLUMN watch_history.is_latest IS '是否为最新记录，用于快速查询用户对某session的最新观看状态（每次观看更新时，将旧记录设为false）';
```

### 2.9 user_subscriptions（订阅提醒表）

```sql
CREATE TYPE subscription_target_type AS ENUM ('room', 'session');

CREATE TABLE user_subscriptions (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    user_id UUID NOT NULL,
    target_id UUID NOT NULL,
    target_type subscription_target_type NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：同一用户对同一目标只能订阅一次
    CONSTRAINT uq_user_subscriptions_user_target 
        UNIQUE(user_id, target_id, target_type)
);

-- 索引
CREATE INDEX idx_user_subscriptions_user_target ON user_subscriptions(user_id, target_id, target_type);
CREATE INDEX idx_user_subscriptions_target ON user_subscriptions(target_type, target_id);
CREATE INDEX idx_user_subscriptions_active ON user_subscriptions(user_id, is_active) 
WHERE is_active = true;

-- 注释
COMMENT ON TABLE user_subscriptions IS '用户订阅开播提醒表（支持订阅房间或单场次）';
COMMENT ON COLUMN user_subscriptions.user_id IS '用户公开ID（users.public_id），应用层验证，JWT Token的sub字段值';
COMMENT ON COLUMN user_subscriptions.target_type IS '订阅目标类型：room=房间，session=单场次';
COMMENT ON COLUMN user_subscriptions.target_id IS '目标ID，根据target_type指向live_rooms.id或live_sessions.id';
COMMENT ON COLUMN user_subscriptions.is_active IS '是否有效：true=已订阅，false=已取消（软删除）';
```

### 2.10 featured_content（首页精选/焦点图表）

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
COMMENT ON COLUMN featured_content.target_type IS '目标类型：room/session/topic/brand/external等';
COMMENT ON COLUMN featured_content.target_id IS '目标ID，根据target_type指向对应表的id';
COMMENT ON COLUMN featured_content.target_url IS '外部链接，优先级高于target_id';
COMMENT ON COLUMN featured_content.start_at IS '上线时间，为空表示立即上线';
COMMENT ON COLUMN featured_content.end_at IS '下线时间，为空表示永久有效';
```

### 2.11 live_sessions表扩展字段

```sql
-- 为 live_sessions 表添加 featured_expert_id 字段
ALTER TABLE live_sessions 
ADD COLUMN featured_expert_id UUID NULL;

-- 添加外键约束（命名）
ALTER TABLE live_sessions
ADD CONSTRAINT fk_live_sessions_featured_expert_id 
    FOREIGN KEY (featured_expert_id) REFERENCES experts(id) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX idx_live_sessions_featured_expert_id ON live_sessions(featured_expert_id)
WHERE featured_expert_id IS NOT NULL;

-- 添加字段注释
COMMENT ON COLUMN live_sessions.featured_expert_id IS '特邀专家ID，用于标识该场次的主讲专家';

-- 为 live_sessions 表添加 summary 字段
ALTER TABLE live_sessions 
ADD COLUMN summary VARCHAR(200);

-- 添加字段注释
COMMENT ON COLUMN live_sessions.summary IS '本场次重点内容摘要（一行），用于卡片展示';
```

### 2.12 notifications（用户通知表）

**设计说明**：

本表用于存储用户通知消息，支持：
1. 订阅提醒（直播即将开始）
2. 系统通知（欢迎消息、公告等）
3. 互动通知（评论、点赞等，未来扩展）

```sql
CREATE TABLE notifications (
    -- 核心标识 (在应用层通过 uuid.uuid4() 生成)
    id UUID PRIMARY KEY,
    
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    notification_type VARCHAR(50) DEFAULT 'system',
    related_id UUID NULL,
    related_type VARCHAR(50) NULL,
    is_read BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_notifications_user_id ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_related ON notifications(related_type, related_id);

-- 注释
COMMENT ON TABLE notifications IS '用户通知表，存储各类通知消息';
COMMENT ON COLUMN notifications.user_id IS '用户公开ID（users.public_id），应用层验证';
COMMENT ON COLUMN notifications.title IS '通知标题（必填）';
COMMENT ON COLUMN notifications.content IS '通知内容（可选）';
COMMENT ON COLUMN notifications.notification_type IS '通知类型：system=系统通知, subscription=订阅提醒, interaction=互动通知';
COMMENT ON COLUMN notifications.related_id IS '关联资源ID（可选），如订阅提醒关联的session_id或room_id';
COMMENT ON COLUMN notifications.related_type IS '关联资源类型（可选）：session, room, topic等';
COMMENT ON COLUMN notifications.is_read IS '是否已读：false=未读，true=已读';
```

### 2.13 live_rooms表扩展字段

**设计说明**：

本节为 `live_rooms` 表添加两个新字段，以支持前端新增的功能需求：
1. `category_id`：全局医学分类ID，用于首页按分类筛选直播间
2. `summary`：直播间简介摘要，用于卡片展示（首页列表、搜索结果等）

```sql
-- 1. 添加 category_id 字段（如果不存在）
ALTER TABLE live_rooms 
ADD COLUMN IF NOT EXISTS category_id UUID NULL;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_live_rooms_category_id ON live_rooms(category_id);

-- 添加字段注释
COMMENT ON COLUMN live_rooms.category_id IS '分类ID，关联categories表（如：肝胆外科、胃肠外科），应用层验证其有效性（is_active=true）';

-- 注意：不添加数据库外键约束，遵循微服务架构原则
-- 在应用层验证 category_id 的存在性和有效性

-- 2. 添加 summary 字段（新增）
ALTER TABLE live_rooms 
ADD COLUMN IF NOT EXISTS summary VARCHAR(255);

-- 添加字段注释
COMMENT ON COLUMN live_rooms.summary IS '直播间简介摘要（一行文本，最多255字符），用于首页卡片、列表页、搜索结果等展示场景';

-- 索引说明：
-- summary 字段通常用于展示，不需要单独索引
-- 如果需要全文搜索，可以考虑：
-- 1. 创建 GIN 索引：CREATE INDEX idx_live_rooms_summary_gin ON live_rooms USING gin(to_tsvector('english', summary));
-- 2. 或使用 Elasticsearch 等外部搜索引擎
```

**字段使用场景**：

| 字段 | 使用场景 | 示例值 |
|------|----------|--------|
| `category_id` | 首页按分类筛选：`GET /api/v1/rooms?category_id=xxx`<br>直播间详情页展示分类标签 | `"c9a0c6a8-..."` (肝胆外科) |
| `summary` | 首页直播间卡片的描述文字<br>列表页的简介<br>搜索结果的摘要 | `"介绍我们即将发布的 v3.0 版本。"` |

**与 live_sessions.summary 的区别**：

- **live_rooms.summary**：描述整个直播间的主题和内容方向（相对固定）
- **live_sessions.summary**：描述单个场次的重点内容（每场次不同）

**示例**：
- 直播间标题：`"肝胆外科微创手术研讨"`
- 直播间summary：`"探讨腹腔镜、机器人辅助等微创技术在肝胆胰脾外科的应用"`
- 某场次summary：`"本期重点：腹腔镜肝切除术的技术要点与并发症处理"`
```

---

## 3. Pydantic Schemas定义

**遵循Pydantic V2语法规范**

### 3.1 Tags Schemas

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator
import uuid
import datetime
from typing import Optional, List
import re

class TagBase(BaseModel):
    """标签基础Schema"""
    name: str = Field(..., min_length=1, max_length=80, description="标签名称")
    slug: Optional[str] = Field(None, max_length=100, description="URL友好标识符")
    description: Optional[str] = Field(None, max_length=500, description="标签描述")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证标签名称：去除首尾空格，检查非法字符"""
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError('标签名称不能包含特殊字符')
        return v
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """验证slug：只允许小写字母、数字和连字符"""
        if v is not None:
            v = v.strip().lower()
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('slug只能包含小写字母、数字和连字符')
        return v

class TagCreate(TagBase):
    """创建标签请求Schema"""
    is_active: Optional[bool] = Field(True, description="是否启用")

class TagUpdate(BaseModel):
    """更新标签请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class TagItem(TagBase):
    """标签响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

class TagListResponse(BaseModel):
    """标签列表响应Schema"""
    code: int = 200
    message: str = "success"
    data: List[TagItem]
    timestamp: datetime.datetime
```

### 3.2 Categories Schemas

```python
class CategoryBase(BaseModel):
    """分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    slug: Optional[str] = Field(None, max_length=120)
    icon: Optional[str] = Field(None, max_length=255, description="图标名称或URL")
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if re.search(r'[<>\'";]', v):
            raise ValueError('分类名称不能包含特殊字符')
        return v

class CategoryCreate(CategoryBase):
    """创建分类请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0, description="排序权重")
    is_active: Optional[bool] = Field(True, description="是否启用")

class CategoryUpdate(BaseModel):
    """更新分类请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class CategoryItem(CategoryBase):
    """分类响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    sort_order: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

class CategoryListResponse(BaseModel):
    """分类列表响应Schema（公开接口，不分页）"""
    code: int = 200
    message: str = "success"
    data: List[CategoryItem]
    timestamp: datetime.datetime

class PaginatedData(BaseModel, Generic[T]):
    """分页数据通用Schema"""
    total: int
    page: int
    size: int
    items: List[T]

class CategoryAdminListResponse(BaseModel):
    """分类列表响应Schema（Admin接口，分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[CategoryItem]
    timestamp: datetime.datetime
```

### 3.3 Brands Schemas

```python
class BrandBase(BaseModel):
    """品牌基础Schema"""
    name: str = Field(..., min_length=1, max_length=150, description="品牌名称")
    slug: Optional[str] = Field(None, max_length=150)
    logo_url: Optional[str] = Field(None, max_length=512, description="品牌Logo URL")
    description: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = Field(None, max_length=255, description="品牌官网")
    
    @field_validator('website_url')
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式"""
        if v is not None:
            v = v.strip()
            if not re.match(r'^https?://', v):
                raise ValueError('网站URL必须以http://或https://开头')
        return v

class BrandCreate(BrandBase):
    """创建品牌请求Schema"""
    sort_order: Optional[int] = Field(0, ge=0)
    is_active: Optional[bool] = Field(True)

class BrandUpdate(BaseModel):
    """更新品牌请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class BrandItem(BrandBase):
    """品牌响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    sort_order: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

# 品牌内容响应（品牌详情+关联专题）
class TopicBriefItem(BaseModel):
    """专题简要信息Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    banner_url: Optional[str] = None

class BrandContentData(BaseModel):
    """品牌内容数据Schema"""
    brand_info: BrandItem
    associated_topics: List[TopicBriefItem]

class BrandContentResponse(BaseModel):
    """品牌内容响应Schema"""
    code: int = 200
    message: str = "success"
    data: BrandContentData
    timestamp: datetime.datetime
```

### 3.4 Experts Schemas

```python
class ExpertBase(BaseModel):
    """专家基础Schema"""
    name: str = Field(..., min_length=1, max_length=120, description="专家姓名")
    title: Optional[str] = Field(None, max_length=120, description="职称")
    hospital: Optional[str] = Field(None, max_length=200, description="所属医院")
    department: Optional[str] = Field(None, max_length=120, description="科室")
    expertise_areas: Optional[str] = Field(None, description="擅长领域")
    bio: Optional[str] = Field(None, max_length=1000, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=512)

class ExpertCreate(ExpertBase):
    """创建专家请求Schema"""
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID（可选）")
    is_featured: Optional[bool] = Field(False, description="是否首页推荐")
    sort_order: Optional[int] = Field(0, ge=0)
    contact_info: Optional[dict] = Field(None, description="联系方式JSONB")

class ExpertUpdate(BaseModel):
    """更新专家请求Schema（部分更新）"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    title: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    expertise_areas: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)

class ExpertItem(ExpertBase):
    """专家响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    is_featured: bool
    sort_order: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

class FeaturedExpertItem(BaseModel):
    """首页推荐专家简要Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    hospital: Optional[str] = None
    avatar_url: Optional[str] = None
```

### 3.5 Session_Tags Schemas

```python
class SessionTagCreate(BaseModel):
    """批量设置标签请求Schema"""
    tag_ids: List[uuid.UUID] = Field(..., min_length=1, description="标签ID列表")
    mode: str = Field("replace", pattern="^(replace|append)$", description="模式：replace=替换，append=追加")

class SessionTagItem(BaseModel):
    """场次-标签关联响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    session_id: uuid.UUID
    tag_id: uuid.UUID
    created_at: datetime.datetime
```

### 3.6 Notifications Schemas

```python
class NotificationItem(BaseModel):
    """通知响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    content: Optional[str] = None
    notification_type: str
    related_id: Optional[uuid.UUID] = None
    related_type: Optional[str] = None
    is_read: bool
    created_at: datetime.datetime

class NotificationListResponse(BaseModel):
    """通知列表响应Schema（分页）"""
    code: int = 200
    message: str = "success"
    data: PaginatedData[NotificationItem]
    timestamp: datetime.datetime

# Admin端Schemas
class NotificationCreateRequest(BaseModel):
    """Admin创建通知请求Schema"""
    user_ids: List[uuid.UUID] = Field(..., description="接收通知的用户ID列表，空列表表示全部用户")
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    notification_type: str = Field(default="system", pattern="^(system|subscription|interaction)$")
    related_id: Optional[uuid.UUID] = None
    related_type: Optional[str] = None

class NotificationBatchCreateResponse(BaseModel):
    """批量创建通知响应Schema"""
    total_created: int
    user_ids: List[uuid.UUID]

class NotificationUpdateRequest(BaseModel):
    """Admin更新通知请求Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None

class NotificationBatchDeleteRequest(BaseModel):
    """批量删除通知请求Schema"""
    notification_ids: Optional[List[uuid.UUID]] = Field(None, description="通知ID列表")
    delete_before: Optional[datetime.datetime] = Field(None, description="删除此日期之前的通知")
    notification_type: Optional[str] = None
    is_read: Optional[bool] = None

    @model_validator(mode='after')
    def check_params(self):
        if not self.notification_ids and not self.delete_before:
            raise ValueError("必须提供 notification_ids 或 delete_before 参数之一")
        return self
```

### 3.7 Homepage & Search Schemas

```python
# Homepage相关Schemas
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
    
    viewer_count: Optional[int] = None
    start_time: Optional[datetime.datetime] = None
    duration_seconds: Optional[int] = None
    play_count: Optional[int] = None

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

# Search相关Schemas
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
```

### 3.8 其他用户相关Schemas

```python
# 用户收藏
class FavoriteCreate(BaseModel):
    """创建收藏请求Schema"""
    room_id: uuid.UUID

class FavoriteItem(BaseModel):
    """收藏响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    room_id: uuid.UUID
    is_active: bool
    created_at: datetime.datetime

# 观看历史
class WatchEventRequest(BaseModel):
    """观看事件上报请求Schema"""
    progress: Optional[int] = Field(None, ge=0, description="观看进度（秒）")
    extra: Optional[dict] = Field(None, description="额外元数据")

class WatchHistoryItem(BaseModel):
    """观看历史响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID
    watched_at: datetime.datetime
    progress: int
    is_latest: bool

# 订阅提醒
class SubscriptionCreate(BaseModel):
    """创建订阅请求Schema"""
    target_id: uuid.UUID
    target_type: str = Field(..., pattern="^(room|session)$")

class SubscriptionItem(BaseModel):
    """订阅响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    target_id: uuid.UUID
    target_type: str
    is_active: bool
    created_at: datetime.datetime

# 首页精选
class FeaturedContentCreate(BaseModel):
    """创建精选内容请求Schema"""
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=512)
    image_url: str = Field(..., max_length=512)
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    target_url: Optional[str] = None
    sort_order: Optional[int] = Field(0, ge=0)
    is_active: Optional[bool] = Field(True)
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None

class FeaturedContentUpdate(BaseModel):
    """更新精选内容请求Schema"""
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

class FeaturedContentItem(BaseModel):
    """精选内容响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    subtitle: Optional[str] = None
    image_url: str
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    target_url: Optional[str] = None
    sort_order: int
    is_active: bool
    start_at: Optional[datetime.datetime] = None
    end_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
```

---

## 4. API接口设计（完整CRUD）

### 4.0 通用错误响应格式

所有接口的错误响应遵循统一格式：

```json
{
  "code": 2002,
  "message": "资源已存在",
  "data": {
    "field": "name",
    "value": "微创手术",
    "error": "标签名称已存在"
  },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

### 4.1 Tags 模块API

#### 4.1.1 获取标签列表（公开）

**Endpoint**: `GET /api/v1/tags`

**描述**: 获取可用标签列表，支持搜索和过滤

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `q` (string, 可选): 标签名称模糊搜索
- `limit` (int, 可选, 默认100, 最大500): 返回数量限制
- `include_inactive` (bool, 可选, 默认false): 是否包含已禁用标签（仅Admin可用）

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "微创手术",
      "slug": "minimally-invasive",
      "description": "有关微创手术的视频与讨论",
      "is_active": true,
      "created_at": "2025-10-22T07:00:00Z",
      "updated_at": "2025-10-22T07:00:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "肝胆外科",
      "slug": "hepatobiliary",
      "description": null,
      "is_active": true,
      "created_at": "2025-10-22T08:00:00Z",
      "updated_at": "2025-10-22T08:00:00Z"
    }
  ],
  "timestamp": "2025-10-23T10:00:00Z"
}
```

**失败响应示例** (`400 Bad Request` - 参数错误):
```json
{
  "code": 4001,
  "message": "参数校验失败",
  "data": {
    "field": "limit",
    "error": "limit参数必须在1-500之间"
  },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

**执行流程**:

1. **参数解析与校验**:
   ```python
   def get_tags_list(
       q: Optional[str] = None,
       limit: int = Query(100, ge=1, le=500),
       include_inactive: bool = False,
       current_user: Optional[User] = Depends(get_current_user_optional)
   ):
   ```
   - 使用 `Query` 验证 `limit` 范围
   - `current_user` 可选，用于判断是否允许 `include_inactive`

2. **权限检查**:
   ```python
   if include_inactive and (not current_user or current_user.role not in ['ADMIN', 'SUPERADMIN']):
       logger.warning(f"非管理员尝试访问禁用标签: user_id={current_user.id if current_user else 'anonymous'}")
       raise ForbiddenException(detail="查看禁用标签需要管理员权限", code=3002)
   ```

3. **构建查询**:
   ```python
   query = select(Tag)
   
   # 默认只返回启用的标签
   if not include_inactive:
       query = query.where(Tag.is_active == True)
   
   # 模糊搜索
   if q:
       query = query.where(Tag.name.ilike(f'%{q}%'))
   
   # 排序和限制
   query = query.order_by(Tag.name.asc()).limit(limit)
   ```

4. **执行查询**:
   ```python
   result = await db.execute(query)
   tags = result.scalars().all()
   ```

5. **日志记录**:
   ```python
   logger.info(f"标签列表查询: q={q}, limit={limit}, count={len(tags)}, user_id={current_user.id if current_user else 'anonymous'}")
   ```

6. **返回响应**:
   ```python
   return APIResponse(
       code=200,
       message="success",
       data=[TagItem.model_validate(tag) for tag in tags],
       timestamp=datetime.utcnow()
   )
   ```

---

#### 4.1.2 创建标签（Admin）

**Endpoint**: `POST /api/v1/admin/tags`

**描述**: 管理员创建新标签

**认证**: 需要JWT Token + `ADMIN` 或 `SUPERADMIN` 角色

**请求头**:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "微创手术",
  "slug": "minimally-invasive",
  "description": "有关微创手术的视频与讨论",
  "is_active": true
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "微创手术",
    "slug": "minimally-invasive",
    "description": "有关微创手术的视频与讨论",
    "is_active": true,
    "created_at": "2025-10-23T10:00:00Z",
    "updated_at": "2025-10-23T10:00:00Z"
  },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

**失败响应示例** (`2002 Conflict` - 名称重复):
```json
{
  "code": 2002,
  "message": "资源已存在",
  "data": {
    "field": "name",
    "value": "微创手术",
    "error": "标签名称已存在"
  },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

**失败响应示例** (`3002 Forbidden` - 权限不足):
```json
{
  "code": 3002,
  "message": "权限不足",
  "data": {
    "required_role": "ADMIN或SUPERADMIN",
    "current_role": "REGULAR"
  },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

**实现流程描述**:

1. 定义FastAPI路由函数，接收Pydantic模型 `TagCreate` 和数据库会话 `db`
2. 通过 `Depends(get_current_user)` 验证JWT Token并提取用户信息，Token无效时抛出 `401 Unauthorized`
3. 检查用户角色是否为 `ADMIN` 或 `SUPERADMIN`，若不是则记录WARNING日志并返回 `3002` 权限不足错误
4. Pydantic自动校验请求体格式（TagCreate模型），包括字段验证器：name去除首尾空格、检查非法字符、slug格式验证
5. 在应用层调用 `uuid.uuid4()` 生成标签ID
6. 查询数据库检查 `name` 唯一性：`SELECT id FROM tags WHERE name = :name`，若名称已存在则记录WARNING日志并返回 `2002` 资源已存在错误
7. 创建 `Tag` 模型实例，填充所有字段信息（id、name、slug、description、is_active）
8. 调用 `db.add()` 将标签对象添加到会话，记录INFO级别日志（tag_id、name、admin_user_id）
9. 调用 `db.commit()` 提交事务，`db.refresh()` 刷新对象以获取数据库生成的时间戳
10. 捕获 `IntegrityError`（唯一约束冲突）并转换为业务异常 `2002`，捕获其他异常转换为系统异常 `1002`
11. 将创建的标签对象序列化为 `TagItem`，构建统一响应结构并返回

---

#### 4.1.3 更新标签（Admin）

**Endpoint**: `PATCH /api/v1/admin/tags/{tag_id}`

**描述**: 管理员部分更新标签信息

**认证**: 需要JWT Token + `ADMIN` 或 `SUPERADMIN` 角色

**请求体** (所有字段可选):
```json
{
  "name": "微创手术（更新）",
  "description": "更新后的描述",
  "is_active": false
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "微创手术（更新）",
    "slug": "minimally-invasive",
    "description": "更新后的描述",
    "is_active": false,
    "created_at": "2025-10-22T07:00:00Z",
    "updated_at": "2025-10-23T10:05:00Z"
  },
  "timestamp": "2025-10-23T10:05:00Z"
}
```

**失败响应示例** (`2001 Not Found` - 标签不存在):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Tag",
    "id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2025-10-23T10:05:00Z"
}
```

**实现流程描述**:

1. 定义FastAPI路由函数，接收路径参数 `tag_id`、Pydantic模型 `TagUpdate` 和数据库会话 `db`
2. 验证JWT Token并检查用户角色是否为 `ADMIN` 或 `SUPERADMIN`，若不是则返回 `3002` 权限不足错误
3. 根据 `tag_id` 查询 `tags` 表：`SELECT * FROM tags WHERE id = :tag_id`，若未找到则记录WARNING日志并返回 `2001` 资源不存在错误
4. Pydantic解析请求体（TagUpdate模型），提取要更新的字段（使用 `exclude_unset=True` 仅获取客户端实际提供的字段）
5. 若更新的字段包含 `name` 且与当前值不同，查询数据库检查新名称的唯一性，若冲突则返回 `2002` 资源已存在错误
6. 遍历更新数据，逐个设置标签对象的属性值
7. 数据库触发器自动更新 `updated_at` 字段为当前时间戳
8. 记录INFO级别日志，包含tag_id和更新的字段列表
9. 调用 `db.commit()` 提交事务，`db.refresh()` 刷新对象以获取最新的 `updated_at`
10. 将更新后的标签对象序列化为 `TagItem`，构建并返回包含更新后数据的成功响应

---

#### 4.1.4 删除标签（Admin）

**Endpoint**: `DELETE /api/v1/admin/tags/{tag_id}`

**描述**: 管理员删除标签（默认软删除，可选硬删除）

**认证**: 
- 软删除：需要 `ADMIN` 或 `SUPERADMIN` 角色
- 硬删除：需要 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `hard_delete` (bool, 可选, 默认false): 是否硬删除（需SUPERADMIN）

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "soft_deleted",
    "deleted_at": "2025-10-23T10:10:00Z"
  },
  "timestamp": "2025-10-23T10:10:00Z"
}
```

**失败响应示例** (`2003 Conflict` - 被引用无法删除):
```json
{
  "code": 2003,
  "message": "操作被禁止",
  "data": {
    "resource": "Tag",
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "reason": "标签被3个直播场次引用，无法删除",
    "referenced_count": 3
  },
  "timestamp": "2025-10-23T10:10:00Z"
}
```

**实现流程描述**:

1. 定义FastAPI路由函数，接收路径参数 `tag_id` 和Query参数 `hard_delete`（默认false）
2. 验证JWT Token并提取用户角色，软删除需要 `ADMIN` 或 `SUPERADMIN` 权限，硬删除需要 `SUPERADMIN` 权限，权限不足时返回 `3002` 错误
3. 根据 `tag_id` 查询标签对象，若不存在则返回 `2001` 资源不存在错误
4. 检查引用关系：查询 `session_tags` 表统计该标签被多少个直播场次引用
5. 若存在引用且为硬删除，记录WARNING日志并返回 `2003` 操作被禁止错误（包含引用数量）；若为软删除则仅记录INFO日志继续执行
6. 根据 `hard_delete` 参数执行不同删除操作：硬删除调用 `db.delete()` 并记录ERROR级别日志，软删除设置 `is_active=false` 并记录WARNING级别日志
7. 调用 `db.commit()` 提交事务
8. 构建删除状态响应数据（包含id、status、deleted_at）
9. 返回包含删除状态的成功响应

---

### 4.2 Categories 模块API

#### 4.2.1 获取分类列表（公开）

**Endpoint**: `GET /api/v1/categories`

**描述**: 获取所有可用的医学分类列表（按 `sort_order` 升序）

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `limit` (int, 可选, 默认100): 最大返回数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "肝胆外科",
      "slug": "hepatobiliary-surgery",
      "icon": "icon-liver",
      "description": "肝胆胰脾外科疾病诊疗",
      "sort_order": 0,
      "is_active": true,
      "created_at": "2025-10-20T10:00:00Z",
      "updated_at": "2025-10-20T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "胃肠外科",
      "slug": "gastrointestinal-surgery",
      "icon": "icon-stomach",
      "description": "胃肠道肿瘤及疾病诊疗",
      "sort_order": 1,
      "is_active": true,
      "created_at": "2025-10-20T10:05:00Z",
      "updated_at": "2025-10-20T10:05:00Z"
    }
  ],
  "timestamp": "2025-10-23T11:00:00Z"
}
```

**执行流程**:

1. 构建查询语句，筛选 `is_active = true` 的分类
2. 按 `sort_order` 升序排序
3. 应用 `limit` 参数（默认100，最大500）
4. 执行查询并获取结果列表
5. 将查询结果序列化为 `CategoryItem` 列表
6. 构建并返回包含分类列表的成功响应

---

#### 4.2.2 创建分类（Admin）

**Endpoint**: `POST /api/v1/admin/categories`

**描述**: 管理员创建新的医学分类

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求头**:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "骨科",
  "slug": "orthopedics",
  "icon": "icon-bone",
  "description": "骨关节疾病诊疗",
  "sort_order": 10,
  "is_active": true
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "骨科",
    "slug": "orthopedics",
    "icon": "icon-bone",
    "description": "骨关节疾病诊疗",
    "sort_order": 10,
    "is_active": true,
    "created_at": "2025-10-23T11:10:00Z",
    "updated_at": "2025-10-23T11:10:00Z"
  },
  "timestamp": "2025-10-23T11:10:00Z"
}
```

**失败响应示例** (`2002 Conflict` - 分类名称已存在):
```json
{
  "code": 2002,
  "message": "资源已存在",
  "data": {
    "resource": "Category",
    "field": "name",
    "value": "骨科",
    "reason": "分类名称已存在"
  },
  "timestamp": "2025-10-23T11:10:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取用户信息（通过 `Depends(get_current_user)`）
2. 检查用户角色是否为 `ADMIN` 或 `SUPERADMIN`，若不是则返回 `3002` 权限不足
3. Pydantic自动校验请求体格式（CategoryCreate模型），包括字段验证器
4. 在应用层调用 `uuid.uuid4()` 生成分类ID
5. 查询数据库检查 `name` 唯一性：`SELECT id FROM categories WHERE name = :name`
6. 若名称已存在，记录警告日志并返回 `2002` 资源已存在错误
7. 创建 `Category` 模型实例，填充所有字段信息
8. 调用 `db.add()` 将分类对象添加到会话
9. 记录INFO级别日志：分类创建操作及管理员ID
10. 调用 `db.commit()` 提交事务，调用 `db.refresh()` 刷新对象
11. 捕获数据库IntegrityError（唯一约束冲突）并转换为业务异常
12. 将创建的分类对象序列化为 `CategoryItem`
13. 构建并返回包含新分类数据的成功响应

---

#### 4.2.3 获取分类列表（Admin分页）

**Endpoint**: `GET /api/v1/admin/categories`

**描述**: 管理员分页获取所有分类（包括已禁用的）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码，从1开始
- `size` (int, 可选, 默认10): 每页数量，最大100
- `sort` (string, 可选, 默认`sort_order:asc`): 排序规则
- `name` (string, 可选): 按名称模糊搜索
- `is_active` (bool, 可选): 筛选激活状态

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 25,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "肝胆外科",
        "slug": "hepatobiliary-surgery",
        "icon": "icon-liver",
        "description": "肝胆胰脾外科疾病诊疗",
        "sort_order": 0,
        "is_active": true,
        "created_at": "2025-10-20T10:00:00Z",
        "updated_at": "2025-10-20T10:00:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T11:15:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 构建基础查询：`SELECT * FROM categories`
3. 根据查询参数添加筛选条件（`name` 使用 `ILIKE` 模糊匹配，`is_active` 精确匹配）
4. 执行 `COUNT(*)` 查询获取筛选后的总记录数
5. 解析 `sort` 参数并应用排序（如 `sort_order:asc` 或 `created_at:desc`）
6. 计算分页的 `offset` 值：`(page - 1) * size`
7. 应用 `LIMIT` 和 `OFFSET` 子句进行分页
8. 执行查询获取当前页的分类列表
9. 将结果序列化为 `CategoryItem` 列表
10. 构建分页响应数据结构
11. 返回符合分页格式的成功响应

---

#### 4.2.4 获取单个分类详情（Admin）

**Endpoint**: `GET /api/v1/admin/categories/{category_id}`

**描述**: 管理员获取指定分类的完整信息

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "肝胆外科",
    "slug": "hepatobiliary-surgery",
    "icon": "icon-liver",
    "description": "肝胆胰脾外科疾病诊疗",
    "sort_order": 0,
    "is_active": true,
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-23T10:30:00Z"
  },
  "timestamp": "2025-10-23T11:20:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Category",
    "id": "non-existent-uuid"
  },
  "timestamp": "2025-10-23T11:20:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 根据路径参数 `category_id` 查询 `categories` 表
3. 若查询结果为空，记录DEBUG日志并返回 `2001` 资源不存在错误
4. 若找到分类，将其序列化为 `CategoryItem`
5. 构建并返回包含分类详情的成功响应

---

#### 4.2.5 更新分类（Admin）

**Endpoint**: `PATCH /api/v1/admin/categories/{category_id}`

**描述**: 管理员部分更新分类信息

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "description": "肝胆胰脾外科疾病诊疗（更新）",
  "sort_order": 5,
  "is_active": true
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "肝胆外科",
    "slug": "hepatobiliary-surgery",
    "icon": "icon-liver",
    "description": "肝胆胰脾外科疾病诊疗（更新）",
    "sort_order": 5,
    "is_active": true,
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-23T11:25:00Z"
  },
  "timestamp": "2025-10-23T11:25:00Z"
}
```

**失败响应示例** (`2002 Conflict` - 名称冲突):
```json
{
  "code": 2002,
  "message": "资源已存在",
  "data": {
    "resource": "Category",
    "field": "name",
    "value": "胃肠外科",
    "reason": "分类名称已被其他分类使用"
  },
  "timestamp": "2025-10-23T11:25:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 根据 `category_id` 查询分类对象，若不存在返回 `2001`
3. Pydantic解析请求体（CategoryUpdate模型），提取要更新的字段
4. 若更新 `name` 字段，查询数据库检查唯一性（排除当前分类自身）
5. 若名称被其他分类占用，返回 `2002` 资源已存在错误
6. 遍历更新数据，逐个设置分类对象的属性值
7. 数据库触发器自动更新 `updated_at` 字段
8. 记录INFO日志：分类更新操作、字段列表、管理员ID
9. 调用 `db.commit()` 提交事务
10. 调用 `db.refresh()` 刷新对象以获取最新的 `updated_at`
11. 将更新后的分类序列化为 `CategoryItem`
12. 构建并返回包含更新后数据的成功响应

---

#### 4.2.6 删除分类（Admin）

**Endpoint**: `DELETE /api/v1/admin/categories/{category_id}`

**描述**: 管理员删除分类（默认软删除，可选硬删除）

**认证**: 
- 软删除：需要 `ADMIN` 或 `SUPERADMIN` 角色
- 硬删除：需要 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `hard_delete` (bool, 可选, 默认false): 是否硬删除（需SUPERADMIN）

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "soft_deleted",
    "deleted_at": "2025-10-23T11:30:00Z"
  },
  "timestamp": "2025-10-23T11:30:00Z"
}
```

**失败响应示例** (`2003 Conflict` - 被引用):
```json
{
  "code": 2003,
  "message": "操作被禁止",
  "data": {
    "resource": "Category",
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "reason": "分类被15个直播间引用，无法删除",
    "referenced_count": 15
  },
  "timestamp": "2025-10-23T11:30:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取用户角色
2. 检查权限：软删除需ADMIN或SUPERADMIN，硬删除需SUPERADMIN
3. 若权限不足，返回 `3002` 权限不足错误
4. 根据 `category_id` 查询分类对象，若不存在返回 `2001`
5. 检查引用关系：查询 `live_rooms` 表中 `category_id` 等于当前分类ID的记录数
6. 若存在引用：
   - 硬删除时：记录WARNING日志并返回 `2003` 操作被禁止错误
   - 软删除时：记录INFO日志继续执行
7. 执行删除操作：
   - 硬删除：调用 `db.delete()` 删除记录，记录ERROR级别日志
   - 软删除：设置 `is_active = false`，记录WARNING级别日志
8. 调用 `db.commit()` 提交事务
9. 构建删除状态响应数据
10. 返回包含删除状态的成功响应

---

### 4.3 Brands 模块API

#### 4.3.1 获取品牌列表（公开）

**Endpoint**: `GET /api/v1/brands`

**描述**: 获取所有可用的合作品牌列表（按 `sort_order` 升序）

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `limit` (int, 可选, 默认100): 最大返回数量
- `q` (string, 可选): 按品牌名称模糊搜索

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "迈瑞医疗",
      "slug": "mindray",
      "logo_url": "/media/brands/mindray-logo.png",
      "description": "医疗器械行业领军企业",
      "website_url": "https://www.mindray.com",
      "sort_order": 0,
      "is_active": true,
      "created_at": "2025-10-20T14:00:00Z",
      "updated_at": "2025-10-20T14:00:00Z"
    }
  ],
  "timestamp": "2025-10-23T12:00:00Z"
}
```

**执行流程**:

1. 构建基础查询：`SELECT * FROM brands WHERE is_active = true`
2. 若提供 `q` 参数，添加条件：`name ILIKE '%q%'`
3. 按 `sort_order` 升序排序
4. 应用 `limit` 参数（默认100，最大500）
5. 执行查询并获取品牌列表
6. 将结果序列化为 `BrandItem` 列表
7. 构建并返回包含品牌列表的成功响应

---

#### 4.3.2 获取品牌详情及关联专题（公开）

**Endpoint**: `GET /api/v1/brands/{brand_id}/content`

**描述**: 获取品牌详细信息及其赞助/关联的所有专题

**认证**: 公开访问，无需JWT Token

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "brand_info": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "迈瑞医疗",
      "logo_url": "/media/brands/mindray-logo.png",
      "description": "医疗器械行业领军企业",
      "website_url": "https://www.mindray.com"
    },
    "associated_topics": [
      {
        "id": "topic_uuid_1",
        "title": "医疗设备创新论坛",
        "banner_url": "/media/topics/banner1.jpg",
        "status": "published",
        "created_at": "2025-10-18T10:00:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T12:05:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Brand",
    "id": "non-existent-uuid"
  },
  "timestamp": "2025-10-23T12:05:00Z"
}
```

**执行流程**:

1. 根据 `brand_id` 查询 `brands` 表获取品牌基本信息
2. 若品牌不存在或 `is_active = false`，返回 `2001` 资源不存在错误
3. 查询关联专题：使用 `brand_topics` 表JOIN `topics` 表
   - 条件：`brand_topics.brand_id = :brand_id`
   - 筛选：`topics.status = 'published'`（仅返回已发布的专题）
4. 按专题的 `created_at` 降序排序
5. 将品牌信息序列化为 `BrandItem`
6. 将关联专题列表序列化为 `TopicBriefItem` 列表
7. 构建组合响应数据（品牌信息 + 关联专题）
8. 返回包含完整内容的成功响应

---

#### 4.3.3 创建品牌（Admin）

**Endpoint**: `POST /api/v1/admin/brands`

**描述**: 管理员创建新的合作品牌

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "name": "威高集团",
  "slug": "weigao",
  "logo_url": "/media/brands/weigao-logo.png",
  "description": "医疗器械与药品研发生产企业",
  "website_url": "https://www.weigaogroup.com",
  "sort_order": 10,
  "is_active": true
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "name": "威高集团",
    "slug": "weigao",
    "logo_url": "/media/brands/weigao-logo.png",
    "description": "医疗器械与药品研发生产企业",
    "website_url": "https://www.weigaogroup.com",
    "sort_order": 10,
    "is_active": true,
    "created_at": "2025-10-23T12:10:00Z",
    "updated_at": "2025-10-23T12:10:00Z"
  },
  "timestamp": "2025-10-23T12:10:00Z"
}
```

**失败响应示例** (`2002 Conflict`):
```json
{
  "code": 2002,
  "message": "资源已存在",
  "data": {
    "resource": "Brand",
    "field": "name",
    "value": "威高集团",
    "reason": "品牌名称已存在"
  },
  "timestamp": "2025-10-23T12:10:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. Pydantic校验请求体（BrandCreate模型），包括字段验证
3. 在应用层生成品牌UUID
4. 查询数据库检查 `name` 唯一性
5. 若名称已存在，返回 `2002` 资源已存在错误
6. 创建 `Brand` 模型实例并填充所有字段
7. 调用 `db.add()` 添加到会话
8. 记录INFO日志：品牌创建操作及管理员ID
9. 提交事务并刷新对象
10. 序列化为 `BrandItem` 并返回成功响应

---

#### 4.3.4 获取品牌列表（Admin分页）

**Endpoint**: `GET /api/v1/admin/brands`

**描述**: 管理员分页获取所有品牌（包括已禁用的）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量
- `sort` (string, 可选, 默认`sort_order:asc`): 排序规则
- `name` (string, 可选): 按名称模糊搜索
- `is_active` (bool, 可选): 筛选激活状态

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 8,
    "page": 1,
    "size": 10,
    "items": [...]
  },
  "timestamp": "2025-10-23T12:15:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 构建基础查询并添加筛选条件
3. 执行COUNT查询获取总数
4. 应用排序和分页
5. 执行查询获取当前页数据
6. 序列化并返回分页响应

---

#### 4.3.5 获取单个品牌详情（Admin）

**Endpoint**: `GET /api/v1/admin/brands/{brand_id}`

**描述**: 管理员获取指定品牌的完整信息

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "迈瑞医疗",
    "slug": "mindray",
    "logo_url": "/media/brands/mindray-logo.png",
    "description": "医疗器械行业领军企业",
    "website_url": "https://www.mindray.com",
    "sort_order": 0,
    "is_active": true,
    "created_at": "2025-10-20T14:00:00Z",
    "updated_at": "2025-10-23T11:00:00Z"
  },
  "timestamp": "2025-10-23T12:20:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 根据 `brand_id` 查询品牌
3. 若不存在返回 `2001`
4. 序列化并返回品牌详情

---

#### 4.3.6 更新品牌（Admin）

**Endpoint**: `PATCH /api/v1/admin/brands/{brand_id}`

**描述**: 管理员部分更新品牌信息

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "description": "医疗器械行业领军企业（更新）",
  "sort_order": 1
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "迈瑞医疗",
    "description": "医疗器械行业领军企业（更新）",
    "sort_order": 1,
    "updated_at": "2025-10-23T12:25:00Z"
  },
  "timestamp": "2025-10-23T12:25:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 查询品牌对象，若不存在返回 `2001`
3. 解析更新字段，若更新 `name` 则检查唯一性
4. 遍历并更新对象属性
5. 触发器自动更新 `updated_at`
6. 提交事务并刷新对象
7. 序列化并返回更新后的品牌信息

---

#### 4.3.7 删除品牌（Admin）

**Endpoint**: `DELETE /api/v1/admin/brands/{brand_id}`

**描述**: 管理员删除品牌（默认软删除）

**认证**:
- 软删除：需要 `ADMIN` 或 `SUPERADMIN` 角色
- 硬删除：需要 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `hard_delete` (bool, 可选, 默认false): 是否硬删除

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "soft_deleted",
    "deleted_at": "2025-10-23T12:30:00Z"
  },
  "timestamp": "2025-10-23T12:30:00Z"
}
```

**失败响应示例** (`2003 Conflict`):
```json
{
  "code": 2003,
  "message": "操作被禁止",
  "data": {
    "resource": "Brand",
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "reason": "品牌被3个专题引用，无法删除",
    "referenced_count": 3
  },
  "timestamp": "2025-10-23T12:30:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查权限（硬删除需SUPERADMIN）
2. 查询品牌对象，若不存在返回 `2001`
3. 检查引用关系：查询 `brand_topics` 表中的关联记录数
4. 若存在引用且为硬删除，返回 `2003` 操作被禁止
5. 执行删除：硬删除调用 `db.delete()`，软删除设置 `is_active=false`
6. 记录相应级别的日志
7. 提交事务并返回删除状态

---

### 4.4 Brand_Topics 模块API（品牌-专题关联管理）

#### 4.4.1 批量关联专题到品牌（Admin）

**Endpoint**: `POST /api/v1/admin/brands/{brand_id}/topics`

**描述**: 管理员为指定品牌批量添加关联专题

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "topic_ids": [
    "topic_uuid_1",
    "topic_uuid_2",
    "topic_uuid_3"
  ]
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "brand_id": "660e8400-e29b-41d4-a716-446655440001",
    "added_count": 3,
    "topic_ids": [
      "topic_uuid_1",
      "topic_uuid_2",
      "topic_uuid_3"
    ]
  },
  "timestamp": "2025-10-23T12:40:00Z"
}
```

**失败响应示例** (`4001 Validation Error`):
```json
{
  "code": 4001,
  "message": "参数校验失败",
  "data": {
    "field": "topic_ids",
    "invalid_ids": ["topic_uuid_999"],
    "reason": "部分专题ID不存在"
  },
  "timestamp": "2025-10-23T12:40:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 根据 `brand_id` 查询品牌，确认存在且 `is_active=true`
3. 若品牌不存在，返回 `2001` 资源不存在错误
4. 批量查询 `topics` 表，验证所有 `topic_ids` 是否存在
5. 若部分topic_id不存在，记录详细信息并返回 `4001` 参数校验失败
6. 批量插入 `brand_topics` 关联记录
   - 使用 `INSERT ... ON CONFLICT (brand_id, topic_id) DO NOTHING` 保证幂等性
   - 避免重复关联导致主键冲突
7. 记录INFO日志：关联操作、品牌ID、专题数量、管理员ID
8. 提交事务
9. 查询并统计实际新增的关联数量
10. 构建响应数据（品牌ID + 新增数量 + 专题ID列表）
11. 返回成功响应

---

#### 4.4.2 解除单个品牌-专题关联（Admin）

**Endpoint**: `DELETE /api/v1/admin/brands/{brand_id}/topics/{topic_id}`

**描述**: 管理员删除指定的品牌-专题关联关系

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "brand_id": "660e8400-e29b-41d4-a716-446655440001",
    "topic_id": "topic_uuid_1",
    "status": "deleted"
  },
  "timestamp": "2025-10-23T12:45:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "BrandTopic",
    "brand_id": "660e8400-e29b-41d4-a716-446655440001",
    "topic_id": "topic_uuid_999",
    "reason": "关联关系不存在"
  },
  "timestamp": "2025-10-23T12:45:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 查询 `brand_topics` 表，条件：`brand_id=:brand_id AND topic_id=:topic_id`
3. 若关联记录不存在，返回 `2001` 资源不存在错误
4. 调用 `db.delete()` 删除关联记录（硬删除，关联表无需软删除）
5. 记录INFO日志：解除关联操作、品牌ID、专题ID、管理员ID
6. 提交事务
7. 构建删除状态响应
8. 返回成功响应

---

#### 4.4.3 获取品牌的关联专题列表（Admin）

**Endpoint**: `GET /api/v1/admin/brands/{brand_id}/topics`

**描述**: 管理员获取指定品牌关联的所有专题

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 5,
    "page": 1,
    "size": 10,
    "items": [
      {
        "topic_id": "topic_uuid_1",
        "topic_title": "医疗设备创新论坛",
        "topic_status": "published",
        "associated_at": "2025-10-20T15:00:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T12:50:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 验证 `brand_id` 对应的品牌存在
3. 构建联表查询：`brand_topics bt JOIN topics t ON bt.topic_id = t.id WHERE bt.brand_id = :brand_id`
4. 执行COUNT查询获取总关联数
5. 应用分页（LIMIT和OFFSET）
6. 执行查询获取当前页的专题信息
7. 按 `brand_topics.created_at` 降序排序
8. 将结果序列化为包含专题信息的列表
9. 构建分页响应
10. 返回成功响应

---

### 4.5 Experts 模块API

#### 4.5.1 获取推荐专家列表（公开）

**Endpoint**: `GET /api/v1/featured-experts`

**描述**: 获取首页推荐的特色专家列表（按 `sort_order` 排序）

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `limit` (int, 可选, 默认10, 最大50): 返回数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "name": "房树强",
      "title": "主任医师、教授",
      "hospital": "北京大学人民医院",
      "department": "肝胆外科",
      "expertise_areas": "肝胆胰脾外科,微创手术",
      "bio": "从事肝胆外科临床工作30余年...",
      "avatar_url": "/media/experts/fangshuqiang.jpg",
      "is_featured": true,
      "sort_order": 0
    }
  ],
  "timestamp": "2025-10-23T13:00:00Z"
}
```

**执行流程**:

1. 构建查询：`SELECT * FROM experts WHERE is_featured = true`
2. 按 `sort_order` 升序、`created_at` 降序排序
3. 应用 `limit` 参数（默认10，最大50）
4. 执行查询获取专家列表
5. 将结果序列化为 `FeaturedExpertItem` 列表（隐藏 `contact_info` 等敏感字段）
6. 构建并返回包含专家列表的成功响应

---

#### 4.5.2 获取专家详情及关联内容（公开）

**Endpoint**: `GET /api/v1/professors/{expert_id}/content`

**描述**: 获取专家详细信息及其主讲的所有直播场次（分页）

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "expert_info": {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "name": "房树强",
      "title": "主任医师、教授",
      "hospital": "北京大学人民医院",
      "department": "肝胆外科",
      "expertise_areas": "肝胆胰脾外科,微创手术",
      "bio": "从事肝胆外科临床工作30余年...",
      "avatar_url": "/media/experts/fangshuqiang.jpg"
    },
    "sessions": {
      "total": 15,
      "page": 1,
      "size": 10,
      "items": [
        {
          "id": "session_uuid_1",
          "room_title": "肝胆外科微创手术研讨",
          "summary": "探讨腹腔镜在肝切除术中的应用",
          "status": "ready",
          "start_time": "2025-10-20T14:00:00Z",
          "cover_url": "/media/rooms/xxx/cover.jpg"
        }
      ]
    }
  },
  "timestamp": "2025-10-23T13:05:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Expert",
    "id": "non-existent-uuid"
  },
  "timestamp": "2025-10-23T13:05:00Z"
}
```

**执行流程**:

1. 根据 `expert_id` 查询 `experts` 表获取专家基本信息
2. 若专家不存在，返回 `2001` 资源不存在错误
3. 查询关联直播场次：
   - 查询 `live_sessions ls JOIN live_rooms lr ON ls.room_id = lr.id`
   - 条件：`ls.featured_expert_id = :expert_id`
   - 使用索引：`idx_live_sessions_featured_expert_id`
4. 使用 `joinedload` 预加载关联数据（room, statistics），避免N+1查询
5. 执行COUNT查询获取该专家的总场次数
6. 按 `start_time` 降序排序（最新的在前）
7. 应用分页（LIMIT和OFFSET）
8. 执行查询获取当前页的场次列表
9. 将专家信息序列化为 `ExpertItem`（隐藏 `contact_info` 敏感字段）
10. 将场次列表序列化为 `SessionBriefItem` 列表
11. 构建组合响应数据（专家信息 + 分页的场次列表）
12. 返回包含完整内容的成功响应

---

#### 4.5.3 创建专家（Admin）

**Endpoint**: `POST /api/v1/admin/experts`

**描述**: 管理员创建新的专家信息

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "user_id": "user_public_uuid",
  "name": "李明",
  "title": "副主任医师",
  "hospital": "上海交通大学医学院附属瑞金医院",
  "department": "普外科",
  "expertise_areas": "胃肠肿瘤,腹腔镜手术",
  "bio": "擅长胃肠道肿瘤的诊断与治疗...",
  "avatar_url": "/media/experts/liming.jpg",
  "is_featured": true,
  "sort_order": 5
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "user_id": "user_public_uuid",
    "name": "李明",
    "title": "副主任医师",
    "hospital": "上海交通大学医学院附属瑞金医院",
    "department": "普外科",
    "expertise_areas": "胃肠肿瘤,腹腔镜手术",
    "bio": "擅长胃肠道肿瘤的诊断与治疗...",
    "avatar_url": "/media/experts/liming.jpg",
    "is_featured": true,
    "sort_order": 5,
    "created_at": "2025-10-23T13:10:00Z",
    "updated_at": "2025-10-23T13:10:00Z"
  },
  "timestamp": "2025-10-23T13:10:00Z"
}
```

**失败响应示例** (`2004 Conflict` - user_id已绑定):
```json
{
  "code": 2004,
  "message": "业务逻辑错误",
  "data": {
    "field": "user_id",
    "value": "user_public_uuid",
    "reason": "该用户已绑定到其他专家档案"
  },
  "timestamp": "2025-10-23T13:10:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. Pydantic校验请求体（ExpertCreate模型）
3. 在应用层生成专家UUID
4. 若请求中提供了 `user_id`：
   - 查询 `users` 表验证用户存在：`SELECT public_id FROM users WHERE public_id = :user_id`
   - 若用户不存在，返回 `4001` 参数校验失败（无效的user_id）
   - 查询 `experts` 表检查该 `user_id` 是否已被绑定：`SELECT id FROM experts WHERE user_id = :user_id`
   - 若已被其他专家绑定，返回 `2004` 业务逻辑错误（user_id已绑定）
5. 创建 `Expert` 模型实例并填充所有字段
6. 调用 `db.add()` 添加到会话
7. 记录INFO日志：专家创建操作、专家名称、管理员ID
8. 提交事务并刷新对象
9. 捕获 `IntegrityError`（唯一约束冲突）并转换为业务异常
10. 将创建的专家序列化为 `ExpertItem`
11. 构建并返回成功响应

---

#### 4.5.4 获取专家列表（Admin分页）

**Endpoint**: `GET /api/v1/admin/experts`

**描述**: 管理员分页获取所有专家

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量
- `sort` (string, 可选): 排序规则
- `name` (string, 可选): 按姓名模糊搜索
- `is_featured` (bool, 可选): 筛选推荐状态
- `hospital` (string, 可选): 按医院筛选

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 42,
    "page": 1,
    "size": 10,
    "items": [...]
  },
  "timestamp": "2025-10-23T13:15:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 构建基础查询：`SELECT * FROM experts`
3. 根据查询参数添加筛选条件
   - `name` 使用 `ILIKE '%name%'` 模糊匹配
   - `hospital` 精确匹配或模糊匹配（根据业务需求）
   - `is_featured` 精确匹配
4. 执行COUNT查询获取筛选后的总数
5. 解析 `sort` 参数（默认 `sort_order:asc,created_at:desc`）
6. 应用排序和分页
7. 执行查询获取当前页数据
8. 将结果序列化为 `ExpertItem` 列表
9. 构建分页响应
10. 返回成功响应

---

#### 4.5.5 更新专家信息（Admin）

**Endpoint**: `PATCH /api/v1/admin/experts/{expert_id}`

**描述**: 管理员部分更新专家信息

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "bio": "擅长胃肠道肿瘤的诊断与治疗（更新）",
  "is_featured": true,
  "sort_order": 3
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "李明",
    "bio": "擅长胃肠道肿瘤的诊断与治疗（更新）",
    "is_featured": true,
    "sort_order": 3,
    "updated_at": "2025-10-23T13:20:00Z"
  },
  "timestamp": "2025-10-23T13:20:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 根据 `expert_id` 查询专家对象，若不存在返回 `2001`
3. Pydantic解析更新字段（ExpertUpdate模型）
4. 若更新 `user_id` 字段：
   - 验证新的 `user_id` 存在于 `users` 表
   - 检查该 `user_id` 未被其他专家绑定
   - 若冲突，返回 `2004` 业务逻辑错误
5. 遍历更新数据，设置专家对象的属性值
6. 触发器自动更新 `updated_at`
7. 记录INFO日志：专家更新操作、字段列表、管理员ID
8. 提交事务并刷新对象
9. 序列化并返回更新后的专家信息

---

#### 4.5.6 删除专家（Admin）

**Endpoint**: `DELETE /api/v1/admin/experts/{expert_id}`

**描述**: 管理员删除专家（软删除）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "status": "deleted",
    "deleted_at": "2025-10-23T13:25:00Z"
  },
  "timestamp": "2025-10-23T13:25:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 根据 `expert_id` 查询专家对象，若不存在返回 `2001`
3. 由于外键设置为 `ON DELETE SET NULL`，删除专家不会影响已关联的直播场次
4. 关联的 `live_sessions.featured_expert_id` 会自动设置为 `NULL`
5. 建议使用软删除：设置 `is_featured=false`（保留历史数据）
6. 或执行硬删除：调用 `db.delete()` 物理删除记录
7. 记录WARNING或ERROR级别日志
8. 提交事务
9. 构建删除状态响应
10. 返回成功响应

---

### 4.6 Session_Tags 模块API（直播场次-标签关联管理）

#### 4.6.1 为直播场次批量设置标签（Admin）

**Endpoint**: `POST /api/v1/admin/sessions/{session_id}/tags`

**描述**: 管理员为指定直播场次批量设置标签

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "tag_ids": [
    "tag_uuid_1",
    "tag_uuid_2",
    "tag_uuid_3"
  ],
  "mode": "replace"
}
```

**字段说明**:
- `tag_ids` (array, required): 标签UUID列表
- `mode` (string, required): 操作模式
  - `replace`: 替换模式，先删除现有标签再添加新标签
  - `append`: 追加模式，仅添加新标签，保留现有标签

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "session_id": "session_uuid_1",
    "mode": "replace",
    "tags": [
      {
        "id": "tag_uuid_1",
        "name": "微创手术"
      },
      {
        "id": "tag_uuid_2",
        "name": "病例讨论"
      },
      {
        "id": "tag_uuid_3",
        "name": "肝胆外科"
      }
    ]
  },
  "timestamp": "2025-10-23T13:30:00Z"
}
```

**失败响应示例** (`4001 Validation Error`):
```json
{
  "code": 4001,
  "message": "参数校验失败",
  "data": {
    "field": "tag_ids",
    "invalid_ids": ["tag_uuid_999"],
    "reason": "部分标签ID不存在或已禁用"
  },
  "timestamp": "2025-10-23T13:30:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 根据 `session_id` 查询直播场次，确认存在
3. 若场次不存在，返回 `2001` 资源不存在错误
4. 批量查询 `tags` 表，验证所有 `tag_ids` 是否存在且 `is_active=true`
5. 若部分tag_id无效，返回 `4001` 参数校验失败，并列出无效的ID列表
6. 根据 `mode` 参数执行不同操作：
   - **replace模式**：
     - 在事务内先删除现有关联：`DELETE FROM session_tags WHERE session_id = :session_id`
     - 然后批量插入新的关联记录
   - **append模式**：
     - 直接批量插入新的关联记录
     - 使用 `INSERT ... ON CONFLICT (session_id, tag_id) DO NOTHING` 避免重复
7. 记录INFO日志：标签设置操作、场次ID、标签数量、模式、管理员ID
8. 提交事务
9. 查询并返回该场次的最终标签列表
10. 构建响应数据（包含场次ID、模式、完整标签列表）
11. 返回成功响应

---

#### 4.6.2 删除直播场次的单个标签（Admin）

**Endpoint**: `DELETE /api/v1/admin/sessions/{session_id}/tags/{tag_id}`

**描述**: 管理员删除直播场次的指定标签关联

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "session_id": "session_uuid_1",
    "tag_id": "tag_uuid_1",
    "status": "deleted"
  },
  "timestamp": "2025-10-23T13:35:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "SessionTag",
    "session_id": "session_uuid_1",
    "tag_id": "tag_uuid_999",
    "reason": "该场次未关联此标签"
  },
  "timestamp": "2025-10-23T13:35:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 查询 `session_tags` 表，条件：`session_id=:session_id AND tag_id=:tag_id`
3. 若关联记录不存在，返回 `2001` 资源不存在错误
4. 调用 `db.delete()` 删除关联记录（硬删除）
5. 记录INFO日志：解除标签关联、场次ID、标签ID、管理员ID
6. 提交事务
7. 构建删除状态响应
8. 返回成功响应

---

#### 4.6.3 获取直播场次的标签列表（公开）

**Endpoint**: `GET /api/v1/sessions/{session_id}/tags`

**描述**: 获取指定直播场次的所有标签

**认证**: 公开访问，无需JWT Token

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "tag_uuid_1",
      "name": "微创手术",
      "slug": "minimally-invasive",
      "description": "有关微创手术的视频与讨论"
    },
    {
      "id": "tag_uuid_2",
      "name": "病例讨论",
      "slug": "case-discussion",
      "description": null
    }
  ],
  "timestamp": "2025-10-23T13:40:00Z"
}
```

**执行流程**:

1. 根据 `session_id` 查询场次是否存在（可选验证）
2. 构建联表查询：
   ```sql
   SELECT t.* 
   FROM tags t 
   JOIN session_tags st ON t.id = st.tag_id 
   WHERE st.session_id = :session_id 
     AND t.is_active = true 
   ORDER BY t.name
   ```
3. 使用索引：`idx_session_tags_session_id` 加速查询
4. 执行查询获取标签列表
5. 将结果序列化为 `TagItem` 列表
6. 构建并返回包含标签列表的成功响应

**注意事项**:
- 该接口通常嵌入到 `GET /api/v1/sessions/{session_id}` 的响应中
- 也可作为独立接口供前端单独调用

---

#### 4.6.4 按标签搜索直播场次（公开）

**Endpoint**: `GET /api/v1/sessions/search`

**描述**: 按标签筛选直播场次（支持多标签AND/OR逻辑）

**认证**: 公开访问，无需JWT Token

**请求参数 (Query)**:
- `tags` (string, required): 标签名称，多个用逗号分隔（如：`微创手术,肝胆外科`）
- `match_mode` (string, 可选, 默认`any`): 匹配模式
  - `any`: 满足任一标签（OR逻辑）
  - `all`: 满足所有标签（AND逻辑）
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 8,
    "page": 1,
    "size": 10,
    "filters": {
      "tags": ["微创手术", "肝胆外科"],
      "match_mode": "any"
    },
    "items": [
      {
        "id": "session_uuid_1",
        "room_id": "room_uuid_1",
        "room_title": "肝胆外科微创手术研讨",
        "summary": "探讨腹腔镜在肝切除术中的应用",
        "status": "ready",
        "start_time": "2025-10-20T14:00:00Z",
        "tags": ["微创手术", "肝胆外科", "病例讨论"]
      }
    ]
  },
  "timestamp": "2025-10-23T13:45:00Z"
}
```

**执行流程**:

1. 解析 `tags` 参数，分割为标签名称数组
2. 查询 `tags` 表获取对应的标签UUID列表
3. 若部分标签名称不存在，记录DEBUG日志但继续执行（使用已找到的标签）
4. 根据 `match_mode` 构建不同的查询：
   - **any模式（OR）**：
     ```sql
     SELECT DISTINCT ls.* 
     FROM live_sessions ls
     JOIN session_tags st ON ls.id = st.session_id
     WHERE st.tag_id IN (:tag_ids)
     ORDER BY ls.start_time DESC
     ```
   - **all模式（AND）**：
     ```sql
     SELECT ls.* 
     FROM live_sessions ls
     WHERE ls.id IN (
       SELECT st.session_id 
       FROM session_tags st
       WHERE st.tag_id IN (:tag_ids)
       GROUP BY st.session_id
       HAVING COUNT(DISTINCT st.tag_id) = :required_count
     )
     ORDER BY ls.start_time DESC
     ```
5. 执行COUNT查询获取符合条件的总场次数
6. 应用分页（LIMIT和OFFSET）
7. 执行查询获取当前页的场次列表
8. 使用 `joinedload` 预加载 room 和 tags 关联数据
9. 将结果序列化为 `SessionBriefWithTagsItem` 列表
10. 构建分页响应，包含筛选条件信息
11. 返回成功响应

---

### 4.7 Featured Content 模块API（首页焦点图）

#### 4.7.1 获取焦点图列表（公开）

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
      "image_url": "/media/featured/banner1.jpg",
      "target_type": "session",
      "target_id": "session_uuid_123",
      "target_url": null,
      "cta_text": "立即观看",
      "sort_order": 0
    },
    {
      "id": "featured_uuid_2",
      "title": "肝胆外科最新进展",
      "image_url": "/media/featured/banner2.jpg",
      "target_type": "topic",
      "target_id": "topic_uuid_456",
      "target_url": null,
      "cta_text": "查看详情",
      "sort_order": 1
    },
    {
      "id": "featured_uuid_3",
      "title": "合作伙伴推广",
      "image_url": "/media/featured/banner3.jpg",
      "target_type": "external",
      "target_id": null,
      "target_url": "https://external-site.com/promo",
      "cta_text": "了解更多",
      "sort_order": 2
    }
  ],
  "timestamp": "2025-10-23T14:00:00Z"
}
```

**执行流程**:

1. 构建查询：`SELECT * FROM featured_content WHERE is_active = true`
2. 添加时间范围筛选：`(start_at IS NULL OR start_at <= NOW()) AND (end_at IS NULL OR end_at >= NOW())`
3. 按 `sort_order` 升序排序
4. 应用默认限制：最多返回10条焦点图
5. 执行查询获取结果列表
6. 将结果序列化为 `FeaturedContentItem` 列表
7. 构建并返回包含焦点图列表的成功响应

---

#### 4.7.2 创建焦点图（Admin）

**Endpoint**: `POST /api/v1/admin/featured-content`

**描述**: 管理员创建焦点图配置

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "title": "年度医学峰会",
  "image_url": "/media/featured/summit2025.jpg",
  "target_type": "session",
  "target_id": "session_uuid_789",
  "target_url": null,
  "cta_text": "立即报名",
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
    "image_url": "/media/featured/summit2025.jpg",
    "target_type": "session",
    "target_id": "session_uuid_789",
    "target_url": null,
    "cta_text": "立即报名",
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

1. 验证JWT Token并检查管理员权限
2. Pydantic校验请求体（FeaturedContentCreate模型）
3. 在应用层生成焦点图UUID
4. 若提供了 `target_id`，根据 `target_type` 验证目标资源是否存在（room/session/topic等）
5. 创建 `FeaturedContent` 模型实例并填充所有字段
6. 调用 `db.add()` 添加到会话
7. 记录INFO日志：焦点图创建操作、标题、管理员ID
8. 提交事务并刷新对象
9. 序列化为 `FeaturedContentItem` 并返回成功响应

---

#### 4.7.3 更新焦点图（Admin）

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

1. 验证JWT Token并检查管理员权限
2. 根据 `content_id` 查询焦点图对象，若不存在返回 `2001`
3. Pydantic解析更新字段（FeaturedContentUpdate模型）
4. 若更新 `target_id` 和 `target_type`，验证目标资源有效性
5. 遍历更新数据，设置对象属性
6. 触发器自动更新 `updated_at`
7. 记录INFO日志并提交事务
8. 序列化并返回更新后的焦点图信息

---

#### 4.7.4 删除焦点图（Admin）

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

1. 验证JWT Token并检查管理员权限
2. 根据 `content_id` 查询焦点图对象，若不存在返回 `2001`
3. 软删除：设置 `is_active=false`
4. 记录WARNING级别日志
5. 提交事务并返回删除状态

---

### 4.8 User Favorites 模块API（用户收藏）

#### 4.8.1 添加收藏（用户）

**Endpoint**: `POST /api/v1/users/me/favorites`

**描述**: 当前用户收藏指定直播间

**认证**: 需要JWT Token（任何已登录用户）

**请求体**:
```json
{
  "room_id": "room_uuid_123"
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "favorite_uuid_1",
    "room_id": "room_uuid_123",
    "room_title": "肝胆外科微创手术研讨",
    "created_at": "2025-10-23T14:20:00Z"
  },
  "timestamp": "2025-10-23T14:20:00Z"
}
```

**失败响应示例** (`2002 Conflict` - 已收藏):
```json
{
  "code": 2002,
  "message": "资源已存在",
  "data": {
    "reason": "您已收藏该直播间"
  },
  "timestamp": "2025-10-23T14:20:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 验证 `room_id` 对应的直播间是否存在
3. 查询 `user_favorites` 表检查是否已收藏（user_id + room_id组合）
4. 若已收藏且 `is_active=true`，返回 `2002` 资源已存在
5. 若已收藏但 `is_active=false`（曾取消），更新为 `is_active=true`（重新收藏）
6. 若未收藏，在应用层生成UUID，创建新记录
7. 调用 `db.add()` 和 `db.commit()`
8. 记录INFO日志并返回收藏信息（含room_title）

---

#### 4.8.2 获取收藏列表（用户）

**Endpoint**: `GET /api/v1/users/me/favorites`

**描述**: 获取当前用户的收藏直播间列表

**认证**: 需要JWT Token

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 5,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "favorite_uuid_1",
        "room_id": "room_uuid_123",
        "room_title": "肝胆外科微创手术研讨",
        "room_cover_url": "/media/rooms/xxx/cover.jpg",
        "created_at": "2025-10-23T14:20:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T14:25:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 构建查询：`SELECT * FROM user_favorites WHERE user_id = :user_id AND is_active = true`
3. JOIN `live_rooms` 表获取room_title和cover_url
4. 按 `created_at` 降序排序（最新收藏在前）
5. 应用分页
6. 执行查询获取当前页数据
7. 执行COUNT查询获取总数
8. 序列化并返回分页响应

---

#### 4.8.3 取消收藏（用户）

**Endpoint**: `DELETE /api/v1/users/me/favorites/{room_id}`

**描述**: 取消收藏指定直播间

**认证**: 需要JWT Token

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room_id": "room_uuid_123",
    "status": "unfavorited"
  },
  "timestamp": "2025-10-23T14:30:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "reason": "未找到该收藏记录"
  },
  "timestamp": "2025-10-23T14:30:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 查询 `user_favorites` 表：`WHERE user_id = :user_id AND room_id = :room_id AND is_active = true`
3. 若不存在，返回 `2001` 资源不存在
4. 软删除：设置 `is_active=false`（保留历史记录用于分析）
5. 记录INFO日志并提交事务
6. 返回取消收藏状态

---

### 4.9 Watch History 模块API（观看历史）

#### 4.9.1 记录观看行为（用户）

**Endpoint**: `POST /api/v1/sessions/{session_id}/watch`

**描述**: 记录用户观看某场次的行为（含观看进度）

**认证**: 需要JWT Token

**请求体**:
```json
{
  "progress": 360,
  "extra": {
    "device": "web",
    "quality": "1080p"
  }
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "history_uuid_1",
    "session_id": "session_uuid_456",
    "progress": 360,
    "watched_at": "2025-10-23T14:35:00Z"
  },
  "timestamp": "2025-10-23T14:35:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 验证 `session_id` 对应的场次是否存在
3. 查询该用户对该场次的历史记录（user_id + session_id）
4. 若存在且 `is_latest=true`，将旧记录的 `is_latest` 设为 `false`
5. 在应用层生成UUID，创建新的观看历史记录
6. 设置 `is_latest=true`，填充progress和extra字段
7. 调用 `db.add()` 和 `db.commit()`
8. 返回观看记录信息

---

#### 4.9.2 获取观看历史（用户）

**Endpoint**: `GET /api/v1/users/me/watch-history`

**描述**: 获取当前用户的观看历史记录

**认证**: 需要JWT Token

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认20): 每页数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 15,
    "page": 1,
    "size": 20,
    "items": [
      {
        "id": "history_uuid_1",
        "session_id": "session_uuid_456",
        "session_title": "肝胆外科病例讨论",
        "room_cover_url": "/media/rooms/xxx/cover.jpg",
        "progress": 360,
        "watched_at": "2025-10-23T14:35:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T14:40:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 构建查询：`SELECT * FROM watch_history WHERE user_id = :user_id AND is_latest = true`
3. JOIN `live_sessions` 和 `live_rooms` 获取场次标题和封面
4. 按 `watched_at` 降序排序（最近观看在前）
5. 应用分页
6. 执行查询获取当前页数据和总数
7. 序列化并返回分页响应

---

#### 4.9.3 删除观看历史（用户）

**Endpoint**: `DELETE /api/v1/users/me/watch-history/{history_id}`

**描述**: 删除单条观看历史记录

**认证**: 需要JWT Token

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "history_uuid_1",
    "status": "deleted"
  },
  "timestamp": "2025-10-23T14:45:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 查询 `watch_history` 表：`WHERE id = :history_id AND user_id = :user_id`
3. 若不存在或user_id不匹配，返回 `2001` 或 `3002`
4. 硬删除：调用 `db.delete()`（观看历史可物理删除）
5. 记录INFO日志并提交事务
6. 返回删除状态

---

### 4.10 User Subscriptions 模块API（订阅提醒）

#### 4.10.1 订阅直播间（用户）

**Endpoint**: `POST /api/v1/users/me/subscriptions`

**描述**: 订阅指定直播间的开播提醒

**认证**: 需要JWT Token

**请求体**:
```json
{
  "room_id": "room_uuid_789"
}
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "subscription_uuid_1",
    "room_id": "room_uuid_789",
    "room_title": "胃肠外科专题讲座",
    "created_at": "2025-10-23T14:50:00Z"
  },
  "timestamp": "2025-10-23T14:50:00Z"
}
```

**失败响应示例** (`2002 Conflict`):
```json
{
  "code": 2002,
  "message": "资源已存在",
  "data": {
    "reason": "您已订阅该直播间"
  },
  "timestamp": "2025-10-23T14:50:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 验证 `room_id` 对应的直播间是否存在
3. 查询 `user_subscriptions` 表检查是否已订阅（user_id + room_id + is_active=true）
4. 若已订阅，返回 `2002` 资源已存在
5. 若曾订阅但已取消（is_active=false），更新为 `is_active=true`
6. 若未订阅，在应用层生成UUID，创建新记录
7. 调用 `db.add()` 和 `db.commit()`
8. 返回订阅信息

---

#### 4.10.2 获取订阅列表（用户）

**Endpoint**: `GET /api/v1/users/me/subscriptions`

**描述**: 获取当前用户的直播间订阅列表

**认证**: 需要JWT Token

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 3,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "subscription_uuid_1",
        "room_id": "room_uuid_789",
        "room_title": "胃肠外科专题讲座",
        "room_cover_url": "/media/rooms/yyy/cover.jpg",
        "created_at": "2025-10-23T14:50:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T14:55:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 构建查询：`SELECT * FROM user_subscriptions WHERE user_id = :user_id AND is_active = true`
3. JOIN `live_rooms` 表获取room_title和cover_url
4. 按 `created_at` 降序排序
5. 应用分页
6. 执行查询获取当前页数据和总数
7. 序列化并返回分页响应

---

#### 4.10.3 取消订阅（用户）

**Endpoint**: `DELETE /api/v1/users/me/subscriptions/{room_id}`

**描述**: 取消订阅指定直播间

**认证**: 需要JWT Token

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room_id": "room_uuid_789",
    "status": "unsubscribed"
  },
  "timestamp": "2025-10-23T15:00:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 查询 `user_subscriptions` 表：`WHERE user_id = :user_id AND room_id = :room_id AND is_active = true`
3. 若不存在，返回 `2001` 资源不存在
4. 软删除：设置 `is_active=false`
5. 记录INFO日志并提交事务
6. 返回取消订阅状态

---

### 4.11 Live Sessions/Rooms API扩展说明

本章节说明需要对已有的 `live_sessions` 和 `live_rooms` API进行的扩展，以支持新增字段和前端需求。

#### 4.11.1 Live Sessions API扩展

**需扩展的接口**：

1. **`GET /api/v1/sessions/{session_id}` - 获取场次详情**
   
   **新增返回字段**：
   ```json
   {
     "id": "session_uuid_1",
     "room_id": "room_uuid_1",
     "summary": "本场次重点讨论腹腔镜肝切除术的技术要点",
     "featured_expert": {
       "id": "expert_uuid_1",
       "name": "房树强",
       "title": "主任医师、教授",
       "hospital": "北京大学人民医院",
       "avatar_url": "/media/experts/fangshuqiang.jpg"
     },
     "tags": [
       {
         "id": "tag_uuid_1",
         "name": "微创手术"
       },
       {
         "id": "tag_uuid_2",
         "name": "肝胆外科"
       }
     ],
     "status": "live",
     "start_time": "2025-10-23T14:00:00Z"
   }
   ```
   
   **扩展要点**：
   - 通过 `featured_expert_id` JOIN `experts` 表获取专家信息
   - 通过 `session_tags` JOIN `tags` 表获取标签列表
   - 使用 `joinedload` 预加载关联数据，避免N+1查询
   - 在Pydantic Schema中添加嵌套的 `ExpertBrief` 和 `TagItem` 模型

2. **`GET /api/v1/rooms/{room_id}/sessions` - 获取房间场次列表**
   
   **新增返回字段**（每个item）：
   - `summary`: 场次摘要
   - `featured_expert_name`: 专家姓名（简化版，无需完整信息）
   - `tags`: 标签名称列表（字符串数组）
   
   **扩展要点**：
   - 在列表查询中使用LEFT JOIN优化性能
   - 使用聚合查询获取tags（GROUP_CONCAT或ARRAY_AGG）

3. **`POST /api/v1/rooms/{room_id}/sessions` - 创建场次**
   
   **新增请求字段**：
   ```json
   {
     "start_time": "2025-10-25T14:00:00Z",
     "summary": "探讨腹腔镜在肝切除术中的应用",
     "featured_expert_id": "expert_uuid_1"
   }
   ```
   
   **扩展要点**：
   - 在创建场次时支持设置 `summary` 和 `featured_expert_id`
   - 验证 `featured_expert_id` 在 `experts` 表中存在
   - 标签通过单独的 `POST /api/v1/admin/sessions/{session_id}/tags` 接口设置

4. **`PATCH /api/v1/sessions/{session_id}` - 更新场次**
   
   **新增可更新字段**：
   - `summary`: 更新场次摘要
   - `featured_expert_id`: 更换主讲专家
   
   **扩展要点**：
   - 更新时验证新的 `featured_expert_id` 有效性
   - 记录INFO日志包含更新的字段

#### 4.11.2 Live Rooms API扩展

**需扩展的接口**：

1. **`GET /api/v1/rooms` - 获取直播间列表**
   
   **新增Query参数**：
   - `category_id` (UUID, 可选): 按分类筛选
   
   **新增返回字段**：
   ```json
   {
     "items": [
       {
         "id": "room_uuid_1",
         "title": "肝胆外科微创手术研讨",
         "summary": "探讨腹腔镜、机器人辅助等微创技术在肝胆胰脾外科的应用",
         "category": {
           "id": "category_uuid_1",
           "name": "肝胆外科",
           "icon": "icon-liver"
         },
         "cover_url": "/media/rooms/xxx/cover.jpg",
         "created_at": "2025-10-20T10:00:00Z"
       }
     ]
   }
   ```
   
   **扩展要点**：
   - 查询时包含 `live_rooms.summary` 字段
   - 添加 `WHERE category_id = :category_id` 筛选条件
   - JOIN `categories` 表获取分类信息
   - 在Pydantic Schema中添加嵌套的 `CategoryBrief` 模型
   - 在Pydantic Schema中添加 `summary: Optional[str]` 字段

2. **`POST /api/v1/rooms` - 创建直播间**
   
   **新增请求字段**：
   ```json
   {
     "title": "新直播间",
     "description": "描述",
     "summary": "直播间简介摘要，用于卡片展示",
     "category_id": "category_uuid_1"
   }
   ```
   
   **扩展要点**：
   - 在请求体Schema中添加 `summary: Optional[str]` 字段
   - 验证 `category_id` 在 `categories` 表中存在且 `is_active=true`
   - 若验证失败，返回 `4001` 参数校验失败

3. **`PATCH /api/v1/rooms/{room_id}` - 更新直播间**
   
   **新增可更新字段**：
   - `summary`: 更新直播间简介摘要
   - `category_id`: 更换分类
   
   **扩展要点**：
   - 在请求体Schema中添加 `summary: Optional[str]` 字段
   - 更新时重新验证 `category_id` 有效性

4. **`GET /api/v1/rooms/{room_id}` - 获取直播间详情**
   
   **新增返回字段**：
   ```json
   {
     "id": "room_uuid_1",
     "title": "肝胆外科微创手术研讨",
     "summary": "探讨腹腔镜、机器人辅助等微创技术在肝胆胰脾外科的应用",
     "category": {
       "id": "category_uuid_1",
       "name": "肝胆外科",
       "slug": "hepatobiliary-surgery",
       "icon": "icon-liver"
     },
     "cover_url": "/media/rooms/xxx/cover.jpg"
   }
   ```
   
   **扩展要点**：
   - 查询时包含 `live_rooms.summary` 字段
   - JOIN `categories` 表获取分类信息
   - 在Pydantic Schema中添加 `summary: Optional[str]` 字段

#### 4.11.3 扩展实施优先级

**阶段1（P0）**：
- `POST /api/v1/rooms` - 支持category_id创建
- `POST /api/v1/rooms/{room_id}/sessions` - 支持summary和expert创建

**阶段2（P1）**：
- `GET /api/v1/sessions/{session_id}` - 返回完整的expert和tags
- `GET /api/v1/rooms` - 支持category_id筛选和返回

**阶段3（P2）**：
- 列表查询性能优化（聚合查询、索引优化）
- Pydantic Schema嵌套结构完善

---

### 4.12 Notifications 模块API（用户通知）

#### 4.12.1 获取通知列表（用户）

**Endpoint**: `GET /api/v1/users/me/notifications`

**描述**: 获取当前用户的通知列表（分页）

**认证**: 需要JWT Token

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认10): 每页数量
- `sort` (string, 可选, 默认`created_at:desc`): 排序规则
- `is_read` (bool, 可选): 筛选已读/未读

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 12,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "notification_uuid_1",
        "title": "您的订阅即将开始",
        "content": "您订阅的 '肝胆胰外科手术直播演示' 将在 10 分钟后开始。",
        "notification_type": "subscription",
        "related_id": "session_uuid_1",
        "related_type": "session",
        "is_read": false,
        "created_at": "2025-10-22T07:50:00Z"
      },
      {
        "id": "notification_uuid_2",
        "title": "欢迎使用",
        "content": "欢迎您注册平台。",
        "notification_type": "system",
        "related_id": null,
        "related_type": null,
        "is_read": true,
        "created_at": "2025-10-21T14:00:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T15:00:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 构建基础查询：`SELECT * FROM notifications WHERE user_id = :user_id`
3. 根据 `is_read` 参数添加筛选条件（如果提供）
4. 执行COUNT查询获取筛选后的总数
5. 解析 `sort` 参数（默认按创建时间倒序）
6. 计算分页的 `offset` 值：`(page - 1) * size`
7. 应用排序和分页（`ORDER BY created_at DESC LIMIT :size OFFSET :offset`）
8. 执行查询获取当前页的通知列表
9. 将结果序列化为 `NotificationItem` 列表
10. 构建分页响应并返回

---

#### 4.12.2 标记通知为已读（用户）

**Endpoint**: `POST /api/v1/users/me/notifications/{notification_id}/read`

**描述**: 将单条通知标记为已读

**认证**: 需要JWT Token

**请求体**: 无

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": null,
  "timestamp": "2025-10-23T15:05:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Notification",
    "id": "notification_uuid_999",
    "reason": "通知不存在或不属于当前用户"
  },
  "timestamp": "2025-10-23T15:05:00Z"
}
```

**执行流程**:

1. 验证JWT Token并提取 `user_id`
2. 根据路径参数 `notification_id` 查询通知：`SELECT * FROM notifications WHERE id = :notification_id AND user_id = :user_id`
3. 若未找到记录（或 `user_id` 不匹配），返回 `2001` 资源不存在错误
4. 检查 `is_read` 状态，若已为 `true`，直接返回成功（幂等性）
5. 更新通知状态：`UPDATE notifications SET is_read = true WHERE id = :notification_id`
6. 记录INFO日志：标记已读操作、通知ID、用户ID
7. 提交事务
8. 返回成功响应（`data` 为 `null`）

---

#### 4.12.3 创建通知（Admin）

**Endpoint**: `POST /api/v1/admin/notifications`

**描述**: 管理员创建系统通知或批量通知

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "user_ids": ["user_uuid_1", "user_uuid_2"],  // 空数组表示发送给所有用户
  "title": "系统维护通知",
  "content": "系统将于今晚22:00进行维护，预计持续2小时。",
  "notification_type": "system",
  "related_id": null,
  "related_type": null
}
```

**Pydantic Schema**:
   ```python
class NotificationCreateRequest(BaseModel):
    """Admin创建通知请求Schema"""
    user_ids: List[uuid.UUID] = Field(..., description="接收通知的用户ID列表，空列表表示全部用户")
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    notification_type: str = Field(default="system", pattern="^(system|subscription|interaction)$")
    related_id: Optional[uuid.UUID] = None
    related_type: Optional[str] = None

class NotificationBatchCreateResponse(BaseModel):
    """批量创建通知响应Schema"""
    total_created: int
    user_ids: List[uuid.UUID]
```

**成功响应** (`201 Created`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_created": 2,
    "user_ids": ["user_uuid_1", "user_uuid_2"]
  },
  "timestamp": "2025-10-23T16:00:00Z"
}
```

**失败响应示例** (`4001 Parameter Error`):
```json
{
  "code": 4001,
  "message": "参数错误",
  "data": {
    "field": "notification_type",
    "error": "通知类型必须是: system, subscription, interaction"
  },
  "timestamp": "2025-10-23T16:00:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查是否为ADMIN或SUPERADMIN角色
2. 验证请求体参数（标题长度、通知类型枚举值等）
3. 若 `user_ids` 为空列表，查询所有活跃用户：`SELECT public_id FROM users WHERE is_active = true`
4. 遍历目标用户列表，为每个用户创建通知记录
5. 每条通知的 `id` 在应用层生成：`uuid.uuid4()`
6. 批量插入通知记录到 `notifications` 表
7. 记录INFO日志：通知类型、接收用户数量、标题
8. 提交事务
9. 返回成功响应，包含创建数量和目标用户ID列表

---

#### 4.12.4 获取通知列表（Admin）

**Endpoint**: `GET /api/v1/admin/notifications`

**描述**: 管理员查询所有通知记录（分页）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求参数 (Query)**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认20): 每页数量
- `sort` (string, 可选, 默认`created_at:desc`): 排序规则
- `user_id` (UUID, 可选): 按用户ID筛选
- `notification_type` (string, 可选): 按通知类型筛选
- `is_read` (bool, 可选): 按已读/未读筛选

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 1250,
    "page": 1,
    "size": 20,
    "items": [
      {
        "id": "notification_uuid_1",
        "user_id": "user_uuid_abc",
        "title": "系统维护通知",
        "content": "系统将于今晚22:00进行维护...",
        "notification_type": "system",
        "related_id": null,
        "related_type": null,
        "is_read": false,
        "created_at": "2025-10-23T15:00:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T16:30:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查是否为ADMIN或SUPERADMIN角色
2. 解析并验证查询参数（page、size、sort等）
3. 构建基础查询：`SELECT * FROM notifications`
4. 根据筛选参数添加WHERE条件（user_id、notification_type、is_read）
5. 执行COUNT查询获取筛选后的总数
6. 解析sort参数并应用排序（默认按创建时间倒序）
7. 计算分页offset：`(page - 1) * size`
8. 应用分页：`LIMIT :size OFFSET :offset`
9. 执行查询获取当前页的通知列表
10. 将结果序列化为 `NotificationItem` 列表
11. 构建分页响应并返回

---

#### 4.12.5 获取通知详情（Admin）

**Endpoint**: `GET /api/v1/admin/notifications/{notification_id}`

**描述**: 管理员查询单条通知的详细信息

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "notification_uuid_1",
    "user_id": "user_uuid_abc",
    "title": "系统维护通知",
    "content": "系统将于今晚22:00进行维护，预计持续2小时。",
    "notification_type": "system",
    "related_id": null,
    "related_type": null,
    "is_read": false,
    "created_at": "2025-10-23T15:00:00Z"
  },
  "timestamp": "2025-10-23T16:35:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Notification",
    "id": "notification_uuid_999"
  },
  "timestamp": "2025-10-23T16:35:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查是否为ADMIN或SUPERADMIN角色
2. 根据路径参数 `notification_id` 查询通知：`SELECT * FROM notifications WHERE id = :notification_id`
3. 若未找到记录，返回 `2001` 资源不存在错误
4. 将查询结果序列化为 `NotificationItem`
5. 记录DEBUG日志：通知ID、查询用户
6. 返回成功响应

---

#### 4.12.6 更新通知（Admin）

**Endpoint**: `PATCH /api/v1/admin/notifications/{notification_id}`

**描述**: 管理员更新通知内容（通常用于修正错误）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "title": "系统维护通知（时间调整）",
  "content": "系统将于明天22:00进行维护，预计持续2小时。"
}
```

**Pydantic Schema**:
   ```python
class NotificationUpdateRequest(BaseModel):
    """Admin更新通知请求Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "notification_uuid_1",
    "user_id": "user_uuid_abc",
    "title": "系统维护通知（时间调整）",
    "content": "系统将于明天22:00进行维护，预计持续2小时。",
    "notification_type": "system",
    "related_id": null,
    "related_type": null,
    "is_read": false,
    "created_at": "2025-10-23T15:00:00Z"
  },
  "timestamp": "2025-10-23T16:40:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Notification",
    "id": "notification_uuid_999"
  },
  "timestamp": "2025-10-23T16:40:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查是否为ADMIN或SUPERADMIN角色
2. 验证请求体参数
3. 根据路径参数 `notification_id` 查询通知：`SELECT * FROM notifications WHERE id = :notification_id`
4. 若未找到记录，返回 `2001` 资源不存在错误
5. 遍历请求体中的非None字段，更新通知对象
6. 执行更新：`UPDATE notifications SET title = :title, content = :content WHERE id = :notification_id`
7. 记录INFO日志：通知ID、更新的字段
8. 提交事务并刷新对象
9. 将更新后的结果序列化为 `NotificationItem`
10. 返回成功响应

**注意**: 
- 不允许更新 `user_id`、`notification_type`、`related_id`、`related_type`、`is_read` 等字段
- 如果需要撤回通知，应使用删除接口

---

#### 4.12.7 删除通知（Admin）

**Endpoint**: `DELETE /api/v1/admin/notifications/{notification_id}`

**描述**: 管理员删除单条通知（撤回通知）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "notification_uuid_1",
    "status": "deleted"
  },
  "timestamp": "2025-10-23T16:45:00Z"
}
```

**失败响应示例** (`2001 Not Found`):
```json
{
  "code": 2001,
  "message": "资源不存在",
  "data": {
    "resource": "Notification",
    "id": "notification_uuid_999"
  },
  "timestamp": "2025-10-23T16:45:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查是否为ADMIN或SUPERADMIN角色
2. 根据路径参数 `notification_id` 查询通知：`SELECT * FROM notifications WHERE id = :notification_id`
3. 若未找到记录，返回 `2001` 资源不存在错误
4. 记录INFO日志：通知ID、删除用户、通知标题
5. 执行删除：`DELETE FROM notifications WHERE id = :notification_id`
6. 提交事务
7. 返回成功响应，包含已删除的通知ID

**注意**: 
- 删除通知是物理删除，不可恢复
- 建议仅在通知发送错误时使用
- 对于历史通知，建议保留记录而不是删除

---

#### 4.12.8 批量删除通知（Admin）

**Endpoint**: `POST /api/v1/admin/notifications/batch-delete`

**描述**: 管理员批量删除通知（用于清理过期通知）

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求体**:
```json
{
  "notification_ids": ["notification_uuid_1", "notification_uuid_2", "notification_uuid_3"]
}
```

或者按条件批量删除：
```json
{
  "delete_before": "2025-09-01T00:00:00Z",  // 删除此日期之前的通知
  "notification_type": "system",  // 可选：仅删除指定类型
  "is_read": true  // 可选：仅删除已读通知
}
```

**Pydantic Schema**:
   ```python
class NotificationBatchDeleteRequest(BaseModel):
    """批量删除通知请求Schema"""
    notification_ids: Optional[List[uuid.UUID]] = Field(None, description="通知ID列表")
    delete_before: Optional[datetime.datetime] = Field(None, description="删除此日期之前的通知")
    notification_type: Optional[str] = None
    is_read: Optional[bool] = None

    @model_validator(mode='after')
    def check_params(self):
        if not self.notification_ids and not self.delete_before:
            raise ValueError("必须提供 notification_ids 或 delete_before 参数之一")
        return self
```

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted_count": 3
  },
  "timestamp": "2025-10-23T16:50:00Z"
}
```

**执行流程**:

1. 验证JWT Token并检查是否为ADMIN或SUPERADMIN角色
2. 验证请求体参数（至少提供notification_ids或delete_before之一）
3. 构建删除条件：
   - 如果提供 `notification_ids`：`WHERE id IN (:ids)`
   - 如果提供 `delete_before`：`WHERE created_at < :delete_before`
   - 添加可选筛选条件（notification_type、is_read）
4. 执行COUNT查询获取将被删除的记录数
5. 记录WARNING日志：删除条件、预计删除数量
6. 执行批量删除：`DELETE FROM notifications WHERE ...`
7. 获取实际删除数量
8. 提交事务
9. 记录INFO日志：实际删除数量
10. 返回成功响应

**注意**: 
- 批量删除是高危操作，记录详细日志
- 建议定期清理90天以上的已读系统通知
- 删除前可以先导出备份

---

### 4.13 Homepage 模块API（首页专用）

#### 4.13.1 获取首页直播间列表

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
          "user_id": "user_uuid_C",
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
        "host": {
          "expert_id": null,
          "user_id": "user_uuid_A",
          "name": "张三",
          "title": null,
          "hospital": null
        },
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

**失败响应示例** (`4001 Parameter Error`):
```json
{
  "code": 4001,
  "message": "参数错误",
  "data": {
    "field": "category_id",
    "error": "分类ID无效或不存在"
  },
  "timestamp": "2025-10-23T16:00:00Z"
}
```

**失败响应示例** (`5001 Internal Error`):
```json
{
  "code": 5001,
  "message": "服务器内部错误",
  "data": {
    "error": "数据库查询失败",
    "trace_id": "trace_abc123"
  },
  "timestamp": "2025-10-23T16:00:00Z"
}
```

**Pydantic Schemas**:
```python
from enum import Enum

class LiveStatusEnum(str, Enum):
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
```

**执行流程**:

1. 解析并验证查询参数（`page`, `size`, `sort`, `category_id`）
2. 构建复杂的联表查询（核心逻辑）：
   - 从 `live_rooms lr` 表开始
   - 若提供 `category_id`，添加筛选条件：`WHERE lr.category_id = :category_id`
   - 使用子查询或窗口函数找到每个房间的"相关场次"（relevant_session）
     - 优先级：live > scheduled > latest replay
     - `SELECT ls.id, ls.status, ls.start_time, ls.end_time, ls.featured_expert_id FROM live_sessions ls WHERE ls.room_id = lr.id ORDER BY (优先级逻辑) LIMIT 1`
3. LEFT JOIN `experts fe` 获取场次的featured_expert信息（主讲专家）
4. JOIN `users su` 获取房间所有者（主播）信息：`ON lr.user_id = su.public_id`
5. LEFT JOIN `experts se` 获取房主的专家信息：`ON su.public_id = se.user_id`
6. LEFT JOIN `session_statistics ss` 获取统计数据：`ON relevant_session_id = ss.session_id`
7. 在Service层应用Host选择逻辑（优先级：featured_expert > 房主专家 > 房主用户）
8. 根据 `relevant_session` 的status确定 `live_status`（映射关系：live→live, scheduled→scheduled, ready/ended→replay）
9. 计算热度（heat）：使用 `session_statistics` 数据和预定义公式
10. 构造 `status_data`：根据 `live_status` 填充相应字段（live填充viewer_count, scheduled填充start_time, replay填充duration和play_count）
11. 执行COUNT查询获取筛选后的总房间数
12. 解析 `sort` 参数并应用排序（热度、开始时间、创建时间等）
13. 应用分页（`LIMIT :size OFFSET :offset`）
14. 执行主查询获取当前页的房间列表
15. 将结果映射到 `HomepageRoomItem` Schema
16. 构建分页响应并返回

**特殊说明**:

- **Host选择逻辑**：
  1. 优先：场次的 `featured_expert`（`live_sessions.featured_expert_id`）
  2. 其次：房主的专家信息（`experts WHERE user_id = live_rooms.user_id`）
  3. 最后：房主的用户信息（`users WHERE public_id = live_rooms.user_id`）
  
- **热度计算**（示例公式）：
  ```
  heat = current_viewer_count * 10 + peak_viewer_count * 5 + play_count
  ```

- **相关场次查询**（PostgreSQL示例）：
  ```sql
  SELECT DISTINCT ON (lr.id)
      lr.*,
      ls.id AS session_id,
      ls.status AS session_status,
      ...
  FROM live_rooms lr
  LEFT JOIN live_sessions ls ON ls.room_id = lr.id
  ORDER BY lr.id,
      CASE ls.status
          WHEN 'live' THEN 1
          WHEN 'scheduled' THEN 2
          WHEN 'ready' THEN 3
          ELSE 4
      END,
      ls.start_time DESC
  ```

---

### 4.14 Search 模块API（全局搜索）

#### 4.14.1 全局搜索

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

**失败响应示例** (`4001 Parameter Error`):
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

**失败响应示例** (`4002 Invalid Parameter`):
```json
{
  "code": 4002,
  "message": "参数值无效",
  "data": {
    "field": "type",
    "error": "资源类型必须是: room, expert, topic, brand"
  },
  "timestamp": "2025-10-23T17:00:00Z"
}
```

**Pydantic Schemas**:
```python
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

**执行流程**:

1. 解析并验证查询参数（q、page、size、type等）
2. 验证搜索关键词长度（至少2个字符，中文1个字符当2个）
3. 解析 `type` 参数，确定搜索范围（默认搜索所有类型）
4. 构建搜索查询（使用PostgreSQL全文搜索或Elasticsearch）：
   - **方案A（PostgreSQL）**：使用 `ILIKE` 或全文搜索索引（tsvector）
   - **方案B（Elasticsearch）**：调用搜索引擎API
5. 对每种资源类型执行搜索：
   - **room**: 搜索 `live_rooms` 表的 `title` 和 `summary` 字段
   - **expert**: 搜索 `experts` 表的 `name`, `bio`, `expertise_areas` 字段
   - **topic**: 搜索 `topics` 表的 `title` 和 `description` 字段
   - **brand**: 搜索 `brands` 表的 `name` 和 `description` 字段
6. 使用 `UNION ALL` 合并各类型的搜索结果
7. 计算匹配分数（基于关键词在标题/内容中的位置和频率）
8. 生成高亮文本（将匹配的关键词用 `<em>` 标签包裹）
9. 填充类型特定的metadata：
   - room: 添加 `live_status`, `viewer_count`
   - expert: 添加 `hospital`, `title`
   - topic: 添加 `room_count`
10. 按匹配分数降序排序
11. 执行COUNT查询获取总结果数
12. 应用分页（`LIMIT :size OFFSET :offset`）
13. 将结果映射到 `SearchResultItem` 列表
14. 记录DEBUG日志：搜索关键词、结果数量、执行时间
15. 构建分页响应并返回

**实现建议**:

**阶段1（MVP）**：使用PostgreSQL的 `ILIKE` 实现基础搜索
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

**阶段2（优化）**：使用PostgreSQL全文搜索（tsvector）
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

**阶段3（高级）**：集成Elasticsearch
- 支持中文分词
- 支持同义词搜索
- 支持拼音搜索
- 更精确的相关性评分

**性能优化**:
1. 为搜索字段添加全文索引
2. 使用Redis缓存热门搜索结果（TTL 5分钟）
3. 搜索历史记录（用于统计和优化）
4. 异步更新搜索索引（避免影响写入性能）

**扩展功能**（后续版本）:
1. 搜索建议（自动补全）
2. 搜索历史（用户个人）
3. 热门搜索词（全局统计）
4. 搜索过滤器（时间范围、分类等）
5. 高级搜索（AND/OR/NOT逻辑）

---

## 5. 补充说明

### 5.1 关于Pydantic Schemas

**决策**: 本文档**包含** Pydantic Schemas定义

**理由**:
1. **设计文档的完整性**: Pydantic Schema是API接口规范的重要组成部分，定义了请求体和响应体的数据结构
2. **开发参考**: 开发人员可以直接参考Schema定义进行实现
3. **前后端协作**: 前端开发人员可以根据Schema了解API的数据格式
4. **符合现有文档规范**: 其他设计文档（如《用户模块设计文档》、《专题功能设计文档》）都包含了详细的Schema定义

**Schema定义位置**: 见本文档 Section 3（Pydantic Schemas）

### 5.2 关于执行流程描述风格

本修订版已将所有API接口的执行流程改为**文字描述**风格，与《直播核心功能设计文档》、《用户模块设计文档》保持一致。

**风格特点**:
- 使用清晰的步骤编号（1, 2, 3...）
- 每一步用简洁的文字说明操作内容
- 提及关键的函数名、表名、字段名
- 不包含完整的代码实现
- 强调业务逻辑和数据流

### 5.3 关于DDL迁移脚本

根据用户要求，本文档**不包含** Alembic DDL迁移脚本。

数据库DDL定义已完整包含在 Section 2（数据库Schema）中，开发团队可以根据DDL手动编写迁移脚本。

---

## 6. 错误码对照表

| 业务场景 | 错误码 | 错误消息 | 使用接口 |
|---------|-------|---------|---------|
| 操作成功 | 200 | success | 所有接口 |
| 资源不存在 | 2001 | 资源不存在 | 所有GET/PATCH/DELETE接口 |
| 资源已存在（名称冲突） | 2002 | 资源已存在 | 所有POST接口（name唯一性检查） |
| 操作被禁止（被引用） | 2003 | 操作被禁止 | 所有DELETE接口（引用检查） |
| 业务逻辑错误（user_id已绑定） | 2004 | 业务逻辑错误 | POST/PATCH experts（user_id冲突） |
| 未认证（Token缺失/无效） | 3001 | 未认证 | 所有需认证的接口 |
| 权限不足 | 3002 | 权限不足 | 所有Admin接口（角色检查） |
| 参数校验失败 | 4001 | 参数校验失败 | 所有接口（Pydantic验证失败） |

---

## 7. 后续开发建议

### 7.1 优先级P0（第一批实现）

1. **基础数据表创建**: tags, categories, brands, experts（含触发器）
2. **关联表创建**: session_tags, brand_topics
3. **字段补充**: 
   - `live_sessions.featured_expert_id`
   - `live_sessions.summary`
   - 确认 `live_rooms.category_id` 存在
4. **核心公开API**: 
   - Tags, Categories, Brands, Experts的查询接口
   - Session Tags查询接口

### 7.2 优先级P1（第二批实现）

1. **Admin管理接口**: 所有模块的完整CRUD
2. **关联管理接口**: 品牌-专题、场次-标签的批量操作
3. **搜索功能**: 按标签搜索直播

### 7.3 优先级P2（优化阶段）

1. **性能优化**: 索引优化、查询优化、N+1问题解决
2. **批量操作**: 批量创建、批量更新、批量删除
3. **审计日志**: 完善所有操作的日志记录

---

**文档结束**


