<template>
  <view class="all-categories-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="all-categories-page__header">
      <view class="header__left" @click="handleBack">
        <text class="header__back">返回</text>
      </view>
      <text class="header__title">全部科室</text>
      <view class="header__right" @click="handleDone">
        <text :class="['header__done', { 'is-disabled': saving }]">完成</text>
      </view>
    </view>

    <view class="all-categories-page__search">
      <input
        v-model="keyword"
        class="search__input"
        placeholder="搜索科室名称"
        confirm-type="search"
      />
    </view>

    <view class="all-categories-page__section">
      <view class="section__title">
        <text>我的关注科室 (最多5个)</text>
      </view>

      <view v-if="draftPinnedCategories.length" class="pinned-list">
        <view v-for="c in draftPinnedCategories" :key="c.id" class="pinned-item">
          <text class="pinned-item__name">⭐ {{ c.name }}</text>
          <text class="pinned-item__remove" @click="togglePin(c.id)">×</text>
        </view>
      </view>

      <view v-else class="section__empty">
        <text class="empty__text">还没有固定任何科室</text>
      </view>
    </view>

    <view class="all-categories-page__section">
      <view class="section__title">
        <text>全部科室</text>
      </view>

      <view v-if="filteredCategories.length" class="category-list">
        <view v-for="c in filteredCategories" :key="c.id" class="category-item">
          <text class="category-item__name">{{ c.name }}</text>
          <text
            :class="['category-item__pin', { 'is-disabled': !isPinned(c.id) && draftPinnedIds.length >= 5 }]"
            @click="togglePin(c.id)"
          >
            {{ isPinned(c.id) ? '★' : '☆' }}
          </text>
        </view>
      </view>

      <view v-else class="section__empty">
        <text class="empty__text">暂无匹配科室</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { logger } from '@/logs/logger'
import { getCategoryList } from '@/api/categories'
import type { Category } from '@/types/category'
import { usePreferencesStore } from '@/store/preferences'

const statusBarHeight = (() => {
  // #ifdef MP-WEIXIN
  try {
    const windowInfo = (wx as any).getWindowInfo?.()
    return windowInfo?.statusBarHeight || 0
  } catch {
    return 0
  }
  // #endif

  // #ifndef MP-WEIXIN
  return uni.getSystemInfoSync().statusBarHeight || 0
  // #endif
})()

const preferencesStore = usePreferencesStore()

const categories = ref<Category[]>([])
const keyword = ref('')

const draftPinnedIds = ref<string[]>([])
const saving = computed(() => preferencesStore.saving)

const categoryNameMap = computed(() => {
  const map = new Map<string, string>()
  categories.value.forEach(c => {
    if (c?.id) map.set(String(c.id), String(c.name || ''))
  })
  return map
})

const draftPinnedCategories = computed(() => {
  return draftPinnedIds.value
    .map(id => ({ id, name: categoryNameMap.value.get(id) || '未知科室' }))
    .filter(v => v.id)
})

const filteredCategories = computed(() => {
  const kw = keyword.value.trim()
  const list = categories.value
    .filter(c => !!c?.id)
    .filter(c => (c.is_active ?? true) === true)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))

  const filtered = kw
    ? list.filter(c => String(c.name || '').includes(kw))
    : list

  // 未固定的排在前面（方便找可固定项）
  return filtered.sort((a, b) => {
    const ap = isPinned(String(a.id)) ? 1 : 0
    const bp = isPinned(String(b.id)) ? 1 : 0
    return ap - bp
  })
})

function isPinned(id: string) {
  return draftPinnedIds.value.includes(id)
}

function summarizeCategory(category: Pick<Category, 'id' | 'name' | 'slug' | 'is_active' | 'sort_order'>) {
  return {
    id: category.id,
    name: category.name,
    slug: category.slug,
    is_active: category.is_active,
    sort_order: category.sort_order
  }
}

