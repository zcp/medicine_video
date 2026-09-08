<template>
  <view class="admin-page consumer-layout">
    <view class="tab-bar">
      <view class="tab-group">
        <view
          v-for="(t, idx) in tabList"
          :key="t.key"
          class="tab-item"
          :class="{ 'tab-item--active': activeIndex === idx }"
          @tap="handleTabTap(idx)"
        >
          <text>{{ t.label }}</text>
        </view>
      </view>
      <view class="header-btn" @tap="openCreateForm">
        <text class="add-icon iconfont icon-add"></text>
        <text>新增</text>
      </view>
    </view>

    <!-- 搜索栏：作用于当前 Tab，q 空值不入参（防 undefined 序列化）；图标/清除收进胶囊（结构归位） -->
    <view class="search-bar">
      <view class="app-search-field search-capsule">
        <text class="search-icon iconfont icon-search"></text>
        <input
          class="search-input"
          v-model="searchKeyword"
          placeholder="搜索标题/副标题"
          placeholder-class="search-placeholder"
          confirm-type="search"
          @input="handleSearchInput"
          @confirm="handleSearchConfirm"
        />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="clearSearch" />
        </view>
      </view>
    </view>

    <!-- 内容区：Tab 内容切换（点击 Tab 切换，仅激活 Tab 渲染内容避免串扰） -->
    <view
      v-for="(t, idx) in tabList"
      :key="t.key"
      class="admin-panel"
      v-show="activeIndex === idx"
    >
          <scroll-view
            class="list-scroll"
            scroll-y
            :refresher-enabled="true"
            :refresher-triggered="isPullRefreshing"
            @refresherrefresh="handleRefresh"
            @scrolltolower="loadMore"
          >
            <view class="list-inner">
              <view v-if="isLoading && items.length === 0">
                <view v-for="i in 3" :key="i" class="skeleton-card">
                  <view class="skeleton-img" />
                  <view class="skeleton-line skeleton-line--long" />
                </view>
              </view>

              <view v-else-if="error && items.length === 0" class="placeholder-block">
                <text class="placeholder-icon iconfont icon-error"></text>
                <text class="placeholder-title">加载失败</text>
                <text class="placeholder-desc">{{ error }}</text>
                <view class="retry-btn" @tap="loadList(true)">点击重试</view>
              </view>

              <view v-else-if="!isLoading && items.length === 0" class="placeholder-block">
                <text class="placeholder-icon"><uni-icons type="images" size="36" /></text>
                <text class="placeholder-title">暂无轮播图</text>
                <text class="placeholder-desc">点击右上角新增轮播图</text>
              </view>

              <template v-else>
                <view v-for="item in items" :key="item.id" class="feat-card">
                  <image
                    class="feat-cover"
                    :src="getImageUrl(item.image_url)"
                    mode="aspectFill"
                    lazy-load
                    @error="onCoverError(item)"
                  />
                  <view class="feat-info">
                    <view class="feat-title-row">
                      <text class="feat-title">{{ item.title }}</text>
                      <text :class="statusTagClass(item)" class="status-tag">
                        {{ statusLabel(item) }}
                      </text>
                    </view>
                    <text v-if="item.subtitle" class="feat-subtitle">{{ item.subtitle }}</text>
                    <view class="feat-meta">
                      <text class="feat-target">{{ targetLabel(item) }}</text>
                      <text class="feat-sort">排序: {{ item.sort_order }}</text>
                    </view>
                    <view class="feat-times" v-if="item.start_at || item.end_at">
                      <text v-if="item.start_at" class="feat-time">上线: {{ formatDate(item.start_at) }}</text>
                      <text v-if="item.end_at" class="feat-time">下线: {{ formatDate(item.end_at) }}</text>
                    </view>
                  </view>
                  <view class="feat-actions">
                    <view class="action-btn" @tap.stop="openEditForm(item)"><text>编辑</text></view>
                    <view class="action-btn action-btn--image" @tap.stop="handleReplaceImage(item)"><text>换图</text></view>
                    <view class="action-btn" :class="item.is_active ? '' : 'action-btn--warn'" @tap.stop="handleToggleActive(item)"><text>{{ toggleActiveLabel(item) }}</text></view>
                    <view class="action-btn action-btn--danger" @tap.stop="handleDelete(item)"><text>删除</text></view>
                  </view>
                </view>

                <view v-if="isLoadingMore" class="load-more">
                  <text class="load-more-text">加载中...</text>
                </view>
                <view v-else-if="!hasMore && items.length > 0" class="load-more">
                  <text class="load-more-text">已到底部</text>
                </view>
              </template>
            </view>
          </scroll-view>
    </view>

    <ModalDialog
      :visible="isFormVisible"
      :title="formMode === 'create' ? '新增轮播图' : '编辑轮播图'"
      :confirmText="formMode === 'create' ? '创建' : '保存'"
      :confirmLoading="isSubmitting"
      @update:visible="isFormVisible = $event"
      @confirm="handleFormConfirm"
      @cancel="closeForm"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">标题</text>
          <input class="form-input" v-model="formModel.title" placeholder="焦点图标题" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">副标题（选填）</text>
          <input class="form-input" v-model="formModel.subtitle" placeholder="副标题" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">图片URL</text>
          <view class="form-row">
            <input class="form-input form-input--grow" v-model="formModel.image_url" placeholder="https://..." placeholder-class="form-placeholder" />
            <view class="upload-btn" @tap="handleChooseImage">从相册选择</view>
          </view>
        </view>
        <view class="form-group">
          <text class="form-label">跳转目标类型</text>
          <wd-picker
            v-model="targetTypeValue"
            :columns="targetTypeLabels"
            title="选择跳转目标类型"
            :z-index="3000"
          >
            <view class="form-picker">
              <text>{{ formTargetLabel }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-picker>
        </view>
        <view v-if="formModel.target_type && formModel.target_type !== 'external'" class="form-group">
          <text class="form-label">跳转目标ID</text>
          <input
            v-if="!isSelectableTarget(formModel.target_type)"
            class="form-input"
            v-model="formModel.target_id"
            placeholder="输入目标ID（外部链接类型无需ID）"
            placeholder-class="form-placeholder"
          />
          <TargetSelector
            v-else
            :target-type="formModel.target_type"
            :model-value="formModel.target_id"
            @update:model-value="formModel.target_id = $event"
          />
        </view>
        <view v-if="formModel.target_type === 'external'" class="form-group">
          <text class="form-label">外部链接</text>
          <input class="form-input" v-model="formModel.target_url" placeholder="https://..." placeholder-class="form-placeholder" />
        </view>
        <view class="form-group">
          <text class="form-label">排序值（越小越靠前）</text>
          <input class="form-input" v-model.number="formModel.sort_order" type="number" placeholder="0" placeholder-class="form-placeholder" />
        </view>
        <view class="form-group form-group--switch">
          <text class="form-label">启用状态</text>
          <switch :checked="formModel.is_active" @change="formModel.is_active = $event.detail.value" color="#0F766E" />
        </view>
        <view class="form-group">
          <text class="form-label">上线时间</text>
          <wd-datetime-picker
            v-model="formModel.start_at"
            type="date"
            title="选择上线日期"
            placeholder="即时上线"
            :default-value="getDefaultPickerDate()"
            :z-index="3000"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !formModel.start_at }">{{ formatPickerDate(formModel.start_at) || '即时上线' }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-datetime-picker>
        </view>
        <view class="form-group">
          <text class="form-label">下线时间</text>
          <wd-datetime-picker
            v-model="formModel.end_at"
            type="date"
            title="选择下线日期"
            placeholder="长期有效"
            :default-value="getDefaultPickerDate()"
            :z-index="3000"
          >
            <view class="form-picker">
              <text :class="{ 'form-placeholder': !formModel.end_at }">{{ formatPickerDate(formModel.end_at) || '长期有效' }}</text>
              <text class="picker-arrow">▼</text>
            </view>
          </wd-datetime-picker>
          <text class="time-tip">不填下线时间表示长期有效</text>
        </view>
      </view>
    </ModalDialog>

    <!-- 重新上线：自定义下线日期（无可见触发区，由 ref.open 唤起；z-index=3000 遵守弹层章程） -->
    <wd-datetime-picker
      ref="reenableEndPickerRef"
      v-model="reenableEndAt"
      type="date"
      title="选择下线日期"
      :default-value="reenableDefaultEndAt"
      :min-date="reenableMinDate"
      :z-index="3000"
      @confirm="onReenableEndConfirm"
      @cancel="onReenableEndCancel"
    >
      <view class="reenable-picker-anchor" />
    </wd-datetime-picker>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { getAdminFeaturedContent, createFeaturedContent, updateFeaturedContent, deleteFeaturedContent, uploadFeaturedImage } from '@/api/featured';
