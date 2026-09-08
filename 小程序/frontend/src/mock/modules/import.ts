/**
 * 批量导入相关 Mock API
 * 严格遵循《直播核心功能设计文档_v6_深度融合最终版.md》第5节"6) 批量导入（CSV/Excel：创建 room + session 并写入 playback_url）"定义
 */

import { registerMockRule, mockSuccess, mockDelay } from '../index'
import type { BatchImportResponse } from '@/api/import'

/**
 * 初始化批量导入相关 Mock
 */
export function setupImportMock() {
  // 批量导入接口
  registerMockRule({
    pattern: /\/api\/v1\/rooms\/import\/batch/,
    method: 'POST',
    handler: async (params: any) => {
      await mockDelay()
      
      // 模拟导入结果
      const mode = params?.mode || 'dry_run'
      const totalRows = 10 // 模拟10行数据
      
      const items = Array.from({ length: totalRows }, (_, i) => ({
        row_no: i + 1,
        room_id: mode === 'apply' ? `room_${Date.now()}_${i}` : null,
        session_id: mode === 'apply' ? `session_${Date.now()}_${i}` : null,
        status: i < 8 ? 'success' as const : 'failed' as const,
        error: i >= 8 ? '缺少必需字段: playback_url' : null,
        skipped: false,
        skip_reason: null
      }))
      
      const successCount = items.filter(item => item.status === 'success').length
      const failedCount = items.filter(item => item.status === 'failed').length
      
      const response: BatchImportResponse = {
        total_rows: totalRows,
        success_count: successCount,
        failed_count: failedCount,
        items
      }
      
      return mockSuccess(response)
    }
  })
}

