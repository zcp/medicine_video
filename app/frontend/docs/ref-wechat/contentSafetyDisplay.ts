/**
 * 鍙戝竷鍐呭璁剧疆 鈥?绠＄悊绔睍绀烘枃妗堬紙绂佹涓撲笟鏈涓婂睆锛? * 鎶€鏈瓧娈典粎鍐欏叆 logger锛涘紑鍙戠粏鑺傝 add-docs锛屼笉鍚戠鐞嗗憳灞曠ず
 */
import { logger } from '@/logs/logger'
import type { ContentSafetyLog, ContentSafetyRule } from '@/types/contentSafety'

const SCENE_LABELS: Record<string, string> = {
  message: '鐣欒█',
  room_title: '鐩存挱鏍囬',
  room_description: '鐩存挱闂寸畝浠?,
  room_tab: '鐩存挱闂存爮鐩?,
  search_query: '鎼滅储璇?,
  nickname: '鏄电О'
}

/** rule_category 鈫?绠＄悊鍛樺彲鎳傜殑涓枃鍚嶏紙涓嶅惈鏂囨。/浠ｇ爜鐢ㄨ锛?*/
const CATEGORY_LABELS: Record<string, string> = {
  framework_url: '澶栭摼',
  framework_contact: '鑱旂郴鏂瑰紡',
  framework_fraud: '骞垮憡寮曟祦',
  absolute_superlative: '缁濆鍖栫敤璇?,
  absolute_time_scale: '鏃堕棿瑙勬ā鏋侀檺璇?,
  absolute_false_promise: '铏氬亣鎵胯',
  medical_treatment_claim: '鐤剧梾娌荤枟鐢ㄨ',
  cosmetic_medical_claim: '鍖荤編鍔熸晥鐢ㄨ',
  wellness_false_claim: '鍏荤敓鍔熸晥鐢ㄨ',
  medical_device_claim: '鍖荤枟鍣ㄦ鐢ㄨ',
  cure_rate_quantified: '娌绘剤鐜囬噺鍖?,
  porn_vulgar: '浣庝織鍐呭',
  political_sensitive: '鏁忔劅鍐呭',
  gambling: '鍗氬僵鐩稿叧',
  controlled_substance: '绠″埗鐗╁搧',
  financial_fraud: '铏氬亣閲戣瀺',
  mlm_fraud: '浼犻攢寰晢',
  loan_fraud: '璐锋璇堥獥',
  abuse_discrimination: '杈遍獋姝ц',
  food_false_claim: '椋熷搧铏氬亣鍔熸晥',
  baby_false_claim: '姣嶅┐铏氬亣鍔熸晥',
  home_false_claim: '瀹跺眳澶稿ぇ瀹ｄ紶',
  counterfeit_infringement: '渚垫潈鍋囧啋',
  false_endorsement: '铏氬亣鑳屼功',
  privacy_gray: '闅愮鐩稿叧',
  cheat_gray: '浣滃紛鐩稿叧',
  cosmetic_surgery: '鍖荤編鏁村舰',
  platform_circumvention: '缁曡繃骞冲彴浜ゆ槗',
  superstition: '杩蜂俊鍐呭',
  military_name: '鍐涘悕涔夌敤璇?,
  special_drug: '鐗规畩鑽搧',
  prescription_drug: '澶勬柟鑽悕',
  platform_custom: '鑷畾涔夐檺鍒?,
  general: '閫氱敤闄愬埗',
  political: '鏁忔劅鍐呭'
}

const DECISION_LABELS: Record<string, string> = {
  block: '鏈繃瀹?,
  warn: '宸茬暀搴?,
  allow: '宸查€氳繃'
}

const ACTION_LABELS: Record<string, string> = {
  block: '涓嶈鍙戝竷',
  warn: '鍙互鍙戝竷锛屼絾鐣欎釜搴?,
  allow: '鍏佽鍙戝竷'
}

/** 鍚庣甯歌鑻辨枃/鎶€鏈悕鐗瑰緛 */
const TECHNICAL_NAME_PATTERN =
  /^(rule|message|room_|search_|content|pattern|block|warn|allow|_[a-z0-9]+|[a-z0-9]+[-_][a-z0-9_-]+)$/i

