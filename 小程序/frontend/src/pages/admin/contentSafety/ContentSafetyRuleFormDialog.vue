<!--
 * ContentSafetyRuleFormDialog - 发布内容限制 创建/编辑
 * 编辑时同步更新同组全部位置；新建默认应用到全部位置
 -->
<template>
  <view class="dialog-overlay" v-if="visible" @click="handleClose">
    <view class="dialog-container" @click.stop>
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '新建限制词' : '编辑限制词' }}</text>
        <view class="dialog-close" @click="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <scroll-view scroll-y class="dialog-body">
        <view v-if="isStatutoryNonPolitical" class="warn-banner">
          <text>这是系统自带的词，改之前请先确认；保存后会同步到全部相关位置</text>
        </view>
        <view v-if="isPoliticalSensitive" class="warn-banner warn-banner--danger">
          <text>这类内容由系统自动处理，这里不能改</text>
        </view>
        <view v-else-if="mode === 'edit' && relatedCount > 1" class="info-banner">
          <text>保存后将同步到 {{ relatedCount }} 个位置</text>
        </view>

        <view class="form">
          <template v-if="mode === 'create'">
            <view class="form-item">
              <text class="label-text">名称</text>
              <view class="field-box">
                <input
                  v-model="createName"
                  class="form-input"
                  placeholder="起个好认的名字，如「极限词」"
                  maxlength="100"
                />
              </view>
            </view>
            <view class="form-item">
              <text class="label-text">用在哪里</text>
              <view class="field-box field-box--readonly">
                <text class="readonly-text">全部位置（讨论、搜索、直播标题等）</text>
              </view>
              <text class="form-hint">一次添加，各处一起生效</text>
            </view>
          </template>

          <template v-else-if="initialData">
            <view class="form-item">
              <text class="label-text">名称</text>
              <view class="field-box field-box--readonly">
                <text class="readonly-text">{{ editDisplayName }}</text>
              </view>
            </view>
            <view class="form-item">
              <text class="label-text">用在哪里</text>
              <view class="field-box field-box--readonly">
                <text class="readonly-text">{{ editScenesLabel }}</text>
              </view>
            </view>
          </template>

          <view class="form-item">
            <text class="label-text">不许出现的词</text>
            <view class="field-box field-box--textarea">
              <textarea
                v-model="form.pattern"
                class="form-textarea"
                :disabled="isPoliticalSensitive"
                placeholder="多个词用逗号分开，如：最,第一,顶级"
                maxlength="2000"
                :auto-height="true"
              />
            </view>
            <text class="form-hint">多个词用逗号分开即可</text>
          </view>

          <view class="form-item">
            <text class="label-text">发现后怎么做</text>
            <picker
              :range="actionOptions"
              range-key="label"
              :value="actionIndex"
              :disabled="isStatutory"
              @change="onActionChange"
            >
              <view
                class="field-box field-box--picker"
                :class="{ 'is-disabled': isStatutory }"
              >
                <text class="picker-text">
                  {{ actionOptions[actionIndex]?.label || '不让发布' }}
                </text>
                <text class="picker-arrow">▼</text>
              </view>
            </picker>
            <text v-if="isStatutory" class="form-hint">系统自带项只能选「不让发布」</text>
          </view>

          <view class="form-item form-item--row">
            <text class="label-text label-text--inline">是否开启</text>
            <switch
              :checked="form.enabled"
              :disabled="isStatutory"
              color="#2d6a5a"
              @change="form.enabled = $event.detail.value"
            />
          </view>
          <text v-if="isStatutory" class="form-hint form-hint--block">系统自带项不能关闭</text>

          <view class="form-item">
            <text class="label-text">备注（可选）</text>
            <view class="field-box field-box--textarea">
              <textarea
                v-model="form.remark"
                class="form-textarea form-textarea--sm"
                placeholder="写给自己看的说明，可留空"
                maxlength="500"
                :auto-height="true"
              />
            </view>
          </view>
        </view>
      </scroll-view>

      <view class="dialog-footer">
        <view class="footer-btn footer-btn--cancel" @click="handleClose">
          <text>取消</text>
        </view>
        <view
          class="footer-btn footer-btn--confirm"
          :class="{ 'is-loading': submitting }"
          @click="handleSubmit"
        >
          <text>{{ submitting ? '提交中...' : mode === 'create' ? '创建' : '保存' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { createContentSafetyRule, updateContentSafetyRule } from '@/api/contentSafety'
import type { ContentSafetyRule } from '@/types/contentSafety'
import { handleContentSafetyError, getUserFacingErrorMessage } from '@/utils/contentSafety'
import {
  ADMIN_ACTION_FORM_OPTIONS,
  ADMIN_ALL_SCENES,
  SCENE_DEFAULT_TARGET_FIELD,
  formatRuleTypeName,
  formatScenesSummary,
  isUserFacingText
} from '@/utils/contentSafetyDisplay'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData: ContentSafetyRule | null
  /** 同组全部位置规则；编辑时一并保存 */
  relatedRules?: ContentSafetyRule[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)
const preserveDevRemark = ref<string | null>(null)
const createName = ref('')

const actionOptions = [...ADMIN_ACTION_FORM_OPTIONS, { label: '允许发布', value: 'allow' as const }]

const form = reactive({
  pattern: '',
  action: 'block' as 'block' | 'warn' | 'allow',
  severity: 'medium' as 'low' | 'medium' | 'high' | 'critical',
  priority: 100,
  enabled: true,
  remark: ''
})

const editRules = computed(() => {
  if (props.relatedRules && props.relatedRules.length > 0) return props.relatedRules
  return props.initialData ? [props.initialData] : []
})

const relatedCount = computed(() => editRules.value.length)

const editDisplayName = computed(() => {
  if (!props.initialData) return ''
  return formatRuleTypeName(props.initialData)
})

const editScenesLabel = computed(() => {
  const scenes = editRules.value.map((r) => r.scene)
  return formatScenesSummary(scenes)
})

const isStatutory = computed(() => props.initialData?.binding_level === 'statutory')
const isPoliticalSensitive = computed(() => props.initialData?.rule_category === 'political_sensitive')
const isStatutoryNonPolitical = computed(() => isStatutory.value && !isPoliticalSensitive.value)

const actionIndex = computed(() => {
  const idx = actionOptions.findIndex((o) => o.value === form.action)
  return idx >= 0 ? idx : 0
})

watch(
  () => [props.visible, props.initialData, props.mode, props.relatedRules] as const,
  ([visible, data, mode]) => {
    if (!visible) return
    preserveDevRemark.value = null
    createName.value = ''
    if (mode === 'edit' && data) {
      form.pattern = data.pattern
      form.action = data.action
      form.severity = data.severity || 'medium'
      form.priority = data.priority ?? 100
      form.enabled = data.enabled
      if (isUserFacingText(data.remark)) {
        form.remark = data.remark || ''
      } else {
        form.remark = ''
        preserveDevRemark.value = data.remark || null
      }
    } else if (mode === 'create') {
      form.pattern = ''
      form.action = 'block'
      form.severity = 'medium'
      form.priority = 100
      form.enabled = true
      form.remark = ''
    }
  },
  { immediate: true }
)

function onActionChange(e: any) {
  const idx = Number(e?.detail?.value ?? 0)
  form.action = actionOptions[idx]?.value ?? 'block'
}

function resolveRemarkPayload(): string | undefined {
  const trimmed = form.remark.trim()
  if (trimmed) return trimmed
  if (preserveDevRemark.value) return preserveDevRemark.value
  return undefined
}

function handleClose() {
  emit('update:visible', false)
}

function slugifyName(name: string): string {
  const base = name.trim().replace(/\s+/g, '').slice(0, 40)
  return base || '自定义限制'
}

async function handleSubmit() {
  if (isPoliticalSensitive.value) {
    uni.showToast({ title: '这类内容不能改', icon: 'none' })
    return
  }

  const pattern = String(form.pattern || '').trim()
  if (!pattern) {
    uni.showToast({ title: '请填写不许出现的词', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    if (props.mode === 'create') {
      const displayName = createName.value.trim()
      if (!displayName) {
        uni.showToast({ title: '请填写名称', icon: 'none' })
        return
      }
      const slug = slugifyName(displayName)
      const userRemark = form.remark.trim() || displayName
      // 一次创建到全部常用位置
      for (let i = 0; i < ADMIN_ALL_SCENES.length; i++) {
        const scene = ADMIN_ALL_SCENES[i]
        const targetField = SCENE_DEFAULT_TARGET_FIELD[scene] || 'content'
        await createContentSafetyRule(
          {
            rule_name: `${scene}-${targetField}-${slug}`.slice(0, 100),
            scene,
            target_field: targetField,
            match_type: 'keyword',
            pattern,
            action: form.action,
            severity: 'medium',
            priority: 100,
            enabled: form.enabled,
            binding_level: 'platform',
            rule_category: 'platform_custom',
            remark: userRemark
          },
          { silent: true }
        )
      }
      uni.showToast({ title: '创建成功', icon: 'success' })
    } else if (editRules.value.length > 0) {
      const payload = {
        pattern,
        action: (isStatutory.value ? 'block' : form.action) as 'block' | 'warn' | 'allow',
        severity: form.severity || ('medium' as const),
        priority: form.priority ?? 100,
        enabled: isStatutory.value ? true : form.enabled,
        remark: resolveRemarkPayload()
      }
      for (const rule of editRules.value) {
        await updateContentSafetyRule(rule.id, payload, { silent: true })
      }
      uni.showToast({ title: '已同步保存', icon: 'success' })
    }
    emit('success')
    handleClose()
  } catch (e: any) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getUserFacingErrorMessage(e, '保存失败，请稍后再试'), icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(26, 46, 40, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 40rpx 32rpx;
  box-sizing: border-box;
}

.dialog-container {
  width: 100%;
  max-width: 680rpx;
  max-height: 86vh;
  background: #fff;
  border-radius: 24rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
  border-bottom: 1px solid #eef3f1;
  flex-shrink: 0;
}

.dialog-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a2e28;
}

.dialog-close {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12rpx;
}

.close-icon {
  font-size: 28rpx;
  color: #7a8f88;
}

.dialog-body {
  flex: 1;
  max-height: 58vh;
  padding: 24rpx 32rpx;
  box-sizing: border-box;
}

.warn-banner,
.info-banner {
  padding: 18rpx 22rpx;
  margin-bottom: 24rpx;
  border-radius: 12rpx;
  font-size: 24rpx;
  line-height: 1.5;
}

.warn-banner {
  background: #fff8ec;
  color: #b87a1a;

  &--danger {
    background: #fff1f0;
    color: #c0392b;
  }
}

.info-banner {
  background: #eef7f3;
  color: #2d6a5a;
}

.form-item {
  margin-bottom: 28rpx;

  &--row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8rpx;
  }
}

.label-text {
  display: block;
  font-size: 26rpx;
  color: #5a726a;
  margin-bottom: 12rpx;
  line-height: 1.4;

  &--inline {
    margin-bottom: 0;
  }
}

.field-box {
  width: 100%;
  box-sizing: border-box;
  background: #f7faf8;
  border: 1px solid #e4ece9;
  border-radius: 14rpx;
  padding: 0 22rpx;
  min-height: 80rpx;
  display: flex;
  align-items: center;

  &--picker {
    justify-content: space-between;
    padding-top: 20rpx;
    padding-bottom: 20rpx;
  }

  &--readonly {
    padding-top: 20rpx;
    padding-bottom: 20rpx;
    align-items: flex-start;
  }

  &--textarea {
    align-items: stretch;
    padding: 18rpx 22rpx;
    min-height: 160rpx;
  }

  &.is-disabled {
    opacity: 0.55;
  }
}

.form-input {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  font-size: 28rpx;
  color: #1a2e28;
  background: transparent;
  border: none;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  min-height: 140rpx;
  font-size: 28rpx;
  line-height: 1.55;
  color: #1a2e28;
  background: transparent;
  border: none;
  box-sizing: border-box;

  &--sm {
    min-height: 96rpx;
  }
}

.picker-text,
.readonly-text {
  flex: 1;
  font-size: 28rpx;
  color: #1a2e28;
  line-height: 1.5;
  word-break: break-all;
}

.picker-arrow {
  flex-shrink: 0;
  margin-left: 12rpx;
  font-size: 18rpx;
  color: #9aaca4;
}

.form-hint {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #9aaca4;
  line-height: 1.4;

  &--block {
    margin-bottom: 20rpx;
  }
}

.dialog-footer {
  display: flex;
  gap: 16rpx;
  padding: 20rpx 32rpx 28rpx;
  border-top: 1px solid #eef3f1;
  flex-shrink: 0;
}

.footer-btn {
  flex: 1;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14rpx;
  font-size: 28rpx;
  box-sizing: border-box;

  &--cancel {
    background: #f5f7f6;
    color: #2c3e38;
  }

  &--confirm {
    background: #2d6a5a;
    color: #fff;

    &.is-loading {
      opacity: 0.7;
    }
  }
}
</style>
