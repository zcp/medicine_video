<template>
  <view class="admin-page consumer-layout">
    <view class="top-bar">
      <view class="tab-bar">
        <view
          v-for="(t, idx) in tabs"
          :key="t.key"
          class="tab-item"
          :class="{ 'tab-item--active': activeIndex === idx }"
          @tap="handleTabTap(idx)"
        >
          <text class="tab-label">{{ t.label }}</text>
          <view v-if="activeIndex === idx" class="tab-indicator" />
        </view>
      </view>
      <view class="header-actions">
        <view
          v-if="!isSelectMode"
          class="header-btn"
          @tap="enterSelectMode"
        >
          <text>选择</text>
        </view>
        <view
          v-else
          class="header-btn header-btn--cancel"
          @tap="exitSelectMode"
        >
          <text>取消</text>
        </view>
      </view>
    </view>

    <view class="filter-bar">
      <view class="app-search-field filter-search">
        <text class="filter-icon iconfont icon-search"></text>
        <input
          class="filter-input"
          v-model="searchKeyword"
          placeholder="搜索用户名/昵称/手机号/邮箱"
          placeholder-class="filter-placeholder"
        />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="searchKeyword = ''" />
        </view>
      </view>
      <wd-picker
        v-model="filterRoleIdx"
        :columns="roleCols"
        title="选择角色"
        :z-index="3000"
        @confirm="onRoleChange"
      >
        <view class="filter-tag">{{ selectedRoleLabel }}</view>
      </wd-picker>
      <wd-picker
        v-model="filterStatusIdx"
        :columns="statusCols"
        title="选择状态"
        :z-index="3000"
        @confirm="onStatusChange"
      >
        <view class="filter-tag">{{ selectedStatusLabel }}</view>
      </wd-picker>
    </view>

    <!-- 内容区：Tab 内容切换（点击 Tab 切换，仅激活 Tab 渲染内容避免串扰） -->
    <view
      v-for="(t, idx) in tabs"
      :key="t.key"
      class="admin-panel"
      v-show="activeIndex === idx"
    >
    <scroll-view
      class="list-scroll"
      scroll-y
      @scrolltolower="loadMore"
      :refresher-enabled="true"
      :refresher-triggered="isPullRefreshing"
      @refresherrefresh="onRefresh"
      :lower-threshold="150"
    >
      <view class="list-inner">
        <view v-if="isLoading && users.length === 0">
          <view v-for="i in 4" :key="i" class="skeleton-card">
            <view class="skeleton-avatar" />
            <view class="skeleton-body">
              <view class="skeleton-line skeleton-line--long" />
              <view class="skeleton-line skeleton-line--short" />
            </view>
          </view>
        </view>

        <view v-else-if="error && users.length === 0" class="placeholder-block">
          <text class="placeholder-icon iconfont icon-error"></text>
          <text class="placeholder-title">加载失败</text>
          <text class="placeholder-desc">{{ error }}</text>
          <view class="retry-btn" @tap="loadUsers(true)">点击重试</view>
        </view>

        <view v-else-if="!isLoading && users.length === 0" class="placeholder-block">
          <text class="placeholder-icon iconfont" :class="emptyIcon"></text>
          <text class="placeholder-title">{{ emptyTitle }}</text>
          <text class="placeholder-desc">{{ emptyDesc }}</text>
        </view>

        <template v-else>
          <view
            v-for="item in users"
            :key="item.public_id"
            class="user-card"
          >
            <view
              v-if="isSelectMode && !isAdminRole(item)"
              class="dept-check"
              :class="{ 'dept-check--on': selectedIds.has(item.public_id) }"
              @tap.stop="toggleSelect(item.public_id)"
            >
              <text v-if="selectedIds.has(item.public_id)" class="check-icon">✓</text>
            </view>
            <image
              v-if="hasAvatar(item)"
              class="user-avatar"
              :src="getAvatar(item)"
              mode="aspectFill"
              lazy-load
              @error="onAvatarError(item)"
            />
            <view v-else class="user-avatar user-avatar-placeholder">
              <text class="iconfont icon-my avatar-icon" />
            </view>
            <view class="user-info">
              <view class="user-name-row">
                <text class="user-name">{{ item.username }}</text>
                <text v-if="item.nickname" class="user-nickname">({{ item.nickname }})</text>
              </view>
              <view class="user-badges">
                <view
                  v-if="canChangeRole(item)"
                  class="badge badge--clickable"
                  :class="'badge--role-' + item.role.toLowerCase()"
                  @tap.stop="openRoleSheet(item)"
                >
                  <text>{{ roleLabel(item.role) }}</text>
                  <text class="role-arrow">▼</text>
                </view>
                <view v-else class="badge" :class="'badge--role-' + item.role.toLowerCase()">
                  <text>{{ roleLabel(item.role) }}</text>
                </view>
                <view class="badge" :class="'badge--status-' + item.status.toLowerCase()">
                  <text>{{ statusLabel(item.status) }}</text>
                </view>
                <view class="stream-badge" :class="streamBadgeClass(item)">
                  <text>{{ streamBadgeText(item) }}</text>
                </view>
              </view>
              <view class="user-meta">
                <text v-if="item.email" class="meta-email">{{ item.email }}</text>
                <text class="meta-time">注册于 {{ formatDate(item.created_at) }}</text>
              </view>
              <view v-if="!isSelectMode && !isReadonly(item)" class="user-actions">
                <view
                  v-if="item.status === 'NORMAL'"
                  class="action-btn action-btn--danger"
                  @tap.stop="handleBan(item)"
                >
                  <text>封禁</text>
                </view>
                <view
                  v-if="item.status === 'BANNED'"
                  class="action-btn action-btn--primary"
                  @tap.stop="handleUnban(item)"
                >
                  <text>解封</text>
                </view>
                <view
                  v-if="item.role !== 'ADMIN'"
                  class="action-btn"
                  @tap.stop="handleToggleStream(item)"
                >
                  <text>{{ item.can_stream ? '禁止开播' : '允许开播' }}</text>
                </view>
              </view>
              <view v-if="isReadonly(item)" class="readonly-hint">
                <text>{{ readonlyHint(item) }}</text>
              </view>
            </view>
          </view>

          <view v-if="isLoadingMore" class="loading-more">
            <text>加载中...</text>
          </view>
          <view v-if="!hasMore && users.length > 0" class="no-more">
            <text>没有更多了</text>
          </view>
        </template>
      </view>
    </scroll-view>
    </view>

    <view v-if="isSelectMode" class="select-bar">
      <view class="select-bar-left">
        <view class="select-all-row" @tap="selectAll">
          <view class="select-bar-check" :class="{ 'select-bar-check--on': allSelected }">
            <text v-if="allSelected" class="check-icon">✓</text>
          </view>
          <text>全选</text>
        </view>
        <text class="select-count">已选 {{ selectedIds.size }} 项</text>
      </view>
      <view
        class="batch-btn"
        :class="{ 'batch-btn--disabled': selectedIds.size === 0 }"
        @tap="handleBatchBan"
      >
        <text>批量封禁</text>
      </view>
      <view
        class="batch-btn"
        :class="{ 'batch-btn--disabled': selectedIds.size === 0 }"
        @tap="handleBatchCloseStream"
      >
        <text>禁止开播</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { getAdminUsers, updateAdminUser } from '@/api/adminUsers';
