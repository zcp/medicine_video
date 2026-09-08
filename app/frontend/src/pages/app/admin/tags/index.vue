<template>
  <view class="admin-page consumer-layout">
    <!-- 状态 Tab + 新增按钮 -->
    <view class="tab-bar">
      <view class="tab-group">
        <view
          v-for="(t, idx) in statusTabs"
          :key="t.key"
          class="tab-item"
          :class="{ 'tab-item--active': statusIndex === idx }"
          @tap="onStatusChange(idx)"
        >
          <text class="tab-label">{{ t.label }}</text>
        </view>
      </view>
      <view class="tab-bar__actions">
        <view class="header-btn" @tap="openCreateForm">
          <text class="header-btn-icon iconfont icon-add"></text>
          <text>新增标签</text>
        </view>
      </view>
    </view>

    <!-- 搜索栏 -->
    <view class="filter-bar">
      <view class="app-search-field filter-search">
        <text class="filter-icon iconfont icon-search"></text>
        <input
          class="filter-input"
          v-model="searchKeyword"
          placeholder="搜索标签名称"
          placeholder-class="filter-placeholder"
          confirm-type="search"
          @confirm="handleSearch"
        />
        <!-- 清除按钮（悬浮槽：absolute 不占布局 → 显隐零变化；v1.14 最终结构） -->
        <view class="search-clear-slot">
          <ClearButton v-if="searchKeyword" @clear="clearSearch" />
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view
      class="content-scroll"
      scroll-y
      @scrolltolower="loadMore"
    >
      <view v-if="isLoading && tags.length === 0" class="loading-state">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="tags.length === 0" class="empty-state">
        <view class="placeholder-icon"><uni-icons type="folder-add" size="36" /></view>
        <text class="placeholder-text">暂无标签</text>
      </view>

      <view v-else class="tag-list">
        <view v-for="item in tags" :key="item.id" class="tag-item">
          <view class="tag-info">
            <view class="tag-name-row">
              <text class="tag-name">{{ item.name }}</text>
              <text :class="['source-tag', item.source === 'user' ? 'source-user' : 'source-admin']">
                {{ item.source === 'user' ? '用户自建' : '运营' }}
              </text>
              <text :class="['status-tag', item.is_active ? 'status-active' : 'status-inactive']">
                {{ item.is_active ? '启用' : '禁用' }}
              </text>
            </view>
            <text v-if="item.slug" class="tag-slug">slug: {{ item.slug }}</text>
            <text v-else class="tag-slug">slug: —</text>
            <text v-if="item.created_by" class="tag-slug">创建者: {{ shortId(item.created_by) }}</text>
            <text v-if="item.description" class="tag-desc">{{ item.description }}</text>
          </view>
          <view class="tag-actions">
            <view class="tag-action" @tap="toggleActive(item)">
              <text>{{ item.is_active ? '停用' : '启用' }}</text>
            </view>
            <view class="tag-action" @tap="openEditForm(item)">
              <text>编辑</text>
            </view>
          </view>
        </view>
        <view v-if="!hasMore && tags.length > 0" class="no-more"><text>没有更多了</text></view>
      </view>
    </scroll-view>

    <!-- 新增/编辑弹窗 -->
    <ModalDialog
      :visible="isFormVisible"
      :title="formMode === 'create' ? '新增标签' : '编辑标签'"
      :confirmText="formMode === 'create' ? '创建' : '保存'"
      :confirmLoading="isSubmitting"
      @update:visible="isFormVisible = $event"
      @confirm="handleFormConfirm"
      @cancel="closeForm"
    >
      <view class="form">
        <view class="form-group">
          <text class="form-label">标签名称 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="formModel.name"
            placeholder="请输入标签名称"
            placeholder-class="form-placeholder"
          />
        </view>
        <view class="form-group">
          <text class="form-label">slug（小写字母/数字/连字符）</text>
          <input
            class="form-input"
            v-model="formModel.slug"
            placeholder="例如：surgery-live"
            placeholder-class="form-placeholder"
          />
        </view>
        <view class="form-group">
          <text class="form-label">描述</text>
          <textarea
            class="form-textarea"
            v-model="formModel.description"
            placeholder="请输入标签描述（可选）"
            placeholder-class="form-placeholder"
          />
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { getAdminTags, createTag, updateTag } from '@/api/tag';
import type { Tag, TagCreatePayload, TagUpdatePayload } from '@/types/tag';
import { useAdminGuard } from '@/composables/useAdminGuard';
import ClearButton from '@/components/app/ClearButton.vue';

