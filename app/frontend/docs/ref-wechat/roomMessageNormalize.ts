/**
 * 鐣欒█鍙戦€佽€呰韩浠藉綊涓€鍖? * 瀵归綈銆奓ive-Saas-Wechat-07-鐩存挱闂寸暀瑷€-鍓嶇璁捐鏂囨。銆媀1.5 搂7.0
 * + 銆?7-鐩存挱闂寸暀瑷€-V3-鐢ㄦ埛鏄电О澶村儚蹇収澧為噺璁捐鏂囨。銆媀3.0
 * + 銆?6-D3-鐣欒█-娉ㄩ攢浣滆€呭睍绀哄崰浣嶃€媀1.1
 *
 * 浼樺厛 user.*锛坋xtra 蹇収锛夆啋 鍥為€€ user_display_name 鈫掞紙鍙€夛級鏈汉 auth 鍏滃簳
 * 宸叉敞閿€鍗犱綅鍚?/ 鏄惧紡绌哄ご鍍忔椂绂佹 auth 瑕嗙洊
 */

import type { MessageUserInfo, RoomMessageItem } from '@/types/roomMessage'
import { resolveAvatarUrl } from '@/utils/url'

/** 涓庡悗绔?D3 DEACTIVATED_DISPLAY_NAME 瀵归綈 */
export const DEACTIVATED_DISPLAY_NAME = '璐﹀彿宸叉敞閿€'

export interface AuthUserFallback {
  user_id?: string | null
  nickname?: string | null
  avatar_url?: string | null
}

type LooseMessage = RoomMessageItem & {
  user_nickname?: string | null
  user_display_name?: string | null
  user_avatar_url?: string | null
  user?: (MessageUserInfo & Record<string, unknown>) | null
}

function pickNonEmpty(...values: Array<string | null | undefined>): string | null {
  for (const v of values) {
    if (typeof v !== 'string') continue
    const trimmed = v.trim()
    if (trimmed) return trimmed
  }
  return null
}

/** 鏄电О宸叉槸娉ㄩ攢鍗犱綅锛屾垨 user 瀵硅薄瀛樺湪涓斿ご鍍忔樉寮忎负绌?鈫?绂佹 auth 鍏滃簳 */
export function shouldSkipAuthFallback(
  nickname: string | null,
  nestedUser: MessageUserInfo | null
): boolean {
  if (nickname === DEACTIVATED_DISPLAY_NAME) return true
  if (!nestedUser) return false
  const avatar = nestedUser.avatar_url
  // null / undefined / '' 鍧囪涓烘樉寮忕┖澶村儚锛堝悗绔?D3 濂戠害锛?  return avatar == null || String(avatar).trim() === ''
}

/**
 * 浠讳竴鏄电О瀛楁涓恒€岃处鍙峰凡娉ㄩ攢銆嶆椂寮哄埗鍗犱綅锛岄伩鍏嶆棫蹇収瀛楁鐩栦綇 D3 瑕嗙洊缁撴灉
 */
export function pickMessageNickname(
  ...values: Array<string | null | undefined>
): string | null {
  const picked: string[] = []
  for (const v of values) {
    const t = pickNonEmpty(v)
    if (t) picked.push(t)
  }
  if (picked.includes(DEACTIVATED_DISPLAY_NAME)) return DEACTIVATED_DISPLAY_NAME
  return picked[0] || null
}

/**
 * 灏嗘帴鍙ｅ師濮嬬暀瑷€椤瑰綊涓€涓烘爣鍑?RoomMessageItem
 */
export function normalizeRoomMessageItem(
  raw: unknown,
  authFallback?: AuthUserFallback | null
): RoomMessageItem {
  const item = (raw && typeof raw === 'object' ? raw : {}) as LooseMessage

  const nested = item.user && typeof item.user === 'object' ? item.user : null
  const nestedAvatar = pickNonEmpty(nested?.avatar_url as string | undefined)
  const flatAvatar = pickNonEmpty(item.user_avatar_url)

  // D3锛氫换涓€瀛楁涓恒€岃处鍙峰凡娉ㄩ攢銆嶅嵆鍗犱綅锛涘惁鍒?nested 鈫?user_display_name 鈫?user_nickname
  const serverNickname = pickMessageNickname(
    nested?.nickname as string | undefined,
    item.user_display_name,
    item.user_nickname
  )
  const skipAuth = shouldSkipAuthFallback(serverNickname, nested)

  const isOwn =
    !skipAuth &&
    !!authFallback?.user_id &&
    !!item.user_id &&
    String(authFallback.user_id) === String(item.user_id)

  const nickname =
    serverNickname ||
    (isOwn ? pickNonEmpty(authFallback?.nickname) : null) ||
    null

  // 宸叉敞閿€鍗犱綅锛氬己鍒跺ご鍍?null锛岀姝?auth / 娈嬬暀 URL 闇茬湡鑴?  const avatar_url =
    serverNickname === DEACTIVATED_DISPLAY_NAME
      ? null
      : nestedAvatar ||
        flatAvatar ||
        (isOwn ? pickNonEmpty(authFallback?.avatar_url) : null) ||
        null

  return {
    id: String(item.id || ''),
    room_id: String(item.room_id || ''),
    user_id: String(item.user_id || ''),
    content: typeof item.content === 'string' ? item.content : '',
    created_at: typeof item.created_at === 'string' ? item.created_at : '',
    user_display_name: nickname,
    user_role: typeof item.user_role === 'string' ? item.user_role : null,
    user: {
      nickname,
      avatar_url
    }
  }
}

export function normalizeRoomMessageItems(
  items: unknown[],
  authFallback?: AuthUserFallback | null
): RoomMessageItem[] {
  if (!Array.isArray(items)) return []
  return items.map((it) => normalizeRoomMessageItem(it, authFallback))
}

/** 灞曠ず鐢ㄥご鍍忥細蹇収 URL 鈫?榛樿澶村儚锛屽啀鍋氬獟浣撳綊涓€鍖?*/
export function resolveMessageAvatarSrc(avatarUrl?: string | null): string {
  return resolveAvatarUrl(pickNonEmpty(avatarUrl))
}

/** 灞曠ず鐢ㄦ樀绉?*/
export function resolveMessageDisplayName(message: RoomMessageItem): string {
  return (
    pickNonEmpty(message.user?.nickname, message.user_display_name) || '鍖垮悕鐢ㄦ埛'
  )
}
