# 播放页Tab功能实现提示词 (uni-app移动端版)

---

## ⚠️ 重要声明

**本提示词用于实现播放页的Tab动态化功能，支持内容型Tab和功能型Tab。**

- ✅ **技术栈**：纯Vue 3 Composition API + TypeScript
- ✅ **核心功能**：Tab动态获取、内容型Tab渲染、功能型Tab交互（专家关注、品牌跳转、聊天发送）
- ✅ **后端支持**：完整的Tab CRUD API、留言API、专家品牌关联API
- ✅ **兼容性**：仅针对APP端，H5端暂不修改
- ✅ **渐进增强**：先实现核心功能，管理员新增Tab功能后续实现

---

## 🏗️ 架构基础（必读）

**在开始开发前，你必须先阅读以下文档：**

📖 **设计文档**：
- `docs/直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md`（Section 4.17 Tab Management API、Section 4.18 Messages API）
- `docs/直播核心功能设计文档_v6_深度融合最终版.md`（live_room_tabs表结构、live_room_messages表结构）
- `docs/直播简介与图文混合-统一方案.md`（直播介绍Tab设计）
- `docs/直播核心功能设计文档_v6_品牌模块设计文档-品牌管理-品牌专题关联.md`（品牌Tab设计）

---

## 第0章：强制性前置检查 ⚡（必须先执行）

### 0.1 检查目的

在生成任何代码之前，必须全面了解项目现状，避免：
- ❌ 覆盖已有的完善代码
- ❌ 与现有类型定义冲突
- ❌ 创建重复的API封装
- ❌ 破坏现有的导入依赖关系

### 0.2 必须执行的检查步骤

#### 步骤1：读取现有核心文件（强制）

你必须先读取以下文件，了解现有实现：

```bash
必须读取的文件清单：
✅ src/pages/app/live/LiveView.vue - 现有播放页实现（重点检查Tab相关代码）
✅ src/api/room.ts - 房间API（getRoomDetail等）
✅ src/api/expert.ts - 专家API（重点检查是否已有getRoomExperts、associateSessionExperts方法）
✅ src/api/brand.ts - 品牌API（需检查是否有关联API）
✅ src/api/expertFollow.ts - 专家关注API
✅ src/store/follow.ts - 关注Store
✅ src/store/user.ts - 用户Store（检查权限验证相关字段）
✅ src/types/room.ts - 房间类型定义
✅ src/types/expert.ts - 专家类型定义
✅ src/utils/request.ts - 请求工具
✅ src/utils/image.ts - 图片URL处理工具
```

**执行命令**：使用 `read_file` 工具逐个读取以上文件。

#### 步骤2：扫描目录结构（强制）

```bash
必须扫描的目录：
✅ src/api/ - 列出所有.ts文件，确认是否存在tab.ts、message.ts
✅ src/types/ - 列出所有.ts文件，确认是否存在tab.ts、message.ts
✅ src/components/ - 列出可复用组件
```

**执行命令**：使用 `find_by_name` 或 `list_dir` 工具扫描目录。

#### 步骤3：在聊天窗口输出项目现状分析（强制）

**重要**：❗ 不要生成单独的分析报告文件，直接在聊天窗口中展示分析结果！

基于步骤1和步骤2的检查结果，在聊天窗口中输出以下结构化分析：

---

**📊 Tab功能开发现状分析**

**一、已存在且可直接复用的文件（✅ 直接使用）**
- 列出所有可复用的API、Store、组件
- 注明文件路径、核心功能
- 给出"直接导入使用"的结论

**二、已存在但需要扩展的文件（🔧 需要补充）**
- 列出需要补充的文件（如expert.ts需要添加关联API）
- 明确列出现有方法清单
- 明确列出缺失方法（如getRoomExperts、associateSessionExperts）
- 说明操作方式（multi_edit，保留现有方法）

**三、需要新建的文件（➕ 需新建）**
- 列出所有需要新建的API文件（tab.ts、message.ts、brand.ts等）
- 列出需要新建的类型定义文件（tab.ts、message.ts等）
- 列出需要新建的组件文件（ContentTab.vue、ExpertsTab.vue等）

**四、LiveView.vue修改范围（📍 需修改）**
- 检查现有Tab实现方式（是否硬编码、是否使用Mock数据）
- 列出需要修改的部分（Tab获取、Tab渲染逻辑）
- 列出需要保留的部分（播放器、顶部信息栏等）
- **重要决策**：如果现有Tab是硬编码或Mock数据：
  - 方案A：直接替换为动态Tab（推荐）
  - 方案B：API调用失败时降级使用硬编码Tab（备选）
  - 需要在分析报告中明确说明采用哪种方案

**五、expert.ts冲突检查（🔍 重点检查）**
- 检查是否已存在`getRoomExperts`方法
- 检查是否已存在`associateSessionExperts`方法
- 如果已存在，列出现有方法的签名和功能
- 如果不存在，确认可以安全添加

**六、安全性分析**
- ⚠️ 列出潜在风险点（文件冲突、方法重复、权限验证等）
- ✅ 给出安全操作策略

---

#### 步骤4：等待用户确认（强制）

在聊天窗口输出分析结果后，**必须等待用户确认**才能继续生成代码。

向用户提问：
```
📋 以上是Tab功能开发现状分析结果。

请确认：
1. 分析结果是否准确？
2. 是否有遗漏或需要调整的地方？
3. 如果确认无误，请输入"确认继续"开始代码生成。
```

**禁止**在用户确认前开始生成任何代码！

---

## 第1章：角色定义（Role Definition）

你是一名**资深移动端前端工程师**，具备以下专业技能：

- **精通技术栈**：uni-app、Vue 3 Composition API、TypeScript、移动端H5开发
- **增量开发能力**：能够在现有项目基础上进行安全的增量开发，不破坏现有功能
- **API集成经验**：熟悉RESTful API设计，能够快速封装后端接口
- **组件化开发**：熟悉Vue组件化开发，能够设计可复用的组件

**你的任务是根据详细设计文档和现有代码基础，编写高质量、功能完整、可直接运行的增量代码。**

---

## 第2章：任务目标（Task Objective）

### 2.1 核心目标

实现播放页的Tab动态化功能，支持以下Tab类型：

1. **内容型Tab**：
   - 直播介绍Tab（tab_key='intro'）：显示直播简介文字和图片
   - 管理员自定义Tab：显示管理员在管理页面新增的内容

2. **功能型Tab**：
   - 专家介绍Tab（tab_key='experts'）：显示专家列表、支持关注、跳转详情页
   - 品牌介绍Tab（tab_key='brands'）：显示品牌列表、支持跳转详情页
   - 聊天Tab（tab_key='chat'）：显示历史消息、支持发送新消息

### 2.2 功能范围

#### 本期实现功能

**API封装**：
- ✅ Tab CRUD API（创建、获取、更新、删除）
- ✅ 留言API（发送留言、获取留言列表）
- ✅ 专家关联API（关联专家、获取房间专家）
- ✅ 品牌关联API（关联品牌、获取房间品牌）

**类型定义**：
- ✅ Tab类型定义（Tab、TabCreatePayload、TabUpdatePayload等）
- ✅ Message类型定义（Message、MessageCreatePayload等）

**组件开发**：
- ✅ ContentTab.vue（内容型Tab组件，支持text/image/mixed）
- ✅ ExpertsTab.vue（专家介绍Tab组件，支持关注、跳转）
- ✅ BrandsTab.vue（品牌介绍Tab组件，支持跳转）
- ✅ ChatTab.vue（聊天Tab组件，支持查看历史、发送消息）

