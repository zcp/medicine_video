# 阶段三：MultiVenueManage代码生成提示词 (Element Plus版)

## 角色与目标

你是一名资深前端重构工程师，**精通 Element Plus** 并对UI细节有像素级要求。我有一个已经可以完整运行的前端项目，其核心功能和业务逻辑（API请求、状态管理、数据处理）已经全部实现。

你的核心任务是**"新建页面开发"**，即根据我提供的最新设计文档（`@前端分析及设计文档.md`），为项目构建一个全新的、基于 Element Plus 的UI视图层。**注意：这是一个全新的页面，需要从零开始开发**。

## 页面功能范围说明

### 本期实现功能
- **添加分会场**: 点击按钮弹出"添加多会场"弹窗，包含分会场名称、直播时间等表单字段
- **分会场列表**: 动态加载并渲染分会场数据表格，包含封面、名称、ID、直播时间、状态、排序、操作等列
- **分页功能**: 支持分页切换和每页条数设置

### 暂缓实现功能
- **封面上传功能**: 分会场封面上传（后端未实现，仅静态复刻UI）
- **回放设置功能**: 回放方式选择和回放有效期设置（后端未实现，仅静态复刻UI）
- 多会场直播总开关（开/关）
- 分会场搜索与筛选功能
- 头部"示例"/"使用指南"跳转
- 头部"修改"后的设置保存流程
- 分会场卡片内更丰富的快捷操作（如一键分享、复制链接、更多菜单等）

## API需求说明

### 必需API
- **获取分会场列表**: `GET /api/v1/rooms?parent_room_id={room_id}&page={page}&size={size}` - 用于加载分会场列表数据
- **获取房间详情**: `GET /api/v1/rooms/{room_id}` - 用于加载主会场基本信息
- **获取分会场场次列表**: `GET /api/v1/rooms/{room_id}/sessions?page=1&size=10` - 用于获取分会场的最新场次信息（状态和开始时间）
- **创建分会场**: `POST /api/v1/rooms` - 用于创建新的分会场，请求体包含 `parent_room_id`、`title`、`is_private` 等字段（**注意**: `cover_url` 字段暂不提交，因为封面上传功能后端未实现）

### 暂缓API
- 其他功能相关的API接口暂不实现

## 核心原则

1.  **[最高准则] UI组件库**: **所有UI元素必须使用 Element Plus 组件库进行构建**。禁止使用原生的HTML标签（如 `<table>`, `<button>`）来模拟复杂组件。你的目标是生成语义化、符合 Element Plus 最佳实践的代码。
2.  **逻辑复用，视图替换**: 这是我们工作的最高原则。所有API请求、状态管理（Pinia/Vuex）、数据处理等逻辑都必须保留。你只负责重写页面的 `<template>` 部分，并调整 `<script>` 以适配 Element Plus 的数据绑定。
3.  **新建页面开发**: 这是一个全新的页面，需要创建完整的业务逻辑，包括数据获取、状态管理、事件处理等。
4.  **API集成**: 需要集成现有的房间和场次相关API接口，实现数据加载和状态管理。

---

## 任务一：创建多会场管理页面

**文件路径**: `/pages/room/new/MultiVenueManage.vue`

### 1. 页面布局 (`<template>`)

请使用 Element Plus 的 `<el-container>` 组件来构建**三栏布局**（Left, Right, Main），并精确复刻所有UI元素：

1.  **使用全局布局**: 整个页面的根组件应该是 `RoomManageLayout`（复用现有的房间管理布局）。

