<!--
 * RoomMessageList - 讨论管理
 * @description 三态：首页选房 → 房间内清扫；也可进全局搜索。找准 → 删掉 → 离开。
 * 对齐运营「默认钉死直播间」；全局为补充入口。删除/清空逻辑沿用既有能力。
 -->
<template>
  <view class="message-list-page">
    <!-- ========== 首页：先选直播间 ========== -->
    <view v-if="scopeMode === 'home'" class="home-panel">
      <text class="home-title">讨论管理</text>
      <text class="home-desc">先选直播间，管理该房讨论。也可全局搜索跨房清扫。</text>

      <view class="home-primary" @tap="openRoomPicker">
        <text class="home-primary-title">选择直播间</text>
        <text class="home-primary-hint">打开即可点选，也可按标题搜索</text>
      </view>

      <view class="home-secondary" @tap="enterGlobalMode">
        <text class="home-secondary-text">全局搜索讨论</text>
        <text class="home-secondary-arrow">›</text>
      </view>
    </view>

    <!-- ========== 房间 / 全局工作区 ========== -->
    <template v-else>
      <!-- 房间钉死条 -->
      <view v-if="scopeMode === 'room'" class="scope-bar scope-bar--room">
        <view class="scope-bar-main">
          <text class="scope-bar-label">当前直播间</text>
          <text class="scope-bar-title">{{ filterRoomTitle || '未命名直播间' }}</text>
        </view>
        <view class="scope-bar-actions">
          <text class="scope-link" @tap="openRoomPicker">更换</text>
          <text class="scope-link scope-link--muted" @tap="goHome">首页</text>
        </view>
      </view>

      <!-- 全局顶栏 -->
      <view v-else class="scope-bar scope-bar--global">
        <view class="scope-bar-main">
          <text class="scope-bar-label">全局讨论</text>
          <text class="scope-bar-hint">跨直播间搜索与清理</text>
        </view>
        <view class="scope-bar-actions">
          <text class="scope-link scope-link--muted" @tap="goHome">首页</text>
        </view>
      </view>

      <view class="page-header">
        <!-- 房间内：关键词为主 -->
        <view v-if="scopeMode === 'room'" class="filter-panel">
          <view class="search-row">
            <input
              v-model="filterKeyword"
              class="field-input search-input"
              placeholder="在该直播间搜索讨论"
              maxlength="100"
              confirm-type="search"
              @confirm="handleSearch"
            />
            <view class="btn btn-primary" @tap="handleSearch">
              <text class="btn-text">查询</text>
            </view>
          </view>

          <view class="fold-toggle" @tap="moreFiltersOpen = !moreFiltersOpen">
            <text class="fold-toggle-text">{{ moreFiltersOpen ? '收起条件' : '用户 / 日期' }}</text>
          </view>

          <template v-if="moreFiltersOpen">
            <view class="filter-field">
              <text class="field-label">用户</text>
              <view class="field-select" @tap="openUserPicker">
                <text :class="filterUserLabel ? 'picker-value' : 'picker-placeholder'">
                  {{ filterUserLabel || '按昵称选择用户' }}
                </text>
                <text v-if="filterUserId" class="field-clear" @tap.stop="clearUserFilter">清除</text>
                <text v-else class="picker-arrow">选择</text>
              </view>
            </view>
            <view class="filter-dates">
              <view class="filter-field filter-field--half">
                <text class="field-label">起</text>
                <picker mode="date" :value="filterStartDate" @change="onStartDateChange">
                  <view class="field-picker">
                    <text :class="filterStartDate ? 'picker-value' : 'picker-placeholder'">
                      {{ filterStartDate || '开始日期' }}
                    </text>
                  </view>
                </picker>
              </view>
              <view class="filter-field filter-field--half">
                <text class="field-label">止</text>
                <picker mode="date" :value="filterEndDate" @change="onEndDateChange">
                  <view class="field-picker">
                    <text :class="filterEndDate ? 'picker-value' : 'picker-placeholder'">
                      {{ filterEndDate || '结束日期' }}
                    </text>
                  </view>
                </picker>
              </view>
            </view>
            <view class="action-row">
              <view class="btn btn-default btn-sm" @tap="handleResetInScope">
                <text class="btn-text">重置条件</text>
              </view>
            </view>
          </template>

          <text v-if="filtersDirty" class="filter-dirty-hint">条件已改，请点击「查询」生效</text>
        </view>

        <!-- 全局：完整筛选 -->
        <view v-else class="filter-panel">
          <view class="filter-field">
            <text class="field-label">内容</text>
            <input
              v-model="filterKeyword"
              class="field-input"
              placeholder="讨论内容关键词"
              maxlength="100"
              @confirm="handleSearch"
            />
          </view>
          <view class="filter-field">
            <text class="field-label">直播间</text>
            <view class="field-select" @tap="openRoomPicker">
              <text :class="filterRoomTitle ? 'picker-value' : 'picker-placeholder'">
                {{ filterRoomTitle || '可选：按标题筛选' }}
              </text>
              <text v-if="filterRoomId" class="field-clear" @tap.stop="clearRoomFilterInGlobal">清除</text>
              <text v-else class="picker-arrow">选择</text>
            </view>
          </view>

          <view class="fold-toggle" @tap="moreFiltersOpen = !moreFiltersOpen">
            <text class="fold-toggle-text">{{ moreFiltersOpen ? '收起条件' : '用户 / 日期' }}</text>
          </view>

          <template v-if="moreFiltersOpen">
            <view class="filter-field">
              <text class="field-label">用户</text>
              <view class="field-select" @tap="openUserPicker">
                <text :class="filterUserLabel ? 'picker-value' : 'picker-placeholder'">
                  {{ filterUserLabel || '按昵称选择用户' }}
                </text>
                <text v-if="filterUserId" class="field-clear" @tap.stop="clearUserFilter">清除</text>
                <text v-else class="picker-arrow">选择</text>
              </view>
            </view>
            <view class="filter-dates">
              <view class="filter-field filter-field--half">
                <text class="field-label">起</text>
                <picker mode="date" :value="filterStartDate" @change="onStartDateChange">
                  <view class="field-picker">
                    <text :class="filterStartDate ? 'picker-value' : 'picker-placeholder'">
                      {{ filterStartDate || '开始日期' }}
                    </text>
                  </view>
                </picker>
              </view>
              <view class="filter-field filter-field--half">
                <text class="field-label">止</text>
                <picker mode="date" :value="filterEndDate" @change="onEndDateChange">
                  <view class="field-picker">
                    <text :class="filterEndDate ? 'picker-value' : 'picker-placeholder'">
                      {{ filterEndDate || '结束日期' }}
                    </text>
                  </view>
                </picker>
              </view>
            </view>
          </template>

          <view class="action-row">
            <view class="btn btn-primary" @tap="handleSearch">
              <text class="btn-text">查询</text>
            </view>
            <view class="btn btn-default" @tap="handleResetInScope">
              <text class="btn-text">重置</text>
            </view>
          </view>
          <text v-if="filtersDirty" class="filter-dirty-hint">条件已改，请点击「查询」生效</text>
        </view>

        <view v-if="filterSummaryText" class="filter-summary">
          <text class="summary-text">{{ filterSummaryText }}</text>
        </view>

        <!-- 工具条：平时极简，选中后出删除，危险操作进更多 -->
        <view
          v-if="tableData.length > 0 || hasSelection"
          class="toolbar-row"
        >
          <text v-if="selectAllPages" class="selected-count">已选全部匹配 {{ total }} 条</text>
          <text v-else-if="selectedIds.length > 0" class="selected-count">已选 {{ selectedIds.length }}</text>
          <view class="toolbar-actions">
            <view
              v-if="tableData.length > 0"
              class="btn btn-default btn-sm"
              @tap="toggleSelectAll"
            >
              <text class="btn-text">{{ isAllSelected && !selectAllPages ? '取消全选' : '全选本页' }}</text>
            </view>
            <view
              v-if="selectAllPages"
              class="btn btn-danger btn-sm"
              @tap="handleClearAllMatching"
            >
              <text class="btn-text">清空匹配 ({{ total }})</text>
            </view>
            <view
              v-else-if="selectedIds.length > 0"
              class="btn btn-danger btn-sm"
              @tap="handleBatchDelete"
            >
              <text class="btn-text">删除 ({{ selectedIds.length }})</text>
            </view>
            <text
              v-if="tableData.length > 0 || canClearRoom"
              class="scope-link scope-link--muted"
              @tap="moreActionsOpen = !moreActionsOpen"
            >
              {{ moreActionsOpen ? '收起' : '更多' }}
            </text>
          </view>
        </view>

        <view v-if="moreActionsOpen && (tableData.length > 0 || canClearRoom)" class="more-actions">
          <view
            v-if="total > 0"
            class="btn btn-default btn-sm"
            @tap="toggleSelectAllPages"
          >
            <text class="btn-text">{{ selectAllPages ? '取消全选所有页' : '全选所有页' }}</text>
          </view>
          <view
            v-if="canClearRoom"
            class="btn btn-warning btn-sm"
            @tap="handleClearRoom"
          >
            <text class="btn-text">清空该直播间全部讨论</text>
          </view>
        </view>
      </view>

      <view v-if="loading" class="loading-state">
        <view class="loading-spinner" />
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="loadError && tableData.length === 0" class="empty-state">
        <text class="empty-text">加载失败</text>
        <text class="empty-hint">请检查网络后重试</text>
        <view class="btn btn-primary btn-sm" @tap="fetchData">
          <text class="btn-text">重试</text>
        </view>
      </view>

      <view v-else-if="tableData.length === 0" class="empty-state">
        <text class="empty-text">{{ emptyListText }}</text>
        <text v-if="hasAppliedExtraFilters" class="empty-hint">可调整条件后点击「查询」</text>
      </view>

      <view v-else class="message-list">
        <view
          v-for="item in tableData"
          :key="item.id"
          class="message-item"
        >
          <view class="item-checkbox" @tap="toggleSelect(item.id)">
            <view :class="['checkbox', isItemSelected(item.id) ? 'checkbox-checked' : '']">
              <text v-if="isItemSelected(item.id)" class="check-icon">✓</text>
            </view>
          </view>

          <view class="item-main">
            <text class="item-content">{{ item.content }}</text>
            <view class="item-header">
              <text class="item-user meta-link" @tap="filterByUser(item)">{{ displayNickname(item) }}</text>
              <text v-if="item.user_role" class="item-role">{{ roleLabel(item.user_role) }}</text>
              <text class="item-time">{{ formatTime(item.created_at) }}</text>
            </view>
            <view class="item-meta">
              <template v-if="scopeMode === 'global'">
                <text class="meta-link" @tap="enterRoomFromItem(item)">
                  {{ item.room_title || shortId(item.room_id) }}
                </text>
                <text class="meta-action" @tap="goToRoom(item)">进房</text>
              </template>
              <template v-else>
                <text class="meta-action" @tap="goToRoom(item)">进房查看</text>
              </template>
            </view>
          </view>

          <view class="item-actions">
            <view class="action-btn action-btn--delete" @tap="handleDelete(item)">
              <text class="action-btn__text">删除</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="total > 0 && !loading" class="pagination-wrapper">
        <text class="page-range">{{ pageRangeText }}</text>
        <view class="pagination">
          <view
            v-if="totalPages > 2"
            :class="['page-btn', currentPage <= 1 ? 'disabled' : '']"
            @tap="changePage(1)"
          >
            <text class="page-btn-text">首页</text>
          </view>
          <view
            :class="['page-btn', currentPage <= 1 ? 'disabled' : '']"
            @tap="changePage(currentPage - 1)"
          >
            <text class="page-btn-text">上一页</text>
          </view>
          <text class="page-info">{{ currentPage }} / {{ totalPages }}</text>
          <view
            :class="['page-btn', currentPage >= totalPages ? 'disabled' : '']"
            @tap="changePage(currentPage + 1)"
          >
            <text class="page-btn-text">下一页</text>
          </view>
          <view
            v-if="totalPages > 2"
            :class="['page-btn', currentPage >= totalPages ? 'disabled' : '']"
            @tap="changePage(totalPages)"
          >
            <text class="page-btn-text">末页</text>
          </view>
        </view>
        <view class="page-size-row">
          <text class="page-size-label">每页</text>
          <view
            v-for="size in pageSizeOptions"
            :key="size"
            :class="['page-size-chip', pageSize === size ? 'is-active' : '']"
            @tap="changePageSize(size)"
          >
            <text class="page-size-text">{{ size }}</text>
          </view>
        </view>
      </view>
    </template>

    <!-- 选直播间：打开即浏览首屏，搜索仅收窄（对齐大厂选内容容器） -->
    <view v-if="roomPickerVisible" class="picker-mask" @tap="roomPickerVisible = false">
      <view class="picker-sheet picker-sheet--room" @tap.stop>
        <view class="picker-sheet-header">
          <text class="picker-sheet-title">选择直播间</text>
          <text class="picker-sheet-close" @tap="roomPickerVisible = false">关闭</text>
        </view>
        <view class="user-search-box">
          <input
            v-model="roomSearchKw"
            class="field-input"
            placeholder="搜索标题（可选）"
            confirm-type="search"
            @confirm="searchRooms"
          />
          <view v-if="roomSearchKw" class="btn btn-default btn-sm" @tap="clearRoomSearch">
            <text class="btn-text">清空</text>
          </view>
          <view class="btn btn-primary btn-sm" @tap="searchRooms">
            <text class="btn-text">搜索</text>
          </view>
        </view>
        <scroll-view
          scroll-y
          class="room-result-list"
          @scrolltolower="loadMoreRooms"
        >
          <view v-if="roomSearchLoading && roomSearchResults.length === 0" class="empty-hint-inline">
            加载中...
          </view>
          <view
            v-for="r in roomSearchResults"
            :key="r.id"
            class="room-result-item"
            @tap="confirmRoomPicker(r)"
          >
            <view class="room-result-main">
              <text class="room-result-name">{{ r.title || '未命名直播间' }}</text>
              <text v-if="r.is_private" class="room-result-tag">不公开</text>
            </view>
          </view>
          <view
            v-if="!roomSearchLoading && roomSearchResults.length === 0"
            class="empty-hint-inline"
          >
            {{ roomSearchKw.trim() ? '未找到直播间' : '暂无直播间' }}
          </view>
          <view
            v-if="roomSearchHasMore && !roomSearchLoading"
            class="btn btn-default btn-sm room-load-more"
            @tap="loadMoreRooms"
          >
            <text class="btn-text">加载更多</text>
          </view>
          <view
            v-else-if="roomSearchResults.length > 0 && !roomSearchHasMore"
            class="empty-hint-inline empty-hint-inline--end"
          >
            已加载全部
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- 选用户 -->
    <view v-if="userPickerVisible" class="picker-mask" @tap="userPickerVisible = false">
      <view class="picker-sheet" @tap.stop>
        <view class="picker-sheet-header">
          <text class="picker-sheet-title">选择用户</text>
          <text class="picker-sheet-close" @tap="userPickerVisible = false">关闭</text>
        </view>
        <view class="user-search-box">
          <input
            v-model="userSearchKw"
            class="field-input"
            placeholder="输入昵称搜索"
            confirm-type="search"
            @confirm="searchUsers"
          />
          <view class="btn btn-primary btn-sm" @tap="searchUsers">
            <text class="btn-text">搜索</text>
          </view>
        </view>
        <scroll-view scroll-y class="user-result-list">
          <view v-if="userSearchLoading" class="empty-hint-inline">搜索中...</view>
          <view
            v-for="u in userSearchResults"
            :key="u.public_id"
            class="user-result-item"
            @tap="confirmUserPicker(u)"
          >
            <text class="user-result-name">{{ u.nickname || u.username || '未命名' }}</text>
            <text class="user-result-sub">{{ u.username }}</text>
          </view>
          <view v-if="!userSearchLoading && userSearchKw && userSearchResults.length === 0" class="empty-hint-inline">
            未找到用户
          </view>
          <view v-if="!userSearchKw && userSearchResults.length === 0" class="empty-hint-inline">
            输入昵称后搜索，无需填写 UUID
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { logger } from '@/logs/logger'
import { getAdminMessages, deleteMessage, batchDeleteMessages, clearRoomMessages } from '@/api/roomMessage'
import { getRoomById, getAdminRooms } from '@/api/room'
import { getAdminUsers } from '@/api/user'
import {
  getRoomMessageErrorMessage,
  ROOM_MESSAGE_ERROR_CODES
} from '@/types/roomMessage'
import type { AdminMessageItem, AdminMessageQueryParams } from '@/types/roomMessage'
import type { ParsedSearchFilters } from '@/utils/roomMessageSearch'
import { normalizeRoomMessageItem, resolveMessageDisplayName } from '@/utils/roomMessageNormalize'
import {
  ADMIN_USER_ROLE_LABEL,
  normalizeAdminUserRole
} from '@/types/adminUser'
import type { AdminUserResponse } from '@/types/adminUser'
import type { AdminRoomListItem } from '@/types/adminRoom'

