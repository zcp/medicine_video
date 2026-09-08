import { SessionStatus } from "./session";

/**
 * 直播房间的基础信息
 */
export interface Room {
  id: string;
  title: string;
  description?: string;
  cover_url?: string;
  is_private: boolean;
  record_by_default: boolean;
  stream_key: string;
  created_at: string;
  updated_at: string;
  live_status?: SessionStatus;
  current_session_id?: string;
  parent_room_id?: string; // 父房间ID，用于区分主会场和分会场
  // 阶段一补充字段（后端文档Section 2.1 live_rooms表）
  user_id: string | null;        // 用户公开ID，关联users.public_id
  owner_user_id?: string;        // 管理员接口使用，与user_id同语义
  // 前端展示字段（非数据库字段，可选）
  category_name?: string;        // 分类名称
  user_name?: string;            // 用户名
  user_avatar_url?: string | null; // 用户头像
}

/**
 * 创建直播房间时需要发送的数据载荷
 */
export interface RoomCreatePayload {
  title: string;
  description?: string;
  cover_url?: string;  // 封面URL（可选）
  is_private?: boolean;  // 私密房间（可选，默认 false）
  category_ids?: string[];  // 分类ID列表（可选，随创建写入分类关联）
} 