2.  **内容区结构**: 在 `RoomManageLayout` 的插槽内部，使用 `<el-space direction="vertical" size="large" style="width: 100%">` 作为主容器，并按顺序放置以下 Element Plus 组件：

    *   **页面头部设置区**: 使用 `<el-card>` 包裹，包含以下元素：
        *   **顶部标题行**: 使用 `<el-row>` 布局，"多会场直播"标题 + 右侧 `<el-switch>` 总开关 + "示例"超链接
        *   **表单设置区域**: 使用 `<el-form>` 包含：
            *   **菜单名称**: `<el-input>` + 字符计数显示 + `<el-switch>`（控制是否显示分会场信息）
            *   **主会场名称**: `<el-input>` + 字符计数显示 + "修改"按钮
            *   **显示位置**: `<el-radio-group>` 包含"视频下方示例"和"视频右侧示例"选项 + 说明文案
        *   **重要提示**: 使用 `<el-alert>` 显示主会场不推流时的统计说明

    *   **列表操作栏**: 使用 `<el-row>` 布局，包含：
        *   **"添加分会场"按钮**: `<el-button type="primary">` 
        *   **筛选下拉**: `<el-select>` 默认"全部"
        *   **关键字搜索框**: `<el-input>` 占位文案"请输入会场名称" + 搜索图标按钮

    *   **添加分会场弹窗**: 使用 `<el-dialog>` 组件，包含以下表单字段：
        *   **弹窗标题**: "添加多会场"
        *   **分会场名称**: `<el-form-item>` + `<el-input>` + 字符计数显示（0/50）+ 必填标识
        *   **分会场封面**: `<el-form-item>` + `<el-upload>` 上传区域（**静态复刻，后端未实现**）：
            - 上传区域：虚线框 + 中央"+"图标
            - 格式提示："推荐图片尺寸为: 1000*562, 不超过10M"
            - 支持格式："支持png、jpg、gif格式"
            - **注意**: 点击时显示 `ElMessage.info('封面上传功能待开发，敬请期待')` 提示
        *   **直播时间**: `<el-form-item>` + `<el-date-picker>` 日期时间选择器 + 时钟图标 + 占位文案"选择日期时间"
        *   **回放设置**: `<el-form-item>` + `<el-radio-group>` 横向排列（**静态复刻，后端未实现**）：
            - "结束后回放"（默认选中）
            - "实时回放"
            - "结束后不回放"
            - 说明文案："结束会场直播后才生成回放视频,分会场同步话题设置的跑马灯信息"
            - **注意**: 选择时显示 `ElMessage.info('回放设置功能待开发，敬请期待')` 提示
        *   **回放有效期**: `<el-switch>` 开关组件（**静态复刻，后端未实现**，默认关闭状态）
            - **注意**: 切换时显示 `ElMessage.info('回放有效期功能待开发，敬请期待')` 提示
        *   **操作按钮**: 底部右侧"取消"和"确定"按钮

    *   **分会场数据列表区**: 使用 `<el-table>` 构建数据表格，列定义如下：
        *   **会场封面**: `<el-table-column>` 使用 `<el-image>` 显示缩略图
        *   **会场名称**: `<el-table-column>` 显示会场标题
        *   **会场ID**: `<el-table-column>` 显示房间ID
        *   **直播时间**: `<el-table-column>` 显示场次开始时间（格式化显示）
        *   **状态**: `<el-table-column>` 使用 `<el-tag>` 根据场次状态显示不同颜色
        *   **排序**: `<el-table-column>` 显示排序值 + 拖拽图标
        *   **操作**: `<el-table-column>` 包含操作按钮：
            *   "下载回放视频"链接（静态占位）
            *   "编辑"按钮（跳转到编辑页面）
            *   "更多"下拉菜单（静态占位）

    *   **分页器**: 使用 `<el-pagination>` 组件，样式与 `RoomList` 页面保持一致

### 2. 逻辑绑定 (`<script setup>`)