import { resolveMediaUrl } from '@/utils/url';
import { isoToLocalDateStr, isoToLocalTimestamp, timestampToLocalDateISO, timestampToLocalDateStr } from '@/utils/datetime';
import WdDatetimePicker from 'wot-design-uni/components/wd-datetime-picker/wd-datetime-picker.vue';
import WdPicker from 'wot-design-uni/components/wd-picker/wd-picker.vue';
import { useAdminGuard } from '@/composables/useAdminGuard';
import type { FeaturedContent } from '@/types/featured';
import ModalDialog from '@/components/shared/ModalDialog.vue';
import TargetSelector from '@/components/common/TargetSelector.vue';
import { useSwiperTabs } from '@/composables/useSwiperTabs';
import ClearButton from '@/components/app/ClearButton.vue';

const items = ref<FeaturedContent[]>([]);
const isLoading = ref(false);
const isRefreshing = ref(false);
const isLoadingMore = ref(false);
const error = ref<string | null>(null);
const loadedOnce = ref(false);
const coverErrors = ref(new Set<string>());

const page = ref(1);
const size = 20;
const total = ref(0);
const hasMore = computed(() => page.value * size < total.value);
let listRequestSeq = 0;
let lastLoadMoreAt = 0;
/** 首屏滤空自动续拉上限（服务端 total 与客户端过滤口径不一致时，防止连环探测） */
const MAX_FILTER_PROBE = 5;
let filterProbeCount = 0;

