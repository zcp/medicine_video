# AGENTS.md — Live Streaming SaaS Frontend

## Project Overview

uni-app (Vue 3 + TypeScript + Vite) cross-platform frontend targeting **WeChat Mini Program and native mobile apps** (Android/iOS). Uses Pinia for state, Element Plus for H5 desktop UI. Backend API at `124.220.235.226:8000`, proxied in dev via Vite.

> **⚠️ 实施范围（重要）**：当前所有页面开发与修改只考虑 **App 端（微信小程序 + 原生 App）** 及 `src/pages/shared/` 共享页面。**`src/pages/h5/` 下的 H5 页面不在实施范围内**——除非需求明确要求，否则不开发、不修改、不评估 H5 端页面实现。

## Essential Architecture

### Cross-Platform Model
Pages live in **two platform-specific trees** plus a shared tree:
- `src/pages/h5/` — H5-only pages (desktop/browser) — **⚠️ 不在当前实施范围，除非需求明确要求否则不处理**
- `src/pages/app/` — Native app & Mini Program pages  — **⚠️ 当前实施范围（所有页面改动以此为主）**
- `src/pages/shared/` — Platform-agnostic pages (auth callback, 404)

Platform branching uses **uni-app conditional compilation comments**:
```
// #ifdef H5
// H5-only code
// #endif
// #ifndef H5
// App/Mini Program code  
// #endif
```

Routing/navigation helpers in `src/utils/router.ts` and `src/utils/navigation.ts` encapsulate this — **always use them instead of raw `uni.navigateTo`** when targeting a page that exists in both trees.

### API Layer (`src/api/`)

Every API module exports functions returning `Promise<ApiResponse<T>>` or `Promise<ApiResponse<PaginatedResponse<T>>>` (defined in `src/types/common.ts`). The wrapper shape is:
```ts
{ code: number; message: string; data: T; timestamp: string }
// Paginated adds: { total, page, size, items[] }
```

- **Base API URL**: from `ENV_CONFIG.VITE_BASE_API_URL` (`src/config/env.ts`), defaults to `http://localhost:8000/api/v1`
- **Auth endpoints** use a separate `VITE_AUTH_API_URL` — see `authUrl()` helper in `src/api/auth.ts`
- **Request helpers**: `get`, `post`, `put`, `del` from `@/utils/request` — they auto-inject JWT `Authorization` header when `auth: true` (see `src/api/room.ts` for canonical examples)
- **Token auto-refresh**: The request interceptor in `src/utils/request.ts` detects tokens expiring within 5 minutes and refreshes *before* the request (skips refresh for `/auth/refresh` to avoid loops)

### State Management (`src/store/`)

Pinia stores mirror the API modules (e.g., `src/api/room.ts` ↔ `src/store/room.ts`). Key patterns:
- `auth.ts` — JWT token lifecycle (storage, decode, refresh), user profile, `initializeAuth()` called at app launch
- `player.ts` — Playback state and statistics (separate from room/session stores)
- Stores use `ref`/`computed` Composition API style (not `state/getters` options style)

### Media/Image Handling (Critical)

**Always use `resolveMediaUrl(path)`** (`src/utils/url.ts`) when displaying any backend-returned image/avatar path. The backend stores relative paths like `/uploads/avatar/1_xxx.png`; `resolveMediaUrl` converts them to full URLs using `VITE_MEDIA_BASE_URL` (or derives origin from `VITE_BASE_API_URL`).

For **external images on APP** (e.g., expert avatars from third-party domains), use `<ProxyImage>` (`src/components/common/ProxyImage.vue`) — it downloads via `uni.downloadFile`, saves locally, and caches for 7 days. Plain `<image>` with external URLs **will not render on APP**.

Default avatar: `DEFAULT_AVATAR` constant from `src/constants/assets.ts` (inline SVG data URI — no HTTP dependency).

### Chinese Character Handling
- `pinyin-pro` library for pinyin conversion
- `src/utils/pinyin.ts` provides `getFirstLetter()` for A-Z grouping and sorting
- Expert/brand lists sorted by pinyin first letter (A-Z groups, then `#` for non-Chinese)

## Build & Development

| Command | Purpose |
|---------|---------|
| `pnpm dev:h5` | H5 dev server (port 5173) |
| `pnpm dev:mp-weixin` | WeChat Mini Program dev |
| `pnpm build:h5` | Production H5 build → `dist/` |
| `pnpm lint` | ESLint |
| `pnpm format` | Prettier |
| `pnpm test` / `pnpm test:run` | Vitest (watch / single run) |

**Production base path** is `/live-center/` (set in `vite.config.ts` via `base`).

### Environment Config
Copy `.env.example` to `.env.development` and `.env.production`. Key vars:
- `VITE_BASE_API_URL` — primary API base
- `VITE_AUTH_API_URL` — auth service base
- `VITE_USE_MOCK=true` — bypass backend, use local mock data

## Testing

**Vitest** is the test runner (Jest config exists but is legacy). All tests in `tests/`.

