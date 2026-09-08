# 直播SaaS平台移动端前端阶段零代码生成提示词 (V1.1 - 增量开发增强版)

---

# ⚠️ 第0章：强制性环境探查与冲突检测（必须先执行）

**这是最高优先级的步骤，必须在生成任何代码之前完成！**

## 0.1 环境扫描强制清单

AI 必须依次执行以下检查，**不得跳过任何一项**：

### ✅ 检查项 1：目录结构扫描
```bash
必须使用 list_dir 工具列出的目录：
- src/common/
- src/utils/
- src/logs/
- src/api/
- src/store/
- src/components/
- src/pages/
```

### ✅ 检查项 2：关键文件存在性检查
```bash
必须使用 read_file 或 find_by_name 工具检查的文件：
□ src/uni.scss
□ src/common/uni.scss
□ src/App.vue
□ src/main.ts
□ src/env.d.ts
□ .env.development
□ .env.app
□ vite.config.ts
□ tsconfig.json
□ package.json
```

**检查结果必须以下列格式输出**：
```markdown
[项目状态分析]
✓ 已存在文件：X 个
  - src/common/uni.scss (529行)
  - src/App.vue (已有生命周期)
  - ...

✗ 需新建文件：Y 个
  - src/logs/logger.ts
  - src/common/constants.ts
  - ...

⚠ 需修改文件：Z 个
  - src/App.vue（第XX行插入日志初始化）
  - vite.config.ts（移除全局注入）
  - ...
```

### ✅ 检查项 3：配置冲突点识别

**必须检查的配置冲突点**：

| 配置项 | 检查内容 | 冲突判定 | 处理策略 |
|--------|---------|---------|----------|
| `vite.config.ts` 中的 `additionalData` | 是否有全局注入 uni.scss | 如有则冲突（循环引用） | 移除全局注入 |
| `src/uni.scss` vs `src/common/uni.scss` | 是否同时存在 | 如是则冲突 | 使用现有的 common/uni.scss |
| `package.json` 中的 `pinia` | 是否在 devDependencies | 如是则需调整 | 移动到 dependencies |
| `.env.*` 文件 | 是否已有日志配置 | 如有则需合并 | 追加新配置 |

### ✅ 检查项 4：技术细节验证

**必须验证的技术细节**：
- [ ] `getCurrentInstance` 应从 `"vue"` 包导入，**不是** `"@dcloudio/uni-app"`
- [ ] TypeScript 类型必须包含 `| undefined`（严格模式）
- [ ] uni.scss 使用 CSS 变量（`:root`），**不需要** Sass 全局注入
- [ ] 所有 `uni.*` API 调用必须有错误处理

### ✅ 检查项 5：生成策略确认

AI 必须输出详细的操作清单，**等待用户确认**：

```markdown
[操作清单]

新建文件（N个）：
1. src/common/constants.ts - 基础常量定义
2. src/utils/security.ts - 安全工具模块（9个函数）
3. src/logs/logTypes.ts - 日志类型定义
4. ...

修改文件（M个）：
1. src/App.vue
   - 第6行：添加 import logger from '@/logs/logger'
   - 第7行：添加 import { getCurrentInstance } from "vue" ← 注意：从 vue 导入
   - 第18行：插入全局错误处理器代码块
   
2. vite.config.ts
   - 第139行：移除 additionalData（避免循环引用）
   
3. ...

跳过文件（K个）：
1. src/common/uni.scss - 已存在且完整，不需要创建 src/uni.scss
2. package.json - 依赖已完整
3. ...

⚠️ 请确认是否继续执行？(Y/N)
```

## 0.2 常见陷阱预警（必读）

### 🔴 陷阱1：循环引用错误
**问题**：在 `vite.config.ts` 中使用 `additionalData: '@import "@/common/uni.scss"'`
**后果**：`uni.scss` 会导入自己，导致 Sass 编译失败
**错误信息**：`[sass] This file is already being loaded`
**解决方案**：移除 `additionalData` 配置，只在 `main.ts` 中导入一次

### 🔴 陷阱2：导入来源错误
**问题**：`import { getCurrentInstance } from "@dcloudio/uni-app"`
**后果**：运行时错误 `Module has no exported member 'getCurrentInstance'`
**正确写法**：
```typescript
import { getCurrentInstance } from "vue"  // ✅ 从 vue 包导入
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app"  // ✅ uni-app 生命周期
```

### 🔴 陷阱3：TypeScript 类型不严格
**问题**：`function demo(obj: any | null): any | null`
**后果**：TypeScript 严格模式下报错 `Type 'undefined' is not assignable to type 'any | null'`
**正确写法**：
```typescript
function demo(obj: any | null | undefined): any | null | undefined {
  if (!obj) return obj  // ✅ 同时处理 null 和 undefined
}
```

### 🟡 陷阱4：文件重复创建
**问题**：未检查 `src/common/uni.scss` 是否存在，直接创建 `src/uni.scss`
**后果**：两个样式文件冲突，导致样式混乱
**解决方案**：执行环境扫描，使用现有文件

### 🟡 陷阱5：Sass 变量 vs CSS 变量混淆
**问题**：对使用 CSS 变量（`:root { --var }`）的文件进行 Sass 全局注入
**后果**：不需要全局注入，只会增加编译时间和出错风险
**正确理解**：
- **Sass 变量** `$color: #fff` → 需要全局注入（编译时替换）
- **CSS 变量** `--color: #fff` → 不需要全局注入（运行时生效）

---

## 1. 角色定义（Role Definition）

你是一名资深移动端前端架构师，精通 uni-app、Vue3、TypeScript 和 Vite，擅长从零开始搭建跨平台移动应用的安全、规范、可维护的项目基础设施。你的任务是为后续的开发工作奠定一个坚实、一致且标准化的基础，并**实现**功能完整的安全模块和日志管理系统。

---

## 2. 任务目标（Task Objective）

本次任务为"直播SaaS平台移动端项目"的**阶段零**，核心目标是：

1. **搭建项目骨架**：创建项目配置文件、核心应用文件、完整目录结构
2. **实现设计规范代码化**：将UI设计规范转换为CSS变量（uni.scss）
3. **建立安全基础设施**：创建符合医学数据安全要求的脱敏、XSS防护、URL校验等安全工具
4. **实现完整日志系统**：支持日志分级、自动脱敏、批量上报、移动端优化
5. **配置环境变量**：按开发/生产环境区分日志配置

**所有生成的代码必须是生产级别的、功能完整的、可直接运行的。**

**为确保任务明确、无歧义，本次需具体生成以下所有文件和目录：**

### 2.1 项目根目录配置文件（8个 - 已存在，需检查并增补移动端配置）
**注意：以下配置文件已存在于项目中，零阶段需要检查并按需增补移动端（App/小程序）所需的配置**
- `package.json` - 检查是否包含uni-app移动端所需依赖（如 `@dcloudio/uni-app`、`@dcloudio/uni-mp-weixin` 等）
- `vite.config.ts` - 检查是否包含移动端平台构建配置（H5/微信小程序/App）
- `tsconfig.json` - 检查是否包含 `@dcloudio/types` 以支持uni-app类型定义
- `.eslintrc.cjs` - 检查是否适配uni-app语法（如 `uni.*` API调用）
- `.prettierrc` - 检查格式化规则是否适用于移动端开发
- `jest.config.js` - 检查测试配置是否支持uni-app组件测试
- `.gitignore` - 检查是否包含移动端构建产物忽略规则（如 `dist/build/`、`unpackage/` 等）
- `README.md` - 检查是否包含移动端开发说明和命令

### 2.2 核心源码文件（`src/`目录 - 部分已存在，需修改/检查）
**已存在需修改**：
- `App.vue` - 应用根组件（需新增全局错误捕获）
- `main.ts` - 应用入口文件（需新增日志系统初始化）

**已存在需检查并增补**：
- `pages.json` - uni-app页面路由配置（检查是否包含移动端全局样式、tabBar配置）
- `manifest.json` - uni-app应用配置（检查是否包含小程序appid、App权限等移动端平台配置）

