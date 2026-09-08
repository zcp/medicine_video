<template>
  <view class="user-info-header">
    <view class="user-info-header__content">
      <view class="user-info-header__logo">
        <text class="user-info-header__title">{{ appTitle }}</text>
      </view>
      
      <view class="user-info-header__user" v-if="isAuthenticated">
        <view class="user-info-header__avatar" @click="toggleDropdown">
          <!-- 如果没有头像，显示用户图标 -->
          <image 
            v-if="user?.avatar" 
            :src="user.avatar" 
            class="user-info-header__avatar-img"
            mode="aspectFill"
          />
          <!-- 默认显示用户图标 -->
          <view v-else class="user-info-header__avatar-icon"><text class="iconfont icon-my"></text></view>
        </view>
        
        <view class="user-info-header__dropdown" v-if="showDropdown">
          <view class="user-info-header__dropdown-item" @click="goToProfile">
            <text class="user-info-header__dropdown-text">个人信息</text>
          </view>
          <view class="user-info-header__dropdown-item" @click="goToHome">
            <text class="user-info-header__dropdown-text">主页</text>
          </view>
          <view class="user-info-header__dropdown-divider"></view>
          <view class="user-info-header__dropdown-item" @click="handleLogout">
            <text class="user-info-header__dropdown-text logout">退出登录</text>
          </view>
        </view>
      </view>
      
      <!-- 未认证时显示登录提示 -->
      <view class="user-info-header__login-prompt" v-else>
        <text class="user-info-header__login-text">请登录</text>
        <view class="user-info-header__login-icon">🔐</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import { APP_TITLE } from '@/constants/api';

const authStore = useAuthStore();
const showDropdown = ref(false);
const defaultAvatar = '/static/default-avatar.png';

const appTitle = computed(() => APP_TITLE);
const isAuthenticated = computed(() => authStore.isAuthenticated);
const user = computed(() => authStore.user);

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

const goToProfile = () => {
  showDropdown.value = false;
  authStore.goToUserService('/pages/user/profile');
};

const goToHome = () => {
  showDropdown.value = false;
  authStore.goToUserService('/pages/index/index');
};

const handleLogout = () => {
  showDropdown.value = false;
  authStore.logout();
};

// 点击外部关闭下拉菜单
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.user-info-header__user')) {
    showDropdown.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped lang="scss">
.user-info-header {
  background-color: var(--nav-bg-color, #ffffff);
  border-bottom: 1px solid var(--border-color, #e5e5e5);
  padding: 0 var(--spacing-md, 16px);
  height: 60px;
  display: flex;
  align-items: center;
  position: relative;
  z-index: 100;

  &__content {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__logo {
    display: flex;
    align-items: center;
  }

  &__title {
    font-size: var(--font-size-lg, 18px);
    font-weight: 600;
    color: var(--text-color-primary, #333333);
  }

  &__user {
    position: relative;
    display: flex;
    align-items: center;
  }

  &__avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    overflow: hidden;
    cursor: pointer;
    border: 3px solid var(--primary-color, #007bff);
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);

    &:hover {
      border-color: var(--primary-color-hover, #0056b3);
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
    }
  }

  &__avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &__avatar-icon {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: var(--primary-color, #007bff);
    background-color: var(--bg-color-light, #f8f9fa);
    border-radius: 50%;
  }

  &__dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    background-color: var(--nav-bg-color, #ffffff);
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: var(--border-radius-base, 4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    min-width: 160px;
    z-index: 1000;
    margin-top: 8px;
  }

  &__dropdown-item {
    padding: var(--spacing-sm, 8px) var(--spacing-md, 16px);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: var(--bg-color-hover, #f5f5f5);
    }
  }

  &__dropdown-text {
    font-size: var(--font-size-base, 14px);
    color: var(--text-color-primary, #333333);

    &.logout {
      color: var(--danger-color, #dc3545);
    }
  }

  &__dropdown-divider {
    height: 1px;
    background-color: var(--border-color, #e5e5e5);
    margin: var(--spacing-xs, 4px) 0;
  }

  &__login-prompt {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 4px);
    padding: var(--spacing-sm, 8px) var(--spacing-md, 16px);
    background-color: var(--warning-color, #ffc107);
    border-radius: var(--border-radius-base, 4px);
    cursor: pointer;
    transition: background-color 0.2s ease;

    &:hover {
      background-color: var(--warning-color-hover, #e0a800);
    }
  }

  &__login-text {
    font-size: var(--font-size-sm, 12px);
    color: var(--text-color-inverse, #ffffff);
    font-weight: 500;
  }

  &__login-icon {
    font-size: var(--font-size-sm, 12px);
  }
}

/* 响应式适配 */
@media (max-width: 768px) {
  .user-info-header {
    padding: 0 var(--spacing-sm, 12px);
    height: 50px;

    &__title {
      font-size: var(--font-size-base, 16px);
    }

    &__avatar {
      width: 44px;
      height: 44px;
    }
  }
}
</style>
