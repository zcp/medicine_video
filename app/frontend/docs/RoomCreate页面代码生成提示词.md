# 阶段四：RoomCreate代码生成提示词 (Element Plus版)

## 角色与目标

你是一名资深前端重构工程师，**精通 Element Plus** 并对UI细节有像素级要求。我有一个已经可以完整运行的前端项目，其核心功能和业务逻辑（API请求、状态管理、数据处理）已经全部实现。

你的核心任务是根据我提供的最新设计文档（`@前端分析及设计文档.md`），为项目新建一个基于 Element Plus 的UI视图层，同时必须**最大限度地复用**现有的业务逻辑代码，将原先在 `RoomList.vue` 中的弹窗创建功能，升级为一个独立的页面。

## 核心原则

1.  **[最高准则] UI组件库**: **所有UI元素必须使用 Element Plus 组件库进行构建**。禁止使用原生的HTML标签来模拟复杂组件。
2.  **逻辑复用，视图替换**: 这是我们工作的最高原则。所有API请求、状态管理（Pinia）等逻辑都必须保留。你只负责构建页面的 `<template>` 部分，并调整 `<script>` 以适配新的页面结构。
3.  **禁止从零开始**: 不要创建任何新的业务逻辑。所有需要的 store actions (如 `addNewRoom`) 都已存在，你只需调用。

---

## 任务：创建 RoomCreate 页面

**文件路径**: `/src/pages/room/new/RoomCreate.vue`

### 1. 页面布局 (`<template>`)

1.  **使用全局布局**: 整个页面的根组件应该是 `AdminLayout`。

2.  **内容区结构**: 在 `AdminLayout` 的插槽内部，按顺序精确复刻以下UI布局：
    *   **顶部类型选择**: 使用一组带图标的 `<el-radio-button>` 实现，默认选中“视频直播”。（静态UI）
    *   **表单容器**: 使用 `<el-card>` 包裹，内部使用 `<el-form label-position="right" label-width="100px">` 构建。
    
    *   **基本信息区块**:
        *   `直播形式`: 使用 `<el-form-item>` 和 `<el-radio-group>`，默认选中“直播”。下方需附带描述文字：“实时直播形式...”。（静态UI）
        *   `直播名称`: 使用 `<el-form-item>` 和 `<el-input>`，`placeholder` 为“请输入直播名称，100字内”。
        *   `开始时间`: 使用 `<el-form-item>` 和 `<el-date-picker type="datetime">`。下方需附带动态生成的描述文字：“本场直播将于...开播”，并提供“设置开播提醒”的链接。（链接功能暂缓）
        *   `显示模式`: 使用 `<el-form-item>` 和 `<el-radio-group>`，默认选中“横屏”。下方需附带描述文字和信息图标：“比例为16:9...”。（静态UI）
        *   `直播封面`: 使用 `<el-form-item>` 和 `<el-upload>` 组件，上传区域需包含“+ 选择图片”的文字。

    *   **分类与场景区块**:
        *   `直播分类`: 使用 `<el-form-item>`，包含一个 `el-select` (placeholder: "请选择话题分类") 和一个 `+ 添加分类` 的 `<el-button>`。（静态UI）
        *   `所属频道`: 使用 `<el-form-item>`，包含一个 `+ 选择频道` 的 `<el-button>`。（静态UI）
        *   `使用场景`: 使用 `<el-form-item>` 和 `<el-radio-group>`，渲染多行单选按钮，默认选中“通用”。（静态UI）

    *   **观看与回放设置区块**:
        *   `观看方式`: 使用 `<el-form-item>`，包含一组带图标的 `<el-radio-button>`（公开、加密、付费等）。下方需附带描述文字。（静态UI，仅“公开/加密”切换逻辑需实现）
        *   `回放方式`: 使用 `<el-form-item>` 和 `<el-radio-group>`，默认选中“结束后回放”。下方需附带描述文字。（静态UI）
        *   `生成回放视频`: 使用 `<el-form-item>`，包含 `<el-radio-group>`（单个/多个视频）和一个带信息图标的 `<el-checkbox>`（开启自动打点）。下方需附带两行描述和注意文字。（静态UI）
        *   `回放有效期`: 使用 `<el-form-item>` 和 `<el-radio-group>`。（静态UI）

    *   **签到活动区块**:
        *   `签到活动`: 使用 `<el-form-item>`，包含一个 `+ 创建活动` 的链接按钮。（静态UI）

    *   **底部固定操作栏**: 使用一个固定在页面底部的 `div` 包裹操作按钮。
        *   `<el-button>`: “返回”。
        *   `<el-button type="primary">`: “立即创建”。

### 2. 逻辑绑定 (`<script setup>`)

*   **导入组件与工具**: 确保导入了 `AdminLayout`、所有需要的 Element Plus 组件、`useRoomStore` 以及 `useRouter`。

*   **核心逻辑迁移与适配**:
    *   **表单数据模型**: 创建一个 `reactive` 的 `formModel` 对象，用于双向绑定表单中**本期需要实现**的字段，至少包括：`title`, `start_time`, `cover_url`, `is_private`。
    *   **复用创建逻辑**: 你必须复用并适配原先在 `RoomList.vue` 的 `<el-dialog>` 中的创建逻辑。
        *   **验证逻辑**: 迁移 `validateForm` 函数，对 `title` 等必填项进行校验。
        *   **提交逻辑**: 创建 `handleCreate` 函数。点击“立即创建”按钮时，首先调用验证函数。验证通过后，调用 `roomStore.addNewRoom()`，并传入 `formModel` 中的数据。`addNewRoom` 的参数应与 `RoomList.vue` 中保持一致（例如 `{ title: formModel.title, ... }`）。
        *   **交互反馈**: 提交过程中，“立即创建”按钮应显示 `loading` 状态。创建成功后，使用 `ElMessage.success('创建成功')` 提示用户，并使用 `router.push('/pages/room/new/RoomList')` 跳转回列表页。创建失败则显示错误信息。

*   **导航逻辑**:
    *   **侧边栏高亮**: 在 `AdminLayout` 组件中，“新建直播”菜单项应处于高亮状态。
    *   **返回按钮**: 点击“返回”按钮，应使用 `router.back()` 或 `router.push('/pages/room/new/RoomList')` 返回列表页。

*   **静态交互**: 对于设计文档中所有标记为“暂缓实现”的UI元素（如“设置开播提醒”链接、“添加分类”按钮等），为其点击事件绑定统一的 `showComingSoonToast` 函数，调用 `ElMessage.info('功能待开发，敬请期待')`。

---

请根据以上详细要求，生成 `RoomCreate.vue` 的完整文件代码。
