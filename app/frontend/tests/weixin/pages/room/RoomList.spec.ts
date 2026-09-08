import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import { setActivePinia, getActivePinia } from 'pinia';
import { useRoomStore } from '@/store/room';
import type { Room } from '@/types/room';

import RoomList from '@/pages/room/new/RoomList.vue';

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
  onPullDownRefresh: [],
  onReachBottom: []
};

vi.mock('@dcloudio/uni-app', () => ({
  onLoad: (cb: (options?: any) => void) => lifecycles.onLoad.push(cb),
  onPullDownRefresh: (cb: () => void) => lifecycles.onPullDownRefresh.push(cb),
  onReachBottom: (cb: () => void) => lifecycles.onReachBottom.push(cb)
}));

const captureLifecycle = () => ({
  triggerOnLoad: (options?: any) => lifecycles.onLoad.forEach(cb => cb(options)),
  triggerOnPullDown: () => lifecycles.onPullDownRefresh.forEach(cb => cb()),
  triggerOnReachBottom: () => lifecycles.onReachBottom.forEach(cb => cb()),
  reset: () => {
    lifecycles.onLoad = [];
    lifecycles.onPullDownRefresh = [];
    lifecycles.onReachBottom = [];
  }
});

const createUniMock = () => ({
  navigateTo: vi.fn(),
  showToast: vi.fn(),
  showModal: vi.fn((options) => {
    // 模拟用户点击确认
    if (options.success) {
      options.success({ confirm: true, cancel: false });
    }
  }),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
  stopPullDownRefresh: vi.fn(),
});

vi.useFakeTimers();

const mockRooms: Room[] = [
  { id: '1', title: 'Room 1', description: 'Desc 1', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), is_private: false, record_by_default: false, stream_key: 'stream_key_1' },
  { id: '2', title: 'Room 2', description: 'Desc 2', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), is_private: false, record_by_default: false, stream_key: 'stream_key_2' },
];

