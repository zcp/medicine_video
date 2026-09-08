<!--
 * FeaturedContentList - 焦点图管理列表页
 * @description 管理端焦点图的增删改查页面
 * @author 直播SaaS团队
 -->
<template>
  <!-- page-meta 必须首节点；其后只能有一个页面根节点（多根会把布尔值漏成文案 true） -->
  <page-meta :page-style="pageMetaStyle" />
  <view class="page-root">
    <view
      class="featured-content-list-page"
      :class="dialogVisible ? 'is-page-locked' : ''"
      :style="pageLockStyle"
    >
      <view class="page-header">
        <text class="title">焦点图管理</text>
      </view>

      <view class="list-toolbar">
        <view class="list-tabs">
          <view
            v-for="tab in listTabs"
            :key="tab.value"
            :class="['list-tab', activeListTab === tab.value ? 'is-active' : '']"
            @click="handleListTabChange(tab.value)"
          >
            <text class="tab-text">{{ tab.label }}</text>
          </view>
        </view>
        <view class="btn-add" @click="openCreateDialog">
          <text class="btn-text">+ 新增焦点图</text>
        </view>
      </view>

      <view class="content-list" v-if="!loading">
        <view v-if="displayData.length === 0" class="empty-state">
          <text class="empty-text">{{ emptyListText }}</text>
        </view>

        <view
          v-for="item in displayData"
          :key="item.id"
          class="content-item"
        >
          <view class="item-image">
            <image
              :src="bannerSrc(item)"
              class="cover-image"
              mode="aspectFill"
              @error="onBannerError(item.id, item.image_url)"
            />
          </view>

          <view class="item-info">
            <view class="item-title-row">
              <text class="item-title">{{ item.title }}</text>
              <view :class="['status-tag', statusTagClass(item)]">
                <text class="status-text">{{ statusTagLabel(item) }}</text>
              </view>
            </view>

            <view class="item-target">
              <view v-if="item.target_type && !isFeaturedContentPureDisplay(item)" class="target-info">
                <view class="target-type-tag">
                  <text class="target-type-text">{{ targetTypeLabel(item.target_type) }}</text>
                </view>
                <text v-if="item.target_url" class="target-url">{{ item.target_url }}</text>
                <text v-else-if="item.target_id" class="target-name">{{ getTargetDisplayName(item) }}</text>
              </view>
              <text v-else class="target-none">纯展示</text>
            </view>

            <view class="item-meta">
              <text class="meta-text">排序: {{ item.sort_order }}</text>
              <view v-if="item.start_at || item.end_at" class="date-range">
                <text class="meta-text">{{ item.start_at ? formatDate(item.start_at) : '不限' }} ~ {{ item.end_at ? formatDate(item.end_at) : '不限' }}</text>
              </view>
              <text v-else class="meta-text">永久有效</text>
            </view>
          </view>

          <view class="item-actions">
            <view class="action-btn btn-plain" @click="openEditDialog(item)">
              <text class="btn-text">编辑</text>
            </view>
            <view class="action-btn btn-plain" @click="handleUploadImage(item)">
              <text class="btn-text">换图</text>
            </view>
            <view class="action-btn btn-delete" @click="handleDelete(item)">
              <text class="btn-text">删除</text>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="loading-state">
        <view class="loading-spinner"></view>
        <text class="loading-text">加载中...</text>
      </view>

      <view class="pagination-wrapper" v-if="total > 0 && activeListTab === 'all'">
        <view class="pagination">
          <view
            :class="['page-btn', currentPage <= 1 ? 'disabled' : '']"
            @click="changePage(currentPage - 1)"
          >
            <text class="page-btn-text">上一页</text>
          </view>
          <view class="page-info">
            <text class="page-text">{{ currentPage }} / {{ totalPages }}</text>
          </view>
          <view
            :class="['page-btn', currentPage >= totalPages ? 'disabled' : '']"
            @click="changePage(currentPage + 1)"
          >
            <text class="page-btn-text">下一页</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 与列表壳并列：锁页只作用列表，不包弹窗 -->
    <FeaturedContentFormDialog
      v-model:visible="dialogVisible"
      :mode="dialogMode"
      :initial-data="currentItem"
      @success="fetchData"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { onPageScroll } from '@dcloudio/uni-app'
