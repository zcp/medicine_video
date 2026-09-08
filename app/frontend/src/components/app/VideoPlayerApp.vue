<template>
  <view class="video-player-app">
    <!-- uni-app原生video组件 -->
    <video
      v-if="src"
      :id="playerId"
      :src="src"
      :controls="true"
      :autoplay="autoplay"
      :enable-play-gesture="true"
      :show-center-play-btn="true"
      :show-fullscreen-btn="true"
      :show-play-btn="true"
      :show-progress="true"
      :poster="poster"
      class="video-elem"
      @play="onPlay"
      @playing="onPlaying"
      @pause="onPause"
      @timeupdate="onTimeUpdate"
      @seeked="onSeeked"
      @ended="onEnded"
      @error="onError"
      @waiting="onWaiting"
      @fullscreenchange="onFullscreenChange"
      @loadedmetadata="onLoadedMetadata"
    >

      <!-- 1. 播放控制遮罩 -->
      <cover-view v-if="showControls" class="player-overlay">
        <cover-view class="control-bar">
          <cover-view class="control-btn" @click="togglePlay">
            <cover-view class="btn-icon iconfont" :class="isPlaying ? 'icon-pause' : 'icon-video'"></cover-view>
          </cover-view>
          <!-- 进度条在cover-view中通常简化处理，或使用原生slider -->
          <cover-view class="control-btn fullscreen" @click="toggleFullscreen">
            <cover-view class="btn-icon iconfont icon-more"></cover-view>
          </cover-view>
        </cover-view>
      </cover-view>

      <!-- 2. 加载状态（克制：透明度不超过 0.8，不抢视觉；不加文字——原生 video 自带缓冲指示） -->
      <cover-view v-if="isLoading" class="loading-overlay"></cover-view>

      <!-- 3. 错误提示 -->
      <cover-view v-if="error" class="error-overlay">
        <cover-view class="error-text">{{ error }}</cover-view>
        <cover-view class="retry-btn" @click="retry">重试</cover-view>
      </cover-view>
    </video>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { ShadowParser } from '@/utils/ShadowParser';
import { useAuthStore } from '@/store/auth';

// Props
interface Props {
  src?: string;
  poster?: string;
  autoplay?: boolean;
  controls?: boolean;
  muted?: boolean;
  initialTime?: number;
}

const props = withDefaults(defineProps<Props>(), {
  autoplay: false,
  controls: true,
  muted: false,
  initialTime: 0
});

// Emits
const emit = defineEmits<{
  play: [];
  playing: [];
  pause: [];
  ended: [];
  timeupdate: [detail: any];
  segmentchange: [data: any];
  error: [error: string];
}>();

// 响应式数据
const isPlaying = ref(false);
const isLoading = ref(false);
const error = ref('');
const currentTime = ref(0);
const duration = ref(0);
const isFullscreen = ref(false);
const showControls = ref(false);
const controlsTimer = ref<number | null>(null);

// ShadowParser实例
let parser: ShadowParser | null = null;
let lastReportedTs: string | null = null;
let reportTimer: number | null = null;

// Store
const authStore = useAuthStore();

// 计算属性
const playerId = computed(() => `video-player-${Date.now()}`);

// 方法定义（必须在watch之前定义，避免"Cannot access before initialization"错误）
// 🎯 关键容错：解析器失败不能阻断视频播放
const initParser = async (m3u8Url: string) => {
  try {
    parser = new ShadowParser(m3u8Url);
    await parser.init();
    console.log('[VideoPlayerApp] ShadowParser初始化成功');
  } catch (error) {
    // 🔧 容错处理：解析器初始化失败不影响视频播放
    // 仅记录错误，继续播放（观看统计功能降级）
    console.warn('[VideoPlayerApp] ShadowParser初始化失败，但视频播放不受影响:', error);
    parser = null; // 确保parser为null，避免后续调用出错
  }
};

const destroyParser = () => {
  if (parser) {
    parser.destroy();
    parser = null;
  }
  lastReportedTs = null;
  clearReportTimer();
};

const clearReportTimer = () => {
  if (reportTimer) {
    clearTimeout(reportTimer);
    reportTimer = null;
  }
};

// 清除控制栏定时器
const clearControlsTimer = () => {
  if (controlsTimer.value) {
    clearTimeout(controlsTimer.value);
    controlsTimer.value = null;
  }
};