Critical setup (`vitest.setup.ts`):
- **All `uni.*` APIs are mocked** — if you add a new `uni.xxx()` call in source, add a corresponding mock
- `@dcloudio/uni-ui` components must be listed in `deps.inline` in `vite.config.ts` (E SM interop)
- `uni-datetime-picker` is aliased to `tests/EmptyComponent.vue` to avoid compilation errors

## Project-Specific Conventions

1. **Import alias**: `@/` → `src/` (configured in both `tsconfig.json` paths and `vite.config.ts` resolve.alias)
2. **JWT token storage**: `uni.getStorageSync('jwt_token')` / `uni.setStorageSync('jwt_token', token)`. Access via `getToken()` exported from `src/store/auth.ts`, not directly.
3. **Frontend data scoping**: The backend does NOT have a `/users/me/rooms` endpoint. "My rooms" filtering is done client-side by comparing `room.user_id === authStore.user.user_id` — see repo memory at `/memories/repo/frontend-data-scoping.md`.
4. **Avatar fallback chain**: host avatar → room cover → `DEFAULT_AVATAR` constant. On `<image @error>`, mutate the current item's avatar to prevent repeated broken-image render loops (see `/memories/repo/avatar-fallbacks.md`).
5. **IPv4 image URLs**: `normalizeImageUrl()` in `src/utils/url.ts` keeps `http://` for IPv4 addresses (not upgraded to HTTPS) — needed for dev environments with local network backends.
6. **Element Plus** is globally registered in `src/main.ts` (all components + all icons), so pages can use `<el-button>`, `<el-table>`, etc. without imports.
7. **iconfont** custom icons: loaded from `@/static/fonts/iconfont.css` in `App.vue`.

### 弹窗与选择器统一章程（底部弹窗统一治理 P0.6 起草 → P4.1 完整版）

**选择器/弹窗选型矩阵（新增交互一律按此选型，禁止引入新实现）**：

| 交互 | 唯一实现 | 说明 |
|---|---|---|
| 时间/日期 | `wd-datetime-picker`（`type="datetime"` 到分钟或 `date`） | 原生 `<picker>` 已全仓清零，禁止回退 |
| 短枚举（角色/状态/筛选等） | `wd-picker`（显式 `:z-index="3000"`） | columns 用 `{value, label}` 或 string[]，v-model 保持"值语义" |
| 长列表资源选择 | `PickerSheet.vue`（single 点选即关 / multiple toggle+max+N/M 完成条 / 本地搜索胶囊） | 禁止复制内联弹层 |
| 业务特殊弹层（服务端搜索+分页+保存中态） | 内联实现 + 登记例外（如 TabManager 管理弹窗） | 套 PickerSheet 会 API 胖化，勿强改 |
| 操作菜单 | 原生 `uni.showActionSheet` | 禁止居中卡片冒充菜单 |

**z-index 章程（四档）**：

| 档 | 值 | 归属 | 铁律 |
|:---:|:---:|------|------|
| 居中 Dialog | `1000` | `ModalDialog.vue` | 不变 |
| 页面级底部 Sheet | `2000` | 共享 Sheet、TargetSelector 弹层 | 自研底部弹层统一此档 |
| wd 弹层 | `3000`（显式传入） | 所有 wd-picker / wd-datetime-picker 等 | **禁止依赖库默认 z-index（wd-popup=10、datetime-picker=15）**；若 3000 仍受父级 stacking context 限制（如 ModalDialog 内嵌场景）→ 追加 `root-portal` 属性兜底 |
| 全屏 | `9999` | AvatarPreview 等 | 不变 |

**wot 主题变量映射表**（首版仅 1 个 token，勿一次性扩；确需新映射时在此登记并说明理由）：

| wot 变量 | 值 | 来源/说明 |
|---|---|---|
| `--wot-color-theme` | `#0F766E` | 定义于 `src/common/uni.scss` `:root`（P0.1）；全库主色 → 品牌青绿；组件确认按钮/选中高亮默认跟随 |

- wot 组件样式为内嵌 scoped + CSS 变量 fallback，与 `--home-*` 同机制生效（改 `--wot-*` 时勿动 `--home-*`）。
- `loading-color` 等 prop 默认色（`#4D80F0`）不随主题变量，如需品牌色在使用处显式传 prop，勿扩映射表。
- 新增 wot 弹窗组件时**必须**显式传 `:z-index="3000"`，并保持与既有页面级 sheet（2000）/Dialog（1000）的层级关系。
- **共享底部选择面板**统一用 `src/components/common/PickerSheet.vue`（single 点选即关 / multiple toggle+max+N/M 完成条 / 本地搜索胶囊 / 0.3s 滑入滑出 / z-index 2000），禁止再复制内联弹层实现。
- **源文件纪律（弹窗治理 P1.3 事故固化）**：`src/` 下源码文件（.vue/.ts/.scss）一律用编辑工具增删改，**禁止用 PowerShell `Get-Content/Set-Content` 等重写文件**（曾致 UTF-8 编码不可逆破坏）。