**播放页修改**：
- ✅ 修改LiveView.vue，从后端动态获取Tab列表
- ✅ 根据tab_key判断渲染哪种组件
- ✅ 保持现有UI风格（蓝色下划线指示器）

**创建直播页修改**：
- ✅ 修改create.vue，创建房间后自动创建Tab
- ✅ 直播介绍Tab（始终创建）
- ✅ 专家介绍Tab（选择了专家时创建）
- ✅ 品牌介绍Tab（选择了品牌时创建）
- ✅ 聊天Tab（移动端自动创建）

#### 暂缓实现功能

- ❌ 管理员新增Tab功能（管理页面，后续实现）
- ❌ H5端Tab动态化（H5端聊天在右侧，保持不变）
- ❌ 资料下载Tab（后端API未实现）
- ❌ WebSocket实时聊天（使用定时轮询，每5秒刷新）

---

## 第3章：Tab类型设计

### 3.1 Tab类型映射

| tab_key | Tab名称 | 组件类型 | 数据来源 | 是否支持交互 |
|---------|---------|---------|---------|------------|
| `intro` | 直播介绍 | ContentTab | Tab表的`text_content`和`image_url` | ❌ 纯展示 |
| `experts` | 专家介绍 | ExpertsTab | `GET /api/v1/rooms/{room_id}/experts` | ✅ 关注、跳转 |
| `brands` | 品牌介绍 | BrandsTab | `GET /api/v1/rooms/{room_id}/brands` | ✅ 跳转 |
| `chat` | 聊天 | ChatTab | `GET /api/v1/rooms/{room_id}/messages` | ✅ 发送消息 |
| 其他 | 自定义Tab | ContentTab | Tab表的`text_content`和`image_url` | ❌ 纯展示 |

### 3.2 Tab渲染逻辑

```typescript
// 功能型Tab的tab_key列表
const FUNCTIONAL_TAB_KEYS = ['experts', 'brands', 'chat']

// 判断Tab类型并渲染对应组件
if (tab.tab_key === 'experts') {
  return <ExpertsTab roomId={roomId} />
} else if (tab.tab_key === 'brands') {
  return <BrandsTab roomId={roomId} />
} else if (tab.tab_key === 'chat') {
  return <ChatTab roomId={roomId} />
} else {
  // 内容型Tab（intro或管理员自定义Tab）
  return <ContentTab tab={tab} />
}
```

---

## 第4章：API需求说明

### 4.0 API路径策略（重要）⚡

**前端统一使用不带版本号的路径**，通过Nginx代理转发到后端的 `/api/v1`：

#### 路径转发流程

```
前端BaseURL: https://mp.dayilive.com/api/core (从 ENV_CONFIG.VITE_BASE_API_URL 获取)
前端调用路径: /rooms/{room_id}/messages
实际请求URL: https://mp.dayilive.com/api/core/rooms/{room_id}/messages

↓ Nginx代理转发 ↓

后端接收路径: http://124.220.235.226:8000/api/v1/rooms/{room_id}/messages
```

#### 关键原则

- ✅ 前端API路径**不带** `/api/v1` 前缀
- ✅ 使用 `request()` 工具函数时，路径以 `/` 开头
- ✅ BaseURL从 `ENV_CONFIG.VITE_BASE_API_URL` 获取
- ✅ 文件上传使用 `${ENV_CONFIG.VITE_BASE_API_URL}/路径` 拼接完整URL
- ❌ **禁止**在前端代码中硬编码 `/api/v1`

#### 正确示例

```typescript
// ✅ 正确：普通API调用
export const getRoomMessages = (roomId: string) => {
  return request<MessageListResponse>({
    url: `/rooms/${roomId}/messages`,  // 不带 /api/v1
    method: 'GET'
  })
}

// ✅ 正确：文件上传
import { ENV_CONFIG } from '@/config/env'
import { getToken } from '@/utils/auth'

export const uploadTabImage = (roomId: string, filePath: string) => {
  return new Promise<string>((resolve, reject) => {
    uni.uploadFile({
      url: `${ENV_CONFIG.VITE_BASE_API_URL}/admin/rooms/${roomId}/tabs/image`,
      filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${getToken()}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          const data = JSON.parse(res.data)
          resolve(data.data.image_url)
        } else {
          reject(new Error('上传失败'))
        }
      },
      fail: reject
    })
  })
}
```

#### 错误示例

```typescript
// ❌ 错误：不要添加 /api/v1
url: `/api/v1/rooms/${roomId}/messages`  // 错误！

// ❌ 错误：不要硬编码完整URL
url: `https://mp.dayilive.com/api/core/rooms/${roomId}/messages`  // 错误！

// ❌ 错误：不要硬编码BASE_URL
url: `${BASE_API_URL}/admin/rooms/${roomId}/tabs/image`  // 错误！应使用 ENV_CONFIG.VITE_BASE_API_URL
```

---

### 4.1 Tab Management API

**获取直播间Tab列表**：
- 后端路径：`GET /api/v1/admin/rooms/{room_id}/tabs`
- 前端调用：`url: '/admin/rooms/${roomId}/tabs'`（不带 `/api/v1`）
- 响应：返回Tab数组，包含所有Tab（前端创建的和管理员新增的）

**创建Tab**：
- 后端路径：`POST /api/v1/admin/rooms/{room_id}/tabs`
- 前端调用：`url: '/admin/rooms/${roomId}/tabs'`（不带 `/api/v1`）
- 请求体：`{ tab_key, title, content_type, text_content, image_url, sort_order, is_active }`
- 响应：返回创建的Tab对象

**更新Tab**：
- 后端路径：`PATCH /api/v1/admin/tabs/{tab_id}`
- 前端调用：`url: '/admin/tabs/${tabId}'`（不带 `/api/v1`）
- 请求体：`{ title?, content_type?, text_content?, image_url?, sort_order?, is_active? }`
- 响应：返回更新后的Tab对象

**删除Tab**：
- 后端路径：`DELETE /api/v1/admin/tabs/{tab_id}`
- 前端调用：`url: '/admin/tabs/${tabId}'`（不带 `/api/v1`）
- 响应：返回删除状态

**上传Tab图片**：
- 后端路径：`POST /api/v1/admin/rooms/{room_id}/tabs/image`
- 前端调用：`url: '${ENV_CONFIG.VITE_BASE_API_URL}/admin/rooms/${roomId}/tabs/image'`（完整URL）
- 请求体：`multipart/form-data`，字段名为 `file`
- 响应：返回图片URL（相对路径）

### 4.2 Messages API

**发送留言**：
- 后端路径：`POST /api/v1/rooms/{room_id}/messages`
- 前端调用：`url: '/rooms/${roomId}/messages'`（不带 `/api/v1`）
- 请求体：`{ content: string }`
- 响应：返回创建的留言对象

**获取留言列表**：
- 后端路径：`GET /api/v1/rooms/{room_id}/messages`
- 前端调用：`url: '/rooms/${roomId}/messages'`（不带 `/api/v1`）
- 查询参数：`page`, `page_size`, `status`
- 响应：返回留言列表和分页信息

### 4.3 Expert API（需补充）

**关联场次专家**：
- 后端路径：`POST /api/v1/admin/sessions/{session_id}/experts`
- 前端调用：`url: '/admin/sessions/${sessionId}/experts'`（不带 `/api/v1`）
- 请求体：`{ expert_ids: string[] }`
- 响应：返回关联结果

**获取房间专家**：
- 后端路径：`GET /api/v1/rooms/{room_id}/experts`
- 前端调用：`url: '/rooms/${roomId}/experts'`（不带 `/api/v1`）
- 响应：返回专家列表

### 4.4 Brand API（需新建）

**关联房间品牌**：
- 后端路径：`POST /api/v1/admin/rooms/{room_id}/brands`
- 前端调用：`url: '/admin/rooms/${roomId}/brands'`（不带 `/api/v1`）
- 请求体：`{ brand_ids: string[] }`
- 响应：返回关联结果

**获取房间品牌**：
- 后端路径：`GET /api/v1/rooms/{room_id}/brands`
- 前端调用：`url: '/rooms/${roomId}/brands'`（不带 `/api/v1`）
- 响应：返回品牌列表

---

## 第5章：核心原则

1. **API规范**：严格遵循后端API规范，使用正确的HTTP方法（PATCH而非PUT）
2. **API路径规范**：前端API路径不带 `/api/v1` 前缀，文件上传使用 `ENV_CONFIG.VITE_BASE_API_URL`
3. **错误处理规范**：
   - ✅ 所有API调用都必须使用 `try-catch` 包装
   - ✅ 在 `catch` 块中使用 `uni.showToast` 显示用户友好的错误提示
   - ✅ 记录详细的错误日志到控制台（`console.error`）
   - ✅ 错误信息要具体明确，包含操作名称和错误原因
   - ❌ 禁止静默失败，所有错误都要让用户知道
4. **组件复用**：内容型Tab使用统一的ContentTab组件，功能型Tab各自独立
5. **数据来源**：所有Tab都从后端API获取，不硬编码Tab列表
6. **渐进增强**：先实现核心功能，管理员新增Tab功能后续实现
7. **兼容性**：仅修改APP端，H5端保持不变
8. **UI一致性**：保持现有播放页的UI风格（蓝色下划线指示器）

### 5.1 错误处理规范示例

**正确的错误处理方式**：

```typescript
// ✅ 正确：完整的错误处理
try {
  const { data } = await getRoomExperts(props.roomId)
  experts.value = data
} catch (error: any) {
  console.error('获取专家列表失败:', error)
  uni.showToast({
    title: error.message || '获取专家列表失败',
    icon: 'none',
    duration: 2000
  })
} finally {
  loading.value = false
}
```

**错误的错误处理方式**：

```typescript
// ❌ 错误：静默失败，用户不知道发生了什么
try {
  const { data } = await getRoomExperts(props.roomId)
  experts.value = data
} catch (error) {
  console.error('获取专家列表失败', error)  // 只记录日志，不提示用户
}

