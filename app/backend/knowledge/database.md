# 数据库设计文档

> 基于 ORM 模型源码和 SQL 迁移文件分析，更新时间：2026-07-13

---

## 一、数据库概览

### 基本信息

| 属性 | 值 |
|------|-----|
| 数据库类型 | PostgreSQL 15 |
| 应用数据库 | live_core_test |
| ORM 框架 | SQLAlchemy 1.4.23 |
| 异步驱动 | asyncpg 0.30.0 |
| 同步驱动 | psycopg2-binary 2.9.1 |
| 缓存 | Redis 7 |

### 数据表统计

| 分类 | 表数量 | 表名 |
|------|--------|------|
| 直播核心 | 3 | live_rooms, live_sessions, session_statistics |
| 专家系统 | 3 | experts, user_expert_subscriptions, live_session_experts |
| 内容管理 | 4 | categories, tags, session_tags, live_room_categories |
| 专题管理 | 3 | topics, topic_categories, topic_category_rooms |
| 品牌管理 | 3 | brands, brand_topics, brand_rooms |
| 直播特性 | 2 | live_room_messages, live_room_tabs |
| 用户行为 | 3 | user_favorites, watch_history, user_subscriptions |
| 偏好通知 | 2 | user_preferences, notifications |
| 搜索 | 2 | user_search_history, search_keyword_stats |
| 首页 | 1 | featured_content |
| 公众号 | 2 | official_accounts, live_room_official_accounts |
| **合计** | **28** | |

---

## 二、数据库设计规范

### 2.1 UUID 主键

所有表使用 UUID 作为主键，在**应用层**通过 `uuid.uuid4()` 生成，而非数据库自增：

```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

### 2.2 时间戳模式

所有业务表包含双时间戳字段：

```python
created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

所有时间字段使用 `TIMESTAMP(timezone=True)`，存储 UTC 时间。

### 2.3 软删除策略

使用 `is_active` 字段实现软删除（不物理删除数据）：

| 表名 | 软删除字段 | 说明 |
|------|-----------|------|
| experts | is_active | 专家上架/下架 |
| categories | is_active | 分类启用/禁用 |
| tags | is_active | 标签启用/禁用 |
| brands | is_active | 品牌上架/下架 |
| live_room_tabs | is_active | Tab 启用/禁用 |
| user_favorites | is_active | 收藏/取消收藏 |
| user_subscriptions | is_active | 订阅/取消订阅 |
| official_accounts | is_active | 公众号启用/禁用 |

### 2.4 幂等性设计

批量导入使用 PostgreSQL **部分唯一索引**（Partial Unique Index）保证幂等：

```sql
-- 仅对非 NULL 的 external_room_id 生效
CREATE UNIQUE INDEX uq_live_rooms_user_external_room
  ON live_rooms (user_id, external_room_id)
  WHERE external_room_id IS NOT NULL;

-- 仅对非 NULL 的 playback_url_hash 生效
CREATE UNIQUE INDEX uq_live_sessions_room_playback_hash
  ON live_sessions (room_id, playback_url_hash)
  WHERE playback_url_hash IS NOT NULL;
```

### 2.5 跨服务引用

对可能独立部署的外部服务，不使用数据库外键，仅做应用层验证：

```python
# user_id 来自用户服务（users 表）
user_id = Column(UUID(as_uuid=True), nullable=False, comment='用户公开ID，应用层验证')
```

---

## 三、数据库模型关系图

```
                          ┌──────────────────┐
                          │    categories    │ ← 全局分类体系
                          └──┬──────┬───────┘
                             │      │
          ┌──────────────────┘      └──────────────┐
          ▼                                        ▼
┌──────────────────────┐              ┌──────────────────────┐
│ live_room_categories │              │       experts        │
│ (多对多关联表)        │              │  category_id → categories│
└────────┬─────────────┘              └──┬───────┬──────────┘
         │                               │       │
         ▼                               ▼       ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│     live_rooms        │  │user_expert_      │  │live_session_      │
│  (直播房间 - 核心实体) │  │subscriptions    │  │experts           │
└─┬──┬──┬──┬──┬──┬──┬──┘  └──────────────────┘  └──────────────────┘
  │  │  │  │  │  │  │
  │  │  │  │  │  │  └──── brand_rooms ──── brands ──── brand_topics ──── topics
  │  │  │  │  │  │
  │  │  │  │  │  └──── live_room_official_accounts ──── official_accounts
  │  │  │  │  │
  │  │  │  │  └──── topic_category_rooms ──── topic_categories ──── topics
  │  │  │  │
  │  │  │  └──── live_room_tabs
  │  │  │
  │  │  └──── live_room_messages
  │  │
  │  └──── live_sessions ──── session_statistics (1:1)
  │          │       │
  │          │       └──── session_tags ──── tags
  │          │
  │          └──── watch_history
  │
  └──── user_favorites
```

