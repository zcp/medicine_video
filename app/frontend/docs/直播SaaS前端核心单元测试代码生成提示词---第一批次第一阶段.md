
# 直播SaaS前端核心单元测试代码生成提示词---第一批次第一阶段

---

## 1. 角色定义 (Role Definition)

你是一名资深前端工程师，精通 Vue3、TypeScript、Pinia、uni-app 生态，擅长自动化测试。你将为 frontend_live/src/ 下的核心业务单元编写高质量、可维护的自动化测试代码，采用 Vitest + @vue/test-utils + TypeScript，所有测试严格遵循 AAA（Arrange-Act-Assert）模式，保证每个测试用例独立、隔离。

---

## 2. 任务目标 (Task Objective)

你的目标是为以下目录下的所有核心单元生成完整的测试代码：
- `src/components/` 下所有核心组件
- `src/utils/` 下所有工具函数
- `src/store/` 下所有 Pinia store
- `src/api/` 下所有 API 封装

每个测试文件需覆盖主要功能、边界条件、异常分支，所有测试用例需独立、mock 所有外部依赖。

---

## 3. 核心上下文信息 (Core Context Information)

### 3.1. Testing Strategy
- **组件**：测试渲染、props、事件、交互、slot、边界条件
- **工具函数**：测试输入输出、异常、边界
- **Pinia store**：测试 state、action、getter、模块间交互
- **API 封装**：测试参数、返回、异常，所有网络请求需 mock
- 所有测试用例必须严格遵循 AAA（Arrange-Act-Assert）三段式结构
- 每个测试用例必须独立，不能依赖其它测试副作用
- 所有 mock、全局变量、定时器等必须在每个测试后清理，保证隔离

### 3.2. Testing Environment Setup
- 使用 Vitest 作为测试运行器，@vue/test-utils 进行组件挂载，Pinia 进行 store 测试
- 所有 API 请求需用 vi.mock/vi.fn mock 掉真实网络请求
- 测试文件命名为 xxx.spec.ts，与被测文件同名，存放于 tests/ 目录下

### 3.3. Project Structure
```
frontend_live/
├── src/
│   ├── components/
│   │   ├── AppButton.vue
│   │   ├── ModalDialog.vue
│   │   ├── RoomCard.vue
│   │   └── VideoPlayer.vue
│   ├── utils/
│   │   └── request.ts
│   ├── store/
│   │   ├── room.ts
│   │   └── session.ts
│   └── api/
│       ├── room.ts
│       └── session.ts
└── tests/  # 测试文件存放目录
```
**已存在的代码全文 (Full Text of Existing Code)**
*You must generate tests based on the logic within the following application code.*

* **已存在的代码**:
    * `/src/components/AppButton.py`
    * `/src/components/ModalDialog.py`
    * `/src/components/RoomCard.py`
    * `/src/components/VideoPlayer.py` 
    * `/src/utils/request.py`
    * `/src/store/room.py`
    * `/src/store/session.py` 
    * `/src/api/room.py`
    * `/src/api/session.py`    
  
### 3.4. 参考代码示例 (Reference Code Samples)
**/src/components/AppButton.py**
```python
<template>
  <button
    class="app-button"
    :class="[
      `app-button--${type}`,
      `app-button--${size}`,
      { 'is-disabled': disabled, 'is-loading': loading }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <view v-if="loading" class="app-button__loading-indicator"></view>
    <view class="app-button__content">
      <slot />
    </view>
  </button>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default';
  size?: 'large' | 'medium' | 'small' | 'mini';
  loading?: boolean;
  disabled?: boolean;
}>(), {
  type: 'default',
  size: 'medium',
  loading: false,
  disabled: false,
});

const emit = defineEmits(['click']);

function handleClick(e: Event) {
  if (!props.disabled && !props.loading) {
    emit('click', e);
  }
}
</script>

<style scoped lang="scss">
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease-in-out;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-weight: 500;
  box-shadow: none;
  outline: none;
  position: relative;
  border-radius: 4px;
  min-width: 80px;
  white-space: nowrap;

  &:hover:not(.is-disabled):not(.is-loading) {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  &:active:not(.is-disabled):not(.is-loading) {
    transform: translateY(0);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  }

  &.is-disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
    box-shadow: none !important;
  }

  &.is-loading {
    opacity: 0.8;
    cursor: wait;
    transform: none !important;
    box-shadow: none !important;
  }

  /* 默认按钮 - 白色背景 */
  &--default {
    background-color: #ffffff;
    border-color: #dcdfe6;
    color: #606266;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #f5f7fa;
      border-color: #c2c7cc;
      color: #606266;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #e4e7ed;
      border-color: #b3b7bf;
      color: #606266;
    }
  }

  /* 主要按钮 - 蓝色背景 */
  &--primary {
    background-color: #409eff;
    border-color: #409eff;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #66b1ff;
      border-color: #66b1ff;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #3a8ee6;
      border-color: #3a8ee6;
      color: #ffffff;
    }
  }

  /* 成功按钮 - 绿色背景 */
  &--success {
    background-color:rgb(58, 153, 11);
    border-color: rgb(58, 153, 11);
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: rgb(58, 153, 11);
      border-color: rgb(58, 153, 11);
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #5daf34;
      border-color: #5daf34;
      color: #ffffff;
    }
  }

  /* 警告按钮 - 橙色背景 */
  &--warning {
    background-color: #e6a23c;
    border-color: #e6a23c;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #ebb563;
      border-color: #ebb563;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #cf9236;
      border-color: #cf9236;
      color: #ffffff;
    }
  }

  /* 危险按钮 - 红色背景 */
  &--danger {
    background-color: #f56c6c;
    border-color: #f56c6c;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #f78989;
      border-color: #f78989;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #dd6161;
      border-color: #dd6161;
      color: #ffffff;
    }
  }

  /* 信息按钮 - 灰色背景 */
  &--info {
    background-color: #909399;
    border-color: #909399;
    color: #ffffff;

    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: #a6a9ad;
      border-color: #a6a9ad;
      color: #ffffff;
    }

    &:active:not(.is-disabled):not(.is-loading) {
      background-color: #82848a;
      border-color: #82848a;
      color: #ffffff;
    }
  }

  /* 尺寸设计 */
  &--large {
    height: 40px;
    padding: 0 20px;
    font-size: 14px;
    border-radius: 4px;
  }

  &--medium {
    height: 32px;
    padding: 0 15px;
    font-size: 12px;
    border-radius: 4px;
  }

  &--small {
    height: 28px;
    padding: 0 12px;
    font-size: 12px;
    border-radius: 3px;
    min-width: 60px;
  }

  &--mini {
    height: 24px;
    padding: 0 8px;
    font-size: 11px;
    border-radius: 3px;
    min-width: 50px;
  }

  /* 加载指示器 */
  &__loading-indicator {
    width: 14px;
    height: 14px;
    margin-right: 6px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    opacity: 0.8;
  }

  /* 内容区域 */
  &__content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    line-height: 1;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
```