import { logger } from '@/logs/logger'
import { request } from '@/utils/request'
import { resolveBannerUrl, shouldMarkBannerBroken } from '@/utils/url'
import {
  getAdminFeaturedContent,
  deleteFeaturedContent,
  uploadFeaturedContentImage,
  updateFeaturedContent
} from '@/api/featuredContent'
import type { FeaturedContent } from '@/types/featuredContent'
import {
  FEATURED_CONTENT_TARGET_TYPE_LABELS,
  isFeaturedContentInDisplayPeriod,
  isFeaturedContentPureDisplay
} from '@/types/featuredContent'
import FeaturedContentFormDialog from './FeaturedContentFormDialog.vue'

// 列表 Tab
type ListTab = 'displaying' | 'offline' | 'all'
const listTabs: Array<{ label: string; value: ListTab }> = [
  { label: '展示中', value: 'displaying' },
  { label: '已下线', value: 'offline' },
  { label: '全部', value: 'all' }
]
const activeListTab = ref<ListTab>('displaying')

// 表格数据
const tableData = ref<FeaturedContent[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 弹窗状态
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentItem = ref<FeaturedContent | null>(null)

/** 页面滚动锁：记录 scrollTop，弹窗打开时 fixed + 负 top，关闭后还原 */
const savedPageScrollTop = ref(0)
/** 小程序 :style 用字符串更稳，避免空对象/布尔绑定被渲染成文案 */
const pageMetaStyle = computed(() =>
  dialogVisible.value ? 'overflow: hidden;' : 'overflow: visible;'
)
const pageLockStyle = computed(() =>
  dialogVisible.value ? `top: -${savedPageScrollTop.value}px;` : ''
)

onPageScroll((e) => {
  if (dialogVisible.value) return
  savedPageScrollTop.value = Number(e?.scrollTop ?? 0) || 0
})

watch(dialogVisible, (open) => {
  if (open) {
    logger.info('system', '焦点图弹窗打开，锁定页面滚动', {
      scrollTop: savedPageScrollTop.value
    })
    return
  }
  nextTick(() => {
    uni.pageScrollTo({
      scrollTop: savedPageScrollTop.value,
      duration: 0
    })
  })
  logger.info('system', '焦点图弹窗关闭，恢复页面滚动', {
    scrollTop: savedPageScrollTop.value
  })
})

// 资源名称缓存：target_id -> 资源名称
const resourceNameCache = ref<Record<string, string>>({})
const brokenBannerIds = ref<Record<string, true>>({})

function bannerSrc(item: FeaturedContent): string {
  return resolveBannerUrl(item.image_url, !!brokenBannerIds.value[item.id])
}

function onBannerError(id: string, raw?: string | null) {
  if (brokenBannerIds.value[id]) return
  if (!shouldMarkBannerBroken(raw, !!brokenBannerIds.value[id])) return
  brokenBannerIds.value = { ...brokenBannerIds.value, [id]: true }
}

// 计算总页数
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

/**
 * Tab 前端过滤（后端 is_active 可能未生效，前端兜底保证「展示中 / 已下线」互斥）
 * - 展示中：启用且在有效期内
 * - 已下线：未启用（与状态标签「已下线」口径一致）
 * - 全部：不过滤
 */
const displayData = computed(() => {
  if (activeListTab.value === 'displaying') {
    return tableData.value.filter((item) => isItemDisplaying(item))
  }
  if (activeListTab.value === 'offline') {
    return tableData.value.filter((item) => !item.is_active)
  }
  return tableData.value
})

const emptyListText = computed(() => {
  if (activeListTab.value === 'displaying') return '暂无展示中的焦点图'
  if (activeListTab.value === 'offline') return '暂无已下线的焦点图'
  return '暂无焦点图数据'
})

// API 路径映射（关联资源名称）
const apiMap: Record<string, string> = {
  room: '/rooms',
  session: '/sessions',
  brand: '/brands'
}

function targetTypeLabel(type: string): string {
  return FEATURED_CONTENT_TARGET_TYPE_LABELS[type] || type
}

function isItemDisplaying(item: FeaturedContent): boolean {
  return item.is_active && isFeaturedContentInDisplayPeriod(item)
}

function statusTagClass(item: FeaturedContent): string {
  if (!item.is_active) return 'status-inactive'
  if (isItemDisplaying(item)) return 'status-active'
  return 'status-pending'
}

function statusTagLabel(item: FeaturedContent): string {
  if (!item.is_active) return '已下线'
  if (isItemDisplaying(item)) return '展示中'
  return '未生效'
}

function handleListTabChange(tab: ListTab) {
  if (activeListTab.value === tab) return
  activeListTab.value = tab
  currentPage.value = 1
  fetchData()
}

// 获取资源显示名称
function getTargetDisplayName(item: FeaturedContent): string {
  if (!item.target_id) return '已关联'
  return resourceNameCache.value[item.target_id] || '已关联'
}

// 批量加载关联资源名称
async function loadResourceNames(items: FeaturedContent[]) {
  const needLoad = items.filter(
    item => item.target_id && item.target_type && !resourceNameCache.value[item.target_id]
  )

  if (needLoad.length === 0) return

  // 按类型分组加载
  const byType = new Map<string, string[]>()
  for (const item of needLoad) {
    const type = item.target_type!
    if (!byType.has(type)) byType.set(type, [])
    byType.get(type)!.push(item.target_id!)
  }

  for (const [type, ids] of byType) {
    const api = apiMap[type]
    if (!api) continue

    // 并发加载每个资源的名称
    await Promise.all(
      ids.map(async (id) => {
        try {
          const res = await request.get(`${api}/${id}`, { auth: false, showError: false })
          const data = res?.data || res
          const name = data?.name || data?.title || ''
          if (name) {
            resourceNameCache.value[id] = name
          }
        } catch {
          // 加载失败不影响显示
        }
      })
    )
  }
}

function formatDate(iso: string): string {
  if (!iso) return ''
  const date = new Date(iso)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// 获取数据
async function fetchData() {
  loading.value = true
  try {
    logger.info('network', '加载管理端焦点图列表', {
      page: currentPage.value,
      page_size: pageSize.value,
      listTab: activeListTab.value
    })

    const queryParams: Parameters<typeof getAdminFeaturedContent>[0] = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (activeListTab.value === 'offline') {
      queryParams.is_active = false
    } else if (activeListTab.value === 'displaying') {
      queryParams.is_active = true
    }

    const res = await getAdminFeaturedContent(queryParams)

    // 适配后端返回格式：data 可能是数组或分页对象
    if (Array.isArray(res.data)) {
      // 后端直接返回数组格式
      tableData.value = res.data
      total.value = res.data.length
    } else if (res.data && typeof res.data === 'object') {
      // 后端返回分页对象格式 { items, total, page, size }
      const data = res.data as any
      tableData.value = data.items || data || []
      total.value = data.total || 0
    } else {
      tableData.value = []
      total.value = 0
    }

    logger.info('network', '管理端焦点图列表加载完成', {
      total: total.value,
      page: currentPage.value,
      page_size: pageSize.value,
      count: tableData.value.length
    })

    // 异步加载关联资源名称（不阻塞渲染）
    loadResourceNames(displayData.value)
  } catch (error) {
    logger.error('system', '加载管理端焦点图列表失败', error)
    uni.showToast({ title: '加载焦点图列表失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// 切换页码
function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchData()
}

// 打开新增弹窗
function openCreateDialog() {
  logger.info('user', '打开新增焦点图弹窗')
  dialogMode.value = 'create'
  currentItem.value = null
  dialogVisible.value = true
}

// 打开编辑弹窗
function openEditDialog(item: FeaturedContent) {
  logger.info('user', '打开编辑焦点图弹窗', { id: item.id, title: item.title })
  dialogMode.value = 'edit'
  currentItem.value = { ...item }
  dialogVisible.value = true
}

// 上传图片
function handleUploadImage(item: FeaturedContent) {
  logger.info('user', '发起焦点图图片上传', { id: item.id })
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const filePath = res.tempFilePaths[0]
      logger.info('network', '选择焦点图图片文件', {
        contentId: item.id,
        filePath
      })
      try {
        const uploadRes = await uploadFeaturedContentImage(item.id, filePath)
        // 兼容多种后端返回格式：data.image_url / image_url / data.url
        const serverUrl = uploadRes?.data?.image_url
          || (uploadRes?.data as any)?.url
          || (uploadRes as any)?.image_url
        logger.info('network', '焦点图图片上传完成', {
          contentId: item.id,
          serverUrl,
          rawResponse: JSON.stringify(uploadRes)
        })
        // 确保服务器返回的 URL 写回数据库（不依赖后端 upload 端点自动更新）
        if (serverUrl) {
          await updateFeaturedContent(item.id, { image_url: serverUrl })
          logger.info('network', '图片URL已回写数据库', { contentId: item.id, serverUrl })
        } else {
          logger.warn('system', '上传成功但未获取到服务器URL，跳过PATCH', {
            contentId: item.id,
            response: JSON.stringify(uploadRes)
          })
        }
        uni.showToast({ title: '图片上传成功', icon: 'success' })
        // 刷新列表以显示新图片
        fetchData()
      } catch (error) {
        logger.error('system', '焦点图图片上传失败', { contentId: item.id, error })
        uni.showToast({ title: '图片上传失败', icon: 'none' })
      }
    }
  })
}

// 删除焦点图
async function handleDelete(item: FeaturedContent) {
  logger.info('user', '准备删除焦点图', { id: item.id, title: item.title })
  uni.showModal({
    title: '确认删除',
    content: `确定删除焦点图"${item.title}"吗？`,
    confirmText: '删除',
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteFeaturedContent(item.id)
          logger.info('network', '焦点图删除成功', { id: item.id })
          uni.showToast({ title: '删除成功', icon: 'success' })
          fetchData()
        } catch (error) {
          logger.error('system', '焦点图删除失败', { contentId: item.id, error })
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

onMounted(() => {
  logger.info('system', '进入焦点图管理页')
  fetchData()
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.page-root {
  min-height: 100vh;
}

.featured-content-list-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-lg);
  box-sizing: border-box;

  /* 弹窗打开：只锁列表壳，弹窗在 page-root 下与其并列 */
  &.is-page-locked {
    position: fixed;
    left: 0;
    right: 0;
    width: 100%;
    overflow: hidden;
    height: 100vh;
  }
}

.page-header {
  margin-bottom: var(--spacing-md);

  .title {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-primary);
  }
}

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.btn-add {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 14px;
  background-color: var(--color-primary);
  border-radius: var(--border-radius-base);
  cursor: pointer;
  flex-shrink: 0;

  .btn-text {
    font-size: 13px;
    color: #ffffff;
  }
}

.list-tabs {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.list-tab {
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-base);
  background-color: var(--color-bg-primary);
  cursor: pointer;

  &.is-active {
    border-color: var(--color-primary);
    background-color: #e6f7ff;

    .tab-text {
      color: var(--color-primary);
      font-weight: 500;
    }
  }

  .tab-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.content-item {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-md);
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--color-border);
  gap: var(--spacing-md);
}

.item-image {
  width: 100%;
  height: 180px;
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  background-color: var(--color-bg-secondary);

  .cover-image {
    width: 100%;
    height: 100%;
  }
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.item-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  .item-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .status-tag {
    padding: 2px 8px;
    border-radius: var(--border-radius-sm);
    flex-shrink: 0;

    &.status-active {
      background-color: #e6f7ff;
      .status-text {
        color: #1890ff;
      }
    }

    &.status-inactive {
      background-color: #fff2f0;
      .status-text {
        color: #ff4d4f;
      }
    }

    &.status-pending {
      background-color: #fffbe6;
      .status-text {
        color: #ad6800;
      }
    }
  }
}

.item-target {
  .target-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .target-type-tag {
    padding: 2px 6px;
    background-color: var(--color-bg-secondary);
    border-radius: var(--border-radius-sm);
    flex-shrink: 0;

    .target-type-text {
      font-size: 11px;
      color: var(--color-text-secondary);
    }
  }

  .target-url {
    font-size: 12px;
    color: var(--color-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .target-name {
    font-size: 12px;
    color: var(--color-text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .target-none {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.item-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);

  .meta-text {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}

.item-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 12px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .btn-text {
    font-size: 12px;
  }

  &.btn-plain {
    background-color: transparent;
    border: 1px solid var(--color-border);

    .btn-text {
      color: var(--color-text-secondary);
    }
  }

  &.btn-delete {
    background-color: #fff2f0;
    border: 1px solid #ffccc7;

    .btn-text {
      color: #ff4d4f;
    }
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  background-color: var(--color-bg-primary);
  border-radius: var(--border-radius-base);

  .empty-text {
    font-size: 14px;
    color: var(--color-text-secondary);
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: var(--spacing-lg);
}

.pagination {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 16px;
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  cursor: pointer;

  .page-btn-text {
    font-size: 13px;
    color: var(--color-text-primary);
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.page-info {
  .page-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}
</style>