---

## 四、详细表结构

### 4.1 直播核心表

#### live_rooms（直播房间表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| parent_room_id | UUID | FK→live_rooms.id, NULL | NULL | 父房间ID（自引用） |
| user_id | UUID | NOT NULL | - | 创建者ID（应用层验证） |
| title | VARCHAR(100) | NOT NULL | - | 房间标题 |
| description | TEXT | NULL | NULL | 房间描述 |
| cover_url | VARCHAR(255) | NULL | NULL | 封面图URL |
| stream_key | VARCHAR(255) | NOT NULL, UNIQUE | - | 推流密钥 |
| is_private | BOOLEAN | - | false | 是否为私有房间 |
| record_by_default | BOOLEAN | - | true | 是否默认录制 |
| external_room_id | VARCHAR(64) | NULL | NULL | 外部房间ID（幂等导入） |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：
- `idx_live_rooms_user_id` (user_id)
- `uq_live_rooms_user_external_room` (user_id, external_room_id) WHERE external_room_id IS NOT NULL

**外键关系**：
- parent_room_id → live_rooms.id (SET NULL)
- child_rooms (自引用反向)
- live_sessions (一对多)
- live_room_tabs (一对多)
- live_room_messages (一对多)
- live_room_categories (多对多→categories)
- brand_rooms (多对多→brands)
- topic_category_rooms (多对多→topics/topic_categories)
- live_room_official_accounts (多对多→official_accounts)
- user_favorites (一对多)

---

#### live_sessions（直播会话表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| room_id | UUID | FK→live_rooms.id, CASCADE | - | 所属房间ID |
| status | ENUM | NOT NULL | - | 状态：scheduled/live/finished/processing/ready/error |
| start_time | TIMESTAMPTZ | NOT NULL | - | 开始时间 |
| end_time | TIMESTAMPTZ | NULL | NULL | 结束时间 |
| video_id | UUID | NULL, UNIQUE | NULL | 录制视频ID |
| playback_url | VARCHAR(1024) | NULL | NULL | 回放地址 |
| playback_url_hash | VARCHAR(128) | NULL | NULL | 回放URL哈希（幂等） |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**状态枚举**：scheduled → live → finished → processing → ready / error

**索引**：
- `uq_live_sessions_room_playback_hash` (room_id, playback_url_hash) WHERE playback_url_hash IS NOT NULL

**外键关系**：
- room → live_rooms (多对一)
- statistics → session_statistics (一对一)
- live_session_experts (一对多→experts)
- session_tags (多对多→tags)
- watch_history (一对多)

---

#### session_statistics（会话统计表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| session_id | UUID | FK→live_sessions.id, CASCADE, UNIQUE | - | 关联会话（一对一） |
| peak_viewer_count | INTEGER | - | 0 | 峰值观看人数 |
| total_viewer_count | BIGINT | - | 0 | 总观看人数 |
| total_like_count | BIGINT | - | 0 | 总点赞数 |
| total_share_count | BIGINT | - | 0 | 总分享数 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

---

### 4.2 专家系统表

#### experts（专家信息表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NULL, UNIQUE | NULL | 关联平台用户ID（可选） |
| name | VARCHAR(120) | NOT NULL | - | 专家姓名 |
| title | VARCHAR(120) | NULL | NULL | 职称（如：主任医师） |
| hospital | VARCHAR(200) | NULL | NULL | 所属医院 |
| department | VARCHAR(120) | NULL | NULL | 细分科室 |
| expertise_areas | TEXT | NULL | NULL | 擅长领域 |
| bio | TEXT | NULL | NULL | 个人简介 |
| avatar_url | VARCHAR(512) | NULL | NULL | 头像URL |
| category_id | UUID | FK→categories.id, SET NULL | NULL | 主专业分类 |
| is_featured | BOOLEAN | NOT NULL | false | 是否首页推荐 |
| is_active | BOOLEAN | NOT NULL | true | 是否启用（软删除） |
| sort_order | INTEGER | NOT NULL | 0 | 排序顺序 |
| contact_info | JSONB | NULL | NULL | 联系方式JSON |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：
- `idx_experts_is_featured` (is_featured, sort_order)
- `idx_experts_is_active` (is_active)
- `idx_experts_user_id` (user_id)
- `idx_experts_category_id` (category_id)

