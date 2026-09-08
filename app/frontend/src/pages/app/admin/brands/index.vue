<template>
  <view class="admin-page consumer-layout">
    <!-- 状态 Tab + 新建按钮 -->
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
          <text>新建品牌</text>
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
          placeholder="搜索品牌名称"
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
    <scroll-view class="content-scroll" scroll-y @scrolltolower="loadMore">
      <view v-if="isLoading && brands.length === 0" class="state-box">
        <text class="state-text">加载中...</text>
      </view>

      <view v-else-if="brands.length === 0" class="state-box">
        <text class="state-text">{{ searchKeyword ? '未找到匹配的品牌' : '暂无品牌，点击「新建品牌」创建' }}</text>
      </view>

      <view v-else class="brand-list">
        <view v-for="item in brands" :key="item.id" class="brand-item">
          <view class="brand-main">
            <view class="name-row">
              <ProxyImage
                :src="item.logo_url || DEFAULT_BRAND_LOGO"
                :fallback="DEFAULT_BRAND_LOGO"
                mode="aspectFill"
                class="logo"
              />
              <text class="name">{{ item.name }}</text>
              <text :class="['status-tag', item.is_active ? 'status-active' : 'status-inactive']">
                {{ item.is_active ? '已启用' : '已停用' }}
              </text>
            </view>
            <text class="meta">
              {{ item.slug ? `标识 ${item.slug}` : '未设置标识' }} · 排序 {{ item.sort_order ?? 0 }}
            </text>
            <text v-if="item.description" class="desc">{{ item.description }}</text>
          </view>
          <view class="brand-actions">
            <view v-if="!item.is_active" class="action-btn action-btn--active" @tap="handleEnable(item)">
              <text>启用</text>
            </view>
            <view class="action-btn" @tap="openEditForm(item)">
              <text>编辑</text>
            </view>
            <view v-if="item.is_active" class="action-btn action-btn--danger" @tap="handleDelete(item)">
              <text>停用</text>
            </view>
          </view>
        </view>
        <view v-if="!hasMore && brands.length > 0" class="no-more"><text>没有更多了</text></view>
      </view>
    </scroll-view>

    <!-- 新建/编辑弹窗 -->
    <ModalDialog
      :visible="isFormVisible"
      :title="formMode === 'create' ? '新建品牌' : '编辑品牌'"
      :confirmText="formMode === 'create' ? '创建' : '保存'"
      :confirmLoading="isSubmitting"
      @update:visible="isFormVisible = $event"
      @confirm="handleFormConfirm"
      @cancel="closeForm"
    >
      <view class="form">
        <!-- Logo：预览 + 上传 / URL（新建与编辑统一） -->
        <view class="form-group">
          <text class="form-label">Logo</text>
          <view class="logo-field">
            <ProxyImage
              :src="formModel.logo_url || DEFAULT_BRAND_LOGO"
              :fallback="DEFAULT_BRAND_LOGO"
              mode="aspectFill"
              class="logo-preview"
            />
            <view class="logo-upload-btn" @tap="handleUploadLogo">
              <text class="logo-upload-text">上传图片</text>
            </view>
          </view>
          <input
            class="form-input"
            v-model="formModel.logo_url"
            placeholder="或输入 Logo 图片 URL"
            placeholder-class="form-placeholder"
          />
        </view>

        <view class="form-group">
          <text class="form-label">品牌名称 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="formModel.name"
            placeholder="请输入品牌名称"
            placeholder-class="form-placeholder"
            maxlength="150"
          />
        </view>

        <view class="form-group">
          <text class="form-label">英文标识 slug</text>
          <input
            class="form-input"
            v-model="formModel.slug"
            placeholder="可选，如 weigao"
            placeholder-class="form-placeholder"
            maxlength="150"
          />
        </view>

        <view class="form-group">
          <text class="form-label">官网</text>
          <input
            class="form-input"
            v-model="formModel.website_url"
            placeholder="可选，需以 http:// 或 https:// 开头"
            placeholder-class="form-placeholder"
            maxlength="255"
          />
        </view>

        <view class="form-group">
          <text class="form-label">简介</text>
          <textarea
            class="form-textarea"
            v-model="formModel.description"
            placeholder="品牌简介"
            placeholder-class="form-placeholder"
            maxlength="500"
          />
        </view>

        <view class="form-group">
          <text class="form-label">排序（数字越小越靠前）</text>
          <input
            class="form-input"
            v-model="formModel.sort_order"
            type="number"
            placeholder="0"
            placeholder-class="form-placeholder"
          />
        </view>

        <view class="form-group form-group--row">
          <text class="form-label">启用</text>
          <switch :checked="formModel.is_active" color="#0f766e" @change="onActiveChange" />
        </view>
      </view>
    </ModalDialog>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { getAdminBrands, createBrand, updateBrand, deleteBrand, uploadBrandLogo } from '@/api/brand';
