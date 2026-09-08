<!--
 * StickyTabPager - 吸顶 Tab + 跟手横滑 Pager
 * @description
 * - 默认：定高 swiper（少数内层定高场景）
 * - flow：只渲染当前 pane，内容随文档流撑高；手势横滑切 Tab（首页 / 直播间功能 Tab）
 *   避免微信 swiper 定高裁切或估高偏大导致「滑不到底 / 大片空白」
 -->
<template>
  <view
    class="sticky-tab-pager"
    :class="{ 'is-fill-root': fillHeight && !flow, 'is-flow': flow }"
    :style="rootStyle"
  >
    <view class="stp-tabs" id="stp-tabs-bar" :class="{ 'is-equal': equalWidth }">
      <view
        v-for="(tab, index) in tabs"
        :id="`stp-tab-${tab.id}`"
        :key="tab.id"
        class="stp-tab"
        :class="{ 'is-active': index === innerCurrent }"
        role="button"
        :aria-label="tab.label"
        @tap="handleTabTap(index)"
      >
        <view v-if="tab.badge === 'live-dot'" class="stp-live-dot" aria-hidden="true" />
        <text class="stp-tab__label">{{ tab.label }}</text>
      </view>
      <view
        class="stp-ink"
        :class="{ 'is-animating': inkAnimating }"
        :style="inkStyle"
      />
    </view>

    <!-- flow：文档流撑高 + 手势横滑，避免微信 swiper 定高裁切 -->
    <view
      v-if="flow"
      class="stp-flow-pane"
      @touchstart="onFlowTouchStart"
      @touchmove="onFlowTouchMove"
      @touchend="onFlowTouchEnd"
      @touchcancel="onFlowTouchEnd"
    >
      <slot
        v-if="currentTab"
        name="pane"
        :tab="currentTab"
        :index="innerCurrent"
      />
    </view>

    <swiper
      v-else
      class="stp-swiper"
      :class="{ 'is-fill': fillHeight }"
      :style="swiperStyle"
      :current="innerCurrent"
      :duration="duration"
      :skip-hidden-item-layout="true"
      @change="handleSwiperChange"
      @animationfinish="handleAnimationFinish"
    >
      <swiper-item v-for="(tab, index) in tabs" :key="tab.id" class="stp-swiper__item">
        <slot name="pane" :tab="tab" :index="index" />
      </swiper-item>
    </swiper>
  </view>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, nextTick, ref, watch } from 'vue'

export interface StickyTabItem {
  id: string
  label: string
  badge?: 'live-dot'
}

const props = withDefaults(
  defineProps<{
    tabs: StickyTabItem[]
    current?: number
    /** swiper 内容区高度（px）；fillHeight / flow 为 true 时忽略 */
    pagerHeight?: number
    duration?: number
    /** 是否均分 Tab 宽度（直播间等多 Tab 场景） */
    equalWidth?: boolean
    /** 由父级 flex 撑满剩余高度 */
    fillHeight?: boolean
    /** 内容随文档流撑高，手势横滑切 Tab（不用定高 swiper）；首页/直播间功能 Tab */
    flow?: boolean
  }>(),
  {
    current: 0,
    pagerHeight: 0,
    duration: 300,
    equalWidth: false,
    fillHeight: false,
    flow: false
  }
)

const emit = defineEmits<{
  change: [index: number]
}>()

const innerCurrent = ref(Math.max(0, props.current || 0))
const inkLeft = ref(0)
const inkWidth = ref(24)
const inkAnimating = ref(true)
const tabCenters = ref<number[]>([])
const measuring = ref(false)
const measureFailCount = ref(0)
const MAX_MEASURE_FAIL = 3

const touchStartX = ref(0)
const touchStartY = ref(0)
/** 0=未判定；1=横滑切 Tab；2=竖滑交给外层（锁定后本轮不再切 Tab） */
const flowAxisLock = ref(0)
const SWIPE_THRESHOLD = 48
const AXIS_LOCK_SLOP = 10

const currentTab = computed(() => props.tabs[innerCurrent.value] || null)

