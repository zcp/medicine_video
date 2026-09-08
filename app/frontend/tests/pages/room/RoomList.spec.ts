// tests/pages/room/RoomList.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, shallowMount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

// Use relative import to the SFC
import RoomList from '../../../src/pages/room/new/RoomList.vue'
import * as uniApp from '@dcloudio/uni-app'
import { useRoomStore } from '../../../src/store/room'

// Simple stubs for child components that re-emit click
const AppButtonStub = {
  name: 'AppButton',
  template: '<button class="app-button-stub" @click="$emit(\'click\')"><slot /></button>'
}
const ModalDialogStub = {
  name: 'ModalDialog',
  props: ['visible', 'title', 'confirmText', 'confirmLoading'],
  template: '<div class="modal-dialog-stub"><slot /></div>'
}

// Helper to trigger captured lifecycle from mocked uni-app
const getOnLoadCallback = () => {
  const onLoad = vi.mocked(uniApp.onLoad)
  const call = onLoad.mock.calls[0]
  return call?.[0] as (options?: any) => void
}

describe('RoomList.vue (pages)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // ensure stopPullDownRefresh is available on global uni
    ;(globalThis as any).uni.stopPullDownRefresh = vi.fn()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('页面渲染：显示标题与空列表状态（无房间）', async () => {
    const wrapper = shallowMount(RoomList, {
      global: {
        stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub }
      }
    })

    // Assert basic rendering
    expect(wrapper.find('.page-title').exists()).toBe(true)
    // No room items rendered when store.rooms is default []
    expect(wrapper.findAll('.room-item').length).toBe(0)
  })

  it('生命周期：onLoad 注册并可触发 fetchRooms({ refresh: true })', async () => {
    const wrapper = shallowMount(RoomList, {
      global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } }
    })
    const roomStore = useRoomStore()
    const spy = vi.spyOn(roomStore, 'fetchRooms').mockResolvedValueOnce()

    // onLoad should be registered in setup
    expect(uniApp.onLoad).toHaveBeenCalled()
    const cb = getOnLoadCallback()
    expect(typeof cb).toBe('function')

    await cb()
    await flushPromises()

    expect(spy).toHaveBeenCalledWith({ refresh: true })
    wrapper.unmount()
  })

  it('房间列表：根据主会场过滤渲染，点击行跳转详情', async () => {
    const wrapper = mount(RoomList, {
      global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } }
    })
    const roomStore = useRoomStore()

    // Arrange rooms: one main (no parent_room_id) and one sub
    roomStore.rooms = [
      { id: 'r1', title: '主会场A', description: '描述A', created_at: '2024-01-01T00:00:00Z' } as any,
      { id: 'r2', title: '分会场B', description: '描述B', parent_room_id: 'r1' } as any,
    ]
    await flushPromises()

    // Only one main room should render
    const rows = wrapper.findAll('.room-item')
    expect(rows.length).toBe(1)

    // Click header to navigate
    await rows[0].find('.room-header').trigger('click')
    expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/room/RoomDetail?id=r1' })
  })

  it('操作按钮：点击删除按钮仅触发其点击而不冒泡到行导航', async () => {
    const wrapper = mount(RoomList, {
      global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } }
    })
    const roomStore = useRoomStore()
    roomStore.rooms = [ { id: 'r1', title: '主会场A' } as any ]
    await flushPromises()

    const item = wrapper.find('.room-item')
    // room-actions 下第2个按钮是“删除”（按页面顺序：编辑、删除、查看详情）
    const actionButtons = item.findAll('.app-button-stub')
    await actionButtons[1].trigger('click')

    // Ensure no navigation
    expect(uni.navigateTo).not.toHaveBeenCalled()
  })

  it('分页：调用 goNextPage 时在 hasMore=true 时触发 fetchRooms()', async () => {
    const wrapper = mount(RoomList, {
      global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } }
    })
    const roomStore = useRoomStore()
    const spy = vi.spyOn(roomStore, 'fetchRooms').mockResolvedValue()

    // Simulate hasMore
    roomStore.pagination.hasMore = true
    ;(wrapper.vm as any).goNextPage()
    await flushPromises()

    expect(spy).toHaveBeenCalled()
  })

  it('下拉刷新：触发 onPullDownRefresh 回调后刷新并停止刷新动画', async () => {
    const wrapper = shallowMount(RoomList, {
      global: { stubs: { AppButton: AppButtonStub, ModalDialog: ModalDialogStub } }
    })
    const roomStore = useRoomStore()
    const fetchSpy = vi.spyOn(roomStore, 'fetchRooms').mockResolvedValue()

    // Capture and trigger onPullDownRefresh registered callback
    const onPullDown = vi.mocked(uniApp.onPullDownRefresh)
    expect(onPullDown).toHaveBeenCalled()
    const cb = onPullDown.mock.calls[0]?.[0] as () => void
    await cb()
    await flushPromises()

    expect(fetchSpy).toHaveBeenCalledWith({ refresh: true })
    expect(uni.stopPullDownRefresh).toHaveBeenCalled()
    wrapper.unmount()
  })
})

