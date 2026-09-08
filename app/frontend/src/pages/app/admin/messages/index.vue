<template>
  <view class="admin-page consumer-layout">
    <!-- 时间 Tab + 选择入口 -->
    <view class="tab-bar">
      <view class="tab-group">
        <view
          v-for="(t, idx) in timeTabs"
          :key="t.key"
          class="tab-item"
          :class="{ 'tab-item--active': timeIndex === idx }"
          @tap="onTimeChange(idx)"
        >
          <text class="tab-label">{{ t.label }}</text>
        </view>
      </view>
      <view class="tab-bar__actions">
        <view v-if="!isSelectMode" class="select-entry-btn" @tap="isSelectMode = true">
          <text class="select-entry-btn__text">选择</text>
        </view>
        <view v-else class="select-entry-btn select-entry-btn--cancel" @tap="isSelectMode = false; selectedIds = new Set()">
          <text class="select-entry-btn__text">取消</text>
        </view>
      </view>
    </view>

    <!-- 搜索栏 + 按房间筛选入口（与搜索框同行） -->
    <view class="filter-bar">
      <view class="app-search-field filter-search">
        <text class="filter-icon iconfont icon-search"></text>
        <input
          class="filter-input"
          v-model="searchKeyword"
          placeholder="搜索留言内容"
          placeholder-class="filter-placeholder"
          confirm-type="search"
          @confirm="handleSearch"
        />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="clearSearch" />
        </view>
      </view>
      <!-- 按房间筛选（房间未预填时可用）：未筛选时展示入口文案；已筛选时展示房间胶囊（点胶囊可换房，点 ✕ 清除） -->
      <view v-if="!roomId" class="room-entry-btn" @tap="openRoomFilter">
        <text v-if="!filteredRoomId" class="room-entry-btn__text">按房间筛选</text>
        <template v-else>
          <text class="room-entry-btn__text room-entry-btn__text--active">{{ roomFilterLabel }}</text>
          <text class="room-entry-btn__clear" @tap.stop="clearRoomFilter">✕</text>
        </template>
      </view>
    </view>

    <!-- roomId 预填：房间筛选标签 + 清空 -->
    <view v-if="roomId" class="room-filter-bar">
      <text class="room-filter-tag">当前房间: {{ roomIdShort }}</text>
      <view class="room-clear-btn" @tap="handleClearRoom">
        <text class="room-clear-btn__text">清空该房间留言</text>
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view class="content-scroll" scroll-y @scrolltolower="loadMore" :lower-threshold="150">
      <view v-if="isLoading && messages.length === 0" class="state-box">
        <view v-for="i in 4" :key="i" class="skeleton-card">
          <view class="skeleton-line skeleton-line--long" />
          <view class="skeleton-line skeleton-line--short" />
        </view>
      </view>

      <view v-else-if="messages.length === 0" class="state-box placeholder-block">
        <view class="empty-icon">💬</view>
        <text class="placeholder-title">{{ searchKeyword ? '未找到匹配的留言' : '暂无留言' }}</text>
        <text class="placeholder-desc">{{ searchKeyword ? '换个关键词或清除筛选试试' : '还没有任何留言数据' }}</text>
      </view>

      <view v-else class="message-list">
        <view
          v-for="item in messages"
          :key="item.id"
          class="message-item"
          @tap="isSelectMode && toggleSelect(item.id)"
        >
          <view
            v-if="isSelectMode"
            class="check-box"
            :class="{ 'check-box--on': selectedIds.has(item.id) }"
          >
            <text v-if="selectedIds.has(item.id)" class="check-icon">✓</text>
          </view>
          <view class="message-main">
            <view class="message-head">
              <view class="message-user-row">
                <image
                  class="message-avatar"
                  :src="item.avatar_url ? resolveMediaUrl(item.avatar_url) : '/static/default-avatar.png'"
                  mode="aspectFill"
                  @error="onAvatarError($event, item)"
                />
                <text class="message-user">{{ displayName(item) }}</text>
                <view class="badge" :class="roleBadgeClass(item.user_role)">
                  <text>{{ roleLabel(item.user_role) }}</text>
                </view>
              </view>
              <text class="message-time">{{ formatTime(item.created_at) }}</text>
            </view>
            <view
              class="message-content-box"
              :class="{ 'message-content-box--clamped': clampedIds.has(item.id) && !expandedIds.has(item.id) }"
            >
              <text class="message-content">{{ item.content }}</text>
              <!-- 隐藏测量节点：量取全文真实高度（不受限高裁剪影响） -->
              <view class="content-measure">
                <text class="message-content">{{ item.content }}</text>
              </view>
            </view>
            <view
              v-if="clampedIds.has(item.id)"
              class="msg-fold"
              @tap.stop="toggleFold(item.id)"
            >
              <text class="msg-fold__text">{{ expandedIds.has(item.id) ? '收起' : '展开全文' }}</text>
            </view>
            <view class="message-meta">
              <text v-if="item.room_title" class="meta-text meta-text--copy" @tap.stop="copyRoomId(item.room_id)">房间: {{ item.room_title }}</text>
              <text v-else class="meta-text meta-text--copy" @tap.stop="copyRoomId(item.room_id)">房间: {{ item.room_id.slice(0, 8) }}…</text>
              <text v-if="!isSelectMode" class="meta-text meta-text--danger" @tap.stop="handleDeleteOne(item)">删除</text>
            </view>
          </view>
        </view>
        <view v-if="!hasMore && messages.length > 0" class="no-more"><text>没有更多了</text></view>
        <view v-if="isSelectMode" class="select-mode-spacer" />
      </view>
    </scroll-view>

    <!-- 底部批量操作栏（选择模式） -->
    <view v-if="isSelectMode" class="select-bar">
      <view class="select-bar-left">
        <view class="select-all-row" @tap="toggleSelectAll">
          <view class="check-box" :class="{ 'check-box--on': isAllSelected }">
            <text v-if="isAllSelected" class="check-icon">✓</text>
          </view>
          <text class="select-all-text">全选本页</text>
        </view>
        <text class="select-count">已选 {{ selectedIds.size }} 条</text>
      </view>
      <view
        class="batch-btn"
        :class="{ 'batch-btn--disabled': selectedIds.size === 0 }"
        @tap="handleBatchDelete"
      >
        <text class="batch-btn__text">批量删除</text>
      </view>
    </view>

    <!-- 按房间筛选弹层（治理例外：服务端搜索+分页业务弹层，TabManager 同款先例，不套 PickerSheet——房间需服务端检索；
         z-index 2000 页面级；动画基线对齐 TargetSelector：mask 淡入 + 0.3s 滑入滑出） -->
    <view v-if="roomPickerVisible" class="room-picker-mask" @tap="closeRoomPicker">
      <view class="room-picker-panel" :class="{ 'is-open': roomPickerShown }" @tap.stop>
        <view class="room-picker-header">
          <text class="room-picker-title">选择直播间</text>
          <view class="room-picker-close" @tap="closeRoomPicker">
            <text class="room-picker-close-text">✕</text>
          </view>
        </view>
        <view class="room-picker-search">
          <view class="app-search-field room-picker-field">
            <text class="room-picker-icon iconfont icon-search"></text>
            <input
              v-model="roomPickerKeyword"
              class="room-picker-input"
              placeholder="搜索直播间标题"
              placeholder-class="room-picker-placeholder"
              confirm-type="search"
              @input="onRoomPickerInput"
              @confirm="onRoomPickerConfirm"
            />
            <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
            <view class="search-clear-slot">
              <ClearButton v-if="roomPickerKeyword" @clear="onRoomPickerClear" />
            </view>
          </view>
        </view>
        <scroll-view class="room-picker-list" scroll-y @scrolltolower="loadMorePickerRooms" :lower-threshold="120">
          <view
            v-for="r in roomPickerRooms"
            :key="r.id"
            class="room-picker-item"
            :class="{ 'is-selected': filteredRoomId === r.id }"
            @tap="pickRoom(r)"
          >
            <view class="room-picker-item-main">
              <text class="room-picker-item-name">{{ r.title || '未命名直播间' }}</text>
              <view v-if="r.is_private" class="room-picker-badge">
                <text class="room-picker-badge-text">私密</text>
              </view>
            </view>
            <text v-if="filteredRoomId === r.id" class="room-picker-check">✓</text>
          </view>
          <view v-if="roomPickerLoading && roomPickerRooms.length === 0" class="room-picker-hint">
            <text class="room-picker-hint-text">加载中...</text>
          </view>
          <view
            v-else-if="!roomPickerLoading && roomPickerError && roomPickerRooms.length === 0"
            class="room-picker-hint"
            @tap="loadRoomPickerRooms(true)"
          >
            <text class="room-picker-hint-text">加载失败，点击重试</text>
          </view>
          <view v-else-if="!roomPickerLoading && !roomPickerError && roomPickerRooms.length === 0" class="room-picker-hint">
            <text class="room-picker-hint-text">暂无匹配的直播间</text>
          </view>
          <view v-if="roomPickerLoading && roomPickerRooms.length > 0" class="room-picker-loadmore">
            <text class="room-picker-hint-text">加载中...</text>
          </view>
          <view v-if="!roomPickerHasMore && roomPickerRooms.length > 0" class="room-picker-loadmore">
            <text class="room-picker-hint-text">没有更多了</text>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onUnmounted } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import {
  getAdminMessages,
  batchDeleteMessages,
  clearRoomMessages,
  deleteRoomMessage,
} from '@/api/message';
import { getAdminRooms } from '@/api/room';
import type { AdminMessageItem, AdminMessageQueryParams, AdminMessagePageResult } from '@/api/message';
import { useAdminGuard } from '@/composables/useAdminGuard';
import { resolveMediaUrl } from '@/utils/url';
import ClearButton from '@/components/app/ClearButton.vue';