const statusTabs = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '已启用' },
  { key: 'inactive', label: '已禁用' },
];
const statusIndex = ref(0);

const tags = ref<Tag[]>([]);
const page = ref(1);
const size = 20;
const total = ref(0);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const loadedOnce = ref(false);
const searchKeyword = ref('');
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const hasMore = computed(() => page.value * size < total.value);

/** 剔除 undefined 字段，避免 uni.request 把 undefined 序列化为空串（如 is_active=）导致后端 422 */
function cleanParams(params: Record<string, any>): Record<string, any> {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
  );
}

const isFormVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const isSubmitting = ref(false);
const editingId = ref('');
const formModel = ref<TagCreatePayload & TagUpdatePayload>({
  name: '',
  slug: '',
  description: '',
});

onShow(() => {
  if (!useAdminGuard()) return;
  if (!loadedOnce.value) loadTags(true);
});

function onStatusChange(idx: number) {
  statusIndex.value = idx;
  loadTags(true);
}

function handleSearch() {
  loadTags(true);
}

function clearSearch() {
  searchKeyword.value = '';
  loadTags(true);
}

async function loadTags(reset = false) {
  if (reset) {
    page.value = 1;
    total.value = 0;
    tags.value = [];
  }
  isLoading.value = true;
  try {
    const isActive =
      statusIndex.value === 0 ? undefined : statusIndex.value === 1;
    const res = await getAdminTags(
      cleanParams({
        page: page.value,
        size,
        is_active: isActive,
        q: searchKeyword.value || undefined,
      })
    );
    const data = res.data as { items: Tag[]; total: number; page: number; size: number };
    const items = data?.items || [];
    total.value = data?.total || 0;
    tags.value = reset ? items : [...tags.value, ...items];
    loadedOnce.value = true;
  } catch (e) {
    // 错误提示已由 request.ts 统一处理
    console.error('[标签管理] 加载失败', e);
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
  }
}

function loadMore() {
  if (isLoadingMore.value || !hasMore.value || isLoading.value) return;
  isLoadingMore.value = true;
  page.value += 1;
  loadTags(false);
}

// ===== 表单 =====
function openCreateForm() {
  formMode.value = 'create';
  editingId.value = '';
  formModel.value = { name: '', slug: '', description: '' };
  isFormVisible.value = true;
}

function openEditForm(item: Tag) {
  formMode.value = 'edit';
  editingId.value = item.id;
  formModel.value = {
    name: item.name,
    slug: item.slug || '',
    description: item.description || '',
  };
  isFormVisible.value = true;
}

function closeForm() {
  isFormVisible.value = false;
  isSubmitting.value = false;
}

async function handleFormConfirm() {
  const name = (formModel.value.name || '').trim();
  if (!name) {
    uni.showToast({ title: '请输入标签名称', icon: 'none' });
    return;
  }
  const slug = (formModel.value.slug || '').trim().toLowerCase();
  if (slug && !/^[a-z0-9-]+$/.test(slug)) {
    uni.showToast({ title: 'slug只能包含小写字母、数字和连字符', icon: 'none' });
    return;
  }

  isSubmitting.value = true;
  try {
    const payload: TagCreatePayload & TagUpdatePayload = {
      name,
      ...(slug ? { slug } : {}),
      ...(formModel.value.description?.trim()
        ? { description: formModel.value.description.trim() }
        : {}),
    };
    if (formMode.value === 'create') {
      await createTag(payload);
      uni.showToast({ title: '创建成功', icon: 'success' });
    } else {
      await updateTag(editingId.value, payload);
      uni.showToast({ title: '保存成功', icon: 'success' });
    }
    closeForm();
    loadTags(true);
  } catch (e) {
    // 保存冲突（重名 400/4001 等）已由 request 层统一 toast 后端 message；此处仅记录，避免重复提示
    console.error('[标签管理] 保存失败', e);
  } finally {
    isSubmitting.value = false;
  }
}

/** 溯源 created_by 短 ID 展示（前 8 位；不做用户名映射，避免引入用户查询耦合） */
function shortId(id: string): string {
  return (id || '').slice(0, 8);
}

