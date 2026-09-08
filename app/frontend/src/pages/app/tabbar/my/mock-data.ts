/**
 * "我的"页面Mock数据
 * @description 用于开发阶段，当 ENV_CONFIG.VITE_USE_MOCK = true 时使用
 * @file src/pages/app/tabbar/my/mock-data.ts
 */

/**
 * 用户统计数据
 * @description 收藏、关注数量
 */
export const mockUserStats = {
  favorites_count: 12,
  follow_count: 5,
};

/**
 * 用户扩展信息
 * @description 认证徽章等信息（auth.ts中的User接口暂不包含这些字段）
 */
export const mockUserProfile = {
  is_broadcaster: true,
  is_expert: false,
};