**/src/components/ModalDialog.py**     
```python
<template>
  <view v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <view class="modal-container" @click.stop>
      <!-- 模态框头部 -->
      <view class="modal-header">
        <view class="modal-title">
          <text class="modal-icon">📺</text>
          <text class="title-text">{{ title }}</text>
        </view>
        <text class="modal-close" @click="$emit('cancel')">×</text>
      </view>
      
      <!-- 分割线 -->
      <view class="modal-divider"></view>
      
      <!-- 模态框内容 -->
      <view class="modal-content">
        <slot></slot>
      </view>
      
      <!-- 模态框底部 -->
      <view class="modal-footer">
        <view class="button-group">
          <button 
            class="btn-cancel" 
            @click="$emit('cancel')"
            :disabled="confirmLoading"
          >
            取消
          </button>
          <button 
            class="btn-confirm" 
            @click="$emit('confirm')"
            :disabled="confirmLoading"
          >
            <text v-if="confirmLoading" class="loading-text">处理中...</text>
            <text v-else>{{ confirmText }}</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean;
  title?: string;
  confirmText?: string;
  confirmLoading?: boolean;
}>();

defineEmits<{
  'update:visible': [value: boolean];
  'confirm': [];
  'cancel': [];
}>();

const handleOverlayClick = () => {
  // 点击遮罩层关闭模态框
  // 这里可以根据需要决定是否允许点击遮罩关闭
};
</script>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-container {
  background: var(--color-background-light);
  border-radius: var(--radius-large);
  box-shadow: var(--shadow-large);
  min-width: 360px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  animation: modalSlideIn 0.3s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xlarge);
  border-bottom: 1px solid var(--color-border);
  
  .modal-title {
    display: flex;
    align-items: center;
    
    .modal-icon {
      font-size: 20px;
      margin-right: var(--spacing-medium);
    }
    
    .title-text {
      font-size: var(--font-size-large);
      font-weight: bold;
      color: var(--color-text-primary);
    }
  }
  
  .modal-close {
    font-size: 24px;
    color: var(--color-text-secondary);
    cursor: pointer;
    padding: var(--spacing-small);
    border-radius: var(--radius-base);
    transition: var(--transition-base);
    
    &:hover {
      color: var(--color-primary);
      background: var(--color-primary-light-1);
    }
  }
}

.modal-divider {
  height: 1px;
  background: var(--color-border);
  margin: 0 var(--spacing-xlarge);
}

.modal-content {
  padding: var(--spacing-xlarge);
  max-height: 60vh;
  overflow-y: auto;
}

.modal-footer {
  padding: var(--spacing-xlarge);
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
  
  .button-group {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-large);
    
    .btn-cancel {
      background: var(--color-background-light);
      color: var(--color-text-secondary);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-base);
      padding: 8px 24px;
      font-size: var(--font-size-medium);
      cursor: pointer;
      transition: var(--transition-base);
      
      &:hover:not(:disabled) {
        background: var(--color-border);
        color: var(--color-text-primary);
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }
    
    .btn-confirm {
      background: var(--color-primary);
      color: var(--color-text-on-primary);
      border: none;
      border-radius: var(--radius-base);
      padding: 8px 32px;
      font-size: var(--font-size-medium);
      font-weight: bold;
      cursor: pointer;
      transition: var(--transition-base);
      box-shadow: var(--shadow-base);
      
      &:hover:not(:disabled) {
        background: var(--color-primary-hover);
        box-shadow: var(--shadow-large);
      }
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      .loading-text {
        display: flex;
        align-items: center;
        justify-content: center;
        
        &::before {
          content: '';
          width: 12px;
          height: 12px;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-right: var(--spacing-small);
        }
      }
    }
  }
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-container {
    min-width: 90vw;
    margin: var(--spacing-large);
  }
  
  .modal-header,
  .modal-content,
  .modal-footer {
    padding: var(--spacing-large);
  }
  
  .button-group {
    flex-direction: column;
    
    .btn-cancel,
    .btn-confirm {
      width: 100%;
    }
  }
}
</style>

```
**/src/components/RoomCard.py**
```python
<template>
  <view class="room-card">
    <view class="card-main-content" @click="handleClick">
    <view class="cover-wrapper">
      <image 
        :src="room.cover_url" 
        class="cover-image" 
        mode="aspectFill"
        @error="handleImageError"
      />
      <view v-if="!imageLoaded" class="image-placeholder">
        <view class="placeholder-icon">📷</view>
        <text class="placeholder-text">暂无封面</text>
      </view>
      <view v-if="room.is_private" class="private-badge">
        <text>私密</text>
      </view>
      <!-- 新增：悬浮操作按钮 -->
      <view class="cover-actions">
        <slot name="actions"></slot>
      </view>
    </view>
    <view class="info-wrapper">
      <text class="title">{{ room.title }}</text>
        <text v-if="showDescription" class="description">{{ room.description || '暂无简介' }}</text>
      </view>
    </view>
    
    <!-- 新增：操作区域的插槽 -->
    <view class="actions-wrapper" v-if="$slots.actions">
      <slot name="actions"></slot>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Room } from '../types/room';

const props = withDefaults(defineProps<{
  room: Room;
  showDescription?: boolean;
}>(), {
  showDescription: true,
});

const emit = defineEmits<{
  (e: 'click'): void;
}>();

const imageLoaded = ref(false);

const handleImageError = () => {
  imageLoaded.value = false;
};

// 如果 props.room.cover_url 存在，则尝试加载图片
watch(() => props.room.cover_url, (newUrl) => {
  if (newUrl) {
    // uni-app 的 image 组件没有 onload 事件，这里用一个标志位模拟
    // 假设有 URL 就是能加载成功，如果失败会触发 @error
    imageLoaded.value = true; 
  } else {
    imageLoaded.value = false;
  }
}, { immediate: true });


const handleClick = () => {
  emit('click');
};
</script>

<style lang="scss" scoped>
.room-card {
  max-width: 340px;         // 限制最大宽度
  min-width: 260px;         // 限制最小宽度
  background-color: var(--color-background-light);
  border-radius: 16px; /* 加大圆角 */
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(74,144,226,0.10); /* 更柔和更明显的阴影 */
  transition: var(--transition-base);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border: none;
  margin-bottom: var(--spacing-xlarge); /* 卡片间距 */
  position: relative;
  min-width: 0;
  
  &:hover {
    border: 2px solid rgb(121, 175, 230);  
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 12px 32px rgba(74,144,226,0.16);
  }
}

.card-main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.cover-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  background-color: var(--color-background);
  border-bottom: 1px solid var(--color-border);
}

.cover-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 0;
}

.image-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: var(--color-text-secondary);
  background-color: #f0f4fa;
}

.placeholder-icon {
  font-size: 44px;
  opacity: 0.5;
}

.placeholder-text {
  margin-top: var(--spacing-small);
  font-size: var(--font-size-medium);
}

.private-badge {
  position: absolute;
  top: var(--spacing-medium);
  right: var(--spacing-medium);
  background-color: rgb(121, 175, 230);
  color: #fff;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: var(--font-size-small);
  font-weight: bold;
  letter-spacing: 1px;
}

.info-wrapper {
  padding: var(--spacing-medium) var(--spacing-medium) var(--spacing-medium) var(--spacing-medium);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-small);
}

.title {
  font-size: 20px;
  font-weight: 700;
  color: #222; /* 或 var(--color-text-primary) 确保不是白色 */
  margin-bottom: 2px;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.actions-wrapper {
  display: none;
}

.cover-actions {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  display: flex;
  gap: var(--spacing-medium);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
  z-index: 2;
}
.cover-wrapper:hover .cover-actions {
  opacity: 1;
  pointer-events: auto;
}
</style>
```
**/src/components/VideoPlayer.py**
```python
<template>
  <div class="video-player-container">
    <video
      ref="videoRef"
      class="video-js"
      controls
      muted
      playsinline
      style="width: 100%; height: 100%;"
    ></video>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
const props = defineProps({ src: String });
const videoRef = ref(null);
const isH5 = process.env.UNI_PLATFORM === 'h5';

onMounted(async () => {
  await nextTick();
  const el = document.querySelector('.video-js'); // 确保选择器正确
  console.log('el:', el); // 确认 el 是原生 HTMLVideoElement
  if (isH5 && el && props.src && props.src.endsWith('.m3u8')) {
    const Hls = (await import('hls.js')).default;
    if (Hls.isSupported()) {
      console.log("1")
      const hls = new Hls();
      hls.attachMedia(el);
      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(props.src.trim());
      });
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        el.play().catch(e => {
          console.warn('Autoplay was prevented:', e);
        });
      });
      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS.js error:', data);
      });
    } else if (el.canPlayType('application/vnd.apple.mpegurl')) {
      el.src = props.src.trim();
      el.play().catch(e => {
        console.warn('Autoplay was prevented:', e);
      });
    }
  }
});
</script>

<style scoped>
.video-player-container {
  width: 100%;
  height: 100%;
}
</style>

```
**/src/utils/request.py**
```python
/**
 * 统一网络请求工具
 * 封装uni.request，提供请求拦截器和响应拦截器
 */

import { ENV_CONFIG } from '../config/env';

// API基础URL，从环境配置中获取
const BASE_URL = ENV_CONFIG.FULL_API_BASE_URL;

// 获取认证Token的函数，后续会从状态管理中获取
const getAuthToken = (): string => {
  // 这里应该从本地存储或状态管理中获取token
  // 目前使用静态token作为示例
  // 使用一个更真实的token格式，避免403错误
  return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';
};

/**
 * 从 document.cookie 中读取csrftoken
 */
const getCsrfToken = (): string | null => {
  if (typeof document === 'undefined') {
    return null;
  }
  const csrfCookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : null;
};

/**
 * 请求配置接口
 */
interface RequestOptions {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'OPTIONS' | 'HEAD' | 'TRACE' | 'CONNECT' | 'PATCH';
  data?: any;
  header?: Record<string, string>;
  // 是否显示加载提示
  showLoading?: boolean;
  // 是否需要认证
  auth?: boolean;
}

/**
 * 统一请求函数
 * @param options 请求配置
 * @param retry 重试次数，默认3次
 * @param timeout 超时时间，默认5000ms
 * @returns Promise 返回请求结果
 */
export const request = <T = any>(options: RequestOptions, retry = 3, timeout = 5000): Promise<T> => {
  // 显示加载提示
  if (options.showLoading !== false) {
    uni.showLoading({
      title: '加载中...',
      mask: true
    });
  }

  // 构建完整URL
  const url = /^(http|https):\/\//.test(options.url) 
    ? options.url 
    : BASE_URL + options.url;

  // 强制生产环境下只能用 https
  if (
    process.env.NODE_ENV === 'production' &&
    !/^https:\/\//.test(url)
  ) {
    uni.hideLoading();
    throw new Error('安全限制：仅允许通过 HTTPS 协议请求 API！');
  }

  // 构建请求头
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.header,
  };

  // 如果需要认证，则添加Authorization头
  if (options.auth) {
    header['Authorization'] = `Bearer ${getAuthToken()}`;
  }

  // 添加CSRF Token
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    header['X-CSRFToken'] = csrfToken;
  }

  return new Promise<T>((resolve, reject) => {
    let isTimeout = false;
    const timer = setTimeout(() => {
      isTimeout = true;
      uni.hideLoading();
      reject(new Error('请求超时'));
    }, timeout);

    uni.request({
      url,
      method: options.method as any || 'GET',
      data: options.data,
      header,
      success: (res: any) => {
        clearTimeout(timer);
        if (isTimeout) return;
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T);
        } else if (res.statusCode === 401) {
          uni.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none',
            duration: 2000
          });
          reject(new Error('Unauthorized'));
        } else if (res.statusCode === 403) {
          uni.showToast({
            title: '您没有权限执行此操作',
            icon: 'none',
            duration: 2000
          });
          reject(new Error('Forbidden'));
        } else if (res.statusCode === 404) {
          uni.showToast({
            title: '请求的资源不存在',
            icon: 'none',
            duration: 2000
          });
          reject(new Error('Not Found'));
        } else {
          console.error(`HTTP Error: ${res.statusCode}`, res);
          const errorMessage = typeof res.data === 'string' ? res.data : `HTTP Error: ${res.statusCode}`;
          uni.showToast({
            title: `请求错误: ${res.statusCode}`,
            icon: 'none',
            duration: 2000
          });
          reject(new Error(errorMessage));
        }
      },
      fail: (err) => {
        clearTimeout(timer);
        if (isTimeout) return;
        if (retry > 0) {
          // 自动重试
          setTimeout(() => {
            request(options, retry - 1, timeout).then(resolve).catch(reject);
          }, 300);
        } else {
          console.error('Request Failed', err);
          uni.showToast({
            title: '网络请求失败，请检查网络连接',
            icon: 'none',
            duration: 2000
          });
          reject(err);
        }
      },
      complete: () => {
        clearTimeout(timer);
        if (options.showLoading !== false) {
          uni.hideLoading();
        }
      }
    });
  });
};

/**
 * 统一GET请求
 * @param url 请求地址
 * @param data 请求参数
 * @param options 其他选项
 * @returns Promise
 */
export const get = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'GET',
    data,
    ...options
  });
};

/**
 * 统一POST请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const post = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'POST',
    data,
    ...options
  });
};

/**
 * 统一PUT请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const put = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'PUT',
    data,
    ...options
  });
};

/**
 * 统一DELETE请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const del = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'DELETE',
    data,
    ...options
  });
};

/**
 * 统一PATCH请求
 * @param url 请求地址
 * @param data 请求数据
 * @param options 其他选项
 * @returns Promise
 */
export const patch = <T = any>(url: string, data?: any, options: Omit<RequestOptions, 'url' | 'method' | 'data'> = {}) => {
  return request<T>({
    url,
    method: 'PATCH',
    data,
    ...options
  });
}; 
```

