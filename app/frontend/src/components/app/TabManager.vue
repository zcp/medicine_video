<template>
  <view class="tab-manager">
    <!-- 标题栏 -->
    <view class="tab-manager__header">
      <text class="tab-manager__title">Tab 管理</text>
      <view class="tab-manager__add-btn" @tap="handleAdd">
        <text class="tab-manager__add-text">+ 新增Tab</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="tab-manager__state">
      <text class="tab-manager__state-text">加载Tab列表...</text>
    </view>

    <!-- 错误状态 -->
    <view v-else-if="error" class="tab-manager__state">
      <text class="tab-manager__state-text">{{ error }}</text>
      <view class="tab-manager__retry" @tap="loadTabs">
        <text class="tab-manager__retry-text">重试</text>
      </view>
    </view>

    <!-- Tab列表（数据 Tab 分区 + 内容 Tab 分区） -->
    <view v-else class="tab-manager__list">
      <!-- 数据 Tab 分区：专家/品牌/聊天（固定卡，仅启停+排序+关联数；管理按钮阶段 3 提供） -->
      <view class="tab-manager__section">
        <text class="tab-manager__section-title">直播关联 Tab</text>
        <view v-for="card in dataTabCards" :key="card.key" class="tab-manager__card">
          <!-- 排序手柄（仅记录存在时可用） -->
          <view class="tab-manager__sort">
            <view
              class="sort-btn"
              :class="{ 'sort-btn--disabled': !card.canUp }"
              @tap="handleDataTabMove(card.key, -1)"
            >
              <text class="sort-btn__text">↑</text>
            </view>
            <view
              class="sort-btn"
              :class="{ 'sort-btn--disabled': !card.canDown }"
              @tap="handleDataTabMove(card.key, 1)"
            >
              <text class="sort-btn__text">↓</text>
            </view>
          </view>

          <!-- 信息 -->
          <view class="tab-manager__info">
            <view class="tab-manager__title-row">
              <text class="tab-manager__card-title">{{ card.meta.title }}</text>
              <view :class="['tab-manager__status', card.statusClass]">
                <text class="tab-manager__status-text">{{ card.statusText }}</text>
              </view>
            </view>
            <text v-if="card.key === 'experts'" class="tab-manager__content">已关联 {{ expertCount }} 位专家</text>
            <text v-else-if="card.key === 'brands'" class="tab-manager__content">已关联 {{ brandCount }} 个品牌</text>
            <text v-else class="tab-manager__content">互动讨论（由留言驱动）</text>
          </view>

          <!-- 操作（数据 Tab：启停 + 关联管理（专家/品牌，阶段 3）） -->
          <view class="tab-manager__actions">
            <view v-if="card.tab" class="action-btn" @tap="handleToggleActive(card.tab)">
              <text class="action-btn__text">{{ card.tab.is_active ? '停用' : '启用' }}</text>
            </view>
            <view v-if="card.key === 'experts'" class="action-btn action-btn--edit" @tap="openExpertPicker">
              <text class="action-btn__text">管理专家</text>
            </view>
            <view v-if="card.key === 'brands'" class="action-btn action-btn--edit" @tap="openBrandPicker">
              <text class="action-btn__text">管理品牌</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 内容 Tab 分区：intro/自定义（现状功能保留） -->
      <view class="tab-manager__section">
        <text class="tab-manager__section-title">内容 Tab</text>
        <view v-if="contentTabs.length === 0" class="tab-manager__state">
          <text class="tab-manager__state-text">暂无内容 Tab，点击上方按钮新增</text>
        </view>
        <view v-for="(tab, index) in contentTabs" :key="tab.id" class="tab-manager__card">
          <!-- 排序手柄 -->
          <view class="tab-manager__sort">
            <view
              class="sort-btn"
              :class="{ 'sort-btn--disabled': index === 0 }"
              @tap="handleMoveUp(index)"
            >
              <text class="sort-btn__text">↑</text>
            </view>
            <view
              class="sort-btn"
              :class="{ 'sort-btn--disabled': index === contentTabs.length - 1 }"
              @tap="handleMoveDown(index)"
            >
              <text class="sort-btn__text">↓</text>
            </view>
          </view>

          <!-- Tab信息 -->
          <view class="tab-manager__info">
            <view class="tab-manager__title-row">
              <text class="tab-manager__card-title">{{ tab.title }}</text>
              <view :class="['tab-manager__status', tab.is_active ? 'status-active' : 'status-inactive']">
                <text class="tab-manager__status-text">{{ tab.is_active ? '启用' : '禁用' }}</text>
              </view>
            </view>
            <text v-if="tab.text_content" class="tab-manager__content">{{ truncateText(tab.text_content, 60) }}</text>
            <ProxyImage
              v-if="tab.image_url"
              :src="tab.image_url"
              :fallback="'/static/default-avatar.png'"
              mode="aspectFill"
              class="tab-manager__image"
            />
          </view>

          <!-- 操作按钮 -->
          <view class="tab-manager__actions">
            <view class="action-btn" @tap="handleToggleActive(tab)">
              <text class="action-btn__text">{{ tab.is_active ? '停用' : '启用' }}</text>
            </view>
            <view class="action-btn action-btn--edit" @tap="handleEdit(tab)">
              <text class="action-btn__text">编辑</text>
            </view>
            <view class="action-btn action-btn--delete" @tap="handleDelete(tab)">
              <text class="action-btn__text">删除</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 新增/编辑弹窗 -->
    <ModalDialog
      :visible="isEditDialogVisible"
      :title="editingTab ? '编辑Tab' : '新增Tab'"
      confirmText="保存"
      :confirmLoading="saving"
      @update:visible="isEditDialogVisible = $event"
      @confirm="handleSave"
      @cancel="closeEditDialog"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">标题 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.title"
            placeholder="请输入Tab标题"
            placeholder-class="form-placeholder"
            maxlength="128"
          />
        </view>

        <view class="form-group">
          <text class="form-label">内容类型</text>
          <view class="content-type-row">
            <view
              v-for="ct in contentTypes"
              :key="ct.value"
              class="content-type-chip"
              :class="{ 'content-type-chip--active': form.content_type === ct.value }"
              @tap="form.content_type = ct.value"
            >
              <text class="content-type-chip__text">{{ ct.label }}</text>
            </view>
          </view>
        </view>

        <view v-if="form.content_type !== 'image'" class="form-group">
          <text class="form-label">文字内容</text>
          <textarea
            class="form-textarea"
            v-model="form.text_content"
            placeholder="请输入文本内容"
            placeholder-class="form-placeholder"
          />
        </view>

        <view v-if="form.content_type !== 'text'" class="form-group">
          <text class="form-label">配图</text>
          <view class="image-field">
            <ProxyImage
              v-if="form.image_url"
              :src="form.image_url"
              :fallback="'/static/default-avatar.png'"
              mode="aspectFill"
              class="image-preview"
            />
            <view v-else class="image-placeholder">
              <text class="image-placeholder__text">未上传图片</text>
            </view>
            <view class="image-actions">
              <view class="ghost-btn" @tap="handlePickImage">
                <text class="ghost-btn__text">{{ uploading ? '上传中...' : '选择图片' }}</text>
              </view>
              <view v-if="form.image_url" class="ghost-btn ghost-btn--danger" @tap="handleClearImage">
                <text class="ghost-btn__text">删除图片</text>
              </view>
            </view>
          </view>
          <input
            class="form-input form-input--url"
            v-model="form.image_url"
            placeholder="或输入图片 URL"
            placeholder-class="form-placeholder"
          />
        </view>

        <view class="form-group">
          <text class="form-label">排序权重</text>
          <input
            class="form-input"
            v-model.number="form.sort_order"
            type="number"
            placeholder="0（数值越小越靠前）"
            placeholder-class="form-placeholder"
          />
        </view>

        <view class="form-group form-group--row">
          <text class="form-label">启用</text>
          <switch :checked="form.is_active" color="#0f766e" @change="onActiveChange" />
        </view>
      </view>
    </ModalDialog>

    <!-- 专家关联管理弹窗（阶段 3：服务端搜索 + 分页 + 多选 ≤5 + replace 保存）
         ⚠️ 治理例外（弹窗统一 P1.4 方向 A）：服务端搜索/分页/保存中态语义特殊，保留内联实现（不套 PickerSheet），
         动画基线已对齐（0.3s 滑入滑出 + 遮罩淡入） -->
    <view v-if="showExpertPicker" class="tab-manager__picker-mask" @click="closeExpertPicker">
      <view class="tab-manager__picker-panel" :class="{ 'is-open': expertShown }" @click.stop>
        <view class="tab-manager__picker-header">
          <text class="tab-manager__picker-title">管理专家</text>
          <text class="tab-manager__picker-close" @click="closeExpertPicker">✕</text>
        </view>
        <view class="tab-manager__picker-search">
          <view class="app-search-field tab-manager__picker-field">
            <text class="tab-manager__picker-icon iconfont icon-search"></text>
            <input
              class="tab-manager__picker-input"
              v-model="expertKeyword"
              placeholder="搜索专家（姓名/医院/科室）"
              placeholder-class="tab-manager__picker-placeholder"
              confirm-type="search"
              @input="handleExpertSearchInput"
            />
            <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
            <view class="search-clear-slot">
              <ClearButton v-if="expertKeyword" @clear="handleExpertClearSearch" />
            </view>
          </view>
        </view>
        <scroll-view class="tab-manager__picker-list" scroll-y>
          <view
            v-for="item in expertOptions"
            :key="item.id"
            class="tab-manager__picker-item"
            :class="{ 'tab-manager__picker-item--selected': isExpertSelected(item.id) }"
            @click="toggleExpert(item)"
          >
            <view class="tab-manager__picker-item-main">
              <text class="tab-manager__picker-item-name">{{ item.name }}</text>
              <text v-if="item.title || item.hospital" class="tab-manager__picker-item-sub">
                {{ [item.title, item.hospital].filter(Boolean).join(' · ') }}
              </text>
            </view>
            <text v-if="isExpertSelected(item.id)" class="tab-manager__picker-check">✓</text>
          </view>
          <view v-if="expertOptions.length === 0 && !expertLoading" class="tab-manager__picker-empty">
            未找到匹配的专家
          </view>
          <view
            v-if="expertHasMore"
            class="tab-manager__picker-more"
            @click="loadMoreExperts"
          >
            <text>{{ expertLoadingMore ? '加载中...' : '加载更多' }}</text>
          </view>
        </scroll-view>
        <view class="tab-manager__picker-footer">
          <button class="tab-manager__picker-done" :disabled="expertSaving" @click="saveExperts">
            {{ expertSaving ? '保存中...' : `完成（已选 ${selectedExperts.length}/${MAX_EXPERTS}）` }}
          </button>
        </view>
      </view>
    </view>

    <!-- 品牌关联管理弹窗（阶段 3：服务端搜索 + 多选 + replace 保存）
         ⚠️ 治理例外（弹窗统一 P1.4 方向 A）：同专家弹窗，保留内联实现，动画基线已对齐 -->
    <view v-if="showBrandPicker" class="tab-manager__picker-mask" @click="closeBrandPicker">
      <view class="tab-manager__picker-panel" :class="{ 'is-open': brandShown }" @click.stop>
        <view class="tab-manager__picker-header">
          <text class="tab-manager__picker-title">管理品牌</text>
          <text class="tab-manager__picker-close" @click="closeBrandPicker">✕</text>
        </view>
        <view class="tab-manager__picker-search">
          <view class="app-search-field tab-manager__picker-field">
            <text class="tab-manager__picker-icon iconfont icon-search"></text>
            <input
              class="tab-manager__picker-input"
              v-model="brandKeyword"
              placeholder="搜索品牌名称"
              placeholder-class="tab-manager__picker-placeholder"
              confirm-type="search"
              @input="handleBrandSearchInput"
            />
            <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
            <view class="search-clear-slot">
              <ClearButton v-if="brandKeyword" @clear="handleBrandClearSearch" />
            </view>
          </view>
        </view>
        <scroll-view class="tab-manager__picker-list" scroll-y>
          <view
            v-for="item in brandOptions"
            :key="item.id"
            class="tab-manager__picker-item"
            :class="{ 'tab-manager__picker-item--selected': isBrandSelected(item.id) }"
            @click="toggleBrand(item)"
          >
            <view class="tab-manager__picker-item-main">
              <text class="tab-manager__picker-item-name">{{ item.name }}</text>
            </view>
            <text v-if="isBrandSelected(item.id)" class="tab-manager__picker-check">✓</text>
          </view>
          <view v-if="brandOptions.length === 0 && !brandLoading" class="tab-manager__picker-empty">
            未找到匹配的品牌
          </view>
        </scroll-view>
        <view class="tab-manager__picker-footer">
          <button class="tab-manager__picker-done" :disabled="brandSaving" @click="saveBrands">
            {{ brandSaving ? '保存中...' : `完成（已选 ${selectedBrands.length}）` }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  getRoomTabList,
  createRoomTab,
  updateRoomTab,
  deleteRoomTab,
  uploadTabImage,
} from '@/api/tab';
import type { Tab, TabCreatePayload, TabUpdatePayload, TabContentType } from '@/types/tab';
import ModalDialog from '@/components/shared/ModalDialog.vue';
import ProxyImage from '@/components/common/ProxyImage.vue';
import ClearButton from '@/components/app/ClearButton.vue';
import { useSessionStore } from '@/store/session';
import { getExperts, getSessionExperts, setSessionExperts } from '@/api/expert';
import { getBrands, getRoomBrands, bindRoomBrands } from '@/api/brand';
import type { Expert } from '@/types/expert';
import type { Brand } from '@/types/brand';

