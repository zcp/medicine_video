<template>
  <view class="create-live-page">
    <view class="create-live-container">
      <view class="section">
        <text class="section-title">基础信息</text>

        <view class="field">
          <view class="label-row">
            <text class="label"><text class="required">*</text>直播标题</text>
            <text class="meta">最多 60 字</text>
          </view>
          <input class="input" v-model="form.title" placeholder="请输入直播标题" maxlength="60" />
        </view>

        <view class="field">
          <view class="label-row">
            <text class="label">所属科室</text>
          </view>
          <view class="category-select" @tap="openCategoryPicker">
            <text class="category-select__text" :class="{ 'is-placeholder': !selectedCategoryName }">
              {{ selectedCategoryName || '请选择科室分类' }}
            </text>
            <text class="category-select__arrow">›</text>
          </view>
        </view>

        <view class="field">
          <view class="label-row">
            <text class="label">简介</text>
            <text class="meta">最多 2000 字</text>
          </view>
          <textarea class="textarea" v-model="form.summary" placeholder="请输入直播间简介，展示在详情页中" maxlength="2000" />
        </view>

        <view class="field">
          <view class="label-row">
            <text class="label">简介图片</text>
          </view>
          <view class="cover">
            <image v-if="introImagePreviewUrl" class="cover__img" :src="introImagePreviewUrl" mode="aspectFill" />
            <view v-else class="cover__placeholder">
              <text class="cover__placeholder-text">点击下方按钮选择简介图片</text>
            </view>
          </view>
          <view class="action-row">
            <text class="text-link" @tap="handlePickIntroImage">相册选择</text>
            <text class="text-link text-link--muted" @tap="handleClearIntroImage">清除</text>
            <input
              class="input input--inline"
              v-model="form.intro_image_url"
              placeholder="或输入网络图片地址"
              maxlength="500"
              @input="handleIntroImageUrlInput"
            />
          </view>
          <view class="hint-row">
            <text class="hint">展示在简介Tab中，支持从相册选择或输入网络图片地址</text>
          </view>
        </view>

        <view class="field">
          <view class="label-row">
            <text class="label">封面</text>
            <text class="meta">{{ coverSizeHint }}</text>
          </view>
          <view class="cover">
            <image v-if="coverPreviewUrl" class="cover__img" :src="coverPreviewUrl" mode="aspectFill" />
            <view v-else class="cover__placeholder">
              <text class="cover__placeholder-text">点击下方按钮选择封面</text>
            </view>
          </view>
          <view class="action-row">
            <text class="text-link" @tap="handlePickCover">相册选择</text>
            <text class="text-link text-link--muted" @tap="handleClearCover">清除</text>
            <input
              class="input input--inline"
              v-model="form.cover_url"
              placeholder="或输入网络图片地址"
              maxlength="500"
              @input="handleCoverUrlInput"
            />
          </view>
          <view class="hint-row">
            <text class="hint">支持从相册选择或输入网络图片地址</text>
          </view>
        </view>

        <view class="field">
          <view class="label-row">
            <text class="label">可见范围</text>
          </view>
          <view class="type-toggle" role="tablist" aria-label="可见范围">
            <view
              class="type-toggle__btn"
              :class="{ 'is-active': !form.is_private }"
              role="tab"
              aria-label="公开"
              @tap="form.is_private = false"
            >
              <text class="type-toggle__text">公开</text>
            </view>
            <view
              class="type-toggle__btn"
              :class="{ 'is-active': form.is_private }"
              role="tab"
              aria-label="不公开"
              @tap="form.is_private = true"
            >
              <text class="type-toggle__text">不公开</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">时间设置</text>

        <view class="field">
          <view class="label-row">
            <text class="label"><text class="required">*</text>创建类型</text>
          </view>
          <view class="type-toggle" role="tablist" aria-label="创建类型">
            <view
              class="type-toggle__btn"
              :class="{ 'is-active': creationMode === 'scheduled' }"
              role="tab"
              aria-label="预告"
              @tap="setCreationMode('scheduled')"
            >
              <text class="type-toggle__text">预告</text>
            </view>
            <view
              class="type-toggle__btn"
              :class="{ 'is-active': creationMode === 'live' }"
              role="tab"
              aria-label="直播"
              @tap="setCreationMode('live')"
            >
              <text class="type-toggle__text">直播</text>
            </view>
            <view
              class="type-toggle__btn"
              :class="{ 'is-active': creationMode === 'replay' }"
              role="tab"
              aria-label="回放"
              @tap="setCreationMode('replay')"
            >
              <text class="type-toggle__text">回放</text>
            </view>
          </view>
        </view>

        <view class="field">
          <view class="label-row">
            <text class="label"><text class="required">*</text>开始时间</text>
          </view>
          <view class="datetime-row">
            <picker mode="date" :value="startDate" @change="handleStartDateChange">
              <view class="datetime-pill">
                <text class="datetime-pill__text">{{ startDate }}</text>
              </view>
            </picker>
            <picker mode="time" :value="startTime" @change="handleStartTimeChange">
              <view class="datetime-pill">
                <text class="datetime-pill__text">{{ startTime }}</text>
              </view>
            </picker>
          </view>
        </view>

        <view v-if="creationMode === 'live'" class="field">
          <view class="label-row">
            <text class="label"><text class="required">*</text>直播地址</text>
            <text class="meta">最多 500 字符</text>
          </view>
          <input class="input" v-model="form.stream_url" placeholder="请输入直播推流地址" maxlength="500" />
          <view class="hint-row">
            <text class="hint">填写后直播间将立即开播</text>
          </view>
        </view>

        <view v-if="creationMode === 'replay'" class="field">
          <view class="label-row">
            <text class="label"><text class="required">*</text>回放地址</text>
            <text class="meta">最多 500 字符</text>
          </view>
          <input class="input" v-model="form.playback_url" placeholder="请输入可播放的视频地址" maxlength="500" />
          <view class="hint-row">
            <text class="hint">请输入可直接播放的视频地址</text>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">专家与品牌</text>

        <view class="field">
          <view class="label-row">
            <text class="label">关联专家</text>
            <text class="meta">已选 {{ selectedExpertIds.length }}</text>
          </view>
          <view class="associate-row">
            <button class="add-tile" @tap="openExpertPicker">
              <text class="add-tile__plus">+</text>
              <text class="add-tile__text">添加专家</text>
            </button>
            <view class="associated-panel">
              <view v-if="selectedExperts.length === 0" class="associated-placeholder">暂未关联专家</view>
              <view v-else class="chip-wrap">
                <view v-for="it in selectedExperts" :key="it.id" class="chip">
                  <text class="chip__text">{{ it.name }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view class="field">
          <view class="label-row">
            <text class="label">品牌介绍</text>
            <text class="meta">已选 {{ selectedBrandIds.length }}</text>
          </view>
          <view class="associate-row">
            <button class="add-tile" @tap="openBrandPicker">
              <text class="add-tile__plus">+</text>
              <text class="add-tile__text">添加品牌</text>
            </button>
            <view class="associated-panel">
              <view v-if="selectedBrands.length === 0" class="associated-placeholder">暂未关联品牌</view>
              <view v-else class="chip-wrap">
                <view v-for="it in selectedBrands" :key="it.id" class="chip">
                  <text class="chip__text">{{ it.name }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">标签</text>

        <view class="field">
          <view class="label-row">
            <text class="label">关联标签</text>
            <text class="meta">已选 {{ selectedTagIds.length }}/5</text>
          </view>

          <view class="chip-wrap tag-chip-wrap">
            <view v-if="selectedTags.length === 0" class="associated-placeholder">暂未关联标签</view>
            <view v-for="it in selectedTags" :key="it.id" class="chip chip--removable">
              <text class="chip__text">#{{ it.name }}</text>
              <text class="chip__remove" @tap.stop="toggleTag(it.id)">×</text>
            </view>
          </view>

          <view class="tag-draft-row">
            <input
              class="input input--tag-draft"
              v-model="tagDraft"
              placeholder="如 #心脏 #皮肤，空格或#分隔"
              maxlength="120"
              confirm-type="done"
              @confirm="commitTagDraft"
            />
            <button class="ghost-btn ghost-btn--small" type="button" @tap.stop="commitTagDraft">添加</button>
          </view>

          <view v-if="tagSuggestions.length > 0" class="tag-suggest">
            <view
              v-for="it in tagSuggestions"
              :key="it.id"
              class="tag-suggest__item"
              @tap="pickSuggestedTag(it)"
            >
              <text class="tag-suggest__text">#{{ it.name }}</text>
            </view>
          </view>

          <view class="hint-row hint-row--tag">
            <text class="hint">最多5个；点添加即自建，输入时可点下方相关词选用词库</text>
          </view>
        </view>
      </view>

      <view v-if="isEdit && editingRoomId" class="section">
        <text class="section-title">内容板块管理</text>
        <RoomTabManager :room-id="editingRoomId" />
      </view>

      <view v-if="!isEdit" class="section">
        <text class="section-title">内容板块</text>
        <view class="field">
          <text class="hint">创建成功后将自动创建一个 intro 类型的 Tab，可在编辑页面继续添加更多</text>
        </view>
      </view>

      <view class="bottom-space" />
    </view>

    <view class="bottom-bar">
      <view class="bottom-bar__inner">
        <button class="primary-btn" :disabled="submitting" @tap="handleSubmit">
          {{ submitting ? (isEdit ? '保存中...' : '创建中...') : (isEdit ? '保存修改' : '创建直播') }}
        </button>
      </view>
    </view>

    <!-- Expert Picker Popup -->
    <view v-if="showExpertPicker" class="picker-mask" @tap="closeExpertPicker" @touchmove.stop.prevent>
      <view class="picker picker--expert" @tap.stop="preventBubble" @touchmove.stop>
        <view class="picker__header">
          <text class="picker__title">选择专家</text>
          <button class="ghost-btn ghost-btn--small" @tap="closeExpertPicker">完成</button>
        </view>
        <view class="expert-picker">
          <view class="expert-picker__list-wrap">
            <input class="input input--search" v-model="expertKeyword" placeholder="搜索专家（姓名/医院/职称）" maxlength="60" />
            <scroll-view class="expert-picker__list" scroll-y>
              <view v-if="filteredExpertOptions.length === 0" class="picker-empty">暂无专家</view>
              <view
                v-for="it in filteredExpertOptions"
                :key="it.id"
                class="picker-item"
                :class="{ 'is-selected': selectedExpertIds.includes(it.id) }"
                @tap="toggleExpert(it.id)"
              >
                <view class="picker-item__checkbox" :class="{ 'is-checked': selectedExpertIds.includes(it.id) }">
                  <text v-if="selectedExpertIds.includes(it.id)" class="picker-item__checkmark">✓</text>
                </view>
                <view class="picker-item__text">
                  <text class="picker-item__title">{{ it.name }}</text>
                  <text v-if="it.title || it.hospital" class="picker-item__sub">{{ [it.title, it.hospital].filter(Boolean).join(' · ') }}</text>
                </view>
              </view>
            </scroll-view>
          </view>
          <view class="expert-picker__selected-wrap">
            <view class="expert-picker__selected-header">
              <text class="picker__subtitle">已选专家（{{ selectedExpertIds.length }}）</text>
            </view>
            <scroll-view class="expert-picker__selected" scroll-y>
              <view v-if="selectedExperts.length === 0" class="picker-empty">暂未选择专家</view>
              <view
                v-for="it in selectedExperts"
                :key="it.id"
                class="expert-picker__selected-item"
              >
                <view class="expert-picker__selected-info">
                  <text class="expert-picker__selected-name">{{ it.name }}</text>
                  <text v-if="it.title || it.hospital" class="expert-picker__selected-meta">{{ [it.title, it.hospital].filter(Boolean).join(' · ') }}</text>
                </view>
                <view class="expert-picker__remove" @tap.stop="toggleExpert(it.id)">
                  <text class="expert-picker__remove-text">移除</text>
                </view>
              </view>
            </scroll-view>
          </view>
        </view>
      </view>
    </view>

    <!-- Brand Picker Popup -->
    <view v-if="showBrandPicker" class="picker-mask" @tap="closeBrandPicker" @touchmove.stop.prevent>
      <view class="picker" @tap.stop="preventBubble" @touchmove.stop>
        <view class="picker__header">
          <text class="picker__title">选择品牌</text>
          <button class="ghost-btn ghost-btn--small" @tap="closeBrandPicker">完成</button>
        </view>
        <view class="picker__body">
          <view class="picker__left">
            <input class="input input--search" v-model="brandKeyword" placeholder="搜索品牌名称" maxlength="60" />
            <scroll-view class="picker__list" scroll-y>
              <view v-if="filteredBrandOptions.length === 0" class="picker-empty">暂无品牌</view>
              <view v-for="it in filteredBrandOptions" :key="it.id" class="picker-item" @tap="toggleBrand(it.id)">
                <view class="picker-item__text">
                  <text class="picker-item__title">{{ it.name }}</text>
                </view>
                <text v-if="selectedBrandIds.includes(it.id)" class="picker-item__checked">已选</text>
              </view>
            </scroll-view>
          </view>
          <view class="picker__right">
            <view class="picker__right-header">
              <text class="picker__subtitle">已关联（{{ selectedBrandIds.length }}）</text>
            </view>
            <scroll-view class="picker__selected" scroll-y>
              <view v-if="selectedBrands.length === 0" class="picker-empty">暂无</view>
              <view v-for="it in selectedBrands" :key="it.id" class="picker-selected-item">
                <text class="picker-selected-item__text">{{ it.name }}</text>
              </view>
            </scroll-view>
          </view>
        </view>
      </view>
    </view>

    <!-- Category Picker Popup -->
    <view v-if="showCategoryPicker" class="picker-mask" @tap="closeCategoryPicker" @touchmove.stop.prevent>
      <view class="picker" @tap.stop="preventBubble" @touchmove.stop>
        <view class="picker__header">
          <text class="picker__title">选择科室</text>
          <text class="text-link" @tap="closeCategoryPicker">关闭</text>
        </view>
        <view class="picker__body picker__body--single">
          <view class="picker__left" style="flex: 1; border-right: none;">
            <input class="input input--search" v-model="categoryKeyword" placeholder="搜索科室名称" maxlength="60" />
            <scroll-view class="picker__list" scroll-y>
              <view v-if="filteredCategoryOptions.length === 0" class="picker-empty">暂无科室</view>
              <view
                v-for="it in filteredCategoryOptions"
                :key="it.id"
                class="picker-item"
                :class="{ 'is-selected': selectedCategoryId === it.id }"
                @tap="selectCategory(it.id)"
              >
                <text class="picker-item__title">{{ it.name }}</text>
                <text v-if="selectedCategoryId === it.id" class="picker-item__checked">✓</text>
              </view>
            </scroll-view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import dayjs from 'dayjs'
import { logger } from '@/logs/logger'
import { useAuthStore } from '@/store/auth'
import { createRoom, deleteRoomSilent, getRoomById, getRoomBrandsTab, setAdminRoomBrands, updateRoom, uploadRoomCover } from '@/api/room'
import { getBrandList } from '@/api/brands'
import { getCategoryList, getRoomCategories, setRoomCategories } from '@/api/categories'
import { getAdminExpertList, getExpertList, getSessionExperts, setSessionExperts } from '@/api/expert'
import { createRoomSession, getRoomSessions, importSession, startSession, updateSession } from '@/api/session'
import { createTab, getTabs as getAdminTabs, updateTab, uploadTabImage } from '@/api/tabs'
import { getTags, getSessionTags, setSessionTags, resolveTag } from '@/api/tags'
import { SESSION_TAGS_MAX } from '@/types/tags'
import { upsertMyLiveCache } from '@/utils/myLiveCache'
import { resolveMediaUrl } from '@/utils/url'
import {
  handleContentSafetyError,
  getUserFacingErrorMessage,
  extractBusinessCode
} from '@/utils/contentSafety'
import RoomTabManager from '@/pages/admin/roomTab/RoomTabManager.vue'

const authStore = useAuthStore()

// V1.1：使用 tab_key 做系统级匹配
const EXPERT_INTRO_TAB_KEY = 'expert_intro'
const BRAND_INTRO_TAB_KEY = 'brand_intro'

/**
 * 在 Tab 列表中查找目标 Tab
 * 优先按 tab_key 匹配（V1.1），兜底按 title 匹配（兼容旧数据）
 */
function findTab(list: any[], tabKey: string, fallbackTitle?: string): any | undefined {
  return list.find((t) => String(t?.tab_key || '') === tabKey)
    || (fallbackTitle ? list.find((t) => String(t?.title || '') === fallbackTitle) : undefined)
}

function persistMyLiveRoom(roomId: string, status: 'live' | 'scheduled' | 'replay') {
  const normalizedRoomId = String(roomId || '').trim()
  if (!normalizedRoomId) return
  upsertMyLiveCache(authStore.userInfo?.user_id || null, {
    id: normalizedRoomId,
    title: form.title.trim(),
    summary: form.summary.trim(),
    cover_url: uploadedCoverUrl.value || form.cover_url.trim() || originalCoverUrl.value || '',
    status,
    created_at: isEdit.value ? undefined : new Date().toISOString()
  })
}

function getSessionExpertsBindWarning(error: any): string {
  if (error?.statusCode === 404) return '直播间已创建，但专家关联保存失败（接口不可用或环境路由未对齐）。'
  if (error?.statusCode === 403) return '直播间已创建，但当前账号暂无绑定场次专家权限，关联专家未保存。'
  return '直播间已创建，但关联专家未保存。'
}

const submitting = ref(false)

const isEdit = ref(false)
const editingRoomId = ref('')
const editingSessionId = ref('')

type CreationMode = 'scheduled' | 'live' | 'replay'
const creationMode = ref<CreationMode>('scheduled')

const form = reactive({
  title: '',
  summary: '',
  cover_url: '',
  intro_image_url: '',
  playback_url: '',
  stream_url: '',
  /** 仅链接可看（unlisted）：首页不可见，持链可看 */
  is_private: false
})

const coverTempPath = ref<string>('')
const uploadedCoverUrl = ref<string>('')
const originalCoverUrl = ref<string>('')

const introImageTempPath = ref<string>('')
const uploadedIntroImageUrl = ref<string>('')
const originalIntroImageUrl = ref<string>('')

type ExpertOption = { id: string; name: string; title?: string; hospital?: string }
type BrandOption = { id: string; name: string }
type TagOption = { id: string; name: string }
type CategoryOption = { id: string; name: string }

const expertOptions = ref<ExpertOption[]>([])
const brandOptions = ref<BrandOption[]>([])
const tagOptions = ref<TagOption[]>([])

const selectedExpertIds = ref<string[]>([])
const selectedBrandIds = ref<string[]>([])
const selectedTagIds = ref<string[]>([])
/** 与《02-V2》SESSION_TAGS_MAX 一致 */
const MAX_SESSION_TAGS = SESSION_TAGS_MAX
/** 标签草稿输入（#/空格分隔；未命中词库可 resolve 创建） */
const tagDraft = ref('')

const showExpertPicker = ref(false)
const showBrandPicker = ref(false)
const showCategoryPicker = ref(false)
const expertKeyword = ref('')
const brandKeyword = ref('')
const categoryKeyword = ref('')

const categoryOptions = ref<CategoryOption[]>([])
const selectedCategoryId = ref('')

const selectedExperts = computed(() => {
  const map = new Map(expertOptions.value.map((x) => [x.id, x]))
  return selectedExpertIds.value
    .map((id) => map.get(id) || { id, name: id })
    .filter((x) => x.id)
})

const selectedBrands = computed(() => {
  const map = new Map(brandOptions.value.map((x) => [x.id, x]))
  return selectedBrandIds.value
    .map((id) => map.get(id) || { id, name: id })
    .filter((x) => x.id)
})

const selectedTags = computed(() => {
  const map = new Map(tagOptions.value.map((x) => [x.id, x]))
  return selectedTagIds.value
    .map((id) => map.get(id) || { id, name: id })
    .filter((x) => x.id)
})

const filteredExpertOptions = computed(() => {
  const kw = expertKeyword.value.trim().toLowerCase()
  if (!kw) return expertOptions.value
  return expertOptions.value.filter((x) => {
    const hay = `${x.name} ${x.title || ''} ${x.hospital || ''}`.toLowerCase()
    return hay.includes(kw)
  })
})

const filteredBrandOptions = computed(() => {
  const kw = brandKeyword.value.trim().toLowerCase()
  if (!kw) return brandOptions.value
  return brandOptions.value.filter((x) => x.name.toLowerCase().includes(kw))
})

/** 输入联想：取草稿末段做包含匹配（未选中的词库项） */
const tagSuggestions = computed(() => {
  const raw = tagDraft.value
  if (!raw.trim()) return []
  const m = raw.match(/(?:^|[\s#])([^#\s]*)$/)
  const kw = String(m?.[1] || '').trim().toLowerCase()
  if (!kw) return []
  return tagOptions.value
    .filter((x) => !selectedTagIds.value.includes(x.id) && x.name.toLowerCase().includes(kw))
    .slice(0, 8)
})

const filteredCategoryOptions = computed(() => {
  const kw = categoryKeyword.value.trim().toLowerCase()
  if (!kw) return categoryOptions.value
  return categoryOptions.value.filter((x) => x.name.toLowerCase().includes(kw))
})

const selectedCategoryName = computed(() => {
  if (!selectedCategoryId.value) return ''
  const found = categoryOptions.value.find((x) => x.id === selectedCategoryId.value)
  return found ? found.name : ''
})

const startDate = ref(dayjs().add(1, 'hour').format('YYYY-MM-DD'))
const startTime = ref(dayjs().add(1, 'hour').format('HH:mm'))

const coverPreviewUrl = computed(() => {
  if (coverTempPath.value) return coverTempPath.value
  if (form.cover_url.trim()) return resolveMediaUrl(form.cover_url.trim())
  if (uploadedCoverUrl.value) return resolveMediaUrl(uploadedCoverUrl.value)
  return ''
})

const introImagePreviewUrl = computed(() => {
  if (introImageTempPath.value) return introImageTempPath.value
  if (form.intro_image_url.trim()) return resolveMediaUrl(form.intro_image_url.trim())
  if (uploadedIntroImageUrl.value) return resolveMediaUrl(uploadedIntroImageUrl.value)
  return ''
})

const maxUploadSizeLabel = computed(() => {
  // 不依赖 settings store（小程序侧拉取 system config 易缺模块/404）；文案固定提示即可
  return ''
})

const coverSizeHint = computed(() => {
  return maxUploadSizeLabel.value || '大小限制以系统配置为准'
})


function goLogin(redirectUrl = '/pages/live/CreateLive') {
  uni.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${encodeURIComponent(redirectUrl)}` })
}

function requireLogin(): boolean {
  if (authStore.isAuthenticated) return true
  const redirect = isEdit.value && editingRoomId.value
    ? `/pages/live/CreateLive?mode=edit&roomId=${encodeURIComponent(editingRoomId.value)}`
    : '/pages/live/CreateLive'
  goLogin(redirect)
  return false
}

async function loadEditData() {
  const roomId = editingRoomId.value
  if (!roomId) return

  try {
    const roomRes: any = await getRoomById(roomId)
    if (roomRes?.code === 200 && roomRes?.data) {
      const r: any = roomRes.data
      form.title = String(r?.title || r?.room_title || form.title || '')
      form.summary = String(r?.summary || form.summary || '')
      form.is_private = Boolean(r?.is_private)
      // 兜底：若未配置 Tab，则用房间 description 回填（纯文本）
      const desc = String(r?.description || '')
      if (!form.summary.trim() && desc.trim()) form.summary = desc

      const cover = String(r?.cover_url || r?.coverUrl || r?.cover || '')
      if (cover) {
        uploadedCoverUrl.value = cover
        originalCoverUrl.value = resolveMediaUrl(cover)
        // 编辑模式：回填URL输入框，让用户能看到已有的封面地址
        form.cover_url = cover
        coverTempPath.value = ''
      }

      // 回填科室分类
      const catId = String(r?.category_id || r?.categoryId || r?.category?.id || '')
      if (catId) {
        selectedCategoryId.value = catId
      } else {
        // 兜底：房间详情未返回分类字段时，通过关联接口获取
        try {
          const catRes: any = await getRoomCategories(roomId)
          const cats: any[] = Array.isArray(catRes?.data) ? catRes.data : (Array.isArray(catRes) ? catRes : [])
          if (cats.length > 0) {
            selectedCategoryId.value = String(cats[0]?.id || '')
          }
        } catch {
          // ignore
        }
      }
    }
  } catch {
    // ignore
  }

  // 读取最近一个场次（用于时间/专家绑定）
  try {
    const sessionsRes: any = await getRoomSessions(roomId, { page: 1, size: 1, sort_by: 'created_at', sort_order: 'desc' } as any)
    const list: any[] = Array.isArray(sessionsRes?.data?.items) ? sessionsRes.data.items : []
    const s0: any = list[0]
    if (s0?.id) {
      editingSessionId.value = String(s0.id)
      const t = dayjs(String(s0?.start_time || ''))
      if (t.isValid()) {
        startDate.value = t.format('YYYY-MM-DD')
        startTime.value = t.format('HH:mm')
      }

      const playback = String(s0?.playback_url || s0?.playbackUrl || '')
      const streamUrl = String(s0?.stream_url || s0?.streamUrl || s0?.stream_url?.url || '')
      if (playback) {
        creationMode.value = 'replay'
        form.playback_url = playback
        form.stream_url = ''
      } else {
        const st = String(s0?.status || '').toLowerCase()
        creationMode.value = streamUrl ? 'live' : (st === 'live' ? 'live' : 'scheduled')
        form.playback_url = ''
        form.stream_url = streamUrl
      }
    }
  } catch {
    // ignore
  }

  // 回填场次专家
  if (editingSessionId.value) {
    try {
      const exRes: any = await getSessionExperts(editingSessionId.value)
      const raw = exRes?.data
      const arr: any[] = Array.isArray(raw)
        ? raw
        : (raw && typeof raw === 'object' && Array.isArray((raw as any).items) ? (raw as any).items : [])
      const ids = arr.map((x) => String(x?.id || x?.expert_id || '')).filter(Boolean)
      selectedExpertIds.value = Array.from(new Set(ids))
    } catch {
      // ignore
    }
  }

  // 回填场次标签（公开接口）
  // 后端返回 TagItem[]（标签完整信息），data 为数组，不带 items 包装
  if (editingSessionId.value) {
    try {
      const tagRes: any = await getSessionTags(editingSessionId.value)
      const tags: any[] = tagRes?.data || []
      selectedTagIds.value = tags.map((t: any) => t.id).filter(Boolean)
      // 合并进词库选项，避免词库未加载完时 chip 只显示 id
      const merged = new Map(tagOptions.value.map((x) => [x.id, x]))
      for (const t of tags) {
        const id = String(t?.id || '')
        const name = String(t?.name || t?.tag_name || '')
        if (id && name) merged.set(id, { id, name })
      }
      tagOptions.value = Array.from(merged.values())
      logger.info('system', '场次标签回填完成', {
        sessionId: editingSessionId.value,
        tagCount: selectedTagIds.value.length
      })
    } catch (e) {
      logger.warn('system', '场次标签回填失败', { error: e })
    }
  }

  // 回填直播间品牌（公开接口）
  try {
    const brRes: any = await getRoomBrandsTab(roomId)
    const raw: any = brRes?.data
    const arr: any[] = Array.isArray(raw)
      ? raw
      : (raw && typeof raw === 'object' && Array.isArray(raw.room_brands) ? raw.room_brands : [])
    const ids = arr.map((x) => String((x as any)?.id || (x as any)?.brand_id || '')).filter(Boolean)
    selectedBrandIds.value = Array.from(new Set(ids))
  } catch {
    // ignore
  }

  // 回填简介Tab图片
  try {
    const tabsRes: any = await getAdminTabs(roomId)
    const tabList: any[] = extractAdminTabsList(tabsRes)
    const introTab = tabList.find((t: any) => String(t?.tab_key || '') === 'intro')
    if (introTab) {
      const img = String(introTab?.image_url || '')
      if (img) {
        uploadedIntroImageUrl.value = img
        originalIntroImageUrl.value = resolveMediaUrl(img)
        form.intro_image_url = img
        introImageTempPath.value = ''
      }
    }
  } catch {
    // ignore
  }
}

async function loadBrands() {
  try {
    const res = await getBrandList({ limit: 500 })
    const list = Array.isArray(res.data) ? res.data : []
    brandOptions.value = list
      .filter((x: any) => x?.is_active !== false)
      .map((x: any) => ({ id: String(x?.id || ''), name: String(x?.name || '') }))
      .filter((x) => x.id && x.name)
  } catch {
    brandOptions.value = []
  }
}

async function loadCategories() {
  try {
    const resp = await getCategoryList()
    const data = (resp as any)?.data ?? resp
    const items = Array.isArray(data) ? data : []
    categoryOptions.value = items
      .filter((c: any) => c?.is_active !== false)
      .sort((a: any, b: any) => (a?.sort_order ?? 0) - (b?.sort_order ?? 0))
      .map((c: any) => ({ id: String(c.id), name: String(c.name || '') }))
      .filter((x: any) => x.id && x.name)
  } catch {
    categoryOptions.value = []
  }
}

async function loadTags() {
  try {
    // 对齐《02-标签管理-后端设计文档》§3.1.1：GET /content/tags，公开；Query: q / search_type / include_inactive
    // 默认不传 include_inactive（后端默认 false=仅启用）
    const res = await getTags()
    // 响应 data：文档示例为 { items }；Schema 另有分页字段；汇总表亦写 TagItem[]——三种兼容
    const data: any = res?.data
    const list: any[] = Array.isArray(data)
      ? data
      : (Array.isArray(data?.items) ? data.items : [])
    tagOptions.value = list
      .map((x: any) => ({
        id: String(x?.id || ''),
        name: String(x?.name || '').trim()
      }))
      .filter((x: { id: string; name: string }) => x.id && x.name)
    logger.info('system', '标签词库加载完成', { count: tagOptions.value.length })
  } catch (e) {
    tagOptions.value = []
    logger.warn('system', '标签词库加载失败', { error: e })
  }
}

async function loadExperts() {
  try {
    const size = 100
    let page = 1
    let total = Infinity
    const all: ExpertOption[] = []

    while (all.length < total) {
      const res = await getAdminExpertList({ page, size })
      const data: any = res.data as any
      const items = Array.isArray(data?.items) ? data.items : []
      total = Number.isFinite(Number(data?.total)) ? Number(data.total) : all.length

      const mapped = items
        .map((x: any) => ({
          id: String(x?.id || x?.expert_id || ''),
          name: String(x?.name || ''),
          title: x?.title ? String(x.title) : undefined,
          hospital: x?.hospital ? String(x.hospital) : undefined
        }))
        .filter((x: any) => x.id && x.name)

      all.push(...mapped)

      if (items.length < size) break
      page += 1
      if (page > 20) break
    }

    const seen = new Set<string>()
    expertOptions.value = all.filter((x) => {
      if (!x.id || seen.has(x.id)) return false
      seen.add(x.id)
      return true
    })

    if (expertOptions.value.length > 0) return
  } catch {
    // ignore → fallback public list
  }

  try {
    const size = 50
    let page = 1
    let total = Infinity
    const all: ExpertOption[] = []

    while (all.length < total) {
      const res = await getExpertList({ page, size })
      const data: any = res.data as any
      const items = Array.isArray(data)
        ? data
        : (Array.isArray(data?.items) ? data.items : [])
      total = Number.isFinite(Number(data?.total)) ? Number(data.total) : all.length + (items.length < size ? 0 : items.length + 1)

      const mapped = items
        .map((x: any) => ({
          id: String(x?.id || ''),
          name: String(x?.name || ''),
          title: x?.title ? String(x.title) : undefined,
          hospital: x?.hospital ? String(x.hospital) : undefined
        }))
        .filter((x: any) => x.id && x.name)

      all.push(...mapped)
      if (items.length < size) break
      page += 1
      if (page > 20) break
    }

    const seen = new Set<string>()
    expertOptions.value = all.filter((x) => {
      if (!x.id || seen.has(x.id)) return false
      seen.add(x.id)
      return true
    })
  } catch {
    expertOptions.value = []
  }
}

/** 占位：配合 @tap.stop，阻止内容点击冒泡到遮罩（勿写裸 @tap.stop，小程序会找 method "false"） */
function preventBubble() {}

function openExpertPicker() {
  if (!requireLogin()) return
  showExpertPicker.value = true
  if (expertOptions.value.length === 0) loadExperts()
}

function closeExpertPicker() {
  showExpertPicker.value = false
  expertKeyword.value = ''
}

function toggleExpert(expertId: string) {
  const id = String(expertId || '')
  if (!id) return
  const current = selectedExpertIds.value
  if (current.includes(id)) {
    selectedExpertIds.value = current.filter((x) => x !== id)
  } else {
    selectedExpertIds.value = [...current, id]
  }
}

function openBrandPicker() {
  showBrandPicker.value = true
  if (brandOptions.value.length === 0) loadBrands()
}

function closeBrandPicker() {
  showBrandPicker.value = false
  brandKeyword.value = ''
}

function toggleBrand(brandId: string) {
  const id = String(brandId || '')
  if (!id) return
  const current = selectedBrandIds.value
  if (current.includes(id)) {
    selectedBrandIds.value = current.filter((x) => x !== id)
  } else {
    selectedBrandIds.value = [...current, id]
  }
}

function openCategoryPicker() {
  showCategoryPicker.value = true
  if (categoryOptions.value.length === 0) loadCategories()
}

function closeCategoryPicker() {
  showCategoryPicker.value = false
  categoryKeyword.value = ''
}

function selectCategory(id: string) {
  selectedCategoryId.value = id
  showCategoryPicker.value = false
  categoryKeyword.value = ''
}

function normalizeTagToken(raw: string): string {
  return String(raw || '').replace(/^#+/g, '').trim()
}

/** 按 # 或空白拆分；兼容 #皮肤#手臂 粘连写法 */
function parseTagTokens(raw: string): string[] {
  const s = String(raw || '').trim()
  if (!s) return []
  const parts = s
    .split(/[#\s]+/)
    .map(normalizeTagToken)
    .filter(Boolean)
  return Array.from(new Set(parts))
}

function findTagOptionByName(name: string): TagOption | undefined {
  const n = String(name || '').trim().toLowerCase()
  if (!n) return undefined
  return tagOptions.value.find((x) => x.name.toLowerCase() === n)
}

function tryAddTagId(tagId: string): boolean {
  const id = String(tagId || '')
  if (!id) return false
  if (selectedTagIds.value.includes(id)) return true
  if (selectedTagIds.value.length >= MAX_SESSION_TAGS) {
    uni.showToast({ title: '最多选择 5 个标签', icon: 'none' })
    return false
  }
  selectedTagIds.value = [...selectedTagIds.value, id]
  return true
}

/** resolve 名本地弱校验（《02》前端 v2.0 §7.1；最终以后端为准） */
function isValidResolveName(name: string): boolean {
  const n = String(name || '').trim()
  if (!n || n.length > 80) return false
  if (/[<>'";]/.test(n)) return false
  return true
}

function mergeTagOption(id: string, name: string) {
  const nid = String(id || '').trim()
  const nname = String(name || '').trim()
  if (!nid || !nname) return
  const merged = new Map(tagOptions.value.map((x) => [x.id, x]))
  merged.set(nid, { id: nid, name: nname })
  tagOptions.value = Array.from(merged.values())
}

/**
 * 创建并使用：POST /content/tags/resolve → 用返回 id 进 chip
 * 禁止伪造 UUID、禁止调 /admin/tags
 */
async function createAndUseTag(rawName: string): Promise<boolean> {
  const name = String(rawName || '').trim()
  if (!isValidResolveName(name)) {
    uni.showToast({ title: '标签名称不合法', icon: 'none' })
    return false
  }
  if (selectedTagIds.value.length >= MAX_SESSION_TAGS) {
    uni.showToast({ title: '最多选择 5 个标签', icon: 'none' })
    return false
  }
  try {
    const res: any = await resolveTag({ name })
    if (res?.code !== 200) throw Object.assign(new Error(res?.message || '无法使用该标签'), { code: res?.code })
    const data = res?.data
    if (!data?.id) throw new Error('empty resolve')
    mergeTagOption(String(data.id), String(data.name || name))
    if (!tryAddTagId(String(data.id))) return false
    if (data.created === true) {
      uni.showToast({ title: '已创建并使用', icon: 'none', duration: 1500 })
    }
    return true
  } catch (e: any) {
    if (handleContentSafetyError(e)) return false
    const code = extractBusinessCode(e)
    if (code === 4001 || code === 400) {
      const msg = getUserFacingErrorMessage(e, '该标签不可用，请换一个名称')
      uni.showToast({ title: msg, icon: 'none' })
      return false
    }
    uni.showToast({
      title: getUserFacingErrorMessage(e, '无法使用该标签'),
      icon: 'none'
    })
    return false
  }
}

/** 点添加：精确命中本地词库直接加 chip；否则直接 resolve 自建（不弹确认） */
async function commitTagDraft() {
  const tokens = parseTagTokens(tagDraft.value)
  if (!tokens.length) {
    uni.showToast({ title: '请先输入标签名', icon: 'none' })
    return
  }

  const unmatched: string[] = []
  for (const token of tokens) {
    const hit = findTagOptionByName(token)
    if (!hit) {
      unmatched.push(token)
      continue
    }
    if (!tryAddTagId(hit.id)) {
      // 已满：保留 draft 便于用户改
      return
    }
  }

  if (unmatched.length === 0) {
    tagDraft.value = ''
    return
  }

  // 未命中先留在 draft；失败时可改；成功逐个清掉
  tagDraft.value = unmatched.map((n) => `#${n}`).join(' ')

  for (const name of unmatched) {
    if (selectedTagIds.value.length >= MAX_SESSION_TAGS) {
      uni.showToast({ title: '最多选择 5 个标签', icon: 'none' })
      break
    }
    const used = await createAndUseTag(name)
    if (used) {
      const left = parseTagTokens(tagDraft.value).filter((t) => t.toLowerCase() !== name.toLowerCase())
      tagDraft.value = left.map((n) => `#${n}`).join(' ')
    }
    if (!used && selectedTagIds.value.length >= MAX_SESSION_TAGS) break
  }
}

function pickSuggestedTag(it: TagOption) {
  if (!it?.id) return
  tryAddTagId(it.id)
  // 清掉末段未完成输入，保留前面已解析意图由 chip 承接
  tagDraft.value = ''
}

function toggleTag(tagId: string) {
  const id = String(tagId || '')
  if (!id) return
  const current = selectedTagIds.value
  if (current.includes(id)) {
    selectedTagIds.value = current.filter((x) => x !== id)
  } else {
    tryAddTagId(id)
  }
}

function handleStartDateChange(e: any) {
  const v = String(e?.detail?.value || '')
  if (v) startDate.value = v
}

function handleStartTimeChange(e: any) {
  const v = String(e?.detail?.value || '')
  if (v) startTime.value = v
}

function handlePickCover() {
  if (!requireLogin()) return

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const path = res.tempFilePaths?.[0]
      if (typeof path === 'string' && path) {
        coverTempPath.value = path
        uploadedCoverUrl.value = ''
        form.cover_url = ''
      }
    }
  })
}

function handleCoverUrlInput() {
  if (form.cover_url.trim()) {
    coverTempPath.value = ''
    uploadedCoverUrl.value = ''
  }
}

function handleClearCover() {
  coverTempPath.value = ''
  form.cover_url = ''
  // 注意：编辑模式下 uploadedCoverUrl 可能是后端已有封面，这里不主动清空，避免误以为能”删除线上封面”
}

function handlePickIntroImage() {
  if (!requireLogin()) return

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const path = res.tempFilePaths?.[0]
      if (typeof path === 'string' && path) {
        introImageTempPath.value = path
        uploadedIntroImageUrl.value = ''
        form.intro_image_url = ''
      }
    }
  })
}

