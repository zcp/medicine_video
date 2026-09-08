/**
 * 首页焦点图管理（Featured Content）类型定义
 * 以后端设计文档为准：featured_content 表 DDL + Pydantic Schema
 * 参考：《03-首页焦点图管理-后端设计文档.md》
 *
 * DDL: featured_content 表
 *   id UUID PK, title VARCHAR(200), subtitle VARCHAR(500), image_url VARCHAR(500),
 *   target_type VARCHAR(20) CHECK (room/session/brand/external)，历史数据可能含 topic/expert
 *   target_id UUID, target_url VARCHAR(1000),
 *   sort_order INTEGER, is_active BOOLEAN,
 *   start_at TIMESTAMPTZ, end_at TIMESTAMPTZ,
 *   created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
 *
 * 约束: external类型必须有target_url, 非external类型必须有target_id
 */

/**
 * 焦点图跳转目标类型（管理端可选）
 */
export type FeaturedContentTargetType = 'room' | 'session' | 'brand' | 'external'

/** 历史废弃类型，仅用于列表展示与 C 端忽略跳转 */
export type FeaturedContentLegacyTargetType = 'topic' | 'expert'

export type FeaturedContentAnyTargetType =
  | FeaturedContentTargetType
  | FeaturedContentLegacyTargetType
  | ''

/** 跳转类型中文标签（全站统一口径） */
export const FEATURED_CONTENT_TARGET_TYPE_LABELS: Record<string, string> = {
  '': '纯展示',
  room: '直播',
  session: '场次',
  brand: '品牌',
  external: '外部链接',
  topic: '专题（已废弃）',
  expert: '专家（已废弃）'
}

/** 管理端表单可选跳转类型 */
export const FEATURED_CONTENT_TARGET_TYPE_OPTIONS: Array<{ label: string; value: FeaturedContentTargetType | '' }> = [
  { label: '纯展示（不跳转）', value: '' },
  { label: '场次', value: 'session' },
  { label: '品牌', value: 'brand' },
  { label: '直播', value: 'room' },
  { label: '外部链接', value: 'external' }
]

/** 是否在对外展示有效期内（配合 is_active 判断「展示中」） */
export function isFeaturedContentInDisplayPeriod(item: {
  start_at?: string | null
  end_at?: string | null
}): boolean {
  const now = Date.now()
  if (item.start_at) {
    const start = new Date(item.start_at).getTime()
    if (!Number.isNaN(start) && start > now) return false
  }
  if (item.end_at) {
    const end = new Date(item.end_at).getTime()
    if (!Number.isNaN(end) && end < now) return false
  }
  return true
}

/** 是否为纯展示（不跳转） */
export function isFeaturedContentPureDisplay(item: { target_type?: string | null }): boolean {
  return !item.target_type
}

/**
 * 焦点图信息（对应后端 FeaturedContentItem Schema）
 */
export interface FeaturedContent {
  /** 焦点图唯一标识（UUID） */
  id: string
  /** 焦点图标题（最大200字符） */
  title: string
  /** 焦点图副标题（最大500字符） */
  subtitle?: string
  /** 图片URL路径 */
  image_url: string
  /** 跳转目标类型；空/null 表示纯展示（历史数据可能含 topic/expert） */
  target_type?: FeaturedContentAnyTargetType | null
  /** 目标资源ID（external类型时为null） */
  target_id: string | null
  /** 外部链接URL（仅target_type=external时使用） */
  target_url: string | null
  /** 排序权重（升序，0最前） */
  sort_order: number
  /** 是否启用状态（软删除标记） */
  is_active: boolean
  /** 展示开始时间（ISO 8601格式） */
  start_at: string | null
  /** 展示结束时间（ISO 8601格式） */
  end_at: string | null
  /** 创建时间（ISO 8601格式） */
  created_at: string
  /** 最后更新时间（ISO 8601格式） */
  updated_at: string
}

/**
 * 创建焦点图请求参数（对应后端 FeaturedContentCreate Schema）
 * 纯展示时可不传 target_type
 */
export interface FeaturedContentCreate {
  /** 焦点图标题（必填） */
  title: string
  /** 焦点图副标题（可选） */
  subtitle?: string
  /** 图片URL路径（必填） */
  image_url: string
  /** 跳转目标类型；省略表示纯展示 */
  target_type?: FeaturedContentTargetType
  /** 目标资源ID（非external时必填） */
  target_id?: string | null
  /** 外部链接URL（external时必填） */
  target_url?: string | null
  /** 排序权重（可选，默认0） */
  sort_order?: number
  /** 是否启用状态（可选，默认true） */
  is_active?: boolean
  /** 展示开始时间（可选） */
  start_at?: string | null
  /** 展示结束时间（可选） */
  end_at?: string | null
}

/**
 * 更新焦点图请求参数（对应后端 FeaturedContentUpdate Schema，PATCH 部分更新）
 */
export interface FeaturedContentUpdate {
  /** 焦点图标题（可选） */
  title?: string
  /** 焦点图副标题（可选） */
  subtitle?: string
  /** 图片URL路径（可选） */
  image_url?: string
  /** 跳转目标类型（可选） */
  target_type?: FeaturedContentTargetType
  /** 目标资源ID（可选） */
  target_id?: string | null
  /** 外部链接URL（可选） */
  target_url?: string | null
  /** 排序权重（可选） */
  sort_order?: number
  /** 是否启用状态（可选） */
  is_active?: boolean
  /** 展示开始时间（可选） */
  start_at?: string | null
  /** 展示结束时间（可选） */
  end_at?: string | null
}