const props = defineProps<{
  roomId: string;
}>();

const emit = defineEmits<{
  changed: [];
}>();

const tabs = ref<Tab[]>([]);
const loading = ref(false);
const error = ref('');

// ===== 数据 Tab（V2：experts/brands/chat 为关联驱动，仅启停+排序+关联数；管理按钮阶段 3 提供） =====
const DATA_TAB_KEYS: string[] = ['experts', 'brands', 'chat'];
const DATA_TAB_META: Record<string, { title: string }> = {
  experts: { title: '专家介绍' },
  brands: { title: '品牌介绍' },
  chat: { title: '互动讨论' },
};

const contentTabs = computed(() => tabs.value.filter(t => !DATA_TAB_KEYS.includes(t.tab_key)));
const dataTabRecords = computed(() => tabs.value.filter(t => DATA_TAB_KEYS.includes(t.tab_key)));
const dataTabRecordsSorted = computed(() =>
  [...dataTabRecords.value].sort((a, b) => a.sort_order - b.sort_order),
);

// 数据 Tab 卡片列表：有记录的按 sort_order 排列在前，无记录的"未启用"卡在后
const dataTabCards = computed(() => {
  const records = dataTabRecordsSorted.value;
  const present = records.map(r => r.tab_key);
  const missing = DATA_TAB_KEYS.filter(k => !present.includes(k));
  return [
    ...records.map((r, i) => ({
      key: r.tab_key,
      tab: r as Tab | null,
      meta: DATA_TAB_META[r.tab_key] || { title: r.title },
      canUp: i > 0,
      canDown: i < records.length - 1,
      statusClass: r.is_active ? 'status-active' : 'status-inactive',
      statusText: r.is_active ? '启用' : '停用',
    })),
    ...missing.map(k => ({
      key: k,
      tab: null as Tab | null,
      meta: DATA_TAB_META[k] || { title: k },
      canUp: false,
      canDown: false,
      statusClass: 'status-inactive',
      statusText: '未启用',
    })),
  ];
});