**需要新建**：
- `env.d.ts` - 全局TypeScript环境声明
- `uni.scss` - 全局样式变量（设计令牌）

### 2.3 基础模块文件
- `src/common/constants.ts` - 基础常量定义
- `src/utils/security.ts` - 安全工具模块（9个完整函数）
- `src/logs/logTypes.ts` - 日志类型定义
- `src/logs/logConfig.ts` - 日志配置管理
- `src/logs/logger.ts` - 日志系统核心实现

### 2.4 空目录结构
**在 `src/` 目录下创建**：
- `api/` - API接口封装
- `components/` - 可复用组件
- `pages/` - 页面级组件
- `static/` - 静态资源
- `store/` - 全局状态管理
- `types/` - TypeScript类型定义
- `utils/` - 工具函数（需先创建目录，security.ts在此）
- `common/` - 全局公共资源（需先创建目录，constants.ts在此）
- `logs/` - 日志管理模块（需先创建目录）

**在根目录创建**：
- `tests/` - 测试用例目录

### 2.5 环境配置文件
- `.env.development` - 开发环境配置
- `.env.app` - 生产环境配置（App打包）

---

## 3. 核心上下文信息（Core Context Information）

### 3.1 项目现状说明

**重要**：这是一个**增量开发**的零阶段任务，项目已完成基础搭建（可能主要为PC端/H5配置）。

**已存在的配置（需检查并增补移动端配置）**：
- 8个项目配置文件：`package.json`、`vite.config.ts`、`tsconfig.json`、`.eslintrc.cjs`、`.prettierrc`、`jest.config.js`、`.gitignore`、`README.md`
- 部分核心文件：`App.vue`、`main.ts`、`pages.json`、`manifest.json`
- 基础目录结构：`src/api`、`src/utils`、`src/common`、`src/logs`、`tests` 等

**零阶段需要做的**：
1. 🔍 **检查并增补**已存在配置文件中的移动端配置（依赖、构建脚本、类型定义、忽略规则等）
2. ✏️ **修改** `App.vue` 和 `main.ts`（新增日志系统集成和全局错误处理）
3. 🔍 **检查并补充** `pages.json` 和 `manifest.json` 中的移动端平台配置（小程序、App等）
4. ➕ **新建** `src/env.d.ts` 和 `src/uni.scss`（设计令牌）
5. ➕ **新建**安全模块和日志模块的所有文件

### 3.2 唯一事实来源

《直播SaaS平台移动端前端设计文档.md》是所有代码生成工作的唯一且最高的设计依据：
- **第3章《移动端前端开发规范》**：代码规范、命名规范、项目结构、日志管理规范（3.5节）
- **第4章《移动端安全规范》**：XSS防护（4.1）、敏感信息脱敏（4.2）、日志脱敏（4.5）

### 3.3 设计令牌来源

《直播SaaS平台移动端前端设计文档.md》**第8.1节（设计令牌）**定义了完整的UI设计规范，`uni.scss` 文件中的所有CSS变量必须严格依据此节转换。

### 3.4 项目结构参考

《直播SaaS平台移动端前端设计文档.md》**第3.3节（项目结构）**定义了完整的目录组织规范。

---

## 4. 全局强制性约束与最高准则

### 4.1 安全第一原则
1. **零敏感信息泄露**：所有日志、API调用必须严格脱敏
2. **XSS零容忍**：禁止使用 v-html，所有用户输入必须转义
3. **HTTPS强制**：生产环境API必须使用 https://

### 4.2 功能完整性原则
1. 生成的所有代码（尤其是安全模块和日志模块）必须是**功能完整**的，可直接运行
2. **不允许TODO注释**（日志上报API地址可使用占位符）
3. 所有配置必须按环境区分（development/production）
4. 所有异步操作必须有错误处理

### 4.3 零偏差原则
严格遵循设计文档，不允许任何形式的"优化"或"变通"。

### 4.4 命名与结构规范
严格遵循《直播SaaS平台移动端前端设计文档.md》第3.2节命名规范：
- 变量/函数：camelCase
- 类型/接口：PascalCase
- 常量：UPPER_SNAKE_CASE
- 文件：kebab-case

### 4.5 依赖导入规范
所有模块必须正确地从其他模块导入所需的类型或函数，使用 `@/` 路径别名。

### 4.6 平台差异化处理
针对不同平台（H5/小程序/App）的差异，使用条件编译：
```typescript
// #ifdef APP-PLUS
// App端特有代码
// #endif

// #ifdef H5
// H5端特有代码
// #endif

// #ifdef MP-WEIXIN
// 微信小程序特有代码
// #endif
```

### 4.7 App端特殊要求
1. **网络检测**：App端需要检测网络状态（`uni.getNetworkType`）
2. **权限申请**：使用相机、位置等功能前需要申请权限
3. **生命周期**：App有特殊的生命周期（`onShow`、`onHide`、`onLaunch`）
4. **原生能力**：可以调用原生模块（如直播推流、视频播放）

### 4.8 增量开发冲突检测规则

**本章节定义了在已有项目基础上进行零阶段开发时的冲突检测和处理策略。**

#### 4.8.1 文件冲突检测矩阵

| 文件路径 | 检测内容 | 冲突判定条件 | 处理策略 |
|---------|---------|------------|---------|
| `src/uni.scss` | 是否存在 | 如存在 | ⚠️ 检查是否与 `src/common/uni.scss` 冲突，优先使用 common/ 下的文件 |
| `src/common/uni.scss` | 是否存在且完整 | 如存在（529行） | ✅ 使用现有文件，不创建新的 `src/uni.scss` |
| `vite.config.ts` | `additionalData` 配置 | 如已配置全局注入 | ❌ **必须移除**（会导致循环引用） |
| `package.json` | `pinia` 位置 | 如在 devDependencies | ⚠️ 移动到 dependencies |
| `src/App.vue` | 生命周期钩子内容 | 如已有认证初始化 | ✅ 保留现有逻辑，在其后追加日志初始化 |
| `src/main.ts` | 应用初始化逻辑 | 如已有 Pinia、Element Plus | ✅ 保留现有逻辑，在 return 前追加日志初始化 |
| `.env.development` | 日志配置项 | 如已有 VITE_LOG_* | ⚠️ 合并配置，不覆盖其他配置 |
| `.env.app` | 日志配置项 | 如已有 VITE_LOG_* | ⚠️ 合并配置，不覆盖其他配置 |

#### 4.8.2 配置冲突严重等级

| 等级 | 标识 | 说明 | 处理方式 |
|------|------|------|---------|
| 🔴 致命冲突 | FATAL | 会导致编译失败或运行时错误 | **必须修复**，不能继续 |
| 🟡 警告冲突 | WARNING | 可能导致功能异常或性能问题 | **建议修复**，可以继续但需告知用户 |
| 🟢 提示冲突 | INFO | 不影响功能，仅建议优化 | **可选修复**，仅提示 |

**示例**：
- 🔴 `vite.config.ts` 中的全局注入 → 致命冲突（循环引用）
- 🟡 `pinia` 在 devDependencies → 警告冲突（打包时可能缺失）
- 🟢 缺少 `.editorconfig` → 提示冲突（代码风格不统一）

#### 4.8.3 处理策略决策树

```
发现文件/配置存在
    ├─ 内容是否完整且符合要求？
    │   ├─ 是 → ✅ 跳过创建，标记为"已验证"
    │   └─ 否 → 判断是否可增补
    │       ├─ 可增补（如 .env.* 追加配置） → ⚠️ 增补内容，不覆盖
    │       └─ 不可增补（如 vite.config 的错误配置） → 提示用户
    │           ├─ 用户同意修改 → 执行修改
    │           └─ 用户拒绝 → ❌ 停止生成，报告冲突
    │
    └─ 文件不存在
        └─ ✅ 创建新文件
```

#### 4.8.4 导入来源冲突检测

**必须验证的导入语句**：

