/**
 * 关注专家类型定义
 * 数据来源：后端文档Section 4.16 User Expert Follow模块
 */

/**
 * 关注专家请求体
 */
export interface ExpertFollowRequest {
  /** 专家ID（UUID格式） */
  expert_id: string;
}

/**
 * 关注专家响应
 */
export interface ExpertFollowResponse {
  /** 用户ID */
  user_id: string;
  /** 专家ID */
  expert_id: string;
  /** 关注时间（ISO 8601格式） */
  subscribed_at: string;
}

/**
 * 关注的专家列表项
 */
export interface FollowedExpertItem {
  /** 专家ID */
  expert_id: string;
  /** 专家姓名 */
  name: string;
  /** 职称（如：主任医师、教授） */
  title: string | null;
  /** 所在医院 */
  hospital: string | null;
  /** 所在科室（向后兼容，后端仍返回此字段） */
  department: string | null;
  /** 标准科室名称（新增，推荐使用） */
  department_name?: string | null;
  /** 头像URL */
  avatar_url: string | null;
  /** 关注时间（ISO 8601格式） */
  subscribed_at: string;
  /** 直播状态（可选） */
  live_status?: ExpertLiveStatus;
}

/**
 * 专家直播状态
 */
export interface ExpertLiveStatus {
  /** 是否正在直播 */
  is_live: boolean;
  /** 直播间ID */
  room_id: string;
  /** 场次ID */
  session_id: string;
  /** 直播标题 */
  title: string;
  /** 开播时间（ISO 8601格式） */
  started_at: string;
  /** 观看人数 */
  viewer_count: number;
}

/**
 * 检查关注状态响应
 */
export interface CheckFollowStatusResponse {
  /** 是否已关注 */
  is_followed: boolean;
}
