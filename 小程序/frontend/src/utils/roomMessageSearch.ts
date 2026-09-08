/**
 * 管理端留言统一搜索框解析
 * 对齐《Live-Saas-Wechat-07-直播间留言-前端设计文档-v1.3.md》§6.1.2
 */

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const TIME_RANGE_RE =
  /^(\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}(?::\d{2})?)?)\s*[~～至]\s*(\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}(?::\d{2})?)?)$/i

export interface ParsedSearchFilters {
  room_id?: string
  user_id?: string
  keyword?: string
  start_time?: string
  end_time?: string
}

function normalizeIso(value: string, kind: 'start' | 'end'): string {
  const trimmed = value.trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    const time = kind === 'start' ? 'T00:00:00' : 'T23:59:59'
    return new Date(`${trimmed}${time}`).toISOString()
  }
  return new Date(trimmed).toISOString()
}

function parseTimeRange(value: string): ParsedSearchFilters {
  const match = value.match(TIME_RANGE_RE)
  if (!match) return {}
  return {
    start_time: normalizeIso(match[1], 'start'),
    end_time: normalizeIso(match[2], 'end')
  }
}

/** 将统一搜索框输入解析为后端 AdminMessageQueryParams 筛选字段 */
export function parseSearchKeyword(raw: string): ParsedSearchFilters {
  const input = raw.trim()
  if (!input) return {}

  const roomPrefix = input.match(/^(?:直播间|房间|room)[:：]\s*(\S+)/i)
  if (roomPrefix) return { room_id: roomPrefix[1].trim() }

  const userPrefix = input.match(/^(?:用户|user)[:：]\s*(\S+)/i)
  if (userPrefix) return { user_id: userPrefix[1].trim() }

  const timePrefix = input.match(/^(?:时间|time)[:：]\s*(.+)$/i)
  if (timePrefix) return parseTimeRange(timePrefix[1].trim())

  const timeMatch = input.match(TIME_RANGE_RE)
  if (timeMatch) {
    return {
      start_time: normalizeIso(timeMatch[1], 'start'),
      end_time: normalizeIso(timeMatch[2], 'end')
    }
  }

  if (UUID_RE.test(input)) return { room_id: input }

  return { keyword: input.slice(0, 100) }
}
