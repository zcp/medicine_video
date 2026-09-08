# 阶段三：RoomList代码生成提示词 (Element Plus版)

## 角色与目标

你是一名资深前端重构工程师，**精通 Element Plus** 并对UI细节有像素级要求。我有一个已经可以完整运行的前端项目，其核心功能和业务逻辑（API请求、状态管理、数据处理）已经全部实现。

你的核心任务是**“换肤”与“组件化重构”**，即根据我提供的最新设计文档（`@前端分析及设计文档.md`），为项目构建一个全新的、基于 Element Plus 的UI视图层，同时必须**最大限度地复用**现有的业务逻辑代码。

## 核心原则

1.  **[最高准则] UI组件库**: **所有UI元素必须使用 Element Plus 组件库进行构建**。禁止使用原生的HTML标签（如 `<table>`, `<button>`）来模拟复杂组件。你的目标是生成语义化、符合 Element Plus 最佳实践的代码。
2.  **逻辑复用，视图替换**: 这是我们工作的最高原则。所有API请求、状态管理（Pinia/Vuex）、数据处理等逻辑都必须保留。你只负责重写页面的 `<template>` 部分，并调整 `<script>` 以适配 Element Plus 的数据绑定。
3.  **禁止从零开始**: 不要创建任何新的业务逻辑。如果你需要数据或方法，请假设它们已经存在于原有的 `<script>` 部分。你只需进行绑定。

---

## 任务一：创建全局布局组件 (AdminLayout)

**文件路径**: `/src/layouts/AdminLayout.vue`

### 1. 布局结构 (`<template>`)

请使用 Element Plus 的 `<el-container>` 组件来构建经典的三段式后台布局（Top, Left, Main），并精确复刻所有UI元素：

1.  **顶部布局 (`<el-header>`)**:
    *   **样式**: `height: 64px`, `padding: 0 24px`, `background: '#2b2f3a'` (深色主题), `display: 'flex'`, `alignItems: 'center'`.
    *   **左侧区域**: 使用 `<el-space :size="24">` 排列。
        *   Logo与标题: `Med-Scholar的直播间` (白色字体, `font-size: 18px`)。
        *   使用 `<el-menu mode="horizontal" background-color="#2b2f3a" text-color="#fff" active-text-color="#ffd04b">` 渲染主导航按钮: `首页`, `直播`(高亮), `营销`, `内容`, `商品`, `交易`, `用户`, `数据`, `企微`。
        *   使用 `<el-dropdown>` 组件渲染 `社区团购` 入口 (白色字体)。
    *   **右侧区域**: `margin-left: auto`。使用 `<el-space :size="16">` 排列以下元素：
        *   `<el-input>` 作为全局搜索框，`placeholder="搜索功能与帮助"`，并使用 `@element-plus/icons-vue` 的 `Search` 图标。
        *   使用 `<el-button link>` 并内嵌 Element Plus 的 Icon 组件渲染所有功能图标按钮: 如 `QuestionFilled`, `Collection`, `Download`, `Bell`, `Refresh`。
        *   使用 `<el-avatar>` 和 `<el-dropdown>` 渲染用户头像及其菜单。

2.  **侧边栏布局 (`<el-aside>`)**:
    *   **属性**: `width: 220px`。
    *   **菜单**: 使用 `<el-menu>` 渲染侧边栏菜单项。严格按照以下顺序，并为每个菜单项指定精确的 Icon：
        *   `新建直播` (Icon: `Plus`)
        *   `直播管理` (高亮, Icon: `Monitor`)
        *   `频道管理` (Icon: `VideoPlay`)
        *   `图片直播` (Icon: `Picture`)
        *   `软件下载` (Icon: `Download`)
        *   `通用设置` (Icon: `Setting`)
        *   `多渠道分发` (Icon: `Share`)
        *   `直播中控台` (Icon: `Platform`, 自定义插槽添加 `<el-tag type="danger">NEW</el-tag>`)
        *   `执行服务` (Icon: `Tools`, 自定义插槽添加 `<el-tag type="warning">HOT</el-tag>`)

3.  **主内容区 (`<el-main>`)**:
    *   **样式**: `padding: 24px`。
    *   请在此处使用 `<slot />` 标签作为页面内容的占位符。

### 2. 逻辑与样式

*   **逻辑**: 在 `<el-menu>` 中设置 `default-active` 属性来确保 `直播` 和 `直播管理` 菜单项在视觉上处于高亮状态。
*   **样式**: 使用 `<style scoped>`。大部分样式由 Element Plus 控制，你只需处理布局容器和自定义元素的样式即可。

---

## 任务二：重构 RoomList 页面

**文件路径**: `/pages/room/new/RoomList.vue`

### 1. 页面布局 (`<template>`)