import type { AdminUser } from '@/types/adminUser';
import { resolveMediaUrl } from '@/utils/url';
import { DEFAULT_AVATAR } from '@/constants/assets';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import { useAdminGuard } from '@/composables/useAdminGuard';
import { useAuthStore } from '@/store/auth';
import ClearButton from '@/components/app/ClearButton.vue';
import WdPicker from 'wot-design-uni/components/wd-picker/wd-picker.vue';

const authStore = useAuthStore();

const tabs = [
  { key: 'all', label: '全部用户' },
  { key: 'banned', label: '已封禁' },
  { key: 'nostream', label: '无开播权限' },
];
const activeTab = ref('all');

/**
 * Tab 索引 ↔ 业务联动：设置 activeTab（watch(activeTab) 会自动触发重新加载）
 */
function onTabActivated(idx: number): void {
  const t = tabs[idx];
  if (!t) return;
  if (activeTab.value === t.key) return;
  activeTab.value = t.key;
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动） */
const { activeIndex, handleTabTap } = useSwiperTabs(
  tabs.length,
  onTabActivated,
  0
);

const users = ref<AdminUser[]>([]);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const error = ref<string | null>(null);
const page = ref(1);
const size = 20;
const total = ref(0);
const hasMore = computed(() => page.value * size < total.value);
const loadedOnce = ref(false);
/** 请求进行中到达的刷新请求标记（本轮结束后自动补跑，替代静默丢弃） */
let pendingRefresh = false;

const searchKeyword = ref('');
const selectedRole = ref<string | null>(null);
const selectedStatus = ref<string | null>(null);
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const roleLabels = ['全部角色', 'REGULAR', 'MODERATOR', 'ADMIN', 'SUPERADMIN'];
const roleValues = [null, 'REGULAR', 'MODERATOR', 'ADMIN', 'SUPERADMIN'];
const selectedRoleLabel = computed(() => {
  if (!selectedRole.value) return '全部角色';
  return selectedRole.value;
});
const statusLabels = ['全部状态', 'NORMAL', 'BANNED', 'PENDING_REVIEW'];
const statusValues = [null, 'NORMAL', 'BANNED', 'PENDING_REVIEW'];
const selectedStatusLabel = computed(() => {
  if (!selectedStatus.value) return '全部状态';
  return selectedStatus.value === 'BANNED' ? 'BANNED' : selectedStatus.value;
});
// —— P2 短枚举迁移：wd-picker 列（value=index）+ 受控 index ——
const roleCols = computed(() => roleLabels.map((label, i) => ({ value: i, label })));
const statusCols = computed(() => statusLabels.map((label, i) => ({ value: i, label })));
const filterRoleIdx = ref(0);
const filterStatusIdx = ref(0);

const avatarErrors = ref(new Set<string>());

const roleOptions = [
  { label: '普通用户', value: 'REGULAR' },
  { label: '协管员', value: 'MODERATOR' },
  { label: '管理员', value: 'ADMIN' },
];

/** 角色变更入口（P3.1：居中卡片错位形态 → 原生 showActionSheet，与其余 7 处操作菜单一致） */
function openRoleSheet(item: AdminUser) {
  uni.showActionSheet({
    itemList: roleOptions.map(o => o.label),
    success: async (res) => {
      const opt = roleOptions[res.tapIndex];
      if (!opt) return;
      await handleRoleSelect(opt.value, item);
    },
    fail: () => {},
  });
}

function roleLabel(role: string): string {
  const map: Record<string, string> = { REGULAR: '普通用户', MODERATOR: '协管员', ADMIN: '管理员', SUPERADMIN: '超级管理员' };
  return map[role] || role;
}

function getAvatar(item: AdminUser): string {
  if (avatarErrors.value.has(item.public_id)) return DEFAULT_AVATAR;
  if (item.avatar_url) return resolveMediaUrl(item.avatar_url);
  return DEFAULT_AVATAR;
}

function onAvatarError(item: AdminUser) {
  avatarErrors.value = new Set([...avatarErrors.value, item.public_id]);
}

function statusLabel(status: string): string {
  const map: Record<string, string> = { NORMAL: '正常', BANNED: '已封禁', DELETED: '已注销', PENDING_REVIEW: '待审核', REJECTED: '已拒绝' };
  return map[status] || status;
}

function formatDate(iso: string): string {
  if (!iso) return '';
  try { return iso.slice(0, 10); } catch { return ''; }
}

function canChangeRole(item: AdminUser): boolean {
  // 改角色仅超级管理员（后端已收紧为 SUPERADMIN，前端对齐隐藏入口）
  return authStore.isSuperAdmin && (item.role === 'REGULAR' || item.role === 'MODERATOR');
}

function hasAvatar(item: AdminUser): boolean {
  return !!(item.avatar_url && !avatarErrors.value.has(item.public_id));
}

function streamBadgeClass(item: AdminUser): string {
  if (item.role === 'ADMIN' || item.role === 'SUPERADMIN') return 'stream-badge--on';
  return item.can_stream ? 'stream-badge--on' : 'stream-badge--off';
}

function streamBadgeText(item: AdminUser): string {
  if (item.role === 'ADMIN' || item.role === 'SUPERADMIN') return '开通';
  return item.can_stream ? '开通' : '未开通';
}

function isAdminRole(item: AdminUser): boolean {
  return item.role === 'ADMIN' || item.role === 'SUPERADMIN';
}

function isReadonly(item: AdminUser): boolean {
  return item.role === 'SUPERADMIN' || item.status === 'DELETED';
}

function readonlyHint(item: AdminUser): string {
  if (item.role === 'SUPERADMIN') return '超级管理员，不可操作';
  if (item.status === 'DELETED') return '账号已注销';
  return '';
}

const isSelectMode = ref(false);
const selectedIds = ref(new Set<string>());
const allSelected = computed(() =>
  users.value.length > 0 && users.value.every(u => selectedIds.value.has(u.public_id))
);

const emptyIcon = computed(() => {
  if (activeTab.value === 'banned') return 'icon-privacy';
  if (activeTab.value === 'nostream') return 'icon-video';
  return 'icon-my';
});
const emptyTitle = computed(() => {
  if (activeTab.value === 'banned') return '没有已封禁用户';
  if (activeTab.value === 'nostream') return '所有用户均有开播权限';
  return '暂无用户';
});
const emptyDesc = computed(() => {
  if (activeTab.value === 'banned') return '当前没有用户处于封禁状态';
  if (activeTab.value === 'nostream') return '当前没有用户被限制开播';
  return '暂无用户数据';
});

async function loadUsers(refresh = false) {
  // 请求进行中到达的刷新请求：标记补跑，本轮结束后自动执行（不再静默丢弃）
  if (isLoading.value || isLoadingMore.value) {
    if (refresh) pendingRefresh = true;
    return;
  }
  if (refresh) {
    isLoading.value = true;
  } else {
    isLoadingMore.value = true;
  }
  error.value = null;

  if (refresh) {
    page.value = 1;
    // 下拉/补跑刷新不清空旧列表（stale-while-revalidate）：
    // 避免内容高度骤降导致原生 refresher 动画错乱（下拉卡死）；骨架仅首载（列表为空）时显示
  }

  const requestPage = refresh ? 1 : page.value + 1;

  try {
    const params: Record<string, any> = { page: requestPage, size };
    if (activeTab.value === 'banned') { params.status = 'BANNED'; }
    // 传字符串 'false'：避免 App 端 uni.request 对 GET 布尔 false 序列化丢失，导致未带筛选、Tab 串入可开播用户
    if (activeTab.value === 'nostream') { params.can_stream = 'false'; }
    if (searchKeyword.value.trim()) { params.keyword = searchKeyword.value.trim(); }
    if (selectedRole.value) { params.role = selectedRole.value; }
    if (selectedStatus.value) { params.status = selectedStatus.value; }

    const res = await getAdminUsers(params);
    if (res.code === 200 || res.code === 0) {
      const rawItems = res.data.items || [];
      let items = rawItems;
      if (activeTab.value === 'nostream') {
        // 服务端 can_stream=false 为主；客户端再兜底：仅保留确被禁播的非管理员，防止参数丢失/漏筛时展示「开通」用户
        items = rawItems.filter(
          (u: AdminUser) =>
            u.can_stream === false &&
            u.role !== 'ADMIN' &&
            u.role !== 'SUPERADMIN'
        );
      }
      if (refresh) {
        users.value = items;
        // 本页被兜底滤掉条目时，服务端 total 与展示口径不一致，按可见数截断，避免 hasMore 虚高连环触底
        if (activeTab.value === 'nostream' && items.length < rawItems.length) {
          total.value = items.length;
        } else {
          total.value = res.data.total;
        }
      } else {
        const existingIds = new Set(users.value.map(u => u.public_id));
        const newItems = items.filter((u: any) => !existingIds.has(u.public_id));
        users.value = [...users.value, ...newItems];
        if (newItems.length < items.length || (activeTab.value === 'nostream' && items.length < rawItems.length)) {
          total.value = users.value.length;
        } else {
          total.value = res.data.total ?? total.value;
        }
      }
      page.value = requestPage;
    }
  } catch (e: any) {
    error.value = e?.message || '加载失败，下拉重试';
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
    loadedOnce.value = true;
    // 加载期间到达的刷新请求：补跑一次（合并连续触发）
    if (pendingRefresh) {
      pendingRefresh = false;
      await loadUsers(true);
    }
  }
}

async function loadMore() {
  if (isLoadingMore.value || !hasMore.value || isLoading.value) return;
  await loadUsers(false);
}

/** 下拉刷新最小展示时长（ms）：请求过快时保证指示器可感知 */
const PULL_REFRESH_MIN_MS = 400;
const isPullRefreshing = ref(false);
let pullRefreshStartTime = 0;

async function onRefresh() {
  if (isPullRefreshing.value) return;
  isPullRefreshing.value = true;
  pullRefreshStartTime = Date.now();
  try {
    await loadUsers(true);
  } finally {
    const elapsed = Date.now() - pullRefreshStartTime;
    if (elapsed < PULL_REFRESH_MIN_MS) {
      await new Promise(resolve => setTimeout(resolve, PULL_REFRESH_MIN_MS - elapsed));
    }
    isPullRefreshing.value = false;
  }
}

function onRoleChange(e: any) { selectedRole.value = roleValues[e?.value ?? e?.detail?.value]; loadUsers(true); }
function onStatusChange(e: any) { selectedStatus.value = statusValues[e?.value ?? e?.detail?.value]; loadUsers(true); }

watch(searchKeyword, () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadUsers(true), 300);
});
watch(activeTab, () => loadUsers(true));
onShow(() => {
  if (!useAdminGuard()) return;
  if (!loadedOnce.value) loadUsers(true);
});
onUnmounted(() => { if (searchTimer) clearTimeout(searchTimer); });

