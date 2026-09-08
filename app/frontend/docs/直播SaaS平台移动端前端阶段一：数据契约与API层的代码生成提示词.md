# 直播SaaS平台移动端前端阶段一：数据契约与API层的代码生成提示词 (增量开发版 V1.0)

---

## ⚠️ 增量开发特别声明

**本项目是在现有可运行的网页端uni-app项目基础上进行移动端增量开发！**

- ✅ **零阶段已完成**：项目配置、日志系统、安全模块、认证系统、设计token系统
- ✅ **已有基础设施**：`src/utils/request.ts`（385行，功能完善）、部分类型定义、部分API封装
- ⚠️ **关键原则**：不覆盖现有代码、不破坏现有功能、增量补充缺失部分

**在生成任何代码之前，你必须先执行第0章的强制性前置检查！**

---

## 🏗️ 架构基础（必读）

**在开始阶段一开发前，你必须先阅读以下架构文档：**

📖 **平台分层架构规范**：`docs/平台分层架构规范（阶段零点五完成）.md`

### 为什么必须阅读？

在阶段零完成后、阶段一开始前，项目已完成**平台分层架构重构**，建立了支持多平台（H5/App/小程序）的组件体系。该文档包含所有架构规范，你必须遵守。

### 该文档包含的核心内容：

1. **组件目录结构**（common/h5/app/mp）
   - ⚠️ 已存在7个组件（5个通用 + 2个平台特定）
   - ⚠️ 禁止在 `src/components/` 根目录创建组件

2. **组件导入规范**
   - ✅ 必须使用 `@/components/common/` 导入通用组件
   - ✅ 平台特定组件必须配合条件编译（`#ifdef H5`）

3. **平台检测工具**（`src/utils/platform.ts`）
   - `isH5()`, `isApp()`, `getPlatform()` 等函数

4. **新建组件决策流程**
   - 完整的决策树图，帮助判断组件应该放在哪个目录

5. **禁止的7个操作**
   - 不要重复创建已存在的7个组件
   - 不要使用相对路径导入
   - 不要在根目录创建组件

6. **阶段一特别注意事项**
   - API层开发通常不需要区分平台
   - 类型定义通常不需要区分平台
   - 极少数情况（如文件上传）需要平台适配

### 快速查阅要点：

```markdown
Q: 阶段一是否需要创建组件？
A: 通常不需要。阶段一主要创建类型定义和API封装。

Q: 如果需要在类型文件中引用组件类型怎么办？
A: import type { ComponentPublicInstance } from 'vue';

Q: API封装是否需要区分平台？
A: 大多数不需要，使用统一的 @/utils/request 即可。
   极少数情况（文件上传）需要使用 isH5()/isApp() 判断。

Q: 已存在哪些组件？
A: 通用组件：AppButton, ModalDialog, RoomCard, 
            RoomSelectionDialog, UserInfoHeader
   平台组件：VideoPlayerH5, VideoPlayerApp
```

### ⚠️ 重要提示：

**请先花3-5分钟完整阅读架构文档**，然后再继续执行第0章的前置检查。

特别关注：
- 第1节：组件目录结构和已存在的7个组件清单
- 第6节：禁止的7个操作
- 第8.1节：阶段一开发注意事项

---

## 第0章：强制性前置检查与冲突检测 ⚡（必须先执行）

### 0.1 检查目的

在生成任何代码之前，必须全面了解项目现状，避免：
- ❌ 覆盖已有的完善代码
- ❌ 与现有类型定义冲突
- ❌ 创建重复的工具函数
- ❌ 破坏现有的导入依赖关系

### 0.2 必须执行的检查步骤

#### 步骤0.1：验证项目配置（强制）

**检查tsconfig.json配置**：

验证TypeScript路径别名配置是否存在：
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["src/*"],
      "@/types/*": ["src/types/*"],
      "@/api/*": ["src/api/*"],
      "@/utils/*": ["src/utils/*"],
      "@/logs/*": ["src/logs/*"]
    }
  }
}
```

**导入路径策略**：
- ✅ **如果配置了@别名**：优先使用@别名导入
  ```typescript
  import { Brand } from '@/types/brand';
  import { get, post } from '@/utils/request';
  import { logger } from '@/logs/logger';
  ```

- ⚠️ **如果没有配置@别名**：使用相对路径导入
  ```typescript
  import { Brand } from '../types/brand';
  import { get, post } from '../utils/request';
  import { logger } from '../logs/logger';
  ```

**执行命令**：使用 `read_file` 工具读取 `tsconfig.json` 检查配置。

#### 步骤1：读取现有核心文件（强制）

你必须先读取以下文件，了解现有实现：

```bash
必须读取的文件清单：
✅ src/utils/request.ts（385行）- 统一请求工具
✅ src/types/room.ts（27行）- Room类型定义
✅ src/types/session.ts（37行）- Session类型定义
✅ src/types/topic.ts（如存在）- Topic类型定义
✅ src/api/room.ts（101行）- Room API封装
✅ src/api/session.ts（63行）- Session API封装
✅ src/api/topic.ts（如存在）- Topic API封装
```

**执行命令**：使用 `read_file` 工具逐个读取以上文件。

#### 步骤2：扫描目录结构（强制）

```bash
必须扫描的目录：
✅ src/types/（列出所有.ts文件）
✅ src/api/（列出所有.ts文件）
✅ src/utils/（列出所有.ts文件）
✅ src/store/（列出所有.ts文件，检查状态管理）
✅ src/logs/（确认日志系统文件）
```

**执行命令**：使用 `find_by_name` 或 `list_dir` 工具扫描目录。

#### 步骤3：在聊天窗口输出项目现状分析（强制）

**重要**：❗ 不要生成单独的分析报告文件，直接在聊天窗口中展示分析结果！

基于步骤1和步骤2的检查结果，在聊天窗口中输出以下结构化分析：

---

**📊 阶段一项目现状分析**

**一、已存在且功能完善的文件（✅ 保留，无需修改）**
- 列出所有检查后确认完善的文件
- 注明文件路径、行数、核心功能
- 给出"无需修改"的结论

**二、已存在但需补充字段的文件（🔧 使用multi_edit）**
- 列出需要补充的文件
- 明确列出现有字段清单
- 明确列出缺失字段及来源（后端文档章节）
- 说明操作方式（multi_edit，保留现有字段）

**三、已存在的API文件（✅ 功能完整或需微调）**
- 列出现有API文件及实现的函数
- 指出与后端文档的差异（如HTTP方法不一致）
- 给出调整建议

**四、缺失的类型定义文件（➕ 需新建）**
- 列出所有需要新建的类型文件
- 基于后端文档Section 2标注来源

**五、缺失的API封装文件（➕ 需新建）**
- 列出所有需要新建的API文件
- 基于后端文档Section 4标注来源

**六、零阶段遗留工具文件（➕ 需新建）**
- 列出storage.ts、enums.ts等工具文件

**七、冲突风险评估**
- ⚠️ 列出潜在冲突点
- ✅ 给出安全操作策略

---

#### 步骤4：等待用户确认（强制）

在聊天窗口输出分析结果后，**必须等待用户确认**才能继续生成代码。

向用户提问：
```
📋 以上是项目现状分析结果。

