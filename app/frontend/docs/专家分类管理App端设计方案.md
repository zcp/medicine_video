# 专家分类管理 — App 端前端实现设计方案

> 基于后端接口全面梳理与前端 18 项功能需求逐项验证后定稿

---

## 一、功能定位

**"专家分类管理"** = 科室词表治理（可运营的受控词表）+ 专家分类完整性监控。

三个实体的关系：

```
categories (25个根分类)      ← 平台级固定架构，本页面仅展示概览
    ↑ FK RESTRICT
expert_departments (158+个)  ← 可运营的词表，本页面的核心管理对象
    ↑ FK SET NULL
experts (专家)               ← 被分类的对象，本页面仅做分类维度的查看和修正
```

**不属于本页面的功能**：专家 CRUD、CSV 导入、专家头像上传、专家精选设置 ——这些属于"专家管理"页面。

---

## 二、后端接口对照

### 2.1 已就绪的接口

| 接口 | 本页面用途 |
|------|---------|
| `GET /admin/expert-departments` | Tab 2 科室列表（支持 is_verified / category_id / q 筛选 + 分页） |
| `PATCH /admin/expert-departments/{id}` | 单条审核 / 编辑科室 |
| `DELETE /admin/expert-departments/{id}` | 软删除科室 |
| `POST /admin/expert-departments` | 新增科室 |
| `POST /admin/expert-departments/merge` | 合并科室（专家迁移 + 同义词继承） |
| `POST /admin/expert-departments/batch-verify` | 批量审核（Spint 3 实施） |
| `PATCH /admin/expert-departments/{id}/category` | 修改科室分类 + 自动同步专家 |
| `GET /admin/expert-departments/unmapped` | Tab 3 未分配专家列表（Phase 2 修复后返回完整 Expert） |
| `GET /admin/expert-departments/{id}` | 科室详情子页（Phase 1 新增） |
| `GET /admin/categories/department-stats` | Tab 1 每分类统计数（Phase 3 新增） |
| `GET /admin/experts?department_id=X` | 科室详情 → 关联专家列表（Phase 4 新增参数） |
| `PATCH /admin/experts/{id}` | 为未分配专家指定 department_id |
| `GET /content/categories?include_counts=true` | 获取分类列表 + 计数 |

### 2.2 已有但本页面不使用的接口

| 接口 | 不使用的理由 |
|------|-----------|
| `POST/PUT/DELETE /admin/categories` | 根分类增删改属于系统配置，放桌面后台 |
| `POST /admin/experts/batch-import` | 属于专家管理页面 |
| 直播间/专题分类相关 | 属于直播/内容管理 |

---

## 三、文件结构

```
src/
├── types/
│   ├── department.ts          ← [修改] 补字段 + 新增响应类型
│   └── category.ts            ← [修改] Category 补 expert_count / department_count
│
├── api/
│   └── department.ts          ← [修改] 新增 3 个 API 函数
│
├── store/
│   └── department.ts          ← [新建] useDepartmentStore（可选，也可用页面 ref）
│
└── pages/app/admin/departments/
    ├── index.vue              ← [重写] 主页面（3 个 Tab 容器）
    ├── detail.vue             ← [新建] 科室详情子页（关联专家列表）
    └── components/
        ├── CategoryOverview.vue       ← [新建] Tab 1：分类总览
        ├── DepartmentList.vue         ← [新建] Tab 2：科室审核列表
        ├── UnmappedExpertList.vue     ← [新建] Tab 3：未分配专家
        ├── DepartmentCard.vue         ← [新建] 科室卡片（Tab 2 复用）
        ├── DepartmentFormSheet.vue    ← [新建] 底部弹窗：编辑/新增科室
        ├── MergeConfirmSheet.vue      ← [新建] 底部弹窗：合并确认
        └── BatchVerifyBar.vue         ← [新建] 批量审核底部操作栏
```

### 3.1 复用已有组件

