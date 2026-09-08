/** 把后端可能返回的 object / array message 收成人话字符串，避免 Toast 变成 [object Object] */
function coerceMessageText(value: unknown): string | undefined {
  if (value == null) return undefined
  if (typeof value === 'string') {
    const t = value.trim()
    return t && t !== '[object Object]' ? t : undefined
  }
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) {
    const parts = value
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          return coerceMessageText((item as any).msg ?? (item as any).message ?? (item as any).detail)
        }
        return undefined
      })
      .filter(Boolean) as string[]
    return parts.length ? parts.join('；') : undefined
  }
  if (typeof value === 'object') {
    const o = value as Record<string, unknown>
    return coerceMessageText(o.message ?? o.detail ?? o.msg ?? o.error)
  }
  return undefined
}

/** 从 Error / request 抛错对象提取 message */
export function extractErrorMessage(error: unknown): string | undefined {
  const e = error as any
  return (
    coerceMessageText(e?.message) ||
    coerceMessageText(e?.raw?.data?.message) ||
    coerceMessageText(e?.raw?.data?.detail) ||
    coerceMessageText(e?.raw?.message) ||
    coerceMessageText(e?.response?.data?.message)
  )
}

/** UGC 等场景：提取并过滤技术后端文案，统一用于 Toast / ErrorBanner */
export function getUserFacingErrorMessage(error: unknown, fallback: string): string {
  return pickUserFacingMessage(extractErrorMessage(error), fallback)
}

/** 内容安全相关业务码 */
export const CONTENT_SAFETY_CODE = {
  SERVICE_ERROR: 2004,
  CONTENT_BLOCKED: 2005
} as const

/** 无后端 message 时的兜底（临时对接：优先展示 body.message） */
export const USER_CONTENT_BLOCKED_MESSAGE = '内容未通过审核，请修改后重试'
export const USER_IMAGE_BLOCKED_MESSAGE = '暂无法使用此图片，请更换后再试'
export const USER_SERVICE_UNAVAILABLE_MESSAGE = '审核服务暂不可用，请稍后再试'

/** 后端已落地的中文审核原因，允许上屏 */
const AUDIT_USER_MESSAGE_PATTERN =
  /未通过审核|审核服务暂不可用|请修改后重试|请稍后再试/

/** 后端审计/运维文案特征（英文标识、规则字段等）；不含已人话化的审核原因 */
const TECHNICAL_MESSAGE_PATTERN =
  /规则|命中|内容安全|block|warn|scene|rule|matched|reason_code|rule_id/i

/** 判断是否为不应展示给用户的后端 message */
export function isTechnicalBackendMessage(message?: string | null): boolean {
  const text = message?.trim()
  if (!text) return true
  // 临时对接：后端中文审核文案直接展示
  if (AUDIT_USER_MESSAGE_PATTERN.test(text)) return false
  if (TECHNICAL_MESSAGE_PATTERN.test(text)) return true
  // 过长多为拼接审计信息
  if (text.length > 80) return true
  return false
}

/** 运营/能力页常见后端原文 → 人话 */
const FRIENDLY_MESSAGE_RULES: Array<{ pattern: RegExp; message: string }> = []

/**
 * 优先使用简短、非技术性的后端 message（如限流、直播间已关闭）；
 * 否则回退到 C 端固定文案。
 */
export function pickUserFacingMessage(
  backendMessage: string | undefined | null,
  fallback: string
): string {
  const text = backendMessage?.trim()
  if (!text) return fallback
  for (const rule of FRIENDLY_MESSAGE_RULES) {
    if (rule.pattern.test(text)) return rule.message
  }
  if (!isTechnicalBackendMessage(text)) return text
  return fallback
}

/** 从 request 抛出的 Error 或原始响应中提取业务 code */
export function extractBusinessCode(error: unknown): number | null {
  const e = error as any
  const code = e?.code ?? e?.raw?.data?.code ?? e?.raw?.code ?? e?.response?.data?.code
  return code != null ? Number(code) : null
}

/**
 * 2004/2005 用户可见文案。
 * 临时对接：优先展示后端中文审核 message；技术文案回退兜底。
 */
export function getContentSafetyMessage(code: number, backendMessage?: string): string {
  const hint = backendMessage?.trim() || ''
  if (code === CONTENT_SAFETY_CODE.CONTENT_BLOCKED) {
    // 图片类优先专用文案（含短句「图片内容违规」）
    if (/图片|头像|封面|image/i.test(hint)) return USER_IMAGE_BLOCKED_MESSAGE
    if (hint && !isTechnicalBackendMessage(hint)) return hint
    return USER_CONTENT_BLOCKED_MESSAGE
  }
  if (code === CONTENT_SAFETY_CODE.SERVICE_ERROR) {
    if (hint && !isTechnicalBackendMessage(hint)) return hint
    return USER_SERVICE_UNAVAILABLE_MESSAGE
  }
  return pickUserFacingMessage(backendMessage, '操作失败，请稍后再试')
}

export function isContentSafetyCode(code: number): boolean {
  return code === CONTENT_SAFETY_CODE.SERVICE_ERROR || code === CONTENT_SAFETY_CODE.CONTENT_BLOCKED
}

/**
 * 处理内容安全错误；若命中 2004/2005 返回 true（已 toast 或调用方声明不 toast），否则 false
 * 业务 catch 中：if (handleContentSafetyError(e)) return
 *
 * 注意：request 的 `__handled` 只表示「错误已包装」，不等于已弹 Toast。
 * `showError: false` 的接口（如 resolve）须靠本函数补人话；仅 `__toastShown` 时跳过重复弹。
 */
export function handleContentSafetyError(
  error: unknown,
  options?: { showToast?: boolean }
): boolean {
  const code = extractBusinessCode(error)
  if (code == null || !isContentSafetyCode(code)) return false

  // request 层已 toast 过人话时不再重复弹
  if ((error as any)?.__toastShown) {
    return true
  }

  const msg = getContentSafetyMessage(code, extractErrorMessage(error))
  if (options?.showToast !== false) {
    setTimeout(() => uni.showToast({ title: msg, icon: 'none', duration: 2500 }), 200)
  }
  return true
}