**/src/store/room.py**
```python
import { defineStore } from 'pinia';
import type { Room, RoomCreatePayload } from '../types/room';
import { get, post, del, put, patch } from '../utils/request';
import { getSubVenues, createSubVenue, updateSubVenue, deleteSubVenue } from '../api/room';

export const useRoomStore = defineStore('room', {
  state: () => ({
    rooms: [] as Room[],
    currentRoom: null as Room | null,
    loading: false,
    error: null as Error | null,
    pagination: {
      page: 1,
      size: 10,
      hasMore: true,
      total: 0, // 新增总页数
    },
    // 分会场相关状态
    subVenues: [] as Room[],
    subVenuesLoading: false,
    subVenuesError: null as Error | null,
  }),
  actions: {
    async fetchRooms(options: { refresh?: boolean, page?: number } = {}) {
      if (this.loading && !options.refresh) return;
      this.loading = true;
      this.error = null;

      if (options.refresh) {
        // 支持外部指定页码跳转
        if (typeof options.page === 'number' && options.page > 0) {
          this.pagination.page = options.page;
        } else {
          this.pagination.page = 1;
        }
        this.rooms = [];//清空当前的房间列表
      }

      try {
        // 后端返回的数据结构是 { code, message, data: { items, total, ... } }
        const response: any = await get('/rooms', {
          page: this.pagination.page,
          size: this.pagination.size,
        });
        // --- DEBUG: 打印后端返回的原始数据 ---
        console.log('DEBUG: API response in fetchRooms:', JSON.stringify(response, null, 2));

        if (response && response.code === 200 && response.data) {
          const newRooms = response.data.items || [];
          if (options.refresh) {
            this.rooms = newRooms;
          } else {
            this.rooms.push(...newRooms);
          }
          // 记录总数
          if (typeof response.data.total === 'number') {
            this.pagination.total = response.data.total;
          }
          this.pagination.page++;
          this.pagination.hasMore = newRooms.length === this.pagination.size;
        } else {
          throw new Error(response.message || 'Failed to fetch rooms');
        }

      } catch (err: any) {
        this.error = err;
        console.error("Failed to fetch rooms:", err);
      } finally {
        this.loading = false;
      }
    },
    async fetchRoomById(roomId: string) {
      this.loading = true;
      this.error = null;
      this.currentRoom = null;

      try {
        const response: any = await get(`/rooms/${roomId}`);
        if (response && response.code === 200 && response.data) {
          this.currentRoom = response.data;
        } else {
          throw new Error(response.message || 'Failed to fetch room details');
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to fetch room ${roomId}:`, err);
      } finally {
        this.loading = false;
      }
    },
    async addNewRoom(payload: RoomCreatePayload): Promise<boolean> {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await post('/rooms', payload);

        if (response && response.code === 200) {
          // 创建成功后，最好的做法是刷新整个列表，以获取最准确的数据
          await this.fetchRooms({ refresh: true });
          uni.showToast({ title: '创建成功', icon: 'success' });
          return true; // 返回true表示成功
        } else {
          throw new Error(response.message || '创建失败');
        }
      } catch (err: any) {
        this.error = err;
        console.error("Failed to create room:", err);
        uni.showToast({ title: err.message || '创建失败', icon: 'none' });
        return false; // 返回false表示失败
      } finally {
        this.loading = false;
      }
    },
    async updateRoom(roomId: string, payload: Partial<RoomCreatePayload>): Promise<boolean> {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await patch(`/rooms/${roomId}`, payload);
        if (response && response.code === 200) {
          return true;
        } else {
          throw new Error(response.message || '更新失败');
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to update room ${roomId}:`, err);
        throw err; // 抛出错误，让组件层能捕获到
      } finally {
        this.loading = false;
      }
    },

    async deleteRoom(roomId: string): Promise<boolean> {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await del(`/rooms/${roomId}`);
        if (response && response.code === 200) {
          return true;
        } else {
          throw new Error(response.message || '删除失败');
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to delete room ${roomId}:`, err);
        throw err; // 抛出错误，让组件层能捕获到
      } finally {
        this.loading = false;
      }
    },

    async checkRoomHasSessions(roomId: string): Promise<boolean> {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await get(`/rooms/${roomId}/sessions`, { page: 1, size: 1 });
        if (response && response.code === 200 && response.data) {
          return response.data.total > 0;
        }
        // 如果接口本身失败，我们也保守地认为无法删除
        return true; 
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to check sessions for room ${roomId}:`, err);
        // 发生错误时，为安全起见，也禁止删除
        return true;
      } finally {
        this.loading = false;
      }
    },

    // 分会场相关方法
    async fetchSubVenues(parentRoomId: string) {
      this.subVenuesLoading = true;
      this.subVenuesError = null;

      try {
        const response: any = await getSubVenues(parentRoomId);
        if (response && response.code === 200 && response.data) {
          this.subVenues = response.data.items || [];
        } else {
          throw new Error(response.message || 'Failed to fetch sub venues');
        }
      } catch (err: any) {
        this.subVenuesError = err;
        console.error("Failed to fetch sub venues:", err);
      } finally {
        this.subVenuesLoading = false;
      }
    },

    async createSubVenue(payload: RoomCreatePayload & { parent_room_id: string }): Promise<boolean> {
      this.subVenuesLoading = true;
      this.subVenuesError = null;
      
      try {
        const response: any = await createSubVenue(payload);
        if (response && response.code === 200) {
          // 创建成功后刷新分会场列表
          await this.fetchSubVenues(payload.parent_room_id);
          return true;
        } else {
          throw new Error(response.message || '创建分会场失败');
        }
      } catch (err: any) {
        this.subVenuesError = err;
        console.error("Failed to create sub venue:", err);
        throw err;
      } finally {
        this.subVenuesLoading = false;
      }
    },

    async updateSubVenue(roomId: string, payload: Partial<RoomCreatePayload>): Promise<boolean> {
      this.subVenuesLoading = true;
      this.subVenuesError = null;
      
      try {
        const response: any = await updateSubVenue(roomId, payload);
        if (response && response.code === 200) {
          return true;
        } else {
          throw new Error(response.message || '更新分会场失败');
        }
      } catch (err: any) {
        this.subVenuesError = err;
        console.error(`Failed to update sub venue ${roomId}:`, err);
        throw err;
      } finally {
        this.subVenuesLoading = false;
      }
    },

    async deleteSubVenue(roomId: string, parentRoomId: string): Promise<boolean> {
      this.subVenuesLoading = true;
      this.subVenuesError = null;
      
      try {
        const response: any = await deleteSubVenue(roomId);
        if (response && response.code === 200) {
          // 删除成功后刷新分会场列表
          await this.fetchSubVenues(parentRoomId);
          return true;
        } else {
          throw new Error(response.message || '删除分会场失败');
        }
      } catch (err: any) {
        this.subVenuesError = err;
        console.error(`Failed to delete sub venue ${roomId}:`, err);
        throw err;
      } finally {
        this.subVenuesLoading = false;
      }
    },
  },
});
```
 
**/src/store/session.py**
```python
import { defineStore } from 'pinia';
import type { Session, SessionCreatePayload } from '../types/session';
import { getSessionList, getSessionDetail, createSession, updateSession, deleteSession } from '../api/session';

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessions: [] as Session[],
    currentSession: null as Session | null,
    loading: false,
    error: null as Error | null,
    pagination: {
      page: 1,
      size: 10,
      hasMore: true,
      total: 0,
    },
  }),
  actions: {
    async fetchSessionsByRoomId(roomId: string, options: { refresh?: boolean } = {}) {
      if (this.loading && !options.refresh) return;
      this.loading = true;
      this.error = null;
      if (options.refresh) {
        this.pagination.page = 1;
        this.sessions = [];
      }
      try {
        const response: any = await getSessionList(roomId, {
          page: this.pagination.page,
          size: this.pagination.size,
        });
        // 兼容统一响应结构和直接业务数据两种情况
        let items, total, page, size;
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            ({ items, total, page, size } = response.data);
          } else {
            throw new Error(response.message || 'Failed to fetch sessions');
          }
        } else {
          ({ items, total, page, size } = response);
        }
        const newSessions = items || [];
        if (options.refresh) {
          this.sessions = newSessions;
        } else {
          this.sessions.push(...newSessions);
        }
        this.pagination.total = total || 0;
        this.pagination.hasMore = newSessions.length === this.pagination.size;
        if (this.pagination.hasMore) {
          this.pagination.page++;
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to fetch sessions for roomId=${roomId}:`, err);
        throw new Error(err.message || 'Failed to fetch sessions');
      } finally {
        this.loading = false;
      }
    },
    async fetchSessionById(id: string) {
      this.loading = true;
      this.error = null;
      this.currentSession = null;
      try {
        const response: any = await getSessionDetail(id);
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            console.log('getSessionDetail返回：', response);
            this.currentSession = response.data;
            console.log('赋值后currentSession：', this.currentSession);
          } else {
            throw new Error(response.message || 'Failed to fetch session details');
          }
        } else {
          this.currentSession = response;
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to fetch session detail, id=${id}:`, err);
        throw new Error(err.message || 'Failed to fetch session details');
      } finally {
        this.loading = false;
      }
    },
    async createSession(roomId: string, payload: SessionCreatePayload) {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await createSession(roomId, payload);
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            uni.showToast({ title: '创建成功', icon: 'success' });
            await this.fetchSessionsByRoomId(roomId, { refresh: true });
            return true;
          } else {
            throw new Error(response.message || '创建失败');
          }
        } else {
          uni.showToast({ title: '创建成功', icon: 'success' });
          await this.fetchSessionsByRoomId(roomId, { refresh: true });
          return true;
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to create session for roomId=${roomId}:`, err);
        throw new Error(err.message || '创建失败');
      } finally {
        this.loading = false;
      }
    },
    async updateSession(id: string, payload: Partial<Session>) {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await updateSession(id, payload);
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            uni.showToast({ title: '更新成功', icon: 'success' });
            return true;
          } else {
            throw new Error(response.message || '更新失败');
          }
        } else {
          uni.showToast({ title: '更新成功', icon: 'success' });
          return true;
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to update session id=${id}:`, err);
        throw new Error(err.message || '更新失败');
      } finally {
        this.loading = false;
      }
    },
    async deleteSession(id: string, roomId: string) {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await deleteSession(id);
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            await this.fetchSessionsByRoomId(roomId, { refresh: true });
            uni.showToast({ title: '删除成功', icon: 'success' });
            return true;
          } else {
            throw new Error(response.message || '删除失败');
          }
        } else {
          await this.fetchSessionsByRoomId(roomId, { refresh: true });
          uni.showToast({ title: '删除成功', icon: 'success' });
          return true;
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to delete session id=${id}:`, err);
        throw new Error(err.message || '删除失败');
      } finally {
        this.loading = false;
      }
    },
  },
});
```

**/src/api/room.py**
```python
/**
 * 房间相关API
 * 封装所有与"房间"相关的API请求
 */
