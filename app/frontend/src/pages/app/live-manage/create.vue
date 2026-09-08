<template>
  <view class="create-live-page">
    <!-- 滚动内容区 -->
    <scroll-view scroll-y class="page-content">
      <!-- 基础信息（标题、简介、封面） -->
      <view class="form-section">
        <view class="section-title">基础信息</view>
        
        <!-- 直播标题（必填） -->
        <view class="form-item">
          <view class="item-label">
            <text>直播标题</text>
            <text class="required">*</text>
          </view>
          <input 
            class="item-input"
            v-model="formData.title"
            placeholder="请输入直播标题，100字以内"
            maxlength="100"
            :class="{ 'error': errors.title }"
          />
          <text v-if="errors.title" class="error-text">{{ errors.title }}</text>
          <view class="char-count">{{ formData.title.length }}/100</view>
        </view>
        
        <!-- 直播简介（非必填） -->
        <view class="form-item">
          <view class="item-label">
            <text>直播简介</text>
          </view>
          <textarea 
            class="item-textarea"
            v-model="formData.description"
            placeholder="请输入直播简介，500字以内"
            maxlength="500"
            :auto-height="true"
            :class="{ 'error': errors.description }"
          />
          <text v-if="errors.description" class="error-text">{{ errors.description }}</text>
          <view class="char-count">{{ formData.description.length }}/500</view>
        </view>
        
        <!-- 简介图片（单图+双模式） -->
        <view class="form-item">
          <view class="item-label">
            <text>简介图片</text>
            <text class="desc-images-tip">（选填）</text>
          </view>
          
          <!-- 模式切换 -->
          <view class="image-mode-tabs">
            <view 
              class="tab-item" 
              :class="{ 'active': introImageMode === 'local' }"
              @click="introImageMode = 'local'"
            >
              本地上传
            </view>
            <view 
              class="tab-item" 
              :class="{ 'active': introImageMode === 'url' }"
              @click="introImageMode = 'url'"
            >
              输入链接
            </view>
          </view>
          
          <!-- 本地上传 -->
          <view v-if="introImageMode === 'local'" class="cover-upload" @click="handleUploadIntroImage">
            <view v-if="formData.intro_image_url" class="cover-preview">
              <image :src="formData.intro_image_url" mode="aspectFill" />
              <view class="cover-remove" @click.stop="clearIntroImage">
                <text class="remove-icon">✕</text>
              </view>
            </view>
            <view v-else class="cover-btn">
              <text class="upload-icon iconfont icon-add"></text>
              <text class="upload-text">上传图片</text>
              <text class="upload-tip">用于直播图文介绍</text>
            </view>
          </view>
          
          <!-- 输入URL -->
          <view v-if="introImageMode === 'url'" class="cover-url-input">
            <input 
              class="item-input"
              v-model="formData.intro_image_url"
              placeholder="请输入图片URL"
              @input="handleIntroImageUrlInput"
            />
            <view v-if="formData.intro_image_url" class="cover-preview-small">
              <image :src="formData.intro_image_url" mode="aspectFill" @error="handleIntroImageUrlError" />
            </view>
          </view>
        </view>
        
        <!-- 直播封面（可选） -->
        <view class="form-item">
          <view class="item-label">
            <text>直播封面</text>
          </view>
          
          <!-- 封面上传方式选择 -->
          <view class="cover-upload-tabs">
            <view 
              class="tab-item" 
              :class="{ 'active': coverUploadMode === 'album' }"
              @click="handleCoverModeChange('album')"
            >
              <text>本地上传</text>
            </view>
            <view 
              class="tab-item" 
              :class="{ 'active': coverUploadMode === 'url' }"
              @click="handleCoverModeChange('url')"
            >
              <text>输入链接</text>
            </view>
          </view>
          
          <!-- 从相册选择 -->
          <view v-if="coverUploadMode === 'album'" class="cover-upload">
            <view v-if="formData.cover_url" class="cover-preview">
              <image :src="formData.cover_url" mode="aspectFill" />
              <view class="cover-remove" @click="removeCover">
                <text class="remove-icon">✕</text>
              </view>
            </view>
            <view v-else class="cover-btn" @click="handleUploadCover">
              <text class="upload-icon iconfont icon-add"></text>
              <text class="upload-text">上传封面</text>
              <text class="upload-tip">建议尺寸：16:9</text>
            </view>
          </view>
          
          <!-- 输入URL -->
          <view v-if="coverUploadMode === 'url'" class="cover-url-input">
            <input 
              class="item-input"
              v-model="formData.cover_url"
              placeholder="请输入图片URL，如：https://example.com/cover.jpg"
              @input="handleCoverUrlInput"
              @blur="handleCoverUrlBlur"
            />
            <view v-if="formData.cover_url" class="cover-preview-small">
              <image :src="formData.cover_url" mode="aspectFill" @error="handleCoverUrlError" />
            </view>
          </view>
        </view>
      </view>
      
      <!-- 时间设置 -->
      <view class="form-section">
        <view class="section-title">时间设置</view>
        
        <!-- 播放地址（必填） -->
        <view class="form-item">
          <view class="item-label">
            <text>播放地址</text>
            <text class="required">*</text>
          </view>
          <input 
            class="item-input"
            v-model="formData.playback_url"
            placeholder="请输入播放地址（支持m3u8/mp4格式）"
            @blur="handlePlaybackUrlBlur"
            :class="{ 'error': errors.playback_url }"
          />
          <text v-if="errors.playback_url" class="error-text">{{ errors.playback_url }}</text>
          <view class="tip-text">外部直播/回放播放地址（m3u8），创建后按所选状态播放</view>
        </view>
        
        <!-- 创建为（填写播放地址后显示） -->
        <view v-if="formData.playback_url" class="form-item">
          <view class="item-label">
            <text>创建为</text>
          </view>
          <view class="image-mode-tabs">
            <view 
              v-for="(option, index) in createModeOptions"
              :key="index"
              class="tab-item" 
              :class="{ 'active': createModeIndex === index }"
              @click="createModeIndex = index; handleCreateModeChange({detail:{value:index}})"
            >
              <text>{{ option.label }}</text>
            </view>
          </view>
          <view class="tip-text">{{ createModeOptions[createModeIndex].tip }}</view>
        </view>
        
        <!-- 开始时间（仅预告模式需要选择；直播中/回放默认当前时间，无定时开播语义） -->
        <view class="form-item" v-if="formData.status === 'scheduled'">
          <view class="item-label">
            <text>开始时间</text>
            <text class="required">*</text>
          </view>
          <wd-datetime-picker
            v-model="startTimeTs"
            type="datetime"
            title="选择开始时间"
            :z-index="3000"
            :min-date="minStartTime"
          >
            <view class="item-picker">
              <text :class="{ 'placeholder': !formData.start_time }">
                {{ startTimeDisplay }}
              </text>
              <text class="picker-arrow">›</text>
            </view>
          </wd-datetime-picker>
          <text v-if="errors.start_time" class="error-text">{{ errors.start_time }}</text>
        </view>
      </view>
      
      <!-- 专家与品牌 -->
      <view class="form-section">
        <view class="section-title">专家与品牌</view>
        
        <!-- 选择专家（可选，支持多专家） -->
        <view class="form-item">
          <view class="item-label">
            <text>选择专家</text>
            <text v-if="selectedExperts.length > 0" class="item-count">{{ selectedExperts.length }}/{{ MAX_EXPERTS }}</text>
          </view>
          <view v-for="(expert, idx) in selectedExperts" :key="expert.id" class="multi-card">
            <ProxyAvatarImage :src="expert.avatar_url" shape="circle" size="72rpx" />
            <view class="multi-card-info">
              <text class="multi-card-name">{{ expert.name }}</text>
              <text class="multi-card-sub">{{ idx === 0 ? '主讲' : '嘉宾' }}{{ expert.title ? ' · ' + expert.title : '' }}</text>
            </view>
            <text class="remove-icon" @click.stop="removeExpert(idx)">✕</text>
          </view>
          <view v-if="selectedExperts.length < MAX_EXPERTS" class="add-btn" @click="handleOpenExpertPicker">
            <text class="add-icon">+</text>
            <text>添加专家</text>
          </view>
        </view>
        
        <!-- 选择品牌（可选，支持多品牌） -->
        <view class="form-item">
          <view class="item-label">
            <text>关联品牌</text>
            <text v-if="selectedBrands.length > 0" class="item-count">{{ selectedBrands.length }}/{{ MAX_BRANDS }}</text>
          </view>
          <view v-for="(brand, idx) in selectedBrands" :key="brand.id" class="multi-card">
            <ProxyAvatarImage :src="brand.logo_url" shape="square" size="72rpx" />
            <view class="multi-card-info">
              <text class="multi-card-name">{{ brand.name }}</text>
              <text v-if="brand.description" class="multi-card-sub">{{ brand.description }}</text>
            </view>
            <text class="remove-icon" @click.stop="removeBrand(idx)">✕</text>
          </view>
          <view v-if="selectedBrands.length < MAX_BRANDS" class="add-btn" @click="handleOpenBrandPicker">
            <text class="add-icon">+</text>
            <text>添加品牌</text>
          </view>
        </view>
      </view>
      
      <!-- 更多设置 -->
      <view class="form-section">
        <view class="section-title">更多设置</view>
        
        <!-- 房间状态（公开/私密） -->
        <view class="form-item">
          <view class="item-label">
            <text>房间状态</text>
          </view>
          <view class="switch-row">
            <switch 
              :checked="formData.is_private" 
              @change="formData.is_private = $event.detail.value"
              color="#0F766E"
            />
            <uni-icons v-if="formData.is_private" type="locked" size="16" />
            <text class="switch-label">{{ formData.is_private ? '私密房间' : '公开房间' }}</text>
          </view>
        </view>
        
        <!-- 直播分类 -->
        <view class="form-item">
          <view class="item-label">
            <text>直播分类</text>
          </view>
          <view v-for="(cat, idx) in selectedCategories" :key="cat.id" class="multi-card">
            <view class="multi-card-icon">
              <text v-if="cat.icon">{{ cat.icon }}</text>
              <uni-icons v-else type="folder-add" size="20" />
            </view>
            <view class="multi-card-info">
              <text class="multi-card-name">{{ cat.display_name || cat.name }}</text>
            </view>
            <text class="remove-icon" @click.stop="removeCategory(idx)">✕</text>
          </view>
          <view v-if="selectedCategories.length < MAX_CATEGORIES" class="add-btn" @click="handleOpenCategoryPicker">
            <text class="add-icon">+</text>
            <text>选择分类</text>
          </view>
        </view>
        
        <!-- 场次标签 -->
        <view class="form-item">
          <view class="item-label">
            <text>场次标签</text>
            <text v-if="selectedTags.length > 0" class="item-count">{{ selectedTags.length }}/{{ MAX_SESSION_TAGS }}</text>
          </view>
          <view class="tag-list">
            <view v-for="(tag, idx) in selectedTags" :key="tag.id" class="tag-chip">
              <text class="tag-text">{{ tag.name }}</text>
              <text class="tag-remove" @click.stop="removeTag(idx)">✕</text>
            </view>
          </view>
          <view v-if="selectedTags.length < MAX_SESSION_TAGS" class="add-btn" @click="handleOpenTagPicker">
            <text class="add-icon">+</text>
            <text>添加标签</text>
          </view>
          <view v-if="selectedTags.length >= MAX_SESSION_TAGS" class="tip-text">最多可添加 {{ MAX_SESSION_TAGS }} 个标签，如需更换请先删除</view>
        </view>
        
        <!-- 预计时长（占位） -->
        <view class="form-item">
          <view class="item-label">
            <text>预计时长</text>
          </view>
          <view class="placeholder-btn" @click="showPlaceholderToast">
            <text class="placeholder-text">设置时长</text>
            <text class="picker-arrow">›</text>
          </view>
        </view>
      </view>
      
      <!-- 提示信息 -->
      <view class="tip-box">
        <view class="tip-content">
          <text class="tip-title">温馨提示</text>
          <text class="tip-text">• 标题和简介是必填项</text>
          <text class="tip-text">• 建议上传清晰的封面图片</text>
          <text class="tip-text">• 开始时间需要在当前时间之后</text>
        </view>
      </view>
      
      <!-- 底部占位 -->
      <view class="bottom-placeholder"></view>
    </scroll-view>
    
    <!-- 底部按钮 -->
    <view class="page-footer">
      <button 
        class="create-btn"
        :class="{ 'disabled': !canSubmit }"
        :disabled="!canSubmit"
        :loading="isSubmitting"
        @click="handleCreate"
      >
        {{ isSubmitting ? '创建中...' : '立即创建直播' }}
      </button>
    </view>
    
    <!-- 专家选择器（单选点选即关；已选过滤由页面 computed 负责；本地搜索姓名/医院/科室） -->
    <PickerSheet
      v-model:visible="showExpertPicker"
      title="选择专家"
      :items="expertPickerItems"
      searchable
      search-placeholder="搜索专家姓名/医院"
      empty-text="暂无专家数据"
      @select="handleExpertSelect"
    />
    
    <!-- 品牌选择器（本地搜索名称/描述） -->
    <PickerSheet
      v-model:visible="showBrandPicker"
      title="选择品牌"
      :items="brandPickerItems"
      searchable
      search-placeholder="搜索品牌名称"
      empty-text="暂无品牌数据"
      @select="handleBrandSelect"
    />
    
    <!-- 分类选择器（toggle 多选，最多 10 个；与标签交互一致，一次开完可勾可取消） -->
    <PickerSheet
      v-model:visible="showCategoryPicker"
      mode="multiple"
      title="选择分类"
      :items="categoryPickerItems"
      :selected-ids="categorySelectedIds"
      :max="MAX_CATEGORIES"
      empty-text="暂无分类数据"
      @update:selected-ids="handleCategoryIdsChange"
      @confirm="handleCategoryPickerConfirm"
    />
    
    <!-- 标签选择器（toggle 多选，最多 5 个；createable：搜无精确同名出「创建并使用」→ resolve 自建） -->
    <PickerSheet
      v-model:visible="showTagPicker"
      mode="multiple"
      title="选择标签"
      :items="tagPickerItems"
      :selected-ids="tagSelectedIds"
      :max="MAX_SESSION_TAGS"
      searchable
      createable
      :create-pending="tagResolving"
      empty-text="暂无标签数据"
      @update:selected-ids="handleTagIdsChange"
      @confirm="handleTagPickerConfirm"
      @create="handleTagCreate"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { useRoomStore } from '@/store/room';
