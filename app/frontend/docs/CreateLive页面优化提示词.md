# 创建直播功能优化提示词（uni-app移动端 + 双写兼容方案）

## 角色与目标

你是一名资深前端重构工程师，精通 **uni-app + Vue 3 Composition API + TypeScript**，对移动端开发和业务逻辑有深刻理解。

你的核心任务是**"功能优化与重构"**，即根据三个设计文档（图片上传规范、直播简介统一方案、开始时间与回放方案）和项目现状分析，对两个创建直播页面进行安全、可控的优化改造。

**重要原则**：
- ✅ 保留现有业务逻辑，仅优化UI和数据流
- ✅ 采用"渐进式迁移 + 双写兼容"策略
- ✅ 确保向后兼容，旧数据可正常读取
- ✅ 错误隔离，非关键步骤失败不阻断流程

---

## 📋 改造范围说明

### 需要优化的页面

| 页面 | 文件路径 | 触发方式 | UI形式 | 代码相似度 |
|------|---------|---------|--------|-----------|
| **全屏创建页** | `src/pages/app/live-manage/create.vue` | 我的→直播管理→创建直播 | 全屏页面 | 95% |
| **抽屉创建页** | `src/components/app/CreateLiveDrawer.vue` | Tabbar加号 | 抽屉弹窗 | 95% |

**共同点**：
- ✅ 表单字段完全相同
- ✅ 验证逻辑相同
- ✅ 创建流程几乎相同
- ✅ API调用方式相同

**差异点**：
- ⚠️ 专家/品牌选择UI不同（弹窗 vs ActionSheet）
- ⚠️ 成功后跳转不同（navigateBack vs navigateTo）

---

## 📚 设计文档依据

### 文档1：图片上传与显示规范

**核心要求**：
- 统一使用 `uni.uploadFile` API
- 文件验证：类型（jpg/jpeg/png/gif）+ 大小（≤5MB）+ blob URL兼容
- 后端返回相对路径，前端转换为完整URL
- Tab图片上传使用专用接口 `POST /admin/rooms/{room_id}/tabs/image`

### 文档2：直播简介与图文混合-统一方案

**核心要求**：
- ✅ 直播简介改为**非必填**
- ✅ 直播简介采用**固定Tab存储**（`tab_key='intro'`）
- ✅ 创建房间后**始终创建"直播介绍"Tab**
- ✅ 简介图片改为**单图** + **本地/URL双模式**
- ✅ 支持类型：`text`（纯文本）或 `mixed`（图文混合）

### 文档3：直播间开始时间与回放-完整实施方案

**核心要求**：
- ✅ 开始时间归属Session，不再写入Room
- ✅ 回放地址不受状态约束，任意状态可修改
- ✅ 有回放地址时显示"创建为"选项：**直播中**（live）/ **回放**（finished）
- ✅ 无回放地址时默认创建为 `scheduled`

---

## 🔍 项目现状分析（基于深度检查）

### 一、API层现状 ✅ 完全安全

| API模块 | 文件 | 状态 | 关键发现 |
|---------|------|------|---------|
| **Room API** | `src/api/room.ts` | ✅ 完整 | 支持description字段读写 |
| **Session API** | `src/api/session.ts` | ✅ 完整 | 支持description字段读写 |
| **Tab API** | `src/api/tab.ts` | ✅ 完整 | 完整实现CRUD + 图片上传 |

**结论**：API层完全支持双写策略，无需修改。

### 二、Store层现状 ✅ 无冲突

**RoomStore**：
- ✅ `addNewRoom(payload)` - 支持description字段
- ✅ 返回room_id供后续使用
- ✅ 已有防重复提交机制

**SessionStore**：
- ✅ `createSession(roomId, payload)` - 支持description字段
- ✅ `importSession(roomId, payload)` - 支持status字段
- ⚠️ **发现问题**：`SessionImportPayload.status`类型定义只允许`'finished'`

**结论**：Store层无冲突，但需修复类型定义。

### 三、类型定义现状 🔧 需要修复

**Tab类型** ✅ 完整：
```typescript
export interface TabCreatePayload {
  tab_key: string;
  title: string;
  content_type: 'text' | 'image' | 'mixed';
  text_content?: string | null;
  image_url?: string | null;
  sort_order?: number;
  is_active?: boolean;
}
```