type ScopeMode = 'home' | 'room' | 'global'

const authStore = useAuthStore()
/** home=选房；room=钉死直播间；global=跨房搜索 */
const scopeMode = ref<ScopeMode>('home')
const moreFiltersOpen = ref(false)
const moreActionsOpen = ref(false)

const tableData = ref<AdminMessageItem[]>([])
const loading = ref(false)
const loadError = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const pageSizeOptions = [20, 50] as const
const selectedIds = ref<string[]>([])
/** 虚拟全选：表示当前筛选下所有页，不一次性拉全量进内存 */
const selectAllPages = ref(false)
const filterSummary = ref<Record<string, unknown> | null>(null)
/** 防竞态：只采纳最后一次请求结果 */
let fetchSeq = 0
const BATCH_DELETE_LIMIT = 200
const CLEAR_ALL_WARN_COUNT = 2000
const CLEAR_ALL_SAFETY_MAX = 50000
const CLEAR_FETCH_PAGE_SIZE = 100

const filterKeyword = ref('')
const filterRoomId = ref('')
const filterRoomTitle = ref('')
const filterUserId = ref('')
const filterUserLabel = ref('')
const filterStartDate = ref('')
const filterEndDate = ref('')
const parsedFilters = ref<ParsedSearchFilters>({})

