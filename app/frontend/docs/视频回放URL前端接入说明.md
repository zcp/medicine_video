## 视频回放 URL 前端接入说明

### 流类型与选用原则（必须）
- **直播流（Live Stream）**：推流进行中时使用的实时播放地址；用户推流→观众观看。
- **回放流（Playback/HLS）**：直播结束后，由后端生成并在场次详情中以 `playback_url` 返回的点播地址。

选流规则：
- 推流进行中（进行直播）：优先使用“直播流”。即使存在历史回放，也应播放直播。
- 推流结束后：如果后端返回了 `playback_url`（且满足后端条件：`status == 'ready'` 且存在 `video_id`），使用回放流；若 `playback_url` 为 `null`，继续显示占位或保留直播结束提示。
- 前端不得自行拼接回放地址，必须直接使用后端返回的 `playback_url`。

### 你需要在前端做什么
- **新增类型**
  - 在 `types/session.ts` 为 `Session` 增加可选字段：`playback_url?: string | null`。

- **更新 API 层**
  - 在 `api/session.ts` 的“获取场次详情/列表”方法中，透传后端返回的 `playback_url`（无需前端拼接）。

- **使用位置调整**
  - 播放页（如 `pages/live/LiveView.vue` 或 `components/VideoPlayer.vue`）：
    - 推流中：使用“直播流地址”。
    - 结束后：当 `session.playback_url` 存在时，使用该 URL 作为 HLS 回放地址；否则展示“回放未就绪/暂无播放地址”。
  - 管理列表/详情（如 `pages/room/new/MultiVenueManage.vue`）：
    - 若存在 `playback_url`，展示“回放预览/播放/复制链接/下载回放视频”等操作；否则禁用或提示“暂不可用”。

- **多端注意事项**
  - Web 端用 `<video>` + hls.js；小程序/APP 端按平台视频组件支持情况处理 HLS。

- **边界与降级**
  - 对 `playback_url` 必须判空，不要在未就绪时初始化播放器；显示“回放未就绪”。
  - 不要在前端自行拼接 URL，不要缓存旧的回放链接。

### 后端会提供什么（接口契约）
- 修改后的获取场次详情接口：`GET /api/v1/sessions/{session_id}`
  - 统一响应结构不变（`code/message/data/timestamp`），只是 `data` 新增字段：`playback_url`。
  - 生成规则：
    - 仅当 `status == 'ready'` 且 `video_id` 存在时返回非空回放地址；用于表示“已生成回放”。
    - 其他状态（未到 `ready`）返回 `null`，表示暂不可回放。
  - URL 形态（示例）：`{PLAYBACK_BASE_URL}/media/videos/{video_id}/playlist.m3u8`
    - 由后端按环境变量 `PLAYBACK_BASE_URL` 动态拼出；前端无需拼接。

### 最小实现清单（Checklist）
- [ ] types：给 `Session` 增加 `playback_url?: string | null`。
- [ ] api：`getSessionDetail/getSessionList` 透传 `playback_url`。
- [ ] 播放页：优先使用 `session.playback_url`（回放），否则走直播或提示未就绪。
- [ ] 管理页：有 `playback_url` 时展示回放相关按钮，无则禁用/提示。

### 示例使用片段（Web）
```ts
// 假设已拿到 session 对象，以及当前是否推流中的标志 liveStreaming（由业务/信令决定）
// 选流策略：推流中优先直播；结束后若有回放则播放回放
let sourceUrl: string | null = null;
if (liveStreaming) {
  sourceUrl = liveStreamUrl; // 你的直播拉流地址（如 flv/hls/ws-flv）
} else {
  sourceUrl = session.playback_url ?? null; // 回放地址由后端提供
}

const isPlayback = !liveStreaming && !!session.playback_url;

if (isPlayback) {
  // 初始化 hls.js 播放回放地址
} else {
  // 维持直播流或显示占位
}
```


