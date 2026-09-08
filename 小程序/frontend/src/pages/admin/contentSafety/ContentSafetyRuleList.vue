<!--
 * ContentSafetyRuleList - 发布内容设置
 * 同类限制词跨位置合并为一条，编辑时统一生效
 -->
<template>
  <view class="rule-list-page">
    <view class="page-header">
      <text class="page-title">发布内容设置</text>
      <text class="page-desc">同类词合并管理，改一次对讨论、搜索、直播间等全部生效</text>
    </view>

    <view class="toolbar">
      <picker :range="sceneOptions" range-key="label" :value="scenePickerIndex" @change="onSceneChange">
        <view class="filter-chip">
          <text class="filter-chip__text">{{ sceneFilterLabel }}</text>
          <text class="filter-chip__arrow">▼</text>
        </view>
      </picker>
      <view class="toolbar-actions">
        <view class="btn btn--ghost" @click="goLogs">
          <text>处理记录</text>
        </view>
        <view class="btn btn--primary" @click="openCreateDialog">
          <text>+ 新建</text>
        </view>
      </view>
    </view>

    <view v-if="!loading" class="rule-list">
      <view v-if="groupedData.length === 0" class="empty-state">
        <text class="empty-text">暂无限制词</text>
      </view>

      <view v-for="group in groupedData" :key="group.key" class="rule-card">
        <view class="rule-card__body">
          <view class="rule-card__title-row">
            <text class="rule-card__name">{{ group.displayName }}</text>
          </view>
          <view class="rule-card__tags">
            <text :class="['tag', group.enabled ? 'tag--on' : 'tag--off']">
              {{ group.enabled ? '开启' : '关闭' }}
            </text>
            <text
              :class="[
                'tag',
                group.binding_level === 'statutory' ? 'tag--sys' : 'tag--custom'
              ]"
            >
              {{ formatBindingLabel(group.binding_level) }}
            </text>
          </view>
          <view class="rule-card__meta">
            <text>用在 {{ group.scenesLabel }}</text>
            <text class="meta-dot">·</text>
            <text>{{ formatActionLabel(group.action) }}</text>
          </view>
        </view>
        <view class="rule-card__edit" @click="openEditGroup(group)">
          <text>编辑</text>
        </view>
      </view>
    </view>

    <view v-else class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <ContentSafetyRuleFormDialog
      v-model:visible="dialogVisible"
      :mode="dialogMode"
      :initial-data="currentRule"
      :related-rules="currentRelatedRules"
      @success="fetchData"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { getContentSafetyRules } from '@/api/contentSafety'
import type { AdminContentScene, ContentSafetyRule } from '@/types/contentSafety'
import ContentSafetyRuleFormDialog from './ContentSafetyRuleFormDialog.vue'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'
import {
  formatActionLabel,
  formatBindingLabel,
  groupContentSafetyRules,
  type ContentSafetyRuleGroup
} from '@/utils/contentSafetyDisplay'

const SCENE_OPTIONS: { label: string; value: AdminContentScene | '' }[] = [
  { label: '全部位置', value: '' },
  { label: '讨论', value: 'message' },
  { label: '直播标题', value: 'room_title' },
  { label: '直播间简介', value: 'room_description' },
  { label: '直播间栏目', value: 'room_tab' },
  { label: '搜索词', value: 'search_query' },
  { label: '标签', value: 'tag_name' } // 《02-V2》§3.4
]

/** 原始规则（全量，用于跨位置合并） */
const allRules = ref<ContentSafetyRule[]>([])
const loading = ref(false)
const sceneFilter = ref<AdminContentScene | ''>('')
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentRule = ref<ContentSafetyRule | null>(null)
const currentRelatedRules = ref<ContentSafetyRule[]>([])

const sceneOptions = SCENE_OPTIONS
const scenePickerIndex = computed(() => {
  const idx = SCENE_OPTIONS.findIndex((o) => o.value === sceneFilter.value)
  return idx >= 0 ? idx : 0
})
const sceneFilterLabel = computed(() => SCENE_OPTIONS[scenePickerIndex.value]?.label || '全部位置')

const groupedData = computed(() => {
  const groups = groupContentSafetyRules(allRules.value)
  if (!sceneFilter.value) return groups
  return groups.filter((g) => g.scenes.includes(sceneFilter.value))
})

