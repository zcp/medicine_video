import { PAGE_PERMISSIONS } from '@/config/permission.config';
import { useAuthStore } from '@/store/auth';
import { hasMinRole } from '@/config/permission.config';
import type { UserRole } from '@/types/enums';

interface CheckResult {
  allowed: boolean;
  reason?: 'login_required' | 'permission_denied';
}

function checkAccess(url: string): CheckResult {
  let path = url.split('?')[0];

  // 优先精确匹配
  if (PAGE_PERMISSIONS[path]) {
    // 精确匹配，继续
  } else if (PAGE_PERMISSIONS[path + '/index']) {
    // 页面路径可能省略 /index 后缀
    path = path + '/index';
  } else {
    // 不在配置中 → 公开页面
    return { allowed: true };
  }

  const requiredRoles = PAGE_PERMISSIONS[path];

  const authStore = useAuthStore();

  if (!authStore.isAuthenticated) {
    return { allowed: false, reason: 'login_required' };
  }

  const userRole = authStore.user?.role as UserRole | undefined;
  if (!userRole || !requiredRoles.some(r => hasMinRole(userRole, r))) {
    return { allowed: false, reason: 'permission_denied' };
  }

  return { allowed: true };
}

function createInterceptor(type: 'navigateTo' | 'redirectTo' | 'switchTab' | 'reLaunch') {
  return {
    invoke(args: { url: string }) {
      const result = checkAccess(args.url);
      if (result.allowed) return;

      // 未登录 → 提示并阻止跳转
      if (result.reason === 'login_required') {
        uni.showToast({ title: '请先登录', icon: 'none' });
        return false;
      }

      // 有登录但权限不足 → toast + 跳首页
      if (result.reason === 'permission_denied') {
        uni.showToast({ title: '权限不足', icon: 'none' });
        if (type === 'switchTab' || type === 'reLaunch') {
          args.url = '/pages/app/tabbar/home/index';
        } else {
          // navigateTo/redirectTo 无法跳 TabBar 页面，用 switchTab 侧路
          uni.switchTab({ url: '/pages/app/tabbar/home/index' });
          // 覆盖目标阻止原跳转，防止权限绕过
          args.url = '/pages/app/tabbar/home/index';
        }
      }
    },
  };
}

export function setupRouteGuards() {
  uni.addInterceptor('navigateTo', createInterceptor('navigateTo'));
  uni.addInterceptor('redirectTo', createInterceptor('redirectTo'));
  uni.addInterceptor('switchTab', createInterceptor('switchTab'));
  uni.addInterceptor('reLaunch', createInterceptor('reLaunch'));
}
