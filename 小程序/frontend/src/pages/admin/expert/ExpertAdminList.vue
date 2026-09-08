<!--
 * ExpertAdminList - Admin 专家管理（CRUD）
 * 依据：专家模块设计文档 Admin POST/PATCH/DELETE /admin/experts
 * 入口：个人中心 → 管理功能 → 专家管理
 * 非目标：本页不做「关联/更换登录账号」（入口已下线）；不做硬删（停用对标品牌）
 -->
<template>
  <view class="page">
    <view class="page-header">
      <text class="title">专家管理</text>
      <view class="toolbar-search">
        <view class="search-box">
          <input
            v-model="keyword"
            class="search-input"
            placeholder="搜索专家姓名"
            @confirm="handleSearch"
          />
        </view>
        <view class="search-box">
          <input
            v-model="hospitalKeyword"
            class="search-input"
            placeholder="筛选医院"
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
          :range="featuredOptions"
          range-key="label"
          :value="featuredPickerIndex"
          @change="onFeaturedFilterChange"
        >
          <view class="filter-picker">
            <text class="filter-picker__label">{{ featuredOptions[featuredPickerIndex].label }}</text>
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
        <text class="state-text">暂无专家，点击「新建」创建</text>
      </view>
      <view
        v-for="item in items"
        :key="item.id"
        :class="['item', { 'item--inactive': !item.is_active }]"
      >
        <view class="item-row">
          <view class="item-avatar">
            <image
              v-if="item.avatar_url"
              class="avatar-img"
              :src="item.avatar_url"
              mode="aspectFill"
            />
            <view v-else class="avatar-placeholder">
              <text class="avatar-text">{{ (item.name || '?').charAt(0) }}</text>
            </view>
          </view>
          <view class="item-main">
            <view class="name-row">
              <text class="name">{{ item.name }}</text>
              <text v-if="item.is_featured" class="tag tag--featured">荐</text>
              <text v-if="!item.is_active" class="tag tag--off">停用</text>
            </view>
            <text class="meta">
              {{
                [item.title, item.hospital, displayDepartment(item)].filter(Boolean).join(' · ') ||
                  '—'
              }}
            </text>
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
            <view v-else class="action-btn btn-muted">
              <text>已停</text>
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

    <!-- 新建 / 编辑专家资料 -->
    <view v-if="formVisible" class="dialog-overlay" @tap="formVisible = false">
      <view class="dialog form-dialog" @tap.stop>
        <text class="dialog-title">{{ formMode === 'create' ? '新建专家' : '编辑专家' }}</text>
        <scroll-view scroll-y class="form-scroll">
          <view class="field">
            <text class="label">头像</text>
            <view class="avatar-picker" @tap="pickFormAvatar">
              <image
                v-if="formAvatarPreview"
                class="avatar-picker__img"
                :src="formAvatarPreview"
                mode="aspectFill"
              />
              <view v-else class="avatar-picker__empty">
                <text>{{ formAvatarUploading ? '上传中...' : '点击选择' }}</text>
              </view>
            </view>
            <text class="field-hint">
              {{ formMode === 'create' ? '创建成功后自动上传所选头像' : '选择后立即上传' }}
            </text>
          </view>
          <view class="field">
            <text class="label">姓名 <text class="req">*</text></text>
            <input v-model="form.name" class="input" placeholder="专家姓名" maxlength="120" />
          </view>
          <view class="field">
            <text class="label">职称 <text class="req">*</text></text>
            <input v-model="form.title" class="input" placeholder="如：主任医师" maxlength="120" />
          </view>
          <view class="field">
            <text class="label">医院 <text class="req">*</text></text>
            <input v-model="form.hospital" class="input" placeholder="所属医院" maxlength="200" />
          </view>
          <view class="field">
            <text class="label">科室</text>
            <picker
              v-if="departmentOptions.length"
              :range="departmentOptions"
              range-key="label"
              :value="departmentPickerIndex"
              @change="onDepartmentPick"
            >
              <view class="picker-trigger">
                <text :class="selectedDepartmentLabel ? 'picker-value' : 'picker-placeholder'">
                  {{ selectedDepartmentLabel || '请从专家科室词表中选择' }}
                </text>
                <text class="arrow">▼</text>
              </view>
            </picker>
            <view v-else-if="departmentLoading" class="field-hint">专家科室加载中...</view>
            <view v-else class="field-hint">暂无可用词表，可下方填写文本（将走后端自适应待审）</view>
            <input
              v-model="form.department"
              class="input"
              style="margin-top: 8px"
              placeholder="或填写新科室名（不选词表时）"
              maxlength="120"
              @input="onDepartmentTextInput"
            />
            <text
              v-if="form.department_id || form.department"
              class="clear-link dept-clear"
              @tap="clearDepartment"
            >清除已选</text>
          </view>
          <view class="field">
            <text class="label">擅长领域</text>
            <textarea
              v-model="form.expertise_areas"
              class="textarea"
              placeholder="多个领域可用逗号或顿号分隔"
              maxlength="500"
            />
          </view>
          <view class="field">
            <text class="label">简介</text>
            <textarea v-model="form.bio" class="textarea" placeholder="专家简介" maxlength="1000" />
          </view>
          <view class="field field-row">
            <text class="label">首页推荐</text>
            <switch :checked="form.is_featured" color="var(--color-primary)" @change="onFeaturedChange" />
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
  getAdminExpertList,
  getExpertDetail,
  createExpert,
  updateExpert,
  deleteExpert,
  uploadAdminExpertAvatar
} from '@/api/expert'
import { listExpertDepartments } from '@/api/expertDepartments'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'

