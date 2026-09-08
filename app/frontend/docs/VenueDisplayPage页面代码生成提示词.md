# 阶段三：VenueDisplayPage 页面代码生成提示词 (Element Plus 版)

## 角色与目标

你是一名资深前端重构工程师，精通 Element Plus 并对 UI 细节有像素级要求。我有一个已经可以完整运行的前端项目，其核心功能和业务逻辑（API 请求、状态管理、数据处理）已经全部实现。

你的核心任务是“新建页面开发”，即根据我提供的设计文档（见 `@前端分析及设计文档.md` 中第 6 章：VenueDisplayPage 主分会场展示页）构建一个全新的、基于 Element Plus 的 UI 视图层。注意：这是一个全新的页面，需要从零开始开发，但必须最大程度复用现有 API 与状态管理方式。

## 页面功能范围说明

### 本期实现功能
- 顶部主视觉 Banner（静态占位图）
- 分类筛选标签页（如“云南省”、“湖南省”）——静态占位，不发生真实筛选
- 分会场卡片列表（动态渲染）
- 单个分会场卡片（左侧封面，右侧信息：标题、开始时间、热度、状态角标）
- 点击分会场卡片跳转到对应的 LiveView 观看页：`/pages/live/new/LiveView?room_id={sub_venue_id}`

### 暂缓实现功能
- 分类筛选的真实过滤逻辑与联动请求
- 热度的真实统计值（本期使用静态占位默认 100）

## API 需求说明

### 必需 API
- 获取直播房间列表：`GET /rooms`（必要字段：`id`, `title`, `cover_url`, `created_at`）
  - 说明：后端若直接返回所有房间，前端需要在页面侧做“主会场/分会场”的区分（可通过 `parent_room_id` 是否为空判断）；本页仅展示“主会场 id 对应的全部分会场”。
- 获取单个房间详情（用于顶部标题或扩展）：`GET /rooms/{room_id}`（可选）

### 参数与数据清洗
- 时间字段展示（分会场卡片“开始时间”）
  - 如果需要从 `sessions` 取最近一条：使用 `GET /rooms/{room_id}/sessions?page=1&size=10`，按 `start_time` 降序后取第一条
  - 时间清洗规则（与 LiveView/RoomManage 保持一致）：
    1) 去掉微秒（`\.\d{1,6}`）
    2) 去掉尾部 `Z` 或 `+XX:XX` 的时区标识
    3) 统一格式化输出为 `YYYY-MM-DD HH:mm:ss`

## 核心原则

1. UI 组件库：所有 UI 元素必须使用 Element Plus 组件；遵循官方最佳实践。
2. 逻辑复用：尽可能复用现有的 API 请求工具、时间清洗与格式化逻辑、Pinia store（如 `room`/`session` store）。
3. 新建页面开发：创建完整页面、路由与必要的最小状态管理代码。

---

## 任务一：创建 VenueDisplayPage 页面

文件路径：`/src/pages/venue/VenueDisplayPage.vue`

### 1. 页面布局（<template>）

请使用 Element Plus 的 `el-container` 构建单列纵向布局，严格复刻“主视觉图 -> 筛选标签页 -> 分会场卡片列表”的结构。

1) 顶部主视觉 Banner
- 使用 `el-card` 包裹一张静态占位图（项目 `public/` 或 `assets/` 中的示例图），铺满横向宽度，高度 180~220px；
- 右上角可放置少量操作位（占位即可）。

2) 分类筛选标签页（静态占位）
- 使用 `el-tabs` 渲染，至少包含两个 Tab（示例：“云南省”、“湖南省”）；
- 切换 Tab 仅更新内部选中态，不触发真实过滤；
- 保持与主设计稿一致的视觉（文字加粗、下划线高亮）。
- 重要：本期“主会场 Banner 与所有分会场卡片均显示在‘云南省’页签下”，其他页签仅作视觉占位，不展示内容。

3) 分会场卡片列表
- 使用 `el-space direction="vertical"` 或 `el-row :gutter="16"` 纵向排列卡片；
- 单个分会场卡片使用 `el-card`：
  - 左侧：`el-image` 显示封面图，左上角使用 `el-tag` 覆盖状态角标（如“未开始/直播中/回放中”）；
  - 右侧：标题（多行省略）、开始时间（清洗后 `YYYY-MM-DD HH:mm:ss`）、热度（静态占位 100）；
- 整卡支持 hover 阴影效果；点击跳转到对应 LiveView 观看页。

