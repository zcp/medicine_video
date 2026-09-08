/**
 * 环境配置测试文件
 * 用于验证环境变量是否正确加载
 */

import { ENV_CONFIG } from '../config/env';

// 测试环境配置
export const testEnvConfig = () => {
  console.log('=== 环境配置测试 ===');
  console.log('API_BASE_URL:', ENV_CONFIG.API_BASE_URL);
  console.log('API_VERSION:', ENV_CONFIG.API_VERSION);
  console.log('APP_ENV:', ENV_CONFIG.APP_ENV);
  console.log('DEBUG:', ENV_CONFIG.DEBUG);
  console.log('FULL_API_BASE_URL:', ENV_CONFIG.FULL_API_BASE_URL);
  console.log('==================');
  
  return {
    apiBaseUrl: ENV_CONFIG.API_BASE_URL,
    fullApiUrl: ENV_CONFIG.FULL_API_BASE_URL,
    isDevelopment: ENV_CONFIG.APP_ENV === 'development',
    isDebug: ENV_CONFIG.DEBUG
  };
};

// 测试环境变量是否可用
export const testEnvVars = () => {
  console.log('=== 环境变量测试 ===');
  
  // #ifdef H5
  // 测试Vite环境变量（仅 H5 环境）
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
    console.log('VITE_APP_ENV:', import.meta.env.VITE_APP_ENV);
    console.log('VITE_API_VERSION:', import.meta.env.VITE_API_VERSION);
    console.log('VITE_DEBUG:', import.meta.env.VITE_DEBUG);
  } else {
    console.log('import.meta.env 不可用');
  }
  // #endif
  
  // #ifndef H5
  console.log('非 H5 环境，跳过 import.meta.env 测试');
  // #endif
  
  // 测试process.env
  if (typeof process !== 'undefined' && process.env) {
    console.log('process.env.NODE_ENV:', process.env.NODE_ENV);
  } else {
    console.log('process.env 不可用');
  }
  
  console.log('==================');
}; 