/** 鎶婂悗绔彲鑳借繑鍥炵殑 object / array message 鏀舵垚浜鸿瘽瀛楃涓诧紝閬垮厤 Toast 鍙樻垚 [object Object] */
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
    return parts.length ? parts.join('锛?) : undefined
  }
  if (typeof value === 'object') {
    const o = value as Record<string, unknown>
    return coerceMessageText(o.message ?? o.detail ?? o.msg ?? o.error)
  }
  return undefined
}

/** 浠?Error / request 鎶涢敊瀵硅薄鎻愬彇 message */
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

/** UGC 绛夊満鏅細鎻愬彇骞惰繃婊ゆ妧鏈悗绔枃妗堬紝缁熶竴鐢ㄤ簬 Toast / ErrorBanner */
export function getUserFacingErrorMessage(error: unknown, fallback: string): string {
  return pickUserFacingMessage(extractErrorMessage(error), fallback)
}

/** 鍐呭瀹夊叏鐩稿叧涓氬姟鐮?*/
export const CONTENT_SAFETY_CODE = {
  SERVICE_ERROR: 2004,
  CONTENT_BLOCKED: 2005
} as const

/** C 绔浐瀹氭枃妗堬細涓嶅惈瑙勫垯/鏍￠獙/瀹℃牳绛夊疄鐜版湳璇?*/
export const USER_CONTENT_BLOCKED_MESSAGE = '鏆傛棤娉曞彂甯冿紝璇蜂慨鏀瑰唴瀹瑰悗鍐嶈瘯'
export const USER_IMAGE_BLOCKED_MESSAGE = '鏆傛棤娉曚娇鐢ㄦ鍥剧墖锛岃鏇存崲鍚庡啀璇?
export const USER_SERVICE_UNAVAILABLE_MESSAGE = '鏆傛椂鏃犳硶鎻愪氦锛岃绋嶅悗鍐嶈瘯'

/** 鍚庣瀹¤/杩愮淮鏂囨鐗瑰緛锛堝惈銆岃鍒欍€嶅強鍚岀被瀹炵幇缁嗚妭锛?*/
const TECHNICAL_MESSAGE_PATTERN =
  /瑙勫垯|鎷︽埅|杩濊|鍛戒腑|鍐呭瀹夊叏|鏍￠獙|瀹℃牳|鏁忔劅璇峾block|warn|scene|rule|matched|reason/i

/** 鍒ゆ柇鏄惁涓轰笉搴斿睍绀虹粰鐢ㄦ埛鐨勫悗绔?message */
export function isTechnicalBackendMessage(message?: string | null): boolean {
  const text = message?.trim()
  if (!text) return true
  if (TECHNICAL_MESSAGE_PATTERN.test(text)) return true
  // 杩囬暱澶氫负鎷兼帴瀹¤淇℃伅
  if (text.length > 48) return true
  return false
}

/** 杩愯惀/鑳藉姏椤靛父瑙佸悗绔師鏂?鈫?浜鸿瘽锛堥伩鍏嶃€屾棤鎴愬憳瑙掕壊銆嶇瓑鏈鐩村嚭锛?*/
const FRIENDLY_MESSAGE_RULES: Array<{ pattern: RegExp; message: string }> = [
  { pattern: /鏃犳垚鍛樿鑹瞸鏃犳晥鎴愬憳瑙掕壊|invalid\s*member\s*role/i, message: '鎴愬憳韬唤鏃犳晥锛岃閲嶆柊閫夋嫨' },
  { pattern: /闈炲搧鐗屾垚鍛榺涓嶆槸鍝佺墝鎴愬憳|not\s*a?\s*brand\s*member/i, message: '瀵规柟杩樹笉鏄鍝佺墝鎴愬憳' },
  { pattern: /鎴愬憳宸插瓨鍦▅already\s*exists.*member|duplicate.*member/i, message: '璇ヨ处鍙峰凡鍦ㄦ垚鍛樺垪琛ㄤ腑' }
]

/**
 * 浼樺厛浣跨敤绠€鐭€侀潪鎶€鏈€х殑鍚庣 message锛堝闄愭祦銆佺洿鎾棿宸插叧闂級锛? * 鍚﹀垯鍥為€€鍒?C 绔浐瀹氭枃妗堛€? */
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

/** 浠?request 鎶涘嚭鐨?Error 鎴栧師濮嬪搷搴斾腑鎻愬彇涓氬姟 code */
export function extractBusinessCode(error: unknown): number | null {
  const e = error as any
  const code = e?.code ?? e?.raw?.data?.code ?? e?.raw?.code ?? e?.response?.data?.code
  return code != null ? Number(code) : null
}

/**
 * 2004/2005 鐢ㄦ埛鍙鏂囨銆? * 2005 涓€寰嬪浐瀹氭枃妗堬紱2004 浠呴€忎紶宸蹭汉璇濆寲鐨勭煭 message锛堝闄愭祦锛夈€? */
export function getContentSafetyMessage(code: number, backendMessage?: string): string {
  if (code === CONTENT_SAFETY_CODE.CONTENT_BLOCKED) {
    const hint = backendMessage?.trim() || ''
    if (/鍥剧墖|澶村儚|avatar/i.test(hint)) {
      return USER_IMAGE_BLOCKED_MESSAGE
    }
    return USER_CONTENT_BLOCKED_MESSAGE
  }
  if (code === CONTENT_SAFETY_CODE.SERVICE_ERROR) {
    return pickUserFacingMessage(backendMessage, USER_SERVICE_UNAVAILABLE_MESSAGE)
  }
  return pickUserFacingMessage(backendMessage, '鎿嶄綔澶辫触锛岃绋嶅悗鍐嶈瘯')
}

export function isContentSafetyCode(code: number): boolean {
  return code === CONTENT_SAFETY_CODE.SERVICE_ERROR || code === CONTENT_SAFETY_CODE.CONTENT_BLOCKED
}

/**
 * 澶勭悊鍐呭瀹夊叏閿欒锛涜嫢鍛戒腑 2004/2005 杩斿洖 true锛堝凡 toast锛夛紝鍚﹀垯 false
 * 涓氬姟 catch 涓細if (handleContentSafetyError(e)) return
 */
export function handleContentSafetyError(
  error: unknown,
  options?: { showToast?: boolean }
): boolean {
  const code = extractBusinessCode(error)
  if (code == null || !isContentSafetyCode(code)) return false

  // request 灞傚凡 toast 杩囦汉璇濇椂涓嶅啀閲嶅寮?  if ((error as any)?.__handled) {
    return true
  }

  const msg = getContentSafetyMessage(code, extractErrorMessage(error))
  if (options?.showToast !== false) {
    setTimeout(() => uni.showToast({ title: msg, icon: 'none', duration: 2500 }), 200)
  }
  return true
}