function handleIntroImageUrlInput() {
  if (form.intro_image_url.trim()) {
    introImageTempPath.value = ''
    uploadedIntroImageUrl.value = ''
  }
}

function handleClearIntroImage() {
  introImageTempPath.value = ''
  form.intro_image_url = ''
}


function buildStartTimeIso(): string {
  // 直播模式：视为“立即开播”，用当前时间避免被归类为预告
  if (creationMode.value === 'live') {
    return dayjs().toISOString()
  }

  const local = `${startDate.value} ${startTime.value}`
  const d = dayjs(local)
  if (!d.isValid()) throw new Error('请选择有效的开播时间')
  // 回放导入：允许选择历史时间；预告/直播：仍要求未来时间
  if (creationMode.value !== 'replay' && d.isBefore(dayjs())) throw new Error('开始时间不能早于当前本地时间')
  return d.toISOString()
}

function setCreationMode(mode: CreationMode) {
  creationMode.value = mode
  if (mode !== 'replay') {
    form.playback_url = ''
  }
  if (mode !== 'live') {
    form.stream_url = ''
  }
}

function extractRoomId(data: any): string {
  const id = String(data?.roomId || data?.id || '')
  return id
}

function extractSessionId(data: any): string {
  return String(data?.id || data?.sessionId || '')
}

