<!--
 * UnmappedExpertsPanel - 未映射专家（词表 Admin 次级区）
 * 展示过渡 department 文本；引导去专家管理绑定词表。本页不做一键建词表。
 -->
<template>
  <view class="unmapped-panel">
    <view class="panel-header">
      <text class="panel-title">未映射专家</text>
      <view class="btn-refresh" @tap="fetchData">
        <text class="btn-text">刷新</text>
      </view>
    </view>

    <view v-if="loading" class="state-box">
      <text class="state-text">加载中...</text>
    </view>
    <view v-else-if="errorMsg" class="state-box">
      <text class="state-text">{{ errorMsg }}</text>
      <view class="btn-refresh" @tap="fetchData"><text class="btn-text">重试</text></view>
    </view>
    <view v-else-if="items.length === 0" class="state-box">
      <text class="state-text">暂无未映射专家</text>
    </view>
    <view v-else class="list">
      <view v-for="item in items" :key="item.id" class="row">
        <view class="row-main">
          <text class="name">{{ item.name }}</text>
          <text class="meta">
            {{ [item.title, item.hospital, item.department].filter(Boolean).join(' · ') || '无过渡科室文本' }}
          </text>
        </view>
        <view class="action-btn" @tap="goExpertAdmin">
          <text>去绑定</text>
        </view>
      </view>
    </view>

    <view v-if="total > pageSize" class="pagination">
      <view :class="['page-btn', page <= 1 ? 'disabled' : '']" @tap="changePage(page - 1)">
        <text>上一页</text>
      </view>
      <text class="page-text">{{ page }} / {{ totalPages }}</text>
      <view :class="['page-btn', page >= totalPages ? 'disabled' : '']" @tap="changePage(page + 1)">
        <text>下一页</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listUnmappedExperts } from '@/api/expertDepartments'
import type { UnmappedExpertItem } from '@/types/expertDepartment'
import { getUserFacingErrorMessage } from '@/utils/contentSafety'

const loading = ref(false)
const errorMsg = ref('')
const items = ref<UnmappedExpertItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

async function fetchData() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await listUnmappedExperts({ page: page.value, size: pageSize.value })
    items.value = Array.isArray(res.items) ? res.items : []
    total.value = Number(res.total) || items.value.length
  } catch (e: any) {
    errorMsg.value = getUserFacingErrorMessage(e, '加载失败')
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  void fetchData()
}

function goExpertAdmin() {
  uni.navigateTo({ url: '/pages/admin/expert/ExpertAdminList' })
}

onMounted(() => {
  void fetchData()
})

defineExpose({ refresh: fetchData })
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.unmapped-panel {
  margin-top: var(--spacing-sm);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.btn-refresh {
  height: 28px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  background: var(--color-primary);
  border-radius: var(--border-radius-base);

  .btn-text {
    color: #fff;
    font-size: 12px;
  }
}

.state-box {
  padding: 24px 12px;
  text-align: center;
}

.state-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 12px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
}

.row-main {
  flex: 1;
  min-width: 0;
}

.name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.meta {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.action-btn {
  flex-shrink: 0;
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 12px;
  color: var(--color-primary);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.page-btn {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  font-size: 12px;

  &.disabled {
    opacity: 0.4;
  }
}

.page-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
