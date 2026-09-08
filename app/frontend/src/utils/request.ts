/**
 * 统一网络请求工具
 * 封装uni.request，提供请求拦截器和响应拦截器
 */

import { ENV_CONFIG } from '../config/env';
import { getToken } from '@/store/auth';
import { useAuthStore } from '@/store/auth';
import { isContentSafetyCode, getContentSafetyMessage } from '@/utils/contentSafety';

// API基础URL，从环境配置中获取
const BASE_URL = ENV_CONFIG.VITE_BASE_API_URL;

// 获取认证Token的函数，从认证模块中获取
const getAuthToken = (): string => {
  const token = getToken();
  console.log('🔍 getAuthToken调用:', {
    hasToken: !!token,
    tokenLength: token ? token.length : 0,
    tokenPreview: token ? `${token.substring(0, 20)}...` : 'null'
  });
  return token || '';
};

/**
 * 从 document.cookie 中读取csrftoken（仅 H5 环境）
 */
const getCsrfToken = (): string | null => {
  // #ifdef H5
  if (typeof document !== 'undefined' && typeof document.cookie !== 'undefined') {
    const csrfCookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : null;
  }
  // #endif
  return null;
};

/**
 * 请求配置接口
 */
interface RequestOptions {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'OPTIONS' | 'HEAD' | 'TRACE' | 'CONNECT' | 'PATCH';
  data?: any;
  header?: Record<string, string>;
  // 是否显示加载提示
  showLoading?: boolean;
  // 是否需要认证
  auth?: boolean;
}

/**
 * 统一请求函数
 * @param options 请求配置
 * @param retry 重试次数，默认3次
 * @param timeout 超时时间，默认5000ms
 * @returns Promise 返回请求结果
 */