interface ExpertRow {
  id: string
  name: string
  title?: string
  hospital?: string
  department?: string
  department_id?: string
  department_name?: string
  expertise_areas?: string
  bio?: string
  avatar_url?: string
  is_featured?: boolean
  is_active?: boolean
}

const authStore = useAuthStore()
const accessGranted = ref(false)
const accessMessage = ref('正在校验权限...')
const loading = ref(false)
const errorMsg = ref('')
const keyword = ref('')
const hospitalKeyword = ref('')
const items = ref<ExpertRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const featuredOptions = [
  { label: '全部推荐', value: '' as '' | 'true' | 'false' },
  { label: '首页推荐', value: 'true' as const },
  { label: '未推荐', value: 'false' as const }
]
const featuredPickerIndex = ref(0)
const filtersDirty = computed(
  () =>
    Boolean(keyword.value.trim()) ||
    Boolean(hospitalKeyword.value.trim()) ||
    featuredPickerIndex.value !== 0
)

const formVisible = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const formSaving = ref(false)
const editingId = ref('')
const formAvatarUrl = ref('')
const formAvatarLocal = ref('')
const formAvatarUploading = ref(false)
const formAvatarPreview = computed(() => formAvatarLocal.value || formAvatarUrl.value || '')
const form = reactive({
  name: '',
  title: '',
  hospital: '',
  department: '',
  department_id: '',
  expertise_areas: '',
  bio: '',
  is_featured: false,
  is_active: true
})

const departmentOptions = ref<Array<{ id: string; name: string; label: string }>>([])
const departmentLoading = ref(false)
const selectedDepartmentLabel = computed(() => {
  if (form.department_id) {
    const hit = departmentOptions.value.find((d) => d.id === form.department_id)
    return hit?.label || form.department || '已选词表科室'
  }
  return form.department.trim()
})
const departmentPickerIndex = computed(() => {
  if (!form.department_id) return 0
  const idx = departmentOptions.value.findIndex((d) => d.id === form.department_id)
  return idx >= 0 ? idx : 0
})