| 导入项 | 错误来源 | 正确来源 | 检测方法 |
|--------|---------|---------|---------|
| `getCurrentInstance` | ❌ `@dcloudio/uni-app` | ✅ `vue` | 检查 import 语句 |
| `createSSRApp` | ❌ `@vue/runtime-core` | ✅ `vue` | 检查 import 语句 |
| `onLaunch`, `onShow`, `onHide` | ❌ `vue` | ✅ `@dcloudio/uni-app` | 检查 import 语句 |
| `uni.*` API | 无需导入（全局） | 直接使用 | 确保 tsconfig 包含 `@dcloudio/types` |

#### 4.8.5 TypeScript 类型冲突检测

**必须验证的类型定义**：

```typescript
// ❌ 不严格的类型（会在严格模式下报错）
function demo(obj: Record<string, any> | null): Record<string, any> | null

// ✅ 严格模式兼容的类型
function demo(obj: Record<string, any> | null | undefined): Record<string, any> | null | undefined
```

**检测规则**：
- 所有可能返回 `undefined` 的函数，类型定义必须包含 `| undefined`
- 所有接受可选参数的函数，参数类型必须包含 `| undefined`

---

## 5. 分步生成指令（Step-by-Step Module Generation）

---

### 步骤0：检查并增补项目配置文件（移动端支持）

**目标**：确保现有配置文件包含uni-app移动端开发所需的所有配置。

#### `package.json` - 检查并增补依赖
**检查项**：
1. **dependencies** 是否包含：
   - `vue@^3.x`、`pinia@^2.x`（状态管理）
   - uni-app核心包（如已有则跳过）
   
2. **devDependencies** 是否包含：
   - `@dcloudio/vite-plugin-uni` - uni-app Vite插件
   - `@dcloudio/types` - uni-app类型定义
   - `@dcloudio/uni-app` - uni-app核心（H5端）
   - **App端编译器**：
     - `@dcloudio/uni-app-plus` - App端基础包
     - `@dcloudio/uni-app-harmony` - 鸿蒙支持（可选）
   - **小程序编译器**：
     - `@dcloudio/uni-mp-weixin` - 微信小程序
   - TypeScript相关：`typescript`、`vue-tsc`、`@vue/tsconfig`
   - 构建工具：`vite`、`sass`（uni.scss需要）
   
3. **scripts** 是否包含移动端命令：
   - `dev:h5` - H5开发（`uni -p h5`）
   - `dev:mp-weixin` - 微信小程序开发（`uni -p mp-weixin`）
   - `dev:app` - App开发（`uni -p app`）
   - `dev:app-android` - Android真机调试（可选）
   - `dev:app-ios` - iOS真机调试（可选）
   - `build:h5` - H5构建
   - `build:mp-weixin` - 微信小程序构建
   - `build:app` - App构建（`uni build -p app`）
   - `build:app-android` - 构建Android安装包（可选）
   - `build:app-ios` - 构建iOS安装包（可选）

**如有缺失，在零阶段给出增补建议，但不强制修改现有文件**

**App端特别说明**：
- App端构建需要HBuilderX或云端打包服务
- 本地调试需要安装Android Studio（Android）或Xcode（iOS）
- 零阶段主要确保依赖和脚本完整，实际打包在后续阶段进行

#### `vite.config.ts` - 检查移动端构建配置
**检查项**：
1. 是否使用 `@dcloudio/vite-plugin-uni` 插件
2. 是否配置 `@` 路径别名指向 `src`
3. ⚠️ **重要**：**不要**配置 SCSS 全局变量注入（`additionalData`）
   - **原因**：项目的 `uni.scss` 使用 CSS 变量（`:root`），不是 Sass 变量
   - **后果**：全局注入会导致循环引用错误（`This file is already being loaded`）
   - **正确做法**：只在 `main.ts` 中导入一次 `import '@/common/uni.scss'`

#### `tsconfig.json` - 检查uni-app类型支持
**检查项**：
1. `compilerOptions.types` 是否包含 `@dcloudio/types`
2. `compilerOptions.paths` 是否配置 `@/*` 映射到 `src/*`

#### `.gitignore` - 检查移动端构建产物忽略
**检查项**：
是否包含以下忽略规则：
- `unpackage/` - uni-app构建产物
- `dist/build/` - 移动端构建目录
- `*.log`

**如有缺失配置，零阶段给出增补建议**

---

### 步骤1：核心应用文件生成（新建/修改）

#### `src/App.vue`
- **目标**：**修改**应用根组件，集成日志系统和全局错误处理。
- **要求**：
  1. **template** 部分为空（uni-app中App.vue不需要template）
  2. **script setup** 部分：
     - **导入** `onLaunch`、`onShow`、`onHide` 从 `"@dcloudio/uni-app"`
     - **导入** `getCurrentInstance` 从 `"vue"`（⚠️ 注意：不是 uni-app，Vue 3 核心 API）
     - **导入** logger 实例从 `'@/logs/logger'`
     - **在 `onLaunch` 中**初始化认证状态（如已有authStore）
     - **在 `onLaunch` 中**设置Vue全局错误处理器
  3. **style** 部分：设置 `#app` 基础样式

**关键代码示例**：
```typescript
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app"
import { getCurrentInstance } from "vue"  // ← 必须从 vue 导入，不是 uni-app
import { useAuthStore } from '@/store/auth'
import logger from '@/logs/logger'
```

#### `src/main.ts`
- **目标**：**修改**应用入口文件，初始化Vue应用和日志系统。
- **要求**：
  1. **导入** `createSSRApp` 从 `"vue"`
  2. **导入** `Pinia` 从 `"pinia"`
  3. **导入** `App.vue` 从 `"./App.vue"`
  4. **导入** `logger` 从 `'@/logs/logger'`（或 `'./logs/logger'`）
  5. **导入** `'@/common/uni.scss'`（⚠️ 注意：导入 common 目录下的现有文件）
  6. **在 `createApp` 函数中**：
     - **创建** Vue SSR 应用实例
     - **创建并使用** Pinia 实例
     - **初始化** logger（`logger.initialize().then(...)` 并记录启动日志）
     - **返回** `{ app, Pinia }`

#### `src/env.d.ts`
- **目标**：**声明**全局 TypeScript 类型。
- **要求**：
  1. **引用** `@dcloudio/types`
  2. **声明** `import.meta.env` 类型
  3. **声明** `.vue` 模块类型

#### `src/pages.json` - 检查并增补移动端配置
- **目标**：检查页面路由配置，确保包含移动端所需的全局样式和导航配置。
- **检查项**：
  1. `globalStyle` 是否引用 `uni.scss` 的颜色变量（如导航栏背景色、文本色）
  2. 是否配置 `tabBar`（底部导航栏，移动端常见）
  3. 是否配置 `easycom` 自动引入组件规则（提升开发效率）

**如有缺失，给出增补建议**（例如：建议在 `globalStyle` 中使用 `$color-primary` 等设计令牌）

#### `src/manifest.json` - 检查并增补移动端平台配置
- **目标**：检查应用清单配置，确保包含移动端平台（小程序、App）的必要配置。
- **检查项**：
  1. **微信小程序配置** (`mp-weixin`)：
     - `appid` 是否已配置（测试appid或真实appid）
     - 是否配置必要的权限（如网络请求、存储）
  
  2. **App配置** (`app-plus`)：
     - **基础信息**：
       - `appid`（App标识符）
       - `name`（应用名称）
       - `description`（应用描述）
       - `version.name` 和 `version.code`（版本号）
     - **权限配置** (`permissions`)：
       - `<uses-permission android:name="android.permission.CAMERA"/>` - 相机权限
       - `<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>` - 存储权限
       - `<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>` - 读取存储
       - `<uses-permission android:name="android.permission.INTERNET"/>` - 网络权限
       - `<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>` - 网络状态
     - **启动页配置** (`splashscreen`)：
       - `alwaysShowBeforeRender: true` - 是否等待首页渲染完成后关闭启动页
       - `autoclose: true` - 是否自动关闭启动页
       - `waiting: true` - 是否显示等待雪花
     - **状态栏配置** (`statusbar`)：
       - `immersed: false` - 是否沉浸式状态栏
       - `style: "dark"` - 状态栏样式（dark/light）
     - **原生模块** (`modules`)：
       - `VideoPlayer` - 视频播放（直播平台必需）
       - `Camera` - 相机模块（如需拍摄）
       - `Storage` - 本地存储
     - **分发配置** (`distribute`)：
       - iOS: `ios.dSYMs: false`, `ios.privacyDescription`（权限说明）
       - Android: `android.targetSdkVersion`, `android.minSdkVersion`
  
  3. **H5配置** (`h5`)：
     - `router.mode: "history"` 或 `"hash"` - 路由模式
     - `devServer.port` - 开发服务器端口
     - `devServer.https: false` - 是否使用HTTPS
     - `domain` - 部署域名

