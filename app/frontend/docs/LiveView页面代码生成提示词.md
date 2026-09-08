# LiveView页面代码生成提示词 (Element Plus版)

## 角色与目标

你是一名资深前端重构工程师，**精通 Element Plus** 并对UI细节有像素级要求。我有一个已经可以完整运行的前端项目，其核心功能和业务逻辑（API请求、状态管理、数据处理）已经全部实现。

你的核心任务是**"换肤"与"组件化重构"**，即根据我提供的最新设计文档（`@前端分析及设计文档.md`）和参考图片，为项目构建一个全新的、基于 Element Plus 的UI视图层，同时必须**最大限度地复用**现有的业务逻辑代码。

## 核心原则

1. **[最高准则] UI组件库**: **所有UI元素必须使用 Element Plus 组件库进行构建**。禁止使用原生的HTML标签（如 `<div>`, `<button>`）来模拟复杂组件。你的目标是生成语义化、符合 Element Plus 最佳实践的代码。

2. **逻辑复用，视图替换**: 这是我们工作的最高原则。所有API请求、状态管理（Pinia/Vuex）、数据处理等逻辑都必须保留。你只负责重写页面的 `<template>` 部分，并调整 `<script>` 以适配 Element Plus 的数据绑定。

3. **禁止从零开始**: 不要创建任何新的业务逻辑。如果你需要数据或方法，请假设它们已经存在于原有的 `<script>` 部分。你只需进行绑定。

---

## 任务：重构 LiveView 页面

**文件路径**: `/src/pages/live/new/LiveView.vue`

**重要说明**: 此文件将创建在 `new/` 目录下，不会覆盖原有的 `src/pages/live/LiveView.vue` 文件，确保新旧代码可以并行存在，便于对比和回退。

### 1. 页面布局结构 (`<template>`)

请使用 Element Plus 组件来构建直播观看页面的完整布局，并精确复刻设计稿的视觉布局：

#### 1.1 整体布局结构

使用 `<el-container>` 构建左右分栏布局：

```vue
<template>
  <el-container class="live-view-container">
    <!-- 左侧主内容区 -->
    <el-main class="main-content">
      <!-- 顶部信息条 -->
      <!-- 视频播放器区域 -->
      <!-- 功能页签区域 -->
    </el-main>
    
    <!-- 右侧聊天互动区 -->
    <el-aside class="chat-sidebar">
      <!-- 聊天头部 -->
      <!-- 二维码区域 -->
      <!-- 管理员消息 -->
      <!-- 用户聊天消息 -->
      <!-- 聊天输入区 -->
      <!-- 悬浮操作按钮 -->
    </el-aside>
  </el-container>
</template>
```

#### 1.2 顶部信息条 (Top Info Bar)

**位置**: 左侧主内容区顶部
**组件**: 使用 `<el-card>` 包裹，内部使用 `<el-row>` 和 `<el-col>` 布局

**左侧区域**:
- 标题：使用 `<el-text>` 显示直播标题，如"脊柱手术演示二"
- 状态标签：使用 `<el-tag>` 显示"回放中"状态，`type="info"`
- 观看数据：使用 `<el-space>` 包含播放图标和观看数"1.31万"
- 时间信息：显示开播时间"2025/09/05 08:40:00"

**右侧区域**:
- 操作按钮组：使用 `<el-space>` 包含以下按钮：
  - 语言切换：`<el-button link>` + `<el-icon><Globe /></el-icon>` + "语言切换"
  - 投诉：`<el-button link>` + `<el-icon><Warning /></el-icon>` + "投诉"  
  - 分享：`<el-button link>` + `<el-icon><Share /></el-icon>` + "分享"

#### 1.3 视频播放器区域 (Video Player Area)

**位置**: 顶部信息条下方
**组件**: 使用 `<el-card>` 包裹

**背景设计**:
- 使用渐变背景：`background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)`
- 添加抽象光效和建筑轮廓装饰元素

**内容覆盖层**:
- 主标题：使用 `<el-text>` 显示"中国骨科教育大会"（大号白色字体）
- 副标题：显示"智能骨科技术培训班"（大号白色字体）
- 日期：显示"2025年9月5日"（中等白色字体）
- 地点：显示"解放军总医院第八医学中心"（中等白色字体）

**播放控制**:
- 中央播放按钮：使用 `<el-button>` 圆形按钮，`type="primary"`，`size="large"`
- 播放提示文字："点击播放"
- 底部状态标签：使用 `<el-tag>` 显示"直播回放中"

#### 1.4 功能页签区域 (Function Tabs)