请确认：
1. 分析结果是否准确？
2. 是否有遗漏或需要调整的地方？
3. 如果确认无误，请输入"确认继续"开始代码生成。
```

**禁止**在用户确认前开始生成任何代码！

---

## 第1章：角色定义（Role Definition）

你是一名**资深移动端前端工程师**，具备以下专业技能：

- **精通技术栈**：uni-app、Vue 3 Composition API、TypeScript、Pinia状态管理
- **跨端开发经验**：H5、Android、iOS、微信小程序等多端适配
- **直播平台经验**：大型直播SaaS平台前端架构与实现经验
- **医学场景理解**：熟悉医学直播平台的特殊需求（隐私保护、数据脱敏、专业性）
- **增量开发能力**：能够在现有项目基础上进行安全的增量开发，不破坏现有功能

**你的任务是根据详细设计文档和现有代码基础，编写高质量、功能完整、可直接运行的增量代码。**

---

## 第2章：任务目标（Task Objective）

本次任务为**直播SaaS平台移动端前端的阶段一：数据契约与API层（增量开发模式）**。

### 2.1 核心目标

在现有项目基础上，**补充和完善**数据契约层与API层，具体包括：

1. **补充现有类型定义**（room.ts, session.ts）- 添加缺失字段
2. **创建通用类型定义**（common.ts）- 提供项目通用类型
3. **创建后端新增模块的类型**（brand, expert, category, tag等）
4. **创建后端新增模块的API封装**（与后端文档100%一致）
5. **创建零阶段遗留的工具**（storage.ts, enums.ts）

### 2.2 质量要求

- ✅ **功能完整性**：所有API函数都能实际调用，所有类型都能正确使用
- ✅ **类型安全性**：TypeScript严格模式，禁止any，明确null和undefined
- ✅ **接口一致性**：与后端文档100%一致（URL、方法、参数、返回值）
- ✅ **增量安全性**：不覆盖现有代码，使用multi_edit补充字段
- ✅ **移动端优化**：考虑uni-app特性、触摸优化、性能优化
- ✅ **文档完整性**：所有代码包含完整的JSDoc注释

---

## 第3章：核心上下文信息（Context）

### 3.1 唯一事实来源（Single Source of Truth）

#### 3.1.1 移动端前端设计文档

**文件**：`直播SaaS平台移动端前端设计文档.md`

**关键章节**：
- **第3章 - 移动端前端开发规范**
  - 3.3节：项目结构规范（目录结构、命名规范）
  - 3.4节：Git提交规范
  - 3.5节：日志管理规范
  - 3.6节：前端设计概述（技术栈、设计原则）

- **第4章 - 移动端安全规范**
  - 4.1节：XSS防护
  - 4.2节：敏感信息脱敏（手机号、身份证、邮箱等）
  - 4.3节：Token安全存储
  - 4.4节：API请求安全（强制HTTPS、Token注入）
  - 4.5节：日志脱敏

- **第6章 - 核心数据模型**
  - 6.2节：数据库表结构 → TypeScript接口转换规则
  - 所有表字段定义、类型、约束

- **第8章 - API接口映射总览表**
  - 前端页面与API接口的对应关系

#### 3.1.2 后端API接口文档

**文件**：`后端新增api接口和模块设计文档-v2.md`

**关键章节**：
- **Section 1 - 设计要点与约定**
  - 1.1节：数据库设计规范（UUID生成、时间戳、外键、注释）
  - 1.2节：API设计规范（HTTP方法、路径设计、认证要求）
  - 1.3节：软删除策略

- **Section 2 - 数据库Schema（DDL）**
  - 所有表结构定义（tags, categories, brands, experts, session_tags等）
  - 字段类型、约束、索引、注释

- **Section 3 - Pydantic Schemas**
  - 请求体（Request Schemas）
  - 响应体（Response Schemas）

- **Section 4 - API接口设计**
  - 所有API端点定义（路径、方法、参数、返回值、执行流程）
  - 统一响应结构、分页格式、认证规范、业务状态码

### 3.2 项目技术栈

- **基础框架**：uni-app (Vue 3 + Composition API + TypeScript)
- **状态管理**：Pinia
- **UI组件库**：uView Plus / NutUI / Vant（按需引入）
- **网络请求**：基于uni.request二次封装（已完成，src/utils/request.ts）
- **日志系统**：已完成（src/logs/logger.ts, logUtils.ts, logConfig.ts）
- **安全模块**：已完成（src/utils/security.ts）

### 3.3 后端技术栈（供参考）

- **后端框架**：FastAPI (Python)
- **数据库**：PostgreSQL
- **认证方式**：JWT Token（存储于users.public_id）
- **响应格式**：统一JSON响应（code, message, data, timestamp）

---

## 第4章：全局强制性约束（Global Constraints）

### 4.1 功能完整性原则

❌ **禁止仅生成静态骨架**  
✅ **必须生成功能完整的代码**

- 所有API函数必须能实际调用，不能只是空壳
- 所有类型定义必须与后端文档100%一致
- 所有工具函数必须有完整实现

### 4.2 零偏差原则

所有数据结构、API接口、字段命名必须与后端文档**完全一致**：

- **字段名**：snake_case（与数据库一致），如`user_id`, `created_at`
- **URL路径**：与后端Section 4完全一致，如`/api/v1/brands/{brand_id}`
- **HTTP方法**：与后端一致（GET/POST/PATCH/DELETE）
- **返回值结构**：与后端Pydantic Schemas一致

### 4.3 增量开发安全原则

⚠️ **这是增量开发项目，必须严格遵守以下规则**：

#### 4.3.1 不覆盖原则

- ❌ **禁止**覆盖整个文件
- ✅ **必须**使用`multi_edit`工具补充字段
- ✅ **保留**现有所有字段和实现

#### 4.3.2 冲突检测原则

在修改文件前，必须：
1. 读取现有文件内容
2. 分析现有字段和实现
3. 确定需要添加的内容
4. 使用multi_edit在合适位置添加

#### 4.3.3 导入语句原则

- 检查是否已有相同导入
- 避免重复导入
- 避免循环依赖

### 4.4 TypeScript严格模式

#### 4.4.1 禁止使用any

```typescript
// ❌ 错误
export const getRoomList = (params: any): Promise<any> => { ... }

