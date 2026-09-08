// tests/pages/live/LiveView.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, shallowMount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import * as uniApp from '@dcloudio/uni-app'

import LiveView from '../../../src/pages/live/LiveView.vue'
import { useSessionStore } from '../../../src/store/session'
import { useRoomStore } from '../../../src/store/room'

// Stub VideoPlayer to avoid real HTMLMediaElement usage
vi.mock('../../../src/components/VideoPlayer.vue', () => ({
  default: { name: 'VideoPlayer', template: '<div class="video-player-stub" />' }
}))

const AppButtonStub = {
  name: 'AppButton',
  template: '<button class="app-button-stub" @click="$emit(\'click\')"><slot /></button>'
}

const getOnLoadCallback = () => {
  const call = vi.mocked(uniApp.onLoad).mock.calls[0]
  return call?.[0] as (options?: any) => void
}

describe('LiveView.vue (pages)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // default platform as h5
    ;(process.env as any).UNI_PLATFORM = 'h5'
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('onLoad: 带 session id 时获取 session 详情；h5 平台时使用 iframe 播放', async () => {
    const wrapper = mount(LiveView, { global: { stubs: { AppButton: AppButtonStub } } })
    const sessionStore = useSessionStore()

    const fetchSpy = vi.spyOn(sessionStore, 'fetchSessionById').mockResolvedValue()
    const cb = getOnLoadCallback()
    await cb({ id: 'session-1' })
    await flushPromises()

    expect(fetchSpy).toHaveBeenCalledWith('session-1')

    // Mock store values to make play_url truthy
    sessionStore.currentSession = { id: 'session-1', room_id: 'r1', status: 'live' } as any
    const roomStore = useRoomStore()
    roomStore.rooms = [ { id: 'r1', title: 'R1', created_at: '2024-01-01T00:00:00Z' } as any ]
    await flushPromises()

    // iframe should exist in h5 when play_url is set
    expect(wrapper.find('iframe').exists()).toBe(true)
  })

  it('非 h5 平台时渲染 VideoPlayer', async () => {
    ;(process.env as any).UNI_PLATFORM = 'app-plus'
    const wrapper = mount(LiveView, { global: { stubs: { AppButton: AppButtonStub } } })

    const cb = getOnLoadCallback()
    const sessionStore = useSessionStore()
    vi.spyOn(sessionStore, 'fetchSessionById').mockResolvedValue()
    await cb({ id: 'session-1' })

    sessionStore.currentSession = { id: 'session-1', room_id: 'r1', status: 'live' } as any
    const roomStore = useRoomStore()
    roomStore.rooms = [ { id: 'r1', title: 'R1', created_at: '2024-01-01T00:00:00Z' } as any ]
    await flushPromises()

    // Should render our stub instead of iframe
    expect(wrapper.find('.video-player-stub').exists()).toBe(true)
    expect(wrapper.find('iframe').exists()).toBe(false)
  })
})