function extractAdminTabsList(resp: any): any[] {
  const raw = resp?.data ?? resp
  if (Array.isArray(raw)) return raw
  if (raw && typeof raw === 'object') {
    if (Array.isArray((raw as any).items)) return (raw as any).items
    if (Array.isArray((raw as any).tabs)) return (raw as any).tabs
    if (Array.isArray((raw as any).list)) return (raw as any).list
    if (Array.isArray((raw as any).records)) return (raw as any).records
    const nested = (raw as any).data
    if (nested && typeof nested === 'object') {
      if (Array.isArray((nested as any).items)) return (nested as any).items
      if (Array.isArray((nested as any).tabs)) return (nested as any).tabs
      if (Array.isArray((nested as any).list)) return (nested as any).list
      if (Array.isArray((nested as any).records)) return (nested as any).records
      if (Array.isArray(nested)) return nested
    }
  }
  return []
}

function humanizeImageDownloadError(raw: unknown): string {
  const msg = String((raw as any)?.errMsg || (raw as any)?.message || raw || '')
  if (/Failed to fetch|ERR_FAILED|net::ERR|timeout|TIMED_OUT|不在.*合法域名|url not in domain|domain list/i.test(msg)) {
    return '图片下载失败：外链需加入小程序「downloadFile 合法域名」，或改用相册选图后再保存'
  }
  if (msg.trim()) {
    return `${msg}（外链请配置 downloadFile 合法域名且为 https；也可改用相册选图）`
  }
  return '图片URL下载失败（请配置 downloadFile 合法域名，或改用相册选图）'
}