const roomPickerVisible = ref(false)
const roomSearchKw = ref('')
const roomSearchLoading = ref(false)
const roomSearchResults = ref<AdminRoomListItem[]>([])
const roomSearchPage = ref(1)
const roomSearchHasMore = ref(false)
const userPickerVisible = ref(false)
const userSearchKw = ref('')
const userSearchLoading = ref(false)
const userSearchResults = ref<AdminUserResponse[]>([])

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const pageRangeText = computed(() => {
  if (total.value <= 0) return ''
  const start = (currentPage.value - 1) * pageSize.value + 1
  const end = Math.min(currentPage.value * pageSize.value, total.value)
  return `第 ${start}–${end} 条 · 共 ${total.value} 条 · 每页 ${pageSize.value}`
})

const isAllSelected = computed(() =>
  tableData.value.length > 0 &&
  tableData.value.every(item => selectedIds.value.includes(item.id))
)

const hasSelection = computed(() => selectAllPages.value || selectedIds.value.length > 0)

const canClearRoom = computed(() => Boolean(parsedFilters.value.room_id?.trim()))

const hasAppliedExtraFilters = computed(() => {
  const f = parsedFilters.value
  return Boolean(f.keyword || f.user_id || f.start_time || f.end_time || (scopeMode.value === 'global' && f.room_id))
})