// ✅ 正确
export const getRoomList = (
  params: { page?: number; size?: number; category_id?: string }
): Promise<PaginatedResponse<Room>> => { ... }
```

#### 4.4.2 null和undefined明确声明

```typescript
// ❌ 错误：未处理null情况
export interface Room {
  user_id: string;  // 实际数据库允许NULL
}

// ✅ 正确：明确标注可为null
export interface Room {
  user_id: string | null;  // 数据库字段：user_id UUID NULL
}

// ✅ 可选字段使用 ?:
export interface Room {
  description?: string;      // 前端可选传递
  user_id: string | null;    // 数据库可为NULL
}
```

#### 4.4.3 泛型必须有约束或默认值

```typescript
// ✅ 正确
export interface PaginatedResponse<T = any> {
  total: number;
  page: number;
  size: number;
  items: T[];
}
```

### 4.5 移动端uni-app特殊要求

#### 4.5.1 uni-app API调用

```typescript
// ✅ 使用uni-app全局API（非导入）
uni.request({...})         // 网络请求
uni.getStorage({...})      // 本地存储
uni.showToast({...})       // 消息提示
uni.navigateTo({...})      // 页面导航
```

#### 4.5.2 条件编译

```typescript
// 不同平台的特殊处理
// #ifdef H5
if (typeof document !== 'undefined') {
  // H5特有逻辑
}
// #endif

// #ifdef APP-PLUS
// App特有逻辑
// #endif
```

#### 4.5.3 性能优化要求

- 使用防抖节流优化频繁操作
- 图片懒加载
- 列表虚拟滚动（长列表）
- 网络状态检测

### 4.6 安全规范

#### 4.6.1 敏感信息脱敏

所有敏感信息必须脱敏后才能存储或上报：

| 信息类型 | 脱敏规则 | 工具函数 |
|---------|---------|---------|
| 手机号 | 保留前3后4位 | `maskPhone()` |
| 身份证 | 保留前3后4位 | `maskIdCard()` |
| 邮箱 | 保留前2位@后全部 | `maskEmail()` |
| Token | 完全隐藏 | `maskToken()` |
**工具位置**：`src/utils/security.ts`（零阶段已完成）

#### 4.6.2 XSS防护

- 禁止使用`v-html`渲染用户输入
- 使用Vue插值`{{ }}`自动转义
- URL跳转前校验合法性

---

### 4.7 导入路径统一规范（强制）

#### 4.7.1 强制使用@别名

**核心规则**：所有导入路径必须使用`@/`别名，禁止使用相对路径。

**标准格式**：
```typescript
// ✅ 正确：使用@别名
import type { Brand } from '@/types/brand';
import { get, post } from '@/utils/request';
import { logger } from '@/logs/logger';
import AppButton from '@/components/common/AppButton.vue';