// 显示控制栏（带自动隐藏）
const showControlsWithTimeout = () => {
  showControls.value = true;
  clearControlsTimer();

  controlsTimer.value = setTimeout(() => {
    showControls.value = false;
  }, 3000) as unknown as number;
};

// 生命周期
onMounted(() => {
  // 触摸显示控制栏
  showControlsWithTimeout();
  
  // 如果初始有src值，手动初始化解析器
  if (props.src && props.src.endsWith('.m3u8')) {
    initParser(props.src);
  }
});

// 监听src变化，初始化解析器（必须在所有函数定义和生命周期之后）
watch(() => props.src, (newSrc, oldSrc) => {
  console.log('[VideoPlayerApp] src变化:', { oldSrc, newSrc });
  if (newSrc && newSrc.endsWith('.m3u8')) {
    initParser(newSrc);
  } else {
    destroyParser();
  }
});

onBeforeUnmount(() => {
  destroyParser();
  clearControlsTimer();
  // 🔧 资源释放优化：清理屏幕常亮状态，防止内存泄漏和电量消耗
  uni.setKeepScreenOn({ keepScreenOn: false });
});

// 上报TS切片（防抖处理）
const reportSegment = async (segment: any, isSeek = false) => {
  if (!segment || segment.name === lastReportedTs) {
    return; // 避免重复上报
  }

  // 防抖：500ms内只上报一次
  if (reportTimer) {
    clearTimeout(reportTimer);
  }

  reportTimer = setTimeout(async () => {
    console.log('[VideoPlayerApp] 进入新切片:', segment.name);

    try {
      // 通知父组件处理业务逻辑
      emit('segmentchange', {
        tsFilename: segment.name,
        segmentIndex: segment.index,
        currentTime: segment.start,
        isSeek
      });

      lastReportedTs = segment.name;
    } catch (error) {
      console.error('[VideoPlayerApp] 上报切片失败:', error);
    }
  }, 500) as unknown as number;
};

// 播放控制方法
const togglePlay = () => {
  const videoContext = uni.createVideoContext(playerId.value);
  if (isPlaying.value) {
    videoContext.pause();
  } else {
    videoContext.play();
  }
};

const toggleFullscreen = () => {
  const videoContext = uni.createVideoContext(playerId.value);
  if (isFullscreen.value) {
    // 退出全屏：恢复竖屏
    videoContext.exitFullScreen();
    // 🔧 全屏方向锁定：退出全屏时恢复竖屏
    try {
      // #ifdef APP-PLUS
      plus.screen.lockOrientation('portrait-primary');
      // #endif
    } catch (error) {
      console.warn('[VideoPlayerApp] 恢复竖屏失败:', error);
    }
  } else {
    // 进入全屏：锁定横屏
    videoContext.requestFullScreen();
    // 🔧 全屏方向锁定：进入全屏时强制横屏，提升观看体验
    try {
      // #ifdef APP-PLUS
      plus.screen.lockOrientation('landscape-primary');
      // #endif
    } catch (error) {
      console.warn('[VideoPlayerApp] 锁定横屏失败:', error);
    }
  }
};

const retry = () => {
  error.value = '';
  isLoading.value = true;

  // 重新加载视频
  const videoContext = uni.createVideoContext(playerId.value);
  videoContext.play();
};

// 事件处理
const onPlay = () => {
  console.log('[VideoPlayerApp] 播放开始');
  isPlaying.value = true;
  isLoading.value = false;
  error.value = '';

  // 屏幕常亮
  uni.setKeepScreenOn({ keepScreenOn: true });

  emit('play');
};

const onPause = () => {
  isPlaying.value = false;
  emit('pause');
};

const onEnded = () => {
  isPlaying.value = false;
  uni.setKeepScreenOn({ keepScreenOn: false });
  emit('ended');
};

const onTimeUpdate = (e: any) => {
  currentTime.value = e.detail?.currentTime || 0;
  duration.value = e.detail?.duration || 0;

  // 如果视频正在播放且有时间更新，说明不在加载状态
  if (isPlaying.value && isLoading.value) {
    isLoading.value = false;
  }

  // TS切片检测
  if (parser) {
    const segment = parser.check(currentTime.value);
    if (segment) {
      reportSegment(segment);
    }
  }

  emit('timeupdate', e.detail);
};