---

#### user_expert_subscriptions（用户关注专家表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL | - | 用户ID（应用层验证） |
| expert_id | UUID | FK→experts.id, CASCADE | - | 专家ID |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 关注时间 |

**索引**：
- `uq_user_expert_subscriptions_user_expert` (user_id, expert_id) UNIQUE
- `idx_user_expert_subscriptions_user_id` (user_id)
- `idx_user_expert_subscriptions_expert_id` (expert_id)
- `idx_user_expert_subscriptions_created_at` (created_at)

---

#### live_session_experts（直播场次专家关联表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| session_id | UUID | FK→live_sessions.id, CASCADE | - | 场次ID |
| expert_id | UUID | FK→experts.id, CASCADE | - | 专家ID |
| role | VARCHAR(50) | NOT NULL | '主讲' | 角色：主讲/主持/嘉宾 |
| sort_order | INTEGER | NOT NULL | 0 | 显示顺序 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：
- `uq_live_session_experts_session_expert_role` (session_id, expert_id, role) UNIQUE
- `idx_live_session_experts_session` (session_id)
- `idx_live_session_experts_expert` (expert_id)
- `idx_live_session_experts_role` (session_id, role)

---

### 4.3 内容管理表

#### categories（全局分类表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| name | VARCHAR(100) | NOT NULL, UNIQUE | - | 分类名称 |
| slug | VARCHAR(120) | NULL | NULL | URL友好标识 |
| icon | VARCHAR(255) | NULL | NULL | 分类图标 |
| description | TEXT | NULL | NULL | 分类描述 |
| sort_order | INTEGER | NOT NULL | 0 | 排序权重（越小越靠前） |
| is_active | BOOLEAN | NOT NULL | true | 是否启用（软删除） |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_categories_sort_order`, `idx_categories_is_active`

---

#### tags（内容标签表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| name | VARCHAR(80) | NOT NULL, UNIQUE | - | 标签名称（全局唯一） |
| slug | VARCHAR(100) | NULL | NULL | URL友好标识 |
| description | TEXT | NULL | NULL | 标签描述 |
| is_active | BOOLEAN | NOT NULL | true | 是否启用（软删除） |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_tags_name`, `idx_tags_is_active`

---

#### session_tags（场次标签关联表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| session_id | UUID | PK, FK→live_sessions.id, CASCADE | - | 场次ID |
| tag_id | UUID | PK, FK→tags.id, CASCADE | - | 标签ID |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`idx_session_tags_session_id`, `idx_session_tags_tag_id`

---

#### live_room_categories（直播间分类关联表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| room_id | UUID | PK, FK→live_rooms.id, CASCADE | - | 直播间ID |
| category_id | UUID | PK, FK→categories.id, CASCADE | - | 分类ID |
| is_primary | BOOLEAN | NOT NULL | false | 是否主分类 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`idx_live_room_categories_room_id`, `idx_live_room_categories_category_id`

---

### 4.4 专题管理表

#### topics（专题活动表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL | - | 创建者ID |
| title | VARCHAR(100) | NOT NULL | - | 专题标题 |
| description | TEXT | NULL | NULL | 专题描述 |
| banner_url | VARCHAR(255) | NULL | NULL | 横幅图URL |
| status | ENUM | NOT NULL | draft | 状态：draft/published/archived |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_topics_user_id`, `idx_topics_status`, `idx_topics_created_at`

---

#### topic_categories（专题内分类表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| topic_id | UUID | FK→topics.id, CASCADE | - | 所属专题ID |
| name | VARCHAR(50) | NOT NULL | - | 分类名称 |
| sort_order | INTEGER | NOT NULL | 0 | 排序顺序 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_topic_categories_topic_id`, `idx_topic_categories_topic_sort` (topic_id, sort_order)
**约束**：`uq_topic_category_name` (topic_id, name) UNIQUE

