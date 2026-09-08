<template>
  <image
    :src="avatarSrc"
    :mode="mode"
    :style="imgStyle"
    @error="handleError"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { loadImageWithProxy } from '@/utils/imageProxy';

const DEFAULT_AVATAR = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1zaXplPSIxNCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzk5OSI+5rOo5YyI5aS06LGhPC90ZXh0Pjwvc3ZnPg==';

const props = withDefaults(defineProps<{
  src?: string | null;
  mode?: string;
  shape?: 'circle' | 'square';
  size?: string;
}>(), {
  mode: 'aspectFill',
  shape: 'circle',
  size: '72rpx'
});

const avatarSrc = ref(DEFAULT_AVATAR);

const imgStyle = computed(() => ({
  width: props.size,
  height: props.size,
  borderRadius: props.shape === 'circle' ? '50%' : '8rpx',
  flexShrink: '0',
  backgroundColor: '#eeeeee'
}));

async function loadAvatar(url: string | null | undefined) {
  if (!url) {
    avatarSrc.value = DEFAULT_AVATAR;
    return;
  }
  const isExternal = /^https?:\/\//i.test(url);
  if (isExternal) {
    avatarSrc.value = DEFAULT_AVATAR;
    try {
      const proxied = await loadImageWithProxy(url);
      if (proxied) {
        avatarSrc.value = proxied;
      }
    } catch {
      // keep DEFAULT_AVATAR
    }
  } else {
    avatarSrc.value = url;
  }
}

onMounted(() => loadAvatar(props.src));
watch(() => props.src, loadAvatar);

function handleError() {
  if (avatarSrc.value !== DEFAULT_AVATAR) {
    avatarSrc.value = DEFAULT_AVATAR;
  }
}
</script>
