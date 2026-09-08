# VideoPlayer 组件分层重构指南

## 📊 现状分析

### 当前实现

**文件位置**：`src/components/VideoPlayer.vue`  
**实现方式**：基于 Artplayer + hls.js  
**适用平台**：❌ 仅H5（App端无法使用Artplayer）  
**代码行数**：147行  
**结论**：**必须分层**

###关键问题

1. **Artplayer** 是H5专属库，App端不支持
2. **hls.js** 也是H5专属，App端需要原生video
3. 整个组件100%为H5实现，App端需要完全重写

---

## 🎯 重构方案

### 方案：创建平台专属组件

```
components/
├── h5/
│   └── VideoPlayerH5.vue      # 基于 Artplayer + hls.js
└── app/
    └── VideoPlayerApp.vue     # 基于 uni-app 原生 video
```

---

## 📝 实施步骤

### 步骤1：创建 H5 版本（迁移现有代码）

```bash
# 将现有 VideoPlayer.vue 移到 h5/ 目录并重命名
Move-Item src/components/VideoPlayer.vue src/components/h5/VideoPlayerH5.vue
```

**src/components/h5/VideoPlayerH5.vue** （保持原有代码不变）

---

### 步骤2：创建 App 版本（新建）

**src/components/app/VideoPlayerApp.vue**

```vue
<template>
  <view class="video-player-container">
    <video
      :src="src"
      :poster="poster"
      :muted="muted"
      :autoplay="false"
      :controls="true"
      :show-center-play-btn="true"
      :show-fullscreen-btn="true"
      :enable-progress-gesture="true"
      class="video-player"
      @play="onPlay"
      @pause="onPause"
      @ended="onEnded"
      @error="onError"
      @timeupdate="onTimeUpdate"
      @fullscreenchange="onFullscreenChange"
    >
      <text class="video-error-message" v-if="errorMessage">
        {{ errorMessage }}
      </text>
    </video>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

/**
 * VideoPlayer 组件 Props
 */
interface VideoPlayerProps {
  /** 视频源地址 */
  src?: string
  /** 封面图 */
  poster?: string
  /** 是否静音 */
  muted?: boolean
}

const props = withDefaults(defineProps<VideoPlayerProps>(), {
  muted: false
})

/**
 * 组件 Emits
 */
const emit = defineEmits<{
  play: []
  pause: []
  ended: []
  error: [error: any]
  timeupdate: [currentTime: number]
  fullscreenchange: [isFullscreen: boolean]
}>()

// 错误信息
const errorMessage = ref('')

/**
 * 播放事件
 */
const onPlay = () => {
  console.log('[VideoPlayerApp] 播放开始')
  errorMessage.value = ''
  emit('play')
}

/**
 * 暂停事件
 */
const onPause = () => {
  console.log('[VideoPlayerApp] 播放暂停')
  emit('pause')
}

/**
 * 播放结束事件
 */
const onEnded = () => {
  console.log('[VideoPlayerApp] 播放结束')
  emit('ended')
}

/**
 * 错误事件
 */
const onError = (e: any) => {
  console.error('[VideoPlayerApp] 播放错误:', e)
  errorMessage.value = '视频加载失败，请稍后重试'
  emit('error', e)
}

/**
 * 时间更新事件
 */
const onTimeUpdate = (e: any) => {
  const currentTime = e.detail.currentTime
  emit('timeupdate', currentTime)
}

/**
 * 全屏变化事件
 */
const onFullscreenChange = (e: any) => {
  const isFullscreen = e.detail.fullScreen
  console.log('[VideoPlayerApp] 全屏状态:', isFullscreen)
  emit('fullscreenchange', isFullscreen)
}

/**
 * 监听 src 变化
 */
watch(() => props.src, (newSrc) => {
  if (newSrc) {
    console.log('[VideoPlayerApp] 视频源更新:', newSrc)
    errorMessage.value = ''
  }
})
</script>

<style scoped>
.video-player-container {
  width: 100%;
  height: 500px;
  position: relative;
  background-color: #000;
}

.video-player {
  width: 100%;
  height: 100%;
}

.video-error-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 14px;
  text-align: center;
  z-index: 10;
}
</style>
```

---

### 步骤3：更新页面引用

**pages/live/LiveView.vue 或其他使用VideoPlayer的页面**

```vue
<template>
  <view class="live-view">
    <!-- ✅ 使用条件编译加载对应平台组件 -->
    <!-- #ifdef H5 -->
    <VideoPlayerH5 
      :src="streamUrl" 
      :poster="coverUrl"
      :muted="isMuted"
      @play="onPlay"
      @pause="onPause"
      @error="onPlayerError"
    />
    <!-- #endif -->
    
    <!-- #ifdef APP-PLUS -->
    <VideoPlayerApp 
      :src="streamUrl" 
      :poster="coverUrl"
      :muted="isMuted"
      @play="onPlay"
      @pause="onPause"
      @error="onPlayerError"
    />
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// #ifdef H5
import VideoPlayerH5 from '@/components/h5/VideoPlayerH5.vue'
// #endif

// #ifdef APP-PLUS
import VideoPlayerApp from '@/components/app/VideoPlayerApp.vue'
// #endif

const streamUrl = ref('https://example.com/live/stream.m3u8')
const coverUrl = ref('https://example.com/cover.jpg')
const isMuted = ref(false)

const onPlay = () => {
  console.log('播放开始')
}

const onPause = () => {
  console.log('播放暂停')
}

const onPlayerError = (error: any) => {
  console.error('播放器错误:', error)
  uni.showToast({
    title: '播放失败',
    icon: 'none'
  })
}
</script>
```

