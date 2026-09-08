# 阶段三：TopicDisplay 页面代码生成提示词 (Element Plus 版)

## 角色与目标

你是一名资深前端重构工程师，精通 Element Plus 与 Vue 3 Composition API，严格复用本项目既有的请求封装、状态管理（Pinia）与图片 URL 规范化逻辑。

你的任务：实现“专题聚合展示页”（TopicDisplay.vue）。本页需要在 `LiveView.vue` 点击“返回营销专题”时，自动获取当前直播房间唯一关联的专题 `topic_id` 并跳转到本页；页面结构与交互风格参考 `VenueDisplayPage.vue`，展示 `TopicCreate.vue` 创建的“Banner/标题/分类/直播间列表”等聚合内容。

- 目标 1：支持从 `LiveView.vue` 自动获取并携带 `topic_id` 访问本页；若仅有 `room_id`，则先通过房间关联专题接口获取唯一 `topic_id` 再跳转。
- 目标 2：从后端拉取“聚合详情”并渲染页面（Banner、标题、分类 Tabs、分类内直播间卡片）。
- 目标 3：确保鉴权、URL 规范化、时间清洗与本项目其它页面一致。

## 页面功能范围说明

- 顶部 Banner：显示专题横幅图（支持相对路径 -> 绝对路径规范化）。
- 专题标题与描述：展示 `title/description`；状态 `status` 可作为角标/标签（可选）。
- 分类 Tabs：渲染后端返回的 `categories` 数组；切换 Tab 显示对应分类下的直播间列表。
- 直播间卡片：封面、标题、状态角标、开始时间（清洗后格式化）、热度（若后端有则展示，否则可用兜底字段）。
- 返回入口：提供“返回主会场/返回直播页”按钮（可选）。

## API 需求说明（所有接口均需 JWT 认证）

认证要求：所有以下接口调用，HTTP Header 必须包含：`Authorization: Bearer <JWT_TOKEN>`。本项目请求工具 `utils/request.ts` 已自动注入 Token。

- 获取房间关联专题（用于从 LiveView 自动定位唯一专题）
  - Endpoint: `GET /api/v1/rooms/{room_id}/topics`
  - 约定：同一直播房间只会被一个专题选中（唯一关联），前端应直接取唯一 `topic_id`（若后端暂返回列表，取第一个符合 `status==='published'` 或首个元素）。
  - Response（示例）:
    ```json
    { "code": 200, "message": "success", "data": [
      { "topic_id": "topic_uuid_1", "topic_title": "专题标题", "topic_status": "published", "category_id": "...", "category_name": "..." }
    ], "timestamp": "..." }
    ```

- 获取专题聚合详情
  - Endpoint: `GET /api/v1/topics/{topic_id}`
  - Response data 为聚合详情对象（`id/title/description/banner_url/status/categories[]`，分类下包含 `rooms[]`）。
  - 示例摘录：见《专题功能完整设计文档-修正版.md》“获取专题聚合页详情”。

（可选）图片上传与管理在 `TopicCreate.vue` 已实现，本页仅消费已存在的 `banner_url/cover_url`。

## 核心原则

1. 鉴权优先：所有请求需携带 JWT，未认证则提示并跳到登录/授权页。
2. 数据契约：直接消费后端聚合对象；避免自行拼装，字段名保持一致。
3. URL 规范化：相对路径（如 `/media/...`）需用 `BASE_API_URL` 推导 `origin` 并拼接。
4. 体验一致：时间清洗、加载/空态、错误提示与 `LiveView.vue`、`VenueDisplayPage.vue` 一致。
5. 稳健性：`topic_id` 必须做 UUID 形态校验；失败时给出清晰错误与回退指引。

---

## 任务一：创建 TopicDisplay 页面

文件路径：`/src/pages/topic/TopicDisplay.vue`

### 1. 页面布局（<template>）

- 参考 `VenueDisplayPage.vue` 的整体结构：
  - 顶部 Banner（`el-card` 包裹 `el-image` 或 `<img>`）；
  - 标题 + 状态标签 + 描述；
  - 分类 Tabs（`el-tabs` + `el-tab-pane`），面板内渲染直播间卡片列表；
  - 卡片：左封面（`el-image fit="cover"`）+ 右信息（标题、开始时间、热度、状态角标）。
- 顶部右侧可以放置“返回主会场/返回直播页”按钮（可选）。

### 2. 逻辑与样式（<script setup> + <style scoped>）

