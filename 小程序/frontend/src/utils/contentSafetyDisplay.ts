/**
 * 发布内容设置 — 管理端展示文案（禁止专业术语上屏）
 * 技术字段仅写入 logger；开发细节见 add-docs，不向管理员展示
 */
import { logger } from '@/logs/logger'
import type { ContentSafetyLog, ContentSafetyRule } from '@/types/contentSafety'

const SCENE_LABELS: Record<string, string> = {
  message: '讨论',
  room_title: '直播标题',
  room_description: '直播间简介',
  room_tab: '直播间栏目',
  search_query: '搜索词',
  tag_name: '标签', // 《02-V2》§3.4 scene=tag_name
  nickname: '昵称'
}

/** rule_category → 管理员可懂的中文名（不含文档/代码用语） */
const CATEGORY_LABELS: Record<string, string> = {
  framework_url: '外链',
  framework_contact: '联系方式',
  framework_fraud: '广告引流',
  absolute_superlative: '绝对化用语',
  absolute_time_scale: '时间规模极限词',
  absolute_false_promise: '虚假承诺',
  medical_treatment_claim: '疾病治疗用语',
  cosmetic_medical_claim: '医美功效用语',
  wellness_false_claim: '养生功效用语',
  medical_device_claim: '医疗器械用语',
  cure_rate_quantified: '治愈率量化',
  porn_vulgar: '低俗内容',
  political_sensitive: '敏感内容',
  gambling: '博彩相关',
  controlled_substance: '管制物品',
  financial_fraud: '虚假金融',
  mlm_fraud: '传销微商',
  loan_fraud: '贷款诈骗',
  abuse_discrimination: '辱骂歧视',
  food_false_claim: '食品虚假功效',
  baby_false_claim: '母婴虚假功效',
  home_false_claim: '家居夸大宣传',
  counterfeit_infringement: '侵权假冒',
  false_endorsement: '虚假背书',
  privacy_gray: '隐私相关',
  cheat_gray: '作弊相关',
  cosmetic_surgery: '医美整形',
  platform_circumvention: '绕过平台交易',
  superstition: '迷信内容',
  military_name: '军名义用语',
  special_drug: '特殊药品',
  prescription_drug: '处方药名',
  platform_custom: '自定义限制',
  general: '通用限制',
  political: '敏感内容'
}

const DECISION_LABELS: Record<string, string> = {
  block: '未过审',
  warn: '已留底',
  allow: '已通过'
}

const ACTION_LABELS: Record<string, string> = {
  block: '不让发布',
  warn: '可以发布，但留个底',
  allow: '允许发布'
}

/** 后端常见英文/技术名特征 */
const TECHNICAL_NAME_PATTERN =
  /^(rule|message|room_|search_|content|pattern|block|warn|allow|_[a-z0-9]+|[a-z0-9]+[-_][a-z0-9_-]+)$/i

/** 开发侧备注：词库 seed、文档引用等，不得上屏 */
const DEV_REMARK_PATTERN =
  /add-docs|医学合规|词库\s*[a-z]|regulation|seed|rule_category|content_safety|framework_|§|科普十不得|广告法|医疗广告/i

function asDisplayText(value: unknown): string {
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return ''
}

/** 是否适合作为管理员可见名称/备注 */
export function isUserFacingText(value?: string | null): boolean {
  const text = asDisplayText(value)
  if (!text) return false
  if (DEV_REMARK_PATTERN.test(text)) return false
  if (TECHNICAL_NAME_PATTERN.test(text)) return false
  // 含英文标识/蛇形命名的一律不当展示名
  if (/[a-z]{3,}/i.test(text) && /[_-]/.test(text)) return false
  if (/^[a-z][a-z0-9_]*$/i.test(text)) return false
  return true
}

export function formatSceneLabel(scene?: string | null): string {
  if (!scene) return '—'
  return SCENE_LABELS[scene] || '其他位置'
}

export function formatCategoryLabel(category?: string | null): string {
  if (!category) return ''
  return CATEGORY_LABELS[category] || ''
}

export function formatDecisionLabel(decision?: string | null): string {
  if (!decision) return '—'
  return DECISION_LABELS[decision] || '其他结果'
}

