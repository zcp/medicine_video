/**
 * 移动端布局尺寸工具
 * @description 提供 swiper 定高（方案A）所需的可用视口高度计算、rpx↔px 换算
 *
 * 背景：页面级 Tab（方案A）需要 swiper 显式高度 = 视口高度 - 顶部固定区高度。
 * 顶部固定区高度因页面而异（导航栏 / 搜索栏 / Tab 头），由调用方传入。
 */
import { ref, type Ref } from 'vue';

/** 系统信息（缓存，避免频繁同步调用 getSystemInfoSync） */
let cachedSystemInfo: UniApp.GetSystemInfoResult | null = null;

function getSystemInfo(): UniApp.GetSystemInfoResult {
  if (!cachedSystemInfo) {
    try {
      cachedSystemInfo = uni.getSystemInfoSync();
    } catch (e) {
      // 极端情况下返回空对象兜底
      cachedSystemInfo = {} as UniApp.GetSystemInfoResult;
    }
  }
  return cachedSystemInfo;
}

/** 重置系统信息缓存（如测试环境或横竖屏切换需要） */
export function resetSystemInfoCache(): void {
  cachedSystemInfo = null;
}

/** 状态栏高度（px） */
export function getStatusBarHeight(): number {
  return getSystemInfo().statusBarHeight || 0;
}

/** 可用视口高度（px，不含底部安全区） */
export function getWindowHeight(): number {
  return getSystemInfo().windowHeight || 0;
}

/** rpx → px 换算（750 设计稿基准） */
export function rpx2px(rpx: number): number {
  const w = getSystemInfo().windowWidth || 375;
  return Math.round((rpx * w) / 750);
}

/**
 * 计算页面级 Tab 的 swiper 定高
 * @param topFixedHeightPx 顶部固定区总高度（px）：导航栏 + 状态栏 + Tab 头等
 * @param bottomReservePx 底部预留（px，可选，如聊天输入框等 fixed 元素高度）
 */
export function calcSwiperHeight(topFixedHeightPx: number, bottomReservePx = 0): number {
  return Math.max(0, getWindowHeight() - topFixedHeightPx - bottomReservePx);
}

/**
 * 响应式页面高度 ref：监听 window resize 自动重算
 * @param topFixedHeightPxRef 顶部固定区高度（px，响应式）
 * @param bottomReservePx 底部预留（px）
 */
export function useResponsivePageHeight(
  topFixedHeightPxRef: Ref<number>,
  bottomReservePx = 0
): Ref<number> {
  const height = ref(calcSwiperHeight(topFixedHeightPxRef.value, bottomReservePx));

  const recalc = () => {
    height.value = calcSwiperHeight(topFixedHeightPxRef.value, bottomReservePx);
  };

  // 仅 H5 端有 window 概念；APP/小程序用页面级 uni 事件（onResize 由页面自行处理）
  if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('resize', recalc);
  }

  return height;
}
