<!--
 * AdminRoomList - 管理端直播间内容运营列表
 * 对齐《Live-Saas-Wechat-17-管理端直播间内容运营MVP-前端设计文档-v1.0》
 * 风格对齐 UserList / TagList / CategoryList
 -->
<template>
  <view class="admin-room-list-page">
    <view class="page-header">
      <view class="header-title-row">
        <view class="header-title">
          <text class="title">直播间运营</text>
          <text class="subtitle">全站房间运营：封面旁看房主，下方改标题与 Tab</text>
        </view>
        <view class="btn-refresh" @tap="handleRefresh">
          <text class="btn-text">刷新</text>
        </view>
      </view>

      <view class="header-actions">
        <view class="search-box">
          <input
            v-model="keyword"
            class="search-input"
            placeholder="搜索标题或房主 UUID"
            maxlength="100"
            @confirm="handleSearch"
          />
          <view v-if="keyword" class="search-clear" @tap="keyword = ''; handleSearch()">✕</view>
        </view>
      </view>

      <view class="filter-row">
        <picker :range="privacyOptions" range-key="label" :value="privacyPickerIndex" @change="handlePrivacyChange">
          <view class="filter-picker">
            <text>{{ currentPrivacyLabel }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <view class="btn-query" @tap="handleSearch">
          <text class="btn-text">查询</text>
        </view>
        <view class="btn-reset" @tap="handleReset">
          <text class="btn-text">重置</text>
        </view>
      </view>
    </view>

    <view v-if="!accessGranted" class="empty-state">
      <text class="empty-text">{{ accessMessage }}</text>
    </view>

    <view v-else-if="loading" class="loading-state">
      <view class="loading-spinner" />
      <text class="loading-text">加载中...</text>
    </view>

    <view v-else-if="errorMsg" class="empty-state">
      <text class="empty-text">{{ errorMsg }}</text>
      <view class="btn-query retry-btn" @tap="fetchData">
        <text class="btn-text">重试</text>
      </view>
    </view>

    <view v-else class="room-list">
      <view v-if="list.length === 0" class="empty-state">
        <text class="empty-text">{{ hasActiveFilter ? '未找到匹配的直播间' : '暂无直播间数据' }}</text>
        <text v-if="hasActiveFilter" class="empty-hint">可清空条件后点「重置」查看全部</text>
      </view>

      <view v-for="item in list" :key="item.id" class="room-item">
        <!-- 上：封面 | 状态+房主+时间；中：标题；下：操作。不展示简介/UUID -->
        <view class="item-top" style="display:flex;flex-direction:row;align-items:stretch;">
          <view class="item-image">
            <image
              v-if="coverSrc(item)"
              :src="coverSrc(item)"
              class="cover-image"
              mode="aspectFill"
              @error="onCoverError(item.id)"
            />
            <view v-else class="cover-placeholder">
              <text class="cover-text">无封面</text>
            </view>
          </view>

          <view class="item-side">
            <view :class="['privacy-tag', item.is_private ? 'privacy-private' : 'privacy-public']">
              <text class="privacy-text">{{ item.is_private ? '不公开' : '公开' }}</text>
            </view>

            <view class="owner-block">
              <image
                v-if="ownerAvatar(item)"
                :src="ownerAvatar(item)"
                class="owner-avatar"
                mode="aspectFill"
              />
              <view v-else class="owner-avatar owner-avatar-fallback">
                <text class="owner-avatar-text">{{ ownerInitial(item) }}</text>
              </view>
              <view class="owner-meta">
                <text class="owner-name">{{ ownerName(item) }}</text>
                <text class="owner-dept">{{ ownerDept(item) }}</text>
              </view>
            </view>

            <text class="meta-time">更新于 {{ formatTime(item.updated_at) }}</text>
          </view>
        </view>

        <view class="item-title-row">
          <text class="item-title">{{ item.title || '未命名直播间' }}</text>
        </view>

        <view class="item-actions" style="display:flex;flex-direction:row;">
          <view class="action-btn btn-plain" @tap="openEdit(item)">
            <text class="btn-text">编辑</text>
          </view>
          <view class="action-btn btn-plain" @tap="openTabs(item)">
            <text class="btn-text">Tab</text>
          </view>
          <view class="action-btn btn-plain" @tap="openMessages(item)">
            <text class="btn-text">讨论</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="accessGranted && total > pageSize" class="pagination-wrapper">
      <view class="pagination">
        <view :class="['page-btn', currentPage <= 1 ? 'disabled' : '']" @tap="changePage(currentPage - 1)">
          <text class="page-btn-text">上一页</text>
        </view>
        <view class="page-info">
          <text class="page-text">{{ currentPage }} / {{ totalPages }}</text>
        </view>
        <view
          :class="['page-btn', currentPage >= totalPages ? 'disabled' : '']"
          @tap="changePage(currentPage + 1)"
        >
          <text class="page-btn-text">下一页</text>
        </view>
      </view>
    </view>

    <AdminRoomEditDialog
      v-model:visible="dialogVisible"
      :room-id="editingRoomId"
      @success="fetchData"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { getAdminRooms } from '@/api/room'
import { getAdminExpertList } from '@/api/expert'
import { getAdminUsers } from '@/api/user'
import { resolveCoverUrl, shouldMarkCoverBroken } from '@/utils/url'
import type { AdminRoomListItem } from '@/types/adminRoom'
import AdminRoomEditDialog from './AdminRoomEditDialog.vue'

interface OwnerProfile {
  name: string
  avatar_url?: string
  department?: string
}

const authStore = useAuthStore()

const accessGranted = ref(false)
const accessMessage = ref('正在校验权限...')

const list = ref<AdminRoomListItem[]>([])
const loading = ref(false)
const errorMsg = ref('')
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

/** owner_user_id → 展示用房主资料（专家优先，缺则用户列表补昵称/头像） */
const ownerMap = ref<Record<string, OwnerProfile>>({})

const dialogVisible = ref(false)
const editingRoomId = ref('')

/** 单一搜索：UUID 走房主，其余走标题 q */
const keyword = ref('')
const filters = reactive({
  privacy: 'all' as 'all' | 'public' | 'private'
})

function resolveSearchFields(raw: string): { q?: string; owner_user_id?: string } {
  const value = raw.trim()
  if (!value) return {}
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)) {
    return { owner_user_id: value }
  }
  return { q: value }
}

