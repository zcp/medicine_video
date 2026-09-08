<template>
  <view class="crop-page">
    <!-- B站风格：无标题栏，简洁说明 -->
    <view class="crop-header">
      <text class="crop-title">移动和缩放图片</text>
    </view>

    <view
      class="crop-stage"
      :style="stageStyle"
      @touchstart="handleTouchStart"
      @touchmove.prevent="handleTouchMove"
      @touchend="handleTouchEnd"
      @touchcancel="handleTouchEnd"
    >
      <image
        v-if="imageSrc"
        class="crop-image"
        :src="imageSrc"
        mode="aspectFill"
        :style="imageStyle"
        @load="handleImageLoad"
        @error="handleImageError"
      />

      <view class="crop-overlay">
        <view class="crop-ring" :style="ringStyle" />
      </view>
    </view>

    <view class="action-bar">
      <button class="btn btn--ghost" :disabled="saving" @tap="handleCancel">取消</button>
      <button class="btn btn--primary" :disabled="saving || !imageReady" @tap="handleConfirm">
        {{ saving ? '处理中…' : '确认裁剪' }}
      </button>
    </view>

    <canvas canvas-id="avatar-crop-canvas" class="hidden-canvas" />

    <AvatarPreview v-model:visible="previewVisible" :src="previewSrc" />
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import AvatarPreview from '@/components/shared/AvatarPreview.vue';
import { uploadAvatar } from '@/api/auth';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

const previewVisible = ref(false);
const previewSrc = ref('');
const imageSrc = ref('');
const saving = ref(false);
const imageReady = ref(false);
const imageWidth = ref(0);
const imageHeight = ref(0);
const stageWidth = ref(0);
const stageHeight = ref(0);
const cropSize = ref(0);
const scale = ref(1);
const minScale = ref(1);
const maxScale = ref(3);
const offsetX = ref(0);
const offsetY = ref(0);
const startX = ref(0);
const startY = ref(0);
const dragging = ref(false);
const touchStartDistance = ref(0);
const touchStartScale = ref(1);
const lastValidOffsetX = ref(0);
const lastValidOffsetY = ref(0);
const lastValidScale = ref(1);

const stageStyle = computed(() => ({
  width: `${stageWidth.value}px`,
  height: `${stageHeight.value}px`,
}));

const imageStyle = computed(() => ({
  width: imageWidth.value ? `${imageWidth.value * scale.value}px` : 'auto',
  height: imageHeight.value ? `${imageHeight.value * scale.value}px` : 'auto',
  transform: `translate(calc(-50% + ${offsetX.value}px), calc(-50% + ${offsetY.value}px))`,
}));

const ringStyle = computed(() => ({
  width: `${cropSize.value}px`,
  height: `${cropSize.value}px`,
}));

onLoad((query) => {
  const src = decodeURIComponent((query?.src as string) || '');
  console.log('[avatar-crop] onLoad', { query, src });
  imageSrc.value = src;
  previewSrc.value = src;
});

onMounted(() => {
  const sys = uni.getSystemInfoSync();
  stageWidth.value = sys.windowWidth;
  stageHeight.value = Math.floor(sys.windowHeight * 0.62);
  cropSize.value = Math.min(Math.floor(sys.windowWidth * 0.72), 520);
  console.log('[avatar-crop] mounted', { stageWidth: stageWidth.value, stageHeight: stageHeight.value, cropSize: cropSize.value });
});

function handleImageLoad(e: any) {
  const { width, height } = e.detail;
  console.log('[avatar-crop] image load', { width, height });
  imageWidth.value = width;
  imageHeight.value = height;
  imageReady.value = true;

  const baseScale = Math.max(cropSize.value / width, cropSize.value / height);
  minScale.value = Number((baseScale * 1.05).toFixed(2));
  scale.value = minScale.value;
  maxScale.value = Number((minScale.value * 3).toFixed(2));
  offsetX.value = 0;
  offsetY.value = 0;
  commitCurrentState();
  console.log('[avatar-crop] init scale', { baseScale, minScale: minScale.value, maxScale: maxScale.value });
}

function handleImageError(err: any) {
  console.error('[avatar-crop] image error', err);
  uni.showToast({ title: '图片加载失败', icon: 'none' });
}

function handleTouchStart(e: any) {
  if (e.touches.length === 1) {
    dragging.value = true;
    startX.value = e.touches[0].clientX;
    startY.value = e.touches[0].clientY;
    console.log('[avatar-crop] touch drag start', { startX: startX.value, startY: startY.value });
  } else if (e.touches.length === 2) {
    dragging.value = false;
    touchStartDistance.value = getDistance(e.touches[0], e.touches[1]);
    touchStartScale.value = scale.value;
    console.log('[avatar-crop] touch pinch start', { distance: touchStartDistance.value, scale: touchStartScale.value });
  }
}