| 组件 | 路径 | 复用场景 |
|------|------|---------|
| `ExpertCard` | `src/components/expert/ExpertCard.vue` | Tab 3 未分配专家卡片 / 详情页关联专家卡片 |
| `ScrollablePickerSheet` | `src/components/common/ScrollablePickerSheet.vue` | 科室选择器 / 分类选择器 |
| `AppCard` | `src/components/app/AppCard.vue` | Tab 1 分类卡片容器 |
| `LoadingIndicator` | `src/components/common/LoadingIndicator.vue` | 全局加载态 |
| `ErrorBanner` | `src/components/common/ErrorBanner.vue` | 全局错误态 |
| `EmptyState` | `src/components/common/EmptyState.vue` | 全局空态 |

---

## 四、类型定义修改

### 4.1 `types/department.ts` 补全

```ts
// ExpertDepartment 新增字段
export interface ExpertDepartment {
  // ... 已有字段 ...
  source: string | null;       // 创建来源（V9 迁移新增）
  created_by: string | null;   // 创建人 UUID
}

// 新增响应类型
export interface DepartmentStatsItem {
  category_id: string;
  category_name: string;
  expert_count: number;
  department_count: number;
  room_count: number;
}

export interface BatchVerifyRequest {
  department_ids: string[];
}

export interface BatchVerifyResult {
  verified_count: number;
  not_found_count: number;
}

export interface MergeRequest {
  source_id: string;
  target_id: string;
}

// 删除 UnmappedExpert（Phase 2 修复后 unmapped 返回完整 Expert，统一复用 Expert 类型）
```

### 4.2 `types/category.ts` 补全

```ts
export interface Category {
  // ... 已有字段 ...
  expert_count?: number;
  room_count?: number;
}

export interface CategoryStatsResponse {
  items: {
    category_id: string;
    category_name: string;
    expert_count: number;
    department_count: number;
    room_count: number;
  }[];
  total: number;
}
```

---

## 五、API 模块修改

### 5.1 `api/department.ts` 新增 3 个函数

```ts
/**
 * 获取科室详情
 * Phase 1 新增端点: GET /admin/expert-departments/{id}
 */
export const getDepartmentById = (
  id: string
): Promise<ApiResponse<ExpertDepartment>> => {
  return get<ApiResponse<ExpertDepartment>>(
    `/admin/expert-departments/${id}`,
    {},
    { auth: true }
  );
};

/**
 * 批量审核科室
 * Spint 3 新增端点: POST /admin/expert-departments/batch-verify
 */
export const batchVerifyDepartments = (
  data: BatchVerifyRequest
): Promise<ApiResponse<BatchVerifyResult>> => {
  return post<ApiResponse<BatchVerifyResult>>(
    '/admin/expert-departments/batch-verify',
    data,
    { auth: true }
  );
};

/**
 * 获取分类统计（每个分类的科室数+专家数）
 * Phase 3 新增端点: GET /admin/categories/department-stats
 */
export const getDepartmentStats = (): Promise<
  ApiResponse<DepartmentStatsItem[]>
> => {
  return get<ApiResponse<DepartmentStatsItem[]>>(
    '/admin/categories/department-stats',
    {},
    { auth: true }
  );
};
```

### 5.2 `api/category.ts` 传参修正

```ts
// 修改 getCategories：增加 include_counts 参数
export const getCategories = (
  includeCounts = false
): Promise<ApiResponse<Category[]>> => {
  const params: Record<string, any> = {};
  if (includeCounts) params.include_counts = true;
  return get<ApiResponse<Category[]>>('/content/categories', params);
};
```

---

## 六、Pinia Store 设计 (useDepartmentStore)

```
src/store/department.ts
```

