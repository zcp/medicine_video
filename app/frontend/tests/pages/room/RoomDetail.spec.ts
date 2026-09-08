// tests/pages/room/RoomDetail.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, shallowMount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import * as uniApp from '@dcloudio/uni-app'

import RoomDetail from '../../../src/pages/room/RoomDetail.vue'
import { useRoomStore } from '../../../src/store/room'
import { useSessionStore } from '../../../src/store/session'

// Stubs
const AppButtonStub = {
  name: 'AppButton',
  template: '<button class="app-button-stub" @click="$emit(\'click\')"><slot /></button>'
}
const ModalDialogStub = {
  name: 'ModalDialog',
  props: ['visible', 'title', 'confirmText', 'confirmLoading'],
  template: '<div class="modal-dialog-stub"><slot /></div>'
}

const getOnLoadCallback = () => {
  const call = vi.mocked(uniApp.onLoad).mock.calls[0]
  return call?.[0] as (options?: any) => void
}

describe('RoomDetail.vue (pages)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('onLoad: 提供 id 时，调用 fetchRoomById', async () => {
    const wrapper = shallowMount(RoomDetail, {
      global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } }
    })
    const roomStore = useRoomStore()
    const spy = vi.spyOn(roomStore, 'fetchRoomById').mockResolvedValue()

    expect(uniApp.onLoad).toHaveBeenCalled()
    const cb = getOnLoadCallback()
    await cb({ id: 'room-123' })
    await flushPromises()

    expect(spy).toHaveBeenCalledWith('room-123')
    wrapper.unmount()
  })

  it('watch: 设置 currentRoom 后，自动加载 sessions（主会场还加载分会场）', async () => {
    mount(RoomDetail, { global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } } })
    const roomStore = useRoomStore()
    const sessionStore = useSessionStore()

    const sessionsSpy = vi.spyOn(sessionStore, 'fetchSessionsByRoomId').mockResolvedValue()
    const subVenuesSpy = vi.spyOn(roomStore, 'fetchSubVenues').mockResolvedValue()

    // 主会场（无 parent_room_id）
    roomStore.currentRoom = { id: 'r1', title: '主会场', description: '', parent_room_id: undefined } as any
    await flushPromises()

    expect(sessionsSpy).toHaveBeenCalledWith('r1', { refresh: true })
    expect(subVenuesSpy).toHaveBeenCalledWith('r1')

    // 分会场（有 parent_room_id）不加载子会场列表
    sessionsSpy.mockClear()
    subVenuesSpy.mockClear()
    roomStore.currentRoom = { id: 'r2', title: '分会场', parent_room_id: 'r1' } as any
    await flushPromises()

    expect(sessionsSpy).toHaveBeenCalledWith('r2', { refresh: true })
    expect(subVenuesSpy).not.toHaveBeenCalled()
  })

  it('渲染：根据 sessions 列表渲染表格行，点击“播放”跳转 LiveView', async () => {
    const roomStore = useRoomStore()
    const sessionStore = useSessionStore()

    // 先设置 store，再挂载组件，避免挂载后 watch 带来的刷新清空
    roomStore.currentRoom = { id: 'r1', title: '主会场' } as any
    sessionStore.sessions = [
      { id: 's1', room_id: 'r1', status: 'live', start_time: '2024-01-01T10:00:00Z' } as any,
      { id: 's2', room_id: 'r1', status: 'scheduled', start_time: '2024-01-02T10:00:00Z' } as any,
    ]

    const wrapper = mount(RoomDetail, { global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } } })
    await flushPromises()

    const rows = wrapper.findAll('.table-row')
    expect(rows.length).toBe(2)

    // actions-cell 中第3个按钮是“播放”
    const actions = rows[0].find('.actions-cell')
    const buttons = actions.findAll('.app-button-stub')
    await buttons[2].trigger('click')

    expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/live/LiveView?id=s1' })
  })
})