function handleTouchMove(e: any) {
  if (e.touches.length === 1 && dragging.value) {
    const currentX = e.touches[0].clientX;
    const currentY = e.touches[0].clientY;
    offsetX.value += currentX - startX.value;
    offsetY.value += currentY - startY.value;
    startX.value = currentX;
    startY.value = currentY;
  } else if (e.touches.length === 2) {
    const distance = getDistance(e.touches[0], e.touches[1]);
    if (!touchStartDistance.value) return;
    const nextScale = touchStartScale.value * (distance / touchStartDistance.value);
    scale.value = Math.min(maxScale.value, Math.max(minScale.value, Number(nextScale.toFixed(2))));
  }
}

function handleTouchEnd() {
  dragging.value = false;
  clampAndCommitState();
}

function clampAndCommitState() {
  clampOffset();
  commitCurrentState();
}

function commitCurrentState() {
  lastValidOffsetX.value = offsetX.value;
  lastValidOffsetY.value = offsetY.value;
  lastValidScale.value = scale.value;
}

function clampOffset() {
  const displayW = imageWidth.value * scale.value;
  const displayH = imageHeight.value * scale.value;
  const limitX = Math.max(0, (displayW - cropSize.value) / 2);
  const limitY = Math.max(0, (displayH - cropSize.value) / 2);

  if (displayW < cropSize.value || displayH < cropSize.value) {
    offsetX.value = 0;
    offsetY.value = 0;
    return;
  }

  offsetX.value = Math.min(limitX, Math.max(-limitX, offsetX.value));
  offsetY.value = Math.min(limitY, Math.max(-limitY, offsetY.value));
}

function getDistance(a: any, b: any) {
  const dx = a.clientX - b.clientX;
  const dy = a.clientY - b.clientY;
  return Math.sqrt(dx * dx + dy * dy);
}

function handleCancel() {
  uni.navigateBack();
}

async function handleConfirm() {
  if (saving.value || !imageReady.value) return;
  saving.value = true;
  uni.showLoading({ title: '裁剪中…', mask: true });
  
  console.log('═══════════════════════════════════════════════════');
  console.log('[avatar-crop] 🔧 确认裁剪 - 开始流程');
  console.log('[avatar-crop] 📐 当前裁剪参数:', {
    scale: scale.value,
    offsetX: offsetX.value,
    offsetY: offsetY.value,
    imageWidth: imageWidth.value,
    imageHeight: imageHeight.value,
    cropSize: cropSize.value
  });
  
  try {
    console.log('[avatar-crop] 📸 步骤1: 导出裁剪图片...');
    const tempFile = await exportCroppedImage();
    console.log('[avatar-crop] ✅ 步骤1完成 - 裁剪文件:', tempFile);
    if (!tempFile) throw new Error('裁剪结果为空');

    previewSrc.value = tempFile;
    previewVisible.value = true;

    console.log('[avatar-crop] 📤 步骤2: 上传头像到服务器...');
    console.log('[avatar-crop] 📤 上传参数:', {
      filePath: tempFile,
      fileType: typeof tempFile,
      fileLength: tempFile?.length || 'unknown'
    });
    const uploadRes = await uploadAvatar(tempFile);
    console.log('[avatar-crop] ✅ 步骤2完成 - 上传响应:', JSON.stringify(uploadRes));
    
    const avatarUrl = uploadRes.data?.avatar_url;
    if (!avatarUrl) {
      console.error('[avatar-crop] ❌ 上传响应中缺少 avatar_url');
      console.error('[avatar-crop] ❌ 响应数据:', uploadRes);
      throw new Error('头像上传失败：服务器未返回头像地址');
    }
    console.log('[avatar-crop] 📍 获取到 avatar_url:', avatarUrl);

    // 后端 POST /me/avatar 已自动写库（update_profile），无需再调 updateProfile 二次写入
    // （预防后端 PATCH /me 收紧为 nickname/bio 后头像功能不受影响）

    console.log('[avatar-crop] 🔄 步骤3: 刷新用户信息...');
    await authStore.fetchUserProfile();
    console.log('[avatar-crop] ✅ 步骤3完成 - 当前头像:', authStore.user?.avatar);
    
    uni.showToast({ title: '头像已更新', icon: 'success' });
    console.log('═══════════════════════════════════════════════════');
    setTimeout(() => uni.navigateBack(), 500);
  } catch (error: any) {
    console.error('═══════════════════════════════════════════════════');
    console.error('[avatar-crop] ❌ 裁剪流程失败');
    console.error('[avatar-crop] ❌ 错误类型:', error?.constructor?.name);
    console.error('[avatar-crop] ❌ 错误消息:', error?.message);
    console.error('[avatar-crop] ❌ 完整错误:', error);
    if (error?.statusCode) {
      console.error('[avatar-crop] ❌ HTTP状态码:', error.statusCode);
    }
    if (error?.data) {
      console.error('[avatar-crop] ❌ 服务器响应:', error.data);
    }
    console.error('═══════════════════════════════════════════════════');
    
    // 回到最近一次合法状态
    offsetX.value = lastValidOffsetX.value;
    offsetY.value = lastValidOffsetY.value;
    scale.value = lastValidScale.value;
    uni.showToast({ title: error?.message || '裁剪失败，请重试', icon: 'none' });
  } finally {
    uni.hideLoading();
    saving.value = false;
  }
}