function downloadToTempFile(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    uni.downloadFile({
      url,
      success: (res) => {
        const statusCode = Number((res as any)?.statusCode)
        if (Number.isFinite(statusCode) && statusCode >= 400) {
          reject(new Error(`图片URL下载失败（HTTP ${statusCode}），请确认 URL 可直接访问且为 https`))
          return
        }
        const path = (res as any)?.tempFilePath
        if (typeof path === 'string' && path) resolve(path)
        else reject(new Error('下载失败'))
      },
      fail: (err: any) => {
        reject(new Error(humanizeImageDownloadError(err)))
      }
    })
  })
}

/**
 * 封面/简介图统一：本地 temp 或需落盘的非外链路径 → 可上传的本地路径
 * 绝对 http(s) 外链不走本函数（由调用方直存 cover_url / image_url）
 */
async function prepareImageFileForUpload(opts: {
  tempPath?: string
  url?: string
}): Promise<string> {
  const temp = String(opts.tempPath || '').trim()
  if (temp) return ensureUploadableImagePath(temp, opts.url)

  const rawUrl = String(opts.url || '').trim()
  if (!rawUrl) return Promise.reject(new Error('图片为空'))
  if (/^https?:\/\//i.test(rawUrl)) {
    return Promise.reject(new Error('外链图片应直接保存 URL，无需下载上传'))
  }

  const normalizedUrl = resolveMediaUrl(rawUrl)
  const rawPath =
    normalizedUrl.startsWith('/static/') || normalizedUrl.startsWith('static/')
      ? await getStaticImageFilePath(normalizedUrl)
      : await downloadToTempFile(normalizedUrl)
  return ensureUploadableImagePath(rawPath, normalizedUrl)
}

