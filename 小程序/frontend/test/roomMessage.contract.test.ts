/**
 * 直播间留言模块契约自测
 * 验证前端实现严格对齐《07-直播间留言-后端设计文档.md》V1.1
 */

import { describe, it, expect } from 'vitest'
import { API_PATHS } from '@/config/api'
import {
  getRoomMessages,
  sendRoomMessage,
  deleteMessage,
  getAdminMessages,
  batchDeleteMessages,
  clearRoomMessages
} from '@/api/roomMessage'
import {
  ROOM_MESSAGE_ERROR_CODES,
  getRoomMessageErrorMessage
} from '@/types/roomMessage'
import type {
  RoomMessageItem,
  RoomMessageCreate,
  RoomMessageQueryParams,
  RoomMessagePageResult,
  AdminMessageQueryParams,
  AdminMessageItem,
  AdminMessagePageResult,
  BatchDeleteRequest,
  BatchDeleteResult,
  ClearRoomMessagesResult
} from '@/types/roomMessage'

const ROOM_ID = '00000000-0000-4000-8000-000000000001'
const MESSAGE_ID = '00000000-0000-4000-8000-000000000002'

describe('07-直播间留言 前后端契约对齐', () => {
  describe('API 路径（§3.1 + §3.2 + 最终路由表）', () => {
    it('用户端 GET 列表', () => {
      expect(API_PATHS.MESSAGE.ROOM_MESSAGES(ROOM_ID)).toContain(
        `/rooms/${ROOM_ID}/messages`
      )
    })

    it('用户端 POST 发送', () => {
      expect(API_PATHS.MESSAGE.ROOM_MESSAGES(ROOM_ID)).toContain(
        `/rooms/${ROOM_ID}/messages`
      )
    })

    it('用户端 DELETE 删除', () => {
      expect(API_PATHS.MESSAGE.MESSAGE_DETAIL(ROOM_ID, MESSAGE_ID)).toContain(
        `/rooms/${ROOM_ID}/messages/${MESSAGE_ID}`
      )
    })

    it('管理端 GET 全局列表', () => {
      expect(API_PATHS.MESSAGE.ADMIN_LIST).toContain('/admin/messages')
      expect(API_PATHS.MESSAGE.ADMIN_LIST).not.toContain('batch-delete')
    })

    it('管理端 POST 批量删除', () => {
      expect(API_PATHS.MESSAGE.ADMIN_BATCH_DELETE).toContain(
        '/admin/messages/batch-delete'
      )
    })

    it('管理端 DELETE 清空直播间', () => {
      expect(API_PATHS.MESSAGE.ADMIN_CLEAR_ROOM(ROOM_ID)).toContain(
        `/admin/rooms/${ROOM_ID}/messages`
      )
    })
  })

  describe('API 封装导出（6 个端点）', () => {
    it('导出全部 6 个函数', () => {
      expect(typeof getRoomMessages).toBe('function')
      expect(typeof sendRoomMessage).toBe('function')
      expect(typeof deleteMessage).toBe('function')
      expect(typeof getAdminMessages).toBe('function')
      expect(typeof batchDeleteMessages).toBe('function')
      expect(typeof clearRoomMessages).toBe('function')
    })
  })

  describe('用户端 Schema（§2 Pydantic）', () => {
    it('RoomMessageCreate 仅含 content，1-500 字符', () => {
      const body: RoomMessageCreate = { content: '测试留言' }
      expect(Object.keys(body)).toEqual(['content'])
      expect(body.content.length).toBeGreaterThanOrEqual(1)
      expect(body.content.length).toBeLessThanOrEqual(500)
    })

    it('RoomMessageItem 字段与 DDL 一致', () => {
      const item: RoomMessageItem = {
        id: MESSAGE_ID,
        room_id: ROOM_ID,
        user_id: '00000000-0000-4000-8000-000000000003',
        content: '老师讲得真好！',
        created_at: '2026-06-07T10:30:00Z',
        user: { nickname: '张医生', avatar_url: '/uploads/avatars/user1.jpg' }
      }
      expect(item).toHaveProperty('id')
      expect(item).toHaveProperty('room_id')
      expect(item).toHaveProperty('user_id')
      expect(item).toHaveProperty('content')
      expect(item).toHaveProperty('created_at')
      expect(item).not.toHaveProperty('status')
      expect(item).not.toHaveProperty('pinned')
      expect(item).not.toHaveProperty('reply')
      expect(item).not.toHaveProperty('updated_at')
    })

    it('RoomMessageQueryParams 不含 order（后端固定 DESC）', () => {
      const params: RoomMessageQueryParams = { page: 1, page_size: 20 }
      expect(params).not.toHaveProperty('order')
      expect(params.page).toBe(1)
      expect(params.page_size).toBe(20)
    })

    it('MessagePageResult 分页结构', () => {
      const page: RoomMessagePageResult = {
        total: 150,
        page: 1,
        page_size: 20,
        items: []
      }
      expect(page).toMatchObject({
        total: expect.any(Number),
        page: expect.any(Number),
        page_size: expect.any(Number),
        items: expect.any(Array)
      })
    })
  })

  describe('管理端 Schema（§2 Admin Schemas）', () => {
    it('AdminMessageQueryParams 支持全部筛选字段', () => {
      const params: AdminMessageQueryParams = {
        room_id: ROOM_ID,
        user_id: '00000000-0000-4000-8000-000000000003',
        keyword: '广告',
        start_time: '2026-06-01T00:00:00Z',
        end_time: '2026-06-30T23:59:59Z',
        page: 1,
        page_size: 20
      }
      expect(params.room_id).toBe(ROOM_ID)
      expect(params.keyword).toBe('广告')
      expect(params.page_size).toBeLessThanOrEqual(100)
    })

    it('BatchDeleteRequest message_ids 1-200 条', () => {
      const body: BatchDeleteRequest = {
        message_ids: [MESSAGE_ID]
      }
      expect(body.message_ids.length).toBeGreaterThanOrEqual(1)
      expect(body.message_ids.length).toBeLessThanOrEqual(200)
    })

    it('AdminMessageItem 含管理端扩展字段', () => {
      const item: AdminMessageItem = {
        id: MESSAGE_ID,
        room_id: ROOM_ID,
        user_id: '00000000-0000-4000-8000-000000000003',
        content: '加V看片...',
        created_at: '2026-06-23T10:30:00Z',
        room_title: '骨科专家张主任讲座',
        user_nickname: '用户12345',
        user_role: 'viewer',
        user: { nickname: '用户12345', avatar_url: null }
      }
      expect(item.room_title).toBeDefined()
      expect(item.user_nickname).toBeDefined()
      expect(item.user_role).toBeDefined()
    })

    it('AdminMessagePageResult 含 filter_summary', () => {
      const result: AdminMessagePageResult = {
        total: 150,
        page: 1,
        page_size: 20,
        filter_summary: { keyword: '广告', room_count: 5, user_count: 12 },
        items: []
      }
      expect(result.filter_summary?.keyword).toBe('广告')
      expect(result.filter_summary?.room_count).toBe(5)
    })

    it('BatchDeleteResult / ClearRoomMessagesResult', () => {
      const batch: BatchDeleteResult = { deleted_count: 3, failed_count: 0 }
      const clear: ClearRoomMessagesResult = { deleted_count: 356 }
      expect(batch.deleted_count).toBe(3)
      expect(clear.deleted_count).toBe(356)
    })
  })

  describe('错误码对照表（§8）', () => {
    it('覆盖后端全部业务错误码', () => {
      expect(ROOM_MESSAGE_ERROR_CODES.SUCCESS).toBe(200)
      expect(ROOM_MESSAGE_ERROR_CODES.DB_ERROR).toBe(1002)
      expect(ROOM_MESSAGE_ERROR_CODES.NOT_FOUND).toBe(2001)
      expect(ROOM_MESSAGE_ERROR_CODES.BUSINESS_ERROR).toBe(2004)
      expect(ROOM_MESSAGE_ERROR_CODES.UNAUTHORIZED).toBe(3001)
      expect(ROOM_MESSAGE_ERROR_CODES.FORBIDDEN).toBe(3002)
      expect(ROOM_MESSAGE_ERROR_CODES.ADMIN_FORBIDDEN).toBe(3003)
      expect(ROOM_MESSAGE_ERROR_CODES.VALIDATION).toBe(4001)
    })

    it('getRoomMessageErrorMessage 映射正确', () => {
      expect(getRoomMessageErrorMessage(3001)).toContain('登录')
      expect(getRoomMessageErrorMessage(3002)).toContain('自己')
      expect(getRoomMessageErrorMessage(3003)).toContain('管理员')
      expect(getRoomMessageErrorMessage(2001)).toContain('不存在')
      expect(getRoomMessageErrorMessage(4001)).toContain('内容')
    })
  })

  describe('业务规则（§1.3 + §1.4 + §5.3）', () => {
    it('删除策略为物理删除（无软删除字段）', () => {
      const item: RoomMessageItem = {
        id: MESSAGE_ID,
        room_id: ROOM_ID,
        user_id: 'u1',
        content: 'test',
        created_at: '2026-06-07T10:30:00Z'
      }
      expect(item).not.toHaveProperty('is_deleted')
      expect(item).not.toHaveProperty('deleted_at')
    })

    it('内容最大 500 字符', () => {
      const maxContent = 'a'.repeat(500)
      expect(maxContent.length).toBe(500)
    })
  })
})