async function handleBan(item: AdminUser) {
  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({ title: '确认封禁', content: `确定要封禁用户「${item.username}」吗？封禁后该用户的登录会话将立即失效。`, confirmColor: '#dc2626', success: r => resolve(r) });
  });
  if (!confirm) return;
  try {
    await updateAdminUser(item.public_id, { status: 'BANNED' });
    uni.showToast({ title: '已封禁', icon: 'success' });
    item.status = 'BANNED';
  } catch (e: any) {
    const msg = e?.message || '';
    uni.showToast({ title: msg === 'Forbidden' ? '不能修改更高权限用户' : (msg || '操作失败'), icon: 'none' });
  }
}

async function handleUnban(item: AdminUser) {
  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({ title: '确认解封', content: `确定要解除对「${item.username}」的封禁吗？`, confirmColor: '#0F766E', success: r => resolve(r) });
  });
  if (!confirm) return;
  try {
    await updateAdminUser(item.public_id, { status: 'NORMAL' });
    uni.showToast({ title: '已解封', icon: 'success' });
    item.status = 'NORMAL';
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  }
}

async function handleToggleStream(item: AdminUser) {
  const newVal = !item.can_stream;
  const action = newVal ? '允许' : '关闭';
  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({ title: `确认${action}开播`, content: `确定要${action}用户「${item.username}」的开播权限吗？`, confirmColor: '#0F766E', success: r => resolve(r) });
  });
  if (!confirm) return;
  try {
    await updateAdminUser(item.public_id, { can_stream: newVal });
    uni.showToast({ title: `已${action}开播`, icon: 'success' });
    item.can_stream = newVal;
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  }
}

