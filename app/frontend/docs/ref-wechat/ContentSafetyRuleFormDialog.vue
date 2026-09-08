<!--
 * ContentSafetyRuleFormDialog - 鍙戝竷鍐呭闄愬埗 鍒涘缓/缂栬緫
 * 缂栬緫鏃跺悓姝ユ洿鏂板悓缁勫叏閮ㄤ綅缃紱鏂板缓榛樿搴旂敤鍒板叏閮ㄤ綅缃? -->
<template>
  <view class="dialog-overlay" v-if="visible" @click="handleClose">
    <view class="dialog-container" @click.stop>
      <view class="dialog-header">
        <text class="dialog-title">{{ mode === 'create' ? '鏂板缓闄愬埗璇? : '缂栬緫闄愬埗璇? }}</text>
        <view class="dialog-close" @click="handleClose">
          <text class="close-icon">鉁?/text>
        </view>
      </view>

      <scroll-view scroll-y class="dialog-body">
        <view v-if="isStatutoryNonPolitical" class="warn-banner">
          <text>杩欐槸绯荤粺鑷甫鐨勮瘝锛屾敼涔嬪墠璇峰厛纭锛涗繚瀛樺悗浼氬悓姝ュ埌鍏ㄩ儴鐩稿叧浣嶇疆</text>
        </view>
        <view v-if="isPoliticalSensitive" class="warn-banner warn-banner--danger">
          <text>杩欑被鍐呭鐢辩郴缁熻嚜鍔ㄥ鐞嗭紝杩欓噷涓嶈兘鏀?/text>
        </view>
        <view v-else-if="mode === 'edit' && relatedCount > 1" class="info-banner">
          <text>淇濆瓨鍚庡皢鍚屾鍒?{{ relatedCount }} 涓綅缃?/text>
        </view>

        <view class="form">
          <template v-if="mode === 'create'">
            <view class="form-item">
              <text class="label-text">鍚嶇О</text>
              <view class="field-box">
                <input
                  v-model="createName"
                  class="form-input"
                  placeholder="璧蜂釜濂借鐨勫悕瀛楋紝濡傘€屾瀬闄愯瘝銆?
                  maxlength="100"
                />
              </view>
            </view>
            <view class="form-item">
              <text class="label-text">鐢ㄥ湪鍝噷</text>
              <view class="field-box field-box--readonly">
                <text class="readonly-text">鍏ㄩ儴浣嶇疆锛堢暀瑷€銆佹悳绱€佺洿鎾爣棰樼瓑锛?/text>
              </view>
              <text class="form-hint">涓€娆℃坊鍔狅紝鍚勫涓€璧风敓鏁?/text>
            </view>
          </template>

          <template v-else-if="initialData">
            <view class="form-item">
              <text class="label-text">鍚嶇О</text>
              <view class="field-box field-box--readonly">
                <text class="readonly-text">{{ editDisplayName }}</text>
              </view>
            </view>
            <view class="form-item">
              <text class="label-text">鐢ㄥ湪鍝噷</text>
              <view class="field-box field-box--readonly">
                <text class="readonly-text">{{ editScenesLabel }}</text>
              </view>
            </view>
          </template>

          <view class="form-item">
            <text class="label-text">涓嶈鍑虹幇鐨勮瘝</text>
            <view class="field-box field-box--textarea">
              <textarea
                v-model="form.pattern"
                class="form-textarea"
                :disabled="isPoliticalSensitive"
                placeholder="澶氫釜璇嶇敤閫楀彿鍒嗗紑锛屽锛氭渶,绗竴,椤剁骇"
                maxlength="2000"
                :auto-height="true"
              />
            </view>
            <text class="form-hint">澶氫釜璇嶇敤閫楀彿鍒嗗紑鍗冲彲</text>
          </view>

          <view class="form-item">
            <text class="label-text">鍙戠幇鍚庢€庝箞鍋?/text>
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
                  {{ actionOptions[actionIndex]?.label || '涓嶈鍙戝竷' }}
                </text>
                <text class="picker-arrow">鈻?/text>
              </view>
            </picker>
            <text v-if="isStatutory" class="form-hint">绯荤粺鑷甫椤瑰彧鑳介€夈€屼笉璁╁彂甯冦€?/text>
          </view>

          <view class="form-item form-item--row">
            <text class="label-text label-text--inline">鏄惁寮€鍚?/text>
            <switch
              :checked="form.enabled"
              :disabled="isStatutory"
              color="#2d6a5a"
              @change="form.enabled = $event.detail.value"
            />
          </view>
          <text v-if="isStatutory" class="form-hint form-hint--block">绯荤粺鑷甫椤逛笉鑳藉叧闂?/text>

          <view class="form-item">
            <text class="label-text">澶囨敞锛堝彲閫夛級</text>
            <view class="field-box field-box--textarea">
              <textarea
                v-model="form.remark"
                class="form-textarea form-textarea--sm"
                placeholder="鍐欑粰鑷繁鐪嬬殑璇存槑锛屽彲鐣欑┖"
                maxlength="500"
                :auto-height="true"
              />
            </view>
          </view>
        </view>
      </scroll-view>

      <view class="dialog-footer">
        <view class="footer-btn footer-btn--cancel" @click="handleClose">
          <text>鍙栨秷</text>
        </view>
        <view
          class="footer-btn footer-btn--confirm"
          :class="{ 'is-loading': submitting }"
          @click="handleSubmit"
        >
          <text>{{ submitting ? '鎻愪氦涓?..' : mode === 'create' ? '鍒涘缓' : '淇濆瓨' }}</text>
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
  /** 鍚岀粍鍏ㄩ儴浣嶇疆瑙勫垯锛涚紪杈戞椂涓€骞朵繚瀛?*/
  relatedRules?: ContentSafetyRule[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const submitting = ref(false)
const preserveDevRemark = ref<string | null>(null)
const createName = ref('')

const actionOptions = [...ADMIN_ACTION_FORM_OPTIONS, { label: '鍏佽鍙戝竷', value: 'allow' as const }]

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
  return base || '鑷畾涔夐檺鍒?
}

async function handleSubmit() {
  if (isPoliticalSensitive.value) {
    uni.showToast({ title: '杩欑被鍐呭涓嶈兘鏀?, icon: 'none' })
    return
  }

  const pattern = String(form.pattern || '').trim()
  if (!pattern) {
    uni.showToast({ title: '璇峰～鍐欎笉璁稿嚭鐜扮殑璇?, icon: 'none' })
    return
  }

  submitting.value = true
  try {
    if (props.mode === 'create') {
      const displayName = createName.value.trim()
      if (!displayName) {
        uni.showToast({ title: '璇峰～鍐欏悕绉?, icon: 'none' })
        return
      }
      const slug = slugifyName(displayName)
      const userRemark = form.remark.trim() || displayName
      // 涓€娆″垱寤哄埌鍏ㄩ儴甯哥敤浣嶇疆
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
      uni.showToast({ title: '鍒涘缓鎴愬姛', icon: 'success' })
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
      uni.showToast({ title: '宸插悓姝ヤ繚瀛?, icon: 'success' })
    }
    emit('success')
    handleClose()
  } catch (e: any) {
    if (handleContentSafetyError(e)) return
    uni.showToast({ title: getUserFacingErrorMessage(e, '淇濆瓨澶辫触锛岃绋嶅悗鍐嶈瘯'), icon: 'none' })
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
