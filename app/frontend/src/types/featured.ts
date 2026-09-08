/**
 * 焦点图类型定义
 * 阶段一新建：2025
 * 数据来源：后端文档Section 2.10 featured_content表
 */

/**
 * 首页精选/焦点图内容
 * @description 对应后端 GET /api/v1/featured-content 返回的数据结构
 * @see 后端文档 Section 4.7.1
 */
export interface FeaturedContent {
  /** 主键UUID */
  id: string;
  /** 焦点图标题 */
  title: string;
  /** 焦点图副标题（可选） */
  subtitle?: string | null;
  /** 焦点图图片URL */
  image_url: string;
  /** 目标类型：room/session/topic/brand/expert/external */
  target_type: string | null;
  /** 目标ID，根据target_type指向对应表的id */
  target_id: string | null;
  /** 外部链接URL（当target_type为external时使用） */
  target_url: string | null;
  /** 排序权重，数字越小越靠前 */
  sort_order: number;
  /** 是否启用（管理员可下架，不删除记录） */
  is_active: boolean;
  /** 动态时间状态（管理员列表接口返回）：active=正在展示，upcoming=待上线，expired=已过期，inactive=已下线（含到期自动下线） */
  status?: 'active' | 'upcoming' | 'expired' | 'inactive' | null;
  /** 定时上线时间（ISO 8601） */
  start_at: string | null;
  /** 定时下线时间（ISO 8601） */
  end_at: string | null;
  /** 创建时间（ISO 8601） */
  created_at: string;
  /** 更新时间（ISO 8601） */
  updated_at: string;
}

/**
 * 创建焦点图请求体（管理员API）
 * @description 注意：此接口为管理员专用，普通用户不可访问
 */
export interface FeaturedContentCreatePayload {
  /** 焦点图标题（必填） */
  title: string;
  /** 焦点图副标题（可选） */
  subtitle?: string;
  /** 焦点图图片URL（必填） */
  image_url: string;
  /** 目标类型（可选）：session/topic/external */
  target_type?: string;
  /** 目标ID（可选） */
  target_id?: string;
  /** 外部链接（可选） */
  target_url?: string;
  /** 排序权重（可选，默认0） */
  sort_order?: number;
  /** 是否启用 */
  is_active?: boolean;
  /** 定时上线时间（ISO 8601） */
  start_at?: string;
  /** 定时下线时间（ISO 8601） */
  end_at?: string;
}

/**
 * 更新焦点图请求体（管理员API）
 * @description 所有字段可选，注意：此接口为管理员专用
 */
export interface FeaturedContentUpdatePayload {
  /** 焦点图标题 */
  title?: string;
  /** 焦点图副标题 */
  subtitle?: string;
  /** 焦点图图片URL */
  image_url?: string;
  /** 目标类型 */
  target_type?: string;
  /** 目标ID */
  target_id?: string;
  /** 外部链接 */
  target_url?: string;
  /** 排序权重 */
  sort_order?: number;
  /** 是否启用 */
  is_active?: boolean;
  /** 定时上线时间（ISO 8601）；传 null 表示即时上线 */
  start_at?: string | null;
  /** 定时下线时间（ISO 8601）；传 null 表示长期有效（清空过期 end_at） */
  end_at?: string | null;
}