逻辑要点：
- 参数解析：支持 `?topic_id={uuid}` 直接进入；若从 `LiveView` 点击进入但只携带 `room_id`，则先调用 `GET /rooms/{room_id}/topics` 获取唯一 `topic_id` 再重定向到本页。
- 鉴权：未登录/无 Token -> Toast + 跳转授权页。
- 拉取数据：`GET /topics/{topic_id}` -> `currentTopic`、`categories`；默认激活第一个分类。
- 图片 URL：`getCoverSrc(url)` 与项目统一实现；相对路径拼接 `origin`。
- 时间清洗：与 `LiveView.vue` 保持一致（去微秒、去时区、标准格式化）。
- 错误处理：接口错误/404 -> Toast，并提供“返回上一页/回到直播页”的操作。

样式要点：
- Banner 高度 200~300px，圆角与阴影；
- Tabs 居中、底线高亮；
- 卡片 hover 阴影；移动端上下布局，使用 `@media (max-width: 767px)` 调整。

### 3. 组件与依赖

必用 EP 组件：`ElContainer`、`ElMain`、`ElCard`、`ElTabs`、`ElTabPane`、`ElImage`、`ElTag`、`ElSpace`、`ElRow`、`ElCol`、`ElButton`、`ElEmpty`、`ElMessage`、`ElMessageBox`。

---

## 任务二：数据与交互细节

1) 数据模型（参考 `src/types/topic.ts`）
```ts
interface TopicDetailResponse {
  id: string
  title: string
  description?: string
  banner_url?: string
  status: 'draft'|'published'|'archived'
  categories: Array<{
    id: string
    name: string
    sort_order: number
    rooms: Array<{
      id: string
      title: string
      cover_url?: string
      live_status: string
      start_time?: string
      heat: number
      sort_order?: number
    }>
  }>
}
```

2) 入口与跳转
- 从 `LiveView.vue` 页签“返回营销专题”进入：
  - 若已在 `LiveView` 拿到 `topic_id`，直接：`/pages/topic/TopicDisplay?topic_id={id}`；
  - 若仅有 `room_id`，先调用 `GET /rooms/{room_id}/topics` 获取唯一 `topic_id`，再跳转；若无返回或失败，提示并允许手动输入 UUID。

3) 加载流程
- 校验 `topic_id`（UUID 正则）；
- 设置 `loading=true`，调用 `GET /topics/{topic_id}`；
- 填充 `currentTopic/categories`，激活第一个分类；
- 失败时：Toast + 回退导航。

4) 展示细节
- 图片：统一 `getCoverSrc` 规范；
- 时间：与 `LiveView.vue` 相同的 `formatTime`；
- 状态角标：`live/scheduled/ended/archived` -> 颜色映射；
- 空态：无分类/分类下无直播间 -> `ElEmpty`。

5) 安全与鉴权
- Header 注入 `Authorization: Bearer <JWT_TOKEN>`；
- 401/403 -> 统一登录引导或 Token 失效处理。

---

## 任务三：路由与接入

- 新增/确认路由：`/pages/topic/TopicDisplay?topic_id={uuid}`。
- 从 `LiveView.vue` 的“返回营销专题”入口跳转；若 LiveView 未拿到 `topic_id`，在该页先通过 `room_id` 查唯一 `topic_id` 再跳转。
- 返回：`uni.navigateBack()` 或回到 `LiveView`。

---

## 关键实现要点 Checklist

- [ ] 从参数自动识别 `topic_id`；若仅有 `room_id`，调用 `GET /rooms/{room_id}/topics` 获取并跳转。
- [ ] 拉取 `GET /topics/{topic_id}`，渲染 Banner/标题/描述/分类/房间卡片。
- [ ] 统一 URL 规范化、时间清洗、状态角标与空态展示。
- [ ] 全链路 JWT 鉴权；401/403 处理与登录引导。
- [ ] 错误兜底与返回导航。
- [ ] UI 风格尽量贴近 `VenueDisplayPage.vue`，但保持本页语义。

---

## 生成要求

1) 只使用 Element Plus 组件，不引入额外 UI 库；
2) 逻辑简洁：参数解析、鉴权校验、请求调用、数据渲染分明；
3) 复用项目现有工具（Pinia、`utils/request.ts`、`BASE_API_URL` 规范化）；
4) 可运行的最小实现优先，确保从 `LiveView` 一键回到专题页通路畅通。


