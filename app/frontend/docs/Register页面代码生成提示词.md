# 注册页面代码生成提示词 (uni-app移动端版)

**版本**: V1.0  
**创建日期**: 2026-03-12  
**适用项目**: 医学直播SaaS平台移动端  
**技术栈**: uni-app + Vue3 + TypeScript + Pinia

---

## ⚠️ 重要声明

**本提示词用于生成注册页面功能，必须与登录页面保持API调用方式的完全一致性。**

- ✅ **技术栈**: uni-app + Vue3 Composition API + TypeScript
- ✅ **设计风格**: Consumer模式（B站/抖音简约风格）
- ✅ **API一致性**: 使用与登录页相同的`authUrl()`函数和请求方式
- ✅ **自动登录**: 注册成功后使用`authStore.login()`自动登录
- ✅ **响应式设计**: Mobile/Tablet/Desktop三种断点适配

---

## 🏗️ 架构基础（必读）

**在开始开发前，你必须先阅读以下文档：**

📖 **设计文档**：
- `docs/注册页面功能设计与实现文档.md`（完整功能设计）
- `docs/登录与跨应用跳转设计文档.md`（统一设计语言规范）
- `docs/用户模块设计文档authing版+权限设计版.md`（后端API文档）

📋 **已实现参考**：
- `src/pages/app/auth/login.vue`（登录页面实现，API调用方式必须保持一致）
- `src/api/auth.ts`（认证API封装）
- `src/store/auth.ts`（认证状态管理）

---

## 第0章：强制性前置检查 ⚡（必须先执行）

### 0.1 检查目的

在生成任何代码之前，必须全面了解项目现状，确保：
- ✅ 与登录页面API调用方式完全一致
- ✅ 复用现有的API封装和认证逻辑
- ✅ 理解现有的表单验证工具函数
- ✅ 遵循统一的设计语言规范

### 0.2 必须执行的检查步骤

#### 步骤1：读取现有核心文件（强制）

你必须先读取以下文件，了解现有实现：

```bash
必须读取的文件清单：
✅ src/pages/app/auth/login.vue - 登录页面实现（API调用方式参考）
✅ src/api/auth.ts - 认证API封装（getCaptcha、login，检查registerUser是否存在）
✅ src/store/auth.ts - 认证状态管理（authStore.login方法完整实现）
✅ src/constants/api.ts - API常量定义（AUTH_API_URL）
✅ src/utils/request.ts - 统一请求封装（get、post方法）
✅ src/types/auth.ts - 认证类型定义（检查RegisterRequest等是否存在）
⚠️ src/utils/validate.ts - 表单校验工具（检查是否存在，可能需新建）
⚠️ src/utils/password.ts - 密码强度计算工具（检查是否存在，可能需新建）
✅ src/static/fonts/iconfont.css - 可用图标列表
```

**执行命令**：使用 `read_file` 工具逐个读取以上文件。

**重点检查项**：
- [ ] `src/api/auth.ts` 中是否存在 `registerUser()` 函数
- [ ] `src/types/auth.ts` 中是否存在以下类型：
  - RegisterRequest
  - RegisterResponse 
  - RegisterForm
  - PasswordStrength
  - PasswordStrengthLevel
- [ ] `src/utils/validate.ts` 是否存在（validateUsername、validateEmail、validatePassword函数）
- [ ] `src/utils/password.ts` 是否存在（calculatePasswordStrengthLevel函数）

#### 步骤2：扫描目录结构（强制）

```bash
必须扫描的目录：
✅ src/pages/app/auth/ - 确认认证页面目录结构
✅ src/api/ - 确认auth.ts是否存在
✅ src/store/ - 确认auth.ts是否存在
✅ src/utils/ - 确认validate.ts、password.ts是否存在
```

#### 步骤3：在聊天窗口输出项目现状分析（强制）

**重要**：❗ 不要生成单独的分析报告文件，直接在聊天窗口中展示分析结果！

---

**📊 注册页面开发现状分析**

**一、已存在且可直接复用的文件（✅ 直接使用）**
- 列出所有可复用的API、Store、工具函数
- 注明文件路径、核心功能
- 确认API调用方式与登录页一致

**二、已存在但需要扩展的文件（🔧 需要补充）**
- `src/api/auth.ts`：检查是否缺少 `registerUser()` 函数
- `src/types/auth.ts`：检查是否缺少以下类型定义：
  - RegisterRequest（注册请求参数）
  - RegisterResponse（注册响应数据）
  - RegisterForm（注册表单数据）
  - PasswordStrength（密码强度对象）
  - PasswordStrengthLevel（密码强度枚举）
- 工具函数检查：
  - `src/utils/validate.ts`：是否存在 validateUsername、validateEmail、validatePassword
  - `src/utils/password.ts`：是否存在 calculatePasswordStrengthLevel

**三、需要新建的文件（➕ 需新建）**
- 列出需要新建的页面文件
- 列出需要新建的工具类文件

**四、路由配置检查（📍 pages.json）**
- 检查注册页面路由是否已配置
- 确认登录页面是否有跳转到注册的入口

**五、API一致性检查**
- ✅ 确认使用authUrl()函数拼接路径
- ✅ 确认使用相同的get/post方法
- ✅ 确认使用相同的错误处理方式

---

#### 步骤4：等待用户确认（强制）

在聊天窗口输出分析结果后，**必须等待用户确认**才能继续生成代码。

---

## 第0.5章：缺失文件补充方案 🔧（如果检查发现缺失，必须先执行）

### 0.5.1 缺失文件影响评估

如果在第0章检查中发现以下文件缺失，**必须先补充这些文件**，否则注册页面无法正常运行：

| 文件 | 影响程度 | 是否必须 | 说明 |
|------|---------|---------|------|
| `src/api/auth.ts` 中的 `registerUser()` | P0 | ✅ 必须 | 无法调用注册接口 |
| `src/types/auth.ts` 中的5个类型 | P0 | ✅ 必须 | TypeScript编译错误 |
| `src/utils/validate.ts` | P0 | ✅ 必须 | 表单校验无法工作 |
| `src/utils/password.ts` | P0 | ✅ 必须 | 密码强度计算无法工作 |
| `pages.json` 路由配置 | P0 | ✅ 必须 | 无法访问注册页面 |