**位置**: 视频播放器下方
**组件**: 使用 `<el-tabs>` 组件

**页签选项**:
- 直播介绍
- 病例介绍  
- 返回主会场

**内容区域**:
- 使用 `<el-tab-pane>` 的默认插槽显示对应内容
- 返回主会场页签：使用 `<el-button type="primary" link>` 显示"返回主会场"

#### 1.5 右侧聊天互动区 (Chat Sidebar)

**位置**: 页面右侧固定宽度区域
**组件**: 使用 `<el-aside>` 包裹，`width="360px"`

**聊天头部**:
- 使用 `<el-card>` 头部，显示"聊天互动"标题

**用户聊天消息**:
- 使用 `<el-space direction="vertical">` 垂直排列消息
- 每条消息使用 `<el-card>` 包裹：
  - 用户头像：`<el-avatar>` 带颜色背景
  - 用户名：显示用户昵称
  - 消息内容：显示聊天文字

**聊天输入区**:
- 使用 `<el-input>` 作为输入框，`placeholder="说点什么~"`
- 左侧图标：表情和收藏图标
- 发送按钮：`<el-button type="primary">发送</el-button>`

**悬浮操作按钮** (右侧边缘):
- 点赞按钮：`<el-button>` 圆形，红色心形图标 + "29"
- 手机观看：`<el-button>` 圆形，手机图标 + "手机看"
- 个人中心：`<el-button>` 圆形，用户头像 + "我的"

### 2. 样式设计 (`<style scoped>`)

#### 2.1 整体布局样式

```scss
.live-view-container {
  height: 100vh;
  background-color: #f5f5f5;
}

.main-content {
  padding: 0;
  background-color: #ffffff;
}

.chat-sidebar {
  background-color: #ffffff;
  border-left: 1px solid #e4e7ed;
  padding: 0;
}
```

#### 2.2 顶部信息条样式

```scss
.top-info-bar {
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  
  .live-title {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    margin-right: 12px;
  }
  
  .status-tag {
    margin-right: 16px;
  }
  
  .view-count {
    display: flex;
    align-items: center;
    color: #606266;
    font-size: 14px;
  }
  
  .live-time {
    color: #909399;
    font-size: 14px;
  }
}
```

#### 2.3 视频播放器样式

```scss
.video-player-area {
  position: relative;
  min-height: 400px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  
  .event-title {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 16px;
    text-align: center;
  }
  
  .event-subtitle {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 12px;
    text-align: center;
  }
  
  .event-date, .event-location {
    font-size: 16px;
    margin-bottom: 8px;
    text-align: center;
  }
  
  .play-button {
    margin: 32px 0 16px 0;
    width: 80px;
    height: 80px;
    border-radius: 50%;
  }
  
  .playback-status {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
  }
}
```

#### 2.4 聊天区域样式

```scss
.chat-sidebar {
  .chat-header {
    padding: 16px;
    border-bottom: 1px solid #e4e7ed;
    text-align: center;
    font-weight: 600;
  }
  
  .qr-code-section {
    padding: 16px;
    text-align: center;
    
    .qr-image {
      width: 120px;
      height: 120px;
      margin: 0 auto 8px;
    }
  }
  
  .admin-messages {
    padding: 16px;
    border-bottom: 1px solid #e4e7ed;
    
    .admin-avatar {
      margin-right: 8px;
    }
    
    .admin-name {
      font-weight: 600;
      color: #303133;
    }
    
    .message-content {
      margin: 8px 0;
      line-height: 1.5;
    }
    
    .message-time {
      color: #909399;
      font-size: 12px;
    }
  }
  
  .user-messages {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    max-height: 300px;
    
    .message-item {
      margin-bottom: 12px;
      
      .user-avatar {
        margin-right: 8px;
      }
      
      .user-name {
        font-weight: 500;
        color: #303133;
        margin-bottom: 4px;
      }
      
      .message-text {
        color: #606266;
        line-height: 1.4;
      }
    }
  }
  
  .chat-input-area {
    padding: 16px;
    border-top: 1px solid #e4e7ed;
    
    .input-with-icons {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      
      .input-icons {
        margin-right: 8px;
      }
    }
  }
  
  .floating-actions {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .action-button {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      
      &.like-button {
        background-color: #ff4757;
        color: white;
      }
      
      &.mobile-button, &.profile-button {
        background-color: #f5f5f5;
        color: #606266;
      }
    }
  }
}
```

### 3. 逻辑绑定适配 (`<script setup>`)

#### 3.1 组件导入

确保导入所有需要的 Element Plus 组件：

