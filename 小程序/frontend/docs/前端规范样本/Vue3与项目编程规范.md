# Vue3 与项目编程规范

**项目**: 通用规范  
**版本**: 1.0  
**创建日期**: 2026-01-23  
**状态**: 设计完成（由《Vue3前端开发规范》与《编程规范文档》合并）

---

## 📋 目录

1. [适用范围与项目概述](#一适用范围与项目概述)
2. [通用开发原则](#二通用开发原则)
3. [命名规范](#三命名规范)
4. [代码风格与组件结构](#四代码风格与组件结构)
5. [文件与目录规范](#五文件与目录规范)
6. [环境与配置](#六环境与配置)
7. [API 调用规范](#七api-调用规范)
8. [组件化开发规范](#八组件化开发规范)
9. [状态管理规范](#九状态管理规范)
10. [表单验证规范](#十表单验证规范)
11. [错误处理规范](#十一错误处理规范)
12. [Git 提交规范](#十二git-提交规范)
13. [测试规范](#十三测试规范)
14. [检查清单](#十四检查清单)
15. [附录](#十五附录)

---

## 一、适用范围与项目概述

### 1.1 适用范围

本规范适用于所有使用 **Vue3** 的前端项目，包括：

- ✅ uni-app + Vue3（uni-ui 或 Element Plus）
- ✅ Vue3 + Element Plus（H5 管理后台）
- ✅ Vue3 + 其他 UI 组件库

不适用于 Vue 2、React 及其他非 Vue3 项目。

### 1.2 技术栈（本项目）

- **框架**: Vue 3 + TypeScript  
- **构建**: Vite  
- **UI**: Element Plus  
- **状态**: Pinia  
- **跨端**: uni-app  
- **规范**: ESLint + Prettier  

### 1.3 项目结构

```
vzan_simul_frontend/
├── src/
│   ├── api/              # API 接口
│   ├── components/       # 公共组件
│   ├── constants/        # 常量（如 api.ts，使用 getEnv）
│   ├── layouts/          # 布局
│   ├── pages/            # 页面
│   ├── store/            # Pinia
│   ├── types/            # TS 类型
│   ├── utils/            # 工具（含 env.ts、request.ts、navigation.ts）
│   └── main.ts
├── public/
│   └── config.js         # 运行时配置，见 §六
├── tests/
└── vite.config.ts
```

---

## 二、通用开发原则

### 2.1 组件化

- 可复用 UI 封装为组件；公共组件 `components/`，业务组件放模块下。
- 组件名 PascalCase，Props/Emits 用 TypeScript 定义。

### 2.2 代码风格

- 使用 Composition API、`<script setup lang="ts">`。
- TypeScript 类型完整；避免 `any`，必要时 `unknown`。
- 组件文件 PascalCase，工具/类型/常量文件 camelCase。

### 2.3 类型支持

- 所有 API、Store、组件均有类型定义；复杂验证可抽到 `utils/validator.ts`。

---

## 三、命名规范

### 3.1 表单数据：`formData`

**所有表单数据统一存放在名为 `formData` 的 `reactive`（或 `ref`）中。**

```typescript
// ✅ 正确
const formData = reactive({ username: '', email: '' });

// ❌ 避免
const formModel = reactive({ ... });
const userForm = reactive({ ... });
```

适用：创建页、编辑页、任意表单页。与《编辑页面数据与校验规范》一致；存量使用 `formModel` 的页面，新增与重构时统一为 `formData`。

### 3.2 加载状态：`isLoading`

**页面级加载状态（按钮 loading、骨架屏等）统一使用 `isLoading`（`ref`）。**

```typescript
// ✅ 正确
const isLoading = ref(false);
<el-button :loading="isLoading" @click="handleSubmit">提交</el-button>

// ❌ 避免（通用加载）
const loading = ref(false);
const isSubmitting = ref(false);
```

若有多个独立操作，可用 `saving`、`deleting`、`uploading` 等，但**通用**加载仍用 `isLoading`。

### 3.3 组合式函数返回值

直接解构使用，不二次重命名：

```typescript
// ✅ 正确
const { captchaImage, refreshCaptcha, isLoading } = useCaptcha();
const { pagination, loadData } = usePagination();
```

### 3.4 其他常用命名

| 类型     | 规范           | 示例                                      |
|----------|----------------|-------------------------------------------|
| 列表数据 | `items` / `list` | `const experts = ref([])`                 |
| 分页信息 | `pagination`   | `reactive({ page: 1, size: 20, total: 0 })` |
| 选中项   | `selectedXxx`  | `selectedExperts`                         |
| 错误     | `error` / `errorMessage` | `ref<string \| null>(null)`        |
| 当前项   | `currentXxx`   | `currentExpert`                           |

---

## 四、代码风格与组件结构

### 4.1 组件结构

```vue
<template><!-- 模板 --></template>

<script setup lang="ts">
// 1. 导入（Vue → 第三方 → 内部工具 → 组件 → 类型）
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { getEnv } from '@/utils/env';
import type { Expert } from '@/types/expert';

// 2. Props / Emits
const props = defineProps<{ id: string }>();
const emit = defineEmits<{ submit: []; cancel: [] }>();

// 3. 响应式数据
const formData = reactive({ ... });
const isLoading = ref(false);

// 4. 计算属性
const isValid = computed(() => ...);

// 5. 方法
const handleSubmit = async () => { ... };

// 6. 生命周期
onMounted(() => { ... });
</script>

<style lang="scss" scoped>
/* 样式 */
</style>
```

### 4.2 导入顺序

1. Vue 核心 API  
2. 第三方库  
3. 项目工具（`@/utils/...`）  
4. 项目组件  
5. 类型（`import type ...`）

### 4.3 注释

- 复杂逻辑、公共函数加注释；函数建议 JSDoc。  
- 类型、枚举等加简要说明；避免过度注释。

---

## 五、文件与目录规范

### 5.1 文件命名

- **组件**: PascalCase，如 `UserProfile.vue`、`RoomCard.vue`。  
- **工具 / 类型 / 常量**: camelCase，如 `formatDate.ts`、`request.ts`、`user.ts`、`api.ts`。

### 5.2 目录组织

- 按功能划分；层级不超过 3 层；目录名小写 + 连字符（kebab-case）。

### 5.3 典型分布

- **api**: `room.ts`、`session.ts` 等  
- **store**: `user.ts`、`room.ts`  
- **types**: `user.ts`、`room.ts`  
- **utils**: `request.ts`、`env.ts`、`navigation.ts`、`validator.ts`

---

## 六、环境与配置

**本项目以 `public/config.js` + `getEnv()` 为配置主方式。**

- **运行时配置**：`public/config.js` 设置 `window.__APP_CONFIG__` / `window.__ENV`。  
- **读取方式**：统一通过 `getEnv(key, defaultValue)`（`@/utils/env`）。  
- **优先级**：`window.__ENV` > `import.meta.env` > 默认值。  
- **环境切换**：通过 `config.js` 内 `USE_LOCAL_DEV` 等控制，无需改代码。

**详细说明、CORS、登录跳转等见《环境配置与CORS编程规范设计文档》。** 禁止在业务代码中硬编码 API 地址等配置；新增配置项时在 `config.js` 与 `getEnv` 中扩展，并在该文档中说明。

---

## 七、API 调用规范

### 7.1 统一请求封装

- 所有接口通过 `@/utils/request` 封装（内部使用 `getEnv('VITE_BASE_API_URL')` 等）。  
- 支持拦截器、统一携带 Token、错误与 401 处理（见《环境配置与CORS》《登录与跨应用跳转》）。  
- 禁止在页面或 Store 中直接使用 `uni.request` / `fetch` 写死 base URL。

### 7.2 API 模块与响应格式

```typescript
// src/api/room.ts
import { request } from '@/utils/request';
import type { Room, RoomCreatePayload } from '@/types/room';

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  timestamp?: string;
}

export const getRoomList = (params: { page?: number; size?: number }) =>
  request<ApiResponse<{ items: Room[]; total: number }>>({
    url: '/rooms',
    method: 'GET',
    data: params,
  });

export const createRoom = (data: RoomCreatePayload) =>
  request<ApiResponse<Room>>({ url: '/rooms', method: 'POST', data });
```

### 7.3 调用处错误处理

```typescript
try {
  const res = await getRoomList({ page: 1 });
  if (res.code === 200) {
    // 使用 res.data
  } else {
    ElMessage.error(res.message || '请求失败');
  }
} catch (e) {
  console.error('请求失败', e);
  ElMessage.error('网络异常，请稍后重试');
}
```

---

## 八、组件化开发规范

### 8.1 原则

- 单一职责、可复用、可维护、可测试；Props 与 Emits 均用 TypeScript 定义。

### 8.2 Props / Emits

```typescript
interface Props {
  title: string;
  count?: number;
  disabled?: boolean;
}
const props = withDefaults(defineProps<Props>(), { count: 0, disabled: false });

const emit = defineEmits<{
  change: [value: string];
  submit: [payload: Record<string, unknown>];
  cancel: [];
}>();
```

（`submit` 的 payload 类型可按业务定义为具体接口，此处仅作示例；勿与浏览器 `FormData` 混淆。）

### 8.3 状态提升

- 跨组件共享状态放在父组件或 Store，避免子组件各自维护再同步。

---

## 九、状态管理规范

### 9.1 Pinia Store

- 全局状态用 Pinia；Store 放 `src/store/`，按模块分文件（如 `user.ts`、`room.ts`）。  
- State / Actions / Getters 均使用 TypeScript。

### 9.2 使用方式

- 组件内通过 `useXxxStore()` 获取，用 `storeToRefs` 解构保持响应式。  
- 仅通过 actions 修改 state，禁止在组件中直接改 `store.xxx = ...`。

### 9.3 与列表、分页的配合

- 列表、分页相关规范见《通用数据列表展示规范》《前端分页实现规范与常见错误》。  
- Store 中分页状态建议包含 `page`、`size`、`total`（`total` 以后端返回为准），组件用 `pagination.total` 等。

---

## 十、表单验证规范

### 10.1 规则组织

- 可复用的校验逻辑放在 `src/utils/validator.ts`，表单内引用。  
- 编辑页动态校验（依创建/编辑、原始数据决定 required）见《编辑页面数据与校验规范》。

### 10.2 Element Plus

- `el-form` + `el-form-item` + `:rules`，`:model` 绑定 `formData`。  
- 复杂校验用自定义 validator 或 `validator.ts` 中的函数。

### 10.3 uni-app + uni-forms

- `uni-forms` + `uni-forms-item`，同上，规则格式按 uni-forms 要求配置。

---

## 十一、错误处理规范

### 11.1 接口与业务错误

- 在调用处 `try/catch`，成功时判断 `code`，失败时 `ElMessage` 提示。  
- 可定义 `ApiError` 等类型便于区分网络错误与业务错误。

### 11.2 用户可感知操作

- 增删改、提交等操作失败时，必须给出明确提示，禁止静默失败。

---

## 十二、Git 提交规范

### 12.1 格式

```
<type>(<scope>): <subject>
```

### 12.2 类型

- `feat`: 新功能  
- `fix`: Bug 修复  
- `docs`: 文档  
- `style`: 格式  
- `refactor`: 重构  
- `test`: 测试  
- `chore`: 构建/工具  

### 12.3 示例

```bash
feat(room): 新增直播间创建
fix(api): 修复超时未重试
docs(readme): 更新环境说明
```

---

## 十三、测试规范

### 13.1 命名与位置

- 组件测试：`*.spec.ts` 与组件同目录或集中 `tests/`。  
- API / Store 测试：`api/*.spec.ts`、`store/*.spec.ts` 等。

### 13.2 建议

- 使用 Vitest + Vue Test Utils；用例结构清晰，覆盖关键交互与分支。

---

## 十四、检查清单

### 命名与数据

- [ ] 表单数据使用 `formData`  
- [ ] 加载状态使用 `isLoading`（或 `saving` 等专用名）  
- [ ] 组合式函数返回值直接解构  
- [ ] 分页、列表等命名符合 §3.4  

### 代码与结构

- [ ] `<script setup lang="ts">`，导入顺序符合 §4.2  
- [ ] 组件结构符合 §4.1  
- [ ] 复杂逻辑与函数有注释  

### 配置与请求

- [ ] 配置通过 `getEnv` 读取，不硬编码  
- [ ] API 通过 `request` 封装，不直接 `uni.request`/`fetch`  

### 组件与状态

- [ ] Props/Emits 有类型定义  
- [ ] 全局状态用 Pinia，通过 actions 修改  
- [ ] 表单校验与编辑页逻辑符合对应规范  

---

## 十五、附录

### 相关文档

- 《环境配置与CORS编程规范设计文档》— 配置、CORS、请求拦截  
- 《前端安全编程规范》— 安全  
- 《响应式布局设计规范》— 布局与断点  
- 《编辑页面数据与校验规范》— 编辑页 formData、原始数据、校验  
- 《前端分页实现规范与常见错误》— 分页  
- 《通用数据列表展示规范》— 列表、表格  
- 《登录与跨应用跳转设计文档》— 登录与跨应用  
- 《页面返回机制设计文档》— 返回与导航  

### 参考资源

- [Vue 3 文档](https://cn.vuejs.org/)  
- [Vue 3 风格指南](https://cn.vuejs.org/style-guide/)  
- [TypeScript](https://www.typescriptlang.org/)  
- [Vite](https://cn.vitejs.dev/)  
- [Element Plus](https://element-plus.org/zh-CN/)  
- [Pinia](https://pinia.vuejs.org/zh/)  

---

**文档版本**: 1.0  
**最后更新**: 2026-01-23  
**维护者**: 开发团队  

**本规范为 Vue3 前端与项目编程的统一依据，与上述各专题规范配套使用。**
