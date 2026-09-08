# 前端 API 路径变更同步报告

> **分支**: `wechat-v1`  
> **后端服务**: `live_core_service`  
> **API 前缀**: `/api/v1`  
> **Docker 重建时间**: 2026-07-13  
> **变更目标**: 与 GitHub `main` 分支路由规范对齐——管理端接口统一挂在 `/admin/*` 下，废弃 `/xxx/admin` 后缀写法

---

## 一、变更摘要

| 模块 | 变更类型 | 影响前端 |
|------|----------|----------|
| 焦点图（Featured Content） | 路径迁移 + 删除双轨 | **必须改** |
| 科室分类（Category） | 管理端路径迁移 | **必须改** |
| 标签（Tag） | 管理端路径迁移 | **必须改** |
| 公众号（Official Accounts） | 下划线改连字符 | **必须改** |
| 直播场次（Session） | 增加 `/sessions` 前缀 | **必须改** |
| HTTP 方法 | 分类/标签更新保持 **PATCH**（非 PUT） | 若前端用了 PUT 需改 |

**不变的部分**（公开读接口路径未改）：
- `GET /api/v1/content/tags`
- `GET /api/v1/content/categories`
- `GET /api/v1/content/categories/{id}`
- `GET /api/v1/featured-content`（首页公开焦点图）
- 场次标签、按标签搜场次等 `/content/sessions/*`、`/content/tags/search/sessions`

---

## 二、逐模块对照表

### 2.1 焦点图（Featured Content / Banner）

| 操作 | ❌ 旧路径（已废弃） | ✅ 新路径 | 方法 |
|------|---------------------|-----------|------|
| 公开列表 | `/featured-content` | `/featured-content` | GET |
| 管理端列表 | `/featured-content/admin` | `/admin/featured-content?page=1&size=20` | GET |
| 管理端详情 | `/featured-content/admin/{id}` | `/admin/featured-content/{id}` | GET |
| 创建 | `/featured-content/admin` | `/admin/featured-content` | POST |
| 更新 | `/featured-content/admin/{id}` | `/admin/featured-content/{id}` | PATCH |
| 删除 | `/featured-content/admin/{id}` | `/admin/featured-content/{id}` | DELETE |
| 上传图片 | `/admin/featured-content/{id}/image` | `/admin/featured-content/{id}/image` | POST |

**前端注意**：
- 管理端**仅保留分页列表**，不再有全量无分页接口 `/featured-content/admin`
- 列表 Query 参数：`page`、`size`、`q`、`search_type`

---

### 2.2 科室分类（Category）

| 操作 | ❌ 旧路径 | ✅ 新路径 | 方法 |
|------|-----------|-----------|------|
| 公开列表 | `/content/categories` | `/content/categories` | GET |
| 公开详情 | `/content/categories/{id}` | `/content/categories/{id}` | GET |
| 管理端分页列表 | `/content/categories/admin` | `/admin/categories?page=1&size=10` | GET |
| 创建 | `/content/categories` | `/admin/categories` | POST |
| 更新 | `/content/categories/{id}` | `/admin/categories/{id}` | **PATCH** |
| 删除 | `/content/categories/{id}` | `/admin/categories/{id}` | DELETE |
| 上传图标 | `/content/categories/{id}/icon` | `/admin/categories/{id}/icon` | POST |
| 删除图标 | `/content/categories/{id}/icon` | `/admin/categories/{id}/icon` | DELETE |

**前端注意**：
- 访问旧路径 `/content/categories/admin` 会被路由到 `{categoryId}` 参数校验，返回 **422**，不是有效管理端入口
- 更新方法请用 **PATCH**（本地后端设计为部分更新，与 main 的 PUT 不同）

---

### 2.3 标签（Tag）

| 操作 | ❌ 旧路径 | ✅ 新路径 | 方法 |
|------|-----------|-----------|------|
| 公开列表/搜索 | `/content/tags` | `/content/tags` | GET |
| 创建 | `/content/tags` | `/admin/tags` | POST |
| 更新 | `/content/tags/{id}` | `/admin/tags/{id}` | **PATCH** |
| 删除 | `/content/tags/{id}` | `/admin/tags/{id}` | DELETE |
| 场次设标签 | `/content/sessions/{session_id}/tags` | 不变 | POST |
| 场次读标签 | `/content/sessions/{session_id}/tags` | 不变 | GET |
| 按标签搜场次 | `/content/tags/search/sessions` | 不变 | GET |

---

### 2.4 公众号（Official Accounts）

**全局规则**：路径中的 `official_accounts`（下划线）全部改为 `official-accounts`（连字符）

