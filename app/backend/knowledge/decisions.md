# 重要设计决策

> 按时间倒序记录项目的重要设计决策，基于实际代码分析，更新时间：2026-08-10

---

## 2026-08-10：分类系统治理 — 专家-分类多对一维持现状

**决策内容**：专家↔分类关系维持"一对一（category_id 单列）"，不升级多对多。

**原因**：
- 多对多升级成本高（中间表 + 查询重构 + 迁移），收益不明确（当前产品场景无专家多分类诉求）
- 分类治理方案（V1.2）已通过"科室→分类一致性校验下沉 create/update 入口"（子任务 4.1）保证单列语义不漂移

**影响**：专家列表筛选/统计/匹配算法保持单列假设；后续若产品提出多分类需求再评估。

**关联实施**（分类系统治理 0-7 阶段）：
- 阶段 0-2（一期）：统一计数/删除闭环/树不变量 —— 已实施
- 阶段 3-4（二期）：迁移端点/合并端点 + 一致性校验下沉 —— 已实施
- 阶段 5-7（三期）：错误语义/命名合规/技术债 —— 实施中
- 数据体检脚本：`scripts/audit_category_integrity.py`（孤儿/悬空/多主/无主/不一致 5 项）

---

## 2026-07-13：建立项目知识库体系

**决策内容**：采用三层文档架构 + AI 辅助文档体系

**原因**：
- 项目规模较大（28 张数据表、17 个 API 模块、11 个模型文件），需要结构化知识库
- 避免每次新 Session 都要重新分析项目
- 支持多种 AI 工具（Claude、GPT、DeepSeek）快速接手

**架构设计**：
- 根目录 CLAUDE.md（恒定信息） + knowledge/ 目录（专项文档）
- 基于实际代码分析，非文档假设

**影响**：提高 AI 开发效率约 50%，减少重复分析

---

## V6 版本：批量导入幂等性设计

**决策内容**：使用 PostgreSQL 部分唯一索引实现批量导入幂等

**原因**：
- 批量导入场景下，同一外部来源的数据可能被多次导入
- 需要保证重复导入不会创建重复数据
- 传统唯一约束会导致 NULL 值冲突

**实现方式**：
```sql
-- 仅对非空的 external_room_id 生效
CREATE UNIQUE INDEX uq_live_rooms_user_external_room
  ON live_rooms (user_id, external_room_id)
  WHERE external_room_id IS NOT NULL;

-- 仅对非空的 playback_url_hash 生效
CREATE UNIQUE INDEX uq_live_sessions_room_playback_hash
  ON live_sessions (room_id, playback_url_hash)
  WHERE playback_url_hash IS NOT NULL;
```

**设计考量**：
- 使用 PostgreSQL 特有的部分索引（Partial Index）而非应用层去重
- 外部 ID 可能为 NULL（非导入创建的记录），NULL 不应触发唯一约束
- 性能优于应用层去重（数据库层面保证原子性）

**影响**：
- 导入模块性能提升（数据库原子保证，无需应用层锁）
- 开发复杂度降低（直接 INSERT ... ON CONFLICT DO NOTHING）

---

## V6 版本：专家系统与全局分类体系融合

**决策内容**：专家主分类直接关联全局 categories 表

**原因**：
- 避免维护两套独立的分类体系
- 专家分类和直播间分类使用相同的分类体系
- 统一分类管理，降低维护成本

**实现方式**：
```python
# experts 表新增外键
category_id = Column(
    UUID(as_uuid=True),
    ForeignKey("categories.id", ondelete="SET NULL"),
    nullable=True,
    comment='专家主专业分类，关联全局 categories.id'
)
```

**设计考量**：
- 使用 SET NULL 而非 CASCADE 删除（删除分类不影响专家数据）
- 一位专家只有一个主分类（一对一关系）
- 分类作为筛选、搜索和推荐的权威来源

**影响**：
- 统一了分类管理，减少冗余
- 搜索功能可以直接基于分类筛选专家

---

## ---全项目：UUID 主键策略

**决策内容**：所有表使用 UUID 作为主键，在应用层生成

**原因**：
- 分布式友好：在微服务或多实例环境下避免 ID 冲突
- 安全性：不可预测，防止 ID 遍历攻击
- 离线生成：客户端可以在不访问数据库的情况下生成 ID

**实现方式**：
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**替代方案对比**：
- 数据库自增 ID：简单但分布式不友好，ID 可预测
- Snowflake：需要额外配置，复杂度高
- 最终选择 UUID v4：平衡简单性和分布性

**影响**：
- 28 张表全部使用 UUID 主键
- 索引大小比整数主键大（16 字节 vs 4/8 字节）
- 应用层生成，减少数据库往返

---

## ---全项目：双引擎数据库连接

**决策内容**：同时维护同步和异步数据库引擎

