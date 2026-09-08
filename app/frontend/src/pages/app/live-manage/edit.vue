<template>
  <view class="edit-live-page">
    <!-- 加载状态 -->
    <view v-if="isLoading" class="loading-container">
      <view class="spinner"></view>
      <text>加载中...</text>
    </view>

    <!-- 内容区 -->
    <scroll-view v-else scroll-y class="page-content">
      <!-- 基础信息 -->
      <view class="form-section">
        <view class="section-title">基础信息</view>
        
        <!-- 房间标题（必填） -->
        <view class="form-item">
          <view class="item-label">
            <text>房间标题</text>
            <text class="required">*</text>
          </view>
          <input 
            class="item-input"
            v-model="formData.title"
            placeholder="请输入房间标题，100字以内"
            maxlength="100"
            :class="{ 'error': errors.title }"
          />
          <text v-if="errors.title" class="error-text">{{ errors.title }}</text>
          <view class="char-count">{{ formData.title.length }}/100</view>
        </view>
        
        <!-- 房间简介 -->
        <view class="form-item">
          <view class="item-label">
            <text>房间简介</text>
          </view>
          <textarea 
            class="item-textarea"
            v-model="formData.description"
            placeholder="请输入房间简介，500字以内"
            maxlength="500"
            :auto-height="true"
            :class="{ 'error': errors.description }"
          />
          <text v-if="errors.description" class="error-text">{{ errors.description }}</text>
          <view class="char-count">{{ formData.description.length }}/500</view>
        </view>
        
        <!-- 简介图片 -->
        <view class="form-item">
          <view class="item-label">
            <text>简介图片</text>
          </view>
          
          <!-- 图片上传方式选择 -->
          <view class="cover-upload-tabs">
            <view 
              class="tab-item" 
              :class="{ 'active': introImageMode === 'album' }"
              @click="handleIntroImageModeChange('album')"
            >
              <text>本地上传</text>
            </view>
            <view 
              class="tab-item" 
              :class="{ 'active': introImageMode === 'url' }"
              @click="handleIntroImageModeChange('url')"
            >
              <text>输入链接</text>
            </view>
          </view>
          
          <!-- 从相册选择 -->
          <view v-if="introImageMode === 'album'" class="cover-upload">
            <view v-if="formData.intro_image_url" class="cover-preview">
              <image :src="formData.intro_image_url" mode="aspectFill" />
              <view class="cover-remove" @click="formData.intro_image_url = ''; formData.intro_image_local_path = ''">
                <text class="remove-icon">✕</text>
              </view>
            </view>
            <view v-else class="cover-btn" @click="handleUploadIntroImage">
              <text class="upload-icon iconfont icon-add"></text>
              <text class="upload-text">上传图片</text>
              <text class="upload-tip">可选，用于图文展示</text>
            </view>
          </view>
          
          <!-- 输入URL -->
          <view v-if="introImageMode === 'url'" class="cover-url-input">
            <input 
              class="item-input"
              v-model="formData.intro_image_url"
              placeholder="请输入图片URL（可选）"
              @input="handleIntroImageUrlInput"
            />
            <view v-if="formData.intro_image_url" class="cover-preview-small">
              <image :src="formData.intro_image_url" mode="aspectFill" @error="handleIntroImageUrlError" />
            </view>
          </view>
          
          <view class="tip-text">可选，为直播间添加图文说明</view>
          
          <!-- 删除简介 Tab -->
          <view v-if="introTabId" class="form-item delete-tab-section">
            <view class="delete-tab-btn" @click="handleDeleteIntroTab">
              <text class="delete-icon iconfont icon-delete"></text>
              <text>删除直播简介</text>
            </view>
          </view>
        </view>
        
        <!-- 房间封面 -->
        <view class="form-item">
          <view class="item-label">
            <text>房间封面</text>
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
              placeholder="请输入图片URL"
              @input="handleCoverUrlInput"
            />
            <view v-if="formData.cover_url" class="cover-preview-small">
              <image :src="formData.cover_url" mode="aspectFill" @error="handleCoverUrlError" />
            </view>
          </view>
        </view>
        
        <!-- 房间状态（公开/私密） -->
        <view class="form-item">
          <view class="item-label">
            <text>房间状态</text>
          </view>
          <view class="switch-row">
            <switch 
              :checked="formData.is_private" 
              @change="handlePrivateChange"
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
            <text v-if="selectedCategories.length > 0" class="item-count">{{ selectedCategories.length }}/{{ MAX_CATEGORIES }}</text>
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
      </view>
      
      <!-- 场次信息 -->
      <view class="form-section">
        <view class="section-title">场次信息</view>
        
        <!-- 开始时间（必填） -->
        <view class="form-item">
          <view class="item-label">
            <text>开始时间</text>
            <text class="required">*</text>
          </view>
          <wd-datetime-picker
            v-model="startTimeTs"
            type="datetime"
            title="选择开始时间"
            :z-index="3000"
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
        
        <!-- 结束时间（可选） -->
        <view class="form-item">
          <view class="item-label">
            <text>结束时间</text>
          </view>
          <wd-datetime-picker
            v-model="endTimeTs"
            type="datetime"
            title="选择结束时间"
            :z-index="3000"
          >
            <view class="item-picker">
              <text :class="{ 'placeholder': !formData.end_time }">
                {{ endTimeDisplay }}
              </text>
              <text class="picker-arrow">›</text>
            </view>
          </wd-datetime-picker>
          <view class="tip-text">可选，留空表示未结束</view>
        </view>
        
        <!-- 场次状态 -->
        <view class="form-item">
          <view class="item-label">
            <text>场次状态</text>
          </view>
          <view class="item-picker item-picker--readonly">
            <text>{{ currentStatusLabel }}</text>
          </view>
          <!-- V15：external 场次手动状态操作（开播/停播/转回放/发布回放，即时生效；push 由推流回调驱动） -->
          <view v-if="isExternalSession" class="session-actions-row">
            <button
              v-for="action in sessionActions"
              :key="action.target"
              class="session-action-btn"
              :class="action.class"
              size="mini"
              @click="handleSwitchStatus(action.target, action.label)"
            >{{ action.label }}</button>
          </view>
          <view class="tip-text">{{ sessionStatusTipText }}</view>
        </view>
        
        <!-- 回放地址 -->
        <view class="form-item">
          <view class="item-label">
            <text>回放地址</text>
          </view>
          <input 
            class="item-input"
            v-model="formData.playback_url"
            placeholder="请输入回放视频链接（支持m3u8/mp4格式）"
            @blur="handlePlaybackUrlBlur"
            :class="{ 'error': errors.playback_url }"
          />
          <text v-if="errors.playback_url" class="error-text">{{ errors.playback_url }}</text>
          <view class="tip-text">支持 .m3u8、.mp4 等格式的视频链接</view>
        </view>

        <!-- 场次标签 -->
        <view class="form-item">
          <view class="item-label">
            <text>直播标签</text>
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
          <view class="tip-text">标签作用于最新场次，保存后生效</view>
          <view v-if="selectedTags.length >= MAX_SESSION_TAGS" class="tip-text">最多可添加 {{ MAX_SESSION_TAGS }} 个标签，如需更换请先删除</view>
        </view>
      </view>
      
      <!-- 提示信息 -->
      <view class="tip-box">
        <view class="tip-content">
          <text class="tip-title">温馨提示</text>
          <text class="tip-text">• 房间标题为必填项</text>
          <text class="tip-text">• 修改封面会同步更新</text>
          <text class="tip-text">• 场次状态影响用户显示</text>
        </view>
      </view>
      
      <!-- 底部占位 -->
      <view class="bottom-placeholder"></view>
    </scroll-view>
    
    <!-- 底部操作栏 -->
    <view class="page-footer">
      <view class="footer-buttons">
        <button class="cancel-btn" @click="handleCancel">取消</button>
        <button 
          class="save-btn"
          :class="{ 'disabled': !canSubmit }"
          :disabled="!canSubmit"
          :loading="isSaving"
          @click="handleSave"
        >
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
      </view>
    </view>
    
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
      empty-text="未找到匹配的标签"
      @update:selected-ids="handleTagIdsChange"
      @confirm="closeTagPicker"
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
import { 
  isoToLocalTimestamp,
  isoToLocalDateTimeDisplay,
  timestampToLocalDateTimeISO
} from '@/utils/datetime';
import WdDatetimePicker from 'wot-design-uni/components/wd-datetime-picker/wd-datetime-picker.vue';
import { validatePlaybackUrl } from '@/utils/videoUrl';
import { isValidUUID } from '@/utils/url';
import type { SessionStatus } from '@/types/session';
import type { Tab, TabContentType } from '@/types/tab';
import { getPublicRoomTabList, updateRoomTab, uploadTabImage, deleteRoomTab } from '@/api/tab';
import { getCategories } from '@/api/category';
import { getRoomCategories } from '@/api/roomCategories';
import { getTags, resolveTag } from '@/api/tag';
import { getSessionTags, setSessionTags } from '@/api/sessionTags';
import PickerSheet, { type PickerItem } from '@/components/common/PickerSheet.vue';
import type { Category } from '@/types/category';
import type { Tag, TagChip, TagResolveResult } from '@/types/tag';
import { MAX_SESSION_TAGS } from '@/constants/live';
import { hasChipName, pushChipUnique, pruneInactiveChips } from '@/utils/tagChip';

