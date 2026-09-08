/**
 * Tab相关类型定义
 * 用于直播间Tab功能
 */

/**
 * Tab内容类型枚举
 */
export type TabContentType = 'text' | 'image' | 'mixed';

/**
 * Tab信息
 */
export interface Tab {
  /** Tab ID */
  id: string;
  /** 房间ID */
  room_id: string;
  /** Tab标识键（用于前端判断渲染哪种组件） */
  tab_key: string;
  /** Tab标题 */
  title: string;
  /** 内容类型 */
  content_type: TabContentType;
  /** 文字内容 */
  text_content: string | null;
  /** 图片URL */
  image_url: string | null;
  /** 排序顺序 */
  sort_order: number;
  /** 是否激活 */
  is_active: boolean;
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at: string;
}

/**
 * 创建Tab请求体
 */
export interface TabCreatePayload {
  /** Tab标识键 */
  tab_key: string;
  /** Tab标题 */
  title: string;
  /** 内容类型 */
  content_type: TabContentType;
  /** 文字内容（可选） */
  text_content?: string | null;
  /** 图片URL（可选） */
  image_url?: string | null;
  /** 排序顺序（可选） */
  sort_order?: number;
  /** 是否激活（可选） */
  is_active?: boolean;
}

/**
 * 更新Tab请求体
 */
export interface TabUpdatePayload {
  /** Tab标题（可选） */
  title?: string;
  /** 内容类型（可选） */
  content_type?: TabContentType;
  /** 文字内容（可选） */
  text_content?: string | null;
  /** 图片URL（可选） */
  image_url?: string | null;
  /** 排序顺序（可选） */
  sort_order?: number;
  /** 是否激活（可选） */
  is_active?: boolean;
}