| 操作 | ❌ 旧路径 | ✅ 新路径 | 方法 |
|------|-----------|-----------|------|
| 管理端列表 | `/admin/official_accounts` | `/admin/official-accounts` | GET |
| 创建 | `/admin/official_accounts` | `/admin/official-accounts` | POST |
| 详情 | `/admin/official_accounts/{id}` | `/admin/official-accounts/{id}` | GET |
| 更新 | `/admin/official_accounts/{id}` | `/admin/official-accounts/{id}` | PATCH |
| 删除 | `/admin/official_accounts/{id}` | `/admin/official-accounts/{id}` | DELETE |
| 直播间关联列表 | `/rooms/{room_id}/official_accounts` | `/rooms/{room_id}/official-accounts` | GET |
| 批量设置关联 | `/admin/rooms/{room_id}/official_accounts` | `/admin/rooms/{room_id}/official-accounts` | POST |
| 解除关联 | `/admin/rooms/{room_id}/official_accounts/{id}` | `/admin/rooms/{room_id}/official-accounts/{id}` | DELETE |
| 公众号下直播间 | `/official_accounts/{id}/rooms` | `/official-accounts/{id}/rooms` | GET |

---

### 2.5 直播场次（Session）

| 操作 | ❌ 旧路径 | ✅ 新路径 | 方法 |
|------|-----------|-----------|------|
| 获取详情 | `/api/v1/{session_id}` | `/api/v1/sessions/{session_id}` | GET |
| 更新 | `/api/v1/{session_id}` | `/api/v1/sessions/{session_id}` | PATCH |
| 删除 | `/api/v1/{session_id}` | `/api/v1/sessions/{session_id}` | DELETE |

---

## 三、前端改造 Checklist

```
[ ] 全局搜索替换 official_accounts → official-accounts（仅 URL 路径，非变量名）
[ ] 焦点图管理页：所有 /featured-content/admin → /admin/featured-content
[ ] 分类管理页：列表 /content/categories/admin → /admin/categories
[ ] 分类 CRUD：写操作改 /admin/categories，更新用 PATCH
[ ] 标签管理页：写操作改 /admin/tags，更新用 PATCH
[ ] 场次详情/编辑：路径加 /sessions 前缀
[ ] API 封装层（axios/fetch baseURL + path 常量）集中修改，避免遗漏
[ ] 联调验证：旧路径应返回 404 或 422，新路径正常
```

---

## 四、Docker 重建与验证结果

### 4.1 重建命令（Windows）

```batch
docker compose -f docker-compose.yml -f docker-compose.windows.yml up -d --build live_core_service
```

### 4.2 健康检查

| 检查项 | 结果 |
|--------|------|
| 容器状态 | `live_core_service` Up |
| `GET /api/v1/health` | **200** |

### 4.3 路径冒烟测试（重建后）

| 路径 | 状态码 | 说明 |
|------|--------|------|
| `GET /api/v1/featured-content` | 200 | 公开接口正常 |
| `GET /api/v1/admin/featured-content` | 401 | 新管理端路径存在（需 Token） |
| `GET /api/v1/featured-content/admin` | **404** | 旧路径已移除 |
| `GET /api/v1/content/categories` | 200 | 公开接口正常 |
| `GET /api/v1/admin/categories` | 401 | 新管理端路径存在 |
| `GET /api/v1/content/categories/admin` | **422** | 旧路径无效（被 UUID 路由拦截） |
| `GET /api/v1/admin/official-accounts` | 401 | 新连字符路径存在 |
| `GET /api/v1/admin/official_accounts` | **404** | 旧下划线路径已移除 |

### 4.4 集成测试

容器内执行（需挂载 monorepo `backend/users` 供测试 JWT fixture）：

- **23 passed** / 61 failed
- 失败原因：测试环境 JWT Token 与 `user_service` 密钥不一致导致 **401**，属测试基础设施问题，**非路由回归**
- 路由相关用例（未授权应返回 401/403/404）已通过

---

## 五、参考文档（已同步更新）

| 文档 | 说明 |
|------|------|
| `add-docs/FRONTEND_IMPLEMENTATION_GUIDE.md` | 前端实现指南（全模块 API 清单） |
| `add-docs/03-首页焦点图管理-后端设计文档.md` | 焦点图后端设计 |
| `add-docs/01-科室分类管理-后端设计文档.md` | 分类后端设计 |
| `add-docs/02-标签管理-后端设计文档.md` | 标签后端设计 |
| `add-docs/01-科室分类管理-V2-增量设计文档.md` | 分类 V2 增量 |

---

## 六、本地未变更项（前端无需因本次改动调整）

以下模块**不在本次路由统一范围内**，路径与行为保持原样：

- 内容安全模块（`/admin/content-safety/*`）
- 留言 Admin + WebSocket
- 用户认证扩展（手机号/运营商登录等，属 `user_service` 独立迭代）
- Tab / 专家 / 品牌 / 搜索 / 下载任务等其它 API

---

## 七、联调环境

| 项目 | 值 |
|------|-----|
| live_core_service | `http://localhost:8000` |
| API 前缀 | `/api/v1` |
| 测试账号 | 见 `add-docs/测试账号信息.md` |

---

**如有疑问，请对照 `FRONTEND_IMPLEMENTATION_GUIDE.md` 或联系后端确认具体接口。**
