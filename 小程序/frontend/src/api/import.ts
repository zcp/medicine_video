/**
 * 导入相关API - 按后端设计文档 v2 重构
 * 设计文档仅定义：POST /rooms/import/batch
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'

export type BatchImportItem = {
	row_no: number
	room_id: string | null
	session_id: string | null
	status: 'success' | 'failed'
	error: string | null
	skipped: boolean
	skip_reason: string | null
}

export type BatchImportResponse = {
	total_rows: number
	success_count: number
	failed_count: number
	items: BatchImportItem[]
}

// 批量导入（房间+场次） - 设计文档：POST /api/v1/import/sessions
export const batchImportRooms = (payload: any) =>
  request.post(API_PATHS.ROOM.IMPORT_BATCH, payload, { loading: true, loadingText: '导入中...' })

export default { batchImportRooms }
