// tests/components/VideoPlayer.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest'
import VideoPlayer from '../src/components/VideoPlayer.vue'

// Mock hls.js
const mockHlsInstance = {
  attachMedia: vi.fn(),
  loadSource: vi.fn(),
  on: vi.fn(),
  destroy: vi.fn()
}

const mockHlsClass = vi.fn(() => mockHlsInstance)
Object.assign(mockHlsClass, {
  isSupported: vi.fn(() => true),
  Events: {
    MEDIA_ATTACHED: 'media-attached',
    MANIFEST_PARSED: 'manifest-parsed',
    ERROR: 'error'
  }
})

vi.mock('hls.js', () => ({
  default: mockHlsClass
}))

// Mock uni-app
vi.mock('@dcloudio/uni-app', () => ({
  showToast: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn()
}))

// Mock 环境变量
const originalEnv = process.env.UNI_PLATFORM
beforeAll(() => {
  process.env.UNI_PLATFORM = 'h5'
})

afterAll(() => {
  if (originalEnv !== undefined) {
    process.env.UNI_PLATFORM = originalEnv
  } else {
    delete process.env.UNI_PLATFORM
  }
})

describe('VideoPlayer.vue', () => {
  let wrapper: any
  let mockVideoElement: any

  beforeEach(() => {
    // 重置所有 mock
    vi.clearAllMocks()
    
    // Mock DOM 元素
    mockVideoElement = {
      play: vi.fn().mockResolvedValue(undefined),
      canPlayType: vi.fn().mockReturnValue(''),
      src: '',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    }
    
    // 重置 HLS mock
    mockHlsInstance.attachMedia = vi.fn()
    mockHlsInstance.loadSource = vi.fn()
    mockHlsInstance.destroy = vi.fn()
    
    // Mock HLS 事件系统
    mockHlsInstance.on = vi.fn((event, callback) => {
      // 模拟 MEDIA_ATTACHED 事件立即触发
      if (event === 'media-attached') {
        setTimeout(() => callback(), 0)
      }
    })
    
    ;(mockHlsClass as any).isSupported = vi.fn(() => true)
    
    // Mock document.querySelector
    vi.spyOn(document, 'querySelector').mockReturnValue(mockVideoElement)
    
    // Arrange: 初始化组件和依赖
    wrapper = mount(VideoPlayer, {
      props: { src: 'https://example.com/video.m3u8' }
    })
  })

  afterEach(() => {
    // 清理副作用，保证隔离
    wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('Props 渲染测试', () => {
    it('正确渲染 video 元素', () => {
      // Assert
      expect(wrapper.find('.video-js').exists()).toBe(true)
      expect(wrapper.find('video').exists()).toBe(true)
    })

    it('正确设置 video 属性', () => {
      // Assert
      const video = wrapper.find('video')
      expect(video.attributes('controls')).toBeDefined()
      expect(video.attributes('muted')).toBeDefined()
      expect(video.attributes('playsinline')).toBeDefined()
    })
  })

  describe('HLS 播放测试', () => {
    it('H5 环境下支持 HLS 时正确初始化', async () => {
      // Act - 等待组件挂载和异步操作完成
      await wrapper.vm.$nextTick()
      // 等待 HLS 导入和事件回调
      await new Promise(resolve => setTimeout(resolve, 10))

      // Assert
      expect(mockHlsInstance.attachMedia).toHaveBeenCalledWith(mockVideoElement)
      expect(mockHlsInstance.loadSource).toHaveBeenCalledWith('https://example.com/video.m3u8')
    })

    it('HLS 不支持时使用原生播放', async () => {
      // Arrange - 重新挂载组件以测试不同的条件
      wrapper.unmount()
      ;(mockHlsClass as any).isSupported = vi.fn(() => false)
      mockVideoElement.canPlayType = vi.fn().mockReturnValue('maybe')

      // Act
      wrapper = mount(VideoPlayer, {
        props: { src: 'https://example.com/video.m3u8' }
      })
      
      // 等待组件挂载和异步操作完成
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      // Assert
      expect(mockVideoElement.src).toBe('https://example.com/video.m3u8')
      expect(mockVideoElement.play).toHaveBeenCalled()
    })
  })

  describe('边界条件测试', () => {
    it('无 src 时不初始化播放器', () => {
      // Arrange
      wrapper = mount(VideoPlayer, { props: { src: '' } })
      
      // Assert
      const video = wrapper.find('video')
      expect(video.attributes('src')).toBeUndefined()
    })
  })

  describe('非 HLS 文件测试', () => {
    let nonHlsWrapper: any
    let cleanMockVideoElement: any
    let independentMockHlsInstance: any

    beforeEach(() => {
      // 为这个测试组创建完全独立的 mock 环境
      vi.clearAllMocks()
      
      cleanMockVideoElement = {
        play: vi.fn().mockResolvedValue(undefined),
        canPlayType: vi.fn().mockReturnValue(''),
        src: '',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      }
      
      // 创建独立的 HLS mock 实例
      independentMockHlsInstance = {
        attachMedia: vi.fn(),
        loadSource: vi.fn(),
        destroy: vi.fn(),
        on: vi.fn()
      }
      
      // 重新 mock hls.js 模块，使其返回我们的独立实例
      vi.doMock('hls.js', () => ({
        default: vi.fn(() => independentMockHlsInstance),
        Events: {
          MEDIA_ATTACHED: 'media-attached',
          MANIFEST_PARSED: 'manifest-parsed',
          ERROR: 'error'
        }
      }))
      
      vi.spyOn(document, 'querySelector').mockReturnValue(cleanMockVideoElement)
    })

    afterEach(() => {
      if (nonHlsWrapper) {
        nonHlsWrapper.unmount()
      }
      vi.clearAllMocks()
      vi.doUnmock('hls.js')
    })

    it('非 m3u8 文件时不使用 HLS', async () => {
      // Act
      nonHlsWrapper = mount(VideoPlayer, {
        props: { src: 'https://example.com/video.mp4' }
      })
      await nonHlsWrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 10))

      // Assert
      // 非 m3u8 文件不会触发 HLS 逻辑
      expect(independentMockHlsInstance.attachMedia).not.toHaveBeenCalled()
      expect(independentMockHlsInstance.loadSource).not.toHaveBeenCalled()
      // video 元素应该存在
      const video = nonHlsWrapper.find('video')
      expect(video.exists()).toBe(true)
    })
  })

  describe('错误处理测试', () => {
    it('HLS 错误时正确处理', async () => {
      // Arrange
      wrapper.unmount()
      vi.clearAllMocks()
      
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      // 创建新的 mock 实例，专门用于错误测试
      const errorMockHlsInstance = {
        attachMedia: vi.fn(),
        loadSource: vi.fn(),
        destroy: vi.fn(),
        on: vi.fn((event, callback) => {
          if (event === 'media-attached') {
            setTimeout(() => callback(), 0)
          } else if (event === 'error') {
            // HLS.js 错误事件的正确格式：callback(event, data)
            setTimeout(() => callback('hlsError', { type: 'networkError' }), 5)
          }
        })
      }
      
      // 临时重新 mock hls.js 以返回错误测试实例
      const originalMockClass = mockHlsClass
      mockHlsClass.mockImplementation(() => errorMockHlsInstance)

      // Act
      wrapper = mount(VideoPlayer, {
        props: { src: 'https://example.com/video.m3u8' }
      })
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 15))

      // Assert
      expect(consoleSpy).toHaveBeenCalledWith('HLS.js error:', { type: 'networkError' })
      
      // Cleanup
      consoleSpy.mockRestore()
      mockHlsClass.mockImplementation(() => mockHlsInstance)
    })
  })
})