// ===== 启停（软删语义：停用即不出现在公开联想/新绑定被拒，存量关联保留） =====
async function toggleActive(item: Tag) {
  const { confirm } = await new Promise<{ confirm: boolean }>((resolve) => {
    uni.showModal({
      title: item.is_active ? '确认停用' : '确认启用',
      content: item.is_active
        ? `停用后「${item.name}」将不再出现在标签联想与场次绑定中，确定停用吗？`
        : `确定启用「${item.name}」吗？启用后立即可被联想与绑定。`,
      confirmColor: item.is_active ? '#dc2626' : '#0F766E',
      success: (r) => resolve(r),
    });
  });
  if (!confirm) return;
  try {
    await updateTag(item.id, { is_active: !item.is_active });
    uni.showToast({ title: item.is_active ? '已停用' : '已启用', icon: 'success' });
    loadTags(true);
  } catch (e) {
    // 状态切换失败（含重名校验冲突）已由 request 层 toast；此处仅记录
    console.error('[标签管理] 切换状态失败', e);
  }
}

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer);
});
</script>

<style lang="scss" scoped>
.admin-page.consumer-layout {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #f5f6f8;
}

.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1rpx solid #eee;
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

  .header-btn {
    display: flex;
    align-items: center;
    gap: 6rpx;
    padding: 10rpx 22rpx;
    background: #0f766e;
    border-radius: 8rpx;
    color: #fff;
    font-size: 26rpx;

    .header-btn-icon {
      font-size: 24rpx;
    }
  }

  .tab-item {
    padding: 20rpx 8rpx;
    margin-right: 40rpx;
    font-size: 28rpx;
    color: #666;
    border-bottom: 4rpx solid transparent;

    &.tab-item--active {
      color: #0f766e;
      font-weight: 600;
      border-bottom-color: #0f766e;
    }
  }
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  background: #fff;

  .filter-search {
    /* 叠加共享容器 .app-search-field：白底+1rpx细边+胶囊；高度 64rpx（管理端档，D6） */
    flex: 1;
    height: 64rpx;
    box-sizing: border-box;

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
      font-size: 26rpx;
      color: #1a1a1a;
      background: transparent;
      padding-right: 56rpx; /* 恒定预留悬浮清除位（不随内容变化 → 布局恒定） */
    }

    .filter-placeholder {
      color: var(--search-placeholder);
    }
  }


}

.content-scroll {
  flex: 1;
  overflow: hidden;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
  color: #999;

  .placeholder-icon {
    margin-bottom: 16rpx;
  }

  .placeholder-text,
  .loading-text {
    font-size: 26rpx;
  }
}

.tag-list {
  padding: 16rpx 24rpx;
}

.tag-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;

  .tag-info {
    flex: 1;
    min-width: 0;
  }

  .tag-name-row {
    display: flex;
    align-items: center;
    gap: 12rpx;
  }

  .tag-name {
    font-size: 30rpx;
    font-weight: 500;
    color: #1a1a1a;
  }

  .status-tag {
    font-size: 22rpx;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;

    &.status-active {
      background: #ecfdf5;
      color: #0f766e;
    }

    &.status-inactive {
      background: #f3f4f6;
      color: #9ca3af;
    }
  }

  /* 来源徽章（V2 治理视图）：user=用户 resolve 自建（灰）；admin/缺省=运营（青绿描边） */
  .source-tag {
    font-size: 22rpx;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;
    flex-shrink: 0;

    &.source-user {
      background: #f3f4f6;
      color: #6b7280;
    }

    &.source-admin {
      border: 1rpx solid rgba(15, 118, 110, 0.4);
      color: #0f766e;
      background: transparent;
    }
  }

  .tag-slug {
    font-size: 24rpx;
    color: #999;
    margin-top: 8rpx;
  }

  .tag-desc {
    font-size: 24rpx;
    color: #666;
    margin-top: 8rpx;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .tag-actions {
    display: flex;
    flex-direction: column;
    gap: 12rpx;
    margin-left: 16rpx;

    .tag-action {
      font-size: 24rpx;
      color: #0f766e;
      padding: 8rpx 16rpx;
      background: #f0fdfa;
      border-radius: 6rpx;
      text-align: center;

    }
  }
}

.no-more {
  text-align: center;
  color: #999;
  font-size: 24rpx;
  padding: 24rpx 0;
}

.form {
  padding: 8rpx 0;

  .form-group {
    margin-bottom: 24rpx;

    .form-label {
      display: block;
      font-size: 26rpx;
      color: #333;
      margin-bottom: 12rpx;

      .form-required {
        color: #dc2626;
      }
    }

    .form-input {
      background: #f5f6f8;
      border-radius: 8rpx;
      padding: 16rpx 20rpx;
      font-size: 28rpx;
      color: #1a1a1a;
    }

    .form-textarea {
      background: #f5f6f8;
      border-radius: 8rpx;
      padding: 16rpx 20rpx;
      font-size: 28rpx;
      color: #1a1a1a;
      width: 100%;
      box-sizing: border-box;
      height: 140rpx;
    }
  }
}
</style>