type BackendSessionStatus = SessionStatus | 'finished' | 'processing' | 'ready' | 'error';

const roomStore = useRoomStore();
const sessionStore = useSessionStore();
const authStore = useAuthStore();

// 椤甸潰鍙傛暟
const roomId = ref('');
const sessionId = ref('');
const introTabId = ref(''); // 鐩存挱浠嬬粛Tab鐨処D

// 加载和保存状态
const isLoading = ref(true);
const isSaving = ref(false);

// 琛ㄥ崟鏁版嵁
const formData = ref({
  title: '',
  description: '',
  cover_url: '',
  cover_local_path: '', // 本地临时路径，用于上传
  is_private: false,
  start_time: '',
  end_time: '',
  status: 'scheduled' as BackendSessionStatus,
  playback_url: '',
  // 直播简介图文混排（intro Tab）
  intro_content_type: 'text' as TabContentType,
  intro_text: '',
  intro_image_url: '',
  intro_image_local_path: '' // 简介图片本地路径
});
const originalSessionStatus = ref<BackendSessionStatus | ''>('');
const originalPlaybackUrl = ref('');
// V15：场次来源（push=推流回调驱动 / external=外部流手动管理），用于状态只读文案区分
const sessionSourceType = ref<'push' | 'external' | ''>('');

// 封面上传模式
const coverUploadMode = ref<'album' | 'url'>('url');
// 简介图片上传模式
const introImageMode = ref<'album' | 'url'>('url');

// 错误信息
const errors = ref({
  title: '',
  description: '',
  start_time: '',
  playback_url: ''
});

// 开播/结束时间（wd-datetime-picker：时间戳 v-model，watch 回写 ISO 契约到 formData）
const startTimeTs = ref<number | null>(null);
const endTimeTs = ref<number | null>(null);

const startTimeDisplay = computed(() => {
  return (formData.value.start_time && isoToLocalDateTimeDisplay(formData.value.start_time)) || '请选择开始时间';
});
const endTimeDisplay = computed(() => {
  return (formData.value.end_time && isoToLocalDateTimeDisplay(formData.value.end_time)) || '请选择结束时间';
});

watch(startTimeTs, (val) => {
  formData.value.start_time = val ? timestampToLocalDateTimeISO(val) : '';
  errors.value.start_time = '';
});
watch(endTimeTs, (val) => {
  formData.value.end_time = val ? timestampToLocalDateTimeISO(val) : '';
});

// 直播分类（支持多选，最多10个；编辑时回填、保存时随 PATCH 提交）
const MAX_CATEGORIES = 10;
const selectedCategories = ref<Category[]>([]);
const categoryList = ref<Category[]>([]);
const showCategoryPicker = ref(false);
// 分类数据是否已成功回填：false 时不提交 category_ids，防止回填失败导致误清空
const categoriesLoaded = ref(false);

