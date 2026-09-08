<template>
  <text 
    class="app-icon iconfont" 
    :class="[iconClass, colorClass]"
    :style="iconStyle"
    @click="handleClick"
  />
</template>

<script setup lang="ts">
/**
 * 通用图标组件
 * @description 封装 iconfont 图标，支持自定义大小和颜色
 * 
 * @example
 * <AppIcon name="home" />
 * <AppIcon name="user" size="48" color="#1890ff" />
 * <AppIcon name="star" size="40rpx" color="primary" />
 */
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  /** 图标名称（不含 icon- 前缀） */
  name: string;
  /** 图标大小，支持数字(rpx)或字符串 */
  size?: number | string;
  /** 图标颜色，支持预设色名或自定义色值 */
  color?: string;
}>(), {
  size: 32,
  color: '',
});

const emit = defineEmits<{
  (e: 'click', event: Event): void;
}>();

/** 图标类名 */
const iconClass = computed(() => `icon-${props.name}`);

/** 预设颜色映射 */
const colorMap: Record<string, string> = {
  primary: '#509cec',
  success: '#28a745',
  warning: '#ffc107',
  danger: '#dc3545',
  info: '#6c757d',
  gray: '#999999',
  white: '#ffffff',
  black: '#333333',
};

/** 颜色类名（用于预设颜色） */
const colorClass = computed(() => {
  if (props.color && colorMap[props.color]) {
    return `app-icon--${props.color}`;
  }
  return '';
});

/** 图标样式 */
const iconStyle = computed(() => {
  const style: Record<string, string> = {};
  
  // 处理大小
  if (typeof props.size === 'number') {
    style.fontSize = `${props.size}rpx`;
  } else if (props.size) {
    style.fontSize = props.size;
  }
  
  // 处理自定义颜色
  if (props.color && !colorMap[props.color]) {
    style.color = props.color;
  }
  
  return style;
});

/** 点击处理 */
const handleClick = (event: Event) => {
  emit('click', event);
};
</script>

<style lang="scss" scoped>
.app-icon {
  display: inline-block;
  line-height: 1;
  vertical-align: middle;
  
  // 预设颜色
  &--primary { color: #509cec; }
  &--success { color: #28a745; }
  &--warning { color: #ffc107; }
  &--danger { color: #dc3545; }
  &--info { color: #6c757d; }
  &--gray { color: #999999; }
  &--white { color: #ffffff; }
  &--black { color: #333333; }
}
</style>