const timeTabs = [
  { key: 'all', label: '全部' },
  { key: 'today', label: '今日' },
  { key: '7d', label: '近7天' },
  { key: '30d', label: '近30天' },
];
const timeIndex = ref(0);

const messages = ref<AdminMessageItem[]>([]);
const page = ref(1);
const pageSize = 20;
const total = ref(0);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const loadedOnce = ref(false);
const searchKeyword = ref('');
const roomId = ref('');
const filteredRoomId = ref('');  // 显式"按房间筛选"入口的房间ID（无 roomId 预填时）
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const roomIdShort = computed(() => (roomId.value ? roomId.value.slice(0, 8) : ''));

// 选择模式
const isSelectMode = ref(false);
const selectedIds = ref<Set<string>>(new Set());

// 留言内容超长折叠（防大段文字撑满管理页面篇幅；普通短留言无任何影响）
const clampedIds = ref<Set<string>>(new Set());
const expandedIds = ref<Set<string>>(new Set());

const hasMore = computed(() => page.value * pageSize < total.value);
const isAllSelected = computed(
  () => messages.value.length > 0 && messages.value.every((m) => selectedIds.value.has(m.id))
);

onLoad((options?: any) => {
  if (options?.roomId) roomId.value = String(options.roomId);
});

onShow(() => {
  if (!useAdminGuard()) return;
  if (!loadedOnce.value) loadMessages(true);
});