---

#### topic_category_rooms（专题分类-直播间关联表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| category_id | UUID | FK→topic_categories.id, CASCADE | - | 分类ID |
| room_id | UUID | FK→live_rooms.id, CASCADE | - | 直播间ID |
| sort_order | INTEGER | NOT NULL | 0 | 排序顺序 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_tcr_category_id`, `idx_tcr_room_id`, `idx_tcr_category_sort`
**约束**：`uq_category_room` (category_id, room_id) UNIQUE

---

### 4.5 品牌管理表

#### brands（品牌表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| name | VARCHAR(150) | NOT NULL, UNIQUE | - | 品牌名称 |
| slug | VARCHAR(150) | NULL | NULL | URL友好标识 |
| logo_url | VARCHAR(512) | NULL | NULL | Logo图片URL |
| description | TEXT | NULL | NULL | 品牌描述 |
| website_url | VARCHAR(255) | NULL | NULL | 官网链接 |
| sort_order | INTEGER | NOT NULL | 0 | 排序权重 |
| is_active | BOOLEAN | NOT NULL | true | 软删除标识 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_brands_sort_order`, `idx_brands_is_active`, `idx_brands_active_sort` (is_active, sort_order) WHERE is_active = true

---

#### brand_topics（品牌-专题关联表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| brand_id | UUID | PK, FK→brands.id, CASCADE | - | 品牌ID |
| topic_id | UUID | PK, FK→topics.id, CASCADE | - | 专题ID |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`idx_brand_topics_brand_id`, `idx_brand_topics_topic_id`

---

#### brand_rooms（品牌-直播间关联表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| brand_id | UUID | PK, FK→brands.id, CASCADE | - | 品牌ID |
| room_id | UUID | PK, FK→live_rooms.id, CASCADE | - | 直播间ID |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`idx_brand_rooms_brand_id`, `idx_brand_rooms_room_id`

---

### 4.6 直播特性表

#### live_room_messages（直播间留言表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| room_id | UUID | FK→live_rooms.id, CASCADE | - | 房间ID |
| session_id | UUID | FK→live_sessions.id, SET NULL | NULL | 场次ID（可选） |
| user_id | UUID | NOT NULL | - | 留言用户ID |
| user_role | ENUM | NOT NULL | - | 用户角色快照：REGULAR/MODERATOR/ADMIN/SUPERADMIN |
| content | TEXT | NOT NULL | - | 留言内容 |
| is_deleted | BOOLEAN | NOT NULL | false | 是否删除 |
| extra | JSONB | NULL | NULL | 扩展数据 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`idx_live_room_messages_room_created` (room_id, created_at), `idx_live_room_messages_session_created` (session_id, created_at)

---

