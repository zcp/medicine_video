/**
 * 权限检查工具函数
 * @description 提供统一的权限拦截、角色校验和登录跳转机制
 */

import { useAuthStore } from '@/store/auth';
import { hasMinRole, PAGE_PERMISSIONS, ACTION_PERMISSIONS } from '@/config/permission.config';
import type { UserRole } from '@/types/enums';

/**
 * 权限检查函数
 * @description 检查用户是否已登录，未登录则提示并返回上一页
 * @returns 是否已登录
 * 
 * @example
 * // 在需要登录的页面使用
 * onMounted(() => {
 *   if (!requireAuth()) {
 *     return; // 未登录会提示并返回上一页
 *   }
 *   loadData();
 * });
 * 
 * @example
 * // 在点赞、评论等功能中使用
 * const handleLike = () => {
 *   if (!requireAuth()) {
 *     return; // 未登录会提示留在当前页面
 *   }
 *   likeApi();
 * };
 */
export const requireAuth = (): boolean => {
  const authStore = useAuthStore();
  
  if (!authStore.isAuthenticated) {
    console.log('❌ 未登录，返回上一页');
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => {
        uni.switchTab({ url: '/pages/app/tabbar/home/index' });
      }
    });
    return false;
  }
  
  console.log('✅ 已登录，继续执行');
  return true;
};

/**
 * 获取当前页面路径
 * @description 获取当前页面的完整路径（包含路由前缀）
 * @returns 当前页面路径
 * 
 * @example
 * const path = getCurrentPagePath();
 * // 返回: "/pages/app/tabbar/my/favorites/index"
 */
export const getCurrentPagePath = (): string => {
  const pages = getCurrentPages();
  if (pages.length === 0) {
    return '/pages/app/tabbar/home/index'; // 默认首页
  }
  
  const currentPage = pages[pages.length - 1];
  const route = currentPage.route || '';
  
  // 确保路径以 / 开头
  return route.startsWith('/') ? route : `/${route}`;
};

/**
 * 检查用户是否拥有指定角色中的任意一个
 * @param roles 允许的角色列表
 * @returns 是否拥有权限
 * 
 * @example
 * if (hasRole(UserRole.ADMIN, UserRole.SUPERADMIN)) {
 *   // 管理员操作
 * }
 */
export const hasRole = (...roles: UserRole[]): boolean => {
  const authStore = useAuthStore();
  if (!authStore.isAuthenticated || !authStore.user?.role) return false;
  return roles.some(r => hasMinRole(authStore.user!.role!, r));
};

/**
 * 检查用户是否有权限访问指定页面
 * @param pagePath 页面路径（如 '/pages/app/admin/departments'）
 * @returns 是否有访问权限
 */
export const canAccessPage = (pagePath: string): boolean => {
  const requiredRoles = PAGE_PERMISSIONS[pagePath];
  if (!requiredRoles) return true; // 未配置的页面默认公开
  return hasRole(...requiredRoles);
};

/**
 * 检查用户是否有权限执行指定操作
 * @param action 操作标识
 * @returns 是否有执行权限
 */
export const canPerformAction = (action: keyof typeof ACTION_PERMISSIONS): boolean => {
  const requiredRoles = ACTION_PERMISSIONS[action];
  if (!requiredRoles) return false;
  return hasRole(...requiredRoles);
};

/**
 * 🔴 P0: 检查用户是否有创建直播的权限
 * @description 已登录且状态正常的非管理员用户可以创建直播（管理员不担任房主，产品口径前端限制）
 * @returns 是否有创建直播权限
 * 
 * @example
 * // 在创建直播按钮点击时使用
 * const handleCreateLive = () => {
 *   if (!canCreateLive()) {
 *     return; // 会自动显示提示
 *   }
 *   // 打开创建直播弹窗
 *   showCreateModal.value = true;
 * };
 */
export const canCreateLive = (): boolean => {
  const authStore = useAuthStore();
  
  // 1. 检查是否已登录
  if (!authStore.isAuthenticated || !authStore.user) {
    return false;
  }
  
  // 2. 检查用户状态（被封禁、删除、待审核的用户不能创建直播）
  if (authStore.user.status !== 'NORMAL') {
    return false;
  }
  
  // 3. 管理员排除（产品口径：管理员不当房主、不创建直播；统一走全站房间管理）
  if (authStore.isAdmin) {
    return false;
  }
  
  // 4. 根据后端API文档（直播核心功能设计文档_v6_深度融合最终版.md 第880行）：
  //    "所有以下API接口都需要JWT Token认证"
  //    普通用户无额外角色权限要求，因此已登录且状态正常即可创建直播（管理员除外，见 3）
  return true;
};

/**
 * 🔴 P0: 检查用户是否已登录
 * @description 简单检查用户登录状态
 * @returns 是否已登录
 * 
 * @example
 * if (!isLoggedIn()) {
 *   navigateToLogin();
 * }
 */
export const isLoggedIn = (): boolean => {
  const authStore = useAuthStore();
  return authStore.isAuthenticated;
};

/**
 * 🔴 P0: 导航到登录页面并记录重定向路径
 * @description 跳转到登录页面，登录成功后自动返回指定页面
 * @param redirectPath 登录成功后要跳转的路径（可选）
 * 
 * @example
 * // 从创建直播页面跳转到登录
 * navigateToLogin('/pages/app/live-manage/create');
 */
export const navigateToLogin = (redirectPath?: string): void => {
  const targetPath = redirectPath || getCurrentPagePath();
  
  console.log('📍 记录登录后回跳路径:', targetPath);
  uni.setStorageSync('loginRedirectPath', targetPath);
  
  uni.navigateTo({
    url: '/pages/app/auth/login',
    fail: (err) => {
      console.error('⚠️ 跳转登录页失败:', err);
      uni.redirectTo({
        url: '/pages/app/auth/login'
      });
    }
  });
};

/**
 * 🔴 P0: 检查创建直播权限并显示相应提示
 * @description 统一的创建直播权限检查，包含登录检查和权限检查
 * @param redirectPath 登录成功后要跳转的路径（可选）
 * @returns 是否有权限创建直播
 * 
 * @example
 * // 在TabBar中间按钮点击时使用
 * const handleCenterClick = () => {
 *   if (!checkCreateLivePermission()) {
 *     return; // 会自动显示相应提示
 *   }
 *   // 打开创建直播弹窗
 *   showCreateModal.value = true;
 * };
 */
export const checkCreateLivePermission = (redirectPath?: string): boolean => {
  const authStore = useAuthStore();
  
  // 1. 检查是否登录
  if (!authStore.isAuthenticated || !authStore.user) {
    uni.showModal({
      title: '需要登录',
      content: '创建直播需要先登录，是否前往登录？',
      confirmText: '去登录',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          navigateToLogin(redirectPath);
        }
      }
    });
    return false;
  }
  
  // 2. 检查是否有创建直播权限
  if (!canCreateLive()) {
    uni.showModal({
      title: '权限不足',
      content: '您暂无创建直播的权限，请联系管理员开通主播权限',
      showCancel: false,
      confirmText: '我知道了'
    });
    return false;
  }
  
  return true;
};