// ❌ 错误：使用相对路径
import type { Brand } from '../types/brand';
import { get, post } from '../../utils/request';
```

**文件扩展名规范**：

| 文件类型 | 是否需要扩展名 | 示例 |
|---------|--------------|------|
| TypeScript类型/接口 | ❌ 不需要 | `from '@/types/brand'` |
| TypeScript函数 | ❌ 不需要 | `from '@/api/brand'` |
| Vue组件 | ✅ 需要.vue | `from '@/components/common/AppButton.vue'` |

**检查命令**（生成后执行）：
```bash
grep -r "from '\.\.\/" src/types/
grep -r "from '\.\.\/" src/api/
# 不应有任何输出
```

---

### 4.8 文件修改顺序规范

#### 4.8.1 顺序执行原则

**规则**：一次只完整处理一个文件，处理完毕后再处理下一个。

**正确流程**：
```
read(file1) → edit(file1) → verify(file1) → 完成
                                             ↓
                            read(file2) → edit(file2) → verify(file2) → 完成
```

**禁止流程**：
```
read(file1) → read(file2) → edit(file1) → edit(file2)
            ↑ 问题：两个old_string都基于初始读取，中间状态变化会导致失败
```

#### 4.8.2 一次性完成原则

对同一个接口/函数的修改，应该一次性添加所有新内容，避免多次修改。

```typescript
// ❌ 不好：分两次修改同一接口
edit1: 添加user_id字段
edit2: 添加category_id字段

// ✅ 好：一次性添加所有字段
edit: 同时添加user_id和category_id
```

---

### 4.9 代码定位规范

#### 4.9.1 禁止使用行号定位

**强制规则**：不要使用"第X行"来定位代码，使用内容搜索。

❌ **错误做法**：
```
在第9行找到ApiResponse
修改第15-20行的内容
```

✅ **正确做法**：
```bash
# 使用grep_search查找
grep_search('export interface ApiResponse', 'src/')

# 使用内容匹配
multi_edit({
  old_string: 'export interface ApiResponse<T> { ... }',  # 内容定位
  new_string: '...'
})
```

**原因**：
1. 行号会变化（添加import、注释后行号改变）
2. 不同文件结构不同（行号不可复用）
3. 内容匹配更可靠（精确匹配，不受位置影响）

---

## 第5章：阶段一文件清单与生成指令（File List & Generation Instructions）

### 5.1 明确需要生成的文件

根据前置检查结果，本次任务需要完成以下文件：

#### **P0级任务（必须完成）** ⚠️

| 序号 | 文件路径 | 操作类型 | 说明 |
|-----|---------|---------|------|
| 1 | `src/types/common.ts` | ✨ **新建** | 通用类型定义 |
| 2 | `src/types/room.ts` | 🔧 **补充** | 添加user_id, category_id字段 |
| 3 | `src/types/session.ts` | 🔧 **补充** | 添加summary, featured_expert_id字段 |
| 4 | `src/utils/storage.ts` | ✨ **新建** | 本地存储封装 |
| 5 | `src/types/enums.ts` | ✨ **新建** | 业务枚举定义 |

#### **P1级任务（重要）** 📋

**类型定义文件（6个）：**

| 序号 | 文件路径 | 操作类型 | 说明 |
|-----|---------|---------|------|
| 6 | `src/types/brand.ts` | ✨ **新建** | 品牌类型 |
| 7 | `src/types/expert.ts` | ✨ **新建** | 专家类型 |
| 8 | `src/types/category.ts` | ✨ **新建** | 分类类型 |
| 9 | `src/types/tag.ts` | ✨ **新建** | 标签类型 |
| 10 | `src/types/favorite.ts` | ✨ **新建** | 收藏类型 |
| 11 | `src/types/subscription.ts` | ✨ **新建** | 订阅类型 |

**API封装文件（6个）：**

| 序号 | 文件路径 | 操作类型 | 说明 |
|-----|---------|---------|------|
| 12 | `src/api/brand.ts` | ✨ **新建** | 品牌API |
| 13 | `src/api/expert.ts` | ✨ **新建** | 专家API |
| 14 | `src/api/category.ts` | ✨ **新建** | 分类API |
| 15 | `src/api/tag.ts` | ✨ **新建** | 标签API |
| 16 | `src/api/favorite.ts` | ✨ **新建** | 收藏API |
| 17 | `src/api/subscription.ts` | ✨ **新建** | 订阅API |

**总计：17个文件（5个P0 + 12个P1）**

---

## 第6章：分步生成与验证流程（Step-by-Step Generation & Validation）

### 6.1 执行原则

⚠️ **按照以下顺序严格执行，每完成一个步骤后，进行验证检查！**

---

### 步骤1：生成通用类型定义（P0 - 最高优先级）

**📁 文件：`src/types/common.ts`**

**目标**：定义所有API共用的通用类型，并统一现有的重复定义

**⚠️ 冲突检测与处理（必须先执行，使用grep_search查找）**：

---

#### 检测步骤1：检查`ApiResponse`是否已存在

**执行搜索**：
```bash
grep_search('export interface ApiResponse', 'src/api/')
grep_search('export type ApiResponse', 'src/api/')
```

**判断逻辑**：
- 有输出 → `ApiResponse`已存在，记录位置和定义
- 无输出 → `ApiResponse`不存在，可以在common.ts中创建

**如果存在，必须输出**：
```
ApiResponse检查结果：
- 状态：已存在
- 位置：src/api/session.ts
- 操作：需要统一到common.ts
```

---

#### 检测步骤2：检查`PaginatedResponse`是否已存在

**执行搜索**：
```bash
grep_search('export interface PaginatedResponse', 'src/api/')
grep_search('export type PaginatedResponse', 'src/api/')
```

**判断逻辑**：同上

---

#### 检测步骤3：统一策略

如果检测到`ApiResponse`或`PaginatedResponse`已存在：

**步骤A**：读取现有定义
```bash
read_file('src/api/session.ts')  # 或grep_search找到的文件
```

**步骤B**：在`common.ts`中创建标准版本（保持字段一致）

**步骤C**：更新原文件的导入
- 使用`multi_edit`删除局部定义
- 添加`import { ApiResponse, PaginatedResponse } from '@/types/common';`

**必须包含的接口**：
- `ApiResponse<T>` - 统一API响应结构（code, message, data, timestamp）
- `PaginatedResponse<T>` - 分页响应结构（total, page, size, items）
- `ApiError` - API错误响应
- `QueryParams` - 查询参数基类（page?, size?）
- `SearchableQueryParams` - 可搜索查询参数（extends QueryParams + search?）
- `SortableQueryParams` - 可排序查询参数（extends QueryParams + order_by?, order?）

**技术要求**：
- ✅ 所有泛型必须有默认值（`<T = any>`）
- ✅ 字段类型严格，禁止any（除泛型默认值）
- ✅ 完整的JSDoc注释，标注"阶段一新建"
- ✅ 字段名使用snake_case（与后端一致）

**生成后的统一操作**：

1. **更新`src/api/session.ts`**：
   ```typescript
   // 删除局部ApiResponse定义
   // 添加导入：
   import { ApiResponse, PaginatedResponse } from '@/types/common'; // 或相对路径
   ```

2. **更新`src/api/room.ts`**：
   ```typescript
   // 删除局部PaginatedResponse定义
   // 添加导入：
   import { PaginatedResponse } from '@/types/common'; // 或相对路径
   ```

**验证点**：
- [ ] 是否定义了`ApiResponse<T>`接口（包含code, message, data, timestamp）？
- [ ] 是否定义了`PaginatedResponse<T>`接口（包含total, page, size, items）？
- [ ] 是否定义了`ApiError`接口？
- [ ] 是否定义了查询参数系列接口？
- [ ] 所有泛型是否有默认值？
- [ ] 是否更新了`room.ts`和`session.ts`的导入语句？
- [ ] 是否删除了`room.ts`和`session.ts`中的重复定义？

---

### 步骤2：补充现有类型定义（P0 - 使用multi_edit)

**📁 文件1：`src/types/room.ts`**

**目标**：在现有Room接口中添加缺失字段

---

#### multi_edit精确流程（5步法，强制执行）

**第1步：读取原始文件**

```bash
read_file('src/types/room.ts')
```

**关键点**:
- ✅ 完整读取文件内容
- ✅ 注意输出中的行号前缀（如`1→`, `2→`）不是文件内容
- ✅ 从代码的第一个字符开始才是真实内容

---

**第2步：定位目标接口**

```bash
grep_search('export interface Room', 'src/types/room.ts')
```

**目的**：确认接口存在，避免误操作

---

**第3步：构造old_string（逐字复制）**

**规则**:
1. 复制第1步read_file输出的**完整接口**
2. 从`export interface Room {`开始
3. 到闭合的`}`结束
4. **去掉行号前缀**（如`5→`, `6→`)
5. **保持原文的缩进**（Tab或空格，完全一致）

**示例**：

如果read_file输出：
```
     5→export interface Room {
     6→  id: string;
     7→  title: string;
     8→}
