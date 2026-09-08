---

# 媒体下载服务前端设计文件 (最终版)

## 一、设计目标

- 构建一个直观、易用的用户界面，使用户能够高效地管理媒体下载任务。
- 实现与后端API的无缝集成，支持下载任务的全生命周期管理（创建、查询、更新、删除、重试）。
- 提供下载任务的实时状态和进度反馈。
- 遵循统一的UI/UX规范，确保良好的用户体验。
- 实现前端的数据验证和错误处理。
- 界面设计参考哔哩哔哩风格，并针对医生和医生从业者的专业视频网站场景进行优化。
- **性能目标:** 确保任务列表页在数据量较大时仍能快速加载和流畅滚动；详情页数据实时更新延迟低。
- **可维护性目标:** 代码结构清晰，模块化程度高，易于理解和修改。
- **安全性目标:** 防范常见的Web安全漏洞（如XSS），确保用户数据安全。
- **可扩展性目标:** 设计灵活，易于未来新增功能或调整界面。
- **SSO认证目标:** 支持基于JWT Token的SSO认证，自动处理用户登录状态和Token管理。

## 二、技术选型

- **前端框架:** Vue 3
- **状态管理:** Pinia
- **UI组件库:** Element Plus
- **API请求库:** Axios
- **路由管理:** Vue Router
- **实时通信:** WebSocket 
- **构建工具:** Vite
- **代码规范:** ESLint 
- **测试框架:** Vue Test Utils (单元测试、组件测试)
- **日期处理库:** Day.js (用于时间戳的格式化和时区处理)

**认证管理:** JWT Token + 自动重定向
- **Token存储:** localStorage用于JWT Token持久化存储
- **自动重定向:** 认证失败时自动跳转到用户登录页面（通过配置文件配置URL）
- **Token验证:** 前端通过JWT Token过期时间进行本地验证
- **HTTP拦截器:** Axios拦截器用于自动添加Token和处理认证失败

**URL配置管理:**
- **禁止硬编码:** 严禁在业务代码中硬编码任何服务器IP地址或端口号
- **配置文件:** 所有URL通过`config/env.js`配置文件统一管理
- **环境变量:** 支持通过环境变量进行多环境配置
- **动态加载:** 运行时动态读取配置，支持部署时修改

**跨服务前端跳转配置：**
- **用户服务前端地址：** 通过环境变量配置用户服务前端的基础URL
- **Profile页面跳转：** 支持从媒体下载服务跳转到用户服务的个人资料页面
- **统一跳转管理：** 所有跨服务跳转都通过配置文件管理，支持多环境部署

## 项目目录结构
```
├── public/
│   └── simple-callback.html    # 外部登录回调处理页面
├── src/
│   ├── components/
│   │   ├── AuthCallback.vue    # Vue 路由回调组件
│   │   ├── DownloadCenter.vue
│   │   ├── DownloadTaskList.vue
│   │   ├── DownloadTaskCreate.vue
│   │   ├── DownloadTaskDetail.vue
│   │   ├── DownloadFailures.vue
│   │   └── DownloadVideosDetail.vue
│   ├── stores/
│   │   ├── auth.js
│   │   └── download.js
│   ├── utils/
│   │   ├── request.js
│   │   ├── auth.js
│   │   └── time.js
│   ├── router/
│   │   └── index.js
│   ├── api/
│   │   └── download.js
│   ├── constants/
│   │   └── api.js           # API地址常量定义
│   └── config/
│       └── env.js           # 环境配置文件
```

## 环境配置与URL管理

### 配置文件结构

**必须在项目根目录创建以下配置文件：**

#### `config/env.js` - 环境变量配置文件
```javascript
// 环境变量配置文件 - 支持多环境部署
// 请根据实际部署环境修改这些值

export const ENV_CONFIG = {
  // ===== 媒体下载服务后端API地址 =====
  VITE_BASE_API_URL: 'http://124.220.235.226:8001/',
  
  // ===== 用户认证服务配置 =====
  VITE_AUTH_API_URL: 'http://124.220.235.226:8002/',
  VITE_LOGIN_URL: 'http://124.220.235.226:5173/pages/auth/login',
  // ===== 用户服务前端地址配置 =====
  VITE_FRONTEND_USER_URL: 'http://localhost:5173',  // 用户服务前端基础地址
  // ===== 跨服务回调配置 =====
  VITE_CALLBACK_PATH: '/simple-callback.html',
  VITE_AUTH_CALLBACK_PATH: '/auth/callback',
  
  // ===== 其他配置 =====
  VITE_APP_TITLE: '媒体下载服务',
  VITE_API_TIMEOUT: '30000',
  VITE_POLLING_INTERVAL: '5000',
  
  // ===== WebSocket配置（可选）=====
  VITE_WS_URL: 'ws://124.220.235.226:8001/ws',
};

// 开发/生产环境自动检测
const isDev = typeof window !== 'undefined' && 
              (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// 导出到全局供 constants/api.js 读取
if (typeof window !== 'undefined') {
  window.__ENV = ENV_CONFIG;
}
```

#### `constants/api.js` - API地址常量定义
```javascript
// API地址常量定义 - 支持多环境配置
// 优先从 import.meta.env 读取，其次从 window.__ENV（由 config/env.js 注入）

const getEnv = (key) => {
  const viteEnv = import.meta?.env?.[key];
  const runtimeEnv = typeof window !== 'undefined' ? window.__ENV?.[key] : undefined;
  return viteEnv || runtimeEnv || '';
};

// 媒体下载服务后端API基础地址
export const BASE_API_URL = (
  getEnv('VITE_BASE_API_URL') || 'http://localhost:8001/'
).replace(/\/?$/, '/');

// 用户认证服务API地址
export const AUTH_API_URL = (
  getEnv('VITE_AUTH_API_URL') || 'http://localhost:8002/'
).replace(/\/?$/, '/');

// 用户登录页面地址
export const LOGIN_URL = 
  getEnv('VITE_LOGIN_URL') || 
  (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}/pages/auth/login` : '');

// 用户服务前端基础地址
export const FRONTEND_USER_URL = getEnv('VITE_FRONTEND_USER_URL') || 
  (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : '');

// 回调路径配置
export const CALLBACK_PATH = getEnv('VITE_CALLBACK_PATH') || '/simple-callback.html';
export const AUTH_CALLBACK_PATH = getEnv('VITE_AUTH_CALLBACK_PATH') || '/auth/callback';

// 其他配置常量
export const APP_TITLE = getEnv('VITE_APP_TITLE') || '媒体下载服务';
export const API_TIMEOUT = parseInt(getEnv('VITE_API_TIMEOUT')) || 30000;
export const POLLING_INTERVAL = parseInt(getEnv('VITE_POLLING_INTERVAL')) || 5000;
export const WS_URL = getEnv('VITE_WS_URL') || '';
```

#### `index.html` - 必须引入配置文件
```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>媒体下载服务</title>
</head>
<body>
  <div id="app"></div>
  <!-- 重要：必须在main.js之前引入配置文件 -->
  <script src="/config/env.js"></script>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

### 部署配置说明

#### 本地开发环境
```bash
# 直接修改 config/env.js 中的配置值
VITE_BASE_API_URL: 'http://localhost:8001/'
VITE_LOGIN_URL: 'http://localhost:5173/pages/auth/login'

VITE_FRONTEND_USER_URL: 'http://localhost:5173'

```

#### 生产部署环境
```bash
# 修改 config/env.js 为实际的生产环境地址
VITE_BASE_API_URL: 'http://124.220.235.226:8001/'
VITE_LOGIN_URL: 'http://124.220.235.226:5173/pages/auth/login'
VITE_FRONTEND_USER_URL: 'http://124.220.235.226:5173'
```

#### Docker部署
```dockerfile
# 在Docker构建时替换配置文件
COPY config/env.prod.js /app/config/env.js
```

### ⚠️ 重要约束

#### 严禁硬编码规则
- **绝对禁止：** 在任何`.vue`、`.js`组件或业务代码中直接写入IP地址、端口号或完整URL
- **必须使用：** 从`@/constants/api`导入的常量（如`BASE_API_URL`、`LOGIN_URL`等）
- **错误示例：** ❌ `axios.get('http://124.220.235.226:8001/api/tasks')`
- **正确示例：** ✅ `axios.get(BASE_API_URL + 'v1/download/tasks')`

#### 配置使用规范
- **配置优先级：** 环境变量 > 配置文件 > 默认值
- **常量导入：** 所有组件必须从`@/constants/api`导入URL常量
- **动态配置：** 支持运行时修改`config/env.js`即可生效
- **部署便利：** 不同环境只需替换配置文件，业务代码零修改

