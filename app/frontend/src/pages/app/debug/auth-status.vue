<template>
  <view class="debug-page">
    <view class="header">
      <text class="title">🔧 认证状态诊断</text>
      <view class="back-btn" @click="goBack">
        <text>返回</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">当前认证状态</text>
      <view class="info-item">
        <text class="label">是否已登录:</text>
        <text :class="['value', authStore.isAuthenticated ? 'success' : 'error']">
          {{ authStore.isAuthenticated ? '✅ 是' : '❌ 否' }}
        </text>
      </view>
      <view class="info-item">
        <text class="label">用户名:</text>
        <text class="value">{{ authStore.user?.username || '无' }}</text>
      </view>
      <view class="info-item">
        <text class="label">用户ID:</text>
        <text class="value">{{ authStore.user?.user_id || '无' }}</text>
      </view>
      <view class="info-item">
        <text class="label">邮箱:</text>
        <text class="value">{{ authStore.user?.email || '无' }}</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">Token信息</text>
      <view class="info-item">
        <text class="label">Store中的Token:</text>
        <text class="value">{{ tokenPreview }}</text>
      </view>
      <view class="info-item">
        <text class="label">Storage中的Token:</text>
        <text class="value">{{ storageTokenPreview }}</text>
      </view>
      <view class="info-item">
        <text class="label">Token一致性:</text>
        <text :class="['value', tokensMatch ? 'success' : 'error']">
          {{ tokensMatch ? '✅ 一致' : '❌ 不一致' }}
        </text>
      </view>
      <view class="info-item">
        <text class="label">Refresh Token:</text>
        <text class="value">{{ refreshTokenPreview }}</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">首次启动标记</text>
      <view class="info-item">
        <text class="label">已显示登录提示:</text>
        <text class="value">{{ hasShownLoginPrompt ? '是' : '否' }}</text>
      </view>
      <view class="info-item">
        <text class="label">登录重定向路径:</text>
        <text class="value">{{ loginRedirectPath || '无' }}</text>
      </view>
    </view>

    <view class="actions">
      <button class="action-btn" @click="refreshStatus">🔄 刷新状态</button>
      <button class="action-btn" @click="testInitAuth">🧪 测试初始化</button>
      <button class="action-btn danger" @click="clearAll">🗑️ 清除所有数据</button>
      <button class="action-btn" @click="printToConsole">📋 输出到控制台</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

const storageToken = ref('');
const refreshToken = ref('');
const hasShownLoginPrompt = ref(false);
const loginRedirectPath = ref('');

const tokenPreview = computed(() => {
  if (!authStore.token) return '无';
  return authStore.token.substring(0, 40) + '...';
});

const storageTokenPreview = computed(() => {
  if (!storageToken.value) return '无';
  return storageToken.value.substring(0, 40) + '...';
});

const refreshTokenPreview = computed(() => {
  if (!refreshToken.value) return '无';
  return refreshToken.value.substring(0, 40) + '...';
});

const tokensMatch = computed(() => {
  if (!authStore.token || !storageToken.value) return false;
  return authStore.token === storageToken.value;
});

const loadStorageData = () => {
  storageToken.value = uni.getStorageSync('jwt_token') || '';
  refreshToken.value = uni.getStorageSync('refresh_token') || '';
  hasShownLoginPrompt.value = uni.getStorageSync('hasShownLoginPrompt') || false;
  loginRedirectPath.value = uni.getStorageSync('loginRedirectPath') || '';
};

const refreshStatus = () => {
  loadStorageData();
  uni.showToast({
    title: '状态已刷新',
    icon: 'success',
    duration: 1000
  });
};

const testInitAuth = async () => {
  console.log('🧪 开始测试初始化认证...');
  await authStore.initializeAuth();
  loadStorageData();
  uni.showToast({
    title: '初始化完成',
    icon: 'success',
    duration: 1000
  });
};

const clearAll = () => {
  uni.showModal({
    title: '确认清除',
    content: '这将清除所有认证数据和标记，确定吗？',
    success: (res) => {
      if (res.confirm) {
        authStore.clearAuth();
        uni.removeStorageSync('refresh_token');
        uni.removeStorageSync('hasShownLoginPrompt');
        uni.removeStorageSync('loginRedirectPath');
        loadStorageData();
        uni.showToast({
          title: '已清除所有数据',
          icon: 'success',
          duration: 1500
        });
      }
    }
  });
};

const printToConsole = () => {
  console.log('═══════════════════════════════════════════════════');
  console.log('🔧 认证状态诊断报告');
  console.log('═══════════════════════════════════════════════════');
  console.log('认证状态:', {
    isAuthenticated: authStore.isAuthenticated,
    user: authStore.user,
    storeToken: authStore.token,
    storageToken: storageToken.value,
    refreshToken: refreshToken.value,
    tokensMatch: tokensMatch.value,
    hasShownLoginPrompt: hasShownLoginPrompt.value,
    loginRedirectPath: loginRedirectPath.value
  });
  console.log('═══════════════════════════════════════════════════');
  
  uni.showToast({
    title: '已输出到控制台',
    icon: 'success',
    duration: 1000
  });
};

const goBack = () => {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/app/tabbar/home/index' });
    }
  });
};

onMounted(() => {
  loadStorageData();
});
</script>

<style lang="scss" scoped>
.debug-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 32rpx;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}

.title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
}

.back-btn {
  padding: 12rpx 24rpx;
  background: #fff;
  border-radius: 8rpx;
  border: 1rpx solid #ddd;
}

.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 24rpx;
  display: block;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
  
  &:last-child {
    border-bottom: none;
  }
}

.label {
  font-size: 28rpx;
  color: #666;
  flex-shrink: 0;
  margin-right: 16rpx;
}

.value {
  font-size: 28rpx;
  color: #333;
  word-break: break-all;
  text-align: right;
  
  &.success {
    color: #52c41a;
    font-weight: bold;
  }
  
  &.error {
    color: #ff4d4f;
    font-weight: bold;
  }
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.action-btn {
  padding: 24rpx;
  background: #1890ff;
  color: #fff;
  border-radius: 12rpx;
  font-size: 32rpx;
  border: none;
  
  &.danger {
    background: #ff4d4f;
  }
  
  &:active {
    opacity: 0.8;
  }
}
</style>
