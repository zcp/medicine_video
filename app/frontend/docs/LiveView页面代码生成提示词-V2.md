# App端播放页面代码生成提示词 (uni-app移动端版 V3.1 - Vue统一方案)

---

## ⚠️ 重要声明

**本提示词采用统一Vue技术栈方案：所有页面（包括播放页）均使用标准.vue文件。**

- ✅ **技术栈**：纯Vue 3 Composition API + TypeScript
- ✅ **核心难点解决**：针对App端原生`<video>`组件层级最高的问题，强制使用`<cover-view>`和`<cover-image>`实现覆盖在视频上的UI
- ✅ **兼容性**：完全避开nvue的CSS限制和编译陷阱，保证开发效率
- ✅ **渐进增强**：通过cover-view组件解决video层级问题
- ✅ **演示模式优化**：聊天和问答功能支持本地模拟交互，提升Demo体验
- ✅ **适配完善**：全面屏安全区适配，键盘遮挡问题解决
- ✅ **资源管理优化**：内存泄漏防护，屏幕常亮自动清理
- ✅ **用户体验增强**：加载状态反馈，全屏方向锁定
- ✅ **容错机制增强**：ShadowParser解析失败不阻断播放，错误处理完善
- ✅ **生产就绪**：包含完整的错误处理、性能优化、测试策略

---

## 🏗️ 架构基础（必读）

**在开始开发前，你必须先阅读以下文档：**

📖 **设计文档**：
- `docs/直播saas平台网站前端效果设计---移动端版(v1.3）.md`（第7.0章节 - 直播间页面设计）
- `docs/直播SaaS平台移动端前端设计文档.md`（第6章 - 核心数据模型、第8章 - API接口映射）
- `docs/后端新增api接口和模块设计文档-v2.md`（Section 4.8-4.12 场次相关API）
- `docs/App端播放功能开发方案分析.md`（播放功能完整架构设计）

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
| `icon-arrow-right` | 右箭头 | `icon-close` | 关闭 |
| `icon-delete` | 删除 | `icon-share` | 分享 |
| `icon-eye` | 查看/流量 | `icon-search` | 搜索 |

---

## 第0章：强制性前置检查 ⚡（必须先执行）

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
✅ src/api/session.ts - 会话数据获取（getSessionDetail等）
✅ src/api/watchHistory.ts - 观看历史录制（recordWatch等）
✅ src/config/env.ts - 环境配置（VITE_USE_MOCK开关）
✅ src/components/app/VideoPlayerApp.vue - 现有播放器组件
✅ src/pages/app/tabbar/home/mock-data.ts - 首页Mock数据格式
✅ src/static/fonts/iconfont.css - 可用图标列表
✅ src/pages.json - 路由配置
✅ src/types/session.ts - 会话类型定义
✅ src/types/watchHistory.ts - 观看历史类型定义
```

**执行命令**：使用 `read_file` 工具逐个读取以上文件。

#### 步骤2：扫描目录结构（强制）

```bash
必须扫描的目录：
✅ src/pages/app/ - 确认页面目录结构
✅ src/api/ - 列出所有.ts文件
✅ src/store/ - 列出所有.ts文件
✅ src/components/ - 列出可复用组件
✅ src/utils/ - 列出现有工具函数
```

**执行命令**：使用 `find_by_name` 或 `list_dir` 工具扫描目录。

#### 步骤3：在聊天窗口输出项目现状分析（强制）

**重要**：❗ 不要生成单独的分析报告文件，直接在聊天窗口中展示分析结果！

基于步骤1和步骤2的检查结果，在聊天窗口中输出以下结构化分析：

---

**📊 LiveView页面开发现状分析**

**一、已存在且可直接复用的文件（✅ 直接使用）**
- 列出所有可复用的API、Store、组件
- 注明文件路径、核心功能
- 给出"直接导入使用"的结论

**二、已存在但需要扩展的文件（🔧 需要补充）**
- 列出需要补充的文件（如VideoPlayerApp.vue的事件处理）
- 明确列出现有字段清单
- 明确列出缺失字段（如ShadowParser集成、TS切片检测）
- 说明操作方式（multi_edit，保留现有字段）

**三、需要新建的文件（➕ 需新建）**
- 列出所有需要新建的页面文件
- 列出需要新建的组件文件
- 列出需要新建的类型定义文件
- 列出需要新建的工具类文件

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
📋 以上是LiveView页面开发现状分析结果。

请确认：
1. 分析结果是否准确？
2. 是否有遗漏或需要调整的地方？
3. 如果确认无误，请输入"确认继续"开始代码生成。
```

**禁止**在用户确认前开始生成任何代码！

---

## 第1章：角色定义（Role Definition）

你是一名**资深移动端前端工程师**，具备以下专业技能：

- **精通技术栈**：uni-app、Vue 3 Composition API、TypeScript、移动端H5、小程序等多端开发
- **视频播放技术**：熟悉HLS协议、m3u8解析、TS切片处理、播放器事件处理
- **增量开发能力**：能够在现有项目基础上进行安全的增量开发，不破坏现有功能
- **跨平台适配**：精通uni-app的平台差异处理和条件编译

**你的任务是根据详细设计文档和现有代码基础，编写高质量、功能完整、可直接运行的增量代码。**

---

## 第2章：任务目标（Task Objective）

### 2.1 核心目标

开发App端播放页面（`src/pages/app/live/LiveView.vue`），实现以下功能模块：

1. **播放器核心功能**：集成ShadowParser进行m3u8解析和TS切片检测
2. **页面布局结构**：顶部信息栏 + 播放器区域 + Sticky底部Tab栏
3. **智能流量提醒**：网络状态监听和流量消耗提醒
4. **观看人数显示**：实时显示当前观看人数
5. **播放统计收集**：收集播放质量数据和技术指标

### 2.2 页面布局设计

```
┌─────────────────────────────────────┐
│         顶部信息栏                   │
│  ┌─────┐                            │
│  │头像 │ 标题（智能折叠）     [分享] │
│  │     │  🔴 LIVE  1.2万观看        │
│  └─────┘                            │
├─────────────────────────────────────┤
│                                     │
│         播放器区域                   │
│    （VideoPlayerApp组件）            │
│                                     │
├═════════════════════════════════════┤
│      Sticky底部Tab栏                │
│  ┌────┬────┬────┬────┐            │
│  │详情│聊天│问答│推荐│            │
│  └────┴────┴── ─┴────┘            │
├─────────────────────────────────────┤
│                                     │
│        Tab内容区                    │
│    （详情/聊天/问答/推荐内容）        │
│                                     │
└─────────────────────────────────────┘
```

### 2.3 开发复用策略

#### 2.3.1 完全复用层（100%复用）
- **API层**：`src/api/session.ts`、`src/api/watchHistory.ts`
- **类型定义**：`src/types/session.ts`、`src/types/watchHistory.ts`、`src/types/common.ts`
- **业务逻辑**：数据获取、状态管理、错误处理、格式化函数

#### 2.3.2 部分复用层（60-80%复用）
- **数据处理逻辑**：playerSourceUrl计算逻辑、状态监听逻辑
- **播放控制逻辑**：TS切片检测、上报逻辑（需适配App端事件）

#### 2.3.3 统一Vue技术栈实现（CSS层级优化）
- **播放页面**：LiveView.vue - 使用Vue组件，通过z-index和定位解决层级问题
- **播放器组件**：VideoPlayerApp.vue - Vue组件，通过样式封装优化播放体验
- **工具类**：ShadowParser.ts - TypeScript工具类，与技术栈无关
- **其他页面**：继续使用.vue格式，保持统一开发体验

---

## 第3章：关键技术规范（Crucial Specs）

### 3.1 视频覆盖层解决方案（Cover-View）⚠️ 重点

**在App端（非H5），`<video>`是原生组件，层级最高。为了在视频上显示UI，必须遵循以下规则：**

**覆盖层组件**：所有悬浮在视频上方的元素（如：顶部的"观看人数"、底部的"播放控制栏"、中间的"加载Loading"），必须使用`<cover-view>`和`<cover-image>`标签。

**普通组件**：不能覆盖视频的元素（如：视频下方的聊天列表、详情页），使用标准的`<view>`、`<text>`、`<scroll-view>`。

**样式限制**：`<cover-view>`不支持复杂的CSS（如阴影、渐变支持有限），布局尽量简单，使用Flexbox。

**示例代码**：
```vue
<template>
  <view class="video-container">
    <video id="myVideo" :src="src" class="video-elem" :controls="false">
      <!-- ✅ 重点：使用cover-view覆盖在视频上 -->
      <cover-view v-if="showControls" class="controls-layer">
        <cover-view class="btn" @click="togglePlay">
          <cover-image src="/static/icons/play.png" />
        </cover-view>
      </cover-view>

      <!-- 观看人数 -->
      <cover-view class="viewer-badge">
        <cover-view class="viewer-text">👁️ {{ viewerCount }}</cover-view>
      </cover-view>
    </video>
  </view>
</template>
```

### 3.2 播放器核心功能（VideoPlayerApp.vue增强）

| 组件 | 功能 | 实现状态 |
|------|------|----------|
| **ShadowParser集成** | m3u8解析、TS切片检测 | 需要新建 |
| **播放事件监听** | timeupdate、seeked、waiting等 | 需要增强 |
| **TS切片上报** | 检测切片切换并上报后端 | 需要实现 |
| **播放地址获取** | Live/VOD模式地址处理 | 需要实现 |

#### 3.1.1 ShadowParser.ts 核心功能

```typescript
interface Segment {
  name: string;        // TS文件名（如：43811948589-3-127088_1984_1631_d0.ts）
  url: string;         // 完整URL
  start: number;       // 开始时间（秒）
  end: number;         // 结束时间（秒）
  duration: number;    // 时长（秒）
  index: number;       // 索引
}

class ShadowParser {
  private m3u8Url: string;
  private segments: Segment[] = [];
  private currentTs: string | null = null;

  // 核心方法
  async init(): Promise<void>
  check(currentTime: number): Segment | null
  private parse(content: string): void
  private resolveUrl(url: string): string
}
```

#### 3.1.2 VideoPlayerApp.vue 事件处理

```typescript
// 播放器事件处理
const onTimeUpdate = (e: any) => {
  const currentTime = e.detail?.currentTime || 0;
  // TS切片检测逻辑
  if (parser.value) {
    const segment = parser.value.check(currentTime);
    if (segment) {
      reportSegment(segment);
    }
  }
};

const onSeeked = (e: any) => {
  const currentTime = e.detail?.currentTime || 0;
  // 用户拖动进度条后的处理
  if (parser.value) {
    const segment = parser.value.check(currentTime);
    if (segment) {
      reportSegment(segment, true); // isSeek = true
    }
  }
};
```

### 3.2 页面布局结构（LiveView.vue）

| 区域 | 功能 | 组件类型 |
|------|------|----------|
| **顶部信息栏** | 标题、状态、操作按钮 | view + text + button |
| **播放器区域** | VideoPlayerApp组件 | VideoPlayerApp |
| **Sticky Tab栏** | 详情/聊天/问答/推荐 | scroll-view + view |
| **Tab内容区** | 动态内容展示 | component + scroll-view（明确使用scroll-view）|

#### 3.3.1 顶部信息栏设计

```
┌─────────────────────────────────────┐
│  ┌─────┐                            │
│  │头像 │ 肝胆胰外科微创手术... [展开▼] │
│  │     │  🔴 LIVE  1.2万观看  10/28 │
│  └─────┘                            │
│  [👨‍⚕️] 张三 教授        [+ 关注]   │
│         北京协和医院                │
│                                     │
│  ❤️收藏  📥下载资料  🔗分享         │
└─────────────────────────────────────┘
```

#### 3.3.2 Sticky Tab栏设计

```vue
<!-- Sticky Tabs -->
<view class="sticky-tabs" :class="{ 'stuck': tabsStuck }">
  <scroll-view scroll-x class="tabs-container">
    <view
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-item"
      :class="{ active: activeTab === tab.key }"
      @tap="switchTab(tab.key)"
    >
      <text>{{ tab.label }}</text>
    </view>
  </scroll-view>
</view>
```

### 3.4 智能流量提醒功能

| 触发时机 | 检测逻辑 | 用户交互 |
|----------|----------|----------|
| **进入直播间时** | `uni.getNetworkType()` | 4G/5G网络显示提醒弹窗 |
| **播放开始时** | 网络状态变化监听 | 继续观看/取消选择 |
| **网络切换时** | `uni.onNetworkStatusChange` | 动态提醒 |

#### 3.3.1 流量提醒弹窗

