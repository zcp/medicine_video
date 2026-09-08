<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { logger } from '@/logs/logger'
import { useAuthStore } from '@/store/auth'

// Pinia在main.ts中已配置，这里只需要导入即可

onLaunch((options) => {
  try {
    // #ifdef MP-WEIXIN
    if (typeof wx !== 'undefined' && typeof (wx as any).onUnhandledRejection === 'function') {
      ;(wx as any).onUnhandledRejection((res: any) => {
        const reason = res?.reason
        const text =
          reason instanceof Error
            ? `${reason.name}: ${reason.message}`
            : typeof reason === 'string'
              ? reason
              : (() => {
                  try {
                    return JSON.stringify(reason)
                  } catch {
                    return String(reason)
                  }
                })()
        logger.warn('system', '未处理的 Promise 异常', { reason: text })
      })
    }
    // #endif

    logger.info('system', '应用启动', {
      path: (options as any)?.path,
      query: (options as any)?.query,
      timestamp: new Date().toISOString()
    })

    // 恢复登录态（小程序/H5通用）
    useAuthStore().restoreAuth()
    
    // 应用启动时的初始化逻辑
    initApp()
  } catch (error) {
    const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error)
    console.error('应用启动失败:', message)
    logger.error('system', '应用启动失败', error as any)
  }
})

onShow((options) => {
  logger.info('system', '应用切换到前台', { options })
  
  // 应用切换到前台时的逻辑
  handleAppShow()
})

onHide(() => {
  logger.info('system', '应用切换到后台')
  
  // 应用切换到后台时的逻辑
  handleAppHide()
})

/**
 * 应用初始化
 */
function initApp() {
  // 检查应用版本更新
  checkAppUpdate()
  
  // 初始化全局配置
  initGlobalConfig()
  
  // 设置状态栏
  setStatusBar()
}

/**
 * 检查应用更新
 */
function checkAppUpdate() {
  // #ifdef MP-WEIXIN
  const updateManager = uni.getUpdateManager()
  
  updateManager.onCheckForUpdate((res) => {
    console.log('检查更新:', res.hasUpdate)
  })
  
  updateManager.onUpdateReady(() => {
    uni.showModal({
      title: '更新提示',
      content: '新版本已经准备好，是否重启应用？',
      success: (res) => {
        if (res.confirm) {
          updateManager.applyUpdate()
        }
      }
    })
  })
  
  updateManager.onUpdateFailed(() => {
    uni.showModal({
      title: '更新失败',
      content: '新版本下载失败，请检查网络后重试',
      showCancel: false
    })
  })
  // #endif
}

/**
 * 初始化全局配置
 */
function initGlobalConfig() {
  // 设置全局错误处理
  // #ifdef APP-PLUS
  plus.screen.lockOrientation('portrait-primary')
  // #endif
  
  // #ifdef H5
  // H5平台特定配置
  document.title = '医学直播平台'
  // #endif
}

/**
 * 设置状态栏
 */
function setStatusBar() {
  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync()
  if (systemInfo.platform === 'ios') {
    uni.setNavigationBarColor({
      frontColor: '#000000',
      backgroundColor: '#ffffff'
    })
  }
  // #endif
}

/**
 * 应用切换到前台
 */
function handleAppShow() {
  // 刷新token有效性
  checkTokenValidity()
  
  // 检查网络状态
  checkNetworkStatus()
}

/**
 * 应用切换到后台
 */
function handleAppHide() {
  // 保存应用状态
  saveAppState()
}

/**
 * 检查Token有效性
 */
function checkTokenValidity() {
  const authStore = useAuthStore()
  if (!authStore.clearAuthIfExpired()) return
  uni.reLaunch({ url: '/pages/auth/OneTapLogin' })
}

/**
 * 检查网络状态
 */
function checkNetworkStatus() {
  uni.getNetworkType({
    success: (res) => {
      if (res.networkType === 'none') {
        uni.showToast({
          title: '网络连接异常',
          icon: 'none',
          duration: 2000
        })
      }
    }
  })
}

/**
 * 保存应用状态
 */
function saveAppState() {
  const appState = {
    lastActiveTime: Date.now(),
    version: '1.0.0'
  }
  uni.setStorageSync('app_state', appState)
}
</script>

<style lang="scss">
@use '@/common/uni.scss';
@import '@/static/iconfont/iconfont.css';

// 全局样式重置
page {
  background-color: var(--color-background);
  color: var(--color-text-primary);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
}

// 全局滚动条样式 (H5)
/* #ifdef H5 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background-color: var(--color-border);
  
  &:hover {
    background-color: var(--color-text-secondary);
  }
}

::-webkit-scrollbar-track {
  background-color: transparent;
}
/* #endif */

// 全局动画类
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-base) var(--ease-in-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active {
  transition: transform var(--duration-base) var(--ease-in-out);
}

.slide-up-enter-from {
  transform: translateY(100%);
}

.slide-up-leave-active {
  transition: transform var(--duration-base) var(--ease-in-out);
}

.slide-up-leave-to {
  transform: translateY(100%);
}

// 全局工具类
.text-center {
  text-align: center;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.flex {
  display: flex;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flex-column {
  display: flex;
  flex-direction: column;
}

.hide {
  display: none;
}

.show {
  display: block;
}

// 安全区域适配
.safe-area-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

.safe-area-top {
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
}
</style>
