# "我的"页面代码生成提示词 (uni-app移动端版 V1.0)

---

## ⚠️ 增量开发特别声明

**本任务是在现有可运行的uni-app移动端项目基础上进行增量开发！**

- ✅ **已有基础设施**：`src/store/auth.ts`（认证状态管理）、`src/api/favorite.ts`、`src/api/subscription.ts`、`src/api/watchHistory.ts`
- ✅ **已有直播管理页面**：`src/pages/app/live-manage/list.vue`、`src/pages/app/live-manage/detail.vue`
- ⚠️ **关键原则**：不覆盖现有代码、不破坏现有功能、增量补充缺失部分

**在生成任何代码之前，你必须先执行第0章的强制性前置检查！**

---

## 🏗️ 架构基础（必读）

**在开始开发前，你必须先阅读以下文档：**

📖 **设计文档**：
- `docs/直播saas平台网站前端效果设计---移动端版(v1.3）.md`（第9.0章节 - 我的页面与昼夜模式设置）
- `docs/直播SaaS平台移动端前端设计文档.md`（第6章 - 核心数据模型、第8章 - API接口映射）
- `docs/后端新增api接口和模块设计文档-v2.md`（Section 4.8-4.12 用户相关API）

### 📋 可用图标速查表

以下图标已在 `src/static/fonts/iconfont.css` 中定义，可直接使用：

| 图标类名 | 用途 | 图标类名 | 用途 |
|---------|------|---------|------|
| `icon-star` | 收藏 | `icon-star-filled` | 已收藏 |
| `icon-heart` | 订阅/喜欢 | `icon-heart-filled` | 已订阅 |
| `icon-history` | 历史记录 | `icon-message` | 消息/通知 |
| `icon-setting` | 设置 | `icon-more` | 更多/关于 |
| `icon-user` | 用户/隐私 | `icon-edit` | 编辑 |
| `icon-video` | 视频/直播 | `icon-add` | 添加/创建 |
| `icon-arrow-right` | 右箭头 | `icon-eye` | 查看/流量 |
| `icon-search` | 搜索 | `icon-close` | 关闭 |
| `icon-delete` | 删除 | `icon-share` | 分享 |

---

## 第0章：强制性前置检查与冲突检测 ⚡（必须先执行）

### 0.1 检查目的

在生成任何代码之前，必须全面了解项目现状，避免：
- ❌ 覆盖已有的完善代码
- ❌ 与现有类型定义冲突
- ❌ 创建重复的工具函数
- ❌ 破坏现有的导入依赖关系

### 0.2 必须执行的检查步骤

#### 步骤1：读取现有核心文件（强制）

你必须先读取以下文件，了解现有实现：

```bash
必须读取的文件清单：
✅ src/store/auth.ts - 认证状态管理（User接口、logout方法）
✅ src/api/favorite.ts - 收藏API
✅ src/api/subscription.ts - 订阅API
✅ src/api/watchHistory.ts - 观看历史API
✅ src/config/env.ts - 环境配置（VITE_USE_MOCK开关）
✅ src/pages/app/live-manage/list.vue - 直播管理列表（已实现）
✅ src/pages/app/tabbar/my/index.vue - 当前我的页面（占位页）
✅ src/pages/app/tabbar/home/index.vue - 首页（参考Mock/API切换模式）
✅ src/pages/app/tabbar/home/mock-data.ts - 首页Mock数据（参考格式）
✅ src/static/fonts/iconfont.css - 可用图标列表
✅ src/pages.json - 路由配置
```

**执行命令**：使用 `read_file` 工具逐个读取以上文件。

#### 步骤2：扫描目录结构（强制）

```bash
必须扫描的目录：
✅ src/pages/app/tabbar/my/（确认子目录结构）
✅ src/api/（列出所有.ts文件）
✅ src/store/（列出所有.ts文件）
✅ src/components/（列出可复用组件）
```

**执行命令**：使用 `find_by_name` 或 `list_dir` 工具扫描目录。

#### 步骤3：在聊天窗口输出项目现状分析（强制）

**重要**：❗ 不要生成单独的分析报告文件，直接在聊天窗口中展示分析结果！

基于步骤1和步骤2的检查结果，在聊天窗口中输出以下结构化分析：

---

**📊 "我的"页面开发现状分析**

**一、已存在且可直接复用的文件（✅ 直接使用）**
- 列出所有可复用的API、Store、组件
- 注明文件路径、核心功能
- 给出"直接导入使用"的结论

**二、已存在但需要扩展的文件（🔧 需要补充）**
- 列出需要补充的文件（如auth.ts的User接口）
- 明确列出现有字段清单
- 明确列出缺失字段（如认证徽章、头像等）
- 说明操作方式（multi_edit，保留现有字段）

**三、需要新建的文件（➕ 需新建）**
- 列出所有需要新建的页面文件
- 列出需要新建的组件文件
- 列出需要新建的类型定义文件

**四、路由配置检查（📍 pages.json）**
- 检查现有路由配置
- 列出需要新增的路由

**五、安全性分析**
- ⚠️ 列出潜在风险点
- ✅ 给出安全操作策略

---

#### 步骤4：等待用户确认（强制）

在聊天窗口输出分析结果后，**必须等待用户确认**才能继续生成代码。

向用户提问：
```
📋 以上是"我的"页面开发现状分析结果。

请确认：
1. 分析结果是否准确？
2. 是否有遗漏或需要调整的地方？
3. 如果确认无误，请输入"确认继续"开始代码生成。
```

**禁止**在用户确认前开始生成任何代码！

---

## 第1章：角色定义（Role Definition）

你是一名**资深移动端前端工程师**，具备以下专业技能：

