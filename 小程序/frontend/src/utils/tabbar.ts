declare const getCurrentPages: undefined | (() => any[])

/** 与 custom-tab-bar / authStore.isAdmin 对齐：仅 ADMIN、SUPERADMIN */
function isAdminRoleFromStorage(): boolean {
  try {
    const raw = uni.getStorageSync('user_info')
    const info = typeof raw === 'string' ? JSON.parse(raw || '{}') : raw || {}
    const role = String((info as { role?: string })?.role || '')
      .trim()
      .toUpperCase()
    return role === 'ADMIN' || role === 'SUPERADMIN'
  } catch {
    return false
  }
}

/**
 * 同步自定义 TabBar 选中态，并按当前登录角色刷新底部「+」创建入口。
 * 管理员隐藏；普通用户 / 未登录显示（点按再走登录）。
 */
export function setCustomTabBarSelected(selected: number) {
  try {
    const pages = typeof getCurrentPages === 'function' ? getCurrentPages() : []
    const currentPage = Array.isArray(pages) && pages.length ? (pages[pages.length - 1] as any) : null
    const tabBar = currentPage && typeof currentPage.getTabBar === 'function' ? currentPage.getTabBar() : null
    if (tabBar && typeof tabBar.setData === 'function') {
      tabBar.setData({
        selected,
        showCreate: !isAdminRoleFromStorage()
      })
    }
  } catch {
    // ignore
  }
}