// ❌ 错误：错误信息不明确
catch (error) {
  uni.showToast({ title: '失败', icon: 'none' })  // 用户不知道什么失败了
}
```

### 5.2 空态处理规范

所有列表组件都必须处理空数据状态：

**空态显示要求**：
- ✅ 显示加载状态（loading）
- ✅ 显示空态图标和提示文案
- ✅ 提供刷新或引导操作

**示例代码**：
```vue
<template>
  <view class="tab-container">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <uni-loading type="circle" />
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 空态 -->
    <view v-else-if="items.length === 0" class="empty-state">
      <image src="/static/empty.png" class="empty-icon" mode="widthFix" />
      <text class="empty-text">暂无数据</text>
      <button class="empty-btn" @tap="handleRefresh">刷新</button>
    </view>
    
    <!-- 列表内容 -->
    <view v-else class="list-content">
      <!-- 列表项 -->
    </view>
  </view>
</template>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.loading-text {
  margin-top: 24rpx;
  font-size: 28rpx;
  color: #999;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.empty-icon {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 32rpx;
}

.empty-btn {
  padding: 16rpx 48rpx;
  background: #1890ff;
  color: #fff;
  border-radius: 32rpx;
  font-size: 28rpx;
}
</style>
```

### 5.3 权限验证规范

**创建Tab权限验证**：
```typescript
import { useUserStore } from '@/store/user'

const handleCreateTab = async () => {
  const userStore = useUserStore()
  
  // 检查是否为Admin
  if (!userStore.isAdmin) {
    uni.showToast({
      title: '无权限创建Tab',
      icon: 'none',
      duration: 2000
    })
    return
  }
  
  // 继续创建逻辑...
}
```

**发送留言权限验证**：
```typescript
const sendMessage = async () => {
  const userStore = useUserStore()
  
  // 检查是否登录
  if (!userStore.isLoggedIn) {
    uni.showToast({
      title: '请先登录',
      icon: 'none',
      duration: 2000
    })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/index' })
    }, 1500)
    return
  }
  
  // 继续发送逻辑...
}
```

**查看私有房间权限验证**：
```typescript
const loadRoomTabs = async () => {
  try {
    const { data } = await getRoomDetail(roomId.value)
    
    // 检查是否为私有房间
    if (data.is_private && !data.has_access) {
      uni.showToast({
        title: '无权限查看该房间',
        icon: 'none'
      })
      setTimeout(() => {
        uni.navigateBack()
      }, 1500)
      return
    }
    
    allTabs.value = data.tabs || []
  } catch (error: any) {
    console.error('获取房间详情失败:', error)
    uni.showToast({
      title: error.message || '获取房间详情失败',
      icon: 'none'
    })
  }
}
```

### 5.4 XSS防护规范

**聊天内容安全处理**：
```typescript
// 内容清理函数
const sanitizeContent = (content: string): string => {
  if (!content) return ''
  
  // 移除HTML标签
  let sanitized = content.replace(/<[^>]*>/g, '')
  
  // 转义特殊字符
  sanitized = sanitized
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
  
  return sanitized
}

// 在模板中使用
<text class="message-text">{{ sanitizeContent(msg.content) }}</text>
```

### 5.5 图片加载失败处理

所有图片都必须处理加载失败：

```vue
<template>
  <image 
    :src="getImageSrc(expert.avatar_url)" 
    @error="handleImageError"
    class="expert-avatar"
  />
</template>

<script setup lang="ts">
const handleImageError = (e: any) => {
  // 使用默认头像
  e.target.src = '/static/default-avatar.png'
}
</script>
```

**品牌Logo加载失败**：
```vue
<image 
  :src="getImageSrc(brand.logo_url)" 
  @error="(e) => e.target.src = '/static/default-logo.png'"
  class="brand-logo"
/>
```

**Tab图片加载失败**：
```vue
<image 
  :src="getImageSrc(tab.image_url)" 
  @error="(e) => e.target.src = '/static/default-image.png'"
  class="tab-image"
/>
```

### 5.6 网络状态监听

**ChatTab网络监听**：
```typescript
const isOnline = ref(true)
let refreshTimer: number | null = null

onMounted(async () => {
  await loadMessages()
  
  // 启动定时刷新
  startRefreshTimer()
  
  // 监听网络状态
  uni.onNetworkStatusChange((res) => {
    isOnline.value = res.isConnected
    
    if (res.isConnected) {
      // 网络恢复，重新加载并启动定时器
      loadMessages()
      startRefreshTimer()
    } else {
      // 网络断开，停止定时器
      stopRefreshTimer()
      uni.showToast({
        title: '网络已断开',
        icon: 'none'
      })
    }
  })
})

onUnmounted(() => {
  stopRefreshTimer()
})

const startRefreshTimer = () => {
  if (refreshTimer) return
  refreshTimer = setInterval(() => {
    if (isOnline.value) {
      loadMessages()
    }
  }, 5000)
}

const stopRefreshTimer = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}
```

### 5.7 性能优化规范

**1. 图片懒加载**：
```vue
<image 
  :src="getImageSrc(expert.avatar_url)" 
  lazy-load
  class="expert-avatar"
/>
```

**2. 防抖处理**（如果需要搜索功能）：
```typescript
import { ref } from 'vue'

