<!--
 * ExpertDepartmentFormDialog - 专家科室词表创建/编辑
 * 闭环：填名称+分类 → 保存；非目标：不做同义词复杂编辑器以外的运营能力
 -->
<template>
  <view v-if="visible" class="dialog-overlay" @tap="handleClose">
    <view class="dialog-container" @tap.stop>
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '新建专家科室' : '编辑专家科室' }}</text>
        <view class="dialog-close" @tap="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <scroll-view scroll-y class="dialog-body">
        <view class="form-item">
          <view class="form-label">
            <text class="label-text">科室名称</text>
            <text class="label-required">*</text>
          </view>
          <input
            v-model="formData.name"
            class="form-input"
            placeholder="1-120 字"
            maxlength="120"
          />
          <text v-if="errors.name" class="error-text">{{ errors.name }}</text>
        </view>

        <view class="form-item">
          <view class="form-label">
            <text class="label-text">所属分类</text>
            <text class="label-required">*</text>
          </view>
          <!-- 组下新增：分类已预填，只读展示，避免再下拉选分类 -->
          <view v-if="categoryLocked" class="picker-trigger picker-trigger--readonly">
            <text class="picker-value">{{ selectedCategoryName || '已选定分类' }}</text>
          </view>
          <picker
            v-else-if="categoryOptions.length"
            :range="categoryOptions"
            range-key="name"
            :value="categoryPickerIndex"
            @change="onCategoryPick"
          >
            <view class="picker-trigger">
              <text :class="formData.category_id ? 'picker-value' : 'picker-placeholder'">
                {{ selectedCategoryName || '请选择科室分类' }}
              </text>
              <text class="arrow">▼</text>
            </view>
          </picker>
          <text v-else-if="categoryLoading" class="field-hint">分类加载中...</text>
          <text v-else class="field-hint">暂无可用分类，请先在本页「新增根分类」</text>
          <text v-if="errors.category_id" class="error-text">{{ errors.category_id }}</text>
        </view>

        <view class="form-item">
          <view class="form-label">
            <text class="label-text">同义词</text>
          </view>
          <textarea
            v-model="synonymsText"
            class="form-textarea"
            placeholder="多个用逗号或顿号分隔（可选）"
            maxlength="500"
          />
        </view>

        <view v-if="mode === 'create'" class="form-item form-row">
          <text class="label-text">创建即审核通过</text>
          <switch :checked="formData.is_verified" color="var(--color-primary)" @change="onVerifiedChange" />
        </view>

        <view v-if="mode === 'edit'" class="form-item form-row">
          <text class="label-text">启用科室</text>
          <switch :checked="formData.is_active" color="var(--color-primary)" @change="onActiveChange" />
        </view>
      </scroll-view>

      <view class="dialog-footer">
        <view class="btn-cancel" @tap="handleClose"><text>取消</text></view>
        <view class="btn-confirm" @tap="handleSubmit">
          <text>{{ saving ? '保存中...' : mode === 'create' ? '创建' : '保存' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { getCategoryList } from '@/api/categories'
import {
  createExpertDepartment,
  updateExpertDepartment
} from '@/api/expertDepartments'
import type { ExpertDepartmentItem } from '@/types/expertDepartment'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData?: ExpertDepartmentItem | null
  /** 按分类下新增时预填 */
  defaultCategoryId?: string
  /** 预填分类展示名（避免等选项加载） */
  defaultCategoryName?: string
}>()

const emit = defineEmits<{
  'update:visible': [boolean]
  success: []
}>()

const saving = ref(false)
const categoryLoading = ref(false)
const categoryOptions = ref<Array<{ id: string; name: string }>>([])
const synonymsText = ref('')
const errors = reactive({ name: '', category_id: '' })

const formData = reactive({
  name: '',
  category_id: '',
  is_verified: false,
  is_active: true
})

const categoryPickerIndex = computed(() => {
  const idx = categoryOptions.value.findIndex((c) => c.id === formData.category_id)
  return idx >= 0 ? idx : 0
})

/** 从分组「新增科室」进入时锁定所属分类 */
const categoryLocked = computed(
  () => props.mode === 'create' && Boolean(props.defaultCategoryId)
)

const selectedCategoryName = computed(() => {
  return (
    categoryOptions.value.find((c) => c.id === formData.category_id)?.name ||
    (categoryLocked.value ? props.defaultCategoryName || '' : '') ||
    ''
  )
})

function parseSynonyms(text: string): string[] {
  return text
    .split(/[,，、;；\n]/)
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 20)
}