```ts
export const useDepartmentStore = defineStore('department', () => {
  // ========== Tab 1：分类总览 ==========
  const statsList = ref<DepartmentStatsItem[]>([]);
  const statsLoading = ref(false);
  const statsError = ref<string | null>(null);

  // ========== Tab 2：科室列表 ==========
  const departments = ref<ExpertDepartment[]>([]);
  const deptPagination = ref({ page: 1, size: 20, total: 0, hasMore: true });
  const deptLoading = ref(false);
  const deptError = ref<string | null>(null);
  const deptFilter = reactive({
    is_verified: undefined as boolean | undefined,
    category_id: '' as string,
    q: '',
  });

  // ========== Tab 3：未分配专家 ==========
  const unmappedExperts = ref<Expert[]>([]);
  const unmappedPagination = ref({ page: 1, size: 20, total: 0, hasMore: true });
  const unmappedLoading = ref(false);
  const unmappedError = ref<string | null>(null);

  // ========== 科室详情子页 ==========
  const currentDepartment = ref<ExpertDepartment | null>(null);
  const currentDeptExperts = ref<Expert[]>([]);
  const detailLoading = ref(false);

  // ========== 通用 ==========
  const categories = ref<Category[]>([]);       // 25 个分类（筛选用）
  const isSelectMode = ref(false);              // 批量选择模式
  const selectedIds = ref<Set<string>>(new Set());

  // ========== Computed ==========
  const pendingCount = computed(
    () => deptPagination.value.total  // 需额外请求或保存筛选结果
  );
  const unmappedCount = computed(() => unmappedPagination.value.total);
  const selectedCount = computed(() => selectedIds.value.size);

  // ========== Actions ==========
  async function fetchCategoriesWithStats() { /* ... */ }
  async function fetchDepartmentList(reset = false) { /* ... */ }
  async function fetchUnmappedExperts(reset = false) { /* ... */ }
  async function fetchDepartmentDetail(id: string) { /* ... */ }
  async function fetchDepartmentExperts(id: string, page = 1) { /* ... */ }
  async function approveDepartment(id: string) { /* ... */ }
  async function batchApproveDepartments() { /* ... */ }
  async function updateDepartment(id: string, data: ExpertDepartmentUpdatePayload) { /* ... */ }
  async function deleteDepartment(id: string) { /* ... */ }
  async function mergeDepartments(sourceId: string, targetId: string) { /* ... */ }
  async function createDepartment(data: ExpertDepartmentCreatePayload) { /* ... */ }
  async function assignExpertDepartment(expertId: string, deptId: string) { /* ... */ }
  function toggleSelect(id: string) { /* ... */ }
  function selectAll() { /* ... */ }
  function clearSelection() { /* ... */ }

  return {
    // state
    statsList, statsLoading, statsError,
    departments, deptPagination, deptLoading, deptError, deptFilter,
    unmappedExperts, unmappedPagination, unmappedLoading, unmappedError,
    currentDepartment, currentDeptExperts, detailLoading,
    categories, isSelectMode, selectedIds,
    // computed
    pendingCount, unmappedCount, selectedCount,
    // actions
    fetchCategoriesWithStats, fetchDepartmentList, fetchUnmappedExperts,
    fetchDepartmentDetail, fetchDepartmentExperts,
    approveDepartment, batchApproveDepartments,
    updateDepartment, deleteDepartment, mergeDepartments, createDepartment,
    assignExpertDepartment,
    toggleSelect, selectAll, clearSelection,
  };
});
```

**备注**：Store 非强制依赖。如果页面数据不需要跨 Tab 共享，也可以用页面内 `ref/reactive` 管理，更简洁。

---

## 七、页面层级与导航流

```
"我的"页
  ├── 管理功能 → 专家分类管理
  │     → /pages/app/admin/departments/index
  │
  ├── 待审核卡片 → 科室审核
  │     → /pages/app/admin/departments/index?tab=pending
  │
  └── 未归类专家卡片
        → /pages/app/admin/departments/index?tab=unmapped

/pages/app/admin/departments/index  ← 主页面 (3 Tab)
    │
    ├── 点击分类卡片
    │     → /pages/app/admin/departments/category-list
    │       ?categoryId=X&categoryName=Y
    │
    └── 点击科室卡片
          → /pages/app/admin/departments/detail
            ?id=X&name=Y
```

---

## 八、Tab 1 — 分类总览 (CategoryOverview.vue)

### 8.1 布局

```
┌──────────────────────────────────────┐
│ 专家分类管理                          │  nav-bar
├──────────────────────────────────────┤
│ [分类总览]  [科室审核 12]  [未分配 5] │  top-tab-bar (sticky)
├──────────────────────────────────────┤
│                                      │
│ ┌─ AppCard (有数据) ────────────────┐ │
│ │ ┌────────────────────────────────┐│ │
│ │ │ 普通外科                 →     ││ │ 30rpx bold + 箭头
│ │ │ 12个科室 · 42位专家             ││ │ 24rpx gray
│ │ │ ████████████████████████░░░    ││ │ 进度条 = 科室数/max
│ │ └────────────────────────────────┘│ │
│ └──────────────────────────────────┘ │
│                                      │
│ ┌─ AppCard (零数据: opacity=0.6) ──┐ │
│ │ 烧伤与创面修复科                   │ │
│ │ 暂无科室 · 暂无专家                │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ──已到底部──                          │
└──────────────────────────────────────┘
```