#### live_room_tabs（直播间Tab表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| room_id | UUID | FK→live_rooms.id, CASCADE | - | 房间ID |
| tab_key | VARCHAR(64) | NOT NULL | - | 系统级key |
| title | VARCHAR(128) | NOT NULL | - | 展示名称 |
| content_type | ENUM | NOT NULL | - | 内容类型：text/image/mixed |
| text_content | TEXT | NULL | NULL | 文本内容 |
| image_url | TEXT | NULL | NULL | 图片URL |
| sort_order | INTEGER | NOT NULL | 0 | 排序顺序 |
| is_active | BOOLEAN | NOT NULL | true | 是否启用 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_live_room_tabs_room_sort` (room_id, sort_order)

---

### 4.7 用户行为表

#### user_favorites（用户收藏表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL | - | 用户ID（应用层验证） |
| room_id | UUID | FK→live_rooms.id, CASCADE | - | 房间ID |
| is_active | BOOLEAN | NOT NULL | true | 是否有效（软删除） |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`uq_user_favorites_user_room` (user_id, room_id) UNIQUE, `idx_user_favorites_user_id`, `idx_user_favorites_room_id`

---

#### watch_history（观看历史表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL | - | 用户ID（应用层验证） |
| session_id | UUID | FK→live_sessions.id, CASCADE | - | 场次ID |
| progress | INTEGER | NULL | NULL | 观看进度（秒） |
| watched_at | TIMESTAMPTZ | NOT NULL | func.now() | 观看时间 |
| is_latest | BOOLEAN | NOT NULL | true | 是否最新记录 |

**索引**：`idx_watch_history_user_session` (user_id, session_id), `idx_watch_history_is_latest` (user_id, is_latest)

---

#### user_subscriptions（用户订阅提醒表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL | - | 用户ID（应用层验证） |
| target_type | ENUM | NOT NULL | - | 目标类型：room/session |
| target_id | UUID | NOT NULL | - | 目标ID（应用层验证） |
| is_active | BOOLEAN | NOT NULL | true | 是否有效（软删除） |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`uq_user_subscriptions_user_target` (user_id, target_id, target_type) UNIQUE, `idx_user_subscriptions_user_id`

---

### 4.8 用户偏好与通知表

#### user_preferences（用户偏好设置表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL, UNIQUE | - | 用户ID（一对一） |
| theme_mode | VARCHAR(20) | NOT NULL | auto | 主题：auto/light/dark/scheduled |
| theme_scheduled_dark_time | TIME | NULL | NULL | 定时深色开始 |
| theme_scheduled_light_time | TIME | NULL | NULL | 定时浅色开始 |
| pinned_categories | JSONB | NULL | NULL | 固定科室ID数组 |
| homepage_view_mode | VARCHAR(20) | NOT NULL | double | 首页视图：double/single |
| cellular_warning_enabled | BOOLEAN | NOT NULL | true | 流量提醒 |
| auto_reduce_quality | BOOLEAN | NOT NULL | true | 自动降画质 |
| auto_play_on_wifi | BOOLEAN | NOT NULL | false | WiFi自动播放 |
| extra | JSONB | NULL | NULL | 扩展偏好 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_user_preferences_user_id` (user_id)

---

#### notifications（用户通知表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL | - | 接收用户ID |
| title | VARCHAR(255) | NOT NULL | - | 通知标题 |
| content | TEXT | NULL | NULL | 通知内容 |
| notification_type | VARCHAR(50) | NOT NULL | system | 类型：system/subscription/interaction |
| related_id | UUID | NULL | NULL | 关联资源ID |
| related_type | VARCHAR(50) | NULL | NULL | 关联资源类型 |
| is_read | BOOLEAN | NOT NULL | false | 是否已读 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`idx_notifications_user_id`, `idx_notifications_user_is_read` (user_id, is_read), `idx_notifications_created_at`

---

### 4.9 搜索表

#### user_search_history（用户搜索历史表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| user_id | UUID | NOT NULL | - | 用户ID |
| keyword | VARCHAR(255) | NOT NULL | - | 原始关键词 |
| keyword_norm | VARCHAR(255) | NOT NULL | - | 规范化关键词 |
| search_count | INTEGER | NOT NULL | 1 | 搜索次数 |
| last_searched_at | TIMESTAMPTZ | NOT NULL | func.now() | 最近搜索时间 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`uq_user_search_history_user_keyword` (user_id, keyword_norm) UNIQUE, `idx_user_search_history_user_time` (user_id, last_searched_at)

---

#### search_keyword_stats（搜索关键词统计表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| keyword_norm | VARCHAR(255) | NOT NULL, UNIQUE | - | 规范化关键词 |
| keyword | VARCHAR(255) | NULL | NULL | 原始关键词（保留大小写） |
| total_count | BIGINT | NOT NULL | 0 | 总搜索次数 |
| last_searched_at | TIMESTAMPTZ | NOT NULL | func.now() | 最近搜索时间 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_search_keyword_stats_count` (total_count)

---

### 4.10 首页表

#### featured_content（焦点图配置表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| title | VARCHAR(255) | NOT NULL | - | 焦点图标题 |
| subtitle | VARCHAR(512) | NULL | NULL | 副标题 |
| image_url | VARCHAR(512) | NOT NULL | - | 图片URL |
| target_type | VARCHAR(50) | NULL | NULL | 目标类型：room/session/topic/brand/external |
| target_id | UUID | NULL | NULL | 目标ID |
| target_url | VARCHAR(512) | NULL | NULL | 外部链接（优先级高于target_id） |
| sort_order | INTEGER | NOT NULL | 0 | 排序权重 |
| is_active | BOOLEAN | NOT NULL | true | 是否启用 |
| start_at | TIMESTAMPTZ | NULL | NULL | 上线时间 |
| end_at | TIMESTAMPTZ | NULL | NULL | 下线时间 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_featured_content_active_sort` (is_active, sort_order), `idx_featured_content_schedule` (start_at, end_at)

