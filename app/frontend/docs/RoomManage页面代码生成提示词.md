# 阶段三：RoomManage代码生成提示词 (Element Plus版)

## 角色与目标

你是一名资深前端重构工程师，**精通 Element Plus** 并对UI细节有像素级要求。我有一个已经可以完整运行的前端项目，其核心功能和业务逻辑（API请求、状态管理、数据处理）已经全部实现。

你的核心任务是**"新建页面开发"**，即根据我提供的最新设计文档（`@前端分析及设计文档.md`），为项目构建一个全新的、基于 Element Plus 的UI视图层。**注意：这是一个全新的页面，需要从零开始开发**。

## 页面功能范围说明

### 本期实现功能
- **基本设置**: 点击可跳转到基本设置子页面，用于编辑房间基本信息
- **多会场直播**: 点击可跳转到多会场管理子页面，用于管理分会场

### 暂缓实现功能
- 其他所有功能卡片（观看页设置、广告设置、订阅设置、私域引流、多语言直播、内容安全、其他等）均为静态占位，点击时显示"功能待开发，敬请期待"

## API需求说明

### 必需API
- **获取房间详情**: `GET /api/v1/rooms/{room_id}` - 用于加载房间基本信息、状态、封面等数据
- **获取房间场次列表（用于取最近一条场次信息）**: `GET /api/v1/rooms/{room_id}/sessions?page=1&size=10`
  - 用途：在页面中展示“最近场次”的 `status` 与 `start_time`
  - 说明：后端时间可能返回形如 `2025-09-28T07:16:42.474000+00:00Z` 的字符串。前端需要在格式化前做一次“清洗”：
    1) 去掉微秒部分（`.\d{6}`） 2) 将尾部 `+00:00Z` 规范化为 `Z`，再用 `dayjs(cleaned).format('YYYY-MM-DD HH:mm:ss')`

### 暂缓API
- 其他功能相关的API接口暂不实现

## 核心原则

1.  **[最高准则] UI组件库**: **所有UI元素必须使用 Element Plus 组件库进行构建**。禁止使用原生的HTML标签（如 `<table>`, `<button>`）来模拟复杂组件。你的目标是生成语义化、符合 Element Plus 最佳实践的代码。
2.  **逻辑复用，视图替换**: 这是我们工作的最高原则。所有API请求、状态管理（Pinia/Vuex）、数据处理等逻辑都必须保留。你只负责重写页面的 `<template>` 部分，并调整 `<script>` 以适配 Element Plus 的数据绑定。
3.  **新建页面开发**: 这是一个全新的页面，需要创建完整的业务逻辑，包括数据获取、状态管理、事件处理等。
4.  **API集成**: 需要集成现有的房间详情API接口，实现数据加载和状态管理。

---

## 任务一：创建房间管理布局组件 (RoomManageLayout)

**文件路径**: `/src/layouts/RoomManageLayout.vue`

### 1. 布局结构 (`<template>`)

请使用 Element Plus 的 `<el-container>` 组件来构建**三栏布局**（Left, Right, Main），**注意：此页面采用双侧边栏设计**，并精确复刻所有UI元素：

1.  **左侧主导航栏 (`<el-aside>`)**: 
     *   **属性**: `width: 220px`, `background: '#f8f9fa'`, `overflow-y: auto` (支持垂直滚动)。
     *   **顶部返回按钮**: 使用 `<el-button type="text" :icon="ArrowLeft">` 显示"返回话题列表"。
     *   **常用功能区域**: 使用 `<el-card>` 包裹，标题为"常用功能"，包含"推荐"标签和星形图标。
         *   `设置首页` (高亮选中状态，蓝色背景)
     *   **主菜单**: 使用 `<el-menu>` 渲染主要功能模块，支持垂直滚动。严格按照以下顺序，并为每个菜单项指定精确的 Icon：
         *   `基本信息` (Icon: `Document`, 当前选中高亮)
         *   `直播互动` (Icon: `ChatDotRound`)
         *   `直播营销` (Icon: `Promotion`)
         *   `数据分析` (Icon: `TrendCharts`)
         *   `直播装修` (Icon: `Star`)
         *   `开播设置` (Icon: `VideoCamera`)
         *   `内容总结` (Icon: `DocumentCopy`)
         *   `营销自动化` (Icon: `MagicStick`)