```typescript
import { 
  ElContainer, ElMain, ElAside, ElCard, ElRow, ElCol, 
  ElText, ElTag, ElSpace, ElButton, ElIcon, ElTabs, 
  ElTabPane, ElImage, ElAvatar, ElLink, ElInput 
} from 'element-plus'
import { 
  Globe, Warning, Share, VideoPlay, ChatDotRound, 
  Heart, Iphone, User 
} from '@element-plus/icons-vue'
```

#### 3.2 数据绑定适配

**重要**: 请完全复用原有 `src/pages/live/LiveView.vue` 中的所有数据、计算属性和方法，只进行UI组件的替换。

将现有的数据绑定到 Element Plus 组件：

- **直播标题**: 绑定到 `<el-text>` 的文本内容（复用 `roomDetail.value?.title`）
- **状态信息**: 绑定到 `<el-tag>` 的 `type` 和文本（复用 `currentSession.value?.status`）
- **观看数据**: 绑定到观看数显示（复用现有的观看数据逻辑）
- **时间信息**: 使用 `dayjs` 格式化后绑定（复用 `formatTime` 函数）
- **聊天消息**: 绑定到消息列表的 `v-for` 循环（复用 `mockComments` 数据）
- **用户信息**: 绑定到头像和用户名显示（复用现有用户数据）
- **播放地址**: 复用 `play_url` 计算属性和 `h5PlayerUrl` 计算属性
- **推荐房间**: 复用 `recommendedRooms` 计算属性

#### 3.3 事件处理适配

**重要**: 请完全复用原有的事件处理函数，只进行组件绑定。

将现有的事件处理函数绑定到 Element Plus 组件：

- **播放按钮**: 绑定到 `<el-button>` 的 `@click` 事件（复用现有的播放逻辑）
- **页签切换**: 绑定到 `<el-tabs>` 的 `@tab-click` 事件（复用现有的页签切换逻辑）
- **聊天发送**: 绑定到发送按钮的 `@click` 事件（复用现有的聊天发送逻辑）
- **悬浮按钮**: 绑定到各个操作按钮的 `@click` 事件（复用现有的操作逻辑）
- **返回按钮**: 复用 `goBackToList` 和 `goBackToRoom` 函数
- **房间跳转**: 复用 `goToRoomDetail` 函数
- **页面加载**: 复用 `onLoad` 和 `onMounted` 生命周期逻辑

### 4. 响应式设计

#### 4.1 移动端适配

```scss
@media (max-width: 768px) {
  .live-view-container {
    flex-direction: column;
  }
  
  .chat-sidebar {
    width: 100% !important;
    height: 300px;
    border-left: none;
    border-top: 1px solid #e4e7ed;
  }
  
  .video-player-area {
    min-height: 250px;
    
    .event-title {
      font-size: 24px;
    }
    
    .event-subtitle {
      font-size: 18px;
    }
  }
  
  .floating-actions {
    position: fixed;
    bottom: 20px;
    right: 20px;
    top: auto;
    transform: none;
    flex-direction: row;
  }
}
```

### 5. 实现优先级

#### 5.1 P0 优先级（必须实现）
- 整体布局结构（左右分栏）
- 顶部信息条（标题、状态、时间）
- 视频播放器区域（背景、标题覆盖、播放按钮）
- 基础聊天区域（消息显示、输入框）

#### 5.2 P1 优先级（重要功能）
- 功能页签（直播介绍、返回主会场）
- 管理员消息区域
- 二维码显示
- 悬浮操作按钮

#### 5.3 P2 优先级（增强体验）
- 响应式移动端适配
- 动画效果和过渡
- 表情面板（占位实现）
- 聊天室管理功能（占位实现）

### 6. 静态占位策略

对于"暂缓实现"的功能，统一使用以下策略：

- **表情面板**: 点击表情图标显示 `ElMessage.info('表情功能待开发，敬请期待')`
- **聊天室管理**: 相关管理功能显示 `ElMessage.info('管理功能待开发，敬请期待')`
- **高级播放控制**: 全屏、清晰度切换等显示 `ElMessage.info('播放控制功能待开发，敬请期待')`

---

请根据以上详细要求，生成完整的 `src/pages/live/new/LiveView.vue` 文件代码，确保：
1. 完全使用 Element Plus 组件构建UI
2. 保持现有业务逻辑不变
3. 精确复刻设计稿的视觉效果
4. 实现响应式布局
5. 提供良好的用户体验

## 文件组织说明

### 目录结构
```
src/pages/live/
├── LiveView.vue          # 原有文件（保持不变）
└── new/
    └── LiveView.vue      # 新重构文件（Element Plus版本）
```