const privacyOptions = [
  { label: '全部可见性', value: 'all' as const },
  { label: '仅公开', value: 'public' as const },
  { label: '仅不公开', value: 'private' as const }
]

const privacyPickerIndex = computed(() =>
  Math.max(0, privacyOptions.findIndex((o) => o.value === filters.privacy))
)
const currentPrivacyLabel = computed(
  () => privacyOptions[privacyPickerIndex.value]?.label || '全部可见性'
)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const hasActiveFilter = computed(() => {
  return !!keyword.value.trim() || filters.privacy !== 'all'
})

const brokenCoverIds = ref<Record<string, true>>({})

function coverSrc(item: AdminRoomListItem): string {
  const id = String(item.id || '').trim()
  if (id && brokenCoverIds.value[id]) return ''
  return resolveCoverUrl(item.cover_url, id ? !!brokenCoverIds.value[id] : false)
}

function onCoverError(roomId: string) {
  const id = String(roomId || '').trim()
  if (!id) return
  const item = list.value.find((r) => r.id === id)
  if (shouldMarkCoverBroken(item?.cover_url, !!brokenCoverIds.value[id])) {
    brokenCoverIds.value = { ...brokenCoverIds.value, [id]: true }
  }
}

function ownerProfile(item: AdminRoomListItem): OwnerProfile | undefined {
  const id = String(item.owner_user_id || '').trim()
  return id ? ownerMap.value[id] : undefined
}

function ownerName(item: AdminRoomListItem): string {
  return ownerProfile(item)?.name || '未知房主'
}

function ownerDept(item: AdminRoomListItem): string {
  return ownerProfile(item)?.department || '暂无科室'
}

function ownerAvatar(item: AdminRoomListItem): string {
  return String(ownerProfile(item)?.avatar_url || '').trim()
}

function ownerInitial(item: AdminRoomListItem): string {
  const name = ownerName(item)
  if (name && name !== '未知房主') return name.charAt(0)
  return '?'
}