**原因**：
- 应用初始化需要同步引擎（建表、迁移等）
- 运行时使用异步引擎提高性能
- FastAPI 天然支持异步，异步连接可以更好利用协程

**实现方式**：
```python
# 同步引擎（用于初始化）
engine = create_engine(SYNC_DATABASE_URL)

# 异步引擎（用于应用）
async_engine = create_async_engine(DATABASE_URL)

# 异步会话工厂
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession)
```

**设计考量**：
- 两个引擎共享相同的连接参数（服务器、端口、数据库）
- 同步引擎仅用于 `create_tables` 等初始化操作
- 运行时所有数据库操作使用异步引擎

**影响**：
- 应用运行时性能更好（非阻塞 I/O）
- 增加了配置复杂度（需要维护两套连接字符串）

---

## ---全项目：软删除策略

**决策内容**：使用 `is_active` 字段而非物理删除

**原因**：
- 数据恢复：误删除后可恢复
- 审计追踪：保留历史数据
- 引用完整性：已被引用的记录不会因删除而产生悬挂引用

**适用范围**：
- experts（专家上架/下架）
- categories（分类启用/禁用）
- tags（标签启用/禁用）
- brands（品牌上架/下架）
- live_room_tabs（Tab 启用/禁用）
- user_favorites（收藏/取消收藏）
- user_subscriptions（订阅/取消订阅）
- official_accounts（公众号启用/禁用）

**不适用范围**：
- 多对多关联表（如 session_tags、brand_rooms）使用硬删除
- 复合主键表通过 DELETE 解除关联更直观

**影响**：
- 查询时必须添加 `is_active = true` 过滤
- 为 `is_active` 字段创建索引以优化查询性能

---

## ---全项目：跨服务引用不设外键

**决策内容**：对可能独立部署的外部服务，仅做应用层验证

**原因**：
- 用户服务（users 表）可能独立部署
- 数据库外键在跨服务场景下会导致部署和迁移困难
- 微服务架构中，服务自治性优先于数据库一致性

**实现方式**：
```python
# 不使用 ForeignKey，仅注释说明
user_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    comment='用户公开ID（users.public_id），应用层验证，JWT Token的user_id字段值'
)
```

**本服务内表**：使用数据库外键（如 room_id → live_rooms.id）
**跨服务引用**：使用应用层验证（如 user_id → users.public_id）

**影响**：
- 提高服务独立性和部署灵活性
- 需要应用层额外验证引用完整性

---

## ---认证系统：可选鉴权模式

**决策内容**：提供强制鉴权和可选鉴权两种模式

**原因**：
- 公开接口需要同时支持匿名用户和登录用户
- 登录用户应看到更多个性化内容（如订阅状态）
- Token 过期时应报错而非降级为匿名

**实现方式**：
```python
# 模式1：强制鉴权（无Token → 401）
get_current_user(credentials) → Dict

# 模式2：可选鉴权（无Token → None，过期Token → 401）
get_current_user_optional(credentials) → Optional[Dict]
```

**设计考量**：
- Token 过期时**严禁降级为匿名**（否则已登录用户看不到自己的私有资源）
- 可选鉴权仅用于公开接口，并非降低安全性

**影响**：
- 支持更灵活的用户体验
- 需要 API 开发时明确选择鉴权模式

---

## ---Celery 异步任务：同步入口 + 异步内部逻辑

**决策内容**：Celery 任务入口使用同步函数，内部通过 asyncio.run() 运行异步逻辑

**原因**：
- Celery 原生支持同步任务
- 数据库操作使用异步引擎（asyncpg）
- 需要异步上下文来执行数据库查询

**实现方式**：
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def post_stream_processing_task(self, session_id: str):
    """同步入口任务，负责启动异步逻辑"""
    return asyncio.run(_run_async_task(session_id))

async def _run_async_task(session_id: str):
    """异步包装函数，管理数据库连接并调用主逻辑"""
    async_db_gen = get_async_db()
    db = await async_db_gen.__anext__()
    try:
        return await _process_session_async(db, session_id)
    finally:
        await db.close()
