/**
 * 标签类型定义
 * 阶段一新建：2025
 * 数据来源：后端文档Section 2.1 tags表 + Section 2.6 session_tags表
 */

/**
 * 内容标签
 * 对应数据库表：tags
 * 用于多对多关联live_sessions等
 */
export interface Tag {
  /** 主键UUID */
  id: string;
  /** 标签名称，全局唯一 */
  name: string;
  /** URL友好的标识符，用于前端路由 */
  slug: string | null;
  /** 标签描述 */
  description: string | null;
  /** 是否启用：true=可用，false=已隐藏（软删除） */
  is_active: boolean;
  /** 创建时间（ISO 8601格式） */
  created_at: string;
  /** 更新时间（ISO 8601格式） */
  updated_at: string;
  /** 来源：admin=运营创建；user=用户 resolve 自建（V2 审计字段，可选） */
  source?: string | null;
  /** 创建者 user_id（V2 审计字段，可选；旧数据/部分响应可能不返回） */
  created_by?: string | null;
}

/**
 * 标签 chip（页面已选标签的最小单元）
 * 仅消费 id/name；resolve 结果与词表项均可转换为此形态
 */
export interface TagChip {
  /** 标签ID（UUID） */
  id: string;
  /** 标签名称（展示用原名） */
  name: string;
}

/**
 * resolve（解析或创建标签）响应 data
 * 对应后端 POST /content/tags/resolve → data: { id, name, created, source }
 */
export interface TagResolveResult {
  /** 标签ID（命中复用同一 id，不产生重复词） */
  id: string;
  /** 标签名称（后端 strip 后原样） */
  name: string;
  /** true=本次新建（source=user）；false=命中已有（复用） */
  created: boolean;
  /** admin | user */
  source?: string | null;
}

/**
 * 创建标签请求体
 */
export interface TagCreatePayload {
  /** 标签名称（必填） */
  name: string;
  /** URL友好的标识符（可选） */
  slug?: string;
  /** 标签描述（可选） */
  description?: string;
}

/**
 * 更新标签请求体
 * 所有字段可选
 */
export interface TagUpdatePayload {
  /** 标签名称 */
  name?: string;
  /** URL友好的标识符 */
  slug?: string;
  /** 标签描述 */
  description?: string;
  /** 是否启用 */
  is_active?: boolean;
}

/**
 * 场次-标签关联
 * 对应数据库表：session_tags
 * 用于直播场次与标签的多对多关联
 */
export interface SessionTag {
  /** 场次ID */
  session_id: string;
  /** 标签ID */
  tag_id: string;
  /** 创建时间（ISO 8601格式） */
  created_at: string;
}

/**
 * 为直播场次批量设置标签请求体
 * mode: replace=整体替换（传空列表表示清空）；append=追加（去重后仍受 0~5 上限约束）
 */
export interface SessionTagsPayload {
  /** 标签ID列表（0~5；replace 传空列表表示清空） */
  tag_ids: string[];
  /** 操作模式 */
  mode: 'replace' | 'append';
}
