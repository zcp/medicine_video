/**
 * 场次相关 Mock API（已禁用）
 *
 * 按你的要求：核心链路不能依赖 mock。
 * 同时按后端设计文档：
 * - 观众播放地址、统计等应从 `GET /api/v1/sessions/{session_id}` 获取（如 `playback_url`、`statistics`）。
 * - 开播激活应由推流触发后端内部回调 `/internal/srs/on_publish`（非前端 mock）。
 *
 * 因此本模块不再注册任何 mock 规则。
 */
export function setupSessionMock() {
  // noop
}

