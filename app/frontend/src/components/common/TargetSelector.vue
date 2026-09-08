<template>
  <view class="target-selector">
    <!-- 触发区：点击弹出资源列表 -->
    <view class="ts-trigger" @tap="openPopup">
      <text v-if="modelValue" class="ts-trigger-name">{{ selectedDisplayName }}</text>
      <text v-else class="ts-trigger-placeholder">点击选择{{ targetTypeLabel }}</text>
      <text class="ts-trigger-arrow">▾</text>
    </view>
    <view v-if="modelValue" class="ts-selected-bar">
      <text class="ts-selected-name">{{ selectedDisplayName }}</text>
      <view class="ts-clear-btn" @tap.stop="handleClear">
        <text class="ts-clear-btn-text">清除</text>
      </view>
    </view>

    <!-- 弹层：资源列表选择（P1.5：动画基线对齐 PickerSheet——mask 淡入 + 0.3s 滑入滑出；对外契约零变化） -->
    <view v-if="popupVisible" class="ts-mask" @tap="closePopup">
      <view class="ts-popup" :class="{ 'is-open': tsShown }" @tap.stop>
        <view class="ts-popup-header">
          <text class="ts-popup-title">选择{{ targetTypeLabel }}</text>
          <view class="ts-popup-close" @tap="closePopup">
            <text class="ts-popup-close-text">✕</text>
          </view>
        </view>
        <view class="ts-popup-search">
          <view class="app-search-field ts-popup-field">
            <text class="ts-popup-icon iconfont icon-search"></text>
            <input
              v-model="searchQuery"
              class="ts-popup-input"
              :placeholder="'搜索' + targetTypeLabel + '名称'"
              placeholder-class="ts-popup-placeholder"
              confirm-type="search"
              @input="handleSearch"
              @confirm="applySearch"
            />
            <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
            <view class="search-clear-slot">
              <ClearButton v-if="searchQuery" @clear="clearSearch" />
            </view>
          </view>
        </view>
        <scroll-view class="ts-popup-list" scroll-y>
          <view
            v-for="item in options"
            :key="item.id"
            class="ts-popup-item"
            :class="{ 'is-selected': modelValue === item.id }"
            @tap="handleSelect(item)"
          >
            <view class="ts-popup-item-info">
              <text class="ts-popup-item-name">{{ item.name }}</text>
              <text v-if="item.subtitle" class="ts-popup-item-subtitle">{{ item.subtitle }}</text>
            </view>
            <text v-if="modelValue === item.id" class="ts-check">✓</text>
          </view>
          <view v-if="searching" class="ts-hint">
            <text class="ts-hint-text">加载中...</text>
          </view>
          <view v-if="!searching && options.length === 0" class="ts-hint">
            <text class="ts-hint-text">暂无{{ targetTypeLabel }}数据</text>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { get as httpGet } from '@/utils/request';
import { getRoomList, getRoomDetail } from '@/api/room';
import ClearButton from '@/components/app/ClearButton.vue';

type SelectableTargetType = 'room' | 'brand';

const props = defineProps<{
  targetType: SelectableTargetType;
  modelValue: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const popupVisible = ref(false);
/** 弹层滑入状态（弹窗统一 P1.5：open 后 50ms 置 true 触发滑入；close 先置 false 延迟 300ms 卸载） */
const tsShown = ref(false);
const searchQuery = ref('');
const options = ref<{ id: string; name: string; subtitle?: string }[]>([]);
const searching = ref(false);
const selectedName = ref('');

let searchTimer: ReturnType<typeof setTimeout> | null = null;

const targetTypeLabel = computed(() => {
  return props.targetType === 'room' ? '直播间' : '品牌';
});

const selectedDisplayName = computed(() => {
  if (selectedName.value) return selectedName.value;
  if (props.modelValue) return `${targetTypeLabel.value} ID: ${props.modelValue.slice(0, 8)}...`;
  return '';
});

async function fetchOptions(query: string): Promise<{ id: string; name: string; subtitle?: string }[]> {
  const kw = query.trim() || undefined;
  if (props.targetType === 'room') {
    const res = await getRoomList({ page: 1, size: 20, q: kw });
    return (res.data?.items || []).map((r: any) => ({
      id: String(r.id),
      name: String(r.title || '未命名直播间'),
      subtitle: `直播状态: ${String(r.live_status || '')}`,
    }));
  }
  const res = await httpGet<{ code: number; data: any[] }>('/brands', { q: kw, limit: 20 }, { auth: false });
  const list = Array.isArray(res.data) ? res.data : [];
  return list.map((b: any) => ({
    id: String(b.id),
    name: String(b.name || b.title || '未命名品牌'),
    subtitle: b.description ? String(b.description) : undefined,
  }));
}

async function loadOptions() {
  searching.value = true;
  try {
    options.value = await fetchOptions(searchQuery.value);
  } catch (e) {
    console.error('[TargetSelector] 加载列表失败:', e);
    options.value = [];
  } finally {
    searching.value = false;
  }
}

function openPopup() {
  popupVisible.value = true;
  tsShown.value = false;
  setTimeout(() => { tsShown.value = true; }, 50);
  if (options.value.length === 0) loadOptions();
}

function closePopup() {
  if (!tsShown.value) {
    popupVisible.value = false;
    return;
  }
  tsShown.value = false;
  setTimeout(() => { popupVisible.value = false; }, 300);
}

function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    loadOptions();
  }, 300);
}

