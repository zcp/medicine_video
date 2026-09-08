import { UserRole } from '@/types/enums';

// 角色等级（值越大权限越高）
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  [UserRole.REGULAR]: 0,
  [UserRole.MODERATOR]: 1,
  [UserRole.ADMIN]: 2,
  [UserRole.SUPERADMIN]: 3,
};

// 判断用户角色是否达到所需级别
export function hasMinRole(userRole: string, requiredRole: UserRole): boolean {
  const userLevel = ROLE_HIERARCHY[userRole as UserRole] ?? -1;
  const requiredLevel = ROLE_HIERARCHY[requiredRole];
  return userLevel >= requiredLevel;
}

// App 端页面权限映射（键为页面路径，值为有权限的角色列表）
// 未在此映射表中的页面视为公开页面（登录即可访问）
export const PAGE_PERMISSIONS: Record<string, UserRole[]> = {
  '/pages/app/admin/departments/index':     [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/expert-list/index':     [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/notification-push/index': [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/content-safety/index':   [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/room-review/index':     [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/featured/index':        [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/users/index':           [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/tags/index':            [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/brands/index':          [UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/admin/messages/index':        [UserRole.ADMIN, UserRole.SUPERADMIN],
  // room-tabs 不登记全局守卫（融合方案 F1b：非管理员房主可管理自己房间 Tab，页面内校验兜底）
  // "我的"子页面（需登录）
  '/pages/app/tabbar/my/follows/index':     [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/tabbar/my/favorites/index':   [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/tabbar/my/subscriptions/index': [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/tabbar/my/watch-history/index': [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/tabbar/my/account-security/index': [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/tabbar/my/edit-profile/index': [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
  '/pages/app/tabbar/my/account-security/bind-phone/index': [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
};

// 操作权限映射（用于按钮/功能级控制）
export const ACTION_PERMISSIONS = {
  'create-live':        [UserRole.REGULAR, UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN],
  'manage-department':  [UserRole.ADMIN, UserRole.SUPERADMIN],
  'manage-expert':      [UserRole.ADMIN, UserRole.SUPERADMIN],
  'push-notification':  [UserRole.ADMIN, UserRole.SUPERADMIN],
  'manage-featured':    [UserRole.ADMIN, UserRole.SUPERADMIN],
  'manage-users':       [UserRole.SUPERADMIN],
  'manage-brands':      [UserRole.ADMIN, UserRole.SUPERADMIN],
  'manage-categories':  [UserRole.ADMIN, UserRole.SUPERADMIN],
  'manage-tags':        [UserRole.ADMIN, UserRole.SUPERADMIN],
} as const;