- **精通技术栈**：uni-app、Vue 3 Composition API、TypeScript、Pinia状态管理
- **跨端开发经验**：H5、Android、iOS、微信小程序等多端适配
- **UI组件库**：uni-app原生组件 + iconfont图标
- **增量开发能力**：能够在现有项目基础上进行安全的增量开发，不破坏现有功能

**你的任务是根据详细设计文档和现有代码基础，编写高质量、功能完整、可直接运行的增量代码。**

---

## 第2章：任务目标（Task Objective）

### 2.1 核心目标

开发"我的"页面（`src/pages/app/tabbar/my/index.vue`），实现以下功能模块：

1. **用户信息卡片**：头像、昵称、认证徽章、编辑入口
2. **快捷功能区**：收藏、历史、订阅、通知（4个图标入口）
3. **直播管理区**：我的直播、创建直播
4. **设置菜单区**：外观设置、流量提醒、关于我们、隐私政策
5. **底部操作区**：退出登录、版本号

### 2.2 页面布局设计

```
┌─────────────────────────────────────────┐
│            状态栏 (系统)                  │
├─────────────────────────────────────────┤
│  ┌─────┐                                │
│  │头像 │  用户昵称              [编辑]   │
│  │80px │  🎙️主播认证  👨‍⚕️专家认证         │
│  └─────┘                                │
│         ← 用户信息卡片 (背景渐变) →       │
├─────────────────────────────────────────┤
│                                         │
│  ┌────┐  ┌────┐  ┌────┐  ┌────┐        │
│  │收藏│  │历史│  │订阅│  │通知│         │
│  └────┘  └────┘  └────┘  └────┘        │
│         ← 快捷功能区 (4个图标) →         │
├─────────────────────────────────────────┤
│                                         │
│  我的直播                          >    │
│  ─────────────────────────────────      │
│  创建直播                          >    │
│         ← 直播管理区 →                   │
├─────────────────────────────────────────┤
│                                         │
│  外观设置                          >    │
│  ─────────────────────────────────      │
│  流量提醒                    [开关]     │
│  ─────────────────────────────────      │
│  关于我们                          >    │
│  ─────────────────────────────────      │
│  隐私政策                          >    │
│         ← 设置菜单区 →                   │
├─────────────────────────────────────────┤
│                                         │
│            [ 退出登录 ]                  │
│         ← 底部操作区 →                   │
│                                         │
│          版本号 v1.0.0                   │
└─────────────────────────────────────────┘
```

### 2.3 未登录状态设计

```
┌─────────────────────────────────────────┐
│  ┌─────┐                                │
│  │默认 │  点击登录                       │
│  │头像 │  登录后享受更多功能              │
│  └─────┘                                │
└─────────────────────────────────────────┘
```

---

## 第3章：功能模块详解（Feature Specifications）

### 3.1 用户信息卡片

| 元素 | 说明 | 交互 |
|------|------|------|
| **头像** | 160rpx 圆形，默认占位图 | 点击可查看大图（后续） |
| **昵称** | 最多显示10字，超出省略 | - |
| **编辑图标** | iconfont `icon-edit` | 点击跳转个人资料编辑页（占位） |
| **认证徽章** | 主播🎙️ / 专家👨‍⚕️ | 根据用户角色显示 |

**数据来源**：`useAuthStore().user`

### 3.2 快捷功能区（4个图标）

| 图标 | 名称 | 跳转路径 | 需登录 | 说明 |
|------|------|----------|--------|------|
| `icon-star` | 我的收藏 | `/pages/app/tabbar/my/favorites/index` | ✅ | 待创建占位页 |
| `icon-history` | 观看历史 | `/pages/app/tabbar/my/watch-history/index` | ✅ | 待创建占位页 |
| `icon-heart` | 我的订阅 | `/pages/app/tabbar/my/subscriptions/index` | ✅ | 待创建占位页 |
| `icon-message` | 消息通知 | `/pages/app/message/index` | ✅ | 已有占位页 |

**⚠️ 图标可用性说明**：以上图标均已在 `src/static/fonts/iconfont.css` 中定义，可直接使用。

**技术要点**：
- 点击前检查 `isAuthenticated`，未登录则跳转登录页
- 使用 `uni.navigateTo` 进行页面跳转

### 3.3 直播管理区

| 菜单项 | 跳转路径 | 需登录 | 说明 |
|--------|----------|--------|------|
| 我的直播 | `/pages/app/live-manage/list` | ✅ | 已有页面 |
| 创建直播 | `/pages/app/live-manage/list?action=create` | ✅ | 复用现有页面，传参打开创建弹窗 |

### 3.4 设置菜单区

| 菜单项 | 图标 | 类型 | 交互 | 需登录 |
|--------|------|------|------|--------|
| 外观设置 | `icon-setting` | 跳转 | 跳转到外观设置页（待创建占位页） | ❌ |
| 流量提醒 | `icon-eye` | 开关 | 本地存储切换状态 `uni.setStorageSync` | ❌ |
| 关于我们 | `icon-more` | 跳转 | 跳转到关于页面（待创建占位页） | ❌ |
| 隐私政策 | `icon-user` | 跳转 | 打开 WebView 或外链 | ❌ |

**⚠️ 图标可用性说明**：以上图标均已在 `src/static/fonts/iconfont.css` 中定义。

### 3.5 底部操作区

| 元素 | 说明 |
|------|------|
| **退出登录** | 红色文字，居中，点击弹出确认框，调用 `authStore.logout()` |
| **版本号** | 灰色小字，显示当前版本 `v1.0.0` |

---

## 第4章：API依赖与数据流（API & Data Flow）

### 4.1 已有API（可直接使用）