// 关联数量与场次维度（专家关联为场次级，取最新场次 sessions[0]）
const sessionId = ref('');
const expertCount = ref(0);
const brandCount = ref(0);

async function loadAssociations() {
  if (!props.roomId) return;
  // 品牌数（房间级）
  try {
    const brRes: any = await getRoomBrands(props.roomId);
    const raw = brRes?.data;
    const arr = Array.isArray(raw) ? raw : (raw?.brands || raw?.items || []);
    brandCount.value = Array.isArray(arr) ? arr.length : 0;
  } catch {
    brandCount.value = 0;
  }
  // 场次 + 专家数（场次级，取最新场次）
  try {
    const sessionStore = useSessionStore();
    await sessionStore.fetchSessionsByRoomId(props.roomId, { refresh: true });
    const s0 = sessionStore.sessions[0];
    if (s0?.id) {
      sessionId.value = String(s0.id);
      const exRes: any = await getSessionExperts(String(s0.id));
      const raw = exRes?.data;
      const arr = Array.isArray(raw) ? raw : (raw?.data || raw?.items || []);
      expertCount.value = Array.isArray(arr) ? arr.length : 0;
    } else {
      sessionId.value = '';
      expertCount.value = 0;
    }
  } catch {
    sessionId.value = '';
    expertCount.value = 0;
  }
}

