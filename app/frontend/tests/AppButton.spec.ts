// tests/components/AppButton.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import AppButton from '../src/components/AppButton.vue'

// Mock uni-app APIs
vi.mock('@dcloudio/uni-app', () => ({
  showToast: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn()
}))

describe('AppButton.vue', () => {
  let wrapper: any
  const mockClick = vi.fn()

  beforeEach(() => {
    // Arrange: 初始化组件和依赖
    wrapper = mount(AppButton, {
      props: { type: 'primary', size: 'medium' },
      attrs: { onClick: mockClick }
    })
  })

  afterEach(() => {
    // 清理副作用，保证隔离
    wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('Props 渲染测试', () => {
    it('正常渲染默认 props', () => {
      // Arrange: 重新挂载组件，不传入任何 props 以测试默认值
      wrapper = mount(AppButton)
      
      // Assert: 检查默认样式类
      expect(wrapper.classes()).toContain('app-button')
      expect(wrapper.classes()).toContain('app-button--default')
      expect(wrapper.classes()).toContain('app-button--medium')
    })

    it('正确渲染 type prop', () => {
      // Arrange
      wrapper = mount(AppButton, { props: { type: 'danger' } })
      
      // Assert
      expect(wrapper.classes()).toContain('app-button--danger')
    })

    it('正确渲染 size prop', () => {
      // Arrange
      wrapper = mount(AppButton, { props: { size: 'large' } })
      
      // Assert
      expect(wrapper.classes()).toContain('app-button--large')
    })

    it('正确渲染 loading 状态', () => {
      // Arrange
      wrapper = mount(AppButton, { props: { loading: true } })
      
      // Assert
      expect(wrapper.classes()).toContain('is-loading')
      expect(wrapper.find('.app-button__loading-indicator').exists()).toBe(true)
      expect(wrapper.attributes('disabled')).toBeDefined()
    })

    it('正确渲染 disabled 状态', () => {
      // Arrange
      wrapper = mount(AppButton, { props: { disabled: true } })
      
      // Assert
      expect(wrapper.classes()).toContain('is-disabled')
      expect(wrapper.attributes('disabled')).toBeDefined()
    })
  })

  describe('事件测试', () => {
    it('点击事件正常触发', async () => {
      // Act
      await wrapper.trigger('click')
      
      // Assert
      expect(mockClick).toHaveBeenCalledTimes(1)
    })

    it('loading 状态下点击事件不触发', async () => {
      // Arrange
      wrapper = mount(AppButton, { 
        props: { loading: true },
        attrs: { onClick: mockClick }
      })
      
      // Act
      await wrapper.trigger('click')
      
      // Assert
      expect(mockClick).not.toHaveBeenCalled()
    })

    it('disabled 状态下点击事件不触发', async () => {
      // Arrange
      wrapper = mount(AppButton, { 
        props: { disabled: true },
        attrs: { onClick: mockClick }
      })
      
      // Act
      await wrapper.trigger('click')
      
      // Assert
      expect(mockClick).not.toHaveBeenCalled()
    })
  })

  describe('Slot 内容测试', () => {
    it('正确渲染默认 slot', () => {
      // Arrange
      wrapper = mount(AppButton, {
        slots: { default: '测试按钮' }
      })
      
      // Assert
      expect(wrapper.text()).toContain('测试按钮')
    })

    it('正确渲染复杂 slot 内容', () => {
      // Arrange
      wrapper = mount(AppButton, {
        slots: { 
          default: '<span>复杂内容</span><i>图标</i>' 
        }
      })
      
      // Assert
      expect(wrapper.html()).toContain('<span>复杂内容</span>')
      expect(wrapper.html()).toContain('<i>图标</i>')
    })
  })

  describe('边界条件测试', () => {
    it('所有 type 值都能正确渲染', () => {
      const types = ['primary', 'success', 'warning', 'danger', 'info', 'default']
      
      types.forEach(type => {
        // Arrange
        const buttonWrapper = mount(AppButton, { props: { type } })
        
        // Assert
        expect(buttonWrapper.classes()).toContain(`app-button--${type}`)
        
        buttonWrapper.unmount()
      })
    })

    it('所有 size 值都能正确渲染', () => {
      const sizes = ['large', 'medium', 'small', 'mini']
      
      sizes.forEach(size => {
        // Arrange
        const buttonWrapper = mount(AppButton, { props: { size } })
        
        // Assert
        expect(buttonWrapper.classes()).toContain(`app-button--${size}`)
        
        buttonWrapper.unmount()
      })
    })
  })
})