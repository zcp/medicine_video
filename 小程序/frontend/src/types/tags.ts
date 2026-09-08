/**
 * 标签管理（Tag）类型定义
 * 以后端设计文档为准：tags 表 DDL + Pydantic Schema
 * 参考：《02-标签管理-后端设计文档.md》
 *
 * DDL: tags 表
 *   id UUID PK, name VARCHAR(100), slug VARCHAR(100) NOT NULL UNIQUE,
 *   description TEXT, is_active BOOLEAN DEFAULT TRUE,
 *   created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
 * V2 可选：created_by, source（admin|user）
 */

/**
 * 标签信息（对应后端 TagItem Schema）
 */
export interface Tag {
  /** 标签唯一标识（UUID） */
  id: string
  /** 标签名称（1-100字符） */
  name: string
  /** URL友好标识（必填，唯一，仅小写字母+数字+连字符） */
  slug: string
  /** 标签描述 */
  description?: string
  /** 是否启用状态（软删除标记） */
  is_active: boolean
  /** 创建时间（ISO 8601格式） */
  created_at: string
  /** 最后更新时间（ISO 8601格式） */
  updated_at: string
  /** 来源（V2 可选）：admin=运营创建；user=用户 resolve */
  source?: 'admin' | 'user' | string
  /** 创建者 public_id（V2 可选） */
  created_by?: string | null
}

/**
 * 创建标签请求参数（对应后端 TagCreate Schema）
 */
export interface TagCreate {
  /** 标签名称（必填，1-100字符） */
  name: string
  /** URL友好标识（必填，唯一） */
  slug: string
  /** 标签描述（可选） */
  description?: string
  /** 是否启用状态（可选，默认true） */
  is_active?: boolean
}

/**
 * 更新标签请求参数（对应后端 TagUpdate Schema）
 */
export interface TagUpdate {
  /** 标签名称（可选） */
  name?: string
  /** URL友好标识（可选） */
  slug?: string
  /** 标签描述（可选） */
  description?: string
  /** 是否启用状态（可选） */
  is_active?: boolean
}

/**
 * 标签列表查询参数
 */
export interface TagListParams {
  /** 搜索关键词（匹配name、slug、description） */
  q?: string
  /** 搜索类型 */
  search_type?: 'name' | 'slug' | 'description'
  /** 是否包含已禁用的标签 */
  include_inactive?: boolean
}

/** 单场次标签上限（《02-V2》SESSION_TAGS_MAX） */
export const SESSION_TAGS_MAX = 5

/**
 * 解析或创建标签请求（《02-V2》TagResolveRequest）
 * name：1～80；服务端 strip；禁 <>'";
 */
export interface TagResolveRequest {
  name: string
}

/**
 * 解析或创建标签响应 data（《02-V2》TagResolveData）
 */
export interface TagResolveData {
  id: string
  name: string
  /** true=本次新建；false=命中已有 */
  created: boolean
  source?: string | null
}

/**
 * 场次标签关联设置请求（对应后端 SessionTagsSetRequest Schema）
 * tag_ids：0～5；[] + replace = 清空
 */
export interface SessionTagsSetRequest {
  /** 标签UUID列表（0～5；元素须为真实 UUID） */
  tag_ids: string[]
  /** 关联模式：replace=替换, append=追加；开播主路径固定 replace */
  mode: 'replace' | 'append'
}

/**
 * 场次标签关联项（对应后端 SessionTagItem Schema）
 */
export interface SessionTagItem {
  /** 场次UUID */
  session_id: string
  /** 标签UUID */
  tag_id: string
  /** 标签名称 */
  tag_name: string
  /** 标签Slug */
  tag_slug: string
  /** 关联创建时间 */
  created_at: string
}

/**
 * 按标签搜索场次请求参数（对应后端 TagSearchParams Schema）
 */
export interface TagSearchParams {
  /** 标签UUID列表（至少1个） */
  tag_ids: string[]
  /** true=AND模式（必须匹配所有标签），false=OR模式（匹配任一标签） */
  match_all: boolean
  /** 页码，默认1 */
  page?: number
  /** 每页数量，默认20 */
  page_size?: number
}

/**
 * 搜索结果项（对应后端 SearchResultItem Schema）
 */
export interface SearchResultItem {
  /** 场次UUID */
  session_id: string
  /** 场次标题 */
  title: string
  /** 匹配到的标签名称列表 */
  matched_tags: string[]
  /** 匹配分数（匹配标签数/总搜索标签数） */
  score: number
}