// ===== 专家关联管理（阶段 3：服务端搜索 keyword + 分页 size≤100 + 多选 ≤20 + replace） =====
const MAX_EXPERTS = 20;
const showExpertPicker = ref(false);
/** 弹层滑入状态（P1.4 动画基线：open 后 50ms 置 true 触发滑入；close 先置 false 延迟 300ms 卸载） */
const expertShown = ref(false);
const expertKeyword = ref('');
const expertOptions = ref<Expert[]>([]);
const expertPage = ref(1);
const expertTotal = ref(0);
const expertLoading = ref(false);
const expertLoadingMore = ref(false);
const expertSaving = ref(false);
const selectedExperts = ref<Expert[]>([]);
let expertSearchTimer: ReturnType<typeof setTimeout> | null = null;

const expertHasMore = computed(() =>
  expertOptions.value.length < expertTotal.value,
);

function isExpertSelected(id: string): boolean {
  return selectedExperts.value.some(e => e.id === id);
}

async function loadExperts(reset: boolean) {
  if (expertLoading.value || expertLoadingMore.value) return;
  if (reset) {
    expertPage.value = 1;
    expertLoading.value = true;
  } else {
    expertLoadingMore.value = true;
  }
  try {
    const res = await getExperts({
      page: expertPage.value,
      size: 100,
      ...(expertKeyword.value.trim() ? { keyword: expertKeyword.value.trim() } : {}),
    } as any);
    const items = res.data?.items || [];
    expertTotal.value = res.data?.total || items.length;
    expertOptions.value = reset ? items : [...expertOptions.value, ...items];
    expertPage.value += 1;
  } catch (e) {
    console.error('[Tab管理] 加载专家失败', e);
    uni.showToast({ title: '加载专家失败', icon: 'none' });
  } finally {
    expertLoading.value = false;
    expertLoadingMore.value = false;
  }
}

function loadMoreExperts() {
  if (expertHasMore.value) void loadExperts(false);
}

function handleExpertSearchInput() {
  if (expertSearchTimer) clearTimeout(expertSearchTimer);
  expertSearchTimer = setTimeout(() => {
    void loadExperts(true);
  }, 300);
}

/** 清除专家搜索关键词（接线：清空后复用防抖搜索逻辑重新加载） */
function handleExpertClearSearch() {
  expertKeyword.value = '';
  handleExpertSearchInput();
}

async function openExpertPicker() {
  if (!sessionId.value) {
    uni.showToast({ title: '暂无场次，请先创建直播', icon: 'none' });
    return;
  }
  expertKeyword.value = '';
  expertOptions.value = [];
  expertTotal.value = 0;
  selectedExperts.value = [];
  showExpertPicker.value = true;
  expertShown.value = false;
  setTimeout(() => { expertShown.value = true; }, 50);
  // 回填已关联专家
  try {
    const res: any = await getSessionExperts(sessionId.value);
    const raw = res?.data;
    const arr = Array.isArray(raw) ? raw : (raw?.data || raw?.items || []);
    selectedExperts.value = Array.isArray(arr) ? arr : [];
  } catch (e) {
    console.warn('[Tab管理] 回填专家失败', e);
  }
  void loadExperts(true);
}

function closeExpertPicker() {
  if (expertSaving.value) return;
  expertKeyword.value = '';
  if (!expertShown.value) {
    showExpertPicker.value = false;
    return;
  }
  expertShown.value = false;
  setTimeout(() => { showExpertPicker.value = false; }, 300);
}

function toggleExpert(item: Expert) {
  const idx = selectedExperts.value.findIndex(e => e.id === item.id);
  if (idx >= 0) {
    selectedExperts.value.splice(idx, 1);
    return;
  }
  if (selectedExperts.value.length >= MAX_EXPERTS) {
    uni.showToast({ title: `最多选择 ${MAX_EXPERTS} 位专家`, icon: 'none' });
    return;
  }
  selectedExperts.value.push(item);
}

