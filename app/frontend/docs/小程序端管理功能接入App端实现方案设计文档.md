# 小程序端管理功能接入 App 端 — 实现方案设计文档

> **文档版本**：v1.0
> **创建日期**：2026-08-06
> **覆盖范围**：小程序端（`app-wechat-frontend-1` wechat 分支）管理功能借鉴接入 App 端（`src/pages/app/`）+ 首页焦点图样式对齐
> **相关文档**：`frontend-admin-connect-plan.md`（上一轮后端融合接入计划）、`留言管理页面实施文档.md`、`用户管理页面实施文档.md`、`专家分类管理App端设计方案.md`、`平台分层架构规范（阶段零点五完成）.md`
> **状态**：方案评审稿

---

# 第一篇 文档编写架构与规范分析

## 一、docs 目录文档体系盘点

经阅读 docs 目录下的实施文档与设计文档，现有文档可归纳为 4 类，各自承担不同职责：

| 类型 | 代表文档 | 适用场景 | 结构特征 |
|------|---------|---------|---------|
| **页面级实施文档** | `留言管理页面实施文档.md`（14 章）、`用户管理页面实施文档.md`、`轮播图管理页面实施文档.md` | 单个管理页面的完整落地指引 | 文件头引用块 → 页面定位 → 功能清单 → 布局 → 数据流 → 接口定义 → 类型定义 → 后端支持度对照 → API 依赖 → 状态管理 → 实施阶段 → 实施步骤 → 风险 → 验收标准 → 变更记录 |
| **模块级设计方案** | `专家分类管理App端设计方案.md`（17 章）、`管理员页面设计文档.md` | 复杂模块的多页面/多组件设计 | 功能定位 → 接口对照 → 文件结构 → 类型/API/Store → 逐 Tab 布局与交互矩阵 → 状态转换 → 空态边界 → 入口参数 → 实施顺序 |
| **批量接入计划** | `frontend-admin-connect-plan.md` | 后端融合后多模块批量接入（与本需求同构） | 后端状态简述 → 前端现状盘点 → 批次划分策略 → 工作项级计划（文件/行号/改法/风险） |
| **架构规范** | `平台分层架构规范（阶段零点五完成）.md`、`RBAC接入指南.md` | 长期强制约束的开发准则 | 目录分层规则 → 导入规范 → 决策树 → 禁止清单 → 检查清单 |

## 二、文档编写规范提取（通用要素）

对 4 类文档交叉提取出的**共同编写规范**：

| 规范要素 | 写法要求 | 示例出处 |
|---------|---------|---------|
| 文档头 | `> 版本/日期/覆盖范围/状态` 引用块 | frontend-admin-connect-plan |
| 表格为王 | 所有维度对比、功能清单、交互、风险均用表格，禁止大段散文 | 全部文档 |
| ASCII 布局图 | 页面布局必须画 `┌──┐` 示意图 | 留言/专家分类文档 |
| 交互矩阵 | 功能/触发方式/前端操作/后端调用/成功后行为 5 列 | 专家分类文档 §9.3 |
| 状态转换图 | `idle → loading → loaded → error → retry` 箭头流 | 专家分类文档 §13 |
| 后端支持度对照 | ✅/⚠️/❌ 三态标注 + 缺口处理策略表 | 留言管理文档 §7 |
| 风险表 | 风险/概率/缓解 3 列 | 全部文档 |
| 实施顺序 | 步骤编号 + 依赖关系 + 工作量估算 | 全部文档 |
| 验收标准 | Markdown checklist（`- [ ]`） | 实施文档系列 |
| 变更记录 | 版本/日期/变更内容，尾部维护 | 全部文档 |
| 命名规范 | `XX页面实施文档.md` / `XX设计方案.md` / `XX接入计划.md` | — |

## 三、本需求适用的规范与架构选型

### 3.1 文档结构选型

本需求 = **小程序 8 个缺失管理模块批量接入 + 首页焦点图对齐 + 通用基建补齐**，与 `frontend-admin-connect-plan.md` 场景完全同构。因此：

**采用「总方案 + 子实施文档」双层结构**：

```
docs/
├── 小程序端管理功能接入App端实现方案设计文档.md   ← 本文件（总方案：问题/批次/风险/路线图）
└── （各模块落地时，按页面实施文档 14 章模板分别编写子文档）
    ├── 标签管理页面实施文档.md（待建）
    ├── 品牌管理页面实施文档.md（待建）
    ├── 留言管理页面实施文档.md（复用现有模板）
    ├── 内容安全管理页面实施文档.md（待建）
    └── ...
```