/** 后端读出时对 http(s) 原样返回；此类 URL 前端直存，不强制 downloadFile */
function isAbsoluteHttpUrl(url: string): boolean {
  return /^https?:\/\//i.test(String(url || '').trim())
}

function getStaticImageFilePath(src: string): Promise<string> {
  const s = String(src || '').trim()
  if (!s) return Promise.reject(new Error('封面URL为空'))

  // #ifdef MP-WEIXIN
  return new Promise((resolve, reject) => {
    uni.getImageInfo({
      src: s,
      success: (res: any) => {
        const p = String(res?.path || res?.tempFilePath || '')
        if (p) resolve(p)
        else resolve(s)
      },
      fail: (err: any) => {
        const msg = String(err?.errMsg || err?.message || '')
        reject(new Error(msg || '读取本地封面图片失败'))
      }
    })
  })
  // #endif

  // #ifndef MP-WEIXIN
  return Promise.resolve(s)
  // #endif
}

function guessImageExtFromUrl(url: string): string {
  const clean = String(url || '').split('#')[0].split('?')[0]
  const m = clean.match(/\.(jpg|jpeg|png|webp|gif)$/i)
  return (m?.[1] || 'jpg').toLowerCase()
}

function ensureUploadableImagePath(tempPath: string, sourceUrl?: string): Promise<string> {
  const path = String(tempPath || '')
  if (!path) return Promise.reject(new Error('封面文件为空'))

  // 已有常见图片后缀则直接使用
  if (/\.(jpg|jpeg|png|webp|gif)$/i.test(path)) return Promise.resolve(path)

  // 小程序端：downloadFile 返回的 tempFilePath 可能没有后缀，部分后端会据此校验失败（如提示“检验文件失败”）
  const ext = guessImageExtFromUrl(String(sourceUrl || ''))
  const fsm = (uni as any).getFileSystemManager?.()
  const wxAny = (globalThis as any)?.wx
  const userDataPath = (wxAny && wxAny.env && wxAny.env.USER_DATA_PATH) ? String(wxAny.env.USER_DATA_PATH) : ''
  if (!fsm || !userDataPath) return Promise.resolve(path)

  const destPath = `${userDataPath}/cover_${Date.now()}.${ext}`
  return new Promise((resolve, reject) => {
    try {
      fsm.copyFile({
        srcPath: path,
        destPath,
        success: () => resolve(destPath),
        fail: (err: any) => {
          const msg = String(err?.errMsg || err?.message || '')
          reject(new Error(msg || '封面文件处理失败'))
        }
      })
    } catch (e: any) {
      reject(new Error(e?.message || '封面文件处理失败'))
    }
  })
}

function buildRoomDescription(): string {
  // 直播间 description 仅保留简短文字（避免与 Tab 内容混用容量）
  const summary = String(form.summary || '').trim()
  return summary || form.title.trim()
}

async function validateCoverFileSize(_filePath: string) {
  // CreateLive 不拉取 /system/config，避免强依赖 settings 模块；超限由后端校验兜底
}

async function upsertRoomFunctionalTab(
  roomId: string,
  tabKey: string,
  displayTitle: string,
  sortOrder: number
) {
  const tabsRes: any = await getAdminTabs(roomId)
  const list: any[] = extractAdminTabsList(tabsRes)
  // 优先 tab_key 匹配，兜底 title 兼容旧数据
  const existing = findTab(list, tabKey, displayTitle)

  if (existing?.id) {
    const r: any = await updateTab(String(existing.id), {
      tab_key: tabKey,
      title: displayTitle,
      content_type: existing.content_type || 'text',
      text_content: displayTitle,
      image_url: existing.image_url || undefined,
      sort_order: sortOrder
    })
    if (r?.code !== 200) throw new Error(r?.message || `更新功能性Tab失败（${displayTitle}）`)
    return
  }

  const c: any = await createTab(roomId, {
    tab_key: tabKey,
    title: displayTitle,
    content_type: 'text',
    text_content: displayTitle,
    sort_order: sortOrder
  })
  if (c?.code !== 200) throw new Error(c?.message || `创建功能性Tab失败（${displayTitle}）`)
}