const activeTab = ref<'active'|'inactive'|'all'>('active');
const tabList = [
  { key: 'active' as const, label: '正在展示' },
  { key: 'inactive' as const, label: '已下线' },
  { key: 'all' as const, label: '全部' },
];

const searchKeyword = ref('');
let searchTimer: ReturnType<typeof setTimeout> | null = null;

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    loadList(true);
  }, 300);
}

function handleSearchConfirm() {
  if (searchTimer) clearTimeout(searchTimer);
  loadList(true);
}

function clearSearch() {
  searchKeyword.value = '';
  loadList(true);
}

/**
 * Tab 索引 ↔ 业务联动：切换 activeTab 并重新加载（复用原 onTabChange 逻辑）
 */
function onTabActivated(idx: number): void {
  const t = tabList[idx];
  if (!t) return;
  if (activeTab.value === t.key) return;
  activeTab.value = t.key;
  loadList(true);
}

/** 使用滑动 Tab（点击 ↔ swiper 双向联动） */
const { activeIndex, handleTabTap } = useSwiperTabs(
  tabList.length,
  onTabActivated,
  0
);

const isFormVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const editingId = ref<string | null>(null);
const isSubmitting = ref(false);
const formModel = ref({
  title: '', subtitle: '', image_url: '',
  target_type: null as string | null, target_id: '', target_url: '',
  sort_order: 0,
  is_active: true,
  start_at: null as number | null,
  end_at: null as number | null,
});

const targetTypeLabels = ['无跳转', '直播间', '品牌', '外部链接'];
const targetTypeValues = [null, 'room', 'brand', 'external'];
const formTargetLabel = ref('无跳转');
/** wd-picker v-model（string 列，值=标签文本；watch 驱动 target_type 联动，见下） */
const targetTypeValue = ref('无跳转');

// 目标类型联动（wd-picker confirm → update:modelValue）：仅类型实际变化时清空 target_id，
// 回填（openEditForm 先赋 target_type）时值相等则跳过，避免误清回填的 target_id
watch(targetTypeValue, (label) => {
  const idx = targetTypeLabels.indexOf(label);
  const next = idx >= 0 ? targetTypeValues[idx] : null;
  if (next === formModel.value.target_type) return;
  formModel.value.target_type = next;
  formModel.value.target_id = '';
  formTargetLabel.value = idx >= 0 ? targetTypeLabels[idx] : '无跳转';
});

/** 过期焦点图「重新上线」默认时长（天） */
const REENABLE_DEFAULT_DAYS = 3;

/** 启停/重上线进行中，防连点 */
const isTogglingActive = ref(false);
/** 自定义下线日期选择器所绑定的条目 */
const reenableTarget = ref<FeaturedContent | null>(null);
const reenableEndAt = ref<number | null>(null);
const reenableEndPickerRef = ref<{ open: () => void; close: () => void } | null>(null);

/** 当天 00:00 时间戳（每次调用取当前日期；用于 picker 默认定位与创建态校验，避免跨零点缓存过期） */
function getDefaultPickerDate(): number {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d.getTime();
}

/** 今天起算 +N 天的 00:00 时间戳（重新上线默认下线日） */
function getDatePlusDays(days: number): number {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + days);
  return d.getTime();
}

const reenableMinDate = computed(() => getDefaultPickerDate());
const reenableDefaultEndAt = computed(() => getDatePlusDays(REENABLE_DEFAULT_DAYS));

/**
 * 启用前是否必须重设下线时间：
 * - 后端 status=expired，或
 * - end_at 已过期（惰性下线后仅改 is_active 会被再次翻回）
 */
function needsRescheduleOnEnable(item: FeaturedContent): boolean {
  if (item.status === 'expired') return true;
  if (!item.end_at) return false;
  const endMs = new Date(item.end_at).getTime();
  if (isNaN(endMs)) return false;
  return endMs < Date.now();
}

function toggleActiveLabel(item: FeaturedContent): string {
  if (item.is_active) return '停用';
  return needsRescheduleOnEnable(item) ? '重新上线' : '启用';
}

/**
 * 创建模式：下线选择器可选最早日期 = max(今天, 已选上线日)；
 * 编辑模式不限制 —— 组件会钳制回写越界的 v-model（wd-datetime-picker-view.vue:363-372），编辑态传 min-date 会静默篡改过去时间
 */
const endPickerMinDate = computed(() => {
  if (formMode.value !== 'create') return undefined;
  const s = formModel.value.start_at;
  const t = getDefaultPickerDate();
  return s ? Math.max(t, s) : t;
});