2.  **右侧详细功能栏 (`<el-aside>`)**: 
     *   **属性**: `width: 200px`, `background: '#ffffff'`, `overflow-y: auto` (支持垂直滚动)。
     *   **功能**: 这是"基本信息"下的详细功能列表，支持垂直滚动，包含以下功能项：
         *   `设置首页` (当前选中高亮，蓝色背景)
         *   `基本设置` (可展开/折叠，包含子项) - **本期实现，可点击跳转**
             *   `基本设置` (子项)
             *   `观看页设置` (静态占位)
             *   `广告设置` (静态占位)
             *   `订阅设置` (静态占位)
             *   `私域引流` (静态占位)
         *   `直播方式` (可展开/折叠，包含子项)
             *   `多会场直播` - **本期实现，可点击跳转**
             *   `多语言直播` (静态占位)
         *   `内容安全` (可展开/折叠，包含子项)
             *   `白名单` (静态占位)
             *   `跑马灯` (静态占位)
         *  `其他` (可展开/折叠，包含子项)
             *   `进入弹窗` (静态占位)
             *   `推荐话题` (静态占位)
             *   `页面跳转` (静态占位)
             *   `智能字幕` (静态占位)
             *   `管理员设置` (静态占位) 

3.  **主内容区 (`<el-main>`)**: 
     *   **样式**: `padding: 24px`, `background: '#ffffff'`。
     *   **顶部操作栏**: 位于主内容区顶部，包含：
         *   右侧功能按钮组：`中控台`(带NEW标签), `推送`, `预览`, `帮助`, `下载`
         *   主要操作按钮：`分享` (蓝色主按钮)
         *   用户头像：`<el-avatar>` 组件
     *   请在此处使用 `<slot />` 标签作为页面内容的占位符。

### 2. 逻辑与样式

*   **逻辑**: 
    *   左侧主导航：在 `<el-menu>` 中设置 `default-active` 属性来确保当前选中的菜单项高亮显示。
    *   右侧详细功能栏：根据左侧选中的主菜单项，动态显示对应的详细功能列表。
    *   当用户点击左侧的"基本信息"时，右侧显示基本信息相关的详细功能，包括设置首页、基本设置、观看页设置、广告设置、订阅设置、私域引流、直播方式、内容安全等。
    *   右侧功能项支持展开/折叠功能，如"基本设置"、"直播方式"、"内容安全"等分组。
*   **样式**: 使用 `<style scoped>`。左侧栏使用浅色背景，右侧栏使用白色背景，主内容区使用白色背景，确保视觉层次清晰。

---

## 任务二：重构 RoomManage 页面

**文件路径**: `/pages/room/new/RoomManage.vue`

### 1. 页面布局 (`<template>`)

1.  **使用全局布局**: 整个页面的根组件应该是 `RoomManageLayout`。