### 8.2 数据与交互

| 项 | 说明 |
|---|---|
| **数据源** | `GET /admin/categories/department-stats`（Phase 3） |
| **排序** | 按 `department_count DESC`，零数据的排末尾 |
| **进度条** | `width = department_count / maxAll * 100%`，颜色 `var(--home-primary)` |
| **零数据卡片** | `opacity: 0.6`，不可点击（或点击弹空列表提示） |
| **有数据卡片** | 点击 → `uni.navigateTo` 到该分类下的科室列表子页 |
| **加载态** | `LoadingIndicator` |
| **错误态** | `ErrorBanner` + 点击重试 |
| **下拉刷新** | `onPullDownRefresh` → 重新获取 stats → `uni.stopPullDownRefresh()` |

---

## 九、Tab 2 — 科室审核列表 (DepartmentList.vue)

### 9.1 布局

```
┌──────────────────────────────────────┐
│ [分类总览]  [科室审核 12]  [未分配 5] │
├──────────────────────────────────────┤
│ [待审核 12] [已审核 146] [全部 158]   │  二级筛选标签
├──────────────────────────────────────┤
│ 🔍 搜索科室...             [分类 ▼]   │  搜索框 + 分类下拉
├──────────────────────────────────────┤
│ 选择模式: [全选] 已选3项 [取消] [通过审核(3)] │  → BatchVerifyBar
├──────────────────────────────────────┤
│                                      │
│ ┌─ DepartmentCard ──────────────────┐ │
│ │ 左列              右列            │ │
│ │ 甲乳外科           [普通外科]      │ │  右：分类 tag pill
│ │ 同义词: 无          ⏳ 待审核      │ │  左：副标题 + 状态
│ │ 2位专家 · 2026-07-22              │ │  左：专家数 + 时间
│ │                                    │ │
│ │ 长按 → [审核通过][编辑][合并][删除] │ │  longpress ActionSheet
│ └──────────────────────────────────┘ │
│                                      │
│ ┌─ DepartmentCard (选择模式) ───────┐ │
│ │ [☑] 甲乳外科          [普通外科]  │ │  左侧 checkbox
│ │      同义词: 无        ⏳ 待审核   │ │  点击整卡 = toggle 勾选
│ └──────────────────────────────────┘ │
│                                      │
│ ... scroll-view, onReachBottom ...   │
│ 加载更多... / 已到底部~              │
└──────────────────────────────────────┘
```

### 9.2 DepartmentCard 组件

| Props | 类型 | 说明 |
|---|---|---|
| `department` | `ExpertDepartment` | 科室数据 |
| `isSelectMode` | `boolean` | 是否批量选择模式 |
| `isSelected` | `boolean` | 当前卡片是否已勾选 |

| Emits | Payload | 说明 |
|---|---|---|
| `click` | `department` | 点击进入详情 |
| `approve` | `department.id` | 审核通过 |
| `edit` | `department` | 编辑 |
| `merge` | `department` | 合并 |
| `delete` | `department.id` | 删除 |

### 9.3 交互矩阵

