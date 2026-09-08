# API 路由规范统一方案

> 创建日期：2026-06-17
> 状态：✅ 已实施完成
> 最后更新：2026-06-17
> 修改文件总数：37 个（25 个 endpoint 文件 + 3 个 api.py + 3 个测试文件 + 1 个 nginx.conf + 5 个注释/文档）

---

## 一、当前后端 API 架构总览

### 1.1 板块划分

项目采用 **三微服务 + Nginx 网关** 架构，对外统一入口为 `https://mp.dayilive.com`：

```
┌──────────────────────────────────────────────────────────────────┐
│                         Nginx 统一入口                             │
│                     https://mp.dayilive.com                       │
├──────────┬──────────────────┬───────────────┬────────────────────┤
│  板块 A  │     板块 B        │    板块 C     │      板块 D         │
│  用户     │   直播核心         │   媒体下载     │    静态资源          │
│ /api/users│  /api/core        │  /api/v1      │  /media, /uploads   │
│          │                  │  /api/dl      │  /hls, /live         │
└──────────┴──────────────────┴──────────────┴────────────────────┘
```

### 1.2 Nginx 路径转换规则

| Nginx 对外路径 | 实际转发目标 | 转换规则 |
|---------------|-------------|---------|
| `/api/users/...` | `user_service:8002/api/v1/...` | 去掉 `/api/users`，拼接 `/api/v1` |
| `/api/core/...` | `live_core_service:8000/api/v1/...` | 去掉 `/api/core`，拼接 `/api/v1` |
| `/api/v1/...` | `media_download_service:8001/api/v1/...` | 路径保持不变 |
| `/api/dl/...` | `media_download_service:8001/api/v1/...` | 去掉 `/api/dl`，拼接 `/api/v1`（已修复 ✅） |

---

## 二、现有 API 设计风格分类

当前代码中存在 **5 种不同的设计风格**：

### 风格一：独立 Router 分离法 ✅ 推荐

**做法**：按访问角色（公开/用户/管理员）拆分为多个 APIRouter，在 `api.py` 中分别指定 prefix。

**代表模块**：`experts.py`, `live_features.py`, `liveroom_official_accounts.py`

> ✅ **全部模块已统一为此风格**：`brand.py`, `user_preference_notification.py`, `content_management.py`, `homepage_search.py` 均已改造为独立 Router 分离法。

```python
# experts.py — 4 个 Router
experts_featured_router    # prefix=""          → /api/v1/featured-experts
experts_public_router      # prefix="/experts"  → /api/v1/experts/*
experts_user_router        # prefix=""          → /api/v1/users/me/followed-experts
experts_admin_router       # prefix="/admin"    → /api/v1/admin/experts/*
```

**admin 路径模式**：`/admin/<资源>` ✅

### 风格二：单 Router 混合 + `/admin/` 路径前缀 ⚠️ 已修复

**做法**：单个 Router 包含公开和管理路由，admin 接口通过路径嵌入 `/admin/` 区分。

**代表模块**：~~`brand.py`, `user_preference_notification.py`~~

> ✅ 已改造为风格一，拆分为 `brand_public_router` + `brand_admin_router`，`user_router` + `admin_router`。

```python
# brand.py — 1 个 Router，15 个路由
@router.get("/brands")                        # 公开
@router.get("/rooms/{id}/brands")              # 公开
@router.post("/admin/brands")                  # 管理
@router.get("/admin/brands")                   # 管理
@router.delete("/admin/brands/{id}")           # 管理
```

**admin 路径模式**：`/admin/<资源>` ✅（路径前缀正确，只是 router 未拆分）

### 风格三：单 Router 混合 + `admin` 作为路径后缀 ❌ 已修复

**做法**：admin 接口路径中 `admin` 出现在**末尾**而非前缀位置。

**代表模块**：~~`content_management.py`（主 router）, `homepage_search.py`（主 router）~~

> ✅ 已改造为风格一。content_management 拆为 `content_public_router` + `content_admin_router`，去除双注册别名。homepage_search 拆为 `featured_content_public_router` + `featured_content_admin_router`，admin 后缀全部改为前缀模式。

```python
# content_management.py — 1 个主 Router
@router.get("/categories/admin")               # ❌ admin 在末尾
@router.post("/categories")                    # ❌ 管理接口，但路径无 admin 标识
@router.put("/categories/{id}")               # ❌ 同上
@router.delete("/categories/{id}")            # ❌ 同上
@router.post("/tags")                          # ❌ 同上

# homepage_search.py — 主 Router
@router.get("/featured-content")               # 公开
@router.get("/featured-content/admin")         # ❌ admin 在末尾
@router.post("/featured-content/admin")        # ❌ admin 在末尾
```