/** 上线日改晚于已选下线日时，清空下线时间并提示（避免下次打开下线选择器被钳制到新 min-date 造成困惑） */
function onStartAtConfirm(e: any) {
  const start = e?.value ?? null;
  if (start && formModel.value.end_at && formModel.value.end_at < start) {
    formModel.value.end_at = null;
    uni.showToast({ title: '下线时间早于新的上线时间，已清空，请重新选择', icon: 'none' });
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '长期有效';
  return isoToLocalDateStr(dateStr) || '长期有效';
}

function formatPickerDate(timestamp: number | null) {
  return timestampToLocalDateStr(timestamp);
}

function getImageUrl(url: string) {
  if (coverErrors.value.has(url)) return '/logo.png';
  if (!url) return '/logo.png';
  if (/^https?:\/\//.test(url)) return url;
  return resolveMediaUrl(url);
}

function onCoverError(item: FeaturedContent) {
  coverErrors.value = new Set([...coverErrors.value, item.image_url]);
}

function targetLabel(item: FeaturedContent) {
  if (!item.target_type) return '无跳转';
  const idx = targetTypeValues.indexOf(item.target_type);
  return `跳转: ${idx > 0 ? targetTypeLabels[idx] : item.target_type}`;
}

function isSelectableTarget(type: string | null): boolean {
  return type === 'room' || type === 'brand';
}

function getItemStatus(item: FeaturedContent): string {
  if (item.status) return item.status;
  return item.is_active ? 'active' : 'inactive';
}

function statusLabel(item: FeaturedContent) {
  const s = getItemStatus(item);
  if (s === 'upcoming') return '待上线';
  if (s === 'expired') return '已过期';
  return s === 'active' ? '已上线' : '已下线';
}

function statusTagClass(item: FeaturedContent) {
  return getItemStatus(item) === 'active' ? 'status-tag status-tag--on' : 'status-tag status-tag--off';
}

function filterItemsByTab(list: FeaturedContent[], tab: 'active'|'inactive'|'all') {
  if (tab === 'active') return list.filter(item => getItemStatus(item) === 'active');
  if (tab === 'inactive') return list.filter(item => ['inactive', 'expired'].includes(getItemStatus(item)));
  return list;
}

async function loadList(reset = true) {
  if (!reset && (isLoading.value || isLoadingMore.value)) return;

  const requestId = ++listRequestSeq;
  const requestTab = activeTab.value;
  const requestPage = reset ? 1 : page.value + 1;

  if (reset) {
    page.value = 1;
    // 刷新/搜索/切 Tab 不清空旧列表（stale-while-revalidate）：
    // 避免内容高度骤降导致原生 refresher 动画错乱；骨架仅首载（列表为空）时显示
    isLoading.value = true;
    isLoadingMore.value = false;
    filterProbeCount = 0;
  } else {
    isLoadingMore.value = true;
  }

  error.value = null;

  try {
    const params: Record<string, any> = { page: requestPage, size };
    if (requestTab === 'active') params.status = 'active';
    else if (requestTab === 'inactive') params.status = 'inactive';
    const kw = searchKeyword.value.trim();
    if (kw) params.q = kw;

    const res = await getAdminFeaturedContent(params);
    if (requestId !== listRequestSeq || requestTab !== activeTab.value) return;

    if (res.code === 200) {
      const rawItems = res.data.items || [];
      const newItems = filterItemsByTab(rawItems, requestTab);
      page.value = requestPage;

      // total 自校正：展示口径与服务端分页口径对齐，防止 hasMore 恒真导致连环加载
      let nextTotal = res.data.total ?? newItems.length;
      if (reset) {
        items.value = newItems;
      } else {
        const existingIds = new Set(items.value.map(i => i.id));
        const deduped = newItems.filter(item => !existingIds.has(item.id));
        items.value = [...items.value, ...deduped];
        // 本页无新增可见数据（全重复或服务端返回空）→ 以实际列表长度为准，终止继续加载
        if (deduped.length < newItems.length || rawItems.length === 0) {
          nextTotal = items.value.length;
        }
      }
      total.value = nextTotal;
    }
  } catch (e: any) {
    if (requestId !== listRequestSeq || requestTab !== activeTab.value) return;
    error.value = e?.message || '加载失败';
  } finally {
    if (requestId !== listRequestSeq || requestTab !== activeTab.value) return;
    isLoading.value = false;
    isRefreshing.value = false;
    isLoadingMore.value = false;
    loadedOnce.value = true;
  }

  // D2：首屏/刷新滤空自动续拉——可见列表为空但服务端仍有数据时最多探测 MAX_FILTER_PROBE 页，
  // 防止"有 total 却显示暂无、无法继续加载"的卡死态
  if (reset && requestId === listRequestSeq && requestTab === activeTab.value) {
    while (items.value.length === 0 && page.value * size < total.value && filterProbeCount < MAX_FILTER_PROBE) {
      filterProbeCount++;
      await loadList(false);
    }
    // 探测达到上限仍未找到可见数据 → 以实际列表为准终止（置空 total 结束加载态）
    if (items.value.length === 0 && filterProbeCount >= MAX_FILTER_PROBE) {
      total.value = 0;
    }
  }
}

async function loadMore() {
  if (isLoadingMore.value || !hasMore.value || isLoading.value || items.value.length === 0) return;

  const now = Date.now();
  if (now - lastLoadMoreAt < 500) return;
  lastLoadMoreAt = now;

  await loadList(false);
}

/** 下拉刷新最小展示时长（ms）：请求过快时保证指示器可感知 */
const PULL_REFRESH_MIN_MS = 400;
const isPullRefreshing = ref(false);
let pullRefreshStartTime = 0;

async function handleRefresh() {
  if (isPullRefreshing.value) return;
  isPullRefreshing.value = true;
  pullRefreshStartTime = Date.now();
  try {
    // 下拉刷新不拦截：即使 loadMore/加载中也在执行一次刷新——
    // loadList 内部有 listRequestSeq 竞态防护，过期响应会被丢弃
    await loadList(true);
  } finally {
    // 最短展示时长：请求过快时补足，保证"正在刷新"可感知
    const elapsed = Date.now() - pullRefreshStartTime;
    if (elapsed < PULL_REFRESH_MIN_MS) {
      await new Promise(resolve => setTimeout(resolve, PULL_REFRESH_MIN_MS - elapsed));
    }
    isPullRefreshing.value = false;
  }
}

async function handleChooseImage() {
  try {
    const res = await uni.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'] });
    const filePath = res.tempFilePaths[0];
    if (!filePath) return;
    if (!editingId.value) {
      formModel.value.image_url = filePath;
      uni.showToast({ title: '已选择，保存后自动上传', icon: 'none' });
      return;
    }
    uni.showLoading({ title: '上传中...' });
    const uploadRes = await uploadFeaturedImage(editingId.value, filePath);
    uni.hideLoading();
    if (uploadRes.code === 200 && uploadRes.data?.image_url) {
      formModel.value.image_url = uploadRes.data.image_url;
      uni.showToast({ title: '上传成功', icon: 'success' });
    } else {
      uni.showToast({ title: '上传失败', icon: 'none' });
    }
  } catch {
    uni.hideLoading();
  }
}

/** 本地临时图片路径判定（覆盖 App/H5/小程序临时文件格式） */
function isLocalImagePath(url: string): boolean {
  const u = (url || '').trim();
  if (!u) return false;
  if (u.startsWith('http://tmp') || u.startsWith('https://tmp')) return true;
  if (u.startsWith('_doc') || u.startsWith('_unpackage') || u.startsWith('wxfile://') || u.startsWith('file://') || u.startsWith('blob:')) return true;
  if (u.includes('tmp/')) return true;
  if (!u.startsWith('http') && !u.startsWith('/media') && !u.startsWith('data:')) return true;
  return false;
}

function openCreateForm() {
  formMode.value = 'create';
  editingId.value = null;
  formModel.value = { title: '', subtitle: '', image_url: '', target_type: null, target_id: '', target_url: '', sort_order: 0, is_active: true, start_at: null, end_at: null };
  formTargetLabel.value = '无跳转';
  targetTypeValue.value = '无跳转';
  isFormVisible.value = true;
}

function openEditForm(item: FeaturedContent) {
  formMode.value = 'edit';
  editingId.value = item.id;
  formModel.value = {
    title: item.title,
    subtitle: item.subtitle || '',
    image_url: item.image_url,
    target_type: item.target_type,
    target_id: item.target_id || '',
    target_url: item.target_url || '',
    sort_order: item.sort_order,
    is_active: item.is_active,
    start_at: isoToLocalTimestamp(item.start_at),
    end_at: isoToLocalTimestamp(item.end_at),
  };
  const idx = targetTypeValues.indexOf(item.target_type);
  formTargetLabel.value = idx >= 0 ? targetTypeLabels[idx] : '无跳转';
  targetTypeValue.value = formTargetLabel.value;
  isFormVisible.value = true;
}

function closeForm() {
  isFormVisible.value = false;
}

function isValidUrlLike(value: string): boolean {
  const v = (value || '').trim();
  return /^https?:\/\//.test(v) || v.startsWith('/');
}

async function handleFormConfirm() {
  const isLocalPath = isLocalImagePath(formModel.value.image_url);
  if (!formModel.value.title.trim() || (!formModel.value.image_url.trim() && !isLocalPath)) {
    uni.showToast({ title: '标题和图片URL为必填', icon: 'none' });
    return;
  }
  if (!isLocalPath && !isValidUrlLike(formModel.value.image_url)) {
    uni.showToast({ title: '图片URL须以http(s)://或/开头', icon: 'none' });
    return;
  }
  if (formModel.value.target_type === 'external' && formModel.value.target_url.trim() && !isValidUrlLike(formModel.value.target_url)) {
    uni.showToast({ title: '外部链接须以http(s)://或/开头', icon: 'none' });
    return;
  }
  const startTs = formModel.value.start_at;
  const endTs = formModel.value.end_at;
  if (startTs && endTs && endTs < startTs) {
    uni.showToast({ title: '下线时间不能早于上线时间', icon: 'none' });
    return;
  }
  if (formMode.value === 'create' && endTs && endTs < getDefaultPickerDate()) {
    uni.showToast({ title: '下线时间不能早于今天', icon: 'none' });
    return;
  }
  isSubmitting.value = true;
  try {
    const payload: Record<string, any> = {
      title: formModel.value.title.trim(),
      image_url: isLocalPath ? '/media/placeholder.jpg' : formModel.value.image_url.trim(),
      subtitle: formModel.value.subtitle.trim() || undefined,
      target_type: formModel.value.target_type || undefined,
      sort_order: formModel.value.sort_order,
      is_active: formModel.value.is_active,
    };
    payload.start_at = formModel.value.start_at ? timestampToLocalDateISO(formModel.value.start_at, 'start') : null;
    payload.end_at = formModel.value.end_at ? timestampToLocalDateISO(formModel.value.end_at, 'end') : null;
    if (formModel.value.target_type === 'external') {
      payload.target_url = formModel.value.target_url.trim() || undefined;
    } else if (formModel.value.target_type && formModel.value.target_id.trim()) {
      payload.target_id = formModel.value.target_id.trim();
    }
    if (formMode.value === 'create') {
      const createRes: any = await createFeaturedContent(payload);
      const newId = createRes?.data?.id;
      if (isLocalPath && newId) {
        uni.showLoading({ title: '上传图片...', mask: true });
        try {
          const uploadRes = await uploadFeaturedImage(newId, formModel.value.image_url);
          if (!(uploadRes.code === 200 && uploadRes.data?.image_url)) {
            uni.showToast({ title: '图片上传失败，请编辑重新上传', icon: 'none', duration: 3000 });
          }
        } catch {
          uni.showToast({ title: '图片上传失败，请编辑重新上传', icon: 'none', duration: 3000 });
        } finally {
          uni.hideLoading();
        }
      }
      uni.showToast({ title: '创建成功', icon: 'success' });
    } else {
      await updateFeaturedContent(editingId.value!, payload);
      uni.showToast({ title: '保存成功', icon: 'success' });
    }
    closeForm();
    await loadList(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    isSubmitting.value = false;
  }
}

async function handleReplaceImage(item: FeaturedContent) {
  try {
    const res = await uni.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'] });
    const filePath = res.tempFilePaths[0];
    if (!filePath) return;
    uni.showLoading({ title: '上传中...' });
    const uploadRes = await uploadFeaturedImage(item.id, filePath);
    uni.hideLoading();
    if (uploadRes.code === 200 && uploadRes.data?.image_url) {
      uni.showToast({ title: '换图成功', icon: 'success' });
      await loadList(true);
    } else {
      uni.showToast({ title: '上传失败', icon: 'none' });
    }
  } catch {
    uni.hideLoading();
  }
}

/** 提交重新上线（含新下线时间）；endAtIso=null 表示长期有效 */
async function applyReenable(item: FeaturedContent, endAtIso: string | null) {
  if (isTogglingActive.value) return;
  isTogglingActive.value = true;
  const prevActive = item.is_active;
  item.is_active = true;
  try {
    // end_at 显式传 null 以清空过期下线时间（与表单「长期有效」口径一致）
    await updateFeaturedContent(item.id, { is_active: true, end_at: endAtIso });
    const tip = endAtIso
      ? `已上线，将于 ${isoToLocalDateStr(endAtIso) || ''} 下线`
      : '已上线，长期有效';
    uni.showToast({ title: tip, icon: 'none', duration: 2500 });
    await loadList(true);
  } catch (e: any) {
    item.is_active = prevActive;
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    isTogglingActive.value = false;
    reenableTarget.value = null;
  }
}

/** 过期项：ActionSheet 选择上线时长（操作菜单章程 → 原生 showActionSheet） */
function openReenableSheet(item: FeaturedContent) {
  reenableTarget.value = item;
  uni.showActionSheet({
    itemList: [`上线 ${REENABLE_DEFAULT_DAYS} 天`, '自定义下线时间', '长期有效'],
    success: (res) => {
      if (res.tapIndex === 0) {
        void applyReenable(item, timestampToLocalDateISO(getDatePlusDays(REENABLE_DEFAULT_DAYS), 'end'));
        return;
      }
      if (res.tapIndex === 1) {
        reenableEndAt.value = reenableDefaultEndAt.value;
        // ActionSheet 关闭动画未完成时立刻 open 易被吃掉（App/小程序）
        setTimeout(() => {
          if (!reenableEndPickerRef.value?.open) {
            reenableTarget.value = null;
            uni.showToast({ title: '日期选择打开失败，请用编辑设置下线时间', icon: 'none' });
            return;
          }
          reenableEndPickerRef.value.open();
        }, 350);
        return;
      }
      if (res.tapIndex === 2) {
        void applyReenable(item, null);
      }
    },
    fail: () => {
      reenableTarget.value = null;
    },
  });
}

function onReenableEndConfirm(e: { value?: number | string }) {
  const item = reenableTarget.value;
  if (!item) return;
  const raw = e?.value ?? reenableEndAt.value;
  const ts = typeof raw === 'number' ? raw : Number(raw);
  if (!ts || isNaN(ts)) {
    uni.showToast({ title: '请选择有效下线日期', icon: 'none' });
    return;
  }
  if (ts < getDefaultPickerDate()) {
    uni.showToast({ title: '下线时间不能早于今天', icon: 'none' });
    return;
  }
  void applyReenable(item, timestampToLocalDateISO(ts, 'end'));
}

function onReenableEndCancel() {
  reenableTarget.value = null;
}

async function handleToggleActive(item: FeaturedContent) {
  if (isTogglingActive.value) return;

  // 停用：仅翻转 is_active
  if (item.is_active) {
    isTogglingActive.value = true;
    const prevActive = item.is_active;
    item.is_active = false;
    try {
      await updateFeaturedContent(item.id, { is_active: false });
      uni.showToast({ title: '已停用', icon: 'none' });
      await loadList(true);
    } catch (e: any) {
      item.is_active = prevActive;
      uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
    } finally {
      isTogglingActive.value = false;
    }
    return;
  }

  // 已过期：必须重设下线时间，否则惰性下线会立刻翻回
  if (needsRescheduleOnEnable(item)) {
    openReenableSheet(item);
    return;
  }

  // 未过期的手动停用：时间窗仍有效，直接启用
  isTogglingActive.value = true;
  const prevActive = item.is_active;
  item.is_active = true;
  try {
    await updateFeaturedContent(item.id, { is_active: true });
    uni.showToast({ title: '已启用', icon: 'none' });
    await loadList(true);
  } catch (e: any) {
    item.is_active = prevActive;
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    isTogglingActive.value = false;
  }
}

async function handleDelete(item: FeaturedContent) {
  const { confirm } = await new Promise<{ confirm: boolean }>(resolve => {
    uni.showModal({ title: '确认永久删除', content: `确定要永久删除「${item.title}」吗？此操作不可恢复！`, confirmColor: '#dc2626', success: r => resolve(r) });
  });
  if (!confirm) return;
  try {
    await deleteFeaturedContent(item.id);
    uni.showToast({ title: '已删除', icon: 'success' });
    await loadList(true);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
  }
}

onShow(() => {
  if (!useAdminGuard()) return;
  if (!loadedOnce.value) loadList(true);
});
</script>

<style lang="scss" scoped>
.admin-page.consumer-layout {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: var(--home-bg);
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  height: 56rpx;
  padding: 0 24rpx;
  font-size: 24rpx;
  color: var(--color-text-on-primary);
  background: var(--home-primary);
  border-radius: var(--home-r-pill);
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.header-btn:active {
  opacity: 0.8;
}

.add-icon {
  font-size: 26rpx;
  font-weight: 300;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx var(--home-spacing-page);
  background-color: var(--home-bg);
  border-bottom: 1rpx solid var(--home-divider);
}

/* 胶囊：叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊）；
   高度 64rpx（管理端档，D6）；图标/清除已收进胶囊（结构归位） */
.search-capsule {
  flex: 1;
  height: 64rpx;
  box-sizing: border-box;
}

.search-icon {
  flex-shrink: 0;
  font-size: 26rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
  line-height: 1;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0;
  background: transparent;
  border: none;
  outline: none;
  font-size: 24rpx;
  box-sizing: border-box;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.search-placeholder {
  color: var(--search-placeholder);
}

.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--home-spacing-page);
  border-bottom: 1rpx solid var(--home-divider);
}

.tab-group {
  display: flex;
  flex: 1;
  min-width: 0;
  align-items: center;
}

.tab-item {
  padding: 20rpx 32rpx;
  font-size: 26rpx;
  color: var(--home-text2);
  border-bottom: 4rpx solid transparent;
  transition: all var(--transition-base);
}

.tab-item:active {
  opacity: 0.7;
}

.tab-item--active {
  color: var(--home-primary);
  border-bottom-color: var(--home-primary);
  font-weight: 600;
}

/* 内容区 Tab 面板：flex 撑满剩余高度（根容器 100vh + flex column） */
.admin-panel {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.list-scroll {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.list-inner {
  padding: 0 var(--home-spacing-page);
}

.feat-card {
  margin-bottom: 24rpx;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  overflow: hidden;
  border: 1rpx solid var(--home-divider);
  box-shadow: var(--home-shadow-card);
  transition: box-shadow var(--transition-base);
}

.feat-cover {
  width: 100%;
  height: 360rpx;
  background: var(--home-divider);
}

.feat-info {
  padding: 20rpx 24rpx 0;
}

.feat-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.feat-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-text1);
  flex: 1;
}

.status-tag {
  font-size: var(--home-tag-font);
  padding: var(--home-tag-padding-y) var(--home-tag-padding-x);
  border-radius: var(--home-tag-radius);
  flex-shrink: 0;
}

.status-tag--on {
  color: var(--home-badge-featured-text);
  background: var(--home-badge-featured-bg);
}

.status-tag--off {
  color: var(--home-text2);
  background: var(--home-action-secondary-bg);
}

.feat-subtitle {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  color: var(--home-text2);
}

.feat-meta {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 10rpx;
}

.feat-target {
  font-size: 22rpx;
  color: var(--home-primary);
}

.feat-sort {
  font-size: 22rpx;
  color: var(--home-text2);
}

.feat-times {
  display: flex;
  gap: 20rpx;
  margin-top: 6rpx;
}

.feat-time {
  font-size: 20rpx;
  color: var(--home-text2);
}

.feat-actions {
  display: flex;
  gap: 12rpx;
  padding: 16rpx 24rpx;
  border-top: 1rpx solid var(--home-divider);
  margin-top: 16rpx;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: var(--home-r-pill);
  font-size: 24rpx;
  color: var(--home-text1);
  background: var(--home-action-secondary-bg);
  transition: all var(--transition-base);
}

.action-btn:active {
  opacity: 0.7;
}

.action-btn--danger {
  color: var(--home-action-danger-text);
  background: var(--home-action-danger-bg);
}

.action-btn--image {
  color: var(--home-badge-featured-text);
  background: var(--home-badge-featured-bg);
}

.action-btn--warn {
  color: var(--home-badge-pending-text);
  background: var(--home-badge-pending-bg);
}

.load-more {
  text-align: center;
  padding: 24rpx 0 40rpx;
}

.load-more-text {
  font-size: 24rpx;
  color: var(--home-text2);
}

.placeholder-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  text-align: center;
}

.placeholder-icon {
  font-size: 72rpx;
  margin-bottom: 24rpx;
}

.placeholder-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--home-text1);
  margin-bottom: 12rpx;
}