**如有缺失，给出详细的增补建议（包含完整的配置示例）**

**App端特别注意**：
- 零阶段可以使用测试appid（如 `__UNI__1234567`）
- 权限配置必须包含视频直播相关权限（CAMERA、RECORD_AUDIO等）
- iOS需要配置隐私权限说明（`privacyDescription`），否则无法提交App Store

#### `src/uni.scss`
- **目标**：**创建**全局样式变量文件，实现设计规范代码化。
- **要求**：
  1. **必须严格遵循**《直播SaaS平台移动端前端设计文档.md》第8.1节的设计令牌定义。
  2. **定义**以下五大设计系统：
     - 颜色系统（主题色、功能色、文本色、背景色、边框色）
     - 字体系统（字体族、字号rpx单位、行高）
     - 间距系统（基于8rpx基准）
     - 圆角系统（小/中/大圆角、圆形）
     - 阴影系统（小/中/大阴影）
  3. **所有变量**使用 `$` 前缀，命名采用 kebab-case 风格。
  4. **字号**必须使用 `rpx` 单位（移动端响应式单位）。

```scss
/**
 * 全局样式变量（设计令牌）
 * 遵循《直播SaaS平台移动端前端设计文档.md》第8.1节
 */

// ===== 8.1.1 颜色系统 =====
// 主题色
$color-primary: #509cec;
$color-primary-hover: #215588;
$color-primary-light-1: #e9f2fc;

// 功能色
$color-success: #28a745;
$color-danger: #dc3545;
$color-warning: #ffc107;
$color-info: #6c757d;

// 文本色
$color-text-primary: #121111;
$color-text-secondary: #6c757d;
$color-text-placeholder: #adb5bd;
$color-text-on-primary: #ffffff;

// 背景色
$color-background: #f8f9fa;
$color-background-light: #ffffff;

// 边框色
$color-border: #e9ecef;

// ===== 8.1.2 字体系统 =====
// 字体族
$font-family-sans-serif: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

// 字号（移动端rpx单位）
$font-size-small: 22rpx;   // 11px
$font-size-base: 26rpx;    // 13px
$font-size-medium: 30rpx;  // 15px
$font-size-large: 36rpx;   // 18px
$font-size-xlarge: 40rpx;  // 20px

// 行高
$line-height-base: 1.5;
$line-height-tight: 1.25;

// ===== 8.1.3 间距系统 =====
$spacing-xs: 8rpx;      // 4px
$spacing-small: 16rpx;  // 8px
$spacing-medium: 24rpx; // 12px
$spacing-large: 32rpx;  // 16px
$spacing-xlarge: 48rpx; // 24px
$spacing-xxlarge: 64rpx; // 32px

// ===== 8.1.4 圆角系统 =====
$radius-small: 8rpx;   // 4px
$radius-base: 12rpx;   // 6px
$radius-large: 16rpx;  // 8px
$radius-circle: 50%;   // 圆形

// ===== 8.1.5 阴影系统 =====
$shadow-small: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
$shadow-base: 0 8rpx 16rpx rgba(0, 0, 0, 0.08);
$shadow-large: 0 16rpx 32rpx rgba(0, 0, 0, 0.12);
```

---

### 步骤2：环境变量配置

#### `.env.development`
- **目标**：**配置**开发环境的日志系统参数。
- **要求**：
  - **在现有文件末尾新增**日志配置区块。
  - **启用**详细日志级别（DEBUG）。
  - **开启**控制台输出，**关闭**远程上报。
  - **定义**本地日志API占位符地址。

```bash
# ===== 日志配置（零阶段新增） =====
# 开发环境：详细日志，不上报
VITE_LOG_ENABLED=true
VITE_LOG_LEVEL=DEBUG
VITE_LOG_CONSOLE=true
VITE_LOG_REPORT_ENABLED=false
VITE_LOG_API_URL=/api/logs/batch
VITE_LOG_BATCH_SIZE=10
VITE_LOG_INTERVAL=30000
```

#### `.env.app`
- **目标**：**配置**生产环境的日志系统参数。
- **要求**：
  - **在现有文件末尾新增**日志配置区块。
  - **启用**精简日志级别（WARN）。
  - **关闭**控制台输出，**开启**远程上报。
  - **定义**真实的日志API地址（HTTPS）。

```bash
# ===== 日志配置（零阶段新增） =====
# 生产环境：精简日志，启用上报
VITE_LOG_ENABLED=true
VITE_LOG_LEVEL=WARN
VITE_LOG_CONSOLE=false
VITE_LOG_REPORT_ENABLED=true
VITE_LOG_API_URL=https://124.220.235.226/api/logs/batch
VITE_LOG_BATCH_SIZE=20
VITE_LOG_INTERVAL=60000
```

---

### 步骤3：基础常量定义

#### `src/common/constants.ts`
- **目标**：**创建**基础常量文件，零阶段仅包含日志和安全相关常量。
- **强制性要求**：
  1. **定义**应用基本信息常量（APP_NAME、APP_VERSION）。
  2. **定义**日志系统常量（存储key、最大条数、批量大小、上报间隔）。
  3. **定义**安全相关常量：
     - `SENSITIVE_FIELD_KEYS` 数组：列出所有需要脱敏的字段关键字。
     - 正则表达式：手机号、身份证、邮箱的验证规则。
  4. **所有常量**必须使用 UPPER_SNAKE_CASE 命名。
  5. **从环境变量读取**的配置必须提供默认值。

```typescript
/**
 * 应用基础常量
 * 零阶段：仅定义日志和安全相关常量
 * 阶段一：添加API、分页等业务常量
 */

// ===== 应用信息 =====
export const APP_NAME = '直播SaaS平台'
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0'

// ===== 日志相关 =====
export const LOG_STORAGE_KEY = 'app_logs'
export const MAX_LOG_ENTRIES = 1000
export const LOG_BATCH_SIZE = parseInt(import.meta.env.VITE_LOG_BATCH_SIZE || '20')
export const LOG_REPORT_INTERVAL = parseInt(import.meta.env.VITE_LOG_INTERVAL || '60000')

// ===== 安全相关 =====
export const SENSITIVE_FIELD_KEYS = [
  'password',
  'token',
  'accessToken',
  'refreshToken',
  'phone',
  'mobile',
  'idCard',
  'idcard',
  'email',
  'patientName',
  'medicalRecord'
]

export const PHONE_REGEX = /^1[3-9]\d{9}$/
export const ID_CARD_REGEX = /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/
export const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
```

---

### 步骤4：安全工具模块

#### `src/utils/security.ts`
- **目标**：**实现**完整的数据脱敏、XSS防护、URL校验功能。
- **强制性要求**：
  1. **必须实现**以下9个函数，每个函数必须处理边界情况（null、undefined、空字符串、非法格式）
  2. **复姓处理**：`maskPatientName` 必须包含常见复姓列表（至少60个）
  3. **递归脱敏**：`desensitizeObject` 和 `desensitizeArray` 必须支持深度递归处理嵌套数据结构
  4. **字段识别**：使用 `SENSITIVE_FIELD_KEYS` 自动识别需要脱敏的字段
  5. **所有函数**必须有完整的 JSDoc 注释和示例

**完整实现代码（约300行）**：

