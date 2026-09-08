<!--
 * ExpertDepartmentMergeDialog - 合并科室（高风险二次确认）
 * 合并后源科室物理删除；目标候选独立拉取（可跨页/可搜）
 -->
<template>
  <view v-if="visible" class="dialog-overlay" @tap="handleClose">
    <view class="dialog-container" @tap.stop>
      <view class="dialog-header">
        <text class="dialog-title">合并科室</text>
        <view class="dialog-close" @tap="handleClose">
          <text class="close-icon">✕</text>
        </view>
      </view>

      <view class="dialog-body">
        <view class="warn-box">
          <text class="warn-text">
            合并后源科室将删除且不可从本页恢复；专家与同义词并入目标（同义词最多 20，后端截断）。
          </text>
        </view>

        <view class="form-item">
          <text class="label-text">源科室（将被删除）</text>
          <text class="value-text">{{ source?.name || '—' }}</text>
        </view>

        <view class="form-item">
          <text class="label-text">搜索目标</text>
          <input
            v-model="targetKeyword"
            class="search-input"
            placeholder="输入名称筛选目标科室"
            maxlength="100"
            @confirm="loadTargets"
          />
        </view>

        <view class="form-item">
          <text class="label-text">目标科室</text>
          <picker
            v-if="targetOptions.length"
            :range="targetOptions"
            range-key="label"
            :value="targetPickerIndex"
            @change="onTargetPick"
          >
            <view class="picker-trigger">
              <text :class="targetId ? 'picker-value' : 'picker-placeholder'">
                {{ targetName || '请选择合并目标' }}
              </text>
              <text class="arrow">▼</text>
            </view>
          </picker>
          <text v-else-if="loadingTargets" class="field-hint">目标加载中...</text>
          <text v-else class="field-hint">暂无其他可合并目标，可调整搜索后重试</text>
        </view>
      </view>

      <view class="dialog-footer">
        <view class="btn-cancel" @tap="handleClose"><text>取消</text></view>
        <view class="btn-danger" @tap="handleConfirm">
          <text>{{ saving ? '合并中...' : '确认合并' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { listExpertDepartments, mergeExpertDepartments } from '@/api/expertDepartments'
import type { ExpertDepartmentItem } from '@/types/expertDepartment'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'

const props = defineProps<{
  visible: boolean
  source: ExpertDepartmentItem | null
}>()

const emit = defineEmits<{
  'update:visible': [boolean]
  success: []
}>()

const saving = ref(false)
const loadingTargets = ref(false)
const targetId = ref('')
const targetKeyword = ref('')
const targetOptions = ref<Array<{ id: string; name: string; label: string }>>([])

const targetPickerIndex = computed(() => {
  const idx = targetOptions.value.findIndex((c) => c.id === targetId.value)
  return idx >= 0 ? idx : 0
})

const targetName = computed(
  () => targetOptions.value.find((c) => c.id === targetId.value)?.name || ''
)

async function loadTargets() {
  loadingTargets.value = true
  try {
    const res = await listExpertDepartments({
      page: 1,
      size: 200,
      is_active: true,
      q: targetKeyword.value.trim() || undefined
    })
    const sourceId = props.source?.id
    targetOptions.value = (res.items || [])
      .filter((c) => c?.id && c.id !== sourceId)
      .map((c) => ({
        id: String(c.id),
        name: String(c.name),
        label: `${c.name}${c.category_name ? `（${c.category_name}）` : ''}`
      }))
    if (!targetOptions.value.some((t) => t.id === targetId.value)) {
      targetId.value = targetOptions.value[0]?.id || ''
    }
  } catch {
    targetOptions.value = []
    targetId.value = ''
  } finally {
    loadingTargets.value = false
  }
}

watch(
  () => props.visible,
  (v) => {
    if (v) {
      targetKeyword.value = ''
      targetId.value = ''
      void loadTargets()
    }
  }
)

function onTargetPick(e: any) {
  const opt = targetOptions.value[Number(e?.detail?.value)]
  if (opt) targetId.value = opt.id
}

function handleClose() {
  if (saving.value) return
  emit('update:visible', false)
}

async function handleConfirm() {
  if (!props.source?.id) return
  if (!targetId.value) {
    uni.showToast({ title: '请选择目标科室', icon: 'none' })
    return
  }
  if (targetId.value === props.source.id) {
    uni.showToast({ title: '不能合并到自身', icon: 'none' })
    return
  }
  uni.showModal({
    title: '再次确认',
    content: `确定将「${props.source.name}」合并到「${targetName.value}」？源科室将删除且不可恢复。`,
    confirmColor: '#ff4d4f',
    success: async (r) => {
      if (!r.confirm || saving.value) return
      saving.value = true
      try {
        const res = await mergeExpertDepartments({
          source_id: props.source!.id,
          target_id: targetId.value
        })
        const n = Number(res?.transferred_experts ?? 0)
        uni.showToast({
          title: Number.isFinite(n) ? `已合并，转移专家 ${n} 人` : '合并成功',
          icon: 'none'
        })
        emit('update:visible', false)
        emit('success')
      } catch (e: any) {
        uni.showToast({ title: getUserFacingErrorMessage(e, '合并失败'), icon: 'none' })
      } finally {
        saving.value = false
      }
    }
  })
}
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
}

.dialog-container {
  width: 100%;
  max-width: 420px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dialog-close {
  padding: 4px 8px;
}

.close-icon {
  font-size: 16px;
  color: var(--color-text-tertiary);
}

.dialog-body {
  padding: 16px;
}

.warn-box {
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: var(--border-radius-base);
  padding: 10px 12px;
  margin-bottom: 14px;
}

.warn-text {
  font-size: 12px;
  color: #ad6800;
  line-height: 1.5;
}

.form-item {
  margin-bottom: 14px;
}

.label-text {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.value-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 14px;
  box-sizing: border-box;
}

.picker-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
}

.picker-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

.picker-placeholder {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.arrow {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.field-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.dialog-footer {
  display: flex;
  gap: 12px;
  padding: 12px 16px 16px;
}

.btn-cancel,
.btn-danger {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-base);
}

.btn-cancel {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.btn-danger {
  background: #ff4d4f;
  color: #fff;
}
</style>
