<!--
 * UserList - 管理端用户管理列表页
 * 风格对齐 TagList / CategoryList / ContentSafetyRuleList
 -->
<template>
  <view class="user-list-page">
    <view class="page-header">
      <view class="header-title-row">
        <view class="header-title">
          <text class="title">用户管理</text>
          <text class="subtitle">禁止/恢复开播、禁用账号、调整后台身份</text>
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
            placeholder="搜索昵称/用户名/手机/邮箱"
            @confirm="handleSearch"
          />
          <view v-if="keyword" class="search-clear" @tap="keyword = ''; handleSearch()">✕</view>
        </view>
      </view>

      <view class="filter-row">
        <picker :range="roleOptions" range-key="label" :value="rolePickerIndex" @change="handleRoleChange">
          <view class="filter-picker">
            <text>{{ currentRoleLabel }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <picker :range="statusOptions" range-key="label" :value="statusPickerIndex" @change="handleStatusChange">
          <view class="filter-picker">
            <text>{{ currentStatusLabel }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <picker :range="streamOptions" range-key="label" :value="streamPickerIndex" @change="handleStreamChange">
          <view class="filter-picker">
            <text>{{ currentStreamLabel }}</text>
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

    <view v-else class="user-list">
      <view v-if="users.length === 0" class="empty-state">
        <text class="empty-text">暂无用户数据</text>
      </view>

      <view v-for="user in users" :key="user.public_id" class="user-item">
        <!-- 第 1 排：头像 + 名字 + 编辑 -->
        <view class="item-top">
          <view class="item-image">
            <image
              v-if="!avatarShowIcon(user.public_id)"
              :src="avatarSrc(user.avatar_url, user.public_id)"
              class="cover-image"
              mode="aspectFill"
              @error="onAvatarError(user.public_id, user.avatar_url)"
            />
            <view v-else class="avatar-placeholder">
              <text class="avatar-text">{{ (user.nickname || user.username).charAt(0) }}</text>
            </view>
          </view>
          <text class="item-name">{{ user.nickname || user.username }}</text>
          <view
            v-if="canEditUser(user)"
            class="action-btn btn-plain"
            @tap="openEditDialog(user)"
          >
            <text class="btn-text">编辑</text>
          </view>
          <view v-else class="action-btn btn-disabled">
            <text class="btn-text">不可编辑</text>
          </view>
        </view>

        <!-- 第 2 排：状态标签 -->
        <view class="item-status-row">
          <view :class="['role-tag', `role-${user.role.toLowerCase()}`]">
            <text class="role-text">{{ getAdminUserRoleLabel(user.role) }}</text>
          </view>
          <view :class="['status-tag', `status-${user.status.toLowerCase()}`]">
            <text class="status-text">{{ getAdminUserStatusLabel(user.status) }}</text>
          </view>
          <view :class="['stream-tag', user.can_stream ? 'stream-on' : 'stream-off']">
            <text class="stream-text">{{ user.can_stream ? '可开播' : '已禁止开播' }}</text>
          </view>
        </view>

        <!-- 其他信息：双列铺开，减少左右空白 -->
        <view class="item-meta-grid">
          <text class="meta-text meta-full">UID：{{ user.public_id }}</text>
          <text class="meta-text">{{ user.email || '未设置邮箱' }}</text>
          <text class="meta-text">{{ user.phone_number ? `手机：${user.phone_number}` : '未设置手机' }}</text>
          <text class="meta-text">账号：{{ user.username }}</text>
          <text class="meta-text">注册：{{ formatTime(user.created_at) }}</text>
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
        <view :class="['page-btn', currentPage >= totalPages ? 'disabled' : '']" @tap="changePage(currentPage + 1)">
          <text class="page-btn-text">下一页</text>
        </view>
      </view>
    </view>

    <UserEditDialog
      v-model:visible="dialogVisible"
      :user="currentUser"
      :operator-role="operatorRole"
      @success="fetchData"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { getAdminUsers } from '@/api/user'
import { useAuthStore } from '@/store/auth'
import { resolveAvatarUrl, shouldMarkAvatarBroken } from '@/utils/url'
import type { AdminUserResponse, AdminUserRole, AdminEntityStatus } from '@/types/adminUser'
import {
  ADMIN_USER_ROLE_LABEL,
  ADMIN_USER_STATUS_LABEL,
  canEditAdminUser,
  getAdminUserRoleLabel,
  getAdminUserStatusLabel,
  getDailyRoleFilterOptions,
  getDailyStatusOptions,
  normalizeAdminUserResponse
} from '@/types/adminUser'
import UserEditDialog from './UserEditDialog.vue'

const authStore = useAuthStore()
const operatorRole = computed(() => authStore.userInfo?.role)
const operatorPublicId = computed(
  () => authStore.userInfo?.public_id || authStore.userInfo?.user_id || ''
)

const accessGranted = ref(false)
const accessMessage = ref('正在校验权限...')

const users = ref<AdminUserResponse[]>([])
const loading = ref(false)
const errorMsg = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const dialogVisible = ref(false)
const currentUser = ref<AdminUserResponse | null>(null)

/** 单一搜索框：按输入形态映射到后端单一筛选字段 */
const keyword = ref('')
const filters = reactive({
  role: '' as AdminUserRole | '',
  status: '' as AdminEntityStatus | '',
  can_stream: '' as '' | 'true' | 'false'
})

function applyKeywordToParams(params: Record<string, unknown>, raw: string) {
  const q = raw.trim()
  if (!q) return
  if (/^1\d{10}$/.test(q)) {
    params.phone_number = q
    return
  }
  if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(q)) {
    params.email = q
    return
  }
  if (/^[a-zA-Z0-9_]{3,}$/.test(q)) {
    params.username = q
    return
  }
  params.nickname = q
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const roleOptions = computed(() => [
  { label: '全部身份', value: '' as const },
  ...getDailyRoleFilterOptions(operatorRole.value).map((value) => ({
    label: ADMIN_USER_ROLE_LABEL[value],
    value
  }))
])

const statusOptions = [
  { label: '全部状态', value: '' as const },
  ...getDailyStatusOptions().map((value) => ({
    label: ADMIN_USER_STATUS_LABEL[value],
    value
  }))
]

const streamOptions = [
  { label: '全部开播状态', value: '' as const },
  { label: '可开播', value: 'true' as const },
  { label: '已禁止开播', value: 'false' as const }
]

const rolePickerIndex = computed(() => Math.max(0, roleOptions.value.findIndex((o) => o.value === filters.role)))
const statusPickerIndex = computed(() => Math.max(0, statusOptions.findIndex((o) => o.value === filters.status)))
const streamPickerIndex = computed(() =>
  Math.max(0, streamOptions.findIndex((o) => o.value === filters.can_stream))
)
const currentRoleLabel = computed(() => roleOptions.value[rolePickerIndex.value]?.label || '全部身份')
const currentStatusLabel = computed(() => statusOptions[statusPickerIndex.value]?.label || '全部状态')
const currentStreamLabel = computed(() => streamOptions[streamPickerIndex.value]?.label || '全部开播状态')

const brokenAvatarIds = ref<Record<string, true>>({})
const avatarIconIds = ref<Record<string, true>>({})

function avatarSrc(raw?: string | null, userId?: string): string {
  const id = String(userId || '').trim()
  return resolveAvatarUrl(raw, id ? !!brokenAvatarIds.value[id] : false)
}

function avatarShowIcon(userId: string): boolean {
  return !!avatarIconIds.value[String(userId || '').trim()]
}

function onAvatarError(userId: string, raw?: string | null) {
  const id = String(userId || '').trim()
  if (!id) return
  if (avatarIconIds.value[id]) return
  if (brokenAvatarIds.value[id] || !shouldMarkAvatarBroken(raw, !!brokenAvatarIds.value[id])) {
    avatarIconIds.value = { ...avatarIconIds.value, [id]: true }
    return
  }
  brokenAvatarIds.value = { ...brokenAvatarIds.value, [id]: true }
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return isoStr
  }
}

function canEditUser(user: AdminUserResponse): boolean {
  return canEditAdminUser(user.role, operatorRole.value, {
    targetPublicId: user.public_id,
    operatorPublicId: operatorPublicId.value
  })
}

function ensureAdminAccess(): boolean {
  if (!authStore.isAuthenticated) {
    accessGranted.value = false
    accessMessage.value = '请先登录后再访问用户管理'
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/auth/OneTapLogin?redirect=' + encodeURIComponent('/pages/admin/user/UserList')
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

async function fetchData() {
  if (!accessGranted.value) return

  loading.value = true
  errorMsg.value = null
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      size: pageSize.value
    }
    applyKeywordToParams(params, keyword.value)
    if (filters.role) params.role = filters.role
    if (filters.status) params.status = filters.status
    if (filters.can_stream === 'true') params.can_stream = true
    if (filters.can_stream === 'false') params.can_stream = false

    const res = await getAdminUsers(params)
    if (res.code === 200 && res.data) {
      users.value = (res.data.items || []).map(normalizeAdminUserResponse)
      total.value = res.data.total
    } else {
      errorMsg.value = res.message || '加载用户列表失败'
    }
  } catch (err: any) {
    errorMsg.value = err.message || '加载用户列表失败'
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
  filters.role = ''
  filters.status = ''
  filters.can_stream = ''
  currentPage.value = 1
  void fetchData()
}

function handleRoleChange(e: any) {
  filters.role = roleOptions.value[Number(e.detail.value)]?.value || ''
  handleSearch()
}

function handleStatusChange(e: any) {
  filters.status = statusOptions[Number(e.detail.value)]?.value || ''
  handleSearch()
}

function handleStreamChange(e: any) {
  filters.can_stream = streamOptions[Number(e.detail.value)]?.value || ''
  handleSearch()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  void fetchData()
}

function openEditDialog(user: AdminUserResponse) {
  if (!canEditUser(user)) {
    uni.showToast({ title: '权限不足，无法编辑该用户', icon: 'none' })
    return
  }
  currentUser.value = user
  dialogVisible.value = true
}

onMounted(() => {
  if (ensureAdminAccess()) {
    void fetchData()
  }
})

onPullDownRefresh(async () => {
  try {
    if (ensureAdminAccess()) {
      await fetchData()
    }
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.user-list-page {
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 120px;
  height: 36px;
  padding: 0 12px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  color: var(--color-text-primary);
  box-sizing: border-box;
}

.picker-arrow {
  font-size: 10px;
  color: var(--color-text-secondary);
}

.btn-query,
.btn-reset {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 16px;
  border-radius: var(--border-radius-base);
}

.btn-query {
  background-color: var(--color-primary);

  .btn-text {
    font-size: 14px;
    color: #fff;
  }
}

.btn-reset {
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);

  .btn-text {
    font-size: 14px;
    color: var(--color-text-primary);
  }
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.user-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.item-top {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.item-image {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background-color: var(--color-bg-secondary);

  .cover-image {
    width: 100%;
    height: 100%;
  }
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
}

.avatar-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.item-name {
  flex: 1;
  min-width: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-status-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.item-meta-grid {
  display: flex;
  flex-wrap: wrap;
  column-gap: 12px;
  row-gap: 4px;
}

.meta-text {
  flex: 1 1 calc(50% - 6px);
  min-width: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

.meta-full {
  flex: 1 1 100%;
}

.role-tag,
.status-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.role-regular {
  background-color: #e6f7ff;
  .role-text { color: #1890ff; font-size: 11px; }
}

.role-moderator {
  background-color: #f9f0ff;
  .role-text { color: #722ed1; font-size: 11px; }
}

.role-admin {
  background-color: #fff7e6;
  .role-text { color: #fa8c16; font-size: 11px; }
}

.role-superadmin {
  background-color: #fff1f0;
  .role-text { color: #f5222d; font-size: 11px; }
}

.status-normal {
  background-color: #f6ffed;
  .status-text { color: #52c41a; font-size: 11px; }
}

.status-banned {
  background-color: #fff2f0;
  .status-text { color: #ff4d4f; font-size: 11px; }
}

.status-deleted,
.status-rejected {
  background-color: #f5f5f5;
  .status-text { color: #8c8c8c; font-size: 11px; }
}

.status-pending_review {
  background-color: #fff7e6;
  .status-text { color: #fa8c16; font-size: 11px; }
}

.stream-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
}

.stream-on {
  background-color: #f6ffed;
  .stream-text { color: #389e0d; font-size: 11px; }
}

.stream-off {
  background-color: #fafafa;
  .stream-text { color: #8c8c8c; font-size: 11px; }
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 10px;
  border-radius: var(--border-radius-sm);
  box-sizing: border-box;
  flex-shrink: 0;

  .btn-text {
    font-size: 12px;
    white-space: nowrap;
  }

  &.btn-plain {
    background-color: transparent;
    border: 1px solid var(--color-border);
    .btn-text { color: var(--color-text-secondary); }
  }

  &.btn-disabled {
    background-color: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    .btn-text { color: var(--color-text-secondary); }
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
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
}

.empty-text,
.loading-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.retry-btn {
  margin-top: var(--spacing-sm);
}

.pagination-wrapper {
  margin-top: var(--spacing-lg);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 14px;
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);

  &.disabled {
    opacity: 0.5;
  }
}

.page-btn-text,
.page-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