### 0.5.2 文件补充顺序

按照以下顺序补充文件，避免依赖冲突：

```
1. src/types/auth.ts        （类型定义）
   ↓
2. src/api/auth.ts           （API函数，依赖类型）
   ↓
3. src/utils/validate.ts     （工具函数）
   ↓
4. src/utils/password.ts     （工具函数，依赖类型）
   ↓
5. pages.json                （路由配置）
   ↓
6. src/pages/app/auth/register.vue  （注册页面）
```

---

### 📝 **补充1：src/types/auth.ts - 添加5个类型定义**

在 `src/types/auth.ts` 文件末尾添加以下类型定义：

```typescript
/**
 * 用户注册请求参数
 */
export interface RegisterRequest {
  /** 用户名（2-50字符，字母/数字/下划线） */
  username: string;
  /** 邮箱地址 */
  email: string;
  /** 密码（至少8位，包含大小写字母+数字+特殊字符） */
  password: string;
  /** 昵称（2-50字符） */
  nickname: string;
  /** 验证码ID */
  captcha_id: string;
  /** 验证码答案 */
  captcha_solution: string;
}

/**
 * 用户注册响应
 */
export interface RegisterResponse {
  /** 用户UUID */
  user_id: string;
  /** 用户名 */
  username: string;
  /** 邮箱 */
  email: string;
  /** 昵称 */
  nickname: string;
}

/**
 * 注册表单数据（前端使用）
 */
export interface RegisterForm {
  /** 用户名 */
  username: string;
  /** 邮箱 */
  email: string;
  /** 密码 */
  password: string;
  /** 昵称 */
  nickname: string;
  /** 验证码答案 */
  captcha_solution: string;
}

/**
 * 密码强度级别枚举
 */
export enum PasswordStrengthLevel {
  /** 很弱（红色） */
  VeryWeak = 1,
  /** 弱（橙色） */
  Weak = 2,
  /** 中（黄色） */
  Medium = 3,
  /** 强（浅绿） */
  Strong = 4,
  /** 很强（深绿） */
  VeryStrong = 5
}

/**
 * 密码强度对象
 */
export interface PasswordStrength {
  /** 强度级别 */
  level: PasswordStrengthLevel;
  /** 显示文本 */
  text: string;
  /** 颜色值 */
  color: string;
  /** 分数（0-5） */
  score: number;
}
```

**操作命令**：
```typescript
// 使用 replace_string_in_file 在文件末尾添加
// 找到最后一个interface或export，然后在其后添加
```

---

### 📝 **补充2：src/api/auth.ts - 添加 registerUser() 函数**

在 `src/api/auth.ts` 文件中，找到 `login()` 函数后面，添加：

```typescript
/**
 * 用户注册
 * @param data 注册信息（用户名/邮箱/密码/昵称/验证码）
 * @returns 注册成功的用户信息
 * @example
 * const response = await registerUser({
 *   username: 'newuser',
 *   email: 'user@example.com',
 *   password: 'Test@123',
 *   nickname: '新用户',
 *   captcha_id: 'xxx',
 *   captcha_solution: '1234'
 * });
 * const user = response.data;
 */
export const registerUser = (data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> => {
  return post<ApiResponse<RegisterResponse>>(authUrl('/users/register'), data);
};
```

**插入位置**：在 `login()` 函数之后，`refreshToken()` 函数之前

**注意事项**：
- ⚠️ 确保导入了 `RegisterRequest` 和 `RegisterResponse` 类型
- ⚠️ API路径是 `/users/register`（不是 `/auth/register`）

---

### 📝 **补充3：src/utils/validate.ts - 创建表单校验工具**

创建新文件 `src/utils/validate.ts`：

```typescript
/**
 * 表单校验工具函数
 * 提供用户名、邮箱、密码等常见字段的校验规则
 */

/**
 * 校验用户名格式
 * 规则：2-50字符，仅允许字母、数字、下划线
 * @param username 用户名
 * @returns 是否符合规则
 * @example
 * validateUsername('john_doe123') // true
 * validateUsername('a') // false (太短)
 * validateUsername('user@name') // false (包含特殊字符)
 */
export function validateUsername(username: string): boolean {
  if (!username) return false;
  const regex = /^[a-zA-Z0-9_]{2,50}$/;
  return regex.test(username);
}

/**
 * 校验邮箱格式
 * 规则：标准邮箱格式（xxx@xxx.xxx）
 * @param email 邮箱地址
 * @returns 是否符合规则
 * @example
 * validateEmail('user@example.com') // true
 * validateEmail('invalid-email') // false
 */
export function validateEmail(email: string): boolean {
  if (!email) return false;
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

/**
 * 校验密码强度
 * 规则：至少8位，必须包含大小写字母、数字和特殊字符
 * @param password 密码
 * @returns 是否符合规则
 * @example
 * validatePassword('Test@123') // true
 * validatePassword('test123') // false (缺少大写和特殊字符)
 * validatePassword('Test123') // false (缺少特殊字符)
 */
export function validatePassword(password: string): boolean {
  if (!password || password.length < 8) return false;
  
  // 必须包含大写字母
  const hasUpperCase = /[A-Z]/.test(password);
  // 必须包含小写字母
  const hasLowerCase = /[a-z]/.test(password);
  // 必须包含数字
  const hasNumber = /[0-9]/.test(password);
  // 必须包含特殊字符
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
  
  return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
}

/**
 * 校验手机号格式（中国大陆）
 * 规则：11位数字，1开头
 * @param phone 手机号
 * @returns 是否符合规则
 * @example
 * validatePhone('13812345678') // true
 * validatePhone('12345678901') // false (不是1开头)
 */
export function validatePhone(phone: string): boolean {
  if (!phone) return false;
  const regex = /^1[3-9]\d{9}$/;
  return regex.test(phone);
}

/**
 * 校验昵称长度
 * 规则：2-50字符
 * @param nickname 昵称
 * @returns 是否符合规则
 */
export function validateNickname(nickname: string): boolean {
  if (!nickname) return false;
  return nickname.length >= 2 && nickname.length <= 50;
}
```

