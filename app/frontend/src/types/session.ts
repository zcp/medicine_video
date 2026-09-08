 // 严格依据设计文档 6.2.3 session_statistics（场次统计表）
export interface Statistics {
    id: string; // UUID
    session_id: string; // UUID
    peak_viewer_count: number; // INT
    total_viewer_count: number; // BIGINT
    total_like_count: number; // BIGINT
    total_share_count: number; // BIGINT
    created_at: string; // TIMESTAMPTZ
    updated_at: string; // TIMESTAMPTZ
  }
  
  // 严格依据设计文档 6.2.2 live_sessions（直播场次表）
  // V15：与后端六态对齐（ended/archived 已删除，后端不存在）
  export type SessionStatus = 'scheduled' | 'live' | 'finished' | 'processing' | 'ready' | 'error';
  
  export interface Session {
    id: string; // UUID
    room_id: string; // UUID
    status: SessionStatus;
    source_type?: 'push' | 'external'; // V15：直播来源（push=推流；external=外部流）
    start_time: string; // TIMESTAMPTZ
    end_time: string | null; // TIMESTAMPTZ
    video_id: string | null; // UUID
    playback_url?: string | null; // 回放播放地址（后端动态返回）
    created_at: string; // TIMESTAMPTZ
    updated_at: string; // TIMESTAMPTZ
    statistics?: Statistics; // 关联的统计数据，可选
    room_title?: string; // 用于UI展示，非数据库字段
    // 阶段一补充字段（后端文档Section 2.2 live_sessions表）
    summary: string | null; // 场次总结/摘要
    featured_expert_id: string | null; // 特邀专家ID，关联experts.id
    // 前端展示字段（非数据库字段，可选）
    title?: string; // 场次标题
    cover_url?: string; // 场次封面
    expert_name?: string; // 专家姓名
    expert_avatar?: string; // 专家头像
    expert_title?: string; // 专家职称
    // 专家信息对象（后端可能返回完整的专家对象）
    expert?: {
      id?: string;
      name?: string;
      title?: string;
      avatar?: string;
      avatar_url?: string;
      hospital?: string;
      department?: string;
    };
  }

/**
 * 创建新场次时需要发送的数据载荷
 * 根据后端API文档：POST /api/v1/rooms/{room_id}/sessions
 * playback_url 为必填（预告=外部直播流地址，回放=已录制视频地址）
 * V15：status 支持 scheduled/live/ready 三态创建
 */
export interface SessionCreatePayload {
  title?: string; // 场次标题（可选）
  description?: string; // 场次描述（可选）
  start_time: string; // 计划开始时间，格式：ISO 8601
  playback_url: string; // 播放地址（必填）
  status?: 'scheduled' | 'live' | 'ready'; // V15：创建初始状态（默认 scheduled）
}

/**
 * 更新场次时需要发送的数据载荷
 * 根据后端API文档：PATCH /api/v1/sessions/{session_id}
 */
export interface SessionUpdatePayload {
  title?: string; // 场次标题
  description?: string; // 场次描述
  playback_url?: string; // 回放地址（仅scheduled/ready/error状态可设置）
  featured_expert_id?: string; // 特邀专家ID
  start_time?: string;
  end_time?: string;
  status?: SessionStatus;
}

/**
 * 导入场次时需要发送的数据载荷
 * 根据后端API文档：POST /api/v1/rooms/{room_id}/sessions/import
 * 用于创建带回放URL的session，支持多种状态
 */
export interface SessionImportPayload {
  title: string;
  description?: string;
  start_time: string;
  playback_url: string;
  status: 'ready';
} // 用户创建回放时固定为ready；live/finished/processing/error由后端系统流程写入