```vue
<!-- 流量提醒弹窗 -->
<view v-if="showTrafficWarning" class="traffic-warning-modal">
  <view class="modal-content">
    <text class="warning-icon">⚠️</text>
    <text class="warning-title">流量提醒</text>
    <text class="warning-message">
      您当前使用的是{{ networkType }}网络，
      观看直播可能消耗较多流量（约500MB/小时）
    </text>
    <view class="modal-actions">
      <button @tap="cancelPlayback">取消</button>
      <button @tap="continuePlayback">继续观看</button>
    </view>
  </view>
</view>
```

### 3.5 观看人数显示功能

| 功能点 | 实现方式 | 更新频率 |
|--------|----------|----------|
| **实时显示** | 播放器右上角悬浮显示 | 每30秒更新 |
| **数据获取** | API调用获取实时数据 | 页面激活时启动 |
| **显示格式** | 👁️ 1,234人在看 | 数字格式化 |

### 3.6 播放统计数据收集

| 数据类型 | 收集时机 | 上报方式 |
|----------|----------|----------|
| **播放事件** | play/pause/seek等 | 实时上报 |
| **质量指标** | 卡顿、缓冲、清晰度切换 | 播放结束时汇总 |
| **错误信息** | 播放失败、网络错误 | 错误发生时立即上报 |

#### 3.5.1 PlaybackStats数据结构

```typescript
interface PlaybackStats {
  session_id: string;
  user_id: string;
  device: string;
  platform: 'app' | 'h5';
  start_time: number;      // 播放开始时间
  end_time: number;        // 播放结束时间
  total_duration: number;  // 总播放时长
  buffered_duration: number; // 缓冲时长
  stall_count: number;     // 卡顿次数
  stall_duration: number;  // 卡顿总时长
  quality_changes: number; // 清晰度切换次数
  final_quality: string;   // 最终播放清晰度
  errors: PlaybackError[]; // 播放错误
}
```

---

## 第4章：API依赖与数据流（API & Data Flow）

### 4.1 已有API（可直接使用）

| API 文件 | 函数 | 用途 |
|----------|------|------|
| `@/api/session.ts` | `getSessionDetail()` | 获取场次详情 |
| `@/api/watchHistory.ts` | `recordWatch()` | 录制观看历史 |
| `@/store/auth.ts` | `useAuthStore()` | 用户认证状态 |

### 4.1.1 新增全局状态管理

**播放器全局状态**：`src/store/player.ts`
```typescript
import { defineStore } from 'pinia';

export const usePlayerStore = defineStore('player', () => {
  // 播放状态管理
  const currentUrl = ref('');
  const isPlaying = ref(false);
  const currentTime = ref(0);
  const viewerCount = ref(0);

  // 方法定义
  const setPlayingState = (playing: boolean) => {
    isPlaying.value = playing;
  };

  const updateViewerCount = (count: number) => {
    viewerCount.value = count;
  };

  return {
    currentUrl,
    isPlaying,
    currentTime,
    viewerCount,
    setPlayingState,
    updateViewerCount
  };
});
```

### 4.2 需要新建的API

#### 4.2.1 播放相关API（新建 `src/api/playback.ts`）

```typescript
// 实时观看人数API
export const getRealtimeViewers = (sessionId: string) => {
  return request<{ count: number; timestamp: string }>({
    url: `/sessions/${sessionId}/viewers`,
    method: 'GET'
  });
};

// 上报播放统计数据
export const reportPlaybackStats = (stats: PlaybackStats) => {
  return request({
    url: '/api/v1/playback/stats',
    method: 'POST',
    data: stats
  });
};

// 直播流地址获取（可选）
export const getLiveStreamUrl = (sessionId: string) => {
  return request<{ url: string; expires_at: string }>({
    url: `/sessions/${sessionId}/stream-url`,
    method: 'GET'
  });
};
```

#### 4.2.2 Mock数据文件（新建 `src/pages/app/live/mock-data.ts`）

```typescript
// 播放页面Mock数据
export const mockViewerCount = {
  count: 1234,
  timestamp: new Date().toISOString()
};

export const mockSessionData = {
  id: 'session-123',
  room_id: 'room-456',
  title: '肝胆胰外科微创手术的最新进展与病例讨论会',
  summary: '本次直播将邀请国内知名肝胆胰外科专家...',
  status: 'live',
  start_time: new Date().toISOString(),
  cover_url: '/static/mock-cover.jpg',
  playback_url: 'https://example.com/live.m3u8',
  expert: {
    name: '张三',
    title: '教授',
    hospital: '北京协和医院'
  }
};
```

### 4.3.1 混合Mock策略详解

#### **🎯 策略核心思想**
采用"**主战场真实，侧翼战场模拟**"的战术：
- **主播放器**：使用你的真实m3u8 URL，测试实际业务环境
- **推荐列表**：使用差异化测试源，验证切换功能

#### **📊 策略优势对比**

| 场景 | 纯示例链接 | 纯真实链接 | 混合策略 ✅ |
|-----|----------|----------|-----------|
| **播放测试** | ❌ 无法播放 | ✅ 真实播放 | ✅ 真实播放 |
| **切换验证** | ❌ 无差异 | ❌ 内容相同 | ✅ 内容区分 |
| **问题发现** | ❌ 无价值 | ✅ 发现问题 | ✅ 发现问题 |
| **演示效果** | ❌ 无意义 | ✅ 专业内容 | ✅ 专业内容 |

#### **🎬 实际测试效果**
```typescript
// 打开页面 → 显示手术视频 ✅
// 点击推荐1 → 还是手术视频（路由测试）
// 点击推荐2 → 切换到兔子动画 🎥（切换确认）
```

#### **🔧 配置灵活性**
```typescript
const CURRENT_CONFIG = {
  primary: TEST_M3U8_URLS.real,      // 可切换测试源
  secondary: TEST_M3U8_URLS.cartoon, // 可切换差异内容
  backup: TEST_M3U8_URLS.apple       // 备用稳定源
};
```

### 4.3.2 数据流向

```
页面加载 (onMounted/onShow)
  ↓
检查登录状态 (authStore.isAuthenticated)
  ├─ 已登录 → 调用 getSessionDetail() 获取场次数据
  │           ├─ VITE_USE_MOCK=true → 使用 mock-data.ts
  │           └─ VITE_USE_MOCK=false → 调用真实API
  │           ↓
  │           初始化ShadowParser，解析m3u8
  │           ↓
  │           开始播放器初始化
  └─ 未登录 → 显示登录提示
  ↓
用户操作播放器
  ├─ 播放开始 → 屏幕常亮 + 网络检测
  ├─ 时间更新 → TS切片检测 + 上报
  ├─ 进度拖动 → seek事件处理
  └─ 播放结束 → 统计数据上报
```

---

## 第5章：核心原则（Core Principles）

### 5.1 统一Vue技术栈原则 ⚡

#### 5.1.1 技术栈选择策略
- **统一格式**：所有页面统一使用`.vue`格式，保证开发一致性
- **组件复用**：通过scoped样式和组件封装解决层级问题
- **工具类**：`.ts`文件与技术栈无关，可复用

#### 5.1.2 文件命名规范
```bash
# 所有页面统一使用vue格式
src/pages/app/live/LiveView.vue
src/components/app/VideoPlayerApp.vue
src/pages/app/tabbar/home.vue
src/components/common/UserAvatar.vue

# 工具和类型 - TypeScript
src/utils/ShadowParser.ts
src/types/playback.ts
```

#### 5.1.3 组件引用规则
```vue
<!-- ✅ vue页面引用vue组件 -->
<template>
  <view>
    <VideoPlayerApp />
  </view>
</template>

<script setup>
import VideoPlayerApp from '@/components/app/VideoPlayerApp.vue'
</script>
```

### 5.1 安全规范（Security Standards）⚠️ 强制遵循

#### 5.1.1 XSS防护
```typescript
// ✅ 正确：使用文本插值（Vue自动转义）
<text>{{ userInput }}</text>

// ❌ 禁止：使用v-html渲染用户输入
<view v-html="userInput"></view>
```

#### 5.1.2 本地存储安全
```typescript
// ✅ 流量提醒开关（非敏感）
uni.setStorageSync('settings_traffic_reminder', true);

// ❌ Token存储（由authStore统一管理）
uni.setStorageSync('jwt_token', token); // 禁止
```

### 5.2 UI组件库规范

#### 5.2.1 Vue文件规范（其他页面）
**所有UI元素必须使用uni-app原生组件 + iconfont图标**

```vue
<!-- ✅ 正确：使用uni-app原生组件 -->
<view class="menu-item">
  <text class="iconfont icon-star"></text>
  <text>收藏</text>
</view>

<!-- ❌ 错误：使用Element Plus组件 -->
<el-button>收藏</el-button>
```

#### 5.2.2 Vue文件规范（所有页面）✅ 完全支持
**Vue文件支持完整的CSS和组件功能，无特殊限制**

```vue
<!-- ✅ Vue完整写法：支持所有uni-app组件 -->
<view class="menu-item">
  <text class="iconfont icon-star"></text>
  <text>收藏</text>
</view>

<!-- ✅ 支持button等组件 -->
<button class="action-btn">收藏</button>
```

**Vue CSS完整支持：**
```scss
/* ✅ 完全支持 */
.container {
  flex: 1;
  background-color: #fff;
}

.container .item {
  margin: 10px;
} /* 后代选择器 */

view {
  border: 1px solid #eee;
} /* 标签选择器 */

* {
  box-sizing: border-box;
} /* 通配符选择器 */
```

**🔧 Vue字体图标标准规范：**

```vue
<!-- 直接使用class名，无需特殊处理 -->
<text class="iconfont icon-play"></text>
<text class="iconfont icon-pause"></text>
```

**🔧 Vue SCSS变量规范：**
```scss
/* ✅ 完全支持全局SCSS变量 */
.container {
  color: $color-primary;
}

/* ✅ 支持scoped样式 */
<style lang="scss" scoped>
.menu-item {
  .icon {
    color: $color-primary;
  }
}
</style>
```

### 5.3 播放地址获取策略

#### 5.3.1 当前推荐策略

```typescript
// App端播放地址获取策略
const playerSourceUrl = computed(() => {
  if (isLive.value) {
    // 直播：优先使用专门API，失败时降级使用playback_url
    return liveStreamUrl.value || currentSession.value?.playback_url;
  } else {
    // 回放：直接使用playback_url
    return currentSession.value?.playback_url || null;
  }
});
```

#### 5.3.2 地址获取流程

```
需要播放地址
  ↓
判断直播类型 (isLive)
  ├─ 直播 (live) → 调用 getLiveStreamUrl() API
  │                 ├─ 成功 → 使用返回的url
  │                 └─ 失败 → 降级使用 playback_url
  └─ 回放 (vod) → 直接使用 playback_url
```

### 5.4 播放统计数据收集策略

#### 5.4.1 数据收集原则

1. **实时事件**：播放开始/暂停/拖动等立即上报
2. **质量指标**：卡顿、缓冲、清晰度切换等累计收集
3. **汇总上报**：播放结束时汇总所有数据一次性上报

#### 5.4.2 数据上报时机

```typescript
// 实时上报（切片切换、用户操作）
const reportSegment = (segment: Segment, isSeek = false) => {
  recordWatch(sessionId, {
    progress: Math.floor(segment.start),
    extra: {
      ts_filename: segment.name,
      segment_index: segment.index,
      is_seek: isSeek,
      device: uni.getSystemInfoSync().model,
      platform: 'app'
    }
  });
};

// 汇总上报（播放结束）
const reportPlaybackStats = () => {
  const stats: PlaybackStats = {
    session_id: sessionId,
    user_id: userId,
    device: deviceInfo,
    platform: 'app',
    start_time: playStartTime,
    end_time: Date.now(),
    total_duration: totalPlayTime,
    buffered_duration: totalBufferTime,
    stall_count: stallCount,
    stall_duration: totalStallTime,
    quality_changes: qualityChangeCount,
    final_quality: currentQuality,
    errors: playbackErrors
  };

  // 调用API上报
  reportPlaybackStats(stats);
};
```

---

## 第6章：文件清单与生成指令（File List & Generation Instructions）

### 6.1 需要生成的文件

#### **P0级任务（必须完成）** ⚠️