// 分类可选项（toggle 面板：展示全量含已选，勾选/取消由组件管理）
const categoryPickerItems = computed<PickerItem[]>(() => {
  return categoryList.value.map(c => ({
    id: c.id,
    name: c.display_name || c.name,
    subtitle: c.parent_id ? undefined : undefined
  }));
});

// 打开分类选择器（实时拉取分类列表）
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

// 移除已选分类
const removeCategory = (idx: number) => {
  selectedCategories.value.splice(idx, 1);
};

// ===== 场次标签（A1：回填/多选/移除/replace 提交/防误清空；V2：上限 5 + resolve 自建） =====
const selectedTags = ref<TagChip[]>([]);
const tagList = ref<Tag[]>([]);
const showTagPicker = ref(false);
// 标签数据是否已成功回填：false 时不提交 tag_ids，防止回填失败导致误清空
const tagsLoaded = ref(false);
// 用户是否操作过标签：仅操作过才提交
const tagsModified = ref(false);
/** resolve 进行中（PickerSheet createPending；防重复提交） */
const tagResolving = ref(false);

// 打开标签选择器（懒加载全量标签；仅展示启用标签）
const handleOpenTagPicker = async () => {
  try {
    if (tagList.value.length === 0) {
      const response = await getTags();
      if (response.data) {
        tagList.value = response.data.filter((t: Tag) => t.is_active !== false);
      }
    }
    showTagPicker.value = true;
  } catch (error) {
    console.error('[edit] 获取标签列表失败:', error);
    uni.showToast({ title: '获取标签列表失败', icon: 'none' });
  }
};

const closeTagPicker = () => {
  showTagPicker.value = false;
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
  tagsModified.value = true;
};

// 移除标签
const removeTag = (idx: number) => {
  selectedTags.value.splice(idx, 1);
  tagsModified.value = true;
};

// ===== 标签 resolve 自建（V2：与创建页同构；成功/复用均落 chip 并并入词表；操作即置 tagsModified） =====
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

/** PickerSheet @create：resolve 创建/复用并落 chip；并入 tagList 使新词留在面板可管理 */
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
    tagsModified.value = true;
    if (res.created) {
      uni.showToast({ title: '已添加新标签', icon: 'none' });
    }
  } catch (error) {
    // resolve 错误（401/400/4001/422/网络）由 request 层统一 toast；此处不落 chip、不重复提示
    console.error('❌ [编辑直播] resolve 标签失败:', error);
  } finally {
    tagResolving.value = false;
  }
};

// 场次状态文案（六态全量）
const statusLabelMap: Record<string, string> = {
  scheduled: '预告',
  live: '直播中',
  finished: '已结束',
  processing: '回放生成中',
  ready: '回放',
  error: '回放生成失败'
};

const currentStatusLabel = computed(() => {
  const status = formData.value.status as string;
  return (status && statusLabelMap[status]) || '未知状态';
});

// V15：external 场次手动状态操作（与后端状态矩阵一致）
// scheduled→开播/直接发回放；live→停播/转回放；finished→恢复开播/发布回放；ready 为终态无操作
const isExternalSession = computed(() => sessionSourceType.value === 'external');

const sessionActions = computed(() => {
  const actions: { target: string; label: string; class: string }[] = [];
  switch (formData.value.status) {
    case 'scheduled':
      actions.push({ target: 'live', label: '开播', class: 'btn-primary' });
      actions.push({ target: 'ready', label: '直接发回放', class: 'btn-plain' });
      break;
    case 'live':
      actions.push({ target: 'finished', label: '停播', class: 'btn-danger' });
      actions.push({ target: 'ready', label: '转回放', class: 'btn-plain' });
      break;
    case 'finished':
      actions.push({ target: 'live', label: '恢复开播', class: 'btn-primary' });
      actions.push({ target: 'ready', label: '发布回放', class: 'btn-plain' });
      break;
    default:
      break;
  }
  return actions;
});

const sessionStatusTipText = computed(() => {
  if (sessionSourceType.value !== 'external') {
    return '该状态由系统流程生成，不能手动切换';
  }
  return formData.value.status === 'ready'
    ? '回放已发布，状态不可变更'
    : '手动切换即时生效，切换后将刷新场次信息';
});

// V15：手动切换场次状态（开播/停播/转回放/恢复开播/发布回放；external 场次专用）
// 转 live/ready 必须携带播放地址（后端守卫；优先使用回放地址输入框已填值）
const handleSwitchStatus = (target: string, label: string) => {
  if (!sessionId.value) return;

  if ((target === 'live' || target === 'ready') && !formData.value.playback_url.trim()) {
    uni.showToast({ title: '请先在回放地址填写直播流/视频地址', icon: 'none' });
    return;
  }

  uni.showModal({
    title: `确认${label}`,
    content: `确定要将当前场次切换为"${label}"状态吗？切换后状态即时生效。`,
    success: async (res) => {
      if (!res.confirm) return;
      uni.showLoading({ title: '切换中...', mask: true });
      try {
        const result = await sessionStore.updateSessionStatus(sessionId.value, roomId.value, {
          status: target,
          ...((target === 'live' || target === 'ready') ? { playback_url: formData.value.playback_url } : {}),
        });
        uni.hideLoading();
        if (result.success) {
          uni.showToast({ title: `${label}成功`, icon: 'success' });
          await refreshSessionFields();
        } else {
          // 409 并发冲突提示
          const message = result.message || '状态切换失败';
          uni.showToast({ title: message.includes('并发') ? '状态已变化，请刷新重试' : message, icon: 'none' });
        }
      } catch (error) {
        uni.hideLoading();
        uni.showToast({ title: '状态切换失败，请重试', icon: 'none' });
      }
    }
  });
};