function onTimeChange(idx: number) {
  timeIndex.value = idx;
  loadMessages(true);
}

function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadMessages(true), 300);
}

function clearSearch() {
  searchKeyword.value = '';
  loadMessages(true);
}

// ===== 按房间筛选（弹层选房：全站房间服务端搜索+分页；治理例外：业务弹层内联实现，TabManager 先例，不套 PickerSheet——资源需服务端检索） =====
interface PickerRoomItem {
  id: string;
  title: string;
  is_private: boolean;
}

const roomPickerVisible = ref(false);
const roomPickerShown = ref(false);
const roomPickerKeyword = ref('');
const roomPickerRooms = ref<PickerRoomItem[]>([]);
const roomPickerTotal = ref(0);
const roomPickerPage = ref(1);
const roomPickerLoading = ref(false);
const roomPickerError = ref(false);
const roomPickerTitle = ref('');
let roomPickerSearchTimer: ReturnType<typeof setTimeout> | null = null;
let roomPickerReqSeq = 0;

const roomPickerHasMore = computed(() => roomPickerRooms.value.length < roomPickerTotal.value);

/** 已筛选房间胶囊文案：优先房间标题，无标题退化 ID 前 8 位 */
const roomFilterLabel = computed(() => {
  if (!filteredRoomId.value) return '';
  return roomPickerTitle.value
    ? `房间: ${roomPickerTitle.value}`
    : `房间: ${filteredRoomId.value.slice(0, 8)}…`;
});

/** 打开房间选择弹层（保留上次关键字并重拉第一页） */
function openRoomFilter() {
  roomPickerVisible.value = true;
  roomPickerShown.value = false;
  setTimeout(() => {
    roomPickerShown.value = true;
  }, 50);
  loadRoomPickerRooms(true);
}

/** 关闭弹层（先滑出动画再卸载，对齐 TargetSelector 动画基线） */
function closeRoomPicker() {
  if (!roomPickerShown.value) {
    roomPickerVisible.value = false;
    return;
  }
  roomPickerShown.value = false;
  setTimeout(() => {
    roomPickerVisible.value = false;
  }, 300);
}

/** 关键字搜索（300ms 防抖，服务端 q 检索标题） */
function onRoomPickerInput() {
  if (roomPickerSearchTimer) clearTimeout(roomPickerSearchTimer);
  roomPickerSearchTimer = setTimeout(() => loadRoomPickerRooms(true), 300);
}

function onRoomPickerConfirm() {
  if (roomPickerSearchTimer) clearTimeout(roomPickerSearchTimer);
  loadRoomPickerRooms(true);
}