#### 代码示例对比

**❌ 错误的硬编码方式：**
```javascript
// 绝对禁止这样写！
window.location.href = 'http://localhost:5173/pages/auth/login';
const response = await axios.get('http://124.220.235.226:8001/api/v1/tasks');
```

**✅ 正确的配置化方式：**
```javascript
// 必须这样写
import { LOGIN_URL, BASE_API_URL } from '@/constants/api';

window.location.href = LOGIN_URL;
const response = await axios.get(BASE_API_URL + 'v1/download/tasks');
```

#### 跨服务跳转规范
- **用户服务跳转：** 所有跳转到用户服务前端的操作必须使用`FRONTEND_USER_URL`常量
- **Profile页面跳转：** 用户点击个人信息时，跳转地址为`${FRONTEND_USER_URL}/pages/user/profile`
- **配置管理：** 用户服务前端地址通过`config/env.js`统一管理，支持多环境部署
- **跳转方式：** 使用`window.location.href`进行完整页面跳转，确保用户体验一致

#### 代码示例对比

**❌ 错误的硬编码方式：**
```javascript
// 绝对禁止这样写！
window.location.href = 'http://localhost:5173/pages/user/profile';
```

**✅ 正确的配置化方式：**
```javascript
// 必须这样写
import { FRONTEND_USER_URL } from '@/constants/api';

const profileUrl = `${FRONTEND_USER_URL}/pages/user/profile`;
window.location.href = profileUrl;
```

#### 部署流程
1. **开发环境：** 修改`config/env.js`中的开发地址
2. **测试环境：** 替换为测试环境的`config/env.js`
3. **生产环境：** 使用生产环境的`config/env.js`
4. **Docker部署：** 通过挂载或COPY替换配置文件

这样设计确保了：
- ✅ **零代码修改部署** - 只需更换配置文件
- ✅ **多环境支持** - 同一套代码适配所有环境  
- ✅ **维护简便** - IP/端口变更只需改配置
- ✅ **安全可靠** - 避免代码中暴露敏感地址


## 三、数据模型/接口定义
### 3.1. 用户认证模型

``` typescript

interface User {
  user_id: string;
  username?: string;
  email?: string;
  // 其他用户信息字段
}


interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  tokenExpiry: number | null;
  redirectPath: string | null;  // 新增：保存登录前的目标路径
}
```


### 3.2. 数据库定义

根据后端 <mcfile name="媒体下载服务设计文档v2.md" path="d:\python_code\user_login\媒体下载服务设计文档v2.md"></mcfile> 中数据库表定义，前端需要定义相应的数据模型来处理从后端接收的数据。这些模型字段将与数据库表字段保持一致。

### 3.2.1. 下载任务模型 (`DownloadTask`)

- `id`: string (UUID)
- `user_id`: string (UUID) - **新增：用户ID字段**
- `video_id`: string (uuid)
- `liveroom_id`: string (VARCHAR)
- `liveroom_title`: string | null (VARCHAR)
- `liveroom_url`: string | null (VARCHAR)
- `resource_url`: string (VARCHAR)
- `resource_type`: string (VARCHAR, 'hls', 'mp4', 'image')
- `status`: string (VARCHAR, 'pending', 'processing', 'completed', 'partial_completed', 'failed', 'cancelled')
- `progress`: number (FLOAT, 0-1)
- `retry_count`: number (INT)
- `last_error`: string | null (TEXT)
- `created_at`: string (TIMESTAMP, ISO 8601格式)
- `updated_at`: string (TIMESTAMP, ISO 8601格式)
- `completed_at`: string | null (TIMESTAMP, ISO 8601格式)

### 3.2.2. 下载失败记录模型 (`DownloadFailure`)

- `id`: string (UUID)
- `task_id`: string (UUID)
- `resource_url`: string (TEXT)
- `expected_path`: string (TEXT)
- `resource_type`: string (VARCHAR, 'ts', 'mp4', 'image')
- `failure_type`: string (VARCHAR, 'network_error', 'timeout', 'invalid_content', 'storage_error', 'permission_error')
- `error_message`: string (TEXT)
- `retry_count`: number (INT)
- `next_retry_time`: string | null (TIMESTAMP, ISO 8601格式)
- `status`: string (VARCHAR, 'pending', 'retrying', 'abandoned')
- `created_at`: string (TIMESTAMP, ISO 8601格式)
- `updated_at`: string (TIMESTAMP, ISO 8601格式)

### 3.2.3. 单任务下已下载视频模型 (`DownloadedVideo`)

- `id`: string (UUID)
- `video_id`: string (uuid)
- `liveroom_id`: string (VARCHAR)
- `liveroom_title`: string | null (VARCHAR)
- `liveroom_url`: string | null (VARCHAR)
- `resource_type`: string (VARCHAR, 'hls', 'mp4')
- `resource_url`: string (VARCHAR)
- `storage_path`: string (VARCHAR)
- `file_size`: number | null (BIGINT)
- `duration`: number | null (INT)
- `resolution`: string | null (VARCHAR)
- `format`: string | null (VARCHAR)
- `cover_url`: string | null (VARCHAR)
- `cover_path`: string | null (VARCHAR)
- `download_task_id`: string | null (UUID)
- `status`: string (VARCHAR, 'completed', 'partial_completed', 'failed')
- `download_start_time`: string | null (TIMESTAMP, ISO 8601格式)
- `download_end_time`: string | null (TIMESTAMP, ISO 8601格式)
- `created_at`: string (TIMESTAMP, ISO 8601格式)
- `updated_at`: string (TIMESTAMP, ISO 8601格式)

### 3.3. API统一响应格式

```typescript
interface ApiResponse<T> {
  code: number; // 状态码，200表示成功，其他表示错误
  message: string; // 响应消息
  data: T | null; // 实际返回内容，根据具体接口返回的数据模型而定
  timestamp: string; // 响应时间戳 (ISO 8601 格式)
}
```
### 3.4. API 接口列表 (已根据后端实际实现调整)

**下载任务相关：**
- GET /api/v1/download/tasks : 获取下载任务列表 (支持分页、排序、筛选)
- POST /api/v1/download/tasks : 创建新的下载任务
- GET /api/v1/download/tasks/{task_id} : 获取单个下载任务详情
- DELETE /api/v1/download/tasks/{task_id} : 取消/删除下载任务
- POST /api/v1/download/tasks/{task_id}/start : 开始下载任务
- POST /api/v1/download/tasks/{task_id}/retry : 重试下载任务

**失败记录相关：**
- GET /api/v1/download/tasks/{task_id}/failures : 获取任务的失败记录列表 (支持分页、排序)
- POST /api/v1/download/tasks/{task_id}/failures : 创建失败记录
- POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry : 重试单个失败资源
- POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon : 放弃单个失败资源

**已下载视频相关：**
- POST /api/v1/download/tasks/{task_id}/videos : 创建已下载视频记录
- GET /api/v1/download/tasks/{task_id}/videos : 获取单任务下的已下载视频列表

> **注意：**
> 1. 全局已下载视频相关接口（如 GET /api/v1/downloaded-videos 等）后端未实现，前端不应设计相关页面和功能。
> 2. 媒体下载服务不提供认证相关API接口，认证由用户服务负责。

### 3.5. API认证规范

**服务架构说明：**
- **用户服务:** 负责用户登录、注册、JWT Token颁发
- **媒体下载服务:** 负责验证JWT Token有效性，实现用户数据隔离

**请求头格式：**
- 所有需要认证的API请求必须在请求头中包含：`Authorization: Bearer <JWT_TOKEN>`

**认证失败响应：**
```json
{
  "code": 401,
  "message": "认证失败",
  "data": {
    "error": "认证凭证无效"
  },
  "timestamp": "2024-03-20T10:00:00Z"
}
```

**用户数据隔离：**
- 后端通过JWT Token中的`user_id`字段实现数据隔离
- 所有下载任务API只返回当前认证用户的数据
- 前端无需调用额外的认证验证接口


## 三、跨服务认证集成规范

### 3.1 外部登录回调页面设计规范

#### simple-callback.html 页面要求

**文件位置：** `public/simple-callback.html`
**功能描述：** 处理来自用户服务的登录回调，作为跨域认证的中间页面

**核心功能要求：**
- URL参数解析：提取 `token`、`error`、`error_description` 等参数
- Token验证：基础的JWT格式验证（检查是否为3段式结构）
- 状态反馈：显示处理状态（处理中、验证中、成功、失败）
- 自动跳转：验证成功后跳转到 `/auth/callback?token=xxx`
- 错误处理：失败时显示错误信息，3秒后跳转到首页

