// tests/utils/request.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { request, get, post, put, del, patch } from '../src/utils/request'

// Mock uni-app
const mockUni = {
  request: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
  showToast: vi.fn(),
  getStorageSync: vi.fn()
}

// 设置全局 uni 对象
;(globalThis as any).uni = mockUni

vi.mock('@dcloudio/uni-app', () => mockUni)

// Mock environment
vi.mock('../src/config/env', () => ({
  ENV_CONFIG: {
    VITE_BASE_API_URL: 'https://api.example.com',
    VITE_AUTH_API_URL: 'https://api.example.com',
    VITE_USE_MOCK: false,
    VITE_MEDIA_BASE_URL: 'https://api.example.com'
  }
}))

// 合法的三段落 JWT：payload 为 '{}'（base64: e30），exp 缺失 → 不触发过期刷新逻辑
const MOCK_TOKEN = 'e30.e30.sig'

describe('request.ts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // 确保全局 uni 对象正确设置
    ;(globalThis as any).uni = mockUni
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('request 函数测试', () => {
    it('成功请求返回数据', async () => {
      // Arrange
      const mockResponse = {
        statusCode: 200,
        data: { id: '1', title: 'test' }
      }
      mockUni.request.mockImplementation((options) => {
        options.success(mockResponse)
        options.complete()
      })

      // Act
      const result = await request({
        url: '/test',
        method: 'GET'
      })

      // Assert
      expect(result).toEqual({ id: '1', title: 'test' })
      expect(mockUni.showLoading).toHaveBeenCalled()
      expect(mockUni.hideLoading).toHaveBeenCalled()
    })

    it('生产环境使用 HTTP 时发出警告（不再强制拦截，测试阶段放开）', () => {
      // Arrange
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'production'
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      // Act：async 函数同步段即发出 uni.request（mock 不回调，promise 保持 pending）
      request({
        url: 'http://api.example.com/test',
        method: 'GET'
      })

      // Assert：请求照常发出并输出 HTTP 警告（throw 已在测试阶段注释）
      expect(mockUni.request).toHaveBeenCalled()
      expect(warnSpy).toHaveBeenCalled()

      // Cleanup
      process.env.NODE_ENV = originalEnv
      warnSpy.mockRestore()
    })

    it('401 错误正确处理', async () => {
      // Arrange
      const mockResponse = {
        statusCode: 401,
        data: 'Unauthorized'
      }
      mockUni.request.mockImplementation((options) => {
        options.success(mockResponse)
        options.complete()
      })

      // Act & Assert
      await expect(request({
        url: '/test',
        method: 'GET'
      })).rejects.toThrow('Unauthorized')
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '登录已过期，请重新登录',
        icon: 'none',
        duration: 2000
      })
    })

    it('403 错误正确处理', async () => {
      // Arrange
      const mockResponse = {
        statusCode: 403,
        data: 'Forbidden'
      }
      mockUni.request.mockImplementation((options) => {
        options.success(mockResponse)
        options.complete()
      })

      // Act & Assert
      await expect(request({
        url: '/test',
        method: 'GET'
      })).rejects.toThrow('Forbidden')
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '您没有权限执行此操作',
        icon: 'none',
        duration: 2000
      })
    })

    it('网络错误时自动重试', async () => {
      // Arrange
      let callCount = 0
      mockUni.request.mockImplementation((options) => {
        callCount++
        if (callCount < 3) {
          // 使用 setTimeout 模拟异步失败
          setTimeout(() => options.fail(new Error('Network Error')), 0)
        } else {
          // 使用 setTimeout 模拟异步成功
          setTimeout(() => options.success({ statusCode: 200, data: { success: true } }), 0)
        }
      })

      // Act
      const result = await request({
        url: '/test',
        method: 'GET'
      }, 3)

      // Assert
      expect(result).toEqual({ success: true })
      expect(mockUni.request).toHaveBeenCalledTimes(3)
    }, 10000)

    it('请求超时处理', async () => {
      // Arrange
      mockUni.request.mockImplementation((options) => {
        // 不调用 success 或 fail，模拟超时
      })

      // Act & Assert
      await expect(request({
        url: '/test',
        method: 'GET'
      }, 1, 100)).rejects.toThrow('请求超时')
    })
  })

  describe('便捷方法测试', () => {
    it('get 方法正确调用', async () => {
      // Arrange
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.request.mockImplementation((options) => {
        expect(options.method).toBe('GET')
        expect(options.url).toContain('/test')
        options.success(mockResponse)
      })

      // Act
      const result = await get('/test', { page: 1 })

      // Assert
      expect(result).toEqual({ success: true })
    })

    it('post 方法正确调用', async () => {
      // Arrange
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.request.mockImplementation((options) => {
        expect(options.method).toBe('POST')
        expect(options.data).toEqual({ title: 'test' })
        options.success(mockResponse)
      })

      // Act
      const result = await post('/test', { title: 'test' })

      // Assert
      expect(result).toEqual({ success: true })
    })

    it('put 方法正确调用', async () => {
      // Arrange
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.request.mockImplementation((options) => {
        expect(options.method).toBe('PUT')
        options.success(mockResponse)
      })

      // Act
      const result = await put('/test', { title: 'updated' })

      // Assert
      expect(result).toEqual({ success: true })
    })

    it('del 方法正确调用', async () => {
      // Arrange
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.request.mockImplementation((options) => {
        expect(options.method).toBe('DELETE')
        options.success(mockResponse)
      })

      // Act
      const result = await del('/test')

      // Assert
      expect(result).toEqual({ success: true })
    })

    it('patch 方法正确调用', async () => {
      // Arrange
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.request.mockImplementation((options) => {
        expect(options.method).toBe('PATCH')
        options.success(mockResponse)
      })

      // Act
      const result = await patch('/test', { title: 'patched' })

      // Assert
      expect(result).toEqual({ success: true })
    })
  })

  describe('认证和 CSRF 测试', () => {
    it('需要认证时添加 Authorization 头', async () => {
      // Arrange
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.getStorageSync.mockReturnValue(MOCK_TOKEN)
      mockUni.request.mockImplementation((options) => {
        expect(options.header.Authorization).toContain('Bearer ')
        options.success(mockResponse)
      })

      // Act
      await request({
        url: '/test',
        method: 'GET',
        auth: true
      })

      // Assert
      expect(mockUni.request).toHaveBeenCalled()
    })

    it('auth: false 时不添加 Authorization 头（匿名请求语义）', async () => {
      // Arrange
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.getStorageSync.mockReturnValue(MOCK_TOKEN)
      mockUni.request.mockImplementation((options) => {
        expect(options.header.Authorization).toBeUndefined()
        options.success(mockResponse)
      })

      // Act
      await request({
        url: '/test',
        method: 'GET',
        auth: false
      })

      // Assert
      expect(mockUni.request).toHaveBeenCalled()
    })

    it('有 CSRF Token 时添加到请求头', async () => {
      // Arrange
      Object.defineProperty(document, 'cookie', {
        value: 'csrftoken=test-token',
        writable: true
      })
      const mockResponse = { statusCode: 200, data: { success: true } }
      mockUni.request.mockImplementation((options) => {
        expect(options.header['X-CSRFToken']).toBe('test-token')
        options.success(mockResponse)
      })

      // Act
      await request({
        url: '/test',
        method: 'POST'
      })

      // Assert
      expect(mockUni.request).toHaveBeenCalled()
    })
  })
})