async function saveExperts() {
  if (!sessionId.value || expertSaving.value) return;
  expertSaving.value = true;
  try {
    await setSessionExperts(sessionId.value, selectedExperts.value.map((e, i) => ({
      expert_id: e.id,
      role: i === 0 ? '主讲' : '嘉宾',
      sort_order: i,
    })));
    uni.showToast({ title: '专家关联已保存', icon: 'success' });
    expertShown.value = false;
    setTimeout(() => { showExpertPicker.value = false; }, 300);
    expertKeyword.value = '';
    await loadAssociations();
    emit('changed');
  } catch (e: any) {
    console.error('[Tab管理] 保存专家失败', e);
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    expertSaving.value = false;
  }
}

// ===== 品牌关联管理（阶段 3：服务端搜索 q + 多选 + replace） =====
const showBrandPicker = ref(false);
/** 弹层滑入状态（P1.4 动画基线，同 expertShown） */
const brandShown = ref(false);
const brandKeyword = ref('');
const brandOptions = ref<Brand[]>([]);
const brandLoading = ref(false);
const brandSaving = ref(false);
const selectedBrands = ref<Brand[]>([]);
let brandSearchTimer: ReturnType<typeof setTimeout> | null = null;

function isBrandSelected(id: string): boolean {
  return selectedBrands.value.some(b => b.id === id);
}

async function loadBrands() {
  if (brandLoading.value) return;
  brandLoading.value = true;
  try {
    const res: any = await getBrands({
      limit: 500,
      ...(brandKeyword.value.trim() ? { q: brandKeyword.value.trim() } : {}),
    });
    const raw = res?.data;
    const arr = Array.isArray(raw) ? raw : (raw?.items || []);
    brandOptions.value = Array.isArray(arr) ? arr : [];
  } catch (e) {
    console.error('[Tab管理] 加载品牌失败', e);
    uni.showToast({ title: '加载品牌失败', icon: 'none' });
  } finally {
    brandLoading.value = false;
  }
}

function handleBrandSearchInput() {
  if (brandSearchTimer) clearTimeout(brandSearchTimer);
  brandSearchTimer = setTimeout(() => {
    void loadBrands();
  }, 300);
}

/** 清除品牌搜索关键词（接线：清空后复用防抖搜索逻辑重新加载） */
function handleBrandClearSearch() {
  brandKeyword.value = '';
  handleBrandSearchInput();
}

async function openBrandPicker() {
  brandKeyword.value = '';
  brandOptions.value = [];
  selectedBrands.value = [];
  showBrandPicker.value = true;
  brandShown.value = false;
  setTimeout(() => { brandShown.value = true; }, 50);
  // 回填已关联品牌
  try {
    const res: any = await getRoomBrands(props.roomId);
    const raw = res?.data;
    const arr = Array.isArray(raw) ? raw : (raw?.brands || raw?.items || []);
    selectedBrands.value = Array.isArray(arr) ? arr : [];
  } catch (e) {
    console.warn('[Tab管理] 回填品牌失败', e);
  }
  void loadBrands();
}

function closeBrandPicker() {
  if (brandSaving.value) return;
  brandKeyword.value = '';
  if (!brandShown.value) {
    showBrandPicker.value = false;
    return;
  }
  brandShown.value = false;
  setTimeout(() => { showBrandPicker.value = false; }, 300);
}

function toggleBrand(item: Brand) {
  const idx = selectedBrands.value.findIndex(b => b.id === item.id);
  if (idx >= 0) {
    selectedBrands.value.splice(idx, 1);
    return;
  }
  selectedBrands.value.push(item);
}

async function saveBrands() {
  if (brandSaving.value) return;
  brandSaving.value = true;
  try {
    await bindRoomBrands(props.roomId, selectedBrands.value.map(b => b.id));
    uni.showToast({ title: '品牌关联已保存', icon: 'success' });
    brandShown.value = false;
    setTimeout(() => { showBrandPicker.value = false; }, 300);
    brandKeyword.value = '';
    await loadAssociations();
    emit('changed');
  } catch (e: any) {
    console.error('[Tab管理] 保存品牌失败', e);
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    brandSaving.value = false;
  }
}

// 数据 Tab 排序：仅记录间相邻交换 sort_order（同区内，防跨区打乱）
async function handleDataTabMove(key: string, dir: number) {
  const records = dataTabRecordsSorted.value;
  const idx = records.findIndex(r => r.tab_key === key);
  if (idx < 0) return;
  const target = records[idx + dir];
  if (!target) return;
  try {
    await Promise.all([
      updateRoomTab(records[idx].id, { sort_order: target.sort_order }),
      updateRoomTab(target.id, { sort_order: records[idx].sort_order }),
    ]);
    uni.showToast({ title: '排序已更新', icon: 'success' });
    await loadTabs();
    emit('changed');
  } catch (e) {
    console.error('[Tab管理] 数据Tab排序失败', e);
    uni.showToast({ title: '排序失败', icon: 'none' });
  }
}

const contentTypes: { label: string; value: TabContentType }[] = [
  { label: '纯文字', value: 'text' },
  { label: '纯图片', value: 'image' },
  { label: '图文', value: 'mixed' },
];