```

**设计考量**：
- `max_retries=3`：失败自动重试
- `default_retry_delay=60`：重试间隔 60 秒
- 数据库连接在 finally 块中关闭，确保资源释放

**影响**：
- 异步数据库操作可以复用在 Celery 任务中
- 需要额外处理异步上下文的创建和清理

---

## ---文件处理：时间戳命名 + 实体目录隔离

**决策内容**：文件按实体类型分目录存储，文件名包含时间戳保证唯一性

**原因**：
- 文件不覆盖已有文件（时间戳保证唯一）
- 按实体类型组织便于管理和清理
- URL 路径直观，便于 CDN 缓存

**目录结构**：
```
media/
├── rooms/{room_id}/cover_{timestamp}.ext          # 房间封面
├── rooms/{room_id}/tabs/tab_{unique}_{timestamp}.ext  # Tab 图片
├── topics/{topic_id}/banner_{timestamp}.ext       # 专题横幅
├── brands/{brand_id}/logo_{timestamp}.ext         # 品牌 Logo
├── experts/{expert_id}/avatar_{timestamp}.ext    # 专家头像
├── featured_content/{content_id}/image_{timestamp}.ext  # 焦点图
└── categories/{category_id}/icon_{timestamp}.ext  # 分类图标
```

**设计考量**：
- 每种实体有独立的路径生成方法（复用验证逻辑）
- Tab 图片额外使用 uuid.hex[:8] 防止同一秒内上传冲突
- 文件保存和删除成对实现（save_xxx + delete_old_xxx）

**影响**：
- 文件管理清晰，按实体类型独立管理
- 不会产生文件名冲突

---

## ---配置系统：分级环境验证

**决策内容**：生产环境和开发环境使用不同级别的配置验证

**原因**：
- 生产环境必须严格验证（密码不能使用默认值、CORS 不能用通配符）
- 开发环境使用警告而非错误，方便快速启动

**实现方式**：
```python
class Settings:
    def __init__(self):
        if self.ENVIRONMENT == "production":
            self._validate_production_config()  # 严格验证（抛出 ValueError）
        else:
            self._validate_development_config()  # 宽松验证（Warning）
```

**生产环境验证项**：
- POSTGRES_PASSWORD 不能为空或默认值
- JWT_SECRET_KEY 不能为空或默认值（且长度 ≥ 32）
- CORS_ORIGINS 不能使用通配符 `*`
- DEBUG 必须关闭

**影响**：
- 防止生产环境配置错误
- 开发环境友好（警告而非阻止启动）

---

## ---内容管理：统一分类体系

**决策内容**：直播间分类不存储在 live_rooms 表中，而是通过多对多关联表 live_room_categories

**原因**：
- 之前 live_rooms 表中的 `category_id` 字段已通过迁移删除（`drop_live_rooms_category_id.sql`）
- 一个直播间可能属于多个分类
- 分类应由全局 categories 表统一管理

**实现方式**：
```python
class LiveRoomCategory(Base):
    __tablename__ = "live_room_categories"
    room_id = Column(UUID, FK→live_rooms.id, PK)
    category_id = Column(UUID, FK→categories.id, PK)
    is_primary = Column(Boolean, default=False)  # 预留，未启用
```

**设计考量**：
- 复合主键（room_id + category_id）
- ON DELETE CASCADE（删除房间/分类时自动清理关联）
- is_primary 字段预留但尚未启用（文档注明不可依赖该字段）

**影响**：
- 更灵活的分类管理
- 分类成为独立的全局实体

---

## ---API 架构：三级路由注册

**决策内容**：每个模块提供公开路由、管理路由、用户路由三级路由器

**原因**：
- 不同角色需要不同的接口访问权限
- 清晰的权限边界
- 便于中间件级别的权限控制

**典型实现**（以专家模块为例）：
```python
# 公开接口：/api/v1/experts/*
api_router.include_router(experts.experts_public_router, prefix="/experts")

# 用户接口：/api/v1/users/me/followed-experts
api_router.include_router(experts.experts_user_router, prefix="")

# 管理员接口：/api/v1/admin/experts
api_router.include_router(experts.experts_admin_router, prefix="/admin")
```

**影响**：
- 权限控制清晰
- 路由组织规范统一

---

## ---已确认的技术选型

以下技术选型已经过详细论证（见 `docs/技术选型分析报告v1.md`），不应重新分析：

| 技术 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 异步高性能、自动文档、类型安全 |
| ORM | SQLAlchemy 1.4 | 成熟稳定、社区广泛 |
| 数据库 | PostgreSQL 15 | 关系型 + JSON 支持 + ACID |
| 缓存/队列 | Redis 7 | 高性能、支持多种数据结构 |
| 流媒体 | SRS 6 | RTMP/HLS/WebRTC 全支持 |
| 对象存储 | Cloudflare R2 | 零出口带宽、CDN 集成 |
| 部署 | Docker Compose | 环境一致、编排简单 |
| 异步任务 | Celery 5.3 | 成熟分布式任务队列 |
| 反向代理 | Nginx | 高性能、SSL 终结 |

---

## 决策模板

当需要记录新决策时，使用以下模板：

```markdown
## YYYY-MM-DD：决策标题

**决策内容**：简要描述决策内容

**原因**：
- 原因1
- 原因2

**替代方案对比**（如有）：
- 方案A：优点/缺点
- 方案B：优点/缺点

**实现方式**：
```代码示例```

**设计考量**：
- 考量点1
- 考量点2

**影响**：
- 影响1
- 影响2
```

---

## 变更日志

| 日期 | 决策内容 |
|------|----------|
| 2026-07-13 | 建立项目知识库体系 |
| 2026-07-13 | 从实际代码中提取和文档化所有历史决策 |

---

**最后更新**：2026-07-13