# API 路由规范统一修改提示词母版

**版本**: V1.0  
**创建日期**: 2026-06-17  
**用途**: 指导 AI 对直播核心服务（live_core_service）、用户服务（user_service）、媒体下载服务（media_download_service）的 API 路由设计进行规范化检查和统一修改。  
**适用范围**: 所有后端微服务的 FastAPI 路由层（endpoint 文件 + api.py + Nginx 配置）。  
**原则**: 最小安全幅度、不引入前端破坏性变更、所有修改须经测试验证。

---

## 1. 角色定义 (Role Definition)

你是一名精通 FastAPI 路由设计、RESTful API 架构和 Nginx 反向代理配置的资深后端架构师。你的任务是：

1. **检查**：审查当前项目所有微服务的 API 路由设计，识别不符合规范的模式
2. **修改**：在确保不引起项目冲突的前提下，以最小安全幅度修正所有违规项
3. **验证**：同步更新相关测试文件，确保修改后所有现有测试继续通过

---

## 2. 路由规范定义

### 2.1 Router 拆分规范

> **一个资源模块 = 一个文件 = 多个 APIRouter（按角色拆分）**

| Router 变量命名 | 适用场景 | api.py 注册 prefix |
|----------------|---------|-------------------|
| `{resource}_public_router` | 匿名/公开 GET 列表和详情 | 按资源路径（如 `/content`） |
| `{resource}_user_router` | 登录用户 self 操作 | `""`（路径自带 `/users/me`） |
| `{resource}_admin_router` | 管理员 CRUD | `"/admin"` |
| `{resource}_internal_router` | 内部服务间回调 | `"/internal"` |

> 不是每个模块都需要全部四种，只创建实际需要的。

### 2.2 Admin 路径规范

**统一为 `/admin/<资源>` 前缀模式**：

| ✅ 正确 | ❌ 错误 |
|--------|--------|
| `/admin/experts` | `/categories/admin` |
| `/admin/brands` | `/featured-content/admin` |
| `/admin/content/categories` | `POST /categories`（路径无 admin 标识） |
| `/admin/content/tags` | `POST /tags`（路径无 admin 标识） |
| `/admin/notifications` | — |
| `/admin/rooms/{id}/tabs` | — |

### 2.3 路径命名规范

**统一使用 kebab-case**：

| ✅ 正确 | ❌ 避免 |
|--------|--------|
| `/featured-content` | `/featured_content` |
| `/hot-keywords` | `/hot_keywords` |
| `/batch-status` | `/batch_status` |
| `/is-favorited` | `/is_favorited` |
| `/topic-categories` | `/topic_categories` |
| `/official-accounts` | `/official_accounts` |
| `/on-publish` | `/on_publish` |

### 2.4 Prefix 定义位置规范

**统一在 `api.py` 中指定 prefix，endpoint 文件不设 prefix**：

```python
# ❌ 不推荐 — endpoint 文件内定义
# auth.py
router = APIRouter(prefix="/auth")

# ✅ 推荐 — endpoint 文件不设 prefix
# auth.py
router = APIRouter()

# api.py 中指定
api_router.include_router(auth.router, prefix="/auth")
```

### 2.5 禁止双注册

同一个 Router 不得以两个 prefix 注册两次。

```python
# ❌ 禁止
api_router.include_router(router, prefix="/content")
api_router.include_router(router, prefix="")      # 别名

# ✅ 选一个前缀
api_router.include_router(router, prefix="/content")
```

### 2.6 Router 命名规范

**不得使用通用名 `router`，必须使用描述性名称**：

| ❌ 禁止 | ✅ 推荐 |
|--------|--------|
| `router = APIRouter()` | `room_router = APIRouter()` |
| `router = APIRouter()` | `auth_router = APIRouter()` |
| `router = APIRouter()` | `download_router = APIRouter()` |

---

## 3. 违规模式检查清单

执行修改前，必须逐项检查以下违规模式：

### 3.1 🔴 严重违规（必须修复）

