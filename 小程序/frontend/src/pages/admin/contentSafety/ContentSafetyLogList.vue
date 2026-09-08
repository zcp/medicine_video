<!--
 * ContentSafetyLogList - 发布处理记录（只读）
 -->
<template>
  <view class="log-list-page">
    <view class="page-header">
      <view class="header-title">
        <text class="title">发布处理记录</text>
      </view>
      <view class="filter-row">
        <picker :range="sceneOptions" range-key="label" :value="sceneIndex" @change="onSceneChange">
          <view class="filter-chip">{{ sceneOptions[sceneIndex]?.label }}</view>
        </picker>
        <picker :range="decisionOptions" range-key="label" :value="decisionIndex" @change="onDecisionChange">
          <view class="filter-chip">{{ decisionOptions[decisionIndex]?.label }}</view>
        </picker>
        <view class="filter-chip filter-chip--action" @click="fetchData">
          <text>查询</text>
        </view>
      </view>
    </view>

    <view v-if="!loading" class="log-list">
      <view v-if="tableData.length === 0" class="empty-state">
        <text class="empty-text">暂无记录</text>
      </view>

      <view v-for="item in tableData" :key="item.id" class="log-item">
        <view class="log-header">
          <text class="log-time">{{ formatDateTime(item.created_at) }}</text>
          <view :class="['decision-tag', `decision-${item.decision}`]">
            <text>{{ formatDecisionLabel(item.decision) }}</text>
          </view>
        </view>
        <view class="log-row">
          <text class="log-label">用户</text>
          <text class="log-value">{{ displayUserLabel(item) }}</text>
        </view>
        <view class="log-row">
          <text class="log-label">位置</text>
          <text class="log-value">{{ formatSceneLabel(item.scene) }}</text>
        </view>
        <view class="log-row">
          <text class="log-label">用户填写</text>
          <text class="log-value">{{ item.input_excerpt || '—' }}</text>
        </view>
      </view>
    </view>

    <view v-else class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { getContentSafetyLogs } from '@/api/contentSafety'
import { getAdminUsers } from '@/api/user'
import type { ContentSafetyLog } from '@/types/contentSafety'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'
import {
  ADMIN_DECISION_FILTER_OPTIONS,
  ADMIN_SCENE_FILTER_OPTIONS,
  formatDecisionLabel,
  formatSceneLabel,
  logContentSafetyAuditDetail,
  resolveContentSafetyLogUserLabel
} from '@/utils/contentSafetyDisplay'

const sceneOptions = ADMIN_SCENE_FILTER_OPTIONS
const decisionOptions = ADMIN_DECISION_FILTER_OPTIONS

const tableData = ref<ContentSafetyLog[]>([])
const loading = ref(false)
const sceneFilter = ref('')
const decisionFilter = ref('')
/** user_id → 昵称/用户名（跨服务补全） */
const userLabelMap = ref<Record<string, string>>({})

const sceneIndex = computed(() => {
  const idx = sceneOptions.findIndex((o) => o.value === sceneFilter.value)
  return idx >= 0 ? idx : 0
})

const decisionIndex = computed(() => {
  const idx = decisionOptions.findIndex((o) => o.value === decisionFilter.value)
  return idx >= 0 ? idx : 0
})

function formatDateTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function displayUserLabel(item: ContentSafetyLog): string {
  const fromPayload = resolveContentSafetyLogUserLabel(item)
  if (fromPayload !== '—' && fromPayload !== item.user_id?.trim()) {
    return fromPayload
  }
  const uid = item.user_id?.trim()
  if (uid && userLabelMap.value[uid]) {
    return userLabelMap.value[uid]
  }
  return fromPayload
}

function onSceneChange(e: any) {
  const idx = Number(e?.detail?.value ?? 0)
  sceneFilter.value = sceneOptions[idx]?.value ?? ''
}

function onDecisionChange(e: any) {
  const idx = Number(e?.detail?.value ?? 0)
  decisionFilter.value = decisionOptions[idx]?.value ?? ''
}

function needsUserEnrichment(item: ContentSafetyLog): boolean {
  const label = resolveContentSafetyLogUserLabel(item)
  const uid = item.user_id?.trim()
  if (!uid) return false
  if (userLabelMap.value[uid]) return false
  // 已有可读昵称/用户名则不再补全
  return label === uid || label === '—'
}

/**
 * 用管理端用户列表按 public_id 补全昵称（无单用户 GET；最多扫 5 页）
 */
async function enrichUserLabels(logs: ContentSafetyLog[]) {
  const needIds = new Set(
    logs.filter(needsUserEnrichment).map((item) => item.user_id!.trim())
  )
  if (needIds.size === 0) return

  const nextMap: Record<string, string> = { ...userLabelMap.value }
  let page = 1
  const size = 100
  const maxPages = 5

  try {
    while (needIds.size > 0 && page <= maxPages) {
      const res = await getAdminUsers({ page, size })
      const items = res.data?.items || []
      if (!items.length) break

      for (const user of items) {
        const pid = String(user.public_id || '').trim()
        if (!pid || !needIds.has(pid)) continue
        const label = String(user.nickname || user.username || '').trim()
        if (label) {
          nextMap[pid] = label
          needIds.delete(pid)
        }
      }

      if (items.length < size) break
      page += 1
    }
  } catch {
    // 补全失败不影响主列表：仍展示 user_id
  }

  userLabelMap.value = nextMap
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getContentSafetyLogs({
      scene: sceneFilter.value || undefined,
      decision: (decisionFilter.value as any) || undefined,
      page: 1,
      page_size: 50
    })
    const data = res.data
    tableData.value = Array.isArray(data) ? (data as any) : (data?.items || [])
    tableData.value.forEach((item) => logContentSafetyAuditDetail(item))
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '加载失败，请稍后再试'), icon: 'none' })
  } finally {
    loading.value = false
  }
  // 列表先展示；昵称补全异步进行，失败仍显示 user_id
  void enrichUserLabels(tableData.value)
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.log-list-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.header-title .title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  display: block;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-chip {
  padding: 8px 12px;
  background: var(--color-surface);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-primary);

  &--action {
    background: var(--color-primary);
    color: #fff;
  }
}

.log-item {
  background: var(--color-surface);
  border-radius: 12px;
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.log-time {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.decision-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.decision-block { background: #fff1f0; color: #cf1322; }
.decision-warn { background: #fff7e6; color: #d48806; }
.decision-allow { background: #e6f7f0; color: #0f766e; }

.log-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
}

.log-label {
  flex-shrink: 0;
  width: 72px;
  color: var(--color-text-tertiary);
}

.log-value {
  flex: 1;
  color: var(--color-text-primary);
  word-break: break-all;
}

.empty-state,
.loading-state {
  padding: 48px 0;
  text-align: center;
}

.empty-text,
.loading-text {
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