describe('RoomList.vue (WeChat Mini Program)', () => {
  let wrapper: any;
  let roomStore: ReturnType<typeof useRoomStore>;

  beforeEach(() => {
    // @ts-ignore
    global.uni = createUniMock();
    captureLifecycle().reset();

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      stubActions: false, // 我们需要测试 action 的调用
    });
    setActivePinia(pinia);

    roomStore = useRoomStore();
    roomStore.rooms = [];
    roomStore.pagination = { page: 1, size: 10, total: 0, hasMore: false };
    roomStore.loading = false;
    roomStore.error = null;

    // Mock store actions
    vi.spyOn(roomStore, 'fetchRooms').mockResolvedValue();
    vi.spyOn(roomStore, 'addNewRoom').mockImplementation(async (payload) => true);
    vi.spyOn(roomStore, 'updateRoom').mockImplementation(async (id, payload) => true);
    vi.spyOn(roomStore, 'deleteRoom').mockImplementation(async (id) => true);
    vi.spyOn(roomStore, 'checkRoomHasSessions').mockResolvedValue(false);
    vi.spyOn(roomStore, 'fetchRoomById').mockImplementation(async (id: string) => {
      const room = mockRooms.find(r => r.id === id);
      roomStore.currentRoom = room || null;
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    wrapper.unmount();
  });

  const createWrapper = () => {
    return mount(RoomList, {
      global: {
        plugins: [getActivePinia()!],
      },
      attachTo: document.body, // 附加到真实 DOM 以测试 teleport
    });
  };

  describe('页面渲染与交互', () => {
    it('应正确渲染房间列表', async () => {
      roomStore.rooms = mockRooms;
      wrapper = createWrapper();
      await wrapper.vm.$nextTick();

      const roomItems = wrapper.findAll('.room-item');
      expect(roomItems.length).toBe(2);
      expect(roomItems[0].find('.room-title').text()).toBe('Room 1');
      expect(roomItems[1].find('.room-title').text()).toBe('Room 2');
    });

    it('在移动端（小程序）应显示“更多”操作按钮', async () => {
      roomStore.rooms = [mockRooms[0]];
      wrapper = createWrapper();
      await wrapper.vm.$nextTick();
      
      // 样式控制显示/隐藏，直接查找 DOM 元素
      const mobileActions = wrapper.find('.mobile-actions');
      expect(mobileActions.exists()).toBe(true);
      expect(mobileActions.find('.more-button').exists()).toBe(true);
    });

    it('点击“更多”按钮应弹出操作菜单', async () => {
      roomStore.rooms = [mockRooms[0]];
      wrapper = createWrapper();
      await wrapper.vm.$nextTick();

      expect(wrapper.find('.action-menu-overlay').exists()).toBe(false);

      await wrapper.find('.more-button').trigger('click');
      await wrapper.vm.$nextTick();

      expect(wrapper.vm.isActionMenuVisible).toBe(true);
      expect(wrapper.find('.action-menu-overlay').exists()).toBe(true);
      expect(wrapper.find('.action-menu-title').text()).toBe('操作菜单');
    });

    it('从操作菜单中可以触发编辑流程', async () => {
      roomStore.rooms = [mockRooms[0]];
      wrapper = createWrapper();
      await wrapper.vm.$nextTick();

      await wrapper.find('.more-button').trigger('click');
      vi.runAllTimers(); // 运行所有定时器
      await flushPromises(); // 等待 DOM 更新

      // 修正选择器：通过 findAll 获取所有菜单项，然后选择第一个（编辑）
      const actionItems = wrapper.findAll('.action-menu-item');
      await actionItems[0].trigger('click');
      await wrapper.vm.$nextTick();

      expect(roomStore.fetchRoomById).toHaveBeenCalledWith('1');
      await wrapper.vm.$nextTick(); // 等待 fetchRoomById 完成

      expect(wrapper.vm.isModalVisible).toBe(true);
      expect(wrapper.vm.modalTitle).toBe('编辑房间');
      expect(wrapper.vm.formModel.title).toBe('Room 1');
    });

    it('从操作菜单中可以触发删除流程', async () => {
      roomStore.rooms = [mockRooms[0]];
      wrapper = createWrapper();
      await wrapper.vm.$nextTick();

      await wrapper.find('.more-button').trigger('click');
      vi.runAllTimers(); // 运行所有定时器
      await flushPromises(); // 等待 DOM 更新

      // 修正选择器：通过 findAll 获取所有菜单项，然后选择第二个（删除）
      const actionItems = wrapper.findAll('.action-menu-item');
      await actionItems[1].trigger('click');
      await wrapper.vm.$nextTick();

      expect(roomStore.checkRoomHasSessions).toHaveBeenCalledWith('1');
      await wrapper.vm.$nextTick();
      
      expect(uni.showModal).toHaveBeenCalledWith(expect.objectContaining({ title: '确认删除' }));
      
      // 模拟确认删除
      await wrapper.vm.handleDeleteRoom('1');
      expect(roomStore.deleteRoom).toHaveBeenCalledWith('1');
    });
  });

  describe('房间操作', () => {
    it('点击悬浮按钮应打开创建房间模态框', async () => {
      wrapper = createWrapper();
      expect(wrapper.vm.isModalVisible).toBe(false);

      // 修正选择器：通过 findComponent 查找 AppButton 组件
      await wrapper.findComponent({ name: 'AppButton' }).trigger('click');
      await wrapper.vm.$nextTick();

      expect(wrapper.vm.isModalVisible).toBe(true);
      expect(wrapper.vm.modalTitle).toBe('创建新房间');
    });

    it('应能成功创建房间，并刷新列表', async () => {
      wrapper = createWrapper();
      await wrapper.findComponent({ name: 'AppButton' }).trigger('click');
      await wrapper.vm.$nextTick();

      // 填充表单
      wrapper.vm.formModel.title = 'New Room';
      wrapper.vm.formModel.description = 'New Desc';
      
      // 触发确认
      // 由于 ModalDialog 使用 teleport，我们需要在 document 中查找按钮
      const confirmButton = document.querySelector('.confirm-button');
      if (confirmButton) {
        (confirmButton as HTMLElement).click();
      } else {
        throw new Error('找不到确认按钮');
      }
      await wrapper.vm.$nextTick();

      expect(roomStore.addNewRoom).toHaveBeenCalledWith({ title: 'New Room', description: 'New Desc' });
      await wrapper.vm.$nextTick();

      expect(roomStore.fetchRooms).toHaveBeenCalledWith({ refresh: true });
      expect(uni.showToast).toHaveBeenCalledWith({ title: '创建成功', icon: 'success' });
      expect(wrapper.vm.isModalVisible).toBe(false);
    });

    it('删除有场次的房间时应显示提示', async () => {
      vi.spyOn(roomStore, 'checkRoomHasSessions').mockResolvedValue(true);
      roomStore.rooms = [mockRooms[0]];
      wrapper = createWrapper();
      await wrapper.vm.$nextTick();

      // 直接调用方法进行测试，因为 confirmDelete 依赖于参数
      await wrapper.vm.confirmDelete(mockRooms[0]);
      await wrapper.vm.$nextTick();

      expect(roomStore.checkRoomHasSessions).toHaveBeenCalledWith('1');
      expect(uni.showModal).toHaveBeenCalledWith(expect.objectContaining({ title: '无法删除' }));
    });
  });

  describe('生命周期', () => {
    it('onLoad 时应调用 fetchRooms 获取数据', () => {
      wrapper = createWrapper();
      captureLifecycle().triggerOnLoad();
      expect(roomStore.fetchRooms).toHaveBeenCalledWith({ refresh: true });
    });

    it('onPullDownRefresh 时应刷新列表', async () => {
      wrapper = createWrapper();
      captureLifecycle().triggerOnPullDown();
      await wrapper.vm.$nextTick();

      expect(roomStore.fetchRooms).toHaveBeenCalledWith({ refresh: true });
      expect(uni.stopPullDownRefresh).toHaveBeenCalled();
    });

    it('onReachBottom 时应加载下一页', () => {
      roomStore.pagination.hasMore = true;
      roomStore.loading = false;
      wrapper = createWrapper();

      captureLifecycle().triggerOnReachBottom();
      expect(roomStore.fetchRooms).toHaveBeenCalled();
    });

    it('onReachBottom 在加载中或没有更多数据时不应触发加载', () => {
      wrapper = createWrapper();

      // Case 1: loading is true
      roomStore.pagination.hasMore = true;
      roomStore.loading = true;
      captureLifecycle().triggerOnReachBottom();
      expect(roomStore.fetchRooms).not.toHaveBeenCalled();

      // Case 2: hasMore is false
      roomStore.pagination.hasMore = false;
      roomStore.loading = false;
      captureLifecycle().triggerOnReachBottom();
      expect(roomStore.fetchRooms).not.toHaveBeenCalled();
    });
  });
});