| API 文件 | 函数 | 用途 |
|----------|------|------|
| `@/api/favorite.ts` | `getFavorites()` | 获取收藏列表（用于显示数量） |
| `@/api/subscription.ts` | `getSubscriptions()` | 获取订阅列表（用于显示数量） |
| `@/api/watchHistory.ts` | `getWatchHistory()` | 获取观看历史（用于显示数量） |
| `@/store/auth.ts` | `useAuthStore()` | 用户信息、登出 |
| `@/config/env.ts` | `ENV_CONFIG` | 环境配置（含Mock开关） |

### 4.2 Mock/API切换机制 ⚠️ 重要

**必须与首页保持一致的Mock/API切换模式！**

参考 `src/pages/app/tabbar/home/index.vue` 的实现模式。

### 4.3 需要创建的Mock数据文件

**📁 文件：`src/pages/app/tabbar/my/mock-data.ts`**

```typescript
/**
 * "我的"页面Mock数据
 * 用于开发阶段，当 ENV_CONFIG.VITE_USE_MOCK = true 时使用
 */

// 用户统计数据
export const mockUserStats = {
  favorites_count: 12,
  history_count: 45,
  subscriptions_count: 8,
  notifications_count: 3,
};

// 用户扩展信息（认证徽章等）
export const mockUserProfile = {
  is_broadcaster: true,
  is_expert: false,
};
```

### 4.4 数据获取函数模板

```typescript
import { ENV_CONFIG } from '@/config/env';
import { getFavorites } from '@/api/favorite';
import { getSubscriptions } from '@/api/subscription';
import { getWatchHistory } from '@/api/watchHistory';
import { mockUserStats, mockUserProfile } from './mock-data';

/**
 * 获取用户统计数据（收藏/历史/订阅/通知数量）
 */
async function fetchUserStats() {
  // Mock模式：使用本地数据
  if (ENV_CONFIG.VITE_USE_MOCK) {
    return mockUserStats;
  }
  // 真实API模式：调用后端接口
  try {
    const [favRes, subRes, histRes] = await Promise.all([
      getFavorites({ page: 1, size: 1 }),
      getSubscriptions({ page: 1, size: 1 }),
      getWatchHistory({ page: 1, size: 1 }),
    ]);
    return {
      favorites_count: favRes.data?.total || 0,
      subscriptions_count: subRes.data?.total || 0,
      history_count: histRes.data?.total || 0,
      notifications_count: 0, // 待后端实现
    };
  } catch (error) {
    console.error('获取用户统计数据失败:', error);
    return mockUserStats; // 失败时降级到Mock数据
  }
}

/**
 * 获取用户扩展信息（认证徽章等）
 */
function getUserProfile() {
  // Mock模式或API未实现时使用Mock数据
  if (ENV_CONFIG.VITE_USE_MOCK) {
    return mockUserProfile;
  }
  // TODO: 待后端实现 GET /api/v1/users/me 后替换
  return mockUserProfile;
}
```

### 4.5 数据流向

```
页面加载 (onMounted / onShow)
  ↓
检查登录状态 (authStore.isAuthenticated)
  ├─ 已登录 → 调用 fetchUserStats() 获取统计数据
  │           ├─ VITE_USE_MOCK=true → 返回 mockUserStats
  │           └─ VITE_USE_MOCK=false → 调用真实API
  │           ↓
  │           更新 quickActions 的 badge 数量
  └─ 未登录 → 显示"点击登录"卡片
  ↓
用户点击菜单项
  ├─ 需登录功能 → 检查isAuthenticated → 未登录调用forceReauth()
  └─ 无需登录功能 → 直接执行操作
```

---

## 第5章：核心原则（Core Principles）

### 5.0 安全规范（Security Standards）⚠️ 强制遵循

本页面开发必须遵循以下安全原则：

#### 5.0.1 XSS防护
```typescript
// ❌ 禁止：使用v-html渲染用户输入
<view v-html="userInput"></view>

// ✅ 正确：直接使用文本插值（Vue自动转义）
<text>{{ userInput }}</text>

// ✅ 或使用内联转义函数（如果需要手动处理）
const escapeHtml = (str: string) => {
  return str.replace(/[&<>"']/g, (m) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[m] || m));
};
```

#### 5.0.2 本地缓存安全
```typescript
// ⚠️ Token存储已由 auth.ts 统一管理，禁止直接操作
// ❌ 禁止：直接存储token
uni.setStorageSync('jwt_token', accessToken);

// ✅ 正确：通过authStore管理token
import { useAuthStore } from '@/store/auth';
const authStore = useAuthStore();
authStore.setToken(token);  // 统一管理

// ✅ 非敏感设置项可直接存储
uni.setStorageSync('settings_traffic_reminder', true);
```

#### 5.0.3 请求安全
- 所有API请求必须通过 `@/utils/request.ts` 发起（已集成签名和CSRF防护）
- 需认证的接口必须传递 `{ auth: true }` 选项
- 禁止在URL中拼接敏感参数

#### 5.0.4 URL参数校验
```typescript
// 对redirect等跳转参数进行合法性校验
const validateRedirectUrl = (url: string): boolean => {
  // 只允许站内跳转
  return url.startsWith('/') && !url.startsWith('//');
};
```

#### 5.0.5 平台差异化安全处理
```typescript
// #ifdef H5
// H5环境：CSRF Token 由 request.ts 自动处理
// Clickjacking防护：需后端配置 X-Frame-Options 响应头
// #endif

// #ifdef APP-PLUS
// App环境：使用原生安全存储
// #endif

// #ifdef MP-WEIXIN
// 小程序环境：遵循微信安全规范
// #endif
```

---

### 5.1 UI组件库规范

**所有UI元素必须使用uni-app原生组件 + iconfont图标**

