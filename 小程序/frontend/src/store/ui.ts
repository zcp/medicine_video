/**
 * UI状态管理
 * 管理界面相关状态、弹窗、加载状态、导航等
 */

import { defineStore } from 'pinia'

interface TabBarItem {
  pagePath: string
  text: string
  iconPath?: string
  selectedIconPath?: string
  badge?: string | number
  redDot?: boolean
}

interface ToastConfig {
  title: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  mask?: boolean
}

interface ModalConfig {
  title: string
  content: string
  showCancel?: boolean
  cancelText?: string
  confirmText?: string
  success?: (res: any) => void
}

interface UIState {
  // 全局加载状态
  globalLoading: boolean
  loadingText: string
  
  // TabBar状态
  currentTab: number
  tabBarItems: TabBarItem[]
  
  // 弹窗状态
  toastQueue: ToastConfig[]
  modalVisible: boolean
  modalConfig: ModalConfig | null
  
  // 导航状态
  navigationHistory: string[]
  currentPage: string
  
  // 滚动位置缓存
  scrollPositions: Record<string, number>
  
  // 下拉刷新状态
  refreshing: Record<string, boolean>
  
  // 底部安全区域
  safeAreaBottom: number
  
  // 状态栏高度
  statusBarHeight: number
  
  // 系统信息
  systemInfo: any | null
  
  // 网络状态
  networkType: string
  isOnline: boolean
}