```typescript
/**
 * 安全工具模块
 * 提供数据脱敏、XSS防护、URL校验等安全功能
 * 遵循《直播SaaS平台移动端前端设计文档.md》第4章安全规范
 */

import { PHONE_REGEX, ID_CARD_REGEX, EMAIL_REGEX, SENSITIVE_FIELD_KEYS } from '@/common/constants'

/**
 * 手机号脱敏
 * @param phone - 手机号
 * @returns 脱敏后的手机号（保留前3后4位）
 * @example maskPhone('13812345678') // '138****5678'
 */
export function maskPhone(phone: string | null | undefined): string {
  if (!phone) return ''
  const phoneStr = String(phone).trim()
  if (!PHONE_REGEX.test(phoneStr)) return phoneStr
  return phoneStr.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 身份证号脱敏
 * @param idCard - 身份证号
 * @returns 脱敏后的身份证号（保留前3后4位）
 * @example maskIdCard('420102199001011234') // '420***********1234'
 */
export function maskIdCard(idCard: string | null | undefined): string {
  if (!idCard) return ''
  const idStr = String(idCard).trim()
  if (!ID_CARD_REGEX.test(idStr)) return idStr
  return idStr.replace(/^(.{3}).*(.{4})$/, '$1***********$2')
}

/**
 * 邮箱脱敏
 * @param email - 邮箱地址
 * @returns 脱敏后的邮箱（保留前2位@后全部）
 * @example maskEmail('abcdef@example.com') // 'ab***@example.com'
 */
export function maskEmail(email: string | null | undefined): string {
  if (!email) return ''
  const emailStr = String(email).trim()
  if (!EMAIL_REGEX.test(emailStr)) return emailStr
  return emailStr.replace(/^(.{2}).*(@.*)$/, '$1***$2')
}

/**
 * 患者姓名脱敏
 * @param name - 患者姓名
 * @returns 脱敏后的姓名（仅显示姓）
 * @example maskPatientName('张三') // '张**'
 * @example maskPatientName('欧阳修') // '欧阳*'
 */
export function maskPatientName(name: string | null | undefined): string {
  if (!name) return ''
  const nameStr = String(name).trim()
  if (nameStr.length <= 1) return nameStr
  if (nameStr.length === 2) return nameStr.charAt(0) + '*'
  
  // 复姓处理（68个常见复姓）
  const surnames = [
    '欧阳', '司马', '上官', '诸葛', '东方', '独孤', '南宫', '万俟',
    '闻人', '夏侯', '皇甫', '尉迟', '公羊', '澹台', '公冶', '宗政',
    '濮阳', '淳于', '单于', '太叔', '申屠', '公孙', '仲孙', '轩辕',
    '令狐', '徐离', '宇文', '长孙', '慕容', '鲜于', '闾丘', '司徒',
    '司空', '亓官', '司寇', '子车', '颛孙', '端木', '巫马', '公西',
    '漆雕', '乐正', '壤驷', '公良', '拓跋', '夹谷', '宰父', '谷梁',
    '段干', '百里', '东郭', '南门', '呼延', '羊舌', '微生', '梁丘',
    '左丘', '东门', '西门', '商', '第五', '赫连', '皇甫', '尉迟',
    '公羊', '澹台', '公冶', '宗政'
  ]
  
  for (const surname of surnames) {
    if (nameStr.startsWith(surname)) {
      return surname + '*'
    }
  }
  
  return nameStr.charAt(0) + '**'
}

/**
 * HTML内容转义（XSS防护）
 * @param html - 原始HTML字符串
 * @returns 转义后的安全字符串
 */
export function sanitizeHtml(html: string | null | undefined): string {
  if (!html) return ''
  const htmlStr = String(html)
  return htmlStr
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
}

/**
 * URL合法性校验
 * @param url - URL字符串
 * @returns 是否为合法URL
 */
export function validateUrl(url: string | null | undefined): boolean {
  if (!url) return false
  try {
    const urlObj = new URL(String(url))
    // 仅允许http和https协议
    return ['http:', 'https:'].includes(urlObj.protocol)
  } catch {
    return false
  }
}

/**
 * 对象深度脱敏
 * @param obj - 待脱敏的对象
 * @returns 脱敏后的对象
 */
export function desensitizeObject(obj: Record<string, any> | null | undefined): Record<string, any> | null | undefined {
  if (!obj || typeof obj !== 'object') return obj
  
  const result: Record<string, any> = {}
  
  for (const key in obj) {
    if (!obj.hasOwnProperty(key)) continue
    
    const value = obj[key]
    const lowerKey = key.toLowerCase()
    
    // 检查是否为敏感字段
    if (SENSITIVE_FIELD_KEYS.some(sensitive => lowerKey.includes(sensitive.toLowerCase()))) {
      // 根据字段类型选择脱敏方式
      if (lowerKey.includes('phone') || lowerKey.includes('mobile')) {
        result[key] = maskPhone(value)
      } else if (lowerKey.includes('idcard')) {
        result[key] = maskIdCard(value)
      } else if (lowerKey.includes('email')) {
        result[key] = maskEmail(value)
      } else if (lowerKey.includes('patient') && lowerKey.includes('name')) {
        result[key] = maskPatientName(value)
      } else {
        result[key] = '***'
      }
    } else if (Array.isArray(value)) {
      result[key] = desensitizeArray(value)
    } else if (typeof value === 'object' && value !== null) {
      result[key] = desensitizeObject(value)
    } else {
      result[key] = value
    }
  }
  
  return result
}

/**
 * 数组深度脱敏
 * @param arr - 待脱敏的数组
 * @returns 脱敏后的数组
 */
export function desensitizeArray(arr: any[] | null | undefined): any[] | null | undefined {
  if (!Array.isArray(arr)) return arr
  
  return arr.map(item => {
    if (Array.isArray(item)) {
      return desensitizeArray(item)
    } else if (typeof item === 'object' && item !== null) {
      return desensitizeObject(item)
    } else {
      return item
    }
  })
}

/**
 * 自动脱敏（根据数据类型自动选择脱敏方式）
 * @param data - 待脱敏的数据
 * @returns 脱敏后的数据
 */
export function autoDesensitize(data: any): any {
  if (data === null || data === undefined) return data
  
  if (Array.isArray(data)) {
    return desensitizeArray(data)
  } else if (typeof data === 'object') {
    return desensitizeObject(data)
  } else {
    return data
  }
}
```

---

### 步骤5：日志类型定义

#### `src/logs/logTypes.ts`
- **目标**：**定义**所有日志相关的类型、接口和枚举。
- **强制性要求**：
  1. **定义** `LogLevel` 枚举：DEBUG、INFO、WARN、ERROR、FATAL 五个级别。
  2. **创建** `LogEntry` 接口，必须包含以下字段：
     - level（日志级别）
     - message（日志消息）
     - timestamp（ISO 8601格式时间戳）
     - module（模块名称）
     - platform（平台标识）
     - appVersion（应用版本）
     - details（详细数据，已脱敏，可选）
     - userId（用户ID，已hash处理，可选）
     - sessionId（会话ID，可选）
     - deviceInfo（设备信息，可选）
     - error（错误堆栈，可选）
  3. **定义** `DeviceInfo` 接口：model、system、platform、screenWidth、screenHeight、networkType。
  4. **定义** `LoggerConfig` 接口及其子接口：
     - LogStorageConfig（存储配置）
     - LogReportConfig（上报配置）

```typescript
/**
 * 日志系统类型定义
 * 遵循《直播SaaS平台移动端前端设计文档.md》第3.5节日志管理规范
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
  FATAL = 'FATAL'
}

export interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  module: string
  platform: string
  appVersion: string
  details?: any
  userId?: string
  sessionId?: string
  deviceInfo?: DeviceInfo
  error?: string
}

export interface DeviceInfo {
  model: string
  system: string
  platform: string
  screenWidth: number
  screenHeight: number
  networkType: string
}

export interface LoggerConfig {
  enabled: boolean
  level: LogLevel
  console: boolean
  storage: LogStorageConfig
  reporting: LogReportConfig
}

export interface LogStorageConfig {
  storageKey: string
  maxEntries: number
}

export interface LogReportConfig {
  enabled: boolean
  apiUrl: string
  batchSize: number
  interval: number
}
```