// 状态切换成功后仅刷新场次信息（保留房间表单未保存修改；R1 最小副作用策略）
const refreshSessionFields = async () => {
  if (!sessionId.value) return;
  try {
    await sessionStore.fetchSessionsByRoomId(roomId.value, { refresh: true });
    await sessionStore.fetchSessionById(sessionId.value);
    applySessionDetail(sessionStore.currentSession);
  } catch (error) {
    console.error('❌ [编辑直播] 切换后刷新场次信息失败:', error);
  }
};

watch(() => formData.value.playback_url, (newVal) => {
  // 仅非 external（push/未知来源）保留"填地址=置回放"的既有表单语义；
  // external 场次状态由上方操作按钮显式切换（POST /sessions/{id}/status）
  if (sessionSourceType.value === 'external') {
    return;
  }
  if (originalSessionStatus.value !== 'scheduled') {
    return;
  }
  formData.value.status = newVal ? 'ready' : 'scheduled';
});

/**
 * 椤甸潰鍔犺浇
 */
onLoad(async (options) => {
  console.log('[edit]');
  
  // 检查登录状态
  if (!authStore.isAuthenticated) {
    uni.showToast({
      title: '璇峰厛鐧诲綍',
      icon: 'none'
    });
    setTimeout(() => {
      uni.navigateBack();
    }, 1500);
    return;
  }
  
  if (!options || !options.roomId) {
    uni.showToast({
      title: '缂哄皯鎴块棿ID',
      icon: 'none'
    });
    setTimeout(() => {
      uni.navigateBack();
    }, 1500);
    return;
  }
  
  roomId.value = options.roomId as string;
  await loadData();
});

/**
 * 回填场次字段到表单（loadData 与状态切换刷新共用；最小副作用：不触碰房间字段）
 */
const applySessionDetail = (sessionDetail: any) => {
  if (!sessionDetail) return;

  let startTime = sessionDetail.start_time;
  let endTime = sessionDetail.end_time;

  if (startTime && /\+\d{2}:\d{2}Z$/.test(startTime)) {
    console.warn('⚠️ [编辑直播] 后端返回了无效的开始时间格式（+XX:XXZ）', startTime);
    startTime = startTime.replace(/Z$/, '');
  }
  if (endTime && /\+\d{2}:\d{2}Z$/.test(endTime)) {
    console.warn('⚠️ [编辑直播] 后端返回了无效的结束时间格式（+XX:XXZ）', endTime);
    endTime = endTime.replace(/Z$/, '');
  }

  if (startTime) {
    formData.value.start_time = startTime;
    startTimeTs.value = isoToLocalTimestamp(startTime);
  } else {
    console.warn('⚠️ [编辑直播] 场次没有开始时间');
  }

  if (endTime) {
    formData.value.end_time = endTime;
    endTimeTs.value = isoToLocalTimestamp(endTime);
  } else {
    formData.value.end_time = '';
    endTimeTs.value = null;
  }

  formData.value.status = sessionDetail.status || 'scheduled';
  originalSessionStatus.value = formData.value.status;
  formData.value.playback_url = sessionDetail.playback_url || '';
  originalPlaybackUrl.value = formData.value.playback_url;
  sessionSourceType.value = (sessionDetail as any).source_type || '';
};

/**
 * 鍔犺浇鎴块棿鍜屽満娆℃暟鎹? */
const loadData = async () => {
  try {
    isLoading.value = true;
    
    // 鍔犺浇鎴块棿淇℃伅
    await roomStore.fetchRoomById(roomId.value);
    const room = roomStore.currentRoom;
    
    if (!room) {
      throw new Error('房间不存在');
    }
    
    // [fixed]
    formData.value.title = room.title || '';
    formData.value.description = room.description || '';
    formData.value.cover_url = room.cover_url || '';
    formData.value.is_private = room.is_private || false;
    
    // 回填已关联分类
    try {
      const catResponse = await getRoomCategories(roomId.value);
      if (catResponse.data) {
        selectedCategories.value = catResponse.data;
        categoriesLoaded.value = true;
      }
    } catch (catError) {
      console.error('[edit] 获取房间分类失败:', catError);
    }
    
    // 鍒ゆ柇灏侀潰妯″紡
    if (formData.value.cover_url && formData.value.cover_url.startsWith('http')) {
      coverUploadMode.value = 'url';
    }
    
    // [fixed]
    console.log('[edit] 开始加载场次信息', { room_id: roomId.value });
    await sessionStore.fetchSessionsByRoomId(roomId.value, { refresh: true });
    const sessions = sessionStore.sessions;
    
    console.log('[edit] 场次列表:', {
      count: sessions?.length || 0,
      sessions: sessions?.map(s => ({ id: s.id, start_time: s.start_time }))
    });
    
    if (sessions && sessions.length > 0) {
      const session = sessions[0]; // 使用第一个场次
      sessionId.value = session.id;
      
      console.log('[edit]');
      
      // [fixed]
      await sessionStore.fetchSessionById(sessionId.value);
      const sessionDetail = sessionStore.currentSession;
      
      // [fixed]
      console.log('[edit]');
      
      if (sessionDetail) {
        applySessionDetail(sessionDetail);
      }
    }
    
    // 加载直播简介Tab（intro）
    try {
      const tabsResponse = await getPublicRoomTabList(roomId.value);
      const tabs = (tabsResponse.data as any)?.items || tabsResponse.data || [];
      const introTab = tabs.find((tab: Tab) => tab.tab_key === 'intro');
      
      if (introTab) {
        introTabId.value = introTab.id;
        formData.value.intro_content_type = introTab.content_type || 'text';
        formData.value.intro_text = introTab.text_content || '';
        formData.value.intro_image_url = introTab.image_url || '';
        
        // 判断简介图片模式
        if (formData.value.intro_image_url && formData.value.intro_image_url.startsWith('http')) {
          introImageMode.value = 'url';
        }
      }
    } catch (error) {
      console.warn('⚠️ [编辑直播] 获取直播简介失败', error);
      // 简介不是必须的，失败不影响其他数据加载
    }
    
    // 回填场次标签（A1：回显仅启用词；映射为 TagChip 形态）
    if (sessionId.value) {
      try {
        const tagRes = await getSessionTags(sessionId.value);
        const tags = (tagRes.data as any) || [];
        selectedTags.value = Array.isArray(tags)
          ? tags
              .filter((t: Tag) => t.is_active !== false)
              .map((t: Tag) => ({ id: t.id, name: t.name }))
          : [];
        tagsLoaded.value = true;
        console.log('[edit] 标签回填完成:', selectedTags.value.length);
      } catch (tagError) {
        console.warn('⚠️ [编辑直播] 获取场次标签失败', tagError);
        // 回填失败：不置 tagsLoaded，保存时不提交标签（防误清空）
      }
    }
    
    // 初始化时间选择器
    initTimePickers();
    
    console.log('[edit]');
  } catch (error: any) {
    console.error('鉂?[缂栬緫鐩存挱] 鍔犺浇澶辫触:', error);
    uni.showToast({
      title: error.message || '鍔犺浇澶辫触',
      icon: 'none'
    });
    setTimeout(() => {
      uni.navigateBack();
    }, 1500);
  } finally {
    isLoading.value = false;
  }
};