| 功能 | 触发方式 | 前端操作 | 后端调用 | 成功后行为 |
|------|---------|---------|---------|-----------|
| 查看科室详情 | 点击卡片 | `navigateTo detail` | — | 进入详情子页 |
| 单条审核通过 | 长按 → "审核通过" | — | `PATCH /{id} {is_verified:true}` | 卡片状态变为 ✅ |
| 批量审核 | 顶栏"批量审核" → 勾选卡片 → 底部"通过审核(N)" | 退出选择模式 | `POST /batch-verify` | Toast N条 | 刷新列表 |
| 编辑科室 | 长按 → "编辑" | 弹 `DepartmentFormSheet` | `PATCH /{id}` | 关闭弹窗 | 刷新 |
| 合并科室 | 长按 → "合并" | 弹 `MergeConfirmSheet` | `POST /merge` | 关闭弹窗 | 刷新 |
| 删除科室 | 长按 → "删除" → Modal确认 | — | `DELETE /{id}` | Toast | 卡片消失 |
| 新增科室 | 顶栏 `[＋新增科室]` | 弹 `DepartmentFormSheet(isEdit=false)` | `POST /admin/expert-departments` | 关闭弹窗 | 刷新 |
| 搜索 | 输入框 @input (debounce 400ms) | 重置分页 | `GET ...?q=xxx` | 列表更新 |
| 分类筛选 | 点击"分类 ▼" → PickerSheet | 重置分页 | `GET ...?category_id=xxx` | 列表更新 |
| 二级筛选 | 点击 [待审核]/[已审核]/[全部] | 重置分页 | `GET ...?is_verified=bool/undefined` | 列表更新 |
| 下拉刷新 | `onPullDownRefresh` | 重置分页 | 重新请求 | 列表更新 |
| 加载更多 | `onReachBottom` | page+1 追加 | 请求下一页 | 列表追加 |
| 选择模式进入 | 点击顶栏"批量审核" | `isSelectMode=true` | — | 卡片出现 checkbox |
| 选择模式退出 | 点击"取消"或操作完成 | `isSelectMode=false; clearSelection()` | — | 恢复普通模式 |

---

## 十、Tab 3 — 未分配专家 (UnmappedExpertList.vue)

### 10.1 布局

```
┌──────────────────────────────────────┐
│ [分类总览]  [科室审核 12]  [未分配 5] │
├──────────────────────────────────────┤
│ ⚠️ 以下专家未关联标准科室               │  橙色提示横幅 (可关闭)
│ 他们将不会出现在科室维度的筛选中         │
├──────────────────────────────────────┤
│                                      │
│ ┌─ ExpertCard (复用) + 分配按钮 ────┐ │
│ │ 头像  张医生  主任医师              │ │
│ │       中山大学附属第一医院           │ │
│ │       当前分类: 普通外科            │ │
│ │       [分配科室 →]                 │ │  primary 按钮
│ └──────────────────────────────────┘ │
│                                      │
│ ... scroll-view, onReachBottom ...   │
│                                      │
│ ── 全部专家已分配科室 ✓ ──            │  空态
└──────────────────────────────────────┘
```

### 10.2 交互

| 功能 | 触发方式 | 后端调用 | 成功后行为 |
|------|---------|---------|-----------|
| 加载列表 | Tab 切换/下拉刷新 | `GET /admin/expert-departments/unmapped` | 渲染专家卡片 |
| 分配科室 | 点击 `[分配科室 →]` → PickerSheet 选择科室 → 确认 | `PATCH /admin/experts/{id} {department_id:X}` | 专家从列表消失 + Toast |

---

## 十一、底部弹窗组件

### 11.1 DepartmentFormSheet（编辑/新增科室表单）

```
┌──────────────────────────────────────┐
│ 遮罩层 rgba(0,0,0,0.5)               │
│ ┌────────────────────────────────┐   │
│ │ 新增科室 / 编辑科室      [保存]  │   │
│ │────────────────────────────────│   │
│ │ 科室名称                        │   │
│ │ [_________________________]    │   │ input maxlength=120
│ │                                │   │
│ │ 所属分类                        │   │
│ │ [ 普通外科                   ▼] │   │ 点击弹出 PickerSheet
│ │                                │   │
│ │ 同义词                          │   │
│ │ [乳腺科 ✕] [乳房外科 ✕]         │   │ tag 列表
│ │ [输入新同义词 +______________]  │   │ inline input 回车添加
│ │                                │   │
│ │ 审核状态:  [========●] 已审核   │   │ Switch
│ │ 启用状态:  [========●] 启用     │   │ Switch
│ └────────────────────────────────┘   │
└──────────────────────────────────────┘
```

**Props**: `visible`, `mode: 'create' | 'edit'`, `department?: ExpertDepartment`（编辑模式传入）

**Emits**: `update:visible`, `submit(data)`

**动画**：参考 `ScrollablePickerSheet.vue` 的 mask + bottom slide-up 模式。

### 11.2 MergeConfirmSheet（合并确认）