**操作命令**：
```typescript
// 使用 create_file 工具创建新文件
```

---

### 📝 **补充4：src/utils/password.ts - 创建密码强度计算工具**

创建新文件 `src/utils/password.ts`：

```typescript
/**
 * 密码强度计算工具
 * 提供密码强度评估和可视化反馈
 */

import type { PasswordStrength, PasswordStrengthLevel } from '@/types/auth';

/**
 * 密码强度级别枚举（与types保持一致）
 */
export const PasswordStrengthEnum = {
  VeryWeak: 1,
  Weak: 2,
  Medium: 3,
  Strong: 4,
  VeryStrong: 5
} as const;

/**
 * 计算密码强度等级
 * 评分规则：
 * - 长度 ≥ 8位：+1分
 * - 长度 ≥ 12位：+1分
 * - 包含大写字母：+1分
 * - 包含小写字母：+1分
 * - 包含数字：+1分
 * - 包含特殊字符：+1分
 * 总分0-5分，对应5个强度等级
 * 
 * @param password 密码字符串
 * @returns 密码强度对象（包含等级、文本、颜色、分数）
 * @example
 * calculatePasswordStrengthLevel('Test@123')
 * // 返回: { level: 4, text: '强', color: '#84CC16', score: 4 }
 */
export function calculatePasswordStrengthLevel(password: string): PasswordStrength {
  let score = 0;
  
  // 1. 长度检查（最多2分）
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  
  // 2. 包含大写字母（1分）
  if (/[A-Z]/.test(password)) score++;
  
  // 3. 包含小写字母（1分）
  if (/[a-z]/.test(password)) score++;
  
  // 4. 包含数字（1分）
  if (/[0-9]/.test(password)) score++;
  
  // 5. 包含特殊字符（1分）
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score++;
  
  // 限制最大分数为5
  score = Math.min(score, 5);
  
  // 根据分数返回强度对象
  const strengthMap: Record<number, PasswordStrength> = {
    0: { 
      level: PasswordStrengthEnum.VeryWeak as PasswordStrengthLevel, 
      text: '密码太短', 
      color: '#EF4444', 
      score: 0 
    },
    1: { 
      level: PasswordStrengthEnum.VeryWeak as PasswordStrengthLevel, 
      text: '很弱', 
      color: '#EF4444', 
      score: 1 
    },
    2: { 
      level: PasswordStrengthEnum.Weak as PasswordStrengthLevel, 
      text: '弱', 
      color: '#F59E0B', 
      score: 2 
    },
    3: { 
      level: PasswordStrengthEnum.Medium as PasswordStrengthLevel, 
      text: '中', 
      color: '#EAB308', 
      score: 3 
    },
    4: { 
      level: PasswordStrengthEnum.Strong as PasswordStrengthLevel, 
      text: '强', 
      color: '#84CC16', 
      score: 4 
    },
    5: { 
      level: PasswordStrengthEnum.VeryStrong as PasswordStrengthLevel, 
      text: '很强', 
      color: '#22C55E', 
      score: 5 
    },
  };
  
  return strengthMap[score];
}

/**
 * 获取密码强度建议
 * @param password 密码字符串
 * @returns 改进建议数组
 * @example
 * getPasswordSuggestions('test123')
 * // 返回: ['添加大写字母', '添加特殊字符', '建议长度达到12位以上']
 */
export function getPasswordSuggestions(password: string): string[] {
  const suggestions: string[] = [];
  
  if (password.length < 8) {
    suggestions.push('密码长度至少8位');
  } else if (password.length < 12) {
    suggestions.push('建议长度达到12位以上');
  }
  
  if (!/[A-Z]/.test(password)) {
    suggestions.push('添加大写字母（A-Z）');
  }
  
  if (!/[a-z]/.test(password)) {
    suggestions.push('添加小写字母（a-z）');
  }
  
  if (!/[0-9]/.test(password)) {
    suggestions.push('添加数字（0-9）');
  }
  
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    suggestions.push('添加特殊字符（!@#$等）');
  }
  
  return suggestions;
}
```

**操作命令**：
```typescript
// 使用 create_file 工具创建新文件
```

---

### 📝 **补充5：pages.json - 添加注册页面路由**

在 `pages.json` 的 `pages` 数组中，找到登录页路由配置附近，添加注册页路由：

```json
{
  "path": "pages/app/auth/register",
  "style": {
    "navigationBarTitleText": "注册账号",
    "navigationStyle": "custom",
    "enablePullDownRefresh": false
  }
}
```

**插入位置**：建议在 `pages/app/auth/login` 之后

**完整示例**：
```json
{
  "pages": [
    // ... 其他页面
    {
      "path": "pages/app/auth/login",
      "style": {
        "navigationBarTitleText": "登录",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/app/auth/register",
      "style": {
        "navigationBarTitleText": "注册账号",
        "navigationStyle": "custom",
        "enablePullDownRefresh": false
      }
    }
    // ... 其他页面
  ]
}
```

---

### 📝 **补充6：src/pages/app/auth/login.vue - 修改"注册账号"按钮**

找到登录页面中的"注册账号"按钮，修改跳转逻辑：

**原代码**：
```vue
<text class="secondary-link" @click="showComingSoon">注册账号</text>
```

**修改为**：
```vue
<text class="secondary-link" @click="handleGoToRegister">注册账号</text>
```

**添加跳转函数**（在 `<script setup>` 中）：
```typescript
/**
 * 跳转到注册页面
 */
function handleGoToRegister(): void {
  uni.navigateTo({
    url: '/pages/app/auth/register'
  });
}
```

---

### 0.5.3 补充完成验证清单

补充所有文件后，执行以下验证：

```bash
验证清单：
✅ src/types/auth.ts - 包含5个新类型定义
✅ src/api/auth.ts - 包含registerUser()函数
✅ src/utils/validate.ts - 文件存在且包含3个校验函数
✅ src/utils/password.ts - 文件存在且包含calculatePasswordStrengthLevel函数
✅ pages.json - 包含注册页面路由配置
✅ src/pages/app/auth/login.vue - "注册账号"按钮已修改
```

**验证方法**：
1. 使用 `read_file` 工具读取每个文件，确认内容正确
2. 使用 TypeScript 编译检查类型错误
3. 确认路由配置格式正确