/**
 * 初始化时间选择器（仅无开始时间时置默认：当前 +30 分钟，沿用原 5 分钟取整口径）
 */
const initTimePickers = () => {
  if (!formData.value.start_time) {
    const d = new Date(Date.now() + 30 * 60 * 1000);
    d.setSeconds(0, 0);
    d.setMinutes(Math.ceil(d.getMinutes() / 5) * 5);
    startTimeTs.value = d.getTime();
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
        uni.getFileInfo({
          filePath: res.tempFilePaths[0],
          success: (fileInfo) => {
            if (fileInfo.size > 5 * 1024 * 1024) {
              uni.showToast({
                title: '灏侀潰鍥剧墖涓嶈兘瓒呰繃5MB',
                icon: 'none'
              });
              return;
            }
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
 * 灏侀潰妯″紡鍒囨崲
 */
const handleCoverModeChange = (mode: 'album' | 'url') => {
  if (mode === 'url' && coverUploadMode.value === 'album') {
    formData.value.cover_local_path = '';
  } else if (mode === 'album' && coverUploadMode.value === 'url') {
    formData.value.cover_url = '';
  }
  coverUploadMode.value = mode;
};

/**
 * 灏侀潰URL杈撳叆鍙樺寲
 */
const handleCoverUrlInput = () => {
  formData.value.cover_local_path = '';
};

/**
 * [fixed]
 */
const handleCoverUrlError = () => {
  uni.showToast({
    title: '图片URL无效或无法加载',
    icon: 'none'
  });
};

/**
 * 简介图片上传
 */
const handleUploadIntroImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      if (res.tempFilePaths && res.tempFilePaths.length > 0) {
        uni.getFileInfo({
          filePath: res.tempFilePaths[0],
          success: (fileInfo) => {
            if (fileInfo.size > 5 * 1024 * 1024) {
              uni.showToast({
                title: '鍥剧墖涓嶈兘瓒呰繃5MB',
                icon: 'none'
              });
              return;
            }
            formData.value.intro_image_url = res.tempFilePaths[0];
            formData.value.intro_image_local_path = res.tempFilePaths[0];
            // [fixed]
            if (formData.value.intro_content_type === 'text' && formData.value.intro_text) {
              formData.value.intro_content_type = 'mixed';
            }
            uni.showToast({
              title: '图片已选择',
              icon: 'success'
            });
          }
        });
      }
    }
  });
};

/**
 * 简介图片模式切换
 */
const handleIntroImageModeChange = (mode: 'album' | 'url') => {
  if (mode === 'url' && introImageMode.value === 'album') {
    formData.value.intro_image_local_path = '';
  } else if (mode === 'album' && introImageMode.value === 'url') {
    formData.value.intro_image_url = '';
  }
  introImageMode.value = mode;
};

/**
 * 简介图片URL输入变化
 */
const handleIntroImageUrlInput = () => {
  formData.value.intro_image_local_path = '';
  // [fixed]
  if (formData.value.intro_image_url && formData.value.intro_text) {
    formData.value.intro_content_type = 'mixed';
  }
};

/**
 * 简介图片URL加载错误
 */
const handleIntroImageUrlError = () => {
  uni.showToast({
    title: '图片URL无效或无法加载',
    icon: 'none'
  });
};

/**
 * 绉婚櫎灏侀潰
 */
const removeCover = () => {
  formData.value.cover_url = '';
  formData.value.cover_local_path = '';
};

/**
 * 房间状态切换
 */
const handlePrivateChange = (e: any) => {
  formData.value.is_private = e.detail.value;
};

/**
 * 鍥炴斁鍦板潃澶辩劍楠岃瘉
 */
const handlePlaybackUrlBlur = () => {
  if (!formData.value.playback_url) {
    errors.value.playback_url = '';
    return;
  }
  
  const result = validatePlaybackUrl(formData.value.playback_url);
  if (!result.valid) {
        errors.value.playback_url = result.message || '格式错误';
  } else {
    errors.value.playback_url = '';
  }
};

/**
 * 琛ㄥ崟楠岃瘉
 */
const validateForm = (): boolean => {
  errors.value = {
    title: '',
    description: '',
    start_time: '',
    playback_url: ''
  };
  
  let isValid = true;
  
  if (!formData.value.title.trim()) {
    errors.value.title = '请输入房间标题';
    isValid = false;
  }
  
  if (!formData.value.start_time) {
    errors.value.start_time = '请选择开始时间';
    isValid = false;
  }
  
  if (formData.value.playback_url) {
    const result = validatePlaybackUrl(formData.value.playback_url);
    if (!result.valid) {
            errors.value.playback_url = result.message || '格式错误';
      isValid = false;
    }
  }

  const isExistingBrokenReady = (
    originalSessionStatus.value === 'ready'
    && !originalPlaybackUrl.value
    && !formData.value.playback_url
  );
  if (formData.value.status === 'ready' && !formData.value.playback_url && !isExistingBrokenReady) {
    errors.value.playback_url = '回放状态必须填写回放地址';
    isValid = false;
  }
  
  return isValid;
};

/**
 * [fixed]
 */
const canSubmit = computed(() => {
  return formData.value.title.trim().length > 0 && !isSaving.value;
});

/**
 * 鍙栨秷缂栬緫
 */
const handleCancel = () => {
  uni.showModal({
    title: '确认取消',
    content: '确定要取消编辑吗？未保存的修改将丢失',
    success: (res) => {
      if (res.confirm) {
        uni.navigateBack();
      }
    }
  });
};

/**
 * 删除直播简介 Tab
 */
const handleDeleteIntroTab = () => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除直播简介吗？删除后直播间将不再显示图文说明内容',
    success: async (res) => {
      if (res.confirm) {
        try {
          isSaving.value = true;
          await deleteRoomTab(introTabId.value);
          introTabId.value = '';
          formData.value.intro_text = '';
          formData.value.intro_image_url = '';
          formData.value.intro_image_local_path = '';
          formData.value.intro_content_type = 'text';
          uni.showToast({ title: '删除成功', icon: 'success' });
        } catch (error: any) {
          uni.showToast({
            title: error.message || '删除失败',
            icon: 'none'
          });
        } finally {
          isSaving.value = false;
        }
      }
    }
  });
};

