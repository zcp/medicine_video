const TAB_LIST = [
  { pagePath: '/pages/home/Home', text: '首页' },
  { pagePath: '/pages/brand/BrandZone', text: '品牌' },
  { pagePath: '/pages/expert/ExpertList', text: '专家' },
  { pagePath: '/pages/profile/Profile', text: '我的' }
]

function getCurrentRoute() {
  if (typeof getCurrentPages !== 'function') return ''
  const pages = getCurrentPages()
  const cur = pages && pages.length ? pages[pages.length - 1] : null
  return cur && cur.route ? `/${cur.route}` : ''
}

function getMiniProgramApi() {
  return typeof wx !== 'undefined' ? wx : null
}

function normalizePath(p) {
  if (!p) return ''
  const s = String(p)
  const clean = s.split('?')[0].split('#')[0]
  return clean.startsWith('/') ? clean : `/${clean}`
}

function isAdminUser(mp) {
  if (!mp || typeof mp.getStorageSync !== 'function') return false
  try {
    const raw = mp.getStorageSync('user_info')
    const info = typeof raw === 'string' ? JSON.parse(raw || '{}') : raw || {}
    // 仅 ADMIN / SUPERADMIN；REGULAR / user / expert 均显示「+」
    const role = String(info.role || '').trim().toUpperCase()
    return role === 'ADMIN' || role === 'SUPERADMIN'
  } catch (e) {
    return false
  }
}

Component({
  data: {
    selected: 0,
    /** 管理员隐藏底部「+」创建直播 */
    showCreate: true
  },

  lifetimes: {
    attached() {
      this.updateCreateVisibility()
      this.updateSelected()
    }
  },

  pageLifetimes: {
    show() {
      this.updateCreateVisibility()
      this.updateSelected()
    }
  },

  methods: {
    updateCreateVisibility() {
      const mp = getMiniProgramApi()
      // 每次 show 强制同步，避免管理员态残留导致普通用户看不到「+」
      this.setData({ showCreate: !isAdminUser(mp) })
    },

    updateSelected() {
      const route = normalizePath(getCurrentRoute())
      const idx = TAB_LIST.findIndex(t => normalizePath(t.pagePath) === route)
      if (idx >= 0 && idx !== this.data.selected) {
        this.setData({ selected: idx })
      }
    },

    onSwitchTab(e) {
      const idx = Number(e.currentTarget.dataset.index)
      const item = TAB_LIST[idx]
      if (!item) return

      this.setData({ selected: idx })
      const mp = getMiniProgramApi()
      if (mp) {
        mp.switchTab({ url: item.pagePath })
      }
    },

    onAddTap() {
      const mp = getMiniProgramApi()
      if (!mp) return

      if (isAdminUser(mp)) {
        mp.showToast({ title: '管理员不可创建直播', icon: 'none' })
        return
      }

      try {
        const token = mp.getStorageSync('access_token')
        if (!token) {
          const redirect = encodeURIComponent('/pages/live/CreateLive')
          mp.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${redirect}` })
          return
        }
      } catch (e) {
        const redirect = encodeURIComponent('/pages/live/CreateLive')
        mp.navigateTo({ url: `/pages/auth/OneTapLogin?redirect=${redirect}` })
        return
      }

      mp.navigateTo({ url: '/pages/live/CreateLive' })
    }
  }
})