import type { Brand, BrandCreatePayload, BrandUpdatePayload } from '@/types/brand';
import { useAdminGuard } from '@/composables/useAdminGuard';
import ProxyImage from '@/components/common/ProxyImage.vue';
import ClearButton from '@/components/app/ClearButton.vue';

/** 品牌默认 Logo（与 BrandCard / 品牌详情页兜底一致） */
const DEFAULT_BRAND_LOGO = '/static/tabbar/brand.png';

const statusTabs = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '已启用' },
  { key: 'inactive', label: '已停用' },
];
const statusIndex = ref(0);

const brands = ref<Brand[]>([]);
const page = ref(1);
const size = 20;
const total = ref(0);
const isLoading = ref(false);
const isLoadingMore = ref(false);
const loadedOnce = ref(false);
const searchKeyword = ref('');
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const hasMore = computed(() => page.value * size < total.value);

const isFormVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const isSubmitting = ref(false);
const editingId = ref('');
const formModel = ref<{
  name: string;
  slug: string;
  logo_url: string;
  description: string;
  website_url: string;
  sort_order: string;
  is_active: boolean;
}>({
  name: '',
  slug: '',
  logo_url: '',
  description: '',
  website_url: '',
  sort_order: '0',
  is_active: true,
});

onShow(() => {
  if (!useAdminGuard()) return;
  if (!loadedOnce.value) loadBrands(true);
});

function onStatusChange(idx: number) {
  statusIndex.value = idx;
  loadBrands(true);
}

function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadBrands(true), 300);
}

function clearSearch() {
  searchKeyword.value = '';
  loadBrands(true);
}

function getActiveFilter(): boolean | undefined {
  if (statusIndex.value === 0) return undefined;
  return statusIndex.value === 1;
}

/** 剔除 undefined 字段，避免 uni.request 把 undefined 序列化为空串（如 is_active=）导致后端 422 */
function cleanParams(params: Record<string, any>): Record<string, any> {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
  );
}

async function loadBrands(reset = false) {
  if (reset) {
    page.value = 1;
    total.value = 0;
    brands.value = [];
  }
  isLoading.value = true;
  try {
    const res = await getAdminBrands(
      cleanParams({
        page: page.value,
        size,
        is_active: getActiveFilter(),
        name: searchKeyword.value.trim() || undefined,
      })
    );
    const data = res.data as { items: Brand[]; total: number; page: number; size: number };
    const items = data?.items || [];
    total.value = data?.total || 0;
    brands.value = reset ? items : [...brands.value, ...items];
    loadedOnce.value = true;
  } catch (e) {
    console.error('[品牌管理] 加载失败', e);
  } finally {
    isLoading.value = false;
    isLoadingMore.value = false;
  }
}

function loadMore() {
  if (isLoadingMore.value || !hasMore.value || isLoading.value) return;
  isLoadingMore.value = true;
  page.value += 1;
  loadBrands(false);
}

// ===== 表单 =====
function resetForm() {
  formModel.value = {
    name: '',
    slug: '',
    logo_url: '',
    description: '',
    website_url: '',
    sort_order: '0',
    is_active: true,
  };
  editingId.value = '';
}

function openCreateForm() {
  formMode.value = 'create';
  resetForm();
  isFormVisible.value = true;
}