import { request, get, post, put, del } from '../utils/request';
import type { Room, RoomCreatePayload } from '../types/room';

/**
 * 分页响应接口
 */
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

/**
 * 获取房间列表
 * @param params 分页参数
 * @returns Promise<PaginatedResponse<Room>>
 */
export const getRoomList = (params: { page?: number; size?: number } = {}): Promise<PaginatedResponse<Room>> => {
  return get<PaginatedResponse<Room>>('/rooms', params);
};

/**
 * 获取单个房间详情
 * @param roomId 房间ID
 * @returns Promise<Room>
 */
export const getRoomDetail = (roomId: string): Promise<Room> => {
  return get<Room>(`/rooms/${roomId}`);
};

/**
 * 创建一个新的直播间
 * @param payload 创建房间所需的数据，如 { title: string, description: string }
 */
export const createRoom = (payload: RoomCreatePayload) => {
  return post<Room>('/rooms', payload, { auth: true }); // 向 /rooms 发送POST请求
};

/**
 * 更新房间
 * @param roomId 房间ID
 * @param data 要更新的房间数据
 * @returns Promise<Room>
 */
export const updateRoom = (roomId: string, data: Partial<Room>): Promise<Room> => {
  // 由于uni.request不支持PATCH，这里使用PUT代替
  // 添加认证选项
  return put<Room>(`/rooms/${roomId}`, data, { auth: true });
};

