/**
 * 留言发送者身份归一化
 * 对齐《Live-Saas-Wechat-07-直播间留言-前端设计文档》V1.5 §7.0
 * + 《07-直播间留言-V3-用户昵称头像快照增量设计文档》V3.0
 * + 《16-D3-留言-注销作者展示占位》V1.1
 *
 * 优先 user.*（extra 快照）→ 回退 user_display_name →（可选）本人 auth 兜底
 * 已注销占位名 / 显式空头像时禁止 auth 覆盖
 */

import type { MessageUserInfo, RoomMessageItem } from '@/types/roomMessage'
import { resolveAvatarUrl } from '@/utils/url'

/** 与后端 D3 DEACTIVATED_DISPLAY_NAME 对齐 */
export const DEACTIVATED_DISPLAY_NAME = '账号已注销'

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

/** 昵称已是注销占位，或 user 对象存在且头像显式为空 → 禁止 auth 兜底 */
export function shouldSkipAuthFallback(
  nickname: string | null,
  nestedUser: MessageUserInfo | null
): boolean {
  if (nickname === DEACTIVATED_DISPLAY_NAME) return true
  if (!nestedUser) return false
  const avatar = nestedUser.avatar_url
  // null / undefined / '' 均视为显式空头像（后端 D3 契约）
  return avatar == null || String(avatar).trim() === ''
}

/**
 * 任一昵称字段为「账号已注销」时强制占位，避免旧快照字段盖住 D3 覆盖结果
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
 * 将接口原始留言项归一为标准 RoomMessageItem
 */
export function normalizeRoomMessageItem(
  raw: unknown,
  authFallback?: AuthUserFallback | null
): RoomMessageItem {
  const item = (raw && typeof raw === 'object' ? raw : {}) as LooseMessage

  const nested = item.user && typeof item.user === 'object' ? item.user : null
  const nestedAvatar = pickNonEmpty(nested?.avatar_url as string | undefined)
  const flatAvatar = pickNonEmpty(item.user_avatar_url)

  // D3：任一字段为「账号已注销」即占位；否则 nested → user_display_name → user_nickname
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

  // 已注销占位：强制头像 null，禁止 auth / 残留 URL 露真脸
  const avatar_url =
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

/** 展示用头像：快照 URL → 默认头像，再做媒体归一化 */
export function resolveMessageAvatarSrc(avatarUrl?: string | null): string {
  return resolveAvatarUrl(pickNonEmpty(avatarUrl))
}

/** 展示用昵称 */
export function resolveMessageDisplayName(message: RoomMessageItem): string {
  return (
    pickNonEmpty(message.user?.nickname, message.user_display_name) || '匿名用户'
  )
}