---

### 0.5.4 补充文件后的下一步

完成所有文件补充后，才能继续生成注册页面（`src/pages/app/auth/register.vue`）。

**流程**：
```
补充支持文件（第0.5章）
    ↓
等待用户确认（第0章步骤4）
    ↓
生成注册页面（第1-8章）
    ↓
测试验证（第6章）
```

---

## 第1章：角色定义（Role Definition）

你是一名**资深移动端前端工程师**，具备以下专业技能：

- **精通技术栈**：uni-app、Vue 3 Composition API、TypeScript、移动端H5开发
- **表单设计**：熟悉复杂表单验证、密码强度校验、验证码处理
- **API集成**：精通RESTful API集成，理解认证流程和Token管理
- **用户体验**：注重表单交互反馈、错误提示、加载状态等细节
- **代码复用**：能够最大化复用现有代码，保持API调用方式的一致性

**你的任务是根据详细设计文档和现有代码基础，编写高质量、功能完整、可直接运行的注册页面代码。**

---

## 第2章：任务目标（Task Objective）

### 2.1 核心目标

开发App端注册页面（`src/pages/app/auth/register.vue`），实现以下功能模块：

1. **表单输入功能**：用户名、邮箱、密码、昵称、验证码输入
2. **实时校验功能**：失去焦点时校验，实时密码强度提示
3. **图形验证码功能**：验证码显示、刷新、输入
4. **注册提交功能**：表单验证、API调用、错误处理
5. **自动登录功能**：注册成功后自动调用登录API并跳转

### 2.2 页面布局设计

```
┌─────────────────────────────────────┐
│  [auth-container]                   │  ← 响应式容器（92vw/420-460px）
│  ← 注册账号                         │  ← 顶部导航栏（auth-top）
├─────────────────────────────────────┤
│  [auth-main]                        │  ← 主内容区（可滚动）
│                                     │
│  [auth-title]                       │  ← 标题区域
│  📱 创建您的账号                     │  ← H1主标题（48rpx/700）
│  快速注册，开启医学直播之旅           │  ← 副标题（28rpx/400）
│                                     │
│  ┌─────────────────────────────┐  │
│  │ 用户名                        │  │  ← 用户名输入框
│  │ [输入框]                      │  │
│  │ 2-50字符，字母/数字/下划线       │  │  ← 输入提示
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │ 邮箱                          │  │  ← 邮箱输入框
│  │ [输入框]                      │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │ 密码                          │  │  ← 密码输入框（带显示/隐藏）
│  │ [输入框] 👁                   │  │
│  │ 密码强度: ●●●○○ 中            │  │  ← 密码强度指示器
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │ 昵称                          │  │  ← 昵称输入框
│  │ [输入框]                      │  │
│  └─────────────────────────────┘  │
│                                     │
│  ┌─────────────────────────────┐  │
│  │ 验证码                        │  │  ← 图形验证码区域
│  │ [输入框]  [图片] 换一张        │  │
│  └─────────────────────────────┘  │
│                                     │
│  [auth-primary]                     │  ← 主操作区
│  ┌─────────────────────────────┐  │
│  │         注 册                │  │  ← 注册按钮（pill样式）
│  └─────────────────────────────┘  │
│                                     │
│  [auth-secondary]                   │  ← 次要操作区
│  已有账号？[立即登录]                │  ← 底部提示
│                                     │
│  [auth-agreement]                   │  ← 协议区（贴底）
│  □ 我已阅读并同意《用户协议》         │  ← checkbox
│                                     │
└─────────────────────────────────────┘
```

### 2.3 开发复用策略

#### 2.3.1 完全复用层（100%复用）
- **API层**：`src/api/auth.ts`（getCaptcha、registerUser、login函数）
- **状态管理**：`src/store/auth.ts`（authStore.login方法）
- **类型定义**：`src/types/auth.ts`（RegisterForm、PasswordStrength等）
- **请求封装**：`src/utils/request.ts`（get、post方法）

#### 2.3.2 部分复用层（可能需要新建）
- **表单校验**：`src/utils/validate.ts`（validateUsername、validateEmail等）
- **密码强度**：`src/utils/password.ts`（calculatePasswordStrengthLevel函数）
- **如果不存在，需要新建这些工具函数**

#### 2.3.3 新建层
- **注册页面**：`src/pages/app/auth/register.vue`（新建）

---

## 第3章：关键技术规范（Crucial Specs）

### 3.1 API调用规范（必须遵守）⚠️ 重点

**核心原则：与登录页面保持完全一致的API调用方式**

#### 3.1.1 路径拼接函数

