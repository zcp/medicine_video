// tests/pages/index/index.spec.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Index from '../../../src/pages/index/index.vue'

describe('index.vue (pages)', () => {
  beforeEach(() => {
    // no-op
  })
  afterEach(() => {
    // no-op
  })

  it('渲染欢迎标题文本', () => {
    const wrapper = shallowMount(Index)
    expect(wrapper.text()).toContain('Hello')
  })
})