function applySearch() {
  if (searchTimer) clearTimeout(searchTimer);
  loadOptions();
}

function clearSearch() {
  searchQuery.value = '';
  loadOptions();
}

function handleSelect(item: { id: string; name: string }) {
  selectedName.value = item.name;
  emit('update:modelValue', item.id);
  closePopup();
}

function handleClear() {
  selectedName.value = '';
  emit('update:modelValue', '');
  options.value = [];
  searchQuery.value = '';
}

async function loadSelectedName() {
  if (!props.modelValue) {
    selectedName.value = '';
    return;
  }
  try {
    if (props.targetType === 'room') {
      const res = await getRoomDetail(props.modelValue);
      const name = (res.data as any)?.title;
      selectedName.value = name ? String(name) : '';
    } else {
      // 公开 /brands/{id} 不存在，品牌详情走管理端接口（需登录）
      const res = await httpGet<{ code: number; data: any }>(`/admin/brands/${props.modelValue}`, undefined, { auth: true });
      selectedName.value = (res.data as any)?.name || '';
    }
  } catch {
    selectedName.value = '';
  }
}

watch(() => props.modelValue, (val) => {
  if (!val) selectedName.value = '';
  else loadSelectedName();
});

watch(() => props.targetType, () => {
  selectedName.value = '';
  searchQuery.value = '';
  options.value = [];
  closePopup();
  emit('update:modelValue', '');
});

onMounted(() => {
  loadSelectedName();
});
</script>

<style lang="scss" scoped>
.target-selector {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.ts-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72rpx;
  padding: 0 20rpx;
  background: var(--home-input-bg);
  border-radius: var(--home-r-md);
  border: 1rpx solid var(--home-divider);

  .ts-trigger-name {
    flex: 1;
    min-width: 0;
    font-size: 26rpx;
    color: var(--home-text1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .ts-trigger-placeholder {
    flex: 1;
    min-width: 0;
    font-size: 26rpx;
    color: var(--home-text2);
  }

  .ts-trigger-arrow {
    flex-shrink: 0;
    font-size: 24rpx;
    color: var(--home-text2);
  }
}

.ts-selected-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  padding: 12rpx 20rpx;
  background: var(--home-badge-featured-bg);
  border: 1rpx solid rgba(15, 118, 110, 0.3);
  border-radius: var(--home-r-md);
}

.ts-selected-name {
  flex: 1;
  min-width: 0;
  font-size: 24rpx;
  color: var(--home-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ts-clear-btn {
  flex-shrink: 0;
  padding: 4rpx 20rpx;
  background: var(--home-action-danger-bg);
  border-radius: var(--home-r-pill);

  .ts-clear-btn-text {
    font-size: 22rpx;
    color: var(--home-action-danger-text);
  }
}

/* ===== 弹层 ===== */
.ts-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 2000;
  animation: tsPopupFadeIn 0.3s ease;
}

.ts-popup {
  width: 100%;
  height: 70vh;
  background: var(--home-bg);
  border-radius: 24rpx 24rpx 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform: translateY(100%);
  transition: transform 0.3s ease;

  &.is-open {
    transform: translateY(0);
  }
}

@keyframes tsPopupFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.ts-popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid var(--home-divider);
}

.ts-popup-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-text1);
}

.ts-popup-close {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  .ts-popup-close-text {
    font-size: 28rpx;
    color: var(--home-text2);
  }
}

.ts-popup-search {
  position: relative;
  padding: 16rpx 32rpx;
}

/* 胶囊：叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊）；高度 64rpx（弹层档） */
.ts-popup-field {
  height: 64rpx;
  box-sizing: border-box;
}

.ts-popup-icon {
  font-size: 26rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
  flex-shrink: 0;
  line-height: 1;
}

.ts-popup-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0;
  font-size: 26rpx;
  background: transparent;
  border: none;
  outline: none;
  box-sizing: border-box;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.ts-popup-placeholder {
  color: var(--search-placeholder);
}

.ts-popup-list {
  flex: 1;
  min-height: 0;
  padding: 0 32rpx 32rpx;
  box-sizing: border-box;
}

.ts-popup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  padding: 20rpx 8rpx;
  border-bottom: 1rpx solid var(--home-divider);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: var(--home-action-secondary-bg);
  }

  &.is-selected {
    background: var(--home-badge-featured-bg);
  }
}

.ts-popup-item-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  flex: 1;
  min-width: 0;
}

.ts-popup-item-name {
  font-size: 26rpx;
  font-weight: 500;
  color: var(--home-text1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ts-popup-item-subtitle {
  font-size: 22rpx;
  color: var(--home-text2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ts-check {
  font-size: 28rpx;
  color: var(--home-primary);
  font-weight: bold;
  flex-shrink: 0;
}

.ts-hint {
  padding: 24rpx 0;
  text-align: center;

  .ts-hint-text {
    font-size: 24rpx;
    color: var(--home-text2);
  }
}
</style>