**UI设计要求：**
- 现代化加载界面：居中布局，蓝紫色渐变背景
- 加载动画：旋转的spinner动画
- 状态提示：动态更新的状态文本和详情描述
- 错误显示：错误时显示红色文本，隐藏spinner
- 响应式设计：适配移动端和桌面端

**技术实现要求：**
- 纯HTML + CSS + JavaScript实现，无依赖
- 使用 `URLSearchParams` 解析参数
- 包含完整的错误捕获和日志输出
- 页面加载时自动执行处理逻辑

### 3.2 AuthCallback.vue 组件设计规范

**文件位置：** `src/components/AuthCallback.vue`
**功能描述：** Vue应用内的最终认证回调处理组件

**核心功能要求：**
- Token获取：从 `route.query.token` 获取JWT Token
- Token设置：调用 `authStore.setToken()` 设置认证状态
- 重定向处理：获取 `localStorage.auth_redirect_path` 并跳转
- 状态管理：维护 processing/success/error 三种状态
- 错误处理：Token无效或设置失败时的错误处理

**UI组件要求：**
- 使用 `el-loading` 组件显示加载状态
- 状态文本动态显示：处理中、成功、错误状态的不同提示
- 简洁的居中布局，白色卡片设计
- 错误时显示具体错误信息

**路由集成要求：**
- 组件挂载时自动执行认证处理逻辑
- 成功后根据 `redirectPath` 进行路由跳转
- 失败后跳转到首页或错误页面
- 支持相对路径和绝对路径的跳转处理

## 四、界面设计与路由规划
### 4.1. 路由规划
- `/login` : 用户登录页面 (重定向自用户服务)
- `/auth/callback` : 认证回调处理页面（处理来自用户服务的登录回调）
- /download-center : 下载中心主页 (包含左侧导航菜单和右侧内容区域)
  - /download-center/tasks : 下载任务列表页 (嵌套在下载中心内)
  - /download-center/tasks/create : 创建下载任务页 (嵌套在下载中心内)
  - /download-center/tasks/:taskId : 下载任务详情页 (嵌套在下载中心内)
  - /download-center/tasks/:taskId/failures : 下载失败记录列表页 (嵌套在下载中心内)
  - /download-center/tasks/:taskId/videos : 单任务下已下载视频列表页 (嵌套在下载中心内)

> **注意：已删除"全局已下载视频列表页"和"全局已下载视频详情页"相关路由。**

### 4.2. 路由守卫配置

```typescript
// 需要认证的路由
const protectedRoutes = [
  '/download-center',
  '/download-center/tasks',
  '/download-center/tasks/create',
  '/download-center/tasks/:taskId',
  '/download-center/tasks/:taskId/failures',
  '/download-center/tasks/:taskId/videos'
];
```