async function handleSubmit() {
  if (!requireLogin()) return

  // V2 B5：仅限制新建；编辑已有房间不因 can_stream=false 剥夺
  if (!isEdit.value && authStore.isAdmin) {
    uni.showToast({ title: '管理员不可创建直播', icon: 'none' })
    return
  }
  if (!isEdit.value && !authStore.canCreateRoom) {
    uni.showToast({ title: '开播功能已被禁用', icon: 'none' })
    return
  }

  if (!form.title.trim()) {
    uni.showToast({ title: '请输入直播标题', icon: 'none' })
    return
  }

  submitting.value = true
  let createdRoomIdForRollback = ''
  try {
    // 约定：首位关联专家作为主播/featured expert
    const featuredExpertId = selectedExpertIds.value.length > 0 ? String(selectedExpertIds.value[0] || '').trim() : ''
    const startIso = buildStartTimeIso()
    const description = buildRoomDescription()

    // 先做“可前置校验”的工作，避免后续报错但 room 已创建
    const playbackUrl = form.playback_url.trim()
    if (creationMode.value === 'replay' && !playbackUrl) {
      uni.showToast({ title: '回放模式需要填写回放地址', icon: 'none' })
      return
    }

    const streamUrl = form.stream_url.trim()
    if (creationMode.value === 'live' && !streamUrl) {
      uni.showToast({ title: '直播模式需要填写直播地址', icon: 'none' })
      return
    }

    // 封面（可选）：相册 → uploadRoomCover；https?:// 外链 → 直存 cover_url（对齐后端）
    const coverUrl = form.cover_url.trim()
    const isCoverUnchanged = isEdit.value && coverUrl && uploadedCoverUrl.value
      && resolveMediaUrl(coverUrl) === resolveMediaUrl(uploadedCoverUrl.value)
    let preparedCoverFilePath = ''
    let directCoverUrl = ''
    if (!isCoverUnchanged && (coverTempPath.value || coverUrl)) {
      if (coverTempPath.value) {
        preparedCoverFilePath = await prepareImageFileForUpload({
          tempPath: coverTempPath.value,
          url: coverUrl
        })
        await validateCoverFileSize(preparedCoverFilePath)
      } else if (isAbsoluteHttpUrl(coverUrl)) {
        directCoverUrl = coverUrl
      } else {
        preparedCoverFilePath = await prepareImageFileForUpload({ url: coverUrl })
        await validateCoverFileSize(preparedCoverFilePath)
      }
    }

    const roomId = isEdit.value ? editingRoomId.value : ''

    if (isEdit.value) {
      if (!roomId) throw new Error('缺少 roomId')
      const up: any = await updateRoom(roomId, {
        title: form.title.trim(),
        description,
        summary: form.summary.trim() ? form.summary.trim() : undefined,
        category_id: selectedCategoryId.value || undefined,
        record_by_default: true,
        is_private: form.is_private,
        ...(directCoverUrl ? { cover_url: directCoverUrl } : {})
      })
      if (up?.code !== 200) throw new Error(up?.message || '保存失败')
      if (directCoverUrl) {
        uploadedCoverUrl.value = directCoverUrl
        originalCoverUrl.value = directCoverUrl
      }
    } else {
      const roomRes = await createRoom({
        title: form.title.trim(),
        description,
        summary: form.summary.trim() ? form.summary.trim() : undefined,
        category_id: selectedCategoryId.value || undefined,
        record_by_default: true,
        is_private: form.is_private,
        ...(directCoverUrl ? { cover_url: directCoverUrl } : {})
      })

      const createdRoomId = extractRoomId(roomRes.data)
      if (!createdRoomId) throw new Error('创建失败：未返回 roomId')
      editingRoomId.value = createdRoomId
      createdRoomIdForRollback = createdRoomId
      if (directCoverUrl) {
        uploadedCoverUrl.value = directCoverUrl
        originalCoverUrl.value = directCoverUrl
      }
    }

    const effectiveRoomId = editingRoomId.value
    if (!effectiveRoomId) throw new Error('保存失败：roomId 为空')

    // 保存科室分类关联（后端通过 live_room_categories 多对多表管理，不处理 room 表的 category_id）
    // 仅管理员可调用 setRoomCategories API
    if (authStore.isAdmin && selectedCategoryId.value) {
      try {
        await setRoomCategories(effectiveRoomId, {
          category_ids: [selectedCategoryId.value],
          mode: 'replace'
        } as any)
      } catch (e: any) {
        logger.warn('system', '设置直播间科室分类关联失败', { roomId: effectiveRoomId, error: e })
      }
    }

    // 本地封面：POST /rooms/{roomId}/cover
    if (preparedCoverFilePath) {
      const coverRes: any = await uploadRoomCover(effectiveRoomId, preparedCoverFilePath)
      if (coverRes?.code === 200) {
        uploadedCoverUrl.value = String(coverRes?.data?.cover_url || '')
        originalCoverUrl.value = resolveMediaUrl(uploadedCoverUrl.value)
      } else {
        throw new Error(coverRes?.message || '封面上传失败')
      }
    }

    let sessionId = editingSessionId.value
    let sessionExpertsBindWarning = ''
    let sessionExpertsBound = false

    if (creationMode.value === 'replay') {
      if (!playbackUrl) {
        uni.showToast({ title: '回放模式需要填写回放地址', icon: 'none' })
        return
      }

      if (sessionId) {
        const u: any = await updateSession(sessionId, {
          start_time: startIso,
          summary: form.summary.trim() ? form.summary.trim() : undefined,
          playback_url: playbackUrl,
          ...(featuredExpertId ? { featured_expert_id: featuredExpertId } : {})
        })
        if (u?.code !== 200) throw new Error(u?.message || '更新回放场次失败')
      } else {
        const s = await importSession(effectiveRoomId, {
          start_time: startIso,
          // 回放导入：用 finished 让后端/首页正确归类为回放（否则可能显示为预告）
          status: 'finished',
          end_time: startIso,
          playback_url: playbackUrl,
          title: form.title.trim(),
          description
        } as any)
        sessionId = extractSessionId(s.data)
        editingSessionId.value = sessionId

        // 回放导入接口可能不支持 featured_expert_id；导入后用 patch 补齐（若有选择专家）
        if (sessionId && featuredExpertId) {
          const u2: any = await updateSession(sessionId, { featured_expert_id: featuredExpertId })
          if (u2?.code !== 200) throw new Error(u2?.message || '更新回放场次专家失败')
        }
      }
    } else if (sessionId) {
      const u: any = await updateSession(sessionId, {
        start_time: startIso,
        summary: form.summary.trim() ? form.summary.trim() : undefined,
        ...(creationMode.value === 'live' && streamUrl ? { stream_url: streamUrl } : {}),
        ...(featuredExpertId ? { featured_expert_id: featuredExpertId } : {})
      })
      if (u?.code !== 200) throw new Error(u?.message || '更新场次失败')
    } else {
      const s = await createRoomSession(effectiveRoomId, {
        start_time: startIso,
        summary: form.summary.trim() ? form.summary.trim() : undefined,
        ...(featuredExpertId ? { featured_expert_id: featuredExpertId } : {})
      })
      sessionId = extractSessionId(s.data)
      editingSessionId.value = sessionId

      // 直播模式：写入直播地址（后端拉流）
      if (sessionId && creationMode.value === 'live' && streamUrl) {
        const uLive: any = await updateSession(sessionId, { stream_url: streamUrl } as any)
        if (uLive?.code !== 200) throw new Error(uLive?.message || '写入直播地址失败')
      }
    }

    if (!sessionId) throw new Error('场次保存失败：未返回 sessionId')

    let startedLive = false
    let liveStartError: any = null

    // 直播模式：创建后立即开播（后端拉流），确保状态为 live
    if (creationMode.value === 'live') {
      try {
        const startRes: any = await startSession(sessionId)
        if (startRes?.code !== 200) throw new Error(startRes?.message || '开播失败')
        startedLive = true
      } catch (e: any) {
        startedLive = false
        liveStartError = e
      }
    }

    // 绑定场次标签（房主或 Admin；replace；空数组清空）
    {
      try {
        const uniqueIds = Array.from(new Set(selectedTagIds.value.filter(Boolean))).slice(0, MAX_SESSION_TAGS)
        const tagRes: any = await setSessionTags(sessionId, { tag_ids: uniqueIds, mode: 'replace' })
        if (tagRes?.code !== 200) throw Object.assign(new Error(tagRes?.message || '设置标签失败'), { code: tagRes?.code })
      } catch (e: any) {
        if (handleContentSafetyError(e)) throw e
        const code = extractBusinessCode(e)
        if (code === 3003 || e?.statusCode === 403) {
          throw Object.assign(new Error('无权修改该场次标签'), { code: 3003, __handled: false })
        }
        throw e
      }
    }

    // 绑定场次专家（可选，多选，默认第一个为主讲）
    if (selectedExpertIds.value.length > 0) {
      const payload = selectedExpertIds.value.map((id, idx) => ({
        expert_id: id,
        role: (idx === 0 ? '主讲' : '嘉宾') as '主讲' | '主持' | '嘉宾',
        sort_order: idx
      }))
      try {
        const exRes: any = await setSessionExperts(sessionId, payload)
        if (exRes?.code !== 200) throw new Error(exRes?.message || '绑定专家失败')
        sessionExpertsBound = true
      } catch (e: any) {
        sessionExpertsBindWarning = getSessionExpertsBindWarning(e)
        logger.warn('system', 'set_session_experts_failed_after_room_saved', {
          roomId: effectiveRoomId,
          sessionId,
          selectedExpertIds: selectedExpertIds.value,
          statusCode: e?.statusCode,
          message: e?.message || e?.errMsg || null
        })
      }
    }

    // 绑定直播间品牌（可选）
    if (selectedBrandIds.value.length > 0) {
      const brRes: any = await setAdminRoomBrands(effectiveRoomId, selectedBrandIds.value)
      if (brRes?.code !== 200) throw new Error(brRes?.message || '绑定品牌失败')
    }

    // 创建/更新功能性Tab：LiveView 的 Tab 列表来自房间详情的 tabs
    // 简介图片：相册 → uploadTabImage；https?:// → 直存 image_url（对齐后端）
    let introImageUrl = ''
    const introUrl = form.intro_image_url.trim()
    const isIntroImageUnchanged = isEdit.value && introUrl && uploadedIntroImageUrl.value
      && resolveMediaUrl(introUrl) === resolveMediaUrl(uploadedIntroImageUrl.value)
    if (!isIntroImageUnchanged) {
      if (introImageTempPath.value) {
        try {
          const filePath = await prepareImageFileForUpload({
            tempPath: introImageTempPath.value,
            url: introUrl
          })
          const upRes: any = await uploadTabImage(effectiveRoomId, filePath)
          if (upRes?.data?.image_url) {
            introImageUrl = String(upRes.data.image_url)
            uploadedIntroImageUrl.value = introImageUrl
          } else {
            throw new Error(upRes?.message || '简介图片上传失败')
          }
        } catch (e) {
          logger.warn('system', '简介图片上传失败', { roomId: effectiveRoomId, error: e })
          throw (e instanceof Error ? e : new Error('简介图片上传失败'))
        }
      } else if (isAbsoluteHttpUrl(introUrl)) {
        introImageUrl = introUrl
        uploadedIntroImageUrl.value = introUrl
      } else if (introUrl) {
        try {
          const filePath = await prepareImageFileForUpload({ url: introUrl })
          const upRes: any = await uploadTabImage(effectiveRoomId, filePath)
          if (upRes?.data?.image_url) {
            introImageUrl = String(upRes.data.image_url)
            uploadedIntroImageUrl.value = introImageUrl
          } else {
            throw new Error(upRes?.message || '简介图片上传失败')
          }
        } catch (e) {
          logger.warn('system', '简介图片上传失败', { roomId: effectiveRoomId, error: e })
          throw (e instanceof Error ? e : new Error('简介图片上传失败'))
        }
      }
    } else {
      introImageUrl = uploadedIntroImageUrl.value
    }

    // 新建直播间时自动创建默认 intro Tab
    if (!isEdit.value) {
      try {
        await createTab(effectiveRoomId, {
          tab_key: 'intro',
          title: '简介',
          content_type: 'mixed',
          text_content: form.summary.trim() || form.title.trim(),
          image_url: introImageUrl || undefined,
          sort_order: 0,
          is_active: true
        })
      } catch (e) {
        if (handleContentSafetyError(e)) throw e
        logger.warn('system', '创建默认 intro Tab 失败', { roomId: effectiveRoomId, error: e })
      }
    } else if (introImageUrl) {
      // 编辑模式：更新已有 intro Tab 的图片
      try {
        const tabsRes: any = await getAdminTabs(effectiveRoomId)
        const tabList: any[] = extractAdminTabsList(tabsRes)
        const existingIntro = tabList.find((t: any) => String(t?.tab_key || '') === 'intro')
        if (existingIntro?.id) {
          await updateTab(String(existingIntro.id), {
            image_url: introImageUrl,
            content_type: existingIntro.content_type || 'mixed',
            text_content: form.summary.trim() || form.title.trim()
          })
        }
      } catch (e) {
        if (handleContentSafetyError(e)) throw e
        logger.warn('system', '更新 intro Tab 图片失败', { roomId: effectiveRoomId, error: e })
      }
    }
    if (sessionExpertsBound) {
      await upsertRoomFunctionalTab(effectiveRoomId, EXPERT_INTRO_TAB_KEY, '专家介绍', 1)
    }
    if (selectedBrandIds.value.length > 0) {
      await upsertRoomFunctionalTab(effectiveRoomId, BRAND_INTRO_TAB_KEY, '品牌介绍', 2)
    }

    persistMyLiveRoom(
      effectiveRoomId,
      creationMode.value === 'replay'
        ? 'replay'
        : creationMode.value === 'live' && startedLive
          ? 'live'
          : 'scheduled'
    )

    if (creationMode.value === 'live' && !startedLive) {
      logger.warn('system', 'startSession_after_create_failed', {
        roomId: effectiveRoomId,
        sessionId,
        isEdit: isEdit.value,
        statusCode: liveStartError?.statusCode,
        message: liveStartError?.message || liveStartError?.errMsg || null
      })

      const modalRes = await uni.showModal({
        title: isEdit.value ? '已保存（待开播）' : '已创建（待开播）',
        content: liveStartError?.statusCode === 404
          ? '直播间和场次已保存，但当前环境未成功开播。你可以留在本页稍后再次点击保存重试，或先回首页到“预告”中查看。'
          : '直播间和场次已保存，但开播未成功。你可以留在本页稍后再次点击保存重试，或先回首页到“预告”中查看。',
        confirmText: '留在本页',
        cancelText: '回首页'
      })

      if (modalRes.cancel) {
        if (isEdit.value) {
          uni.navigateBack({ delta: 1 })
        } else {
          uni.switchTab({ url: '/pages/home/Home' })
        }
      }
      return
    }

    const okTitle = creationMode.value === 'live'
      ? (startedLive
        ? (isEdit.value ? '已开播' : '已创建（直播中）')
        : (isEdit.value ? '已保存（待开播）' : '已创建（待开播）'))
      : (isEdit.value ? '已保存' : '创建成功')
    uni.showToast({ title: okTitle, icon: 'success' })

    if (sessionExpertsBindWarning) {
      setTimeout(() => {
        uni.showToast({ title: sessionExpertsBindWarning, icon: 'none', duration: 2500 })
      }, 350)
    }

    setTimeout(() => {
      if (isEdit.value) {
        uni.navigateBack({ delta: 1 })
        return
      }
      // 创建成功：回到首页（TabBar 页面必须用 switchTab）
      uni.switchTab({ url: '/pages/home/Home' })
    }, 300)
  } catch (e: any) {
    if (handleContentSafetyError(e)) return
    let rollbackNote = ''
    // 创建流程失败：若本次新建了 room，则尽量回滚删除，避免“既报错又创建”
    if (!isEdit.value && createdRoomIdForRollback) {
      try {
        const r: any = await deleteRoomSilent(createdRoomIdForRollback)
        if (r?.code === 200) rollbackNote = '（已自动回滚）'
      } catch {
        // ignore
      }
      // 房间删除后场次通常一并失效；必须清空，否则重试会误走 PATCH 旧 sessionId → 404
      if (editingRoomId.value === createdRoomIdForRollback) {
        editingRoomId.value = ''
      }
      editingSessionId.value = ''
    }
    uni.showToast({
      title: getUserFacingErrorMessage(e, isEdit.value ? '保存失败，请稍后再试' : '创建失败，请稍后再试') + rollbackNote,
      icon: 'none'
    })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadBrands()
  loadExperts()
  loadCategories()
  loadTags()
  // 说明：/settings/system 在部分环境下后端未部署，会产生 404 噪音。
  // 该配置仅用于上传大小“提示文案”，不影响创建流程；因此默认不在此页面强制拉取。
  // 如后端补齐该接口，可按需恢复调用。
})

