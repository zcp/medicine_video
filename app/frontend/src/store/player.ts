import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const usePlayerStore = defineStore('player', () => {
  // 播放状态管理
  const currentUrl = ref('');
  const isPlaying = ref(false);
  const currentTime = ref(0);
  const viewerCount = ref(0);

  // 播放统计
  const playStartTime = ref(0);
  const totalPlayTime = ref(0);
  const totalBufferTime = ref(0);
  const stallCount = ref(0);
  const totalStallTime = ref(0);
  const qualityChangeCount = ref(0);
  const currentQuality = ref('720p');

  // 方法定义
  const setPlayingState = (playing: boolean) => {
    isPlaying.value = playing;
    if (playing && playStartTime.value === 0) {
      playStartTime.value = Date.now();
    }
  };

  const updateViewerCount = (count: number) => {
    viewerCount.value = count;
  };

  const setCurrentUrl = (url: string) => {
    currentUrl.value = url;
  };

  const updateCurrentTime = (time: number) => {
    currentTime.value = time;
  };

  const incrementStallCount = () => {
    stallCount.value++;
  };

  const addStallTime = (duration: number) => {
    totalStallTime.value += duration;
  };

  const incrementQualityChanges = () => {
    qualityChangeCount.value++;
  };

  const setQuality = (quality: string) => {
    currentQuality.value = quality;
    qualityChangeCount.value++;
  };

  const addPlayTime = (duration: number) => {
    totalPlayTime.value += duration;
  };

  const addBufferTime = (duration: number) => {
    totalBufferTime.value += duration;
  };

  const resetStats = () => {
    playStartTime.value = 0;
    totalPlayTime.value = 0;
    totalBufferTime.value = 0;
    stallCount.value = 0;
    totalStallTime.value = 0;
    qualityChangeCount.value = 0;
    currentQuality.value = '720p';
  };

  // 计算属性
  const playDuration = computed(() => {
    if (playStartTime.value === 0) return 0;
    return Date.now() - playStartTime.value;
  });

  return {
    // 状态
    currentUrl,
    isPlaying,
    currentTime,
    viewerCount,
    playStartTime,
    totalPlayTime,
    totalBufferTime,
    stallCount,
    totalStallTime,
    qualityChangeCount,
    currentQuality,

    // 方法
    setPlayingState,
    updateViewerCount,
    setCurrentUrl,
    updateCurrentTime,
    incrementStallCount,
    addStallTime,
    incrementQualityChanges,
    setQuality,
    addPlayTime,
    addBufferTime,
    resetStats,

    // 计算属性
    playDuration
  };
});
