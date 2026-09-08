/**
 * useSwiperTabs
 * @description Tab 头点击 ↔ 内容区左右滑动 双向联动的通用 composable
 *
 * 设计要点：
 * - activeIndex 作为唯一数据源，Tab 头点击与 swiper 滑动都写它，天然双向同步
 * - 同索引判重：@change 事件多端可能重复触发（iOS 已知问题），同索引直接 return
 * - onActivate 钩子在索引真正变化时立即触发（请求/分类/切 store 等业务逻辑）
 * - 支持响应式 total：当 Tab 列表异步加载（初始为 0 后变为 N）时，total 变化会自动
 *   归一化 activeIndex，避免越界导致高亮消失/内容不渲染
 */
import { ref, type Ref } from 'vue';

/** swiper change 事件的 detail 结构（uni-app 各端一致） */
export interface SwiperChangeEvent {
  detail: { current: number };
}

/**
 * 使用滑动 Tab
 * @param total  Tab 总数（支持 Ref，异步加载场景传入 ref 或响应式 getter）
 * @param onActivate  索引真正变化时触发的业务钩子（可 async）
 * @param initialIndex 初始索引
 */
export function useSwiperTabs(
  total: number | Ref<number>,
  onActivate: (index: number) => void | Promise<void>,
  initialIndex = 0
) {
  /** 当前激活索引（0 起） */
  const activeIndex: Ref<number> = ref(initialIndex);

  /** 当前 tab 总数（归一化时取最新的值） */
  function getTotal(): number {
    if (typeof total === 'number') return total;
    return total.value;
  }

  /**
   * 归一化索引，防止越界（total 为 0 时归 0，避免 -1）
   */
  function normalizeIndex(idx: number): number {
    const t = getTotal();
    if (t <= 0) return 0;
    if (idx < 0) return 0;
    if (idx >= t) return t - 1;
    return idx;
  }

  /**
   * 切换索引（Tab 头点击 / swiper 滑动共用）
   */
  function setActive(index: number): void {
    const idx = normalizeIndex(index);
    if (idx === activeIndex.value) return;
    activeIndex.value = idx;
    void onActivate(idx);
  }

  /**
   * Tab 头点击处理
   */
  function handleTabTap(index: number): void {
    setActive(index);
  }

  /**
   * swiper 滑动/翻页 change 处理
   * @description 同索引判重防止 iOS/各端重复触发；索引变化则立即触发业务钩子
   */
  function handleSwiperChange(e: SwiperChangeEvent): void {
    const idx = normalizeIndex(e.detail.current);
    if (idx === activeIndex.value) return;
    activeIndex.value = idx;
    void onActivate(idx);
  }

  /**
   * 等待 swiper 动画结束（供需要动画结束后再测高/操作布局的场景使用，如首页模块级 Tab）
   */
  function waitForSwiperSettle(duration = 300): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(resolve, duration);
    });
  }

  return {
    activeIndex,
    handleTabTap,
    handleSwiperChange,
    setActive,
    waitForSwiperSettle,
  };
}