const onSeeked = (e: any) => {
  const seekTime = e.detail?.currentTime || 0;
  console.log('[VideoPlayerApp] 用户拖动到:', seekTime);

  // 用户拖动后立即检测切片
  if (parser) {
    const segment = parser.check(seekTime);
    if (segment) {
      reportSegment(segment, true); // 标记为seek操作
    }
  }
};

const onWaiting = () => {
  console.log('[VideoPlayerApp] 视频缓冲中...');
  isLoading.value = true;
};

// 🔧 加载状态优化：视频开始播放时关闭loading状态
const onPlaying = () => {
  console.log('[VideoPlayerApp] 视频开始播放');
  isLoading.value = false;
  isPlaying.value = true;
  error.value = '';
  emit('playing');
};

const onLoadedMetadata = (e: any) => {
  console.log('[VideoPlayerApp] 视频元数据加载完成:', {
    duration: e.detail?.duration,
    width: e.detail?.width,
    height: e.detail?.height
  });
  duration.value = e.detail?.duration || 0;
  // 元数据加载完成，关闭loading状态
  if (isLoading.value) {
    isLoading.value = false;
  }
};

const onError = (e: any) => {
  console.error('[VideoPlayerApp] 播放错误:', e);
  isLoading.value = false;
  const errorMsg = e.detail?.errMsg || e.errMsg || '播放失败';
  error.value = errorMsg;
  emit('error', errorMsg);
};

const onFullscreenChange = (e: any) => {
  const fullScreen = e.detail?.fullScreen || false;
  isFullscreen.value = fullScreen;
  
  // 全屏状态变化时的处理
  nextTick(() => {
    if (!fullScreen) {
      // 退出全屏时，强制重新渲染视频组件以修复布局
      console.log('[VideoPlayerApp] 退出全屏，重置布局');
      
      // 方法1: 触发页面重新布局
      nextTick(() => {
        // 强制触发页面重新计算布局
        const query = uni.createSelectorQuery();
        query.select('.video-player-app').boundingClientRect();
        query.exec();
      });
      
      // 方法2: 重置屏幕方向锁定
      try {
        // #ifdef APP-PLUS
        plus.screen.lockOrientation('portrait-primary');
        // #endif
      } catch (error) {
        console.warn('[VideoPlayerApp] 重置屏幕方向失败:', error);
      }
      
      // 方法3: 延迟触发窗口resize事件
      setTimeout(() => {
        // 触发窗口resize事件，让页面重新计算布局
        const resizeEvent = new Event('resize');
        window.dispatchEvent && window.dispatchEvent(resizeEvent);
      }, 100);
    }
  });
};

// 暴露方法给父组件
defineExpose({
  play: () => {
    const videoContext = uni.createVideoContext(playerId.value);
    videoContext.play();
  },
  pause: () => {
    const videoContext = uni.createVideoContext(playerId.value);
    videoContext.pause();
  },
  seek: (time: number) => {
    const videoContext = uni.createVideoContext(playerId.value);
    videoContext.seek(time);
  }
});

</script>

<style lang="scss" scoped>
.video-player-app {
  position: relative;
  width: 100%;
  background: #000;
  overflow: hidden;
  
  // 确保全屏退出后布局正确恢复
  &::after {
    content: '';
    display: block;
    clear: both;
  }
}

.video-elem {
  width: 100% !important;
  height: 100% !important;
  min-height: 200px;
  display: block;
  object-fit: contain;
  
  // 强制重置可能被全屏影响的样式
  position: relative !important;
  top: 0 !important;
  left: 0 !important;
  transform: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 播放控制覆盖层 */
.player-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 20rpx;

  .control-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20rpx;

    .control-btn {
      width: 80rpx;
      height: 80rpx;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;

      .btn-icon {
        font-size: 32rpx;
        color: #fff;
      }
    }
  }
}

/* 加载状态：克制，透明度不超过 0.8，不抢视觉 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

/* 错误状态 */
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  padding: 40rpx;

  .error-text {
    text-align: center;
    margin-bottom: 40rpx;
    font-size: 28rpx;
  }

  .retry-btn {
    padding: 20rpx 40rpx;
    background: #509cec;
    color: #fff;
    border: none;
    border-radius: 8rpx;
    font-size: 28rpx;
  }
}
</style>