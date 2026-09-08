/**
 * 直播业务共享常量
 * 与后端契约对齐项统一在此收敛（禁止页面各自定义导致漂移）
 */

/**
 * 直播场次可关联标签上限
 * 后端硬约束 0~5（锚：后端 schemas SessionTagsSetRequest.tag_ids max_length=5）；双端不得单方放宽
 */
export const MAX_SESSION_TAGS = 5