const swiperStyle = computed(() => {
  if (props.fillHeight || props.flow) return {}
  return { height: `${Math.max(180, Number(props.pagerHeight) || 200)}px` }
})

const rootStyle = computed(() => {
  if (props.flow) return {}
  if (props.fillHeight) return { height: '100%' }
  const ph = Number(props.pagerHeight) || 0
  if (ph > 0) return { height: `${ph + 40}px` }
  return {}
})

const inkStyle = computed(() => ({
  transform: `translate3d(${inkLeft.value}px, 0, 0)`,
  width: `${inkWidth.value}px`
}))

const instance = getCurrentInstance()

function applyInk(index: number, animate: boolean) {
  const centers = tabCenters.value
  if (centers[index] == null) return
  inkAnimating.value = animate
  inkLeft.value = centers[index] - inkWidth.value / 2
}

function cacheTabCenters() {
  if (measuring.value) return
  if (!props.tabs.length) return
  if (measureFailCount.value >= MAX_MEASURE_FAIL) return

  measuring.value = true
  const unlockTimer = setTimeout(() => {
    measuring.value = false
  }, 800)
  nextTick(() => {
    const proxy = instance?.proxy as any
    const query = proxy ? uni.createSelectorQuery().in(proxy) : uni.createSelectorQuery()
    query.select('#stp-tabs-bar').boundingClientRect()
    props.tabs.forEach((tab) => {
      query.select(`#stp-tab-${tab.id}`).boundingClientRect()
    })
    query.exec((res: any[]) => {
      clearTimeout(unlockTimer)
      measuring.value = false
      const bar = res?.[0]
      if (!bar || typeof bar.left !== 'number') {
        measureFailCount.value += 1
        return
      }

      let nextInkW = inkWidth.value
      const centers: number[] = []
      for (let i = 0; i < props.tabs.length; i++) {
        const rect = res?.[i + 1]
        if (!rect || typeof rect.left !== 'number' || !rect.width) {
          measureFailCount.value += 1
          return
        }
        nextInkW = Math.max(18, Math.min(32, Number(rect.width) * 0.42))
        centers.push(Number(rect.left) - Number(bar.left) + Number(rect.width) / 2)
      }

      measureFailCount.value = 0
      inkWidth.value = nextInkW
      tabCenters.value = centers
      applyInk(innerCurrent.value, false)
    })
  })
}

function snapInkToIndex(index: number, animate: boolean) {
  const centers = tabCenters.value
  if (centers[index] != null) {
    applyInk(index, animate)
    return
  }
  // 量不到时只触发一次量高，禁止 snap ↔ cache 互递归
  cacheTabCenters()
}

function setCurrent(index: number, emitChange: boolean) {
  if (index < 0 || index >= props.tabs.length) return
  if (innerCurrent.value === index) {
    snapInkToIndex(index, true)
    return
  }
  innerCurrent.value = index
  snapInkToIndex(index, true)
  if (emitChange) emit('change', index)
}

function handleTabTap(index: number) {
  inkAnimating.value = true
  setCurrent(index, true)
}

function handleSwiperChange(e: any) {
  const idx = Number(e?.detail?.current ?? 0)
  inkAnimating.value = true
  if (idx === innerCurrent.value) {
    snapInkToIndex(idx, true)
    return
  }
  innerCurrent.value = idx
  snapInkToIndex(idx, true)
  emit('change', idx)
}

function handleAnimationFinish() {
  inkAnimating.value = true
  snapInkToIndex(innerCurrent.value, false)
}

function onFlowTouchStart(e: any) {
  const t = e?.changedTouches?.[0] || e?.touches?.[0]
  touchStartX.value = Number(t?.clientX || t?.pageX || 0)
  touchStartY.value = Number(t?.clientY || t?.pageY || 0)
  flowAxisLock.value = 0
}

