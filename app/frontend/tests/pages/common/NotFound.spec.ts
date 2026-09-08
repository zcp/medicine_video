// tests/pages/common/NotFound.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'

import NotFound from '../../../src/pages/common/NotFound.vue'

const AppButtonStub = {
  name: 'AppButton',
  template: '<button class="app-button-stub" @click="$emit(\'click\')"><slot /></button>'
}

describe('NotFound.vue (pages)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('点击“返回首页”调用 reLaunch 跳转到 RoomList', async () => {
    const wrapper = shallowMount(NotFound, { global: { stubs: { AppButton: AppButtonStub } } })

    await wrapper.find('.app-button-stub').trigger('click')

    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/room/new/RoomList' })
  })
})