// 弹窗状态
const isEditDialogVisible = ref(false);
const editingTab = ref<Tab | null>(null);
const saving = ref(false);
const uploading = ref(false);
const form = ref<{
  title: string;
  content_type: TabContentType;
  text_content: string;
  image_url: string;
  sort_order: number;
  is_active: boolean;
}>({
  title: '',
  content_type: 'mixed',
  text_content: '',
  image_url: '',
  sort_order: 0,
  is_active: true,
});

function truncateText(text: string, max: number): string {
  const s = String(text || '').trim();
  if (s.length <= max) return s;
  return `${s.slice(0, max)}…`;
}

async function loadTabs() {
  if (!props.roomId) return;
  loading.value = true;
  error.value = '';
  try {
    const res = await getRoomTabList(props.roomId);
    const data = res.data as any;
    tabs.value = Array.isArray(data) ? data : (data?.items || []);
    await loadAssociations();
  } catch (e: any) {
    error.value = '加载Tab列表失败';
    console.error('[Tab管理] 加载失败', e);
  } finally {
    loading.value = false;
  }
}

// ===== 新增/编辑 =====
function resetForm() {
  form.value = {
    title: '',
    content_type: 'mixed',
    text_content: '',
    image_url: '',
    sort_order: 0,
    is_active: true,
  };
}

function handleAdd() {
  editingTab.value = null;
  resetForm();
  isEditDialogVisible.value = true;
}

function handleEdit(tab: Tab) {
  editingTab.value = tab;
  form.value = {
    title: tab.title,
    content_type: tab.content_type,
    text_content: tab.text_content || '',
    image_url: tab.image_url || '',
    sort_order: tab.sort_order,
    is_active: tab.is_active,
  };
  isEditDialogVisible.value = true;
}

function closeEditDialog() {
  if (saving.value || uploading.value) return;
  isEditDialogVisible.value = false;
  editingTab.value = null;
}

function onActiveChange(e: any) {
  form.value.is_active = Boolean(e?.detail?.value);
}

async function handlePickImage() {
  if (uploading.value) return;
  const res = await new Promise<{ path: string }>((resolve) => {
    uni.chooseImage({
      count: 1,
      success: (r) => resolve({ path: r.tempFilePaths[0] }),
      fail: () => resolve({ path: '' }),
    });
  });
  if (!res.path) return;
  uploading.value = true;
  try {
    const imageUrl = await uploadTabImage(props.roomId, res.path);
    if (imageUrl) {
      form.value.image_url = imageUrl;
      uni.showToast({ title: '图片已上传', icon: 'success' });
    } else {
      uni.showToast({ title: '上传失败', icon: 'none' });
    }
  } catch (e) {
    console.error('[Tab管理] 图片上传失败', e);
    uni.showToast({ title: '上传失败', icon: 'none' });
  } finally {
    uploading.value = false;
  }
}

function handleClearImage() {
  form.value.image_url = '';
}

async function handleSave() {
  const title = form.value.title.trim();
  if (!title) {
    uni.showToast({ title: '请输入Tab标题', icon: 'none' });
    return;
  }
  if (saving.value) return;
  saving.value = true;
  try {
    if (editingTab.value) {
      // 编辑：部分更新
      const payload: TabUpdatePayload = {
        title,
        content_type: form.value.content_type,
        text_content: form.value.text_content || null,
        image_url: form.value.image_url || null,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active,
      };
      await updateRoomTab(editingTab.value.id, payload);
      uni.showToast({ title: '已保存', icon: 'success' });
    } else {
      // 新增
      const payload: TabCreatePayload = {
        tab_key: 'intro',
        title,
        content_type: form.value.content_type,
        text_content: form.value.text_content || null,
        image_url: form.value.image_url || null,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active,
      };
      await createRoomTab(props.roomId, payload);
      uni.showToast({ title: '创建成功', icon: 'success' });
    }
    isEditDialogVisible.value = false;
    editingTab.value = null;
    await loadTabs();
    emit('changed');
  } catch (e) {
    console.error('[Tab管理] 保存失败', e);
    uni.showToast({ title: '保存失败', icon: 'none' });
  } finally {
    saving.value = false;
  }
}

// ===== 启停 =====
async function handleToggleActive(tab: Tab) {
  try {
    await updateRoomTab(tab.id, { is_active: !tab.is_active });
    uni.showToast({ title: tab.is_active ? '已停用' : '已启用', icon: 'success' });
    await loadTabs();
    emit('changed');
  } catch (e) {
    console.error('[Tab管理] 切换状态失败', e);
    uni.showToast({ title: '操作失败', icon: 'none' });
  }
}

// ===== 删除 =====
function handleDelete(tab: Tab) {
  uni.showModal({
    title: '确认删除',
    content: `确定删除Tab「${tab.title}」吗？删除后不可恢复。`,
    confirmColor: '#dc2626',
    success: async (r) => {
      if (!r.confirm) return;
      try {
        await deleteRoomTab(tab.id);
        uni.showToast({ title: '已删除', icon: 'success' });
        await loadTabs();
        emit('changed');
      } catch (e) {
        console.error('[Tab管理] 删除失败', e);
        uni.showToast({ title: '删除失败', icon: 'none' });
      }
    },
  });
}