export function formatActionLabel(action?: string | null): string {
  if (!action) return '—'
  return ACTION_LABELS[action] || '按默认处理'
}

export function formatBindingLabel(bindingLevel?: string | null): string {
  if (bindingLevel === 'statutory') return '系统自带'
  if (bindingLevel === 'platform') return '可自行改'
  return '—'
}

/** 从 rule_name 末段提取中文后缀，如 message-content-外链 → 外链 */
function extractChineseSuffix(ruleName: string): string {
  const parts = ruleName.split('-').filter(Boolean)
  const last = parts[parts.length - 1] || ''
  if (/^[\u4e00-\u9fffA-Za-z0-9·]{1,20}$/.test(last) && /[\u4e00-\u9fff]/.test(last)) {
    return last
  }
  return ''
}

/** 可跨位置合并展示的系统类目（不含自定义） */
export function isShareableCategory(category?: string | null): boolean {
  const cat = asDisplayText(category)
  if (!cat) return false
  if (cat === 'platform_custom' || cat === 'general') return false
  return Boolean(CATEGORY_LABELS[cat])
}

/**
 * 限制词类型名（不带「留言·」前缀）
 * 同一种词在各位置共用一个名字，如「绝对化用语」
 */
export function formatRuleTypeName(
  rule: Pick<ContentSafetyRule, 'rule_name' | 'remark' | 'scene'> & {
    rule_category?: string
  }
): string {
  const remark = asDisplayText(rule.remark)
  if (isUserFacingText(remark)) return remark

  const categoryLabel = formatCategoryLabel(rule.rule_category)
  if (categoryLabel) return categoryLabel

  const name = asDisplayText(rule.rule_name)
  const chineseSuffix = extractChineseSuffix(name)
  if (chineseSuffix) return chineseSuffix

  if (isUserFacingText(name) && !/[a-z]/i.test(name)) return name

  return '自定义限制'
}

/** @deprecated 列表已按类目合并；保留兼容，等同 formatRuleTypeName */
export function formatRuleDisplayName(
  rule: Pick<ContentSafetyRule, 'rule_name' | 'remark' | 'scene'> & {
    rule_category?: string
  }
): string {
  return formatRuleTypeName(rule)
}

/** 管理端可维护的全部位置（不含昵称） */
export const ADMIN_ALL_SCENES = [
  'message',
  'room_title',
  'room_description',
  'room_tab',
  'search_query',
  'tag_name' // 《02-V2》§3.4
] as const

/** 「用在哪里」摘要：覆盖全部则显示「全部位置」 */
export function formatScenesSummary(scenes: string[]): string {
  const unique = [...new Set(scenes.filter(Boolean))]
  if (unique.length === 0) return '—'
  const adminSet = new Set<string>(ADMIN_ALL_SCENES)
  const coversAllAdmin =
    ADMIN_ALL_SCENES.every((s) => unique.includes(s)) &&
    unique.every((s) => adminSet.has(s) || s === 'nickname')
  if (coversAllAdmin || unique.length >= ADMIN_ALL_SCENES.length) {
    return '全部位置'
  }
  return unique.map((s) => formatSceneLabel(s)).join('、')
}

export interface ContentSafetyRuleGroup {
  key: string
  rules: ContentSafetyRule[]
  /** 表单回填用代表项（优先开启中的） */
  representative: ContentSafetyRule
  rule_category: string
  binding_level: ContentSafetyRule['binding_level']
  scenes: string[]
  enabled: boolean
  action: ContentSafetyRule['action']
  displayName: string
  scenesLabel: string
}

function normalizePatternKey(pattern?: string | null): string {
  return String(pattern || '')
    .split(/[,，]/)
    .map((s) => s.trim())
    .filter(Boolean)
    .sort()
    .join(',')
}

function buildGroupKey(rule: ContentSafetyRule): string {
  const cat = asDisplayText(rule.rule_category) || 'general'
  if (isShareableCategory(cat)) {
    return `cat:${cat}`
  }
  // 自定义：相同词表合并，便于一次改多处
  return `custom:${normalizePatternKey(rule.pattern)}:${rule.binding_level || 'platform'}`
}