**理由**：
1. 批量接入需要"批次/依赖/风险"的全局视图，单一页面模板无法承载 → 总方案承担
2. 每个页面落地需要"文件/行号/接口/验收"的可执行粒度 → 子实施文档承担
3. 与仓库既有惯例（frontend-admin-connect-plan + 页面实施文档）一致，不引入新文档体系

### 3.2 技术架构选型

| 架构项 | 选型 | 依据 |
|-------|------|------|
| 组件分层 | 沿用 `components/common|app|h5|mp` 分层 + `@/` 别名 + easycom | 平台分层架构规范（强制） |
| 页面模板 | 沿用 App 现有 admin 页面范式：`useSwiperTabs` + `ModalDialog` + 无限滚动 + 骨架/空/错三态 | users/index.vue、featured/index.vue 已验证 |
| 图片处理 | 统一 `<ProxyImage>` + `resolveMediaUrl` + `DEFAULT_AVATAR` | AGENTS.md 强制（外链图 App 端必须本地缓存） |
| API 层 | 沿用双网关（core=`BASE_API_URL` / users=`AUTH_API_URL`）+ `get(url, params, {auth})` 签名 | request.ts、adminUsers.ts |
| **权限守卫（新增基建）** | 新建 `useAdminGuard` 组合式函数（requireAuth + isAdmin 判定 + 非管理员返回提示） | App 现有 admin 页面无守卫（users/index.vue 直接拉数据），小程序有 `ensureAdminAccess`，需补齐统一 |
| 状态管理 | 页面内 ref/computed（参照现有 admin 页面），不引入 Store | 专家分类文档 §6 备注：非跨 Tab 共享不建 Store |
| 焦点图 | 3D 效果移植 + 保留 App 混排能力 | 详见第八章 |

---

# 第二篇 实现方案设计

## 四、问题定义

### 4.1 背景

App 端与小程序端共用后端。后端已完成小程序管理功能融合（参考 `frontend-admin-connect-plan.md`：用户/房间/留言/内容安全/专家科室/通知/精选内容等接口已上线）。小程序端管理页面已基本完成（12 个模块、22 个文件、约 13,400 行），App 端管理能力明显落后。

### 4.2 当前问题

| # | 问题 | 现状 | 影响 |
|:--:|------|------|------|
| P1 | **管理页面缺失** | App 端仅 6 个管理入口（用户/专家分类/专家/轮播图/推送通知/我的直播），小程序端多出 8 个模块：标签管理、品牌管理、品牌成员、品牌商品、留言管理、内容安全、Tab 管理、全站直播间运营 | 管理能力不对等，运营只能依赖小程序端 |
| P2 | **API 半就绪** | App 端 `tag.ts`/`brand.ts`（CRUD 部分）/`tab.ts`/`room.ts`(getAdminRooms)/`category.ts` 已封装；`message.ts`/`contentSafety`/`brand-products`/`brands-members`/`tabs-sort` 缺失 | 各模块落地成本差异大，需分批 |
| P3 | **两端代码不可直接拷贝** | 请求层签名不同（`get(url,params,{auth})` vs `request.get(url,{data,auth})`）、图片链路不同（ProxyImage vs 原生 image）、样式变量不同（`--home-*` vs `--color-*`）、权限守卫不同（无 vs ensureAdminAccess） | 必须"借鉴重写"，不能"复制粘贴" |
| P4 | **权限入口无守卫** | App 端 `my/index.vue` 的 `handleAdminNav` 与 admin 页面均无 `isAdmin` 判定，靠后端 401 兜底 | 非管理员可见入口、可进入页面（体验差，安全弱） |
| P5 | **分类双体系口径未对齐** | 小程序走 `/admin/categories`，App 走 `/admin/expert-departments`；`category.ts` 全套接口标注"当前无前端调用方" | 存在重复建设风险，需先确认 |
| P6 | **首页焦点图视觉不一致** | 小程序为 3D 卡片轮播（缩放/变暗/层级），App 为平面轮播；小程序支持 expert/brand 跳转，App 不支持 | 两端体验割裂 |

### 4.3 目标

1. **能力对齐**：App 端补齐 8 个缺失管理模块，管理能力与小程序端对齐
2. **复用最大化**：已就绪 API 直接复用，缺失 API 照小程序契约封装，杜绝重复开发
3. **规范统一**：所有新页面按 App 现有 admin 范式 + 平台分层规范落地，形成可复制模板
4. **体验一致**：首页焦点图对齐（3D 效果 + 跳转能力补齐）
5. **安全补齐**：统一 admin 权限守卫，入口与页面双重控制