// 简单的防抖函数
const debounce = (fn: Function, delay: number) => {
  let timer: number | null = null
  return function(...args: any[]) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

const handleSearch = debounce((keyword: string) => {
  // 搜索逻辑
}, 300)
```

**3. 缓存策略**：
```typescript
// 专家列表缓存（5分钟）
const CACHE_DURATION = 5 * 60 * 1000
const expertsCache = ref<{
  data: Expert[]
  timestamp: number
} | null>(null)

const loadExperts = async () => {
  // 检查缓存
  if (expertsCache.value) {
    const now = Date.now()
    if (now - expertsCache.value.timestamp < CACHE_DURATION) {
      experts.value = expertsCache.value.data
      return
    }
  }
  
  // 从API加载
  try {
    const { data } = await getRoomExperts(props.roomId)
    experts.value = data
    
    // 更新缓存
    expertsCache.value = {
      data,
      timestamp: Date.now()
    }
  } catch (error: any) {
    console.error('获取专家列表失败:', error)
    uni.showToast({
      title: error.message || '获取专家列表失败',
      icon: 'none'
    })
  }
}
```

**4. 列表分页加载**（ChatTab）：
```typescript
const currentPage = ref(1)
const hasMore = ref(true)
const isLoadingMore = ref(false)

const loadMore = async () => {
  if (!hasMore.value || isLoadingMore.value) return
  
  isLoadingMore.value = true
  currentPage.value++
  
  try {
    const { data } = await getRoomMessages(props.roomId, {
      page: currentPage.value,
      page_size: 20
    })
    
    // 将新消息添加到列表顶部（历史消息）
    messages.value = [...data.items, ...messages.value]
    hasMore.value = currentPage.value < data.pagination.total_pages
  } catch (error: any) {
    console.error('加载更多消息失败:', error)
    currentPage.value-- // 回退页码
  } finally {
    isLoadingMore.value = false
  }
}
```

```vue
<scroll-view 
  scroll-y 
  class="message-list"
  @scrolltoupper="loadMore"
>
  <view v-if="isLoadingMore" class="loading-more">
    <text>加载中...</text>
  </view>
  <view v-for="msg in messages" :key="msg.id" class="message-item">
    <!-- 消息内容 -->
  </view>
</scroll-view>
```

---

## 任务一：创建API封装

### 1.1 创建Tab API封装

**文件路径**：`src/api/tab.ts`

**必需方法**：
```typescript
// 获取直播间Tab列表
export const getRoomTabList = (roomId: string) => {
  return request<Tab[]>({
    url: `/admin/rooms/${roomId}/tabs`,
    method: 'GET'
  })
}

// 创建Tab
export const createRoomTab = (roomId: string, data: TabCreatePayload) => {
  return request<Tab>({
    url: `/admin/rooms/${roomId}/tabs`,
    method: 'POST',
    data
  })
}

// 更新Tab
export const updateRoomTab = (tabId: string, data: TabUpdatePayload) => {
  return request<Tab>({
    url: `/admin/tabs/${tabId}`,
    method: 'PATCH',
    data
  })
}

// 删除Tab
export const deleteRoomTab = (tabId: string) => {
  return request({
    url: `/admin/tabs/${tabId}`,
    method: 'DELETE'
  })
}

// 上传Tab图片
import { ENV_CONFIG } from '@/config/env'
import { getToken } from '@/utils/auth'

export const uploadTabImage = (roomId: string, filePath: string) => {
  return new Promise<string>((resolve, reject) => {
    uni.uploadFile({
      url: `${ENV_CONFIG.VITE_BASE_API_URL}/admin/rooms/${roomId}/tabs/image`,
      filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${getToken()}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          const data = JSON.parse(res.data)
          resolve(data.data.image_url)
        } else {
          reject(new Error('上传失败'))
        }
      },
      fail: reject
    })
  })
}
```

### 1.2 创建Message API封装

**文件路径**：`src/api/message.ts`

**必需方法**：
```typescript
// 发送留言
export const sendRoomMessage = (roomId: string, data: MessageCreatePayload) => {
  return request<Message>({
    url: `/rooms/${roomId}/messages`,
    method: 'POST',
    data
  })
}

// 获取留言列表
export const getRoomMessages = (
  roomId: string,
  params?: {
    page?: number
    page_size?: number
    status?: MessageStatus
  }
) => {
  return request<MessageListResponse>({
    url: `/rooms/${roomId}/messages`,
    method: 'GET',
    params
  })
}
```

### 1.3 补充Expert API

**文件路径**：`src/api/expert.ts`（已存在，需补充）

**需补充方法**：
```typescript
// 关联场次专家
export const associateSessionExperts = (sessionId: string, expertIds: string[]) => {
  return request({
    url: `/admin/sessions/${sessionId}/experts`,
    method: 'POST',
    data: { expert_ids: expertIds }
  })
}

// 获取房间专家
export const getRoomExperts = (roomId: string) => {
  return request<Expert[]>({
    url: `/rooms/${roomId}/experts`,
    method: 'GET'
  })
}
```

### 1.4 创建Brand API

**文件路径**：`src/api/brand.ts`（需新建）

**必需方法**：
```typescript
// 关联房间品牌
export const associateRoomBrands = (roomId: string, brandIds: string[]) => {
  return request({
    url: `/admin/rooms/${roomId}/brands`,
    method: 'POST',
    data: { brand_ids: brandIds }
  })
}

// 获取房间品牌
export const getRoomBrands = (roomId: string) => {
  return request<Brand[]>({
    url: `/rooms/${roomId}/brands`,
    method: 'GET'
  })
}
```

---

## 任务二：创建类型定义

### 2.1 创建Tab类型定义

**文件路径**：`src/types/tab.ts`

**必需类型**：
```typescript
// Tab内容类型
export type TabContentType = 'text' | 'image' | 'mixed'

// Tab信息
export interface Tab {
  id: string
  room_id: string
  tab_key: string
  title: string
  content_type: TabContentType
  text_content: string | null
  image_url: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 创建Tab请求
export interface TabCreatePayload {
  tab_key: string
  title: string
  content_type: TabContentType
  text_content?: string
  image_url?: string
  sort_order: number
  is_active?: boolean
}

// 更新Tab请求
export interface TabUpdatePayload {
  title?: string
  content_type?: TabContentType
  text_content?: string
  image_url?: string
  sort_order?: number
  is_active?: boolean
}
```

### 2.2 创建Message类型定义

**文件路径**：`src/types/message.ts`

**必需类型**：
```typescript
// 留言状态
export type MessageStatus = 'pending' | 'approved' | 'rejected'

// 留言信息
export interface Message {
  id: string
  room_id: string
  user_id: string
  content: string
  status: MessageStatus
  replied_by: string | null
  reply_content: string | null
  replied_at: string | null
  created_at: string
  extra?: {
    user_display_name?: string
    user_avatar?: string
  }
}

// 发送留言请求
export interface MessageCreatePayload {
  content: string
}

// 留言列表响应
export interface MessageListResponse {
  items: Message[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}
```

### 2.3 补充Brand类型定义

**文件路径**：`src/types/brand.ts`（需新建）

**必需类型**：
```typescript
// 品牌信息
export interface Brand {
  id: string
  name: string
  logo_url: string | null
  description: string | null
  website_url: string | null
  created_at: string
  updated_at: string
}
```

---

## 任务三：创建Tab组件

### 3.1 创建ContentTab组件

**文件路径**：`src/components/ContentTab.vue`

**功能说明**：
- 根据`content_type`渲染不同内容
- `text`：显示纯文字
- `image`：显示纯图片
- `mixed`：显示图文混合

**UI规范**：
```css
/* 文字内容 */
.text-content {
  padding: 32rpx;
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
}

/* 图片内容 */
.image-content {
  width: 100%;
  max-height: 800rpx;
}

/* 图文混合 */
.mixed-content {
  padding: 32rpx;
}

.text-part {
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
  margin-bottom: 24rpx;
}

.image-part {
  width: 100%;
  max-height: 800rpx;
  border-radius: 8rpx;
}
```

**完整代码示例**：
```vue
<template>
  <view class="content-tab">
    <!-- 纯文字 -->
    <view v-if="tab.content_type === 'text'" class="text-content">
      <text>{{ tab.text_content }}</text>
    </view>
    