export const request = async <T = any>(options: RequestOptions, retry = 3, timeout = 5000): Promise<T> => {
  // 显示加载提示
  if (options.showLoading !== false) {
    uni.showLoading({
      title: '加载中...',
      mask: true
    });
  }

  // 调试信息：记录请求开始
  console.log('🌐 请求开始:', {
    url: options.url,
    method: options.method,
    data: options.data,
    retry: retry,
    timeout: timeout,
    timestamp: new Date().toISOString()
  });

  // 测试阶段：网络诊断
  const fullUrl = /^(http|https):\/\//.test(options.url) 
    ? options.url 
    : BASE_URL.replace(/\/+$/, '') + '/' + options.url.replace(/^\/+/, '');
    
  // #ifdef H5
  console.log('🔍 网络诊断信息:', {
    url: options.url,
    baseUrl: BASE_URL,
    fullUrl: fullUrl,
    env: process.env.NODE_ENV,
    userAgent: navigator?.userAgent || 'unknown'
  });

  // 测试阶段：检查网络连接
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    console.warn('⚠️ 检测到离线状态，请检查网络连接');
  }
  // #endif

  // 构建完整URL（修复双斜杠问题）
  const url = /^(http|https):\/\//.test(options.url) 
    ? options.url 
    : BASE_URL.replace(/\/+$/, '') + '/' + options.url.replace(/^\/+/, '');

  // 测试阶段：完全绕过HTTPS验证（生产环境请恢复此验证）
  if (
    process.env.NODE_ENV === 'production' &&
    !/^https:\/\//.test(url)
  ) {
    console.warn('⚠️ 测试阶段：生产环境使用HTTP协议，请确保安全！');
    // 测试阶段暂时注释掉HTTPS验证
    // uni.hideLoading();
    // throw new Error('安全限制：仅允许通过 HTTPS 协议请求 API！');
  }
  
  // 测试阶段：允许所有HTTP请求
  if (/^http:\/\//.test(url)) {
    console.warn('🔧 测试阶段：使用 HTTP 协议，生产环境请使用 HTTPS');
  }

  // 构建请求头
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    // 🔴 ngrok 免费版会拦截浏览器请求，加此 Header 跳过警告页
    'ngrok-skip-browser-warning': 'true',
    ...options.header,
  };

  // 自动注入JWT Token（增量开发：JWT认证拦截器）
  let token = getAuthToken();
  console.log('🔑 请求认证Token:', {
    hasToken: !!token,
    tokenLength: token ? token.length : 0,
    tokenPreview: token ? `${token.substring(0, 20)}...` : 'null'
  });
  
  // 检查Token是否即将过期（提前5分钟刷新）
  // 🔴 关键修复：跳过刷新Token的请求，避免死循环
  const isRefreshRequest = url.includes('/auth/refresh');
  if (token && options.auth !== false && !isRefreshRequest) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
      const currentTime = Date.now() / 1000;
      const timeUntilExpiry = payload.exp - currentTime;
      
      // 如果Token在5分钟内过期，尝试刷新
      if (timeUntilExpiry < 300 && timeUntilExpiry > 0) {
        console.log('⏰ Token即将过期，尝试自动刷新...', {
          剩余时间: Math.floor(timeUntilExpiry) + '秒'
        });
        
        try {
          const authStore = useAuthStore();
          const refreshSuccess = await authStore.refreshAccessToken();
          
          if (refreshSuccess) {
            token = getAuthToken(); // 获取新Token
            console.log('✅ Token自动刷新成功');
          } else {
            console.warn('⚠️ Token自动刷新失败，使用旧Token继续请求');
          }
        } catch (error) {
          console.error('❌ Token自动刷新异常:', error);
          // 继续使用旧Token
        }
      }
    } catch (error) {
      console.error('❌ 解析Token失败:', error);
    }
  }
  
  // 验证JWT格式
  const isValidJWT = token && token.split('.').length === 3;
  console.log('🔍 JWT格式验证:', {
    isValid: isValidJWT,
    parts: token ? token.split('.').length : 0
  });
  
  if (token && token.trim() && isValidJWT) {
    // auth:false 为匿名请求语义：不注入 Authorization 头。
    // 若注入已过期 token，后端 optional-auth 接口会严格 401（不降级匿名），导致公开接口静默失败。
    if (options.auth !== false) {
      header['Authorization'] = `Bearer ${token}`;
      // 如果Bearer格式不工作，可以尝试：
      // header['Authorization'] = `JWT ${token}`;
      // header['Authorization'] = token;
      // header['X-Auth-Token'] = token;
      console.log('✅ 已添加认证头:', `Bearer ${token.substring(0, 20)}...`);
    } else {
      console.log('ℹ️ 匿名请求（auth:false），跳过Token注入');
    }
  } else {
    console.log('❌ 未找到有效认证Token或格式错误，请求可能失败');
  }

  // 添加CSRF Token
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    header['X-CSRFToken'] = csrfToken;
  }

  // 调试：打印完整请求头
  console.log('📋 完整请求头:', header);

  return new Promise<T>((resolve, reject) => {
    let isTimeout = false;
    const timer = setTimeout(() => {
      isTimeout = true;
      uni.hideLoading();
      reject(new Error('请求超时'));
    }, timeout);

    uni.request({
      url,
      method: options.method as any || 'GET',
      data: options.data,
      header,
      success: (res: any) => {
        clearTimeout(timer);
        if (isTimeout) return;
        
        console.log('🌐 [DEBUG] 请求成功响应:', {
          statusCode: res.statusCode,
          url: url,
          data: res.data,
          dataType: typeof res.data
        });
        
        if (res.statusCode >= 200 && res.statusCode < 300) {
          console.log('✅ [DEBUG] 请求成功，返回数据:', res.data);
          
          // 业务码校验：2xx 但 body.code 非 200/0 → 业务错误（避免静默成功）
          const body = res.data as any;
          if (body && typeof body === 'object' && typeof body.code === 'number' && body.code !== 200 && body.code !== 0) {
            const bizError: any = new Error(body.message || `业务错误: ${body.code}`);
            bizError.code = body.code;
            bizError.statusCode = res.statusCode;
            bizError.data = body.data;
            bizError.fullResponse = res.data;
            console.error('❌ [业务码校验] 非成功业务码:', body.code, body.message);
            reject(bizError);
            return;
          }
          
          resolve(res.data as T);
                 } else if (res.statusCode === 401) {
           // 增量开发：401认证失败处理
           console.error('🔐 401认证失败 - 完整响应:', {
             statusCode: res.statusCode,
             data: res.data,
             headers: res.header,
             url: url
           });
           
           // 🔧 如果是登录接口返回401，不要强制跳转，而是抛出错误让登录页面处理
           if (url.includes('/auth/login')) {
             console.log('🔍 [诊断] 登录接口返回401，详细信息:');
             console.log('  - 错误码:', res.data?.code);
             console.log('  - 错误消息:', res.data?.message);
             console.log('  - 完整数据:', res.data);
             
             // 构造错误对象，包含后端返回的详细信息
             const error: any = new Error(res.data?.message || 'Unauthorized');
             error.code = res.data?.code;
             error.statusCode = res.statusCode;
             error.data = res.data;
             reject(error);
             return;
           }
           
            try {
              const authStore = useAuthStore();
              // 仅当用户曾持有有效token（非游客状态）才跳转登录
              if (authStore.token) {
                const currentPath = getCurrentPages()[getCurrentPages().length - 1].route;
                authStore.forceReauth(`/pages/${currentPath}`);
              }
            } catch (error) {
             console.error('认证失败处理错误:', error);
             uni.showToast({
               title: '登录已过期，请重新登录',
               icon: 'none',
               duration: 2000
             });
           }
           reject(new Error('Unauthorized'));
        } else if (res.statusCode === 403) {
          uni.showToast({
            title: '您没有权限执行此操作',
            icon: 'none',
            duration: 2000
          });
          reject(new Error('Forbidden'));
        } else if (res.statusCode === 404) {
          uni.showToast({
            title: '请求的资源不存在',
            icon: 'none',
            duration: 2000
          });
          reject(new Error('Not Found'));
        } else if (res.statusCode === 422) {
          // 422 参数验证失败 - 详细诊断
          console.error('❌ [422错误] 参数验证失败:', {
            url,
            method: options.method,
            statusCode: res.statusCode,
            requestData: options.data,
            responseBody: res.data,
            responseType: typeof res.data,
            responseKeys: res.data ? Object.keys(res.data) : [],
            headers: res.header
          });
          
          // 尝试解析错误详情
          let errorDetail = '参数验证失败';
          if (res.data) {
            if (typeof res.data === 'string') {
              errorDetail = res.data;
            } else if (res.data.detail) {
              errorDetail = typeof res.data.detail === 'string' 
                ? res.data.detail 
                : JSON.stringify(res.data.detail);
            } else if (res.data.message) {
              errorDetail = res.data.message;
            }
          }
          
          console.error('🔍 [422错误详情]:', errorDetail);
          
          const error: any = new Error(errorDetail);
          error.statusCode = 422;
          error.code = res.data?.code;
          error.data = res.data;
          error.detail = errorDetail;
          error.fullResponse = res;
          
          // 内容安全错误（2004/2005）统一友好文案 + 完整 toast（不截断）+ 防双重提示标记
          if (isContentSafetyCode(Number(res.data?.code))) {
            const friendly = getContentSafetyMessage(Number(res.data?.code), errorDetail);
            error.message = friendly;
            error.__toasted = true;
            uni.showToast({ title: friendly, icon: 'none', duration: 3000 });
          } else {
            uni.showToast({
              title: errorDetail.length > 20 ? errorDetail.substring(0, 20) + '...' : errorDetail,
              icon: 'none',
              duration: 3000
            });
          }
          
          reject(error);
        } else {
          console.error(`HTTP Error: ${res.statusCode}`, {
            url,
            method: options.method,
            requestData: options.data,
            responseBody: res.data,
          });
          
          // 构造包含完整错误信息的 error 对象
          const backendData = res.data || {};
          const errorMessage = backendData.message || `HTTP Error: ${res.statusCode}`;
          const error: any = new Error(errorMessage);
          error.statusCode = res.statusCode;
          error.code = backendData.code;
          error.message = errorMessage;
          error.data = backendData.data;
          error.fullResponse = res.data;
          
          console.log('🔍 [诊断] 构造错误对象:', {
            statusCode: error.statusCode,
            code: error.code,
            message: error.message,
            data: error.data
          });
          
          // 对于登录接口，不显示 toast（让页面自己处理错误提示）
          if (!url.includes('/auth/login')) {
            // 内容安全错误（2004/2005）统一友好文案 + 完整 toast（不截断）+ 防双重提示标记
            if (isContentSafetyCode(Number(backendData.code))) {
              const friendly = getContentSafetyMessage(Number(backendData.code), errorMessage);
              error.message = friendly;
              error.__toasted = true;
              uni.showToast({ title: friendly, icon: 'none', duration: 3000 });
            } else {
              uni.showToast({
                title: errorMessage.length > 20 ? errorMessage.substring(0, 20) + '...' : errorMessage,
                icon: 'none',
                duration: 2000
              });
            }
          }
          
          reject(error);
        }
      },
                   fail: (err) => {
        clearTimeout(timer);
        if (isTimeout) return;
        
        // 详细错误日志
        console.error('🔍 请求失败详情:', {
          error: err,
          errorMessage: err.errMsg,
          url: url,
          method: options.method,
          headers: header,
          retryCount: retry,
          timeout: timeout,
          timestamp: new Date().toISOString()
        });
         
         // 网络错误处理
         let errorMessage = '网络请求失败';
         if (err.errMsg) {
           if (err.errMsg.includes('timeout')) {
             errorMessage = '请求超时，请检查网络';
           } else if (err.errMsg.includes('fail')) {
             errorMessage = '网络连接失败，请检查网络设置';
           } else if (err.errMsg.includes('proxy')) {
             errorMessage = '代理连接失败，请检查网络配置';
           } else if (err.errMsg.includes('401')) {
             errorMessage = '认证失败，请重新登录';
           } else if (err.errMsg.includes('403')) {
             errorMessage = '权限不足';
           } else if (err.errMsg.includes('404')) {
             errorMessage = '请求的资源不存在';
           } else if (err.errMsg.includes('500')) {
             errorMessage = '服务器内部错误';
           }
         }
         
                 // 只对GET请求和幂等操作进行重试，避免POST/PUT/DELETE重复操作
        const isIdempotentMethod = options.method === 'GET' || options.method === 'HEAD' || options.method === 'OPTIONS';
        
        if (retry > 0 && isIdempotentMethod) {
          // 自动重试（仅GET等幂等请求）
          console.log(`🔄 请求失败，${retry}秒后重试...`, {
            originalError: err.errMsg,
            retryCount: retry,
            url: url,
            method: options.method,
            timestamp: new Date().toISOString()
          });
          setTimeout(() => {
            request(options, retry - 1, timeout).then(resolve).catch(reject);
          }, 1000); // 增加重试延迟到1秒
        } else if (retry > 0 && !isIdempotentMethod) {
          // POST/PUT/DELETE请求不自动重试，避免重复操作
          console.warn('⚠️ 非幂等请求失败，不自动重试:', {
            method: options.method,
            url: url,
            error: err.errMsg
          });
          uni.showToast({
            title: errorMessage,
            icon: 'none',
            duration: 2000
          });
          reject(err);
        } else {
           console.error('❌ 最终请求失败:', {
             error: err,
             errorMessage: errorMessage,
             url: url
           });
           uni.showToast({
             title: errorMessage,
             icon: 'none',
             duration: 2000
           });
           reject(err);
         }
       },
      complete: () => {
        clearTimeout(timer);
        if (options.showLoading !== false) {
          uni.hideLoading();
        }
      }
    });
  });
};

/**
 * 统一GET请求
 * @param url 请求地址
 * @param data 请求参数
 * @param options 其他选项
 * @param requestOptions 请求级参数（可选：retry 重试次数 / timeout 超时毫秒；缺省沿用全局默认 3 次 / 5000ms）
 * @returns Promise
 */
export const get = <T = any>(
  url: string,
  data?: any,
  options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {},
  requestOptions: { retry?: number; timeout?: number } = {}
) => {
  return request<T>(
    {
      url,
      method: 'GET',
      data,
      ...options
    },
    requestOptions.retry,
    requestOptions.timeout
  );
};

/**
 * 统一POST请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const post = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'POST',
    data,
    ...options
  }, 0, 5000); // 禁用重试机制，避免重复创建
};

/**
 * 统一PUT请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const put = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'PUT',
    data,
    ...options
  });
};

/**
 * 统一DELETE请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const del = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'DELETE',
    data,
    ...options
  }, 0, 5000); // 禁用重试机制，避免重复删除
};

/**
 * 统一PATCH请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const patch = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'PATCH',
    data,
    ...options
  }, 0, 5000); // 禁用重试机制，避免重复操作
}; 