```

则old_string是（去掉`5→`, `6→`等）：
```typescript
export interface Room {
  id: string;
  title: string;
}
```

⚠️ **不要手动输入，直接复制read_file的输出**

---

**第4步：构造new_string（一次性添加所有新字段）**

**规则**:
1. 完整复制old_string
2. 在接口末尾（闭合`}`之前）一次性添加所有新字段
3. 保持缩进一致
4. 字段对齐

**新增字段**（基于后端文档Section 2.1 live_rooms表）：
```typescript
user_id: string | null;        // 用户公开ID，关联users.public_id
category_id: string | null;    // 分类ID，关联categories.id
category_name?: string;        // 前端展示字段：分类名称
user_name?: string;            // 前端展示字段：用户名
```

---

**第5步：执行并验证**

**执行**:
```typescript
multi_edit({
  file_path: 'src/types/room.ts',
  old_string: '【第3步的完整内容】',
  new_string: '【第4步的新内容】'
})
```

**立即验证**:
```bash
read_file('src/types/room.ts')
grep_search('user_id', 'src/types/room.ts')
grep_search('category_id', 'src/types/room.ts')
```

**输出验证结果**:
```
✅ 修改成功：
- user_id已添加
- category_id已添加
- 原有字段完整保留
```

---

**📁 文件2：`src/types/session.ts`**

**目标**：在现有Session接口中添加缺失字段

**操作方式**：❗ **必须使用`multi_edit`工具**

**目标**：在现有Session接口中添加缺失字段

**现有字段（保留全部11个）**：
- id, room_id, status, start_time, end_time, video_id, playback_url
- created_at, updated_at, statistics, room_title

**需要添加的字段**（基于后端文档Section 2.2）：
```typescript
// 新增字段（阶段一补充 - 后端文档Section 2.2 live_sessions表）
summary: string | null;            // 场次总结/摘要
featured_expert_id: string | null; // 特邀专家ID，关联experts.id