function displayDepartment(item: ExpertRow): string {
  return String(item.department_name || item.department || '').trim()
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

function ensureAdminAccess(): boolean {
  if (!authStore.isAuthenticated) {
    accessGranted.value = false
    accessMessage.value = '请先登录'
    uni.navigateTo({
      url:
        '/pages/auth/OneTapLogin?redirect=' +
        encodeURIComponent('/pages/admin/expert/ExpertAdminList')
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

function mapExpertRow(x: any): ExpertRow {
  const departmentName = x.department_name ? String(x.department_name) : undefined
  const departmentText = x.department ? String(x.department) : undefined
  return {
    id: String(x.id || x.expert_id || ''),
    name: String(x.name || '未命名'),
    title: x.title ? String(x.title) : undefined,
    hospital: x.hospital ? String(x.hospital) : undefined,
    department: departmentName || departmentText,
    department_id: x.department_id ? String(x.department_id) : undefined,
    department_name: departmentName,
    expertise_areas: x.expertise_areas ? String(x.expertise_areas) : undefined,
    bio: x.bio ? String(x.bio) : undefined,
    avatar_url: x.avatar_url ? String(x.avatar_url) : undefined,
    is_featured: Boolean(x.is_featured),
    is_active: x.is_active !== false
  }
}

async function fetchData() {
  if (!accessGranted.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const featuredVal = featuredOptions[featuredPickerIndex.value]?.value
    const res = await getAdminExpertList({
      page: page.value,
      size: pageSize.value,
      name: keyword.value.trim() || undefined,
      hospital: hospitalKeyword.value.trim() || undefined,
      is_featured: featuredVal === '' ? undefined : featuredVal === 'true'
    })
    if (res?.code !== 200) {
      errorMsg.value = res?.message || '加载失败'
      return
    }
    const data: any = res.data
    const list = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
    items.value = list.map(mapExpertRow).filter((x: ExpertRow) => x.id)
    total.value = Number(data?.total) || items.value.length
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

function handleResetFilters() {
  keyword.value = ''
  hospitalKeyword.value = ''
  featuredPickerIndex.value = 0
  page.value = 1
  void fetchData()
}

function onFeaturedFilterChange(e: any) {
  featuredPickerIndex.value = Number(e?.detail?.value) || 0
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
  form.title = ''
  form.hospital = ''
  form.department = ''
  form.department_id = ''
  form.expertise_areas = ''
  form.bio = ''
  form.is_featured = false
  form.is_active = true
  editingId.value = ''
  formAvatarUrl.value = ''
  formAvatarLocal.value = ''
}

async function pickFormAvatar() {
  if (formAvatarUploading.value || formSaving.value) return
  try {
    const choose = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera']
    })
    const filePath = choose?.tempFilePaths?.[0]
    if (!filePath) return
    formAvatarLocal.value = filePath
    if (formMode.value === 'edit' && editingId.value) {
      await uploadAvatarForExpert(editingId.value, filePath)
    }
  } catch {
    // 用户取消选图
  }
}

async function uploadAvatarForExpert(expertId: string, filePath: string, silent = false) {
  formAvatarUploading.value = true
  try {
    const res = await uploadAdminExpertAvatar(expertId, filePath)
    if (res?.code !== 200) throw new Error(res?.message || '头像上传失败')
    const nextUrl = String((res.data as any)?.avatar_url || '').trim()
    if (nextUrl) {
      formAvatarUrl.value = nextUrl
      formAvatarLocal.value = ''
      const row = items.value.find((x) => x.id === expertId)
      if (row) row.avatar_url = nextUrl
    }
    if (!silent) uni.showToast({ title: '头像已更新', icon: 'success' })
  } catch (e: any) {
    if (!silent) {
      uni.showToast({ title: getUserFacingErrorMessage(e, '头像上传失败'), icon: 'none' })
    } else {
      throw e
    }
  } finally {
    formAvatarUploading.value = false
  }
}

async function ensureDepartmentsLoaded() {
  if (departmentOptions.value.length || departmentLoading.value) return
  departmentLoading.value = true
  try {
    const page = await listExpertDepartments({
      page: 1,
      size: 100,
      is_active: true
    })
    departmentOptions.value = (page.items || [])
      .filter((d) => d?.id && d?.name)
      .map((d) => {
        const name = String(d.name)
        const cat = d.category_name ? String(d.category_name) : ''
        return {
          id: String(d.id),
          name,
          label: cat ? `${name}（${cat}）` : name
        }
      })
  } catch {
    departmentOptions.value = []
  } finally {
    departmentLoading.value = false
  }
}

function onDepartmentPick(e: any) {
  const opt = departmentOptions.value[Number(e.detail.value)]
  if (!opt) return
  form.department_id = opt.id
  form.department = opt.name
}

function onDepartmentTextInput() {
  // 自由文本走后端自适应：不再绑 department_id
  form.department_id = ''
}

function clearDepartment() {
  form.department = ''
  form.department_id = ''
}

function openCreate() {
  formMode.value = 'create'
  resetForm()
  formVisible.value = true
  void ensureDepartmentsLoaded()
}

async function openEdit(item: ExpertRow) {
  formMode.value = 'edit'
  editingId.value = item.id
  // 先用列表数据填表，避免弹窗空白；再拉详情补全 bio 等字段，防止保存时误清空
  form.name = item.name || ''
  form.title = item.title || ''
  form.hospital = item.hospital || ''
  form.department_id = item.department_id || ''
  form.department = item.department_name || item.department || ''
  form.expertise_areas = item.expertise_areas || ''
  form.bio = item.bio || ''
  form.is_featured = Boolean(item.is_featured)
  form.is_active = item.is_active !== false
  formAvatarUrl.value = item.avatar_url || ''
  formAvatarLocal.value = ''
  formVisible.value = true
  void ensureDepartmentsLoaded()
  try {
    const res = await getExpertDetail(item.id)
    if (res?.code === 200 && res.data) {
      const d = mapExpertRow(res.data)
      form.name = d.name || form.name
      form.title = d.title || form.title
      form.hospital = d.hospital || form.hospital
      form.department_id = d.department_id || ''
      form.department = d.department_name || d.department || ''
      form.expertise_areas = d.expertise_areas || ''
      form.bio = d.bio || ''
      form.is_featured = Boolean(d.is_featured)
      form.is_active = d.is_active !== false
      if (d.avatar_url) formAvatarUrl.value = d.avatar_url
    }
  } catch {
    // 详情失败仍可用列表字段编辑核心信息
  }
}

function onFeaturedChange(e: any) {
  form.is_featured = Boolean(e?.detail?.value)
}

function onActiveChange(e: any) {
  form.is_active = Boolean(e?.detail?.value)
}

function buildFormPayload() {
  const name = form.name.trim()
  const title = form.title.trim()
  const hospital = form.hospital.trim()
  const department = form.department.trim()
  const department_id = form.department_id.trim()
  const expertise_areas = form.expertise_areas.trim()
  const bio = form.bio.trim()
  // 优先传 department_id；仅文本时传 department，前端不 UPSERT 词表
  const payload: Record<string, any> = {
    name,
    title,
    hospital,
    expertise_areas: expertise_areas || undefined,
    bio: bio || undefined,
    is_featured: form.is_featured,
    is_active: form.is_active
  }
  if (department_id) {
    payload.department_id = department_id
  } else if (department) {
    payload.department = department
  }
  return payload
}

function validateForm(): string | null {
  const name = form.name.trim()
  const title = form.title.trim()
  const hospital = form.hospital.trim()
  if (!name) return '请填写专家姓名'
  if (!title) return '请填写职称'
  if (!hospital) return '请填写医院'
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
    const payload = buildFormPayload()
    const res =
      formMode.value === 'create'
        ? await createExpert(payload)
        : await updateExpert(editingId.value, payload)
    if (res?.code !== 200) throw new Error(res?.message || '保存失败')

    if (formMode.value === 'create' && formAvatarLocal.value) {
      const createdId = String(res?.data?.id || res?.data?.expert_id || '').trim()
      if (createdId) {
        try {
          await uploadAvatarForExpert(createdId, formAvatarLocal.value, true)
        } catch {
          // 头像失败不阻断创建成功提示
        }
      }
    }

    uni.showToast({
      title: formMode.value === 'create' ? '创建成功' : '已保存',
      icon: 'success'
    })
    formVisible.value = false
    if (formMode.value === 'create') page.value = 1
    await fetchData()
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败'), icon: 'none' })
  } finally {
    formSaving.value = false
  }
}

function handleDeactivate(item: ExpertRow) {
  uni.showModal({
    title: '停用专家',
    content: `确定停用「${item.name}」？停用后 C 端不再展示该专家，可在编辑中重新启用。`,
    confirmColor: '#ff4d4f',
    success: async (r) => {
      if (!r.confirm) return
      try {
        const res = await deleteExpert(item.id)
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

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: var(--spacing-sm);
}

.tab {
  padding: 6px 14px;
  border-radius: 16px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.tab.is-active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
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

.item-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.item-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
}

.avatar-img {
  width: 100%;
  height: 100%;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);

  .avatar-text {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
  }
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
  flex-shrink: 0;
}

.btn-reset-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.item--inactive {
  opacity: 0.62;
}

.name-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  min-width: 0;
}

.tag {
  flex-shrink: 0;
  height: 16px;
  padding: 0 5px;
  border-radius: 3px;
  font-size: 10px;
  line-height: 16px;
}

.tag--featured {
  background: rgba(24, 144, 255, 0.12);
  color: var(--color-primary);
}

.tag--off {
  background: #f5f5f5;
  color: var(--color-text-tertiary, var(--color-text-secondary));
}

.avatar-picker {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px dashed var(--color-border);
  background: var(--color-bg-secondary);
}

.avatar-picker__img {
  width: 100%;
  height: 100%;
}

.avatar-picker__empty {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-align: center;
  padding: 4px;
  box-sizing: border-box;
}

.item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.name {
  font-size: 15px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.meta {
  font-size: 11px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  flex-shrink: 0;
}

.action-btn {
  height: 26px;
  min-width: 48px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-sm);
  font-size: 11px;
  border: 1px solid var(--color-border);
}

.btn-plain {
  background: transparent;
  color: var(--color-text-secondary);
}

.btn-ok {
  background: #f6ffed;
  border-color: #b7eb8f;
  color: #389e0d;
}

.btn-del {
  background: #fff2f0;
  border-color: #ffccc7;
  color: #ff4d4f;
}

.btn-muted {
  background: transparent;
  border-color: transparent;
  color: var(--color-text-tertiary, var(--color-text-secondary));
  pointer-events: none;
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

.label {
  display: block;
  font-size: 13px;
  margin-bottom: 6px;
  color: var(--color-text-secondary);
}

.req {
  color: #ff4d4f;
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

.clear-link {
  font-size: 13px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.dept-clear {
  display: inline-block;
  margin-top: 6px;
}

.picker-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background: var(--color-bg-primary);
  box-sizing: border-box;
}

.picker-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

.picker-placeholder {
  font-size: 14px;
  color: var(--color-text-tertiary, var(--color-text-secondary));
}

.arrow {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-left: 8px;
}

.field-hint {
  display: block;
  font-size: 12px;
  color: var(--color-text-tertiary, var(--color-text-secondary));
  line-height: 1.4;
  margin-bottom: var(--spacing-md);
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
