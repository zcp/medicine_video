/**
 * 用户收藏类型定义
 * 阶段一新建：2025
 * 数据来源：后端文档Section 2.7 user_favorites表
 */

/**
 * 用户收藏记录
 * 对应数据库表：user_favorites
 * 用户可以收藏直播间
 */
export interface Favorite {
  /** 主键UUID */
  id: string;
  /** 用户公开ID（users.public_id），JWT Token的sub字段值 */
  user_id: string;
  /** 房间ID，关联live_rooms表 */
  room_id: string;
  /** 是否有效：true=已收藏，false=已取消（软删除） */
  is_active: boolean;
  /** 创建时间（ISO 8601格式） */
  created_at: string;
}

/**
 * 创建收藏请求体
 */
export interface FavoriteCreatePayload {
  /** 房间ID（必填） */
  room_id: string;
}

/**
 * 收藏列表项（前端展示）
 * 包含房间的基本信息
 */
export interface FavoriteWithRoom extends Favorite {
  /** 房间标题 */
  room_title?: string;
  /** 房间封面URL */
  room_cover_url?: string;
  /** 房间直播状态 */
  room_live_status?: string;
  /** 专家姓名 */
  expert_name?: string;
  /** 专家头像 */
  expert_avatar?: string;
  /** 专家职称 */
  expert_title?: string;
  /** 专家医院 */
  expert_hospital?: string;
  /** 专家科室 */
  expert_department?: string;
  /** 时长（秒） */
  duration?: number;
  /** 观看数 */
  view_count?: number;
  /** 评论数 */
  comment_count?: number;
}