---

### 4.11 公众号关联表

#### official_accounts（公众号表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | UUID | PK | uuid.uuid4() | 主键 |
| name | VARCHAR(100) | NOT NULL, UNIQUE | - | 公众号名称 |
| slug | VARCHAR(120) | NULL | NULL | URL友好标识 |
| app_id | VARCHAR(255) | NULL | NULL | 外部系统标识 |
| description | VARCHAR(500) | NULL | NULL | 描述 |
| is_active | BOOLEAN | NOT NULL | true | 是否启用 |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | func.now() | 更新时间 |

**索引**：`idx_official_accounts_name`, `idx_official_accounts_is_active`

---

#### live_room_official_accounts（直播间-公众号关联表）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| room_id | UUID | PK, FK→live_rooms.id, CASCADE | - | 直播间ID |
| account_id | UUID | PK, FK→official_accounts.id, CASCADE | - | 公众号ID |
| created_at | TIMESTAMPTZ | NOT NULL | func.now() | 创建时间 |

**索引**：`idx_live_room_official_accounts_room_id`, `idx_live_room_official_accounts_account_id`

---

## 五、数据迁移历史

| 迁移文件 | 执行日期 | 说明 |
|----------|----------|------|
| `add_experts_is_active.sql` | 2025 | 为 experts 表添加 is_active 字段和索引 |
| `20260531_add_keyword_to_search_keyword_stats.sql` | 2026-05-31 | 为 search_keyword_stats 添加 keyword 字段并回填 |
| `drop_live_rooms_category_id.sql` | - | 移除 live_rooms 表的 category_id 字段（迁移到多对多） |

---

## 六、Redis 缓存设计

### 6.1 缓存键命名规范

| 缓存类型 | Key 模式 | 数据类型 | 说明 |
|----------|----------|----------|------|
| 会话Token | session:{user_id} | Hash | JWT Token + 过期时间 + 用户信息 |
| 直播状态 | live:room:{room_id} | Hash | status, viewer_count, start_time |
| 聊天消息 | chat:{room_id} | List | 最近100条消息JSON |
| Celery队列 | (由Celery管理) | List | 异步任务队列 |

### 6.2 Redis 配置

| 参数 | 值 | 说明 |
|------|-----|------|
| Host | redis (Docker) / localhost (本地) | Redis 服务器地址 |
| Port | 6379 | 默认端口 |
| DB | 0 | Celery Broker + Result Backend |
| URL | redis://redis:6379/0 | 连接字符串 |

---

## 七、数据库操作规范

### 7.1 查询规范

- ✅ 使用 SQLAlchemy ORM，避免手写 SQL
- ✅ 大表查询使用分页（`limit` + `offset`）
- ✅ 避免 `SELECT *`，指定需要的列
- ✅ 复杂查询在 CRUD 层使用 `select()` 构建

### 7.2 事务管理

项目在 `get_async_db()` 中自动管理事务：

```python
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.is_active:
                await session.commit()    # 成功：提交
        except Exception:
            if session.is_active:
                await session.rollback()  # 失败：回滚
            raise
        finally:
            await session.close()
```

### 7.3 迁移规范

- 数据库变更必须编写 SQL 迁移文件
- 文件名格式：`YYYYMMDD_描述.sql`
- 迁移应包括正向操作和注释说明
- 生产环境使用迁移文件，开发环境可用 `create_tables` 脚本

---

## 八、性能优化建议

### 8.1 索引策略

- ✅ 所有外键字段已创建索引
- ✅ 常用查询字段（user_id, status, created_at）已创建索引
- ✅ 多对多关联表使用复合主键
- ⚠️ 需关注慢查询日志，按需添加复合索引

### 8.2 查询优化

- 使用 `.options(selectinload())` 预加载关联数据，避免 N+1 查询
- 大结果集使用分页（建议每页不超过 50 条）
- 搜索功能可考虑 PostgreSQL 全文搜索或 Elasticsearch

### 8.3 缓存策略

- 热点数据（首页内容、焦点图）可使用 Redis 缓存
- 建议设置合理的 TTL（如 5-15 分钟）
- 关注缓存穿透、击穿、雪崩问题

---

**最后更新**：2026-07-13