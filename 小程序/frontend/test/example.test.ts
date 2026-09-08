/**
 * 测试示例文件
 * 演示如何测试组件和Pinia store
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

describe('Example Tests', () => {
  beforeEach(() => {
    // 为每个测试创建新的pinia实例
    setActivePinia(createPinia())
  })

  it('should work', () => {
    expect(1 + 1).toBe(2)
  })
})

/*
Pinia Store 测试示例：

import { useUserStore } from '@/store/user'

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should set user login state', () => {
    const userStore = useUserStore()
    expect(userStore.isLoggedIn).toBe(false)
    
    userStore.setLoginState(true)
    expect(userStore.isLoggedIn).toBe(true)
  })
})
*/
