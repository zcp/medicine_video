/**
 * 16-D3 留言注销作者展示占位 — 前端自测
 * 对齐《16-D3-留言-注销作者展示占位-后端设计文档》V1.1
 */
import { describe, it, expect } from 'vitest'
import {
  DEACTIVATED_DISPLAY_NAME,
  normalizeRoomMessageItem,
  resolveMessageAvatarSrc,
  resolveMessageDisplayName,
  shouldSkipAuthFallback
} from '@/utils/roomMessageNormalize'
import { DEFAULT_CONFIG } from '@/common/constants'

const UID = 'user-deactivated-001'
const AUTH = {
  user_id: UID,
  nickname: '当前登录昵称',
  avatar_url: 'https://cdn.example.com/my-avatar.png'
}

describe('16-D3 注销作者展示占位', () => {
  it('T1: 已注销标记 → 昵称占位、头像 null、正文不变', () => {
    const content = '这个剂量在指南里如何调整？'
    const normalized = normalizeRoomMessageItem(
      {
        id: 'msg-1',
        room_id: 'room-1',
        user_id: UID,
        content,
        created_at: '2026-07-01T08:00:00Z',
        user_display_name: DEACTIVATED_DISPLAY_NAME,
        user: { nickname: DEACTIVATED_DISPLAY_NAME, avatar_url: null }
      },
      AUTH
    )

    expect(normalized.content).toBe(content)
    expect(resolveMessageDisplayName(normalized)).toBe(DEACTIVATED_DISPLAY_NAME)
    expect(normalized.user?.avatar_url).toBeNull()
    expect(resolveMessageAvatarSrc(normalized.user?.avatar_url)).toBe(
      DEFAULT_CONFIG.DEFAULT_AVATAR
    )
  })

  it('T2: 已注销作者曾是当前登录用户 → 禁止 auth 覆盖昵称/头像', () => {
    const normalized = normalizeRoomMessageItem(
      {
        id: 'msg-2',
        room_id: 'room-1',
        user_id: UID,
        content: 'hello',
        created_at: '2026-07-01T08:00:00Z',
        user: { nickname: DEACTIVATED_DISPLAY_NAME, avatar_url: null }
      },
      AUTH
    )

    expect(normalized.user?.nickname).toBe(DEACTIVATED_DISPLAY_NAME)
    expect(normalized.user?.avatar_url).toBeNull()
    expect(normalized.user?.avatar_url).not.toBe(AUTH.avatar_url)
  })

  it('T3: Admin 旧 user_nickname 不得盖住占位名', () => {
    const normalized = normalizeRoomMessageItem({
      id: 'msg-3',
      room_id: 'room-1',
      user_id: UID,
      content: 'keep',
      created_at: '2026-07-01T08:00:00Z',
      user_nickname: '历史真名',
      user_display_name: DEACTIVATED_DISPLAY_NAME,
      user: { nickname: DEACTIVATED_DISPLAY_NAME, avatar_url: null }
    })

    expect(resolveMessageDisplayName(normalized)).toBe(DEACTIVATED_DISPLAY_NAME)
    expect(normalized.user?.nickname).not.toBe('历史真名')
  })

  it('T3b: nested 仍为旧快照、flat 已占位 → 仍显示账号已注销并清空头像', () => {
    const normalized = normalizeRoomMessageItem(
      {
        id: 'msg-3b',
        room_id: 'room-1',
        user_id: UID,
        content: 'keep',
        created_at: '2026-07-01T08:00:00Z',
        user_display_name: DEACTIVATED_DISPLAY_NAME,
        user: {
          nickname: '历史真名',
          avatar_url: 'https://cdn.example.com/old.png'
        }
      },
      AUTH
    )

    expect(resolveMessageDisplayName(normalized)).toBe(DEACTIVATED_DISPLAY_NAME)
    expect(normalized.user?.avatar_url).toBeNull()
    expect(resolveMessageAvatarSrc(normalized.user?.avatar_url)).toBe(
      DEFAULT_CONFIG.DEFAULT_AVATAR
    )
  })

  it('T5: 作者未注销仅改过昵称 → 仍显示发送时快照（V3）', () => {
    const normalized = normalizeRoomMessageItem({
      id: 'msg-5',
      room_id: 'room-1',
      user_id: 'other',
      content: 'ok',
      created_at: '2026-07-01T08:00:00Z',
      user: { nickname: '发送时昵称', avatar_url: 'https://cdn.example.com/snap.png' }
    })

    expect(resolveMessageDisplayName(normalized)).toBe('发送时昵称')
    expect(normalized.user?.avatar_url).toBe('https://cdn.example.com/snap.png')
  })

  it('T6: 无占位时本人 auth 兜底仍可用', () => {
    const normalized = normalizeRoomMessageItem(
      {
        id: 'msg-6',
        room_id: 'room-1',
        user_id: UID,
        content: 'mine',
        created_at: '2026-07-01T08:00:00Z'
      },
      AUTH
    )

    expect(normalized.user?.nickname).toBe(AUTH.nickname)
    expect(normalized.user?.avatar_url).toBe(AUTH.avatar_url)
  })

  it('shouldSkipAuthFallback 规则', () => {
    expect(shouldSkipAuthFallback(DEACTIVATED_DISPLAY_NAME, null)).toBe(true)
    expect(shouldSkipAuthFallback('张三', { nickname: '张三', avatar_url: null })).toBe(true)
    expect(shouldSkipAuthFallback('张三', { nickname: '张三', avatar_url: 'https://x' })).toBe(false)
    expect(shouldSkipAuthFallback(null, null)).toBe(false)
  })
})