## 五、方案总览

### 5.1 批次划分

按「API 就绪度 × 依赖复杂度」分 4 批（与 frontend-admin-connect-plan 的批次原则一致）：

| 批次 | 内容 | 依赖 | 说明 |
|:----:|------|------|------|
| **P0** | 统一权限守卫基建 + 标签管理页 | 无 | 守卫是全部后续页面的前置；标签 API 已就绪，作为"标准范式页" |
| **P1** | 品牌管理页 + 直播间运营增强 | 无（API 已就绪） | 品牌 CRUD API 就绪；admin 房间列表已有，补编辑能力 |
| **P2** | 留言管理 + 内容安全 | 需补 API 封装（后端已上线） | 参考 frontend-admin-connect-plan：留言/内容安全后端已融合 |
| **P3** | Tab 独立管理页 + 品牌成员/商品 | 需补 API 封装 + 产品确认 | sort/成员/商品接口需与后端核对 |
| **并行** | 首页焦点图 3D 对齐 + expert/brand 跳转 | 无 | 独立工作项，可与各批并行 |
| **待定** | 分类双体系对齐（C1） | 需与后端确认口径 | 确认前不动作 |

### 5.2 涉及文件全景

```
新增：
  src/composables/useAdminGuard.ts                     ← P0 统一守卫基建
  src/pages/app/admin/tags/index.vue                   ← P0 标签管理
  src/pages/app/admin/brands/index.vue                 ← P1 品牌管理
  src/pages/app/admin/messages/index.vue               ← P2 留言管理
  src/pages/app/admin/content-safety/index.vue         ← P2 内容安全（规则+日志双 Tab，或两页）
  src/pages/app/admin/room-tabs/index.vue              ← P3 Tab 独立管理页
  src/pages/app/admin/brand-members/index.vue          ← P3 品牌成员
  src/pages/app/admin/brand-products/index.vue         ← P3 品牌商品
  src/api/contentSafety.ts                             ← P2 新增
  src/types/contentSafety.ts                           ← P2 新增

修改：
  src/api/message.ts                                   ← P2 追加 3 函数
  src/api/brand.ts                                     ← P3 追加 members/products
  src/api/tab.ts                                       ← P3 追加 sortTabs
  src/pages/app/tabbar/my/index.vue                    ← 各批同步补 adminRoutes 入口 + isAdmin 可见性
  src/pages.json                                       ← 各批同步注册路由
  src/pages/app/live-manage/list.vue                   ← P1 admin 模式补编辑操作
  src/pages/app/tabbar/home/components/FeaturedCarousel.vue  ← 并行：3D + 跳转
  src/pages/app/admin/featured/index.vue               ← 并行：表单补 expert/brand 目标类型
```

## 六、批次详细方案

### 6.1 P0：统一权限守卫 + 标签管理（标准范式页）

#### 6.1.1 统一权限守卫 `useAdminGuard`

**为什么需要**：App 端现有 admin 页面无页面级守卫（`users/index.vue` 直接拉数据）；小程序端有 `ensureAdminAccess()`（未登录跳 `OneTapLogin?redirect=`）。新页面若各写各的守卫逻辑，会出现 8 种变体；若照抄小程序逻辑，会引入 App 端不存在的登录跳转约定。统一守卫让后续所有页面获得一致的安全基线。

**方案**：

```typescript
// src/composables/useAdminGuard.ts
// 页面 onShow 中调用：返回是否具备管理员访问资格
export function useAdminGuard(redirectPath?: string): boolean {
  const authStore = useAuthStore();
  if (!authStore.isLoggedIn) {
    uni.navigateTo({ url: `${APP_LOGIN_PATH}?redirect=${encodeURIComponent(redirectPath || '')}` });
    return false;
  }
  if (!authStore.isAdmin) {
    uni.showToast({ title: '暂无访问权限', icon: 'none' });
    uni.navigateBack(); // 或跳回我的页
    return false;
  }
  return true;
}
```

**配套改造**：
- `my/index.vue` 的「管理功能」区块改为 `v-if="authStore.isAdmin"` 渲染（当前无条件渲染）
- 现有 admin 页面（users/departments/expert-list/featured/notification-push）后续统一接入守卫（低优先，随 P0 一并处理）