| 序号 | 文件路径 | 操作类型 | 说明 |
|-----|---------|---------|------|
| 1 | `src/utils/ShadowParser.ts` | ✨ **新建** | m3u8解析器核心类（TypeScript） |
| 2 | `src/pages/app/live/LiveView.vue` | 🔧 **新建** | App端播放页面主入口（vue格式） |
| 3 | `src/components/app/VideoPlayerApp.vue` | 🔧 **新建** | 播放器组件（vue格式） |
| 4 | `src/api/playback.ts` | ✨ **新建** | 播放相关API接口 |
| 5 | `src/pages/app/live/mock-data.ts` | ✨ **新建** | 播放页面Mock数据 |
| 6 | `src/types/playback.ts` | ✨ **新建** | 播放相关类型定义 |
| 7 | `src/store/player.ts` | ✨ **新建** | 播放器全局状态管理 |

#### **P1级任务（体验优化）** 📋

| 序号 | 文件路径 | 操作类型 | 说明 |
|-----|---------|---------|------|
| 8 | `src/pages.json` | 🔧 **补充** | 添加LiveView页面路由 |
| 9 | `src/pages/app/live/index.vue` | 🔧 **修改** | 占位页添加自动重定向到LiveView的逻辑 |

---

## 第7章：分步生成与验证流程（Step-by-Step Generation）

### 步骤1：生成ShadowParser核心类

**📁 文件：`src/utils/ShadowParser.ts`**

```typescript
/**
 * ShadowParser - m3u8播放列表解析器
 * 用于uni-app原生video组件，实现TS切片检测和上报
 */

interface Segment {
  name: string;        // TS文件名（如：43811948589-3-127088_1984_1631_d0.ts）
  url: string;         // 完整URL
  start: number;       // 开始时间（秒）
  end: number;         // 结束时间（秒）
  duration: number;    // 时长（秒）
  index: number;       // 索引
}

export class ShadowParser {
  private m3u8Url: string;
  private baseUrl: string;
  private segments: Segment[] = [];
  private currentTs: string | null = null;
  private isLive: boolean = false;
  private refreshTimer: number | null = null;

  constructor(m3u8Url: string) {
    this.m3u8Url = m3u8Url;
    this.baseUrl = this.extractBaseUrl(m3u8Url);
  }

  /**
   * 初始化解析器
   */
  async init(): Promise<void> {
    await this.fetchM3u8();
    this.parseContent();
    if (this.isLive) {
      this.startRefreshTimer();
    }
  }

  /**
   * 销毁解析器
   */
  destroy(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * 根据播放时间检测当前切片
   * @param currentTime 当前播放时间（秒）
   * @returns 当前切片信息或null
   */
  check(currentTime: number): Segment | null {
    // 2秒容忍度，避免边界问题
    const tolerance = 2.0;

    const segment = this.segments.find(seg =>
      currentTime >= seg.start - tolerance && currentTime < seg.end + tolerance
    );

    if (segment && segment.name !== this.currentTs) {
      this.currentTs = segment.name;
      return segment;
    }

    return null;
  }

  /**
   * 获取所有切片信息（调试用）
   */
  getSegments(): Segment[] {
    return [...this.segments];
  }

  /**
   * 提取基础URL
   */
  private extractBaseUrl(url: string): string {
    const urlObj = new URL(url);
    return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname.substring(0, urlObj.pathname.lastIndexOf('/') + 1)}`;
  }

  /**
   * 获取m3u8内容
   */
  private async fetchM3u8(): Promise<void> {
    try {
      const response = await uni.request({
        url: this.m3u8Url,
        method: 'GET',
        timeout: 10000,
        // 🔧 增强容错：SSL证书验证关闭（App端）
        sslVerify: false,
        // 🔧 增强容错：处理CORS问题
        header: {
          'Accept': 'application/vnd.apple.mpegurl, application/x-mpegURL, */*',
          'Cache-Control': 'no-cache'
        }
      });

      if (response.statusCode === 200) {
        this.parseContent(response.data);
      } else {
        throw new Error(`HTTP ${response.statusCode}`);
      }
    } catch (error) {
      console.error('[ShadowParser] 获取m3u8失败:', error);

      // 🔧 增强容错：CORS错误处理
      if (error.errMsg && error.errMsg.includes('CORS')) {
        console.warn('[ShadowParser] 检测到CORS限制，播放器仍可正常播放，但切片检测功能受限');
        // 不抛出错误，允许播放器继续工作
        return;
      }

      throw error;
    }
  }

  /**
   * 解析m3u8内容
   */
  private parseContent(content: string): void {
    if (!content || typeof content !== 'string') {
      throw new Error('Invalid m3u8 content');
    }

    const lines = content.split('\n').filter(line => line.trim());
    let currentTime = 0;
    let segmentIndex = 0;
    let mediaSequence = 0;

    // 清空之前的数据
    this.segments = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // 检测是否为直播流
      if (line.includes('#EXT-X-PLAYLIST-TYPE:VOD')) {
        this.isLive = false;
      } else if (line.includes('#EXT-X-ENDLIST')) {
        this.isLive = false;
      }

      // 处理媒体序列号
      if (line.startsWith('#EXT-X-MEDIA-SEQUENCE:')) {
        mediaSequence = parseInt(line.split(':')[1]) || 0;
      }

      // 处理片段信息
      if (line.startsWith('#EXTINF:')) {
        const duration = parseFloat(line.split(':')[1].split(',')[0]);
        const nextLine = lines[i + 1]?.trim();

        if (nextLine && !nextLine.startsWith('#')) {
          const tsName = this.extractTsName(nextLine);
          const fullUrl = this.resolveUrl(nextLine);

          this.segments.push({
            name: tsName,
            url: fullUrl,
            start: currentTime,
            end: currentTime + duration,
            duration,
            index: segmentIndex++
          });

          currentTime += duration;
        }
      }
    }

    // 如果没有明确标记，默认认为是直播流
    if (!this.segments.length) {
      this.isLive = true;
    }

    console.log(`[ShadowParser] 解析完成: ${this.segments.length}个切片, ${this.isLive ? '直播' : '点播'}模式`);
  }

  /**
   * 提取TS文件名
   */
  private extractTsName(url: string): string {
    if (url.startsWith('http')) {
      return url.split('/').pop() || '';
    }
    return url.split('/').pop() || '';
  }

  /**
   * 解析URL（处理相对路径）
   */
  private resolveUrl(url: string): string {
    if (url.startsWith('http')) {
      return url;
    }
    return `${this.baseUrl}/${url}`.replace(/\/+/g, '/');
  }

  /**
   * 启动定时刷新（直播流）
   */
  private startRefreshTimer(): void {
    // 每30秒重新获取m3u8（直播流可能有新切片）
    this.refreshTimer = setInterval(async () => {
      try {
        await this.fetchM3u8();
        console.log('[ShadowParser] 直播流m3u8已刷新');
      } catch (error) {
        console.error('[ShadowParser] 刷新m3u8失败:', error);
      }
    }, 30000) as unknown as number;
  }
}
```

### 步骤2：创建VideoPlayerApp组件

**📁 文件：`src/components/app/VideoPlayerApp.vue`**

**⚠️ 重要**：作为Vue组件，通过CSS层级优化解决video显示问题

```vue
<template>
  <view class="video-player-app">
    <!-- uni-app原生video组件 -->
    <video
      v-if="src"
      :id="playerId"
      :src="src"
      :controls="false" <!-- 必须禁用原生控制条，使用自定义cover-view -->
      :autoplay="autoplay"
      class="video-elem"
      @play="onPlay"
      @pause="onPause"
      @timeupdate="onTimeUpdate"
    >
      <!-- ⚠️ 修正：所有覆盖在视频上的UI必须使用 cover-view -->

      <!-- 1. 播放控制遮罩 -->
      <cover-view v-if="showControls" class="player-overlay">
        <cover-view class="control-bar">
          <cover-view class="control-btn" @click="togglePlay">
            <cover-image class="btn-icon" :src="isPlaying ? '/static/icons/pause.png' : '/static/icons/play.png'" />
          </cover-view>
          <!-- 进度条在cover-view中通常简化处理，或使用原生slider -->
          <cover-view class="control-btn fullscreen" @click="toggleFullscreen">
            <cover-image class="btn-icon" src="/static/icons/fullscreen.png" />
          </cover-view>
        </cover-view>
      </cover-view>

      <!-- 2. 加载状态 -->
      <cover-view v-if="isLoading" class="loading-overlay">
        <cover-view class="loading-text">加载中...</cover-view>
      </cover-view>

      <!-- 3. 错误提示 -->
      <cover-view v-if="error" class="error-overlay">
        <cover-view class="error-text">{{ error }}</cover-view>
        <cover-view class="retry-btn" @click="retry">重试</cover-view>
      </cover-view>

      <!-- 4. 观看人数悬浮 -->
      <cover-view v-if="showViewerCount" class="viewer-count-overlay">
        <cover-view class="viewer-text">👁️ {{ formatViewerCount(viewerCount) }}</cover-view>
      </cover-view>
    </video>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { ShadowParser } from '@/utils/ShadowParser';
import { recordWatch } from '@/api/watchHistory';
import { useAuthStore } from '@/store/auth';

// Props
interface Props {
  src?: string;
  poster?: string;
  autoplay?: boolean;
  controls?: boolean;
  muted?: boolean;
  initialTime?: number;
  showViewerCount?: boolean;
  viewerCount?: number;
}

const props = withDefaults(defineProps<Props>(), {
  autoplay: false,
  controls: true,
  muted: false,
  initialTime: 0,
  showViewerCount: false,
  viewerCount: 0
});

// Emits
const emit = defineEmits<{
  play: [];
  playing: [];  // 🔧 加载状态优化：视频开始播放事件
  pause: [];
  ended: [];
  timeupdate: [detail: any];
  segmentchange: [data: any];
  error: [error: string];
}>();

// 响应式数据
const isPlaying = ref(false);
const isLoading = ref(false);
const error = ref('');
const currentTime = ref(0);
const duration = ref(0);
const isFullscreen = ref(false);
const showControls = ref(false);
const controlsTimer = ref<number | null>(null);

// ShadowParser实例
let parser: ShadowParser | null = null;
let lastReportedTs: string | null = null;
let reportTimer: number | null = null;

// 计算属性
const playerId = computed(() => `video-player-${Date.now()}`);
const progressPercent = computed(() => {
  return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0;
});

// 监听src变化，初始化解析器
watch(() => props.src, (newSrc) => {
  if (newSrc && newSrc.endsWith('.m3u8')) {
    initParser(newSrc);
  } else {
    destroyParser();
  }
});

// 生命周期
onMounted(() => {
  // 触摸显示控制栏
  showControlsWithTimeout();
});

onBeforeUnmount(() => {
  destroyParser();
  clearControlsTimer();
  // 🔧 资源释放优化：清理屏幕常亮状态，防止内存泄漏和电量消耗
  uni.setKeepScreenOn({ keepScreenOn: false });
});

// 方法
// 🎯 关键容错：解析器失败不能阻断视频播放
const initParser = async (m3u8Url: string) => {
  try {
    parser = new ShadowParser(m3u8Url);
    await parser.init();
    console.log('[VideoPlayerApp] ShadowParser初始化成功');
  } catch (error) {
    // 🔧 容错处理：解析器初始化失败不影响视频播放
    // 仅记录错误，继续播放（观看统计功能降级）
    console.warn('[VideoPlayerApp] ShadowParser初始化失败，但视频播放不受影响:', error);
    parser = null; // 确保parser为null，避免后续调用出错
  }
};

const destroyParser = () => {
  if (parser) {
    parser.destroy();
    parser = null;
  }
  lastReportedTs = null;
  clearReportTimer();
};

const clearReportTimer = () => {
  if (reportTimer) {
    clearTimeout(reportTimer);
    reportTimer = null;
  }
};

// 上报TS切片（防抖处理）
const reportSegment = async (segment: any, isSeek = false) => {
  if (!segment || segment.name === lastReportedTs) {
    return; // 避免重复上报
  }

  // 防抖：500ms内只上报一次
  if (reportTimer) {
    clearTimeout(reportTimer);
  }

  reportTimer = setTimeout(async () => {
    console.log('[VideoPlayerApp] 进入新切片:', segment.name);

    try {
      // 通知父组件处理业务逻辑
      emit('segmentchange', {
        tsFilename: segment.name,
        segmentIndex: segment.index,
        currentTime: segment.start,
        isSeek
      });

      lastReportedTs = segment.name;
    } catch (error) {
      console.error('[VideoPlayerApp] 上报切片失败:', error);
    }
  }, 500) as unknown as number;
};

// 播放控制方法
const togglePlay = () => {
  const videoContext = uni.createVideoContext(playerId.value);
  if (isPlaying.value) {
    videoContext.pause();
  } else {
    videoContext.play();
  }
};

const seekTo = (e: any) => {
  const rect = e.target.getBoundingClientRect();
  const percent = (e.detail.x - rect.left) / rect.width;
  const seekTime = percent * duration.value;

  const videoContext = uni.createVideoContext(playerId.value);
  videoContext.seek(seekTime);
};