---

### 步骤6：日志配置管理

#### `src/logs/logConfig.ts`
- **目标**：**配置**日志系统的行为和安全策略.
- **强制性要求**：
  1. **实现** `createLoggerConfig` 函数，必须**感知**当前环境（development/production）。
  2. **根据环境**返回不同的配置：
     - 开发环境：DEBUG级别，控制台输出开启，上报关闭
     - 生产环境：WARN级别，控制台输出关闭，上报开启
  3. **实现** `getLogLevelPriority` 函数：返回日志级别的优先级数值.
  4. **实现** `shouldLog` 函数：判断是否应该记录该级别的日志.
  5. **所有配置项**必须从环境变量读取，并提供合理的默认值.

```typescript
/**
 * 日志配置管理
 * 根据环境（开发/生产）提供不同的日志配置
 */

import { LoggerConfig, LogLevel } from './logTypes'
import { LOG_STORAGE_KEY, MAX_LOG_ENTRIES, LOG_BATCH_SIZE, LOG_REPORT_INTERVAL } from '@/common/constants'

function getEnvironment(): 'development' | 'production' {
  return import.meta.env.MODE === 'development' ? 'development' : 'production'
}

export function createLoggerConfig(): LoggerConfig {
  const env = getEnvironment()
  const isDev = env === 'development'
  
  return {
    enabled: import.meta.env.VITE_LOG_ENABLED === 'true',
    level: (import.meta.env.VITE_LOG_LEVEL as LogLevel) || (isDev ? LogLevel.DEBUG : LogLevel.WARN),
    console: import.meta.env.VITE_LOG_CONSOLE === 'true',
    storage: {
      storageKey: LOG_STORAGE_KEY,
      maxEntries: MAX_LOG_ENTRIES
    },
    reporting: {
      enabled: import.meta.env.VITE_LOG_REPORT_ENABLED === 'true',
      apiUrl: import.meta.env.VITE_LOG_API_URL || '/api/logs/batch',
      batchSize: LOG_BATCH_SIZE,
      interval: LOG_REPORT_INTERVAL
    }
  }
}

export function getLogLevelPriority(level: LogLevel): number {
  const priorities: Record<LogLevel, number> = {
    [LogLevel.DEBUG]: 0,
    [LogLevel.INFO]: 1,
    [LogLevel.WARN]: 2,
    [LogLevel.ERROR]: 3,
    [LogLevel.FATAL]: 4
  }
  return priorities[level] || 0
}

export function shouldLog(level: LogLevel, config: LoggerConfig): boolean {
  if (!config.enabled) return false
  return getLogLevelPriority(level) >= getLogLevelPriority(config.level)
}
```

---

### 步骤7：日志系统核心实现

#### `src/logs/logger.ts`
- **目标**：**实现**完整的日志记录、处理和上报功能。
- **数据流与错误处理要求**：
  1. **实现** `log` 方法作为核心入口。此方法必须**接收**日志级别、模块、消息和可选数据。
  2. **数据流**：
     - **输入**：`log` 方法接收原始日志数据。
     - **级别过滤**：**调用** `shouldLog` 检查是否需要记录该级别的日志。
     - **数据脱敏**：**调用** `autoDesensitize` 方法对 `details` 参数进行深度递归脱敏。
     - **构建条目**：**创建** `LogEntry` 对象，包含所有必需字段（timestamp使用ISO 8601格式）。
     - **存储**：**将**处理后的 `LogEntry` 对象 **push** 到内存中的 `logQueue` 数组，并**调用** `saveLogsToStorage` 将整个队列**写入** `uni.storage`。
     - **输出**：如果 `config.console` 为 true，**调用** `printToConsole` 将日志**输出**到控制台。
  3. **状态变化逻辑**：
     - **存储裁剪**：在**保存**到本地存储前，**检查** `logQueue` 的长度是否超过 `config.storage.maxEntries`。如果超过，**必须截断**数组（使用slice），只保留最新的日志。
     - **批量上报**：当 `logQueue` 长度达到 `config.reporting.batchSize`，或定时器触发时，**必须**触发 `reportLogs` 方法。
     - **定时机制**：使用 `setInterval` 创建定时器，间隔为 `config.reporting.interval`。
  4. **错误处理**：
     - 所有对 `uni.storage` 的读写操作都必须被 `try...catch` 包裹。如果 `uni.getStorageSync` 失败（例如数据损坏），**必须**在 `catch` 块中**清空** `logQueue` 并**移除**损坏的 storage item。
     - `reportLogs` 中的 `uni.request` 必须处理 `fail` 回调。如果上报失败，**不能**清除已上报的日志，**必须**将日志 `unshift` 回队列头部，以便下次重试。
  5. **全局错误捕获**：
     - **实现** `setupErrorCapture` 方法，在 `initialize` 时被调用。
     - **必须使用** `uni.onError` 捕获全局JS错误，**调用** `this.error` 方法记录。
     - **必须使用** `uni.onUnhandledRejection` 捕获未处理的Promise拒绝，**调用** `this.error` 方法记录。
  6. **生命周期管理**：
     - **实现** `setupLifecycleListeners` 方法。
     - **使用** `uni.onAppHide` 监听应用进入后台，**触发** `reportLogs` 立即上报。
     - **使用** `uni.onAppShow` 监听应用返回前台，**记录**日志。
  7. **设备信息收集**：
     - **使用** `uni.getSystemInfoSync` 同步获取设备信息。
     - **使用** `uni.getNetworkType` 异步获取网络类型。
  8. **类结构**：
     - **私有属性**：config、logQueue、reportTimer、sessionId、deviceInfo、isInitialized
     - **公共方法**：initialize、debug、info、warn、error、fatal、destroy
     - **私有方法**：log、collectDeviceInfo、loadLogsFromStorage、saveLogsToStorage、reportLogs、setupErrorCapture、setupLifecycleListeners、startReportTimer、stopReportTimer、printToConsole、generateSessionId

**导出方式**：
```typescript
export const logger = new Logger()
export default logger
```

---

### 步骤8：应用入口集成（已在步骤0和步骤1中处理）

#### `src/main.ts`
- **目标**：在应用入口**初始化**日志系统。
- **要求**：
  - **在 `return` 语句之前**新增日志系统初始化代码。
  - **导入** logger 实例。
  - **调用** `logger.initialize()` 初始化日志系统。
  - **记录**应用启动日志。

```typescript
// 在现有代码中添加导入
import { logger } from './logs/logger'

export function createApp() {
  const app = createSSRApp(App);
  const pinia = Pinia.createPinia();
  app.use(pinia);
  
  // ... 现有的 Element Plus 配置代码 ...
  
  // 新增：初始化日志系统（在 return 之前）
  logger.initialize()
  logger.info('App', '应用启动成功', {
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    platform: 'unknown' // 运行时会自动获取
  })
  
  return {
    app,
    Pinia,
  };
}
```

#### `src/App.vue`
- **目标**：在应用根组件**设置**Vue层的全局错误处理。
- **要求**：
  - **在 `onLaunch` 钩子中**新增全局错误处理器配置。
  - **导入** logger 实例和 `getCurrentInstance`。
  - **配置** Vue 的 `errorHandler` 捕获组件错误。
  - **注意**：`uni.onError` 和 `uni.onUnhandledRejection` 已在 logger.ts 的 `setupErrorCapture` 中处理，此处仅处理Vue层错误。

```typescript
// 在 <script setup lang="ts"> 中添加导入
import { logger } from '@/logs/logger'
import { getCurrentInstance } from 'vue'

onLaunch(() => {
  console.log("App Launch");
  const authStore = useAuthStore();
  authStore.initializeAuth();
  
  // 新增：设置Vue全局错误处理器（作为uni.onError的补充）
  const instance = getCurrentInstance()
  const app = instance?.appContext.app
  if (app) {
    app.config.errorHandler = (err: any, instance: any, info: string) => {
      logger.error('VueError', 'Vue组件异常', {
        error: err?.message || String(err),
        stack: err?.stack,
        componentName: instance?.$options?.name || 'Unknown',
        errorInfo: info
      })
    }
  }
});
```