    <!-- 纯图片 -->
    <image 
      v-else-if="tab.content_type === 'image'" 
      :src="getImageSrc(tab.image_url)" 
      @error="handleImageError"
      mode="widthFix"
      lazy-load
      class="image-content"
    />
    
    <!-- 图文混合 -->
    <view v-else-if="tab.content_type === 'mixed'" class="mixed-content">
      <view v-if="tab.text_content" class="text-part">
        <text>{{ tab.text_content }}</text>
      </view>
      <image 
        v-if="tab.image_url" 
        :src="getImageSrc(tab.image_url)" 
        @error="handleImageError"
        mode="widthFix"
        lazy-load
        class="image-part"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { getImageSrc } from '@/utils/image'
import type { Tab } from '@/types/tab'

interface Props {
  tab: Tab
}

defineProps<Props>()

// 图片加载失败处理
const handleImageError = (e: any) => {
  e.target.src = '/static/default-image.png'
}
</script>
```

### 3.2 创建ExpertsTab组件

**文件路径**：`src/components/ExpertsTab.vue`

**功能说明**：
- 显示专家列表（头像、姓名、职称、医院）
- 支持关注/取消关注
- 点击专家卡片跳转到专家详情页

**完整代码示例**：
```vue
<template>
  <view class="experts-tab">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <uni-loading type="circle" />
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 空态 -->
    <view v-else-if="experts.length === 0" class="empty-state">
      <image src="/static/empty.png" class="empty-icon" mode="widthFix" />
      <text class="empty-text">暂无专家信息</text>
    </view>
    
    <!-- 专家列表 -->
    <view v-else class="experts-list">
      <view 
        v-for="expert in experts" 
        :key="expert.id"
        class="expert-card"
        @tap="goToExpertDetail(expert.id)"
      >
        <image 
          :src="getImageSrc(expert.avatar_url)" 
          @error="handleImageError"
          lazy-load
          class="expert-avatar"
        />
        <view class="expert-info">
          <text class="expert-name">{{ expert.name }}</text>
          <text class="expert-title">{{ expert.title }}</text>
          <text class="expert-hospital">{{ expert.hospital }}</text>
        </view>
        <button 
          class="follow-btn"
          :class="{ 'followed': expert.is_followed }"
          @tap.stop="toggleFollow(expert)"
        >
          {{ expert.is_followed ? '已关注' : '关注' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getRoomExperts } from '@/api/expert'
import { followExpert, unfollowExpert } from '@/api/expertFollow'
import { getImageSrc } from '@/utils/image'
import type { Expert } from '@/types/expert'

interface Props {
  roomId: string
}

const props = defineProps<Props>()

const experts = ref<Expert[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await getRoomExperts(props.roomId)
    experts.value = data
  } catch (error: any) {
    console.error('获取专家列表失败:', error)
    uni.showToast({
      title: error.message || '获取专家列表失败',
      icon: 'none',
      duration: 2000
    })
  } finally {
    loading.value = false
  }
})

// 图片加载失败处理
const handleImageError = (e: any) => {
  e.target.src = '/static/default-avatar.png'
}

// 跳转到专家详情页
const goToExpertDetail = (expertId: string) => {
  uni.navigateTo({
    url: `/pages/expert/detail?id=${expertId}`
  })
}

// 切换关注状态
const toggleFollow = async (expert: Expert) => {
  try {
    if (expert.is_followed) {
      await unfollowExpert(expert.id)
      expert.is_followed = false
      uni.showToast({ title: '已取消关注', icon: 'success' })
    } else {
      await followExpert(expert.id)
      expert.is_followed = true
      uni.showToast({ title: '关注成功', icon: 'success' })
    }
  } catch (error: any) {
    console.error('关注操作失败:', error)
    uni.showToast({
      title: error.message || '操作失败，请重试',
      icon: 'none',
      duration: 2000
    })
  }
}
</script>
```

**UI规范**：
```css
.expert-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #fff;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.expert-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  margin-right: 24rpx;
}

.expert-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.expert-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.expert-title {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 4rpx;
}

.expert-hospital {
  font-size: 24rpx;
  color: #999;
}

.follow-btn {
  padding: 12rpx 32rpx;
  background: #1890ff;
  color: #fff;
  border-radius: 32rpx;
  font-size: 26rpx;
}

.follow-btn.followed {
  background: #f0f0f0;
  color: #666;
}
```

### 3.3 创建BrandsTab组件

**文件路径**：`src/components/BrandsTab.vue`

**功能说明**：
- 显示品牌列表（Logo、名称、简介）
- 点击品牌卡片跳转到品牌详情页

**完整代码示例**：
```vue
<template>
  <view class="brands-tab">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <uni-loading type="circle" />
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 空态 -->
    <view v-else-if="brands.length === 0" class="empty-state">
      <image src="/static/empty.png" class="empty-icon" mode="widthFix" />
      <text class="empty-text">暂无品牌信息</text>
    </view>
    
    <!-- 品牌列表 -->
    <view v-else class="brands-list">
      <view 
        v-for="brand in brands" 
        :key="brand.id"
        class="brand-card"
        @tap="goToBrandDetail(brand.id)"
      >
        <image 
          :src="getImageSrc(brand.logo_url)" 
          @error="handleImageError"
          lazy-load
          class="brand-logo"
        />
        <view class="brand-info">
          <text class="brand-name">{{ brand.name }}</text>
          <text class="brand-desc">{{ brand.description }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getRoomBrands } from '@/api/brand'
import { getImageSrc } from '@/utils/image'
import type { Brand } from '@/types/brand'

interface Props {
  roomId: string
}

const props = defineProps<Props>()

const brands = ref<Brand[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await getRoomBrands(props.roomId)
    brands.value = data
  } catch (error: any) {
    console.error('获取品牌列表失败:', error)
    uni.showToast({
      title: error.message || '获取品牌列表失败',
      icon: 'none',
      duration: 2000
    })
  } finally {
    loading.value = false
  }
})

// 图片加载失败处理
const handleImageError = (e: any) => {
  e.target.src = '/static/default-logo.png'
}

// 跳转到品牌详情页
const goToBrandDetail = (brandId: string) => {
  uni.navigateTo({
    url: `/pages/brand/detail?id=${brandId}`
  })
}
</script>
```

**UI规范**：
```css
.brand-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #fff;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.brand-logo {
  width: 96rpx;
  height: 96rpx;
  border-radius: 8rpx;
  margin-right: 24rpx;
}