function onSceneChange(e: any) {
  const idx = Number(e?.detail?.value ?? 0)
  sceneFilter.value = SCENE_OPTIONS[idx]?.value ?? ''
}

function goLogs() {
  uni.navigateTo({ url: '/pages/admin/contentSafety/ContentSafetyLogList' })
}

async function fetchData() {
  loading.value = true
  try {
    // 必须拉全量再合并；后端 page_size 最大 100
    const pageSize = 100
    const first = await getContentSafetyRules({ page: 1, page_size: pageSize })
    const firstData = first.data
    if (Array.isArray(firstData)) {
      allRules.value = firstData as any
      return
    }
    const items = [...(firstData?.items || [])]
    const total = Number(firstData?.total ?? items.length)
    const totalPages = Math.max(1, Math.ceil(total / pageSize))
    for (let page = 2; page <= totalPages; page++) {
      const res = await getContentSafetyRules({ page, page_size: pageSize })
      const data = res.data
      if (Array.isArray(data)) {
        items.push(...(data as any))
      } else {
        items.push(...(data?.items || []))
      }
    }
    allRules.value = items
  } catch (e: any) {
    uni.showToast({ title: getUserFacingErrorMessage(e, '加载失败，请稍后再试'), icon: 'none' })
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  dialogMode.value = 'create'
  currentRule.value = null
  currentRelatedRules.value = []
  dialogVisible.value = true
}

function openEditGroup(group: ContentSafetyRuleGroup) {
  dialogMode.value = 'edit'
  currentRule.value = { ...group.representative }
  currentRelatedRules.value = group.rules.map((r) => ({ ...r }))
  dialogVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.rule-list-page {
  min-height: 100vh;
  background: #f5f7f6;
  padding: 24rpx 28rpx 48rpx;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 24rpx;
}

.page-title {
  display: block;
  font-size: 36rpx;
  font-weight: 600;
  color: #1a2e28;
  line-height: 1.3;
}

.page-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #7a8f88;
  line-height: 1.4;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 14rpx 22rpx;
  background: #fff;
  border-radius: 999rpx;
  border: 1px solid #e4ece9;
}

.filter-chip__text {
  font-size: 26rpx;
  color: #2c3e38;
  white-space: nowrap;
}

.filter-chip__arrow {
  font-size: 18rpx;
  color: #9aaca4;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-shrink: 0;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  padding: 0 24rpx;
  border-radius: 12rpx;
  font-size: 26rpx;
  white-space: nowrap;
  box-sizing: border-box;

  &--ghost {
    background: #fff;
    color: #2d6a5a;
    border: 1px solid #d5e8e1;
  }

  &--primary {
    background: #2d6a5a;
    color: #fff;
  }
}

.rule-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  border: 1px solid #eef3f1;
}

.rule-card__body {
  flex: 1;
  min-width: 0;
}

.rule-card__title-row {
  margin-bottom: 12rpx;
}

.rule-card__name {
  font-size: 30rpx;
  font-weight: 600;
  color: #1a2e28;
  line-height: 1.35;
  word-break: break-all;
}

.rule-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-bottom: 12rpx;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  line-height: 1.4;
  white-space: nowrap;

  &--on {
    background: #e8f6f0;
    color: #1f7a5c;
  }

  &--off {
    background: #f2f2f2;
    color: #999;
  }

  &--sys {
    background: #fff6e8;
    color: #c07a1a;
  }

  &--custom {
    background: #eaf3ff;
    color: #2f6fdb;
  }
}

.rule-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4rpx;
  font-size: 24rpx;
  color: #7a8f88;
  line-height: 1.4;
}

.meta-dot {
  margin: 0 4rpx;
}

.rule-card__edit {
  flex-shrink: 0;
  width: 88rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef7f3;
  border-radius: 16rpx;
  border: 1px solid #d5e8e1;
  box-sizing: border-box;

  text {
    font-size: 26rpx;
    color: #2d6a5a;
    font-weight: 500;
    white-space: nowrap;
    writing-mode: horizontal-tb;
    letter-spacing: 0;
    line-height: 1;
  }
}

.empty-state,
.loading-state {
  padding: 96rpx 0;
  text-align: center;
}

.empty-text,
.loading-text {
  color: #7a8f88;
  font-size: 28rpx;
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid #e4ece9;
  border-top-color: #2d6a5a;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