function onRoomPickerClear() {
  roomPickerKeyword.value = '';
  loadRoomPickerRooms(true);
}

/** 上拉加载下一页 */
function loadMorePickerRooms() {
  if (roomPickerLoading.value || !roomPickerHasMore.value) return;
  roomPickerPage.value += 1;
  loadRoomPickerRooms(false);
}

/**
 * 全站房间分页拉取（admin 鉴权接口）。
 * 竞态/健壮性：seq 丢弃过期响应；追加按 id 去重；
 * 首页空但 total>0（端口契约不一致）或追加断裂时以实际条数兜底，防分页死循环（参照 live-manage admin 模式）。
 */
async function loadRoomPickerRooms(reset = false) {
  const seq = ++roomPickerReqSeq;
  if (reset) {
    roomPickerPage.value = 1;
    roomPickerTotal.value = 0;
    roomPickerRooms.value = [];
  }
  roomPickerLoading.value = true;
  roomPickerError.value = false;
  try {
    const kw = roomPickerKeyword.value.trim();
    const params: { page: number; size: number; q?: string } = { page: roomPickerPage.value, size: 20 };
    if (kw) params.q = kw;
    const res = await getAdminRooms(params);
    if (seq !== roomPickerReqSeq) return;
    const data = res.data as { items?: any[]; total?: number } | undefined;
    const items: PickerRoomItem[] = (data?.items || []).map((r: any) => ({
      id: String(r.id),
      title: String(r.title || ''),
      is_private: !!r.is_private,
    }));
    let total = data?.total || 0;
    if (reset) {
      if (items.length === 0 && total > 0) total = 0;
      roomPickerRooms.value = items;
    } else {
      const existing = new Set(roomPickerRooms.value.map((r) => r.id));
      const fresh = items.filter((r) => !existing.has(r.id));
      if (fresh.length < items.length || items.length === 0) {
        total = roomPickerRooms.value.length + fresh.length;
      }
      roomPickerRooms.value = [...roomPickerRooms.value, ...fresh];
    }
    roomPickerTotal.value = total;
  } catch (e) {
    if (seq === roomPickerReqSeq) {
      roomPickerError.value = true;
      console.error('[留言管理] 全站房间列表加载失败', e);
    }
  } finally {
    if (seq === roomPickerReqSeq) roomPickerLoading.value = false;
  }
}

/** 选中房间：回填 id + 标题（供胶囊展示），随后按房间刷新留言 */
function pickRoom(r: PickerRoomItem) {
  if (filteredRoomId.value !== r.id) {
    filteredRoomId.value = r.id;
    roomPickerTitle.value = r.title;
    loadMessages(true);
  }
  closeRoomPicker();
}

function clearRoomFilter() {
  filteredRoomId.value = '';
  roomPickerTitle.value = '';
  loadMessages(true);
}

/** 复制房间 ID */
function copyRoomId(id: string) {
  uni.setClipboardData({
    data: id,
    success: () => uni.showToast({ title: '房间ID已复制', icon: 'success' }),
  });
}

/** 计算时间 Tab 的 start_time（本地时间，ISO 格式） */
function getStartTime(): string | undefined {
  const now = new Date();
  let start: Date;
  switch (timeIndex.value) {
    case 1:
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
      break;
    case 2:
      start = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
      break;
    case 3:
      start = new Date(now.getTime() - 30 * 24 * 3600 * 1000);
      break;
    default:
      return undefined;
  }
  return start.toISOString();
}

/** 剔除 undefined/空串字段（避免 uni.request 序列化空值导致 422） */
function cleanParams(params: Record<string, any>): Record<string, any> {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
  );
}

async function loadMessages(reset = false) {
  if (reset) {
    page.value = 1;
    total.value = 0;
    messages.value = [];
    clampedIds.value = new Set();
    expandedIds.value = new Set();
  }
  isLoading.value = true;
  try {
    // 搜索框解析：`房间:ID`/`room:ID` 前缀 → room_id；裸 UUID → room_id
    const kw = searchKeyword.value.trim();
    let keyword: string | undefined;
    let searchRoomId: string | undefined;
    const roomPrefix = kw.match(/^(?:房间|直播间|room)[:：]\s*(\S+)/i);
    if (roomPrefix) {
      searchRoomId = roomPrefix[1].trim();
    } else if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(kw)) {
      searchRoomId = kw;
    } else if (kw) {
      keyword = kw;
    }

    const params: AdminMessageQueryParams = cleanParams({
      page: page.value,
      page_size: pageSize,
      keyword,
      room_id: roomId.value || filteredRoomId.value || searchRoomId || undefined,
      start_time: getStartTime(),
    });
    const res = await getAdminMessages(params);
    const data = res.data as AdminMessagePageResult;
    const items = data?.items || [];
    total.value = data?.total || 0;
    messages.value = reset ? items : [...messages.value, ...items];
    loadedOnce.value = true;
  } catch (e) {
    console.error('[留言管理] 加载失败', e);
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
    // 数据落定后重新测量内容高度，决定哪些留言需要折叠
    scheduleOverflowMeasure();
  }
}