```vue
<!-- ✅ 正确：使用uni-app原生组件 -->
<view class="menu-item">
  <text class="iconfont icon-star"></text>
  <text>我的收藏</text>
</view>

<!-- ❌ 错误：使用Element Plus组件 -->
<el-button>我的收藏</el-button>
```

### 5.2 样式规范

- **单位**：统一使用 `rpx`（响应式像素）
- **最小可点击区域**：44x44px（88rpx）
- **颜色变量**：使用CSS变量支持主题切换

```scss
/* 浅色模式 */
:root {
  --bg-page: #F5F5F5;
  --bg-content: #FFFFFF;
  --text-primary: #333333;
  --text-secondary: #666666;
  --text-tertiary: #999999;
  --border-color: #E5E5E5;
  --color-primary: #509CEC;
  --color-danger: #FF4D4F;
}
```

### 5.3 登录拦截规范

```typescript
// 需要登录的操作统一使用此函数
const requireAuth = (callback: () => void) => {
  if (!authStore.isAuthenticated) {
    uni.showToast({
      title: '请先登录',
      icon: 'none'
    });
    // ⚠️ 使用authStore.forceReauth()，内部已处理多平台登录跳转
    // H5: 跳转到外部登录服务 LOGIN_URL
    // App/小程序: 使用内部登录流程
    authStore.forceReauth('/pages/app/tabbar/my/index');
    return;
  }
  callback();
};

// 使用示例
const handleFavorites = () => {
  requireAuth(() => {
    uni.navigateTo({ url: '/pages/app/tabbar/my/favorites/index' });
  });
};
```

### 5.4 本地存储规范

```typescript
// 流量提醒开关（非敏感信息，可直接存储）
const STORAGE_KEY_TRAFFIC_REMINDER = 'settings_traffic_reminder';

// 读取
const trafficReminder = uni.getStorageSync(STORAGE_KEY_TRAFFIC_REMINDER) ?? true;

// 保存
uni.setStorageSync(STORAGE_KEY_TRAFFIC_REMINDER, value);

// ⚠️ Token等敏感信息由 auth.ts 统一管理，禁止直接操作
```

### 5.5 响应式与多端适配规范

#### 5.5.1 布局单位规范
```scss
// ✅ 优先使用 rpx（响应式像素）
.container {
  width: 750rpx;        // 满宽
  padding: 32rpx;       // 间距
  font-size: 28rpx;     // 字体
}

// ✅ 百分比用于弹性布局
.flex-item {
  width: 50%;
  flex: 1;
}

// ✅ vw/vh 用于视口相关尺寸
.full-screen {
  width: 100vw;
  height: 100vh;
}
```

#### 5.5.2 Flex布局优先
```scss
// ✅ 全局使用 flex 布局，支持横竖屏切换
.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}
```

#### 5.5.3 媒体查询断点（平板/PC适配）
```scss
// 移动端默认样式
.menu-item {
  padding: 32rpx;
}

// 平板适配 (≥768px)
@media screen and (min-width: 768px) {
  .menu-item {
    padding: 24rpx 48rpx;
  }
  
  .quick-actions {
    max-width: 600px;
    margin: 0 auto;
  }
}

// PC适配 (≥1024px)
@media screen and (min-width: 1024px) {
  .my-page {
    max-width: 800px;
    margin: 0 auto;
  }
}
```

#### 5.5.4 平台条件编译
```typescript
// #ifdef H5
// H5特有逻辑（如：浏览器API）
// #endif

// #ifdef APP-PLUS
// App特有逻辑（如：原生插件调用）
// #endif

// #ifdef MP-WEIXIN
// 微信小程序特有逻辑（如：wx API）
// #endif
```

#### 5.5.5 图片自适应
```vue
<!-- ✅ 使用 mode 属性控制图片适配 -->
<image 
  :src="avatarUrl" 
  mode="aspectFill"
  class="avatar"
/>

<style lang="scss">
.avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
}

// 大屏适配
@media screen and (min-width: 768px) {
  .avatar {
    width: 120px;
    height: 120px;
  }
}
</style>
```

---

## 第6章：文件清单与生成指令（File List & Generation Instructions）

### 6.1 需要生成的文件

#### **P0级任务（必须完成）** ⚠️

| 序号 | 文件路径 | 操作类型 | 说明 |
|-----|---------|---------|------|
| 1 | `src/pages/app/tabbar/my/mock-data.ts` | ✨ **新建** | Mock数据文件（参考4.3节） |
| 2 | `src/pages/app/tabbar/my/index.vue` | 🔧 **重写** | 我的页面主入口 |
| 3 | `src/pages/app/tabbar/my/favorites/index.vue` | ✨ **新建** | 收藏列表占位页 |
| 4 | `src/pages/app/tabbar/my/watch-history/index.vue` | ✨ **新建** | 观看历史占位页 |
| 5 | `src/pages/app/tabbar/my/subscriptions/index.vue` | ✨ **新建** | 订阅列表占位页 |
| 6 | `src/pages/app/tabbar/my/settings/appearance.vue` | ✨ **新建** | 外观设置占位页 |
| 7 | `src/pages/app/tabbar/my/about/index.vue` | ✨ **新建** | 关于我们占位页 |

#### **P1级任务（路由配置）** 📋

| 序号 | 文件路径 | 操作类型 | 说明 |
|-----|---------|---------|------|
| 8 | `src/pages.json` | 🔧 **补充** | 添加新页面路由 |

---

## 第7章：分步生成与验证流程（Step-by-Step Generation）

### 步骤1：生成"我的"页面主入口

**📁 文件：`src/pages/app/tabbar/my/index.vue`**

**目标**：完整实现"我的"页面所有功能模块

#### 7.1.1 模板结构 (`<template>`)

