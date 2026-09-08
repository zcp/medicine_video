/**
 * 分类类型定义
 * 阶段一新建：2025
 * 数据来源：后端文档Section 2.2 categories表
 */

/**
 * 全局医学内容分类
 * 对应数据库表：categories
 * 如：肝胆胰外科、胃肠外科等
 */
export interface Category {
  /** 主键UUID */
  id: string;
  /** 父分类ID（null=一级科目，非null=二级科目） */
  parent_id: string | null;
  /** 分类名称（标准名，驱动匹配，全局唯一） */
  name: string;
  /** 口语名（C端展示用）；NULL 回退 name */
  display_name?: string | null;
  /** 标准科目标记：true=name 命中名录标准名清单；false=扩展科目（如"其他"） */
  standard?: boolean;
  /** URL友好的标识符 */
  slug: string | null;
  /** 分类图标名称或URL */
  icon: string | null;
  /** 分类描述 */
  description: string | null;
  /** 排序权重，数字越小越靠前，用于前端展示顺序 */
  sort_order: number;
  /** 是否启用：true=前端可见，false=已下线（软删除） */
  is_active: boolean;
  /** 创建时间（ISO 8601格式） */
  created_at: string;
  /** 更新时间（ISO 8601格式） */
  updated_at: string;
}

/**
 * 创建分类请求体
 */
export interface CategoryCreatePayload {
  /** 分类名称（标准名，必填） */
  name: string;
  /** 口语名（C端展示用，可选） */
  display_name?: string | null;
  /** 标准科目标记（可选，默认 true） */
  standard?: boolean;
  /** 父分类ID（可选，null=一级科目） */
  parent_id?: string | null;
  /** URL友好的标识符（可选） */
  slug?: string;
  /** 分类图标名称或URL（可选） */
  icon?: string;
  /** 分类描述（可选） */
  description?: string;
  /** 排序权重（可选，默认0） */
  sort_order?: number;
  /** 是否启用（可选，默认true） */
  is_active?: boolean;
}

/**
 * 更新分类请求体
 * 所有字段可选
 */
export interface CategoryUpdatePayload {
  /** 分类名称（标准名） */
  name?: string;
  /** 口语名（C端展示用） */
  display_name?: string | null;
  /** 标准科目标记 */
  standard?: boolean;
  /** 父分类ID */
  parent_id?: string | null;
  /** URL友好的标识符 */
  slug?: string;
  /** 分类图标名称或URL */
  icon?: string;
  /** 分类描述 */
  description?: string;
  /** 排序权重 */
  sort_order?: number;
  /** 是否启用 */
  is_active?: boolean;
}