// 前端展示字段（非数据库字段，可选）
expert_name?: string;              // 专家姓名
expert_avatar?: string;            // 专家头像
expert_title?: string;             // 专家职称
```

**验证点**：
- [ ] 是否保留了所有现有11个字段？
- [ ] 是否添加了summary和featured_expert_id？
- [ ] 是否使用了`| null`明确声明？

---

### 步骤3：生成零阶段遗留工具（P0）

**📁 文件1：`src/utils/storage.ts`**

**目标**：封装uni-app的本地存储API，集成日志和安全脱敏

**必须实现的4个函数**：
```typescript
getStorage<T>(key: string): Promise<T | null>     // 获取
setStorage<T>(key: string, value: T): Promise<void>  // 设置
removeStorage(key: string): Promise<void>          // 删除
clearStorage(): Promise<void>                      // 清空
```

**导入依赖**（根据步骤0.1的配置）：
```typescript
// 如果有@别名配置：
import { logger } from '@/logs/logger';
import { autoDesensitize } from '@/utils/security';

// 如果没有@别名配置：
import { logger } from '../logs/logger';
import { autoDesensitize } from './security';
```

**错误处理统一模式**（必须遵循）：
```typescript
/**
 * 获取本地存储数据
 * @param key 存储键名
 * @returns Promise<T | null> 存储的数据，失败返回null
 * @example
 * const userInfo = await getStorage<User>('userInfo');
 */
export const getStorage = async <T = any>(key: string): Promise<T | null> => {
  try {
    const result = await new Promise<T>((resolve, reject) => {
      uni.getStorage({
        key,
        success: (res) => {
          logger.info('读取存储成功', { key });
          resolve(res.data as T);
        },
        fail: reject,
      });
    });
    return result;
  } catch (error) {
    logger.error('读取存储失败', { key, error });
    // 不抛出异常，返回null，避免中断业务流程
    return null;
  }
};

/**
 * 设置本地存储数据
 * @param key 存储键名
 * @param value 要存储的数据
 * @example
 * await setStorage('userInfo', { name: '张三', phone: '13800138000' });
 */
export const setStorage = async <T = any>(key: string, value: T): Promise<void> => {
  try {
    // 自动脱敏敏感数据后记录日志
    logger.info('设置存储', { key, value: autoDesensitize(value) });
    
    await new Promise<void>((resolve, reject) => {
      uni.setStorage({
        key,
        data: value,
        success: () => resolve(),
        fail: reject,
      });
    });
  } catch (error) {
    logger.error('设置存储失败', { key, error });
    throw error; // 抛出异常，让调用方处理
  }
};
```

**技术要求**：
- 使用Promise封装uni-app回调API（async/await模式）
- 集成logger记录所有操作（info、error级别）
- 自动脱敏敏感数据（调用`autoDesensitize`）
- 完整的错误处理（getStorage返回null，setStorage抛出异常）
- 完整的JSDoc注释（含@param, @returns, @example）

**验证点**：
- 是否实现了4个函数？
- 是否使用了Promise封装？
- 是否集成了logger？
- 是否集成了安全脱敏？
- 是否遵循统一的错误处理模式？
- 是否有完整的JSDoc注释？

---

**📁 文件2：`src/common/enums.ts`**

**目标**：集中管理所有业务枚举

**重要说明**：
- `SessionStatus`已在`src/types/session.ts`中定义为`export type SessionStatus = 'scheduled' | 'live' | 'ended' | 'archived'`
- 不要重复定义，保留现有类型定义
- 如果其他文件需要使用，从`session.ts`导入

**必须包含的3个枚举**：
```typescript
UserRole           // 用户角色：GUEST, USER, ADMIN, SUPERADMIN
FavoriteType       // 收藏类型：ROOM, SESSION, EXPERT
SubscriptionType   // 订阅类型：ROOM, EXPERT, CATEGORY
```

**必须包含的中文映射**：
```typescript
// SessionStatus使用现有定义，只提供映射
export const SessionStatusLabel: Record<string, string> = {
  'scheduled': '未开始',
  'live': '直播中',
  'ended': '已结束',
  'archived': '已归档',
};

export const UserRoleLabel: Record<UserRole, string> = {
  [UserRole.GUEST]: '访客',
  [UserRole.USER]: '普通用户',
  [UserRole.ADMIN]: '管理员',
  [UserRole.SUPERADMIN]: '超级管理员',
};

export const FavoriteTypeLabel: Record<FavoriteType, string> = {
  [FavoriteType.ROOM]: '房间',
  [FavoriteType.SESSION]: '场次',
  [FavoriteType.EXPERT]: '专家',
};

