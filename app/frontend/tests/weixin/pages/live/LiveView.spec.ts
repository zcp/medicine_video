import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import { setActivePinia, getActivePinia } from 'pinia';
import { useSessionStore } from '@/store/session';
import { useRoomStore } from '@/store/room';
import * as roomApi from '@/api/room';
import type { Session } from '@/types/session';
import type { Room } from '@/types/room';

import LiveView from '@/pages/live/LiveView.vue';

// Mock 子组件
vi.mock('@/components/VideoPlayer.vue', () => ({
  default: {
    name: 'VideoPlayer',
    template: '<div>Mocked VideoPlayer</div>',
  }
}));

vi.mock('@/components/AppButton.vue', () => ({
  default: {
    name: 'AppButton',
    template: '<button @click="$emit(\'click\')"><slot /></button>',
    props: ['type', 'size', 'disabled']
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
});

const mockSession: Session = { id: 'session1', room_id: 'room1', status: 'live', start_time: '2024-01-01T00:00:00Z', end_time: null, video_id: null, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' };
const mockRoomDetail = { data: { id: 'room1', description: 'Room Description' } };
const now = new Date();
const mockRecommendedRooms: Room[] = [
    { id: 'room2', title: 'Recommended Room 1', description: 'Rec Desc 1', created_at: now.toISOString(), updated_at: now.toISOString(), is_private: false, record_by_default: false, stream_key: 'stream_key_2' },
    { id: 'room3', title: 'Recommended Room 2', description: 'Rec Desc 2', created_at: new Date(now.getTime() - 1000).toISOString(), updated_at: new Date(now.getTime() - 1000).toISOString(), is_private: false, record_by_default: false, stream_key: 'stream_key_3' },
];

vi.useFakeTimers();

describe('LiveView.vue (WeChat Mini Program)', () => {
  let wrapper: any;
  let sessionStore: ReturnType<typeof useSessionStore>;
  let roomStore: ReturnType<typeof useRoomStore>;

  beforeEach(() => {
    // @ts-ignore
    global.uni = createUniMock();
    captureLifecycle().reset();

    const pinia = createTestingPinia({ createSpy: vi.fn, stubActions: false });
    setActivePinia(pinia);

    sessionStore = useSessionStore();
    roomStore = useRoomStore();

    // Mock store state
    sessionStore.currentSession = null;
    sessionStore.loading = true;
    sessionStore.error = null;
    roomStore.rooms = [];

    // Mock store actions
    vi.spyOn(sessionStore, 'fetchSessionById').mockImplementation(async (id) => {
        if (id === mockSession.id) sessionStore.currentSession = mockSession;
        sessionStore.loading = false;
    });
    vi.spyOn(roomStore, 'fetchRooms').mockImplementation(async () => {
        roomStore.rooms = mockRecommendedRooms;
    });

    // Mock API
    vi.spyOn(roomApi, 'getRoomDetail').mockResolvedValue(mockRoomDetail as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
    wrapper.unmount();
  });

  const createWrapper = () => {
    return mount(LiveView, {
      global: {
        plugins: [getActivePinia()!],
        stubs: {
          // Stub the VideoPlayer to prevent it from rendering in the non-H5 test env
          VideoPlayer: {
            template: '<!-- VideoPlayer stub -->',
          },
        },
      }
    });
  };

  describe('页面渲染与平台差异', () => {
    it('onLoad 时应根据路由参数获取场次信息和房间详情', async () => {
      wrapper = createWrapper();
      captureLifecycle().triggerOnLoad({ id: 'session1' });
      await wrapper.vm.$nextTick();

      expect(sessionStore.fetchSessionById).toHaveBeenCalledWith('session1');
      await wrapper.vm.$nextTick(); // wait for session fetch

      expect(roomApi.getRoomDetail).toHaveBeenCalledWith('room1');
      vi.runAllTimers();
      await flushPromises();

      expect(wrapper.find('.description-content').text()).toBe('Room Description');
    });

    it('在小程序环境下不应渲染返回按钮', async () => {
        sessionStore.currentSession = mockSession;
        sessionStore.loading = false;
        wrapper = createWrapper();
        await wrapper.vm.$nextTick();

        const backButtons = wrapper.findAll('.header-left .app-button');
        expect(backButtons.length).toBe(0);
    });

    it('在小程序环境下不应渲染 VideoPlayer 组件', async () => {
        sessionStore.currentSession = mockSession;
        sessionStore.loading = false;
        wrapper = createWrapper();
        await wrapper.vm.$nextTick();

        const videoPlayer = wrapper.findComponent({ name: 'VideoPlayer' });
        expect(videoPlayer.exists()).toBe(false);
        const iframe = wrapper.find('iframe');
        expect(iframe.exists()).toBe(false);
    });

    it('在小程序上应展示为上下垂直布局', async () => {
        sessionStore.currentSession = mockSession;
        sessionStore.loading = false;
        wrapper = createWrapper();
        await wrapper.vm.$nextTick();

        const contentContainer = wrapper.find('.content-container');
        expect(contentContainer.find('.left-section').exists()).toBe(true);
        expect(contentContainer.find('.recommendations-section').exists()).toBe(true);
    });
  });

  describe('功能交互', () => {
    beforeEach(async () => {
        wrapper = createWrapper();
        captureLifecycle().triggerOnLoad({ id: 'session1' });
        await flushPromises();
    });

    it('应正确显示房间简介和模拟评论', () => {
      expect(wrapper.find('.description-content').text()).toBe('Room Description');
      const comments = wrapper.findAll('.comment-card');
      expect(comments.length).toBe(3);
      expect(comments[0].text()).toContain('用户小白');
    });

    it('应正确显示推荐房间列表', async () => {
        await wrapper.vm.$nextTick();
        expect(roomStore.fetchRooms).toHaveBeenCalled();
        await wrapper.vm.$nextTick();

        const recommendedCards = wrapper.findAll('.recommendations-section .room-card');
        expect(recommendedCards.length).toBe(2);
        expect(recommendedCards[0].find('.room-title').text()).toBe('Recommended Room 1');
    });

    it('点击推荐房间应能跳转到对应的房间详情页', async () => {
        await wrapper.vm.$nextTick();
        await wrapper.vm.$nextTick();

        const firstRecommendedCard = wrapper.find('.recommendations-section .room-card');
        await firstRecommendedCard.trigger('click');

        expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/room/RoomDetail?id=room2' });
    });
  });
});