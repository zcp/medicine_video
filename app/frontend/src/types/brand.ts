/**
 * 品牌/合作伙伴类型定义
 * 阶段一新建：2025
 * 数据来源：后端文档Section 2.3 brands表 + Section 2.4 brand_topics表
 */

/**
 * 品牌/合作伙伴信息
 * 对应数据库表：brands
 */
export interface Brand {
  /** 主键UUID */
  id: string;
  /** 品牌名称，全局唯一 */
  name: string;
  /** URL友好的标识符 */
  slug: string | null;
  /** 品牌Logo图片URL */
  logo_url: string | null;
  /** 品牌描述 */
  description: string | null;
  /** 品牌官网链接 */
  website_url: string | null;
  /** 排序权重，数字越小越靠前 */
  sort_order: number;
  /** 是否启用：true=前端可见，false=已下线（软删除） */
  is_active: boolean;
  /** 创建时间（ISO 8601格式） */
  created_at: string;
  /** 更新时间（ISO 8601格式） */
  updated_at: string;
}

/**
 * 创建品牌请求体
 */
export interface BrandCreatePayload {
  /** 品牌名称（必填） */
  name: string;
  /** URL友好的标识符（可选） */
  slug?: string;
  /** 品牌Logo图片URL（可选） */
  logo_url?: string;
  /** 品牌描述（可选） */
  description?: string;
  /** 品牌官网链接（可选） */
  website_url?: string;
  /** 排序权重（可选，默认0） */
  sort_order?: number;
}

/**
 * 更新品牌请求体
 * 所有字段可选
 */
export interface BrandUpdatePayload {
  /** 品牌名称 */
  name?: string;
  /** URL友好的标识符 */
  slug?: string;
  /** 品牌Logo图片URL */
  logo_url?: string;
  /** 品牌描述 */
  description?: string;
  /** 品牌官网链接 */
  website_url?: string;
  /** 排序权重 */
  sort_order?: number;
  /** 是否启用 */
  is_active?: boolean;
}

/**
 * 品牌-专题关联
 * 对应数据库表：brand_topics
 */
export interface BrandTopic {
  /** 品牌ID */
  brand_id: string;
  /** 专题ID */
  topic_id: string;
  /** 创建时间（ISO 8601格式） */
  created_at: string;
}

/**
 * 批量关联专题到品牌请求体
 */
export interface BrandTopicsPayload {
  /** 专题ID列表 */
  topic_ids: string[];
}