### 风格四：用户专属路由（无 admin）

**做法**：所有路由在 `/users/me/...` 下，无管理端接口。

**代表模块**：`user_behavior.py`

### 风格五：无认证 / 内部回调

**做法**：无 `Depends(get_current_user)`，公开或内部服务调用。

**代表模块**：`internal.py`, `health.py`

---

## 三、各板块问题诊断汇总

### 3.1 板块 A：用户板块 (`user_service`)

| 子模块 | Router 变量名 | prefix 位置 | 状态 |
|--------|-------------|------------|------|
| health | `health_router` | api.py | ✅ |
| auth | `auth_router` | api.py | ✅ 已修复 |
| users | `users_router` | api.py | ✅ 已修复 |
| membership_products | `membership_products_router` | api.py | ✅ 已修复 |
| subscriptions | `subscriptions_router` | api.py | ✅ 已修复 |

### 3.2 板块 B：直播核心板块 (`live_core_service`)

| 子模块 | 路由数 | Router 数 | Router 命名 | 状态 |
|--------|--------|----------|-----------|------|
| room | 10 | 2 | `room_router`, `users_me_rooms_router` | ✅ |
| session | 3 | 1 | `session_router` | ✅ 已修复 |
| topic | 18 | 3 | `topic_router`, `category_router`, `room_router` | ✅ |
| live_features | 9 | 3 | `admin_tab_router`, `public_tab_router`, `public_message_router` | ✅ |
| experts | 13 | 4 | `experts_*_router` ×4 | ✅ |
| liveroom_official_accounts | 10 | 4 | `*_official_accounts_router` ×4 | ✅ kebab 已修复 |
| brand | 15 | 2 | `brand_public_router`, `brand_admin_router` | ✅ 已修复 |
| user_behavior | 9 | 2 | `user_behavior_router`, `room_favorite_router` | ✅ |
| user_preference_notification | 11 | 2 | `user_router`, `admin_router` | ✅ 已修复 |
| content_management | 17 | 4 | `content_public_router`, `content_admin_router`, `live_room_categories_router`, `live_room_categories_admin_router` | ✅ 已修复 |
| homepage_search | 10 | 4 | `featured_content_public_router`, `featured_content_admin_router`, `homepage_router`, `search_router` | ✅ 已修复 |
| search_extra | 6 | 2 | `search_history_router`, `search_extra_router` | ✅ |
| batch_import | 1 | 1 | `batch_import_router` | ✅ |
| session_import | 1 | 1 | `session_import_router` | ✅ |
| internal | 4 | 1 | `internal_router` | ✅ kebab 已修复 |
| health | 3 | 1 | `health_router` | ✅ |

### 3.3 板块 C：媒体下载板块 (`media_download_service`)

| 子模块 | 路由数 | Router 命名 | 状态 |
|--------|--------|-----------|------|
| download | 22 | `download_router` | ✅ Nginx 已修复，router 已重命名 |

---

## 四、统一规范

### 4.1 Router 拆分规范

> 一个资源模块 = 一个文件 = 多个 Router（按角色拆分）

| Router 变量命名 | 适用场景 | api.py 注册 prefix |
|----------------|---------|-------------------|
| `{resource}_public_router` | 匿名/公开 GET | 按资源路径 |
| `{resource}_user_router` | 登录用户 self 操作 | `""`（路径自带 `/users/me`） |
| `{resource}_admin_router` | 管理员 CRUD | `"/admin"` |
| `{resource}_internal_router` | 内部服务间回调 | `"/internal"` |

> 不是每个模块都需要全部四种，只创建实际需要的。

### 4.2 Admin 路径规范

**统一为 `/admin/<资源>` 前缀模式**：

| ✅ 正确 | ❌ 错误 |
|--------|--------|
| `/admin/experts` | `/categories/admin` |
| `/admin/brands` | `/featured-content/admin` |
| `/admin/content/categories` | `POST /categories`（无 admin 标识） |
| `/admin/content/tags` | `POST /tags`（无 admin 标识） |
| `/admin/notifications` | — |
| `/admin/rooms/{id}/tabs` | — |

### 4.3 路径命名规范

**统一使用 kebab-case**：

| ✅ 正确 | ❌ 避免 |
|--------|--------|
| `/featured-content` | `/featured_content` |
| `/hot-keywords` | `/hot_keywords` |
| `/batch-status` | `/batch_status` |
| `/is-favorited` | `/is_favorited` |
| `/topic-categories` | `/topic_categories` |

### 4.4 Prefix 定义位置规范

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

### 4.5 禁止双注册

同一个 Router 不得以两个 prefix 注册两次。如需兼容别名，使用 Nginx rewrite。