async function ensureCategories() {
  if (categoryOptions.value.length || categoryLoading.value) return
  categoryLoading.value = true
  try {
    const resp: any = await getCategoryList(200)
    const data = resp?.data ?? resp
    const items = Array.isArray(data)
      ? data
      : Array.isArray(data?.items)
        ? data.items
        : Array.isArray(resp?.items)
          ? resp.items
          : []
    categoryOptions.value = items
      .filter((c: any) => c?.is_active !== false && c?.id && c?.name)
      .sort((a: any, b: any) => (a?.sort_order ?? 0) - (b?.sort_order ?? 0))
      .map((c: any) => ({ id: String(c.id), name: String(c.name) }))
  } catch {
    categoryOptions.value = []
  } finally {
    categoryLoading.value = false
  }
}

function resetForm() {
  formData.name = ''
  formData.category_id = ''
  formData.is_verified = false
  formData.is_active = true
  synonymsText.value = ''
  errors.name = ''
  errors.category_id = ''
}

function fillFromInitial() {
  resetForm()
  const d = props.initialData
  if (!d) {
    if (props.mode === 'create' && props.defaultCategoryId) {
      formData.category_id = props.defaultCategoryId
    }
    return
  }
  formData.name = d.name || ''
  formData.category_id = d.category_id || ''
  formData.is_verified = Boolean(d.is_verified)
  formData.is_active = d.is_active !== false
  synonymsText.value = Array.isArray(d.synonyms) ? d.synonyms.join('，') : ''
}

watch(
  () => [props.visible, props.defaultCategoryId, props.mode, props.initialData] as const,
  ([v]) => {
    if (v) {
      fillFromInitial()
      void ensureCategories()
    }
  }
)

function onCategoryPick(e: any) {
  const opt = categoryOptions.value[Number(e?.detail?.value)]
  if (opt) formData.category_id = opt.id
}

function onVerifiedChange(e: any) {
  formData.is_verified = Boolean(e?.detail?.value)
}

function onActiveChange(e: any) {
  formData.is_active = Boolean(e?.detail?.value)
}

function validate(): boolean {
  errors.name = ''
  errors.category_id = ''
  const name = formData.name.trim()
  if (!name) {
    errors.name = '请填写科室名称'
    return false
  }
  if (name.length > 120) {
    errors.name = '名称最多 120 字'
    return false
  }
  if (!formData.category_id) {
    errors.category_id = '请选择所属分类'
    return false
  }
  return true
}

function handleClose() {
  if (saving.value) return
  emit('update:visible', false)
}

async function handleSubmit() {
  if (!validate() || saving.value) return
  saving.value = true
  try {
    const synonyms = parseSynonyms(synonymsText.value)
    if (props.mode === 'create') {
      await createExpertDepartment({
        name: formData.name.trim(),
        category_id: formData.category_id,
        synonyms: synonyms.length ? synonyms : undefined,
        is_verified: formData.is_verified
      })
      uni.showToast({ title: '创建成功', icon: 'success' })
    } else if (props.initialData?.id) {
      await updateExpertDepartment(props.initialData.id, {
        name: formData.name.trim(),
        category_id: formData.category_id,
        synonyms,
        is_active: formData.is_active,
        is_verified: formData.is_verified
      })
      uni.showToast({ title: '已保存', icon: 'success' })
    }
    emit('update:visible', false)
    emit('success')
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败'), icon: 'none' })
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-container {
  width: 90%;
  max-width: 520px;
  max-height: 80vh;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.dialog-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dialog-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-icon {
  font-size: 16px;
  color: var(--color-text-secondary);
}

.dialog-body {
  flex: 1;
  max-height: 55vh;
  padding: var(--spacing-lg);
  box-sizing: border-box;
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
}

.label-text {
  font-size: 14px;
  color: var(--color-text-primary);
}

.label-required {
  color: #ff4d4f;
}

.form-input {
  width: 100%;
  height: 44px;
  line-height: 44px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  box-sizing: border-box;
  background: var(--color-bg-primary);
}

.form-textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  box-sizing: border-box;
  background: var(--color-bg-primary);
  min-height: 72px;
  line-height: 1.5;
}

.picker-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 40px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  box-sizing: border-box;
}

.picker-trigger--readonly {
  background: var(--color-bg-secondary);
}

.picker-value {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 1.4;
  word-break: break-all;
}

.picker-placeholder {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.arrow {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.field-hint,
.error-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
}

.field-hint {
  color: var(--color-text-secondary);
}

.error-text {
  color: #ff4d4f;
}

.dialog-footer {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-base);
  font-size: 15px;
}

.btn-cancel {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.btn-confirm {
  background: var(--color-primary);
  color: #fff;
}
</style>
