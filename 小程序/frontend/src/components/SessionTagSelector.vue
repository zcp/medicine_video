<!--
 * SessionTagSelector - 场次标签选择器
 * @description 嵌入场次编辑页，管理场次的标签关联
 * @author 直播SaaS团队
 -->
<template>
  <view class="session-tag-selector">
    <view class="selector-header">
      <text class="selector-title">场次标签</text>
      <text class="selector-hint">最多可选5个标签</text>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="selector-loading">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 标签搜索输入 -->
    <view v-else class="selector-body">
      <view class="search-row">
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="输入关键词搜索标签"
          @confirm="handleSearch"
        />
      </view>

      <!-- 搜索结果/全部标签 -->
      <scroll-view class="tag-scroll" scroll-y>
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

      <!-- 已选标签展示 -->
      <view v-if="selectedIds.length > 0" class="selected-section">
        <view class="selected-header">
          <text class="selected-title">已选标签（{{ selectedIds.length }}）</text>
          <view class="btn-clear" @click="clearAll">
            <text class="clear-text">清空</text>
          </view>
        </view>
        <view class="selected-tags">
          <view
            v-for="tagId in selectedIds"
            :key="tagId"
            class="selected-chip"
          >
            <text class="chip-text">{{ getTagName(tagId) }}</text>
            <view class="chip-remove" @click="removeTag(tagId)">
              <text class="remove-icon">✕</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 保存按钮 -->
      <view class="save-row">
        <view
          class="btn-save"
          :class="{ 'is-loading': saving }"
          @click="handleSave"
        >
          <text class="btn-text">{{ saving ? '保存中...' : '保存标签' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getTags, getSessionTags, setSessionTags } from '@/api/tags'
import type { Tag } from '@/types/tags'

const props = defineProps<{
  /** 场次ID */
  sessionId: string
}>()

const emit = defineEmits<{
  success: []
}>()

const loading = ref(false)
const saving = ref(false)
const searchKeyword = ref('')
const availableTags = ref<Tag[]>([])
const selectedIds = ref<string[]>([])
let allTags: Tag[] = []

/** 根据ID获取标签名称 */
function getTagName(id: string): string {
  return allTags.find(t => t.id === id)?.name || id
}

/** 加载数据 */
async function loadData() {
  loading.value = true
  try {
    logger.info('network', '加载场次标签数据', { sessionId: props.sessionId })
    const [allRes, selectedRes] = await Promise.all([
      getTags({ include_inactive: false }),
      getSessionTags(props.sessionId)
    ])
    // 兼容后端返回格式：可能是 { items: [...] } 或直接是 [...]
    const allData = allRes?.data
    allTags = Array.isArray(allData) ? allData : (Array.isArray(allData?.items) ? allData.items : [])
    availableTags.value = [...allTags]
    selectedIds.value = (selectedRes.data?.items || []).map(item => item.tag_id)
    logger.info('network', '场次标签数据加载完成', {
      allCount: allTags.length,
      selectedCount: selectedIds.value.length
    })
  } catch (error) {
    logger.error('system', '加载场次标签数据失败', error)
    uni.showToast({ title: '加载标签数据失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 搜索标签 */
function handleSearch() {
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

/** 切换标签选中状态 */
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

/** 移除单个标签 */
function removeTag(tagId: string) {
  selectedIds.value = selectedIds.value.filter(id => id !== tagId)
}

/** 清空所有选中 */
function clearAll() {
  selectedIds.value = []
}

/** 保存标签关联 */
async function handleSave() {
  if (saving.value) return
  saving.value = true
  try {
    logger.info('network', '保存场次标签', {
      sessionId: props.sessionId,
      tagIds: selectedIds.value
    })
    await setSessionTags(props.sessionId, {
      tag_ids: selectedIds.value,
      mode: 'replace'
    })
    uni.showToast({ title: '标签保存成功', icon: 'success' })
    emit('success')
  } catch (error) {
    logger.error('system', '保存场次标签失败', error)
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.session-tag-selector {
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  padding: var(--spacing-md);
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

.selector-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 0;
  gap: var(--spacing-sm);

  .loading-spinner {
    width: 24px;
    height: 24px;
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

.search-row {
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

.tag-scroll {
  max-height: 200px;
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

.selected-section {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.selected-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);

  .selected-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .btn-clear {
    cursor: pointer;

    .clear-text {
      font-size: 12px;
      color: var(--color-primary);
    }
  }
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.selected-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: #e6f7ff;
  border-radius: var(--border-radius-sm);

  .chip-text {
    font-size: 12px;
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

.save-row {
  margin-top: var(--spacing-md);
}

.btn-save {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;

  .btn-text {
    font-size: 14px;
    color: #ffffff;
  }

  &.is-loading {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
