/**
 * 专家信息类型定义
 * 阶段一新建：2025
 * 数据来源：后端文档Section 2.5 experts表
 */

/**
 * 专家信息
 * 对应数据库表：experts
 * 注意：user_id关联平台用户的public_id，可为null表示外部专家
 */
export interface Expert {
  /** 主键UUID */
  id: string;
  /** 关联平台用户公开ID（users.public_id），可为空表示外部专家 */
  user_id: string | null;
  /** 专家姓名 */
  name: string;
  /** 职称（如：主任医师、教授） */
  title: string | null;
  /** 所在医院 */
  hospital: string | null;
  /** 所在科室（自由文本，已废弃，保留兼容） */
  department: string | null;
  /** 标准科室名称（来自 expert_departments 受控词表） */
  department_name: string | null;
  /** 科室ID */
  department_id: string | null;
  /** 主专业分类ID（来自 categories 表） */
  category_id: string | null;
  /** 分类名称（来自 categories 表） */
  category_name: string | null;
  /** 擅长领域，逗号分隔或JSON字符串 */
  expertise_areas: string | null;
  /** 专家简介 */
  bio: string | null;
  /** 专家头像URL */
  avatar_url: string | null;
  /** 是否为首页推荐专家 */
  is_featured: boolean;
  /** 是否启用（false=软删除，Admin不可见） */
  is_active: boolean;
  /** 是否已审核（false=待审批） */
  is_verified: boolean;
  /** 排序权重，数字越小越靠前 */
  sort_order: number;
  /** 联系方式，JSONB格式：{phone, email, office} */
  contact_info: Record<string, any> | null;
  /** 创建时间（ISO 8601格式） */
  created_at: string;
  /** 更新时间（ISO 8601格式） */
  updated_at: string;
  /** 是否已关注（前端扩展字段） */
  is_followed?: boolean;
  /** 专家角色（场次关联时的字段，如：主讲、主持、嘉宾） */
  role?: string;
}

/**
 * 创建专家请求体
 */
export interface ExpertCreatePayload {
  /** 关联平台用户公开ID（可选，外部专家可不填） */
  user_id?: string;
  /** 专家姓名（必填） */
  name: string;
  /** 职称（可选） */
  title?: string;
  /** 所在医院（可选） */
  hospital?: string;
  /** 所在科室（可选，已废弃） */
  department?: string;
  /** 标准科室名称（匹配 expert_departments 受控词表） */
  department_name?: string;
  /** 标准化科室ID（关联 expert_departments 表） */
  department_id?: string;
  /** 擅长领域（可选） */
  expertise_areas?: string;
  /** 专家简介（可选） */
  bio?: string;
  /** 专家头像URL（可选） */
  avatar_url?: string;
  /** 是否为首页推荐专家（可选，默认false） */
  is_featured?: boolean;
  /** 是否启用（可选，默认true） */
  is_active?: boolean;
  /** 审核状态（可选，默认false=待审批） */
  is_verified?: boolean;
  /** 排序权重（可选，默认0） */
  sort_order?: number;
  /** 联系方式（可选） */
  contact_info?: Record<string, any>;
}

/**
 * 更新专家请求体
 * 所有字段可选
 */
export interface ExpertUpdatePayload {
  /** 关联平台用户公开ID */
  user_id?: string;
  /** 专家姓名 */
  name?: string;
  /** 职称 */
  title?: string;
  /** 所在医院 */
  hospital?: string;
  /** 所在科室（已废弃） */
  department?: string;
  /** 标准科室名称（匹配 expert_departments 受控词表） */
  department_name?: string;
  /** 标准化科室ID（关联 expert_departments 表，Admin 分配科室时必传） */
  department_id?: string;
  /** 擅长领域 */
  expertise_areas?: string;
  /** 专家简介 */
  bio?: string;
  /** 专家头像URL */
  avatar_url?: string;
  /** 是否为首页推荐专家 */
  is_featured?: boolean;
  /** 是否启用（false=软删除/下架） */
  is_active?: boolean;
  /** 审核状态（false=待审批, true=已审批） */
  is_verified?: boolean;
  /** 排序权重 */
  sort_order?: number;
  /** 联系方式 */
  contact_info?: Record<string, any>;
}
