 // api/session.ts
import { request } from '@/utils/request';
import { ENV_CONFIG } from '@/config/env';
import type { Session, SessionCreatePayload, SessionUpdatePayload, SessionImportPayload } from '@/types/session';
import type { ApiResponse, PaginatedResponse } from '@/types/common';

// 分页响应体（Session特定类型）
export type PaginatedSessions = PaginatedResponse<Session>;

// 获取房间下所有场次 (GET /rooms/{room_id}/sessions)
export const getSessionList = (
  roomId: string,
  params: { page?: number, size?: number },
  options: { showLoading?: boolean } = {}
) => {
  return request<PaginatedSessions>({
    url: `/rooms/${roomId}/sessions`,
    method: 'GET',
    data: params,
    ...options,
  });
};

// 获取单个场次详情 (GET /sessions/{session_id})
export const getSessionDetail = (sessionId: string, options: { showLoading?: boolean } = {}) => {
  return request<ApiResponse<Session>>({
    url: `/sessions/${sessionId}`,
    method: 'GET',
    ...options,
  });
};

// 创建场次 (POST /rooms/{room_id}/sessions)
export const createSession = (roomId: string, data: Partial<SessionCreatePayload>) => {
  return request<Session>({
    url: `/rooms/${roomId}/sessions`,
    method: 'POST',
    data,
  });
};

// 更新场次 (PATCH /sessions/{session_id})
export const updateSession = (sessionId: string, data: SessionUpdatePayload) => {
  return request<Session>({
    url: `/sessions/${sessionId}`,
    method: 'PATCH',
    data,
  });
};

// 删除场次 (DELETE /sessions/{session_id})
export const deleteSession = (sessionId: string) => {
  return request<{ id: string; status: string }>({
    url: `/sessions/${sessionId}`,
    method: 'DELETE',
  });
};

// 导入场次 (POST /rooms/{room_id}/sessions/import)
// 用于创建带回放URL的finished状态session
export const importSession = (roomId: string, data: SessionImportPayload) => {
  return request<Session>({
    url: `/rooms/${roomId}/sessions/import`,
    method: 'POST',
    data,
  });
};

// 手动切换场次状态 (POST /sessions/{session_id}/status)
// V15：external 场次专用（开播/停播/转回放/回退预告）
export const updateSessionStatus = (sessionId: string, data: { status: string; playback_url?: string }) => {
  return request<Session>({
    url: `/sessions/${sessionId}/status`,
    method: 'POST',
    data,
  });
};

// 生成 m3u8 代理地址（V15：external 场次播放统一走代理，session 关联防 SSRF）
// 注意：必须返回完整 URL（video/live-player 组件的 src 不支持相对路径）
export const getProxyM3u8Url = (sessionId: string): string => {
  const base = (ENV_CONFIG.VITE_BASE_API_URL || '').replace(/\/+$/, '');
  return `${base}/proxy/m3u8/${sessionId}`;
};
