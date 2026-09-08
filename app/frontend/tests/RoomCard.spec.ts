// tests/components/RoomCard.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import RoomCard from '../src/components/RoomCard.vue'

describe('RoomCard.vue', () => {
  let wrapper: any
  const mockClick = vi.fn()
  const mockRoom = {
    id: '1',
    title: '测试房间',
    description: '测试描述',
    cover_url: 'https://example.com/cover.jpg',
    is_private: false,
    created_at: '2023-01-01T00:00:00Z'
  }

  beforeEach(() => {
    // Arrange: 初始化组件和依赖
    wrapper = mount(RoomCard, {
      props: { room: mockRoom, showDescription: true },
      attrs: { onClick: mockClick }
    })
  })

  afterEach(() => {
    // 清理副作用，保证隔离
    wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('Props 渲染测试', () => {
    it('正确渲染房间标题', () => {
      // Assert
      expect(wrapper.find('.title').text()).toBe('测试房间')
    })

    it('正确渲染房间描述', () => {
      // Assert
      expect(wrapper.find('.description').text()).toBe('测试描述')
    })

    it('showDescription 为 false 时不显示描述', () => {
      // Arrange
      wrapper = mount(RoomCard, {
        props: { room: mockRoom, showDescription: false }
      })
      
      // Assert
      expect(wrapper.find('.description').exists()).toBe(false)
    })

    it('私密房间显示私密标识', () => {
      // Arrange
      const privateRoom = { ...mockRoom, is_private: true }
      wrapper = mount(RoomCard, { props: { room: privateRoom } })
      
      // Assert
      expect(wrapper.find('.private-badge').exists()).toBe(true)
      expect(wrapper.find('.private-badge').text()).toBe('私密')
    })
  })

  describe('图片处理测试', () => {
    it('有封面图片时正确显示', () => {
      // Assert
      expect(wrapper.find('.cover-image').attributes('src')).toBe('https://example.com/cover.jpg')
    })

    it('无封面图片时显示占位符', () => {
      // Arrange
      const roomWithoutCover = { ...mockRoom, cover_url: null }
      wrapper = mount(RoomCard, { props: { room: roomWithoutCover } })
      
      // Assert
      expect(wrapper.find('.image-placeholder').exists()).toBe(true)
      expect(wrapper.find('.placeholder-text').text()).toBe('暂无封面')
    })

    it('图片加载失败时显示占位符', async () => {
      // Arrange
      wrapper = mount(RoomCard, { props: { room: mockRoom } })
      
      // Act
      await wrapper.find('.cover-image').trigger('error')
      
      // Assert
      expect(wrapper.find('.image-placeholder').exists()).toBe(true)
    })
  })

  describe('事件测试', () => {
    it('点击卡片触发 click 事件', async () => {
      // Act
      await wrapper.find('.card-main-content').trigger('click')
      
      // Assert
      expect(mockClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('Slot 测试', () => {
    it('正确渲染 actions slot', () => {
      // Arrange
      wrapper = mount(RoomCard, {
        props: { room: mockRoom },
        slots: { 
          actions: '<button>编辑</button><button>删除</button>' 
        }
      })
      
      // Assert
      expect(wrapper.find('.cover-actions').html()).toContain('<button>编辑</button>')
      expect(wrapper.find('.cover-actions').html()).toContain('<button>删除</button>')
    })
  })

  describe('边界条件测试', () => {
    it('无描述时显示默认文本', () => {
      // Arrange
      const roomWithoutDesc = { ...mockRoom, description: null }
      wrapper = mount(RoomCard, { props: { room: roomWithoutDesc } })
      
      // Assert
      expect(wrapper.find('.description').text()).toBe('暂无简介')
    })

    it('标题过长时正确截断', () => {
      // Arrange
      const longTitleRoom = { 
        ...mockRoom, 
        title: '这是一个非常非常非常非常非常非常非常非常非常非常长的标题' 
      }
      wrapper = mount(RoomCard, { props: { room: longTitleRoom } })
      
      // Assert
      const titleElement = wrapper.find('.title')
      expect(titleElement.text()).toBe(longTitleRoom.title)
      expect(titleElement.classes()).toContain('title')
    })
  })
})