.brand-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.brand-desc {
  font-size: 26rpx;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
```

### 3.4 创建ChatTab组件

**文件路径**：`src/components/ChatTab.vue`

**功能说明**：
- 显示历史消息列表（分页加载）
- 支持发送新消息
- 定时刷新消息列表（每5秒）

**完整代码示例**：
```vue
<template>
  <view class="chat-tab">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-state">
      <uni-loading type="circle" />
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 空态 -->
    <view v-else-if="messages.length === 0" class="empty-state">
      <image src="/static/empty.png" class="empty-icon" mode="widthFix" />
      <text class="empty-text">暂无聊天消息</text>
      <text class="empty-hint">快来发送第一条消息吧！</text>
    </view>
    
    <!-- 消息列表 -->
    <scroll-view 
      v-else
      scroll-y 
      :scroll-top="scrollTop"
      class="message-list"
      @scrolltoupper="loadMore"
    >
      <!-- 加载更多提示 -->
      <view v-if="isLoadingMore" class="loading-more">
        <text>加载中...</text>
      </view>
      <view v-else-if="!hasMore && messages.length > 0" class="no-more">
        <text>没有更多消息了</text>
      </view>
      
      <!-- 消息列表 -->
      <view 
        v-for="msg in messages" 
        :key="msg.id"
        class="message-item"
      >
        <image 
          :src="getImageSrc(msg.extra?.user_avatar)" 
          @error="handleAvatarError"
          lazy-load
          class="user-avatar"
        />
        <view class="message-content">
          <text class="user-name">{{ msg.extra?.user_display_name || '匿名用户' }}</text>
          <text class="message-text">{{ sanitizeContent(msg.content) }}</text>
          <text class="message-time">{{ formatTime(msg.created_at) }}</text>
        </view>
      </view>
    </scroll-view>
    
    <!-- 输入栏 -->
    <view class="input-bar">
      <input 
        v-model="inputText"
        class="message-input"
        placeholder="说点什么..."
        :maxlength="500"
        @confirm="handleSendMessage"
      />
      <button 
        class="send-btn"
        :disabled="!inputText.trim()"
        @tap="handleSendMessage"
      >
        发送
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getRoomMessages, sendRoomMessage } from '@/api/message'
import { getImageSrc } from '@/utils/image'
import { useUserStore } from '@/store/user'
import type { Message } from '@/types/message'

interface Props {
  roomId: string
}

const props = defineProps<Props>()

const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(true)
const scrollTop = ref(0)
const isOnline = ref(true)
const currentPage = ref(1)
const hasMore = ref(true)
const isLoadingMore = ref(false)
let refreshTimer: number | null = null

onMounted(async () => {
  await loadMessages()
  
  // 启动定时刷新
  startRefreshTimer()
  
  // 监听网络状态
  uni.onNetworkStatusChange((res) => {
    isOnline.value = res.isConnected
    
    if (res.isConnected) {
      // 网络恢复，重新加载并启动定时器
      loadMessages()
      startRefreshTimer()
    } else {
      // 网络断开，停止定时器
      stopRefreshTimer()
      uni.showToast({
        title: '网络已断开',
        icon: 'none'
      })
    }
  })
})

onUnmounted(() => {
  stopRefreshTimer()
})

// 启动定时器
const startRefreshTimer = () => {
  if (refreshTimer) return
  refreshTimer = setInterval(() => {
    if (isOnline.value) {
      loadMessages()
    }
  }, 5000)
}

// 停止定时器
const stopRefreshTimer = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 加载消息列表
const loadMessages = async () => {
  try {
    const { data } = await getRoomMessages(props.roomId, {
      page: 1,
      page_size: 50
    })
    messages.value = data.items
    currentPage.value = 1
    hasMore.value = data.pagination.total_pages > 1
  } catch (error: any) {
    console.error('获取消息失败:', error)
    // 首次加载失败才显示错误，刷新失败静默失败
    if (loading.value) {
      uni.showToast({
        title: error.message || '获取消息失败',
        icon: 'none',
        duration: 2000
      })
    }
  } finally {
    loading.value = false
  }
}

// 加载更多消息（分页）
const loadMore = async () => {
  if (!hasMore.value || isLoadingMore.value) return
  
  isLoadingMore.value = true
  currentPage.value++
  
  try {
    const { data } = await getRoomMessages(props.roomId, {
      page: currentPage.value,
      page_size: 20
    })
    
    // 将新消息添加到列表顶部（历史消息）
    messages.value = [...data.items, ...messages.value]
    hasMore.value = currentPage.value < data.pagination.total_pages
  } catch (error: any) {
    console.error('加载更多消息失败:', error)
    currentPage.value-- // 回退页码
  } finally {
    isLoadingMore.value = false
  }
}

// 发送消息（包含权限验证）
const handleSendMessage = async () => {
  if (!inputText.value.trim()) return
  
  // 权限验证
  const userStore = useUserStore()
  if (!userStore.isLoggedIn) {
    uni.showToast({
      title: '请先登录',
      icon: 'none',
      duration: 2000
    })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/index' })
    }, 1500)
    return
  }
  
  try {
    await sendRoomMessage(props.roomId, {
      content: inputText.value
    })
    inputText.value = ''
    await loadMessages()
    // 滚动到底部
    scrollTop.value = 99999
    uni.showToast({ title: '发送成功', icon: 'success' })
  } catch (error: any) {
    console.error('发送消息失败:', error)
    uni.showToast({
      title: error.message || '发送失败，请重试',
      icon: 'none',
      duration: 2000
    })
  }
}

// XSS防护：内容清理函数
const sanitizeContent = (content: string): string => {
  if (!content) return ''
  
  // 移除HTML标签
  let sanitized = content.replace(/<[^>]*>/g, '')
  
  // 转义特殊字符
  sanitized = sanitized
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
  
  return sanitized
}

// 图片加载失败处理
const handleAvatarError = (e: any) => {
  e.target.src = '/static/default-avatar.png'
}

// 时间格式化
const formatTime = (timeStr: string): string => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 超过24小时
  return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
}
</script>
```

**UI规范**：
```css
.chat-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.message-list {
  flex: 1;
  padding: 24rpx;
  overflow-y: auto;
}

.message-item {
  display: flex;
  margin-bottom: 24rpx;
}

.user-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  margin-right: 16rpx;
}

.message-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 8rpx;
}

.message-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  word-break: break-all;
}

.input-bar {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f5f5f5;
  border-top: 1rpx solid #e5e5e5;
}

.message-input {
  flex: 1;
  padding: 16rpx 24rpx;
  background: #fff;
  border-radius: 32rpx;
  font-size: 28rpx;
}

.send-btn {
  margin-left: 16rpx;
  padding: 16rpx 32rpx;
  background: #1890ff;
  color: #fff;
  border-radius: 32rpx;
  font-size: 28rpx;
}
```

---

## 任务四：修改LiveView.vue

### 4.1 修改范围

**需要修改的部分**：
- ✅ Tab获取逻辑：从后端API动态获取Tab列表
- ✅ Tab渲染逻辑：根据tab_key判断渲染哪种组件
- ✅ 导入新组件：ContentTab、ExpertsTab、BrandsTab、ChatTab

**需要保留的部分**：
- ✅ 播放器区域（VideoPlayerApp组件）
- ✅ 顶部信息栏（头像、标题、分享按钮）
- ✅ Tab导航栏UI（蓝色下划线指示器）
- ✅ 其他现有功能（收藏、订阅、观看历史等）

### 4.2 核心修改逻辑

**获取Tab列表（包含降级方案）**：
```typescript
import { ref, computed, onMounted } from 'vue'
import { getRoomDetail } from '@/api/room'
import type { Tab } from '@/types/tab'

const allTabs = ref<Tab[]>([])
const currentTabKey = ref('intro')
const isUsingFallback = ref(false)

// 备用的硬编码Tab（仅当API调用失败时使用）
const fallbackTabs: Tab[] = [
  {
    id: 'fallback-intro',
    room_id: roomId.value,
    tab_key: 'intro',
    title: '直播介绍',
    content_type: 'text',
    text_content: '正在加载直播介绍...',
    image_url: null,
    sort_order: 1,
    is_active: true,
    created_at: '',
    updated_at: ''
  },
  {
    id: 'fallback-chat',
    room_id: roomId.value,
    tab_key: 'chat',
    title: '聊天',
    content_type: 'text',
    text_content: '',
    image_url: null,
    sort_order: 10,
    is_active: true,
    created_at: '',
    updated_at: ''
  }
]