2.  **内容区结构**: 在 `RoomManageLayout` 的插槽内部，使用 `<el-space direction="vertical" size="large" style="width: 100%">` 作为主容器，并按顺序放置以下 Element Plus 组件：

    *   **直播房间信息区（固定尺寸）**: 使用 `<el-card>` 包裹，内部使用 `<el-row :gutter="24">` 布局。
        *   **固定尺寸要求（重要）**：
            - 外层 `<el-card>` 固定高度：`height: 220px`，固定宽度：`100%`（随容器宽度）
            - 左右内容区在该固定高度内垂直居中，超出内容隐藏（`overflow: hidden`）
            - 右侧封面预览固定尺寸：`width: 180px; height: 120px;`，`fit="cover"`
        *   **左侧区域** (`<el-col :span="16">`): 
            *   使用 `<el-breadcrumb>` 渲染返回面包屑导航。
            *   使用 `<el-typography>` 的 `<h2>` 渲染直播名称（长标题使用 `<el-tooltip>` 处理）。
            *   使用 `<el-space>` 包含多个 `<el-tag>` 显示状态、观看方式、类型标签。
            *   使用 `<el-text>` 显示“最近场次开始时间”（来自 sessions 的最近一条），格式为 `YYYY-MM-DD HH:mm:ss`。
        *   **右侧区域** (`<el-col :span="8">`): 
            *   使用 `<el-image>` 显示封面预览，添加角标显示状态。

    *   **直播房间预览卡片**: 使用 `<el-card>` 创建大型预览卡片：
        *   **背景**: 使用渐变背景（橙色到白色），包含城市天际线剪影。
        *   **内容**: 
            *   状态标签：`<el-tag type="success">未开始`
            *   机构名称：`NCRC 国家骨科与运动康复临床医学研究中心`
            *   主标题：`2025年北京康复医学会 青年工作委员会第三十七期文献导读`
            *   直播时间：`直播时间: 9月28日 (周日) 19:00`

    *   **直播设置信息区**: 使用 `<el-card>` 显示当前设置：
        *   **直播类型**: 显示"横屏直播"和"通用"标签
        *   **观看限制**: 显示"公开"标签
        *   **开播时间**: 显示时间设置和"开播"按钮

    *   **功能卡片网格区**: 使用 `<el-row :gutter="16">` 构建网格布局，分为多个区块：
        *   **基本设置区块** (`<el-col :span="6">`): 使用 `<el-card>` 包含以下卡片：
            *   `基本设置` (必须实现，Icon: `Setting`)
            *   `观看页设置` (静态占位，Icon: `View`)
            *   `广告设置` (静态占位，Icon: `Promotion`)
            *   `订阅设置` (静态占位，Icon: `Bell`)
            *   `私域引流` (静态占位，Icon: `Share`)
        *   **直播方式区块** (`<el-col :span="6">`): 使用 `<el-card>` 包含以下卡片：
            *   `多会场直播` (必须实现，Icon: `Platform`, 右侧"进入"按钮)
            *   `多语言直播` (静态占位，Icon: `Translation`)
        *   **内容安全区块** (`<el-col :span="6">`): 使用 `<el-card>` 包含以下卡片：
            *   `白名单` (静态占位，Icon: `User`)
            *   `跑马灯` (静态占位，Icon: `ChatLineRound`)
        *   **其他区块** (`<el-col :span="6">`): 使用 `<el-card>` 包含以下卡片：
            *   `进入弹窗` (静态占位，Icon: `FullScreen`)
            *   `推荐话题` (静态占位，Icon: `ChatDotSquare`)
            *   `页面跳转` (静态占位，Icon: `Link`)
            *   `智能字幕` (静态占位，Icon: `Document`)
            *   `管理员设置` (静态占位，Icon: `UserFilled`)

### 2. 逻辑绑定 (`<script setup>`)

*   **导入组件与工具**: 确保导入了 `RoomManageLayout`、所有需要的 Element Plus 组件及 Icon、`ElMessage`，以及 `useSessionStore`（或 `getSessionList` API）。
*   **数据获取**: 
    - 创建 `useRoomDetail` 钩子获取房间详情：`GET /api/v1/rooms/{room_id}`。
    - 并行/串行获取“最近场次”：`GET /api/v1/rooms/{room_id}/sessions?page=1&size=10`，在前端按 `start_time` 降序排序后取第一条。
    - 将最近场次的 `status` 与 `start_time` 映射到页面展示区（左侧标签与时间文本）。
*   **状态管理**: 使用 Pinia store 管理房间状态，包括 `roomDetail` (房间详情数据), `loading`, `error` 等。
*   **事件处理**: 需要实现 `handleEnterLive`, `handleBasicSettings`, `handleMultiVenue` 等事件处理函数。
*   **适配 Element Plus**: 
    *   **直播房间信息区**: 
        *   使用 `<el-tooltip>` 处理长标题的显示。
        *   使用 `<el-tag>` 根据“最近场次”的状态值显示不同 `type`（`success`, `warning`, `info`）。
        *   时间格式化：对 `start_time` 先做“清洗”（去微秒、规范化 `+00:00Z` 为 `Z`），再 `dayjs(cleaned).format('YYYY-MM-DD HH:mm:ss')`。
        *   封面图片使用 `<el-image>` 的 `fit="cover"` 属性。
    *   **预览卡片**: 
        *   使用渐变背景样式，包含城市天际线剪影。
        *   状态标签使用 `<el-tag type="success">` 显示。
        *   机构名称和主标题使用不同的字体大小和颜色。
        *   直播时间使用特定格式显示。
    *   **直播设置信息区**: 
        *   使用 `<el-tag>` 显示直播类型和观看限制。
        *   时间设置使用 `<el-time-picker>` 组件。
        *   "开播"按钮使用 `<el-button type="primary">`。
    *   **功能卡片**: 
        *   每个卡片使用 `<el-card>` 组件，设置 `hover` 效果。
        *   卡片内容使用 `<el-space>` 布局，包含图标、标题和描述。
        *   对于"必须实现"的卡片，绑定真实的点击事件。
        *   对于"静态占位"的卡片，绑定统一的提示函数。
