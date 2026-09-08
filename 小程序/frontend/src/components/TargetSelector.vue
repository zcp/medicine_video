<!--
 * TargetSelector - 跳转目标选择器（管理员友好版）
 * @description 根据跳转类型搜索并选择关联资源，显示可读名称而非UUID
 * @author 直播SaaS团队
 -->
<template>
  <view class="target-selector">
    <!-- 搜索输入 -->
    <view class="search-box">
      <input
        v-model="searchQuery"
        class="search-input"
        :placeholder="placeholder"
        @input="handleSearch"
      />
      <view v-if="searchQuery" class="search-clear" @click="clearSearch">
        <text class="clear-icon">✕</text>
      </view>
    </view>

    <!-- 独立限高滚动：结果可全量保留，区域内滑动 -->
    <scroll-view
      class="result-list"
      v-if="options.length > 0"
      scroll-y
      :show-scrollbar="true"
      :enable-flex="true"
    >
      <view
        v-for="item in options"
        :key="item.id"
        :class="['result-item', selectedId === item.id ? 'is-selected' : '']"
        @tap="handleSelect(item)"
      >
        <view class="result-info">
          <text class="result-name">{{ item.name }}</text>
          <text v-if="item.subtitle" class="result-subtitle">{{ item.subtitle }}</text>
        </view>
        <view v-if="selectedId === item.id" class="check-mark">
          <text class="check-icon">✓</text>
        </view>
      </view>
    </scroll-view>

    <!-- 已选中显示 -->
    <view v-else-if="selectedId && !searchLoading" class="selected-display">
      <view class="selected-info">
        <text class="selected-icon">📌</text>
        <text class="selected-name">{{ selectedDisplayName }}</text>
      </view>
      <view class="btn-clear" @click="handleClear">
        <text class="clear-text">清除</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="searchLoading" class="loading-hint">
      <text class="loading-text">搜索中...</text>
    </view>

    <!-- 空结果 -->
    <view v-if="searchQuery && !searchLoading && options.length === 0 && !selectedId" class="empty-hint">
      <text class="empty-text">未找到匹配结果</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { request } from '@/utils/request'
import type { FeaturedContentTargetType } from '@/types/featuredContent'

const props = defineProps<{
  targetType: FeaturedContentTargetType
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const selectedId = ref(props.modelValue)
const selectedName = ref('')  // 缓存已选资源的名称
const searchQuery = ref('')
const options = ref<{ id: string; name: string; subtitle?: string }[]>([])
const searchLoading = ref(false)

const placeholder = computed(() => {
  const map: Record<string, string> = {
    session: '搜索场次名称...',
    brand: '搜索品牌名称...'
  }
  return map[props.targetType] || '搜索...'
})

// 显示名称：优先显示缓存的名称，否则显示ID的前8位
const selectedDisplayName = computed(() => {
  if (selectedName.value) return selectedName.value
  if (selectedId.value) return `ID: ${selectedId.value.slice(0, 8)}...`
  return ''
})

// API 路径映射
const apiMap: Record<string, string> = {
  session: '/sessions',
  brand: '/brands'
}

let searchTimer: ReturnType<typeof setTimeout> | null = null

function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    search(searchQuery.value)
  }, 300)
}

async function search(query: string) {
  const baseApi = apiMap[props.targetType]
  if (!baseApi) return

  searchLoading.value = true
  try {
    const data = await request.get(baseApi, {
      data: { q: query || undefined, page: 1, page_size: 20 },
      auth: false
    })
    const items = data?.data?.items || data?.items || data?.data || data || []
    const itemList = Array.isArray(items) ? items : []
    options.value = itemList.map((item: any) => ({
      id: item.id,
      name: item.name || item.title || `未命名${getTargetLabel()}`,
      subtitle: getSubtitle(item)
    }))
  } catch (error) {
    console.error('搜索失败:', error)
    options.value = []
  } finally {
    searchLoading.value = false
  }
}

// 获取目标类型的中文标签
function getTargetLabel(): string {
  const map: Record<string, string> = {
    session: '场次',
    brand: '品牌'
  }
  return map[props.targetType] || '资源'
}

// 获取副标题（显示额外信息）
function getSubtitle(item: any): string {
  switch (props.targetType) {
    case 'session':
      return item.status || ''
    case 'brand':
      return item.description || ''
    default:
      return ''
  }
}

async function handleSelect(item: { id: string; name: string }) {
  selectedId.value = item.id
  selectedName.value = item.name  // 缓存名称
  emit('update:modelValue', item.id)
  options.value = []
  searchQuery.value = ''
}

function handleClear() {
  selectedId.value = ''
  selectedName.value = ''
  emit('update:modelValue', '')
}

function clearSearch() {
  searchQuery.value = ''
  options.value = []
}

// 如果有初始值，尝试获取其名称
async function loadSelectedName() {
  if (!selectedId.value || !props.targetType) return

  const baseApi = apiMap[props.targetType]
  if (!baseApi) return

  try {
    // 尝试通过 ID 获取详情
    const data = await request.get(`${baseApi}/${selectedId.value}`, { auth: false })
    const item = data?.data || data
    if (item) {
      selectedName.value = item.name || item.title || `已选${getTargetLabel()}`
    }
  } catch {
    // 获取失败不影响功能，显示ID即可
  }
}

watch(() => props.modelValue, (val) => {
  selectedId.value = val
  if (!val) {
    selectedName.value = ''
  } else if (!selectedName.value) {
    loadSelectedName()
  }
})

watch(() => props.targetType, () => {
  selectedId.value = ''
  selectedName.value = ''
  searchQuery.value = ''
  options.value = []
  emit('update:modelValue', '')
})

onMounted(() => {
  search('')
  // 如果有初始值，加载名称
  if (selectedId.value) {
    loadSelectedName()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.target-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.search-box {
  position: relative;

  .search-input {
    width: 100%;
    height: 40px;
    padding: 0 32px 0 12px;
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-base);
    font-size: 14px;
    background-color: var(--color-bg-primary);
    box-sizing: border-box;
  }

  .search-clear {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;

    .clear-icon {
      font-size: 14px;
      color: var(--color-text-secondary);
    }
  }
}

.result-list {
  height: 200px;
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-bg-primary);
  box-sizing: border-box;
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--color-border);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background-color: #f5f5f5;
  }

  &.is-selected {
    background-color: #e6f7ff;
  }

  .result-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 0;

    .result-name {
      font-size: 14px;
      color: var(--color-text-primary);
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .result-subtitle {
      font-size: 12px;
      color: var(--color-text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .check-mark {
    flex-shrink: 0;
    margin-left: var(--spacing-sm);

    .check-icon {
      font-size: 18px;
      color: var(--color-primary);
      font-weight: bold;
    }
  }
}

.selected-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: var(--border-radius-base);

  .selected-info {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;

    .selected-icon {
      font-size: 16px;
      flex-shrink: 0;
    }

    .selected-name {
      font-size: 14px;
      color: var(--color-primary);
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .btn-clear {
    padding: 4px 10px;
    background-color: #fff2f0;
    border: 1px solid #ffccc7;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    flex-shrink: 0;

    .clear-text {
      font-size: 12px;
      color: #ff4d4f;
    }
  }
}

.loading-hint {
  padding: 8px 0;
  text-align: center;

  .loading-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.empty-hint {
  padding: 12px 0;
  text-align: center;

  .empty-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}
</style>
