/**
 * useAdminGuard
 * @description 管理端页面级守卫组合式函数（P0 基建）
 *
 * 设计要点：
 * - 定位为「页面级校验」：入口可见性已由 my/index.vue 的 v-if="authStore.isAdmin" 控制，
 *   本守卫负责用户直达 URL / 深链时的二次兜底
 * - 未登录：跳转登录页并带回跳参数（APP_LOGIN_PATH?redirect=<当前页>）
 * - 非管理员：toast 提示并返回上一页（无上一页则回「我的」页）
 * - 判定使用 authStore.isAuthenticated（state）与 isAdmin（getter），role 由后端统一大写
 *
 * 用法（onShow 中调用）：
 *   import { useAdminGuard } from '@/composables/useAdminGuard';
 *   onShow(() => { if (!useAdminGuard()) return; ... })
 */
import { useAuthStore } from '@/store/auth';
import { APP_LOGIN_PATH } from '@/constants/routes';

/**
 * 管理端页面守卫
 * @param redirectPath 登录后回跳路径；默认取当前页面路径（含参数）
 * @returns 是否具备管理员访问资格（true=放行，false=已拦截）
 */
export function useAdminGuard(redirectPath?: string): boolean {
  const authStore = useAuthStore();

  // 未登录：跳登录页带回跳
  if (!authStore.isAuthenticated) {
    const target = redirectPath || getCurrentPagePath();
    uni.navigateTo({
      url: `${APP_LOGIN_PATH}?redirect=${encodeURIComponent(target)}`,
    });
    return false;
  }

  // 非管理员：提示并返回
  if (!authStore.isAdmin) {
    uni.showToast({ title: '暂无访问权限', icon: 'none' });
    // 有上一页则返回，否则回「我的」页
    const pages = getCurrentPages();
    if (pages.length > 1) {
      uni.navigateBack();
    } else {
      uni.reLaunch({ url: '/pages/app/tabbar/my/index' });
    }
    return false;
  }

  return true;
}

/**
 * 获取当前页面路径（含 query 参数），供登录后回跳使用
 */
function getCurrentPagePath(): string {
  const pages = getCurrentPages();
  const current = pages[pages.length - 1];
  if (!current) return '';
  const route = (current as any).route || '';
  const options = (current as any).options || {};
  const query = Object.keys(options)
    .map((k) => `${k}=${encodeURIComponent(options[k])}`)
    .join('&');
  return query ? `/${route}?${query}` : `/${route}`;
}