// ===== 内容 Tab 排序（上移/下移 = 交换相邻 sort_order 逐个 PATCH，限内容区内）=====
async function handleMoveUp(index: number) {
  if (index <= 0) return;
  await swapSort(index, index - 1);
}

async function handleMoveDown(index: number) {
  if (index >= contentTabs.value.length - 1) return;
  await swapSort(index, index + 1);
}

async function swapSort(from: number, to: number) {
  const list = [...contentTabs.value];
  const a = list[from];
  const b = list[to];
  if (!a || !b) return;
  try {
    // 交换 sort_order（相邻交换，各自 PATCH）
    await Promise.all([
      updateRoomTab(a.id, { sort_order: b.sort_order }),
      updateRoomTab(b.id, { sort_order: a.sort_order }),
    ]);
    uni.showToast({ title: '排序已更新', icon: 'success' });
    await loadTabs();
    emit('changed');
  } catch (e) {
    console.error('[Tab管理] 排序失败', e);
    uni.showToast({ title: '排序失败', icon: 'none' });
  }
}

// 初始化加载
if (props.roomId) {
  void loadTabs();
}

defineExpose({ loadTabs });
</script>

<style lang="scss" scoped>
.tab-manager {
  width: 100%;
}

.tab-manager__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;

  .tab-manager__title {
    font-size: 30rpx;
    font-weight: 600;
    color: var(--home-text1);
  }

  .tab-manager__add-btn {
    padding: 10rpx 22rpx;
    background: var(--home-primary);
    border-radius: var(--home-r-pill);

    .tab-manager__add-text {
      font-size: 26rpx;
      color: #fff;
    }
  }
}

.tab-manager__state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0;
  gap: 16rpx;

  .tab-manager__state-text {
    font-size: 26rpx;
    color: var(--home-tabbar-inactive);
  }

  .tab-manager__retry {
    padding: 8rpx 24rpx;
    background: var(--home-primary);
    border-radius: var(--home-r-pill);

    .tab-manager__retry-text {
      font-size: 24rpx;
      color: #fff;
    }
  }
}

.tab-manager__list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

/* 分区标题 */
.tab-manager__section {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.tab-manager__section-title {
  font-size: 26rpx;
  font-weight: 600;
  color: var(--home-text2);
  padding-left: 8rpx;
  border-left: 4rpx solid var(--home-primary);
  line-height: 1.4;
}

.tab-manager__card {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  background: var(--home-input-bg);
  border-radius: var(--home-r-md);
  padding: 16rpx;

  .tab-manager__sort {
    display: flex;
    flex-direction: column;
    gap: 8rpx;

    .sort-btn {
      width: 44rpx;
      height: 44rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--home-card);
      border-radius: var(--home-r-md);

      .sort-btn__text {
        font-size: 24rpx;
        color: var(--home-primary);
      }

      &.sort-btn--disabled {
        opacity: 0.3;
      }
    }
  }

  .tab-manager__info {
    flex: 1;
    min-width: 0;

    .tab-manager__title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12rpx;

      .tab-manager__card-title {
        font-size: 28rpx;
        font-weight: 500;
        color: var(--home-text1);
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .tab-manager__status {
        font-size: 22rpx;
        padding: 2rpx 12rpx;
        border-radius: var(--home-tag-radius);
        flex-shrink: 0;

        &.status-active {
          background: rgba(15, 118, 110, 0.08);
          color: var(--home-primary);
        }

        &.status-inactive {
          background: var(--home-card);
          color: var(--home-tabbar-inactive);
        }
      }
    }

    .tab-manager__content {
      font-size: 24rpx;
      color: var(--home-text2);
      margin-top: 8rpx;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .tab-manager__image {
      width: 100%;
      height: 140rpx;
      border-radius: 8rpx;
      margin-top: 8rpx;
      background: var(--home-card);
    }
  }

  .tab-manager__actions {
    display: flex;
    flex-direction: column;
    gap: 8rpx;
    margin-left: 8rpx;

    .action-btn {
      padding: 8rpx 16rpx;
      background: rgba(15, 118, 110, 0.08);
      border-radius: var(--home-r-pill);
      text-align: center;
      min-height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;

      .action-btn__text {
        font-size: 24rpx;
        color: var(--home-primary);
      }

      &.action-btn--edit {
        background: rgba(15, 118, 110, 0.08);
        .action-btn__text {
          color: var(--home-primary);
        }
      }

      &.action-btn--delete {
        background: var(--home-action-danger-bg);
        .action-btn__text {
          color: var(--home-action-danger-text);
        }
      }
    }
  }
}

/* 表单样式 */
.form {
  padding: 8rpx 0;

  .form-group {
    margin-bottom: 24rpx;

    .form-label {
      display: block;
      font-size: 26rpx;
      color: var(--home-text1);
      margin-bottom: 12rpx;

      .form-required {
        color: var(--color-danger);
      }
    }

    &.form-group--row {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .form-label {
        margin-bottom: 0;
      }
    }

    .form-input {
      background: var(--home-input-bg);
      border-radius: var(--home-r-md);
      padding: 16rpx 20rpx;
      font-size: 28rpx;
      color: var(--home-text1);
    }

    .form-input--url {
      margin-top: 12rpx;
      font-size: 24rpx;
    }

    .form-textarea {
      background: var(--home-input-bg);
      border-radius: var(--home-r-md);
      padding: 16rpx 20rpx;
      font-size: 28rpx;
      color: var(--home-text1);
      width: 100%;
      box-sizing: border-box;
      height: 140rpx;
    }

    .content-type-row {
      display: flex;
      gap: 12rpx;

      .content-type-chip {
        flex: 1;
        text-align: center;
        padding: 12rpx 0;
        background: var(--home-input-bg);
        border-radius: var(--home-r-pill);
        border: 1rpx solid transparent;

        .content-type-chip__text {
          font-size: 26rpx;
          color: var(--home-text2);
        }

        &.content-type-chip--active {
          background: rgba(15, 118, 110, 0.08);
          border-color: var(--home-primary);

          .content-type-chip__text {
            color: var(--home-primary);
            font-weight: 500;
          }
        }
      }
    }

    .image-field {
      .image-preview {
        width: 100%;
        height: 160rpx;
        border-radius: var(--home-r-md);
        background: var(--home-input-bg);
      }

      .image-placeholder {
        width: 100%;
        height: 160rpx;
        border-radius: var(--home-r-md);
        background: var(--home-input-bg);
        display: flex;
        align-items: center;
        justify-content: center;

        .image-placeholder__text {
          font-size: 24rpx;
          color: var(--home-tabbar-inactive);
        }
      }

      .image-actions {
        display: flex;
        gap: 12rpx;
        margin-top: 12rpx;

        .ghost-btn {
          padding: 10rpx 24rpx;
          background: var(--home-primary);
          border-radius: var(--home-r-pill);
          min-height: 56rpx;
          display: flex;
          align-items: center;
          justify-content: center;

          .ghost-btn__text {
            font-size: 24rpx;
            color: #fff;
          }

          &.ghost-btn--danger {
            background: var(--home-action-danger-bg);
            .ghost-btn__text {
              color: var(--home-action-danger-text);
            }
          }
        }
      }
    }
  }
}

/* ===== 关联管理弹窗（专家/品牌，阶段 3）=====
   P1.4 动画基线：mask 淡入 + panel 0.3s 滑入滑出（与 PickerSheet 同机制） */
.tab-manager__picker-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  z-index: 999;
  display: flex;
  align-items: flex-end;
  animation: tmPickerFadeIn 0.3s ease;
}