const toggleFullscreen = () => {
  const videoContext = uni.createVideoContext(playerId.value);
  if (isFullscreen.value) {
    // 退出全屏：恢复竖屏
    videoContext.exitFullScreen();
    // 🔧 全屏方向锁定：退出全屏时恢复竖屏
    try {
      // #ifdef APP-PLUS
      plus.screen.lockOrientation('portrait-primary');
      // #endif
    } catch (error) {
      console.warn('[VideoPlayerApp] 恢复竖屏失败:', error);
    }
  } else {
    // 进入全屏：锁定横屏
    videoContext.requestFullScreen();
    // 🔧 全屏方向锁定：进入全屏时强制横屏，提升观看体验
    try {
      // #ifdef APP-PLUS
      plus.screen.lockOrientation('landscape-primary');
      // #endif
    } catch (error) {
      console.warn('[VideoPlayerApp] 锁定横屏失败:', error);
    }
  }
};

const retry = () => {
  error.value = '';
  isLoading.value = true;

  // 重新加载视频
  const videoContext = uni.createVideoContext(playerId.value);
  videoContext.play();
};

// 显示控制栏（带自动隐藏）
const showControlsWithTimeout = () => {
  showControls.value = true;
  clearControlsTimer();

  controlsTimer.value = setTimeout(() => {
    showControls.value = false;
  }, 3000) as unknown as number;
};

// 事件处理
const onPlay = () => {
  isPlaying.value = true;
  isLoading.value = false;
  error.value = '';

  // 屏幕常亮
  uni.setKeepScreenOn({ keepScreenOn: true });

  emit('play');
};

const onPause = () => {
  isPlaying.value = false;
  emit('pause');
};

const onEnded = () => {
  isPlaying.value = false;
  uni.setKeepScreenOn({ keepScreenOn: false });
  emit('ended');
};

const onTimeUpdate = (e: any) => {
  currentTime.value = e.detail?.currentTime || 0;
  duration.value = e.detail?.duration || 0;

  // TS切片检测
  if (parser) {
    const segment = parser.check(currentTime.value);
    if (segment) {
      reportSegment(segment);
    }
  }

  emit('timeupdate', e.detail);
};

const onSeeked = (e: any) => {
  const seekTime = e.detail?.currentTime || 0;
  console.log('[VideoPlayerApp] 用户拖动到:', seekTime);

  // 用户拖动后立即检测切片
  if (parser) {
    const segment = parser.check(seekTime);
    if (segment) {
      reportSegment(segment, true); // 标记为seek操作
    }
  }
};

const onWaiting = () => {
  isLoading.value = true;
};

// 🔧 加载状态优化：视频开始播放时关闭loading状态
const onPlaying = () => {
  isLoading.value = false;
  emit('playing');
};

const onError = (e: any) => {
  isLoading.value = false;
  const errorMsg = e.detail?.errMsg || '播放失败';
  error.value = errorMsg;
  emit('error', errorMsg);
};

const onFullscreenChange = (e: any) => {
  isFullscreen.value = e.detail?.fullScreen || false;
};

// 工具方法
const formatViewerCount = (count: number): string => {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`;
  } else if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`;
  }
  return count.toString();
};

// 暴露方法给父组件
defineExpose({
  play: () => {
    const videoContext = uni.createVideoContext(playerId.value);
    videoContext.play();
  },
  pause: () => {
    const videoContext = uni.createVideoContext(playerId.value);
    videoContext.pause();
  },
  seek: (time: number) => {
    const videoContext = uni.createVideoContext(playerId.value);
    videoContext.seek(time);
  }
});
</script>

<style lang="scss" scoped>
.video-player-app {
  position: relative;
  width: 100%;
  background: #000;

  video {
    width: 100%;
    height: 100%;
    min-height: 200px;
  }
}

/* 播放控制覆盖层 */
.player-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 20rpx;

  .control-bar {
    display: flex;
    align-items: center;
    gap: 20rpx;

    .control-btn {
      width: 80rpx;
      height: 80rpx;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;

      .iconfont {
        font-size: 32rpx;
        color: #fff;
      }
    }

    .progress-bar {
      flex: 1;
      height: 6rpx;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 3rpx;
      position: relative;

      .progress-fill {
        height: 100%;
        background: #509CEC;
        border-radius: 3rpx;
        transition: width 0.2s;
      }
    }
  }
}

/* 加载状态 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;

  .loading-spinner {
    width: 60rpx;
    height: 60rpx;
    border: 4rpx solid rgba(255, 255, 255, 0.3);
    border-top: 4rpx solid #509CEC;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 20rpx;
  }
}

/* 错误状态 */
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  padding: 40rpx;

  .error-message {
    text-align: center;
    margin-bottom: 40rpx;
    font-size: 28rpx;
  }

  .retry-btn {
    padding: 20rpx 40rpx;
    background: #509CEC;
    color: #fff;
    border: none;
    border-radius: 8rpx;
    font-size: 28rpx;
  }
}