import { useSessionStore } from '@/store/session';
import { useAuthStore } from '@/store/auth';
import PickerSheet, { type PickerItem } from '@/components/common/PickerSheet.vue';
import ProxyAvatarImage from '@/components/common/ProxyAvatarImage.vue';
import { getExperts, setSessionExperts } from '@/api/expert';
import { getBrands, bindRoomBrands } from '@/api/brand';
import { getCategories } from '@/api/category';
import { getTags, resolveTag } from '@/api/tag';
import { setSessionTags } from '@/api/sessionTags';
import { createRoomTab, uploadTabImage } from '@/api/tab';
import type { Expert } from '@/types/expert';
import type { Brand } from '@/types/brand';
import type { Category } from '@/types/category';
import type { Tag, TagChip, TagResolveResult } from '@/types/tag';
import { MAX_SESSION_TAGS } from '@/constants/live';
import { hasChipName, pushChipUnique, pruneInactiveChips } from '@/utils/tagChip';
import { 
  isoToLocalDateTimeDisplay, 
  timestampToLocalDateTimeISO 
} from '@/utils/datetime';
import WdDatetimePicker from 'wot-design-uni/components/wd-datetime-picker/wd-datetime-picker.vue';
import { validatePlaybackUrl } from '@/utils/videoUrl';
import { isValidUUID } from '@/utils/url';
import type { SessionStatus } from '@/types/session';

const roomStore = useRoomStore();
const sessionStore = useSessionStore();
const authStore = useAuthStore();