/** 寮€鍙戜晶澶囨敞锛氳瘝搴?seed銆佹枃妗ｅ紩鐢ㄧ瓑锛屼笉寰椾笂灞?*/
const DEV_REMARK_PATTERN =
  /add-docs|鍖诲鍚堣|璇嶅簱\s*[a-z]|regulation|seed|rule_category|content_safety|framework_|搂|绉戞櫘鍗佷笉寰梶骞垮憡娉晐鍖荤枟骞垮憡/i

function asDisplayText(value: unknown): string {
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return ''
}

/** 鏄惁閫傚悎浣滀负绠＄悊鍛樺彲瑙佸悕绉?澶囨敞 */
export function isUserFacingText(value?: string | null): boolean {
  const text = asDisplayText(value)
  if (!text) return false
  if (DEV_REMARK_PATTERN.test(text)) return false
  if (TECHNICAL_NAME_PATTERN.test(text)) return false
  // 鍚嫳鏂囨爣璇?铔囧舰鍛藉悕鐨勪竴寰嬩笉褰撳睍绀哄悕
  if (/[a-z]{3,}/i.test(text) && /[_-]/.test(text)) return false
  if (/^[a-z][a-z0-9_]*$/i.test(text)) return false
  return true
}

export function formatSceneLabel(scene?: string | null): string {
  if (!scene) return '鈥?
  return SCENE_LABELS[scene] || '鍏朵粬浣嶇疆'
}

export function formatCategoryLabel(category?: string | null): string {
  if (!category) return ''
  return CATEGORY_LABELS[category] || ''
}

export function formatDecisionLabel(decision?: string | null): string {
  if (!decision) return '鈥?
  return DECISION_LABELS[decision] || '鍏朵粬缁撴灉'
}

export function formatActionLabel(action?: string | null): string {
  if (!action) return '鈥?
  return ACTION_LABELS[action] || '鎸夐粯璁ゅ鐞?
}

export function formatBindingLabel(bindingLevel?: string | null): string {
  if (bindingLevel === 'statutory') return '绯荤粺鑷甫'
  if (bindingLevel === 'platform') return '鍙嚜琛屾敼'
  return '鈥?
}

/** 浠?rule_name 鏈鎻愬彇涓枃鍚庣紑锛屽 message-content-澶栭摼 鈫?澶栭摼 */
function extractChineseSuffix(ruleName: string): string {
  const parts = ruleName.split('-').filter(Boolean)
  const last = parts[parts.length - 1] || ''
  if (/^[\u4e00-\u9fffA-Za-z0-9路]{1,20}$/.test(last) && /[\u4e00-\u9fff]/.test(last)) {
    return last
  }
  return ''
}

/** 鍙法浣嶇疆鍚堝苟灞曠ず鐨勭郴缁熺被鐩紙涓嶅惈鑷畾涔夛級 */
export function isShareableCategory(category?: string | null): boolean {
  const cat = asDisplayText(category)
  if (!cat) return false
  if (cat === 'platform_custom' || cat === 'general') return false
  return Boolean(CATEGORY_LABELS[cat])
}

/**
 * 闄愬埗璇嶇被鍨嬪悕锛堜笉甯︺€岀暀瑷€路銆嶅墠缂€锛? * 鍚屼竴绉嶈瘝鍦ㄥ悇浣嶇疆鍏辩敤涓€涓悕瀛楋紝濡傘€岀粷瀵瑰寲鐢ㄨ銆? */
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

  return '鑷畾涔夐檺鍒?
}

/** @deprecated 鍒楄〃宸叉寜绫荤洰鍚堝苟锛涗繚鐣欏吋瀹癸紝绛夊悓 formatRuleTypeName */
export function formatRuleDisplayName(
  rule: Pick<ContentSafetyRule, 'rule_name' | 'remark' | 'scene'> & {
    rule_category?: string
  }
): string {
  return formatRuleTypeName(rule)
}

/** 绠＄悊绔彲缁存姢鐨勫叏閮ㄤ綅缃紙涓嶅惈鏄电О锛?*/
export const ADMIN_ALL_SCENES = [
  'message',
  'room_title',
  'room_description',
  'room_tab',
  'search_query'
] as const

