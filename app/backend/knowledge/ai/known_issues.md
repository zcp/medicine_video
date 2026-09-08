# AI 辅助开发 - 已知问题和注意事项

> 基于实际项目修复文档和代码分析，记录已知问题和需要避免的重复分析内容，更新时间：2026-07-13

---

## 一、历史修复问题（避免重复犯同样的错误）

### 1.1 路由注册遗漏

**问题**：`batch_import` 和 `session_import` 路由在 `api.py` 中未被 import 和注册，导致所有导入端点返回 404。

**修复**：在 `app/api/v1/api.py` 中添加 import 和 `include_router` 调用。

**教训**：新增 API 端点时，必须同时：
1. 创建端点文件
2. 在 `api.py` 中 import
3. 在 `api.py` 中注册路由

**参考文档**：`backend/live_core_service/路由注册修复说明.md`

---

### 1.2 UUID 构造崩溃

**问题**：测试环境中的 `current_user` 字典没有 `public_id` 字段，直接调用 `UUID(current_user.get("public_id"))` 当值为 `None` 时抛出 TypeError。

**修复**：改为多级回退：
```python
public_id_str = current_user.get("public_id") or current_user.get("user_id") or current_user.get("sub")
if not public_id_str:
    return error_response(code=3001, message="用户身份信息缺失")
public_id = UUID(public_id_str)
```

**教训**：
- 永远不要对可能为 None 的值直接调用 `UUID()`
- `UUID(None)` 会抛出 `TypeError`，而非返回 None

**参考文档**：`backend/live_core_service/UUID构造错误修复说明.md`

---

### 1.3 Deprecation Warning

**问题**：FastAPI 新版本中 `Query(regex=...)` 已废弃，需改为 `Query(pattern=...)`。

**修复**：全局替换 `regex` 参数为 `pattern`。

**教训**：升级 FastAPI 版本时注意 API 变更。

---

### 1.4 编码问题

**问题**：GBK 编码导致 `UnicodeEncodeError`。

**原因**：Windows 环境默认 GBK 编码，Python 控制台输出 Unicode 字符时报错。

**修复**：
- 脚本中设置 UTF-8 编码
- 使用兼容字符替代特殊 Unicode 字符

**教训**：跨平台开发注意编码问题，测试时使用 `PYTHONIOENCODING=utf-8` 环境变量。

---

### 1.5 外键约束缺失

**问题**：部分表缺少外键约束导致数据一致性问题。

**修复**：补充缺失的外键定义。

**参考文档**：`backend/live_core_service/修复外键约束缺失问题.md`

---

## 二、当前已确认的问题

### 2.1 Celery 任务中的占位逻辑

**文件**：`app/tasks/session_processing.py`

**问题**：
```python
await asyncio.sleep(5)  # 模拟视频处理
```

**说明**：当前 Celery 任务的视频处理使用 `asyncio.sleep(5)` 占位，**不是完整的实现**。实际视频处理逻辑需要集成 FFmpeg 转码。

**不要假设**：任务已完成完整实现。当前的 session status 流转只是模拟。

---

### 2.2 get_db 别名覆盖

**文件**：`app/database.py`

**问题**：
```python
get_db = get_async_db  # 第93行
```

**说明**：`get_db` 被重新赋值为异步版本，覆盖了原始的同步版本。这可能导致同步初始化代码失败。

**需要注意**：
- 如果代码中需要同步数据库连接，不能使用 `get_db`
- 同步操作应使用 `SessionLocal` 手动管理会话

---

### 2.3 数据库枚举使用 SQLAlchemy Enum

**文件**：`app/models/live_core.py`

**问题**：
```python
status = Column(SAEnum(LiveSessionStatus, values_callable=lambda obj: [e.value for e in obj]), ...)
```

**说明**：当前使用 SQLAlchemy 的 Enum 类型在数据库中创建 PostgreSQL 原生 ENUM。这种方式的缺点是：
- 添加新状态值需要数据库迁移（ALTER TYPE ... ADD VALUE）
- 迁移回滚比较困难

**替代方案**（未来可考虑）：使用 VARCHAR + Python Enum 验证，更灵活。

---

### 2.4 is_primary 字段未启用

**文件**：`app/models/content_management.py`

```python
is_primary = Column(Boolean, nullable=False, default=False, comment="是否为主分类（规则尚未启用；启用前不得依赖该字段做业务判断）")
```

**说明**：`live_room_categories` 表的 `is_primary` 字段已定义但**业务规则尚未启用**。当前不要依赖此字段做任何业务判断。

---

### 2.5 搜索功能无全文索引

**现状**：`search_keyword_stats` 和 `user_search_history` 使用 `keyword_norm` 字段进行精准匹配。

**待实现**：全文搜索功能，可考虑：
- PostgreSQL `tsvector` + `tsquery` 全文搜索
- 或引入 Elasticsearch