| # | 违规项 | 检查方法 | 目标状态 |
|---|--------|---------|---------|
| 1 | Admin 路径使用后缀而非前缀 | grep `"/xxx/admin"` 在 endpoint 文件 | 全部改为 `/admin/xxx` |
| 2 | Admin CRUD 路径无 admin 标识 | 查看 POST/PUT/DELETE 路由的路径 | 全部加 `/admin` 前缀 |
| 3 | 同一 Router 双注册 | api.py 中同一个 router 多次 `include_router` | 仅保留一次注册 |
| 4 | Nginx proxy_pass 路径不匹配 | nginx.conf 中 `proxy_pass` 缺少 `/api/v1/` | 补充完整路径 |

### 3.2 🟠 中等违规（建议修复）

| # | 违规项 | 检查方法 | 目标状态 |
|---|--------|---------|---------|
| 5 | 公开和管理路由混在同一 Router | 单文件内 `@router` 同时有公开和授权路由 | 拆分为 `{name}_public_router` + `{name}_admin_router` |
| 6 | URL 路径使用 snake_case | grep `_` 在路径字符串中 | 改为 kebab-case |
| 7 | Prefix 定义在 endpoint 文件内 | `APIRouter(prefix=...)` 在 endpoint 文件 | 移到 api.py |

### 3.3 🟢 轻微违规（可选修复）

| # | 违规项 | 检查方法 | 目标状态 |
|---|--------|---------|---------|
| 8 | Router 变量使用通用名 `router` | `router = APIRouter()` | 改为 `{resource}_router` |
| 9 | Orphan router 变量 | api.py 中未引用的 router 变量 | 删除 |

---

## 4. 修改执行流程

### 4.1 第一步：全量审计

阅读所有 endpoint 文件和 api.py，对照以上规范输出违规清单（文件:行 + 问题描述 + 建议修复）。

### 4.2 第二步：分模块修改（严格按此顺序）

```
1. P0 严重违规 — admin 后缀修正 + 双注册消除
   ├── homepage_search.py：/featured-content/admin → /admin/featured-content
   └── content_management.py：/categories/admin → /admin/categories + 消除双注册

2. P1 中等违规 — Router 拆分
   ├── brand.py：router → brand_public_router + brand_admin_router
   └── user_preference_notification.py：router → user_router + admin_router

3. P2 轻微违规 — prefix 位置统一 + 路径命名 + router 命名
   ├── session.py：prefix 从 endpoint 移到 api.py
   ├── 用户板块 4 文件：prefix 从 endpoint 移到 api.py
   ├── nginx.conf：/api/dl/ proxy_pass 修复
   ├── 全部 endpoint 文件：router → {name}_router
   ├── liveroom_official_accounts.py：official_accounts → official-accounts
   └── internal.py + 测试文件：on_publish → on-publish

4. P3 验证
   └── 同步更新所有测试文件中的 URL 引用
```

### 4.3 第三步：同步测试文件

修改 endpoint 路径后，必须同步更新以下位置的 URL 引用：

| 位置 | 搜索模式 |
|------|---------|
| `tests/integration/test_api_*.py` | 旧 URL 路径字符串 |
| `frontend/src/` | API 调用路径 |

> 前端若无引用，标注"零影响"并跳过。

### 4.4 第四步：验证

**对每个修改过的测试文件**，在 Docker 容器中以 `run_preload.py` 模式运行：

```powershell
docker cp "backend\live_core_service\tests\integration\{test_file}.py" {container}:/app/tests/integration/
docker exec {container} python /app/run_preload.py
```

确认失败数未增加（或合理减少）即为通过。

---

## 5. 各板块路径转换规则速查

### 5.1 Nginx 对外 → 内部转换

