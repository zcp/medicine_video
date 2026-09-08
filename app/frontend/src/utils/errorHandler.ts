/**
 * 统一错误处理工具
 */

import type { ApiError } from '@/types/common'

/**
 * 统一错误处理函数
 * @param error API错误对象
 * @param showToast 是否显示Toast提示（默认true）
 */
export const handleApiError = (error: any, showToast = true): void => {
  const code = error?.code || error?.statusCode || 500
  let message = '操作失败，请重试'
  
  // HTTP状态码处理
  switch (code) {
    case 401:
      // Token过期或未认证
      message = '登录已过期，请重新登录'
      if (showToast) {
        uni.showToast({
          title: message,
          icon: 'none',
          duration: 2000,
          success: () => {
            // 跳转登录页（延迟500ms以显示Toast）
            setTimeout(() => {
              uni.navigateTo({ url: '/pages/app/auth/login' })
            }, 500)
          }
        })
      }
      break
      
    case 403:
      // 权限不足
      message = '权限不足，无法访问'
      if (showToast) {
        uni.showToast({ title: message, icon: 'none', duration: 2000 })
      }
      break
      
    case 404:
      // 资源不存在
      message = '请求的资源不存在'
      if (showToast) {
        uni.showToast({ title: message, icon: 'none', duration: 2000 })
      }
      break
      
    case 429:
      // 请求过于频繁
      message = '操作过于频繁，请稍后再试'
      if (showToast) {
        uni.showToast({ title: message, icon: 'none', duration: 2000 })
      }
      break
      
    case 500:
    case 502:
    case 503:
    case 504:
      // 服务器错误
      message = '服务器异常，请稍后重试'
      if (showToast) {
        uni.showToast({
          title: message,
          icon: 'none',
          duration: 2000
        })
      }
      break
      
    case -1:
      // 网络超时或连接失败
      message = '网络连接失败，请检查网络'
      if (showToast) {
        uni.showModal({
          title: '网络异常',
          content: message,
          showCancel: true,
          cancelText: '取消',
          confirmText: '重试',
          success: (res) => {
            if (res.confirm) {
              // 用户点击重试，可以在这里重新发起请求
              // 或者抛出一个特殊的错误码，由调用方处理
            }
          }
        })
      }
      break
      
    default:
      // 业务错误码（2xxx、3xxx、4xxx）
      message = error?.message || '操作失败，请重试'
      if (showToast) {
        uni.showToast({ title: message, icon: 'none', duration: 2000 })
      }
  }
  
  // 开发环境打印错误详情（生产环境不打印）
  if (import.meta.env.DEV) {
    console.error('[API Error]', {
      code,
      message,
      details: error?.details || error,
      timestamp: new Date().toISOString()
    })
  }
}