### 开发策略
- **并行开发**: 新旧文件可以同时存在，便于对比和测试
- **渐进迁移**: 可以先在 `new/` 目录下完成重构，测试无误后再考虑替换
- **回退保障**: 如果新版本有问题，可以快速回退到原版本
- **代码复用**: 新版本完全复用原版本的业务逻辑，只替换UI层

### 路由配置
如果需要测试新版本，可以在 `pages.json` 中临时添加新路由：
```json
{
  "path": "pages/live/new/LiveView",
  "style": {
    "navigationBarTitleText": "直播观看",
    "navigationStyle": "custom"
  }
}
```

## 附录：直播/回放切换实现说明（前端改动概要）

### VideoPlayer.vue（播放器组件）
- 增加了对 `props.src` 的监听：当外部传入的播放地址变化时，优先调用 `art.switchUrl(newSrc)` 平滑切换，若失败则销毁并重建播放器实例。
- 管理 HLS 内核实例：引入 `currentHls`，在每次切换/卸载时 `destroy()`，防止内存泄漏与多实例冲突。
- 组件卸载时同时销毁 Artplayer 与 Hls 实例，保证资源释放干净。
- 目的：让外部只需要变更 `src`，播放器就能无缝切到“直播流→回放”。

### LiveView.vue（业务页面）
- 引入播放状态机与源地址抽象：
  - `playbackPhase`: `'live' | 'generating' | 'vod'` 表示“直播中/回放生成中/回放就绪”。
  - `liveUrl`: 基于 `roomDetail.stream_key` 生成直播 HLS 地址（`/hls-proxy/${stream_key}.m3u8`）。
  - `vodUrl`: 回放地址，等到后端可用时赋值。
  - `playerSourceUrl`: 播放器真正使用的地址，按状态在 `liveUrl` 与 `vodUrl` 之间切换。
  - `emptySourceHint`: 在“生成中”时显示“回放生成中，请稍候...”，其余为空源提示。
- 自动切换与轮询回放：
  - 监听 `currentSession.status`：
    - `live` → 设置 `playbackPhase='live'`（继续使用直播源）。
    - `ended/archived` → 设置 `playbackPhase='generating'` 并启动回放轮询。
  - `startVodPolling()` 做两件事：
    1) 优先刷新 `roomDetail`，尝试读取后端返回的 `vod_url` 或 `replay_url` 字段；若存在则设置 `vodUrl` 并切到 `vod`，停止轮询。
    2) 若没有明确字段，则根据约定尝试根据直播地址推导一个录播地址（示例：把 `.m3u8` 改成 `-vod.m3u8`），对该地址发 `HEAD` 探测，成功即切到 `vod` 并停轮询。
  - 轮询采用“指数退避”（2s 起，逐步加大至 30s 上限），避免高频请求。
- 模板改动：
  - 播放器从使用 `play_url` 改为使用 `playerSourceUrl`，并在空源时展示更友好的文案。
  - 非 H5 备用 `<video>` 也统一用 `playerSourceUrl`。

### 前端如何获取后端“回播地址”
- 首选：后端在房间详情或场次详情中提供字段
  - 例如在 `GET /rooms/{roomId}` 或 `GET /sessions/{sessionId}` 的响应里包含 `vod_url` 或 `replay_url` 字段。
  - 前端在轮询时会“刷新房间详情”，一旦发现该字段存在，就会立刻把播放器切换到回放播放源。
  - 这不需要改后端接口定义，只要后端在既有返回体里补充该字段即可。
- 兜底：命名规则推断 + HEAD 探测
  - 如果后端没有显式字段，但存储有“录播文件与直播清单的可推断命名规则”，前端会把 `/xxx/stream_key.m3u8` 推断为录播 `/xxx/stream_key-vod.m3u8`（可按实际修改规则），并用 `fetch(url, { method: 'HEAD' })` 探测该 URL 是否可访问。
  - 探测成功就切到回放；未成功继续指数退避轮询（避免频繁打后端/存储）。
- 可选优化（可忽略后端改造时）
  - 若后端能在“推流完成”时通过 WebSocket/事件推送“回放已就绪 + URL”，前端即可免轮询即刻切换。
  - 回放 URL 若带鉴权签名/过期时间，建议配一个“刷新回放地址”的查询；本前端轮询时会自然刷新。

> 要点：
> - “直播中”确保有 `roomDetail.stream_key` 用于拼 HLS 直播 URL。
> - “直播结束后”后端要么在详情里带上 `vod_url/replay_url`，要么对象存储具备可推断命名规则供前端 HEAD 探测。