### 2. 逻辑与样式（<script setup> + <style scoped>）

逻辑：
- 路由参数：支持 `?venue_id={主会场ID}`（必传）。
- 数据加载：
  - 根据 `venue_id` 获取主会场详情（可选）；
  - 获取所有房间列表后在前端按 `parent_room_id === venue_id` 过滤得到分会场集合；
  - 若需要展示“最近场次时间”，调用 `GET /rooms/{room_id}/sessions`，降序取第一条并格式化 `start_time`。
- 时间清洗：实现与 LiveView/RoomManage 同步的 `formatTime` 工具，确保 ISO 串/带微秒/带时区的字符串都能稳定转换。
- 导航：点击分会场卡片跳转到 `/pages/live/new/LiveView?room_id={sub_venue_id}`。
 - 展示规则：渲染时固定将主会场 Banner 与分会场卡片插入到“云南省”页签对应的面板，其它页签面板保持空内容（仅壳）。

样式：
- Banner 使用渐变或浅灰底，四角圆角阴影；
- Tabs 使用居中对齐，高亮底线；
- 卡片图片固定尺寸（如 200x120），`fit="cover"`；
- 标题 2~3 行省略；
- 开始时间与热度使用次级文本色；
- 移动端适配：图片与文本上下布局，使用 `@media (max-width: 767px)` 调整为垂直排列。

### 3. 组件与依赖

需要用到的 EP 组件：`ElContainer`、`ElMain`、`ElCard`、`ElTabs`、`ElTabPane`、`ElImage`、`ElTag`、`ElSpace`、`ElRow`、`ElCol`、`ElButton`、`ElSkeleton`（可选）。

---

## 任务二：数据与交互细节

1) 数据来源与映射
- 房间列表字段：`id`, `title`, `cover_url`, `parent_room_id`, `created_at`；
- 场次字段（如使用）：`id`, `room_id`, `status`, `start_time`；
- 卡片展示：
  - 封面：`cover_url`
  - 标题：`title`
  - 状态角标：优先根据最近一条场次的 `status`，找不到则回退为“未开始”
  - 开始时间：最近一条场次的 `start_time`（经清洗格式化）
  - 热度：静态占位 100

2) 时间清洗函数（与其它页面一致）
- 清理规则（先清理再格式化）：
  - 去微秒（`\.\d{1,6}`）
  - 去掉结尾 `Z` 或 `+XX:XX` 时区
  - 统一输出 `YYYY-MM-DD HH:mm:ss`

3) 空态与 Loading
- 首次加载时展示 `el-skeleton` 或简单 Loading；
- 无分会场数据时展示空态占位文案。

---

## 任务三：路由与接入

路由：`/pages/venue/VenueDisplayPage?venue_id={主会场ID}`

入口：
- 从单个分会场的 LiveView 页返回时，可跳到该页用于展示主会场下所有分会场；
- 也可在 Room/Live 的其它入口添加“查看全部分会场”的按钮，跳转到本页。

---

## 关键实现要点 Checklist

- [ ] 使用 Element Plus 搭建页面结构，视觉风格贴近设计稿
- [ ] Banner 静态占位图，Tabs 静态占位
- [ ] 获取全部房间列表并过滤出 `parent_room_id === venue_id` 的分会场
- [ ]（可选）为每个分会场请求最近场次并清洗时间
- [ ] 分会场卡片：封面、状态角标、标题、开始时间、热度
- [ ] 点击卡片跳转到 `/pages/live/new/LiveView?room_id={id}`
- [ ] 时间清洗逻辑与其它页面保持一致
- [ ] 移动端响应式适配

---

## 代码结构建议

```
src/
  pages/
    venue/
      VenueDisplayPage.vue
  utils/
    datetime.ts         # 可抽出 formatTime 清洗函数（可选）
```

在 `VenueDisplayPage.vue` 中：
- `<template>`：Container + Banner + Tabs + CardList
- `<script setup>`：路由参数解析、API 请求、数据整理、时间清洗、跳转事件
- `<style scoped>`：卡片与 Banner 的样式、响应式适配

---

## 生成要求

1) 只使用 Element Plus 组件，不使用原生复杂元素模拟；
2) 逻辑简洁清晰，数据加载与状态处理放在 `<script setup>` 中；
3) 代码风格与现有项目保持一致（Pinia/请求封装/工具函数的使用）；
4) 时间展示统一为 `YYYY-MM-DD HH:mm:ss`；
5) 可运行的最小实现优先（先通路，后美化）。


