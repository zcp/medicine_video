<template>
  <!-- uni-app中App.vue不需要template内容 -->
</template>

<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { getCurrentInstance } from "vue";
import logger from '@/utils/logger';
import { checkClipboardForInvite } from '@/utils/clipboardShare';
import { getRoomDetail, getMyRooms } from '@/api/room';
import { useAuthStore } from '@/store/auth';

// #ifndef H5
import { setupRouteGuards } from '@/utils/routeGuard';
// #endif

// 私密房邀请：剪贴板检测节流阈值（回前台距上次读取 >30s 才再读，控制 iOS 剪贴板系统提示频次）
const CLIPBOARD_CHECK_THROTTLE_MS = 30_000;
const CLIPBOARD_LAST_CHECK_KEY = 'private_room_invite_last_check';

/**
 * 私密房邀请：读取剪贴板 → 命中 → 弹窗确认 → 进入 LiveView
 * 观看不限制登录（匿名可看，V1.1 决策 D4）；任何失败静默
 * 仅 App 端生效（onShow 调用处 #ifdef APP-PLUS）
 */
async function checkClipboardInvite(): Promise<void> {
  try {
    // 节流：冷启动（无记录）必读；回前台距上次读取 >30s 才读
    const now = Date.now();
    const lastCheck = Number(uni.getStorageSync(CLIPBOARD_LAST_CHECK_KEY) || 0);
    if (now - lastCheck < CLIPBOARD_CHECK_THROTTLE_MS) return;
    uni.setStorageSync(CLIPBOARD_LAST_CHECK_KEY, now);

    const roomId = await checkClipboardForInvite();
    if (!roomId) return;

    // 取房间标题（404/失败静默不弹）；并判断是否房主自己的房间
    let title = '私密直播间';
    try {
      const res = await getRoomDetail(roomId);
      if (!res?.data) return; // 房间不存在 → 不弹
      if (res.data.title) title = res.data.title;

      // 房主自己的房间不弹窗（自己知晓该房间，通过"我的直播"进入即可；2026-08-11 联调反馈）
      const authStore = useAuthStore();
      if (authStore.isAuthenticated) {
        try {
          const myRes = await getMyRooms({ page: 1, size: 100 });
          const myIds = (myRes?.data?.items || []).map((r: any) => r.id);
          if (myIds.includes(roomId)) return;
        } catch {
          /* 查询失败按非房主处理（照常弹窗） */
        }
      }
    } catch {
      return; // 标题获取失败（404 等）→ 静默不弹
    }

    uni.showModal({
      title: '私密直播间邀请',
      content: `检测到私密直播间邀请，是否进入「${title}」？`,
      confirmText: '进入',
      cancelText: '取消',
      success: (r) => {
        if (r.confirm) {
          // 会话级标记已在 checkClipboardForInvite 内完成（本会话不再提示；杀 App 重开可再进入）
          uni.navigateTo({ url: `/pages/app/live/LiveView?roomId=${roomId}` });
        }
      },
    });
  } catch {
    /* 全程静默：不影响 App 正常启动/回前台 */
  }
}

onLaunch(() => {
  console.log("App Launch");
  
  // #ifndef H5
  // 安装路由守卫（仅 App/小程序，H5 端由 AdminLayout 自行管理）
  setupRouteGuards();
  // #endif
  
  // 零阶段：设置Vue全局错误处理器（作为uni.onError的补充）
  const instance = getCurrentInstance();
  const app = instance?.appContext.app;
  if (app) {
    app.config.errorHandler = (err: any, instance: any, info: string) => {
      logger.error('VueError', 'Vue组件异常', {
        error: err?.message || String(err),
        stack: err?.stack,
        componentName: instance?.$options?.name || 'Unknown',
        errorInfo: info
      });
    };
  }
});

onShow(() => {
  console.log("App Show");
  // #ifdef APP-PLUS
  checkClipboardInvite();
  // #endif
});

onHide(() => {
  console.log("App Hide");
});
</script>

<style lang="scss">
/* 注意：uni.scss 已通过 vite.config.js 全局注入，无需在此处 @import */

/* 全局引入 iconfont 图标字体 */
@import '@/static/fonts/iconfont.css';

#app {
  width: 100%;
  height: 100vh;
}

.app-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