**效果**：入口不可见 + 页面双重校验；未登录跳登录页并带回跳参数；非管理员 toast 提示并返回。

#### 6.1.2 标签管理页

| 项 | 详情 |
|---|---|
| 小程序参考 | `TagList.vue`(444) + `TagFormDialog.vue`(449) |
| App API 现状 | ✅ `src/api/tag.ts:66-102` 已封装 `createTag/updateTag/deleteTag/getAdminTags`（`/admin/tags` 全套） |
| 新建文件 | `src/pages/app/admin/tags/index.vue`（列表 + `ModalDialog` 表单弹窗） |
| 功能 | 名称/slug 搜索、CRUD、slug 校验（小写字母数字连字符）、启停开关、软删除确认 |
| 页面规范 | 套用 App admin 范式：`useSwiperTabs`（全部/已启用/已禁用）+ 无限滚动 + 三态 |
| 注册 | `pages.json` + `my/index.vue` adminRoutes 加 `tags` |

**效果**：App 端首个"零 API 成本"管理页，同时沉淀标准页面模板供后续 7 个模块复用。

### 6.2 P1：品牌管理页 + 直播间运营增强

#### 6.2.1 品牌管理页

| 项 | 详情 |
|---|---|
| 小程序参考 | `BrandAdminList.vue`(777) |
| App API 现状 | ✅ `brand.ts:52-85` 全套 CRUD + `brandTopics.ts` 专题绑定 |
| 新建文件 | `src/pages/app/admin/brands/index.vue` |
| 注意 | 小程序"停用=DELETE 软删除"语义，App 端保留 `is_active` 语义，与后端确认后再定 |
| 依赖 | P0 守卫 |

#### 6.2.2 直播间运营增强（改造现有页）

| 项 | 详情 |
|---|---|
| 现状 | `live-manage/list.vue` 的 `mode=admin` 已有全站房间列表（`getAdminRooms` + 标题搜索 + 公开/私密筛选 + 房主尾号），但 `handleMoreAction` 对 admin 模式直接 return，**纯只读** |
| 改造 | 为 admin 模式补卡片操作菜单：编辑（标题/简介/私密/封面）→ 复用 `live-manage/edit.vue` 或新增轻量弹窗；清空留言（跳转留言管理页带 roomId）；删除（`deleteRoom`，需后端确认管理员权限） |
| 参照 | 小程序 `AdminRoomEditDialog.vue`(702) 的交互 |
| 风险 | `updateRoom`(PUT `/rooms/{id}`)/`deleteRoom` 非 admin 专用端点，后端是否放行管理员操作他人房间**需联调验证**；若后端不允许，本批仅保留只读 + 跳转留言管理 |

### 6.3 P2：留言管理 + 内容安全

#### 6.3.1 留言管理

| 项 | 详情 |
|---|---|
| 小程序参考 | `RoomMessageList.vue`(746)（**排除**遗留的 `MessageReplyDialog.vue`——孤儿组件，依赖的 `replyMessage` 不存在） |
| API 现状 | ❌ `message.ts` 仅公开接口 |
| API 追加 | `getAdminMessages`(GET `/admin/messages`)、`batchDeleteAdminMessages`(POST `/admin/messages/batch-delete`)、`clearRoomMessages`(DELETE `/admin/rooms/{id}/messages`) |
| 类型追加 | `AdminMessageItem` / `AdminMessageQueryParams` / `AdminMessagePageResult` / `BatchDeleteMessagesPayload`（照 `留言管理页面实施文档.md` §6 已定义契约） |
| 新建页面 | `src/pages/app/admin/messages/index.vue`，按 `留言管理页面实施文档.md` 的 14 章模板实施（时间 Tab/搜索/筛选摘要/选择模式/批量删除/清空房间） |
| 联动迁移 | 智能搜索解析 + 昵称归一化逻辑（小程序 `roomMessageNormalize`） |
| 后端现状 | ✅ 已上线（frontend-admin-connect-plan §一） |

#### 6.3.2 内容安全

| 项 | 详情 |
|---|---|
| 小程序参考 | `ContentSafetyRuleList`(400) + `RuleFormDialog`(561) + `LogList`(307) |
| API 现状 | ❌ 完全空白 |
| 新增 | `api/contentSafety.ts` + `types/contentSafety.ts`：`GET/POST /admin/content-safety/rules`、`PATCH /admin/content-safety/rules/{id}`、`GET /admin/content-safety/logs` |
| 新建页面 | `src/pages/app/admin/content-safety/index.vue`（规则管理 + 处理记录双 Tab） |
| 核心算法迁移 | `groupContentSafetyRules`（按词跨位置合并）→ `src/utils/contentSafetyDisplay.ts` |
| ⚠️ 后端风险 | frontend-admin-connect-plan 明确：内容安全 schema/model 字段不一致、DDL 不完整——**本模块开工前必须与后端确认字段契约**，否则联调阻塞 |