---

### 步骤4：使用平台工具动态加载（可选高级方案）

如果不想在每个页面都写条件编译，可以使用平台工具：

```vue
<template>
  <view class="live-view">
    <component :is="VideoPlayer" :src="streamUrl" @play="onPlay" />
  </view>
</template>

<script setup lang="ts">
import { ref, shallowRef, onMounted } from 'vue'
import { importPlatformComponent } from '@/utils/platform'

const VideoPlayer = shallowRef(null)
const streamUrl = ref('https://example.com/live/stream.m3u8')

onMounted(async () => {
  // 自动根据平台加载对应组件
  VideoPlayer.value = await importPlatformComponent('VideoPlayer')
})

const onPlay = () => {
  console.log('播放开始')
}
</script>
```

---

## ✅ 验证清单

重构完成后，检查以下项目：

- [ ] H5 版本文件已创建：`src/components/h5/VideoPlayerH5.vue`
- [ ] App 版本文件已创建：`src/components/app/VideoPlayerApp.vue`
- [ ] 原始 `src/components/VideoPlayer.vue` 已删除或归档
- [ ] 所有引用VideoPlayer的页面已更新导入路径
- [ ] H5 环境测试：运行 `npm run dev:h5`，播放器正常
- [ ] App 环境测试：运行 `npm run dev:app-android` 或 `npm run dev:app-ios`，播放器正常
- [ ] 播放、暂停、错误处理等功能正常
- [ ] 全屏功能正常
- [ ] 视频源切换正常

---

## 📊 重构前后对比

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| **文件数量** | 1个 | 2个（H5 + App） |
| **代码复用** | ❌ 无法复用 | ✅ 各平台独立优化 |
| **可维护性** | ⚠️ 条件编译混乱 | ✅ 结构清晰 |
| **H5性能** | ✅ 正常 | ✅ 保持不变 |
| **App性能** | ❌ 无法使用 | ✅ 原生性能 |
| **扩展性** | ❌ 难以扩展 | ✅ 易于扩展 |

---

## 🚀 后续优化建议

### 1. 提取公共Props和Events

创建 `types/video-player.ts`：

```typescript
/**
 * 视频播放器通用Props接口
 */
export interface VideoPlayerProps {
  src?: string
  poster?: string
  muted?: boolean
  autoplay?: boolean
}

/**
 * 视频播放器通用Events接口
 */
export interface VideoPlayerEvents {
  play: []
  pause: []
  ended: []
  error: [error: any]
  timeupdate: [currentTime: number]
  fullscreenchange: [isFullscreen: boolean]
}
```

两个组件都使用这个接口，保证API一致性。

### 2. 添加单元测试

```typescript
// tests/unit/components/VideoPlayerH5.spec.ts
import { mount } from '@vue/test-utils'
import VideoPlayerH5 from '@/components/h5/VideoPlayerH5.vue'

describe('VideoPlayerH5', () => {
  it('应该正确渲染', () => {
    const wrapper = mount(VideoPlayerH5, {
      props: {
        src: 'https://example.com/test.m3u8'
      }
    })
    expect(wrapper.find('.video-player-container').exists()).toBe(true)
  })
  
  it('应该触发play事件', async () => {
    const wrapper = mount(VideoPlayerH5, {
      props: {
        src: 'https://example.com/test.m3u8'
      }
    })
    await wrapper.vm.$emit('play')
    expect(wrapper.emitted().play).toBeTruthy()
  })
})
```

### 3. 添加错误边界

```vue
<!-- components/common/VideoPlayerWrapper.vue -->
<template>
  <view class="video-player-wrapper">
    <template v-if="!loadError">
      <!-- #ifdef H5 -->
      <VideoPlayerH5 v-bind="$attrs" @error="onError" />
      <!-- #endif -->
      
      <!-- #ifdef APP-PLUS -->
      <VideoPlayerApp v-bind="$attrs" @error="onError" />
      <!-- #endif -->
    </template>
    
    <view v-else class="error-state">
      <text>播放器加载失败</text>
      <button @click="retry">重试</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// #ifdef H5
import VideoPlayerH5 from '@/components/h5/VideoPlayerH5.vue'
// #endif

// #ifdef APP-PLUS
import VideoPlayerApp from '@/components/app/VideoPlayerApp.vue'
// #endif

const loadError = ref(false)

const onError = (error: any) => {
  console.error('播放器错误:', error)
  loadError.value = true
}

const retry = () => {
  loadError.value = false
  // 重新加载
}
</script>
```

---

## 📝 注意事项

1. **依赖管理**
   - Artplayer 和 hls.js 只在 H5 环境需要，可以保留在 dependencies
   - 构建时 vite 会自动排除 App 端不需要的代码

2. **视频格式支持**
   - H5：支持 m3u8(HLS)、mp4
   - App：支持 mp4、m3u8（原生支持）、rtmp
   - 小程序：仅支持 mp4、m3u8

3. **性能优化**
   - H5：使用 hls.js 的 Worker 模式
   - App：启用硬件加速
   - 避免频繁切换视频源

4. **错误处理**
   - 统一错误码和错误信息
   - 提供友好的错误提示
   - 记录错误日志便于排查

---

## ⏱️ 预计时间

- **创建H5版本**：10分钟（迁移现有代码）
- **创建App版本**：30分钟（重写组件）
- **更新页面引用**：20分钟
- **测试验证**：30分钟

**总计：约1.5小时**
