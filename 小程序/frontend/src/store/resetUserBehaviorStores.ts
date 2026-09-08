/**
 * 登出 / 注销后清空观众端行为态，避免换号短暂露旧列表（对照《18》G2）
 *
 * 注意：各 Store 必须在函数内延迟加载，不可顶层 import。
 * 否则启动环 auth → reset → favorites → request → auth 会在小程序里
 * 表现为 common_vendor.defineStore is not a function。
 */

export function resetUserBehaviorStores(): void {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { useUserFavoritesStore } = require('./userFavorites') as typeof import('./userFavorites')
    useUserFavoritesStore().resetForLogout()
  } catch (e) {
    console.warn('[resetUserBehaviorStores] favorites', e)
  }
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { useUserSubscriptionsStore } = require('./userSubscriptions') as typeof import('./userSubscriptions')
    useUserSubscriptionsStore().resetForLogout()
  } catch (e) {
    console.warn('[resetUserBehaviorStores] subscriptions', e)
  }
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { useWatchHistoryStore } = require('./watchHistory') as typeof import('./watchHistory')
    useWatchHistoryStore().resetForLogout()
  } catch (e) {
    console.warn('[resetUserBehaviorStores] watchHistory', e)
  }
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { useNotificationsStore } = require('./notifications') as typeof import('./notifications')
    useNotificationsStore().clearNotificationsData()
  } catch (e) {
    console.warn('[resetUserBehaviorStores] notifications', e)
  }
}
