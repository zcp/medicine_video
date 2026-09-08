import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { normalizePath } from '@/common/authRoutes'

const TABBAR_PATHS = [
  '/pages/home/Home',
  '/pages/brand/BrandZone',
  '/pages/expert/ExpertList',
  '/pages/profile/Profile'
]

function safeRedirect(url: string): void {
  const target = String(url || '').trim() || '/pages/home/Home'
  const path = normalizePath(target)
  if (TABBAR_PATHS.indexOf(path) >= 0) {
    uni.switchTab({ url: path })
    return
  }
  uni.redirectTo({ url: target })
}

/**
 * 认证页 redirect 参数解析与登录成功后跳转
 */
export function useAuthRedirect(defaultRedirect = '/pages/home/Home') {
  const redirect = ref<string>(defaultRedirect)

  onLoad((options?: { redirect?: string }) => {
    if (options?.redirect) {
      try {
        redirect.value = decodeURIComponent(options.redirect)
      } catch {
        redirect.value = options.redirect
      }
    }
  })

  function redirectQuery(): string {
    return `redirect=${encodeURIComponent(redirect.value)}`
  }

  function finishAuth(): void {
    safeRedirect(redirect.value)
  }

  return {
    redirect,
    redirectQuery,
    finishAuth
  }
}
