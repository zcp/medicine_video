<template>
  <image 
    :src="displaySrc" 
    :mode="mode"
    :class="{ loading: isLoading }"
    @error="handleError"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
/**
 * 支持外部URL代理的Image组件
 * @description 自动检测外部URL并使用代理加载，解决APP端跨域/防盗链问题
 * 
 * 使用方式：
 * ```vue
 * <ProxyImage 
 *   :src="expert.avatar_url" 
 *   :fallback="/static/default-avatar.png"
 *   mode="aspectFill"
 *   class="avatar"
 * />
 * ```
 */
import { ref, watch, onMounted } from 'vue';
import { loadImageWithProxy } from '@/utils/imageProxy';

interface Props {
  /** 图片URL */
  src: string;
  /** 加载失败时的回退图片 */
  fallback?: string;
  /** 图片裁剪模式 */
  mode?: string;
  /** 是否启用代理（默认自动检测外部URL） */
  useProxy?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  fallback: '/static/default.png',
  mode: 'aspectFill',
  useProxy: true
});

const emit = defineEmits<{
  (e: 'load'): void;
  (e: 'error'): void;
}>();

// 当前显示的图片URL
const displaySrc = ref(props.fallback);

// 是否正在加载
const isLoading = ref(false);

/**
 * 检查是否为外部URL
 */
function isExternalUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

/**
 * 加载图片
 */
async function loadImage(url: string) {
  if (!url) {
    displaySrc.value = props.fallback;
    return;
  }
  
  // 检查是否需要代理
  const needProxy = props.useProxy && isExternalUrl(url);
  
  if (needProxy) {
    // 使用代理加载外部图片
    isLoading.value = true;
    
    try {
      const proxyUrl = await loadImageWithProxy(url);
      if (proxyUrl) {
        displaySrc.value = proxyUrl;
        emit('load');
      } else {
        displaySrc.value = props.fallback;
        emit('error');
      }
    } catch (e) {
      console.error('[ProxyImage] 加载失败:', e);
      displaySrc.value = props.fallback;
      emit('error');
    } finally {
      isLoading.value = false;
    }
  } else {
    // 直接使用URL（本地图片或不需要代理）
    displaySrc.value = url;
  }
}

/**
 * 图片加载错误处理
 */
function handleError() {
  console.warn('[ProxyImage] 图片加载失败，使用回退图片');
  displaySrc.value = props.fallback;
  emit('error');
}

// 组件挂载时加载图片
onMounted(() => {
  loadImage(props.src);
});

// 监听src变化
watch(() => props.src, (newSrc) => {
  loadImage(newSrc);
});
</script>

<style lang="scss" scoped>
image.loading {
  /* 可以添加加载动画 */
  opacity: 0.6;
}
</style>
