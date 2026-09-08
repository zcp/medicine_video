<!--
 * RoomTargetSelector - 焦点图关联直播间选择器
 * @description 从首页房间列表选择预告/直播/回放房间，回填 target_id
 -->
<template>
  <view class="room-target-selector">
    <!-- 状态快筛 -->
    <view class="status-tabs">
      <view
        v-for="tab in statusTabs"
        :key="tab.value"
        :class="['status-tab', activeStatus === tab.value ? 'is-active' : '']"
        @click="handleStatusChange(tab.value)"
      >
        <text class="tab-text">{{ tab.label }}</text>
      </view>
    </view>

    <!-- 搜索 -->
    <view class="search-box">
      <input
        v-model="searchQuery"
        class="search-input"
        placeholder="搜索直播间标题..."
        @input="handleSearchInput"
      />
      <view v-if="searchQuery" class="search-clear" @click="clearSearch">
        <text class="clear-icon">✕</text>
      </view>
    </view>

    <!-- 列表 -->
    <view v-if="listLoading" class="loading-hint">
      <text class="loading-text">加载直播间...</text>
    </view>
    <!-- 独立限高滚动：列表可全量展示，区域内滑动，避免把整个弹窗撑太长 -->
    <scroll-view
      v-else-if="filteredRooms.length > 0"
      class="result-list"
      scroll-y
      :show-scrollbar="true"
      :enable-flex="true"
    >
      <view
        v-for="item in filteredRooms"
        :key="item.id"
        :class="['result-item', selectedId === item.id ? 'is-selected' : '']"
        @tap="handleSelect(item)"
      >
        <view class="result-info">
          <view class="result-title-row">
            <text class="result-name">{{ item.title }}</text>
            <view :class="['status-badge', `status-${item.liveStatus}`]">
              <text class="status-text">{{ liveStatusLabel(item.liveStatus) }}</text>
            </view>
          </view>
          <text v-if="item.hostName" class="result-subtitle">{{ item.hostName }}</text>
        </view>
        <view v-if="selectedId === item.id" class="check-mark">
          <text class="check-icon">✓</text>
        </view>
      </view>
    </scroll-view>
    <view v-else-if="!listLoading" class="empty-hint">
      <text class="empty-text">{{ searchQuery ? '未找到匹配的直播间' : '暂无直播间' }}</text>
    </view>

    <!-- 已选中 -->
    <view v-if="selectedId && !listLoading" class="selected-display">
      <view class="selected-info">
        <text class="selected-icon">📌</text>
        <text class="selected-name">{{ selectedDisplayName }}</text>
      </view>
      <view class="btn-clear" @click="handleClear">
        <text class="clear-text">清除</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { getHomepageRooms, getRoomById } from '@/api/room'

type LiveStatusFilter = 'all' | 'scheduled' | 'live' | 'replay'

interface RoomOption {
  id: string
  title: string
  liveStatus: 'scheduled' | 'live' | 'replay'
  hostName?: string
}

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const statusTabs: Array<{ label: string; value: LiveStatusFilter }> = [
  { label: '全部', value: 'all' },
  { label: '预告', value: 'scheduled' },
  { label: '直播', value: 'live' },
  { label: '回放', value: 'replay' }
]

const activeStatus = ref<LiveStatusFilter>('all')
const searchQuery = ref('')
const rooms = ref<RoomOption[]>([])
const listLoading = ref(false)
const selectedId = ref(props.modelValue)
const selectedName = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null

const selectedDisplayName = computed(() => {
  if (selectedName.value) return selectedName.value
  if (selectedId.value) return `ID: ${selectedId.value.slice(0, 8)}...`
  return ''
})

const filteredRooms = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return rooms.value.filter((room) => {
    if (activeStatus.value !== 'all' && room.liveStatus !== activeStatus.value) return false
    if (!q) return true
    return room.title.toLowerCase().includes(q) || (room.hostName || '').toLowerCase().includes(q)
  })
})