onLoad((q: any) => {
  const mode = String(q?.mode || '')
  const rid = String(q?.roomId || q?.room_id || '').trim()
  if (mode === 'edit' && rid) {
    isEdit.value = true
    editingRoomId.value = rid
    try {
      uni.setNavigationBarTitle({ title: '编辑直播' })
    } catch {
      // ignore
    }
    // 异步回填（不阻塞渲染）
    loadEditData()
    return
  }

  // 新建模式：管理员不开放创建入口；普通用户受 can_stream 限制
  if (authStore.isAdmin) {
    uni.showToast({ title: '管理员不可创建直播', icon: 'none' })
    setTimeout(() => {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/profile/Profile' }) })
    }, 400)
    return
  }
  if (!authStore.canCreateRoom) {
    uni.showToast({ title: '开播功能已被禁用', icon: 'none' })
    setTimeout(() => {
      uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/profile/Profile' }) })
    }, 400)
  }
})
</script>

<style lang="scss" scoped>
@import '@/common/uni.scss';

.create-live-page {
  min-height: 100vh;
  background: #F7F8FA;
  color: var(--color-text-primary);
}

.create-live-container {
  width: 100%;
  padding: 24rpx 0 0;
  box-sizing: border-box;
}

// ── Cards ──
.section {
  margin: 0 24rpx 24rpx;
  padding: 32rpx;
  background: #FFFFFF;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: #1A1A1A;
  margin-bottom: 28rpx;
  letter-spacing: 0.5rpx;

  &::before {
    content: '';
    display: inline-block;
    width: 8rpx;
    height: 32rpx;
    background: linear-gradient(180deg, #0F766E, #27A79A);
    border-radius: 4rpx;
    flex-shrink: 0;
  }
}

.section-title--inline {
  margin-bottom: 0;

  &::before {
    display: none;
  }
}

.required {
  color: #F56C6C;
  margin-right: 4rpx;
}

// ── Fields ──
.field {
  margin-bottom: 28rpx;
  padding-bottom: 28rpx;
  border-bottom: 1rpx solid #F2F3F5;

  &:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }
}

.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.label {
  font-size: 28rpx;
  font-weight: 600;
  color: #1A1A1A;
}

.meta {
  font-size: 24rpx;
  color: #999;
}

// ── Collapsible ──
.collapsible-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8rpx 0;
}

.collapsible-arrow {
  font-size: 32rpx;
  color: #C0C4CC;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  transform: rotate(0deg);

  &.is-expanded {
    transform: rotate(90deg);
  }
}

.collapsible-body {
  padding-top: 16rpx;
}

// ── Type toggle (segmented control) ──
.type-toggle {
  display: flex;
  background: #F2F3F5;
  border-radius: 999rpx;
  padding: 6rpx;
}

.type-toggle__btn {
  flex: 1;
  padding: 20rpx 0;
  border: none;
  border-radius: 999rpx;
  background: transparent;
  text-align: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.type-toggle__btn.is-active {
  background: #FFFFFF;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
}

.type-toggle__text {
  font-size: 28rpx;
  color: #666;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.type-toggle__btn.is-active .type-toggle__text {
  color: #0F766E;
  font-weight: 700;
}

// ── Datetime picker ──
.datetime-row {
  display: flex;
  gap: 20rpx;
}

.datetime-pill {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 24rpx 20rpx;
  background: #F7F8FA;
  border-radius: 16rpx;
  border: 2rpx solid transparent;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:active {
    border-color: #0F766E;
    background: #F0FAF9;
  }
}

.datetime-pill__text {
  font-size: 28rpx;
  color: #1A1A1A;
  font-weight: 500;
}

// ── Associate row ──
.associate-row {
  display: flex;
  gap: 20rpx;
}

.add-tile {
  width: 160rpx;
  height: 140rpx;
  padding: 0;
  border: 3rpx dashed #D9D9D9;
  border-radius: 20rpx;
  background: #FAFBFC;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;

  &:active {
    border-color: #0F766E;
    background: #F0FAF9;
    transform: scale(0.96);
  }
}

.add-tile__plus {
  font-size: 44rpx;
  line-height: 44rpx;
  color: #0F766E;
  margin-bottom: 8rpx;
  font-weight: 300;
}

.add-tile__text {
  font-size: 22rpx;
  color: #999;
}

.associated-panel {
  flex: 1;
  min-height: 140rpx;
  border-radius: 20rpx;
  background: #F7F8FA;
  padding: 20rpx;
  box-sizing: border-box;
}

.associated-placeholder {
  font-size: 26rpx;
  color: #C0C4CC;
  padding: 12rpx 4rpx;
}

.chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 16rpx 28rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #E8F8F5, #F0FAF9);
  border: 1rpx solid rgba(15, 118, 110, 0.12);
}