onMounted(async () => {
  try {
    // 获取房间详情（包含Tab列表）
    const { data } = await getRoomDetail(roomId.value)
    
    if (data.tabs && data.tabs.length > 0) {
      allTabs.value = data.tabs
      isUsingFallback.value = false
    } else {
      // 如果后端返回空Tab列表，使用备用Tab
      allTabs.value = fallbackTabs
      isUsingFallback.value = true
      console.warn('后端返回空Tab列表，使用备用Tab')
    }
    
    // 默认选中第一个Tab
    if (allTabs.value.length > 0) {
      currentTabKey.value = allTabs.value[0].tab_key
    }
  } catch (error: any) {
    console.error('获取Tab列表失败:', error)
    
    // API调用失败，使用备用Tab
    allTabs.value = fallbackTabs
    isUsingFallback.value = true
    currentTabKey.value = 'intro'
    
    uni.showToast({
      title: '加载Tab失败，使用默认Tab',
      icon: 'none',
      duration: 2000
    })
  }
})

// 当前选中的Tab
const currentTab = computed(() => {
  return allTabs.value.find(tab => tab.tab_key === currentTabKey.value)
})
```

**降级方案说明**：

1. **方案A：直接替换为动态Tab（推荐）**
   - 完全依赖后端API返回Tab列表
   - 如果API调用失败，使用备用的硬编码Tab（仅包含“直播介绍”和“聊天”）
   - 优点：逻辑清晰，易于维护
   - 缺点：API失败时功能受限

2. **方案B：API调用失败时降级使用硬编码Tab（备选）**
   - 上述代码已实现此方案
   - 优点：即使后端故障，用户仍能使用基本功能
   - 缺点：需要维护两套Tab逻辑

**当前采用：方案B（带降级）**

**Tab渲染逻辑**：
```vue
<template>
  <view class="live-view">
    <!-- 播放器区域（保留） -->
    <VideoPlayerApp :session="session" />
    
    <!-- 顶部信息栏（保留） -->
    <view class="info-bar">
      <!-- ... 现有代码 ... -->
    </view>
    
    <!-- Tab导航（修改） -->
    <scroll-view scroll-x class="tab-nav">
      <view 
        v-for="tab in allTabs" 
        :key="tab.id"
        class="tab-item"
        :class="{ 'active': currentTabKey === tab.tab_key }"
        @tap="currentTabKey = tab.tab_key"
      >
        {{ tab.title }}
      </view>
    </scroll-view>
    
    <!-- Tab内容（修改） -->
    <view class="tab-content">
      <!-- 专家介绍Tab -->
      <ExpertsTab 
        v-if="currentTab?.tab_key === 'experts'"
        :room-id="roomId"
      />
      
      <!-- 品牌介绍Tab -->
      <BrandsTab 
        v-else-if="currentTab?.tab_key === 'brands'"
        :room-id="roomId"
      />
      
      <!-- 聊天Tab -->
      <ChatTab 
        v-else-if="currentTab?.tab_key === 'chat'"
        :room-id="roomId"
      />
      
      <!-- 其他Tab（内容型） -->
      <ContentTab 
        v-else-if="currentTab"
        :tab="currentTab"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getRoomDetail } from '@/api/room'
import ContentTab from '@/components/ContentTab.vue'
import ExpertsTab from '@/components/ExpertsTab.vue'
import BrandsTab from '@/components/BrandsTab.vue'
import ChatTab from '@/components/ChatTab.vue'