export const SubscriptionTypeLabel: Record<SubscriptionType, string> = {
  [SubscriptionType.ROOM]: '房间订阅',
  [SubscriptionType.EXPERT]: '专家订阅',
  [SubscriptionType.CATEGORY]: '分类订阅',
};
```

**验证点**：
- [ ] 是否定义了3个枚举（不包括SessionStatus）？
- [ ] 是否提供了4个中文映射（包括SessionStatus）？
- [ ] 是否避免了与session.ts的SessionStatus冲突？

---

### 步骤4：生成后端新增模块类型（P1）

按以下顺序依次生成6个类型文件，每个文件必须包含：主接口、CreatePayload、UpdatePayload

**📁 文件1：`src/types/brand.ts`**

**数据来源**：后端文档Section 2.3 brands表 + Section 2.4 brand_topics表

**必须包含**：
- `Brand` 接口（品牌信息，包含所有数据库字段）
- `BrandCreatePayload` 接口（创建请求体）
- `BrandUpdatePayload` 接口（更新请求体）
- `BrandTopic` 接口（品牌-专题关联）

**验证点**：
- [ ] 字段是否与后端文档100%一致？
- [ ] 是否明确标注了`| null`？
- [ ] 是否有完整的JSDoc注释？

---

**📁 文件2-6：依次生成**
- `src/types/expert.ts` - 专家类型（Section 2.5 experts表）
- `src/types/category.ts` - 分类类型（Section 2.2 categories表）
- `src/types/tag.ts` - 标签类型（Section 2.1 tags + Section 2.6 session_tags）
- `src/types/favorite.ts` - 收藏类型（Section 2.7 user_favorites表）
- `src/types/subscription.ts` - 订阅类型（Section 2.8 user_subscriptions表）

**共同技术要求**：
- ✅ 字段名与数据库表完全一致（snake_case）
- ✅ 时间字段统一使用`string`类型（ISO 8601格式）
- ✅ UUID字段统一使用`string`类型
- ✅ 可选字段使用`| null`或`?:`明确区分
- ✅ 完整的JSDoc注释，标注字段来源

---

### 步骤5：生成后端新增模块API（P1）

按以下顺序依次生成6个API文件，每个文件必须包含CRUD函数

**📁 文件1：`src/api/brand.ts`**

**数据来源**：后端文档Section 4对应API接口

**必须实现的6个函数**：
```typescript
getBrandList(params): Promise<PaginatedResponse<Brand>>    // 分页列表
getBrandDetail(brandId): Promise<Brand>                    // 详情
createBrand(data): Promise<Brand>                          // 创建
updateBrand(brandId, data): Promise<Brand>                 // 更新
deleteBrand(brandId): Promise<void>                        // 删除
getBrandTopics(brandId): Promise<BrandTopic[]>             // 品牌专题
```

**⚠️ API路径规范（重要）**：

所有API路径使用**相对路径**，`request.ts`会自动拼接`BASE_URL`：

**✅ 正确示例**：
```typescript
// 后端文档路径：/api/v1/brands
// 前端调用路径：/brands （不要包含/api/v1前缀）
export const getBrandList = (params: QueryParams) => {
  return get<PaginatedResponse<Brand>>('/brands', params);
  // 实际请求：BASE_URL + '/brands' = http://xxx/api/v1/brands
};

export const getBrandDetail = (brandId: string) => {
  return get<Brand>(`/brands/${brandId}`);
  // 实际请求：BASE_URL + '/brands/{id}'
};
```

**❌ 错误示例**：
```typescript
// ❌ 不要包含完整路径
return get('/api/v1/brands', params);

// ❌ 不要重复BASE_URL
return get('http://localhost:8000/api/v1/brands', params);
```

**路径复制规则**：
- 从后端文档Section 4中复制API路径
- 去掉`/api/v1`前缀
- 保留剩余路径部分
- 例如：`/api/v1/brands/{id}` → `/brands/{id}`

**技术要求**：
- ✅ 从`@/utils/request`导入`get, post, patch, del`（根据步骤0.1配置）
- ✅ 从`@/types/brand`导入类型
- ✅ 从`@/types/common`导入`PaginatedResponse`
- ✅ URL路径：完全复制后端文档路径格式（去掉/api/v1前缀）
- ✅ HTTP方法一致（GET/POST/**PATCH**/DELETE）
- ✅ 需认证接口传递`{ auth: true }`
- ✅ 完整的JSDoc注释（含@param, @returns, @example）

**验证点**：
- [ ] 是否实现了所有函数？
- [ ] URL路径是否与后端文档一致？
- [ ] HTTP方法是否正确（PATCH不是PUT）？
- [ ] 是否传递了auth选项？
- [ ] 是否有JSDoc注释和示例？

---

**📁 文件2-6：依次生成**
- `src/api/expert.ts` - 专家API（CRUD 5个函数）
- `src/api/category.ts` - 分类API（CRUD 5个函数）
- `src/api/tag.ts` - 标签API（CRUD + Session Tag关联函数）
- `src/api/favorite.ts` - 收藏API（CRUD + `checkFavorite`函数）
- `src/api/subscription.ts` - 订阅API（CRUD 5个函数）

**共同技术要求**：
- ✅ 所有函数参数和返回值必须使用对应的TypeScript类型
- ✅ 需要认证的接口必须传递`{ auth: true }`选项
- ✅ 函数命名清晰（如：getBrandList, createExpert）
- ✅ 完整的JSDoc注释
- ✅ URL路径与后端文档完全一致
- ✅ HTTP方法与后端文档一致

**统一错误处理模式**（所有API函数）：
```typescript
/**
 * 获取品牌列表
 * @param params 查询参数
 * @returns Promise<PaginatedResponse<Brand>>
 * @example
 * const brands = await getBrandList({ page: 1, size: 20 });
 */
export const getBrandList = (params?: QueryParams): Promise<PaginatedResponse<Brand>> => {
  // ✅ 错误由request.ts统一处理（日志记录、toast提示）
  return get<PaginatedResponse<Brand>>('/brands', params);
};

/**
 * 创建品牌
 * @param data 品牌创建数据
 * @returns Promise<Brand>
 * @example
 * const newBrand = await createBrand({ name: '测试品牌', description: '描述' });
 */
export const createBrand = (data: BrandCreatePayload): Promise<Brand> => {
  // ✅ 需要认证的接口传递{ auth: true }
  return post<Brand>('/brands', data, { auth: true });
};

**1. 导入检查**：
- [ ] 所有import语句正确
- [ ] 无循环依赖
- [ ] 使用@别名（@/types, @/api, @/utils）
- [ ] 添加了包来源注释

