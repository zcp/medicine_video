<!--
 * SearchByTag - 按标签搜索场次页面
 * @description 用户端选择标签后搜索匹配的场次
 * @author 直播SaaS团队
 -->
<template>
  <view class="search-by-tag-page">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">按标签搜索</text>
    </view>

    <!-- 已选标签展示 -->
    <view v-if="selectedIds.length > 0" class="selected-bar">
      <view class="selected-tags">
        <view
          v-for="tagId in selectedIds"
          :key="tagId"
          class="selected-chip"
        >
          <text class="chip-text">{{ getTagName(tagId) }}</text>
          <view class="chip-remove" @click="removeSelectedTag(tagId)">
            <text class="remove-icon">✕</text>
          </view>
        </view>
      </view>
      <view class="btn-clear-all" @click="clearAllTags">
        <text class="clear-text">清空</text>
      </view>
    </view>

    <!-- 标签选择区 -->
    <view class="tag-selector">
      <view class="selector-header">
        <text class="selector-title">选择标签</text>
        <text class="selector-hint">（最多5个）</text>
      </view>
      <view class="search-box">
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索标签"
          @confirm="handleTagSearch"
        />
      </view>

      <!-- 标签列表 -->
      <view v-if="tagLoading" class="tag-loading">
        <view class="loading-spinner"></view>
        <text class="loading-text">加载标签...</text>
      </view>
      <scroll-view v-else class="tag-scroll" scroll-y>
        <view v-if="availableTags.length === 0" class="empty-tags">
          <text class="empty-text">暂无可选标签</text>
        </view>
        <view class="tag-grid">
          <view
            v-for="tag in availableTags"
            :key="tag.id"
            :class="['tag-chip', selectedIds.includes(tag.id) ? 'tag-selected' : '']"
            @click="toggleTag(tag.id)"
          >
            <text class="chip-text">{{ tag.name }}</text>
            <text v-if="selectedIds.includes(tag.id)" class="chip-check">✓</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 匹配模式选择（多个标签时显示） -->
    <view v-if="selectedIds.length > 1" class="match-mode">
      <view class="mode-header">
        <text class="mode-title">匹配模式</text>
      </view>
      <view class="mode-options">
        <view
          :class="['mode-option', matchAll ? 'mode-active' : '']"
          @click="matchAll = true"
        >
          <text class="mode-text">同时包含所有标签（AND）</text>
        </view>
        <view
          :class="['mode-option', !matchAll ? 'mode-active' : '']"
          @click="matchAll = false"
        >
          <text class="mode-text">包含任一标签（OR）</text>
        </view>
      </view>
    </view>

    <!-- 搜索按钮 -->
    <view class="search-action">
      <view
        class="btn-search"
        :class="{ 'is-disabled': selectedIds.length === 0, 'is-loading': searching }"
        @click="handleSearch"
      >
        <text class="btn-text">{{ searching ? '搜索中...' : '搜索场次' }}</text>
      </view>
    </view>

    <!-- 搜索结果 -->
    <view class="search-results">
      <view class="results-header" v-if="hasSearched">
        <text class="results-title">搜索结果（{{ results.length }}）</text>
      </view>

      <!-- 搜索中 -->
      <view v-if="searching" class="loading-state">
        <view class="loading-spinner"></view>
        <text class="loading-text">搜索中...</text>
      </view>

      <!-- 空结果 -->
      <view v-else-if="hasSearched && results.length === 0" class="empty-state">
        <text class="empty-text">未找到匹配的场次</text>
      </view>

      <!-- 结果列表 -->
      <view v-else class="results-list">
        <view
          v-for="item in results"
          :key="item.session_id"
          class="result-item"
          @click="navigateToSession(item.session_id)"
        >
          <view class="result-info">
            <text class="result-title">{{ item.title }}</text>
            <view class="result-tags">
              <text
                v-for="tagName in item.matched_tags"
                :key="tagName"
                class="result-tag"
              >{{ tagName }}</text>
            </view>
            <view class="result-meta">
              <text class="meta-text">匹配度: {{ Math.round(item.score * 100) }}%</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getTags, searchSessionsByTag } from '@/api/tags'
import type { Tag, SearchResultItem } from '@/types/tags'

const searchKeyword = ref('')
const tagLoading = ref(false)
const searching = ref(false)
const hasSearched = ref(false)
const matchAll = ref(true)
const availableTags = ref<Tag[]>([])
const selectedIds = ref<string[]>([])
const results = ref<SearchResultItem[]>([])
let allTags: Tag[] = []

/** 根据ID获取标签名称 */
function getTagName(id: string): string {
  return allTags.find(t => t.id === id)?.name || id
}

/** 加载标签列表 */
async function loadTags() {
  tagLoading.value = true
  try {
    const res = await getTags({ include_inactive: false })
    allTags = res.data?.items || []
    availableTags.value = [...allTags]
    logger.info('network', '标签列表加载完成', { count: allTags.length })
  } catch (error) {
    logger.error('system', '加载标签列表失败', error)
    uni.showToast({ title: '加载标签失败', icon: 'none' })
  } finally {
    tagLoading.value = false
  }
}