async function handleRoleSelect(newRole: string, target: AdminUser) {
  if (!target || newRole === target.role) return;
  try {
    await updateAdminUser(target.public_id, { role: newRole });
    uni.showToast({ title: '角色已更新', icon: 'success' });
    target.role = newRole as AdminUser['role'];
  } catch (e: any) {
    const msg = e?.message || '';
    uni.showToast({ title: msg === 'Forbidden' ? '不能修改更高权限用户' : (msg || '操作失败'), icon: 'none' });
  }
}

function enterSelectMode() { isSelectMode.value = true; selectedIds.value = new Set(); }
function exitSelectMode() { isSelectMode.value = false; selectedIds.value = new Set(); }
function toggleSelect(id: string) { const next = new Set(selectedIds.value); if (next.has(id)) { next.delete(id); } else { next.add(id); } selectedIds.value = next; }
function selectAll() { selectedIds.value = allSelected.value ? new Set() : new Set(users.value.map(u => u.public_id)); }

async function handleBatchBan() {
  if (selectedIds.value.size === 0) return;
  const ids = [...selectedIds.value]; let success = 0;
  for (const id of ids) { try { await updateAdminUser(id, { status: 'BANNED' }); success++; } catch { /* skip */ } }
  uni.showToast({ title: `已封禁 ${success}/${ids.length} 个用户`, icon: 'success' });
  exitSelectMode(); loadUsers(true);
}

