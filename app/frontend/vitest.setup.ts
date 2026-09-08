// vitest.setup.ts
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// Mock uni-app APIs using vi.mock
vi.mock('@dcloudio/uni-app', () => ({
  showToast: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
  request: vi.fn(),
  navigateTo: vi.fn(),
  redirectTo: vi.fn(),
  switchTab: vi.fn(),
  reLaunch: vi.fn(),
  showModal: vi.fn(),
  showActionSheet: vi.fn(),
  setStorage: vi.fn(),
  getStorage: vi.fn(),
  removeStorage: vi.fn(),
  clearStorage: vi.fn(),
  getSystemInfo: vi.fn(),
  getSystemInfoSync: vi.fn(),
  onPageScroll: vi.fn(),
  onReachBottom: vi.fn(),
  onPullDownRefresh: vi.fn(),
  onShareAppMessage: vi.fn(),
  onShareTimeline: vi.fn(),
  onTabItemTap: vi.fn(),
  onResize: vi.fn(),
  onLoad: vi.fn(),
  onReady: vi.fn(),
  onShow: vi.fn(),
  onHide: vi.fn(),
  onUnload: vi.fn(),
  onError: vi.fn(),
  onPageNotFound: vi.fn(),
  onUnhandledRejection: vi.fn(),
  onThemeChange: vi.fn(),
  onAddToFavorites: vi.fn(),
  onUpdateReady: vi.fn(),
  onUpdateFailed: vi.fn(),
  onLaunch: vi.fn(),
}))

// Mock global uni object
const uni = {
  showToast: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
  request: vi.fn(),
  navigateTo: vi.fn(),
  redirectTo: vi.fn(),
  switchTab: vi.fn(),
  reLaunch: vi.fn(),
  showModal: vi.fn(),
  showActionSheet: vi.fn(),
  setStorage: vi.fn(),
  getStorage: vi.fn(),
  removeStorage: vi.fn(),
  clearStorage: vi.fn(),
  getSystemInfo: vi.fn(),
  getSystemInfoSync: vi.fn(),
  onPageScroll: vi.fn(),
  onReachBottom: vi.fn(),
  onPullDownRefresh: vi.fn(),
  onShareAppMessage: vi.fn(),
  onShareTimeline: vi.fn(),
  onTabItemTap: vi.fn(),
  onResize: vi.fn(),
  onLoad: vi.fn(),
  onReady: vi.fn(),
  onShow: vi.fn(),
  onHide: vi.fn(),
  onUnload: vi.fn(),
  onError: vi.fn(),
  onPageNotFound: vi.fn(),
  onUnhandledRejection: vi.fn(),
  onThemeChange: vi.fn(),
  onAddToFavorites: vi.fn(),
  onUpdateReady: vi.fn(),
  onUpdateFailed: vi.fn(),
  onLaunch: vi.fn(),
}

// Set global uni object
;(globalThis as any).uni = uni

// Mock weex（@dcloudio/uni-ui 组件中 APP-NVUE 条件编译块在测试环境未被剥离时引用 weex）
;(globalThis as any).weex = {
  requireModule: () => ({ addRule: vi.fn() }),
}

// Configure @vue/test-utils global options
config.global.mocks = {
  $t: (key: string) => key, // Mock i18n
  $route: {
    path: '/',
    query: {},
    params: {},
  },
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
  },
}

console.log('Vitest setup file loaded.') 