function formatTime(isoStr?: string | null): string {
  if (!isoStr) return '—'
  try {
    const d = new Date(isoStr)
    if (Number.isNaN(d.getTime())) return String(isoStr)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${day} ${hh}:${mm}`
  } catch {
    return String(isoStr)
  }
}

/**
 * 列表仅有 owner_user_id：专家页补名字/头像/科室，其余用用户列表补昵称/头像（最多各扫 5 页）
 */
async function enrichOwners(items: AdminRoomListItem[]) {
  const needIds = new Set(
    items
      .map((item) => String(item.owner_user_id || '').trim())
      .filter((id) => id && !ownerMap.value[id]?.name)
  )
  if (needIds.size === 0) return

  const next: Record<string, OwnerProfile> = { ...ownerMap.value }
  const size = 100
  const maxPages = 5

  try {
    for (let page = 1; page <= maxPages && needIds.size > 0; page += 1) {
      const res = await getAdminExpertList({ page, size })
      const experts = Array.isArray(res?.data?.items)
        ? res.data.items
        : Array.isArray((res as any)?.data)
          ? (res as any).data
          : []
      if (!experts.length) break

      for (const expert of experts) {
        const uid = String(expert?.user_id || '').trim()
        if (!uid || !needIds.has(uid)) continue
        const name = String(expert?.name || '').trim()
        if (!name) continue
        const department = String(expert?.department || '').trim()
        const avatar_url = String(expert?.avatar_url || '').trim()
        next[uid] = {
          name,
          ...(department ? { department } : {}),
          ...(avatar_url ? { avatar_url } : {})
        }
        needIds.delete(uid)
      }
      if (experts.length < size) break
    }
  } catch {
    // 专家补全失败不影响主列表
  }

  try {
    for (let page = 1; page <= maxPages && needIds.size > 0; page += 1) {
      const res = await getAdminUsers({ page, size })
      const users = res.data?.items || []
      if (!users.length) break

      for (const user of users) {
        const pid = String(user.public_id || '').trim()
        if (!pid || !needIds.has(pid)) continue
        const name = String(user.nickname || user.username || '').trim()
        if (!name) continue
        const avatar_url = String(user.avatar_url || '').trim()
        next[pid] = {
          name,
          ...(avatar_url ? { avatar_url } : {})
        }
        needIds.delete(pid)
      }
      if (users.length < size) break
    }
  } catch {
    // 用户补全失败不影响主列表
  }

  ownerMap.value = next
}

function ensureAdminAccess(): boolean {
  if (!authStore.isAuthenticated) {
    accessGranted.value = false
    accessMessage.value = '请先登录后再访问直播间运营'
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({
        url:
          '/pages/auth/OneTapLogin?redirect=' +
          encodeURIComponent('/pages/admin/room/AdminRoomList')
      })
    }, 300)
    return false
  }

  if (!authStore.isAdmin) {
    accessGranted.value = false
    accessMessage.value = '暂无访问权限，请使用管理员账号登录'
    uni.showToast({ title: '暂无访问权限', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 1500)
    return false
  }

  accessGranted.value = true
  accessMessage.value = ''
  return true
}

/**
 * 组装查询参数：空字符串 / null / 未选筛选一律不传，避免被后端当成过滤条件导致空列表
 */
function buildQueryParams() {
  const params: {
    page: number
    size: number
    q?: string
    owner_user_id?: string
    is_private?: boolean
  } = {
    page: currentPage.value,
    size: pageSize.value
  }

  const search = resolveSearchFields(keyword.value)
  if (search.q) params.q = search.q
  if (search.owner_user_id) params.owner_user_id = search.owner_user_id

  if (filters.privacy === 'private') params.is_private = true
  if (filters.privacy === 'public') params.is_private = false

  return params
}

async function fetchData() {
  if (!accessGranted.value) return

  loading.value = true
  errorMsg.value = ''
  try {
    const res = await getAdminRooms(buildQueryParams())
    if (res.code === 200 && res.data) {
      list.value = res.data.items || []
      total.value = res.data.total || 0
      void enrichOwners(list.value)
      return
    }
    if (res.code === 3003) {
      errorMsg.value = '需要管理员权限'
      return
    }
    if (res.code === 3001) {
      errorMsg.value = '请先登录'
      return
    }
    errorMsg.value = res.message || '加载直播间列表失败'
  } catch (err: any) {
    const code = err?.code
    if (code === 3003) {
      errorMsg.value = '需要管理员权限'
    } else if (code === 3001) {
      errorMsg.value = '请先登录'
    } else {
      errorMsg.value = err?.message || '网络异常，请重试'
    }
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  void fetchData()
}

function handleRefresh() {
  if (!ensureAdminAccess()) return
  void fetchData()
}

function handleReset() {
  keyword.value = ''
  filters.privacy = 'all'
  currentPage.value = 1
  void fetchData()
}

function handlePrivacyChange(e: any) {
  filters.privacy = privacyOptions[Number(e.detail.value)]?.value || 'all'
  handleSearch()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  void fetchData()
}

function openEdit(item: AdminRoomListItem) {
  editingRoomId.value = item.id
  dialogVisible.value = true
}

function openTabs(item: AdminRoomListItem) {
  uni.navigateTo({
    url: `/pages/admin/roomTab/RoomTabManagerShell?roomId=${encodeURIComponent(item.id)}`
  })
}

function openMessages(item: AdminRoomListItem) {
  uni.navigateTo({
    url: `/pages/admin/roomMessage/RoomMessageList?roomId=${encodeURIComponent(item.id)}`
  })
}

onLoad((query) => {
  const ownerFromQuery = String(query?.owner_user_id || '').trim()
  if (ownerFromQuery) {
    keyword.value = ownerFromQuery
  }
})

onMounted(() => {
  if (ensureAdminAccess()) {
    void fetchData()
  }
})

onPullDownRefresh(async () => {
  try {
    if (ensureAdminAccess()) await fetchData()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.admin-room-list-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-lg);
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.header-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.header-title {
  flex: 1;
  min-width: 0;
}

.header-title .title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-title .subtitle {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.btn-refresh {
  flex-shrink: 0;
  height: 32px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);

  .btn-text {
    font-size: 13px;
    color: var(--color-primary);
  }
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 0;
  width: 100%;

  .search-input {
    width: 100%;
    height: 36px;
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
    color: var(--color-text-secondary);
  }
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
}

.filter-picker {
  min-width: 120px;
  height: 36px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 13px;
  color: var(--color-text-primary);

  .picker-arrow {
    font-size: 10px;
    color: var(--color-text-tertiary);
  }
}

.btn-query,
.btn-reset {
  height: 36px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  border-radius: var(--border-radius-base);

  .btn-text {
    font-size: 13px;
  }
}

.btn-query {
  background: var(--color-primary);

  .btn-text {
    color: #fff;
  }
}

.btn-reset {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);

  .btn-text {
    color: var(--color-text-secondary);
  }
}

.retry-btn {
  margin-top: var(--spacing-md);
  display: inline-flex;
}

.loading-state,
.empty-state {
  padding: 48px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text,
.empty-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.empty-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.room-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.room-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  padding: 12px;
  border: 1px solid var(--color-border);
}

.item-top {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 12px;
}

.item-image {
  width: 220rpx;
  height: 220rpx;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-bg-secondary);

  .cover-image {
    width: 100%;
    height: 100%;
  }
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;

  .cover-text {
    font-size: 11px;
    color: var(--color-text-tertiary);
  }
}

.item-side {
  flex: 1;
  min-width: 0;
  height: 220rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8rpx;
  padding: 4rpx 0;
  box-sizing: border-box;
}

.privacy-tag {
  align-self: flex-start;
  padding: 2px 8px;
  border-radius: 999px;

  .privacy-text {
    font-size: 11px;
  }
}

.privacy-public {
  background: rgba(82, 196, 26, 0.12);

  .privacy-text {
    color: #52c41a;
  }
}

.privacy-private {
  background: rgba(250, 173, 20, 0.15);

  .privacy-text {
    color: #d48806;
  }
}

.owner-block {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.owner-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
}

.owner-avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;

  .owner-avatar-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

.owner-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.owner-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.owner-dept {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-time {
  font-size: 11px;
  color: var(--color-text-tertiary);
  line-height: 1.3;
}

.item-title-row {
  min-width: 0;
}

.item-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--color-text-primary);
  word-break: break-all;
  line-height: 1.35;
}

.item-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}

.action-btn {
  height: 28px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--color-border);
  box-sizing: border-box;
}

.btn-plain {
  background: transparent;

  .btn-text {
    font-size: 12px;
    color: var(--color-text-secondary);
    white-space: nowrap;
  }
}

.pagination-wrapper {
  margin-top: var(--spacing-lg);
  padding-bottom: var(--spacing-xl);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
}

.page-btn {
  height: 32px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);

  .page-btn-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  &.disabled {
    opacity: 0.4;
  }
}

.page-info .page-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
