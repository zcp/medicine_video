<template>
  <view v-if="visible" class="picker-sheet">
    <!-- 遮罩层 -->
    <view class="mask" @click="handleClose"></view>

    <!-- 内容区 -->
    <view class="content" :class="{ show: showContent }">
      <!-- 标题栏 -->
      <view class="header">
        <text class="title">{{ title }}</text>
        <text class="close-btn" @click="handleClose">✕</text>
      </view>

      <!-- 搜索（本地过滤，可选） -->
      <view v-if="searchable" class="search">
        <view class="app-search-field ps-field">
          <text class="ps-icon iconfont icon-search"></text>
          <input
            v-model="keyword"
            class="ps-input"
            :placeholder="searchPlaceholder"
            placeholder-class="ps-placeholder"
            confirm-type="search"
          />
          <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
          <view class="search-clear-slot">
            <ClearButton v-if="keyword" @clear="keyword = ''" />
          </view>
        </view>
      </view>

      <!-- 可滚动列表区域 -->
      <scroll-view class="scroll-list" scroll-y @scrolltolower="handleLoadMore">
        <!-- 空状态（搜索无结果且无可创建行时展示） -->
        <view v-if="filteredItems.length === 0 && !showCreateRow" class="empty-state">
          <text class="empty-text">{{ emptyText }}</text>
        </view>

        <!-- 列表项 -->
        <view
          v-for="(item, index) in renderedItems"
          :key="item.id || index"
          class="list-item"
          :class="{ 'is-selected': isSelected(item.id), 'is-disabled': isDisabled(item.id) }"
          @click="handleItemTap(item)"
        >
          <ProxyAvatarImage
            v-if="item.avatar"
            :src="item.avatar"
            shape="circle"
            size="80rpx"
          />
          <view class="item-content">
            <text class="item-name">{{ item.name }}</text>
            <text v-if="item.subtitle" class="item-subtitle">{{ item.subtitle }}</text>
          </view>
          <view v-if="mode === 'multiple' && isSelected(item.id)" class="check-icon">✓</view>
        </view>

        <!-- 创建并使用（createable：搜无精确同名时的自建入口，resolve 由父级处理） -->
        <view
          v-if="showCreateRow"
          class="create-row"
          :class="{ 'is-pending': createPending }"
          @click="handleCreateTap"
        >
          <text class="create-icon">+</text>
          <text class="create-text">{{ createPending ? '创建中...' : `创建并使用「${keyword.trim()}」` }}</text>
        </view>
      </scroll-view>

      <!-- 底部按钮 -->
      <view v-if="mode === 'single' || !hideFooter" class="footer">
        <button
          v-if="mode === 'single'"
          class="cancel-btn"
          @click="handleClose"
        >取消</button>
        <button
          v-else
          class="confirm-btn"
          @click="handleConfirm"
        >{{ confirmLabel }}</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import ProxyAvatarImage from '@/components/common/ProxyAvatarImage.vue';
import ClearButton from '@/components/app/ClearButton.vue';

export interface PickerItem {
  id: string;
  name: string;
  subtitle?: string;
  avatar?: string;
  [key: string]: any;
}

const props = withDefaults(defineProps<{
  visible: boolean;
  title: string;
  items: PickerItem[];
  /** 单选（点选即关） / 多选（toggle + 完成条） */
  mode?: 'single' | 'multiple';
  /** multiple 已选 id 列表（受控，配合 update:selectedIds） */
  selectedIds?: string[];
  /** multiple 上限；undefined 不限制（满员时未选项置灰） */
  max?: number;
  /** 本地搜索（按 name/subtitle 过滤） */
  searchable?: boolean;
  /** 搜索框占位文案（searchable 时生效） */
  searchPlaceholder?: string;
  /** 允许「创建并使用」行：开启后搜索无精确同名（trim+小写，对 items 全量判定）时展示，点击 emit create(keyword) */
  createable?: boolean;
  /** 创建进行中（父级 resolve 期间置 true：禁用创建行、显示"创建中..."，防重复提交） */
  createPending?: boolean;
  hideFooter?: boolean;
  emptyText?: string;
}>(), {
  mode: 'single',
  selectedIds: () => [],
  searchable: false,
  searchPlaceholder: '搜索名称',
  createable: false,
  createPending: false,
  hideFooter: false,
  emptyText: '暂无数据'
});

const emit = defineEmits<{
  'update:visible': [value: boolean];
  /** single：选中项（组件自动关闭） */
  'select': [item: PickerItem];
  /** multiple：toggle 后的完整已选 id 列表（受控） */
  'update:selectedIds': [value: string[]];
  /** multiple：点击完成 */
  'confirm': [];
  /** createable：点击「创建并使用」→ 提交去空白关键词（resolve 由父级处理） */
  'create': [keyword: string];
}>();

const showContent = ref(false);
const keyword = ref('');

/** 增量渲染：初始/搜索时只渲染前 50 项，滚动到底部再加 50（全量 384 项列表不卡顿；小数据列表行为不变） */
const RENDER_CHUNK = 50;
const visibleCount = ref(RENDER_CHUNK);

const renderedItems = computed(() => filteredItems.value.slice(0, visibleCount.value));

const handleLoadMore = () => {
  if (visibleCount.value < filteredItems.value.length) {
    visibleCount.value = Math.min(visibleCount.value + RENDER_CHUNK, filteredItems.value.length);
  }
};

watch(() => props.visible, (newVal) => {
  if (newVal) {
    keyword.value = '';
    visibleCount.value = RENDER_CHUNK;
    setTimeout(() => {
      showContent.value = true;
    }, 50);
  } else {
    showContent.value = false;
  }
});

