import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.useFakeTimers();

// Mock the entire @dcloudio/uni-ui package at the top level to prevent compilation errors.
vi.mock('@dcloudio/uni-ui', () => ({}));


import { mount, flushPromises, DOMWrapper, VueWrapper } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import { setActivePinia, getActivePinia } from 'pinia';
import { useRoomStore } from '@/store/room';
import { useSessionStore } from '@/store/session';
import type { Room } from '@/types/room';
import type { Session } from '@/types/session';

import RoomDetail from '@/pages/room/RoomDetail.vue';



// Mock 子组件
vi.mock('@/components/AppButton.vue', () => ({
  default: {
    name: 'AppButton',
    template: '<button @click="$emit(\'click\')"><slot /></button>',
    props: ['type', 'size', 'disabled']
  }
}));

vi.mock('@/components/ModalDialog.vue', () => ({
  default: {
    name: 'ModalDialog',
    template: `
      <div v-if="visible">
        <slot />
        <button class="confirm-button" @click="$emit('confirm')">Confirm</button>
        <button class="cancel-button" @click="$emit('cancel')">Cancel</button>
      </div>
    `,
    props: ['visible', 'title', 'confirmText', 'confirmLoading']
  }
}));

// Mock uni-app API 和生命周期
const lifecycles: Record<string, Array<(options?: any) => void>> = {
  onLoad: [],
};

vi.mock('@dcloudio/uni-app', () => ({
  onLoad: (cb: (options?: any) => void) => lifecycles.onLoad.push(cb),
}));

const captureLifecycle = () => ({
  triggerOnLoad: (options?: any) => {
    lifecycles.onLoad.forEach(cb => cb(options));
  },
  reset: () => {
    lifecycles.onLoad = [];
  }
});

const createUniMock = () => ({
  navigateTo: vi.fn(),
  navigateBack: vi.fn(),
  showToast: vi.fn(),
  showModal: vi.fn(async (options) => {
    if (options.success) {
      // Await the async success callback to ensure its completion
      await options.success({ confirm: true, cancel: false });
    }
    return { confirm: true, cancel: false };
  }),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
});

