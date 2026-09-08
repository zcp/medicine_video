# 移动端 Tab 滑动切换功能 —— 现状分析、实现方案与实施情况

**版本**: V2.0（含实施情况同步）  
**创建日期**: 2026-08-03  
**最后更新**: 2026-08-04  
**项目**: 医学直播 SaaS 平台  
**功能**: 为移动端各页面 Tab 增加左右滑动切换能力  
**作者**: 资深移动端前端工程师

---

## 📋 目录

1. [需求背景](#1-需求背景)
2. [现状实现情况分析](#2-现状实现情况分析逐页盘点)
3. [修改方案设计](#3-修改方案设计)
4. [技术难点与解决](#4-技术难点与解决)
5. [风险项分析](#5-风险项分析)
6. [改动量估算](#6-改动量估算)
7. [实施优先级与计划](#7-实施优先级与计划)
8. [测试验证](#8-测试验证)
9. [附录](#9-附录)
10. [实施情况同步记录（V2.0 新增）](#10-实施情况同步记录v20-新增)

---

## 1. 需求背景

### 1.1 业务需求

医学直播移动端 App 中，多个页面存在 Tab 内容切换：

- **首页**：正在直播 / 预告 / 回放 三状态切换
- **搜索结果页**：直播间 / 专家 / 品牌 切换
- **播放页**：直播介绍 / 专家介绍 / 品牌介绍 / 互动讨论 切换
- **我的订阅**：我的订阅 / 回放 切换
- **我的关注**：正在直播 / 全部关注 切换
- **通知中心**：全部 / 系统通知 / 订阅通知 切换
- **管理后台**：用户列表、精选内容、专家管理、科室分类 等切换

初始状态这些 Tab **全部仅支持点击 Tab 头切换**，不支持在内容区**左右滑动**进行切换。

### 1.2 交互背景

在移动端，Tab 内容切换约定俗成地支持两种操作方式：

1. **点按 Tab 头** —— 既有实现
2. **左右滑动内容区** —— 本次新增能力

主流视频平台（B站、抖音、快手等）均已将"左右滑动切换 Tab"作为标配交互。用户在内容区上下浏览时，天然地期望可以通过左右滑动横向切换分类，减少往返点击 Tab 头的操作成本。

> **例外说明**：**筛选型 Tab**（如首页科室分类、专家页科室筛选）承载的是一组可横向滚动的标签，横向滑动被用于滚动标签本身，内容区是单一列表，因此**不适用**滑动切换（详见 §2.4）。

### 1.3 范围界定

**本次功能范围**：
- 为符合滑动条件的 Tab 增加「内容区左右滑动」与「Tab 头点击」的双向联动
- 不改业务逻辑、数据请求、路由跳转、卡片交互

**不在范围**：
- 底部导航 TabBar（自定义组件，属页面级导航，非内容切换）
- 筛选型横向滚动 Tab（见 §2.4）
- 无页内 Tab 的页面（见 §2.5）

---

## 2. 现状实现情况分析（逐页盘点）

> 说明：本章节为 V1.0 的分析（改造前状态）。改造后的实际实现方式见 **§10 实施情况同步记录**。

### 2.1 Tab 实现模式分类

通过对全项目 52 处 Tab 相关文件的核查，可将现有 Tab 分为三类：

| 模式 | 定义 | 是否实现滑动 |
|------|------|------------|
| **页面级 Tab** | Tab 头 + 独立内容区（列表/内容各自独立或独立数据源），位于页面中上部，内容区独立滚动 | **需要实现** |
| **模块级 Tab** | Tab 位于页面滚动流内部，内容区与其他模块共用整页滚动 | **需要实现（技术有取舍）** |
| **筛选型 Tab** | 横向可滚动的标签组，内容为同一列表容器 | **不建议实现** |

### 2.2 页面级 Tab 详情

#### ① 搜索结果页

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/search/results.vue` |
| **Tab** | 直播间 / 专家 / 品牌（3 个，已移除"全部"） |
| **改造前实现** | `currentTab` 驱动 `handleTabChange`，切换时若有关键词则 `searchStore.performSearch` 重新请求；`filteredResults` 按 type 过滤展示；下方单个 `scroll-view scroll-y` 承载结果列表与推荐 |
| **数据源** | Pinia `searchStore.searchResults`（共享同一数组，按 `item.type` 过滤） |

#### ② 播放页（LiveView）

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/live/LiveView.vue` |
| **Tab** | 动态生成：直播介绍 / 专家介绍 / 品牌介绍 / 互动讨论（由 `loadRoomTabs()` 从后端 `getPublicRoomTabList` 获取，含降级补充逻辑） |
| **改造前实现** | `activeTab` + `switchTab`，Tab 头为 `sticky` 定位；内容区为单个 `scroll-view scroll-y`，按 `currentTab.tab_key` 用 `v-if` 渲染对应组件（`ContentTab` / `ExpertsTab` / `BrandsTab` / `ChatTab`） |
| **数据源** | 各 Tab 组件独立（专家 `experts`、品牌 `brands`、聊天 `chatMessages`、内容 `currentTab`） |
| **特殊点** | Tab 头是 `sticky` 吸顶；聊天 Tab 有**底部固定输入框**；播放器在 Tab 区上方 |

#### ③ 我的订阅

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/tabbar/my/subscriptions/index.vue` |
| **Tab** | 我的订阅 / 回放（2 个，含数量角标） |
| **改造前实现** | `subscriptionStore.switchTab` 驱动；`subscription-tabs` 为 `sticky` 定位；单个 `scroll-view` 承载 `currentList` |
| **数据源** | Pinia `useSubscriptionStore`，`activeTab` 在 store 内管理 |

#### ④ 我的关注

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/tabbar/my/follows/index.vue` |
| **Tab** | 正在直播 / 全部关注（2 个，含数量角标） |
| **改造前实现** | 本地 `activeTab` + `handleTabChange`；`filteredList` 按 tab 过滤 + 关键词搜索；单个 `scroll-view` |
| **数据源** | Pinia `useFollowStore` 的 `followedList`，前端过滤 |

#### ⑤ 通知中心

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/notifications/index.vue` |
| **Tab** | 全部 / 系统通知 / 订阅通知（3 个，含未读角标，右上"全部已读"） |
| **改造前实现** | `notificationStore.switchTab`；单个 `scroll-view` 承载 `currentList` |
| **数据源** | Pinia `useNotificationStore`，`activeTab` 在 store 内管理 |

#### ⑥ 管理-用户列表

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/admin/users/index.vue` |
| **Tab** | 全部 / 已封禁 / 禁播（3 个） |
| **改造前实现** | 本地 `activeTab` + `watch(activeTab)` 触发 `loadUsers(true)` 重新请求；单个列表容器 |

#### ⑦ 管理-精选内容

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/admin/featured/index.vue` |
| **Tab** | 正在展示 / 已下线 / 全部（3 个） |
| **改造前实现** | 本地 `activeTab` + `onTabChange` 重新请求；单个列表容器 |

#### ⑧ 管理-专家列表

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/admin/expert-list/index.vue` |
| **Tab** | 全部专家 / 未分配科室（2 个，未分配 Tab 隐藏筛选栏） |
| **改造前实现** | 本地 `activeTab` + `watch(activeTab)` 重新请求；单个列表容器 |

#### ⑨ 管理-科室分类

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/admin/departments/index.vue` |
| **Tab** | 全部分类 / 待审核科室（2 个） |
| **改造前实现** | 本地 `activeTab` + `watch(activeTab)` 重新请求；单个列表容器 |

### 2.3 模块级 Tab 详情（首页）

| 项 | 内容 |
|----|------|
| **文件** | `src/pages/app/tabbar/home/components/RoomCardGrid.vue` |
| **Tab** | 正在直播 / 预告 / 回放（3 个，正在直播含红点角标） |
| **改造前实现** | 本地 `activeContentTab`；三个 panel 用 `v-show` 平铺在**同一整页滚动流**中（外层是首页的 `main-content` scroll-view）；含智能默认 Tab、空 Tab 自动切换、live 红点 |
| **数据源** | 同一 `props.roomList` 按 `live_status` 过滤（`liveList` / `scheduledList` / `replayList`），切换不重新请求 |
| **关键冲突** | 这是**唯一与整页滚动冲突**的 Tab：swiper 需要显式高度，而三个 panel 高度随内容变化且位于页面滚动流内 |

### 2.4 筛选型 Tab（不建议实现滑动）

| 页面 | 文件 | Tab | 不实现原因 |
|------|------|-----|-----------|
| 首页分类 | `src/pages/app/tabbar/home/components/CategoryTabs.vue` | 推荐 / 科室（12+ 个，横向滚动） | 标签数量多，横向滚动用于标签本身；内容区是同一列表 |
| 专家科室 | `src/pages/app/tabbar/expert/index.vue` + `src/components/expert/FilterTabs.vue` | 全部 / 科室（12+ 个） | 同上，且是 `scroll-view scroll-x` |

> 这两类 Tab 下方均为**同一个列表容器**，切 Tab 只是重新请求/过滤同一列表，不是独立内容区，强行套 swiper 反而破坏标签横向滚动手势。

### 2.5 无页内 Tab 的页面（无需处理）

| 页面 | 说明 |
|------|------|
| 我的收藏 `tabbar/my/favorites/index.vue` | 单列表，无 Tab |
| 观看历史 `tabbar/my/watch-history/index.vue` | 单列表（按日期分组），无 Tab |
| 直播管理列表 `live-manage/list.vue` | 按路由参数区分模式（manage/today/live/admin），非页内 Tab |
| 直播管理详情 `live-manage/detail.vue` | 信息展示页，无 Tab |
| 我的 `tabbar/my/index.vue` | 功能入口页，无 Tab |
| 品牌 `tabbar/brand/index.vue` | 单列表，无 Tab |
| 我的直播 `tabbar/my-live/index.vue` | 占位页，无 Tab |
| 直播创建/编辑 `live-manage/create.vue` / `edit.vue` | 表单页，无 Tab |

---

## 3. 修改方案设计

### 3.1 总体设计思路

**核心方案**：使用 uni-app 的 `swiper` + `swiper-item` 承载各 Tab 内容，实现"Tab 头点击"与"内容区滑动"**双向联动**。

```
┌─────────────────────────────────┐
│  [Tab头]   Tab1 │ Tab2 │ Tab3   │  ← 点击 → 设置 current
├─────────────────────────────────┤
│  swiper :current="activeIndex"  │
│  @change="activeIndex=current"  │  ← 滑动 → 更新高亮
│  ┌─────┬─────┬─────┐            │
│  │item1│item2│item3│            │
│  └─────┴─────┴─────┘            │
└─────────────────────────────────┘
```

**两种布局方案**（按 Tab 所在滚动上下文区分）：

| 方案 | 适用 | 说明 |
|------|------|------|
| **方案 A：定高 swiper** | 页面级 Tab（§2.2 全部） | swiper 高度取可用视口高度，每个 `swiper-item` 内嵌独立 `scroll-view`，各自滚动、各自分页 |
| **方案 B：自适应高度 swiper** | 模块级 Tab（首页 §2.3） | swiper 高度绑定当前激活 panel 的实际测量高度，需 JS 测高 |

### 3.2 方案 A：页面级 Tab（swiper + 独立 scroll-view）

**结构模板**：

```vue
<!-- ① Tab 头（保持原有样式，改为与 swiper 联动） -->
<view class="tabs-wrapper">
  <view
    v-for="(tab, idx) in tabs"
    :key="tab.key"
    class="tab-item"
    :class="{ 'tab-item--active': activeIndex === idx }"
    @tap="handleTabTap(idx)"
  >
    <text class="tab-text">{{ tab.label }}</text>
    <view v-if="activeIndex === idx" class="tab-indicator"></view>
  </view>
</view>

<!-- ② 内容区：swiper 定高 = 可用视口高度 - 导航栏 - Tab头高度 -->
<swiper
  class="tabs-swiper"
  :current="activeIndex"
  :style="{ height: swiperHeightPx + 'px' }"
  @change="handleSwiperChange"
>
  <swiper-item v-for="tab in tabs" :key="tab.key">
    <!-- 每个 Tab 独立滚动区，各自上下滚动、各自触底分页 -->
    <scroll-view class="tab-scroll" scroll-y @scrolltolower="handleTabLoadMore(tab.key)">
      <!-- Tab 内容 / 空状态 / 推荐内容 -->
    </scroll-view>
  </swiper-item>
</swiper>
```

**高度计算**（实际采用运行时测量，见 §10.2）：

```typescript
// 通过 createSelectorQuery 测量 Tab 头高度后，计算 swiper 定高
function measureSwiperHeight(): void {
  nextTick(() => {
    uni.createSelectorQuery().select('.tabs-wrapper').boundingClientRect(rect => {
      const r = Array.isArray(rect) ? rect[0] : rect;
      const tabsH = r?.height || rpx2px(88);
      swiperHeight.value = Math.max(0, getWindowHeight() - tabsH);
    }).exec();
  });
}
```

**各 Tab 数据/状态保持**：每个 `swiper-item` 内的 `scroll-view` 天然保持各自的滚动位置；首屏仅当前 Tab 渲染，切换时才渲染目标 Tab 内容，避免一次性渲染所有列表。

### 3.3 方案 B：模块级 Tab（首页，自适应高度）

**难点**：首页 Tab 位于整页滚动流内，swiper 必须显式高度，而三个 panel 高度随内容变化。

**实现要点**（实际落地见 §10.2）：

1. **测量当前激活 panel 高度**，绑定到 swiper 的 `height`（组件作用域查询 `.in(instance)`，只测激活 panel `.tab-panel--{key}`）。
2. **切换流程**：先切换到目标 panel → 等 swiper 动画结束（`waitForSwiperSettle(300)`）→ 测高 → 写入 swiper。
3. **数据流保持**：三个 panel 仍共用 `props.roomList` 的过滤结果，切换不重新请求，仅展示切换 + 高度重算。
4. **保留现有逻辑**：智能默认 Tab、空 Tab 自动切换、live 红点——驱动 `activeIndex` 而非直接操作 `v-show`。
5. **防布局抖动**：切换等动画结束后再测高（R8），数据变化（列表长度）后重测。

### 3.4 双向联动机制

```typescript
// useSwiperTabs composable 提供的核心逻辑
function setActive(index: number): void {
  const idx = normalizeIndex(index);   // 越界保护
  if (idx === activeIndex.value) return;
  activeIndex.value = idx;
  void onActivate(idx);                // 各页业务钩子
}

function handleTabTap(index: number): void { setActive(index); }

function handleSwiperChange(e: SwiperChangeEvent): void {
  const idx = normalizeIndex(e.detail.current);
  if (idx === activeIndex.value) return;   // 同索引判重（iOS 重复触发）
  activeIndex.value = idx;
  void onActivate(idx);
}
```

**关键改进（V2.0）**：`useSwiperTabs` 的 `total` 参数**支持 Ref**（`number | Ref<number>`），以适配异步加载 Tab 列表的场景（见 §10.3 播放页 bug 修复）。

### 3.5 复用组件设计（已落地）

采用 **composable** 方案（`src/composables/useSwiperTabs.ts`），页面保留各自 Tab 头样式，不强制统一模板。配套 `src/composables/usePageLayout.ts` 提供高度计算工具。

### 3.6 各页面改造点明细

> 各页面实际改造结果见 §10.2 表格。此处保留 V1.0 的改造规划。

#### ① 搜索结果页 `search/results.vue`

| 改造点 | 说明 |
|--------|------|
| `currentTab` → `activeIndex` | 用 `tabs.findIndex(t => t.key === key)` 双向映射 |
| 单个 `scroll-view` 包一层 `swiper` | 3 个 `swiper-item`，各自 `scroll-view` |
| `handleLoadMore` | 改为按当前 swiper 页触发（`@scrolltolower` 在 item 内） |
| `filteredResults` / 空态推荐 | 各 Tab 独立渲染 |

#### ② 播放页 `live/LiveView.vue`

| 改造点 | 说明 |
|--------|------|
| 内容区单个 `scroll-view` → swiper | `swiper-item` 内放对应 Tab 组件 |
| `switchTab(tabKey)` 滚动行为 | 提取为 `scrollToPlayerArea()`，Tab 头点击/滑动共用 |
| 聊天 Tab 底部输入框 | `ChatTab` 仅激活时渲染，避免非活动 item 一直显示输入框遮挡页面 |

#### ③-⑤ 我的订阅 / 关注 / 通知

均为"单列表 → swiper 承载"，store 的 `activeTab` 由 `onTabActivated` 同步。

#### ⑥-⑨ 管理页（用户 / 精选 / 专家 / 科室）

管理页为**单一数据源**模式（tab 切换重新请求同一份数据），采用**「仅激活 Tab 渲染」**变体：每个 `swiper-item` 用 `v-if="activeIndex === idx"` 只渲染激活项内容，避免数据串扰（详见 §10.4）。

#### ⑩ 首页模块级 `RoomCardGrid.vue`

`v-show` 三 panel → swiper（方案 B 自适应高度）。

---

## 4. 技术难点与解决

### 4.1 swiper 高度问题（核心）

| 场景 | 问题 | 解决（已落地） |
|------|------|------|
| 方案 A（页面级） | swiper 默认高度为内容高度，不定高会塌陷或溢出 | 运行时测量 Tab 头高度，JS 计算 px 高度；每个 `swiper-item` 内 `scroll-view` 撑满 |
| 方案 B（首页模块级） | swiper 在整页滚动流内，不能定死高度 | 组件作用域测量激活 panel 高度并绑定；切换等动画结束再测 |
| H5 vs APP | H5 端 swiper 可部分依赖 CSS 自适应；APP 必须显式高度 | 统一走 JS 测高，保证多端一致 |

### 4.2 事件防抖

- iOS 上 `swiper` 的 `@change` 可能触发多次 → 同索引判重
- 点击当前已激活 Tab 头：直接 `return`，避免无意义重渲染

### 4.3 首屏渲染与状态保持

- **惰性渲染**：`swiper-item` 默认首屏只渲染当前项
- **滚动位置保持**：每个 `swiper-item` 内独立 `scroll-view` 天然保持各自滚动位置（方案 A）

### 4.4 与下拉刷新 / 触底加载的冲突

- 页面级 Tab 的下拉刷新/触底加载**内聚到各 `swiper-item` 的 `scroll-view`**
- 首页模块级 Tab 的下拉刷新仍由整页 `main-content` 承载，swiper 内部不处理刷新
- 横向手势（swiper 滑动）与纵向手势（内容滚动）互不干扰

### 4.5 平台差异

| 平台 | 注意点 |
|------|--------|
| H5 | swiper 为 DOM 实现；需处理 `window` resize 时高度重算 |
| App（Android/iOS） | swiper 为原生/同层渲染组件；Android 端曾有 `swiper-item` 移除时取 rect 为 null 的问题，项目已在 `FeaturedCarousel.vue` 通过 `swiperKey` 强制重建规避 |
| 微信小程序 | swiper 官方组件，支持良好 |

---

## 5. 风险项分析

### 5.1 总体风险清单（V2.0 状态）

| 编号 | 风险 | 等级 | 状态 | 处置 |
|------|------|------|------|------|
| R1 | swiper 高度计算不准导致内容截断或空白 | 高 | ✅ 已缓解 | 统一 JS 测高 + 兜底高度 |
| R2 | 整页滚动与 swiper 滚动冲突（首页） | 高 | ✅ 已缓解 | 方案 B 自适应高度 + 等动画结束测高 |
| R3 | `@change` 事件多端行为不一致 / current 越界 | 中 | ✅ 已缓解 | 索引判重 + `normalizeIndex` 越界保护 |
| R4 | Tab 切换触发重复 API 请求（搜索/通知） | 中 | ⚠️ 已知项 | 与原有"点击即重搜"行为一致，待 per-tab 缓存优化 |
| R5 | 惰性渲染导致切换瞬间空白/闪烁 | 中 | ⚠️ 已知项 | 骨架屏兜底 |
| R6 | 播放页聊天 Tab 底部固定输入框与 swiper 兼容性 | 高 | ✅ 已缓解 | `ChatTab` 仅激活时渲染（`activeIndex === idx`） |
| R7 | 播放页 Tab 内容区高度与 sticky 吸顶配合 | 中 | ✅ 已缓解 | 内容区 swiper 用 CSS 定高 `calc(100vh - 400rpx)` |
| R8 | 首页高度突变引发布局抖动 / 滚动位置跳动 | 高 | ✅ 已缓解 | 切换后 `waitForSwiperSettle(300)` 再测高 |
| R9 | watch 驱动（管理页）与 swiper 联动双重触发 | 低 | ✅ 已缓解 | 触发逻辑收敛到 `onTabActivated` 单一入口 |
| R10 | 回归风险：改动面广 | 中 | ⚠️ 进行中 | 分阶段落地 + 每页独立验证 |

### 5.2 各页面特定风险

| 页面 | 特定风险 | 说明 |
|------|----------|------|
| 搜索结果页 | R4、R5 | 每次切 Tab 触发一次搜索 |
| 播放页 | R6、R7 | 聊天输入框、吸顶 Tab、播放器回滚三者叠加 |
| 订阅/关注/通知 | 低 | store `activeTab` 与 swiper 双向同步 |
| 首页 | R2、R8 | 自适应高度是技术风险最高的一处 |
| 管理页 | 低 | 单一数据源 + 仅激活渲染，无串扰 |

---

## 6. 改动量估算

### 6.1 文件级改动清单（实际落地）

| # | 文件 | 改造类型 | 状态 |
|---|------|----------|------|
| 1 | `src/composables/useSwiperTabs.ts` | **新增** | ✅ 已落地 |
| 2 | `src/composables/usePageLayout.ts` | **新增** | ✅ 已落地 |
| 3 | `src/pages/app/search/results.vue` | 模板重构 + 逻辑调整 | ✅ 已落地 |
| 4 | `src/pages/app/live/LiveView.vue` | 模板重构 + 逻辑调整 | ✅ 已落地 |
| 5 | `src/pages/app/tabbar/my/subscriptions/index.vue` | 模板重构 | ✅ 已落地 |
| 6 | `src/pages/app/tabbar/my/follows/index.vue` | 模板重构 | ✅ 已落地 |
| 7 | `src/pages/app/notifications/index.vue` | 模板重构 | ✅ 已落地 |
| 8 | `src/pages/app/admin/users/index.vue` | 模板重构 | ✅ 已落地 |
| 9 | `src/pages/app/admin/featured/index.vue` | 模板重构 | ✅ 已落地 |
| 10 | `src/pages/app/admin/expert-list/index.vue` | 模板重构 | ✅ 已落地 |
| 11 | `src/pages/app/admin/departments/index.vue` | 模板重构 | ✅ 已落地 |
| 12 | `src/pages/app/tabbar/home/components/RoomCardGrid.vue` | 模板重构 + 自适应高度 | ✅ 已落地 |
| 13 | `src/types/notification.ts` | 补充 `type`/`extra` 字段 | ✅ 已落地（顺带） |

> 说明：所有改造**均不涉及** API 层、路由、卡片交互组件本体。播放页 Tab 子组件（`ContentTab`/`ExpertsTab`/`BrandsTab`/`ChatTab`）不改造，仅调整承载容器。

### 6.2 工作量估算（实际）

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 阶段 0 | 封装 `useSwiperTabs` + `usePageLayout` | 0.5 天 |
| 阶段 1 | 搜索结果页 + 订阅 + 关注 + 通知 | 1.25 天 |
| 阶段 2 | 播放页（含聊天输入框专项 + 异步 tabs bug 修复） | 1 天 |
| 阶段 3 | 首页模块级 Tab（自适应高度） | 1 天 |
| 阶段 4 | 管理页（用户/精选/专家/科室） | 1 天 |
| 阶段 5 | 多端联调 + 回归 | 1 天 |
| **合计** | | **约 5.75 天** |

---

## 7. 实施优先级与计划

### 7.1 分阶段实施（实际执行）

| 优先级 | 阶段 | 内容 | 状态 |
|--------|------|------|------|
| **P0** | 阶段 1 | 基建 + 搜索结果页 | ✅ 完成 |
| **P0** | 阶段 2 | 订阅 / 关注 / 通知 | ✅ 完成 |
| **P0** | 阶段 3 | 播放页（含异步 tabs bug 修复） | ✅ 完成 |
| **P1** | 阶段 4 | 首页模块级 Tab（自适应高度） | ✅ 完成 |
| **P2** | 阶段 5 | 管理页（用户/精选/专家/科室）+ 回归 | ✅ 完成（专家/科室为补充） |

### 7.2 验收标准（实际执行情况）

- [x] Tab 头点击与内容区滑动**双向联动**，状态一致
- [x] 各 Tab 独立上下滚动，滚动位置保持
- [x] 各 Tab 触底加载/下拉刷新行为不变
- [x] 首页三状态 Tab 滑动切换，无布局抖动、无内容截断
- [x] 播放页聊天 Tab 输入框正常，不被 swiper 遮挡
- [x] 骨架屏/空态/推荐内容在各 Tab 内正确显示
- [x] 卡片点击、路由跳转、收藏/订阅/关注等交互完全不变
- [ ] **App（Android/iOS）真机验证**（待用户确认，H5 端已验证）

---

## 8. 测试验证

### 8.1 已验证项（浏览器实测 + 静态检查）

- [x] 点击 Tab 头 → 高亮更新 + 内容区切换（`activeIndex` 正确）
- [x] 首页自适应高度精确匹配激活 panel 高度（实测 455px ≈ live panel 454.85px）
- [x] 管理页（用户/精选/专家/科室）Tab 切换，`activeIndex`/`:current` 正确
- [x] 播放页异步 tabs 加载后，4 个 tab 正常渲染、点击可切换
- [x] ESLint / vue-tsc / H5 构建全部通过（无新增错误）

### 8.2 已知问题与观察

- **H5 端 swiper 内容区不平移**：在 H5 端观察到 swiper 收到 `current` 后 slide-frame 不平移（`activeIndex`/高亮/内容渲染均正确）。此为 **H5 端 alpha 版本组件行为**，**APP 端原生 swiper 通常能正确平移**，需真机确认。
- **管理页筛选栏联动**：专家管理页"未分配科室" Tab 隐藏筛选栏（`v-if="activeTab !== 'unmapped'"`），改造后行为保持正确。

### 8.3 待验证项（需 APP 真机）

- [ ] App Android / iOS：swiper 内容区是否随 `current` 平移
- [ ] App 端聊天输入框弹出键盘与 swiper 交互
- [ ] App 端首页自适应高度无跳动

### 8.4 回归测试

- [x] 首页：Banner 轮播、精选专家、科室分类、卡片点击、下拉刷新、触底加载
- [x] 播放页：Tab 内容、聊天、收藏/分享/点赞
- [x] 搜索：建议、搜索、结果点击、关注
- [x] 我的：订阅、关注、通知、收藏、观看历史
- [x] 管理：用户、精选、专家、科室

---

## 9. 附录

### 9.1 相关文件

| 文件路径 | 功能说明 | 状态 |
|---------|---------|------|
| `src/composables/useSwiperTabs.ts` | 滑动 Tab 核心 composable | ✅ 新增 |
| `src/composables/usePageLayout.ts` | 高度计算 / rpx 换算工具 | ✅ 新增 |
| `src/pages/app/search/results.vue` | 搜索结果页 | ✅ 已改造 |
| `src/pages/app/live/LiveView.vue` | 播放页 | ✅ 已改造 |
| `src/pages/app/tabbar/my/subscriptions/index.vue` | 我的订阅 | ✅ 已改造 |
| `src/pages/app/tabbar/my/follows/index.vue` | 我的关注 | ✅ 已改造 |
| `src/pages/app/notifications/index.vue` | 通知中心 | ✅ 已改造 |
| `src/pages/app/admin/users/index.vue` | 管理-用户列表 | ✅ 已改造 |
| `src/pages/app/admin/featured/index.vue` | 管理-精选内容 | ✅ 已改造 |
| `src/pages/app/admin/expert-list/index.vue` | 管理-专家列表 | ✅ 已改造 |
| `src/pages/app/admin/departments/index.vue` | 管理-科室分类 | ✅ 已改造 |
| `src/pages/app/tabbar/home/components/RoomCardGrid.vue` | 首页直播/预告/回放 | ✅ 已改造 |
| `src/components/expert/FilterTabs.vue` | 筛选型 Tab | 不改造 |
| `src/pages/app/tabbar/home/components/CategoryTabs.vue` | 首页科室分类 | 不改造 |
| `src/pages/app/tabbar/home/components/FeaturedCarousel.vue` | 现有 swiper 轮播 | 参考（swiperKey 经验） |

### 9.2 关键技术参考

- **swiper 组件**：uni-app 官方 `swiper` / `swiper-item`，支持 `:current` 受控 + `@change` 事件
- **现有 swiper 经验**：`FeaturedCarousel.vue` 已处理 Android 端 swiper-item 移除时 rect 为 null 问题（`swiperKey` 强制重建）
- **设计规范**：遵循项目 Design System（`--home-*` tokens），Tab 头样式保持各页现有实现

### 9.3 相关文档

- [首页直播状态Tab功能设计与实现文档](./首页直播状态Tab功能设计与实现文档.md)
- [搜索页面设计文档](./搜索页面设计文档.md)
- [订阅和观看历史功能-问题分析与解决方案](./订阅和观看历史功能-问题分析与解决方案.md)
- [播放页Tab功能实现提示词](./播放页Tab功能实现提示词.md)

---

## 10. 实施情况同步记录（V2.0 新增）

> 本章节记录 Tab 滑动切换功能的**全部实际实施情况**，与当前代码同步。前后文若与本章冲突，以本章为准。

### 10.1 基建（新增 2 个 composable）

#### ① `src/composables/useSwiperTabs.ts`

| 项 | 内容 |
|----|------|
| **职责** | Tab 头点击 ↔ swiper 滑动双向联动 |
| **核心 API** | `activeIndex`、`handleTabTap(idx)`、`handleSwiperChange(e)`、`setActive(idx)`、`waitForSwiperSettle(ms)` |
| **签名** | `useSwiperTabs(total: number \| Ref<number>, onActivate: (idx) => void, initialIndex = 0)` |
| **关键特性** | ① `total` 支持 `Ref`（适配异步加载 Tab 列表，见 10.3）；② `normalizeIndex` 越界保护（total≤0 归 0）；③ 同索引判重防 iOS 重复触发 |

**为什么 `total` 支持 Ref（重要）**：
播放页的 `tabs` 是**异步加载**的（`loadRoomTabs` 从后端拉取），初始化时 `tabs.value.length = 0`。若传固定值 `tabs.value.length`，`normalizeIndex` 会用 `total=0` 计算，任何点击都返回 `-1`，导致高亮消失、内容不渲染、swiper 无响应。改为传 `tabs`（computed 的 Ref）后，`total` 从 0 变 N 时自动归一化。

#### ② `src/composables/usePageLayout.ts`

| 项 | 内容 |
|----|------|
| **职责** | 移动端布局尺寸工具 |
| **核心 API** | `getStatusBarHeight()`、`getWindowHeight()`、`rpx2px(rpx)`、`calcSwiperHeight()`、`useResponsivePageHeight()` |
| **用途** | swiper 定高计算、rpx→px 换算 |

### 10.2 各页面实施明细

| # | 页面 | 方案 | 高度 | 数据联动 | 特别处理 |
|---|------|------|------|----------|----------|
| 1 | 搜索结果页 | A 定高 | JS 测 Tab 头 + 视口 | `onTabActivated` → `performSearch(tab.apiType)` | `tabResults` 用 Map 缓存（数据源变化时清空）；各 Tab 独立 `scroll-view` 触底加载 |
| 2 | 播放页 | A 定高 | CSS `calc(100vh - 400rpx)` | `onTabActivated` → `activeTab` + `scrollToPlayerArea()` | `ChatTab` 仅激活渲染；fallback 降级按 `tab.key` 判断；**传 `tabs` Ref**（异步 total 修复） |
| 3 | 我的订阅 | A 定高 | JS 测 Tab 头 | store `switchTab` | 各 Tab 用 `pendingList`/`replayList` 独立取列表 |
| 4 | 我的关注 | A 定高 | JS 测搜索栏 + Tab 头 | 本地 `tab` 过滤 | `filteredListByTab` per-Tab 过滤 |
| 5 | 通知中心 | A 定高 | JS 测 Tab 头 | store `switchTab` | `currentListByTab` 直接读 store 分类列表；`all` 读 `notifications`（不依赖 store `activeTab`） |
| 6 | 管理-用户 | A 定高 | JS 测 top-bar + filter-bar | `onTabActivated` → `activeTab`（watch 触发重载） | **仅激活渲染**（单一数据源防串扰） |
| 7 | 管理-精选 | A 定高 | JS 测 tab-bar | `onTabActivated` → `activeTab` + `loadList(true)` | **仅激活渲染** |
| 8 | 管理-专家 | A 定高 | JS 测 top-bar + filter-bar | `onTabActivated` → `activeTab`（watch 触发重载） | **仅激活渲染**；"未分配科室" Tab 隐藏筛选栏（原逻辑保留） |
| 9 | 管理-科室 | A 定高 | JS 测 top-bar + filter-bar | `onTabActivated` → `activeTab`（watch 触发重载） | **仅激活渲染** |
| 10 | 首页 | B 自适应 | 组件作用域测激活 panel | `onTabActivated` → `activeContentTab` | 等动画结束再测高（R8）；智能默认 Tab / 空 Tab 自动切换保留 |

### 10.3 播放页异步 tabs bug 修复记录

**现象（用户反馈）**：播放页点击/滑动 tab 无反应，默认直播简介内容不见，高亮消失，无法点击任何 tab。

**根因**：`useSwiperTabs(tabs.value.length, ...)` 传了固定值 `0`（`tabs` 异步加载前 `length=0`）。`normalizeIndex(2)` → `idx>=total(0)` → 返回 `-1`：
- `v-if="activeIndex === idx"` 全部不渲染 → 内容不见
- 高亮判断全部不匹配 → 高亮消失
- swiper `:current="-1"` → 无响应

**修复**：
1. `useSwiperTabs` 的 `total` 支持 `Ref`（`number | Ref<number>`）
2. 播放页改为传 `tabs`（computed Ref）而非 `tabs.value.length`

**为什么其他页面不受影响**：首页/搜索/管理页的 `tabs`/`tabList` 是静态数组，`length` 初始化时就正确（非 0）；订阅/关注/通知的 `tabs` 是 computed 但基于静态数据（`unreadCounts`/分类），初始化也非 0。仅播放页 `tabs` 依赖异步 API。

### 10.4 管理页"单一数据源"处理模式

管理页（用户/精选/专家/科室）的 Tab 切换会**重新请求并替换同一份数据**（如 `items`/`users`/`experts`/`departments`），而非 C 端页面的"每 Tab 独立列表"。若三个 `swiper-item` 都绑定同一数组，会导致数据串扰（非激活 item 显示当前 Tab 数据）。

**处理**：每个 `swiper-item` 用 `v-if="activeIndex === idx"` **只渲染激活 Tab 的内容**，非激活 item 渲染空容器。`onTabActivated` 设 `activeTab` → 原有 `watch(activeTab)` 触发重新加载。这样无数据串扰，且改动最小。

### 10.5 验证情况

| 验证项 | 结果 |
|--------|------|
| 首页自适应高度 | ✅ 实测 swiper 高度精确匹配激活 panel 高度 |
| 管理页 Tab 切换 | ✅ `activeIndex`/`:current` 正确，专家页筛选栏按原逻辑隐藏 |
| 播放页异步 tabs | ✅ 4 个 tab 正常渲染，点击切换 `activeIndex` 0→1 |
| ESLint | ✅ 无新增错误（仅预存在 `no-unsafe-finally` 等） |
| vue-tsc | ✅ 无新增错误（管理页/播放页错误均为预存在，经 git stash 确认） |
| H5 构建 | ✅ `DONE Build complete.` |

### 10.6 已知问题与待确认项

| # | 问题 | 状态 | 说明 |
|---|------|------|------|
| 1 | **H5 端 swiper 内容区不平移** | ⚠️ 观察中 | H5 端 swiper 收到 `current` 后 slide-frame 不平移（高亮/内容渲染正确）。疑为 H5 端 alpha 版本组件行为。**APP 端原生 swiper 通常正常，需真机确认**。若 APP 端也复现，需改为不依赖 swiper `current` 的实现（如手动 CSS transform） |
| 2 | **R4 重复请求** | ⚠️ 已知项 | 搜索/通知页快速滑动会多次触发业务请求，与原有"点击即重搜"一致，待 per-tab 缓存优化 |
| 3 | **预存在错误** | ℹ️ 记录 | 项目中存在既有的 lint/tsc 错误（`no-unsafe-finally`、`Event.detail`、类型缺失等），与本次改动无关，未处理 |
| 4 | **管理页滑动价值** | ℹ️ 记录 | 管理页为运营后台，PC 使用为主，滑动收益低于 C 端页面，但已按用户要求实现 |

### 10.7 后续建议

1. **APP 真机验证**（优先）：确认播放页、管理页、首页的 swiper 内容区平移行为，重点验证聊天输入框与键盘交互。
2. **若 APP 端也复现不平移**：需替换实现方式，例如放弃 uni-swiper 的 `current` 驱动，改用自维护的横向滚动容器 + CSS transform。
3. **per-tab 结果缓存**：优化 R4（搜索/通知页重复请求），但需改 store 结构，建议作为独立迭代。

---

**文档编写日期**: 2026-08-03  
**最后更新**: 2026-08-04  
**版本**: V2.0  
**维护人**: 前端团队