const emptyListText = computed(() => {
  if (hasAppliedExtraFilters.value) return '未找到匹配的讨论'
  if (scopeMode.value === 'room') return '该直播间暂无讨论'
  return '暂无讨论数据'
})

const filtersDirty = computed(() => {
  const draft = buildFiltersFromFields()
  const applied = parsedFilters.value
  return (
    (draft.keyword || '') !== (applied.keyword || '') ||
    (draft.room_id || '') !== (applied.room_id || '') ||
    (draft.user_id || '') !== (applied.user_id || '') ||
    (draft.start_time || '') !== (applied.start_time || '') ||
    (draft.end_time || '') !== (applied.end_time || '')
  )
})

const filterSummaryText = computed(() => {
  if (scopeMode.value === 'home') return ''
  const parts: string[] = []
  if (total.value > 0) parts.push(`共 ${total.value} 条`)
  const summary = filterSummary.value
  if (summary) {
    if (summary.keyword) parts.push(`关键词: ${summary.keyword}`)
    if (scopeMode.value === 'global' && summary.room_count != null) {
      parts.push(`涉及直播间: ${summary.room_count}`)
    }
    if (summary.user_count != null) parts.push(`涉及用户: ${summary.user_count}`)
  }
  if (parsedFilters.value.user_id) {
    parts.push(filterUserLabel.value ? `用户: ${filterUserLabel.value}` : '已按用户筛选')
  }
  return parts.join(' · ')
})

const clearRoomLabel = computed(() => {
  if (filterRoomTitle.value) return filterRoomTitle.value
  const roomId = parsedFilters.value.room_id?.trim()
  if (!roomId) return ''
  const title = tableData.value.find(i => i.room_id === roomId)?.room_title
  return title || shortId(roomId)
})

function displayNickname(item: AdminMessageItem): string {
  return resolveMessageDisplayName(normalizeRoomMessageItem(item))
}

function roleLabel(role?: string | null): string {
  if (!role) return ''
  return ADMIN_USER_ROLE_LABEL[normalizeAdminUserRole(role)] || role
}

function shortId(id?: string | null): string {
  const raw = (id || '').trim()
  if (!raw) return '—'
  if (raw.length <= 12) return raw
  return `${raw.slice(0, 8)}…${raw.slice(-4)}`
}