---

## 三、不要重复分析的内容

### 3.1 已确认不做修改的部分

以下逻辑已经过验证，**不要重新分析或修改**：

| 模块 | 文件 | 原因 |
|------|------|------|
| JWT 认证 | `app/core/auth.py` | 稳定运行，无需修改 |
| 配置验证 | `app/core/config.py` | 生产/开发双模式验证已完成 |
| 数据库连接 | `app/database.py` | 双引擎模式已确认 |
| Celery 配置 | `app/tasks/celery_app.py` | Broker/Backend 配置已固定 |
| 异常体系 | `app/core/exceptions.py` | 两种核心异常已定义 |
| 响应格式 | `app/core/response.py` | 统一格式不可变更 |

---

### 3.2 已确认的实现模式

以下实现模式已经过团队确认，**新代码必须遵循**：

1. **UUID 主键**：所有表使用 UUID，在应用层 `uuid.uuid4()` 生成
2. **双时间戳**：`created_at` + `updated_at`（`onupdate=func.now()`）
3. **软删除**：核心实体使用 `is_active` 字段
4. **跨服务引用**：不设数据库外键，在注释中说明
5. **三级路由**：public → user → admin
6. **五层架构**：API → Service → CRUD → Model → Database
7. **部分唯一索引**：幂等导入使用 `WHERE ... IS NOT NULL`
8. **异常处理**：捕获具体异常，重新抛出 HTTPException

---

## 四、常见陷阱

### 4.1 路由注册顺序

**陷阱**：在 `/rooms` prefix 下的路由，**具体路径必须注册在参数化路径之前**。

```python
# ✅ 正确：batch_import 先注册
api_router.include_router(batch_import.router, prefix="/rooms")    # /rooms/import/batch
api_router.include_router(room.router, prefix="/rooms")            # /rooms/{room_id}

# ❌ 错误：参数化路径先注册，/import/batch 会被 {room_id} 匹配
```

**影响文件**：`app/api/v1/api.py` 路由注册部分。

---

### 4.2 跨服务 user_id 的获取

**陷阱**：`current_user` 字典的键在不同环境下不同。

```python
# ❌ 错误：直接取值可能为 None
user_uuid = UUID(current_user.get("public_id"))

# ✅ 正确：多级回退
user_id_str = (
    current_user.get("public_id") or 
    current_user.get("user_id") or 
    current_user.get("sub")
)
if not user_id_str:
    raise HTTPException(401, "用户身份信息缺失")
user_uuid = UUID(user_id_str)
```

---

### 4.3 异步测试中的 pytest 配置

**配置**：`pytest.ini`
```ini
[pytest]
pythonpath = /app
asyncio_mode = strict
```

**陷阱**：`asyncio_mode = strict` 要求所有异步测试使用 `@pytest.mark.asyncio` 装饰器。

---

### 4.4 环境变量加载顺序

**陷阱**：根目录 `.env` 和 `backend/live_core_service/.env` 可能冲突。

**说明**：当前 `main.py` 中使用 `load_dotenv()` 加载环境变量，如果多级 `.env` 文件存在同名变量，**后加载的会覆盖先加载的**。

---

## 五、技术债务清单

| # | 问题 | 严重程度 | 预计修复时间 |
|---|------|----------|-------------|
| 1 | Celery 视频处理为占位逻辑 | 高 | 待定 |
| 2 | `is_primary` 字段业务规则未实现 | 中 | 待定 |
| 3 | 全文搜索未实现 | 中 | 待定 |
| 4 | get_db 别名覆盖可能导致混淆 | 中 | 待定 |
| 5 | DB Enum 类型迁移困难 | 低 | 长期规划 |
| 6 | 前端应用未开发 | 高 | 待定 |

---

## 六、部署注意事项

### 6.1 媒体文件持久化

**关键配置**：
```yaml
volumes:
  - /var/www/html/live-core-media:/app/media
```

**陷阱**：如果没有挂载卷，容器重启后媒体文件会丢失。

---

### 6.2 多个 .env 文件

项目中存在多个 `.env` 位置：
- 根目录 `.env`
- `backend/live_core_service/.env`
- `.env.docker`（Docker 环境）

**注意**：修改环境变量时需确认正确的文件。

---

### 6.3 PostgreSQL 数据库初始化

Docker Compose 中通过 `init-db.sh` 初始化多个数据库：
```yaml
volumes:
  - ./init-db.sh:/docker-entrypoint-initdb.d/init-db.sh:ro
```

生产环境部署时需确保此文件存在且可执行。

---

## 七、变更日志

| 日期 | 更新内容 |
|------|----------|
| 2026-07-13 | 基于实际项目修复文档和代码分析，完全重写已知问题文档 |

---

**最后更新**：2026-07-13