/**
 * 删除房间
 * @param roomId 房间ID
 * @returns Promise<void>
 */
export const deleteRoom = (roomId: string): Promise<void> => {
  return del<void>(`/rooms/${roomId}`, undefined, { auth: true });
};

/**
 * 获取主会场下所有分会场
 * @param roomId 主会场ID
 * @returns Promise<Room[]>
 */
export const getSubVenues = (roomId: string): Promise<Room[]> => {
  return get<Room[]>(`/rooms/${roomId}/sub-venues`);
};

/**
 * 创建分会场
 * @param payload 创建分会场的数据，包含 parent_room_id
 * @returns Promise<Room>
 */
export const createSubVenue = (payload: RoomCreatePayload & { parent_room_id: string }): Promise<Room> => {
  return post<Room>('/rooms', payload, { auth: true });
};

/**
 * 更新分会场
 * @param roomId 分会场ID
 * @param data 要更新的数据
 * @returns Promise<Room>
 */
export const updateSubVenue = (roomId: string, data: Partial<Room>): Promise<Room> => {
  return put<Room>(`/rooms/${roomId}`, data, { auth: true });
};

/**
 * 删除分会场
 * @param roomId 分会场ID
 * @returns Promise<void>
 */
export const deleteSubVenue = (roomId: string): Promise<void> => {
  return del<void>(`/rooms/${roomId}`, undefined, { auth: true });
}; 
```
* `/src/api/session.py`
```python
 // api/session.ts