function formatTime(iso: string): string {
  if (!iso) return ''
  const diffMs = Date.now() - new Date(iso).getTime()
  const min = Math.floor(diffMs / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min}分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}小时前`
  const day = Math.floor(hr / 24)
  if (day < 7) return `${day}天前`
  return new Date(iso).toLocaleDateString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
}

function normalizeIso(value: string, kind: 'start' | 'end'): string {
  const trimmed = value.trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    const time = kind === 'start' ? 'T00:00:00' : 'T23:59:59'
    return new Date(`${trimmed}${time}`).toISOString()
  }
  return new Date(trimmed).toISOString()
}

function buildFiltersFromFields(): ParsedSearchFilters {
  const filters: ParsedSearchFilters = {}
  const keyword = filterKeyword.value.trim()
  const roomId = filterRoomId.value.trim()
  const userId = filterUserId.value.trim()
  if (keyword) filters.keyword = keyword.slice(0, 100)
  if (roomId) filters.room_id = roomId
  if (userId) filters.user_id = userId
  if (filterStartDate.value) filters.start_time = normalizeIso(filterStartDate.value, 'start')
  if (filterEndDate.value) filters.end_time = normalizeIso(filterEndDate.value, 'end')
  return filters
}

function buildQueryParams(): AdminMessageQueryParams {
  return {
    page: currentPage.value,
    page_size: pageSize.value,
    ...parsedFilters.value
  }
}

function extractErrorMessage(error: unknown): string {
  const err = error as { code?: number; message?: string; data?: { message?: string } }
  const code = err?.code ?? (err?.data as { code?: number } | undefined)?.code
  const msg = err?.message || (err?.data as { message?: string } | undefined)?.message
  return getRoomMessageErrorMessage(code, msg)
}

function contentSnippet(content?: string | null, max = 40): string {
  const text = (content || '').replace(/\s+/g, ' ').trim()
  if (!text) return '（无内容）'
  return text.length > max ? `${text.slice(0, max)}…` : text
}

function clearListState() {
  tableData.value = []
  total.value = 0
  selectedIds.value = []
  selectAllPages.value = false
  filterSummary.value = null
  loadError.value = false
  currentPage.value = 1
  moreActionsOpen.value = false
}

function resetExtraFilters() {
  filterKeyword.value = ''
  filterUserId.value = ''
  filterUserLabel.value = ''
  filterStartDate.value = ''
  filterEndDate.value = ''
  moreFiltersOpen.value = false
}

function goHome() {
  scopeMode.value = 'home'
  filterRoomId.value = ''
  filterRoomTitle.value = ''
  resetExtraFilters()
  parsedFilters.value = {}
  clearListState()
  loading.value = false
}

function enterGlobalMode() {
  scopeMode.value = 'global'
  filterRoomId.value = ''
  filterRoomTitle.value = ''
  resetExtraFilters()
  parsedFilters.value = {}
  moreActionsOpen.value = false
  currentPage.value = 1
  fetchData()
}

function enterRoomMode(roomId: string, roomTitle: string) {
  scopeMode.value = 'room'
  filterRoomId.value = roomId
  filterRoomTitle.value = roomTitle
  resetExtraFilters()
  parsedFilters.value = { room_id: roomId }
  moreActionsOpen.value = false
  currentPage.value = 1
  fetchData()
}

function onStartDateChange(e: { detail?: { value?: string } }) {
  filterStartDate.value = e.detail?.value || ''
}

function onEndDateChange(e: { detail?: { value?: string } }) {
  filterEndDate.value = e.detail?.value || ''
}

async function fetchData() {
  if (scopeMode.value === 'home') return
  const seq = ++fetchSeq
  loading.value = true
  loadError.value = false
  selectedIds.value = []
  selectAllPages.value = false
  try {
    const params = buildQueryParams()
    logger.info('network', '加载管理端讨论列表', { scope: scopeMode.value, ...params })
    const res = await getAdminMessages(params)
    if (seq !== fetchSeq) return
    const rawItems = res.data?.items || []
    tableData.value = rawItems.map((item) => {
      const normalized = normalizeRoomMessageItem(item)
      return {
        ...item,
        user: normalized.user,
        user_display_name: normalized.user_display_name,
        user_nickname: normalized.user?.nickname || item.user_nickname || null
      }
    })
    total.value = res.data?.total || 0
    filterSummary.value = (res.data?.filter_summary as Record<string, unknown>) || null
  } catch (error) {
    if (seq !== fetchSeq) return
    loadError.value = true
    logger.error('system', '加载管理端讨论列表失败', error)
    uni.showToast({ title: extractErrorMessage(error), icon: 'none' })
  } finally {
    if (seq === fetchSeq) loading.value = false
  }
}

function handleSearch() {
  if (scopeMode.value === 'home') return
  if (scopeMode.value === 'room' && !filterRoomId.value.trim()) {
    uni.showToast({ title: '请先选择直播间', icon: 'none' })
    return
  }
  const draft = buildFiltersFromFields()
  if (scopeMode.value === 'room') {
    draft.room_id = filterRoomId.value.trim()
  }
  if (draft.start_time && draft.end_time) {
    const startMs = new Date(draft.start_time).getTime()
    const endMs = new Date(draft.end_time).getTime()
    if (!Number.isNaN(startMs) && !Number.isNaN(endMs) && startMs > endMs) {
      uni.showToast({ title: '开始日期不能晚于结束日期', icon: 'none' })
      return
    }
  }
  parsedFilters.value = draft
  currentPage.value = 1
  fetchData()
}

/** 房间内重置：保留钉死的直播间；全局重置：清空全部条件 */
function handleResetInScope() {
  if (scopeMode.value === 'room') {
    const roomId = filterRoomId.value.trim()
    resetExtraFilters()
    parsedFilters.value = roomId ? { room_id: roomId } : {}
    currentPage.value = 1
    filterSummary.value = null
    fetchData()
    return
  }
  filterRoomId.value = ''
  filterRoomTitle.value = ''
  resetExtraFilters()
  parsedFilters.value = {}
  currentPage.value = 1
  filterSummary.value = null
  fetchData()
}

function openRoomPicker() {
  roomSearchKw.value = ''
  roomSearchResults.value = []
  roomSearchPage.value = 1
  roomSearchHasMore.value = false
  roomPickerVisible.value = true
  // 打开即拉首屏，可直接点选
  fetchRoomSearchPage(false)
}

function clearRoomSearch() {
  roomSearchKw.value = ''
  roomSearchPage.value = 1
  roomSearchResults.value = []
  fetchRoomSearchPage(false)
}

function clearRoomFilterInGlobal() {
  filterRoomId.value = ''
  filterRoomTitle.value = ''
  if (parsedFilters.value.room_id) {
    const next = { ...parsedFilters.value }
    delete next.room_id
    parsedFilters.value = next
    currentPage.value = 1
    fetchData()
  }
}

async function searchRooms() {
  roomSearchPage.value = 1
  roomSearchResults.value = []
  await fetchRoomSearchPage(false)
}

async function loadMoreRooms() {
  if (!roomSearchHasMore.value || roomSearchLoading.value) return
  roomSearchPage.value += 1
  await fetchRoomSearchPage(true)
}

/** 空关键词 = 浏览分页；有关键词 = 标题收窄。不一次拉全量。 */
async function fetchRoomSearchPage(append: boolean) {
  const kw = roomSearchKw.value.trim()
  roomSearchLoading.value = true
  try {
    const params: { page: number; size: number; q?: string } = {
      page: roomSearchPage.value,
      size: 20
    }
    if (kw) params.q = kw
    const res = await getAdminRooms(params)
    const items = res.data?.items || []
    const totalRooms = res.data?.total || 0
    roomSearchResults.value = append ? [...roomSearchResults.value, ...items] : items
    roomSearchHasMore.value = roomSearchResults.value.length < totalRooms
  } catch (error) {
    logger.error('system', '加载直播间列表失败', error)
    uni.showToast({ title: kw ? '搜索直播间失败' : '加载直播间失败', icon: 'none' })
    if (!append) roomSearchResults.value = []
    roomSearchHasMore.value = false
  } finally {
    roomSearchLoading.value = false
  }
}

function confirmRoomPicker(room: AdminRoomListItem) {
  const id = String(room.id || '').trim()
  if (!id) {
    uni.showToast({ title: '该直播间缺少可用ID', icon: 'none' })
    return
  }
  const title = room.title || shortId(id)
  roomPickerVisible.value = false

  if (scopeMode.value === 'global') {
    filterRoomId.value = id
    filterRoomTitle.value = title
    return
  }
  // 首页或房间态：钉死并进入房间工作区
  enterRoomMode(id, title)
}

async function resolveRoomTitle(roomId: string): Promise<string> {
  const fromList = tableData.value.find(i => i.room_id === roomId)?.room_title
  if (fromList) return String(fromList)
  try {
    const resp = await getRoomById(roomId)
    if (resp.data?.title) return String(resp.data.title)
  } catch {
    // ignore
  }
  return shortId(roomId)
}

function openUserPicker() {
  userSearchKw.value = ''
  userSearchResults.value = []
  userPickerVisible.value = true
}

function clearUserFilter() {
  filterUserId.value = ''
  filterUserLabel.value = ''
  if (parsedFilters.value.user_id) {
    const next = { ...parsedFilters.value }
    delete next.user_id
    parsedFilters.value = next
    currentPage.value = 1
    fetchData()
  }
}

async function searchUsers() {
  const kw = userSearchKw.value.trim()
  if (!kw) {
    uni.showToast({ title: '请输入昵称', icon: 'none' })
    return
  }
  userSearchLoading.value = true
  try {
    const res = await getAdminUsers({ page: 1, size: 20, nickname: kw })
    let items = res.data?.items || []
    if (items.length === 0) {
      const byUser = await getAdminUsers({ page: 1, size: 20, username: kw })
      items = byUser.data?.items || []
    }
    userSearchResults.value = items
  } catch (error) {
    logger.error('system', '搜索用户失败', error)
    uni.showToast({ title: '搜索用户失败', icon: 'none' })
    userSearchResults.value = []
  } finally {
    userSearchLoading.value = false
  }
}

function confirmUserPicker(user: AdminUserResponse) {
  const uid = (user.public_id || '').trim()
  if (!uid) {
    uni.showToast({ title: '该用户缺少可用ID', icon: 'none' })
    return
  }
  filterUserId.value = uid
  filterUserLabel.value = user.nickname || user.username || shortId(uid)
  userPickerVisible.value = false
}

function enterRoomFromItem(item: AdminMessageItem) {
  const roomId = (item.room_id || '').trim()
  if (!roomId) return
  enterRoomMode(roomId, item.room_title || shortId(roomId))
}

function filterByUser(item: AdminMessageItem) {
  const userId = (item.user_id || '').trim()
  if (!userId) return
  filterUserId.value = userId
  filterUserLabel.value = displayNickname(item)
  moreFiltersOpen.value = true
  handleSearch()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  currentPage.value = page
  fetchData()
}

function changePageSize(size: number) {
  if (pageSize.value === size) return
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

function isItemSelected(id: string): boolean {
  return selectAllPages.value || selectedIds.value.includes(id)
}

function toggleSelect(id: string) {
  if (selectAllPages.value) {
    selectAllPages.value = false
    selectedIds.value = tableData.value.map(item => item.id).filter(x => x !== id)
    return
  }
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function toggleSelectAll() {
  selectAllPages.value = false
  if (isAllSelected.value) {
    selectedIds.value = []
    return
  }
  selectedIds.value = tableData.value.map(item => item.id)
}

function toggleSelectAllPages() {
  if (selectAllPages.value) {
    selectAllPages.value = false
    selectedIds.value = []
    return
  }
  if (total.value <= 0) {
    uni.showToast({ title: '当前没有可匹配的讨论', icon: 'none' })
    return
  }
  selectAllPages.value = true
  selectedIds.value = tableData.value.map(item => item.id)
  moreActionsOpen.value = true
}

function hasOnlyRoomFilter(): boolean {
  const f = parsedFilters.value
  return Boolean(
    f.room_id?.trim() &&
    !f.keyword?.trim() &&
    !f.user_id?.trim() &&
    !f.start_time &&
    !f.end_time
  )
}

function describeActiveFilters(): string {
  const parts: string[] = []
  const f = parsedFilters.value
  if (f.keyword) parts.push(`关键词「${f.keyword}」`)
  if (f.room_id) parts.push(filterRoomTitle.value ? `房间「${filterRoomTitle.value}」` : '指定直播间')
  if (f.user_id) parts.push(filterUserLabel.value ? `用户「${filterUserLabel.value}」` : '指定用户')
  if (f.start_time || f.end_time) parts.push('时间范围')
  return parts.length ? parts.join('、') : '全站（无筛选）'
}

async function batchDeleteInChunks(ids: string[]): Promise<{ deleted: number; failed: number }> {
  let deleted = 0
  let failed = 0
  for (let i = 0; i < ids.length; i += BATCH_DELETE_LIMIT) {
    const chunk = ids.slice(i, i + BATCH_DELETE_LIMIT)
    const result = await batchDeleteMessages({ message_ids: chunk })
    deleted += result.data?.deleted_count ?? 0
    failed += result.data?.failed_count ?? 0
  }
  return { deleted, failed }
}

async function drainMatchingMessages(
  expectedTotal: number,
  onProgress?: (done: number, expected: number) => void
): Promise<{ deleted: number; failed: number; stoppedEarly: boolean }> {
  let deleted = 0
  let failed = 0
  let idleRounds = 0

  while (deleted + failed < CLEAR_ALL_SAFETY_MAX) {
    const res = await getAdminMessages({
      page: 1,
      page_size: CLEAR_FETCH_PAGE_SIZE,
      ...parsedFilters.value
    })
    const items = res.data?.items || []
    const ids = items.map(i => i.id).filter(Boolean)
    if (ids.length === 0) break

    const chunkResult = await batchDeleteInChunks(ids)
    deleted += chunkResult.deleted
    failed += chunkResult.failed
    onProgress?.(deleted, expectedTotal)

    if (chunkResult.deleted === 0) {
      idleRounds += 1
      if (idleRounds >= 3) break
    } else {
      idleRounds = 0
    }
  }

  const stoppedEarly = deleted + failed >= CLEAR_ALL_SAFETY_MAX
  return { deleted, failed, stoppedEarly }
}

async function handleClearAllMatching() {
  if (!selectAllPages.value || total.value <= 0) return

  if (hasOnlyRoomFilter()) {
    handleClearRoom()
    return
  }

  const count = total.value
  const scope = describeActiveFilters()
  const largeHint =
    count > CLEAR_ALL_WARN_COUNT
      ? `\n数量较大（约 ${count} 条），将自动分批清空，请保持页面勿关闭。`
      : ''

  uni.showModal({
    title: '清空全部匹配',
    content: `将删除当前筛选下全部约 ${count} 条讨论（${scope}），含所有页，不可恢复。${largeHint}`,
    confirmText: '确认清空',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (!res.confirm) return
      uni.showLoading({ title: `清空中 0/${count}`, mask: true })
      try {
        const { deleted, failed, stoppedEarly } = await drainMatchingMessages(count, (done, expected) => {
          uni.showLoading({
            title: `清空中 ${done}/${expected}`,
            mask: true
          })
        })
        selectAllPages.value = false
        selectedIds.value = []

        if (stoppedEarly) {
          uni.showToast({
            title: `已处理 ${deleted} 条（达单次上限），请再次「全选所有页」继续`,
            icon: 'none',
            duration: 3500
          })
        } else {
          uni.showToast({
            title: failed > 0 ? `已删 ${deleted} 条，失败 ${failed} 条` : `已清空 ${deleted} 条`,
            icon: 'none',
            duration: 2500
          })
        }
        fetchData()
      } catch (error) {
        logger.error('system', '清空全部匹配失败', error)
        uni.showToast({ title: extractErrorMessage(error), icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    }
  })
}

function goToRoom(item: AdminMessageItem) {
  const roomId = (item.room_id || '').trim()
  if (!roomId) {
    uni.showToast({ title: '缺少直播间ID', icon: 'none' })
    return
  }
  uni.navigateTo({
    url: `/pages/live/LiveView?roomId=${encodeURIComponent(roomId)}`
  })
}

async function handleDelete(item: AdminMessageItem) {
  const room = item.room_title || shortId(item.room_id)
  uni.showModal({
    title: '确认删除',
    content: `房间「${room}」\n「${contentSnippet(item.content)}」\n删除后不可恢复。`,
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteMessage(item.room_id, item.id)
        uni.showToast({ title: '删除成功', icon: 'success' })
        fetchData()
      } catch (error) {
        uni.showToast({ title: extractErrorMessage(error), icon: 'none' })
      }
    }
  })
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  if (selectedIds.value.length > 200) {
    uni.showToast({ title: '单次最多删除 200 条', icon: 'none' })
    return
  }

  uni.showModal({
    title: '批量删除',
    content: `确定删除选中的 ${selectedIds.value.length} 条讨论吗？删除后不可恢复。`,
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const result = await batchDeleteMessages({ message_ids: [...selectedIds.value] })
        const deleted = result.data?.deleted_count ?? 0
        const failed = result.data?.failed_count ?? 0
        uni.showToast({
          title: failed > 0 ? `已删 ${deleted} 条，失败 ${failed} 条` : `已删除 ${deleted} 条`,
          icon: 'none'
        })
        fetchData()
      } catch (error) {
        uni.showToast({ title: extractErrorMessage(error), icon: 'none' })
      }
    }
  })
}

async function handleClearRoom() {
  const roomId = parsedFilters.value.room_id?.trim()
  if (!roomId) return

  const label = clearRoomLabel.value

  uni.showModal({
    title: '清空直播间讨论',
    content: `将删除「${label}」的全部讨论（与当前关键词/用户/时间筛选无关），不可恢复。\n完整ID：${roomId}`,
    confirmText: '确认清空',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const result = await clearRoomMessages(roomId)
        const count = result.data?.deleted_count ?? 0
        uni.showToast({ title: `已清空 ${count} 条讨论`, icon: 'success' })
        fetchData()
      } catch (error) {
        const err = error as { code?: number }
        if (err?.code === ROOM_MESSAGE_ERROR_CODES.NOT_FOUND) {
          uni.showToast({ title: '直播间不存在', icon: 'none' })
        } else {
          uni.showToast({ title: extractErrorMessage(error), icon: 'none' })
        }
      }
    }
  })
}

const pendingRoomIdFromQuery = ref('')

onLoad((query) => {
  const roomId = String(query?.roomId || query?.room_id || '').trim()
  if (roomId) pendingRoomIdFromQuery.value = roomId
})

onMounted(() => {
  logger.info('system', '进入讨论管理页')
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    const redirectPath = pendingRoomIdFromQuery.value
      ? `/pages/admin/roomMessage/RoomMessageList?roomId=${encodeURIComponent(pendingRoomIdFromQuery.value)}`
      : '/pages/admin/roomMessage/RoomMessageList'
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/auth/OneTapLogin?redirect=' + encodeURIComponent(redirectPath) })
    }, 300)
    return
  }
  if (!authStore.isAdmin) {
    uni.showToast({ title: '权限不足：仅管理员可访问', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 1500)
    return
  }
  if (pendingRoomIdFromQuery.value) {
    const roomId = pendingRoomIdFromQuery.value
    pendingRoomIdFromQuery.value = ''
    scopeMode.value = 'room'
    filterRoomId.value = roomId
    parsedFilters.value = { room_id: roomId }
    resolveRoomTitle(roomId).then((title) => {
      filterRoomTitle.value = title
    })
    fetchData()
    return
  }
  // 默认首页：不拉全站列表
  scopeMode.value = 'home'
})

onPullDownRefresh(async () => {
  try {
    if (scopeMode.value !== 'home') await fetchData()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.message-list-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-md);
}

.home-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 28px 8px 16px;
}

.home-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.3;
}

.home-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-bottom: 8px;
}

.home-primary {
  padding: 20px 16px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.home-primary-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
}

.home-primary-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.home-secondary {
  margin-top: 4px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px dashed var(--color-border);
}

.home-secondary-text {
  font-size: 14px;
  color: var(--color-text-primary);
}

.home-secondary-arrow {
  font-size: 18px;
  color: var(--color-text-tertiary);
}

.scope-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  margin-bottom: var(--spacing-sm);
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.scope-bar--room {
  border-left: 3px solid var(--color-primary);
}

.scope-bar--global {
  border-left: 3px solid var(--color-text-tertiary);
}

.scope-bar-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.scope-bar-label {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.scope-bar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  word-break: break-word;
}

.scope-bar-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.scope-bar-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 2px;
}

.scope-link {
  font-size: 13px;
  color: var(--color-primary);

  &--muted {
    color: var(--color-text-secondary);
  }
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.filter-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.search-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  flex: 1;
}

.fold-toggle {
  padding: 2px 0;
}

.fold-toggle-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.filter-field {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;

  &--half {
    flex: 1;
  }

  picker {
    flex: 1;
    min-width: 0;
  }
}

.field-label {
  flex-shrink: 0;
  width: 44px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.field-input {
  flex: 1;
  min-width: 0;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 13px;
  background-color: var(--color-bg-primary);
  box-sizing: border-box;
}

.field-select {
  flex: 1;
  min-width: 0;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
}

.field-clear,
.picker-arrow {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--color-primary);
}

.field-clear {
  color: var(--color-text-secondary);
}

.field-picker {
  flex: 1;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  display: flex;
  align-items: center;
  box-sizing: border-box;
  min-width: 0;
}

.picker-value {
  font-size: 13px;
  color: var(--color-text-primary);
}

.picker-placeholder {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.filter-dates {
  display: flex;
  gap: var(--spacing-sm);
}

.action-row,
.toolbar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
}

.filter-dirty-hint {
  font-size: 12px;
  color: #d48806;
  line-height: 1.4;
}

.toolbar-row {
  justify-content: space-between;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
  margin-left: auto;
}

.more-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  padding: 0 2px;
}

.selected-count {
  font-size: 13px;
  color: var(--color-primary);
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  padding: 0 14px;
  border-radius: var(--border-radius-base);

  .btn-text {
    font-size: 13px;
    color: #ffffff;
  }
}

.btn-sm {
  height: 30px;
  padding: 0 10px;

  .btn-text {
    font-size: 12px;
  }
}

.btn-primary {
  background-color: var(--color-primary);
}

.btn-default {
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--color-border);

  .btn-text {
    color: var(--color-text-primary);
  }
}

.btn-danger {
  background-color: #ff4d4f;
}

.btn-warning {
  background-color: #fa8c16;
}

.filter-summary {
  padding: 6px 10px;
  background-color: #f6ffed;
  border-radius: var(--border-radius-sm);

  .summary-text {
    font-size: 12px;
    color: #389e0d;
    line-height: 1.4;
  }
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 12px;
  border-bottom: 1px solid var(--color-border);

  &:last-child {
    border-bottom: none;
  }
}

.item-checkbox {
  padding-top: 2px;

  .checkbox {
    width: 18px;
    height: 18px;
    border: 2px solid var(--color-border);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;

    &.checkbox-checked {
      background-color: var(--color-primary);
      border-color: var(--color-primary);
    }

    .check-icon {
      font-size: 11px;
      color: #ffffff;
    }
  }
}

.item-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.item-content {
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 1.45;
  word-break: break-word;
  white-space: pre-wrap;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.item-user {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.item-role {
  font-size: 11px;
  color: var(--color-text-secondary);
  background-color: var(--color-bg-secondary);
  padding: 1px 5px;
  border-radius: 3px;
}

.item-time {
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.meta-link {
  font-size: 12px;
  color: var(--color-primary);
}

.meta-action {
  font-size: 12px;
  color: var(--color-text-secondary);
  text-decoration: underline;
}

.picker-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.picker-sheet {
  width: 100%;
  max-height: 78vh;
  background: var(--color-bg-primary);
  border-radius: 12px 12px 0 0;
  padding: 12px 14px 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;

  &--room {
    height: 72vh;
    max-height: 72vh;
    padding-bottom: calc(16px + env(safe-area-inset-bottom));
  }
}

.picker-sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-sheet-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.picker-sheet-close {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.user-search-box {
  display: flex;
  gap: 8px;
  align-items: center;
}

.user-result-list {
  max-height: 50vh;
}

.room-result-list {
  flex: 1;
  min-height: 0;
  height: 0;
}

.user-result-item {
  padding: 10px 4px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.room-result-item {
  min-height: 48px;
  padding: 14px 4px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

.room-result-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-result-name,
.room-result-name {
  font-size: 15px;
  color: var(--color-text-primary);
  line-height: 1.35;
  word-break: break-word;
}

.room-result-tag {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: 3px;
}

.user-result-sub {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.empty-hint-inline {
  padding: 24px 0;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-tertiary);

  &--end {
    padding: 12px 0 8px;
    font-size: 12px;
  }
}

.item-actions {
  flex-shrink: 0;
}

.action-btn {
  padding: 4px 10px;
  border-radius: var(--border-radius-sm);

  &--delete {
    background-color: #fff2f0;
  }

  &__text {
    font-size: 12px;
    color: #ff4d4f;
  }
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  gap: var(--spacing-md);
}

.empty-text,
.loading-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.empty-hint {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.pagination-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.page-range {
  font-size: 12px;
  color: var(--color-text-secondary);
  text-align: center;
}

.pagination {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--spacing-sm);
}

.page-size-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-size-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.page-size-chip {
  min-width: 36px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-primary);

  &.is-active {
    border-color: var(--color-primary);
    background: rgba(24, 144, 255, 0.08);
  }

  .page-size-text {
    font-size: 12px;
    color: var(--color-text-primary);
  }
}

.room-load-more {
  margin: 12px auto;
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 16px;
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);

  &.disabled {
    opacity: 0.5;
  }

  .page-btn-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }
}

.page-info {
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