// 当前选中的Tab
const currentTab = computed(() => {
  return allTabs.value.find(tab => tab.tab_key === currentTabKey.value)
})
</script>
```

---

## 任务五：修改创建直播页面

### 5.1 修改范围

**需要修改的部分**：
- ✅ 创建房间后自动创建Tab
- ✅ 直播介绍Tab（始终创建）
- ✅ 专家介绍Tab（选择了专家时创建）
- ✅ 品牌介绍Tab（选择了品牌时创建）
- ✅ 聊天Tab（移动端自动创建）

**需要保留的部分**：
- ✅ 现有表单字段
- ✅ 现有创建流程
- ✅ 现有UI布局

### 5.2 核心修改逻辑

**创建Tab的时机**：
```typescript
const handleCreate = async () => {
  try {
    uni.showLoading({ title: '创建中...' })
    
    // 1. 创建房间
    const room = await roomStore.addNewRoom({
      title: formData.value.title,
      description: formData.value.description,
      category_id: formData.value.category_id,
      is_private: formData.value.is_private
    })
    const roomId = room.id
    
    // 2. 上传封面（如果有）
    if (formData.value.cover_local_path) {
      await uploadRoomCover(roomId, formData.value.cover_local_path)
    }
    
    // 3. 创建"直播介绍"Tab（始终创建）
    await createRoomTab(roomId, {
      tab_key: 'intro',
      title: '直播介绍',
      content_type: formData.value.description_images.length > 0 ? 'mixed' : 'text',
      text_content: formData.value.description || '',
      image_url: formData.value.description_images[0] || null,
      sort_order: 1,
      is_active: true
    })
    
    // 4. 创建"专家介绍"Tab（如果选择了专家）
    if (formData.value.selectedExperts.length > 0) {
      await createRoomTab(roomId, {
        tab_key: 'experts',
        title: '专家介绍',
        content_type: 'text',
        text_content: '',
        image_url: null,
        sort_order: 2,
        is_active: true
      })
    }
    
    // 5. 创建"品牌介绍"Tab（如果选择了品牌）
    if (formData.value.selectedBrands.length > 0) {
      await createRoomTab(roomId, {
        tab_key: 'brands',
        title: '品牌介绍',
        content_type: 'mixed',
        text_content: '',
        image_url: null,
        sort_order: 3,
        is_active: true
      })
    }
    
    // 6. 创建"聊天"Tab（移动端自动创建）
    // #ifdef APP-PLUS
    await createRoomTab(roomId, {
      tab_key: 'chat',
      title: '聊天',
      content_type: 'text',
      text_content: '',
      image_url: null,
      sort_order: 10,
      is_active: true
    })
    // #endif
    
    // 7. 创建场次
    const session = await sessionStore.createSession({
      room_id: roomId,
      title: formData.value.title,
      description: formData.value.description,
      start_time: formData.value.start_time,
      status: formData.value.playback_url ? 'ready' : 'scheduled'
    })
    
    // 8. 关联专家
    if (formData.value.selectedExperts.length > 0) {
      await associateSessionExperts(session.id, formData.value.selectedExperts)
    }
    
    // 9. 关联品牌
    if (formData.value.selectedBrands.length > 0) {
      await associateRoomBrands(roomId, formData.value.selectedBrands)
    }
    
    // 10. 设置回放地址（如果有）
    if (formData.value.playback_url) {
      await sessionStore.updateSession(session.id, {
        playback_url: formData.value.playback_url
      })
    }
    
    uni.hideLoading()
    uni.showToast({
      title: '创建成功',
      icon: 'success'
    })
    
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
    
  } catch (error) {
    uni.hideLoading()
    console.error('创建直播失败', error)
    uni.showToast({
      title: error.message || '创建失败',
      icon: 'none'
    })
  }
}
```

---

## 第6章：关键实现要点 Checklist

### API封装
- [ ] **Tab API**：创建、获取、更新、删除、上传图片
  - [ ] 使用 `ENV_CONFIG.VITE_BASE_API_URL` 上传图片
  - [ ] 所有API路径不带 `/api/v1` 前缀
- [ ] **Message API**：发送留言、获取留言列表
  - [ ] 支持分页加载
- [ ] **Expert API**：补充关联API、获取房间专家
  - [ ] 检查是否已存在同名方法
- [ ] **Brand API**：创建关联API、获取房间品牌

### 类型定义
- [ ] **Tab类型**：Tab、TabCreatePayload、TabUpdatePayload
- [ ] **Message类型**：Message、MessageCreatePayload、MessageListResponse
- [ ] **Brand类型**：Brand

### 组件开发
- [ ] **ContentTab**：支持text/image/mixed三种类型
  - [ ] 完整的导入语句
  - [ ] 图片加载失败处理
  - [ ] 图片懒加载
- [ ] **ExpertsTab**：显示专家列表、支持关注、跳转
  - [ ] 完整的导入语句
  - [ ] 空态处理（loading + empty）
  - [ ] 图片加载失败处理
  - [ ] 错误处理（显示给用户）
  - [ ] 缓存策略（5分钟）
- [ ] **BrandsTab**：显示品牌列表、支持跳转
  - [ ] 完整的导入语句
  - [ ] 空态处理（loading + empty）
  - [ ] 图片加载失败处理
  - [ ] 错误处理（显示给用户）
  - [ ] 缓存策略（5分钟）
- [ ] **ChatTab**：显示历史消息、支持发送、定时刷新
  - [ ] 完整的导入语句
  - [ ] 空态处理（loading + empty）
  - [ ] 分页加载（上拉加载更多）
  - [ ] 网络状态监听
  - [ ] 定时器清理（onUnmounted）
  - [ ] 权限验证（发送前检查登录）
  - [ ] XSS防护（sanitizeContent）
  - [ ] 时间格式化（相对时间）
  - [ ] 图片加载失败处理

### 播放页修改
- [ ] **Tab获取**：从后端API动态获取Tab列表
  - [ ] 实现降级方案（API失败时使用备用Tab）
  - [ ] 错误处理（显示给用户）
- [ ] **Tab渲染**：根据tab_key判断渲染哪种组件
  - [ ] 导入所有Tab组件
  - [ ] 使用computed计算currentTab
- [ ] **UI一致性**：保持现有UI风格（蓝色下划线指示器）
- [ ] **功能保留**：不破坏现有功能（播放器、收藏、订阅等）

### 创建直播页修改
- [ ] **直播介绍Tab**：始终创建
- [ ] **专家介绍Tab**：选择了专家时创建
- [ ] **品牌介绍Tab**：选择了品牌时创建
- [ ] **聊天Tab**：移动端自动创建
- [ ] **关联逻辑**：关联专家和品牌

### 错误处理
- [ ] **API调用**：所有API调用都要有try-catch包装
- [ ] **用户反馈**：所有错误都要显示给用户
  - [ ] 使用 `uni.showToast` 显示错误
  - [ ] 错误信息包含操作名称和原因
- [ ] **错误信息**：错误信息要具体明确
  - [ ] 使用 `error.message || '默认错误信息'`
- [ ] **流程控制**：关键步骤失败时要提前返回
- [ ] **控制台日志**：所有错误都要记录到控制台

### 安全性
- [ ] **XSS防护**：聊天内容使用sanitizeContent清理
- [ ] **权限验证**：
  - [ ] 创建Tab需要Admin权限
  - [ ] 发送留言需要登录
  - [ ] 查看私有房间需要权限
- [ ] **图片加载失败**：所有图片都要处理@error事件
- [ ] **网络状态**：ChatTab监听uni.onNetworkStatusChange

### 用户体验
- [ ] **空态处理**：所有列表组件都要处理空态
  - [ ] 显示加载状态（loading）
  - [ ] 显示空态图标和提示文案
  - [ ] 提供刷新按钮
- [ ] **加载状态**：显示加载中提示
- [ ] **成功反馈**：操作成功后显示成功提示

### 性能优化
- [ ] **定时器清理**：组件卸载时清理定时器
- [ ] **分页加载**：聊天消息支持分页加载
  - [ ] 上拉加载更多
  - [ ] 加载更多提示
  - [ ] 没有更多提示
- [ ] **图片懒加载**：所有图片都使用lazy-load属性
- [ ] **缓存策略**：
  - [ ] 专家列表缓存5分钟
  - [ ] 品牌列表缓存5分钟
  - [ ] 聊天消息不缓存
- [ ] **防抖处理**：搜索功能使用防抖（如果需要）

---

## 第7章：测试验证

### 7.1 功能测试

**创建直播测试**：
- ✅ 只有直播简介：检查是否创建了"直播介绍"Tab
- ✅ 关联了专家：检查是否创建了"专家介绍"Tab
- ✅ 关联了品牌：检查是否创建了"品牌介绍"Tab
- ✅ 同时关联专家和品牌：检查是否创建了所有Tab

**播放页测试**：
- ✅ Tab列表正确显示：检查Tab导航是否正确显示
- ✅ 内容型Tab：检查直播介绍Tab是否正确显示内容
- ✅ 专家Tab：检查专家列表、关注功能、跳转功能
- ✅ 品牌Tab：检查品牌列表、跳转功能
- ✅ 聊天Tab：检查历史消息、发送消息、定时刷新

**管理员新增Tab测试**：
- ✅ 管理页面新增Tab：检查播放页是否正确显示新增的Tab

### 7.2 错误处理测试

**网络错误**：
- ✅ API调用失败：检查是否显示错误提示
- ✅ 超时错误：检查是否显示超时提示

**数据异常**：
- ✅ Tab列表为空：检查是否显示空态提示
- ✅ 专家列表为空：检查是否显示空态提示
- ✅ 聊天消息为空：检查是否显示空态提示

---

## 第8章：注意事项

### 8.1 安全性

- ✅ **API鉴权**：所有API调用都要携带JWT Token
- ✅ **权限验证**：创建Tab需要Admin权限
- ✅ **输入验证**：聊天消息内容需要验证长度和格式

### 8.2 兼容性

- ✅ **仅修改APP端**：H5端保持不变
- ✅ **条件编译**：使用`#ifdef APP-PLUS`区分平台

### 8.3 性能

- ✅ **定时器清理**：组件卸载时清理定时器
- ✅ **分页加载**：聊天消息支持分页加载
- ✅ **图片懒加载**：使用uni-app的图片懒加载

### 8.4 用户体验

- ✅ **加载状态**：显示加载中提示
- ✅ **错误提示**：显示具体的错误信息
- ✅ **成功反馈**：操作成功后显示成功提示

---

## 第9章：后续优化

### 9.1 管理员新增Tab功能

- ⏳ 在管理页面添加"新增Tab"功能
- ⏳ 支持创建自定义Tab
- ⏳ 支持上传Tab图片
- ⏳ 支持编辑和删除Tab

### 9.2 WebSocket实时聊天

- ⏳ 使用WebSocket替代定时轮询
- ⏳ 实时推送新消息
- ⏳ 显示在线人数

### 9.3 资料下载Tab

- ⏳ 等待后端API实现
- ⏳ 创建MaterialsTab组件
- ⏳ 支持资料列表显示和下载

---

## 第10章：开始开发

**在开始开发前，请务必执行第0章的强制性前置检查！**

1. 读取现有核心文件
2. 扫描目录结构
3. 输出项目现状分析
4. 等待用户确认

**确认后，按照以下顺序开始开发：**

1. 创建API封装（tab.ts、message.ts、brand.ts）
2. 创建类型定义（tab.ts、message.ts）
3. 创建Tab组件（ContentTab、ExpertsTab、BrandsTab、ChatTab）
4. 修改LiveView.vue
5. 修改create.vue
6. 测试验证

**祝开发顺利！** 🚀