/** 銆岀敤鍦ㄥ摢閲屻€嶆憳瑕侊細瑕嗙洊鍏ㄩ儴鍒欐樉绀恒€屽叏閮ㄤ綅缃€?*/
export function formatScenesSummary(scenes: string[]): string {
  const unique = [...new Set(scenes.filter(Boolean))]
  if (unique.length === 0) return '鈥?
  const adminSet = new Set<string>(ADMIN_ALL_SCENES)
  const coversAllAdmin =
    ADMIN_ALL_SCENES.every((s) => unique.includes(s)) &&
    unique.every((s) => adminSet.has(s) || s === 'nickname')
  if (coversAllAdmin || unique.length >= ADMIN_ALL_SCENES.length) {
    return '鍏ㄩ儴浣嶇疆'
  }
  return unique.map((s) => formatSceneLabel(s)).join('銆?)
}

export interface ContentSafetyRuleGroup {
  key: string
  rules: ContentSafetyRule[]
  /** 琛ㄥ崟鍥炲～鐢ㄤ唬琛ㄩ」锛堜紭鍏堝紑鍚腑鐨勶級 */
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
    .split(/[,锛宂/)
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
  // 鑷畾涔夛細鐩稿悓璇嶈〃鍚堝苟锛屼究浜庝竴娆℃敼澶氬
  return `custom:${normalizePatternKey(rule.pattern)}:${rule.binding_level || 'platform'}`
}

/**
 * 灏嗗悗绔€屾寜浣嶇疆鎷嗗紑銆嶇殑瑙勫垯鍚堝苟涓虹鐞嗗憳瑙嗚鐨勪竴缁? * 濡傜暀瑷€/鎼滅储/鏍囬涓嬬殑鏋侀檺璇?鈫?涓€鏉°€岀粷瀵瑰寲鐢ㄨ銆? */
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

/** 浠庢棩蹇楅」瑙ｆ瀽鍙鐢ㄦ埛鍚嶏紙涓嶅惈璺ㄦ湇鍔¤ˉ鍏級 */
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
  return '鈥?
}

/** 灏嗗畬鏁村璁?payload 鍐欏叆 logger锛屼緵寮€鍙戞帓鏌ワ紱涓嶅湪 UI 灞曠ず */
export function logContentSafetyAuditDetail(item: ContentSafetyLog): void {
  logger.info('business', '鍙戝竷澶勭悊璁板綍璇︽儏锛堜粎鏃ュ織锛?, {
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
  { label: '鍏ㄩ儴缁撴灉', value: '' },
  { label: '鏈繃瀹?, value: 'block' },
  { label: '宸茬暀搴?, value: 'warn' },
  { label: '宸查€氳繃', value: 'allow' }
] as const

export const ADMIN_SCENE_FILTER_OPTIONS = [
  { label: '鍏ㄩ儴浣嶇疆', value: '' },
  { label: '鐣欒█', value: 'message' },
  { label: '鐩存挱鏍囬', value: 'room_title' },
  { label: '鐩存挱闂寸畝浠?, value: 'room_description' },
  { label: '鐩存挱闂存爮鐩?, value: 'room_tab' },
  { label: '鎼滅储璇?, value: 'search_query' },
  { label: '鏄电О', value: 'nickname' }
] as const

export const ADMIN_SCENE_FORM_OPTIONS = ADMIN_SCENE_FILTER_OPTIONS.filter(
  (o) => o.value !== 'nickname' && o.value !== ''
)

export const ADMIN_ACTION_FORM_OPTIONS = [
  { label: '涓嶈鍙戝竷', value: 'block' as const },
  { label: '鍙互鍙戝竷锛屼絾鐣欎釜搴?, value: 'warn' as const }
]

/** 鎸変綅缃嚜鍔ㄥ～鍏咃紝杩愯惀鏃犻渶濉啓鎶€鏈瓧娈?*/
export const SCENE_DEFAULT_TARGET_FIELD: Record<string, string> = {
  message: 'content',
  room_title: 'title',
  room_description: 'description',
  room_tab: 'content',
  search_query: 'query',
  nickname: 'nickname'
}