async function handleBatchCloseStream() {
  if (selectedIds.value.size === 0) return;
  const ids = [...selectedIds.value]; let success = 0;
  for (const id of ids) { try { await updateAdminUser(id, { can_stream: false }); success++; } catch { /* skip */ } }
  uni.showToast({ title: `已关闭 ${success}/${ids.length} 个用户的开播权限`, icon: 'success' });
  exitSelectMode(); loadUsers(true);
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.admin-page.consumer-layout {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: var(--home-bg);
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24rpx;
  background: var(--home-card);
  border-bottom: 1rpx solid var(--home-divider);
}

.tab-bar { display: flex; gap: 0; }

.tab-item {
  position: relative;
  padding: 20rpx 8rpx;
  margin-right: 40rpx;
  flex-shrink: 0;
  transition: $motion-fast;
}
.tab-label { font-size: $font-md; color: var(--home-text2); transition: $motion-fast; }
.tab-item--active .tab-label { color: var(--home-primary); font-weight: 600; }
.tab-indicator {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 28rpx;
  height: 4rpx;
  background-color: var(--home-primary);
  border-radius: 2rpx;
  transition: $motion-normal;
}

.header-actions { display: flex; align-items: center; gap: 16rpx; }
.header-btn {
  min-height: 64rpx;
  display: flex;
  align-items: center;
  padding: 8rpx 24rpx;
  background: var(--home-primary);
  border-radius: $radius-full;
  font-size: $font-xs;
  color: $color-text-white;
  box-shadow: $shadow-button-primary;
  transition: $motion-fast;
}
.header-btn:active { opacity: 0.85; transform: scale(0.97); }
.header-btn--cancel {
  color: var(--home-text2);
  background: var(--home-action-secondary-bg);
  box-shadow: none;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 24rpx;
  background: var(--home-card);
  border-bottom: 1rpx solid var(--home-divider);
}
.filter-search {
  /* 叠加共享容器 .app-search-field：白底+1rpx细边+胶囊；高度 64rpx（管理端档，D6，原 68 统一） */
  height: 64rpx;
  box-sizing: border-box;
  /* 聚焦态：默认态即最终态，无灰→白切换、无光晕（原 :focus-within 光晕已删） */
}
.filter-icon {
  font-size: 26rpx;
  margin-right: 12rpx;
  color: var(--search-icon);
  flex-shrink: 0;
  line-height: 1;
}
.filter-input {
  flex: 1;
  height: 100%;
  font-size: 26rpx;
  color: var(--home-text1);
  background: transparent;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}
.filter-placeholder {
  color: var(--search-placeholder);
}
.filter-tag {
  height: 68rpx;
  line-height: 68rpx;
  padding: 0 24rpx;
  background: var(--home-input-bg);
  border-radius: $radius-full;
  font-size: $font-sm;
  color: var(--home-text1);
  white-space: nowrap;
}

/* 内容区 Tab 面板：flex 撑满剩余高度（根容器 100vh + flex column） */
.admin-panel { flex: 1; min-height: 0; overflow: hidden; }

.list-scroll { height: 100%; overflow-y: auto; overflow-x: hidden; -webkit-overflow-scrolling: touch; }
.list-inner { padding: 16rpx 24rpx; }

.user-card {
  display: flex;
  align-items: flex-start;
  padding: 24rpx;
  margin-bottom: 16rpx;
  background: var(--home-card);
  border-radius: $radius-lg;
  box-shadow: var(--home-shadow-card);
}
.user-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-circle);
  background: var(--home-input-bg);
  flex-shrink: 0;
  margin-right: 16rpx;
}
.user-avatar-placeholder {
  background: var(--home-input-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-icon { font-size: 36rpx; color: var(--home-text2); }
.user-info { flex: 1; min-width: 0; }
.user-name-row { display: flex; align-items: center; gap: 8rpx; margin-bottom: 6rpx; }
.user-name { font-size: $font-lg; font-weight: 600; color: var(--home-text1); }
.user-nickname { font-size: $font-sm; color: var(--home-text2); }

.user-badges { display: flex; align-items: center; gap: 8rpx; margin-bottom: 6rpx; flex-wrap: wrap; }
.badge {
  padding: 2rpx 12rpx;
  border-radius: $radius-full;
  font-size: 20rpx;
  line-height: 1.5;
  flex-shrink: 0;
}
.badge--clickable { display: flex; align-items: center; gap: 4rpx; }

.badge--role-regular { background: var(--home-badge-muted-bg); color: var(--home-badge-muted-text); }
.badge--role-moderator { background: var(--home-badge-info-bg); color: var(--home-badge-info-text); }
.badge--role-admin { background: var(--home-badge-verified-bg); color: var(--home-badge-verified-text); }
.badge--role-superadmin { background: var(--home-badge-pending-bg); color: var(--home-badge-pending-text); }
.badge--status-normal { background: var(--home-badge-verified-bg); color: var(--home-badge-verified-text); }
.badge--status-banned { background: var(--home-badge-danger-bg); color: var(--home-badge-danger-text); }
.badge--status-deleted { background: var(--home-badge-muted-bg); color: var(--home-badge-muted-text); }
.badge--status-pending_review { background: var(--home-badge-pending-bg); color: var(--home-badge-pending-text); }
.badge--status-rejected { background: var(--home-badge-danger-bg); color: var(--home-badge-danger-text); }

.stream-badge {
  padding: 2rpx 10rpx;
  border-radius: $radius-full;
  font-size: 20rpx;
  line-height: 1.5;
  flex-shrink: 0;
}
.stream-badge--on { background: var(--home-badge-verified-bg); color: var(--home-badge-verified-text); }
.stream-badge--off { background: var(--home-badge-muted-bg); color: var(--home-badge-muted-text); }
.role-arrow { font-size: 16rpx; margin-left: 4rpx; opacity: 0.5; }

.user-meta { display: flex; align-items: center; gap: 16rpx; margin-bottom: 10rpx; }
.meta-email {
  font-size: $font-xs;
  color: var(--home-text2);
  max-width: 300rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta-time { font-size: $font-xs; color: var(--home-text2); }
.user-actions {
  display: flex;
  gap: 12rpx;
  padding-top: 12rpx;
  border-top: 1rpx solid var(--home-divider);
}
.readonly-hint {
  padding-top: 10rpx;
  font-size: $font-xs;
  color: var(--home-text2);
  font-style: italic;
}

.action-btn {
  min-height: 64rpx;
  display: flex;
  align-items: center;
  padding: 8rpx 24rpx;
  border-radius: $radius-full;
  font-size: $font-xs;
  color: var(--home-text1);
  background: var(--home-action-secondary-bg);
  transition: $motion-fast;
}
.action-btn:active { opacity: 0.85; transform: scale(0.97); }
.action-btn--primary { color: var(--home-action-primary-text); background: var(--home-action-primary-bg); }
.action-btn--danger { color: var(--home-action-danger-text); background: var(--home-action-danger-bg); }

.placeholder-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  text-align: center;
}
.placeholder-icon { font-size: 72rpx; margin-bottom: 24rpx; opacity: 0.6; color: var(--home-text2); }
.placeholder-title { font-size: $font-lg; font-weight: 600; color: var(--home-text1); margin-bottom: 12rpx; }
.placeholder-desc { font-size: $font-sm; color: var(--home-text2); }
.retry-btn {
  margin-top: 24rpx;
  padding: 16rpx 48rpx;
  background: var(--home-primary);
  color: $color-text-white;
  border-radius: $radius-full;
  font-size: $font-md;
  box-shadow: $shadow-button-primary;
  transition: $motion-fast;
}
.retry-btn:active { opacity: 0.85; transform: scale(0.97); }

.skeleton-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  margin-bottom: 16rpx;
  background: var(--home-card);
  border-radius: $radius-lg;
  box-shadow: var(--home-shadow-card);
}
.skeleton-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-circle);
  background: var(--home-divider);
  flex-shrink: 0;
  margin-right: 16rpx;
}
.skeleton-body { flex: 1; }
.skeleton-line {
  height: 20rpx;
  background: var(--home-divider);
  border-radius: 4rpx;
  margin-bottom: 12rpx;
}
.skeleton-line--long { width: 50%; }
.skeleton-line--short { width: 35%; margin-bottom: 0; }