import { request } from '../utils/request';
import type { Session, SessionCreatePayload } from '../types/session';

// 统一响应结构
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

// 分页响应体
export interface PaginatedSessions {
  total: number;
  page: number;
  size: number;
  items: Session[];
}

// 获取房间下所有场次 (GET /rooms/{room_id}/sessions)
export const getSessionList = (roomId: string, params: { page?: number, size?: number }) => {
  return request<PaginatedSessions>({
    url: `/rooms/${roomId}/sessions`,
    method: 'GET',
    data: params,
  });
};

// 获取单个场次详情 (GET /sessions/{session_id})
export const getSessionDetail = (sessionId: string) => {
  return request<Session>({
    url: `/sessions/${sessionId}`,
    method: 'GET',
  });
};

// 创建场次 (POST /rooms/{room_id}/sessions)
export const createSession = (roomId: string, data: Partial<SessionCreatePayload>) => {
  return request<Session>({
    url: `/rooms/${roomId}/sessions`,
    method: 'POST',
    data,
  });
};

// 更新场次 (PATCH /sessions/{session_id})
export const updateSession = (sessionId: string, data: Partial<Session>) => {
  return request<Session>({
    url: `/sessions/${sessionId}`,
    method: 'PATCH',
    data,
  });
};

// 删除场次 (DELETE /sessions/{session_id})
export const deleteSession = (sessionId: string) => {
  return request<{ id: string; status: string }>({
    url: `/sessions/${sessionId}`,
    method: 'DELETE',
  });
};