/* 观看人数显示 */
.viewer-count-overlay {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  background: rgba(0, 0, 0, 0.6);
  padding: 12rpx 20rpx;
  border-radius: 20rpx;

  .viewer-count {
    font-size: 24rpx;
    color: #fff;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
```

### 步骤3：生成LiveView主页面

**📁 文件：`src/pages/app/live/LiveView.vue`**

**⚠️ 重要**：使用vue格式，通过CSS层级优化解决video组件显示问题

```vue
<template>
  <!-- 🔧 Vue标准布局：顶部视频固定，底部内容区域使用scroll-view滚动 -->
  <view class="live-view-page">

    <!-- 顶部信息栏 -->
    <view class="info-section">
      <view class="info-header">
        <view class="title-section">
          <view class="title-row">
            <text class="live-title" :class="{ 'expanded': titleExpanded }">
              {{ sessionInfo?.title || '直播标题' }}
            </text>
            <view v-if="!titleExpanded && isTitleLong" class="expand-btn" @tap="toggleTitle">
              <text>展开 ▼</text>
            </view>
          </view>

          <view class="status-section">
            <view class="status-badge" :class="statusClass">
              <text>{{ statusText }}</text>
            </view>
            <text v-if="viewerCount > 0" class="viewer-count">
              👁️ {{ formatViewerCount(viewerCount) }}人在看
            </text>
            <text class="live-time">
              {{ formatTime(sessionInfo?.start_time) }}
            </text>
          </view>
        </view>

        <view class="host-section">
          <image
            class="host-avatar"
            :src="sessionInfo?.expert?.avatar || '/static/default-avatar.png'"
            mode="aspectFill"
          />
          <view class="host-info">
            <text class="host-name">
              {{ sessionInfo?.expert?.name || '专家' }}
              {{ sessionInfo?.expert?.title || '' }}
            </text>
            <text class="host-hospital">
              {{ sessionInfo?.expert?.hospital || '' }}
              {{ sessionInfo?.expert?.department || '' }}
            </text>
          </view>
          <button
            class="follow-btn"
            :class="{ followed: isFollowed }"
            @tap="toggleFollow"
          >
            <text>{{ isFollowed ? '已关注' : '+ 关注' }}</text>
          </button>
        </view>

        <view class="action-section">
          <button class="action-btn" @tap="toggleFavorite">
            <text class="iconfont icon-star"></text>
            <text>{{ isFavorited ? '已收藏' : '收藏' }}</text>
          </button>
          <button class="action-btn" @tap="shareContent">
            <text class="iconfont icon-share"></text>
            <text>分享</text>
          </button>
          <button class="action-btn" @tap="downloadMaterials">
            <text class="iconfont icon-download"></text>
            <text>资料</text>
          </button>
        </view>
      </view>
    </view>

    <!-- 播放器区域 -->
    <view class="player-section">
      <VideoPlayerApp
        ref="playerRef"
        :src="playerSourceUrl"
        :poster="sessionInfo?.cover_url"
        :autoplay="true"
        :show-viewer-count="true"
        :viewer-count="viewerCount"
        @segmentchange="handleSegmentChange"
        @play="handlePlay"
        @pause="handlePause"
        @error="handlePlaybackError"
      />

      <!-- 流量提醒弹窗 -->
      <view v-if="showTrafficWarning" class="traffic-warning-modal">
        <view class="modal-content">
          <text class="warning-icon">⚠️</text>
          <text class="warning-title">流量提醒</text>
          <text class="warning-message">
            您当前使用的是{{ networkType }}网络，
            观看直播可能消耗较多流量（约500MB/小时）
          </text>
          <view class="modal-actions">
            <button @tap="cancelPlayback">取消</button>
            <button @tap="continuePlayback">继续观看</button>
          </view>
        </view>
      </view>
    </view>

    <!-- Sticky Tabs -->
    <view class="sticky-tabs" :class="{ 'stuck': tabsStuck }">
      <view class="tabs-container">
        <view
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>
    </view>

    <!-- Tab内容区域 -->
    <view class="content-section">
      <scroll-view class="content-scroll" scroll-y>
        <!-- 详情Tab -->
        <view v-if="activeTab === 'details'" class="details-content">
          <view class="content-block">
            <text class="block-title">直播介绍</text>
            <text class="block-content">
              {{ sessionInfo?.summary || sessionInfo?.description || '暂无介绍' }}
            </text>
          </view>

          <view v-if="sessionInfo?.tags && sessionInfo.tags.length > 0" class="content-block">
            <text class="block-title">标签</text>
            <view class="tags-list">
              <text
                v-for="tag in sessionInfo.tags"
                :key="tag.id"
                class="tag-item"
              >
                #{{ tag.name }}
              </text>
            </view>
          </view>

          <view v-if="materials && materials.length > 0" class="content-block">
            <text class="block-title">相关资料</text>
            <view class="materials-list">
              <view
                v-for="material in materials"
                :key="material.id"
                class="material-item"
                @tap="downloadMaterial(material)"
              >
                <text class="iconfont icon-file"></text>
                <text class="material-name">{{ material.name }}</text>
                <text class="material-size">{{ formatFileSize(material.size) }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 其他Tab内容保持不变 -->
        <!-- 聊天Tab -->
        <view v-if="activeTab === 'chat'" class="chat-content">
          <view class="chat-messages">
            <view
              v-for="message in chatMessages"
              :key="message.id"
              class="message-item"
            >
              <image class="message-avatar" :src="message.user.avatar" mode="aspectFill" />
              <view class="message-content">
                <text class="message-user">{{ message.user.name }}</text>
                <text class="message-text">{{ message.content }}</text>
                <text class="message-time">{{ formatTime(message.timestamp) }}</text>
              </view>
            </view>
          </view>

          <!-- 演示模式提示 -->
          <view class="demo-notice">
            <text>💡 演示模式：消息仅本地显示</text>
          </view>

          <view class="chat-input">
            <input
              v-model="chatInput"
              placeholder="请输入消息..."
              @confirm="sendMessage"
            />
            <button @tap="sendMessage">发送</button>
          </view>
        </view>

        <!-- 问答Tab -->
        <view v-if="activeTab === 'qa'" class="qa-content">
          <view class="qa-header">
            <button class="ask-btn" @tap="showAskDialog">
              <text class="iconfont icon-add"></text>
              <text>我要提问</text>
            </button>

            <!-- 演示模式提示 -->
            <view class="demo-notice">
              <text>💡 演示模式：问题提交后专家不会收到通知</text>
            </view>
          </view>

          <view class="qa-list">
            <view
              v-for="question in questions"
              :key="question.id"
              class="question-item"
            >
              <view class="question-content">
                <text class="question-text">{{ question.content }}</text>
                <view class="question-meta">
                  <text class="question-user">{{ question.user.name }}</text>
                  <text class="question-time">{{ formatTime(question.timestamp) }}</text>
                </view>
              </view>

              <view v-if="question.answer" class="answer-content">
                <text class="answer-text">{{ question.answer.content }}</text>
                <view class="answer-meta">
                  <text class="answer-user">{{ question.answer.expert.name }}</text>
                  <text class="answer-time">{{ formatTime(question.answer.timestamp) }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <!-- 推荐Tab -->
        <view v-if="activeTab === 'related'" class="related-content">
          <view class="related-sessions">
            <view
              v-for="session in relatedSessions"
              :key="session.id"
              class="session-card"
              @tap="goToSession(session)"
            >
              <image class="session-cover" :src="session.cover_url" mode="aspectFill" />
              <view class="session-info">
                <text class="session-title">{{ session.title }}</text>
                <text class="session-expert">{{ session.expert?.name }}</text>
                <text class="session-time">{{ formatTime(session.start_time) }}</text>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

  </view>

  <!-- 废弃的view布局（请勿使用） -->
  <!-- <view class="live-view-page">
    <!-- 顶部信息栏 -->
    <view class="info-section">
      <view class="info-header">
        <view class="title-section">
          <view class="title-row">
            <text class="live-title" :class="{ 'expanded': titleExpanded }">
              {{ sessionInfo?.title || '直播标题' }}
            </text>
            <view v-if="!titleExpanded && isTitleLong" class="expand-btn" @tap="toggleTitle">
              <text>展开 ▼</text>
            </view>
          </view>

          <view class="status-section">
            <view class="status-badge" :class="statusClass">
              <text>{{ statusText }}</text>
            </view>
            <text v-if="viewerCount > 0" class="viewer-count">
              👁️ {{ formatViewerCount(viewerCount) }}人在看
            </text>
            <text class="live-time">
              {{ formatTime(sessionInfo?.start_time) }}
            </text>
          </view>
        </view>

        <view class="host-section">
          <image
            class="host-avatar"
            :src="sessionInfo?.expert?.avatar || '/static/default-avatar.png'"
            mode="aspectFill"
          />
          <view class="host-info">
            <text class="host-name">
              {{ sessionInfo?.expert?.name || '专家' }}
              {{ sessionInfo?.expert?.title || '' }}
            </text>
            <text class="host-hospital">
              {{ sessionInfo?.expert?.hospital || '' }}
              {{ sessionInfo?.expert?.department || '' }}
            </text>
          </view>
          <button
            class="follow-btn"
            :class="{ followed: isFollowed }"
            @tap="toggleFollow"
          >
            <text>{{ isFollowed ? '已关注' : '+ 关注' }}</text>
          </button>
        </view>

        <view class="action-section">
          <button class="action-btn" @tap="toggleFavorite">
            <text class="iconfont icon-star"></text>
            <text>{{ isFavorited ? '已收藏' : '收藏' }}</text>
          </button>
          <button class="action-btn" @tap="shareContent">
            <text class="iconfont icon-share"></text>
            <text>分享</text>
          </button>
          <button class="action-btn" @tap="downloadMaterials">
            <text class="iconfont icon-download"></text>
            <text>资料</text>
          </button>
        </view>
      </view>
    </view>

    <!-- 播放器区域 -->
    <view class="player-section">
      <VideoPlayerApp
        ref="playerRef"
        :src="playerSourceUrl"
        :poster="sessionInfo?.cover_url"
        :autoplay="true"
        :show-viewer-count="true"
        :viewer-count="viewerCount"
        @segmentchange="handleSegmentChange"
        @play="handlePlay"
        @pause="handlePause"
        @error="handlePlaybackError"
      />

      <!-- 流量提醒弹窗 -->
      <view v-if="showTrafficWarning" class="traffic-warning-modal">
        <view class="modal-content">
          <text class="warning-icon">⚠️</text>
          <text class="warning-title">流量提醒</text>
          <text class="warning-message">
            您当前使用的是{{ networkType }}网络，
            观看直播可能消耗较多流量（约500MB/小时）
          </text>
          <view class="modal-actions">
            <button @tap="cancelPlayback">取消</button>
            <button @tap="continuePlayback">继续观看</button>
          </view>
        </view>
      </view>
    </view>

    <!-- Sticky Tabs -->
    <view class="sticky-tabs" :class="{ 'stuck': tabsStuck }">
      <scroll-view scroll-x class="tabs-container">
        <view
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </scroll-view>
    </view>

    <!-- Tab内容区 -->
    <view class="content-section">
      <scroll-view scroll-y class="content-scroll">
        <!-- 详情Tab -->
        <view v-if="activeTab === 'details'" class="details-content">
          <view class="content-block">
            <text class="block-title">直播介绍</text>
            <text class="block-content">
              {{ sessionInfo?.summary || sessionInfo?.description || '暂无介绍' }}
            </text>
          </view>

          <view v-if="sessionInfo?.tags && sessionInfo.tags.length > 0" class="content-block">
            <text class="block-title">标签</text>
            <view class="tags-list">
              <text
                v-for="tag in sessionInfo.tags"
                :key="tag.id"
                class="tag-item"
              >
                #{{ tag.name }}
              </text>
            </view>
          </view>

          <view v-if="materials && materials.length > 0" class="content-block">
            <text class="block-title">相关资料</text>
            <view class="materials-list">
              <view
                v-for="material in materials"
                :key="material.id"
                class="material-item"
                @tap="downloadMaterial(material)"
              >
                <text class="iconfont icon-file"></text>
                <text class="material-name">{{ material.name }}</text>
                <text class="material-size">{{ formatFileSize(material.size) }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 聊天Tab -->
        <view v-if="activeTab === 'chat'" class="chat-content">
          <view class="chat-messages">
            <view
              v-for="message in chatMessages"
              :key="message.id"
              class="message-item"
            >
              <image class="message-avatar" :src="message.user.avatar" mode="aspectFill" />
              <view class="message-content">
                <text class="message-user">{{ message.user.name }}</text>
                <text class="message-text">{{ message.content }}</text>
                <text class="message-time">{{ formatTime(message.timestamp) }}</text>
              </view>
            </view>
          </view>

          <!-- 演示模式提示 -->
          <view class="demo-notice">
            <text>💡 演示模式：消息仅本地显示</text>
          </view>

          <view class="chat-input">
            <input
              v-model="chatInput"
              placeholder="请输入消息..."
              @confirm="sendMessage"
            />
            <button @tap="sendMessage">发送</button>
          </view>
        </view>

        <!-- 问答Tab -->
        <view v-if="activeTab === 'qa'" class="qa-content">
          <view class="qa-header">
            <button class="ask-btn" @tap="showAskDialog">
              <text class="iconfont icon-add"></text>
              <text>我要提问</text>
            </button>

            <!-- 演示模式提示 -->
            <view class="demo-notice">
              <text>💡 演示模式：问题提交后专家不会收到通知</text>
            </view>
          </view>

          <view class="qa-list">
            <view
              v-for="question in questions"
              :key="question.id"
              class="question-item"
            >
              <view class="question-content">
                <text class="question-text">{{ question.content }}</text>
                <view class="question-meta">
                  <text class="question-user">{{ question.user.name }}</text>
                  <text class="question-time">{{ formatTime(question.timestamp) }}</text>
                </view>
              </view>

              <view v-if="question.answer" class="answer-content">
                <text class="answer-text">{{ question.answer.content }}</text>
                <view class="answer-meta">
                  <text class="answer-user">{{ question.answer.expert.name }}</text>
                  <text class="answer-time">{{ formatTime(question.answer.timestamp) }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <!-- 推荐Tab -->
        <view v-if="activeTab === 'related'" class="related-content">
          <view class="related-sessions">
            <view
              v-for="session in relatedSessions"
              :key="session.id"
              class="session-card"
              @tap="goToSession(session)"
            >
              <image class="session-cover" :src="session.cover_url" mode="aspectFill" />
              <view class="session-info">
                <text class="session-title">{{ session.title }}</text>
                <text class="session-expert">{{ session.expert?.name }}</text>
                <text class="session-time">{{ formatTime(session.start_time) }}</text>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import VideoPlayerApp from '@/components/app/VideoPlayerApp.vue';
import { useAuthStore } from '@/store/auth';
import { usePlayerStore } from '@/store/player';
import { getSessionDetail, getSessionList } from '@/api/session';
import { getRoomDetail } from '@/api/room';
import { recordWatch } from '@/api/watchHistory';
import { getRealtimeViewers } from '@/api/playback';
import { ENV_CONFIG } from '@/config/env';
import { mockViewerCount, mockSessionData, mockChatMessages, mockQuestions, mockRelatedSessions, mockMaterials } from './mock-data';

// 路由参数
const sessionId = ref('');
const roomId = ref('');

// Store
const authStore = useAuthStore();
const playerStore = usePlayerStore();

// 响应式数据
const sessionInfo = ref<any>(null);
const viewerCount = ref(0);
const isLoading = ref(true);
const error = ref('');

// 播放器相关
const playerRef = ref<any>(null);
const playerSourceUrl = ref('');

// UI状态
const titleExpanded = ref(false);
const tabsStuck = ref(false);
const activeTab = ref('details');
const isFollowed = ref(false);
const isFavorited = ref(false);

// 网络状态
const networkType = ref('wifi');
const showTrafficWarning = ref(false);

// Tab数据
const chatMessages = ref<any[]>([]);
const questions = ref<any[]>([]);
const relatedSessions = ref<any[]>([]);
const materials = ref<any[]>([]);
const chatInput = ref('');

// 定时器
let viewerCountTimer: number | null = null;

// 计算属性
const isAuthenticated = computed(() => authStore.isAuthenticated);
const statusText = computed(() => {
  const status = sessionInfo.value?.status;
  switch (status) {
    case 'live': return '🔴 直播中';
    case 'scheduled': return '⏰ 预告';
    case 'ended': return '📺 回放';
    default: return '未知状态';
  }
});
const statusClass = computed(() => {
  const status = sessionInfo.value?.status;
  switch (status) {
    case 'live': return 'status-live';
    case 'scheduled': return 'status-scheduled';
    case 'ended': return 'status-ended';
    default: return 'status-unknown';
  }
});
const isTitleLong = computed(() => {
  const title = sessionInfo.value?.title || '';
  return title.length > 20; // 简单判断
});

const tabs = [
  { key: 'details', label: '详情' },
  { key: 'chat', label: '聊天' },
  { key: 'qa', label: '问答' },
  { key: 'related', label: '推荐' }
];

// 页面加载
onLoad((options: any) => {
  sessionId.value = options.sessionId || '';
  roomId.value = options.roomId || '';
});

onMounted(async () => {
  await loadSessionData();
  initNetworkListener();
  startViewerCountTimer();
});

onShow(async () => {
  // 页面显示时刷新数据
  await loadSessionData();
});

onBeforeUnmount(() => {
  clearViewerCountTimer();
});

// 数据加载
async function loadSessionData() {
  // 如果没有 sessionId，尝试通过 roomId 获取
  if (!sessionId.value && roomId.value) {
    try {
      isLoading.value = true;
      
      // 获取房间详情，查找当前场次ID
      const roomResponse = await getRoomDetail(roomId.value);
      const room = (roomResponse as any).data || roomResponse;
      
      if (room.current_session_id) {
        // 如果房间有当前场次，使用该场次ID
        sessionId.value = room.current_session_id;
      } else {
        // 如果没有当前场次，尝试获取房间的第一个场次（按优先级：live > scheduled > ended）
        const sessionsResponse = await getSessionList(roomId.value, { page: 1, size: 1 });
        const sessions = (sessionsResponse as any).data?.items || (sessionsResponse as any).items || [];
        
        if (sessions.length > 0) {
          sessionId.value = sessions[0].id;
        } else {
          error.value = '该房间暂无可用场次';
          isLoading.value = false;
          return;
        }
      }
    } catch (err) {
      console.error('获取房间信息失败:', err);
      error.value = '加载房间信息失败，请重试';
      isLoading.value = false;
      return;
    }
  }

  if (!sessionId.value) {
    error.value = '缺少场次ID或房间ID';
    return;
  }

  try {
    isLoading.value = true;

    if (ENV_CONFIG.VITE_USE_MOCK) {
      sessionInfo.value = mockSessionData;
      chatMessages.value = mockChatMessages;
      questions.value = mockQuestions;
      relatedSessions.value = mockRelatedSessions;
      materials.value = mockMaterials;
    } else {
      const response = await getSessionDetail(sessionId.value);
      // API 返回可能是 ApiResponse<Session> 或直接是 Session
      sessionInfo.value = (response as any).data || response;
      // TODO: 加载聊天、问答、推荐数据
    }

    // 设置播放地址
    setupPlayerSource();

    // 加载观看人数
    await loadViewerCount();

    isLoading.value = false;
  } catch (err) {
    console.error('加载场次数据失败:', err);
    error.value = '加载失败，请重试';
    isLoading.value = false;
  }
}

function setupPlayerSource() {
  const session = sessionInfo.value;
  if (!session) return;

  // 播放地址获取策略
  if (session.status === 'live') {
    // 直播：优先使用专门API，失败时降级使用playback_url
    playerSourceUrl.value = session.live_url || session.playback_url;
  } else {
    // 回放：直接使用playback_url
    playerSourceUrl.value = session.playback_url;
  }
}

// 网络监听
function initNetworkListener() {
  uni.getNetworkType({
    success: (res) => {
      networkType.value = res.networkType;
    }
  });

  uni.onNetworkStatusChange((res) => {
    networkType.value = res.networkType;

    // 流量提醒逻辑
    if (res.networkType !== 'wifi' && res.isConnected) {
      const noPrompt = uni.getStorageSync('settings_traffic_reminder');
      if (noPrompt !== false) {
        showTrafficWarning.value = true;
      }
    }
  });
}

// 观看人数定时更新
function startViewerCountTimer() {
  // 立即加载一次
  loadViewerCount();

  // 每30秒更新一次
  viewerCountTimer = setInterval(loadViewerCount, 30000) as unknown as number;
}

function clearViewerCountTimer() {
  if (viewerCountTimer) {
    clearInterval(viewerCountTimer);
    viewerCountTimer = null;
  }
}

async function loadViewerCount() {
  if (!sessionId.value) return;

  try {
    if (ENV_CONFIG.VITE_USE_MOCK) {
      viewerCount.value = mockViewerCount.count;
    } else {
      const res = await getRealtimeViewers(sessionId.value);
      viewerCount.value = res.data?.count || 0;
    }
  } catch (err) {
    console.error('获取观看人数失败:', err);
    // 失败时不更新，保持原有数据
  }
}

// 事件处理
function handleSegmentChange(data: any) {
  // 上报观看历史
  if (isAuthenticated.value && sessionId.value) {
    recordWatch(sessionId.value, {
      progress: Math.floor(data.currentTime),
      extra: {
        ts_filename: data.tsFilename,
        segment_index: data.segmentIndex,
        is_seek: data.isSeek || false,
        device: uni.getSystemInfoSync().model,
        platform: 'app'
      }
    }).catch(err => {
      console.error('上报观看历史失败:', err);
    });
  }
}

function handlePlay() {
  playerStore.setPlayingState(true);
  console.log('播放开始');
}

function handlePause() {
  playerStore.setPlayingState(false);
  console.log('播放暂停');
}

function handlePlaybackError(errorMsg: string) {
  uni.showToast({
    title: '播放失败：' + errorMsg,
    icon: 'none',
    duration: 3000
  });
}

function toggleTitle() {
  titleExpanded.value = !titleExpanded.value;
}

function switchTab(tabKey: string) {
  activeTab.value = tabKey;
}

function toggleFollow() {
  if (!isAuthenticated.value) {
    authStore.forceReauth('/pages/app/live/LiveView');
    return;
  }

  isFollowed.value = !isFollowed.value;
  uni.showToast({
    title: isFollowed.value ? '已关注' : '已取消关注',
    icon: 'none'
  });
}

function toggleFavorite() {
  if (!isAuthenticated.value) {
    authStore.forceReauth('/pages/app/live/LiveView');
    return;
  }

  isFavorited.value = !isFavorited.value;
  uni.showToast({
    title: isFavorited.value ? '已收藏' : '已取消收藏',
    icon: 'none'
  });
}

function shareContent() {
  uni.showShareMenu();
}

function downloadMaterials() {
  uni.showToast({
    title: '资料下载功能开发中',
    icon: 'none'
  });
}

function cancelPlayback() {
  showTrafficWarning.value = false;
  if (playerRef.value) {
    playerRef.value.pause();
  }
}

function continuePlayback() {
  showTrafficWarning.value = false;
  if (playerRef.value) {
    playerRef.value.play();
  }
}

// 🎯 演示模式：本地模拟问答交互
function showAskDialog() {
  uni.showModal({
    title: '我要提问',
    editable: true, // 允许输入
    placeholderText: '请输入您的问题...',
    success: (res) => {
      if (res.confirm && res.content?.trim()) {
        // 本地模拟添加问题（演示模式）
        const newQuestion = {
          id: `q-${Date.now()}`,
          user: { id: 'current-user', name: '我' },
          content: res.content,
          timestamp: new Date().toISOString(),
          status: 'pending' // 待回答状态
        };

        // 添加到问题列表顶部
        questions.value.unshift(newQuestion);

        uni.showToast({
          title: '问题已提交，专家会尽快回答',
          icon: 'success'
        });
      }
    }
  });
}

// 🎯 演示模式：本地模拟聊天交互
function sendMessage() {
  if (!chatInput.value.trim()) return;

  // 本地模拟发送成功（演示模式）
  const newMsg = {
    id: `msg-${Date.now()}`,
    user: {
      id: 'current-user',
      name: '我',
      avatar: '/static/default-avatar.png'
    },
    content: chatInput.value,
    timestamp: new Date().toISOString()
  };

  // 本地追加消息
  chatMessages.value.push(newMsg);
  chatInput.value = '';

  // 模拟滚动到底部（演示模式）
  nextTick(() => {
    // 这里可以添加滚动到底部的逻辑
    console.log('消息已发送（演示模式）');
  });
}

function handlePlay() {
  playerStore.setPlayingState(true);
  console.log('播放开始');
}

function handlePause() {
  playerStore.setPlayingState(false);
  console.log('播放暂停');
}

function goToSession(session: any) {
  uni.navigateTo({
    url: `/pages/app/live/LiveView?sessionId=${session.id}`
  });
}

function downloadMaterial(material: any) {
  uni.showToast({
    title: '下载功能开发中',
    icon: 'none'
  });
}

// 工具函数
function formatViewerCount(count: number): string {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`;
  } else if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`;
  }
  return count.toString();
}

function formatTime(timeStr: string): string {
  if (!timeStr) return '';

  try {
    // 清洗时间字符串（去微秒，规范化Z）
    const cleaned = timeStr.replace(/\.\d{6}/, '').replace(/\+00:00$/, 'Z');
    const date = new Date(cleaned);

    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const diffDays = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      // 今天
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } else if (diffDays === 1) {
      // 昨天
      return `昨天 ${date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })}`;
    } else {
      // 其他日期
      return date.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  } catch (err) {
    console.error('时间格式化失败:', err);
    return timeStr;
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
</script>

<style lang="scss" scoped>
/* ✅ Vue样式规范：支持scoped和完整CSS选择器 */
.live-view-page {
  flex: 1;
  background-color: #f5f5f5;
}

/* 顶部信息栏 */
.info-section {
  background-color: #ffffff;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.info-header {
  .title-section {
    margin-bottom: 24rpx;

    .title-row {
      display: flex;
      align-items: center;
      margin-bottom: 16rpx;

      .live-title {
        flex: 1;
        font-size: 36rpx;
        font-weight: 600;
        color: #333333;
        line-height: 1.4;

        &.expanded {
          display: block;
          white-space: normal;
        }

        &:not(.expanded) {
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          overflow: hidden;
        }
      }

      .expand-btn {
        margin-left: 16rpx;
        padding: 8rpx 16rpx;
        background-color: #f0f0f0;
        border-radius: 12rpx;
        font-size: 24rpx;
        color: #666666;
      }
    }

    .status-section {
      display: flex;
      align-items: center;
      gap: 16rpx;

      .status-badge {
        padding: 6rpx 16rpx;
        border-radius: 12rpx;
        font-size: 24rpx;

        &.status-live {
          background-color: #ff4d4f;
          color: #ffffff;
        }

        &.status-scheduled {
          background-color: #ffa500;
          color: #ffffff;
        }

        &.status-ended {
          background-color: #666666;
          color: #ffffff;
        }
      }

      .viewer-count, .live-time {
        font-size: 26rpx;
        color: #999999;
      }
    }
  }

  .host-section {
    display: flex;
    align-items: center;
    margin-bottom: 24rpx;

    .host-avatar {
      width: 120rpx;
      height: 120rpx;
      border-radius: 60rpx;
      margin-right: 24rpx;
    }

    .host-info {
      flex: 1;

      .host-name {
        display: block;
        font-size: 32rpx;
        font-weight: 600;
        color: #333333;
        margin-bottom: 8rpx;
      }

      .host-hospital {
        font-size: 26rpx;
        color: #666666;
      }
    }

    .follow-btn {
      padding: 16rpx 24rpx;
      border-radius: 20rpx;
      border: 2rpx solid #509cec;
      background-color: #ffffff;
      font-size: 26rpx;
      color: #509cec;

      &.followed {
        background-color: #509cec;
        color: #ffffff;
      }
    }
  }

  .action-section {
    display: flex;
    gap: 32rpx;

    .action-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16rpx;
      background-color: transparent;
      border: none;
      font-size: 24rpx;
      color: #666666;

      .iconfont {
        font-size: 40rpx;
        margin-bottom: 8rpx;
      }
    }
  }
}

/* 播放器区域 */
.player-section {
  position: relative;
  width: 100%;
  background-color: #000000;
  margin-bottom: 24rpx;

  :deep(.video-player-app) {
    width: 100%;
    height: 56.25vw; // 16:9比例
    max-height: 60vh;
  }
}

/* 流量提醒弹窗 */
.traffic-warning-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;

  .modal-content {
    background-color: #ffffff;
    border-radius: 16rpx;
    padding: 48rpx;
    margin: 32rpx;
    max-width: 600rpx;
    text-align: center;

    .warning-icon {
      font-size: 80rpx;
      margin-bottom: 24rpx;
    }

    .warning-title {
      display: block;
      font-size: 36rpx;
      font-weight: 600;
      color: #333333;
      margin-bottom: 16rpx;
    }

    .warning-message {
      display: block;
      font-size: 28rpx;
      color: #666666;
      line-height: 1.5;
      margin-bottom: 40rpx;
    }

    .modal-actions {
      display: flex;
      gap: 24rpx;

      button {
        flex: 1;
        padding: 24rpx;
        border-radius: 8rpx;
        border: none;
        font-size: 32rpx;

        &:first-child {
          background-color: #f0f0f0;
          color: #666666;
        }

        &:last-child {
          background-color: #509cec;
          color: #ffffff;
        }
      }
    }
  }
}

/* Sticky Tabs */
.sticky-tabs {
  position: sticky;
  top: 0;
  background-color: #ffffff;
  z-index: 100;
  border-bottom: 1rpx solid #e5e5e5;

  &.stuck {
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  }

  .tabs-container {
    height: 88rpx;
    white-space: nowrap;

    .tab-item {
      display: inline-block;
      padding: 0 32rpx;
      height: 88rpx;
      line-height: 88rpx;
      font-size: 30rpx;
      color: #666666;
      position: relative;

      &.active {
        color: #509cec;
        font-weight: 600;

        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 60rpx;
          height: 6rpx;
          background-color: #509cec;
          border-radius: 3rpx;
        }
      }
    }
  }
}

/* Tab内容区 */
.content-section {
  background-color: #ffffff;
  min-height: calc(100vh - 400rpx);

  .content-scroll {
    min-height: calc(100vh - 400rpx);
  }
}

/* 详情Tab */
.details-content {
  .content-block {
    padding: 32rpx;
    border-bottom: 1rpx solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .block-title {
      display: block;
      font-size: 32rpx;
      font-weight: 600;
      color: #333333;
      margin-bottom: 16rpx;
    }

    .block-content {
      font-size: 28rpx;
      color: #666666;
      line-height: 1.6;
    }

    .tags-list {
      display: flex;
      flex-wrap: wrap;
      gap: 16rpx;

      .tag-item {
        padding: 8rpx 16rpx;
        background-color: #f0f0f0;
        border-radius: 12rpx;
        font-size: 24rpx;
        color: #666666;
      }
    }

    .materials-list {
      .material-item {
        display: flex;
        align-items: center;
        padding: 24rpx 0;
        border-bottom: 1rpx solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .iconfont {
          font-size: 40rpx;
          color: #509cec;
          margin-right: 16rpx;
        }

        .material-name {
          flex: 1;
          font-size: 28rpx;
          color: #333333;
        }

        .material-size {
          font-size: 24rpx;
          color: #999999;
        }
      }
    }
  }
}

/* 聊天Tab */
.chat-content {
  .chat-messages {
    padding: 0 32rpx;
    max-height: 60vh;
    overflow-y: auto;

    .message-item {
      display: flex;
      padding: 24rpx 0;
      border-bottom: 1rpx solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .message-avatar {
        width: 80rpx;
        height: 80rpx;
        border-radius: 40rpx;
        margin-right: 16rpx;
        flex-shrink: 0;
      }

      .message-content {
        flex: 1;

        .message-user {
          display: block;
          font-size: 28rpx;
          font-weight: 600;
          color: #333333;
          margin-bottom: 8rpx;
        }

        .message-text {
          display: block;
          font-size: 26rpx;
          color: #666666;
          line-height: 1.4;
          margin-bottom: 8rpx;
        }

        .message-time {
          font-size: 24rpx;
          color: #999999;
        }
      }
    }
  }

  /* 演示模式提示样式（全局可用） */
  .demo-notice {
    padding: 16rpx 32rpx;
    background-color: #f0f8ff;
    border-left: 4rpx solid #509cec;
    margin: 0 32rpx 16rpx 32rpx;
    border-radius: 8rpx;

    text {
      font-size: 24rpx;
      color: #509cec;
      line-height: 1.4;
    }
  }

  .chat-input {
    display: flex;
    padding: 24rpx 32rpx;
    /* 🔧 Vue全面屏适配：适配iPhone X等底部安全区 */
    padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
    padding-bottom: calc(24rpx + constant(safe-area-inset-bottom));
    border-top: 1rpx solid #f0f0f0;
    background-color: #fafafa;

    input {
      flex: 1;
      padding: 16rpx 24rpx;
      border: 1rpx solid #e5e5e5;
      border-radius: 20rpx;
      margin-right: 16rpx;
      font-size: 28rpx;
    }

    button {
      padding: 16rpx 32rpx;
      background-color: #509cec;
      color: #ffffff;
      border: none;
      border-radius: 20rpx;
      font-size: 28rpx;
      /* 🔧 Vue底部安全区适配 */
      margin-bottom: env(safe-area-inset-bottom);
      margin-bottom: constant(safe-area-inset-bottom);
    }
  }
}

/* 问答Tab */
.qa-content {
  .qa-header {
    padding: 32rpx;
    border-bottom: 1rpx solid #f0f0f0;

    .ask-btn {
      width: 100%;
      padding: 24rpx;
      background-color: #509cec;
      color: #ffffff;
      border: none;
      border-radius: 12rpx;
      font-size: 32rpx;
      display: flex;
      align-items: center;
      justify-content: center;

      .iconfont {
        font-size: 32rpx;
        margin-right: 8rpx;
      }
    }
  }

  .qa-list {
    .question-item {
      padding: 32rpx;
      border-bottom: 1rpx solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .question-content, .answer-content {
        margin-bottom: 24rpx;

        &:last-child {
          margin-bottom: 0;
        }

        .question-text, .answer-text {
          display: block;
          font-size: 28rpx;
          color: #333333;
          line-height: 1.5;
          margin-bottom: 12rpx;
        }

        .question-meta, .answer-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .question-user, .answer-user, .question-time, .answer-time {
            font-size: 24rpx;
            color: #999999;
          }

          .answer-user {
            color: #509cec;
            font-weight: 600;
          }
        }
      }

      .answer-content {
        background-color: #f8f9fa;
        padding: 24rpx;
        border-radius: 8rpx;
        margin-left: 32rpx;
      }
    }
  }
}

/* 推荐Tab */
.related-content {
  .related-sessions {
    padding: 32rpx;

    .session-card {
      display: flex;
      padding: 24rpx 0;
      border-bottom: 1rpx solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .session-cover {
        width: 200rpx;
        height: 112rpx;
        border-radius: 8rpx;
        margin-right: 24rpx;
        flex-shrink: 0;
      }

      .session-info {
        flex: 1;

        .session-title {
          display: block;
          font-size: 30rpx;
          font-weight: 600;
          color: #333333;
          margin-bottom: 8rpx;
          line-height: 1.3;
        }

        .session-expert {
          display: block;
          font-size: 26rpx;
          color: #666666;
          margin-bottom: 4rpx;
        }

        .session-time {
          font-size: 24rpx;
          color: #999999;
        }
      }
    }
  }
}
</style>
```

### 步骤4：生成API和类型文件

**📁 文件：`src/api/playback.ts`**

```typescript
/**
 * 播放相关API
 * 包含观看人数获取、播放统计上报等功能
 */

import { request } from '@/utils/request';
import type { ApiResponse } from '@/types/common';

// 观看人数接口
export interface RealtimeViewers {
  count: number;
  timestamp: string;
}

// 播放错误接口
export interface PlaybackError {
  code: string;
  message: string;
  timestamp: number;
}

// 播放统计数据接口
export interface PlaybackStats {
  session_id: string;
  user_id: string;
  device: string;
  platform: 'app' | 'h5';
  start_time: number;      // 播放开始时间
  end_time: number;        // 播放结束时间
  total_duration: number;  // 总播放时长（秒）
  buffered_duration: number; // 缓冲时长（秒）
  stall_count: number;     // 卡顿次数
  stall_duration: number;  // 卡顿总时长（秒）
  quality_changes: number; // 清晰度切换次数
  final_quality: string;   // 最终播放清晰度
  errors: PlaybackError[]; // 播放错误列表
}

// 直播流地址接口
export interface StreamUrl {
  url: string;
  expires_at: string;
}

/**
 * 获取实时观看人数
 * @param sessionId 场次ID
 * @returns Promise<ApiResponse<RealtimeViewers>>
 */
export const getRealtimeViewers = (sessionId: string): Promise<ApiResponse<RealtimeViewers>> => {
  return request<ApiResponse<RealtimeViewers>>({
    url: `/sessions/${sessionId}/viewers`,
    method: 'GET'
  });
};

/**
 * 上报播放统计数据
 * @param stats 播放统计数据
 * @returns Promise<ApiResponse<void>>
 */
export const reportPlaybackStats = (stats: PlaybackStats): Promise<ApiResponse<void>> => {
  return request<ApiResponse<void>>({
    url: '/api/v1/playback/stats',
    method: 'POST',
    data: stats
  });
};

/**
 * 获取直播流地址
 * @param sessionId 场次ID
 * @returns Promise<ApiResponse<StreamUrl>>
 */
export const getLiveStreamUrl = (sessionId: string): Promise<ApiResponse<StreamUrl>> => {
  return request<ApiResponse<StreamUrl>>({
    url: `/sessions/${sessionId}/stream-url`,
    method: 'GET'
  });
};
```

**📁 文件：`src/types/playback.ts`**

```typescript
/**
 * 播放相关类型定义
 */

export interface Segment {
  name: string;        // TS文件名
  url: string;         // 完整URL
  start: number;       // 开始时间（秒）
  end: number;         // 结束时间（秒）
  duration: number;    // 时长（秒）
  index: number;       // 索引
}

export interface PlaybackError {
  code: string;
  message: string;
  timestamp: number;
}

export interface PlaybackStats {
  session_id: string;
  user_id: string;
  device: string;
  platform: 'app' | 'h5';
  start_time: number;
  end_time: number;
  total_duration: number;
  buffered_duration: number;
  stall_count: number;
  stall_duration: number;
  quality_changes: number;
  final_quality: string;
  errors: PlaybackError[];
}

export interface RealtimeViewers {
  count: number;
  timestamp: string;
}

export interface StreamUrl {
  url: string;
  expires_at: string;
}
```

**📁 文件：`src/pages/app/live/mock-data.ts`**

```typescript
/**
 * LiveView页面Mock数据
 * 用于开发阶段，当 ENV_CONFIG.VITE_USE_MOCK = true 时使用
 *
 * 🎯 混合Mock策略：
 * - 主播放器：使用真实业务流，提前发现环境问题
 * - 推荐列表：使用差异化测试源，验证切换功能
 */

import type { RealtimeViewers } from '@/types/playback';

// 🎯 测试用m3u8链接配置（混合Mock策略）
// 优势：
// ✅ 主播放器用真实流：提前发现SSL/CORS/编码等问题
// ✅ 推荐列表用差异内容：一眼确认视频切换成功
// ✅ 符合实际业务场景：手术视频 + 相关推荐
// ✅ 演示价值高：专业医疗内容展示
export const TEST_M3U8_URLS = {
  // 1. 你的真实业务流（用于主播放器，测试真实环境）
  // 提前暴露服务器SSL、CORS、编码等实际问题
  real: 'https://mp2.dayilive.com/clip/2aa5b88f3d.m3u8',

  // 2. 差异化测试流（用于推荐列表，测试切换功能）
  // 使用动画片内容，一眼就能确认视频切换成功
  cartoon: 'https://multiplatform-f.akamaihd.net/i/multi/will/bunny/big_buck_bunny_,640x360_400,640x360_700,640x360_1000,950x540_1500,.f4v.csmil/master.m3u8',

  // 3. 备用测试流（Apple官方测试源）
  apple: 'https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8'
};

// 当前使用的测试链接配置（可根据需要切换）
const CURRENT_CONFIG = {
  primary: TEST_M3U8_URLS.real,      // 主场次用真实流
  secondary: TEST_M3U8_URLS.cartoon, // 推荐场次用差异化内容
  backup: TEST_M3U8_URLS.apple       // 备用测试源
};

// 观看人数Mock数据
export const mockViewerCount: RealtimeViewers = {
  count: 1234,
  timestamp: new Date().toISOString()
};

// 主场次Mock数据（使用真实业务流）
export const mockSessionData = {
  id: 'session-123',
  room_id: 'room-456',
  title: '肝胆胰外科微创手术的最新进展与病例讨论会——2025年秋季学术研讨会第三场',
  summary: '本次直播将邀请国内知名肝胆胰外科专家，围绕微创手术技术最新进展进行深入讨论...',
  status: 'live', // 'live' | 'scheduled' | 'ended'
  start_time: new Date().toISOString(),
  cover_url: '/static/mock-cover.jpg',
  playback_url: CURRENT_CONFIG.primary,  // 🔧 主场次使用真实URL
  expert: {
    id: 'expert-789',
    name: '张三',
    title: '教授',
    hospital: '北京协和医院',
    department: '肝胆外科',
    avatar: '/static/mock-avatar.jpg'
  },
  tags: [
    { id: 'tag-1', name: '微创手术' },
    { id: 'tag-2', name: '肝胆胰外科' },
    { id: 'tag-3', name: '病例讨论' }
  ]
};

// 聊天消息Mock数据
export const mockChatMessages = [
  {
    id: 'msg-1',
    user: {
      id: 'user-1',
      name: '李医生',
      avatar: '/static/mock-avatar-1.jpg'
    },
    content: '这个手术技术很不错！',
    timestamp: new Date(Date.now() - 300000).toISOString()
  },
  {
    id: 'msg-2',
    user: {
      id: 'user-2',
      name: '王护士',
      avatar: '/static/mock-avatar-2.jpg'
    },
    content: '请问术后恢复需要多久？',
    timestamp: new Date(Date.now() - 180000).toISOString()
  }
];

// 问答Mock数据
export const mockQuestions = [
  {
    id: 'q-1',
    user: {
      id: 'user-3',
      name: '赵医生'
    },
    content: '请问这种手术的成功率如何？',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    answer: {
      expert: {
        id: 'expert-789',
        name: '张三教授'
      },
      content: '根据我们的临床经验，这种手术的成功率在95%以上...',
      timestamp: new Date(Date.now() - 300000).toISOString()
    }
  }
];

// 相关推荐Mock数据（混合使用真实流和测试流）
export const mockRelatedSessions = [
  {
    id: 'session-124',
    title: '胃肠外科微创手术新技术分享',
    expert: {
      name: '李四教授'
    },
    start_time: new Date(Date.now() + 86400000).toISOString(),
    cover_url: '/static/mock-cover-2.jpg',
    playback_url: CURRENT_CONFIG.primary,  // 🔧 相关场次也可用真实URL测试
    status: 'live'
  },
  {
    id: 'session-125',
    title: '骨科关节置换手术案例分析',
    expert: {
      name: '王五主任'
    },
    start_time: new Date(Date.now() + 172800000).toISOString(),
    cover_url: '/static/mock-cover-3.jpg',
    playback_url: CURRENT_CONFIG.secondary,  // 🔧 用动画片区分切换效果
    status: 'ended'
  }
];

// 资料下载Mock数据
export const mockMaterials = [
  {
    id: 'material-1',
    name: '手术技术要点.pdf',
    size: 2048000, // 2MB
    url: '/static/materials/surgery-guide.pdf'
  },
  {
    id: 'material-2',
    name: '病例分析报告.pdf',
    size: 1536000, // 1.5MB
    url: '/static/materials/case-report.pdf'
  }
];
```

### 步骤5：更新路由配置和占位页

**📁 文件1：`src/pages.json`**

添加LiveView页面路由：

```json
{
  "path": "pages/app/live/LiveView",
  "style": {
    "navigationBarTitleText": "直播间",
    "navigationStyle": "custom"
  }
}
```

**📁 文件2：`src/pages/app/live/index.vue`（占位页自动重定向）**

占位页需要支持自动重定向到真正的播放页面：

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import PlaceholderPage from '@/components/app/PlaceholderPage.vue';

const pageTitle = ref('直播间');
const pageDescription = ref('直播功能正在开发中，敬请期待');

/**
 * 页面加载，接收路由参数
 * 如果接收到 id 参数（房间ID），自动重定向到真正的播放页面 LiveView
 */
onLoad((options) => {
  // 如果接收到房间ID，自动重定向到真正的播放页面
  const roomId = options?.id || options?.roomId;
  if (roomId) {
    uni.redirectTo({
      url: `/pages/app/live/LiveView?roomId=${roomId}${options?.title ? `&title=${encodeURIComponent(options.title)}` : ''}`
    });
    return;
  }

  // 否则显示占位页
  if (options?.title) {
    pageTitle.value = decodeURIComponent(options.title);
  }
  if (options?.id) {
    pageDescription.value = `直播间 ID: ${options.id}\n功能正在开发中，敬请期待`;
  }
});
</script>
```

**说明**：首页点击直播间卡片时传递的是 `room.id`（房间ID），占位页会自动重定向到 `LiveView.vue` 并传递 `roomId` 参数，`LiveView.vue` 会通过 `roomId` 自动查找当前场次并加载。

---

## 第8章：验证清单（Validation Checklist）

### 8.1 功能验证

- [ ] **页面加载**: LiveView页面正常打开，显示场次信息
- [ ] **播放器**: VideoPlayerApp正确集成，m3u8播放正常
- [ ] **TS切片检测**: ShadowParser正常工作，切片切换时上报观看历史
- [ ] **观看人数**: 实时显示观看人数，每30秒更新
- [ ] **流量提醒**: 4G/5G网络时显示提醒弹窗
- [ ] **Sticky Tabs**: Tab栏正确吸顶，内容切换正常
- [ ] **Mock/API切换**: VITE_USE_MOCK配置正确生效
- [ ] **错误处理**: 网络错误时有友好提示和重试机制

### 8.2 Mock模式验证

- [ ] `VITE_USE_MOCK=true`时使用本地Mock数据
- [ ] 观看人数显示mockViewerCount数据
- [ ] 场次信息显示mockSessionData
- [ ] 聊天/问答显示Mock消息列表
- [ ] **演示模式提示**: 聊天和问答Tab显示"演示模式"提示文字
- [ ] **本地聊天交互**: 可以发送消息并在本地显示（不发送到服务器）
- [ ] **本地问答交互**: 可以提交问题并在本地显示（不通知专家）

### 8.3 样式验证

- [ ] 页面布局符合设计稿（16:9播放器比例）
- [ ] 信息栏折叠/展开动画流畅
- [ ] Tab切换有视觉反馈
- [ ] 响应式布局在不同屏幕下正常显示
- [ ] **全面屏适配验证**: 全面屏设备（iPhone X+）底部安全区适配正常
- [ ] **键盘适配验证**: 输入框在键盘弹起时不被遮挡（cursor-spacing生效）
- [ ] **资源释放验证**: 退出页面时屏幕常亮自动关闭，定时器正确清理
- [ ] **加载状态验证**: 视频缓冲时显示loading，播放时自动隐藏
- [ ] **全屏方向验证**: 进入全屏自动横屏，退出全屏恢复竖屏

### 8.4 性能验证

- [ ] 页面首屏加载时间 < 3秒
- [ ] 播放器初始化时间 < 2秒
- [ ] m3u8解析时间 < 1秒
- [ ] 内存使用在合理范围内

---

## 第9章：测试策略与执行

### 9.1 测试环境准备

```typescript
// 测试用例：不同码率m3u8链接
const testM3u8Urls = {
  '720p': 'https://example.com/live_720p.m3u8',
  '1080p': 'https://example.com/live_1080p.m3u8',
  'low': 'https://example.com/live_low.m3u8'
};
```

### 9.2 性能测试指标

- **首帧时间**: 从播放开始到第一帧显示的时间 < 2秒
- **卡顿率**: 播放过程中卡顿总时长/总播放时长 < 5%
- **加载速度**: m3u8解析 + 首片段加载 < 3秒
- **内存使用**: 播放期间峰值内存 < 100MB

### 9.3 测试执行方法

1. **单元测试**: Jest + Vue Test Utils测试ShadowParser
2. **集成测试**: 播放器组件与页面交互测试
3. **网络模拟**: Chrome DevTools模拟不同网络条件
4. **设备测试**: 在Android/iOS真机上测试
5. **弱网测试**: 模拟2G/3G网络环境

---

## 🎯 执行指令（Execution Instructions）

**AI，现在请严格按照以上V3.0演示优化版提示词执行代码生成：**

### 执行流程

1. **第0章**: 执行强制性前置检查
2. **确认用户**: 等待用户输入"确认继续"
3. **按优先级生成**:
   - P0任务：ShadowParser.ts → VideoPlayerApp.vue → LiveView.vue
   - P1任务：API文件 → 类型定义 → Mock数据
   - P2任务：路由配置 → 测试验证

### 关键提醒

⚠️ **V3.0版本特性 - 演示优化版！**
- ✅ **完整演示交互**：聊天和问答支持本地模拟发送
- ✅ **适配完善**：全面屏安全区 + 键盘遮挡处理
- ✅ **容错机制增强**：ShadowParser失败不阻断播放
- ✅ **风险分析完整**：明确标注局限性和未来规划
- ⚠️ **演示版定位**：适合产品演示，不适合生产部署

⚠️ **这是增量开发项目，安全第一！**
- 不覆盖现有代码（除VideoPlayerApp.vue需要增强）
- 遵循现有的Mock/API切换模式
- 保持现有认证和错误处理逻辑

✅ **代码质量要求**
- Vue 3 Composition API + TypeScript
- uni-app原生组件 + iconfont图标
- 完整的类型定义和错误处理
- 安全区适配和键盘处理

---

## 第10章：当前版本局限性与未来规划

### **10.1 当前版本的局限性分析**

#### **⚠️ 功能体验局限（演示版特性）**
- **通信"伪"实时**：当前仅本地模拟，无WebSocket长连接
  - 后果：消息无法实时同步，刷新页面数据丢失
  - 影响：多人互动体验不完整
- **专家互动缺失**：问答提交仅前端模拟
  - 后果：专家无法收到通知，无真实回复机制
  - 影响：专业问答功能不完整

#### **⚠️ 技术实现风险（Vue方案）**
- **CSS层级风险**：video组件可能被其他元素遮挡
  - 缓解措施：已添加z-index优化和布局调整
- **ShadowParser解析风险**：m3u8解析可能因网络或格式问题失败
  - 缓解措施：已实现容错处理，失败不阻断播放
- **全面屏适配风险**：iPhone X等设备底部安全区适配
  - 缓解措施：已添加安全区CSS变量适配

#### **✅ 技术优势**
- **调试便利**：完整的Chrome DevTools支持
- **样式自由**：支持完整的CSS功能和选择器
- **热重载快**：修改后立即生效，无需重载模拟器

### **10.2 未来优化规划**

#### **🟢 Phase 2：短期迭代（1-2周）**
- **实时通信**：接入WebSocket，实现真正的实时聊天
- **数据持久化**：本地缓存聊天记录和观看进度
- **播放器增强**：添加倍速播放、画质切换功能

#### **🟡 Phase 3：中期优化（2-4周）**
- **专家系统**：完整的问答通知和回复机制
- **高级统计**：接入专业视频分析SDK
- **性能优化**：内存管理、加载速度优化

#### **🔴 Phase 4：长期规划（商业化）**
- **视频加密**：DRM保护，防止非法下载
- **多平台适配**：小程序、H5等平台支持
- **大数据分析**：用户行为深度分析

### **10.3 实施建议**

#### **当前版本定位**
- ✅ **Demo展示**：完整可交互的演示版本
- ✅ **功能验证**：验证UI和基础播放功能
- ✅ **问题发现**：提前暴露技术风险
- ✅ **开发基础**：为真实功能提供完整框架

#### **渐进式开发策略**
1. **V3.0当前**：完善Demo体验和Vue适配 ✅
2. **V4.0近期**：接入实时通信和数据持久化
3. **V5.0中期**：完整专家系统和高级功能
4. **V6.0长期**：商业化产品能力

---

## 第11章：统一Vue方案最佳实践（Unified Vue Best Practices）

### 11.1 统一Vue方案的优势与注意事项

#### 11.1.1 技术优势
```bash
# Vue统一方案的优势
✅ 完整的Chrome DevTools调试支持
✅ 支持scoped样式和完整CSS功能
✅ 热重载响应迅速，无需重载模拟器
✅ 统一的代码风格和开发规范
✅ 无需学习nvue特殊语法
✅ 完整的Vue生态支持
```

#### 11.1.2 组件使用原则
```bash
# 覆盖视频的UI组件（必须使用cover-view）
✅ 播放控制栏 (<cover-view>)
✅ 观看人数显示 (<cover-view>)
✅ 加载状态遮罩 (<cover-view>)
✅ 返回按钮 (<cover-view>)

# 普通UI组件（使用标准view）
✅ 页面布局 (<view>)
✅ 聊天列表 (<scroll-view>)
✅ 按钮组件 (<button>)
✅ 表单输入 (<input>)
```

### 10.2 开发规范

#### 11.2.1 Vue CSS规范
```scss
/* ✅ 推荐写法 */
.container {
  flex: 1;
  justify-content: center;
  align-items: center;
}

.video-player {
  width: 100%;
  height: 56.25vw; /* 16:9 */
}

/* ❌ 避免写法 */
.container .item { ... }  /* 后代选择器 */
view { ... }             /* 标签选择器 */
* { margin: 0; }         /* 通配符 */
```

#### 10.2.2 组件通信规范
```vue
<!-- ✅ vue页面引用vue组件 -->
<template>
  <VideoPlayerApp
    :src="url"
    @play="handlePlay"
  />
</template>

<script setup>
import VideoPlayerApp from '@/components/app/VideoPlayerApp.vue'
</script>
```

#### 11.2.3 状态管理规范
```typescript
// ✅ 播放状态用全局store
import { usePlayerStore } from '@/store/player'

const playerStore = usePlayerStore()

// ✅ 页面状态用局部state
const isLoading = ref(false)
```

### 10.3 调试和测试

#### 11.3.1 调试方式统一
```bash
# 统一vue文件调试
✅ Chrome DevTools
✅ 热重载
✅ 源码映射
✅ HBuilderX真机调试
✅ 控制台日志
```

#### 10.3.2 测试策略
```bash
# 功能测试
✅ 播放功能测试（多种设备）
✅ CSS层级优化测试（重点验证）
✅ 性能测试（内存、帧率）

# 兼容性测试
✅ iOS/Android真机测试
✅ 不同uni-app版本测试
✅ 网络环境测试
```

### 10.4 团队协作

#### 10.4.1 代码审查清单
```bash
vue文件检查项：
✅ 是否使用.vue扩展名
✅ 是否使用scoped样式
✅ 是否遵循Vue开发规范
✅ 是否正确引用vue组件
✅ 是否使用完整的CSS功能
```

#### 10.4.2 文档和培训
```bash
团队培训内容：
1. Vue开发最佳实践 (2h)
2. uni-app平台差异处理 (1h)
3. 调试技巧分享 (1h)
4. CSS层级优化技巧 (1h)
```

### 10.5 性能监控

#### 10.5.1 关键指标监控
```typescript
// 播放页面性能指标
const metrics = {
  firstFrameTime: 0,    // 首帧显示时间
  memoryUsage: 0,       // 内存占用
  frameRate: 60,        // 帧率
  loadTime: 0          // 页面加载时间
}
```

#### 10.5.2 错误监控
```typescript
// Vue播放错误监控
const handlePlaybackError = (error: string) => {
  console.error('[vue] Playback error:', error)
  // 上报错误日志
  reportError({
    type: 'playback_error',
    error,
    platform: 'vue',
    timestamp: Date.now()
  })
}
```

---

## 🎯 执行指令（Execution Instructions）

**AI，现在请严格按照纯 Vue + Cover-View 方案生成代码：**

### 执行流程
1. **第0章**: 执行强制性前置检查（了解项目现状）
2. **确认用户**: 等待用户确认分析结果
3. **Vue方案生成**:
   - **vue文件**: `LiveView.vue`、`VideoPlayerApp.vue` - 核心播放功能（使用cover-view）
   - **工具文件**: `ShadowParser.ts`、`player.ts`等 - TypeScript工具

### 关键提醒
✅ **统一开发要点**
- 所有页面使用vue格式，开发体验一致
- 通过CSS层级优化解决播放器显示问题
- 组件引用保持vue生态统一

✅ **代码质量保证**
- Vue文件遵循Vue开发规范
- vue文件保持现有风格
- 统一的状态管理和API调用

---

**[LiveView页面代码生成提示词文档 - V3.1 纯 Vue 方案 - 完成]**