.tab-manager__picker-panel {
  width: 100%;
  max-height: 75vh;
  background-color: var(--home-card);
  border-radius: var(--home-r-lg) var(--home-r-lg) 0 0;
  display: flex;
  flex-direction: column;
  padding-bottom: env(safe-area-inset-bottom);
  transform: translateY(100%);
  transition: transform 0.3s ease;

  &.is-open {
    transform: translateY(0);
  }
}

@keyframes tmPickerFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.tab-manager__picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
  border-bottom: 1.5rpx solid var(--home-border);
}

.tab-manager__picker-title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
}

.tab-manager__picker-close {
  font-size: 32rpx;
  color: var(--home-tabbar-inactive);
  padding: 8rpx;
}

.tab-manager__picker-search {
  padding: 20rpx 32rpx;
}

/* 胶囊：叠加共享容器 .app-search-field（B站风格：白底+1rpx细边+胶囊）；高度 64rpx（弹层档） */
.tab-manager__picker-field {
  height: 64rpx;
  box-sizing: border-box;
}

.tab-manager__picker-icon {
  font-size: 26rpx;
  color: var(--search-icon);
  margin-right: 12rpx;
  flex-shrink: 0;
  line-height: 1;
}

.tab-manager__picker-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  background: transparent;
  border: none;
  outline: none;
  padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
}

.tab-manager__picker-placeholder {
  color: var(--search-placeholder);
}

.tab-manager__picker-list {
  flex: 1;
  max-height: 45vh;
  padding: 0 32rpx;
  box-sizing: border-box;
}

.tab-manager__picker-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 24rpx 8rpx;
  border-bottom: 1.5rpx solid var(--home-border);
  min-height: 72rpx;

  &.tab-manager__picker-item--selected .tab-manager__picker-item-name {
    color: var(--home-primary);
    font-weight: 500;
  }
}

.tab-manager__picker-item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.tab-manager__picker-item-name {
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-manager__picker-item-sub {
  font-size: 22rpx;
  color: var(--home-tabbar-inactive);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-manager__picker-check {
  font-size: 32rpx;
  color: var(--home-primary);
  flex-shrink: 0;
}

.tab-manager__picker-empty {
  padding: 48rpx 0;
  text-align: center;
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
}

.tab-manager__picker-more {
  padding: 24rpx 0;
  text-align: center;
  font-size: var(--home-fs-meta);
  color: var(--home-primary);
  min-height: 44rpx;
}

.tab-manager__picker-footer {
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
}

.tab-manager__picker-done {
  height: 88rpx;
  line-height: 88rpx;
  border-radius: var(--home-r-pill);
  background-color: var(--home-primary);
  color: #ffffff;
  font-size: var(--home-fs-section);
  font-weight: 500;
  border: none;

  &::after {
    border: none;
  }

  &[disabled] {
    opacity: 0.6;
  }
}
</style>