**Session类型** 🚨 需修复：
```typescript
// 当前定义（错误）
export interface SessionImportPayload {
  status: 'finished';  // ❌ 只允许finished
}

// 需要修改为
export interface SessionImportPayload {
  status: 'finished' | 'ready' | 'live';  // ✅ 支持文档要求
}
```

### 四、潜在冲突点 ⚠️ 已识别

| 冲突ID | 问题描述 | 影响 | 应对措施 |
|--------|---------|------|---------|
| **C1** | SessionImportPayload类型限制 | 无法创建live状态回放 | 修改类型定义 |
| **D1** | Tab创建可能在Room未持久化时执行 | Tab创建可能失败 | 错误隔离 + 不阻断流程 |
| **B1** | 旧直播间没有Tab | LiveView降级读description | 双写策略保障 |

---

## 🎯 核心改造策略

### 策略概述：渐进式迁移 + 双写兼容

```
┌─────────────────────────────────────────────────────────┐
│                    创建直播流程（优化后）                 │
├─────────────────────────────────────────────────────────┤
│ 1. 创建Room (description: 用户输入或空)  ← 双写兼容     │
│    ↓                                                     │
│ 2. 上传封面 (可选，失败不阻断)                          │
│    ↓                                                     │
│ 3. 创建"直播介绍"Tab (始终创建，失败不阻断) ← 新增      │
│    ├─ 有图片：先上传图片 → 创建Tab                      │
│    └─ 无图片：直接创建Tab (image_url='')                │
│    ↓                                                     │
│ 4. 创建Session (description: 空字符串)                  │
│    ├─ 无回放：createSession                             │
│    └─ 有回放：importSession (status: live/finished)     │
│    ↓                                                     │
│ 5. 关联专家 (可选，失败不阻断)                          │
│    ↓                                                     │
│ 6. 关联品牌 (可选，失败不阻断)                          │
│    ↓                                                     │
│ 7. 设置回放地址 (仅createSession时，失败不阻断)         │
└─────────────────────────────────────────────────────────┘
```

### 数据流设计

**新数据**：
- Room.description：用户输入（双写）
- Tab（tab_key='intro'）：存储直播简介 + 图片
- Session.description：空字符串

**旧数据**：
- LiveView优先读取Tab
- 无Tab时降级读取Room.description

---

## 📝 详细实施步骤

### 步骤1：修复类型定义 🔴 P0（必须）

**文件**：`src/types/session.ts`

**修改内容**：
```typescript
// 修改前
export interface SessionImportPayload {
  title?: string;
  description?: string;
  start_time: string;
  playback_url: string;
  status: 'finished';  // ❌ 只允许finished
}

// 修改后
export interface SessionImportPayload {
  title?: string;
  description?: string;
  start_time: string;
  playback_url: string;
  status: 'finished' | 'ready' | 'live';  // ✅ 支持文档要求的状态
}
```

**理由**：文档明确要求支持创建`status='live'`的回放场次。

---

### 步骤2：全屏创建页改造 🔴 P0

**文件**：`src/pages/app/live-manage/create.vue`

#### 2.1 修改formData结构

```typescript
// 修改前
const formData = ref({
  title: '',
  description: '',
  description_images: [] as string[],  // ❌ 9张图片
  start_time: '',
  cover_url: '',
  cover_local_path: '',
  expert_id: '',
  brand_id: '',
  playback_url: '',
  status: 'scheduled' as SessionStatus
});

// 修改后
const formData = ref({
  title: '',
  description: '',  // ✅ 保留，用于双写
  intro_image_url: '',  // ✅ 新增：简介单图
  // description_images: [],  // ❌ 删除
  start_time: '',
  cover_url: '',
  cover_local_path: '',
  expert_id: '',
  brand_id: '',
  playback_url: '',
  status: 'live' as SessionStatus  // ✅ 默认改为'live'（有回放时）
});

// 新增：图片相关状态
const introImageMode = ref<'local' | 'url'>('local');
const introImageUrlInput = ref('');
const introImageLocalPath = ref('');
```

#### 2.2 修改UI：简介改为非必填

```vue
<!-- 修改前 -->
<view class="item-label">
  <text>直播简介</text>
  <text class="required">*</text>  <!-- ❌ 删除必填标记 -->
</view>

<!-- 修改后 -->
<view class="item-label">
  <text>直播简介</text>
  <!-- 无必填标记 -->
</view>
```