**2. 类型检查**：
- [ ] 无any类型（除泛型默认值）
- [ ] null和undefined明确声明
- [ ] 字段名使用snake_case（与后端一致）
- [ ] 泛型有约束或默认值

**3. 功能检查**：
- [ ] API函数能实际调用（不是空壳）
- [ ] 工具函数有完整实现
- [ ] 与后端文档100%一致

**4. 文档检查**：
- [ ] 所有函数有JSDoc注释
- [ ] 关键代码有注释说明
- [ ] 标注了包来源和字段来源

---

## 第7章：最终交付与验收标准（Final Delivery & Acceptance Criteria）

### 7.1 完整性检查清单

生成完所有代码后，进行最终检查：

#### P0级任务检查（必须100%完成）

- [ ] **通用类型完整**（src/types/common.ts）
  - [ ] PaginatedResponse<T>定义
  - [ ] ApiResponse<T>定义  
  - [ ] ApiError定义
  - [ ] QueryParams系列定义

- [ ] **现有类型已补充**
  - [ ] src/types/room.ts添加了user_id, category_id
  - [ ] src/types/session.ts添加了summary, featured_expert_id
  - [ ] 使用multi_edit，保留了所有现有字段

- [ ] **零阶段遗留工具完成**
  - [ ] src/utils/storage.ts（4个函数：get, set, remove, clear）
  - [ ] src/common/enums.ts（SessionStatus, UserRole, FavoriteType, SubscriptionType）

#### P1级任务检查（重要）

- [ ] **后端新增模块类型完整**（至少6个）
  - [ ] src/types/brand.ts (Brand, BrandCreatePayload, BrandUpdatePayload, BrandTopic)
  - [ ] src/types/expert.ts (Expert, ExpertCreatePayload, ExpertUpdatePayload)
  - [ ] src/types/category.ts (Category, CategoryCreatePayload, CategoryUpdatePayload)
  - [ ] src/types/tag.ts (Tag, SessionTag, TagCreatePayload)
  - [ ] src/types/favorite.ts (Favorite, FavoriteCreatePayload)
  - [ ] src/types/subscription.ts (Subscription, SubscriptionCreatePayload)

- [ ] **后端新增模块API完整**（至少6个）
  - [ ] src/api/brand.ts (CRUD + getBrandTopics)
  - [ ] src/api/expert.ts (CRUD)
  - [ ] src/api/category.ts (CRUD)
  - [ ] src/api/tag.ts (CRUD + Session Tag关联)
  - [ ] src/api/favorite.ts (CRUD + checkFavorite)
  - [ ] src/api/subscription.ts (CRUD)

### 7.2 质量保证检查

- [ ] **所有导入语句正确**
  - 无循环依赖
  - 无重复导入
  - 使用@别名（@/types, @/api, @/utils等)
  - 添加包来源注释

- [ ] **所有类型严格**
  - 无any类型
  - null和undefined明确声明
  - 泛型有约束或默认值
  - 字段名使用snake_case（与后端一致）

- [ ] **所有API与后端文档一致**
  - URL路径100%匹配
  - HTTP方法一致（GET/POST/PATCH/DELETE）
  - 参数结构一致
  - 返回值结构一致
  - 认证接口传递{ auth: true }

- [ ] **所有代码符合规范**
  - TypeScript严格模式
  - uni-app API正确使用
  - 集成日志系统（logger）
  - 集成安全模块（脱敏）
  - 完整的JSDoc注释

### 7.3 最终断言

生成完所有代码后，输出以下断言声明：

```
[PHASE 1 ASSERTION - MOBILE INCREMENTAL DEVELOPMENT]

✅ All generated code has been validated against existing codebase.

Validation Results:
- Conflict Detection: 100% ✅
- Type Safety (No any): 100% ✅  
- API Consistency (Backend Doc Match): 100% ✅
- Incremental Development Safety: Adhered ✅
- Zero Overwrite Principle: Adhered ✅
- Import Dependency Check: Passed ✅
- Mobile uni-app Compatibility: Verified ✅

Generated Files Summary:
- P0 Tasks: [X] files (common.ts, storage.ts, enums.ts + 补充room/session)
- P1 Tasks: [X] files (types: brand/expert/category/tag/favorite/subscription, apis: 同名6个)
- Total Lines of Code: [估算总行数]

All code is production-ready and can be directly integrated into the project.
阶段一数据契约与API层代码生成完成！✅
```

---

## 🎯 执行指令（Execution Instructions）

**AI，现在请严格按照以上提示词执行代码生成：

### 执行流程

1. **第0章**：执行强制性前置检查
   - 读取所有现有核心文件
   - 扫描types/api/utils/store目录
   - 生成详细的项目现状分析报告

2. **等待用户确认**
   - 展示分析报告
   - 等待用户输入"确认继续"

3. **按优先级生成代码**
   - P0任务：common.ts → 补充room/session → storage.ts → enums.ts
   - P1任务：依次生成brand/expert/category/tag/favorite/subscription的types和apis

4. **最终质量检查**
   - 执行完整性检查清单
   - 执行质量保证检查
   - 输出最终断言

### 关键提醒

⚠️ **这是增量开发项目，安全第一！
- 不覆盖现有代码
- 使用multi_edit补充字段
- 保留所有现有实现
- 检查循环依赖

✅ **代码质量要求
- TypeScript严格模式
- 与后端文档100%一致
- 完整的JSDoc注释
- 集成日志和安全模块

---
**[阶段一代码生成提示词文档 - 完成]**