.loading-more,
.no-more {
  text-align: center;
  padding: 24rpx 0;
  font-size: $font-sm;
  color: var(--home-text2);
}

.dept-check {
  width: 44rpx;
  height: 44rpx;
  border-radius: var(--radius-circle);
  border: 3rpx solid rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  margin-top: 16rpx;
  flex-shrink: 0;
  transition: $motion-fast;
}
.dept-check--on { background: var(--home-primary); border-color: var(--home-primary); }
.check-icon { font-size: 24rpx; color: $color-text-white; font-weight: 700; }

.select-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background: var(--home-card);
  border-top: 1rpx solid var(--home-divider);
  box-shadow: $shadow-sm;
  z-index: 100;
}
.select-bar-left { display: flex; align-items: center; gap: 20rpx; }
.select-all-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-height: $touch-target-min;
  font-size: $font-sm;
  color: var(--home-text1);
}
.select-bar-check {
  width: 44rpx;
  height: 44rpx;
  border-radius: var(--radius-circle);
  border: 3rpx solid rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $motion-fast;
}
.select-bar-check--on { background: var(--home-primary); border-color: var(--home-primary); }
.select-count { font-size: $font-sm; color: var(--home-text2); }
.batch-btn {
  min-height: 76rpx;
  display: flex;
  align-items: center;
  padding: 12rpx 36rpx;
  background: var(--home-action-danger-bg);
  color: var(--home-action-danger-text);
  border-radius: $radius-full;
  font-size: $font-sm;
  transition: $motion-fast;
}
.batch-btn + .batch-btn {
  background: var(--home-action-secondary-bg);
  color: var(--home-text1);
}
.batch-btn:active:not(.batch-btn--disabled) { opacity: 0.85; transform: scale(0.97); }
.batch-btn--disabled { opacity: 0.45; }
</style>