```
---

## 4. 代码生成具体要求 (Test Code Generation Requirements)

### 4.1. 组件测试
- 每个核心组件生成独立的 .spec.ts 文件，覆盖：
  - props 正常渲染
  - 事件触发
  - slot 内容渲染
  - 边界条件（如必填/可选、禁用、异常）
- 每个测试用例严格遵循 AAA 模式，mock 所有外部依赖

### 4.2. 工具函数测试
- 每个工具函数生成独立的 .spec.ts 文件，覆盖：
  - 正常输入输出
  - 边界/异常输入
  - 断言输出类型和值

### 4.3. Pinia store 测试
- 每个 store 生成独立的 .spec.ts 文件，覆盖：
  - state 初始值
  - action 调用及状态变更
  - getter 逻辑
  - 模块间交互（如有）

### 4.4. API 封装测试
- 每个 API 封装生成独立的 .spec.ts 文件，覆盖：
  - 参数校验
  - 返回值结构
  - 异常分支
  - 所有网络请求需 mock，不允许真实请求

### 4.5. 断言与隔离
- 所有断言需具体、可复现（如 toBe、toEqual、toContain、toHaveBeenCalled）
- 每个测试用例独立，beforeEach/afterEach 清理副作用

---

### 【重点补充：高质量测试的细节要求】

1. **mock 与依赖隔离**
   - 所有 API 封装、store action、组件事件、工具函数中涉及的网络请求、全局依赖、uni-app API、定时器、外部模块，必须用 `vi.mock` 或 `vi.fn` 进行 mock，绝不允许真实请求或副作用。
   - 示例：
     - mock uni.showToast: `vi.spyOn(uni, 'showToast').mockImplementation(() => {})`
     - mock 网络请求: `vi.mock('@/utils/request', () => ({ get: vi.fn(), post: vi.fn() }))`
     - mock setTimeout: `vi.useFakeTimers()`

2. **断言要具体，禁止模糊断言**
   - 所有断言必须具体、可复现，优先使用 `toBe`、`toEqual`、`toContain`、`toHaveBeenCalledWith` 等，禁止使用 `toBeTruthy`、`toBeFalsy`。
   - 示例：
     - `expect(wrapper.attributes('disabled')).toBe('disabled')`
     - `expect(res).toEqual({ id: '1', title: 'test' })`

3. **组件测试要覆盖 slot、边界、交互**
   - 每个组件测试需覆盖：props 的所有分支（必填、可选、默认值、异常值）、slot 内容渲染、事件触发与回调、边界条件（如 loading、disabled、无数据、图片加载失败等）。
   - 示例：RoomCard.vue 测试 cover_url 为空、图片加载失败、私密房间、actions slot、点击事件。

4. **Store 测试要覆盖 action、state、异常**
   - 每个 store 测试需覆盖：state 初始值、action 的正常流程、异常流程、getter 逻辑（如有）、与 API/mock 的集成。
   - 示例：useRoomStore：fetchRooms 正常/异常、addNewRoom 成功/失败、deleteRoom、分会场相关 action。

5. **API 封装测试要 mock 网络、覆盖异常**
   - API 封装测试需 mock 掉所有 request，覆盖参数校验、返回值结构、异常分支（如网络错误、返回非 200、数据为空等）。

6. **工具函数测试要覆盖边界和异常**
   - 工具函数需覆盖正常输入、边界输入、异常输入。

7. **统一测试文件结构和命名**
   - 所有测试文件命名为 `xxx.spec.ts`，与被测文件同名，放在 `tests/` 目录下，或与被测文件同级的 `__tests__` 目录。

8. **本提示词适用范围说明**
   - 本文档仅适用于第一批次（src/components、src/utils、src/store、src/api 的核心单元测试）。
   - 第二批次（页面与集成）：src/pages/ 下所有页面（RoomList、RoomDetail、LiveView 等），组件与 store、api 的集成交互。
   - 第三批次（端到端/E2E）：典型业务流程的端到端测试（如：房间创建-详情-场次-播放全链路）、权限、异常、边界场景。

---

## 5. 最终交付 (Final Deliverable)

请为 frontend_live/src/ 下的 components、utils、store、api 目录下所有核心单元，分别生成完整、可运行的 Vitest 测试文件（.spec.ts），每个测试文件需覆盖主要功能、边界条件、异常分支，所有测试用例需独立、mock 所有外部依赖，严格遵循 AAA（Arrange-Act-Assert）模式。

每个测试文件请用清晰的代码块标注文件名和内容，便于直接落地。