/**
 * 将后端「按位置拆开」的规则合并为管理员视角的一组
 * 如留言/搜索/标题下的极限词 → 一条「绝对化用语」
 */
export function groupContentSafetyRules(rules: ContentSafetyRule[]): ContentSafetyRuleGroup[] {
  const map = new Map<string, ContentSafetyRule[]>()
  for (const rule of rules) {
    const key = buildGroupKey(rule)
    const list = map.get(key) || []
    list.push(rule)
    map.set(key, list)
  }

  const groups: ContentSafetyRuleGroup[] = []
  for (const [key, list] of map) {
    const sorted = [...list].sort((a, b) => {
      if (a.enabled !== b.enabled) return a.enabled ? -1 : 1
      return String(a.scene).localeCompare(String(b.scene))
    })
    const representative = sorted[0]
    const scenes = [...new Set(sorted.map((r) => r.scene).filter(Boolean))] as string[]
    const enabled = sorted.some((r) => r.enabled)
    groups.push({
      key,
      rules: sorted,
      representative,
      rule_category: representative.rule_category || 'general',
      binding_level: representative.binding_level,
      scenes,
      enabled,
      action: representative.action,
      displayName: formatRuleTypeName(representative),
      scenesLabel: formatScenesSummary(scenes)
    })
  }

  return groups.sort((a, b) => a.displayName.localeCompare(b.displayName, 'zh-CN'))
}

/** 从日志项解析可读用户名（不含跨服务补全） */
export function resolveContentSafetyLogUserLabel(item: ContentSafetyLog): string {
  const nested = item.user
  const candidates = [
    item.user_nickname,
    item.username,
    nested?.nickname,
    nested?.username
  ]
  for (const value of candidates) {
    if (typeof value !== 'string') continue
    const trimmed = value.trim()
    if (trimmed) return trimmed
  }
  if (item.user_id?.trim()) return item.user_id.trim()
  return '—'
}

/** 将完整审计 payload 写入 logger，供开发排查；不在 UI 展示 */
export function logContentSafetyAuditDetail(item: ContentSafetyLog): void {
  logger.info('business', '发布处理记录详情（仅日志）', {
    id: item.id,
    scene: item.scene,
    decision: item.decision,
    user_id: item.user_id,
    user_nickname: item.user_nickname,
    username: item.username,
    user: item.user,
    reason_code: item.reason_code,
    reason_message: item.reason_message,
    matched_rule_ids: item.matched_rule_ids,
    matched_rule_names: item.matched_rule_names,
    normalized_excerpt: item.normalized_excerpt,
    client_ip: item.client_ip,
    input_excerpt: item.input_excerpt
  })
}

export const ADMIN_DECISION_FILTER_OPTIONS = [
  { label: '全部结果', value: '' },
  { label: '未过审', value: 'block' },
  { label: '已留底', value: 'warn' },
  { label: '已通过', value: 'allow' }
] as const

export const ADMIN_SCENE_FILTER_OPTIONS = [
  { label: '全部位置', value: '' },
  { label: '讨论', value: 'message' },
  { label: '直播标题', value: 'room_title' },
  { label: '直播间简介', value: 'room_description' },
  { label: '直播间栏目', value: 'room_tab' },
  { label: '搜索词', value: 'search_query' },
  { label: '标签', value: 'tag_name' }, // 《02-V2》§3.4
  { label: '昵称', value: 'nickname' }
] as const

export const ADMIN_SCENE_FORM_OPTIONS = ADMIN_SCENE_FILTER_OPTIONS.filter(
  (o) => o.value !== 'nickname' && o.value !== ''
)

export const ADMIN_ACTION_FORM_OPTIONS = [
  { label: '不让发布', value: 'block' as const },
  { label: '可以发布，但留个底', value: 'warn' as const }
]

/** 按位置自动填充，运营无需填写技术字段 */
export const SCENE_DEFAULT_TARGET_FIELD: Record<string, string> = {
  message: 'content',
  room_title: 'title',
  room_description: 'description',
  room_tab: 'content',
  search_query: 'query',
  tag_name: 'name', // 《02-V2》§3.4 field=name
  nickname: 'nickname'
}