/**
 * [fixed]
 */
const handleSave = async () => {
  if (!validateForm()) {
    const firstError = Object.values(errors.value).find(err => err);
    if (firstError) {
      uni.showToast({
        title: firstError,
        icon: 'none'
      });
    }
    return;
  }
  
  try {
    isSaving.value = true;
    
    console.log('[edit] 准备保存，当前表单数据:', {
      start_time: formData.value.start_time,
      start_time_type: typeof formData.value.start_time,
      end_time: formData.value.end_time,
      end_time_type: typeof formData.value.end_time,
      playback_url: formData.value.playback_url
    });
    
    // 1. 鏇存柊鎴块棿淇℃伅
    const roomUpdateData: any = {
      title: formData.value.title,
      description: formData.value.description,
      is_private: formData.value.is_private
    };
    
    // 分类随 PATCH 提交（replace 语义；空数组=清空；仅提交 UUID 格式分类）
    // 仅在分类回填成功后提交，防止回填失败（网络异常）时误清空已有分类
    if (categoriesLoaded.value) {
      const validCategoryIds = selectedCategories.value
        .map(c => c.id)
        .filter(id => isValidUUID(id));
      roomUpdateData.category_ids = validCategoryIds;
    }
    
    // 濡傛灉鏄疷RL妯″紡锛岀洿鎺ヤ娇鐢║RL
    if (coverUploadMode.value === 'url' && formData.value.cover_url) {
      roomUpdateData.cover_url = formData.value.cover_url;
    }
    
    await roomStore.updateRoom(roomId.value, roomUpdateData);
    
    // 2. 濡傛灉鏈夋湰鍦板皝闈㈡枃浠讹紝涓婁紶灏侀潰
    if (formData.value.cover_local_path && coverUploadMode.value === 'album') {
      await uploadRoomCover(roomId.value, formData.value.cover_local_path);
    }
    
    // [fixed]
      console.log('[edit]');
      console.log('[edit]');
      
      // [fixed]
      let startTime = formData.value.start_time;
      let endTime = formData.value.end_time;
      
      // 检测并修复异常的时间格式（如 2025-12-31T16:00:00+00:00Z）
      if (startTime && /\+\d{2}:\d{2}Z$/.test(startTime)) {
        console.warn('⚠️ [编辑直播] 检测到异常的开始时间格式', startTime);
        startTime = startTime.replace(/Z$/, ''); // 移除末尾的Z
        console.log('✅ [编辑直播] 修正后的开始时间', startTime);
      }
      if (endTime && /\+\d{2}:\d{2}Z$/.test(endTime)) {
        console.warn('⚠️ [编辑直播] 检测到异常的结束时间格式', endTime);
        endTime = endTime.replace(/Z$/, ''); // 移除末尾的Z
        console.log('[edit]');
      }
      
      const editableStatuses: BackendSessionStatus[] = ['scheduled', 'ready'];
      const canEditSession = editableStatuses.includes(originalSessionStatus.value as BackendSessionStatus);
      const canRecoverError = originalSessionStatus.value === 'error' && !!formData.value.playback_url;
      const isExistingBrokenReady = (
        originalSessionStatus.value === 'ready'
        && !originalPlaybackUrl.value
        && !formData.value.playback_url
      );
      // V15：仅非 external 场次在状态实际变化时才提交 status 字段——
      // external 场次 PATCH 带 status 会转发 switch_external_status（丢弃时间字段），
      // external 场次状态切换统一走页面操作按钮（POST /sessions/{id}/status）即时生效；
      // 未变化时带 status 将导致开始/结束时间修改静默丢失（幂等返回不更新时间）
      const statusChanged = formData.value.status !== originalSessionStatus.value;
      const sessionUpdateData: any = {};

      if (canEditSession && !isExistingBrokenReady) {
        sessionUpdateData.start_time = startTime;

        if (statusChanged && sessionSourceType.value !== 'external') {
          sessionUpdateData.status = formData.value.status;
        }

        if (endTime) {
          sessionUpdateData.end_time = endTime;
        }

        if (formData.value.playback_url) {
          sessionUpdateData.playback_url = formData.value.playback_url;
        }

        if (Object.keys(sessionUpdateData).length > 0) {
          console.log('📦 [编辑直播] 发送场次更新数据', sessionUpdateData);
          console.log('馃摛 [缂栬緫鐩存挱] 璇锋眰鏂规硶: PATCH');
          console.log('馃摛 [缂栬緫鐩存挱] 璇锋眰URL: /sessions/' + sessionId.value);

          const result = await sessionStore.updateSession(sessionId.value, sessionUpdateData);

          console.log('[edit]');
          console.log('[edit]');
        } else {
          console.log('ℹ️ [编辑直播] 当前场次状态由系统管理，跳过场次状态更新', originalSessionStatus.value);
        }
      } else if (canRecoverError) {
        sessionUpdateData.status = 'ready';
        sessionUpdateData.playback_url = formData.value.playback_url;
      } else {
        console.warn('[edit]');
      }
    
    // 4. 更新直播简介Tab（如果有intro Tab）
    if (introTabId.value) {
      // 使用description作为直播简介文本，确定内容类型
      const hasText = formData.value.description && formData.value.description.trim();
      const hasImage = formData.value.intro_image_url || formData.value.intro_image_local_path;
      
      let contentType: TabContentType = 'text';
      if (hasText && hasImage) {
        contentType = 'mixed';
      } else if (hasText && !hasImage) {
        contentType = 'text';
      } else if (!hasText && hasImage) {
        contentType = 'image';
      }
      
      // [fixed]
      const introUpdateData: any = {
        content_type: contentType,
        text_content: formData.value.description || null
      };
      
      // 如果有本地简介图片，先上传
      if (formData.value.intro_image_local_path && introImageMode.value === 'album') {
        try {
          const uploadedImageUrl = await uploadTabImage(roomId.value, formData.value.intro_image_local_path);
          introUpdateData.image_url = uploadedImageUrl;
        } catch (uploadError) {
          console.error('❌ [编辑直播] 简介图片上传失败', uploadError);
          // [fixed]
        }
      } else if (introImageMode.value === 'url') {
        // 使用URL模式的图片
        introUpdateData.image_url = formData.value.intro_image_url || null;
      }
      
      // 更新intro Tab
      await updateRoomTab(introTabId.value, introUpdateData);
    }
    
    // 5. 更新场次标签（A1 双闸保留；V2：失败中止"保存成功+返回"，4001 差集剔除自动重试一次；剔光不提交 [] 防误清空）
    let tagSaveFailed = false;
    const tryBindTags = async (tagIds: string[]) => {
      await setSessionTags(sessionId.value, { tag_ids: tagIds, mode: 'replace' });
    };
    if (sessionId.value && tagsLoaded.value && tagsModified.value) {
      try {
        if (selectedTags.value.length > MAX_SESSION_TAGS) {
          // legacy >5 防御：存量超限场次必须先删到 ≤5（I4-5）
          uni.showToast({ title: `最多 ${MAX_SESSION_TAGS} 个标签，请先删除多余标签`, icon: 'none' });
          tagSaveFailed = true;
        } else {
          console.log('[edit] 标签提交 replace，数量:', selectedTags.value.length);
          await tryBindTags(selectedTags.value.map((t) => t.id));
          console.log('[edit] 标签更新成功:', selectedTags.value.length);
        }
      } catch (tagError: any) {
        if (tagError?.code === 4001) {
          console.warn('⚠️ [编辑直播] 标签绑定 4001（部分停用/不存在），按启用词表差集剔除后重试一次');
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
                console.log('[edit] 标签剔除后重试成功:', pruned.length);
              } catch (retryError) {
                console.error('❌ [编辑直播] 标签剔除后重试失败:', retryError);
                tagSaveFailed = true;
              }
            } else {
              // 剔光：不 bind、不提交 []（防误清空存量关联），仅提示（§4.4）
              uni.showToast({ title: '所选标签均已停用，请重新选择', icon: 'none' });
              tagSaveFailed = true;
            }
          } else {
            tagSaveFailed = true; // 词表异常或剔除无变化 → 不再自动重试（避免反复 4001）
          }
        } else {
          // 其它错误（403/422/网络）request 层已 toast；此处标记失败即可
          console.error('❌ [编辑直播] 标签更新失败', tagError);
          tagSaveFailed = true;
        }
      }
    }

    if (tagSaveFailed) {
      // I4-3：失败不落"保存成功+返回"；房间/场次等修改已保存（幂等），停留页面可重试
      uni.showToast({ title: '房间其他修改已保存，标签保存失败，请重试', icon: 'none', duration: 2500 });
      return;
    }

    uni.showToast({
      title: '保存成功',
      icon: 'success'
    });
    
    // [fixed]
    setTimeout(() => {
      uni.navigateBack();
    }, 1500);
    
  } catch (error: any) {
    console.error('鉂?[缂栬緫鐩存挱] 淇濆瓨澶辫触:', error);
    uni.showToast({
      title: error.message || '淇濆瓨澶辫触',
      icon: 'none'
    });
  } finally {
    isSaving.value = false;
  }
};