/** 搜索标签 */
function handleTagSearch() {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) {
    availableTags.value = [...allTags]
    return
  }
  availableTags.value = allTags.filter(tag =>
    tag.name.toLowerCase().includes(keyword) ||
    tag.slug.toLowerCase().includes(keyword)
  )
}

/** 切换标签选中 */
function toggleTag(tagId: string) {
  const index = selectedIds.value.indexOf(tagId)
  if (index >= 0) {
    selectedIds.value.splice(index, 1)
  } else {
    if (selectedIds.value.length >= 5) {
      uni.showToast({ title: '最多只能选择5个标签', icon: 'none' })
      return
    }
    selectedIds.value.push(tagId)
  }
}

/** 移除已选标签 */
function removeSelectedTag(tagId: string) {
  selectedIds.value = selectedIds.value.filter(id => id !== tagId)
}

/** 清空所有选中 */
function clearAllTags() {
  selectedIds.value = []
  results.value = []
  hasSearched.value = false
}

/** 执行搜索 */
async function handleSearch() {
  if (selectedIds.value.length === 0 || searching.value) return

  searching.value = true
  hasSearched.value = true
  try {
    logger.info('network', '按标签搜索场次', {
      tagIds: selectedIds.value,
      matchAll: matchAll.value
    })
    const res = await searchSessionsByTag({
      tag_ids: selectedIds.value,
      match_all: matchAll.value,
      page: 1,
      page_size: 50
    })
    results.value = res.data?.items || []
    logger.info('network', '标签搜索完成', { count: results.value.length })
  } catch (error) {
    logger.error('system', '标签搜索失败', error)
    uni.showToast({ title: '搜索失败', icon: 'none' })
  } finally {
    searching.value = false
  }
}

/** 跳转到直播观看页（场次） */
function navigateToSession(sessionId: string) {
  const sid = String(sessionId || '').trim()
  if (!sid) {
    uni.showToast({ title: '场次无效', icon: 'none' })
    return
  }
  uni.navigateTo({
    url: `/pages/live/LiveView?sessionId=${encodeURIComponent(sid)}`
  })
}

onMounted(() => {
  logger.info('system', '进入按标签搜索页')
  loadTags()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.search-by-tag-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-primary);
  }
}

.selected-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  flex: 1;
}

.selected-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background-color: #e6f7ff;
  border-radius: var(--border-radius-sm);

  .chip-text {
    font-size: 13px;
    color: var(--color-primary);
  }

  .chip-remove {
    cursor: pointer;

    .remove-icon {
      font-size: 12px;
      color: var(--color-primary);
      opacity: 0.7;
    }
  }
}

.btn-clear-all {
  flex-shrink: 0;
  cursor: pointer;

  .clear-text {
    font-size: 13px;
    color: var(--color-primary);
  }
}

.tag-selector {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.selector-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);

  .selector-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .selector-hint {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.search-box {
  margin-bottom: var(--spacing-md);

  .search-input {
    width: 100%;
    height: 36px;
    padding: 0 12px;
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-base);
    font-size: 14px;
    background-color: var(--color-bg-secondary);
    box-sizing: border-box;
  }
}

.tag-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  gap: var(--spacing-sm);

  .loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.tag-scroll {
  max-height: 240px;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .chip-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  .chip-check {
    font-size: 12px;
    color: var(--color-primary);
  }

  &.tag-selected {
    background-color: #e6f7ff;
    border: 1px solid var(--color-primary);

    .chip-text {
      color: var(--color-primary);
    }
  }
}

.empty-tags {
  padding: 20px 0;
  text-align: center;

  .empty-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.match-mode {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
}

.mode-header {
  margin-bottom: var(--spacing-md);

  .mode-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
  }
}

.mode-options {
  display: flex;
  gap: var(--spacing-md);
}

.mode-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .mode-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }

  &.mode-active {
    background-color: #e6f7ff;
    border: 1px solid var(--color-primary);

    .mode-text {
      color: var(--color-primary);
      font-weight: 500;
    }
  }
}

.search-action {
  margin-bottom: var(--spacing-lg);
}

.btn-search {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 15px;
    color: #ffffff;
    font-weight: 500;
  }

  &.is-disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.is-loading {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.search-results {
  .results-header {
    margin-bottom: var(--spacing-md);

    .results-title {
      font-size: 15px;
      font-weight: 500;
      color: var(--color-text-primary);
    }
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  gap: var(--spacing-md);

  .loading-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);

  .empty-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.result-item {
  display: flex;
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  cursor: pointer;

  &:active {
    opacity: 0.8;
  }
}

.result-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;

  .result-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
  }
}

.result-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;

  .result-tag {
    padding: 2px 8px;
    background-color: #e6f7ff;
    border-radius: var(--border-radius-sm);
    font-size: 12px;
    color: var(--color-primary);
  }
}

.result-meta {
  .meta-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