function togglePin(id: string) {
  if (!id) return

  if (isPinned(id)) {
    logger.info('user', '取消固定科室', { categoryId: id, beforeIds: [...draftPinnedIds.value] })
    draftPinnedIds.value = draftPinnedIds.value.filter(x => x !== id)
    // 点星即时反映到首页 Tab（返回后可见）；离开页时再落库
    preferencesStore.setPinnedCategoriesLocal(draftPinnedIds.value)
    uni.showToast({ title: '已取消固定', icon: 'success' })
    return
  }

  if (draftPinnedIds.value.length >= 5) {
    logger.warn('system', '固定科室数量已达上限', { categoryId: id, currentIds: [...draftPinnedIds.value] })
    uni.showToast({ title: '最多固定5个科室，请先取消其他科室', icon: 'none' })
    return
  }

  logger.info('user', '固定科室到首页', { categoryId: id, beforeIds: [...draftPinnedIds.value] })
  draftPinnedIds.value = [...draftPinnedIds.value, id]
  preferencesStore.setPinnedCategoriesLocal(draftPinnedIds.value)
  uni.showToast({ title: '已固定到首页', icon: 'success' })
}

async function persistAndLeave(source: 'done' | 'back') {
  logger.info('network', '保存固定科室配置', {
    source,
    pinnedIds: [...draftPinnedIds.value]
  })
  try {
    // 点星已写本地；返回时 silent，避免与「已固定」Toast 叠弹
    await preferencesStore.savePinnedCategories(draftPinnedIds.value, { silent: source === 'back' })
    logger.info('network', '固定科室配置保存完成', {
      source,
      pinnedIds: [...draftPinnedIds.value]
    })
    uni.navigateBack()
  } catch {
    // savePinnedCategories 已 toast；停留本页可重试
  }
}

async function handleBack() {
  logger.info('user', '返回上一页 - 全部科室页')
  // 未点「完成」直接返回也落库，避免刷新后星标丢失
  await persistAndLeave('back')
}

async function handleDone() {
  await persistAndLeave('done')
}

onMounted(async () => {
  logger.info('system', '进入全部科室页')
  await preferencesStore.fetchPreferences({ force: true })
  draftPinnedIds.value = [...preferencesStore.pinnedCategoryIds]

  try {
    logger.info('network', '加载全部科室列表', { limit: 200 })
    const resp = await getCategoryList(200)
    const data = (resp as any)?.data ?? resp
    const items = Array.isArray(data) ? data : []

    categories.value = items.filter((c: any) => c?.is_active !== false)

    logger.info('network', '全部科室列表加载完成', {
      count: categories.value.length,
      sample: categories.value.slice(0, 5).map((item: any) => summarizeCategory(item))
    })
  } catch (error) {
    categories.value = []
    logger.error('system', '加载全部科室列表失败', { error })
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.all-categories-page {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);

  &__header {
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
    background-color: var(--color-bg-primary);
    border-bottom: 1px solid var(--color-border);
  }
}

.header__left,
.header__right {
  width: 80px;
  display: flex;
  align-items: center;
}

.header__left {
  justify-content: flex-start;
}

.header__right {
  justify-content: flex-end;
}

.header__back {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.header__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header__done {
  font-size: 14px;
  color: var(--color-primary);

  &.is-disabled {
    color: var(--color-text-tertiary);
  }
}

.all-categories-page__search {
  padding: 12px;
  background-color: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
}

.search__input {
  height: 36px;
  padding: 0 12px;
  background-color: var(--color-bg-secondary);
  border-radius: 18px;
  font-size: 14px;
  color: var(--color-text-primary);
}

.all-categories-page__section {
  margin-top: 12px;
  background-color: var(--color-bg-primary);
}

.section__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  font-size: 14px;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
}

.section__edit {
  font-size: 14px;
  color: var(--color-primary);
}

.section__empty {
  padding: 16px 12px;
}

.empty__text {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.pinned-list,
.category-list {
  padding: 4px 0;
}

.pinned-item,
.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--color-border);
}

.pinned-item__name,
.category-item__name {
  font-size: 14px;
  color: var(--color-text-primary);
}

.pinned-item__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.pinned-item__remove {
  margin-left: 12px;
  font-size: 18px;
  color: var(--color-text-tertiary);
}

.category-item__pin {
  font-size: 16px;
  color: var(--color-primary);

  &.is-disabled {
    color: var(--color-text-tertiary);
  }
}
</style>