export const useUIStore = defineStore('ui', {
  state: (): UIState => ({
    globalLoading: false,
    loadingText: '加载中...',
    currentTab: 0,
    tabBarItems: [
      { pagePath: 'pages/home/Home', text: '首页' },
      { pagePath: 'pages/brand/BrandZone', text: '品牌' },
      { pagePath: 'pages/expert/ExpertList', text: '专家' },
      { pagePath: 'pages/profile/Profile', text: '我的' }
    ],
    toastQueue: [],
    modalVisible: false,
    modalConfig: null,
    navigationHistory: [],
    currentPage: '',
    scrollPositions: {},
    refreshing: {},
    safeAreaBottom: 0,
    statusBarHeight: 44,
    systemInfo: null,
    networkType: 'unknown',
    isOnline: true
  }),

  getters: {
    /**
     * 当前TabBar项
     */
    currentTabItem: (state) => state.tabBarItems[state.currentTab],
    
    /**
     * 是否显示TabBar
     */
    showTabBar: (state) => {
      const tabBarPages = state.tabBarItems.map(item => item.pagePath)
      return tabBarPages.includes(state.currentPage)
    },
    
    /**
     * 屏幕宽度
     */
    screenWidth: (state) => state.systemInfo?.screenWidth || 375,
    
    /**
     * 屏幕高度
     */
    screenHeight: (state) => state.systemInfo?.screenHeight || 667,
    
    /**
     * 是否为iPhone X及以上机型
     */
    isIPhoneX: (state) => {
      if (!state.systemInfo) return false
      const { model, safeArea } = state.systemInfo
      return model.includes('iPhone') && safeArea && safeArea.bottom > 0
    },
    
    /**
     * 导航栏高度
     */
    navBarHeight: (state) => {
      // #ifdef MP-WEIXIN
      return state.statusBarHeight + 44
      // #endif
      // #ifndef MP-WEIXIN
      return 44
      // #endif
    }
  },

  actions: {
    /**
     * 显示全局加载
     */
    showLoading(text: string = '加载中...'): void {
      this.globalLoading = true
      this.loadingText = text
      
      uni.showLoading({
        title: text,
        mask: true
      })
    },

    /**
     * 隐藏全局加载
     */
    hideLoading(): void {
      this.globalLoading = false
      uni.hideLoading()
    },

    /**
     * 显示Toast
     */
    showToast(config: ToastConfig): void {
      const rawTitle = config?.title
      const title =
        typeof rawTitle === 'string' && rawTitle.trim() && rawTitle !== '[object Object]'
          ? rawTitle.trim()
          : '操作失败，请稍后再试'

      const toastConfig: ToastConfig & { duration: number; mask: boolean } = {
        duration: 2000,
        mask: false,
        ...config,
        title
      }
      
      this.toastQueue.push(toastConfig)
      
      // 显示Toast（微信 icon 仅支持 success / loading / none / error）
      const icon = this._getToastIcon(toastConfig.type)
      uni.showToast({
        title: toastConfig.title,
        icon: icon === 'error' ? 'none' : icon,
        duration: toastConfig.duration,
        mask: toastConfig.mask
      })
      
      // 自动移除
      setTimeout(() => {
        this.toastQueue.shift()
      }, toastConfig.duration)
    },

    /**
     * 显示成功Toast
     */
    showSuccess(title: string): void {
      this.showToast({ title, type: 'success' })
    },

    /**
     * 显示错误Toast
     */
    showError(title: string): void {
      this.showToast({ title, type: 'error' })
    },

    /**
     * 显示模态框
     */
    showModal(config: ModalConfig): Promise<boolean> {
      return new Promise((resolve) => {
        this.modalVisible = true
        this.modalConfig = {
          showCancel: true,
          cancelText: '取消',
          confirmText: '确定',
          ...config,
          success: (res) => {
            this.modalVisible = false
            this.modalConfig = null
            resolve(res.confirm)
            config.success?.(res)
          }
        }
        
        uni.showModal(this.modalConfig)
      })
    },

    /**
     * 切换Tab
     */
    switchTab(index: number): void {
      if (index >= 0 && index < this.tabBarItems.length) {
        this.currentTab = index
        const tabItem = this.tabBarItems[index]
        
        uni.switchTab({
          url: `/${tabItem.pagePath}`
        })
      }
    },

    /**
     * 设置Tab徽标
     */
    setTabBarBadge(index: number, text: string): void {
      if (index >= 0 && index < this.tabBarItems.length) {
        this.tabBarItems[index].badge = text
        
        uni.setTabBarBadge({
          index,
          text
        })
      }
    },

    /**
     * 移除Tab徽标
     */
    removeTabBarBadge(index: number): void {
      if (index >= 0 && index < this.tabBarItems.length) {
        this.tabBarItems[index].badge = undefined
        
        uni.removeTabBarBadge({ index })
      }
    },

    /**
     * 显示Tab红点
     */
    showTabBarRedDot(index: number): void {
      if (index >= 0 && index < this.tabBarItems.length) {
        this.tabBarItems[index].redDot = true
        
        uni.showTabBarRedDot({ index })
      }
    },

    /**
     * 隐藏Tab红点
     */
    hideTabBarRedDot(index: number): void {
      if (index >= 0 && index < this.tabBarItems.length) {
        this.tabBarItems[index].redDot = false
        
        uni.hideTabBarRedDot({ index })
      }
    },

    /**
     * 更新当前页面
     */
    updateCurrentPage(path: string): void {
      this.currentPage = path
      
      // 更新导航历史
      if (this.navigationHistory[this.navigationHistory.length - 1] !== path) {
        this.navigationHistory.push(path)
        
        // 限制历史记录长度
        if (this.navigationHistory.length > 20) {
          this.navigationHistory.shift()
        }
      }
    },

    /**
     * 保存滚动位置
     */
    saveScrollPosition(path: string, scrollTop: number): void {
      this.scrollPositions[path] = scrollTop
    },

    /**
     * 获取滚动位置
     */
    getScrollPosition(path: string): number {
      return this.scrollPositions[path] || 0
    },

    /**
     * 设置下拉刷新状态
     */
    setRefreshing(path: string, refreshing: boolean): void {
      this.refreshing[path] = refreshing
    },

    /**
     * 获取下拉刷新状态
     */
    isRefreshing(path: string): boolean {
      return this.refreshing[path] || false
    },

    /**
     * 初始化系统信息
     */
    async initSystemInfo(): Promise<void> {
      try {
        const systemInfo = await uni.getSystemInfo()
        this.systemInfo = systemInfo
        this.statusBarHeight = systemInfo.statusBarHeight || 44
        this.safeAreaBottom = systemInfo.safeAreaInsets?.bottom || 0
      } catch (error) {
        console.error('获取系统信息失败:', error)
      }
    },

    /**
     * 监听网络状态
     */
    initNetworkStatus(): void {
      // 获取当前网络状态
      uni.getNetworkType({
        success: (res: any) => {
          this.networkType = res.networkType
          this.isOnline = res.networkType !== 'none'
        }
      })
      
      // 监听网络状态变化
      uni.onNetworkStatusChange((res: any) => {
        this.networkType = res.networkType
        this.isOnline = res.isConnected
        
        if (!this.isOnline) {
          this.showError('网络连接已断开')
        }
      })
    },

    /**
     * 获取Toast图标
     * @private
     */
    _getToastIcon(type: ToastConfig['type']): 'success' | 'error' | 'none' {
      switch (type) {
        case 'success':
          return 'success'
        case 'error':
          return 'error'
        case 'warning':
        case 'info':
        default:
          return 'none'
      }
    }
  },

  // persist: {
  //   key: 'ui-store',
  //   paths: ['currentTab', 'scrollPositions', 'safeAreaBottom', 'statusBarHeight']
  // }
})