```
┌──────────────────────────────────────┐
│ 合并科室                      [确认]  │
├──────────────────────────────────────┤
│ 源科室（将被删除）                    │
│ ┌────────────────────────────────┐   │
│ │ 甲乳外科      [普通外科]         │   │ 灰色，不可修改
│ │ 2位专家                        │   │
│ └────────────────────────────────┘   │
│          ▼ 合并到 ▼                  │
│ 目标科室（保留）                      │
│ ┌────────────────────────────────┐   │
│ │ 🔍 搜索或选择科室...            │   │ 搜索 + 下列表
│ │ 乳腺外科   [普通外科]  ✅ 8人    │   │ 可选目标
│ │ 肝胆外科   [普通外科]  ✅ 5人    │   │
│ └────────────────────────────────┘   │
│ ⚠️ "甲乳外科"的2位专家→迁移到目标     │ 预览
│ ⚠️ 源科室名将作为同义词保留           │
└──────────────────────────────────────┘
```

### 11.3 BatchVerifyBar（批量审核底部栏）

```
┌──────────────────────────────────────┐
│ ☑ 全选   已选 3 / 12   [取消] [通过审核(3)] │
└──────────────────────────────────────┘
  position: fixed; bottom: 0; z-index: 100
  仅在 isSelectMode 时显示
```

---

## 十二、科室详情子页 (detail.vue)

### 12.1 布局

```
┌──────────────────────────────────────┐
│ ← 科室                          [⋮]  │  nav-bar: 返回 + 名称 + ActionSheet
├──────────────────────────────────────┤
│ ┌─ AppCard ────────────────────────┐ │
│ │ 乳腺外科                         │ │  36rpx bold
│ │ [普通外科]  ✅ 已审核 · 已启用    │ │  category pill + status tag
│ │                                  │ │
│ │ 同义词: 乳腺科, 乳房外科, 甲乳科   │ │
│ │ 来源: auto_match                 │ │
│ │ 创建时间: 2026-07-15 14:30       │ │
│ └──────────────────────────────────┘ │
│                                      │
│ 关联专家 (8人)                        │
│ ┌─ ExpertCard (复用) ──────────────┐ │
│ │ 头像  张医生  主任医师            │ │
│ │       中山大学附属第一医院         │ │
│ └──────────────────────────────────┘ │
│ ┌─ ExpertCard (复用) ──────────────┐ │
│ │ 头像  李主任  教授                │ │
│ │       北京协和医院                │ │
│ └──────────────────────────────────┘ │
│ 加载更多专家 (6人) →                  │
│                                      │
├──────────────────────────────────────┤
│  [编辑科室]    [合并科室]    [禁用科室]  │  bottom-bar fixed
└──────────────────────────────────────┘
```

### 12.2 交互

| 项 | 说明 |
|---|---|
| **数据源(科室)** | `GET /admin/expert-departments/{id}` (Phase 1) |
| **数据源(专家)** | `GET /admin/experts?department_id=X` (Phase 4 新增参数) |
| **顶部 ⋮** | `uni.showActionSheet({itemList: ['编辑', '合并', '禁用/启用', '删除']})` |
| **底部栏按钮** | `[编辑科室]` primary / `[合并科室]` outline / `[禁用科室]` danger-ghost |
| **加载更多专家** | `onReachBottom` → page+1 请求关联专家 |
| **专家卡片点击** | `navigateTo /pages/app/expert/detail?id=Z` |

---

## 十三、状态转换

```
页面级别:
  idle ──(enter tab)──→ loading ──(ok)──→ loaded
  loaded ──(下拉刷新)──→ refreshing ──(ok)──→ loaded
                        loading ──(err)──→ error ──(retry)──→ loading
  loaded ──(触底)──────→ loadingMore ──(ok)──→ loaded
                                      ──(noMore)──→ loaded(end)

操作级别:
  审核:      confirm → pending → ok → Toast | 刷新列表
  批量审核:  confirm → pending → ok → Toast N条 | 退出选择 | 刷新
  编辑:      submit  → pending → ok → 关闭弹窗 | 刷新
  删除:      confirm → pending → ok → Toast | 卡片消失
  合并:      confirm → pending → ok → 关闭弹窗 | Toast | 刷新
  分配:      选择科室→ pending → ok → Toast | 专家消失
```