#### 2.3 修改UI：简介图片改为单图+双模式

```vue
<!-- 删除：9张图片网格 -->
<!-- <view class="desc-images-grid">...</view> -->

<!-- 新增：单图 + 双模式 -->
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
      📷 本地选择
    </view>
    <view 
      class="tab-item" 
      :class="{ 'active': introImageMode === 'url' }"
      @click="introImageMode = 'url'"
    >
      🔗 输入URL
    </view>
  </view>
  
  <!-- 本地选择模式 -->
  <view v-if="introImageMode === 'local'" class="intro-image-block">
    <view class="intro-image-upload" @click="handleUploadIntroImage">
      <image v-if="formData.intro_image_url" :src="formData.intro_image_url" mode="aspectFill" />
      <view v-else class="upload-placeholder">
        <text class="upload-icon">+</text>
        <text class="upload-text">添加图片</text>
      </view>
    </view>
    <!-- 更换图片按钮 -->
    <view v-if="formData.intro_image_url" class="image-actions">
      <text class="action-btn" @click="handleUploadIntroImage">
        📷 更换图片
      </text>
      <text class="action-btn delete" @click="clearIntroImage">
        🗑️ 删除图片
      </text>
    </view>
  </view>
  
  <!-- URL模式 -->
  <view v-if="introImageMode === 'url'">
    <input 
      class="item-input"
      v-model="introImageUrlInput"
      placeholder="请输入图片URL"
      @blur="handleIntroImageUrlChange"
    />
    <view v-if="introImageUrlInput" class="intro-image-preview">
      <image :src="introImageUrlInput" mode="aspectFill" @error="handleIntroImageUrlError" />
    </view>
  </view>
</view>
```

#### 2.4 修改UI：状态选择器优化

```vue
<!-- 修改前：状态选择器始终显示 -->
<!-- <view class="form-item">
  <view class="item-label">
    <text>直播状态</text>
  </view>
  <picker ...>
    ...
  </picker>
</view> -->

<!-- 修改后：根据回放地址动态显示 -->
<view v-if="formData.playback_url" class="form-item">
  <view class="item-label">
    <text>创建为</text>
  </view>
  <picker 
    mode="selector"
    :value="createModeIndex"
    :range="createModeOptions"
    range-key="label"
    @change="handleCreateModeChange"
  >
    <view class="item-picker">
      <text>{{ createModeOptions[createModeIndex].label }}</text>
      <text class="picker-arrow">›</text>
    </view>
  </picker>
  <view class="tip-text">{{ createModeOptions[createModeIndex].tip }}</view>
</view>
```

#### 2.5 新增逻辑：图片上传处理

```typescript
// 上传简介图片
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

// 处理URL输入
const handleIntroImageUrlChange = () => {
  if (introImageUrlInput.value) {
    formData.value.intro_image_url = introImageUrlInput.value;
    introImageLocalPath.value = '';
  }
};

// 清空图片
const clearIntroImage = () => {
  formData.value.intro_image_url = '';
  introImageLocalPath.value = '';
  introImageUrlInput.value = '';
};

// 处理URL加载错误
const handleIntroImageUrlError = () => {
  uni.showToast({ title: '图片URL无效或无法加载', icon: 'none' });
};
```

#### 2.6 新增逻辑：状态选择器

```typescript
// 修改状态选项
const createModeOptions = [
  { value: 'live', label: '直播中', tip: '用户进入直播间会播放回放地址的视频' },
  { value: 'finished', label: '回放', tip: '用户进入直播间会播放回放视频' }
];
const createModeIndex = ref(1);  // 默认选择"回放"

const handleCreateModeChange = (e: any) => {
  createModeIndex.value = e.detail.value;
  formData.value.status = createModeOptions[createModeIndex.value].value as SessionStatus;
};

// 监听回放地址变化
watch(() => formData.value.playback_url, (newVal) => {
  if (!newVal) {
    // 清空回放地址时，重置为scheduled
    formData.value.status = 'scheduled';
  } else {
    // 有回放地址时，默认为finished
    formData.value.status = createModeOptions[createModeIndex.value].value as SessionStatus;
  }
});
```

#### 2.7 核心改造：创建流程