// @ts-ignore -- The type might be slightly out of sync with the actual data model which uses null.
const mockRoom: Room = { id: 'room1', title: 'Main Room', description: 'Main Desc', parent_room_id: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), is_private: false, record_by_default: false, stream_key: 'stream_key_room1' };
const mockSubVenue: Room = { id: 'sub1', title: 'Sub Venue 1', description: 'Sub Desc', parent_room_id: 'room1', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), is_private: false, record_by_default: false, stream_key: 'stream_key_sub1' };
const mockSessions: Session[] = [
  { id: 'session1', room_id: 'room1', status: 'live', start_time: new Date().toISOString(), end_time: null, video_id: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: 'session2', room_id: 'room1', status: 'scheduled', start_time: new Date().toISOString(), end_time: null, video_id: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
];

describe('RoomDetail.vue (WeChat Mini Program)', () => {
  let wrapper: any;
  let roomStore: ReturnType<typeof useRoomStore>;
  let sessionStore: ReturnType<typeof useSessionStore>;

  beforeEach(() => {
    // @ts-ignore
    global.uni = createUniMock();
    captureLifecycle().reset();

    const pinia = createTestingPinia({ createSpy: vi.fn, stubActions: false });
    setActivePinia(pinia);

    roomStore = useRoomStore();
    sessionStore = useSessionStore();

    // Mock store state
    roomStore.currentRoom = null;
    roomStore.subVenues = [];
    sessionStore.sessions = [];
    roomStore.loading = true;
    sessionStore.loading = true;
    roomStore.error = null;
    sessionStore.error = null;

    // Mock store actions
    vi.spyOn(roomStore, 'fetchRoomById').mockImplementation(async (id) => {
      if (id === mockRoom.id) roomStore.currentRoom = mockRoom;
      roomStore.loading = false;
    });
    vi.spyOn(sessionStore, 'fetchSessionsByRoomId').mockImplementation(async () => {
        sessionStore.sessions = mockSessions;
        sessionStore.loading = false;
    });
    vi.spyOn(roomStore, 'fetchSubVenues').mockImplementation(async () => {
        roomStore.subVenues = [mockSubVenue];
    });
    vi.spyOn(sessionStore, 'createSession').mockImplementation(async (roomId, payload) => true);
    vi.spyOn(sessionStore, 'updateSession').mockImplementation(async (sessionId, payload) => true);
    vi.spyOn(sessionStore, 'deleteSession').mockImplementation(async (sessionId, roomId) => true);
    vi.spyOn(roomStore, 'createSubVenue').mockImplementation(async (payload) => true);
    vi.spyOn(roomStore, 'deleteSubVenue').mockImplementation(async (subVenueId, parentRoomId) => true);
  });

  afterEach(() => {
    vi.clearAllMocks();
    wrapper.unmount();
  });

  const createWrapper = () => {
    return mount(RoomDetail, {
      global: {
        plugins: [getActivePinia()!],
      },
      attachTo: document.body, // Attach to the real DOM to handle teleport and other DOM-related issues
    });
  };

  describe('数据渲染', () => {
    it('onLoad 时应根据路由参数获取并渲染房间详情', async () => {
      wrapper = createWrapper();
      captureLifecycle().triggerOnLoad({ id: 'room1' });
      
      vi.runAllTimers();
      await flushPromises();

      expect(roomStore.fetchRoomById).toHaveBeenCalledWith('room1');

      // Use more robust selectors
      const infoItems = wrapper.findAll('.info-item');
      const roomNameItem = infoItems.find((item: DOMWrapper<Element>) => item.text().includes('房间名称'));
      const descriptionItem = infoItems.find((item: DOMWrapper<Element>) => item.text().includes('简介'));

      expect(roomNameItem.find('.info-value').text()).toBe('Main Room');
      expect(descriptionItem.find('.info-value').text()).toBe('Main Desc');
    });

    it('应正确渲染场次和分会场列表', async () => {
      wrapper = createWrapper();
      captureLifecycle().triggerOnLoad({ id: 'room1' });

      vi.runAllTimers();
      await flushPromises();

      expect(sessionStore.fetchSessionsByRoomId).toHaveBeenCalledWith('room1', { refresh: true });
      expect(roomStore.fetchSubVenues).toHaveBeenCalledWith('room1');

      const sessionRows = wrapper.findAll('.sessions-table .table-row');
      expect(sessionRows.length).toBe(2);
      // The mock session no longer has a title, so we check for the status instead.
      expect(sessionRows[0].text()).toContain('live');

      const subVenueRows = wrapper.findAll('.sub-venues-table .table-row');
      expect(subVenueRows.length).toBe(1);
      expect(subVenueRows[0].text()).toContain('Sub Venue 1');
    });

    it('在小程序上表格应展示为卡片式布局', async () => {
        wrapper = createWrapper();
        captureLifecycle().triggerOnLoad({ id: 'room1' });

        vi.runAllTimers();
        await flushPromises();

        const tableRow = wrapper.find('.sessions-table .table-row');
        expect(tableRow.find('[data-label="场次ID"]').exists()).toBe(true);
    });
  });

  describe('场次与分会场操作', () => {
    beforeEach(async () => {
        wrapper = createWrapper();
        captureLifecycle().triggerOnLoad({ id: 'room1' });
        vi.runAllTimers();
        await flushPromises();
    });

    it('应能打开、提交和关闭创建场次的模态框', async () => {
      await wrapper.find('.sessions-header').findComponent({ name: 'AppButton' }).trigger('click');
      await wrapper.vm.$nextTick();
      expect(wrapper.vm.isSessionModalVisible).toBe(true);

      // 填充表单并提交
      wrapper.vm.newSession.title = 'New Test Session';
      wrapper.vm.newSession.start_time = '2025-01-01 10:00:00';
      
      // Find the correct modal and emit the confirm event
      const createSessionModal = wrapper.findAllComponents({ name: 'ModalDialog' }).find((m: VueWrapper<any>) => m.props('title') === '创建新场次');
      await createSessionModal.vm.$emit('confirm');
      await wrapper.vm.$nextTick();

      expect(sessionStore.createSession).toHaveBeenCalled();
      expect(uni.showToast).toHaveBeenCalledWith({ title: '创建成功', icon: 'success' });
      expect(wrapper.vm.isSessionModalVisible).toBe(false);
    });

    it('当场次状态不为 live 时，点击“播放”按钮应提示用户', async () => {
      const scheduledSessionRow = wrapper.findAll('.sessions-table .table-row')[1];
      const playButton = scheduledSessionRow.findAllComponents({ name: 'AppButton' }).find((b: VueWrapper<any>) => b.text() === '播放');
      await playButton.trigger('click');

      vi.runAllTimers();
      await flushPromises();

      expect(uni.navigateTo).not.toHaveBeenCalled();
      expect(uni.showToast).toHaveBeenCalledWith(expect.objectContaining({ title: expect.stringContaining('无法直播') }));
    });

    it('当场次状态为 live 时，点击“播放”按钮应跳转页面', async () => {
      const liveSessionRow = wrapper.findAll('.sessions-table .table-row')[0];
      const playButton = liveSessionRow.findAllComponents({ name: 'AppButton' }).find((b: VueWrapper<any>) => b.text() === '播放');
      await playButton.trigger('click');

      vi.runAllTimers();
      await flushPromises();

      expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/live/LiveView?id=session1' });
    });

    it('应能成功删除场次', async () => {
      const firstSessionRow = wrapper.findAll('.sessions-table .table-row')[0];
      const deleteButton = firstSessionRow.findAllComponents({ name: 'AppButton' }).find((b: VueWrapper<any>) => b.text() === '删除');
      await deleteButton.trigger('click');

      // The uni.showModal mock automatically confirms, triggering the delete operation.
      vi.runAllTimers();
      await flushPromises();

      expect(uni.showModal).toHaveBeenCalled();
      expect(sessionStore.deleteSession).toHaveBeenCalledWith('session1', 'room1');
      expect(uni.showToast).toHaveBeenCalledWith({ title: '删除成功', icon: 'success' });
    });

    it('应能成功创建和删除分会场', async () => {
        // 创建
        await wrapper.find('.sub-venues-header').findComponent({ name: 'AppButton' }).trigger('click');
        await wrapper.vm.$nextTick();
        expect(wrapper.vm.isSubVenueModalVisible).toBe(true);

        wrapper.vm.newSubVenue.title = 'New Sub Venue';

        // Find the correct modal and emit the confirm event
        const createSubVenueModal = wrapper.findAllComponents({ name: 'ModalDialog' }).find((m: VueWrapper<any>) => m.props('title') === '创建分会场');
        await createSubVenueModal.vm.$emit('confirm');
        await wrapper.vm.$nextTick();

        expect(roomStore.createSubVenue).toHaveBeenCalled();
        expect(uni.showToast).toHaveBeenCalledWith({ title: '创建成功', icon: 'success' });

        // Reset the mock before the next assertion
        vi.mocked(uni.showToast).mockClear();

        // 删除
        const deleteButton = wrapper.find('.sub-venues-table .table-row').findAllComponents({ name: 'AppButton' }).find((b: VueWrapper<any>) => b.text() === '删除');
        await deleteButton.trigger('click');

        // The uni.showModal mock automatically confirms and awaits the async success callback.
        // We need to advance timers to handle the setTimeout within that callback.
        vi.runAllTimers();
        // Finally, wait for any promises created by the timer's execution to resolve.
        await flushPromises();

        expect(uni.showModal).toHaveBeenCalled();
        expect(roomStore.deleteSubVenue).toHaveBeenCalledWith('sub1', 'room1');
        expect(uni.showToast).toHaveBeenCalledWith({ title: '删除成功', icon: 'success' });
    });
  });
});