.chip__text {
  font-size: 28rpx;
  color: #0F766E;
  font-weight: 600;
  line-height: 1.3;
}

.chip--removable {
  padding-right: 16rpx;
  gap: 8rpx;
}

.chip__remove {
  font-size: 28rpx;
  color: #0F766E;
  opacity: 0.65;
  padding: 0 8rpx;
  line-height: 1;
}

.tag-chip-wrap {
  margin-bottom: 16rpx;
  min-height: 56rpx;
}

.tag-draft-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.input--tag-draft {
  flex: 1;
}

.tag-suggest {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 12rpx;
}

.tag-suggest__item {
  padding: 10rpx 20rpx;
  border-radius: 12rpx;
  background: #F5F7FA;
  border: 1rpx solid #E4E7ED;
}

.tag-suggest__text {
  font-size: 24rpx;
  color: #606266;
}

.hint-row--tag {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 12rpx;
}

// ── Media / Cover preview ──
.media {
  width: 100%;
  height: 260rpx;
  border-radius: 20rpx;
  overflow: hidden;
  background: #F7F8FA;
}

.media__img {
  width: 100%;
  height: 100%;
}

.media__placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.media__placeholder-text {
  font-size: 26rpx;
  color: #C0C4CC;
}

.cover {
  width: 100%;
  height: 320rpx;
  border-radius: 20rpx;
  overflow: hidden;
  background: #F7F8FA;
  position: relative;
}

.cover__img {
  width: 100%;
  height: 100%;
}

.cover__placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  background: linear-gradient(180deg, #F7F8FA 0%, #EEF1F5 100%);
  border: 3rpx dashed #D9D9D9;
  border-radius: 20rpx;
  box-sizing: border-box;
}

.cover__placeholder-text {
  font-size: 26rpx;
  color: #C0C4CC;
}

// ── Action row & ghost button ──
.action-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
  margin-top: 20rpx;
}

.ghost-btn {
  height: 64rpx;
  line-height: 64rpx;
  padding: 0 28rpx;
  background: #F7F8FA;
  color: #666;
  border: none;
  border-radius: 999rpx;
  font-size: 24rpx;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:active {
    background: #EEF1F5;
    color: #333;
  }
}

.ghost-btn--small {
  padding: 0 24rpx;
  height: 56rpx;
  line-height: 56rpx;
  font-size: 24rpx;
  border-radius: 999rpx;
  background: #E8F8F5;
  color: #0F766E;
  border: none;
  font-weight: 600;
}

// ── Input fields ──
.input {
  height: 88rpx;
  border-radius: 16rpx;
  background: #F7F8FA;
  border: 2rpx solid transparent;
  padding: 0 24rpx;
  font-size: 28rpx;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:focus {
    background: #FFFFFF;
    border-color: #0F766E;
    box-shadow: 0 0 0 4rpx rgba(15, 118, 110, 0.08);
  }
}

.input--inline {
  flex: 1;
  padding: 0 24rpx;
}

.input--search {
  height: 72rpx;
  border-radius: 999rpx;
  padding-left: 28rpx;
  background: #F7F8FA;
}

.textarea {
  min-height: 200rpx;
  padding: 20rpx 24rpx;
  line-height: 1.6;
  border-radius: 16rpx;
  background: #F7F8FA;
  border: 2rpx solid transparent;
  font-size: 28rpx;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:focus {
    background: #FFFFFF;
    border-color: #0F766E;
    box-shadow: 0 0 0 4rpx rgba(15, 118, 110, 0.08);
  }
}

// ── Text link (plain) ──
.text-link {
  font-size: 28rpx;
  color: #0F766E;
  font-weight: 500;
  white-space: nowrap;

  &--muted {
    color: #999;
    font-weight: 400;
  }
}

// ── Category select ──
.category-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 24rpx;
  background: #F7F8FA;
  border-radius: 16rpx;
  border: 2rpx solid transparent;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:active {
    border-color: #0F766E;
    background: #F0FAF9;
  }
}

.category-select__text {
  font-size: 28rpx;
  color: #1A1A1A;

  &.is-placeholder {
    color: #C0C4CC;
  }
}

.category-select__arrow {
  font-size: 32rpx;
  color: #C0C4CC;
}

// ── Expert picker（上下布局，避免右侧窄栏把文字挤成竖排）──
.expert-picker {
  width: 100%;
  height: 78vh;
  max-height: 720px;
  min-height: 480px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.expert-picker__list-wrap {
  width: 100%;
  flex: 1;
  min-height: 0;
  padding: 24rpx 24rpx 16rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  border-bottom: 1rpx solid #F2F3F5;
}

.expert-picker__list {
  width: 100%;
  flex: 1;
  height: 0;
  min-height: 200rpx;
}

.expert-picker__selected-wrap {
  width: 100%;
  flex-shrink: 0;
  height: 400rpx;
  padding: 20rpx 24rpx 24rpx;
  box-sizing: border-box;
  background: #F7F8FA;
  display: flex;
  flex-direction: column;
}

.expert-picker__selected-header {
  width: 100%;
  margin-bottom: 12rpx;
  flex-shrink: 0;
}

.expert-picker__selected {
  width: 100%;
  height: 300rpx;
  flex-shrink: 0;
  box-sizing: border-box;
}

.expert-picker__selected-item {
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 20rpx;
  margin-bottom: 12rpx;
  background: #FFFFFF;
  border-radius: 16rpx;
}

.expert-picker__selected-info {
  flex: 1;
  width: 0;
  padding-right: 16rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.expert-picker__selected-name {
  display: block;
  width: 100%;
  font-size: 32rpx;
  font-weight: 600;
  color: #1A1A1A;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expert-picker__selected-meta {
  display: block;
  width: 100%;
  margin-top: 6rpx;
  font-size: 26rpx;
  color: #666;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expert-picker__remove {
  flex-shrink: 0;
  padding: 10rpx 20rpx;
  background: #FEF0F0;
  border-radius: 999rpx;
}

.expert-picker__remove-text {
  font-size: 26rpx;
  color: #F56C6C;
  line-height: 1.2;
}

// ── Picker enhancements ──
.picker__body--single {
  height: 50vh;
  max-height: 400px;
  min-height: 260px;
}

.picker-item.is-selected {
  background: #F0FAF9;
}

.picker-item__checkbox {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 3rpx solid #D9D9D9;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  flex-shrink: 0;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);

  &.is-checked {
    background: #0F766E;
    border-color: #0F766E;
  }
}

.picker-item__checkmark {
  font-size: 22rpx;
  color: #FFFFFF;
  font-weight: 700;
  line-height: 1;
}

.picker-selected-item__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.picker-selected-item__sub {
  font-size: 22rpx;
  color: #999;
  line-height: 1.4;
  word-break: break-all;
}

.picker-selected-item__remove {
  font-size: 24rpx;
  color: #F56C6C;
  flex-shrink: 0;
  margin-left: 12rpx;
}

// ── Hint text ──
.hint-row {
  margin-top: 12rpx;
}

.hint {
  font-size: 24rpx;
  color: #B0B3B8;
  line-height: 1.5;
}

.bottom-space {
  height: 180rpx;
}

// ── Picker modal ──
.picker-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: flex-end;
  padding: 0;
  box-sizing: border-box;
}

.picker {
  width: 100%;
  max-height: 80vh;
  background: #FFFFFF;
  border-radius: 32rpx 32rpx 0 0;
  overflow: hidden;
  box-shadow: 0 -8rpx 40rpx rgba(0, 0, 0, 0.12);
}

.picker--expert {
  max-height: 90vh;
}

.picker__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
  border-bottom: 1rpx solid #F2F3F5;
}

.picker__title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1A1A1A;
}

.picker__body {
  display: flex;
  height: 60vh;
  max-height: 480px;
  min-height: 320px;
}

.picker__left {
  flex: 1;
  padding: 24rpx;
  box-sizing: border-box;
  border-right: 1rpx solid #F2F3F5;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  min-height: 0;
}

.picker__right {
  width: 36%;
  padding: 24rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: #F7F8FA;
}

.picker__right-header {
  margin-bottom: 16rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #F2F3F5;
}

.picker__subtitle {
  font-size: 26rpx;
  font-weight: 600;
  color: #666;
}

.picker__list {
  flex: 1;
  height: 100%;
  min-height: 0;
}

.picker__selected {
  flex: 1;
  height: 100%;
  min-height: 0;
}

.picker-item {
  display: flex;
  align-items: center;
  padding: 20rpx 12rpx;
  border-bottom: 1rpx solid #F7F8FA;
  border-radius: 12rpx;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);

  &:active {
    background: #F0FAF9;
  }
}

.picker-item__text {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  flex: 1;
  min-width: 0;
}

.picker-item__title {
  font-size: 28rpx;
  color: #1A1A1A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-item__sub {
  font-size: 24rpx;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-item__checked {
  font-size: 28rpx;
  color: #0F766E;
  font-weight: 700;
  margin-left: 16rpx;
}

.picker-selected-item {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  padding: 16rpx 12rpx;
  border-bottom: 1rpx solid #F2F3F5;
}

.picker-selected-item__text {
  font-size: 26rpx;
  color: #1A1A1A;
  word-break: break-all;
}

.picker-empty {
  padding: 40rpx 12rpx;
  font-size: 26rpx;
  color: #C0C4CC;
  text-align: center;
}

// ── Bottom bar & primary button ──
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 0 -2rpx 20rpx rgba(0, 0, 0, 0.06);
  box-sizing: border-box;
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

.bottom-bar__inner {
  width: 100%;
  margin: 0;
  padding: 20rpx 32rpx;
  box-sizing: border-box;
}

.primary-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #159488 0%, #0F766E 50%, #0B5C56 100%);
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 700;
  border: none;
  box-shadow: 0 8rpx 32rpx rgba(15, 118, 110, 0.35);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 2rpx;

  &:active {
    transform: scale(0.97);
    box-shadow: 0 4rpx 16rpx rgba(15, 118, 110, 0.25);
  }

  &[disabled] {
    opacity: 0.45;
    box-shadow: none;
    background: linear-gradient(135deg, #B0B3B8 0%, #999 100%);
  }
}
</style>
