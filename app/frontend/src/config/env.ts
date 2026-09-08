/**
 * 环境变量配置文件
 * 
 * 配置优先级：
 * 1. 环境变量文件 (.env.development / .env.production)
 * 2. 下方的默认值（仅作为兜底）
 * 
 * 注意：修改配置请编辑对应的 .env 文件，不要在此处硬编码
 */
export const ENV_CONFIG = {
  // ===== 后端API地址 =====
  // 开发环境在 .env.development 中配置
  // 生产环境在 .env.production 中配置
  VITE_BASE_API_URL: import.meta.env.VITE_BASE_API_URL || '',
  VITE_AUTH_API_URL: import.meta.env.VITE_AUTH_API_URL || '',
  
  // ===== 用户认证配置 =====
  VITE_LOGIN_URL: import.meta.env.VITE_LOGIN_URL || '',
  VITE_FRONTEND_USER_URL: import.meta.env.VITE_FRONTEND_USER_URL || '',
  
  // ===== 应用路径配置 =====
  VITE_APP_BASE_PATH: import.meta.env.VITE_APP_BASE_PATH || '/',
  VITE_CALLBACK_PATH: import.meta.env.VITE_CALLBACK_PATH || '/pages/shared/auth/callback',
  VITE_AUTH_REDIRECT_PATH: import.meta.env.VITE_AUTH_REDIRECT_PATH || '/pages/app/tabbar/home/index',
   
  // ===== 应用信息 =====
  VITE_APP_TITLE: import.meta.env.VITE_APP_TITLE || '直播SaaS平台',
  VITE_API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT || '30000',
  
  // ===== 环境标识 =====
  VITE_APP_ENV: import.meta.env.VITE_APP_ENV || 'development',
  VITE_DEBUG: import.meta.env.VITE_DEBUG === 'true',
  
  // ===== Mock数据开关 =====
  // true: 使用本地 Mock 数据，不请求后端
  // false: 请求真实后端 API（需确保后端可用）
  VITE_USE_MOCK: import.meta.env.VITE_USE_MOCK === 'true',

  // ===== DCloud univerify 一键登录 Mock 开关 =====
  // true: 跳过 uni.login 和云函数，直接 mock 手机号调后端
  // false: 走真实 univerify 流程（需审核通过）
  VITE_UNIVERIFY_MOCK_ENABLED: import.meta.env.VITE_UNIVERIFY_MOCK_ENABLED === 'true',
};

// 开发/生产环境自动检测
const isDev = typeof window !== 'undefined' && 
              (window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               ENV_CONFIG.VITE_APP_ENV === 'development');

// 导出到全局供 constants/api.ts 读取
declare global {
  interface Window {
    __ENV?: typeof ENV_CONFIG;
  }
}

if (typeof window !== 'undefined') {
  window.__ENV = ENV_CONFIG;
}