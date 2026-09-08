/**
 * 业务枚举定义
 * 阶段一新建：2025
 * 集中管理所有业务枚举和中文映射
 */

/**
 * 用户角色枚举
 * 对应后端用户模块的角色定义
 * @remarks 值需与后端 API 类型保持一致（REGULAR | MODERATOR | ADMIN | SUPERADMIN）
 */
export enum UserRole {
  /** 普通用户 */
  REGULAR = 'REGULAR',
  /** 房管 */
  MODERATOR = 'MODERATOR',
  /** 管理员 */
  ADMIN = 'ADMIN',
  /** 超级管理员 */
  SUPERADMIN = 'SUPERADMIN',
}

/**
 * 收藏类型枚举
 * 用于user_favorites表的type字段
 */
export enum FavoriteType {
  /** 直播间 */
  ROOM = 'ROOM',
  /** 直播场次 */
  SESSION = 'SESSION',
  /** 专家 */
  EXPERT = 'EXPERT',
}

// ==================== 中文映射 ====================

/**
 * SessionStatus中文映射
 * SessionStatus定义在 src/types/session.ts 中
 * 'scheduled' | 'live' | 'finished' | 'processing' | 'ready' | 'error'
 */
export const SessionStatusLabel: Record<string, string> = {
  'scheduled': '预告',
  'live': '直播中',
  'finished': '已结束',
  'processing': '回放生成中',
  'ready': '回放',
  'error': '异常',
};

/**
 * 用户角色中文映射
 */
export const UserRoleLabel: Record<UserRole, string> = {
  [UserRole.REGULAR]: '普通用户',
  [UserRole.MODERATOR]: '房管',
  [UserRole.ADMIN]: '管理员',
  [UserRole.SUPERADMIN]: '超级管理员',
};

/**
 * 收藏类型中文映射
 */
export const FavoriteTypeLabel: Record<FavoriteType, string> = {
  [FavoriteType.ROOM]: '直播间',
  [FavoriteType.SESSION]: '直播场次',
  [FavoriteType.EXPERT]: '专家',
};