function normalizeLiveStatus(raw: unknown): 'scheduled' | 'live' | 'replay' {
  const s = String(raw || '').toLowerCase()
  if (s === 'live') return 'live'
  if (s === 'scheduled') return 'scheduled'
  return 'replay'
}

function liveStatusLabel(status: RoomOption['liveStatus']): string {
  const map = { scheduled: '预告', live: '直播', replay: '回放' }
  return map[status] || '回放'
}

function mapRoomItem(item: any): RoomOption | null {
  const id = String(item?.id || '')
  if (!id) return null
  const host = item?.host && typeof item.host === 'object' ? item.host : null
  return {
    id,
    title: String(item?.title || '未命名直播间'),
    liveStatus: normalizeLiveStatus(item?.live_status),
    hostName: host?.name ? String(host.name) : undefined
  }
}

async function loadRooms() {
  listLoading.value = true
  const collected: RoomOption[] = []
  try {
    for (let page = 1; page <= 5; page += 1) {
      const resp = await getHomepageRooms({ page, size: 50, sort: 'created_at:desc' })
      const paginated = (resp as any)?.data || resp
      const items = Array.isArray(paginated?.items) ? paginated.items : []
      if (!items.length) break
      items.forEach((item: any) => {
        const mapped = mapRoomItem(item)
        if (mapped) collected.push(mapped)
      })
      if (items.length < 50) break
    }
    rooms.value = collected
  } catch {
    rooms.value = []
  } finally {
    listLoading.value = false
  }
}

async function loadSelectedName() {
  if (!selectedId.value) return
  const cached = rooms.value.find((r) => r.id === selectedId.value)
  if (cached) {
    selectedName.value = cached.title
    return
  }
  try {
    const resp = await getRoomById(selectedId.value)
    const data = (resp as any)?.data || resp
    if (data?.title) selectedName.value = String(data.title)
  } catch {
    // 获取失败时保留 ID 展示
  }
}

function handleStatusChange(value: LiveStatusFilter) {
  activeStatus.value = value
}

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    // 本地过滤，无需额外请求
  }, 200)
}

function clearSearch() {
  searchQuery.value = ''
}

function handleSelect(item: RoomOption) {
  selectedId.value = item.id
  selectedName.value = item.title
  emit('update:modelValue', item.id)
}

function handleClear() {
  selectedId.value = ''
  selectedName.value = ''
  emit('update:modelValue', '')
}

watch(
  () => props.modelValue,
  (val) => {
    selectedId.value = val
    if (!val) {
      selectedName.value = ''
    } else if (!selectedName.value) {
      loadSelectedName()
    }
  }
)

onMounted(() => {
  loadRooms().then(() => {
    if (selectedId.value) loadSelectedName()
  })
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.room-target-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.status-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.status-tab {
  padding: 4px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  background-color: var(--color-bg-primary);
  cursor: pointer;

  &.is-active {
    border-color: var(--color-primary);
    background-color: #e6f7ff;

    .tab-text {
      color: var(--color-primary);
    }
  }

  .tab-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
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
  height: 220px;
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
  padding: 8px 10px;
  border-bottom: 1px solid var(--color-border);
  box-sizing: border-box;
  min-width: 0;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background-color: #f5f5f5;
  }

  &.is-selected {
    background-color: #e6f7ff;
  }
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.result-name {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.status-badge {
  padding: 2px 6px;
  border-radius: var(--border-radius-sm);
  flex-shrink: 0;

  &.status-live {
    background-color: #fff2f0;
    .status-text { color: #ff4d4f; }
  }

  &.status-scheduled {
    background-color: #e6f7ff;
    .status-text { color: #1890ff; }
  }

  &.status-replay {
    background-color: var(--color-bg-secondary);
    .status-text { color: var(--color-text-secondary); }
  }

  .status-text {
    font-size: 11px;
  }
}

.result-subtitle {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.loading-hint,
.empty-hint {
  padding: 12px 0;
  text-align: center;

  .loading-text,
  .empty-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}
</style>
