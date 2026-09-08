/**
 * 播放相关类型定义
 */

export interface Segment {
  name: string;        // TS文件名
  url: string;         // 完整URL
  start: number;       // 开始时间（秒）
  end: number;         // 结束时间（秒）
  duration: number;    // 时长（秒）
  index: number;       // 索引
}

export interface PlaybackError {
  code: string;
  message: string;
  timestamp: number;
}

export interface PlaybackStats {
  session_id: string;
  user_id: string;
  device: string;
  platform: 'app' | 'h5';
  start_time: number;
  end_time: number;
  total_duration: number;
  buffered_duration: number;
  stall_count: number;
  stall_duration: number;
  quality_changes: number;
  final_quality: string;
  errors: PlaybackError[];
}

export interface StreamUrl {
  url: string;
  expires_at: string;
}