function loadMore() {
  if (isLoadingMore.value || !hasMore.value || isLoading.value) return;
  isLoadingMore.value = true;
  page.value += 1;
  loadMessages(false);
}

/** 留言内容折叠上限（3 行 × 行高 40rpx） */
const CONTENT_MAX_RPX = 120;

/** 展开/收起超长留言 */
function toggleFold(id: string) {
  const next = new Set(expandedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  expandedIds.value = next;
}

/**
 * 批量测量留言全文真实高度（隐藏测量节点，不受限高裁剪影响），
 * 超出上限的条目标记为可折叠；测量失败兜底不折叠（fail-open，宁可不折叠也不藏内容）。
 */
function scheduleOverflowMeasure() {
  const snapshot = messages.value.map((m) => m.id);
  if (snapshot.length === 0) return;
  nextTick(() => {
    setTimeout(() => {
      uni
        .createSelectorQuery()
        .selectAll('.content-measure')
        .boundingClientRect()
        .exec((res) => {
          const rects: any[] = (res && res[0]) || [];
          if (!rects || rects.length === 0) return;
          const limit = uni.upx2px(CONTENT_MAX_RPX);
          const current = new Set(messages.value.map((m) => m.id));
          const nextClamped = new Set<string>();
          snapshot.forEach((id, idx) => {
            if (!current.has(id)) return; // 测量期间数据已刷新，跳过陈旧项
            const h = rects[idx] && rects[idx].height;
            if (h && h > limit) nextClamped.add(id);
          });
          clampedIds.value = nextClamped;
        });
    }, 50);
  });
}

/** 昵称兜底：user_display_name（后端透出）→ extra.user_display_name → ID 尾号 */
function displayName(item: AdminMessageItem): string {
  const name = item.user_display_name || item.extra?.user_display_name;
  if (name) return name;
  const uid = String(item.user_id || '');
  return uid ? `用户 ${uid.slice(-4)}` : '未知用户';
}

/** 头像加载失败兜底（变异地字段防重复渲染） */
function onAvatarError(e: any, item: AdminMessageItem) {
  const target = e?.target || e?.currentTarget;
  if (target) target.src = '/static/default-avatar.png';
  if (item) item.avatar_url = null;
}

function formatTime(iso: string): string {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${m}-${day} ${hh}:${mm}`;
  } catch {
    return iso;
  }
}

/** 角色徽章文案（对齐用户管理页 roleLabel 语义） */
function roleLabel(role: string): string {
  const map: Record<string, string> = {
    REGULAR: '普通用户',
    MODERATOR: '协管员',
    ADMIN: '管理员',
    SUPERADMIN: '超级管理员',
  };
  return map[role] || role || 'REGULAR';
}

/** 角色徽章样式（低饱和 tint，对齐 --home-badge-* 与用户管理页徽章体系） */
function roleBadgeClass(role: string): string {
  const cls: Record<string, string> = {
    REGULAR: 'badge--role-regular',
    MODERATOR: 'badge--role-moderator',
    ADMIN: 'badge--role-admin',
    SUPERADMIN: 'badge--role-superadmin',
  };
  return cls[role] || 'badge--role-regular';
}

// ===== 选择 / 批删 =====
function toggleSelect(id: string) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = new Set();
  } else {
    selectedIds.value = new Set(messages.value.map((m) => m.id));
  }
}

async function handleBatchDelete() {
  const ids = [...selectedIds.value];
  if (ids.length === 0) return;
  if (ids.length > 200) {
    uni.showToast({ title: '单次最多删除 200 条', icon: 'none' });
    return;
  }
  const { confirm } = await new Promise<{ confirm: boolean }>((resolve) => {
    uni.showModal({
      title: '批量删除',
      content: `确定删除选中的 ${ids.length} 条留言？此操作不可恢复。`,
      confirmColor: '#dc2626',
      success: (r) => resolve(r),
    });
  });
  if (!confirm) return;
  try {
    const res = await batchDeleteMessages(ids);
    uni.showToast({ title: `已删除 ${res.data?.deleted_count ?? ids.length} 条`, icon: 'success' });
    selectedIds.value = new Set();
    isSelectMode.value = false;
    loadMessages(true);
  } catch (e) {
    console.error('[留言管理] 批量删除失败', e);
    uni.showToast({ title: '删除失败', icon: 'none' });
  }
}

// ===== 单条删除留言（管理员） =====
function handleDeleteOne(item: any) {
  uni.showModal({
    title: '删除留言',
    content: '确定删除这条留言？此操作不可恢复。',
    confirmText: '删除',
    confirmColor: '#dc2626',
    success: async (r) => {
      if (!r.confirm) return;
      try {
        await deleteRoomMessage(item.room_id, item.id);
        uni.showToast({ title: '已删除', icon: 'success' });
        loadMessages(true);
      } catch (e) {
        console.error('[留言管理] 单删失败', e);
        uni.showToast({ title: '删除失败', icon: 'none' });
      }
    },
  });
}

// ===== 清空房间留言 =====
function handleClearRoom() {
  if (!roomId.value) return;
  uni.showModal({
    title: '清空留言',
    content: '确定清空该直播间全部留言？此操作不可恢复。',
    confirmText: '清空',
    confirmColor: '#dc2626',
    success: async (r) => {
      if (!r.confirm) return;
      try {
        await clearRoomMessages(roomId.value);
        uni.showToast({ title: '已清空留言', icon: 'success' });
        loadMessages(true);
      } catch (e) {
        console.error('[留言管理] 清空失败', e);
        uni.showToast({ title: '清空失败', icon: 'none' });
      }
    },
  });
}

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer);
  if (roomPickerSearchTimer) clearTimeout(roomPickerSearchTimer);
});
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.admin-page.consumer-layout {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--home-bg);
}

.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--home-card);
  border-bottom: 1rpx solid var(--home-divider);
  padding: 0 24rpx;

  .tab-group {
    display: flex;
    align-items: center;
    flex: 1;
    min-width: 0;
  }

  .tab-bar__actions {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    margin-left: 16rpx;
  }

  .select-entry-btn {
    /* 扁平胶囊：保持原主色填充，去投影/去缩放（对齐其余管理页 header-btn--primary 范式） */
    min-height: 64rpx;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    padding: 8rpx 28rpx;
    background: var(--home-primary);
    border-radius: $radius-full;
    transition: $motion-fast;

    &.select-entry-btn--cancel {
      background: var(--home-action-secondary-bg);

      .select-entry-btn__text {
        color: var(--home-text2);
      }
    }

    &:active {
      opacity: 0.85;
    }

    .select-entry-btn__text {
      font-size: $font-sm;
      line-height: 1;
      color: $color-text-white;
    }
  }

  .tab-item {
    position: relative;
    padding: 20rpx 8rpx;
    margin-right: 40rpx;
    font-size: $font-md;
    color: var(--home-text2);
    transition: $motion-fast;

    &.tab-item--active {
      color: var(--home-primary);
      font-weight: 600;
    }

    &::after {
      content: '';
      position: absolute;
      left: 50%;
      bottom: 0;
      transform: translateX(-50%);
      width: 0;
      height: 4rpx;
      border-radius: 2rpx;
      background: var(--home-primary);
      transition: $motion-normal;
    }

    &.tab-item--active::after {
      width: 28rpx;
    }
  }
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  background: var(--home-card);
  border-bottom: 1rpx solid var(--home-divider);

  .filter-search {
    /* 叠加共享容器 .app-search-field：白底+1rpx细边+胶囊；高度 64rpx（管理端档，D6，原 68 统一） */
    flex: 1;
    min-width: 0;
    height: 64rpx;
    box-sizing: border-box;
    /* 聚焦态：默认态即最终态，无灰→白切换、无光晕（原 :focus-within 光晕已删） */

    .filter-icon {
      color: var(--search-icon);
      font-size: 26rpx;
      margin-right: 12rpx;
      flex-shrink: 0;
      line-height: 1;
    }

    .filter-input {
      flex: 1;
      height: 100%;
      font-size: $font-sm;
      color: var(--home-text1);
      background: transparent;
      padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
    }

    .filter-placeholder {
      color: var(--search-placeholder);
    }
  }

  /* 按房间筛选入口：与搜索框同高的扁平胶囊（保持原主色填充、去阴影，对齐其余管理页扁平按钮范式） */
  .room-entry-btn {
    flex-shrink: 0;
    min-height: 64rpx;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    padding: 0 24rpx;
    background: var(--home-primary);
    border-radius: $radius-full;
    transition: $motion-fast;

    &:active {
      opacity: 0.85;
    }

    .room-entry-btn__text {
      font-size: $font-sm;
      line-height: 1;
      color: $color-text-white;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 300rpx;
    }

    .room-entry-btn__clear {
      margin-left: 16rpx;
      padding-left: 16rpx;
      border-left: 1rpx solid rgba(255, 255, 255, 0.4);
      font-size: $font-sm;
      line-height: 1;
      color: rgba(255, 255, 255, 0.85);
    }
  }
}

.room-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 24rpx;
  background: var(--home-primary-light);
  border-bottom: 1rpx solid var(--home-divider);

  .room-filter-tag {
    font-size: $font-sm;
    color: var(--home-primary);
  }

  .room-clear-btn {
    min-height: 64rpx;
    display: flex;
    align-items: center;
    padding: 8rpx 24rpx;
    background: var(--home-action-danger-bg);
    border-radius: $radius-full;
    transition: $motion-fast;

    &:active {
      opacity: 0.8;
    }

    .room-clear-btn__text {
      font-size: $font-sm;
      color: var(--home-action-danger-text);
    }
  }
}

.content-scroll {
  flex: 1;
  overflow: hidden;
}

.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
  color: var(--home-text2);

  .state-text {
    font-size: $font-sm;
  }
}

.message-list {
  padding: 16rpx 24rpx;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  background: var(--home-card);
  border-radius: $radius-lg;
  padding: 20rpx;
  margin-bottom: 16rpx;
  box-shadow: var(--home-shadow-card);
  transition: $motion-fast;

  &:active {
    background: var(--home-input-bg);
  }

  .check-box {
    width: 44rpx;
    height: 44rpx;
    border-radius: 50%;
    border: 3rpx solid rgba(0, 0, 0, 0.15);
    background: var(--home-card);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 4rpx;
    transition: $motion-fast;

    &.check-box--on {
      background: var(--home-primary);
      border-color: var(--home-primary);
    }

    .check-icon {
      color: $color-text-white;
      font-size: 22rpx;
      font-weight: 700;
    }
  }

  .message-main {
    flex: 1;
    min-width: 0;

    .message-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12rpx;

      .message-user-row {
        display: flex;
        align-items: center;
        gap: 12rpx;

        .message-avatar {
          width: 44rpx;
          height: 44rpx;
          border-radius: 50%;
          flex-shrink: 0;
          background: var(--home-border, #eee);
        }
        flex: 1;
        min-width: 0;

        .message-user {
          font-size: $font-sm;
          font-weight: 600;
          color: var(--home-text1);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }

      .message-time {
        font-size: 22rpx;
        color: var(--home-text2);
        flex-shrink: 0;
      }
    }

    .message-content-box {
      position: relative;
      margin-top: 10rpx;

      /* 超长留言限高折叠：超过 3 行（120rpx）裁剪，展开后解除限制 */
      &.message-content-box--clamped {
        max-height: 120rpx;
        overflow: hidden;
      }
    }

    /* 隐藏测量节点：同宽同字体的真实内容副本，量取完整高度，不参与布局 */
    .content-measure {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      visibility: hidden;
    }

    .message-content {
      font-size: $font-md;
      color: var(--home-text1);
      line-height: 40rpx;
      word-break: break-word;
    }

    .msg-fold {
      min-height: 44rpx;
      margin-top: 4rpx;
      display: flex;
      align-items: center;

      .msg-fold__text {
        font-size: 22rpx;
        color: var(--home-primary);
      }
    }

    .message-meta {
      display: flex;
      align-items: center;
      gap: 24rpx;
      margin-top: 8rpx;

      .meta-text {
        font-size: 22rpx;
        color: var(--home-text2);
        /* 卡片高度随留言行数自适应：meta 行不再按 88rpx 触控档撑高（房间复制/删除仍可点），改为紧凑高度 */
        min-height: 56rpx;
        display: flex;
        align-items: center;

        &.meta-text--copy {
          text-decoration: underline;
          text-decoration-color: var(--home-border);
        }

        &.meta-text--danger {
          color: #dc2626;
          margin-left: 16rpx;
        }
      }
    }
  }
}

/* 角色徽章（低饱和 tint，对齐用户管理页徽章体系） */
.badge {
  padding: 2rpx 12rpx;
  border-radius: $radius-full;
  font-size: 20rpx;
  line-height: 1.5;
  flex-shrink: 0;
}
.badge--role-regular { background: rgba(100, 116, 139, 0.12); color: #64748b; }
.badge--role-moderator { background: rgba(59, 130, 246, 0.1); color: #2563eb; }
.badge--role-admin { background: rgba(22, 163, 74, 0.1); color: #15803d; }
.badge--role-superadmin { background: rgba(234, 179, 8, 0.14); color: #a16207; }

/* 加载骨架（对齐用户管理页 skeleton 范式） */
.skeleton-card {
  padding: 24rpx;
  margin-bottom: 16rpx;
  background: var(--home-card);
  border-radius: $radius-lg;
  box-shadow: var(--home-shadow-card);
}
.skeleton-line {
  height: 20rpx;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 4rpx;
  margin-bottom: 12rpx;
}
.skeleton-line--long { width: 50%; }
.skeleton-line--short { width: 35%; margin-bottom: 0; }

/* 空态（对齐用户管理页 placeholder 范式） */
.placeholder-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  text-align: center;
}
.empty-icon {
  font-size: 72rpx;
  margin-bottom: 24rpx;
  opacity: 0.6;
}
.placeholder-title {
  font-size: $font-lg;
  font-weight: 600;
  color: var(--home-text1);
  margin-bottom: 12rpx;
}
.placeholder-desc {
  font-size: $font-sm;
  color: var(--home-text2);
}

.no-more {
  text-align: center;
  color: var(--home-text2);
  font-size: $font-sm;
  padding: 24rpx 0;
}

.select-mode-spacer {
  height: 140rpx;
}

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
  z-index: 100;
  box-shadow: $shadow-sm;

  .select-bar-left {
    display: flex;
    align-items: center;
    gap: 20rpx;

    .select-all-row {
      display: flex;
      align-items: center;
      gap: 8rpx;
      min-height: $touch-target-min;

      .check-box {
        width: 44rpx;
        height: 44rpx;
        border-radius: 50%;
        border: 3rpx solid rgba(0, 0, 0, 0.15);
        background: var(--home-card);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: $motion-fast;

        &.check-box--on {
          background: var(--home-primary);
          border-color: var(--home-primary);
        }

        .check-icon {
          color: $color-text-white;
          font-size: 22rpx;
          font-weight: 700;
        }
      }

      .select-all-text {
        font-size: $font-sm;
        color: var(--home-text1);
      }
    }

    .select-count {
      font-size: $font-sm;
      color: var(--home-text2);
    }
  }

  .batch-btn {
    min-height: 76rpx;
    display: flex;
    align-items: center;
    padding: 12rpx 36rpx;
    background: var(--home-action-danger-bg);
    border-radius: $radius-full;
    transition: $motion-fast;

    &.batch-btn--disabled {
      background: var(--home-action-secondary-bg);
    }

    &:active:not(.batch-btn--disabled) {
      opacity: 0.85;
      transform: scale(0.97);
    }

    .batch-btn__text {
      font-size: $font-sm;
      color: var(--home-action-danger-text);
    }
  }
}

/* ===== 按房间筛选弹层（治理例外：服务端搜索+分页业务弹层；z-index 2000 页面级；mask 淡入 + 0.3s 滑入滑出） ===== */
.room-picker-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 2000;
  animation: roomPickerFadeIn 0.3s ease;
}

@keyframes roomPickerFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.room-picker-panel {
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

.room-picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid var(--home-divider);
}

.room-picker-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-text1);
}

.room-picker-close {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  .room-picker-close-text {
    font-size: 28rpx;
    color: var(--home-text2);
  }
}

.room-picker-search {
  padding: 16rpx 32rpx;
}

/* 胶囊：叠加共享容器 .app-search-field（B站风格）；高度 64rpx（弹层档，对齐 TargetSelector） */
.room-picker-field {
  height: 64rpx;
  box-sizing: border-box;
}

.room-picker-icon {
  font-size: 26rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
  flex-shrink: 0;
  line-height: 1;
}

.room-picker-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  font-size: 26rpx;
  color: var(--home-text1);
  background: transparent;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.room-picker-placeholder {
  color: var(--search-placeholder);
}

.room-picker-list {
  flex: 1;
  min-height: 0;
  padding: 0 32rpx 32rpx;
  box-sizing: border-box;
}

.room-picker-item {
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

.room-picker-item-main {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 1;
  min-width: 0;
}

.room-picker-item-name {
  font-size: 26rpx;
  color: var(--home-text1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-picker-badge {
  flex-shrink: 0;
  padding: 2rpx 12rpx;
  border-radius: $radius-full;
  background: var(--home-primary-light);

  .room-picker-badge-text {
    font-size: 20rpx;
    color: var(--home-primary);
  }
}

.room-picker-check {
  font-size: 28rpx;
  color: var(--home-primary);
  font-weight: bold;
  flex-shrink: 0;
}

.room-picker-hint {
  padding: 24rpx 0;
  text-align: center;
}

.room-picker-loadmore {
  padding: 12rpx 0 4rpx;
  text-align: center;
}

.room-picker-hint-text {
  font-size: 24rpx;
  color: var(--home-text2);
}
</style>
