<!--
 * BrandAdminList - Admin 品牌管理（主体库瘦 CRUD）
 * 依据：品牌模块设计文档 Admin POST/PATCH/DELETE /admin/brands + logo
 * 入口：个人中心 → 管理功能 → 品牌管理
 * 闭环：搜/筛 → 建/改（含 Logo）→ 停用 → 列表启用
 * 非目标：本版不做专题关联；不做品牌成员 / 成员货架；不做行内关联房数（无列表字段，避免 N+1）
 -->
<template>
  <view class="page">
    <view class="page-header">
      <text class="title">品牌管理</text>
      <view class="toolbar-search">
        <view class="search-box">
          <input
            v-model="keyword"
            class="search-input"
            placeholder="搜索品牌名称"
            @confirm="handleSearch"
          />
        </view>
      </view>
      <view class="toolbar-actions">
        <view class="btn-query" @tap="handleSearch">
          <text class="btn-text">查询</text>
        </view>
        <view class="btn-add" @tap="openCreate">
          <text class="btn-text">新建</text>
        </view>
        <picker
          :range="activeOptions"
          range-key="label"
          :value="activePickerIndex"
          @change="onActiveFilterChange"
        >
          <view class="filter-picker">
            <text class="filter-picker__label">{{ activeOptions[activePickerIndex].label }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <view v-if="filtersDirty" class="btn-reset" @tap="handleResetFilters">
          <text class="btn-reset-text">重置</text>
        </view>
      </view>
    </view>

    <view v-if="!accessGranted" class="state-box">
      <text class="state-text">{{ accessMessage }}</text>
    </view>

    <view v-else-if="loading" class="state-box">
      <view class="loading-spinner" />
      <text class="state-text">加载中...</text>
    </view>

    <view v-else-if="errorMsg" class="state-box">
      <text class="state-text">{{ errorMsg }}</text>
      <view class="btn-query" @tap="fetchData">
        <text class="btn-text">重试</text>
      </view>
    </view>

    <view v-else class="list">
      <view v-if="items.length === 0" class="state-box">
        <text class="state-text">暂无品牌，点击「新建」创建</text>
      </view>
      <view
        v-for="item in items"
        :key="item.id"
        :class="['item', { 'item--inactive': !item.is_active }]"
      >
        <view class="item-row">
          <view class="item-logo">
            <image
              class="logo-img"
              :src="logoSrc(item)"
              mode="aspectFit"
              @error="onLogoError(item.id, item.logo_url)"
            />
          </view>
          <view class="item-main">
            <view class="name-row">
              <text class="name">{{ item.name }}</text>
              <text v-if="!item.is_active" class="tag tag--off">停用</text>
            </view>
            <text class="meta">
              {{ item.slug ? `标识 ${item.slug}` : '未设置标识' }}
              · 排序 {{ item.sort_order ?? 0 }}
            </text>
            <text v-if="item.description" class="meta desc">{{ item.description }}</text>
          </view>
          <view class="item-actions">
            <view class="action-btn btn-plain" @tap="openEdit(item)">
              <text>编辑</text>
            </view>
            <view
              v-if="item.is_active"
              class="action-btn btn-del"
              @tap="handleDeactivate(item)"
            >
              <text>停用</text>
            </view>
            <view v-else class="action-btn btn-enable" @tap="handleActivate(item)">
              <text>启用</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="accessGranted && total > pageSize" class="pagination">
      <view :class="['page-btn', page <= 1 ? 'disabled' : '']" @tap="changePage(page - 1)">
        <text>上一页</text>
      </view>
      <text class="page-text">{{ page }} / {{ totalPages }}</text>
      <view :class="['page-btn', page >= totalPages ? 'disabled' : '']" @tap="changePage(page + 1)">
        <text>下一页</text>
      </view>
    </view>

    <!-- 新建 / 编辑 -->
    <view v-if="formVisible" class="dialog-overlay" @tap="formVisible = false">
      <view class="dialog form-dialog" @tap.stop>
        <text class="dialog-title">{{ formMode === 'create' ? '新建品牌' : '编辑品牌' }}</text>
        <scroll-view scroll-y class="form-scroll">
          <view class="field">
            <text class="label">Logo</text>
            <view class="logo-picker" @tap="pickFormLogo">
              <image
                v-if="formLogoPreview"
                class="logo-picker__img"
                :src="formLogoPreview"
                mode="aspectFit"
              />
              <view v-else class="logo-picker__empty">
                <text>{{ formLogoUploading ? '上传中...' : '点击选择' }}</text>
              </view>
            </view>
            <text class="field-hint">
              {{ formMode === 'create' ? '创建成功后自动上传所选 Logo' : '选择后立即上传；也可下方填 URL' }}
            </text>
          </view>
          <view class="field">
            <text class="label">品牌名称 <text class="req">*</text></text>
            <input v-model="form.name" class="input" placeholder="品牌名称" maxlength="150" />
          </view>
          <view class="field">
            <text class="label">英文标识 slug</text>
            <input
              v-model="form.slug"
              class="input"
              placeholder="可选，如 weigao"
              maxlength="150"
            />
          </view>
          <view class="field">
            <text class="label">Logo 地址</text>
            <input
              v-model="form.logo_url"
              class="input"
              placeholder="可选，图片 URL（上传后会自动填入）"
              maxlength="512"
            />
          </view>
          <view class="field">
            <text class="label">官网</text>
            <input
              v-model="form.website_url"
              class="input"
              placeholder="可选，需以 http:// 或 https:// 开头"
              maxlength="255"
            />
          </view>
          <view class="field">
            <text class="label">简介</text>
            <textarea
              v-model="form.description"
              class="textarea"
              placeholder="品牌简介"
              maxlength="500"
            />
          </view>
          <view class="field">
            <text class="label">排序（数字越小越靠前）</text>
            <input
              v-model="form.sort_order"
              class="input"
              type="number"
              placeholder="0"
            />
          </view>
          <view class="field field-row">
            <text class="label">启用</text>
            <switch :checked="form.is_active" color="var(--color-primary)" @change="onActiveChange" />
          </view>
        </scroll-view>
        <view class="dialog-footer">
          <view class="btn-cancel" @tap="formVisible = false"><text>取消</text></view>
          <view class="btn-confirm" @tap="handleSaveForm">
            <text>{{ formSaving ? '保存中...' : formMode === 'create' ? '创建' : '保存' }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import {
  getAdminBrandList,
  getAdminBrandDetail,
  createBrand,
  updateBrand,
  deleteBrand,
  uploadBrandLogo
} from '@/api/brands'
import { resolveBrandLogoUrl, shouldMarkBrandLogoBroken } from '@/utils/url'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'

interface BrandRow {
  id: string
  name: string
  slug?: string
  logo_url?: string
  description?: string
  website_url?: string
  sort_order?: number
  is_active?: boolean
}

const authStore = useAuthStore()
const accessGranted = ref(false)
const accessMessage = ref('正在校验权限...')
const loading = ref(false)
const errorMsg = ref('')
const keyword = ref('')
const items = ref<BrandRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const activeOptions = [
  { label: '全部状态', value: '' as '' | 'true' | 'false' },
  { label: '已启用', value: 'true' as const },
  { label: '已停用', value: 'false' as const }
]
const activePickerIndex = ref(0)

const formVisible = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const formSaving = ref(false)
const editingId = ref('')
const formLogoUrl = ref('')
const formLogoLocal = ref('')
const formLogoUploading = ref(false)
const form = reactive({
  name: '',
  slug: '',
  logo_url: '',
  description: '',
  website_url: '',
  sort_order: '0',
  is_active: true
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const filtersDirty = computed(
  () => !!keyword.value.trim() || activePickerIndex.value !== 0
)

const formLogoPreview = computed(
  () => formLogoLocal.value || formLogoUrl.value || form.logo_url.trim() || ''
)

function ensureAdminAccess(): boolean {
  if (!authStore.isAuthenticated) {
    accessGranted.value = false
    accessMessage.value = '请先登录'
    uni.navigateTo({
      url:
        '/pages/auth/OneTapLogin?redirect=' +
        encodeURIComponent('/pages/admin/brand/BrandAdminList')
    })
    return false
  }
  if (!authStore.isAdmin) {
    accessGranted.value = false
    accessMessage.value = '权限不足：仅管理员可访问'
    setTimeout(() => uni.navigateBack(), 1200)
    return false
  }
  accessGranted.value = true
  return true
}

function extractList(res: any): { list: any[]; total: number } {
  const raw = res?.data ?? res
  const list = Array.isArray(raw)
    ? raw
    : Array.isArray(raw?.items)
      ? raw.items
      : Array.isArray(raw?.list)
        ? raw.list
        : Array.isArray(raw?.data)
          ? raw.data
          : Array.isArray(res?.items)
            ? res.items
            : []
  return {
    list,
    total: Number(raw?.total ?? res?.total ?? list.length) || 0
  }
}

function mapBrandRow(x: any): BrandRow {
  return {
    id: String(x.id || ''),
    name: String(x.name || '未命名品牌'),
    slug: x.slug ? String(x.slug) : undefined,
    logo_url: x.logo_url ? String(x.logo_url) : undefined,
    description: x.description ? String(x.description) : undefined,
    website_url: x.website_url ? String(x.website_url) : undefined,
    sort_order: Number(x.sort_order ?? 0) || 0,
    is_active: x.is_active !== false
  }
}

const brokenLogoIds = ref<Record<string, true>>({})

function logoSrc(item: BrandRow): string {
  return resolveBrandLogoUrl(item.logo_url, !!brokenLogoIds.value[item.id])
}

function onLogoError(id: string, raw?: string | null) {
  if (brokenLogoIds.value[id]) return
  if (!shouldMarkBrandLogoBroken(raw, !!brokenLogoIds.value[id])) return
  brokenLogoIds.value = { ...brokenLogoIds.value, [id]: true }
}

async function fetchData() {
  if (!accessGranted.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const kw = keyword.value.trim()
    const activeOpt = activeOptions[activePickerIndex.value]
    const params: {
      page: number
      size: number
      name?: string
      is_active?: boolean
    } = {
      page: page.value,
      size: pageSize.value,
      name: kw || undefined
    }
    if (activeOpt.value === 'true') params.is_active = true
    if (activeOpt.value === 'false') params.is_active = false

    const res: any = await getAdminBrandList(params)
    const { list, total: t } = extractList(res)
    if (res?.code != null && res.code !== 200 && !list.length) {
      errorMsg.value = res?.message || '加载失败'
      return
    }
    items.value = list.map(mapBrandRow).filter((x: BrandRow) => x.id)
    total.value = t || items.value.length
  } catch (e: any) {
    errorMsg.value = getUserFacingErrorMessage(e, '加载失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  void fetchData()
}

function onActiveFilterChange(e: any) {
  activePickerIndex.value = Number(e?.detail?.value) || 0
  page.value = 1
  void fetchData()
}

function handleResetFilters() {
  keyword.value = ''
  activePickerIndex.value = 0
  page.value = 1
  void fetchData()
}

function changePage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  void fetchData()
}

function resetForm() {
  form.name = ''
  form.slug = ''
  form.logo_url = ''
  form.description = ''
  form.website_url = ''
  form.sort_order = '0'
  form.is_active = true
  editingId.value = ''
  formLogoUrl.value = ''
  formLogoLocal.value = ''
}

function openCreate() {
  formMode.value = 'create'
  resetForm()
  formVisible.value = true
}

async function openEdit(item: BrandRow) {
  formMode.value = 'edit'
  editingId.value = item.id
  form.name = item.name || ''
  form.slug = item.slug || ''
  form.logo_url = item.logo_url || ''
  form.description = item.description || ''
  form.website_url = item.website_url || ''
  form.sort_order = String(item.sort_order ?? 0)
  form.is_active = item.is_active !== false
  formLogoUrl.value = item.logo_url || ''
  formLogoLocal.value = ''
  formVisible.value = true
  try {
    const res = await getAdminBrandDetail(item.id)
    if (res?.code === 200 && res.data) {
      const d = mapBrandRow(res.data)
      form.name = d.name || form.name
      form.slug = d.slug || ''
      form.logo_url = d.logo_url || ''
      form.description = d.description || ''
      form.website_url = d.website_url || ''
      form.sort_order = String(d.sort_order ?? 0)
      form.is_active = d.is_active !== false
      formLogoUrl.value = d.logo_url || ''
    }
  } catch {
    // 列表字段可继续编辑
  }
}

function onActiveChange(e: any) {
  form.is_active = Boolean(e?.detail?.value)
}

async function pickFormLogo() {
  if (formLogoUploading.value || formSaving.value) return
  try {
    const choose = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera']
    })
    const filePath = choose?.tempFilePaths?.[0]
    if (!filePath) return
    formLogoLocal.value = filePath
    if (formMode.value === 'edit' && editingId.value) {
      await uploadLogoForBrand(editingId.value, filePath)
    }
  } catch {
    // 用户取消选图
  }
}

async function uploadLogoForBrand(brandId: string, filePath: string, silent = false) {
  formLogoUploading.value = true
  try {
    const res = await uploadBrandLogo(brandId, filePath)
    if (res?.code !== 200) throw new Error(res?.message || 'Logo 上传失败')
    const nextUrl = String((res.data as any)?.logo_url || '').trim()
    if (nextUrl) {
      formLogoUrl.value = nextUrl
      form.logo_url = nextUrl
      formLogoLocal.value = ''
      const row = items.value.find((x) => x.id === brandId)
      if (row) row.logo_url = nextUrl
      brokenLogoIds.value = { ...brokenLogoIds.value }
      delete brokenLogoIds.value[brandId]
    }
    if (!silent) uni.showToast({ title: 'Logo 已更新', icon: 'success' })
  } catch (e: any) {
    if (!silent) {
      uni.showToast({ title: getUserFacingErrorMessage(e, 'Logo 上传失败'), icon: 'none' })
    } else {
      throw e
    }
  } finally {
    formLogoUploading.value = false
  }
}

function buildPayload() {
  const name = form.name.trim()
  const slug = form.slug.trim()
  const logo_url = (formLogoUrl.value || form.logo_url).trim()
  const description = form.description.trim()
  const website_url = form.website_url.trim()
  const sort_order = Math.max(0, parseInt(form.sort_order, 10) || 0)
  return {
    name,
    slug: slug || undefined,
    logo_url: logo_url || undefined,
    description: description || undefined,
    website_url: website_url || undefined,
    sort_order,
    is_active: form.is_active
  }
}

function validateForm(): string | null {
  if (!form.name.trim()) return '请填写品牌名称'
  const site = form.website_url.trim()
  if (site && !/^https?:\/\//i.test(site)) {
    return '官网需以 http:// 或 https:// 开头'
  }
  return null
}

async function handleSaveForm() {
  const err = validateForm()
  if (err) {
    uni.showToast({ title: err, icon: 'none' })
    return
  }
  if (formSaving.value) return
  formSaving.value = true
  try {
    const payload = buildPayload()
    if (formMode.value === 'create') {
      const res = await createBrand(payload)
      if (res?.code !== 200) throw new Error(res?.message || '保存失败')
      const newId = String((res.data as any)?.id || '').trim()
      if (newId && formLogoLocal.value) {
        try {
          await uploadLogoForBrand(newId, formLogoLocal.value, true)
        } catch (e: any) {
          uni.showToast({
            title: getUserFacingErrorMessage(e, '品牌已创建，但 Logo 上传失败'),
            icon: 'none'
          })
          formVisible.value = false
          page.value = 1
          await fetchData()
          return
        }
      }
      uni.showToast({ title: '创建成功', icon: 'success' })
      formVisible.value = false
      page.value = 1
      await fetchData()
    } else {
      const res = await updateBrand(editingId.value, payload)
      if (res?.code !== 200) throw new Error(res?.message || '保存失败')
      uni.showToast({ title: '已保存', icon: 'success' })
      formVisible.value = false
      await fetchData()
    }
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败'), icon: 'none' })
  } finally {
    formSaving.value = false
  }
}

function handleDeactivate(item: BrandRow) {
  uni.showModal({
    title: '停用品牌',
    content: `确定停用「${item.name}」？停用后 C 端不再展示该品牌，可在列表中重新启用。`,
    confirmColor: '#ff4d4f',
    success: async (r) => {
      if (!r.confirm) return
      try {
        const res = await deleteBrand(item.id)
        if (res?.code !== 200) throw new Error(res?.message || '停用失败')
        uni.showToast({ title: '已停用', icon: 'success' })
        if (items.value.length <= 1 && page.value > 1) page.value -= 1
        await fetchData()
      } catch (e: any) {
        uni.showToast({ title: getUserFacingErrorMessage(e, '停用失败'), icon: 'none' })
      }
    }
  })
}

async function handleActivate(item: BrandRow) {
  try {
    const res = await updateBrand(item.id, { is_active: true })
    if (res?.code !== 200) throw new Error(res?.message || '启用失败')
    uni.showToast({ title: '已启用', icon: 'success' })
    await fetchData()
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '启用失败'), icon: 'none' })
  }
}