*   **导入组件与工具**: 确保导入了 `RoomManageLayout`、所有需要的 Element Plus 组件及 Icon、`ElMessage`，以及相关的 store 和 API。
*   **数据获取**: 
    - 创建响应式数据：`parentRoomDetail`（主会场详情）、`subRooms`（分会场列表）、`loading`、`pagination` 等
    - 创建弹窗相关数据：`dialogVisible`（弹窗显示状态）、`formModel`（表单数据）、`formRules`（表单验证规则）等
    - 实现 `loadParentRoomDetail` 函数：调用 `GET /api/v1/rooms/{room_id}` 获取主会场信息
    - 实现 `loadSubRooms` 函数：调用 `GET /api/v1/rooms?parent_room_id={room_id}` 获取分会场列表
    - 实现 `loadSubRoomSessions` 函数：为每个分会场获取最新场次信息
*   **状态管理**: 使用 Pinia store 管理分会场状态，包括 `subRooms`、`pagination`、`loading`、`error` 等。
*   **事件处理**: 需要实现以下事件处理函数：
    *   `handleAddSubVenue`: 打开"添加分会场"弹窗
    *   `handleDialogClose`: 关闭弹窗并重置表单
    *   `handleSubmit`: 提交分会场创建表单，调用创建API
    *   `handleEditSubVenue`: 跳转到分会场编辑页面
    *   `handlePageChange`: 分页切换处理
    *   `handlePageSizeChange`: 每页条数切换处理
    *   `handleSearch`: 搜索功能（暂缓实现，显示占位提示）
    *   `handleFilter`: 筛选功能（暂缓实现，显示占位提示）
*   **适配 Element Plus**: 
    *   **头部设置区**: 
        *   使用 `<el-switch>` 实现总开关和菜单显示开关
        *   使用 `<el-input>` 的 `show-word-limit` 属性显示字符计数
        *   使用 `<el-radio-group>` 实现显示位置选择
        *   使用 `<el-alert>` 显示重要提示信息
    *   **操作栏**: 
        *   使用 `<el-button>` 实现"添加分会场"按钮
        *   使用 `<el-select>` 实现筛选下拉
        *   使用 `<el-input>` + 搜索图标实现搜索框
    *   **添加分会场弹窗**: 
        *   使用 `<el-dialog>` 实现弹窗容器，设置 `v-model="dialogVisible"`
        *   使用 `<el-form>` + `<el-form-item>` 构建表单结构
        *   使用 `<el-input>` 的 `maxlength="50"` 和 `show-word-limit` 属性实现字符计数
        *   **封面上传**: 使用 `<el-upload>` 实现图片上传UI（静态复刻），点击时显示占位提示
        *   使用 `<el-date-picker>` 实现日期时间选择，设置 `type="datetime"`
        *   **回放设置**: 使用 `<el-radio-group>` 实现回放设置选择UI（静态复刻），选择时显示占位提示
        *   **回放有效期**: 使用 `<el-switch>` 实现回放有效期开关UI（静态复刻），切换时显示占位提示
        *   使用表单验证规则 `formRules` 实现必填字段校验（仅验证分会场名称和直播时间）
    *   **数据表格**: 
        *   使用 `<el-table>` 和 `<el-table-column>` 构建表格
        *   使用 `<el-image>` 显示会场封面，设置 `fit="cover"` 和合适尺寸
        *   使用 `<el-tag>` 根据场次状态显示不同颜色（`success`、`warning`、`info`、`danger`）
        *   时间格式化：对 `start_time` 先做"清洗"（去微秒、规范化 `+00:00Z` 为 `Z`），再 `dayjs(cleaned).format('YYYY-MM-DD HH:mm:ss')`
        *   使用 `<el-button>` 和 `<el-dropdown>` 实现操作按钮
    *   **分页器**: 
        *   使用 `<el-pagination>` 实现分页功能
        *   设置 `v-model:current-page`、`v-model:page-size`、`total` 等属性
        *   实现 `@current-change` 和 `@size-change` 事件处理