```typescript
// src/api/auth.ts 中已存在
const authUrl = (path: string) => 
  `${AUTH_API_URL.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;
```

**说明**：
- 自动去除基础URL末尾的斜杠
- 自动去除相对路径开头的斜杠
- 用单个斜杠连接

#### 3.1.2 API调用示例

```typescript
// 1. 获取验证码
const response = await getCaptcha();
// 实际请求: GET https://mp.dayilive.com/api/users/auth/captcha

// 2. 用户注册
const registerRes = await registerUser({
  username: formData.username,
  email: formData.email,
  password: formData.password,
  nickname: formData.nickname,
  captcha_id: captchaId.value,
  captcha_solution: formData.captcha_solution,
});
// 实际请求: POST https://mp.dayilive.com/api/users/users/register

// 3. 自动登录（使用authStore）
await authStore.login({
  username: formData.username,
  password: formData.password,
  captcha_id: captchaId.value,
  captcha_solution: formData.captcha_solution,
});
// authStore内部会调用: POST https://mp.dayilive.com/api/users/auth/login
```

### 3.2 表单字段设计

| 字段 | 类型 | 必填 | 长度限制 | 校验规则 | 错误提示 |
|------|------|------|---------|---------|---------|
| **username** | text | ✅ | 2-50字符 | 字母、数字、下划线 | "用户名格式不正确" |
| **email** | email | ✅ | 符合邮箱格式 | 标准邮箱正则 | "请输入有效的邮箱地址" |
| **password** | password | ✅ | 最小8位 | 大小写+数字+特殊字符 | "密码强度不足" |
| **nickname** | text | ✅ | 2-50字符 | 任意字符 | "昵称不能为空" |
| **captcha_solution** | text | ✅ | 4-6位 | 字母数字组合 | "请输入验证码" |

### 3.3 密码强度指示器

#### 3.3.1 强度级别定义

```typescript
export enum PasswordStrengthLevel {
  VeryWeak = 1,  // 很弱（红色）
  Weak = 2,      // 弱（橙色）
  Medium = 3,    // 中（黄色）
  Strong = 4,    // 强（浅绿）
  VeryStrong = 5 // 很强（深绿）
}
```

#### 3.3.2 计算规则

```typescript
// 密码强度计算规则（带防抖优化）
import { ref } from 'vue';

// 防抖定时器
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function calculatePasswordStrengthLevel(password: string): PasswordStrength {
  let score = 0;
  
  // 1. 长度检查（最多2分）
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  
  // 2. 包含大写字母（1分）
  if (/[A-Z]/.test(password)) score++;
  
  // 3. 包含小写字母（1分）
  if (/[a-z]/.test(password)) score++;
  
  // 4. 包含数字（1分）
  if (/[0-9]/.test(password)) score++;
  
  // 5. 包含特殊字符（1分）
  if (/[!@#$%^&*()]/.test(password)) score++;
  
  // 限制最大分数为5
  score = Math.min(score, 5);
  
  // 根据分数返回强度对象
  const strengthMap: Record<number, PasswordStrength> = {
    0: { level: PasswordStrengthLevel.VeryWeak, text: '密码太短', color: '#EF4444', score: 0 },
    1: { level: PasswordStrengthLevel.VeryWeak, text: '很弱', color: '#EF4444', score: 1 },
    2: { level: PasswordStrengthLevel.Weak, text: '弱', color: '#F59E0B', score: 2 },
    3: { level: PasswordStrengthLevel.Medium, text: '中', color: '#EAB308', score: 3 },
    4: { level: PasswordStrengthLevel.Strong, text: '强', color: '#84CC16', score: 4 },
    5: { level: PasswordStrengthLevel.VeryStrong, text: '很强', color: '#22C55E', score: 5 },
  };
  
  return strengthMap[score];
}

// 带防抖的密码强度计算（在组件中使用）
function calculatePasswordStrength(password: string): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  debounceTimer = setTimeout(() => {
    passwordStrength.value = calculatePasswordStrengthLevel(password);
  }, 300); // 300ms防抖
}
```

**使用方式**（在组件中）：

```vue
<!-- 监听密码输入，添加防抖 -->
<input
  v-model="formData.password"
  @input="calculatePasswordStrength(formData.password)"
  @blur="validateField('password')"
/>
```

#### 3.3.3 UI显示

```vue
<!-- 密码强度指示器 -->
<view v-if="formData.password" class="password-strength">
  <view class="strength-bars">
    <view
      v-for="i in 5"
      :key="i"
      class="strength-bar"
      :class="{ 'strength-bar--active': i <= passwordStrength.score }"
      :style="{ 
        backgroundColor: i <= passwordStrength.score 
          ? passwordStrength.color 
          : '#E5E7EB' 
      }"
    ></view>
  </view>
  <text 
    class="strength-text" 
    :style="{ color: passwordStrength.color }"
  >
    {{ passwordStrength.text }}
  </text>
</view>
```

### 3.4 图形验证码处理

#### 3.4.1 验证码加载流程

```typescript
// 页面加载时获取验证码
onMounted(() => {
  loadCaptcha();
});

// 加载图形验证码
async function loadCaptcha(): Promise<void> {
  try {
    const res = await getCaptcha();
    captchaId.value = res.data.captcha_id;
    captchaImage.value = res.data.image_base64;
  } catch (error) {
    console.error('[Register] 验证码加载失败', error);
    uni.showToast({ 
      title: '验证码加载失败', 
      icon: 'none' 
    });
  }
}
```

#### 3.4.2 验证码UI布局

```vue
<!-- 验证码输入区域 -->
<view class="captcha-wrapper">
  <input
    class="form-input captcha-input"
    v-model="formData.captcha_solution"
    placeholder="请输入验证码"
    maxlength="6"
    @blur="validateField('captcha_solution')"
  />
  <image
    v-if="captchaImage"
    class="captcha-image"
    :src="captchaImage"
    mode="aspectFit"
    @tap="refreshCaptcha"
  />
  <text class="captcha-refresh" @tap="refreshCaptcha">
    换一张
  </text>
</view>
```

### 3.5 表单验证规则

#### 3.5.1 单字段验证函数

```typescript
function validateField(field: keyof RegisterForm): boolean {
  let isValid = true;
  errors[field] = '';

  switch (field) {
    case 'username':
      if (!formData.username) {
        errors.username = '请输入用户名';
        isValid = false;
      } else if (!validateUsername(formData.username)) {
        errors.username = '用户名格式不正确（2-50字符，字母/数字/下划线）';
        isValid = false;
      }
      break;

    case 'email':
      if (!formData.email) {
        errors.email = '请输入邮箱';
        isValid = false;
      } else if (!validateEmail(formData.email)) {
        errors.email = '请输入有效的邮箱地址';
        isValid = false;
      }
      break;

    case 'password':
      if (!formData.password) {
        errors.password = '请输入密码';
        isValid = false;
      } else if (!validatePassword(formData.password)) {
        errors.password = '密码强度不足（至少8位，包含大小写字母+数字+特殊字符）';
        isValid = false;
      }
      break;

    case 'nickname':
      if (!formData.nickname) {
        errors.nickname = '请输入昵称';
        isValid = false;
      } else if (formData.nickname.length < 2 || formData.nickname.length > 50) {
        errors.nickname = '昵称长度为2-50字符';
        isValid = false;
      }
      break;

    case 'captcha_solution':
      if (!formData.captcha_solution) {
        errors.captcha_solution = '请输入验证码';
        isValid = false;
      }
      break;
  }

  return isValid;
}
```

#### 3.5.2 工具函数（需要在utils中实现）

```typescript
// src/utils/validate.ts

/**
 * 校验用户名格式
 * 规则：2-50字符，仅允许字母、数字、下划线
 */
export function validateUsername(username: string): boolean {
  const regex = /^[a-zA-Z0-9_]{2,50}$/;
  return regex.test(username);
}

/**
 * 校验邮箱格式
 */
export function validateEmail(email: string): boolean {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

/**
 * 校验密码强度
 * 规则：至少8位，包含大小写字母+数字+特殊字符
 */
export function validatePassword(password: string): boolean {
  if (password.length < 8) return false;
  
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecialChar = /[!@#$%^&*()]/.test(password);
  
  return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
}
```

### 3.6 注册提交流程（核心）⚠️

#### 3.6.1 提交函数实现

```typescript
async function handleSubmit(): Promise<void> {
  // 1. 前端校验
  if (!validateAllFields()) {
    uni.showToast({ 
      title: '请检查表单填写', 
      icon: 'none' 
    });
    return;
  }

  // 2. 开始提交
  isSubmitting.value = true;

  try {
    // 3. 调用注册API
    const res = await registerUser({
      username: formData.username,
      email: formData.email,
      password: formData.password,
      nickname: formData.nickname,
      captcha_id: captchaId.value,
      captcha_solution: formData.captcha_solution,
    });

    // 4. 注册成功
    console.log('[Register] 注册成功', res.data);
    uni.showToast({ 
      title: '注册成功，正在登录...', 
      icon: 'success', 
      duration: 2000 
    });

    // 5. 自动登录（使用刚注册的账号）
    await autoLogin(formData.username, formData.password);

    // 6. 跳转到首页
    setTimeout(() => {
      uni.reLaunch({ 
        url: '/pages/app/tabbar/home/index' 
      });
    }, 1500);

  } catch (error: any) {
    // 使用统一错误处理函数
    handleRegisterError(error);

  } finally {
    isSubmitting.value = false;
  }
}
```

#### 3.6.2 自动登录函数（核心）⚠️

**重要问题修正**：注册接口调用后会消耗图形验证码，导致验证码失效。因此**自动登录前必须重新获取验证码**。

```typescript
/**
 * 注册成功后自动登录
 * @param username 用户名
 * @param password 密码
 */
async function autoLogin(username: string, password: string): Promise<void> {
  try {
    console.log('[Register] 开始自动登录...');
    
    // ⚠️ 关键修正：注册后验证码已失效，必须重新获取
    console.log('[Register] 重新获取验证码...');
    const captchaRes = await getCaptcha();
    const newCaptchaId = captchaRes.data.captcha_id;
    const newCaptchaImage = captchaRes.data.image_base64;
    
    console.log('[Register] 新验证码获取成功，ID:', newCaptchaId);
    
    // ⚠️ 方案选择：
    // 方案1：使用新验证码，但不要求用户输入（后端如果验证码校验是可选的）
    // 方案2：如果后端强制要求验证码，则提示用户前往登录页
    // 方案3：检查后端API是否支持自动登录接口（不需要验证码）
    
    // 推荐：方案3 - 使用后端提供的自动登录Token（如果有）
    // 如果注册接口返回了access_token，直接使用
    // 如果没有，则走方案2
    
    // 使用 authStore.login() 进行登录（与登录页面保持一致）
    const authStore = useAuthStore();
    
    // 构造登录表单数据
    const loginFormData = {
      username,
      password,
      captcha_id: newCaptchaId, // ✅ 使用新获取的验证码ID
      captcha_solution: '', // ⚠️ 问题：无法自动填写验证码
    };
    
    // ⚠️ 验证码问题：
    // 1. 如果后端登录接口验证码是必填的，自动登录会失败
    // 2. 建议：后端提供一个「注册后自动登录」的专用接口，或者在注册响应中直接返回Token
    // 3. 临时方案：自动登录失败时，提示用户前往登录页手动登录
    
    try {
      await authStore.login(loginFormData);
      console.log('[Register] 自动登录成功');
    } catch (loginError: any) {
      // 如果是验证码错误（预期情况），不抛出错误
      if (loginError.code === 4003) {
        console.log('[Register] 验证码校验失败（预期），提示用户前往登录页');
        uni.showToast({ 
          title: '注册成功，请前往登录', 
          icon: 'success',
          duration: 2000
        });
        setTimeout(() => {
          uni.navigateBack();
        }, 2000);
        return; // 不抛出错误，正常返回
      }
      // 其他错误才抛出
      throw loginError;
    }
    
  } catch (error) {
    console.error('[Register] 自动登录失败', error);
    // 自动登录失败，提示用户前往登录页
    uni.showToast({ 
      title: '注册成功，请前往登录', 
      icon: 'none' 
    });
    setTimeout(() => {
      uni.navigateBack();
    }, 1500);
    throw error; // 抛出错误，阻止跳转到首页
  }
}
```

**最佳实践建议**：

1. **后端优化方案**（推荐）：
   ```typescript
   // 注册接口直接返回Token，前端无需再次登录
   interface RegisterResponse {
     code: number;
     message: string;
     data: {
       user_id: number;
       username: string;
       access_token: string;  // ✅ 直接返回Token
       refresh_token: string;
       expires_in: number;
     };
   }
   
   // 前端处理
   const registerRes = await registerUser({...});
   if (registerRes.data.access_token) {
     // 直接保存Token，无需再次登录
     authStore.setTokens(
       registerRes.data.access_token,
       registerRes.data.refresh_token
     );
     await authStore.fetchUserProfile();
     // 跳转首页
   }
   ```

2. **前端临时方案**（当前）：
   - 自动登录失败时，提示用户"注册成功，请前往登录"
   - 返回登录页，用户手动输入验证码登录
   - 用户体验略有下降，但不影响核心功能

---

## 第4章：样式规范（Style Specs）

### 4.1 响应式适配规则

**断点定义**（与登录注册统一）：

| 断点 | 宽度范围 | 容器宽度 | 布局特点 |
|------|---------|---------|--------|
| **Mobile** | < 480px | `92vw; max-width: 420px` | 单列、全宽按钮 |
| **Tablet** | 480px ~ 900px | `420px; max-width: 460px` | 卡片居中 |
| **Desktop** | >= 900px | `420px; max-width: 460px` | 居中容器 |

### 4.2 色彩系统

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 品牌主色 | #0F766E | 注册按钮、链接 |
| 文字主色 | #111827 | 标题、重要文字 |
| 文字副色 | #6B7280 | 副标题、提示文字 |
| 边框颜色 | #D1D5DB | 输入框默认边框 |
| 错误颜色 | #EF4444 | 错误提示、错误边框 |
| 背景色 | #F9FAFB | 页面背景 |
| 白色 | #FFFFFF | 卡片、输入框背景 |

### 4.3 字体规范

| 元素 | 字号 | 字重 | 颜色 |
|------|------|------|------|
| 页面标题 | 48rpx | 700 | #111827 |
| 副标题 | 28rpx | 400 | #6B7280 |
| 表单标签 | 28rpx | 500 | #374151 |
| 输入框 | 30rpx | 400 | #111827 |
| 按钮文字 | 32rpx | 600 | #FFFFFF |
| 错误提示 | 24rpx | 400 | #EF4444 |

### 4.4 Consumer模式设计要点

**✅ 必须遵守**：
1. **去卡片化**：不使用明显的白色卡片+阴影，整个页面保持轻背景
2. **pill按钮**：主按钮必须是完整圆角（border-radius: 48rpx，高度96rpx）
3. **轻输入**：输入框边框轻（2rpx），focus时变为品牌色
4. **协议贴底**：协议区与auth-main平级，采用flex-shrink: 0确保始终可见
5. **响应式容器**：严格遵循92vw/420-460px规则
6. **垂直位置**：Mobile靠上（padding-top: 12vh）

**❌ 禁止操作**：
1. 不使用明显的卡片阴影
2. 不使用方形按钮（必须是pill样式）
3. 不在Mobile端使用过大的top padding

---

## 第5章：错误处理与反馈（Error Handling）

### 5.1 错误码对照表

| 错误码 | 说明 | 前端处理 | 用户提示 |
|-------|------|---------|----------|
| 4003 | 验证码错误或已过期 | 刷新验证码，清空输入框 | "验证码错误或已过期，请重新输入" |
| 4009 | 用户名已被占用 | 输入框红色边框，focus到username | "用户名已被占用，请更换" |
| 4010 | 邮箱已被注册 | 输入框红色边框，focus到email | "邮箱已被注册，请更换或前往登录" |
| 4001 | 参数校验失败 | 解析error.data.errors，逐字段显示 | 显示具体字段错误（如"密码格式不正确"）|
| 4000 | 请求参数错误 | 检查formData，显示通用提示 | "请检查表单填写" |
| 5000 | 服务器内部错误 | Toast提示，不清空表单 | "服务器繁忙，请稍后重试" |
| 5003 | 网络连接超时 | Toast提示，保留表单数据 | "网络连接超时，请检查网络" |

**错误处理优化**：

```typescript
// 统一错误处理函数
function handleRegisterError(error: any): void {
  console.error('[Register] 注册失败', error);
  
  // 1. 提取错误信息
  const errorCode = error.code || error.response?.data?.code;
  const errorMsg = error.message || error.response?.data?.message || '注册失败，请重试';
  const errorData = error.response?.data?.data;
  
  // 2. 根据错误码处理
  switch (errorCode) {
    case 4003:
      // 验证码错误
      errors.captcha_solution = '验证码错误或已过期';
      formData.captcha_solution = '';
      refreshCaptcha();
      uni.showToast({ title: '验证码错误，请重新输入', icon: 'none' });
      break;
      
    case 4009:
      // 用户名已占用
      errors.username = '用户名已被占用';
      uni.showToast({ title: '用户名已被占用，请更换', icon: 'none' });
      break;
      
    case 4010:
      // 邮箱已注册
      errors.email = '邮箱已被注册';
      uni.showToast({ 
        title: '邮箱已被注册，请更换或前往登录', 
        icon: 'none',
        duration: 3000
      });
      break;
      
    case 4001:
      // 参数校验失败，显示具体字段错误
      if (errorData && typeof errorData === 'object') {
        Object.keys(errorData).forEach((field) => {
          if (field in errors) {
            errors[field as keyof typeof errors] = errorData[field];
          }
        });
      }
      uni.showToast({ title: '请检查表单填写', icon: 'none' });
      break;
      
    default:
      // 通用错误处理
      uni.showToast({ title: errorMsg, icon: 'none' });
  }
  
  // 3. 非验证码错误也刷新验证码（防止表单重复提交）
  if (errorCode !== 4003) {
    refreshCaptcha();
  }
}
```

### 5.2 用户反馈设计

**实时反馈**：
- 输入框失去焦点时校验，错误提示显示在字段下方
- 密码输入时实时更新强度指示器
- 验证码输入框限制6位字符
- 用户名/邮箱已存在时，输入框显示红色边框+错误提示

**提交反馈**：
- 点击注册按钮→按钮显示"注册中..."，禁用防重复提交
- 成功：显示Toast提示"注册成功，正在登录..."
- 失败：显示Toast提示错误信息，按钮恢复可点击状态

---

## 第6章：测试清单（Testing Checklist）

### 6.1 功能测试

- [ ] 页面加载时自动获取验证码
- [ ] 用户名输入框支持2-50字符，字母/数字/下划线
- [ ] 邮箱输入框支持标准邮箱格式
- [ ] 密码输入框支持显示/隐藏切换
- [ ] 密码强度指示器实时更新
- [ ] 昵称输入框支持2-50字符
- [ ] 验证码图片正常显示
- [ ] 点击"换一张"刷新验证码
- [ ] 点击注册按钮，前端校验所有字段
- [ ] 校验失败显示错误提示
- [ ] 校验通过调用注册API
- [ ] 注册成功自动登录并跳转首页
- [ ] 注册失败显示错误提示并刷新验证码
- [ ] 点击"立即登录"跳转到登录页
- [ ] 点击返回按钮返回登录页

### 6.2 边界测试

- [ ] 用户名为空，显示"请输入用户名"
- [ ] 用户名过短（<2字符），显示"用户名格式不正确"
- [ ] 用户名过长（>50字符），显示"用户名格式不正确"
- [ ] 用户名包含特殊字符，显示"用户名格式不正确"
- [ ] 邮箱为空，显示"请输入邮箱"
- [ ] 邮箱格式错误，显示"请输入有效的邮箱地址"
- [ ] 密码为空，显示"请输入密码"
- [ ] 密码过短（<8字符），显示"密码强度不足"
- [ ] 密码缺少大写字母，显示"密码强度不足"
- [ ] 昵称为空，显示"请输入昵称"
- [ ] 验证码为空，显示"请输入验证码"
- [ ] 网络异常时显示"网络连接超时"
- [ ] 用户名已存在时显示"用户名已被占用"
- [ ] 邮箱已注册时显示"邮箱已被注册"
- [ ] 验证码错误时显示"验证码错误或已过期"

---

## 第7章：完整代码结构（Code Structure）

### 7.1 核心文件路径

```
src/pages/app/auth/
├── register.vue              # 注册页面主组件（新建）
└── login.vue                 # 登录页面（已存在，需添加跳转到注册的入口）

src/api/
└── auth.ts                   # 认证API（已存在，确认registerUser函数存在）

src/store/
└── auth.ts                   # 认证状态管理（已存在，使用authStore.login）

src/types/
└── auth.ts                   # 认证类型定义（已存在或需补充）

src/utils/
├── validate.ts               # 表单校验工具（可能需要新建）
└── password.ts               # 密码强度计算工具（可能需要新建）
```

### 7.2 页面组件结构

```vue
<template>
  <view class="register-page">
    <!-- 顶部导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @tap="handleBack">
        <text class="icon-back">←</text>
      </view>
      <text class="nav-title">注册账号</text>
    </view>

    <!-- 页面内容 -->
    <view class="content">
      <!-- 标题区域 -->
      <view class="header">
        <text class="title">创建您的账号</text>
        <text class="subtitle">快速注册，开启医学直播之旅</text>
      </view>

      <!-- 表单区域 -->
      <view class="form">
        <!-- 用户名 -->
        <view class="form-item" :class="{ 'form-item--error': errors.username }">
          <!-- ... -->
        </view>

        <!-- 邮箱 -->
        <view class="form-item" :class="{ 'form-item--error': errors.email }">
          <!-- ... -->
        </view>

        <!-- 密码 -->
        <view class="form-item" :class="{ 'form-item--error': errors.password }">
          <!-- ... -->
          <!-- 密码强度指示器 -->
          <view v-if="formData.password" class="password-strength">
            <!-- ... -->
          </view>
        </view>

        <!-- 昵称 -->
        <view class="form-item" :class="{ 'form-item--error': errors.nickname }">
          <!-- ... -->
        </view>

        <!-- 验证码 -->
        <view class="form-item" :class="{ 'form-item--error': errors.captcha_solution }">
          <view class="captcha-wrapper">
            <!-- ... -->
          </view>
        </view>

        <!-- 注册按钮 -->
        <button
          class="submit-btn"
          :class="{ 'submit-btn--loading': isSubmitting }"
          :disabled="isSubmitting"
          @tap="handleSubmit"
        >
          {{ isSubmitting ? '注册中...' : '注 册' }}
        </button>

        <!-- 底部提示 -->
        <view class="footer-tip">
          <text class="tip-text">已有账号？</text>
          <text class="tip-link" @tap="handleGoToLogin">立即登录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { getCaptcha, registerUser } from '@/api/auth';
import { useAuthStore } from '@/store/auth';
import type { RegisterForm, PasswordStrength } from '@/types/auth';
import { validateUsername, validateEmail, validatePassword } from '@/utils/validate';
import { calculatePasswordStrengthLevel } from '@/utils/password';

// ==================== 状态定义 ====================
const formData = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  nickname: '',
  captcha_solution: '',
});

const errors = reactive<Record<string, string>>({
  username: '',
  email: '',
  password: '',
  nickname: '',
  captcha_solution: '',
});

const captchaId = ref<string>('');
const captchaImage = ref<string>('');
const showPassword = ref<boolean>(false);
const isSubmitting = ref<boolean>(false);
const passwordStrength = ref<PasswordStrength>({
  level: 1,
  text: '密码太短',
  color: '#EF4444',
  score: 0,
});

// ==================== 初始化 ====================
onMounted(() => {
  loadCaptcha();
});

// ==================== 核心函数 ====================
// 1. loadCaptcha() - 加载验证码
// 2. refreshCaptcha() - 刷新验证码
// 3. validateField() - 校验单个字段
// 4. validateAllFields() - 校验所有字段
// 5. calculatePasswordStrength() - 计算密码强度
// 6. handleSubmit() - 提交注册
// 7. autoLogin() - 自动登录
// 8. handleBack() - 返回上一页
// 9. handleGoToLogin() - 跳转到登录页

</script>

<style lang="scss" scoped>
// Consumer模式样式
// 参考登录页面样式，保持一致性
</style>
```

---

## 第8章：关键实现要点（Key Points）

### 8.1 API一致性要点

1. ✅ **必须使用authUrl()函数**拼接API路径
2. ✅ **必须使用authStore.login()**进行自动登录
3. ✅ **必须复用登录页面的错误处理逻辑**
4. ✅ **必须使用相同的请求方法**（get、post）

### 8.2 用户体验要点

1. ✅ **实时反馈**：输入框失去焦点时校验
2. ✅ **清晰提示**：错误信息明确、易懂
3. ✅ **防误操作**：防重复提交、返回确认
4. ✅ **无缝体验**：注册成功后自动登录并跳转

### 8.3 安全性要点

1. ✅ **密码强度强制要求**：至少8位，包含大小写+数字+特殊字符
2. ✅ **图形验证码防护**：防止机器人批量注册
3. ✅ **HTTPS加密传输**：所有API请求使用HTTPS
4. ✅ **敏感信息保护**：密码输入框默认隐藏

---

## 附录：相关文档

- [注册页面功能设计与实现文档](./注册页面功能设计与实现文档.md)
- [登录与跨应用跳转设计文档](./登录与跨应用跳转设计文档.md)
- [用户模块设计文档authing版+权限设计版](./后端设计文档/用户模块设计文档authing版+权限设计版.md)

---

**文档创建日期**: 2026-03-12  
**当前版本**: V1.0  
**维护人**: 前端团队