onMounted(() => {
  if (ensureAdminAccess()) void fetchData()
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

.page {
  min-height: 100vh;
  background: var(--color-bg-secondary);
  padding: var(--spacing-md);
}

.page-header {
  margin-bottom: var(--spacing-sm);
}

.title {
  display: block;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
}

.toolbar-search {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-sm);
}

.search-box {
  flex: 1;
  min-width: 0;
}

.search-input {
  width: 100%;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background: var(--color-bg-primary);
  font-size: 13px;
  box-sizing: border-box;
}

.btn-query,
.btn-add {
  height: 32px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  border-radius: var(--border-radius-base);
  flex-shrink: 0;

  .btn-text {
    color: #fff;
    font-size: 13px;
  }
}

.btn-query {
  background: var(--color-primary);
}

.btn-add {
  background: #52c41a;
}

.filter-picker {
  height: 32px;
  max-width: 110px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  flex-shrink: 0;
  overflow: hidden;
}

.filter-picker__label {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-arrow {
  font-size: 10px;
  color: var(--color-text-tertiary, var(--color-text-secondary));
  flex-shrink: 0;
}

.btn-reset {
  height: 32px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  background: var(--color-bg-primary);
}

.btn-reset-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: 60px 0;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
}

.state-text {
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.item {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
}

.item--inactive {
  opacity: 0.72;
}

.item-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.item-logo {
  width: 44px;
  height: 44px;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  width: 100%;
  height: 100%;
}

.item-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.name {
  font-size: 15px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag {
  flex-shrink: 0;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
}

.tag--off {
  background: #f5f5f5;
  color: var(--color-text-secondary);
}

.meta {
  font-size: 12px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

.desc {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
}

.item-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  flex-shrink: 0;
}

.action-btn {
  height: 28px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-sm);
  font-size: 12px;
  border: 1px solid var(--color-border);
}

.btn-plain {
  background: transparent;
  color: var(--color-text-secondary);
}

.btn-del {
  background: #fff2f0;
  border-color: #ffccc7;
  color: #ff4d4f;
}

.btn-enable {
  background: #f6ffed;
  border-color: #b7eb8f;
  color: #389e0d;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.page-btn {
  height: 32px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;

  &.disabled {
    opacity: 0.5;
  }
}

.page-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-lg);
}

.dialog {
  width: 100%;
  max-width: 480px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
}

.form-dialog {
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.form-scroll {
  max-height: 55vh;
  margin: 12px 0;
}

.dialog-title {
  display: block;
  font-size: 17px;
  font-weight: 600;
}

.field {
  margin-bottom: 12px;
}

.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-tertiary, var(--color-text-secondary));
}

.label {
  display: block;
  font-size: 13px;
  margin-bottom: 6px;
  color: var(--color-text-secondary);
}

.req {
  color: #ff4d4f;
}

.logo-picker {
  width: 72px;
  height: 72px;
  border-radius: var(--border-radius-sm);
  border: 1px dashed var(--color-border);
  background: var(--color-bg-secondary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-picker__img {
  width: 100%;
  height: 100%;
}

.logo-picker__empty {
  padding: 8px;
  text-align: center;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  box-sizing: border-box;
}

.textarea {
  width: 100%;
  min-height: 72px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  box-sizing: border-box;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.btn-cancel,
.btn-confirm {
  height: 36px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  border-radius: var(--border-radius-base);
  font-size: 14px;
}

.btn-cancel {
  background: var(--color-bg-secondary);
}

.btn-confirm {
  background: var(--color-primary);
  color: #fff;
}
</style>