function exportCroppedImage(): Promise<string> {
  return new Promise((resolve, reject) => {
    const outputSize = 600;

    // ===== 核心：以圆形区域直径为边长，截取正方形区域 =====
    // B站实现原理：
    // 1. 预览时显示圆形遮罩（用户看到的是圆形）
    // 2. 实际截取时，以圆心为中心、圆直径为边长，截取一个正方形
    // 3. 显示时用 CSS border-radius:50% 裁剪为圆形
    // 4. 点击预览时展示完整的正方形图片

    // 计算缩放后的图片在 stage 上的位置
    const displayW = imageWidth.value * scale.value;
    const displayH = imageHeight.value * scale.value;
    const stageCenterX = stageWidth.value / 2;
    const stageCenterY = stageHeight.value / 2;
    const imageLeft = stageCenterX - displayW / 2 + offsetX.value;
    const imageTop = stageCenterY - displayH / 2 + offsetY.value;

    // 圆心在原始图片上的坐标（未缩放）
    const centerOnImageX = (stageCenterX - imageLeft) / scale.value;
    const centerOnImageY = (stageCenterY - imageTop) / scale.value;

    // 正方形边长（原始图片坐标系）= 圆直径 / 缩放比例
    const sourceSize = cropSize.value / scale.value;

    // 正方形左上角（原始图片坐标系）
    const sx = centerOnImageX - sourceSize / 2;
    const sy = centerOnImageY - sourceSize / 2;

    console.log('[avatar-crop] 📐 B站模式裁剪参数:', {
      outputSize,
      displayW, displayH,
      imageLeft, imageTop,
      centerOnImageX, centerOnImageY,
      sourceSize,
      sx, sy,
      scale: scale.value,
      offsetX: offsetX.value,
      offsetY: offsetY.value
    });

    const ctx = uni.createCanvasContext('avatar-crop-canvas');

    // 先填充黑色背景（处理图片无法覆盖全部正方形区域的情况）
    ctx.setFillStyle('#000000');
    ctx.fillRect(0, 0, outputSize, outputSize);

    // 将正方形区域绘制到整个 canvas 上（完全填充 outputSize x outputSize）
    ctx.drawImage(
      imageSrc.value,
      sx,
      sy,
      sourceSize,
      sourceSize,
      0,           // dx: canvas 左上角
      0,           // dy: canvas 左上角
      outputSize,  // dWidth: 填满整个 canvas
      outputSize   // dHeight: 填满整个 canvas
    );

    ctx.draw(false, () => {
      uni.canvasToTempFilePath({
        canvasId: 'avatar-crop-canvas',
        width: outputSize,
        height: outputSize,
        destWidth: outputSize,
        destHeight: outputSize,
        success: (res) => {
          console.log('[avatar-crop] canvas export success', res.tempFilePath);
          resolve(res.tempFilePath);
        },
        fail: (err) => {
          console.error('[avatar-crop] canvas export fail', err);
          reject(err);
        },
      });
    });
  });
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.crop-page {
  min-height: 100vh;
  background: $color-surface-dark;
  padding: $spacing-xl $spacing-lg $spacing-2xl;
  box-sizing: border-box;
}

.crop-header {
  padding-bottom: $spacing-lg;
  color: $color-text-on-dark-secondary;
}

.crop-title {
  display: block;
  font-size: $font-sm;
  color: $color-text-on-dark-secondary;
  text-align: center;
}

.crop-stage {
  position: relative;
  margin: 0 auto;
  overflow: hidden;
  border-radius: $radius-2xl;
  background: radial-gradient(circle at center, rgba(15, 23, 42, 0.4) 0%, #000 100%);
  box-shadow: inset 0 0 0 1rpx $color-border-ring-on-dark;
}

.crop-image {
  position: absolute;
  left: 50%;
  top: 50%;
  transform-origin: center center;
  will-change: transform;
}

.crop-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

// B站风格：纯白圆环 + 深色遮罩（0.65 不透明度），无十字线
.crop-ring {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 4rpx solid rgba(255, 255, 255, 0.96);
  box-shadow: 0 0 0 9999rpx rgba(0, 0, 0, 0.65), 0 0 0 12rpx rgba(255, 255, 255, 0.06) inset;
}

.action-bar {
  display: flex;
  gap: $spacing-md;
  margin-top: $spacing-xl;
}

.btn {
  flex: 1;
  height: $touch-target-min;
  border-radius: 44rpx;
  font-size: $font-lg;
  font-weight: 600;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity $motion-fast, transform $motion-fast;

  &--ghost {
    background: $color-surface-ghost-on-dark;
    color: $color-text-on-dark;

    &:active {
      opacity: 0.7;
      transform: scale(0.97);
    }
  }

  &--primary {
    background: $color-primary;
    color: $color-text-white;

    &:active {
      opacity: 0.88;
      transform: scale(0.97);
    }

    &[disabled] {
      opacity: 0.5;
      transform: none;
    }
  }
}

.hidden-canvas {
  position: fixed;
  left: -9999px;
  top: -9999px;
  width: 600px;
  height: 600px;
}
</style>
