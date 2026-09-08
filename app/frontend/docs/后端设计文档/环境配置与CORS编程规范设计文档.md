# 环境配置与CORS编程规范

**项目**: vzan_simul_frontend  
**版本**: 1.0  
**最后更新**: 2025-01-XX

---

## 📋 目录

1. [环境配置规范](#一环境配置规范)
2. [CORS配置规范](#二cors配置规范)
3. [登录跳转规范](#三登录跳转规范)
4. [配置文件规范](#四配置文件规范)
5. [配置安全性规范](#五配置安全性规范) ⚠️ **重要**
6. [代码组织规范](#六代码组织规范)
7. [安全验证规范](#七安全验证规范) ⚠️ **P0 优先级**
8. [最佳实践](#八最佳实践)
9. [检查清单](#九检查清单)
10. [常见问题](#十常见问题)

---

## 一、环境配置规范

### 1.1 配置文件结构

#### ✅ 标准结构

```javascript
// public/config.js
window.__APP_CONFIG__ = {
  // ==========================================
  // 环境切换开关（修改这里即可切换环境）
  // ==========================================
  USE_LOCAL_DEV: true,  // true: 本地开发环境  false: 生产环境

  // ==========================================
  // 本地开发环境配置
  // ==========================================
  LOCAL_DEV: {
    // API配置
    VITE_BASE_API_URL: 'http://localhost:8000/api/v1',
    VITE_AUTH_API_URL: 'http://localhost:8002/',
    
    // 前端配置
    VITE_LOGIN_URL: 'http://localhost:5174/#/pages/auth/login',
    VITE_FRONTEND_USER_URL: 'http://localhost:5174',
    VITE_APP_BASE_PATH: '/live-center',
    
    // CORS配置
    VITE_CORS_ORIGINS: [
      'http://localhost:5175',
      'http://127.0.0.1:5175',
      'http://localhost:5174',
      'http://127.0.0.1:5174'
    ],
    VITE_CORS_CREDENTIALS: true,
    
    // 其他配置
    VITE_APP_TITLE: '直播SaaS平台(本地开发)',
    VITE_API_TIMEOUT: '30000',
    VITE_APP_ENV: 'development',
    VITE_DEBUG: true,
  },

  // ==========================================
  // 生产环境配置
  // ==========================================
  PRODUCTION: {
    // API配置
    VITE_BASE_API_URL: 'https://mp.dayilive.com/api/core/',
    VITE_AUTH_API_URL: 'https://mp.dayilive.com/api/users/',
    
    // 前端配置
    VITE_LOGIN_URL: 'https://mp.dayilive.com/#/pages/auth/login',
    VITE_FRONTEND_USER_URL: 'https://mp.dayilive.com',
    VITE_APP_BASE_PATH: '/live-center',
    
    // CORS配置
    VITE_CORS_ORIGINS: [
      'https://mp.dayilive.com',
      'https://www.mp.dayilive.com'
    ],
    VITE_CORS_CREDENTIALS: true,
    
    // 其他配置
    VITE_APP_TITLE: '直播SaaS平台',
    VITE_API_TIMEOUT: '30000',
    VITE_APP_ENV: 'production',
    VITE_DEBUG: false,
  },
};

// 自动选择配置
window.__ENV = window.__APP_CONFIG__.USE_LOCAL_DEV
  ? window.__APP_CONFIG__.LOCAL_DEV
  : window.__APP_CONFIG__.PRODUCTION;
```

### 1.2 环境判断规范

#### ✅ 正确方式：使用统一工具函数（必须包含 fallback 逻辑）

```typescript
// src/utils/env.ts
/**
 * 判断是否为本地开发环境
 * ⚠️ 重要：必须包含 fallback 逻辑，防止 config.js 未加载时返回错误值
 */
export const isLocalDev = (): boolean => {
  if (typeof window === 'undefined') return false;
  
  // 优先使用 config.js 中的 USE_LOCAL_DEV
  if ((window as any).__APP_CONFIG__?.USE_LOCAL_DEV !== undefined) {
    return !!(window as any).__APP_CONFIG__?.USE_LOCAL_DEV;
  }
  
  // ⚠️ Fallback：如果 config.js 未加载，根据当前 URL 路径判断
  // 本地开发环境：base = '/'，pathname 通常是 '/'
  // 生产环境：base = '/live-center/'，pathname 包含 '/live-center'
  // 这样可以避免在 config.js 加载前调用 buildCallbackUrl 时错误添加 /live-center
  const pathname = window.location.pathname;
  return pathname === '/' || !pathname.includes('/live-center');
};

// 使用示例
import { isLocalDev } from '@/utils/env';

if (isLocalDev()) {
  console.log('当前是本地开发环境');
} else {
  console.log('当前是生产环境');
}
```

**⚠️ 关键注意事项**：
- **必须包含 fallback 逻辑**：如果 `config.js` 未加载，`window.__APP_CONFIG__` 为 `undefined`，直接返回 `false` 会导致 `buildCallbackUrl` 错误添加 `/live-center`
- **Fallback 判断逻辑**：根据 `window.location.pathname` 判断，本地开发环境通常是 `/`，生产环境包含 `/live-center`
- **时机问题**：`buildCallbackUrl` 可能在 `config.js` 加载前被调用（例如在 `store/auth.ts` 的初始化阶段），因此 fallback 逻辑至关重要

**📌 关于本地开发环境的说明**：
- **本地开发环境**（`USE_LOCAL_DEV: true`）：
  - `vite.config.ts` 中 `base = '/'`（通过端口区分不同前端，不需要子路径）
  - 端口区分：`localhost:5175` → `vzan_simul_frontend`，`localhost:5174` → `user_service_frontend`
  - `pathname` 通常是 `/`（因为 `base = '/'`）
- **生产环境**（`USE_LOCAL_DEV: false`）：
  - `vite.config.ts` 中 `base = '/live-center/'`（部署在子路径下）
  - `pathname` 包含 `/live-center`（因为 `base = '/live-center/'`）

#### ❌ 错误方式：不要直接访问内部实现

```typescript
// ❌ 错误：直接访问 __APP_CONFIG__
const isLocalDev = (window as any).__APP_CONFIG__.USE_LOCAL_DEV;

// ❌ 错误：使用 VITE_APP_ENV 判断
const isLocalDev = window.__ENV.VITE_APP_ENV === 'development';

// ❌ 错误：在每个文件中重复判断逻辑
if (typeof window !== 'undefined' && (window as any).__APP_CONFIG__) {
  isLocalDev = !!(window as any).__APP_CONFIG__.USE_LOCAL_DEV;
}
```

### 1.3 配置读取规范

#### ✅ 正确方式：使用统一工具函数

```typescript
// src/utils/env.ts
export const getEnv = (key: string, defaultValue: string = ''): string => {
  // 优先使用 window.__ENV（运行时配置）
  const runtimeEnv = (typeof window !== 'undefined' 
    ? (window as any).__ENV?.[key] 
    : undefined);
  
  // 回退到 import.meta.env（Vite 构建时注入）
  const viteEnv = (import.meta as any)?.env?.[key];
  
  // 返回优先级：window.__ENV > import.meta.env > 默认值
  return runtimeEnv || viteEnv || defaultValue;
};

// 使用示例
import { getEnv } from '@/utils/env';

const apiUrl = getEnv('VITE_BASE_API_URL', 'http://localhost:8000/api/v1');
const loginUrl = getEnv('VITE_LOGIN_URL', 'http://localhost:5174/#/pages/auth/login');
```

#### ❌ 错误方式：不要直接访问 window.__ENV

```typescript
// ❌ 错误：直接访问 window.__ENV
const apiUrl = (window as any).__ENV.VITE_BASE_API_URL;

// ❌ 错误：没有回退逻辑
const apiUrl = window.__ENV?.VITE_BASE_API_URL || '';
```

### 1.4 config.js 加载规范

#### ✅ 正确方式：使用绝对路径 `/config.js`

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <!-- ... -->
  </head>
  <body>
    <div id="app"></div>
    <!-- ✅ 使用绝对路径 /config.js，Vite 会将 public/config.js 复制到 dist 根目录 -->
    <!-- 无论 base 配置如何，/config.js 都指向根目录的 config.js -->
    <script src="/config.js"></script>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

**⚠️ 重要说明**：
- Vite 会将 `public/config.js` 复制到 `dist/config.js`（根目录）
- 无论 `base` 配置是 `/` 还是 `/live-center/`，`/config.js` 都指向根目录
- 如果使用 `./config.js`，在 base 为 `/live-center/` 时会变成 `/live-center/config.js`，可能找不到
- 因此使用 `/config.js` 绝对路径是正确的

**📌 关于本地开发环境的路径说明**：
- **本地开发环境**（`USE_LOCAL_DEV: true`）：
  - `vite.config.ts` 中 `base = '/'`（开发环境）
  - 通过**端口区分**不同前端模块：
    - `localhost:5175` → `vzan_simul_frontend`（直播前端）
    - `localhost:5174` → `user_service_frontend`（用户前端）
  - 访问 `http://localhost:5175/config.js` 正确（因为 `base = '/'`）
- **生产环境**（`USE_LOCAL_DEV: false`）：
  - `vite.config.ts` 中 `base = '/live-center/'`（生产环境）
  - 但 `/config.js` 仍然指向根目录（因为 Vite 将 `public/config.js` 复制到 `dist/config.js`）
  - 访问 `https://mp.dayilive.com/config.js` 正确

**⚠️ vite.config.ts 必须添加 `serve-config-js` 插件**：
- 在开发环境中，必须添加 `serve-config-js` 插件，确保 `/config.js` 能正确加载
- 不要使用 `ignore-config-js-module` 插件，它会错误地拦截所有请求
- 详细说明请参考《代码重构整改方案.md》第 2.1 节和第 9.1 节

#### ❌ 错误方式：使用相对路径

```html
<!-- ❌ 错误：使用相对路径在 base 为 '/live-center/' 时会失败 -->
<script src="./config.js"></script>
```

---

## 二、CORS配置规范

### 2.1 CORS配置集中管理

#### ✅ 正确方式：在 config.js 中配置

```javascript
// public/config.js
LOCAL_DEV: {
  // CORS配置
  VITE_CORS_ORIGINS: [
    'http://localhost:5175',
    'http://127.0.0.1:5175',
    'http://localhost:5174',
    'http://127.0.0.1:5174'
  ],
  VITE_CORS_CREDENTIALS: true,
}

PRODUCTION: {
  // CORS配置
  VITE_CORS_ORIGINS: [
    'https://mp.dayilive.com',
    'https://www.mp.dayilive.com'
  ],
  VITE_CORS_CREDENTIALS: true,
}
```

#### ❌ 错误方式：在 vite.config.ts 中硬编码

```typescript
// ❌ 错误：硬编码CORS配置
proxyRes.headers['Access-Control-Allow-Origin'] = '*';
proxyRes.headers['Access-Control-Allow-Credentials'] = 'true';
```

### 2.2 CORS配置读取

#### ✅ 正确方式：从 config.js 读取

```typescript
// src/utils/cors.ts
import { getEnv } from './env';

export const getCorsConfig = () => {
  const originsStr = getEnv('VITE_CORS_ORIGINS', '');
  const origins = originsStr
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
  
  const credentials = getEnv('VITE_CORS_CREDENTIALS', 'false') === 'true';
  
  return { origins, credentials };
};

// vite.config.ts
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { getCorsConfig } from './src/utils/cors';

const corsConfig = getCorsConfig();

export default defineConfig({
  plugins: [
    // ... 其他插件 ...
    
    // ⚠️ 必须添加：确保 /config.js 作为静态文件正确提供服务
    // 不要使用 ignore-config-js-module 插件，它会错误地拦截所有请求
    {
      name: 'serve-config-js',
      configureServer(server) {
        // 在 Vite 内置中间件之前添加，确保优先处理
        server.middlewares.use((req, res, next) => {
          if (req.url === '/config.js') {
            try {
              const configPath = resolve(__dirname, 'public/config.js');
              const content = readFileSync(configPath, 'utf-8');
              res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
              res.setHeader('Cache-Control', 'no-cache');
              res.end(content);
            } catch (error) {
              console.error('❌ 读取 config.js 失败:', error);
              res.statusCode = 500;
              res.end('// Error loading config.js');
            }
            return;
          }
          next();
        });
      },
    },
  ],
  server: {
    proxy: {
      '/hls-proxy': {
        configure: (proxy, options) => {
          const { origins, credentials } = corsConfig;
          
          proxy.on('proxyRes', (proxyRes, req, res) => {
            const origin = req.headers.origin || '';
            const allowedOrigin = origins.includes(origin) 
              ? origin 
              : origins[0] || '*';
            
            // ✅ 使用具体域名，而非 *
            proxyRes.headers['Access-Control-Allow-Origin'] = allowedOrigin;
            
            if (credentials) {
              proxyRes.headers['Access-Control-Allow-Credentials'] = 'true';
            }
          });
        }
      }
    }
  }
});
```

**⚠️ 关键注意事项**：
- **必须添加 `serve-config-js` 插件**：确保 `/config.js` 在开发环境中能正确加载
- **不要使用 `ignore-config-js-module` 插件**：它会错误地拦截所有 `/config.js` 请求，包括 HTML `<script>` 标签的请求
- 详细说明请参考《代码重构整改方案.md》第 2.1 节和第 9.1 节

### 2.3 CORS安全规范

#### ✅ 正确方式：生产环境使用具体域名

```typescript
// ✅ 正确：使用具体域名列表
const allowedOrigin = allowedOrigins.includes(origin) 
  ? origin 
  : allowedOrigins[0];

proxyRes.headers['Access-Control-Allow-Origin'] = allowedOrigin;
```

#### ❌ 错误方式：使用 `*` 通配符

```typescript
// ❌ 错误：使用 * 通配符（不安全）
proxyRes.headers['Access-Control-Allow-Origin'] = '*';

// ❌ 错误：使用 credentials 时不能使用 *
proxyRes.headers['Access-Control-Allow-Origin'] = '*';
proxyRes.headers['Access-Control-Allow-Credentials'] = 'true'; // 浏览器会拒绝
```

### 2.4 OPTIONS预检请求处理

#### ✅ 正确方式：处理OPTIONS请求

```typescript
proxy.on('proxyReq', (proxyReq, req, res) => {
  if (req.method === 'OPTIONS') {
    const origin = req.headers.origin || '';
    const allowedOrigin = allowedOrigins.includes(origin) 
      ? origin 
      : allowedOrigins[0] || '*';
    
    res.writeHead(204, {
      'Access-Control-Allow-Origin': allowedOrigin,
      'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
      'Access-Control-Allow-Headers': 'Range, Content-Type',
      'Access-Control-Max-Age': '86400',
      ...(credentials && { 'Access-Control-Allow-Credentials': 'true' })
    });
    res.end();
    return;
  }
});
```

---

## 三、登录跳转规范

### 3.1 环境判断统一

#### ✅ 正确方式：使用统一工具函数

```typescript
// src/store/auth.ts
import { isLocalDev } from '@/utils/env';
import { APP_BASE_PATH } from '@/constants/api';

forceReauth(targetPath: string) {
  this.clearAuth();
  this.setRedirectPath(targetPath);
  
  const loginUrlValue = getLoginUrl();
  const originDomain = typeof window !== 'undefined' 
    ? window.location.hostname + (window.location.port ? ':' + window.location.port : '')
    : '';
  const callbackUrl = typeof window !== 'undefined'
    ? `${window.location.protocol}//${originDomain}/pages/auth/callback`
    : '/pages/auth/callback';

  // ✅ 使用统一的环境判断函数
  let loginUrl = `${loginUrlValue}?external_callback=true&origin=${originDomain}&callback=${encodeURIComponent(callbackUrl)}&redirect=${encodeURIComponent(targetPath)}`;

  // 仅在远程部署（非本地开发）时，附加 app_path
  if (!isLocalDev() && APP_BASE_PATH) {
    loginUrl += `&app_path=${encodeURIComponent(APP_BASE_PATH)}`;
  }

  window.location.href = loginUrl;
}
```

#### ❌ 错误方式：在每个文件中重复判断逻辑

```typescript
// ❌ 错误：重复判断逻辑
let isLocalDev = true;
try {
  if (typeof window !== 'undefined' && (window as any).__APP_CONFIG__) {
    isLocalDev = !!(window as any).__APP_CONFIG__.USE_LOCAL_DEV;
  } else if (typeof window !== 'undefined' && (window as any).__ENV) {
    const env = (window as any).__ENV;
    isLocalDev = (env.VITE_APP_ENV === 'development');
  }
} catch (e) {
  console.warn('检测本地/生产环境失败，默认按本地开发处理:', e);
  isLocalDev = true;
}
```

### 3.2 回调URL构造规范

#### ✅ 正确方式：使用工具函数

```typescript
// src/utils/auth.ts
import { APP_BASE_PATH } from '@/constants/api';
import { isLocalDev } from './env';

/**
 * 构造回调 URL（统一工具函数）
 * 
 * 📌 关于本地开发环境的路径说明：
 * - 本地开发环境（USE_LOCAL_DEV: true）：
 *   - vite.config.ts 中 base = '/'（通过端口区分不同前端，不需要子路径）
 *   - 端口区分：localhost:5175 → vzan_simul_frontend，localhost:5174 → user_service_frontend
 *   - callback URL：http://localhost:5175/#/pages/auth/callback（不包含 /live-center）
 * - 生产环境（USE_LOCAL_DEV: false）：
 *   - vite.config.ts 中 base = '/live-center/'（部署在子路径下）
 *   - callback URL：https://mp.dayilive.com/live-center/#/pages/auth/callback（包含 /live-center）
 */
export const buildCallbackUrl = (): string => {
  if (typeof window === 'undefined') {
    return '/pages/auth/callback';
  }
  
  const originDomain = window.location.hostname + 
    (window.location.port ? ':' + window.location.port : '');
  
  const protocol = window.location.protocol;
  
  // ✅ 判断是否为本地开发环境
  // 本地开发：base = '/'，不需要添加 APP_BASE_PATH（通过端口区分不同前端）
  // 生产环境：base = '/live-center/'，需要添加 APP_BASE_PATH
  const basePath = isLocalDev() ? '' : APP_BASE_PATH;
  
  return `${protocol}//${originDomain}${basePath}/#/pages/auth/callback`;
};

// 使用示例
import { buildCallbackUrl } from '@/utils/auth';

const callbackUrl = buildCallbackUrl();
const loginUrl = `${getLoginUrl()}?external_callback=true&origin=${originDomain}&callback=${encodeURIComponent(callbackUrl)}&redirect=${encodeURIComponent(targetPath)}`;
```

---

## 四、配置文件规范

### 4.1 config.js 文件规范

#### ✅ 必须包含的配置项

```javascript
window.__APP_CONFIG__ = {
  USE_LOCAL_DEV: true,  // 必须：环境切换开关
  
  LOCAL_DEV: {
    // 必须：API配置
    VITE_BASE_API_URL: '...',
    VITE_AUTH_API_URL: '...',
    
    // 必须：前端配置
    VITE_LOGIN_URL: '...',
    VITE_FRONTEND_USER_URL: '...',
    VITE_APP_BASE_PATH: '...',
    
    // 必须：CORS配置
    VITE_CORS_ORIGINS: [...],
    VITE_CORS_CREDENTIALS: true,
    
    // 必须：安全配置（用于 callback 验证）
    VITE_ALLOWED_ORIGINS: 'localhost:5175,127.0.0.1:5175,localhost:5174,127.0.0.1:5174',
    
    // 可选：其他配置
    VITE_APP_TITLE: '...',
    VITE_API_TIMEOUT: '30000',
    VITE_APP_ENV: 'development',
    VITE_DEBUG: true,
  },
  
  PRODUCTION: {
    // 同上，但使用生产环境值
  }
};
```

### 4.2 配置项命名规范

#### ✅ 命名规则

1. **所有配置项必须以 `VITE_` 开头**（与 Vite 环境变量规范一致）
2. **使用大写字母和下划线**（如 `VITE_BASE_API_URL`）
3. **使用描述性名称**（如 `VITE_CORS_ORIGINS` 而不是 `CORS_ORIGINS`）

#### ❌ 错误命名

```javascript
// ❌ 错误：没有 VITE_ 前缀
BASE_API_URL: '...'

// ❌ 错误：使用驼峰命名
viteBaseApiUrl: '...'

// ❌ 错误：名称不清晰
API_URL: '...'
```

### 4.3 配置值规范

#### ✅ 正确格式

```javascript
// ✅ 字符串配置
VITE_BASE_API_URL: 'http://localhost:8000/api/v1',

    // ✅ 数组配置（CORS）
    VITE_CORS_ORIGINS: [
      'http://localhost:5175',
      'http://127.0.0.1:5175'
    ],

    // ✅ 布尔配置
    VITE_CORS_CREDENTIALS: true,
    VITE_DEBUG: false,
    
    // ✅ 安全配置（逗号分隔的字符串）
    VITE_ALLOWED_ORIGINS: 'localhost:5175,127.0.0.1:5175,localhost:5174,127.0.0.1:5174',

// ✅ 数字配置（字符串形式）
VITE_API_TIMEOUT: '30000',
```

#### ❌ 错误格式

```javascript
// ❌ 错误：数组应该使用数组格式，不是字符串
VITE_CORS_ORIGINS: 'http://localhost:5175,http://127.0.0.1:5175',

// ❌ 错误：数字应该使用字符串形式（统一处理）
VITE_API_TIMEOUT: 30000,
```

---

## 五、配置安全性规范 ⚠️ **重要**

### 5.1 前端配置的公开性

**重要说明**：所有前端配置都会暴露在浏览器中，用户可以通过浏览器开发者工具查看到。

**原因**：
- 前端代码都会下载到用户的浏览器
- 前端代码都在用户的浏览器中执行
- 用户可以通过浏览器开发者工具查看所有代码

**无法避免**：这是前端代码的本质，无法隐藏。

**暴露方式**：

1. **运行时配置（config.js）**：
   - 用户可以直接访问 `https://your-domain.com/config.js`
   - 或在浏览器 Console 中输入 `window.__APP_CONFIG__`
   - ✅ **可以看到所有配置值**

2. **构建时注入（.env 文件）**：
   - 配置值在构建时被硬编码到 JavaScript 代码中
   - 用户可以在浏览器开发者工具的 Sources 标签中查看
   - ✅ **可以看到所有配置值**

### 5.2 可以暴露的配置 ✅

以下配置可以暴露在浏览器中：

1. **API 地址**
   ```javascript
   VITE_BASE_API_URL: 'https://mp.dayilive.com/api/core/'
   VITE_AUTH_API_URL: 'https://mp.dayilive.com/api/users/'
   ```
   - ✅ 可以暴露：API 地址通常是公开的
   - ⚠️ 注意：如果 API 有 IP 白名单，暴露地址可能增加攻击面

2. **前端 URL**
   ```javascript
   VITE_LOGIN_URL: 'https://mp.dayilive.com/#/pages/auth/login'
   VITE_FRONTEND_USER_URL: 'https://mp.dayilive.com'
   ```
   - ✅ 可以暴露：前端 URL 本身就是公开的

3. **应用标题**
   ```javascript
   VITE_APP_TITLE: '直播SaaS平台'
   ```
   - ✅ 可以暴露：应用标题是公开信息

4. **功能开关**
   ```javascript
   VITE_DEBUG: false
   ```
   - ✅ 可以暴露：功能开关通常可以暴露

5. **应用路径**
   ```javascript
   VITE_APP_BASE_PATH: '/live-center'
   ```
   - ✅ 可以暴露：应用路径是公开信息

6. **CORS 配置**
   ```javascript
   VITE_CORS_ORIGINS: ['https://mp.dayilive.com']
   VITE_CORS_CREDENTIALS: true
   ```
   - ✅ 可以暴露：CORS 配置通常可以暴露

7. **安全配置（白名单）**
   ```javascript
   VITE_ALLOWED_ORIGINS: 'mp.dayilive.com,www.mp.dayilive.com'
   ```
   - ✅ 可以暴露：白名单配置可以暴露（用于验证，不是敏感信息）

### 5.3 不能暴露的配置 ❌

以下配置**绝对不能**暴露在浏览器中：

1. **API 密钥 / Secret Key**
   ```javascript
   // ❌ 错误：绝对不能暴露
   VITE_API_SECRET: 'streamkey_1234567890abcdef'
   VITE_STRIPE_SECRET_KEY: 'sk_test_...'
   VITE_AWS_SECRET_ACCESS_KEY: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
   ```

2. **数据库连接字符串**
   ```javascript
   // ❌ 错误：绝对不能暴露
   VITE_DATABASE_URL: 'postgresql://user:password@host:5432/dbname'
   ```

3. **第三方服务密钥**
   ```javascript
   // ❌ 错误：绝对不能暴露
   VITE_GOOGLE_API_KEY: 'AIzaSy...'  // 如果有限制，不能暴露
   VITE_STRIPE_PUBLISHABLE_KEY: 'pk_test_...'  // 公开密钥可以，但私钥不能
   ```

4. **JWT Secret**
   ```javascript
   // ❌ 错误：绝对不能暴露
   VITE_JWT_SECRET: 'your-secret-key'
   ```

5. **管理员密码**
   ```javascript
   // ❌ 错误：绝对不能暴露
   VITE_ADMIN_PASSWORD: 'admin123'
   ```

### 5.4 前端安全模型

**正确的安全模型**：

```
前端（公开）         后端（私有）
├─ API 地址          ├─ API 密钥
├─ 前端 URL          ├─ 数据库连接
├─ 应用标题          ├─ Secret Key
├─ 功能开关          ├─ JWT Secret
├─ 应用路径          └─ 敏感凭证
└─ CORS 配置
```

**原则**：
- ✅ **前端配置是公开的**：无法避免，这是前端代码的本质
- ✅ **敏感信息放在后端**：API 密钥、Secret Key 等应该放在后端
- ✅ **通过后端保护**：敏感操作通过后端 API 进行

### 5.5 安全配置建议

#### 建议1：敏感信息放在后端

```typescript
// ❌ 错误：在前端配置中
VITE_API_SECRET: 'streamkey_1234567890abcdef'

// ✅ 正确：在后端配置中
// 后端环境变量
API_SECRET=streamkey_1234567890abcdef
```

#### 建议2：使用环境变量（后端）

```bash
# 后端 .env 文件（不在前端代码中）
API_SECRET=streamkey_1234567890abcdef
DATABASE_URL=postgresql://user:password@host:5432/dbname
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### 建议3：API 密钥通过后端代理

```typescript
// ❌ 错误：前端直接使用 API 密钥
const response = await fetch('https://api.example.com', {
  headers: {
    'Authorization': `Bearer ${VITE_API_KEY}`  // ❌ 暴露密钥
  }
});

// ✅ 正确：通过后端代理
const response = await fetch('/api/proxy', {
  method: 'POST',
  body: JSON.stringify({ url: 'https://api.example.com' })
});
// 后端使用密钥，前端不暴露
```

### 5.6 当前项目的配置检查

#### ✅ 当前配置是安全的

```javascript
// public/config.js
// 所有配置都是可以暴露的：
- VITE_BASE_API_URL      // ✅ API 地址，可以暴露
- VITE_AUTH_API_URL      // ✅ 认证 API 地址，可以暴露
- VITE_LOGIN_URL         // ✅ 登录 URL，可以暴露
- VITE_FRONTEND_USER_URL // ✅ 前端 URL，可以暴露
- VITE_APP_BASE_PATH    // ✅ 应用路径，可以暴露
- VITE_APP_TITLE         // ✅ 应用标题，可以暴露
- VITE_DEBUG             // ✅ 调试开关，可以暴露
- VITE_CORS_ORIGINS      // ✅ CORS 配置，可以暴露
- VITE_CORS_CREDENTIALS  // ✅ CORS 配置，可以暴露
- VITE_ALLOWED_ORIGINS   // ✅ 安全配置（白名单），可以暴露
```

#### ⚠️ 将来需要注意

如果将来需要添加以下配置，**绝对不能放在前端**：
- API 密钥
- Secret Key
- 数据库连接
- 第三方服务密钥
- JWT Secret
- 管理员密码

### 5.7 配置审查原则

#### 原则1：最小暴露原则

- ✅ 只暴露必要的配置
- ❌ 不要暴露敏感信息

#### 原则2：后端保护原则

- ✅ 敏感操作通过后端 API
- ❌ 不要在前端直接使用敏感密钥

#### 原则3：配置审查原则

- ✅ 定期审查前端配置
- ❌ 确保没有敏感信息

---

## 六、代码组织规范

### 6.1 工具函数组织

#### ✅ 推荐结构

```
src/
├── utils/
│   ├── env.ts          # 环境相关工具函数
│   ├── cors.ts         # CORS相关工具函数
│   └── auth.ts         # 认证相关工具函数
├── constants/
│   └── api.ts          # API常量定义
└── store/
    └── auth.ts         # 认证状态管理
```

### 6.2 工具函数导出规范

#### ✅ 正确方式

```typescript
// src/utils/env.ts
export const isLocalDev = (): boolean => { ... };
export const getEnv = (key: string, defaultValue?: string): string => { ... };

// src/utils/cors.ts
export const getCorsConfig = () => { ... };

// src/utils/auth.ts
export const buildCallbackUrl = (): string => { ... };
```

#### ❌ 错误方式

```typescript
// ❌ 错误：使用 default export
export default { isLocalDev, getEnv };

// ❌ 错误：导出内部实现
export const __APP_CONFIG__ = window.__APP_CONFIG__;
```

---

## 七、安全验证规范

### 7.1 Origin 白名单验证

#### ✅ 正确方式：在 callback.vue 中验证请求来源

```typescript
// src/pages/auth/callback.vue
import { getEnv } from '@/utils/env';

onMounted(async () => {
  try {
    // ✅ 验证请求来源（Origin 白名单）
    const allowedOrigins = getEnv('VITE_ALLOWED_ORIGINS', '').split(',').filter(Boolean);
    const currentOrigin = typeof window !== 'undefined' 
      ? window.location.hostname + (window.location.port ? ':' + window.location.port : '')
      : '';
    
    // 验证当前域名是否在白名单中
    if (!allowedOrigins.includes(currentOrigin)) {
      console.error('❌ 不允许的来源域名:', currentOrigin);
      throw new Error('不允许的来源域名');
    }
    
    // 继续处理 token 和 redirect...
  } catch (error) {
    // 错误处理
  }
});
```

#### ✅ 正确方式：在 config.js 中配置白名单

```javascript
// public/config.js
LOCAL_DEV: {
  // ... 其他配置 ...
  
  // ✅ 安全配置：允许的来源域名（用于 callback 验证）
  VITE_ALLOWED_ORIGINS: [
    'localhost:5175',
    '127.0.0.1:5175',
    'localhost:5174',
    '127.0.0.1:5174'
  ].join(','),
}

PRODUCTION: {
  // ... 其他配置 ...
  
  // ✅ 安全配置：允许的来源域名
  VITE_ALLOWED_ORIGINS: [
    'mp.dayilive.com',
    'www.mp.dayilive.com'
  ].join(','),
}
```

#### ❌ 错误方式：不验证来源

```typescript
// ❌ 错误：不验证请求来源，任何网站都可以调用 callback
onMounted(async () => {
  const token = options.token;  // 直接使用，没有验证来源
  authStore.setToken(token);    // 安全风险！
});
```

### 7.2 Redirect 参数验证

#### ✅ 正确方式：验证 redirect 参数，防止开放重定向攻击

```typescript
// src/utils/auth.ts
export const validateRedirectPath = (path: string): string => {
  // ✅ 只允许相对路径，不允许外部 URL
  if (!path || !path.startsWith('/pages/')) {
    return '/pages/room/new/RoomList'; // 默认路径
  }
  
  // ✅ 不允许包含协议（http://, https://）
  if (path.includes('://')) {
    console.warn('❌ 检测到外部 URL，使用默认路径');
    return '/pages/room/new/RoomList';
  }
  
  // ✅ 不允许包含特殊字符（防止 XSS）
  if (path.includes('javascript:') || path.includes('data:') || path.includes('<')) {
    console.warn('❌ 检测到危险字符，使用默认路径');
    return '/pages/room/new/RoomList';
  }
  
  // ✅ 不允许包含 .. 路径遍历
  if (path.includes('../') || path.includes('..\\')) {
    console.warn('❌ 检测到路径遍历，使用默认路径');
    return '/pages/room/new/RoomList';
  }
  
  return path;
};

// 使用示例
// src/pages/auth/callback.vue
import { validateRedirectPath } from '@/utils/auth';

const redirect = options.redirect;
if (redirect) {
  // ✅ 验证并清理 redirect 参数
  const safeRedirect = validateRedirectPath(redirect);
  authStore.setRedirectPath(safeRedirect);
}
```

#### ❌ 错误方式：直接使用 redirect 参数

```typescript
// ❌ 错误：直接使用 redirect 参数，存在开放重定向攻击风险
if (redirect) {
  authStore.setRedirectPath(redirect);  // 安全风险！
  // 恶意网站可以构造：?redirect=https://evil.com
}
```

### 7.3 Token 来源验证

#### ✅ 正确方式：验证 token 格式和有效性

```typescript
// src/utils/auth.ts
export const validateToken = (token: string): { valid: boolean; error?: string } => {
  // ✅ 1. 验证 token 是否存在
  if (!token || typeof token !== 'string' || token.trim() === '') {
    return { valid: false, error: 'Token 不存在' };
  }
  
  // ✅ 2. 验证 token 格式（JWT 格式：xxx.yyy.zzz）
  const parts = token.split('.');
  if (parts.length !== 3) {
    return { valid: false, error: 'Token 格式无效' };
  }
  
  // ✅ 3. 验证 token 是否过期
  try {
    const payload = JSON.parse(
      atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
    );
    const currentTime = Date.now() / 1000;
    if (payload.exp && payload.exp < currentTime) {
      return { valid: false, error: 'Token 已过期' };
    }
  } catch (error) {
    return { valid: false, error: 'Token 解析失败' };
  }
  
  return { valid: true };
};

// 使用示例
// src/pages/auth/callback.vue
import { validateToken } from '@/utils/auth';

const token = options.token;
const validation = validateToken(token);
if (!validation.valid) {
  throw new Error(validation.error || 'Token 验证失败');
}

// ✅ 验证通过后，才设置 token
authStore.setToken(token);
authStore.parseUserFromToken(token);
```

#### ❌ 错误方式：仅验证格式，不验证有效性

```typescript
// ❌ 错误：仅验证格式，不验证是否过期
const isValidJWTFormat = (token: string): boolean => {
  return token.split('.').length === 3;  // 不够！
};

if (isValidJWTFormat(token)) {
  authStore.setToken(token);  // 可能使用已过期的 token
}
```

### 7.4 综合安全验证示例

#### ✅ 完整的 callback.vue 安全实现

```typescript
// src/pages/auth/callback.vue
import { getEnv } from '@/utils/env';
import { validateRedirectPath, validateToken } from '@/utils/auth';

onMounted(async () => {
  try {
    // ✅ 1. 验证请求来源（Origin 白名单）
    const allowedOrigins = getEnv('VITE_ALLOWED_ORIGINS', '').split(',').filter(Boolean);
    const currentOrigin = typeof window !== 'undefined' 
      ? window.location.hostname + (window.location.port ? ':' + window.location.port : '')
      : '';
    
    if (!allowedOrigins.includes(currentOrigin)) {
      console.error('❌ 不允许的来源域名:', currentOrigin);
      throw new Error('不允许的来源域名');
    }
    
    // ✅ 2. 获取并验证 token
    const token = options.token;
    if (!token) {
      throw new Error('未找到认证Token');
    }
    
    const tokenValidation = validateToken(token);
    if (!tokenValidation.valid) {
      throw new Error(tokenValidation.error || 'Token 验证失败');
    }
    
    // ✅ 3. 获取并验证 redirect 参数
    const redirect = options.redirect;
    const safeRedirect = redirect ? validateRedirectPath(redirect) : null;
    
    // ✅ 4. 验证通过后，才设置 token 和 redirect
    authStore.setToken(token);
    authStore.parseUserFromToken(token);
    
    if (safeRedirect) {
      authStore.setRedirectPath(safeRedirect);
    }
    
    // ✅ 5. 延迟跳转，确保状态已更新
    setTimeout(() => {
      authStore.handleAuthRedirect();
    }, 1500);
    
  } catch (error) {
    console.error('认证处理失败:', error);
    isProcessing.value = false;
    isError.value = true;
    errorMessage.value = error instanceof Error ? error.message : '未知错误';
  }
});
```

### 7.5 安全配置检查清单

#### ✅ 必须实现的安全验证

- [ ] **Origin 白名单验证**：在 callback.vue 中验证请求来源
- [ ] **Redirect 参数验证**：防止开放重定向攻击
- [ ] **Token 格式验证**：验证 JWT 格式
- [ ] **Token 过期验证**：验证 token 是否过期
- [ ] **白名单配置**：在 config.js 中配置允许的域名
- [ ] **错误处理**：友好的错误提示，不泄露敏感信息

#### ❌ 常见安全错误

```typescript
// ❌ 错误1：不验证来源
const token = options.token;
authStore.setToken(token);

// ❌ 错误2：直接使用 redirect 参数
authStore.setRedirectPath(redirect);

// ❌ 错误3：仅验证格式，不验证过期
if (token.split('.').length === 3) {
  authStore.setToken(token);
}

// ❌ 错误4：硬编码白名单
const ALLOWED_ORIGINS = ['localhost:5175'];  // 应该从配置读取
```

---

## 八、最佳实践

### 8.1 环境切换最佳实践

1. **开发时**：
   - 设置 `USE_LOCAL_DEV: true`
   - 启动开发服务器：`npm run dev:h5`

2. **构建生产版本**：
   - 设置 `USE_LOCAL_DEV: false`
   - 构建：`npm run build:h5`

3. **部署后切换**：
   - 直接修改 `dist/config.js` 中的 `USE_LOCAL_DEV`
   - 无需重新编译

### 8.2 CORS配置最佳实践

1. **开发环境**：
   - 允许 `localhost` 和 `127.0.0.1` 的所有端口
   - 使用 `credentials: true` 支持 cookies

2. **生产环境**：
   - 只允许具体的生产域名
   - 不使用 `*` 通配符
   - 确保与后端API的CORS配置一致

3. **配置同步**：
   - 确保 `config.js` 中的CORS配置与后端API配置一致
   - 确保 `config.js` 中的CORS配置与Nginx配置一致（如果使用）

### 8.3 登录跳转最佳实践

1. **统一使用工具函数**：
   - 使用 `isLocalDev()` 判断环境
   - 使用 `buildCallbackUrl()` 构造回调URL

2. **错误处理**：
   - 处理环境判断失败的情况
   - 处理回调URL构造失败的情况

3. **测试**：
   - 测试本地开发环境的跳转
   - 测试生产环境的跳转
   - 测试子路径部署的跳转

### 8.4 配置管理最佳实践

1. **版本控制**：
   - `public/config.js` 应该提交到 git
   - 包含所有环境的配置模板

2. **文档**：
   - 每个配置项都应该有注释说明
   - 更新配置时更新文档

3. **验证**：
   - 在应用启动时验证配置完整性
   - 在控制台输出当前使用的配置

---

## 九、检查清单

### 9.1 环境配置检查

- [ ] `public/config.js` 存在且结构正确
- [ ] `USE_LOCAL_DEV` 开关正确设置
- [ ] `LOCAL_DEV` 和 `PRODUCTION` 配置完整
- [ ] `index.html` 中使用绝对路径 `/config.js` 加载 `config.js`
- [ ] ⚠️ **关键**：`vite.config.ts` 中**必须**添加 `serve-config-js` 插件
- [ ] ⚠️ **关键**：`isLocalDev()` **必须**包含 fallback 逻辑（根据 `pathname` 判断）
- [ ] 代码中使用统一的环境判断函数
- [ ] 代码中使用统一的配置读取函数

### 9.2 CORS配置检查

- [ ] CORS配置在 `config.js` 中集中管理
- [ ] 生产环境不使用 `*` 通配符
- [ ] 使用 `credentials` 时使用具体域名
- [ ] `vite.config.ts` 从 `config.js` 读取CORS配置
- [ ] 处理OPTIONS预检请求
- [ ] 与后端API的CORS配置一致

### 9.3 登录跳转检查

- [ ] 使用统一的环境判断函数
- [ ] 使用统一的回调URL构造函数
- [ ] 正确处理本地开发和生产环境的差异
- [ ] 正确处理子路径部署的情况
- [ ] 错误处理完善

### 9.4 配置安全性检查 ⚠️ **重要**

- [ ] **配置审查**：确保没有敏感信息（API 密钥、Secret Key 等）
- [ ] **配置分类**：只暴露必要的配置，敏感信息放在后端
- [ ] **配置文档**：每个配置项都有注释说明其安全性

### 9.5 安全验证检查（P0 - 必须实现）

- [ ] **Origin 白名单验证**：在 `callback.vue` 中验证请求来源
- [ ] **Redirect 参数验证**：使用 `validateRedirectPath()` 防止开放重定向攻击
- [ ] **Token 格式验证**：使用 `validateToken()` 验证 JWT 格式
- [ ] **Token 过期验证**：验证 token 是否过期
- [ ] **白名单配置**：在 `config.js` 中配置 `VITE_ALLOWED_ORIGINS`
- [ ] **错误处理**：友好的错误提示，不泄露敏感信息
- [ ] **日志记录**：记录所有认证尝试和失败的验证

---

## 十、常见问题

### Q1: 为什么不能使用 `*` 作为 CORS 的 `Access-Control-Allow-Origin`？

**A**: 
1. **安全风险**：允许所有来源访问资源，存在安全风险
2. **credentials 限制**：如果使用 `Access-Control-Allow-Credentials: true`，浏览器会拒绝 `*`，必须使用具体域名

### Q2: 为什么要在 `config.js` 中配置 CORS，而不是在 `vite.config.ts` 中？

**A**:
1. **集中管理**：所有配置集中在一个文件中，便于管理
2. **运行时修改**：可以在编译后修改配置，无需重新编译
3. **环境区分**：可以为不同环境配置不同的CORS策略

### Q3: 生产环境的 CORS 应该在哪里配置？

**A**:
1. **开发环境**：由 Vite 代理处理（从 `config.js` 读取配置）
2. **生产环境**：应该由 Nginx 或后端API处理，前端 `config.js` 中的配置主要用于开发环境

### Q4: 如何判断当前是本地开发还是生产环境？

**A**: 使用统一工具函数：
```typescript
import { isLocalDev } from '@/utils/env';

if (isLocalDev()) {
  // 本地开发环境
} else {
  // 生产环境
}
```

**⚠️ 重要**：`isLocalDev()` 函数**必须包含 fallback 逻辑**，防止 `config.js` 未加载时返回错误值。详细说明请参考第 1.2 节。

**📌 关于本地开发环境的说明**：
- **本地开发环境**（`USE_LOCAL_DEV: true`）：
  - `vite.config.ts` 中 `base = '/'`（通过端口区分不同前端，不需要子路径）
  - 端口区分：`localhost:5175` → `vzan_simul_frontend`，`localhost:5174` → `user_service_frontend`
  - callback URL：`http://localhost:5175/#/pages/auth/callback`（**不包含** `/live-center`）
- **生产环境**（`USE_LOCAL_DEV: false`）：
  - `vite.config.ts` 中 `base = '/live-center/'`（部署在子路径下）
  - callback URL：`https://mp.dayilive.com/live-center/#/pages/auth/callback`（**包含** `/live-center`）

### Q5: 前端配置是否会暴露？哪些配置可以暴露？

**A**: 
1. **前端配置会暴露**：所有前端配置都会暴露在浏览器中，用户可以通过浏览器开发者工具查看到。这是前端代码的本质，无法避免。
2. **可以暴露的配置**：
   - API 地址（`VITE_BASE_API_URL`）
   - 前端 URL（`VITE_LOGIN_URL`）
   - 应用标题（`VITE_APP_TITLE`）
   - 功能开关（`VITE_DEBUG`）
   - 应用路径（`VITE_APP_BASE_PATH`）
   - CORS 配置（`VITE_CORS_ORIGINS`）
3. **不能暴露的配置**：
   - API 密钥 / Secret Key
   - 数据库连接字符串
   - 第三方服务密钥
   - JWT Secret
   - 管理员密码
4. **安全原则**：
   - 敏感信息应该放在后端
   - 敏感操作通过后端 API 进行
   - 定期审查前端配置，确保没有敏感信息

### Q6: 为什么需要在 callback.vue 中验证 Origin？

**A**: 
1. **防止 CSRF 攻击**：恶意网站可能通过构造 URL 来调用 callback
2. **防止 Token 泄露**：确保 token 只能从可信来源接收
3. **安全最佳实践**：所有外部输入都应该验证来源

### Q7: 如何配置允许的来源域名？

**A**: 在 `config.js` 中配置：
```javascript
LOCAL_DEV: {
  VITE_ALLOWED_ORIGINS: 'localhost:5175,127.0.0.1:5175,localhost:5174,127.0.0.1:5174',
}

PRODUCTION: {
  VITE_ALLOWED_ORIGINS: 'mp.dayilive.com,www.mp.dayilive.com',
}
```

### Q8: 为什么需要验证 redirect 参数？

**A**: 
1. **防止开放重定向攻击**：恶意网站可以构造 URL，将用户重定向到恶意网站
2. **防止 XSS 攻击**：验证 redirect 参数中不包含危险字符
3. **安全最佳实践**：所有用户输入都应该验证和清理

### Q9: Token 验证应该验证哪些内容？

**A**: 
1. **格式验证**：验证是否为有效的 JWT 格式（xxx.yyy.zzz）
2. **过期验证**：验证 token 是否过期
3. **签名验证**（可选）：如果后端支持，可以验证 token 的签名
4. **来源验证**：通过 Origin 白名单验证请求来源

---

**文档版本**: 1.0  
**最后更新**: 2025-01-XX  
**维护者**: 开发团队