---

## 6. 最终交付与质量保证协议

### 6.1 输出格式
- 每个文件一个完整、可直接运行的代码块，并标注清晰的文件路径。
- 禁止在代码之外添加任何解释、道歉或不必要的寒暄。

### 6.2 自我修正
在每一步生成后，你必须在内部进行自查。如果发现与设计文档或本提示词有任何偏差，必须**立即撤销并重新生成**。

### 6.3 功能完整性检查清单

生成完成后，请确认以下功能已全部实现：

**安全模块（9个函数）**：
- [ ] maskPhone() - 手机号脱敏（保留前3后4位）
- [ ] maskIdCard() - 身份证脱敏（保留前3后4位）
- [ ] maskEmail() - 邮箱脱敏（保留前2位@后全部）
- [ ] maskPatientName() - 患者姓名脱敏（支持至少60个复姓）
- [ ] sanitizeHtml() - HTML转义（XSS防护）
- [ ] validateUrl() - URL校验（仅http/https）
- [ ] desensitizeObject() - 对象深度递归脱敏
- [ ] desensitizeArray() - 数组深度递归脱敏
- [ ] autoDesensitize() - 自动脱敏

**日志模块**：
- [ ] LogLevel枚举 - 5个级别（DEBUG/INFO/WARN/ERROR/FATAL）
- [ ] LogEntry接口 - 完整字段定义
- [ ] DeviceInfo接口 - 设备信息字段
- [ ] LoggerConfig接口 - 配置结构
- [ ] createLoggerConfig() - 环境感知配置
- [ ] shouldLog() - 级别过滤判断
- [ ] Logger.initialize() - 初始化流程
- [ ] Logger.debug/info/warn/error/fatal() - 5个日志方法
- [ ] Logger.log() - 核心记录方法（级别过滤、脱敏、存储、输出）
- [ ] Logger.collectDeviceInfo() - 设备信息收集
- [ ] Logger.loadLogsFromStorage() - 本地日志加载
- [ ] Logger.saveLogsToStorage() - 本地日志保存（含裁剪逻辑）
- [ ] Logger.reportLogs() - 批量上报（含失败重试）
- [ ] Logger.setupErrorCapture() - 全局错误捕获（uni.onError + uni.onUnhandledRejection）
- [ ] Logger.setupLifecycleListeners() - 生命周期监听（onAppHide/onAppShow）
- [ ] Logger.startReportTimer() - 定时上报启动
- [ ] Logger.stopReportTimer() - 定时上报停止
- [ ] Logger.printToConsole() - 控制台输出
- [ ] Logger.destroy() - 资源清理

**项目配置文件（8个 - 已存在，仅验证）**：
- [x] package.json - 已存在，无需修改
- [x] vite.config.ts - 已存在，无需修改
- [x] tsconfig.json - 已存在，无需修改
- [x] .eslintrc.cjs - 已存在，无需修改
- [x] .prettierrc - 已存在，无需修改
- [x] jest.config.js - 已存在，无需修改
- [x] .gitignore - 已存在，无需修改
- [x] README.md - 已存在，无需修改

**核心应用文件（6个 - 部分新建/部分修改）**：
- [ ] src/App.vue - **修改**现有文件（新增全局错误处理）
- [ ] src/main.ts - **修改**现有文件（新增日志初始化）
- [x] src/pages.json - 已存在，无需修改
- [x] src/manifest.json - 已存在，无需修改
- [ ] src/env.d.ts - **新建**TypeScript类型声明
- [ ] src/uni.scss - **新建**全局样式变量（设计令牌）

**空目录结构**：
- [ ] src/api/ - API接口目录
- [ ] src/components/ - 组件目录
- [ ] src/pages/ - 页面目录
- [ ] src/static/ - 静态资源目录
- [ ] src/store/ - 状态管理目录
- [ ] src/types/ - 类型定义目录
- [ ] src/utils/ - 工具函数目录
- [ ] src/common/ - 公共资源目录
- [ ] src/logs/ - 日志模块目录
- [ ] tests/ - 测试目录

**环境配置**：
- [ ] .env.development - 开发环境配置（DEBUG、控制台输出、不上报）
- [ ] .env.app - 生产环境配置（WARN、无控制台输出、启用上报）

### 6.4 错误预防检查表（代码生成前强制检查）

**AI 在执行代码生成前必须完成以下检查清单**：

#### ✅ 环境检查（7项）
- [ ] 1. 已使用 `list_dir` 扫描项目目录结构
- [ ] 2. 已使用 `read_file` 检查至少 8 个关键文件的存在性
- [ ] 3. 已识别至少 3 个潜在冲突点（vite.config、uni.scss、类型定义）
- [ ] 4. 已确认技术栈细节（Vue3、uni-app版本、TypeScript配置）
- [ ] 5. 已制定生成策略（新建X个，修改Y个，跳过Z个）
- [ ] 6. 已输出操作清单并等待用户确认
- [ ] 7. 用户已明确回复"同意"或"Y"才可继续

#### ✅ 技术细节检查（5项）
- [ ] 1. 所有 `getCurrentInstance` 导入都标注了来源包 `"vue"`
- [ ] 2. 所有 TypeScript 函数返回类型都包含 `| undefined`（如适用）
- [ ] 3. 所有 `uni.*` API 调用都有 `success`/`fail` 错误处理
- [ ] 4. 没有配置 `vite.config.ts` 的 `additionalData` 全局注入
- [ ] 5. 使用 `import '@/common/uni.scss'` 而不是创建新的 `src/uni.scss`

#### ✅ 代码质量检查（4项）
- [ ] 1. 所有敏感操作（storage、request）都有 try-catch 包裹
- [ ] 2. 所有 Promise 都有 `.catch()` 或 try-catch 处理
- [ ] 3. 所有函数都有完整的 JSDoc 注释
- [ ] 4. 没有 TODO 注释（日志API占位符除外）

**⚠️ 只有全部完成上述检查后，AI 才能开始生成代码！**

---

### 6.5 验证标准

生成完成后，必须满足以下验证标准：

1. **项目可运行性**：
   - 项目可以无错误地执行 `npm install`
   - 项目可以无错误地执行 `npm run dev:h5`
   - 浏览器可以正常访问开发服务器
   - **没有循环引用错误**（`This file is already being loaded`）
   - **没有导入错误**（`Module has no exported member`）

2. **设计令牌一致性**：
   - 使用现有的 `src/common/uni.scss` 文件
   - CSS变量与《直播SaaS平台移动端前端设计文档.md》第8.1节完全一致
   - 所有颜色、字号、间距、圆角、阴影变量都已定义
   - 变量命名遵循规范（使用 `$` 前缀或 `--` 前缀，kebab-case风格）

3. **TypeScript类型检查**：
   - 所有 `.ts` 文件可以通过 `vue-tsc --noEmit` 类型检查
   - 没有 TypeScript 编译错误
   - 所有类型定义都包含 `| undefined`（严格模式）

4. **代码规范检查**：
   - 所有文件可以通过 `npm run lint` 检查
   - 代码格式符合 Prettier 规范
   - 所有导入语句都标注了正确的来源包

5. **功能完整性**：
   - 日志系统在开发环境下可以正常输出到控制台
   - 全局错误捕获可以正常工作
   - 环境变量可以正确读取
   - 数据脱敏功能正常工作

### 6.6 最终一致性断言

在完成所有文件生成后，输出：