watch(keyword, () => {
  visibleCount.value = RENDER_CHUNK;
});

const filteredItems = computed(() => {
  const kw = keyword.value.trim().toLowerCase();
  if (!kw) return props.items;
  return props.items.filter(
    (item) =>
      (item.name || '').toLowerCase().includes(kw) ||
      (item.subtitle || '').toLowerCase().includes(kw)
  );
});

/** 「创建并使用」行可见条件：searchable + createable + 关键词非空 + items 全量无精确同名（§4.3：对 items 全量判定，不限于 filteredItems） */
const showCreateRow = computed(() => {
  if (!props.createable || !props.searchable) return false;
  const kw = keyword.value.trim();
  if (!kw) return false;
  return !props.items.some(
    (item) => (item.name || '').trim().toLowerCase() === kw.toLowerCase()
  );
});

/** 点击「创建并使用」：防重复（createPending）；提交 trim 后关键词，关键词保留以便父级并入列表后可见 */
const handleCreateTap = () => {
  if (props.createPending) return;
  const kw = keyword.value.trim();
  if (!kw) return;
  emit('create', kw);
};

const isSelected = (id: string) => props.selectedIds.includes(id);

const isDisabled = (id: string) => {
  if (props.mode !== 'multiple') return false;
  if (isSelected(id)) return false;
  return props.max != null && props.selectedIds.length >= props.max;
};

const confirmLabel = computed(() => {
  const n = props.selectedIds.length;
  if (props.max != null) return `完成（已选 ${n}/${props.max}）`;
  return `完成（已选 ${n}）`;
});

const handleClose = () => {
  showContent.value = false;
  setTimeout(() => {
    emit('update:visible', false);
  }, 300);
};

const handleItemTap = (item: PickerItem) => {
  if (props.mode === 'multiple') {
    if (isDisabled(item.id)) return;
    const next = isSelected(item.id)
      ? props.selectedIds.filter((id) => id !== item.id)
      : [...props.selectedIds, item.id];
    emit('update:selectedIds', next);
    return;
  }
  emit('select', item);
  handleClose();
};

const handleConfirm = () => {
  emit('confirm');
  handleClose();
};
</script>

<style lang="scss" scoped>
.picker-sheet {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
}

.mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  animation: fadeIn 0.3s ease;
}

.content {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  /* 固定高度（V2 联调反馈）：结果数变化（含搜空出创建行）不改变弹层高度，
     避免弹层塌缩到输入键盘下方；列表区内部滚动兜底 */
  height: 70vh;
  display: flex;
  flex-direction: column;
  background-color: var(--home-card);
  border-radius: var(--home-r-lg) var(--home-r-lg) 0 0;
  transform: translateY(100%);
  transition: transform 0.3s ease;
  padding-bottom: env(safe-area-inset-bottom);

  &.show {
    transform: translateY(0);
  }
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
  border-bottom: 1.5rpx solid var(--home-border);
  flex-shrink: 0;
}

.title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
}

.close-btn {
  font-size: 32rpx;
  color: var(--home-tabbar-inactive);
  padding: 8rpx;
  line-height: 1;
}

.search {
  padding: 20rpx 32rpx;
  flex-shrink: 0;
}

/* 胶囊：叠加共享容器 .app-search-field（B站风格）；高度 64rpx（弹层档） */
.ps-field {
  height: 64rpx;
  box-sizing: border-box;
}

.ps-icon {
  font-size: 26rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
  flex-shrink: 0;
  line-height: 1;
}

.ps-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  background: transparent;
  border: none;
  outline: none;
  box-sizing: border-box;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.ps-placeholder {
  color: var(--search-placeholder);
}

.scroll-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 32rpx;
  box-sizing: border-box;
}

.empty-state {
  padding: 80rpx 0;
  text-align: center;

  .empty-text {
    font-size: 24rpx;
    color: var(--home-tabbar-inactive);
  }
}

/* 创建并使用行（createable）：品牌主色 + 分隔线，pending 态降透明禁点 */
.create-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 24rpx 8rpx;
  min-height: 88rpx;
  box-sizing: border-box;
  border-top: 1rpx solid var(--home-divider);
  color: var(--home-primary);

  &:active {
    background: var(--home-action-secondary-bg);
  }

  &.is-pending {
    opacity: 0.55;
  }

  .create-icon {
    font-size: 32rpx;
    font-weight: 600;
    line-height: 1;
    flex-shrink: 0;
  }

  .create-text {
    font-size: var(--home-fs-card-title);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.list-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx 8rpx;
  border-bottom: 1rpx solid var(--home-divider);
  min-height: 88rpx;
  box-sizing: border-box;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: var(--home-action-secondary-bg);
  }

  &.is-selected {
    background: var(--home-badge-featured-bg);
  }

  &.is-disabled {
    opacity: 0.45;
  }
}

.item-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.item-name {
  font-size: var(--home-fs-card-title);
  font-weight: 500;
  color: var(--home-text1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-subtitle {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.check-icon {
  font-size: 32rpx;
  color: var(--home-primary);
  font-weight: bold;
  flex-shrink: 0;
}

.footer {
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid var(--home-border);
  flex-shrink: 0;

  .cancel-btn,
  .confirm-btn {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    border-radius: var(--home-r-pill);
    border: none;
    font-size: var(--home-fs-section);
    font-weight: 500;
    padding: 0;

    &::after {
      border: none;
    }
  }

  .cancel-btn {
    background: var(--home-action-secondary-bg);
    color: var(--home-text2);
  }

  .confirm-btn {
    background-color: var(--home-primary);
    color: #ffffff;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
