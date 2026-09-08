/**
 * 场次标签 API
 */

import { request } from '@/utils/request'
import type { ApiResponse } from '@/types/common'
import { API_PATHS } from '@/config/api'

// §4.6.3 GET /api/v1/sessions/{session_id}/tags
export const getSessionTags = (sessionId: string): Promise<ApiResponse<string[]>> => {
  return request.get(API_PATHS.SESSION.TAGS(sessionId), { showError: false })
}

// §4.6.1 POST /api/v1/admin/sessions/{session_id}/tags
export const setSessionTags = (
  sessionId: string,
  tagIds: string[],
  mode: 'replace' | 'append' = 'replace'
): Promise<ApiResponse<{ updated: boolean } & any>> => {
  return request.post(
    API_PATHS.ADMIN.SESSION_TAGS(sessionId),
    { tag_ids: tagIds, mode },
    { loading: true, loadingText: '保存中...' }
  )
}

export default {
  getSessionTags,
  setSessionTags
}
