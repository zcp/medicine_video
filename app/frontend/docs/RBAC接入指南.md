# RBAC 接入指南

## 角色体系

共 4 种角色，等级从低到高：

| 角色 | 枚举值 | 等级 | 说明 |
|------|--------|------|------|
| 普通用户 | `UserRole.REGULAR` | 0 | 默认注册用户 |
| 房管 | `UserRole.MODERATOR` | 1 | 直播间管理员 |
| 管理员 | `UserRole.ADMIN` | 2 | 平台管理员 |
| 超级管理员 | `UserRole.SUPERADMIN` | 3 | 最高权限 |

等级比较规则：`hasMinRole(当前角色, 要求角色)` — 当前角色等级 >= 要求等级即通过。

---

## 一、给新页面加权限

**场景**：新建了一个管理页面 `/pages/app/admin/departments`，只想让 ADMIN 及以上访问。

**步骤：**

1. 打开 `src/config/permission.config.ts`
2. 在 `PAGE_PERMISSIONS` 中添加一行：

```typescript
export const PAGE_PERMISSIONS: Record<string, UserRole[]> = {
  // ... 已有配置
  '/pages/app/admin/departments': [UserRole.ADMIN, UserRole.SUPERADMIN],
};
```

3. 完成。路由拦截器会自动生效：
   - 未登录 → 跳转登录页
   - 已登录但角色不足 → toast "权限不足" + 跳首页
   - 已登录且角色满足 → 正常进入页面

**注意**：未在 `PAGE_PERMISSIONS` 中配置的页面视为**公开页面**，所有已登录用户均可访问。公开页面不需要任何配置。

---

## 二、给页面按钮加权限（v-permission 指令）

**场景**：页面上有一个"删除专家"按钮，只想让 ADMIN 及以上看到。

```html
<button v-permission="UserRole.ADMIN">删除专家</button>
```

效果：
- 当前用户角色 >= ADMIN → 正常显示
- 当前用户角色 < ADMIN（或无角色）→ `display: none` 隐藏
- 开发模式下（`import.meta.env.DEV`）控制台会输出 warn 提示

**注意**：
- `v-permission` 只检查 `mounted` 时的角色状态，不动态监听登录态变化（登录/登出通常伴随页面跳转）
- 指令接受 `UserRole` 枚举值作为参数，不接收数组。需要多角色时传入最低要求角色（因为等级比较是 >=）

---

## 三、脚本中做权限判断

### 判断角色

```typescript
import { hasRole } from '@/utils/auth';
import { UserRole } from '@/types/enums';

// 是否是管理员及以上
if (hasRole(UserRole.ADMIN)) { ... }

// 是否是超级管理员
if (hasRole(UserRole.SUPERADMIN)) { ... }

// 是否同时满足多个角色（满足任一即可）
if (hasRole(UserRole.ADMIN, UserRole.SUPERADMIN)) { ... }
```

### 判断页面访问权限

```typescript
import { canAccessPage } from '@/utils/auth';

if (canAccessPage('/pages/app/admin/departments')) {
  // 当前用户可以访问该页面
}
```

### 判断操作权限

```typescript
import { canPerformAction } from '@/utils/auth';

if (canPerformAction('manage-expert')) {
  // 当前用户可以执行专家管理操作
}
```

操作标识定义在 `ACTION_PERMISSIONS` 中（`src/config/permission.config.ts`）。

### Auth Store 直接判断（模板中用）

```html
<template>
  <!-- 直接用 store 的 getter -->
  <view v-if="authStore.isAdmin">管理员可见内容</view>
  <view v-if="authStore.isSuperAdmin">超管可见内容</view>
</template>

<script setup lang="ts">
const authStore = useAuthStore();
</script>
```

可用的 getter：
| getter | 返回值 | 说明 |
|--------|--------|------|
| `authStore.isAuthenticated` | `boolean` | 是否已登录 |
| `authStore.userRole` | `string \| null` | 当前角色值（如 `'ADMIN'`） |
| `authStore.isAdmin` | `boolean` | 是否为 ADMIN 或 SUPERADMIN |
| `authStore.isSuperAdmin` | `boolean` | 是否为 SUPERADMIN |

---

## 四、路由守卫行为

路由守卫仅在 **App 和微信小程序** 端生效，H5 端不安装。