```vue
<template>
  <view class="my-page">
    <!-- 用户信息卡片 -->
    <view class="user-card" :class="{ 'not-logged-in': !isAuthenticated }">
      <!-- 已登录状态 -->
      <view v-if="isAuthenticated" class="user-info">
        <image class="avatar" :src="userAvatar" mode="aspectFill" />
        <view class="user-details">
          <view class="nickname-row">
            <text class="nickname">{{ userNickname }}</text>
            <view class="edit-btn" @click="handleEditProfile">
              <text class="iconfont icon-edit"></text>
            </view>
          </view>
          <view class="badges">
            <view v-if="isBroadcaster" class="badge broadcaster">
              <text>🎙️ 主播</text>
            </view>
            <view v-if="isExpert" class="badge expert">
              <text>👨‍⚕️ 专家</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 未登录状态 -->
      <view v-else class="login-prompt" @click="handleLogin">
        <image class="avatar default" src="/static/tabbar/my.png" mode="aspectFill" />
        <view class="login-text">
          <text class="title">点击登录</text>
          <text class="subtitle">登录后享受更多功能</text>
        </view>
      </view>
    </view>

    <!-- 快捷功能区 -->
    <view class="quick-actions">
      <view 
        v-for="action in quickActions" 
        :key="action.key"
        class="action-item"
        @click="handleQuickAction(action)"
      >
        <view class="icon-wrapper">
          <text class="iconfont" :class="action.icon"></text>
          <view v-if="action.badge > 0" class="badge-count">{{ action.badge }}</view>
        </view>
        <text class="action-label">{{ action.label }}</text>
      </view>
    </view>

    <!-- 直播管理区 -->
    <view class="menu-section">
      <view class="section-title">直播管理</view>
      <view class="menu-list">
        <view class="menu-item" @click="handleMyLive">
          <text class="iconfont icon-video"></text>
          <text class="menu-label">我的直播</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item" @click="handleCreateLive">
          <text class="iconfont icon-add"></text>
          <text class="menu-label">创建直播</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
      </view>
    </view>

    <!-- 设置菜单区 -->
    <view class="menu-section">
      <view class="section-title">设置</view>
      <view class="menu-list">
        <view class="menu-item" @click="handleAppearance">
          <text class="iconfont icon-setting"></text>
          <text class="menu-label">外观设置</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item">
          <text class="iconfont icon-eye"></text>
          <text class="menu-label">流量提醒</text>
          <switch 
            :checked="trafficReminder" 
            @change="handleTrafficReminderChange"
            color="#509CEC"
          />
        </view>
        <view class="menu-item" @click="handleAbout">
          <text class="iconfont icon-more"></text>
          <text class="menu-label">关于我们</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
        <view class="menu-item" @click="handlePrivacy">
          <text class="iconfont icon-user"></text>
          <text class="menu-label">隐私政策</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
      </view>
    </view>

    <!-- 底部操作区 -->
    <view v-if="isAuthenticated" class="logout-section">
      <view class="logout-btn" @click="handleLogout">
        <text>退出登录</text>
      </view>
    </view>

    <!-- 版本号 -->
    <view class="version-info">
      <text>版本号 v1.0.0</text>
    </view>
  </view>
</template>
```

#### 7.1.2 逻辑实现 (`<script setup>`)

