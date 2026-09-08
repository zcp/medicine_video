<template>

  <view class="custom-tabbar">

    <!-- 首页 -->

    <view 

      class="tab-item"

      :class="{ 'active': current === 0 }"

      @click="handleTabClick(0)"

    >

      <image 

        class="tab-icon" 

        :src="current === 0 ? '/static/tabbar_svg/home-active.svg' : '/static/tabbar_svg/home.svg'" 

        mode="aspectFit"

      />

      <text class="tab-text" :class="{ 'active': current === 0 }">首页</text>

    </view>

    

    <!-- 品牌 -->

    <view 

      class="tab-item"

      :class="{ 'active': current === 1 }"

      @click="handleTabClick(1)"

    >

      <image 

        class="tab-icon" 

        :src="current === 1 ? '/static/tabbar_svg/brand-active.svg' : '/static/tabbar_svg/brand.svg'" 

        mode="aspectFit"

      />

      <text class="tab-text" :class="{ 'active': current === 1 }">品牌</text>

    </view>

    

    <!-- 中间按钮：创建直播（管理员隐藏，统一走全站房间管理） -->
    <template v-if="!authStore.isAdmin">
      <view
        v-if="!flatCenter"
        class="center-tab center-tab--fab"
        @click="handleCenterClick"
      >
        <view class="center-button">
          <text class="center-icon-plus">+</text>
        </view>
      </view>
      <view
        v-else
        class="tab-item center-tab center-tab--flat"
        @click="handleCenterClick"
      >
        <text class="center-icon-plus center-icon-flat">+</text>
        <text class="tab-text">发起</text>
      </view>
    </template>

    

    <!-- 专家 -->

    <view 

      class="tab-item"

      :class="{ 'active': current === 2 }"

      @click="handleTabClick(2)"

    >

      <image 

        class="tab-icon" 

        :src="current === 2 ? '/static/tabbar_svg/expert-active.svg' : '/static/tabbar_svg/expert.svg'" 

        mode="aspectFit"

      />

      <text class="tab-text" :class="{ 'active': current === 2 }">专家</text>

    </view>

    

    <!-- 我的 -->

    <view 

      class="tab-item"

      :class="{ 'active': current === 3 }"

      @click="handleTabClick(3)"

    >

      <image 

        class="tab-icon" 

        :src="current === 3 ? '/static/tabbar_svg/my-active.svg' : '/static/tabbar_svg/my.svg'" 

        mode="aspectFit"

      />

      <text class="tab-text" :class="{ 'active': current === 3 }">我的</text>

    </view>

  </view>

</template>



<script setup lang="ts">

import { onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();



// 隐藏原生 TabBar

onMounted(() => {

  uni.hideTabBar({

    animation: false

  });

});



const props = withDefaults(
  defineProps<{
    current: number; // 0=首页, 1=品牌, 2=专家, 3=我的
    /** 为 true 时中间按钮降级为普通 tab（不凸起），避免平台裁切问题 */
    flatCenter?: boolean;
  }>(),
  { flatCenter: false }
);



// Tab 页面路径映射

const tabPaths = [

  '/pages/app/tabbar/home/index',      // 0: 首页

  '/pages/app/tabbar/brand/index',     // 1: 品牌

  '/pages/app/tabbar/expert/index',    // 2: 专家

  '/pages/app/tabbar/my/index'         // 3: 我的

];



/**

 * 处理普通 Tab 点击

 */

function handleTabClick(index: number) {

  if (props.current === index) {

    return; // 已在当前页面，不重复跳转

  }

  

  // 使用 switchTab 跳转

  uni.switchTab({

    url: tabPaths[index],

    fail: (err) => {

      console.error('TabBar 跳转失败:', err);

    }

  });

}



/**

 * 处理中间按钮点击（创建直播）

 */

function handleCenterClick() {

  // 双保险：管理员无创建入口（模板 v-if 之外再兜一道）
  if (authStore.isAdmin) {
    return;
  }

  if (!authStore.isAuthenticated) {

    uni.showToast({ title: '登录后才能使用更多服务和功能', icon: 'none' });

    return;

  }

  

  uni.navigateTo({

    url: '/pages/app/live-manage/create',

    fail: (err) => {

      console.error('创建直播页跳转失败:', err);

      uni.showToast({ title: '页面打开失败，请稍后重试', icon: 'none' });

    }

  });

}

</script>



<style scoped>

.custom-tabbar {

  position: fixed;

  bottom: 0;

  left: 0;

  right: 0;

  /* 精确高度：112rpx = 56px @ 375px屏，内容区确定不变动 */
  height: 112rpx;

  /* safe-area 下方扩展，不压缩内容区 */
  padding-bottom: env(safe-area-inset-bottom);

  background-color: #ffffff;

  display: flex;

  align-items: center;

  justify-content: space-around;

  /* 微弱上边阴影代替硬边框，层次感更自然 */
  box-shadow: 0 -1rpx 0 rgba(17, 24, 39, 0.08);

  z-index: 999;

  overflow: hidden;

}



/* 统一 TabBar 规范：icon 48rpx、icon 与文字间距 8rpx、文案 24rpx/1.2，与 B 站风格一致 */
.tab-item {

  flex: 1;

  display: flex;

  flex-direction: column;

  align-items: center;

  justify-content: center;

  height: 112rpx;

  padding-top: 18rpx;

  padding-bottom: 10rpx;

  box-sizing: border-box;

  position: relative;

}



.tab-icon {

  width: 48rpx;

  height: 48rpx;

  flex-shrink: 0;

  margin-bottom: 6rpx;

}



.tab-text {

  font-size: 22rpx;

  line-height: 1.2;

  color: var(--home-tabbar-inactive);

}
.tab-text.active {

  font-size: 24rpx;

  font-weight: 500;

  color: var(--home-primary);

}



/* 中间槽位：内嵌扁平胶囊，与左右 tab 同线，无凸起无阴影 */
.center-tab--fab {
  flex: 1;
  height: 112rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.center-tab--fab .center-button {
  /* 胶囊形色块：宽高比 1.75:1，高度约占 112rpx 的 54%，严禁溢出 */
  width: 108rpx;
  height: 60rpx;
  background: var(--home-primary);
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}
.center-tab--fab .center-icon-plus {
  display: block;
  font-size: 40rpx;
  line-height: 1;
  color: #ffffff;
  font-weight: 400;
  text-align: center;
}
/* 降级方案：中间为普通 tab，不凸起 */
.center-tab--flat {
  position: relative;
  flex: 1;
  pointer-events: auto;
  overflow: visible;
}
.center-icon-flat {
  display: block;
  width: 48rpx;
  height: 48rpx;
  line-height: 48rpx;
  font-size: 40rpx;
  text-align: center;
  color: var(--home-primary);
  font-weight: 300;
  margin-bottom: 8rpx;
}
.center-tab--flat .tab-text {
  color: var(--home-tabbar-inactive);
}
.center-tab--flat:active .tab-text {
  color: var(--home-primary);
}

</style>