.placeholder-desc {
  font-size: 24rpx;
  color: var(--home-text2);
}

.retry-btn {
  margin-top: 24rpx;
  height: 88rpx;
  line-height: 88rpx;
  padding: 0 48rpx;
  background: var(--home-primary);
  color: var(--color-text-on-primary);
  border-radius: var(--home-r-pill);
  font-size: 26rpx;
  transition: all var(--transition-base);
}

.retry-btn:active {
  background: var(--home-primary-hover);
}

.skeleton-card {
  margin-bottom: 24rpx;
  background: var(--home-card);
  border-radius: var(--home-r-lg);
  overflow: hidden;
}

.skeleton-img {
  width: 100%;
  height: 360rpx;
  background: var(--home-divider);
}

.skeleton-line {
  height: 20rpx;
  background: var(--home-divider);
  border-radius: 4rpx;
  margin: 20rpx 24rpx;
}

.skeleton-line--long {
  width: 60%;
  margin-bottom: 24rpx;
}

.form {
  padding: 8rpx 0;
}

.form-group {
  margin-bottom: 24rpx;
}

.form-group--switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-label {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: var(--home-text1);
  margin-bottom: 10rpx;
}

.form-group--switch .form-label {
  margin-bottom: 0;
}

.form-input {
  width: 100%;
  height: 72rpx;
  padding: 0 20rpx;
  background: var(--home-input-bg);
  border-radius: var(--home-r-md);
  font-size: 26rpx;
  box-sizing: border-box;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.form-input--grow {
  flex: 1;
}

.upload-btn {
  flex-shrink: 0;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 24rpx;
  font-size: 24rpx;
  color: var(--home-badge-featured-text);
  background: var(--home-badge-featured-bg);
  border-radius: var(--home-r-pill);
  transition: all var(--transition-base);
}

.upload-btn:active {
  opacity: 0.75;
}

.form-placeholder {
  color: var(--home-text2);
}

.form-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72rpx;
  padding: 0 20rpx;
  background: var(--home-input-bg);
  border: 1rpx solid var(--home-border);
  border-radius: var(--home-r-md);
  font-size: 26rpx;
}

.picker-arrow {
  font-size: 20rpx;
  color: var(--home-text2);
}

.time-tip {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: var(--home-text2);
}

/* 重新上线自定义日期：无布局占位，仅供 ref.open 挂载 */
.reenable-picker-anchor {
  width: 0;
  height: 0;
  overflow: hidden;
  position: absolute;
  left: -9999px;
  pointer-events: none;
}
</style>

<style lang="scss">
page {
  --wot-color-theme: var(--home-primary);
}
</style>