```typescript
// 路由守卫增强版本
import { LOGIN_URL } from '@/constants/api';

router.beforeEach(async (to, from, next) => {
  console.log(`路由导航: ${from.path} -> ${to.path}`);
  
  // 更新页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 媒体下载服务`;
  }
  
  // 检查是否需要认证
  const requiresAuth = to.meta?.requiresAuth || isProtectedRoute(to.path);
  
  if (requiresAuth) {
    const authStore = useAuthStore();
    
    console.log('检查认证状态...');
    
    // 检查Token是否存在
    const savedToken = localStorage.getItem('jwt_token');
    if (!savedToken) {
      console.log('未找到Token，跳转登录');
      authStore.setRedirectPath(to.fullPath);
      
      // 保存原始路径到localStorage
      localStorage.setItem('auth_redirect_path', to.fullPath);
      
      // 使用简化参数避免URL编码问题
      const originDomain = window.location.origin.replace('http://', '').replace('https://', '');
      const loginUrlWithCallback = `${LOGIN_URL}?external_callback=true&origin=${originDomain}`;
      
      console.log('跳转登录，原始路径:', to.fullPath);
      console.log('回调域名:', originDomain);
      window.location.href = loginUrlWithCallback;
      return;
    }
    
    // 检查Token是否有效
    if (!authStore.checkTokenExpiry()) {
      console.log('Token已过期，跳转登录');
      authStore.clearAuth();
      authStore.setRedirectPath(to.fullPath);
      
      // 保存原始路径到localStorage
      localStorage.setItem('auth_redirect_path', to.fullPath);
      
      // 使用简化参数避免URL编码问题
      const originDomain = window.location.origin.replace('http://', '').replace('https://', '');
      const loginUrlWithCallback = `${LOGIN_URL}?external_callback=true&origin=${originDomain}`;
      
      console.log('Token过期，跳转登录，原始路径:', to.fullPath);
      console.log('回调域名:', originDomain);
      window.location.href = loginUrlWithCallback;
      return;
    }
    
    // Token有效，确保store中的认证状态正确
    if (!authStore.isAuthenticated) {
      console.log('恢复认证状态...');
      const success = authStore.setToken(savedToken);
      if (!success) {
        console.error('恢复认证状态失败');
        authStore.forceReauth(to.fullPath);
        return;
      }
    }
    
    console.log('认证检查通过');
    authStore.isAuthenticated = true;
  }
  
  next();
});
```


### 4.3. 下载中心页面 (/download-center)
- 布局:
  - 页面整体分为左侧导航和右侧内容区域的两栏布局
  - 左侧导航菜单：提供各个下载功能模块的入口，包括下载任务列表、创建下载任务等
  - 右侧内容区域：根据左侧选择的菜单项，显示对应的功能页面内容
  - 整体风格保持与系统其他页面一致，特别是参考Bilibili风格进行设计

- 左侧导航菜单:
  - 菜单项：
    - "下载任务列表"：跳转到 /download-center/tasks
    - "创建下载任务"：跳转到 /download-center/tasks/create
    - "下载失败记录"：跳转到 /download-center/tasks/:taskId/failures
    - "单任务已下载视频"：跳转到 /download-center/tasks/:taskId/videos
  - 菜单项样式：当前选中的菜单项有高亮效果，鼠标悬停时有交互反馈
  - 每个菜单项配有对应的图标，增强视觉识别度

- 右侧内容区域:
  - 通过 Vue Router 的 <router-view> 组件动态加载对应的子组件
  - 内容区域有适当的内边距，确保内容不会贴近边缘
  - 内容区域可以独立滚动，左侧导航固定

- 响应式考虑:
  - 在较小屏幕上，可以考虑将左侧导航变为可折叠的侧边栏或顶部导航菜单

- 顶部用户信息区域：
  - 显示当前登录用户名（从JWT Token中解析）
  - 提供登出按钮（清理本地Token并跳转登录页）
  - 显示用户头像（如果JWT Token中包含相关信息）
  - 实现用户下拉菜单，包含：
    - [ ] "个人信息"选项：跳转地址 `${FRONTEND_USER_URL}/pages/user/profile`
    - [ ] "主页"选项：跳转地址`${FRONTEND_USER_URL}/pages/index/index`
  - 使用`window.location.href`进行页面跳转，确保完全跳转到用户服务前端


### 4.4. 下载任务列表页 (/download-center/tasks)
- 布局:
  - 页面采用左右分栏结构，左侧为导航菜单，右侧为内容区。
  - 内容区顶部为操作区（标题+按钮），下方为表格区，底部为分页区。
  - 参考 Bilibili 的简洁、专业风格，配色以蓝、灰、白为主，强调医疗行业的专业感和信息密度。
- 卡片式分区:
  - 操作区和表格区分别用 Element Plus 的 <el-card> 包裹，增加圆角和阴影，提升层次感。
  - 操作按钮右对齐，标题左对齐，按钮风格主色调突出。
- 数据表格/列表项:
  - 使用 <el-table>，开启 border 和 stripe，提升可读性。
  - 表格高度固定，内容超出时内部滚动，避免页面整体滚动。
  - 表格内容左对齐，重要字段（如状态、进度）居中或用颜色/图标突出。
  - 鼠标悬停高亮行，点击行可查看详情
  - 核心信息: 任务ID ( id )、视频ID ( video_id )、直播间ID ( liveroom_id )、资源类型 ( resource_type )、状态 ( status )、进度 ( progress ，前端展示时转换为0-100%)、重试次数 ( retry_count )、创建时间 ( created_at )、更新时间 ( updated_at )。
  - 操作列:
    - "详情": 跳转到任务详情页 ( /download-center/tasks/:taskId )。
    - "开始下载": 调用 POST /api/v1/download/tasks/{task_id}/start API。仅在 pending 状态下可用。**必须异步执行，不阻塞用户操作。**
    - "重试": 调用 POST /api/v1/download/tasks/{task_id}/retry API。仅在 failed 状态下可用。**必须异步执行，不阻塞用户操作。**
    - "取消": 调用 DELETE /api/v1/download/tasks/{task_id} API。仅在 pending , processing 状态下可用。操作前应有确认提示。
    - "失败记录": 跳转到失败记录列表页 ( /download-center/tasks/:taskId/failures )。仅在 failed 或 partial_completed 状态下可用。
    - "单任务已下载视频": 跳转到 /download-center/tasks/:taskId/videos
  - 状态显示: 使用不同颜色、图标或标签清晰表示不同的任务状态 ( pending , processing , completed , partial_completed , failed , cancelled )。例如，绿色表示完成，红色表示失败，蓝色表示进行中。
  - 进度显示: 使用简洁的进度条组件展示 progress 字段的值（0-1），并转换为百分比显示。进度条颜色可随状态变化。
- 筛选与排序:
  - 在列表上方或侧边提供筛选区域，允许按状态 ( status )、资源类型 ( resource_type )、直播间ID ( liveroom_id ) 等进行筛选。
  - 表格头部提供按创建时间 ( created_at )、更新时间 ( updated_at )、状态 ( status ) 等字段进行排序的功能。
- 数据刷新: 实现定时轮询 ( GET /api/v1/download/tasks ) 获取最新任务列表数据，更新界面状态和进度。轮询间隔可根据任务状态智能调整。如果后端支持，优先使用WebSocket进行实时推送。
- **异步操作要求:** 所有操作按钮（开始下载、重试、取消）必须异步执行，点击后立即返回，不阻塞用户界面。操作过程中按钮显示加载状态并禁用，操作完成后自动恢复。
- **状态管理:** 使用响应式数据管理正在操作的任务集合，确保按钮状态正确反映当前操作状态。
- **实时通知:** 任务状态变化时自动显示通知，包括成功、失败、进度更新等不同类型通知。
- 性能考虑: 对于大量任务，考虑使用虚拟列表（Virtual Scrolling）技术，只渲染可视区域内的列表项，提高页面性能。
- 表格字段与交互
  - 字段展示
    - 任务ID、视频ID等长字段中间省略（如 xxxx...xxxx），悬停显示完整内容。
    - 状态字段用彩色标签（<el-tag>），进度用进度条（<el-progress>），提升视觉识别度。
    - 操作列按钮分组，间距适中，避免拥挤。
  - 操作按钮
    - 详情、开始下载、重试、删除、失败记录等操作按钮分组显示，主次分明。
    - 重要操作（如删除）需二次确认，防止误操作。
    - **异步操作按钮必须支持加载状态和禁用状态，防止重复操作。**
    - **操作完成后自动更新任务状态和界面显示。**
 -  空状态与加载
  - 无数据时显示友好提示，引导用户创建新任务。
  - 数据加载时显示 loading 动画，防止误操作。

### 批量操作功能设计

**批量选择机制：**
- 在表格第一列添加复选框列（`<el-table-column type="selection" />`），支持多选任务
- 实现全选/反选功能，支持跨页选择（如果后端支持）
- 选择状态实时更新，显示当前选中的任务数量

**批量操作按钮：**
- 在操作区域顶部添加批量操作按钮组，包括：
  - "批量下载"按钮：仅当选中任务中有可下载状态的任务时启用
  - "批量重试"按钮：仅当选中任务中有可重试状态的任务时启用
- **按钮可见性策略：**
  - **始终显示：** 批量下载和批量重试按钮始终在界面上可见，不隐藏
  - **状态感知启用：** 根据选中任务的可用状态动态启用/禁用按钮
  - **视觉状态区分：** 使用颜色和透明度变化来区分不同状态
- **按钮状态设计：**
  - **无选中任务时：** 按钮显示为灰色（禁用状态），但保持可见
  - **有选中任务但无可操作任务时：** 按钮显示为浅灰色，文本显示"批量下载 (0)"或"批量重试 (0)"
  - **有可操作任务时：** 按钮显示为明亮颜色，文本显示"批量下载 (3)"或"批量重试 (2)"
- 按钮文本显示：显示可操作的任务数量，如"批量下载 (3)"

**状态感知的批量操作：**
- **批量下载状态控制：**
  - 可下载状态：`pending`（待处理）
  - 不可下载状态：`processing`（处理中）、`completed`（已完成）、`failed`（失败）、`cancelled`（已取消）
  - 按钮启用条件：选中任务中至少有一个`pending`状态的任务

- **批量重试状态控制：**
  - 可重试状态：`failed`（失败）、`cancelled`（已取消）、`partial_completed`（部分完成）
  - 不可重试状态：`pending`（待处理）、`processing`（处理中）、`completed`（已完成）
  - 按钮启用条件：选中任务中至少有一个可重试状态的任务

**批量操作执行流程：**
1. **用户选择任务** → 批量操作按钮根据选中任务状态动态启用/禁用
2. **点击批量操作** → 显示确认对话框，列出将要操作的任务数量和状态
3. **确认执行** → 并行执行所有操作，每个任务独立处理
4. **状态反馈** → 实时显示操作进度，操作完成后显示结果统计
5. **界面更新** → 自动刷新任务列表，更新所有相关任务状态

**批量操作状态管理：**
- 使用响应式数据管理批量操作状态：`batchStarting`、`batchRetrying`
- 操作过程中禁用所有相关按钮，防止重复操作
- 每个任务的操作状态独立管理，支持部分成功/失败的情况
- 操作完成后自动清理状态，恢复按钮可用性

**用户反馈机制：**
- 操作前：显示确认对话框，明确操作内容和影响范围
- 操作中：显示进度提示，告知用户当前操作状态
- 操作后：显示结果统计，包括成功数量、失败数量和具体失败原因
- 错误处理：单个任务失败不影响其他任务，提供详细的错误信息

**用户体验优势：**
- **一致性：** 用户始终能看到所有可用的批量操作选项
- **学习性：** 新用户可以了解系统支持哪些批量操作
- **状态透明：** 用户可以清楚看到当前选择状态和可执行的操作
- **操作引导：** 按钮文本显示可操作数量，引导用户进行有效选择

### 4.5. 创建下载任务页 (/download-center/tasks/create)
- 布局:
  - 页面顶部：标题 "创建下载任务"。
  - 页面主体：结构化的表单区域。表单项应分组清晰，例如"基本信息"、"下载参数"等。
  - 参考Bilibili: 可以借鉴其投稿页面的表单布局和交互方式，确保用户输入流畅。
- 表单项:
  - 资源URL ( resource_url ): 文本输入框，必填。提供输入提示或格式要求说明。
  - 资源类型 ( resource_type ): 下拉选择框，选项包括 'hls', 'mp4', 'image'，必填。
  - 视频ID ( video_id ): 文本输入框，必填，是uuid类型。提供格式说明或输入校验提示。
  - 直播间ID ( liveroom_id ): 文本输入框，必填。
  - 直播间标题 ( liveroom_title ): 文本输入框，可选。
  - 直播间URL ( liveroom_url ): 文本输入框，可选。
  - 其他可能的参数 (根据后端创建任务API定义补充，如清晰度选择等)。
- 表单验证:
  - 对必填项进行前端验证，并实时显示验证错误信息。
  - 对URL格式进行基本验证。

- 提交操作:
  - "创建" 按钮：调用 POST /api/v1/download/tasks API。按钮应在提交过程中显示加载状态并禁用。
  - "取消" 按钮：返回任务列表页。
  - 提交成功后，显示成功提示，并跳转回任务列表页或新创建的任务详情页。
  - 提交失败时，显示错误提示（使用消息提示组件），并高亮出错的表单项。
- 用户引导: 对于 video_id 格式要求，可以提供一个示例或生成器，帮助用户输入正确的格式。
- 智能识别: 考虑是否可以根据输入的 resource_url 尝试自动识别 video_id , liveroom_id , liveroom_title , liveroom_url 等信息，减少用户输入负担。这需要后端或第三方库支持。
- 重复提交: 提交按钮在点击后应立即禁用，防止用户重复提交。

### 4.6. 下载任务详情页 (/download-center/tasks/:taskId)
- 布局:
  - 页面顶部：标题区域，显示 "任务详情" 和任务ID。
  - 页面主体：核心区域展示任务详细信息。可以采用分块或Tab页的方式组织信息。
  - 参考Bilibili: 可以借鉴其视频详情页的布局，将核心信息（状态、进度）放在显眼位置，其他信息（元数据、失败记录）放在下方或侧边区域，或通过Tab切换。
- 信息展示:
  - 基本信息块: 显示 DownloadTask 模型中的所有字段：ID ( id )、视频ID ( video_id )、直播间ID ( liveroom_id )、直播间标题 ( liveroom_title )、直播间URL ( liveroom_url )、原始URL ( resource_url )、资源类型 ( resource_type )、状态 ( status )、进度 ( progress )、重试次数 ( retry_count )、最后错误 ( last_error )、创建时间 ( created_at )、更新时间 ( updated_at )、完成时间 ( completed_at )。
  - 状态和进度应实时更新（通过轮询 GET /api/v1/download/tasks/{task_id} 或 WebSocket）。进度条和状态显示应与列表页保持一致。
  - last_error 字段在有错误时才显示，并可能需要展开/收起功能以避免占用过多空间。
- 操作按钮区域:
  - 与列表页的操作按钮类似 (开始下载、重试、取消)，根据当前任务状态动态显示/隐藏。按钮应醒目且易于点击。
  - **所有操作按钮必须异步执行，不阻塞用户界面，操作过程中显示加载状态。**
  - "开始下载" 按钮：调用开始下载API，仅在 pending 状态下可用。
  - "重试" 按钮：调用重试API，仅在 failed 或 cancelled 状态下可用。
  - "取消" 按钮：调用取消API，仅在 pending 或 processing 状态下可用。
  - "查看失败记录" 按钮：跳转到失败记录列表页 ( /download-center/tasks/:taskId/failures )。仅在 failed 或 partial_completed 状态下可用。
  - "单任务已下载视频" 按钮：跳转到 /download-center/tasks/:taskId/videos
- 失败记录 Tab/区域:
  - 如果采用Tab页布局，一个Tab用于展示基本信息，另一个Tab用于展示该任务关联的失败记录列表。
- 实时更新机制: 明确是采用定时轮询还是WebSocket。如果使用轮询，需要考虑轮询频率的动态调整，例如任务处于 processing 状态时频率高，其他状态频率低或停止轮询。如果使用WebSocket，需要处理连接断开和重连。
- 状态变化处理: 当任务状态发生变化时（例如从 processing 到 completed 或 failed ），界面应有明显的视觉反馈，并可能需要自动停止实时更新。
- 关联信息: 如果 download_task_id 在 DownloadedVideo 中有值，在任务详情页是否需要链接到关联的已下载视频详情页？（现仅支持单任务下视频列表）

### 4.7. 下载失败记录列表页 (/download-center/tasks/:taskId/failures)
- 布局:
  - 页面顶部：标题区域，显示 "任务 [任务ID] 的失败记录"。提供返回任务详情页的导航。
  - 页面主体：数据表格，展示失败记录列表。
  - 页面底部：分页控件。
- 数据表格:
  - 列: 失败ID ( id )、资源URL ( resource_url )、期望路径 ( expected_path )、资源类型 ( resource_type )、失败类型 ( failure_type )、错误信息 ( error_message )、重试次数 ( retry_count )、下次重试时间 ( next_retry_time )、状态 ( status )、创建时间 ( created_at )、更新时间 ( updated_at )、操作。
  - 操作列:
    - "重试": 调用 POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry API。**必须异步执行，操作过程中按钮显示加载状态。**
    - "放弃": 调用 POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon API。操作前应有确认提示。**必须异步执行，操作过程中按钮显示加载状态。**
  - 错误信息显示: error_message 字段可能较长，可以考虑截断显示，提供查看完整信息的选项（如Tooltip或Modal）。
- 分页与排序:
  - 实现基于后端API ( GET /api/v1/download/tasks/{task_id}/failures ) 的分页和排序功能。
- 错误信息可读性: error_message 可能包含技术细节，考虑是否需要对用户友好的错误描述进行映射或处理。
- 重试/放弃操作反馈: 用户点击重试或放弃后，该条失败记录的状态应立即更新，并给出操作结果提示。
- **异步操作要求:** 重试和放弃操作必须异步执行，点击后立即返回，不阻塞用户界面。操作过程中按钮显示加载状态并禁用，操作完成后自动更新失败记录状态。
- **状态同步:** 操作完成后自动刷新失败记录列表，确保界面显示最新状态。

### 4.8. 单任务下已下载视频列表页 (/download-center/tasks/:taskId/videos)
- 布局:
  - 页面顶部：标题 "已下载视频列表（当前任务）"。
  - 页面主体：数据表格或卡片列表，展示当前任务下的已下载视频列表。
  - 页面底部：分页控件。
- 数据表格/卡片项:
  - 核心信息: ID ( id )、视频ID ( video_id )、直播间ID ( liveroom_id )、资源类型 ( resource_type )、存储路径 ( storage_path )、文件大小 ( file_size )、分辨率 ( resolution )、格式 ( format )、时长 ( duration )、完成时间 ( download_end_time )。
  - 封面图: 如果 cover_url 或 cover_path 字段有值，在卡片中展示封面图。
  - 操作列/按钮:
    - "详情": 可扩展为弹窗或新页面展示视频详情。
- 分页与排序:
  - 实现基于后端API的分页和排序功能。
- 筛选与搜索:
  - 提供按视频ID、直播间ID、资源类型等进行筛选和搜索的功能。
- 文件大小/时长格式化: file_size (BIGINT) 需要转换为用户友好的单位（KB, MB, GB）。 duration (INT, 秒) 需要转换为时分秒格式。
- 封面图加载失败: 如果封面图URL无效或加载失败，需要显示一个默认占位图。

> **注意：已删除"全局已下载视频列表页"和"全局已下载视频详情页"相关内容。**

## 五、功能实现细节

#### 5.1 认证状态管理

#### 5.1.1. 认证Store设计
**跨服务跳转支持：**
- 所有需要跳转到用户服务的操作都通过`FRONTEND_USER_URL`常量构建完整URL
- 跳转前确保用户服务前端地址配置正确
- 支持开发、测试、生产环境的动态配置

// stores/auth.js 完整实现
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false,
    tokenExpiry: null,
    redirectPath: null
  }),
  
  getters: {
    isTokenValid: (state) => {
      // 实现Token有效性检查
    }
  },
  
  actions: {
    // 完整的actions实现
  }
})


```typescript
// 在认证Store中新增方法
actions: {
  // ... 现有方法 ...
  
  async initializeAuth() {
    const savedToken = localStorage.getItem('jwt_token');
    if (savedToken) {
      if (this.checkTokenExpiry()) {
        this.setToken(savedToken);
        // 从Token中解析用户信息
        this.parseUserFromToken(savedToken);
      } else {
        this.clearAuth();
      }
    }
  },
  
  checkTokenExpiry() {
    if (!this.token) return false;
    try {
      const payload = JSON.parse(atob(this.token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp > currentTime;
    } catch {
      return false;
    }
  },
  
  parseUserFromToken(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      this.user = {
        user_id: payload.user_id || payload.sub,
        username: payload.username,
        email: payload.email
      };
      this.tokenExpiry = payload.exp * 1000;
    } catch (error) {
      console.error('解析Token失败:', error);
      this.clearAuth();
    }
  },
  
  handleAuthRedirect() {
    const redirectPath = this.getRedirectPath();
    if (redirectPath) {
      this.clearRedirectPath();
      this.$router.push(redirectPath);
    } else {
      this.$router.push('/download-center/tasks');
    }
  },
  
  /**
   * 设置重定向路径
   */
  setRedirectPath(path) {
    this.redirectPath = path;
    localStorage.setItem('auth_redirect_path', path);
  },
  
  /**
   * 获取重定向路径
   */
  getRedirectPath() {
    return this.redirectPath || localStorage.getItem('auth_redirect_path');
  },
  
  /**
   * 清除重定向路径
   */
  clearRedirectPath() {
    this.redirectPath = null;
    localStorage.removeItem('auth_redirect_path');
  },
  
  /**
   * 处理认证后的重定向
   */
  handleAuthRedirect() {
    const redirectPath = this.getRedirectPath();
    
    if (redirectPath && redirectPath !== '/login') {
      console.log('重定向到:', redirectPath);
      this.clearRedirectPath();
      
      // 使用router实例进行导航
      const router = this.$router || window.$router;
      if (router) {
        router.push(redirectPath);
      } else {
        // 降级方案：直接修改location
        window.location.href = redirectPath;
      }
    } else {
      console.log('重定向到默认页面');
      
      const router = this.$router || window.$router;
      if (router) {
        router.push('/download-center/tasks');
      } else {
        window.location.href = '/download-center/tasks';
      }
    }
  },
  
  /**
   * 强制重新认证
   */
  forceReauth(targetPath) {
    this.clearAuth();
    this.setRedirectPath(targetPath);
    
    import('@/constants/api').then(({ LOGIN_URL }) => {
      const originDomain = window.location.origin.replace('http://', '').replace('https://', '');
      const loginUrlWithCallback = `${LOGIN_URL}?external_callback=true&origin=${originDomain}`;
      window.location.href = loginUrlWithCallback;
    });
  },
  
  /**
   * 登出并跳转到登录页面
   */
  logout() {
    this.clearAuth();
    this.clearRedirectPath();
    // 使用配置文件中的登录URL，而不是硬编码
    import('@/constants/api').then(({ LOGIN_URL }) => {
      window.location.href = LOGIN_URL;
    });
  }
}
```


#### 5.1.2. 初始化认证状态

```typescript
// main.ts
const app = createApp(App);
const authStore = useAuthStore();

// 应用启动时初始化认证状态
await authStore.initializeAuth();

app.mount('#app');
```

### 5.2. API交互
- 封装API请求函数，统一处理请求头、错误处理和响应格式解析。
- 使用异步请求 ( async/await )。
- 在请求发送时显示加载状态，请求完成后隐藏。
- 根据后端统一响应格式（ `媒体下载服务设计文档v2.md` 5.1.1），判断请求是否成功 ( code == 200 )，成功则处理 data ，失败则提取 message 和 code 进行错误提示。
- 处理分页请求参数 ( page , size , sort ) 和解析分页响应 ( total , page , size , items )。
- 请求取消: 在组件卸载或用户切换页面时，应取消正在进行的API请求，避免内存泄漏和不必要的资源消耗。
- 错误码处理: 除了通用的错误提示，是否需要针对特定的后端错误码进行特殊处理或更详细的提示？
- 认证/授权: 如何处理用户认证（如Token）和API请求的授权？这部分通常是前端框架或全局API封装层需要考虑的。
  {{ edit_2 }}
- API 版本控制: 考虑API版本变化时的兼容性处理。
- 请求重试机制: 对于网络不稳定等情况，是否需要在前端实现请求的自动重试？


### 5.2.1. HTTP拦截器配置

**请求拦截器：**
```javascript
// 请求拦截器 - 自动添加Authorization头
import { BASE_API_URL } from '@/constants/api';

// 创建axios实例时使用配置的URL
const request = axios.create({
  baseURL: BASE_API_URL,  // 使用配置文件中的API地址
  timeout: API_TIMEOUT,   // 使用配置文件中的超时时间
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
```

**响应拦截器：**
```javascript
// 响应拦截器 - 处理认证失败和成功状态码
import { LOGIN_URL } from '@/constants/api';

request.interceptors.response.use(
  (response) => {
    // 处理成功响应
    const { code, message, data } = response.data;
    
    // 支持多种成功状态码：200(成功)、201(创建成功)、202(接受处理)、204(无内容)
    if (code >= 200 && code < 300) {
      return data; // 成功时直接返回data部分
    } else {
      // 业务错误
      console.error('业务错误:', code, message);
      ElMessage.error(message || '请求失败');
      return Promise.reject(new Error(message || '请求失败'));
    }
  },
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore();
      
      // 清除认证状态
      authStore.clearAuth();
      
      // 保存当前路径
      const currentPath = window.location.pathname;
      authStore.setRedirectPath(currentPath);
      
      // 跳转到外部登录页面
      const originDomain = window.location.origin.replace('http://', '').replace('https://', '');
      const loginUrlWithCallback = `${LOGIN_URL}?external_callback=true&origin=${originDomain}`;
      
      console.log('API认证失败，跳转登录');
      window.location.href = loginUrlWithCallback;
    }
    return Promise.reject(error);
  }
);
```

**重要说明：**
- 响应拦截器必须支持所有2xx状态码（200-299），包括201(创建成功)、202(接受处理)、204(无内容)等
- 避免只检查code === 200导致的业务逻辑错误
- 确保前端能正确处理后端返回的各种成功状态码


### 5.2. 状态管理
- 在全局状态中存储下载任务列表、单个任务详情、失败记录列表、已下载视频列表等。
- 当从后端获取到新的数据时，更新状态。
- 对于列表页，实现分页和排序的状态管理。
- 对于任务详情页，实现定时刷新逻辑，更新任务状态和进度。
- 状态结构设计: 状态树的设计应考虑模块化和可扩展性，避免状态过于扁平或耦合。
- 数据同步: 如何确保不同页面或组件之间的数据同步？例如，在详情页更新了任务状态，列表页如何反映这个变化？（WebSocket或全局事件总线可能是解决方案）。
- 缓存策略: 是否需要对某些不经常变化的数据进行缓存，减少API请求？
  {{ edit_3 }}
- Loading/Error 状态管理: 除了数据本身，状态管理还需要包含数据加载状态 ( loading: boolean ) 和错误状态 ( error: any )，以便在UI中正确展示加载中或错误信息。
- 数据范式化: 如果数据之间存在复杂关联（如任务与失败记录），考虑使用范式化存储数据，避免数据冗余和不一致。
### 5.3. 实时进度更新
- 任务列表和详情页需要实时显示下载进度。
- 可以采用定时轮询后端API ( GET /api/v1/download/tasks 或 GET /api/v1/download/tasks/{task_id} ) 的方式获取最新进度。轮询间隔可以根据任务状态调整（例如， processing 状态下轮询更频繁）。
- 更优的方案是后端支持WebSocket或Server-Sent Events，前端建立连接并监听任务状态和进度更新事件。
- WebSocket/SSE 实现细节: 如果采用WebSocket/SSE，需要详细设计前端的连接管理（连接、断开、重连）、消息接收和处理逻辑。如何将接收到的消息更新到对应的任务状态？
- 轮询优化: 如果使用轮询，除了动态调整频率，还可以考虑长轮询（Long Polling）或只在用户当前查看的页面进行轮询。
  {{ edit_4 }}
- 心跳机制: 如果使用WebSocket，需要实现心跳机制来检测连接是否仍然有效，并处理断开重连。
- 消息格式: 明确WebSocket/SSE推送的消息格式，包含哪些字段（如任务ID、最新状态、进度等）。
- 权限控制: 确保用户只能接收到自己有权限的任务的更新。

### 5.3.1. 异步下载操作设计

**异步下载核心要求：**
- **非阻塞操作：** 点击下载按钮后立即返回，不阻塞用户界面操作
- **按钮状态管理：** 下载过程中按钮禁用，显示加载状态，防止重复点击
- **实时状态更新：** 通过轮询或WebSocket更新任务状态，无需用户手动刷新
- **完成通知：** 下载完成后自动给用户通知，提升用户体验

**技术实现要点：**
```javascript
// 异步下载按钮处理示例
const handleStartDownload = async (taskId) => {
  try {
    // 1. 立即禁用按钮，显示加载状态
    startingTasks.value.add(taskId);
    
    // 2. 显示操作提示
    ElMessage.info('正在启动下载任务，请稍候...');
    
    // 3. 异步执行，不阻塞用户操作
    downloadStore.startTask(taskId)
      .then(() => {
        ElMessage.success('任务开始下载成功');
        fetchTasks(); // 刷新状态
      })
      .catch((error) => {
        ElMessage.error('启动下载失败，请重试');
        fetchTasks(); // 刷新状态
      })
      .finally(() => {
        startingTasks.value.delete(taskId); // 恢复按钮状态
      });
      
  } catch (error) {
    // 处理确认对话框取消等错误
    if (error !== 'cancel') {
      console.error('操作失败:', error);
    }
  }
};
```

**按钮状态管理规范：**
- 使用 `Set` 数据结构管理正在操作的任务ID
- 按钮加载状态：`:loading="startingTasks.has(row.id)"`
- 按钮禁用状态：`:disabled="startingTasks.has(row.id)"`
- 操作完成后自动恢复按钮状态

**实时状态更新机制：**
- 轮询间隔：任务进行中时5秒，其他状态时10秒
- 智能轮询：只在用户当前查看的页面进行轮询
- 状态变化检测：通过 `watch` 监听任务状态变化
- 自动通知：状态变为完成/失败时自动显示通知

**用户通知系统：**
- 成功通知：任务完成时显示绿色成功提示
- 失败通知：任务失败时显示红色错误提示，包含重试建议
- 进度通知：长时间任务提供进度更新提示
- 浏览器通知：支持浏览器原生通知（用户授权后）
### 5.4. 错误处理与提示
- 捕获API请求失败（网络错误、超时等）和后端返回的业务错误 ( code != 200 )。
- 使用UI组件库提供的消息提示组件（如Toast、Notification）向用户显示错误信息 ( response.message )。
- 在表单提交失败时，在表单下方或相关字段旁显示错误提示。
- 对于下载失败的任务或失败记录，在详情页或失败记录列表中清晰展示 failure_type 和 error_message 。
- 全局错误捕获: 实现一个全局的错误处理机制，捕获未预料的JavaScript错误或API错误，并进行上报（如果需要）。
- 用户反馈: 错误提示应清晰、简洁，避免技术术语。对于可操作的错误（如网络断开），提供重试按钮。
- 日志记录: 在前端记录关键的错误信息，方便调试和问题排查。
  {{ edit_5 }}
- 错误分类: 将错误分为网络错误、业务错误、前端运行时错误等，针对不同类型错误采用不同的处理和提示方式。
- 用户操作回滚: 对于某些操作（如取消任务），如果后端返回失败，前端需要将状态回滚到操作前的状态。
### 5.5. 路径处理 (前端展示)

- 后端负责跨平台路径生成和处理。前端仅负责展示后端返回的 storage_path 和 cover_path 。
- 路径复制功能: 考虑为 `storage_path` 提供一键复制到剪贴板的功能，方便用户在本地文件管理器中打开。

### 5.6. 时间戳处理

- 后端返回的时间戳是ISO 8601格式。前端需要将其转换为用户友好的本地时间格式进行展示。
{{ edit_1 }}
- **时区考虑:** 转换时间时，需要考虑用户所在的时区。通常使用JavaScript的 `Date` 对象或日期处理库（如 `moment.js`, `dayjs`）进行转换。
- **格式化选项:** 提供不同的时间格式选项，例如"刚刚"、"X分钟前"、"今天 HH:mm"、"YYYY-MM-DD HH:mm"等，增强用户体验。对于专业用户，精确到秒的格式（YYYY-MM-DD HH:mm:ss）可能更重要。
- **日期库选择:** 推荐使用 Day.js，它比 Moment.js 更轻量，且API相似。

### 5.8. 异步操作与用户体验优化

#### 5.8.1. 异步下载操作规范

**操作流程设计：**
1. **用户点击操作按钮** → 立即显示确认对话框
2. **用户确认操作** → 按钮立即禁用，显示加载状态
3. **异步执行操作** → 不阻塞用户界面，用户可进行其他操作
4. **操作完成** → 自动更新状态，显示结果通知，恢复按钮状态

**按钮状态管理：**
- 每个操作按钮必须支持 `loading` 和 `disabled` 状态
- 使用响应式数据管理正在操作的任务集合
- 操作完成后自动清理状态，避免按钮永久禁用

**实时状态监控：**
- 实现任务状态变化监听器
- 状态变化时自动更新界面和显示通知
- 支持批量状态更新，避免频繁的API调用

#### 5.8.2. 用户通知规范

**通知类型：**
- **操作成功：** 绿色成功提示，包含操作结果摘要
- **操作失败：** 红色错误提示，包含错误原因和解决建议
- **进度更新：** 蓝色信息提示，显示当前操作状态
- **系统提醒：** 黄色警告提示，提醒用户注意事项

**通知时机：**
- 任务状态变化时（pending → processing → completed/failed）
- 用户操作完成后（创建、删除、重试等）
- 系统异常发生时（网络错误、认证失败等）
- 长时间操作进度更新时

**通知实现：**
- 使用 Element Plus 的 `ElMessage` 组件
- 支持自动消失和手动关闭
- 重要通知可配置为持久显示
- 考虑添加浏览器原生通知支持

### 批量操作实现规范

**批量操作核心要求：**
- **状态感知：** 根据任务当前状态智能判断是否可执行批量操作
- **并行执行：** 所有任务操作并行执行，提高操作效率
- **独立状态管理：** 每个任务的操作状态独立管理，互不影响
- **实时反馈：** 操作过程中实时更新界面状态，提供操作进度

**技术实现要点：**
```javascript
// 批量操作状态管理示例
const batchStarting = ref(false);
const batchRetrying = ref(false);
const selectedTasks = ref([]);

// 计算可操作的任务数量
const startableTasksCount = computed(() => {
  return selectedTasks.value.filter(task => canStart(task.status)).length;
});

const retryableTasksCount = computed(() => {
  return selectedTasks.value.filter(task => canRetry(task.status)).length;
});

// 按钮启用条件
const hasStartableTasks = computed(() => startableTasksCount.value > 0);
const hasRetryableTasks = computed(() => retryableTasksCount.value > 0);
```

**状态变化处理：**
- 实现任务状态变化监听器，自动更新批量操作按钮状态
- 当选中任务状态发生变化时，重新计算可操作任务数量
- 支持动态选择：用户可以在操作过程中继续选择/取消选择任务
- 状态同步：确保批量操作按钮状态与选中任务的实际状态保持一致

**错误处理策略：**
- 单个任务操作失败不影响其他任务的执行
- 提供详细的操作结果报告，包括成功和失败的详细信息
- 失败任务提供重试选项，支持快速重新操作
- 网络异常时提供重试机制，确保操作的可靠性

### 5.7. 数据验证

- 在创建任务表单提交前，进行前端数据验证，包括必填项、URL格式、 video_id 格式等，减少无效请求。
- 后端验证: 强调前端验证是辅助性的，后端必须进行严格的数据验证，前端不应完全依赖前端验证。
- 实时验证: 输入框失焦或内容变化时进行实时验证，及时给用户反馈。
- 复杂验证规则: 对于 `video_id` 格式等复杂规则，使用正则表达式或专门的验证库。
{{ edit_2 }}
- **验证规则定义:** 明确列出每个需要验证的字段及其验证规则（如 `resource_url` 必须是有效的URL，`video_id` 必须匹配 `{liveroom_id}_{uuid4后缀}` 的正则等）。
- **用户友好提示:** 验证失败时的错误提示信息应清晰、具体，指导用户如何修正输入。

### 5.9. 用户主页与下载中心的集成

- 用户主页导航栏中添加"下载中心"按钮，点击后跳转到下载中心页面 (`/download-center`)。
- 按钮设计:
  - 使用橙色背景使按钮突出，增加可见性
  - 配有下载图标，提高识别度
  - 放置在导航栏右侧，与其他功能按钮并排，位置合理
- 跳转逻辑:
  - 点击按钮执行 `goToDownloadPage()` 方法
  - 该方法通过 Vue Router 导航到 `/download-center` 路径
  - 默认显示下载任务列表页面 (`/download-center/tasks`)
- 用户体验考虑:
  - 按钮点击后有明显的视觉反馈
  - 跳转流畅，保持一致的界面风格
  - 在下载中心可以通过左侧菜单轻松切换不同功能

## 六、用户体验优化

- 加载指示: 在进行API请求时，显示加载动画或禁用相关按钮，防止用户重复操作。
- 空状态: 当任务列表、失败记录列表或已下载视频列表为空时，显示友好的提示信息。
- 操作反馈: 用户执行暂停、恢复、取消、重试等操作后，及时更新界面状态，并给出操作成功的提示。
- 响应式设计: 考虑不同屏幕尺寸的设备，确保界面在桌面和移动端都能正常显示和使用。
- 可访问性: 遵循Web可访问性标准，确保所有用户都能方便地使用应用。
- 国际化 (i18n): 如果应用需要支持多种语言，考虑实现国际化。
{{ edit_3 }}
- **键盘导航:** 确保用户可以使用键盘进行导航和操作，特别是对于专业用户，键盘操作效率可能更高。
- **快捷键:** 考虑为常用操作（如创建任务、刷新列表）设置快捷键。
- **通知系统:** 对于任务状态变化（如完成、失败），考虑使用浏览器通知或应用内通知进行提醒。
- **用户偏好设置:** 未来可以考虑增加用户偏好设置，如列表每页显示数量、时间格式等。
- **性能感知:** 优化前端渲染性能，减少不必要的重绘和回流。对于长列表，使用虚拟滚动。

- **异步操作体验:** 所有耗时操作必须异步执行，不阻塞用户界面
- **操作状态反馈:** 实时显示操作进度和状态变化，让用户了解当前操作进展
- **智能轮询:** 根据任务状态动态调整轮询频率，减少不必要的网络请求
- **批量操作支持:** 支持批量选择任务进行批量操作，提升操作效率

- **认证状态反馈:** 在认证过程中显示加载状态，认证失败时显示友好的错误提示。
- **无感知认证:** Token自动管理，用户无需手动处理认证状态。
- **登录后回跳:** 用户登录成功后自动跳转到登录前尝试访问的页面。
- **权限友好提示:** 当用户访问无权限的资源时，提供清晰的错误提示和解决方案。

## 七、UI/UX 设计规范 (参考Bilibili并专业化)

- 整体风格: 简洁、专业、信息密度适中。避免过多花哨的动画和装饰。
- 色调: 采用偏冷色调或中性色调为主，如蓝色、灰色、白色。使用少量强调色（如绿色表示成功，红色表示失败，黄色表示警告）来突出状态信息。参考医疗或科技类网站的常用配色。
- 布局:
  - 顶部导航/侧边导航: 提供清晰的导航结构，方便用户在不同页面（任务列表、已下载视频等）之间切换。
  - 内容区域: 采用栅格系统布局，确保在不同分辨率下内容都能良好展示。列表页可采用表格或卡片布局，详情页采用分块布局。
  - 信息层级: 使用不同的字体大小、粗细和颜色来区分标题、正文、辅助信息等，确保信息易于扫描和理解。
- 组件:
  - 表格/列表: 列头清晰，数据对齐。重要状态信息使用标签或图标。操作按钮分组或使用下拉菜单。
  - 进度条: 简洁明了，实时更新。颜色随状态变化（如进行中蓝色，完成绿色，失败红色）。
  - 表单: 标签与输入框对齐，必填项有明确标记。输入验证提示友好且及时。
  - 按钮: 主要操作按钮醒目，次要操作按钮样式区分。禁用状态清晰可见。操作前需要确认的，使用Modal或Popconfirm。
  - 图标: 使用简洁、易于理解的图标，辅助文字说明。
- 字体: 选择易于阅读的无衬线字体，如 Arial, Helvetica, 或常用的中文字体（如思源黑体）。
- 交互反馈:
  - 加载状态: 按钮点击后显示加载中，列表/详情页数据加载时显示Loading Spinner。
  - 操作结果: 使用全局消息提示（Toast/Notification）反馈操作成功或失败。
  - 鼠标悬停: 列表项、按钮等可交互元素在鼠标悬停时有视觉反馈。
- 错误提示: 错误信息应具体、友好，并提供可能的解决方案（如重试）。表单验证错误应在对应输入框下方实时显示。
- 数据可视化: 考虑使用简单的图表（如果需要）来展示下载趋势或统计信息，但保持专业性。
{{ edit_4 }}
- **专业性体现:** 在UI细节上，避免过于娱乐化的元素。例如，图标设计应偏向扁平、线条简洁风格；配色应稳重；文字描述应准确、专业。
- **信息密度:** 考虑到医生用户可能需要快速浏览大量信息，列表页的信息密度可以适当提高，但要保证可读性。关键信息（如状态、进度、错误）应突出显示。
- **操作流程:** 简化创建任务、管理任务的操作流程，减少不必要的步骤。
- **帮助与文档:** 在界面中提供必要的帮助信息或链接到详细的使用文档，特别是对于复杂的字段（如 `video_id` 格式）或操作。

### 7.1. 异步操作UI设计规范

**按钮状态设计：**
- **正常状态：** 标准按钮样式，可点击
- **加载状态：** 显示加载动画，按钮禁用，防止重复操作
- **完成状态：** 短暂显示成功图标，然后恢复正常状态
- **错误状态：** 显示错误图标，按钮可重试

**加载指示器：**
- 使用 Element Plus 的 `v-loading` 指令
- 加载动画简洁明了，不干扰用户注意力
- 提供加载状态文字说明，告知用户当前操作进度

**状态反馈：**
- 操作结果立即反馈，避免用户等待
- 使用颜色和图标区分不同状态
- 状态变化有平滑的过渡动画
- 重要状态变化提供声音或视觉提醒

**异步操作流程设计：**
- **操作前：** 显示确认对话框，说明操作内容和影响
- **操作中：** 按钮显示加载状态，禁用重复操作
- **操作后：** 显示结果通知，自动更新相关数据
- **异常处理：** 错误时显示友好提示，提供重试选项

### 批量操作UI设计规范

**批量选择界面：**
- 表格选择列使用标准复选框样式，支持单选和多选
- 表头提供全选/反选功能，提升批量操作效率
- 选中状态有明显的视觉反馈，如行高亮、复选框勾选等

**批量操作按钮设计：**
- 按钮位置：放置在操作区域顶部，与单个操作按钮分组
- 按钮样式：使用不同的颜色区分下载（绿色）和重试（橙色）
- 状态指示：按钮文本显示可操作的任务数量，如"批量下载 (3)"
- **禁用状态样式：**
  - 不可操作时按钮显示为灰色，但保持可见
  - 使用透明度变化来区分不同状态
  - 确保按钮在禁用状态下仍然可见，提供一致的用户体验

**操作反馈设计：**
- 确认对话框：显示操作摘要，包括任务数量、状态分布等
- 进度指示：操作过程中显示进度条或加载动画
- 结果展示：操作完成后显示结果统计，使用表格或列表形式
- 错误详情：失败任务提供展开/收起功能，显示具体错误信息


## 八、测试策略 (新增)

为了确保前端应用的质量和稳定性，需要制定详细的测试策略。

- **单元测试:** 对核心的工具函数、API服务封装、状态管理模块、Vuex/Pinia Actions/Mutations/Getters 等进行单元测试，确保其逻辑正确性。
- **组件测试:** 对独立的UI组件进行测试，验证其渲染、交互和props/events是否符合预期。
- **页面测试:** 对关键页面（如任务列表页、创建任务页）进行集成测试，模拟用户操作流程，验证页面功能和数据流是否正常。
- **端到端测试 (E2E):** 使用 Cypress 或 Playwright 等工具，模拟真实用户在浏览器中的完整操作路径，测试整个应用的流程，包括登录（如果需要）、创建任务、查看列表、操作任务等。
- **性能测试:** 测试页面加载时间、列表渲染性能、实时更新的延迟等，确保满足性能目标。
- **兼容性测试:** 在不同的浏览器和设备上测试应用，确保兼容性。
- **可访问性测试:** 使用工具或手动检查，确保应用符合可访问性标准。

## 九、部署与维护考虑 (新增)

- **构建流程:** 定义清晰的前端构建流程，包括代码检查、单元测试、打包、压缩、版本控制等。
- **部署方式:** 考虑应用的部署方式（如静态文件托管、Docker容器等），以及如何与后端服务集成。
- **日志与监控:** 集成前端错误日志收集和性能监控工具，及时发现和解决线上问题。
- **版本管理:** 采用语义化版本控制，方便管理和回滚。
- **持续集成/持续部署 (CI/CD):** 建立CI/CD流水线，自动化测试和部署过程，提高开发效率和部署质量。

## 十、安全性考虑 (新增)

- **XSS 防范:** 对用户输入和后端返回的数据进行严格的过滤和转义，防止跨站脚本攻击。
- **CSRF 防范:** 在关键的写操作API请求中，使用CSRF Token或其他机制进行防护。
- **认证与授权:** 确保只有经过认证和授权的用户才能访问和操作数据。前端需要正确处理Token的存储、传递和刷新。
- **敏感信息处理:** 避免在前端代码或日志中存储和传输敏感信息。
- **依赖安全:** 定期检查和更新项目依赖，避免使用存在已知安全漏洞的库。
- **HTTPS:** 强制使用HTTPS协议，保证数据传输安全。

## 十一、认证与安全

### 11.1. JWT Token管理

- **Token存储:** 使用localStorage存储JWT Token，应用启动时自动检查和加载
- **Token验证:** 每次API请求前检查Token有效性，过期时自动清理
- **自动续期:** 根据Token过期时间提前提示用户或静默续期（如果后端支持）

### 11.2. 安全策略

- **XSS防护:** 对所有用户输入和API返回数据进行严格的过滤和转义
- **Token安全:** JWT Token仅在HTTPS环境下传输，避免在控制台日志中输出
- **会话管理:** 用户主动登出时清理所有本地认证信息
- **路由保护:** 所有需要认证的路由都通过路由守卫进行保护

### 11.3. 错误处理

- **401未认证:** 自动跳转登录页面，保存当前路径便于登录后返回
- **403无权限:** 显示权限不足提示，引导用户联系管理员
- **Token过期:** 自动清理认证状态并跳转登录页面
- **网络错误:** 区分认证错误和网络错误，提供不同的用户提示

---