/**
 * 涓婁紶鎴块棿灏侀潰
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
          reject(new Error('涓婁紶澶辫触'));
        }
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
};
</script>

<style lang="scss" scoped>
/* 编辑直播页 - 对齐设计系统 Tokens */
.edit-live-page {
  min-height: 100vh;
  background-color: var(--home-bg);
  padding-bottom: calc(120rpx + env(safe-area-inset-bottom));
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 24rpx;
}

.spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid rgba(17, 24, 39, 0.08);
  border-top-color: var(--home-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.page-content {
  height: 100vh;
  padding: 24rpx 0;
}

.form-section {
  margin-bottom: var(--home-spacing-card);
  padding: 32rpx 32rpx 16rpx;
  background-color: var(--home-card);
  border-radius: var(--home-r-lg);
  box-shadow: var(--home-shadow-card);
}

.section-title {
  font-size: var(--home-fs-section);
  font-weight: 600;
  color: var(--home-text1);
  margin-bottom: 32rpx;
  padding-left: 16rpx;
  border-left: 5rpx solid var(--home-primary);
}

.form-item {
  margin-bottom: 32rpx;
  
  &:last-child {
    margin-bottom: 16rpx;
  }
}

.item-label {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: var(--home-spacing-inner);
  font-size: var(--home-fs-card-title);
  color: var(--home-text2);
}

.required {
  color: var(--color-danger);
  font-size: 32rpx;
}

.item-input {
  height: 88rpx;
  padding: 0 24rpx;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  background-color: var(--home-bg);
  border-radius: var(--home-r-md);
  border: 1.5rpx solid var(--home-border);
  transition: all 0.2s ease;
  
  &:focus {
    border-color: var(--home-primary);
    background-color: var(--home-card);
  }
  
  &.error {
    border-color: var(--color-danger);
    background-color: rgba(220, 53, 69, 0.04);
  }
}

.item-textarea {
  min-height: 180rpx;
  padding: 20rpx 24rpx;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  background-color: var(--home-bg);
  border-radius: var(--home-r-md);
  border: 1.5rpx solid var(--home-border);
  line-height: 1.6;
  transition: all 0.2s ease;
  
  &:focus {
    border-color: var(--home-primary);
    background-color: var(--home-card);
  }
  
  &.error {
    border-color: var(--color-danger);
    background-color: rgba(220, 53, 69, 0.04);
  }
}

.char-count {
  margin-top: 10rpx;
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
  text-align: right;
}

.error-text {
  display: block;
  margin-top: 10rpx;
  font-size: var(--home-fs-meta);
  color: var(--color-danger);
}

.item-picker {
  height: 88rpx;
  padding: 0 24rpx;
  min-height: 88rpx;
  background-color: var(--home-bg);
  border-radius: var(--home-r-md);
  border: 1.5rpx solid var(--home-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
  transition: border-color 0.2s ease;
  
  .placeholder {
    color: var(--home-tabbar-inactive);
  }
}

.picker-arrow {
  font-size: 32rpx;
  color: var(--home-tabbar-inactive);
}

/* V15：external 场次手动状态操作按钮组（与详情页样式一致） */
.session-actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 16rpx;
}

.session-action-btn {
  font-size: 24rpx;
  line-height: 1.6;
  padding: 4rpx 20rpx;
  border-radius: 8rpx;
  margin: 0;

  &.btn-primary {
    background: var(--home-primary);
    color: #ffffff;
  }

  &.btn-danger {
    background: var(--color-danger);
    color: #ffffff;
  }

  &.btn-plain {
    background: var(--home-bg);
    color: var(--home-text1);
    border: 1rpx solid var(--home-border);
  }
}

.cover-upload-tabs {
  display: flex;
  border: 2rpx solid var(--home-border);
  border-radius: var(--home-r-md);
  overflow: hidden;
  margin-bottom: 24rpx;
}

.tab-item {
  flex: 1;
  padding: 18rpx 16rpx;
  text-align: center;
  background-color: transparent;
  border-right: 1rpx solid var(--home-border);
  font-size: var(--home-fs-tab);
  color: var(--home-text2);
  transition: all 0.2s ease;
  
  &:last-child {
    border-right: none;
  }
  
  &.active {
    background-color: var(--home-primary);
    color: #ffffff;
    border-right-color: transparent;
  }
}

.cover-upload {
  position: relative;
}

.cover-preview,
.cover-btn {
  width: 100%;
  height: 360rpx;
  border-radius: var(--home-r-lg);
  overflow: hidden;
}

.cover-preview {
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
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .remove-icon {
    color: #ffffff;
    font-size: 32rpx;
    font-weight: bold;
  }
}

.cover-btn {
  background-color: var(--home-bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  border: 1.5rpx dashed var(--home-border);
}

.upload-icon {
  font-size: 64rpx;
  color: var(--home-tabbar-inactive);
}

.upload-text {
  font-size: var(--home-fs-card-title);
  color: var(--home-text2);
}

.upload-tip {
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
}

.cover-url-input {
  .item-input {
    width: 100%;
  }
}

.cover-preview-small {
  width: 100%;
  height: 360rpx;
  border-radius: var(--home-r-lg);
  overflow: hidden;
  margin-top: var(--home-spacing-inner);
  
  image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.switch-label {
  font-size: var(--home-fs-card-title);
  color: var(--home-text1);
}

.tip-text {
  margin-top: 10rpx;
  font-size: var(--home-fs-meta);
  color: var(--home-tabbar-inactive);
}

.tip-box {
  margin: 24rpx 32rpx;
  padding: 24rpx;
  background: rgba(15, 118, 110, 0.05);
  border-radius: var(--home-r-md);
  border-left: 5rpx solid var(--home-primary);
  display: flex;
  gap: 16rpx;
}

.tip-icon {
  font-size: 40rpx;
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
  color: var(--home-text1);
  margin-bottom: 8rpx;
}

.tip-box .tip-text {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
  line-height: 1.6;
  margin-top: 0;
}

.bottom-placeholder {
  height: 120rpx;
}

.page-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background-color: var(--home-card);
  border-top: 1.5rpx solid rgba(17, 24, 39, 0.06);
  z-index: 100;
}

.footer-buttons {
  display: flex;
  gap: 24rpx;
}

.cancel-btn,
.save-btn {
  flex: 1;
  height: 88rpx;
  border-radius: var(--home-r-pill);
  font-size: var(--home-fs-section);
  font-weight: 500;
  border: none;
  transition: opacity 0.2s ease;
  
  &::after {
    border: none;
  }
}

.cancel-btn {
  background-color: var(--home-bg);
  color: var(--home-text2);
  border: 1.5rpx solid var(--home-border);
}

.save-btn {
  color: #ffffff;
  background-color: var(--home-primary);
  
  &.disabled {
    opacity: 0.5;
  }
  
  &:active:not(.disabled) {
    opacity: 0.88;
  }
}

/* 删除简介 Tab */
.delete-tab-section {
  margin-top: 16rpx;
  padding-top: 24rpx;
  border-top: 1.5rpx solid var(--home-border);
}

.delete-tab-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  height: 80rpx;
  background-color: rgba(220, 38, 38, 0.06);
  border: 1.5rpx solid rgba(220, 38, 38, 0.2);
  border-radius: var(--home-r-md);
  color: var(--color-danger);
  font-size: var(--home-fs-card-title);
  font-weight: 500;

  &:active {
    background-color: rgba(220, 38, 38, 0.12);
  }
}

.delete-icon {
  font-size: 32rpx;
}

/* 直播分类多选卡片（与创建页一致） */
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

.multi-card-icon {
  font-size: 40rpx;
  min-width: 72rpx;
  min-height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

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
}

.item-count {
  font-size: var(--home-fs-meta);
  color: var(--home-text2);
}

/* 场次标签（A1，复用创建页风格） */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

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

</style>