### 6.4 P3：Tab 独立管理页 + 品牌成员/商品

| 模块 | API 动作 | 页面 | 前置 |
|------|---------|------|------|
| Tab 独立管理页 | `tab.ts` 追加 `sortTabs`(PATCH `/admin/rooms/{id}/tabs/sort`)；确认后端是否实现（小程序对 404 有降级） | `admin/room-tabs/index.vue` | 与产品确认是否需要全站 Tab 治理 |
| 品牌成员 | `brand.ts` 追加 `GET/POST /admin/brands/{id}/members`、`DELETE /admin/brands/{id}/members/{uid}` | `admin/brand-members/index.vue` | 产品确认 App 端开放品牌管理入口 |
| 品牌商品 | `brand.ts` 追加 `GET /admin/brand-products`、`PATCH/DELETE /admin/brand-products/{id}` | `admin/brand-products/index.vue` | 同上 |

**为什么放最后**：依赖产品决策（App 端是否开放品牌管理）+ 后端契约确认（sort/成员/商品端点是否已随融合上线）。

### 6.5 并行工作项：首页焦点图对齐

#### 6.5.1 3D 卡片效果移植

| 项 | 详情 |
|---|---|
| 参照 | 小程序 `Banner3D.vue`：中间 `scale(1)`/左右 `scale(0.85)` + `opacity 0.65` + `brightness(0.82)` + z-index 分层 + 露边 72rpx |
| 落地 | 将 `getCardClass()` 缩放逻辑移植进 `FeaturedCarousel.vue`，**保留 App 差异化能力**：upcoming 预告混排 + CTA 按钮 + ProxyImage + 自定义胶囊指示器 + swiperKey 强制重建 |
| 交互补充 | 触摸暂停自动播放、松手 8 秒恢复（约 20 行）；点侧卡先切中不跳转 |
| ⚠️ 注意 | `swiperKey` 机制是 App Android 端兼容的关键（`SWIPER-ITEM.remove` 时 `getBoundingClientRect` 为 null 的 bug），改造不得破坏 |

#### 6.5.2 跳转能力补齐

`handleCampaignClick` 增加 `expert`（→ `/pages/app/expert/detail?id=`）与 `brand`（→ `/pages/app/brand/detail?id=`）分支（落地页已存在，约 15 行）；同步在 `admin/featured/index.vue` 表单目标类型中补这两个选项。

**效果**：两端焦点图视觉对齐（3D 封面流），App 保留更丰富的信息密度（预告置顶 + CTA），跳转能力超越小程序端。

## 七、通用改造清单（每个模块落地必过）

从小程序页面"借鉴重写"到 App 端的**标准 4 层映射**：

| 层 | 小程序写法 | App 端写法 | 说明 |
|----|-----------|-----------|------|
| ① 请求 | `request.get(url, {data, auth})` | `get(url, params, {auth})` | 所有 API 调用行改写；上传走 `uni.uploadFile` + `getToken()` 手拼 header 模式（参考 `featured.ts:69-90`），**字段名以 App 端现有契约为准**（`file`，勿照抄小程序的 `image`） |
| ② 图片 | `<image>` + `resolveXxxUrl` | `<ProxyImage>` + `resolveMediaUrl` + `DEFAULT_AVATAR` | 外链图必须 ProxyImage，否则 App 端白屏 |
| ③ 样式/组件 | `--color-*` 变量 + 自绘弹窗/分页 | `--home-*` 变量 + easycom（`ModalDialog`）+ `useSwiperTabs` + 无限滚动 | 不引入小程序自绘弹窗 |
| ④ 守卫 | `ensureAdminAccess()` | `useAdminGuard()`（P0 基建） | 未登录跳登录页带回跳、非管理员 toast |

## 八、风险与应对

