import type { Directive } from 'vue';
import { useAuthStore } from '@/store/auth';
import { hasMinRole } from '@/config/permission.config';
import type { UserRole } from '@/types/enums';

export const vPermission: Directive<any, UserRole> = {
  mounted(el, binding) {
    const requiredRole = binding.value;
    if (!requiredRole) return;

    const authStore = useAuthStore();
    const userRole = authStore.user?.role;

    if (!userRole || !hasMinRole(userRole, requiredRole)) {
      el.style.display = 'none';
      if (import.meta.env.DEV) {
        console.warn(
          `[v-permission] 元素已隐藏：需要角色 ${requiredRole}，当前用户角色 ${userRole || '未登录'}`
        );
      }
    }
  },
};