| 用户状态 | 目标页面 | 行为 |
|---------|---------|------|
| 未登录 | 公开页面 | 放行 |
| 未登录 | 受保护页面 | 保存回跳路径 → 跳转登录页 |
| 未登录 + switchTab | 受保护页面 | 保存回跳路径 → navigateTo 侧路跳登录页 → switchTab 跳首页 |
| 已登录 | 公开页面 | 放行 |
| 已登录，角色不足 | 受保护页面 | toast "权限不足" → 跳首页 |
| 已登录，角色满足 | 受保护页面 | 放行 |

守卫逻辑位于 `src/utils/routeGuard.ts`，在 `App.vue` 的 `onLaunch` 中通过 `setupRouteGuards()` 安装。

---

## 五、App 端与 H5 端的差异

| 能力 | App 端 | H5 端 |
|------|--------|-------|
| 路由拦截（addInterceptor） | ✅ 4 个拦截器全部安装 | ❌ 不安装（AdminLayout 自行管理导航） |
| v-permission 指令 | ✅ 可用 | ✅ 也可用（无副作用） |
| hasRole / canAccessPage / canPerformAction | ✅ 可用 | ✅ 可用 |
| Auth Store getter（isAdmin / isSuperAdmin） | ✅ 可用 | ✅ 可用 |

H5 端的 AdminLayout 目前没有做角色校验。后续如需为 H5 端添加角色控制，需要在 vue-router 的 `beforeEach` 中自行实现。

---

## 六、完整示例：新建一个管理员页面

以新建"轮播图管理"页面为例：

### 步骤 1：新建页面文件

`src/pages/app/admin/featured/index.vue`（使用 uni-app 原生组件，不用 Element Plus）

### 步骤 2：在 pages.json 中注册

```json
{
  "path": "pages/app/admin/featured/index",
  "style": {
    "navigationBarTitleText": "轮播图管理"
  }
}
```

### 步骤 3：配置页面权限

在 `src/config/permission.config.ts` 的 `PAGE_PERMISSIONS` 中：

```typescript
'/pages/app/admin/featured': [UserRole.ADMIN, UserRole.SUPERADMIN],
```

### 步骤 4：在某个位置添加入口

在"我的"页面管理面板 section 中或 CustomTabBar 中加入跳转链接。

### 步骤 5：使用 API

直接调用 `src/api/featured.ts` 中已有的 `createFeaturedContent` / `updateFeaturedContent` / `deleteFeaturedContent`。

---

## 七、权限配置总览

| 配置文件 | 路径 | 作用 |
|---------|------|------|
| 角色定义 | `src/types/enums.ts` | `UserRole` 枚举 |
| 权限映射 | `src/config/permission.config.ts` | `PAGE_PERMISSIONS` + `ACTION_PERMISSIONS` + 角色等级 |
| 权限工具 | `src/utils/auth.ts` | `hasRole()` / `canAccessPage()` / `canPerformAction()` |
| 路由守卫 | `src/utils/routeGuard.ts` | 4 个 `addInterceptor` |
| 权限指令 | `src/directives/permission.ts` | `v-permission` |

### 添加新操作权限的流程

1. 在 `ACTION_PERMISSIONS` 中新增一个操作标识：

```typescript
'my-new-action': [UserRole.ADMIN, UserRole.SUPERADMIN],
```

2. 在代码中使用：

```typescript
if (canPerformAction('my-new-action')) { ... }
```

---

## 八、常见问题

**Q: v-permission 指令为什么接受的是 UserRole 不是数组？**
A: 因为角色等级是 >= 比较，传入 ADMIN 就意味着 SUPERADMIN 也可见。不需要传递数组。

**Q: 为什么 H5 端没有路由守卫？**
A: H5 端的 AdminLayout 使用 Element Plus 的 el-menu 管理导航，与 uni-app 的页面栈不同。后续如需加 H5 端的角色控制，应在 AdminLayout.vue 的 vue-router beforeEach 中实现。

**Q: canAccessPage 返回 true 但用户实际上无法访问？**
A: 确认该页面路径是否在 `PAGE_PERMISSIONS` 中配置。未配置的页面默认返回 true（公开页面）。

**Q: 如何临时禁用某个页面的权限控制？**
A: 从 `PAGE_PERMISSIONS` 中移除该条目即可，未配置的页面自动变为公开。