// 表单数据
const formData = ref({
  title: '',
  description: '',  // 保留，用于双写
  intro_image_url: '',  // 新增：简介单图
  start_time: '',
  cover_url: '',
  cover_local_path: '', // 本地临时路径，用于上传
  is_private: false,
  playback_url: '',
  status: '' as SessionStatus | ''
});

// 封面上传模式：album（从相册）或 url（输入URL）
const coverUploadMode = ref<'album' | 'url'>('album');

// 新增：简介图片相关状态
const introImageMode = ref<'local' | 'url'>('local');
const introImageLocalPath = ref('');

// 错误信息
const errors = ref({
  title: '',
  description: '',
  start_time: '',
  playback_url: ''
});

// 提交状态
const isSubmitting = ref(false);

// 专家和品牌选择（支持多选）
const MAX_EXPERTS = 20;
const MAX_BRANDS = 10;
const selectedExperts = ref<Expert[]>([]);
const selectedBrands = ref<Brand[]>([]);
const showExpertPicker = ref(false);
const showBrandPicker = ref(false);
const expertList = ref<Expert[]>([]);
const brandList = ref<Brand[]>([]);

// 分类和标签选择（支持多选；标签上限 5 来自共享常量 MAX_SESSION_TAGS，与后端契约一致）
const MAX_CATEGORIES = 10;
const selectedCategories = ref<Category[]>([]);
const selectedTags = ref<TagChip[]>([]);
const showCategoryPicker = ref(false);
const showTagPicker = ref(false);
const categoryList = ref<Category[]>([]);
const tagList = ref<Tag[]>([]);
/** resolve 进行中（PickerSheet createPending；防重复提交） */
const tagResolving = ref(false);

const expertPickerItems = computed<PickerItem[]>(() => {
  const selectedIds = new Set(selectedExperts.value.map(e => e.id));
  return expertList.value
    .filter(e => !selectedIds.has(e.id))
    .map(expert => ({
      id: expert.id,
      name: expert.name,
      subtitle: [expert.title, expert.hospital, expert.department_name ?? expert.department].filter(Boolean).join(' · ') || undefined,
      avatar: expert.avatar_url || undefined
    }));
});

const brandPickerItems = computed<PickerItem[]>(() => {
  const selectedIds = new Set(selectedBrands.value.map(b => b.id));
  return brandList.value
    .filter(b => !selectedIds.has(b.id))
    .map(brand => ({
      id: brand.id,
      name: brand.name,
      subtitle: brand.description || undefined
    }));
});

// 分类可选项（toggle 面板：展示全量含已选，勾选/取消由组件管理）
const categoryPickerItems = computed<PickerItem[]>(() => {
  return categoryList.value.map(cat => ({
    id: cat.id,
    name: cat.display_name || cat.name,
    subtitle: cat.description || undefined
  }));
});

// 分类已选 id（受控给 PickerSheet multiple）
const categorySelectedIds = computed(() => selectedCategories.value.map(c => c.id));

// toggle 联动：面板勾选/取消实时同步 selectedCategories；保留列表外已选避免误清
const handleCategoryIdsChange = (ids: string[]) => {
  const idSet = new Set(ids);
  const inList = categoryList.value.filter((c) => idSet.has(c.id));
  const outOfList = selectedCategories.value.filter(
    (c) => !categoryList.value.some((x) => x.id === c.id) && idSet.has(c.id)
  );
  selectedCategories.value = [...inList, ...outOfList];
};

const handleCategoryPickerConfirm = () => {
  showCategoryPicker.value = false;
};

// 标签可选项（toggle 面板：展示全量含已选，勾选/取消由组件管理）
const tagPickerItems = computed<PickerItem[]>(() => {
  return tagList.value.map(tag => ({
    id: tag.id,
    name: tag.name,
    subtitle: tag.description || undefined
  }));
});

// 标签已选 id（受控给 PickerSheet multiple）
const tagSelectedIds = computed(() => selectedTags.value.map(t => t.id));

// toggle 联动（D1）：面板勾选/取消实时同步 selectedTags；保留列表外已选（停用标签等）避免误清
const handleTagIdsChange = (ids: string[]) => {
  const idSet = new Set(ids);
  const inList = tagList.value.filter((t) => idSet.has(t.id)).map((t) => ({ id: t.id, name: t.name }));
  const outOfList = selectedTags.value.filter(
    (t) => !tagList.value.some((x) => x.id === t.id) && idSet.has(t.id)
  );
  selectedTags.value = [...inList, ...outOfList];
};

const handleTagPickerConfirm = () => {
  showTagPicker.value = false;
};

// ===== 标签 resolve 自建（V2：搜无精确同名 →「创建并使用」→ resolve → 落 chip + 并入词表） =====
/** resolve 结果转词表项（tagList 为 Tag[] 形态；补全非展示字段，仅参与列表渲染/反选） */
const resolveToTagListEntry = (res: TagResolveResult): Tag => ({
  id: res.id,
  name: res.name,
  slug: null,
  description: null,
  is_active: true,
  created_at: '',
  updated_at: ''
});

/** PickerSheet @create：resolve 创建/复用并落 chip；成功并入 tagList（新词留在面板可管理、可反选） */
const handleTagCreate = async (keyword: string) => {
  const kw = keyword.trim();
  if (!kw || tagResolving.value) return;
  if (selectedTags.value.length >= MAX_SESSION_TAGS) {
    uni.showToast({ title: `最多可添加 ${MAX_SESSION_TAGS} 个标签，请先删除后再添加`, icon: 'none' });
    return;
  }
  if (hasChipName(selectedTags.value, kw)) {
    uni.showToast({ title: '该标签已添加', icon: 'none' });
    return;
  }
  tagResolving.value = true;
  try {
    const response = await resolveTag(kw);
    const res = response.data;
    if (!res?.id) return;
    if (!tagList.value.some((t) => t.id === res.id)) {
      tagList.value = [...tagList.value, resolveToTagListEntry(res)];
    }
    selectedTags.value = pushChipUnique(selectedTags.value, { id: res.id, name: res.name });
    if (res.created) {
      uni.showToast({ title: '已添加新标签', icon: 'none' });
    }
  } catch (error) {
    // resolve 错误（401/400/4001/422/网络）由 request 层统一 toast；此处不落 chip、不重复提示
    console.error('⚠️ [创建直播] resolve 标签失败:', error);
  } finally {
    tagResolving.value = false;
  }
};

// 开播时间（wd-datetime-picker：时间戳 v-model，watch 回写 ISO 契约到 formData）
const startTimeTs = ref<number | null>(null);
/** 可选最早开播时间 = 页面加载时刻（开播时间需在当前之后，仅 UI 约束，与既有校验口径一致） */
const minStartTime = Date.now();
const startTimeDisplay = computed(() => {
  return (formData.value.start_time && isoToLocalDateTimeDisplay(formData.value.start_time)) || '请选择开始时间';
});

watch(startTimeTs, (val) => {
  formData.value.start_time = val ? timestampToLocalDateTimeISO(val) : '';
  errors.value.start_time = '';
});

// 创建模式选择器数据：V15 支持三态创建（预告/直播中/回放），系统态由后端流转产生
const createModeOptions = [
  { value: 'scheduled', label: '预告', tip: '计划中的直播，开播后自动转为直播中' },
  { value: 'live', label: '直播中', tip: '外部流正在直播，创建后立即播放（开始时间自动取当前）' },
  { value: 'ready', label: '回放', tip: '使用现有视频链接，用户进入后直接观看回放' }
];
const createModeIndex = ref(0);  // 默认创建为预告

/**
 * 初始化开播时间（默认当前 +30 分钟，沿用原 5 分钟取整口径）
 */
const initDateTimeRange = () => {
  const d = new Date(Date.now() + 30 * 60 * 1000);
  d.setSeconds(0, 0);
  d.setMinutes(Math.ceil(d.getMinutes() / 5) * 5);
  startTimeTs.value = d.getTime();
};

/**
 * 页面加载时初始化
 */