```typescript
/**
 * 创建"直播介绍"Tab
 * @param roomId 房间ID
 * @returns Promise<void>
 */
const createIntroTab = async (roomId: string): Promise<void> => {
  try {
    console.log('📝 [创建直播] 步骤1.6: 创建直播介绍Tab');
    
    // 1. 确定内容类型
    const hasImage = !!formData.value.intro_image_url;
    const hasText = !!formData.value.description.trim();
    let contentType: 'text' | 'mixed' = 'text';
    
    if (hasImage && hasText) {
      contentType = 'mixed';
    } else if (hasImage) {
      contentType = 'mixed';  // 纯图片也用mixed
    }
    
    // 2. 如果是本地图片，先上传
    let finalImageUrl = '';
    if (introImageLocalPath.value) {
      console.log('📤 [创建直播] 上传简介图片...');
      try {
        finalImageUrl = await uploadTabImage(roomId, introImageLocalPath.value);
        console.log('✅ [创建直播] 简介图片上传成功:', finalImageUrl);
      } catch (uploadError) {
        console.error('⚠️ [创建直播] 简介图片上传失败:', uploadError);
        // 图片上传失败，继续创建Tab但不带图片
        finalImageUrl = '';
      }
    } else if (formData.value.intro_image_url) {
      // URL模式，直接使用
      finalImageUrl = formData.value.intro_image_url;
    }
    
    // 3. 创建Tab（始终创建，即使内容为空）
    await createRoomTab(roomId, {
      tab_key: 'intro',
      title: '直播介绍',
      content_type: contentType,
      text_content: formData.value.description.trim() || '',  // 空字符串也可以
      image_url: finalImageUrl || '',  // 空字符串也可以
      sort_order: 1,
      is_active: true
    });
    
    console.log('✅ [创建直播] 直播介绍Tab创建成功');
  } catch (error) {
    console.error('⚠️ [创建直播] 直播介绍Tab创建失败:', error);
    // ⚠️ 不抛出错误，不阻断流程
    // Tab创建失败不影响Room和Session的创建
  }
};

/**
 * 上传Tab图片
 * @param roomId 房间ID
 * @param filePath 本地文件路径
 */
const uploadTabImage = async (roomId: string, filePath: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    const baseURL = import.meta.env.VITE_BASE_API_URL || 'https://mp.dayilive.com/api/core';
    
    uni.uploadFile({
      url: `${baseURL}/admin/rooms/${roomId}/tabs/image`,
      filePath: filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${authStore.token}`
      },
      success: (uploadRes) => {
        if (uploadRes.statusCode === 200) {
          try {
            const data = JSON.parse(uploadRes.data);
            if (data.code === 200 && data.data && data.data.image_url) {
              resolve(data.data.image_url);
            } else {
              reject(new Error(data.message || '上传失败'));
            }
          } catch (error) {
            reject(new Error('解析响应失败'));
          }
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
 * 创建直播（主流程）
 */
const handleCreate = async () => {
  if (!validateForm()) return;
  
  isSubmitting.value = true;
  
  try {
    console.log('🎬 [创建直播] ========== 开始创建流程 ==========');
    
    // 步骤1：创建Room（双写description）
    console.log('🏠 [创建直播] 步骤1: 创建Room');
    const roomResult = await roomStore.addNewRoom({
      title: formData.value.title.trim(),
      description: formData.value.description.trim() || ''  // ✅ 双写，空字符串也传
    });
    
    if (!roomResult.success) {
      throw new Error(roomResult.message || '创建直播间失败');
    }
    const roomId = roomResult.room_id!;
    console.log('✅ [创建直播] Room创建成功, room_id:', roomId);
    
    // 步骤1.5：上传封面（现有逻辑，失败不阻断）
    if (formData.value.cover_url) {
      try {
        if (formData.value.cover_local_path) {
          await uploadRoomCover(roomId, formData.value.cover_local_path);
        } else {
          await updateRoom(roomId, { cover_url: formData.value.cover_url });
        }
        console.log('✅ [创建直播] 封面设置成功');
      } catch (coverError) {
        console.error('⚠️ [创建直播] 封面设置失败:', coverError);
        // 不阻断流程
      }
    }
    
    // 步骤1.6：创建"直播介绍"Tab（新增，失败不阻断）
    await createIntroTab(roomId);
    
    // 步骤2：创建Session
    console.log('📅 [创建直播] 步骤2: 创建Session');
    let sessionResult;
    
    if (formData.value.playback_url) {
      // 有回放地址，使用importSession
      sessionResult = await sessionStore.importSession(roomId, {
        title: formData.value.title.trim(),
        description: '',  // ✅ 不再写入session.description
        start_time: formData.value.start_time,
        playback_url: formData.value.playback_url,
        status: formData.value.status  // ✅ 'live' 或 'finished'
      });
    } else {
      // 无回放地址，使用createSession
      sessionResult = await sessionStore.createSession(roomId, {
        title: formData.value.title.trim(),
        description: '',  // ✅ 不再写入session.description
        start_time: formData.value.start_time
      });
    }
    
    if (!sessionResult.success) {
      throw new Error(sessionResult.message || 'Session创建失败');
    }
    console.log('✅ [创建直播] Session创建成功');
    
    // 步骤3-7：专家、品牌、回放（现有逻辑，保持不变）
    // ... 保持现有代码 ...
    
    console.log('🎉 [创建直播] ========== 创建流程完成 ==========');
    
    uni.showToast({ title: '创建成功', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 500);
    
  } catch (error: any) {
    console.error('❌ [创建直播] 创建失败:', error);
    uni.showToast({
      title: error.message || '创建失败，请重试',
      icon: 'none',
      duration: 2000
    });
  } finally {
    isSubmitting.value = false;
  }
};
```

#### 2.8 修改验证逻辑

```typescript
const validateForm = (): boolean => {
  let isValid = true;
  errors.value.title = '';
  // errors.value.description = '';  // ❌ 删除简介必填验证
  errors.value.start_time = '';
  
  if (!formData.value.title.trim()) {
    errors.value.title = '请输入直播标题';
    isValid = false;
  }
  
  // ❌ 删除简介必填验证
  // if (!formData.value.description.trim()) {
  //   errors.value.description = '请输入直播简介';
  //   isValid = false;
  // }
  
  if (!formData.value.start_time) {
    errors.value.start_time = '请选择开始时间';
    isValid = false;
  }
  
  return isValid;
};

const canSubmit = computed(() => {
  return formData.value.title.trim() && 
         // formData.value.description.trim() && // ❌ 删除
         formData.value.start_time && 
         !isSubmitting.value;
});
```

#### 2.9 添加样式

```scss
/* 图片模式切换 */
.image-mode-tabs {
  display: flex;
  gap: 16rpx;
  margin-bottom: 16rpx;
  
  .tab-item {
    flex: 1;
    padding: 16rpx;
    text-align: center;
    background-color: #f7f8fa;
    border-radius: 8rpx;
    font-size: 26rpx;
    color: #666666;
    transition: all 0.3s;
    
    &.active {
      background-color: #1890ff;
      color: #ffffff;
    }
  }
}

/* 简介图片区域 */
.intro-image-block {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.intro-image-upload {
  width: 100%;
  height: 360rpx;
  border-radius: 12rpx;
  overflow: hidden;
  background-color: #f8f8f8;
  
  image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .upload-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16rpx;
    
    .upload-icon {
      font-size: 64rpx;
      color: #999999;
    }
    
    .upload-text {
      font-size: 28rpx;
      color: #666666;
    }
  }
}

/* 图片操作按钮 */
.image-actions {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 8rpx 0;
}

.action-btn {
  font-size: 26rpx;
  color: #1890ff;
  
  &.delete {
    color: #ff4d4f;
  }
}

/* URL模式预览 */
.intro-image-preview {
  width: 100%;
  height: 360rpx;
  border-radius: 12rpx;
  overflow: hidden;
  margin-top: 16rpx;
  
  image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
```

---

### 步骤3：抽屉创建页改造 🔴 P0

**文件**：`src/components/app/CreateLiveDrawer.vue`

**改造内容**：与全屏创建页完全相同，只需复制以下内容：
1. formData结构修改
2. UI模板修改（简介非必填、单图+双模式、状态选择器）
3. 逻辑函数（图片上传、Tab创建、验证逻辑）
4. 样式添加

**差异处理**：
- 保持专家/品牌选择的ActionSheet方式
- 保持成功后的跳转逻辑（navigateTo）

---

## 🔒 安全保障措施

### 措施1：错误隔离 ✅

```typescript
// 每个非关键步骤都用try-catch包裹
try {
  await uploadCover();
} catch (error) {
  console.error('封面上传失败:', error);
  // 不阻断流程
}

try {
  await createIntroTab();
} catch (error) {
  console.error('Tab创建失败:', error);
  // 不阻断流程
}
```

### 措施2：防重复提交 ✅

```typescript
// Store已有防护
if (this.loading) {
  return { success: false, message: '正在处理中' };
}

// 组件层额外防护
const isSubmitting = ref(false);

const handleCreate = async () => {
  if (isSubmitting.value) {
    uni.showToast({ title: '正在创建中，请稍候', icon: 'none' });
    return;
  }
  isSubmitting.value = true;
  try {
    // ...
  } finally {
    isSubmitting.value = false;
  }
};
```

### 措施3：详细日志记录 ✅

```typescript
console.log('🎬 [创建直播] ========== 开始创建流程 ==========');
console.log('📋 [创建直播] 表单数据:', formData.value);
console.log('🏠 [创建直播] 步骤1: 创建Room');
console.log('✅ [创建直播] Room创建成功, room_id:', roomId);
console.log('⚠️ [创建直播] 封面设置失败:', error);
console.log('🎉 [创建直播] ========== 创建流程完成 ==========');
```

### 措施4：数据验证 ✅

```typescript
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
    // ...
  }
});
```

---

## 📊 风险评估与应对

| 风险类别 | 风险点 | 概率 | 影响 | 应对措施 | 状态 |
|---------|--------|------|------|---------|------|
| **类型冲突** | SessionImportPayload.status限制 | 高 | 高 | 修改类型定义 | ✅ 已规划 |
| **数据一致性** | Tab创建失败但Room已创建 | 中 | 低 | 错误隔离 + 降级读取 | ✅ 已规划 |
| **并发安全** | 重复点击创建按钮 | 中 | 中 | Store防护 + 组件防护 | ✅ 已实现 |
| **向后兼容** | 旧数据没有Tab | 低 | 中 | LiveView降级逻辑 | ✅ 已实现 |
| **图片上传** | 上传失败导致流程中断 | 中 | 低 | 错误隔离 | ✅ 已规划 |
| **网络异常** | API调用失败 | 中 | 高 | try-catch + 错误提示 | ✅ 已规划 |

**总体风险评级：🟢 低风险**

---

## ✅ 实施检查清单

### P0级任务（必须完成）

- [x] **类型定义修复**：`src/types/session.ts` - 修复SessionImportPayload.status ✅ **已完成**
- [ ] **全屏创建页**：`src/pages/app/live-manage/create.vue` - 完整改造
- [ ] **抽屉创建页**：`src/components/app/CreateLiveDrawer.vue` - 完整改造

### 详细检查项

#### 一、类型定义
- [x] SessionImportPayload.status支持'live' ✅ **已完成**
- [x] 类型定义与文档要求一致 ✅ **已完成**

#### 二、UI改造
- [ ] 简介字段移除必填标记
- [ ] 简介图片改为单图
- [ ] 添加图片模式切换（本地/URL）
- [ ] 添加"更换图片"按钮
- [ ] 添加"删除图片"按钮
- [ ] 状态选择器根据回放地址动态显示
- [ ] 状态选项改为"直播中/回放"

#### 三、逻辑改造
- [ ] formData结构调整
- [ ] 图片上传逻辑实现
- [ ] Tab创建逻辑实现
- [ ] 验证逻辑修改（简介非必填）
- [ ] 创建流程调整（添加Tab创建步骤）
- [ ] 错误隔离机制实现

#### 四、样式添加
- [ ] 图片模式切换样式
- [ ] 简介图片区域样式
- [ ] 图片操作按钮样式
- [ ] URL预览样式

#### 五、安全保障
- [ ] 错误隔离机制
- [ ] 防重复提交
- [ ] 详细日志记录
- [ ] 数据验证

#### 六、测试验证
- [ ] 仅填标题和开始时间可创建
- [ ] 简介图片本地上传成功
- [ ] 简介图片URL模式成功
- [ ] 更换图片功能正常
- [ ] 删除图片功能正常
- [ ] 有回放地址显示状态选择器
- [ ] 无回放地址不显示状态选择器
- [ ] 创建为"直播中"成功
- [ ] 创建为"回放"成功
- [ ] Tab创建成功
- [ ] Tab图片上传成功
- [ ] 图片大小超限提示
- [ ] 图片格式错误提示
- [ ] 旧数据可正常读取

#### 七、降级场景测试（重要）

**Tab创建失败降级测试**：
- [ ] 模拟Tab创建失败（网络断开）
- [ ] 验证Room和Session仍创建成功
- [ ] 验证LiveView可降级读取room.description
- [ ] 验证用户收到友好提示
- [ ] 验证日志正确记录错误

**测试步骤**：
```typescript
// 1. 在createIntroTab函数中模拟失败
const createIntroTab = async (roomId: string): Promise<void> => {
  try {
    // 模拟失败：throw new Error('模拟Tab创建失败');
    await createRoomTab(roomId, {...});
  } catch (error) {
    console.error('⚠️ Tab创建失败:', error);
    // 不阻断流程
  }
};

// 2. 验证创建流程继续
// 3. 检查LiveView降级逻辑
```

**图片上传失败降级测试**：
- [ ] 模拟图片上传失败（文件过大）
- [ ] 验证Tab仍创建成功（无图片）
- [ ] 验证用户收到明确提示
- [ ] 验证可以后续补传图片

#### 八、监控指标建议

**图片上传成功率监控**：
```typescript
// 在uploadTabImage函数中添加监控
const uploadTabImage = async (roomId: string, filePath: string): Promise<string> => {
  const startTime = Date.now();
  try {
    const result = await uni.uploadFile({...});
    
    // 成功监控
    console.log('[监控] 图片上传成功', {
      roomId,
      duration: Date.now() - startTime,
      fileSize: fileInfo.size
    });
    
    return result;
  } catch (error) {
    // 失败监控
    console.error('[监控] 图片上传失败', {
      roomId,
      duration: Date.now() - startTime,
      error: error.message
    });
    throw error;
  }
};
```

**关键监控指标**：
- 图片上传成功率（目标：>95%）
- 图片上传平均耗时（目标：<3秒）
- Tab创建成功率（目标：>98%）
- 整体创建成功率（目标：>96%）

**监控数据收集**：
```typescript
// 建议在生产环境添加埋点
interface CreateLiveMetrics {
  room_created: boolean;
  tab_created: boolean;
  image_uploaded: boolean;
  session_created: boolean;
  total_duration: number;
  errors: string[];
}

// 创建完成后上报
reportMetrics(metrics);
```

---

## 🎯 预期效果

### 功能完整性
- ✅ 直播简介改为非必填
- ✅ 直播简介采用固定Tab存储
- ✅ 创建房间后始终创建"直播介绍"Tab
- ✅ 简介图片改为单图 + 本地/URL双模式
- ✅ 回放地址与状态联动优化
- ✅ 图片上传规范统一
- ✅ 符合《图片上传与显示规范》
- ✅ 符合《直播简介与图文混合-统一方案》
- ✅ 符合《直播间开始时间与回放-完整实施方案》

### 向后兼容性
- ✅ 旧数据可以正常读取
- ✅ 不影响现有功能
- ✅ 渐进式迁移

### 安全性
- ✅ 错误隔离，非关键步骤失败不阻断
- ✅ 防重复提交
- ✅ 详细日志记录
- ✅ 数据验证完善

---

## 📚 参考文档

1. **图片上传与显示规范**：`docs/图片上传与显示规范.md`
2. **直播简介与图文混合-统一方案**：`docs/直播简介与图文混合-统一方案.md`
3. **直播间开始时间与回放-完整实施方案**：`docs/直播间开始时间与回放-完整实施方案.md`
4. **MultiVenueManage提示词**：`docs/MultiVenueManage页面代码生成提示词.md`
5. **TopicCreate提示词**：`docs/TopicCreate页面代码生成提示词.md`
6. **LiveView提示词**：`docs/LiveView页面代码生成提示词-V2.md`

---

## 🚀 开始实施

请按照以上详细步骤，逐步实施创建直播功能的优化改造。

**实施顺序建议**：
1. 修复类型定义（5分钟）
2. 改造全屏创建页（2-3小时）
3. 改造抽屉创建页（1-2小时）
4. 全面测试验证（1-2小时）

**预计总工时**：4-7小时

**注意事项**：
- ⚠️ 每完成一个步骤，立即测试验证
- ⚠️ 遇到问题及时记录和反馈
- ⚠️ 保持代码风格与现有项目一致
- ⚠️ 详细的日志记录便于调试

---

**祝实施顺利！如有问题，请随时反馈。** 🎉