*   **功能实现**: 
    *   **基本设置**: 点击跳转到 `/pages/room/new/RoomBasicSettings?room_id={id}` 页面
    *   **多会场直播**: 点击跳转到 `/pages/room/new/RoomMultiVenue?room_id={id}` 页面
    *   **其他功能**: 点击时显示 `ElMessage.info('功能待开发，敬请期待')` 提示
*   **滚动支持**: 两个侧边栏都需要支持垂直滚动，当内容超出容器高度时显示滚动条。

---

## 任务三：创建基本设置子页面

**文件路径**: `/pages/room/new/RoomBasicSettings.vue`

### 1. 页面布局 (`<template>`)

1.  **使用全局布局**: 整个页面的根组件应该是 `RoomManageLayout`。

2.  **内容区结构**: 在 `RoomManageLayout` 的插槽内部，使用 `<el-card>` 作为主容器：

    *   **页面标题**: 使用 `<el-page-header>` 显示"基本设置"标题和返回按钮。
    *   **表单区域**: 使用 `<el-form>` 构建编辑表单，包含以下字段：
        *   `直播名称`: `<el-input>` 组件，必填校验。
        *   `直播封面`: `<el-upload>` 组件，支持图片上传和预览。
        *   `观看方式`: `<el-radio-group>` 组件，选项为"公开"和"加密"。
        *   `直播描述`: `<el-input type="textarea">` 组件，可选字段。
    *   **操作按钮**: 使用 `<el-space>` 包含"取消"和"保存"按钮。

### 2. 逻辑绑定 (`<script setup>`)

*   **表单验证**: 使用 Element Plus 的表单验证规则。
*   **图片上传**: 集成图片上传功能，上传成功后更新封面URL。
*   **数据提交**: 调用更新房间详情的API接口。

---

## 关键实现要点

### 1. 数据流设计
- **房间详情加载**: 根据路由参数 `room_id` 获取房间详情数据
- **状态管理**: 使用 Pinia store 管理房间状态和操作
- **实时更新**: 支持房间信息的实时更新和状态同步

### 2. 路由设计
- **主页面**: `/pages/room/new/RoomManage?room_id={id}`
- **基本设置**: `/pages/room/new/RoomBasicSettings?room_id={id}`
- **多会场管理**: `/pages/room/new/RoomMultiVenue?room_id={id}`

### 3. 组件复用
- **布局组件**: 创建专用的 `RoomManageLayout` 布局组件
- **卡片组件**: 创建可复用的功能卡片组件
- **表单组件**: 创建可复用的编辑表单组件

### 4. 交互设计
- **状态反馈**: 所有操作都有明确的成功/失败反馈
- **加载状态**: 数据加载时显示 loading 状态
- **错误处理**: 网络错误和数据错误的友好提示
- **滚动支持**: 双侧边栏支持垂直滚动

### 5. API集成
- **必需API**:
  - `GET /api/v1/rooms/{room_id}` - 获取房间详情
  - `GET /api/v1/rooms/{room_id}/sessions?page=1&size=10` - 获取场次列表（取最近一条用于展示）
- **数据字段**: 
  - 房间详情：`id`, `title`, `description`, `cover_url`, `is_private` 等
  - 场次：`id`, `room_id`, `status`（`scheduled|live|ended|archived`）, `start_time`（注意清洗格式后再展示）

---

请根据以上详细要求，依次生成 `RoomManageLayout.vue`、`RoomManage.vue`、`RoomBasicSettings.vue` 的完整文件代码。
