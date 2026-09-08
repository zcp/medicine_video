// API地址常量定义 - 直接使用配置对象，避免环境变量读取问题
import { ENV_CONFIG } from '@/config/env';

// 直接使用配置对象，确保配置值正确读取
export const BASE_API_URL = ENV_CONFIG.VITE_BASE_API_URL.replace(/\/?$/, '/');
export const AUTH_API_URL = ENV_CONFIG.VITE_AUTH_API_URL.replace(/\/?$/, '/');
export const LOGIN_URL = ENV_CONFIG.VITE_LOGIN_URL;
export const FRONTEND_USER_URL = ENV_CONFIG.VITE_FRONTEND_USER_URL;
export const APP_TITLE = ENV_CONFIG.VITE_APP_TITLE;
export const API_TIMEOUT = parseInt(ENV_CONFIG.VITE_API_TIMEOUT) || 30000;

export const APP_BASE_PATH = ENV_CONFIG.VITE_APP_BASE_PATH;
export const AUTH_REDIRECT_PATH = ENV_CONFIG.VITE_AUTH_REDIRECT_PATH || '/pages/app/tabbar/home/index';

// 添加调试日志
console.log('API配置加载成功:', {
  LOGIN_URL,
  FRONTEND_USER_URL,
  BASE_API_URL
});