```
[PHASE 0 ASSERTION - MOBILE - V1.1]
Mobile project foundation and infrastructure setup is complete.

- Environment Check & Conflict Detection: 100% ✓
  - Directory scan: Completed ✓
  - File existence check: 10/10 files checked ✓
  - Conflict identification: 3 conflicts resolved ✓
  - Technical details verified: All passed ✓
  - User confirmation: Received ✓

- Project Configuration Files: 8/8 (Already Existed - Verified) ✓
  - package.json: Verified (dependencies correct) ✓
  - vite.config.ts: Verified (NO global injection) ✓
  - tsconfig.json: Verified (@dcloudio/types included) ✓
  - .gitignore: Verified (unpackage/ included) ✓
  - Build & Tool Configs: Verified ✓
  - Documentation: Verified ✓

- Core Application Files: 6/6 (100%) ✓
  - Modified: App.vue (getCurrentInstance from "vue"), main.ts (logger init) ✓
  - Verified: pages.json, manifest.json ✓
  - Augmented: env.d.ts (uni-app types + env vars) ✓
  - Used Existing: common/uni.scss (NOT created new src/uni.scss) ✓

- Directory Structure: 100% ✓
  - All required directories created or verified

- Security Module Implementation: 100% ✓
  - Data Desensitization Functions: 9/9
    - TypeScript types: Strict mode (| null | undefined) ✓
  - XSS Protection: Enabled
  - URL Validation: Implemented

- Logger Module Implementation: 100% ✓
  - Log Types Definition: 100%
  - Environment-aware Configuration: 100%
  - Core Logger Class: 100%
  - Dynamic Logic Implementation: 100%
  - Auto Desensitization: Integrated
  - Batch Reporting: Enabled
  - Global Error Capture: Enabled (uni.onError + Vue errorHandler)

- Environment Configuration: Complete ✓
  - .env.development: LOG_LEVEL=DEBUG, console=true
  - .env.app: LOG_LEVEL=WARN, console=false

- Application Integration: Complete ✓
  - main.ts: logger.initialize() added
  - App.vue: Vue errorHandler configured
  - Correct imports: getCurrentInstance from "vue" ✓

- Technical Details Accuracy: 100% ✓
  - No circular reference (vite.config has NO additionalData) ✓
  - Correct import sources (vue, @dcloudio/uni-app) ✓
  - TypeScript strict types (| undefined included) ✓

- Zero Business Logic Principle: Adhered ✓
```

---

## 附录A：常见错误与解决方案

本附录总结了在零阶段代码生成过程中最常见的3类错误及其解决方案。

### A.1 循环引用错误

**错误信息**：
```
[sass] This file is already being loaded.
  ╷
1 │ @import "@/common/uni.scss";
  │         ^^^^^^^^^^^^^^^^^^^
  ╵
  src\common\uni.scss 1:9  root stylesheet
```

**问题原因**：
在 `vite.config.ts` 中配置了全局注入：
```typescript
css: {
  preprocessorOptions: {
    scss: {
      additionalData: '@import "@/common/uni.scss";'  // ← 这会导致循环引用
    }
  }
}
```

当 Sass 编译 `uni.scss` 时：
1. Vite 自动在文件开头注入 `@import "@/common/uni.scss";`
2. 然后编译文件本身的内容
3. 结果：`uni.scss` 导入了自己 → **无限循环**

**解决方案**：
```typescript
// ✅ 方案1：完全移除全局注入（推荐）
css: {
  preprocessorOptions: {
    scss: {
      // 不配置 additionalData
      quietDeps: true,
      silenceDeprecations: ['legacy-js-api']
    }
  }
}

// 在 main.ts 中导入一次即可
import '@/common/uni.scss'
```

**原理说明**：
- **Sass 变量**（`$color: #fff`）需要全局注入，因为编译时需要替换
- **CSS 变量**（`--color: #fff`）不需要全局注入，运行时自动生效
- 本项目使用 CSS 变量，所以不需要全局注入

---

### A.2 导入来源错误

**错误信息**：
```
Module '@dcloudio/uni-app' has no exported member 'getCurrentInstance'
```

**问题原因**：
```typescript
// ❌ 错误写法
import { getCurrentInstance } from "@dcloudio/uni-app"
```

`getCurrentInstance` 是 **Vue 3 的核心 API**，不属于 uni-app。

**解决方案**：
```typescript
// ✅ 正确写法
import { getCurrentInstance } from "vue"  // Vue 3 核心 API
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app"  // uni-app 生命周期
```

**记忆方法**：
| API | 来源包 | 说明 |
|-----|-------|------|
| `getCurrentInstance` | `vue` | Vue 3 核心，获取组件实例 |
| `createSSRApp` | `vue` | Vue 3 核心，创建 SSR 应用 |
| `onLaunch`, `onShow`, `onHide` | `@dcloudio/uni-app` | uni-app 专有生命周期 |
| `uni.*` 全局API | 无需导入 | uni-app 全局对象，直接使用 |

---

### A.3 TypeScript 类型不严格错误

**错误信息**：
```
Type 'undefined' is not assignable to type 'Record<string, any> | null'
```

**问题原因**：
```typescript
// ❌ 不严格的类型定义
export function desensitizeObject(obj: Record<string, any> | null): Record<string, any> | null {
  if (!obj) return obj  // obj 可能是 undefined，但返回类型没有 | undefined
}
```

在 TypeScript 严格模式下，`null` 和 `undefined` 是**不同的类型**。

**解决方案**：
```typescript
// ✅ 严格模式兼容的类型定义
export function desensitizeObject(
  obj: Record<string, any> | null | undefined
): Record<string, any> | null | undefined {
  if (!obj) return obj  // ✓ 同时处理 null 和 undefined
}
```

**规则**：
- 所有可能接收 `undefined` 的参数，类型必须显式包含 `| undefined`
- 所有可能返回 `undefined` 的函数，返回类型必须显式包含 `| undefined`
- 使用 `!obj` 判断时，可以同时处理 `null` 和 `undefined`

---

### A.4 其他常见错误速查表

| 错误类型 | 症状 | 快速解决 |
|---------|------|---------|
| **文件重复创建** | 创建了 `src/uni.scss`，但已有 `src/common/uni.scss` | 删除新创建的，使用现有的 |
| **Pinia 打包缺失** | `pinia` 在 devDependencies | 移动到 dependencies |
| **环境变量读取失败** | `import.meta.env.XXX` 为 undefined | 检查 `.env.*` 文件和 `env.d.ts` 声明 |
| **uni API 未定义** | `uni is not defined` | 确保 tsconfig.json 包含 `@dcloudio/types` |
| **Sass 弃用警告** | `@import is deprecated` | 可忽略或迁移到 `@use`（不影响功能） |

---

## 附录B：增量开发最佳实践

### B.1 执行前检查清单（复制使用）

```markdown
## 零阶段代码生成前检查清单

### 第一步：环境探查
- [ ] 已执行 list_dir 扫描 src/ 目录
- [ ] 已读取 10 个关键文件
- [ ] 已输出项目状态分析报告

### 第二步：冲突检测
- [ ] 检查 vite.config.ts 的 additionalData（必须为空）
- [ ] 检查 src/uni.scss vs src/common/uni.scss（使用 common/）
- [ ] 检查 package.json 的 pinia 位置（必须在 dependencies）

### 第三步：技术验证
- [ ] 确认 getCurrentInstance 从 "vue" 导入
- [ ] 确认 TypeScript 类型包含 | undefined
- [ ] 确认所有 uni API 有错误处理

### 第四步：用户确认
- [ ] 已输出操作清单（新建/修改/跳过）
- [ ] 用户已明确回复"同意"

✅ 全部完成后才能开始生成代码
```

### B.2 验证命令清单

```bash
# 1. 安装依赖
npm install

# 2. TypeScript 类型检查
npx vue-tsc --noEmit

# 3. ESLint 检查
npm run lint

# 4. 启动 H5 开发服务器
npm run dev:h5

# 5. 检查是否有循环引用错误
# 如果出现 "This file is already being loaded"，检查 vite.config.ts

# 6. 检查是否有导入错误
# 如果出现 "Module has no exported member"，检查 import 语句来源
```

---

**文档版本**: V1.1 (增量开发增强版)  
**创建日期**: 2025-11-20  
**最后更新**: 2025-11-20  
**适用平台**: uni-app (H5/Android/iOS/微信小程序)  
**参考文档**: 《直播SaaS平台移动端前端设计文档.md》  
**更新内容**: 新增环境探查、冲突检测、错误预防机制