| # | 风险 | 概率 | 影响 | 应对方案 |
|:--:|------|:----:|------|---------|
| R1 | **网关/基址错误**：`adminUsers` 走 users 网关，其余走 core 网关；新封装接口走错网关 → 404/鉴权失败 | 中 | 高 | 每个新 API 文件按 `adminUsers.ts` 的 `usersUrl()` 模式显式声明网关；开工前与后端确认端点归属清单 |
| R2 | **权限语义**：`updateRoom`/`deleteRoom` 为普通端点，管理员改他人房间可能被后端拒绝 | 中 | 中 | P1 联调验证；若拒绝则 admin 模式保持只读 + 跳转留言管理 |
| R3 | **内容安全后端字段不一致**（schema/model 不一致、DDL 不完整，frontend-admin-connect-plan 已记录） | 高 | 高 | P2 开工前先与后端对齐字段契约；联调窗口预留 |
| R4 | **上传字段名差异**：小程序焦点图用 `image`，App 用 `file` | 低 | 中 | 以 App 端现有契约为准，逐个核对 |
| R5 | **双分类体系**（categories vs expert-departments）口径未对齐 | 中 | 中 | 待定项，确认前不动作 |
| R6 | **遗留代码**：`MessageReplyDialog.vue` 孤儿组件（依赖不存在的 `replyMessage`） | 已确认 | 低 | 明确排除，不迁移 |
| R7 | **焦点图 3D 破坏 Android 兼容**（swiperKey 机制） | 低 | 中 | 保留 swiperKey；改造后真机回归 |
| R8 | **分页参数差异**：小程序 `page_size`/`size` 混用 | 低 | 低 | App 统一 `size`，封装时归一 |
| R9 | **响应结构差异**：App `ApiResponse` 含 `timestamp` | 低 | 低 | 类型以 App `types/common.ts` 为准 |
| R10 | **批量删除大请求体**（100+ 条） | 低 | 低 | 沿用小程序 ≤200 条限制校验 |
| R11 | **管理入口可见性**：当前 `handleAdminNav` 无条件渲染 | 中 | 中 | P0 一并改为 `v-if="authStore.isAdmin"` |
| R12 | **品牌模块产品决策未定**（App 端是否开放品牌管理） | 中 | 中 | P3 前置确认，不做先行开发 |

## 九、实施路线图

| 阶段 | 内容 | 依赖 | 预计工作量 | 验收要点 |
|:----:|------|------|:---------:|---------|
| **P0** | `useAdminGuard` + 现有 admin 页面接入守卫 + 标签管理页 | 无 | 0.5d | 非管理员无法进入任何 admin 页；标签 CRUD 全通 |
| **P1** | 品牌管理页 + live-manage admin 模式编辑 | P0 | 1d | 品牌 CRUD；admin 模式可编辑他人房间（或确认只读） |
| **P2** | 留言管理 + 内容安全 | P0 + 后端契约确认 | 1.5d | 留言查询/批量删除/清空；规则配置 + 日志查询 |
| **P3** | Tab 独立页 + 品牌成员/商品 | 产品确认 + 后端确认 | 1.5d | 按子实施文档验收清单 |
| **并行** | 焦点图 3D + 跳转补齐 | 无 | 0.5d | Android 真机轮播无异常；expert/brand 跳转生效 |
| **待定** | 分类双体系对齐 | 后端确认 | — | — |

**效果预估**：
1. App 端管理能力从 6 入口 → 13 入口，与小程序端对齐
2. 形成可复制的"管理页标准范式"（守卫 + 模板 + 4 层映射），后续新管理页成本降至 0.5d/页
3. 权限安全基线补齐（入口不可见 + 页面守卫 + 后端双重保障）
4. 首页焦点图两端视觉统一，App 端保留差异化信息密度

## 十、验收标准（总方案级）

- [ ] 统一权限守卫落地：未登录跳登录页带回跳；非管理员 toast + 返回；管理功能入口仅管理员可见
- [ ] 标签管理页上线（API 零成本，作为标准范式）
- [ ] 品牌管理、直播间运营增强完成
- [ ] 留言管理、内容安全完成（与后端联调通过）
- [ ] Tab 独立页、品牌成员/商品完成（产品确认后）
- [ ] 焦点图 3D 效果 + expert/brand 跳转完成，Android 真机回归通过
- [ ] 所有新页面通过 `pnpm lint` + `pnpm test:run`
- [ ] 各模块子实施文档按模板补充至 docs 目录

## 十一、变更记录

| 版本 | 日期 | 变更内容 |
|:----:|:----:|---------|
| v1.0 | 2026-08-06 | 初版：基于两端源码逐文件核实（小程序 12 管理模块、App 6 入口与全部 API 文件），完成文档规范提取、选型分析、批次方案与风险清单 |
