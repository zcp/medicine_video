<template>
  <div class="video-player-container" ref="containerRef"></div>
</template>

<script setup lang="ts">
/**
 * H5端视频播放器
 * 基于 Artplayer + hls.js
 * 支持HLS直播流和点播视频
 */
import { ref, onMounted, onBeforeUnmount, withDefaults, watch } from 'vue';
import Artplayer from 'artplayer';
import Hls from 'hls.js';

interface Props {
  src?: string;
  muted?: boolean;
  autoplay?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  muted: false,
  autoplay: false,
});

const containerRef = ref<HTMLDivElement | null>(null);
let art: Artplayer | null = null;
let currentHls: Hls | null = null;

/**
 * 创建Artplayer实例
 */
const createPlayer = (url: string) => {
  if (!containerRef.value) return;

  art = new Artplayer({
    container: containerRef.value,
    url: url,
    autoplay: props.autoplay,
    muted: props.muted,
    volume: 1,
    setting: true,
    playbackRate: true,
    fullscreen: true,
    fullscreenWeb: true,
    pip: true,
    theme: '#1e80ff',
    type: url.endsWith('.m3u8') ? 'm3u8' : undefined as any,
    customType: {
      m3u8(video: HTMLVideoElement, url: string) {
        if (Hls.isSupported()) {
          // 清理旧的HLS实例
          if (currentHls) {
            try { currentHls.destroy(); } catch {}
            currentHls = null;
          }
          // 创建新的HLS实例
          const hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
          });
          hls.loadSource(url);
          hls.attachMedia(video);
          currentHls = hls;

          // HLS错误处理
          hls.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
              console.error('[VideoPlayerH5] HLS Fatal Error:', data);
              switch (data.type) {
                case Hls.ErrorTypes.NETWORK_ERROR:
                  console.log('[VideoPlayerH5] Network error, trying to recover...');
                  hls.startLoad();
                  break;
                case Hls.ErrorTypes.MEDIA_ERROR:
                  console.log('[VideoPlayerH5] Media error, trying to recover...');
                  hls.recoverMediaError();
                  break;
                default:
                  console.error('[VideoPlayerH5] Cannot recover, destroying HLS instance');
                  hls.destroy();
                  break;
              }
            }
          });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          // iOS原生支持HLS
          video.src = url;
        }
      },
    },
  });
};

/**
 * 销毁播放器
 */
const destroyPlayer = () => {
  if (art) {
    try { art.destroy(false); } catch {}
    art = null;
  }
  if (currentHls) {
    try { currentHls.destroy(); } catch {}
    currentHls = null;
  }
};

onMounted(() => {
  if (props.src) {
    createPlayer(props.src);
  }
});

onBeforeUnmount(() => {
  destroyPlayer();
});

// 监听src变化，动态切换播放源
watch(() => props.src, (newSrc) => {
  if (!newSrc) return;

  if (!art) {
    // 播放器不存在，创建新的
    createPlayer(newSrc);
    return;
  }

  // 播放器已存在，切换URL
  try {
    // 清理旧的HLS实例
    if (currentHls) {
      currentHls.destroy();
      currentHls = null;
    }
    // 使用Artplayer API切换URL
    // @ts-ignore
    art.switchUrl(newSrc);
  } catch (e) {
    console.error('[VideoPlayerH5] Failed to switch URL:', e);
    // 切换失败，重新创建播放器
    destroyPlayer();
    createPlayer(newSrc);
  }
});
</script>

<style scoped>
.video-player-container {
  width: 100%;
  height: 500px;
  position: relative;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
}
</style>
