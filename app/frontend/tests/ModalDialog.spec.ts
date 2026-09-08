// tests/components/ModalDialog.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import ModalDialog from '../src/components/ModalDialog.vue'

describe('ModalDialog.vue', () => {
  let wrapper: any
  const mockConfirm = vi.fn()
  const mockCancel = vi.fn()
  const mockUpdateVisible = vi.fn()

  beforeEach(() => {
    // Arrange: 初始化组件和依赖
    wrapper = mount(ModalDialog, {
      props: {
        visible: true,
        title: '测试标题',
        confirmText: '确认',
        confirmLoading: false
      },
      attrs: {
        onConfirm: mockConfirm,
        onCancel: mockCancel,
        'onUpdate:visible': mockUpdateVisible
      }
    })
  })

  afterEach(() => {
    // 清理副作用，保证隔离
    wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('Props 渲染测试', () => {
    it('visible 为 false 时不渲染', () => {
      // Arrange
      wrapper = mount(ModalDialog, { props: { visible: false } })
      
      // Assert
      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('正确渲染标题', () => {
      // Assert
      expect(wrapper.find('.title-text').text()).toBe('测试标题')
    })

    it('正确渲染确认按钮文本', () => {
      // Assert
      expect(wrapper.find('.btn-confirm').text()).toContain('确认')
    })

    it('loading 状态下显示加载文本', () => {
      // Arrange
      wrapper = mount(ModalDialog, {
        props: { visible: true, confirmLoading: true }
      })
      
      // Assert
      expect(wrapper.find('.loading-text').exists()).toBe(true)
      expect(wrapper.find('.btn-confirm').attributes('disabled')).toBeDefined()
    })
  })

  describe('事件测试', () => {
    it('点击确认按钮触发 confirm 事件', async () => {
      // Act
      await wrapper.find('.btn-confirm').trigger('click')
      
      // Assert
      expect(mockConfirm).toHaveBeenCalledTimes(1)
    })

    it('点击取消按钮触发 cancel 事件', async () => {
      // Act
      await wrapper.find('.btn-cancel').trigger('click')
      
      // Assert
      expect(mockCancel).toHaveBeenCalledTimes(1)
    })

    it('点击关闭按钮触发 cancel 事件', async () => {
      // Act
      await wrapper.find('.modal-close').trigger('click')
      
      // Assert
      expect(mockCancel).toHaveBeenCalledTimes(1)
    })

    it('loading 状态下按钮被禁用', async () => {
      // Arrange
      wrapper = mount(ModalDialog, {
        props: { visible: true, confirmLoading: true },
        attrs: { onConfirm: mockConfirm, onCancel: mockCancel }
      })
      
      // Act
      await wrapper.find('.btn-confirm').trigger('click')
      await wrapper.find('.btn-cancel').trigger('click')
      
      // Assert
      expect(mockConfirm).not.toHaveBeenCalled()
      expect(mockCancel).not.toHaveBeenCalled()
    })
  })

  describe('Slot 内容测试', () => {
    it('正确渲染默认 slot', () => {
      // Arrange
      wrapper = mount(ModalDialog, {
        props: { visible: true },
        slots: { default: '<div>模态框内容</div>' }
      })
      
      // Assert
      expect(wrapper.find('.modal-content').html()).toContain('<div>模态框内容</div>')
    })

    it('正确渲染复杂 slot 内容', () => {
      // Arrange
      wrapper = mount(ModalDialog, {
        props: { visible: true },
        slots: { 
          default: `
            <form>
              <input type="text" />
              <textarea></textarea>
            </form>
          ` 
        }
      })
      
      // Assert
      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('input').exists()).toBe(true)
      expect(wrapper.find('textarea').exists()).toBe(true)
    })
  })

  describe('边界条件测试', () => {
    it('无标题时正常渲染', () => {
      // Arrange
      wrapper = mount(ModalDialog, {
        props: { visible: true, title: undefined }
      })
      
      // Assert
      expect(wrapper.find('.modal-title').exists()).toBe(true)
    })

    it('无确认文本时使用默认值', () => {
      // Arrange
      wrapper = mount(ModalDialog, {
        props: { visible: true, confirmText: undefined }
      })
      
      // Assert
      expect(wrapper.find('.btn-confirm').text()).toBe('确认')
    })
  })
})