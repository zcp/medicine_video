/**
 * 消息相关API - 按后端设计文档 v2 重构
 * 设计文档仅定义房间维度消息：GET/POST /rooms/{room_id}/messages
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { log } from '@/logs/logger'

export type Message = {
  id: string
  room_id: string
  session_id: string | null
  user_id: string
  user_role: string
  content: string
  user_display_name: string
  created_at: string
  is_deleted: boolean
}

export const getRoomMessages = (roomId: string, params?: any) => {
  log.info('live', '[留言] 开始获取留言列表', {
    roomId,
    page: params?.page || 1,
    pageSize: params?.size || params?.limit || 20
  })

  return request.get(API_PATHS.ROOM.MESSAGES(roomId), { data: params, showError: false })
    .then(response => {
      const messages = response?.data || []
      log.info('live', '[留言] 获取留言列表成功', {
        roomId,
        fetchedCount: messages.length,
        totalCount: response?.total || messages.length,
        messageDetails: messages.map(msg => ({
          id: msg.id,
          userId: msg.user_id,
          userRole: msg.user_role,
          userName: msg.user_display_name,
          content: msg.content,
          contentLength: msg.content?.length || 0,
          createdAt: msg.created_at,
          isDeleted: msg.is_deleted
        }))
      })
      return response
    })
    .catch(error => {
      log.error('live', '[留言] 获取留言列表失败', error)
      throw error
    })
}

export const postRoomMessage = (roomId: string, data: any) => {
  log.info('live', '[留言] 开始发送留言', {
    roomId,
    sessionId: data?.session_id || null,
    contentLength: data?.content?.length || 0,
    content: data?.content || '',
    requestPayload: {
      content: data?.content,
      sessionId: data?.session_id
    }
  })

  return request.post(API_PATHS.ROOM.MESSAGES(roomId), { ...(data || {}) }, { loading: true, loadingText: '发送中...' })
    .then(response => {
      const message = response?.data
      log.info('live', '[留言] 发送留言成功', {
        roomId,
        messageId: message?.id,
        userId: message?.user_id,
        userRole: message?.user_role,
        userName: message?.user_display_name,
        content: message?.content,
        contentLength: message?.content?.length || 0,
        createdAt: message?.created_at,
        sessionId: message?.session_id,
        isDeleted: message?.is_deleted,
        responseCode: response?.code,
        responseMessage: response?.message
      })
      return response
    })
    .catch(error => {
      log.error('live', '[留言] 发送留言失败', {
        roomId,
        contentLength: data?.content?.length || 0,
        content: data?.content,
        error
      })
      throw error
    })
}
