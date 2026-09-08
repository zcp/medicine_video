/**
 * 首页专用类型定义
 * @description 对应后端 API: GET /api/v1/homepage/rooms
 * @see 后端文档 Section 4.13.1
 */

/**
 * 首页直播状态枚举
 * @description 与通用 SessionStatus 不同，首页只区分三种状态
 */
export type HomepageLiveStatus = 'live' | 'scheduled' | 'replay';

/**
 * 首页主讲人信息
 * @description 优先级：featured_expert > 房主专家 > 房主用户
 */
export interface HomepageHost {
  /** 专家ID（如果是专家） */
  expert_id: string | null;
  /** 用户ID（如果是普通用户） */
  user_id: string | null;
  /** 主讲人姓名 */
  name: string;
  /** 职称（如：主任医师、教授） */
  title: string | null;
  /** 所在医院 */
  hospital: string | null;
  /** 主讲头像URL（后端可能缺失） */
  avatar_url?: string | null;
  /** 兼容字段：部分接口返回 avatar */
  avatar?: string | null;
}

/**
 * 首页状态数据
 * @description 根据 live_status 不同，不同字段会有值
 */
export interface HomepageStatusData {
  /** 当前观看人数（直播中时有值） */
  viewer_count: number | null;
  /** 计划开始时间（预告时有值） */
  start_time: string | null;
  /** 预告开始时间（预告时有值，与start_time同义） */
  scheduled_start_time: string | null;
  /** 回放时长（秒）（回放时有值） */
  duration_seconds: number | null;
  /** 回放播放次数（回放时有值） */
  play_count: number | null;
}

/**
 * 首页直播间卡片数据
 * @description 首页列表专用的精简数据结构
 */
export interface HomepageRoomItem {
  /** 直播间ID */
  id: string;
  /** 直播间标题 */
  title: string;
  /** 封面图URL */
  cover_url: string | null;
  /** 直播间简介摘要 */
  summary: string | null;
  /** 直播状态 */
  live_status: HomepageLiveStatus;
  /** 主讲人信息 */
  host: HomepageHost | null;
  /** 状态相关数据 */
  status_data: HomepageStatusData;
  /** 热度值（用于排序） */
  heat: number | null;
  /** 分类ID（用于分类筛选） */
  category_id?: string;
  /** 当前场次ID（后端可能按版本返回） */
  current_session_id?: string;
  /** 兼容字段：场次ID */
  session_id?: string;
  /** 兼容字段：最新场次ID */
  latest_session_id?: string;
}

/**
 * 首页直播间列表响应
 */
export interface HomepageRoomsResponse {
  total: number;
  page: number;
  size: number;
  items: HomepageRoomItem[];
}