| Nginx 对外路径 | FastAPI 内部路径 | 转换规则 |
|---------------|-----------------|---------|
| `/api/users/...` | `user_service:8002/api/v1/...` | 去掉 `/api/users`，拼接 `/api/v1` |
| `/api/core/...` | `live_core_service:8000/api/v1/...` | 去掉 `/api/core`，拼接 `/api/v1` |
| `/api/v1/...` | `media_download_service:8001/api/v1/...` | 路径保持不变 |
| `/api/dl/...` | `media_download_service:8001/api/v1/...` | 去掉 `/api/dl`，拼接 `/api/v1` |

### 5.2 改造前 → 改造后路径对照

| 模块 | 改造前（❌） | 改造后（✅） |
|------|-----------|-----------|
| homepage_search | `GET /featured-content/admin` | `GET /admin/featured-content` |
| content_management | `GET /categories/admin` | `GET /admin/categories` |
| content_management | `POST /categories`（无 admin） | `POST /admin/categories` |
| content_management | `POST /tags`（无 admin） | `POST /admin/tags` |
| content_management | 双注册 `/content` + `""` | 单注册 `/content` |
| liveroom | `/official_accounts` | `/official-accounts` |
| internal | `/on_publish` | `/on-publish` |

### 5.3 Router 名称对照

| 文件 | 改造前 | 改造后 |
|------|--------|--------|
| room.py | `router` | `room_router` |
| session.py | `router` | `session_router` |
| topic.py | `router` | `topic_router` |
| internal.py | `router` | `internal_router` |
| health.py | `router` | `health_router` |
| user_behavior.py | `router` | `user_behavior_router` |
| homepage_search.py | `router` | `featured_content_public_router` |
| brand.py | `router` | `brand_public_router` + `brand_admin_router` |
| user_preference_notification.py | `router` | `user_router` + `admin_router` |
| content_management.py | `router` | `content_public_router` + `content_admin_router` |
| auth.py | `router` | `auth_router` |
| users.py | `router` | `users_router` |
| download.py | `router` | `download_router` |

---

## 6. 实施记录（2026-06-17 已完成）

### 6.1 修改统计

| 批次 | 内容 | 文件数 |
|------|------|--------|
| P0 | homepage_search admin 后缀修正 | 1 |
| P0 | content_management admin 后缀 + 双注册消除 | 2 |
| P1 | brand Router 拆分 | 2 |
| P1 | user_preference_notification Router 拆分 | 2 |
| P2 | prefix 位置统一（session + 用户板块 5 文件） | 6 |
| P2 | Nginx /api/dl/ 修复 | 1 |
| P2 | 全局 router 重命名（15 文件） | 15 |
| P2 | snake_case → kebab-case（4 文件 + 3 测试） | 7 |
| P3 | 测试文件路径同步（6 测试文件） | 6 |
| **合计** | | **42** |

### 6.2 前端影响

前端 `src/` 目录下无任何本次修改涉及的 API 路径引用，**零前端修改**。

### 6.3 测试结果

| 状态 | 数量 | 说明 |
|------|------|------|
| ✅ 全部通过 | 95 | 路由相关测试全部通过 |
| 🟡 非路由相关失败 | 17 | 4 个 validator 首次生效 + 13 个已有测试隔离 bug |

### 6.4 规范文档

详见 `app修改记录/API路由规范统一方案.md`（完整路由清单 + 诊断汇总）。

---

## 7. 使用本母版的方法

### 7.1 新建项目时（预防）

在新模块开发时，将以下内容作为 code review checklist：

```markdown
- [ ] Router 按角色拆分（public/user/admin/internal）
- [ ] Admin 路径使用 `/admin/<resource>` 前缀
- [ ] 所有 URL 路径使用 kebab-case
- [ ] prefix 在 api.py 中定义，不在 endpoint 文件中
- [ ] 同一 Router 不重复注册
- [ ] Router 变量使用描述性命名，不用 `router`
```

### 7.2 已有项目改造时（治疗）

```markdown
@本母版 请对 {服务名} 进行 API 路由规范化检查和修改
```

AI 将按 Section 4 的流程执行全量审计 → 分模块修改 → 同步测试 → 验证。