function onFlowTouchMove(e: any) {
  if (flowAxisLock.value !== 0) return
  const t = e?.changedTouches?.[0] || e?.touches?.[0]
  const x = Number(t?.clientX || t?.pageX || 0)
  const y = Number(t?.clientY || t?.pageY || 0)
  const dx = Math.abs(x - touchStartX.value)
  const dy = Math.abs(y - touchStartY.value)
  if (dx < AXIS_LOCK_SLOP && dy < AXIS_LOCK_SLOP) return
  // 先动的轴锁定：竖滑绝不切 Tab，避免与页面/scroll-view 抢手势导致滑不到底
  flowAxisLock.value = dy >= dx ? 2 : 1
}

function onFlowTouchEnd(e: any) {
  const locked = flowAxisLock.value
  flowAxisLock.value = 0
  if (locked === 2) return // 竖滑本轮不切 Tab
  const t = e?.changedTouches?.[0] || e?.touches?.[0]
  const endX = Number(t?.clientX || t?.pageX || 0)
  const endY = Number(t?.clientY || t?.pageY || 0)
  const dx = endX - touchStartX.value
  const dy = endY - touchStartY.value
  if (Math.abs(dx) < SWIPE_THRESHOLD) return
  if (locked !== 1 && Math.abs(dx) <= Math.abs(dy)) return
  if (dx < 0) {
    setCurrent(innerCurrent.value + 1, true)
  } else {
    setCurrent(innerCurrent.value - 1, true)
  }
}

watch(
  () => props.current,
  (v) => {
    const idx = Math.max(0, Number(v) || 0)
    if (idx !== innerCurrent.value) {
      innerCurrent.value = idx
      snapInkToIndex(idx, true)
    }
  }
)

watch(
  () => props.tabs.map((t) => t.id).join('|'),
  () => {
    measureFailCount.value = 0
    tabCenters.value = []
    cacheTabCenters()
  },
  { immediate: true }
)

defineExpose({
  refreshInk: () => {
    measureFailCount.value = 0
    cacheTabCenters()
  }
})
</script>

<script lang="ts">
export default {
  name: 'StickyTabPager',
  options: {
    /* 允许页面 :deep 改 Tab 吸顶；勿开 virtualHost——微信端会丢组件 scoped 样式 */
    styleIsolation: 'shared'
  }
}
</script>

<style lang="scss" scoped>
/* 颜色写死：不用 uni.scss 的 var(--color-*)，避免微信 scoped 下变量不生效 */
.sticky-tab-pager {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: auto;
  min-height: 0;
  background: #ffffff;

  &.is-fill-root {
    height: 100%;
  }

  &.is-flow {
    height: auto;
  }
}

.stp-tabs {
  position: relative;
  flex-shrink: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 76rpx;
  padding: 0 24rpx;
  background: #ffffff;
  border-bottom: 1px solid #ebeef5;
  box-sizing: border-box;
  z-index: 2;

  &.is-equal {
    padding: 0 8rpx;
  }
}

.stp-tab {
  position: relative;
  flex: 0 0 auto;
  height: 76rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  padding: 0 22rpx;

  .stp-tabs.is-equal & {
    flex: 1;
    min-width: 0;
    padding: 0 8rpx;
  }

  &.is-active {
    .stp-tab__label {
      color: #0f766e;
      font-weight: 600;
    }
  }
}

.stp-tab__label {
  font-size: 15px;
  color: #606266;
  line-height: 1.2;
}

.stp-live-dot {
  width: 14rpx;
  height: 14rpx;
  margin-right: 8rpx;
  border-radius: 50%;
  background-color: #ff3b30;
  box-shadow: 0 0 0 4rpx rgba(255, 59, 48, 0.18);
  flex-shrink: 0;
}

.stp-ink {
  position: absolute;
  left: 0;
  bottom: 0;
  height: 6rpx;
  border-radius: 3rpx;
  background-color: #0f766e;
  pointer-events: none;
  will-change: transform;
  transition: none;

  &.is-animating {
    transition: transform 280ms cubic-bezier(0.22, 0.61, 0.36, 1), width 280ms ease;
  }
}

.stp-flow-pane {
  width: 100%;
  min-height: 0;
}

.stp-swiper {
  width: 100%;
  min-height: 0;

  &.is-fill {
    flex: 1;
    height: 0;
  }
}

.stp-swiper__item {
  height: 100%;
  overflow: hidden;
}
</style>