onMounted(() => {
  console.log('📱 [创建直播] ========== 页面初始化 ==========');
  console.log('📱 [创建直播] 封面上传模式:', coverUploadMode.value);
  console.log('📱 [创建直播] 简介图片模式:', introImageMode.value);
  console.log('📱 [创建直播] formData初始状态:', {
    cover_url: formData.value.cover_url || '(空)',
    cover_local_path: formData.value.cover_local_path || '(空)',
    intro_image_url: formData.value.intro_image_url || '(空)'
  });
});

/**
 * 创建模式选择器change事件
 */
const handleCreateModeChange = (e: any) => {
  createModeIndex.value = e.detail.value;
  formData.value.status = createModeOptions[createModeIndex.value].value as SessionStatus;
};

/**
 * 监听回放地址变化
 */
watch(() => formData.value.playback_url, (newVal) => {
  if (!newVal) {
    // 清空回放地址时，重置为未选择态（开始时间随之隐藏）
    formData.value.status = '';
  } else {
    // 有回放地址时，使用选择的状态
    formData.value.status = createModeOptions[createModeIndex.value].value as SessionStatus;
  }
});


/**
 * 回放地址失焦验证
 */
const handlePlaybackUrlBlur = () => {
  if (!formData.value.playback_url) {
    errors.value.playback_url = '';
    return;
  }
  
  const result = validatePlaybackUrl(formData.value.playback_url);
  if (!result.valid) {
    errors.value.playback_url = result.message || '回放地址格式不正确';
  } else {
    errors.value.playback_url = '';
  }
};

/**
 * 封面上传
 */
const handleUploadCover = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      if (res.tempFilePaths && res.tempFilePaths.length > 0) {
        // 验证文件大小
        uni.getFileInfo({
          filePath: res.tempFilePaths[0],
          success: (fileInfo) => {
            if (fileInfo.size > 5 * 1024 * 1024) { // 5MB
              uni.showToast({
                title: '封面图片不能超过5MB',
                icon: 'none'
              });
              return;
            }
            // 保存本地路径用于预览和上传
            formData.value.cover_url = res.tempFilePaths[0];
            formData.value.cover_local_path = res.tempFilePaths[0];
            uni.showToast({
              title: '封面已选择',
              icon: 'success'
            });
          }
        });
      }
    }
  });
};

/**
 * 处理封面模式切换
 */
const handleCoverModeChange = (mode: 'album' | 'url') => {
  console.log('🔄 [封面] 模式切换:', { from: coverUploadMode.value, to: mode });
  
  if (mode === 'url' && coverUploadMode.value === 'album') {
    // 从相册模式切换到URL模式，清空本地路径
    formData.value.cover_local_path = '';
    console.log('🧹 [封面] 已清空本地路径');
  } else if (mode === 'album' && coverUploadMode.value === 'url') {
    // 从URL模式切换到相册模式，清空URL
    formData.value.cover_url = '';
    console.log('🧹 [封面] 已清空URL');
  }
  
  coverUploadMode.value = mode;
  console.log('✅ [封面] 模式切换完成:', mode);
};

/**
 * 处理封面URL输入变化（实时更新）
 */
const handleCoverUrlInput = () => {
  // 清空本地路径，标记为URL模式
  formData.value.cover_local_path = '';
  console.log('🔗 [封面] URL输入更新:', formData.value.cover_url);
};

/**
 * 处理封面URL失焦验证
 */
const handleCoverUrlBlur = () => {
  console.log('👁️ [封面] 输入框失焦，当前值:', formData.value.cover_url || '(空)');
  if (formData.value.cover_url && formData.value.cover_url.trim()) {
    console.log('✅ [封面] URL已确认:', formData.value.cover_url);
  } else {
    console.warn('⚠️ [封面] URL为空');
  }
};

/**
 * 处理封面URL加载错误
 */
const handleCoverUrlError = () => {
  uni.showToast({
    title: '图片URL无效或无法加载',
    icon: 'none'
  });
};

/**
 * 移除封面
 */
const removeCover = () => {
  formData.value.cover_url = '';
  formData.value.cover_local_path = '';
  console.log('🗑️ [封面] 已清除');
};

/**
 * 上传房间封面
 * @param roomId 房间ID
 * @param filePath 本地文件路径
 */