```typescript
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { ENV_CONFIG } from '@/config/env';
import { getFavorites } from '@/api/favorite';
import { getSubscriptions } from '@/api/subscription';
import { getWatchHistory } from '@/api/watchHistory';
import { mockUserStats, mockUserProfile } from './mock-data';

// Store
const authStore = useAuthStore();

// 响应式数据
const trafficReminder = ref(true);
const userStats = ref({
  favorites_count: 0,
  history_count: 0,
  subscriptions_count: 0,
  notifications_count: 0,
});
const userProfile = ref({
  is_broadcaster: false,
  is_expert: false,
});

// 计算属性
const isAuthenticated = computed(() => authStore.isAuthenticated);
const userAvatar = computed(() => authStore.user?.avatar || '/static/tabbar/my.png');
const userNickname = computed(() => {
  const name = authStore.user?.username || '用户';
  return name.length > 10 ? name.slice(0, 10) + '...' : name;
});
const isBroadcaster = computed(() => userProfile.value.is_broadcaster);
const isExpert = computed(() => userProfile.value.is_expert);

// 快捷功能配置 - 使用动态badge数据
const quickActions = computed(() => [
  { key: 'favorites', icon: 'icon-star', label: '收藏', badge: userStats.value.favorites_count, path: '/pages/app/tabbar/my/favorites/index', requireAuth: true },
  { key: 'history', icon: 'icon-history', label: '历史', badge: userStats.value.history_count, path: '/pages/app/tabbar/my/watch-history/index', requireAuth: true },
  { key: 'subscriptions', icon: 'icon-heart', label: '订阅', badge: userStats.value.subscriptions_count, path: '/pages/app/tabbar/my/subscriptions/index', requireAuth: true },
  { key: 'notifications', icon: 'icon-message', label: '通知', badge: userStats.value.notifications_count, path: '/pages/app/message/index', requireAuth: true },
]);

// ========== 数据获取函数（Mock/API切换） ==========

/**
 * 获取用户统计数据
 * 与首页保持一致的Mock/API切换模式
 */
async function fetchUserStats() {
  // Mock模式：使用本地数据
  if (ENV_CONFIG.VITE_USE_MOCK) {
    return mockUserStats;
  }
  // 真实API模式：调用后端接口
  try {
    const [favRes, subRes, histRes] = await Promise.all([
      getFavorites({ page: 1, size: 1 }),
      getSubscriptions({ page: 1, size: 1 }),
      getWatchHistory({ page: 1, size: 1 }),
    ]);
    return {
      favorites_count: favRes.data?.total || 0,
      subscriptions_count: subRes.data?.total || 0,
      history_count: histRes.data?.total || 0,
      notifications_count: 0, // 待后端实现
    };
  } catch (error) {
    console.error('获取用户统计数据失败:', error);
    return mockUserStats; // 失败时降级到Mock数据
  }
}

/**
 * 获取用户扩展信息（认证徽章等）
 */
function fetchUserProfile() {
  // Mock模式或API未实现时使用Mock数据
  if (ENV_CONFIG.VITE_USE_MOCK) {
    return mockUserProfile;
  }
  // TODO: 待后端实现 GET /api/v1/users/me 后替换
  return mockUserProfile;
}

/**
 * 加载用户数据（登录后调用）
 */
async function loadUserData() {
  if (!isAuthenticated.value) return;
  
  // 并行加载统计数据和用户信息
  const [stats, profile] = await Promise.all([
    fetchUserStats(),
    Promise.resolve(fetchUserProfile()),
  ]);
  
  userStats.value = stats;
  userProfile.value = profile;
}

// 生命周期
onMounted(async () => {
  loadSettings();
  await loadUserData();
});

onShow(async () => {
  // 每次显示页面时刷新数据
  loadSettings();
  await loadUserData();
});

// 方法
const loadSettings = () => {
  // 加载本地设置
  const savedTrafficReminder = uni.getStorageSync('settings_traffic_reminder');
  trafficReminder.value = savedTrafficReminder !== false;
};

const requireAuth = (callback: () => void) => {
  if (!isAuthenticated.value) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    // 使用authStore的登录跳转方法（内部已处理多平台兼容）
    authStore.forceReauth('/pages/app/tabbar/my/index');
    return;
  }
  callback();
};

const handleLogin = () => {
  // 使用authStore的登录跳转方法（内部已处理多平台兼容）
  authStore.forceReauth('/pages/app/tabbar/my/index');
};

const handleEditProfile = () => {
  requireAuth(() => {
    uni.showToast({ title: '个人资料编辑功能开发中', icon: 'none' });
  });
};

const handleQuickAction = (action: typeof quickActions.value[0]) => {
  if (action.requireAuth) {
    requireAuth(() => {
      uni.navigateTo({ url: action.path });
    });
  } else {
    uni.navigateTo({ url: action.path });
  }
};

const handleMyLive = () => {
  requireAuth(() => {
    uni.navigateTo({ url: '/pages/app/live-manage/list' });
  });
};

const handleCreateLive = () => {
  requireAuth(() => {
    uni.navigateTo({ url: '/pages/app/live-manage/list?action=create' });
  });
};

const handleAppearance = () => {
  uni.navigateTo({ url: '/pages/app/tabbar/my/settings/appearance' });
};

const handleTrafficReminderChange = (e: any) => {
  trafficReminder.value = e.detail.value;
  uni.setStorageSync('settings_traffic_reminder', e.detail.value);
  uni.showToast({
    title: e.detail.value ? '已开启流量提醒' : '已关闭流量提醒',
    icon: 'none'
  });
};

const handleAbout = () => {
  uni.navigateTo({ url: '/pages/app/tabbar/my/about/index' });
};

const handlePrivacy = () => {
  // 打开隐私政策链接
  uni.navigateTo({
    url: '/pages/shared/webview/index?url=' + encodeURIComponent('https://example.com/privacy')
  });
};

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        authStore.logout();
      }
    }
  });
};
</script>
```

#### 7.1.3 样式实现 (`<style>`)

```scss
<style lang="scss" scoped>
.my-page {
  min-height: 100vh;
  background-color: var(--bg-page, #F5F5F5);
  padding-bottom: 40rpx;
}

/* 用户信息卡片 */
.user-card {
  background: linear-gradient(135deg, #509CEC 0%, #3B7DD8 100%);
  padding: 60rpx 32rpx 40rpx;
  margin-bottom: 24rpx;
  
  &.not-logged-in {
    background: linear-gradient(135deg, #999999 0%, #666666 100%);
  }
}

.user-info {
  display: flex;
  align-items: center;
}

.avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(255, 255, 255, 0.3);
  
  &.default {
    opacity: 0.8;
  }
}

.user-details {
  flex: 1;
  margin-left: 32rpx;
}

.nickname-row {
  display: flex;
  align-items: center;
}

.nickname {
  font-size: 40rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.edit-btn {
  margin-left: 16rpx;
  padding: 8rpx;
  
  .iconfont {
    font-size: 32rpx;
    color: rgba(255, 255, 255, 0.8);
  }
}

.badges {
  display: flex;
  margin-top: 16rpx;
  gap: 16rpx;
}

.badge {
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
  
  &.broadcaster {
    background-color: rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
  }
  
  &.expert {
    background-color: rgba(255, 215, 0, 0.3);
    color: #FFFFFF;
  }
}

.login-prompt {
  display: flex;
  align-items: center;
}

.login-text {
  margin-left: 32rpx;
  
  .title {
    display: block;
    font-size: 36rpx;
    font-weight: 600;
    color: #FFFFFF;
  }
  
  .subtitle {
    display: block;
    font-size: 26rpx;
    color: rgba(255, 255, 255, 0.7);
    margin-top: 8rpx;
  }
}

/* 快捷功能区 */
.quick-actions {
  display: flex;
  justify-content: space-around;
  background-color: var(--bg-content, #FFFFFF);
  padding: 32rpx 0;
  margin-bottom: 24rpx;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 120rpx;
}

.icon-wrapper {
  position: relative;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
  border-radius: 50%;
  
  .iconfont {
    font-size: 40rpx;
    color: var(--text-primary, #333333);
  }
}

.badge-count {
  position: absolute;
  top: -8rpx;
  right: -8rpx;
  min-width: 32rpx;
  height: 32rpx;
  padding: 0 8rpx;
  background-color: #FF4D4F;
  border-radius: 16rpx;
  font-size: 20rpx;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-label {
  font-size: 24rpx;
  color: var(--text-secondary, #666666);
  margin-top: 12rpx;
}

/* 菜单区域 */
.menu-section {
  background-color: var(--bg-content, #FFFFFF);
  margin-bottom: 24rpx;
}

.section-title {
  padding: 24rpx 32rpx 16rpx;
  font-size: 26rpx;
  color: var(--text-tertiary, #999999);
}

.menu-list {
  padding: 0 32rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 32rpx 0;
  border-bottom: 1rpx solid var(--border-color, #E5E5E5);
  
  &:last-child {
    border-bottom: none;
  }
  
  .iconfont {
    font-size: 40rpx;
    color: var(--text-primary, #333333);
    
    &.icon-arrow-right {
      font-size: 28rpx;
      color: var(--text-tertiary, #999999);
    }
  }
  
  .menu-label {
    flex: 1;
    margin-left: 24rpx;
    font-size: 30rpx;
    color: var(--text-primary, #333333);
  }
  
  switch {
    transform: scale(0.8);
  }
}

/* 退出登录 */
.logout-section {
  padding: 48rpx 32rpx;
}

.logout-btn {
  background-color: var(--bg-content, #FFFFFF);
  padding: 28rpx;
  border-radius: 16rpx;
  text-align: center;
  
  text {
    font-size: 32rpx;
    color: var(--color-danger, #FF4D4F);
  }
}

/* 版本号 */
.version-info {
  text-align: center;
  padding: 24rpx;
  
  text {
    font-size: 24rpx;
    color: var(--text-tertiary, #999999);
  }
}
</style>
```