```python
# ❌
api_router.include_router(content_management.router, prefix="/content")
api_router.include_router(content_management.router, prefix="")      # 别名，禁止

# ✅ 选一个前缀，如需兼容在 Nginx 做 rewrite
api_router.include_router(content_management.router, prefix="/content")
```

---

## 五、改造计划（✅ 已全部完成）

### 5.1 实施记录

所有改造按以下顺序执行，每一步独立验证：

| 批次 | 模块 | 改动内容 | 文件数 | 路径变化 |
|------|------|---------|--------|---------|
| 1 | `homepage_search.py` | admin 后缀 → 前缀 | 1 | 是 |
| 2 | `content_management.py` + `api.py` | admin 后缀 → 前缀 + 双注册消除 | 2 | 是 |
| 3 | `brand.py` + `api.py` | Router 拆分 | 2 | 否 |
| 4 | `user_preference_notification.py` + `api.py` | Router 拆分 | 2 | 否 |
| 5 | `session.py` + `api.py`（两服务） | prefix 迁移到 api.py | 4 | 否 |
| 6 | `auth.py`, `users.py`, `membership_products.py`, `subscriptions.py` + `api.py` | prefix 迁移到 api.py | 8 | 否 |
| 7 | `nginx.conf` | `/api/dl/` proxy_pass 修复 | 1 | 否（修复路由匹配） |
| 8 | 全部 endpoint 文件 | 通用 `router` 重命名（15 文件） | 15 | 否 |
| 9 | `liveroom_official_accounts.py` + `api.py` | snake_case → kebab-case | 2 | 是 |
| 10 | `internal.py` + 3 个测试文件 | snake_case → kebab-case | 4 | 是 |

### 5.2 修改文件总数

| 服务 | 文件数 |
|------|--------|
| live_core_service endpoint | 16 |
| live_core_service api.py | 1 |
| users endpoint | 5 |
| users api.py | 1 |
| media_download endpoint | 1 |
| media_download api.py | 1 |
| 测试文件 | 3 |
| nginx.conf | 1 |
| orphan router 清理 | 2 |
| **合计** | **31** |

### 5.3 内容管理模块详细改造对照
## 六、统一后的路由规范速查

```
┌─────────────────────────────────────────────────────────┐
│              统一 API 路由命名规范                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. 角色拆分：每个模块按角色创建独立 APIRouter            │
│     xxx_public_router  → prefix = "/<resource>"          │
│     xxx_user_router    → prefix = ""  (/users/me/...)    │
│     xxx_admin_router   → prefix = "/admin"               │
│     xxx_internal_router → prefix = "/internal"           │
│                                                          │
│  2. Admin 统一前缀：/admin/<resource>                     │
│                                                          │
│  3. 路径命名：kebab-case                                 │
│                                                          │
│  4. Prefix 定义：统一在 api.py 中设定                     │
│                                                          │
│  5. 一个 Router 只挂载一次，禁止双注册                    │
│                                                          │
│  6. Nginx 对外：/api/core/<内部路径>                      │
└─────────────────────────────────────────────────────────┘
```

---

## 七、完整路由清单（改造后目标状态）

### 7.1 板块 B — live_core_service