*   **功能实现**: 
    *   **添加分会场**: 点击按钮打开弹窗，填写表单后调用 `POST /api/v1/rooms` 创建分会场，成功后关闭弹窗并刷新列表
    *   **编辑分会场**: 点击跳转到 `/pages/room/new/RoomCreate?room_id={id}&mode=edit` 页面
    *   **表单验证**: 分会场名称（必填，最大50字符）、直播时间（必填）
    *   **静态功能提示**: 
        - 封面上传：点击时显示 `ElMessage.info('封面上传功能待开发，敬请期待')`
        - 回放设置：选择时显示 `ElMessage.info('回放设置功能待开发，敬请期待')`
        - 回放有效期：切换时显示 `ElMessage.info('回放有效期功能待开发，敬请期待')`
    *   **其他功能**: 点击时显示 `ElMessage.info('功能待开发，敬请期待')` 提示

---

## 任务二：数据流设计

### 1. 页面加载流程
1. 根据路由参数 `room_id` 获取主会场详情
2. 加载分会场列表数据（第一页，默认每页10条）
3. 为每个分会场并行获取最新场次信息
4. 更新页面状态和数据展示

### 2. 状态管理
- 使用 Pinia store 管理分会场相关状态
- 实现分会场列表的增删改查操作
- 处理加载状态和错误状态

### 3. 路由设计
- **主页面**: `/pages/room/new/MultiVenueManage?room_id={id}`
- **添加分会场**: 通过弹窗表单实现，无需跳转页面
- **编辑分会场**: `/pages/room/new/RoomCreate?room_id={id}&mode=edit`

---

## 任务三：样式与交互

### 1. 样式要求
- 复用 `RoomManageLayout` 的样式体系
- 数据表格样式与 `RoomList` 页面保持一致
- 分页器样式与 `RoomList` 页面保持一致
- 响应式设计，支持不同屏幕尺寸

### 2. 交互设计
- **状态反馈**: 所有操作都有明确的成功/失败反馈
- **加载状态**: 数据加载时显示 loading 状态
- **错误处理**: 网络错误和数据错误的友好提示
- **空状态**: 无分会场时显示友好的空状态提示

### 3. 性能优化
- 使用 `v-memo` 优化列表渲染性能
- 实现虚拟滚动（如果数据量很大）
- 图片懒加载优化

---

## 关键实现要点

### 1. 数据清洗与格式化
- **时间字段处理**: 后端返回的时间格式如 `2025-09-28T07:16:42.474000+00:00Z`，需要：
  1) 去掉微秒部分（`.\d{6}`）
  2) 将尾部 `+00:00Z` 规范化为 `Z`
  3) 再用 `dayjs(cleaned).format('YYYY-MM-DD HH:mm:ss')`

### 2. 状态映射
- **场次状态映射**:
  - `scheduled` → `<el-tag type="info">未开始`
  - `live` → `<el-tag type="success">直播中`
  - `ended` → `<el-tag type="warning">已结束`
  - `archived` → `<el-tag type="info">已归档`

### 3. 组件复用
- **布局组件**: 复用 `RoomManageLayout` 布局组件
- **表格组件**: 复用 `RoomList` 的表格样式和分页组件
- **创建/编辑**: 复用 `RoomCreate` 页面，通过参数区分模式

### 4. API集成
- **必需API**:
  - `GET /api/v1/rooms/{room_id}` - 获取主会场详情
  - `GET /api/v1/rooms?parent_room_id={room_id}&page={page}&size={size}` - 获取分会场列表
  - `GET /api/v1/rooms/{room_id}/sessions?page=1&size=10` - 获取分会场场次信息
  - `POST /api/v1/rooms` - 创建分会场
- **数据字段**: 
  - 主会场详情：`id`, `title`, `description`, `cover_url` 等
  - 分会场列表：`id`, `title`, `cover_url`, `parent_room_id` 等
  - 场次信息：`status`, `start_time`（注意清洗格式后再展示）
  - 创建分会场请求体：`parent_room_id`, `title`, `is_private`, `description` 等（**注意**: `cover_url` 字段暂不包含，因为封面上传功能后端未实现）

---

请根据以上详细要求，生成 `MultiVenueManage.vue` 的完整文件代码。