---

### 步骤2：生成占位页面

**📁 文件：`src/pages/app/tabbar/my/favorites/index.vue`**

```vue
<template>
  <view class="placeholder-page">
    <view class="content">
      <text class="iconfont icon-star icon"></text>
      <text class="title">我的收藏</text>
      <text class="description">收藏列表功能即将上线</text>
    </view>
  </view>
</template>

<script setup lang="ts">
// 占位页面，后续实现完整功能
</script>

<style lang="scss" scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx;
}

.icon {
  font-size: 120rpx;
  color: #CCCCCC;
  margin-bottom: 32rpx;
}

.title {
  font-size: 36rpx;
  color: #333333;
  margin-bottom: 16rpx;
}

.description {
  font-size: 28rpx;
  color: #999999;
}
</style>
```

---

**📁 文件：`src/pages/app/tabbar/my/watch-history/index.vue`**

```vue
<template>
  <view class="placeholder-page">
    <view class="content">
      <text class="iconfont icon-history icon"></text>
      <text class="title">观看历史</text>
      <text class="description">观看历史功能即将上线</text>
    </view>
  </view>
</template>

<script setup lang="ts">
// 占位页面，后续实现完整功能
</script>

<style lang="scss" scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx;
}

.icon {
  font-size: 120rpx;
  color: #CCCCCC;
  margin-bottom: 32rpx;
}

.title {
  font-size: 36rpx;
  color: #333333;
  margin-bottom: 16rpx;
}

.description {
  font-size: 28rpx;
  color: #999999;
}
</style>
```

---

**📁 文件：`src/pages/app/tabbar/my/subscriptions/index.vue`**

```vue
<template>
  <view class="placeholder-page">
    <view class="content">
      <text class="iconfont icon-heart icon"></text>
      <text class="title">我的订阅</text>
      <text class="description">订阅列表功能即将上线</text>
    </view>
  </view>
</template>

<script setup lang="ts">
// 占位页面，后续实现完整功能
</script>

<style lang="scss" scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx;
}

.icon {
  font-size: 120rpx;
  color: #CCCCCC;
  margin-bottom: 32rpx;
}

.title {
  font-size: 36rpx;
  color: #333333;
  margin-bottom: 16rpx;
}

.description {
  font-size: 28rpx;
  color: #999999;
}
</style>
```

---

**📁 文件：`src/pages/app/tabbar/my/settings/appearance.vue`**

```vue
<template>
  <view class="placeholder-page">
    <view class="content">
      <text class="iconfont icon-setting icon"></text>
      <text class="title">外观设置</text>
      <text class="description">外观设置功能即将上线</text>
    </view>
  </view>
</template>

<script setup lang="ts">
// 占位页面，后续实现完整功能
</script>

<style lang="scss" scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx;
}

.icon {
  font-size: 120rpx;
  color: #CCCCCC;
  margin-bottom: 32rpx;
}

.title {
  font-size: 36rpx;
  color: #333333;
  margin-bottom: 16rpx;
}

.description {
  font-size: 28rpx;
  color: #999999;
}
</style>
```

---

**📁 文件：`src/pages/app/tabbar/my/about/index.vue`**

```vue
<template>
  <view class="placeholder-page">
    <view class="content">
      <text class="iconfont icon-more icon"></text>
      <text class="title">关于我们</text>
      <text class="description">应用版本 v1.0.0</text>
    </view>
  </view>
</template>

<script setup lang="ts">
// 占位页面，后续实现完整功能
</script>

<style lang="scss" scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F5F5;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx;
}

.icon {
  font-size: 120rpx;
  color: #CCCCCC;
  margin-bottom: 32rpx;
}

.title {
  font-size: 36rpx;
  color: #333333;
  margin-bottom: 16rpx;
}

.description {
  font-size: 28rpx;
  color: #999999;
}
</style>
```

---

### 步骤3：更新路由配置

**📁 文件：`src/pages.json`**

使用 `multi_edit` 在 `pages` 数组中添加以下路由：

