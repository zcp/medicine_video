# 直播SaaS前端JWT认证与跨服务跳转增量开发提示词

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通uni-app、Vue3、TypeScript和Pinia，具备大型SaaS平台前端架构与JWT认证集成经验，**精通多端适配（H5/微信小程序/App）**。你的任务是基于现有代码结构，**增量式地集成JWT Token认证机制和跨服务前端跳转功能**，确保与现有代码的完全兼容性，并支持多平台部署。

---

## 2. 任务目标（Task Objective）
本次任务为直播SaaS平台前端项目的**JWT认证与跨服务跳转增量开发**。目标是**在不修改现有核心业务逻辑的前提下**，集成以下功能：

1. **JWT Token认证管理**：实现基于JWT Token的用户认证、Token存储、验证和自动重定向
2. **跨服务前端跳转**：实现从直播SaaS前端到用户服务前端的页面跳转功能
3. **顶部用户信息区域**：在所有页面添加统一的用户信息展示和操作区域

**增量开发原则：**
- ✅ **零侵入性**：不修改现有的API层、状态管理和组件逻辑
- ✅ **向后兼容**：确保现有功能完全不受影响
- ✅ **配置驱动**：所有新增功能通过配置文件管理，支持多环境部署

---

## 3. 核心上下文信息（Core Context Information）
- **现有代码基础**：基于《直播SaaS前端阶段一、二、三》已生成的完整代码结构
- **设计依据**：严格遵循《多媒体下载功能模块前端设计文件_最终版+jwt token认证版.md》中的认证和跳转规范
- **技术栈**：uni-app + Vue3 + TypeScript + Pinia + uni.request
- **多平台支持**：H5、微信小程序、App（iOS/Android）

---

## 4. 全局强制性约束与最高准则
- **零修改原则**：严禁修改现有的`src/api/`、`src/store/`、`src/types/`目录下的任何文件
- **配置化原则**：所有URL、Token管理、跳转地址必须通过配置文件管理
- **安全优先**：严格遵循JWT Token安全存储和传输规范
- **命名一致性**：新增代码必须遵循现有项目的命名规范和代码风格

---

## 5. 分步增量开发流程

### 步骤1：配置文件创建与URL管理
- **目标**：创建环境配置文件，实现URL的统一管理
- **要求**：
  - 创建`src/config/env.ts`文件，定义所有环境变量
  - 创建`src/constants/api.ts`文件，导出所有API相关常量
  - 支持开发、测试、生产环境的动态配置
  - 严禁硬编码任何IP地址或端口号

### 步骤2：JWT Token认证模块创建
- **目标**：创建独立的认证管理模块，不修改现有Store
- **要求**：
  - 创建`src/utils/auth.ts`文件，实现Token管理功能
  - 创建`src/store/auth.ts`文件，实现认证状态管理
  - 实现Token存储、验证、解析、清理等完整功能
  - 支持自动重定向和重定向路径保存

### 步骤3：HTTP请求拦截器增强
- **目标**：增强现有的`src/utils/request.ts`，添加JWT Token自动注入
- **要求**：
  - **不修改现有request函数签名**
  - 添加请求拦截器，自动注入Authorization头
  - 添加响应拦截器，处理401认证失败
  - 保持现有错误处理逻辑不变

### 步骤4：顶部用户信息组件创建
- **目标**：创建可复用的顶部用户信息组件
- **要求**：
  - 创建`src/components/UserInfoHeader.vue`组件
  - 支持用户名显示、头像展示、下拉菜单
  - 实现跨服务跳转功能
  - **多平台适配**：
    - **H5平台**：使用`window.location.href`进行跨服务跳转
    - **微信小程序**：使用`uni.navigateToMiniProgram`跳转到其他小程序
    - **App平台**：使用`uni.navigateTo`或`uni.redirectTo`进行页面跳转

### 步骤5：页面集成与路由守卫
- **目标**：在现有页面中集成认证和用户信息功能
- **要求**：
  - 在`src/pages.json`中添加认证相关路由
  - 创建认证回调页面`src/pages/auth/callback.vue`
  - 在现有页面中集成`UserInfoHeader`组件
  - 实现路由守卫，保护需要认证的页面

---

## 6. 模块生成指令

### 6.1 环境配置文件 
### A. 本地配置文件(`src/config/env.ts`)
```typescript
// 环境变量配置文件 - 支持多环境部署
export const ENV_CONFIG = {
  // ===== 直播SaaS后端API地址 =====
  VITE_BASE_API_URL: 'http://localhost:8001/',
  
  // ===== 用户认证服务配置 =====
  VITE_AUTH_API_URL: 'http://localhost:8002/',
  VITE_LOGIN_URL: 'http://localhost:5173/pages/auth/login',
  
  // ===== 用户服务前端地址配置 =====
  VITE_FRONTEND_USER_URL: 'http://localhost:5173',
  
  VITE_APP_BASE_PATH: '',
  // ===== 跨服务回调配置 =====
  VITE_CALLBACK_PATH: '/pages/auth/callback',
  
    // ===== 认证重定向配置 =====
  VITE_AUTH_REDIRECT_PATH: '/pages/room/RoomList',
  // ===== 其他配置 =====
  VITE_APP_TITLE: '直播SaaS平台',
  VITE_API_TIMEOUT: '30000',
};

// 开发/生产环境自动检测
const isDev = typeof window !== 'undefined' && 
              (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// 导出到全局供 constants/api.ts 读取
if (typeof window !== 'undefined') {
  window.__ENV = ENV_CONFIG;
}
```