const uploadRoomCover = async (roomId: string, filePath: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    const baseURL = import.meta.env.VITE_BASE_API_URL || 'https://mp.dayilive.com/api/core';
    
    uni.uploadFile({
      url: `${baseURL}/rooms/${roomId}/cover`,
      filePath: filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${authStore.token}`
      },
      success: (uploadRes) => {
        if (uploadRes.statusCode === 200) {
          resolve();
        } else {
          reject(new Error('上传失败'));
        }
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
};

/**
 * 上传简介图片（新增 - 单图模式）
 */
const handleUploadIntroImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const filePath = res.tempFilePaths?.[0];
      if (!filePath) {
        uni.showToast({ title: '未选择文件', icon: 'none' });
        return;
      }
      
      // 文件类型验证（兼容blob URL）
      const isBlobUrl = filePath.startsWith('blob:');
      if (!isBlobUrl) {
        const ext = filePath.split('.').pop()?.toLowerCase();
        const allowedExts = ['jpg', 'jpeg', 'png', 'gif'];
        if (ext && !allowedExts.includes(ext)) {
          uni.showToast({ title: '仅支持JPG、PNG、GIF格式', icon: 'none' });
          return;
        }
      }
      
      // 文件大小验证
      uni.getFileInfo({
        filePath: filePath,
        success: (fileInfo) => {
          if (fileInfo.size > 5 * 1024 * 1024) {
            uni.showToast({ title: '图片不能超过5MB', icon: 'none' });
            return;
          }
          
          formData.value.intro_image_url = filePath;
          introImageLocalPath.value = filePath;
          uni.showToast({ title: '已选择图片', icon: 'success' });
        },
        fail: () => {
          uni.showToast({ title: '获取文件信息失败', icon: 'none' });
        }
      });
    }
  });
};

/**
 * 处理简介图片URL输入变化（实时更新）
 */
const handleIntroImageUrlInput = () => {
  // 清空本地路径，标记为URL模式
  introImageLocalPath.value = '';
  console.log('[简介图片] URL输入更新:', formData.value.intro_image_url);
};

/**
 * 简介图片URL加载错误
 */
const handleIntroImageUrlError = () => {
  uni.showToast({ title: '图片URL无效或无法加载', icon: 'none' });
};

/**
 * 清空简介图片
 */
const clearIntroImage = () => {
  formData.value.intro_image_url = '';
  introImageLocalPath.value = '';
  console.log('🗑️ [简介图片] 已清除');
};

/**
 * 创建"直播介绍"Tab
 * @param roomId 房间ID
 */
const createIntroTab = async (roomId: string): Promise<void> => {
  try {
    console.log('📝 [创建直播] 步骤1.6: 检查是否需要创建直播介绍Tab');
    
    const hasText = !!formData.value.description.trim();
    const hasLocalImage = !!introImageLocalPath.value;
    const hasUrlImage = !!formData.value.intro_image_url;
    const hasImage = hasLocalImage || hasUrlImage;
    
    // ⚠️ 关键修复：只有当有实际内容时才创建Tab
    if (!hasText && !hasImage) {
      console.log('ℹ️ [创建直播] 无简介内容，跳过Tab创建');
      return;
    }
    
    console.log('📝 [创建直播] 有内容，开始创建Tab', { hasText, hasImage });
    
    let contentType: 'text' | 'image' | 'mixed' = 'text';
    if (hasImage && hasText) {
      contentType = 'mixed';
    } else if (hasImage) {
      contentType = 'image';
    } else {
      contentType = 'text';
    }
    
    let finalImageUrl = '';
    if (hasLocalImage) {
      console.log('📤 [创建直播] 上传简介图片...');
      try {
        finalImageUrl = await uploadTabImage(roomId, introImageLocalPath.value);
        console.log('✅ [创建直播] 简介图片上传成功:', finalImageUrl);
      } catch (uploadError) {
        console.error('⚠️ [创建直播] 简介图片上传失败:', uploadError);
        finalImageUrl = '';
      }
    } else if (hasUrlImage) {
      finalImageUrl = formData.value.intro_image_url;
    }
    
    await createRoomTab(roomId, {
      tab_key: 'intro',
      title: '直播介绍',
      content_type: contentType,
      text_content: formData.value.description.trim(),
      image_url: finalImageUrl,
      sort_order: 1,
      is_active: true
    });
    
    console.log('✅ [创建直播] 直播介绍Tab创建成功');
  } catch (error) {
    console.error('⚠️ [创建直播] 直播介绍Tab创建失败:', error);
  }
};

/**
 * 打开专家选择器（全量拉取：循环翻页直到 total，避免只能选到前 100 个）
 */
const handleOpenExpertPicker = async () => {
  try {
    const experts = await fetchAllExperts();
    expertList.value = experts;
    showExpertPicker.value = true;
  } catch (error) {
    console.error('获取专家列表失败:', error);
    expertList.value = [];
    showExpertPicker.value = true;
  }
};

/**
 * 拉取全量专家列表（第一页拿 total 后剩余页并发请求；上限 20 页防接口异常死循环）
 */
const fetchAllExperts = async (): Promise<Expert[]> => {
  const pageSize = 100;
  const maxPages = 20;
  const first = await getExperts({ page: 1, size: pageSize });
  const data = first.data;
  if (!data?.items?.length) return [];
  let items: Expert[] = [...data.items];
  const total = Number(data.total ?? 0);
  const totalPages = Math.min(Math.ceil(total / pageSize), maxPages);
  if (totalPages > 1 && items.length < total) {
    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => getExperts({ page: i + 2, size: pageSize }))
    );
    for (const r of rest) {
      if (r.data?.items) items = [...items, ...r.data.items];
    }
  }
  return items;
};

/**
 * 选择专家（追加模式）
 */
const handleExpertSelect = (item: PickerItem) => {
  if (selectedExperts.value.length >= MAX_EXPERTS) return;
  const expert = expertList.value.find(e => e.id === item.id);
  if (expert && !selectedExperts.value.some(e => e.id === expert.id)) {
    selectedExperts.value.push(expert);
  }
};

/**
 * 移除专家（按索引）
 */
const removeExpert = (idx: number) => {
  selectedExperts.value.splice(idx, 1);
};

/**
 * 打开品牌选择器（全量拉取：分页接口循环翻页直到 total；旧接口数组形态一次返回）
 */
const handleOpenBrandPicker = async () => {
  try {
    const brands = await fetchAllBrands();
    brandList.value = brands;
    if (brandList.value.length === 0) {
      uni.showToast({ title: '暂无品牌数据', icon: 'none' });
    }
    showBrandPicker.value = true;
  } catch (error) {
    console.error('获取品牌列表失败:', error);
    uni.showToast({ title: '获取品牌列表失败', icon: 'none' });
  }
};

/**
 * 拉取全量品牌列表
 * - 旧接口：返回裸数组（limit:100 语义），一次返回全量
 * - 分页接口：第一页拿 total 后剩余页并发请求；上限 20 页防接口异常死循环
 */
const fetchAllBrands = async (): Promise<Brand[]> => {
  const maxPages = 20;
  const pageSize = 100;
  const response = await getBrands({ limit: pageSize });
  const data = response.data as any;
  if (!data) return [];
  if (Array.isArray(data)) {
    // 旧接口形态：数组即全量
    return data;
  }
  const firstItems: Brand[] = data?.items?.length ? data.items : [];
  const total = Number(data?.total ?? 0);
  if (!firstItems.length || total <= firstItems.length) {
    return firstItems;
  }
  let items = [...firstItems];
  const totalPages = Math.min(Math.ceil(total / pageSize), maxPages);
  if (totalPages > 1) {
    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) => getBrands({ page: i + 2, size: pageSize }))
    );
    for (const next of rest) {
      const nextData: any = next.data;
      if (Array.isArray(nextData) || !nextData?.items?.length) continue;
      items = [...items, ...nextData.items];
    }
  }
  return items;
};

/**
 * 选择品牌（追加模式）
 */
const handleBrandSelect = (item: PickerItem) => {
  if (selectedBrands.value.length >= MAX_BRANDS) return;
  const brand = brandList.value.find(b => b.id === item.id);
  if (brand && !selectedBrands.value.some(b => b.id === brand.id)) {
    selectedBrands.value.push(brand);
  }
};

/**
 * 移除品牌（按索引）
 */
const removeBrand = (idx: number) => {
  selectedBrands.value.splice(idx, 1);
};

/**
 * 打开分类选择器
 */
const handleOpenCategoryPicker = async () => {
  try {
    const response = await getCategories();
    if (response.data) {
      categoryList.value = response.data;
      showCategoryPicker.value = true;
    }
  } catch (error) {
    console.error('获取分类列表失败:', error);
    uni.showToast({ title: '获取分类列表失败', icon: 'none' });
  }
};

/**
 * 移除分类（按索引）
 */
const removeCategory = (idx: number) => {
  selectedCategories.value.splice(idx, 1);
};

/**
 * 打开标签选择器
 */
const handleOpenTagPicker = async () => {
  try {
    const response = await getTags();
    if (response.data) {
      tagList.value = response.data;
      showTagPicker.value = true;
    }
  } catch (error) {
    console.error('获取标签列表失败:', error);
    uni.showToast({ title: '获取标签列表失败', icon: 'none' });
  }
};

/**
 * 移除标签（按索引）
 */
const removeTag = (idx: number) => {
  selectedTags.value.splice(idx, 1);
};

/**
 * 占位功能提示
 */
const showPlaceholderToast = () => {
  uni.showToast({
    title: '该功能暂未开放，敬请期待',
    icon: 'none',
    duration: 2000
  });
};

/**
 * 表单验证
 */
const validateForm = (): boolean => {
  let isValid = true;
  errors.value.title = '';
  errors.value.start_time = '';
  errors.value.playback_url = '';
  
  if (!formData.value.title.trim()) {
    errors.value.title = '请输入直播标题';
    isValid = false;
  }
  
  // 开始时间仅预告（scheduled）模式需要；直播中/回放由后端自动取当前时间
  if (formData.value.status === 'scheduled' && !formData.value.start_time) {
    errors.value.start_time = '请选择开始时间';
    isValid = false;
  }
  
  if (!formData.value.playback_url) {
    errors.value.playback_url = '请输入播放地址';
    isValid = false;
  } else {
    const result = validatePlaybackUrl(formData.value.playback_url);
    if (!result.valid) {
      errors.value.playback_url = result.message || '播放地址格式不正确';
      isValid = false;
    }
  }
  
  return isValid;
};

/**
 * 是否可以提交
 */
const canSubmit = computed(() => {
  return formData.value.title.trim() && 
         (formData.value.status !== 'scheduled' || formData.value.start_time) && 
         formData.value.playback_url &&
         !isSubmitting.value;
});

/**
 * 创建直播
 */
const handleCreate = async () => {
  if (!validateForm()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    console.log('🎬 [创建直播] ========== 开始创建流程 ==========');
    console.log('📋 [创建直播] 表单数据:', {
      title: formData.value.title,
      description: formData.value.description,
      intro_image_url: formData.value.intro_image_url,
      intro_image_local: introImageLocalPath.value,
      start_time: formData.value.start_time,
      cover_url: formData.value.cover_url,
      cover_local_path: formData.value.cover_local_path,
      status: formData.value.status,
      playback_url: formData.value.playback_url,
      experts: selectedExperts.value.map(e => e.id),
      brands: selectedBrands.value.map(b => b.id),
      categories: selectedCategories.value.map(c => c.id),
      tags: selectedTags.value.map(t => t.id)
    });
    
    // 🔍 封面数据详细验证
    console.log('🔍 [封面验证] ========== 封面数据详细检查 ==========');
    console.log('🔍 [封面验证] 封面上传模式:', coverUploadMode.value);
    console.log('🔍 [封面验证] formData.cover_url:', formData.value.cover_url || '(空)');
    console.log('🔍 [封面验证] formData.cover_local_path:', formData.value.cover_local_path || '(空)');
    console.log('🔍 [封面验证] cover_url长度:', formData.value.cover_url?.length || 0);
    console.log('🔍 [封面验证] 是否有封面:', !!formData.value.cover_url);
    if (formData.value.cover_url) {
      console.log('✅ [封面验证] 封面URL已设置，将在创建Room后更新');
    } else {
      console.warn('⚠️ [封面验证] 未设置封面URL，将使用后端默认封面');
    }
    
    // 创建直播间（直接传入封面URL）
    console.log('🏠 [创建直播] 步骤1: 创建Room');
    const createRoomPayload: any = {
      title: formData.value.title.trim(),
      description: formData.value.description.trim(),
      is_private: formData.value.is_private
    };
    
    // ✅ 如果有封面URL，直接在创建时传入
    if (formData.value.cover_url && !formData.value.cover_local_path) {
      createRoomPayload.cover_url = formData.value.cover_url;
      console.log('✅ [创建直播] 封面URL将在创建Room时直接传入:', formData.value.cover_url);
    }
    
    // ✅ 关联分类：随主请求写入（后端 POST /rooms 原生支持 category_ids，普通用户可用）
    // 仅提交 UUID 格式分类，防止分类接口降级（Mock id 如 '1'~'8'）导致后端 422 创建失败
    if (selectedCategories.value.length > 0) {
      const validCategoryIds = selectedCategories.value
        .map(c => c.id)
        .filter(id => isValidUUID(id));
      if (validCategoryIds.length < selectedCategories.value.length) {
        uni.showToast({ title: '部分分类数据异常，已跳过', icon: 'none' });
      }
      if (validCategoryIds.length > 0) {
        createRoomPayload.category_ids = validCategoryIds;
        console.log('✅ [创建直播] 分类将随创建写入:', validCategoryIds);
      }
    }
    
    console.log('📤 [创建直播] 创建Room的完整payload:', createRoomPayload);
    const roomResult = await roomStore.addNewRoom(createRoomPayload);
    
    if (!roomResult.success) {
      throw new Error(roomResult.message || '创建直播间失败');
    }
    console.log('✅ [创建直播] Room创建成功, room_id:', roomResult.room_id);
    
    // 步骤1.5：上传封面（仅处理本地文件上传）
    if (formData.value.cover_local_path) {
      console.log('📷 [创建直播] 步骤1.5: 上传本地封面图片');
      try {
        const uploadResult = await uploadRoomCover(roomResult.room_id!, formData.value.cover_local_path);
        console.log('✅ [创建直播] 封面上传成功:', uploadResult);
      } catch (coverError) {
        console.error('⚠️ [创建直播] 封面上传失败:', coverError);
        console.error('🐞 [创建直播] 错误详情:', JSON.stringify(coverError, null, 2));
        // 不阻断流程
      }
    } else if (formData.value.cover_url) {
      console.log('✅ [创建直播] 封面URL已在创建Room时传入，无需额外更新');
    } else {
      console.log('ℹ️ [创建直播] 未设置封面，使用后端默认封面');
    }
    
    // 步骤1.6：创建"直播介绍"Tab（新增，失败不阻断）
    await createIntroTab(roomResult.room_id!);
    
    // 步骤2：创建场次（V15 三态创建：scheduled/live/ready 统一走 createSession）
    console.log('📅 [创建直播] 步骤2: 创建Session');
    let sessionResult;

    {
      // 三态创建：status 由用户选择（预告/直播中/回放）
      // live 模式 start_time 由后端自动取当前时间；回放模式默认当前时间（无定时开播语义）
      console.log(`📅 [创建直播] 使用createSession（${formData.value.status}模式）`);
      const sessionPayload = {
        title: formData.value.title.trim(),
        description: '',
        start_time: formData.value.status === 'scheduled'
          ? formData.value.start_time
          : new Date().toISOString(),
        playback_url: formData.value.playback_url,
        status: formData.value.status
      };
      console.log('📤 [创建直播] Session payload:', sessionPayload);
      sessionResult = await sessionStore.createSession(roomResult.room_id!, sessionPayload);
    }
    
    if (!sessionResult.success) {
      console.warn('⚠️ [创建直播] Session创建/导入失败，但Room已创建');
      throw new Error(sessionResult.message || 'Session创建/导入失败');
    }
    
    console.log('✅ [创建直播] Session创建/导入成功');
    
    // 获取刚创建的Session ID
    await sessionStore.fetchSessionsByRoomId(roomResult.room_id!, { refresh: true });
    
    if (sessionStore.sessions.length === 0) {
      console.error('❌ [创建直播] 无法获取新创建的Session');
      throw new Error('无法获取新创建的Session');
    }
    
    const newSession = sessionStore.sessions[0];
    console.log('🎯 [创建直播] 获取到新创建的Session ID:', newSession.id);
    
    // 步骤3：关联专家（支持多专家）
    if (selectedExperts.value.length > 0) {
      console.log('👨‍⚕️ [创建直播] 步骤3: 关联专家，数量:', selectedExperts.value.length);
      try {
        await setSessionExperts(newSession.id, selectedExperts.value.map((e, i) => ({
          expert_id: e.id,
          role: i === 0 ? '主讲' : '嘉宾',
          sort_order: i
        })));
        console.log('✅ [创建直播] 专家关联成功');
      } catch (expertError) {
        console.error('⚠️ [创建直播] 专家关联失败:', expertError);
      }
      
      // 创建专家Tab（独立容错，不因关联失败而跳过）
      try {
        console.log('📝 [创建直播] 创建专家Tab');
        await createRoomTab(roomResult.room_id!, {
          tab_key: 'experts',
          title: '专家介绍',
          content_type: 'mixed',
          text_content: '专家信息将在此显示',
          image_url: '',
          sort_order: 2,
          is_active: true
        });
        console.log('✅ [创建直播] 专家Tab创建成功');
      } catch (tabError) {
        console.error('⚠️ [创建直播] 专家Tab创建失败:', tabError);
      }
    }
    
    // 步骤4：关联品牌（支持多品牌）
    if (selectedBrands.value.length > 0) {
      console.log('🏷️ [创建直播] 步骤4: 关联品牌，数量:', selectedBrands.value.length);
      try {
        await bindRoomBrands(roomResult.room_id!, selectedBrands.value.map(b => b.id));
        console.log('✅ [创建直播] 品牌关联成功');
      } catch (brandError) {
        console.error('⚠️ [创建直播] 品牌关联失败:', brandError);
      }
      
      // 创建品牌Tab（独立容错，不因关联失败而跳过）
      try {
        console.log('📝 [创建直播] 创建品牌Tab');
        await createRoomTab(roomResult.room_id!, {
          tab_key: 'brands',
          title: '品牌介绍',
          content_type: 'mixed',
          text_content: '品牌信息将在此显示',
          image_url: '',
          sort_order: 3,
          is_active: true
        });
        console.log('✅ [创建直播] 品牌Tab创建成功');
      } catch (tabError) {
        console.error('⚠️ [创建直播] 品牌Tab创建失败:', tabError);
      }
    }
    
    // 步骤5：关联分类（已随创建主请求 POST /rooms 的 category_ids 写入，见步骤1）
    // 原步骤5调用的 POST /admin/rooms/{roomId}/categories 仅 ADMIN 可用，普通用户必失败且被静默吞掉，
    // 已删除（分类写入统一走主链路）
    
    // 步骤6：关联标签（V2：replace 整组 ≤5；失败可见化；4001 按启用词表差集剔除并自动重试一次；剔光不 bind）
    let tagSaveFailed = false;
    const tryBindTags = async (tagIds: string[]) => {
      await setSessionTags(newSession.id, { tag_ids: tagIds, mode: 'replace' });
    };
    if (selectedTags.value.length > 0) {
      try {
        if (selectedTags.value.length > MAX_SESSION_TAGS) {
          uni.showToast({ title: `最多 ${MAX_SESSION_TAGS} 个标签`, icon: 'none' });
          tagSaveFailed = true;
        } else {
          console.log('🏷️ [创建直播] 步骤6: 关联标签，数量:', selectedTags.value.length);
          await tryBindTags(selectedTags.value.map((t) => t.id));
          console.log('✅ [创建直播] 标签关联成功');
        }
      } catch (tagError: any) {
        if (tagError?.code === 4001) {
          console.warn('⚠️ [创建直播] 标签绑定 4001（部分停用/不存在），按启用词表差集剔除后重试一次');
          let activeList: unknown;
          try {
            const listResponse = await getTags();
            activeList = listResponse.data;
          } catch (listError) {
            activeList = undefined; // 词表拉取失败 → 放弃自动剔除（防御性降级）
          }
          const pruned = pruneInactiveChips(selectedTags.value, activeList);
          if (pruned !== selectedTags.value) {
            selectedTags.value = pruned;
            if (pruned.length > 0) {
              uni.showToast({ title: '部分标签已停用，已自动移除', icon: 'none' });
              try {
                await tryBindTags(pruned.map((t) => t.id));
                console.log('✅ [创建直播] 标签剔除后重试成功');
              } catch (retryError) {
                console.error('❌ [创建直播] 标签剔除后重试失败:', retryError);
                tagSaveFailed = true;
              }
            } else {
              uni.showToast({ title: '所选标签均已停用，请重新选择', icon: 'none' });
              tagSaveFailed = true; // 剔光不 bind、不提交 []（§4.4）
            }
          } else {
            tagSaveFailed = true; // 词表异常或剔除无变化 → 不再自动重试（避免反复 4001）
          }
        } else {
          // 其它错误（403/422/网络等）request 层已 toast；此处仅标记失败以替换收尾成功文案
          console.error('❌ [创建直播] 标签绑定失败', tagError);
          tagSaveFailed = true;
        }
      }
    }
    
    // 步骤7：创建聊天Tab（始终创建）
    console.log('💬 [创建直播] 步骤7: 创建聊天Tab');
    try {
      await createRoomTab(roomResult.room_id!, {
        tab_key: 'chat',
        title: '聊天',
        content_type: 'mixed',
        text_content: '欢迎参与讨论',
        image_url: '',
        sort_order: 10,
        is_active: true
      });
      console.log('✅ [创建直播] 聊天Tab创建成功');
    } catch (chatError) {
      console.error('⚠️ [创建直播] 聊天Tab创建失败:', chatError);
    }
    
    // 步骤8：回放地址已在import时设置，无需额外处理
    console.log('✅ [创建直播] 回放地址处理完成（已在Session创建时设置）');
    
    console.log('🎉 [创建直播] ========== 创建流程完成 ==========');
    
    // 标签绑定失败时收尾文案不假装全成功（D1）；room/session 已创建，提示到编辑页补设
    const finalTitle = tagSaveFailed
      ? '直播已创建，但标签保存失败，请到编辑页补设'
      : '创建成功，可在我的直播中管理';
    uni.showToast({
      title: finalTitle,
      icon: 'none',
      duration: 1800
    });
    
    setTimeout(() => {
      uni.redirectTo({
        url: '/pages/app/live-manage/list',
        fail: () => {
          uni.navigateTo({
            url: '/pages/app/live-manage/list',
            fail: () => {
              uni.switchTab({ url: '/pages/app/tabbar/my/index' });
            }
          });
        }
      });
    }, 800);
    
  } catch (error: any) {
    console.error('创建失败:', error);
    const msg = error.message || '';
    // 403 Forbidden 通常表示没有开播权限
    if (msg === 'Forbidden' || msg.includes('开播资格') || msg.includes('permission')) {
      uni.showToast({
        title: '您暂无开播权限，请联系管理员',
        icon: 'none',
        duration: 2000
      });
    } else {
      uni.showToast({
        title: msg || '创建失败，请重试',
        icon: 'none',
        duration: 2000
      });
    }
  } finally {
    isSubmitting.value = false;
  }
};

/**
 * 页面加载时检查登录
 */
onLoad(() => {
  if (!authStore.isAuthenticated) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/home/index' }); }
    });
    return;
  }

  // 管理员无创建直播权限（入口已隐藏；此处封住深链/登录回跳/历史栈绕行路径）
  if (authStore.isAdmin) {
    uni.showToast({ title: '管理员请使用全站房间管理', icon: 'none' });
    uni.navigateBack({
      fail: () => { uni.switchTab({ url: '/pages/app/tabbar/my/index' }); }
    });
    return;
  }
  
  initDateTimeRange();
});
</script>

<style lang="scss" scoped>
.create-live-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  // Design Token: 全局背景
  background-color: var(--home-bg);
  overflow: hidden;
}

/* 页面内容区 */
.page-content {
  flex: 1;
  width: 100%;
  overflow-y: auto;
  padding: 0 32rpx 32rpx;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
}

/* 表单区块 */
.form-section {
  margin-top: var(--home-spacing-module);
  width: 100%;
  background-color: var(--home-card);
  border-radius: var(--home-r-lg);
  padding: calc(var(--home-spacing-card) * 2);
  box-sizing: border-box;
  box-shadow: var(--home-shadow-card);
}

.section-title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
  margin-bottom: calc(var(--home-spacing-card) * 2);
}

/* 表单项 */
.form-item {
  margin-bottom: 40rpx;
  position: relative;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.item-label {
  display: flex;
  align-items: center;
  margin-bottom: var(--home-spacing-card);
  font-size: var(--home-fs-card-title);
  color: var(--home-text2);
}

.required {
  color: #ff4d4f;
  margin-left: 4rpx;
}

// 输入框：轻边框 + focus ring（品牌主色），对齐设计规范
.item-input,
.item-textarea {
  width: 100%;
  padding: 24rpx;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: var(--home-r-md);
  border: 2rpx solid transparent;
  transition: border-color 0.2s ease, background-color 0.2s ease;
  box-sizing: border-box;
  
  &:focus {
    background-color: var(--home-bg);
    border-color: var(--home-primary);
  }
  
  &.error {
    border-color: var(--color-danger);
  }
}

.item-textarea {
  min-height: 160rpx;
  line-height: 1.6;
}

.item-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  background-color: var(--home-bg);
  border-radius: var(--home-r-md);
  border: 1.5rpx solid var(--home-border);
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  min-height: 88rpx; // 热区 >= 44px
  transition: border-color 0.2s ease;
  
  &:active {
    border-color: var(--home-primary);
  }
  
  .placeholder {
    color: var(--home-tabbar-inactive);
  }
}

.picker-arrow {
  font-size: 40rpx;
  color: var(--home-tabbar-inactive);
  font-weight: 300;
}

.char-count {
  display: block;
  text-align: right;
  margin-top: 8rpx;
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
  padding-right: 4rpx;
}

.error-text {
  font-size: var(--home-fs-meta);
  color: var(--color-danger);
  margin-top: 8rpx;
  display: block;
}

.tip-text {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  margin-top: 8rpx;
  line-height: 1.5;
}

/* 封面/简介图片模式切换：iOS 风格分段控制器 */
.cover-upload-tabs {
  display: flex;
  border: 2rpx solid var(--home-border);
  border-radius: var(--home-r-md);
  overflow: hidden;
  margin-bottom: var(--home-spacing-inner);
  
  .tab-item {
    flex: 1;
    padding: 16rpx;
    text-align: center;
    background-color: transparent;
    font-size: var(--home-fs-tab);
    color: var(--home-text2);
    transition: all 0.2s ease;
    min-height: 72rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 1rpx solid var(--home-border);
    
    &:last-child {
      border-right: none;
    }
    
    &.active {
      background-color: var(--home-primary);
      color: #ffffff;
      border-right-color: transparent;
    }
  }
}

.cover-upload {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: var(--home-r-lg);
  overflow: hidden;
  position: relative;
}

.cover-url-input {
  .item-input {
    margin-bottom: 16rpx;
  }
  
  .cover-preview-small {
    width: 100%;
    aspect-ratio: 16/9;
    border-radius: 12rpx;
    overflow: hidden;
    
    image {
      width: 100%;
      height: 100%;
    }
  }
}

.cover-preview {
  width: 100%;
  height: 100%;
  position: relative;
  
  image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.cover-remove {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  width: 56rpx;
  height: 56rpx;
  background-color: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-icon {
  color: #ffffff;
  font-size: 32rpx;
}

.cover-btn {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  background-color: var(--home-input-bg);
  border: 2rpx dashed var(--home-border);
  border-radius: var(--home-r-lg);
  box-sizing: border-box;
  transition: border-color 0.2s ease, background-color 0.2s ease;
  
  &:active {
    background-color: #EEF1F8;
    border-color: var(--home-primary);
  }
}

.cover-btn .upload-icon {
  font-size: 56rpx;
  color: var(--home-tabbar-inactive);
}

.cover-btn .upload-text {
  font-size: var(--home-fs-card-title);
  color: var(--home-text2);
}

.upload-tip {
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
}

/* 简介图片上传 */
.desc-images-section {
  margin-top: 24rpx;
}

.desc-images-label {
  display: flex;
  align-items: center;
  margin-bottom: var(--home-spacing-card);
  font-size: var(--home-fs-card-title);
  color: var(--home-text2);
}

.desc-images-tip {
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
  margin-left: 8rpx;
}

.desc-images-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
}

.desc-image-item {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  background-color: var(--home-bg);
  border-radius: var(--home-r-md);
  overflow: hidden;
}

.desc-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.desc-image-remove {
  position: absolute;
  top: 4rpx;
  right: 4rpx;
  width: 40rpx;
  height: 40rpx;
  background-color: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  
  .remove-icon {
    color: #ffffff;
    font-size: 24rpx;
  }
}

.desc-image-upload {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  background-color: var(--home-bg);
  border-radius: var(--home-r-md);
  border: 1.5rpx dashed var(--home-border);
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  
  .upload-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -70%);
    font-size: 48rpx;
    color: var(--home-tabbar-inactive);
  }
  
  .upload-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, 30%);
    font-size: 22rpx;
    color: var(--home-text2);
    white-space: nowrap;
  }
}

/* 多选计数 */
.item-count {
  margin-left: 12rpx;
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  font-weight: 400;
}

/* 多专家/多品牌卡片 */
.multi-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 16rpx;
  background-color: var(--home-bg);
  border-radius: var(--home-r-lg);
  border: 1.5rpx solid var(--home-border);
  margin-bottom: 12rpx;
}

.multi-card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  overflow: hidden;
}

.multi-card-name {
  font-size: var(--home-fs-card-title);
  font-weight: 600;
  color: var(--home-text1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.multi-card-sub {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-icon {
  font-size: 28rpx;
  color: var(--home-text2);
  min-width: 72rpx;
  min-height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 分类卡片图标 */
.multi-card-icon {
  font-size: 40rpx;
  min-width: 72rpx;
  min-height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 标签列表（水平排列，可换行） */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

/* 标签胶囊 */
.tag-chip {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 20rpx;
  background-color: rgba(15, 118, 110, 0.08);
  border-radius: var(--home-r-pill);
  border: 1.5rpx solid rgba(15, 118, 110, 0.15);
}

.tag-text {
  font-size: var(--home-fs-card-title);
  color: var(--home-primary);
}

.tag-remove {
  font-size: 24rpx;
  color: var(--home-primary);
  min-width: 40rpx;
  min-height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 添加按钮：品牌主色轮廓，热区 >= 44px */
.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--home-spacing-inner);
  padding: 24rpx;
  min-height: 88rpx;
  background-color: var(--home-bg);
  border-radius: var(--home-r-lg);
  font-size: var(--home-fs-card-title);
  color: var(--home-primary);
  border: 1.5rpx dashed var(--home-primary);
  transition: background-color 0.2s ease;
  
  &:active {
    background-color: rgba(15, 118, 110, 0.06);
  }
}

.add-icon {
  font-size: 32rpx;
  font-weight: 300;
}

/* 占位按钮 */
.placeholder-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  min-height: 88rpx;
  background-color: var(--home-bg);
  border-radius: var(--home-r-md);
  border: 1.5rpx solid var(--home-border);
  font-size: var(--home-fs-card-title);
  transition: border-color 0.2s;

  &:active {
    border-color: var(--home-primary);
  }
}

.placeholder-text {
  color: var(--home-tabbar-inactive);
}

/* 提示框：品牌色极轻点缀 */
.tip-box {
  display: flex;
  align-items: flex-start;
  padding: 24rpx;
  background-color: rgba(15, 118, 110, 0.06);
  border-radius: var(--home-r-lg);
  border-left: 3rpx solid var(--home-primary);
  margin-top: var(--home-spacing-module);
}

.tip-icon {
  font-size: 32rpx;
  margin-right: var(--home-spacing-inner);
  flex-shrink: 0;
}

.tip-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.tip-title {
  font-size: var(--home-fs-card-title);
  font-weight: 600;
  color: var(--home-primary);
}

.tip-text {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  line-height: 1.65;
}

/* 图片模式切换：与 cover-upload-tabs 统一（分段控制器） */
.image-mode-tabs {
  display: flex;
  border: 2rpx solid var(--home-border);
  border-radius: var(--home-r-md);
  overflow: hidden;
  margin-bottom: var(--home-spacing-inner);
}

.image-mode-tabs .tab-item {
  flex: 1;
  padding: 16rpx;
  text-align: center;
  background-color: transparent;
  font-size: var(--home-fs-tab);
  color: var(--home-text2);
  transition: all 0.2s ease;
  min-height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1rpx solid var(--home-border);

  &:last-child {
    border-right: none;
  }
}

.image-mode-tabs .tab-item.active {
  background-color: var(--home-primary);
  color: #ffffff;
  border-right-color: transparent;
}

/* URL模式预览 */
.intro-image-preview {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: var(--home-r-lg);
  overflow: hidden;
  margin-top: var(--home-spacing-card);
}

.intro-image-preview image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 底部占位 */
.bottom-placeholder {
  height: 120rpx;
}

/* 底部按钮 Footer */
.page-footer {
  padding: 24rpx var(--home-spacing-card);
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background-color: var(--home-card);
  // 若隐若现分割线（~4% 对比度）
  border-top: 1rpx solid rgba(17, 24, 39, 0.06);
  position: sticky;
  bottom: 0;
  z-index: 100;
}

// 主按钮：Pill 胶囊 + 品牌主色（对齐设计规范）
.create-btn {
  width: 100%;
  height: 88rpx;
  border-radius: var(--home-r-pill);
  font-size: var(--home-fs-section);
  font-weight: 500;
  color: #ffffff;
  background-color: var(--home-primary);
  border: none;
  transition: opacity 0.2s ease;
  
  &::after {
    border: none;
  }

  &:active:not(.disabled) {
    opacity: 0.85;
  }
  
  &.disabled {
    opacity: 0.45;
  }
}

/* 选择器弹窗 */
.picker-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-end;
}

.picker-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
}

.picker-content {
  position: relative;
  width: 100%;
  max-height: 50vh;
  background-color: var(--home-card);
  border-radius: var(--home-r-pill) var(--home-r-pill) 0 0; // 顶部大圆角
  display: flex;
  flex-direction: column;
  animation: slideUp 0.2s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 40rpx;
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.06);
  flex-shrink: 0;
}

.picker-title {
  font-size: var(--home-fs-banner);
  font-weight: 600;
  color: var(--home-text1);
}

.picker-close {
  font-size: 48rpx;
  color: var(--home-text2);
  line-height: 1;
  padding: 10rpx;
  min-width: 60rpx;
  min-height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 40rpx 40rpx;
  -webkit-overflow-scrolling: touch;
}

.picker-item {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid rgba(17, 24, 39, 0.05);
  min-height: 88rpx; // 热区 >= 44px
  
  &:last-child {
    border-bottom: none;
  }
  
  &:active {
    background-color: rgba(15, 118, 110, 0.04);
  }
}

.item-avatar,
.item-logo {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background-color: var(--home-border);
  flex-shrink: 0;
}

.item-logo {
  border-radius: var(--home-r-md);
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  overflow: hidden;
}

.item-name {
  font-size: var(--home-fs-card-title);
  font-weight: 600;
  color: var(--home-text1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-desc {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