```json
{
  "path": "pages/app/tabbar/my/favorites/index",
  "style": {
    "navigationBarTitleText": "我的收藏"
  }
},
{
  "path": "pages/app/tabbar/my/watch-history/index",
  "style": {
    "navigationBarTitleText": "观看历史"
  }
},
{
  "path": "pages/app/tabbar/my/subscriptions/index",
  "style": {
    "navigationBarTitleText": "我的订阅"
  }
},
{
  "path": "pages/app/tabbar/my/settings/appearance",
  "style": {
    "navigationBarTitleText": "外观设置"
  }
},
{
  "path": "pages/app/tabbar/my/about/index",
  "style": {
    "navigationBarTitleText": "关于我们"
  }
}
```

---

## 第8章：验证清单（Validation Checklist）

### 8.1 功能验证

- [ ] 用户信息卡片正常显示（已登录/未登录两种状态）
- [ ] 快捷功能区4个图标可点击，跳转正确
- [ ] 快捷功能区badge数量正确显示（Mock模式下显示Mock数据）
- [ ] 直播管理菜单可点击，跳转到已有页面
- [ ] 设置菜单可点击，跳转到占位页
- [ ] 流量提醒开关可切换，状态保存到本地
- [ ] 退出登录弹出确认框，确认后正确登出
- [ ] 未登录时点击需登录功能，提示并跳转登录页

### 8.2 Mock/API切换验证

- [ ] `VITE_USE_MOCK=true` 时使用 `mock-data.ts` 中的数据
- [ ] `VITE_USE_MOCK=false` 时调用真实API（`getFavorites`等）
- [ ] API调用失败时降级到Mock数据
- [ ] 与首页的Mock/API切换模式保持一致

### 8.3 样式验证

- [ ] 页面布局与设计稿一致
- [ ] 颜色使用CSS变量，支持主题切换
- [ ] 响应式单位使用rpx
- [ ] 最小可点击区域 ≥ 88rpx

### 8.4 代码质量验证

- [ ] 使用Vue 3 Composition API + TypeScript
- [ ] 无any类型
- [ ] 导入路径使用@别名
- [ ] 有完整的注释

---

## 第9章：后续扩展API清单（待后端实现）

### 9.1 已有API（本次开发直接使用）

以下API已存在于项目中，本次开发直接调用：

| API 文件 | 函数 | 用途 | 状态 |
|----------|------|------|------|
| `@/api/favorite.ts` | `getFavorites()` | 获取收藏列表 | ✅ 已有 |
| `@/api/subscription.ts` | `getSubscriptions()` | 获取订阅列表 | ✅ 已有 |
| `@/api/watchHistory.ts` | `getWatchHistory()` | 获取观看历史 | ✅ 已有 |

### 9.2 待后端实现的API

以下API接口在本次开发中使用Mock数据，待后端实现后对接：

| 接口 | 方法 | 用途 | 当前状态 |
|------|------|------|----------|
| `GET /api/v1/users/me` | GET | 获取当前用户完整信息（含认证徽章） | ❌ 需新建 |
| `PATCH /api/v1/users/me` | PATCH | 更新用户信息 | ❌ 需新建 |
| `GET /api/v1/users/me/notifications` | GET | 获取通知列表 | ❌ 需新建 |
| `POST /api/v1/auth/logout` | POST | 后端登出（使Token失效） | ❌ 需新建 |

**建议创建的API文件**：`src/api/user.ts`（仅包含上述待实现的接口）

```typescript
/**
 * 用户相关API（待后端实现后补充）
 * @file src/api/user.ts
 */

import { get, patch, post } from '@/utils/request';
import type { ApiResponse } from '@/types/common';

// 用户信息接口（扩展auth.ts中的User接口）
export interface UserProfile {
  user_id: string;
  username: string;
  email?: string;
  avatar?: string;
  is_broadcaster?: boolean;  // 是否主播
  is_expert?: boolean;       // 是否专家
  created_at?: string;
  updated_at?: string;
}

/**
 * 获取当前用户信息
 * @returns Promise<ApiResponse<UserProfile>>
 */
export const getCurrentUser = (): Promise<ApiResponse<UserProfile>> => {
  return get<ApiResponse<UserProfile>>('/users/me', undefined, { auth: true });
};

/**
 * 更新用户信息
 * @param data 更新数据
 * @returns Promise<ApiResponse<UserProfile>>
 */
export const updateCurrentUser = (data: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> => {
  return patch<ApiResponse<UserProfile>>('/users/me', data, { auth: true });
};

/**
 * 后端登出（使Token失效）
 * @returns Promise<ApiResponse<void>>
 */
export const logoutApi = (): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>('/auth/logout', undefined, { auth: true });
};
```

---

## 🎯 执行指令（Execution Instructions）

**AI，现在请严格按照以上提示词执行代码生成：**

### 执行流程

1. **第0章**：执行强制性前置检查
   - 读取所有现有核心文件
   - 扫描pages/app/tabbar/my/目录
   - 在聊天窗口输出项目现状分析

2. **等待用户确认**
   - 展示分析报告
   - 等待用户输入"确认继续"

3. **按优先级生成代码**
   - P0任务：my/index.vue → 占位页面 → 路由配置
   - 每个文件生成后进行验证

4. **最终质量检查**
   - 执行验证清单
   - 输出完成报告

### 关键提醒

⚠️ **这是增量开发项目，安全第一！**
- 不覆盖现有代码（除my/index.vue需要重写）
- 使用multi_edit补充路由配置
- 保留所有现有实现

✅ **代码质量要求**
- Vue 3 Composition API + TypeScript
- uni-app原生组件 + iconfont
- 完整的注释和类型定义

---

**[我的页面代码生成提示词文档 - 完成]**