### B. 远程配置文件 (`src/config/env.prod.js`)
// 生产环境配置
const CONFIG = {
    // ===== 直播SaaS后端API地址 =====
    VITE_BASE_API_URL: 'https://124.220.235.226/api/core/',
    
    // ===== 用户认证服务配置 =====
    VITE_AUTH_API_URL: 'https://124.220.235.226/api/users/',
    VITE_LOGIN_URL: 'https://124.220.235.226/pages/auth/login',
    
    // ===== 用户服务前端地址配置 =====
    VITE_FRONTEND_USER_URL: 'https://124.220.235.226',
    
    // ===== 应用路径配置 =====
    VITE_APP_BASE_PATH: '/live-center',
    
    VITE_AUTH_REDIRECT_PATH: '/pages/room/RoomList',

    // ===== 其他配置 =====
    VITE_APP_TITLE: '直播SaaS平台',
    VITE_API_TIMEOUT: '30000',
    VITE_APP_ENV: 'production',
    VITE_DEBUG: false,
  };
  
  // 导出配置到全局
  if (typeof window !== 'undefined') {
    window.__ENV = CONFIG;
  }
  
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
  }

### C. nginx 前端配置文件
    # ===== 重定向规则 =====
    location = /user-service {
        return 301 https://124.220.235.226/;
    }


    location ~ ^/user-service/(.*)$ {
        return 301 https://124.220.235.226/$1;
    }
    # ===== 用户服务前端 - 主页面 =====
    location / {
            root /var/www/html/user-service;
            index index.html;
            try_files $uri $uri/ /index.html;

            # 静态资源缓存
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                root /var/www/html/user-service;
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

    # 新增：处理静态资源请求
    location /assets/ {
            root /var/www/html/user-service;
            expires 1y;
            add_header Cache-Control "public, immutable";
    }

   # 修改：前端静态文件服务 - 改为 /download-center 路径
   location /download-center {
            alias /var/www/html/media-download/;
            index index.html;
            try_files $uri $uri/ /download-center/index.html;

            # 静态资源缓存
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
   }
# ===== 下载中心静态资源 =====
location /download-center/assets/ {
    alias /var/www/html/media-download/assets/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /download-center/config/ {
    alias /var/www/html/media-download/config/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
    # ===== 直播前端 =====
    location /live-center {
        alias /var/www//html/live-center;  # 假设直播前端路径
        index index.html;
        try_files $uri $uri/ /live-center/index.html;

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }



### 6.2 API常量定义 (`src/constants/api.ts`)
```typescript
// API地址常量定义 - 直接使用配置对象，避免环境变量读取问题
import { ENV_CONFIG } from '@/config/env';

// 直接使用配置对象，确保配置值正确读取
// 直接使用配置对象，确保配置值正确读取
export const BASE_API_URL = ENV_CONFIG.VITE_BASE_API_URL.replace(/\/?$/, '/');
export const AUTH_API_URL = ENV_CONFIG.VITE_AUTH_API_URL.replace(/\/?$/, '/');
export const LOGIN_URL = ENV_CONFIG.VITE_LOGIN_URL;
export const FRONTEND_USER_URL = ENV_CONFIG.VITE_FRONTEND_USER_URL;
export const APP_BASE_PATH = ENV_CONFIG.VITE_APP_BASE_PATH;
export const AUTH_REDIRECT_PATH = ENV_CONFIG.VITE_AUTH_REDIRECT_PATH;
export const APP_TITLE = ENV_CONFIG.VITE_APP_TITLE;
export const API_TIMEOUT = parseInt(ENV_CONFIG.VITE_API_TIMEOUT) || 30000;


// 添加调试日志
console.log('API配置加载成功:', {
  LOGIN_URL,
  FRONTEND_USER_URL,
  BASE_API_URL，
  APP_BASE_PATH,
  AUTH_REDIRECT_PATH
});
```

### 6.3 JWT Token认证工具 (`src/utils/auth.ts`)
```typescript
// JWT Token认证工具函数
export interface User {
  user_id: string;
  username?: string;
  email?: string;
  avatar?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  tokenExpiry: number | null;
  redirectPath: string | null;
}

// Token存储键名
const TOKEN_KEY = 'jwt_token';
const REDIRECT_PATH_KEY = 'auth_redirect_path';

// 获取Token
export const getToken = (): string | null => {
  return uni.getStorageSync(TOKEN_KEY) || null;
};

// 设置Token
export const setToken = (token: string): void => {
  uni.setStorageSync(TOKEN_KEY, token);
};

// 清除Token
export const clearToken = (): void => {
  uni.removeStorageSync(TOKEN_KEY);
  uni.removeStorageSync(REDIRECT_PATH_KEY);
};

// 检查Token是否有效
export const checkTokenExpiry = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp > currentTime;
  } catch {
    return false;
  }
};

// 从Token解析用户信息
export const parseUserFromToken = (token: string): User | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      user_id: payload.user_id || payload.sub,
      username: payload.username,
      email: payload.email
    };
  } catch (error) {
    console.error('解析Token失败:', error);
    return null;
  }
};

// 设置重定向路径
export const setRedirectPath = (path: string): void => {
  uni.setStorageSync(REDIRECT_PATH_KEY, path);
};

// 获取重定向路径
export const getRedirectPath = (): string | null => {
  return uni.getStorageSync(REDIRECT_PATH_KEY) || null;
};

// 清除重定向路径
export const clearRedirectPath = (): void => {
  uni.removeStorageSync(REDIRECT_PATH_KEY);
};

// 构建SSO登录URL
export const buildSSOLoginUrl = (): string => {
  const { LOGIN_URL, APP_BASE_PATH } = require('@/constants/api');
  const currentDomain = window.location.hostname + (window.location.port ? ':' + window.location.port : '');
  return `${LOGIN_URL}?external_callback=true&origin=${currentDomain}&app_path=${APP_BASE_PATH}`;
};

```

### 6.4 认证状态管理 (`src/store/auth.ts`)
```typescript
import { defineStore } from 'pinia';
import { 
  getToken, 
  setToken, 
  clearToken, 
  checkTokenExpiry, 
  parseUserFromToken,
  setRedirectPath,
  getRedirectPath,
  clearRedirectPath,
  type User,
  type AuthState
} from '@/utils/auth';
import { LOGIN_URL, FRONTEND_USER_URL } from '@/constants/api';

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
    isAuthenticated: false,
    tokenExpiry: null,
    redirectPath: null
  }),

  getters: {
    isTokenValid: (state) => {
      if (!state.token) return false;
      return checkTokenExpiry(state.token);
    }
  },

  actions: {
    // 初始化认证状态
    async initializeAuth() {
      const savedToken = getToken();
      if (savedToken) {
        if (checkTokenExpiry(savedToken)) {
          this.setToken(savedToken);
          this.parseUserFromToken(savedToken);
        } else {
          this.clearAuth();
        }
      }
    },

    // 设置Token
    setToken(token: string) {
      this.token = token;
      setToken(token);
      this.isAuthenticated = true;
    },

    // 解析用户信息
    parseUserFromToken(token: string) {
      const user = parseUserFromToken(token);
      if (user) {
        this.user = user;
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          this.tokenExpiry = payload.exp * 1000;
        } catch (error) {
          console.error('解析Token过期时间失败:', error);
        }
      }
    },

    // 清除认证状态
    clearAuth() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      this.tokenExpiry = null;
      clearToken();
    },

    // 设置重定向路径
    setRedirectPath(path: string) {
      this.redirectPath = path;
      setRedirectPath(path);
    },

    // 获取重定向路径
    getRedirectPath() {
      return this.redirectPath || getRedirectPath();
    },

    // 清除重定向路径
    clearRedirectPath() {
      this.redirectPath = null;
      clearRedirectPath();
    },

    // 处理认证后的重定向
    handleAuthRedirect() {
      const redirectPath = this.getRedirectPath();
      
      if (redirectPath && redirectPath !== '/pages/auth/login') {
        console.log('重定向到:', redirectPath);
        this.clearRedirectPath();
        uni.navigateTo({ url: redirectPath });
      } else {
        // 使用环境变量配置的默认重定向路径
        const { AUTH_REDIRECT_PATH } = require('@/constants/api');
        console.log('重定向到默认页面:', AUTH_REDIRECT_PATH);
        uni.navigateTo({ url: AUTH_REDIRECT_PATH });
      }
    },

    // 强制重新认证
    forceReauth(targetPath: string) {
      this.clearAuth();
      this.setRedirectPath(targetPath);
      
      // #ifdef H5
      // H5平台：使用window.location.href跳转
     // 构建SSO登录URL，包含外部应用参数
      const { LOGIN_URL, APP_BASE_PATH } = require('@/constants/api');
      const currentDomain = window.location.hostname + (window.location.port ? ':' + window.location.port : '');
      const loginUrlWithCallback = `${LOGIN_URL}?external_callback=true&origin=${currentDomain}&app_path=${APP_BASE_PATH}`;
      
      
      console.log('🔄 H5平台跳转到登录页面:', loginUrlWithCallback);
      window.location.href = loginUrlWithCallback;
      // #endif
      
      // #ifdef MP-WEIXIN
      // 微信小程序：跳转到登录页面
      console.log('🔄 微信小程序跳转到登录页面');
      uni.navigateTo({
        url: '/pages/auth/login',
        fail: () => {
          uni.showToast({
            title: '跳转失败，请手动打开登录页面',
            icon: 'none'
          });
        }
      });
      // #endif
      
      // #ifdef APP-PLUS
      // App平台：跳转到登录页面
      console.log('🔄 App平台跳转到登录页面');
      uni.navigateTo({
        url: '/pages/auth/login',
        fail: () => {
          uni.showToast({
            title: '跳转失败，请手动打开登录页面',
            icon: 'none'
          });
        }
      });
      // #endif
    },

    // 登出并跳转到登录页面
    logout() {
      this.clearAuth();
      this.clearRedirectPath();
      
      // #ifdef H5
      // H5平台：使用window.location.href跳转
      window.location.href = LOGIN_URL;
      // #endif
      
      // #ifdef MP-WEIXIN
      // 微信小程序：跳转到登录页面
      uni.navigateTo({
        url: '/pages/auth/login',
        fail: () => {
          uni.showToast({
            title: '跳转失败，请手动打开登录页面',
            icon: 'none'
          });
        }
      });
      // #endif
      
      // #ifdef APP-PLUS
      // App平台：跳转到登录页面
      uni.navigateTo({
        url: '/pages/auth/login',
        fail: () => {
          uni.showToast({
            title: '跳转失败，请手动打开登录页面',
            icon: 'none'
          });
        }
      });
      // #endif
    },

    // 跳转到用户服务
    goToUserService(page: string) {
      const userServiceUrl = `${FRONTEND_USER_URL}${page}`;
      
      // #ifdef H5
      // H5平台：使用window.location.href进行跨服务跳转
      window.location.href = userServiceUrl;
      // #endif
      
      // #ifdef MP-WEIXIN
      // 微信小程序：跳转到其他小程序
      uni.navigateToMiniProgram({
        appId: '用户服务小程序的appId', // 需要配置用户服务小程序的appId
        path: page,
        success: () => {
          console.log('跳转到用户服务小程序成功');
        },
        fail: (err) => {
          console.error('跳转到用户服务小程序失败:', err);
          // 降级处理：显示提示信息
          uni.showToast({
            title: '跳转失败，请手动打开用户服务',
            icon: 'none'
          });
        }
      });
      // #endif
      
      // #ifdef APP-PLUS
      // App平台：使用uni.navigateTo进行页面跳转
      uni.navigateTo({
        url: userServiceUrl,
        fail: (err) => {
          console.error('App跳转失败:', err);
          // 降级处理：尝试使用redirectTo
          uni.redirectTo({
            url: userServiceUrl,
            fail: () => {
              uni.showToast({
                title: '跳转失败，请手动打开用户服务',
                icon: 'none'
              });
            }
          });
        }
      });
      // #endif
    }
  }
});
```

### 6.5 顶部用户信息组件 (`src/components/UserInfoHeader.vue`)
```vue
<template>
  <view class="user-info-header">
    <view class="user-info-header__content">
      <view class="user-info-header__logo">
        <text class="user-info-header__title">{{ appTitle }}</text>
      </view>
      
      <view class="user-info-header__user" v-if="isAuthenticated">
        <view class="user-info-header__avatar" @click="toggleDropdown">
          <!-- 如果有头像，显示真实头像；否则显示用户图标 -->
          <image 
            v-if="user?.avatar" 
            :src="user.avatar" 
            class="user-info-header__avatar-img"
            mode="aspectFill"
          />
          <!-- 默认显示用户图标，充满整个圆形区域 -->
          <view v-else class="user-info-header__avatar-icon">👤</view>
        </view>
        
        <view class="user-info-header__dropdown" v-if="showDropdown">
          <view class="user-info-header__dropdown-item" @click="goToProfile">
            <text class="user-info-header__dropdown-text">个人信息</text>
          </view>
          <view class="user-info-header__dropdown-item" @click="goToHome">
            <text class="user-info-header__dropdown-text">主页</text>
          </view>
          <view class="user-info-header__dropdown-divider"></view>
          <view class="user-info-header__dropdown-item" @click="handleLogout">
            <text class="user-info-header__dropdown-text logout">退出登录</text>
          </view>
        </view>
      </view>
      
      <!-- 未认证时显示登录提示 -->
      <view class="user-info-header__login-prompt" v-else>
        <text class="user-info-header__login-text">请登录</text>
        <view class="user-info-header__login-icon">🔐</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import { APP_TITLE } from '@/constants/api';

const authStore = useAuthStore();
const showDropdown = ref(false);
const defaultAvatar = '/static/default-avatar.png';

const appTitle = computed(() => APP_TITLE);
const isAuthenticated = computed(() => authStore.isAuthenticated);
const user = computed(() => authStore.user);

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

const goToProfile = () => {
  showDropdown.value = false;
  authStore.goToUserService('/pages/user/profile');
};

const goToHome = () => {
  showDropdown.value = false;
  authStore.goToUserService('/pages/index/index');
};

const handleLogout = () => {
  showDropdown.value = false;
  authStore.logout();
};

// 点击外部关闭下拉菜单
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.user-info-header__user')) {
    showDropdown.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped lang="scss">
.user-info-header {
  background-color: var(--nav-bg-color, #ffffff);
  border-bottom: 1px solid var(--border-color, #e5e5e5);
  padding: 0 var(--spacing-md, 16px);
  height: 60px;
  display: flex;
  align-items: center;
  position: relative;
  z-index: 100;

  &__content {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__logo {
    display: flex;
    align-items: center;
  }

  &__title {
    font-size: var(--font-size-lg, 18px);
    font-weight: 600;
    color: var(--text-color-primary, #333333);
  }

  &__user {
    position: relative;
    display: flex;
    align-items: center;
  }

  &__avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    overflow: hidden;
    cursor: pointer;
    border: 3px solid var(--primary-color, #007bff);
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);

    &:hover {
      border-color: var(--primary-color-hover, #0056b3);
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
    }
  }

  &__avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &__avatar-icon {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: var(--primary-color, #007bff);
    background-color: var(--bg-color-light, #f8f9fa);
    border-radius: 50%;
  }

  &__dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    background-color: var(--nav-bg-color, #ffffff);
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: var(--border-radius-base, 4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    min-width: 160px;
    z-index: 1000;
    margin-top: 8px;
  }

  &__dropdown-item {
    padding: var(--spacing-sm, 8px) var(--spacing-md, 16px);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: var(--bg-color-hover, #f5f5f5);
    }
  }

  &__dropdown-text {
    font-size: var(--font-size-base, 14px);
    color: var(--text-color-primary, #333333);

    &.logout {
      color: var(--danger-color, #dc3545);
    }
  }

  &__dropdown-divider {
    height: 1px;
    background-color: var(--border-color, #e5e5e5);
    margin: var(--spacing-xs, 4px) 0;
  }

  &__login-prompt {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 4px);
    padding: var(--spacing-sm, 8px) var(--spacing-md, 16px);
    background-color: var(--warning-color, #ffc107);
    border-radius: var(--border-radius-base, 4px);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: var(--warning-color-hover, #e0a800);
    }
  }

  &__login-text {
    font-size: var(--font-size-sm, 12px);
    color: var(--text-color-inverse, #ffffff);
    font-weight: 500;
  }

  &__login-icon {
    font-size: var(--font-size-sm, 12px);
  }
}

/* 响应式适配 */
@media (max-width: 768px) {
  .user-info-header {
    padding: 0 var(--spacing-sm, 12px);
    height: 50px;

    &__title {
      font-size: var(--font-size-base, 16px);
    }

    &__avatar {
      width: 44px;
      height: 44px;
    }
  }
}
</style>
```

### 6.6 认证回调页面 (`src/pages/auth/callback.vue`)
```vue
<template>
  <view class="auth-callback">
    <view class="auth-callback__container">
      <view class="auth-callback__loading" v-if="isProcessing">
        <view class="auth-callback__spinner"></view>
        <text class="auth-callback__text">正在处理认证...</text>
      </view>
      
      <view class="auth-callback__success" v-else-if="isSuccess">
        <view class="auth-callback__icon success">✓</view>
        <text class="auth-callback__text">认证成功</text>
        <text class="auth-callback__subtext">正在跳转...</text>
      </view>
      
      <view class="auth-callback__error" v-else-if="isError">
        <view class="auth-callback__icon error">✗</view>
        <text class="auth-callback__text">认证失败</text>
        <text class="auth-callback__subtext">{{ errorMessage }}</text>
        <button class="auth-callback__retry" @click="retryAuth">重试</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();
const isProcessing = ref(true);
const isSuccess = ref(false);
const isError = ref(false);
const errorMessage = ref('');

onMounted(async () => {
  try {
    // 从URL参数中获取token
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];
    const options = currentPage.options;
    
    const token = options.token;
    const error = options.error;
    const errorDescription = options.error_description;

    if (error) {
      throw new Error(errorDescription || '认证失败');
    }

    if (!token) {
      throw new Error('未找到认证Token');
    }

    // 验证Token格式
    if (!isValidJWTFormat(token)) {
      throw new Error('Token格式无效');
    }

    // 设置Token
    authStore.setToken(token);
    authStore.parseUserFromToken(token);

    isProcessing.value = false;
    isSuccess.value = true;

    // 延迟跳转
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

const isValidJWTFormat = (token: string): boolean => {
  const parts = token.split('.');
  return parts.length === 3;
};

const retryAuth = () => {
  // 重新跳转到登录页面
  // 重新跳转到登录页面，包含SSO参数
  const { LOGIN_URL, APP_BASE_PATH } = require('@/constants/api');
  const currentDomain = window.location.hostname + (window.location.port ? ':' + window.location.port : '');
  const loginUrlWithCallback = `${LOGIN_URL}?external_callback=true&origin=${currentDomain}&app_path=${APP_BASE_PATH}`;
  window.location.href = loginUrlWithCallback;
};
</script>

<style scoped lang="scss">
.auth-callback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-lg, 24px);

  &__container {
    background-color: var(--nav-bg-color, #ffffff);
    border-radius: var(--border-radius-lg, 8px);
    padding: var(--spacing-xl, 32px);
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    max-width: 400px;
    width: 100%;
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 16px);
  }

  &__success {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 16px);
  }

  &__error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 16px);
  }

  &__spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-color, #e5e5e5);
    border-top-color: var(--primary-color, #007bff);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  &__icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: bold;
    color: var(--text-color-inverse, #ffffff);

    &.success {
      background-color: var(--success-color, #28a745);
    }

    &.error {
      background-color: var(--danger-color, #dc3545);
    }
  }

  &__text {
    font-size: var(--font-size-lg, 18px);
    font-weight: 600;
    color: var(--text-color-primary, #333333);
  }

  &__subtext {
    font-size: var(--font-size-base, 14px);
    color: var(--text-color-secondary, #666666);
  }

  &__retry {
    background-color: var(--primary-color, #007bff);
    color: var(--text-color-inverse, #ffffff);
    border: none;
    border-radius: var(--border-radius-base, 4px);
    padding: var(--spacing-sm, 8px) var(--spacing-md, 16px);
    font-size: var(--font-size-base, 14px);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: var(--primary-color-hover, #0056b3);
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
```

### 6.8 页面配置更新 (`src/pages.json`)
```json
{
  "pages": [
    {
      "path": "pages/auth/callback",
      "style": {
        "navigationBarTitleText": "认证回调",
        "navigationStyle": "custom"
      }
    }
  ],
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "直播SaaS平台",
    "navigationBarBackgroundColor": "#ffffff",
    "backgroundColor": "#f5f5f5"
  }
}
```

---

## 7. 集成指南

### 7.1 需要集成的页面清单

基于三个阶段提示词文档，以下页面需要集成JWT认证和顶部用户信息区域：

#### 7.1.1 需要强制认证的页面
- `src/pages/room/RoomList.vue` - 房间列表页 ✅
- `src/pages/room/RoomDetail.vue` - 房间详情页 ✅  
- `src/pages/session/SessionList.vue` - 场次列表页 ✅
- `src/pages/live/LiveView.vue` - 直播观看页 ✅

#### 7.1.2 不需要认证的页面
- `src/pages/index/index.vue` - 重定向页面（直接跳转到房间列表）
- `src/pages/common/NotFound.vue` - 404页面
- `src/pages/auth/callback.vue` - 认证回调页面（新增）

#### 7.1.3 页面认证状态说明
- **✅ 已实现认证检查**：`RoomList.vue`、`RoomDetail.vue`、`LiveView.vue`、`callback.vue`
- **❌ 需要添加认证检查**：`SessionList.vue`（如果存在）
- **🚫 不需要认证检查**：`index.vue`、`NotFound.vue`

#### 7.1.4 实际集成经验总结
- **UserInfoHeader 组件**：必须集成到所有需要认证的页面
- **头像显示优化**：使用条件渲染，有头像显示头像，无头像显示用户图标
- **视觉效果增强**：头像尺寸50px，蓝色边框，悬停动画效果
- **未认证提示**：显示黄色"请登录"提示，包含锁图标
- **页面布局调整**：为顶部用户信息区域预留60px高度

### 7.2 页面集成步骤（最小化修改原则）

#### 7.2.1 在现有页面中集成UserInfoHeader组件

**步骤1：导入组件**
```vue
<!-- 在每个页面的 <script setup> 部分添加 -->
import UserInfoHeader from '@/components/UserInfoHeader.vue';
```

**步骤2：在模板中添加组件**
```vue
<!-- 在每个页面的 <template> 顶部添加 -->
<template>
  <!-- 添加顶部用户信息区域 -->
  <UserInfoHeader />
  
  <!-- 现有页面内容保持不变 -->
  <view class="page-content">
    <!-- 原有页面内容 -->
  </view>
</template>
```

**步骤3：调整页面样式**
```scss
/* 在每个页面的 <style> 部分添加 */
.page-content {
  padding-top: 60px; /* 为顶部用户信息区域留出空间 */
}

/* 响应式适配 */
@media (max-width: 768px) {
  .page-content {
    padding-top: 50px;
  }
}
```

#### 7.2.2 认证状态检查集成

**步骤1：在页面onLoad中添加认证检查**
```typescript
// 在每个页面的 onLoad 生命周期中添加
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

onLoad(async (options) => {
  // 检查认证状态
  if (!authStore.isAuthenticated) {
    // 保存当前页面路径
    const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
    authStore.setRedirectPath(`/pages/${currentPath}`);
    
    // 跳转到登录页面
    const originDomain = window.location.origin.replace('http://', '').replace('https://', '');
    const loginUrlWithCallback = `${LOGIN_URL}?external_callback=true&origin=${originDomain}`;
    window.location.href = loginUrlWithCallback;
    return;
  }
  
  // 原有页面逻辑保持不变
  // ... 现有代码
});
```

**步骤2：在需要认证的API调用前检查Token**
```typescript
// 在调用API前检查Token有效性
if (!authStore.isTokenValid) {
  authStore.forceReauth(getCurrentPages()[getCurrentPages().length - 1].route);
  return;
}
```

### 7.3 具体页面实现指令

#### 7.3.1 RoomDetail.vue 认证集成
```typescript
// 在 <script setup> 部分添加
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

// 在 onLoad 生命周期中添加认证检查
onLoad(async (options) => {
  // 认证检查
  if (!authStore.isAuthenticated) {
    const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
    authStore.forceReauth(`/pages/${currentPath}`);
    return;
  }
  
  // 原有页面逻辑继续执行
  // ... 现有代码
});
```

#### 7.3.2 LiveView.vue 认证集成
```typescript
// 在 <script setup> 部分添加
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

// 在 onLoad 生命周期中添加认证检查
onLoad(async (options) => {
  // 认证检查
  if (!authStore.isAuthenticated) {
    const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
    authStore.forceReauth(`/pages/${currentPath}`);
    return;
  }
  
  // 原有页面逻辑继续执行
  // ... 现有代码
});
```

#### 7.3.3 SessionList.vue 认证集成
```typescript
// 在 <script setup> 部分添加
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

// 在 onLoad 生命周期中添加认证检查
onLoad(async (options) => {
  // 认证检查
  if (!authStore.isAuthenticated) {
    const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
    authStore.forceReauth(`/pages/${currentPath}`);
    return;
  }
  
  // 原有页面逻辑继续执行
  // ... 现有代码
});
```

### 7.4 标准认证检查模板

#### 7.4.1 页面级认证检查
```typescript
// 在每个需要认证的页面的 onLoad 中添加
onLoad(async (options) => {
  const authStore = useAuthStore();
  
  // 检查认证状态
  if (!authStore.isAuthenticated) {
    // 保存当前页面路径
    const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
    authStore.forceReauth(`/pages/${currentPath}`);
    return;
  }
  
  // 原有页面逻辑继续执行
  // ... 现有代码
});
```

#### 7.4.2 API调用前认证检查
```typescript
// 在调用需要认证的API前添加
if (!authStore.isAuthenticated) {
  const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
  authStore.forceReauth(`/pages/${currentPath}`);
  return;
}
```

#### 7.4.3 认证检查最佳实践
1. **时机选择**：在页面的 `onLoad` 生命周期中进行认证检查
2. **路径保存**：使用 `getCurrentPages()` 获取当前页面路径
3. **提前返回**：认证失败时立即返回，不执行后续业务逻辑
4. **错误处理**：认证失败时自动跳转到登录页面
5. **调试日志**：添加适当的调试日志便于问题排查

### 7.5 主应用入口集成

#### 7.5.1 在main.ts中初始化认证状态
```typescript
// src/main.ts
import { createSSRApp } from 'vue';
import App from './App.vue';
import pinia from './store';
import { useAuthStore } from './store/auth';

const app = createSSRApp(App);
app.use(pinia);

// 初始化认证状态
const authStore = useAuthStore();
await authStore.initializeAuth();

app.mount('#app');
```

#### 7.3.2 在App.vue中添加全局认证状态监听
```vue
<!-- src/App.vue -->
<template>
  <view id="app">
    <router-view />
  </view>
</template>

<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

onLaunch(() => {
  // 应用启动时初始化认证状态
  authStore.initializeAuth();
});
</script>
```

### 7.6 HTTP请求拦截器增强（最小化修改）

#### 7.6.1 增强现有request.ts文件
```typescript
// 在现有的 src/utils/request.ts 中添加以下代码
// 注意：不修改现有函数签名，只添加拦截器逻辑

import { getToken } from './auth';
import { useAuthStore } from '@/store/auth';

// 在现有request函数前添加拦截器逻辑
const requestWithAuth = <T = any>(options: RequestOptions): Promise<T> => {
  return new Promise((resolve, reject) => {
    // 获取Token并添加到请求头
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.header,
    };
    
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: headers,
      success: (res: any) => {
        // 处理401认证失败
        if (res.statusCode === 401) {
          const authStore = useAuthStore();
          const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
          authStore.forceReauth(`/pages/${currentPath}`);
          reject(new Error('认证失败'));
          return;
        }
        
        // 原有成功处理逻辑保持不变
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T);
        } else {
          console.error(`HTTP Error: ${res.statusCode}`, res);
          uni.showToast({
            title: `请求错误: ${res.statusCode}`,
            icon: 'none',
          });
          reject(res);
        }
      },
      fail: (err) => {
        // 原有失败处理逻辑保持不变
        console.error('Request Failed', err);
        uni.showToast({
          title: '网络请求失败',
          icon: 'none',
        });
        reject(err);
      },
    });
  });
};

// 导出增强后的request函数
export const request = requestWithAuth;
```

### 7.7 页面配置更新

#### 7.7.1 更新pages.json
```json
{
  "pages": [
    {
      "path": "pages/room/RoomList",
      "style": {
        "navigationBarTitleText": "房间列表",
        "navigationStyle": "custom",
        "enablePullDownRefresh": true
      }
    },
    {
      "path": "pages/room/RoomDetail",
      "style": {
        "navigationBarTitleText": "房间详情",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/session/SessionList",
      "style": {
        "navigationBarTitleText": "场次列表",
        "navigationStyle": "custom",
        "enablePullDownRefresh": true
      }
    },
    {
      "path": "pages/live/LiveView",
      "style": {
        "navigationBarTitleText": "直播观看",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/common/NotFound",
      "style": {
        "navigationBarTitleText": "页面未找到",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/auth/callback",
      "style": {
        "navigationBarTitleText": "认证回调",
        "navigationStyle": "custom"
      }
    }
  ],
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "直播SaaS平台",
    "navigationBarBackgroundColor": "#ffffff",
    "backgroundColor": "#f5f5f5"
  }
}
```

### 7.8 配置文件部署

#### 7.8.1 环境配置
1. **开发环境**：修改`src/config/env.ts`中的配置为开发环境地址
2. **测试环境**：修改配置为测试环境地址
3. **生产环境**：修改配置为生产环境地址

#### 7.8.2 验证清单
- [ ] 所有页面都正确集成了UserInfoHeader组件
- [ ] 认证状态检查在所有需要认证的页面中正常工作
- [ ] HTTP请求拦截器正确注入JWT Token
- [ ] 401认证失败时正确跳转到登录页面
- [ ] 跨服务跳转功能正常工作
- [ ] 用户信息显示正确（用户名、头像等）
- [ ] 登出功能正常工作
- [ ] 认证回调页面正确处理Token

### 7.9 兼容性保证

#### 7.9.1 现有功能不受影响
- ✅ 所有现有API调用逻辑保持不变
- ✅ 现有Store状态管理逻辑不变
- ✅ 现有组件功能不受影响
- ✅ 现有页面路由配置保持不变

#### 7.9.2 新增功能独立运行
- ✅ JWT认证模块独立运行，不依赖现有业务逻辑
- ✅ 顶部用户信息组件独立运行，不影响页面内容
- ✅ 跨服务跳转功能独立运行，不影响现有导航

### 7.10 多平台适配说明

#### 7.10.1 平台差异处理
- **H5平台**：
  - 使用`window.location.href`进行跨服务跳转
  - 支持完整的URL跳转和回调机制
  - Token存储使用`localStorage`
- **微信小程序**：
  - 使用`uni.navigateToMiniProgram`跳转到其他小程序
  - 需要配置用户服务小程序的appId
  - Token存储使用`uni.setStorageSync`
  - 跨服务跳转受小程序平台限制
- **App平台**：
  - 使用`uni.navigateTo`或`uni.redirectTo`进行页面跳转
  - Token存储使用`uni.setStorageSync`
  - 支持原生App间的跳转

#### 7.10.2 平台特定配置
- **微信小程序配置**：
  - 需要在`manifest.json`中配置用户服务小程序的appId
  - 需要在小程序管理后台配置跳转关系
- **App平台配置**：
  - 需要在`manifest.json`中配置URL Scheme
  - 需要处理App间的数据传递

#### 7.10.3 降级处理策略
- **跨服务跳转失败**：显示提示信息，引导用户手动打开目标服务
- **Token存储失败**：使用内存存储作为临时方案
- **认证回调失败**：提供手动登录入口

---

## 8. 最终交付与质量保证协议
- **输出格式**：每个文件一个完整、可直接运行的代码块，并标注清晰的文件路径
- **兼容性检查**：确保所有新增代码与现有代码完全兼容
- **安全验证**：确保JWT Token安全存储和传输
- **功能验证**：确保认证和跳转功能正常工作

---

## 9. 常见问题与解决方案

### 9.1 认证死循环问题
**现象**：页面不断跳转到登录页面，无法正常访问
**原因**：
- 环境变量读取失败，导致`LOGIN_URL`解析错误
- 页面在未认证状态下直接调用API，触发401错误
- `forceReauth`中的origin参数格式错误

**解决方案**：
1. 使用直接导入配置对象，避免`import.meta.env`读取问题
2. 在页面加载时先检查认证状态，再调用API
3. 使用`window.location.origin`获取完整的origin


### 9.3 Token传递问题
**现象**：登录成功后无法获取到token
**原因**：
- 跨服务跳转时token丢失
- URL参数传递失败
- localStorage存储失败

**解决方案**：
1. 使用URL参数和localStorage双重机制
2. 在中间页面中验证token存储
3. 添加详细的调试日志

### 9.4 多平台兼容性问题
**现象**：不同平台表现不一致
**原因**：
- 平台特定的API差异
- 存储机制不同
- 跳转方式不同

**解决方案**：
1. 使用条件编译处理平台差异
2. 提供降级处理方案
3. 在每个平台进行充分测试

### 9.5 UserInfoHeader 组件不显示问题
**现象**：页面顶部没有显示用户信息区域
**原因**：
- 组件导入错误或路径错误
- 页面模板中缺少组件引用
- 语法错误导致页面无法正常渲染
- 缺少必要的依赖导入

**解决方案**：
1. 检查组件导入路径：`import UserInfoHeader from '@/components/UserInfoHeader.vue'`
2. 确保在模板中添加：`<UserInfoHeader />`
3. 检查页面语法错误，特别是缺少的导入
4. 确保 User 类型包含 avatar 属性
5. 检查页面布局，确保为顶部区域预留空间

### 9.6 头像显示问题
**现象**：用户头像显示异常或无法显示
**原因**：
- User 类型定义缺少 avatar 属性
- 头像URL无效或无法访问
- 条件渲染逻辑错误

**解决方案**：
1. 在 User 接口中添加 `avatar?: string` 属性
2. 使用条件渲染：`v-if="user?.avatar"` 和 `v-else`
3. 提供默认用户图标作为后备方案
4. 确保头像URL的有效性

---

## 10. 调试指南

### 10.1 认证流程调试
1. **检查环境变量**：确认`ENV_CONFIG`正确加载
2. **验证token格式**：确保JWT格式正确（3个部分）
3. **确认跨服务跳转URL**：检查URL构造和协议
4. **检查用户系统白名单**：确保包含完整URL

### 10.2 关键调试日志
- `🔍 当前认证状态`：显示认证状态和token信息
- `🔑 请求认证Token`：显示token获取和验证过程
- `✅ 已添加认证头`：确认请求头设置成功
- `🔄 根路径访问，自动跳转到房间列表`：确认页面跳转逻辑
- `🚀 准备跳转到`：确认跨服务跳转URL
- `✅ 用户已认证，加载房间列表`：确认认证检查通过
- `❌ 用户未认证，跳转到登录页面`：确认认证检查失败

### 10.3 UserInfoHeader 组件调试
1. **检查组件渲染**：
   - 确认组件已正确导入和引用
   - 检查模板中是否有 `<UserInfoHeader />` 标签
   - 验证组件路径是否正确

2. **检查认证状态**：
   - 确认 `isAuthenticated` 状态是否正确
   - 检查 `user` 对象是否包含必要属性
   - 验证头像显示逻辑

3. **检查样式问题**：
   - 确认页面为顶部区域预留了足够空间
   - 检查头像尺寸和边框样式
   - 验证响应式布局是否正确

### 10.4 测试流程
1. **环境准备**：
   - 启动直播系统前端 (localhost:5174)
   - 启动用户系统前端 (localhost:5173)
   - 启动后端服务 (localhost:8000)

2. **功能测试**：
   - 访问 `http://localhost:5174/` 应该自动跳转到房间列表
   - 未认证时访问房间列表应该跳转到登录页面
   - 登录成功后应该跳转回房间列表
   - 认证状态应该正确显示
   - 跨服务跳转应该正常工作

3. **多平台测试**：
   - **H5平台**：在浏览器中测试完整流程
   - **微信小程序**：测试小程序内跳转和存储
   - **App平台**：测试原生App跳转和存储

---

## 11. 多平台支持说明

### 11.1 平台差异处理
- **H5平台**：
  - 使用`window.location.href`进行跨服务跳转
  - 支持完整的URL跳转和回调机制
  - Token存储使用`localStorage`

- **微信小程序**：
  - 使用`uni.navigateToMiniProgram`跳转到其他小程序
  - 需要配置用户服务小程序的appId
  - Token存储使用`uni.setStorageSync`
  - 跨服务跳转受小程序平台限制

- **App平台**：
  - 使用`uni.navigateTo`或`uni.redirectTo`进行页面跳转
  - Token存储使用`uni.setStorageSync`
  - 支持原生App间的跳转
  - 需要配置URL Scheme

### 11.2 平台特定配置
- **微信小程序配置**：
  - 在`manifest.json`中配置用户服务小程序的appId
  - 在小程序管理后台配置跳转关系
  - 处理小程序间的数据传递

- **App平台配置**：
  - 在`manifest.json`中配置URL Scheme
  - 处理App间的数据传递
  - 配置原生跳转权限

### 11.3 降级处理策略
- **跨服务跳转失败**：显示提示信息，引导用户手动打开目标服务
- **Token存储失败**：使用内存存储作为临时方案
- **认证回调失败**：提供手动登录入口
- **网络错误**：提供重试机制和错误提示

---

**最终一致性断言**：
```
[FINAL ASSERTION]
JWT认证与跨服务跳转增量开发已完成：
- 零侵入性：现有代码未修改
- 功能完整性：认证和跳转功能完整实现
- 配置化：所有配置通过配置文件管理
- 安全性：JWT Token安全处理
- 兼容性：与现有代码完全兼容
- 多平台支持：H5、微信小程序、App全平台支持
- 错误处理：完善的错误处理和调试指南
- 用户体验：优化的头像显示和用户界面
- 实际验证：基于真实实现经验的完善文档
- 问题预防：详细的常见问题解决方案
```