```
/api/v1/health                          [无认证]   健康检查
/api/v1/health/ready                    [无认证]   就绪检查
/api/v1/health/config                   [无认证]   配置检查

/api/v1/internal/srs/on-publish         [无认证]   SRS 推流回调
/api/v1/internal/srs/on-unpublish       [无认证]   SRS 停流回调
/api/v1/internal/srs/on_record_mp4      [无认证]   SRS 录制回调

# === 直播间 (room) ===
/api/v1/rooms                           [可选]     直播间列表
/api/v1/rooms                           [严格]     创建直播间
/api/v1/rooms/{id}                      [可选]     直播间详情
/api/v1/rooms/{id}                      [严格]     更新/删除直播间
/api/v1/rooms/{id}/sub-venues           [可选]     子直播间
/api/v1/rooms/{id}/sessions             [严格]     创建会话 / [可选] 列表
/api/v1/rooms/{id}/cover                [严格]     上传封面
/api/v1/users/me/rooms                  [严格]     我的直播间

# === 会话 (session) ===
/api/v1/sessions/{id}                   [可选]     详情 / [严格] 更新/删除

# === 专题 (topic) ===
/api/v1/topics                          [可选]     专题列表 / [严格] 创建
/api/v1/topics/{id}                     [可选]     详情 / [严格] 更新
/api/v1/topics/{id}/banner              [严格]     上传 banner
/api/v1/topics/batch-status             [可选]     批量状态
/api/v1/topic-categories               [可选]     分类列表
/api/v1/rooms/{id}/topics               [可选]     直播间专题

# === 专家 (experts) ===
/api/v1/featured-experts               [无认证]   推荐专家
/api/v1/experts                         [无认证]   专家列表
/api/v1/experts/{id}                    [可选]     专家详情
/api/v1/experts/{id}/sessions           [可选]     专家会话
/api/v1/experts/{id}/is-followed        [严格]     是否已关注
/api/v1/sessions/{id}/experts           [严格]     会话关联专家
/api/v1/users/me/followed-experts       [严格]     关注/列表
/api/v1/users/me/followed-experts/{id}  [严格]     取消关注
/api/v1/admin/experts                   [严格]     管理列表 / 创建
/api/v1/admin/experts/{id}              [严格]     更新 / 删除
/api/v1/admin/experts/{id}/avatar       [严格]     上传头像
/api/v1/admin/experts/batch-import      [严格]     批量导入

# === 选项卡 (tab) ===
/api/v1/rooms/{id}/tabs                 [可选]     公开选项卡
/api/v1/admin/rooms/{id}/tabs           [严格]     管理选项卡
/api/v1/admin/tabs/{id}                 [严格]     更新/删除选项卡

# === 留言 (message) ===
/api/v1/rooms/{id}/messages             [可选]     留言列表 / [严格] 发送

# === 品牌 (brand) — 拆分 public/admin router ===
/api/v1/brands                          [可选]     品牌列表
/api/v1/brands/{id}/content             [可选]     品牌内容
/api/v1/rooms/{id}/brands               [可选]     直播间品牌
/api/v1/admin/brands                    [严格]     管理列表 / 创建
/api/v1/admin/brands/{id}               [严格]     详情 / 更新 / 删除
/api/v1/admin/brands/{id}/logo          [严格]     上传 logo
/api/v1/admin/brands/{id}/topics        [严格]     关联专题
/api/v1/admin/brands/{id}/rooms         [严格]     关联直播间
/api/v1/admin/rooms/{id}/brands         [严格]     管理直播间品牌

# === 内容管理 (content_management) — 拆分 public/admin router ===
/api/v1/content/categories              [可选]     分类列表（公开）
/api/v1/content/tags                    [可选]     标签列表（公开）
/api/v1/content/tags/search/sessions    [可选]     按标签搜索会话
/api/v1/content/sessions/{id}/tags      [可选]     场次标签列表 / [严格] 设置/删除
/api/v1/rooms/{id}/categories           [可选]     直播间分类（公开）
/api/v1/admin/categories                [严格]     管理分类列表（分页） / 创建
/api/v1/admin/categories/{id}           [严格]     更新 / 删除 / 上传图标
/api/v1/admin/tags                      [严格]     创建标签
/api/v1/admin/tags/{id}                 [严格]     更新 / 删除
/api/v1/admin/rooms/{id}/categories     [严格]     设置/删除直播间分类

# === 通知 (notification) — 拆分 public/admin router ===
/api/v1/users/me/preferences            [严格]     偏好查询 / 更新
/api/v1/users/me/notifications          [严格]     通知列表
/api/v1/users/me/notifications/unread   [严格]     未读数
/api/v1/users/me/notifications/read-all [严格]     全部已读
/api/v1/users/me/notifications/{id}     [严格]     标记已读
/api/v1/admin/notifications             [严格]     管理列表 / 创建
/api/v1/admin/notifications/{id}        [严格]     更新 / 删除
/api/v1/admin/notifications/batch-delete[严格]     批量删除

# === 首页 & 搜索 ===
/api/v1/homepage                        [无认证]   首页数据
/api/v1/featured-content                [无认证]   焦点图（公开）
/api/v1/admin/featured-content          [严格]     管理焦点图列表 / 创建
/api/v1/admin/featured-content/{id}     [严格]     详情 / 更新 / 删除
/api/v1/admin/featured-content/{id}/image [严格]   上传焦点图图片
/api/v1/search                          [可选]     搜索
/api/v1/search/hot-keywords            [无认证]   热搜词
/api/v1/search/suggestions             [无认证]   搜索建议
/api/v1/search/recommendations          [可选]     推荐
/api/v1/users/me/search-history         [严格]     搜索历史

# === 公众号关联 ===
/api/v1/rooms/{id}/official-accounts    [可选]     公开列表
/api/v1/official-accounts/{id}/rooms   [严格]     公众号房间列表
/api/v1/admin/official-accounts         [严格]     管理 CRUD
/api/v1/admin/rooms/{id}/official-accounts [严格] 管理关联

# === 导入 ===
/api/v1/rooms/import/batch              [严格]     批量导入直播间
/api/v1/rooms/{id}/sessions/import      [严格]     导入会话
```