---

## 十四、数据流

```
useDepartmentStore
  ├── statsList ← GET /admin/categories/department-stats ──→ Tab 1
  ├── departments ← GET /admin/expert-departments?filters ──→ Tab 2 + DepartmentCard
  ├── unmappedExperts ← GET /admin/expert-departments/unmapped ──→ Tab 3 + ExpertCard
  ├── currentDepartment ← GET /admin/expert-departments/{id} ──→ detail.vue
  ├── currentDeptExperts ← GET /admin/experts?department_id=X ──→ detail.vue
  └── categories ← GET /content/categories ──→ 筛选下拉 (Tab 2) + 表单弹窗选择
```

---

## 十五、空态 / 边界处理

| 场景 | 展示 |
|------|------|
| Tab 1 加载失败 | `ErrorBanner` + "加载分类数据失败，点击重试" |
| Tab 1 全部零数据 | 不可能（25 个分类始终存在） |
| Tab 2 待审核为空 | `EmptyState(title='没有待审核科室', description='全部科室已审核通过 ✓')` |
| Tab 2 搜索结果为空 | `EmptyState(title='暂无匹配科室', description='试试更换筛选条件')` |
| Tab 3 无未分配专家 | `EmptyState(title='全部专家已分配科室 ✓')` |
| Tab 3 平台无专家 | `EmptyState(title='暂无专家', description='还没有创建任何专家')` |
| 科室详情页加载失败 | `ErrorBanner` + 返回按钮 |
| 科室详情页无关联专家 | `EmptyState(title='该科室暂无关联专家')` |
| 网络请求超时/失败 | `ErrorBanner` + Toast 错误信息 |
| 审核操作失败 | Toast "审核失败，请重试"（不刷新列表） |
| 批量审核部分失败 | Toast "3/5 成功，2 个失败" |
| 删除有专家关联的科室 | Modal 警告："该科室下有 N 位专家，删除后他们将失去科室归属" |

---

## 十六、入口参数

| 来源 | 路径 | 参数 |
|------|------|------|
| "我的" → 管理功能 → 专家分类管理 | `/pages/app/admin/departments/index` | 无，默认 Tab 1 |
| "我的" → 待审核卡片 → 科室审核 | `/pages/app/admin/departments/index` | `?tab=pending` |
| "我的" → 未归类专家卡片 | `/pages/app/admin/departments/index` | `?tab=unmapped` |

页面在 `onLoad(options)` 中解析 `options.tab` 设置 `activeTab` 初始值：

```ts
onLoad((options?: AnyObject) => {
  const tab = options?.tab;
  if (tab === 'pending') activeTab.value = 'pending';
  else if (tab === 'unmapped') activeTab.value = 'unmapped';
  else activeTab.value = 'overview';
});
```

---

## 十七、实施顺序

| 步骤 | 产出 | 依赖 |
|:--:|------|:--:|
| 1 | 类型补全 | `types/department.ts` + `types/category.ts` | 无 |
| 2 | API 函数 | `api/department.ts` 新增 3 个 + `api/category.ts` 修正 | 步骤 1 |
| 3 | Store | `store/department.ts`（或确认使用页面 ref） | 步骤 2 |
| 4 | DepartmentCard | 基础卡片组件（纯展示 + emit） | 步骤 1 |
| 5 | DepartmentFormSheet | 底部表单弹窗 | 步骤 4 |
| 6 | DepartmentList | Tab 2 完整功能 | 步骤 2-5 |
| 7 | CategoryOverview | Tab 1（依赖 P3 端点） | 步骤 2-3 |
| 8 | UnmappedExpertList | Tab 3（依赖 P2 端点） | 步骤 2-3 |
| 9 | detail.vue | 科室详情子页（依赖 P1 + P4） | 步骤 2-4 |
| 10 | MergeConfirmSheet + BatchVerifyBar | 辅助组件 | 步骤 2-4 |
| 11 | index.vue 组装 | 3 Tab 主页面 + 路由解析 | 步骤 6-10 |
| 12 | "我的"页对接 | 确认 ?tab= 参数传递正确 | 步骤 11 |
