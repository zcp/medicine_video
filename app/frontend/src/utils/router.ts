/**
 * 统一路由工具
 * 根据平台自动选择正确的页面路径
 */
import { getPlatform } from '@/utils/platform';

/**
 * 获取平台专用页面路径前缀
 * @returns 页面路径前缀 (/pages/h5 或 /pages/app)
 */
export const getPageBasePath = (): string => {
  const platform = getPlatform();
  
  // #ifdef H5
  return '/pages/h5';
  // #endif
  
  // #ifndef H5
  return '/pages/app';
  // #endif
};

/**
 * 导航到房间列表
 */
export const navigateToRoomList = () => {
  // #ifdef H5
  uni.navigateTo({ url: '/pages/h5/room/RoomList' });
  // #endif
  // #ifndef H5
  uni.navigateTo({ url: '/pages/app/live-manage/list' });
  // #endif
};

/**
 * 导航到房间详情
 * @param roomId 房间ID
 */
export const navigateToRoomDetail = (roomId: string) => {
  // #ifdef H5
  // H5环境暂无RoomDetail页面，跳转到RoomManage
  uni.navigateTo({
    url: `/pages/h5/room/RoomManage?roomId=${roomId}`
  });
  // #endif
  
  // #ifndef H5
  // App环境使用RoomDetail
  uni.navigateTo({
    url: `/pages/app/live-manage/detail?id=${roomId}`
  });
  // #endif
};

/**
 * 导航到直播观看
 * @param sessionId 直播场次ID
 * @param roomId 房间ID（可选）
 */
export const navigateToLiveView = (sessionId: string, roomId?: string) => {
  let url = '';
  
  // #ifdef H5
  url = `/pages/h5/live/LiveView?id=${sessionId}`;
  // #endif
  // #ifndef H5
  url = `/pages/app/live/LiveView?id=${sessionId}`;
  // #endif
  
  if (roomId) {
    url += `&roomId=${roomId}`;
  }
  
  uni.navigateTo({ url });
};

/**
 * 导航到创建房间（H5专用）
 */
export const navigateToRoomCreate = () => {
  // #ifdef H5
  uni.navigateTo({
    url: '/pages/h5/room/RoomCreate'
  });
  // #endif
  
  // #ifndef H5
  console.warn('RoomCreate page is only available on H5 platform');
  // #endif
};

/**
 * 导航到房间管理（H5专用）
 * @param roomId 房间ID
 */
export const navigateToRoomManage = (roomId: string) => {
  // #ifdef H5
  uni.navigateTo({
    url: `/pages/h5/room/RoomManage?roomId=${roomId}`
  });
  // #endif
  
  // #ifndef H5
  console.warn('RoomManage page is only available on H5 platform');
  // #endif
};

/**
 * 导航到直播详情页（房间管理详情）
 * @param roomId 房间ID
 */
export const navigateToLiveDetail = (roomId: string) => {
  // #ifdef H5
  uni.navigateTo({
    url: `/pages/h5/room/RoomManage?roomId=${roomId}`
  });
  // #endif
  
  // #ifndef H5
  uni.navigateTo({
    url: `/pages/app/live-manage/detail?id=${roomId}`
  });
  // #endif
};

/**
 * 导航到专题列表（H5专用）
 */
export const navigateToTopicList = () => {
  // #ifdef H5
  uni.navigateTo({
    url: '/pages/h5/topic/TopicList'
  });
  // #endif
  
  // #ifndef H5
  console.warn('Topic pages are only available on H5 platform');
  // #endif
};

/**
 * 返回上一页
 */
export const navigateBack = () => {
  uni.navigateBack({
    delta: 1
  });
};

/**
 * 重定向到首页
 */
export const redirectToIndex = () => {
  uni.reLaunch({
    url: '/pages/shared/index/index'
  });
};

/**
 * 通用导航方法
 * @param path 相对路径（不包含平台前缀）
 * @param query 查询参数对象
 */
export const navigateTo = (path: string, query?: Record<string, any>) => {
  const basePath = getPageBasePath();
  let url = `${basePath}${path}`;
  
  if (import.meta.env.DEV) {
    if (!path.startsWith('/')) {
      console.warn(`[router:navigateTo] 路径格式异常（缺少前导斜杠）: ${path}`);
    }
  }
  
  // 拼接查询参数
  if (query) {
    const queryString = Object.entries(query)
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&');
    
    if (queryString) {
      url += `?${queryString}`;
    }
  }
  
  uni.navigateTo({ url });
};