function openEditForm(item: Brand) {
  formMode.value = 'edit';
  editingId.value = item.id;
  formModel.value = {
    name: item.name,
    slug: item.slug || '',
    logo_url: item.logo_url || '',
    description: item.description || '',
    website_url: item.website_url || '',
    sort_order: String(item.sort_order ?? 0),
    is_active: item.is_active,
  };
  isFormVisible.value = true;
}

function closeForm() {
  isFormVisible.value = false;
  isSubmitting.value = false;
}

function onActiveChange(e: any) {
  formModel.value.is_active = Boolean(e?.detail?.value);
}

async function handleUploadLogo() {
  const res = await new Promise<{ path: string }>((resolve) => {
    uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (r) => resolve({ path: r.tempFilePaths[0] }),
      fail: () => resolve({ path: '' }),
    });
  });
  if (!res.path) return;

  // 新建尚未有 brandId：先本地预览，创建成功后再上传（与焦点图管理一致）
  if (!editingId.value) {
    formModel.value.logo_url = res.path;
    uni.showToast({ title: '已选择，保存后自动上传', icon: 'none' });
    return;
  }

  try {
    uni.showLoading({ title: '上传中...' });
    const resp = await uploadBrandLogo(editingId.value, res.path);
    const data = resp?.data as { logo_url?: string } | undefined;
    if (data?.logo_url) {
      formModel.value.logo_url = data.logo_url;
      uni.showToast({ title: 'Logo 已上传', icon: 'success' });
    } else {
      uni.showToast({ title: '上传响应异常', icon: 'none' });
    }
  } catch (e) {
    console.error('[品牌管理] Logo上传失败', e);
    uni.showToast({ title: '上传失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

/** 本地临时图片路径判定（覆盖 App/H5/小程序临时文件格式） */
function isLocalImagePath(url: string): boolean {
  const u = (url || '').trim();
  if (!u) return false;
  if (u.startsWith('http://tmp') || u.startsWith('https://tmp')) return true;
  if (
    u.startsWith('_doc') ||
    u.startsWith('_unpackage') ||
    u.startsWith('wxfile://') ||
    u.startsWith('file://') ||
    u.startsWith('blob:')
  ) {
    return true;
  }
  if (u.includes('tmp/')) return true;
  if (!u.startsWith('http') && !u.startsWith('/media') && !u.startsWith('/static') && !u.startsWith('data:')) {
    return true;
  }
  return false;
}

function buildPayload(): BrandCreatePayload & BrandUpdatePayload {
  const name = formModel.value.name.trim();
  const slug = formModel.value.slug.trim();
  const logo_url = formModel.value.logo_url.trim();
  const description = formModel.value.description.trim();
  const website_url = formModel.value.website_url.trim();
  const sort_order = Math.max(0, parseInt(formModel.value.sort_order, 10) || 0);
  const isLocal = isLocalImagePath(logo_url);
  return {
    name,
    ...(slug ? { slug } : {}),
    // 本地临时路径不可作为远端 URL 提交；创建后走 uploadBrandLogo
    ...(!isLocal && logo_url ? { logo_url } : {}),
    ...(description ? { description } : {}),
    ...(website_url ? { website_url } : {}),
    sort_order,
    is_active: formModel.value.is_active,
  };
}

function validateForm(): string | null {
  if (!formModel.value.name.trim()) return '请填写品牌名称';
  const site = formModel.value.website_url.trim();
  if (site && !/^https?:\/\//i.test(site)) {
    return '官网需以 http:// 或 https:// 开头';
  }
  const logo = formModel.value.logo_url.trim();
  if (logo && !isLocalImagePath(logo) && !/^https?:\/\//i.test(logo) && !logo.startsWith('/')) {
    return 'Logo URL 需以 http(s):// 或 / 开头';
  }
  return null;
}

async function handleFormConfirm() {
  const err = validateForm();
  if (err) {
    uni.showToast({ title: err, icon: 'none' });
    return;
  }
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  try {
    const localLogo = isLocalImagePath(formModel.value.logo_url) ? formModel.value.logo_url : '';
    const payload = buildPayload();
    if (formMode.value === 'create') {
      const createRes = await createBrand(payload);
      const newId = (createRes?.data as Brand | undefined)?.id;
      if (localLogo && newId) {
        uni.showLoading({ title: '上传 Logo...', mask: true });
        try {
          const uploadRes = await uploadBrandLogo(newId, localLogo);
          if (!(uploadRes?.data as { logo_url?: string } | undefined)?.logo_url) {
            uni.showToast({ title: 'Logo 上传失败，请编辑重新上传', icon: 'none', duration: 3000 });
          }
        } catch {
          uni.showToast({ title: 'Logo 上传失败，请编辑重新上传', icon: 'none', duration: 3000 });
        } finally {
          uni.hideLoading();
        }
      }
      uni.showToast({ title: '创建成功', icon: 'success' });
    } else {
      await updateBrand(editingId.value, payload);
      uni.showToast({ title: '保存成功', icon: 'success' });
    }
    closeForm();
    loadBrands(true);
  } catch (e) {
    console.error('[品牌管理] 保存失败', e);
  } finally {
    isSubmitting.value = false;
  }
}

// ===== 启停 / 软删 =====
async function handleEnable(item: Brand) {
  try {
    await updateBrand(item.id, { is_active: true });
    uni.showToast({ title: '已启用', icon: 'success' });
    loadBrands(true);
  } catch (e) {
    console.error('[品牌管理] 启用失败', e);
  }
}

async function handleDelete(item: Brand) {
  const { confirm } = await new Promise<{ confirm: boolean }>((resolve) => {
    uni.showModal({
      title: '停用品牌',
      content:
        `确定停用「${item.name}」？\n` +
        `· 停用后将不再展示该品牌及其关联内容\n` +
        `· 复开后即可恢复展示`,
      confirmColor: '#dc2626',
      success: (r) => resolve(r),
    });
  });
  if (!confirm) return;
  try {
    await deleteBrand(item.id);
    uni.showToast({ title: '已停用', icon: 'success' });
    if (brands.value.length <= 1 && page.value > 1) page.value -= 1;
    loadBrands(true);
  } catch (e) {
    console.error('[品牌管理] 停用失败', e);
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

.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
  color: #999;

  .state-text {
    font-size: 26rpx;
  }
}

.brand-list {
  padding: 16rpx 24rpx;
}

.brand-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;

  .brand-main {
    flex: 1;
    min-width: 0;
  }

  .name-row {
    display: flex;
    align-items: center;
    gap: 12rpx;
  }

  .logo {
    width: 72rpx;
    height: 72rpx;
    border-radius: 12rpx;
    flex-shrink: 0;
  }

  .name {
    font-size: 30rpx;
    font-weight: 500;
    color: #1a1a1a;
    max-width: 320rpx;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .status-tag {
    font-size: 22rpx;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;
    flex-shrink: 0;

    &.status-active {
      background: #ecfdf5;
      color: #0f766e;
    }

    &.status-inactive {
      background: #f3f4f6;
      color: #9ca3af;
    }
  }

  .meta {
    font-size: 24rpx;
    color: #999;
    margin-top: 12rpx;
    display: block;
  }

  .desc {
    font-size: 24rpx;
    color: #666;
    margin-top: 8rpx;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .brand-actions {
    display: flex;
    flex-direction: column;
    gap: 12rpx;
    margin-left: 16rpx;

    .action-btn {
      font-size: 24rpx;
      color: #0f766e;
      padding: 8rpx 16rpx;
      background: #f0fdfa;
      border-radius: 6rpx;
      text-align: center;

      &.action-btn--active {
        color: #0f766e;
        background: #ecfdf5;
      }

      &.action-btn--danger {
        color: #dc2626;
        background: #fef2f2;
      }
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

    &.form-group--row {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .form-label {
        margin-bottom: 0;
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

  .logo-field {
    display: flex;
    align-items: center;
    gap: 16rpx;
    margin-bottom: 12rpx;

    .logo-preview {
      width: 96rpx;
      height: 96rpx;
      border-radius: 12rpx;
      flex-shrink: 0;
      background: #f0f1f3;
    }

    .logo-upload-btn {
      padding: 12rpx 24rpx;
      background: #0f766e;
      border-radius: 8rpx;

      .logo-upload-text {
        font-size: 26rpx;
        color: #fff;
      }
    }
  }
}
</style>