1.  **使用全局布局**: 整个页面的根组件应该是 `AdminLayout`。

2.  **内容区结构**: 在 `AdminLayout` 的插槽内部，使用 `<el-space direction="vertical" size="large" style="width: 100%">` 作为主容器，并按顺序放置以下 Element Plus 组件：
    *   **信息提示条**: 使用 `<el-alert type="info" :closable="false" show-icon>`。`title` 设为 “当前直播间分数：100分（正常）”，右侧链接通过 `v-slot:default` 添加。
    *   **主操作与标签页**: 使用 `<el-card>` 包裹。内部使用 `<el-row justify="space-between">` 布局。
        *   左侧 `<el-col>`: `<el-space :size="8">` 包裹的 `<el-button>` 组件 (`创建直播` (primary), `批量创建直播` 等)。
        *   右侧 `<el-col>`: `<el-tabs>` 组件 (`待整改直播内容`, `分类管理`, `回收站`)。
    *   **搜索/筛选表单**: 使用 `<el-card>` 包裹，内部使用 `<el-form :inline="true">` 构建，包含 `<el-select>`, `<el-input>`, `<el-button type="primary">`。
    *   **数据表格**: **这是核心**。使用 `<el-table>` 组件。
        *   **属性**: 绑定 `:data` (数据源), `v-loading` (加载状态), `border`, `@selection-change` (行选择事件)。
        *   **列定义 (`<el-table-column>`)**: 严格遵循设计文档顺序，在 `<el-table>` 内部使用 `<el-table-column>` 逐列定义。对于复杂列，使用默认插槽进行自定义渲染。
        *   **批量操作栏**: 使用 `<el-alert type="info">`，通过 `v-if` 控制其在有行选中时显示。`title` 属性动态显示 “已选 N 条”，`description` 属性通过 `v-slot` 渲染所有批量操作按钮。
    *   **独立分页器**: 在 `<el-table>` 的父容器（如 `<el-card>`）的底部，使用 `<el-row justify="end" style="margin-top: 16px">` 包裹 `<el-pagination>` 组件。绑定 `v-model:current-page`, `v-model:page-size`, `:total`, `layout="total, sizes, prev, pager, next, jumper"`。
    *   **创建/编辑模态框**: 使用 `<el-dialog>`，通过 `v-model` 控制显示。`title` 动态绑定。内部包含一个 `<el-form>` 用于创建和编辑直播间。

### 2. 逻辑绑定 (`<script setup>`)

*   **导入组件与工具**: 确保导入了 `AdminLayout` 和所有需要的 Element Plus 组件及 Icon，以及 `ElMessage` 服务。
*   **复用逻辑**: 假设已有的 `useRooms` 钩子返回了 `rooms` (数据源), `loading`, `pagination` (分页对象), `handleCreateRoom`, `handleUpdateRoom` 等。
*   **适配 Element Plus**: 
    *   **表格列**: 在 `<template>` 中使用 `<el-table-column>` 定义每一列的 `prop`, `label`, `width`, `align`。对于需要自定义的列，使用默认插槽并解构出 `{ row }` 来访问行数据。
        *   `直播` 列: `width: 350`。插槽内使用 `<el-space>` 包含 `<el-image>` 和一个垂直 `div` 容器来展示标题和 `<el-tag>`。
        *   `直播状态` 列: `width: 120`, `align: 'center'`。插槽内使用 `<el-tag>` 根据状态值显示不同 `type`（`success`, `warning`, `info`）。
        *   `开始时间` 列: `width: 180`, `align: 'center'`。数据需用 `dayjs(row.startTime).format('YYYY-MM-DD HH:mm:ss')` 进行格式化。
        *   `操作` 列: `width: 240`, `align: 'center'`, `fixed: 'right'`。插槽内使用 `<el-space :size="0" spacer="<el-divider direction='vertical' />">` 来分隔多个 `<el-button type="primary" link size="small">` 操作按钮。
    *   **数据绑定**: 将 `useRooms` 返回的数据适配并绑定到 `<el-table>` 和 `<el-pagination>` 的 props 上。
    *   **事件处理**: 将 `<el-pagination>` 的 `@current-change` 和 `@size-change` 事件连接到已有的分页逻辑函数上。
    *   **模态框逻辑**: 将 `handleCreateRoom` 绑定到“创建直播”按钮的 `@click` 事件，该函数应打开 `<el-dialog>` 并重置表单。行内“编辑”按钮应打开同一个模态框并填充数据。
*   **静态交互**: 对于“暂缓实现”的按钮，为其 `@click` 事件绑定一个统一的提示函数，该函数应调用 `ElMessage.info('功能待开发，敬请期待')`。

---

请根据以上详细要求，依次生成 `AdminLayout.vue` 和 `RoomList.vue` 的完整文件代码。