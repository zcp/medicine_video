/**
 * 私密房间分享邀请工具
 * 阶段：私密房分享（2026-08-11，方案 V1.1 决策 D1/D4）
 * 用途：App 端"复制邀请文本 → 打开 App 自动识别进入"的解析与会话级防重复
 *
 * 链接格式：私密直播间邀请：https://mp.dayilive.com/live/room/{36位UUID}，请复制链接直接打开App观看
 *
 * 防重复策略（2026-08-11 联调反馈 V2）：
 * - 会话级标记（进程内存 Set）：弹窗显示过一次（无论取消/进入）→ 本会话不再弹
 * - 杀 App 重开 → 内存清空 → 必弹（可重复进入）
 * - 多用户共享链接互不影响（标记在各自设备内存）
 */

const INVITE_URL_PATTERN =
  /live\/room\/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/;

/** 会话级已提示标记（进程内存；杀 App 自动清空） */
const promptedThisSession = new Set<string>();

/** 邀请链接基础地址（域名与生产一致，格式唯一可匹配） */
export const INVITE_BASE_URL = 'https://mp.dayilive.com/live/room/';

/**
 * 生成邀请文本（分享端复制载体，含使用指引——提示接收方"复制后直接打开 App"而非点击链接）
 * @param roomId 私密房间 UUID
 * @returns 邀请文本
 * @example
 * const text = buildInviteText('550e8400-e29b-41d4-a716-446655440000');
 */
export function buildInviteText(roomId: string): string {
  return `私密直播间邀请：${INVITE_BASE_URL}${roomId}，请复制链接直接打开App观看`;
}

/**
 * 从任意文本中解析私密房邀请链接
 * @param text 剪贴板内容或任意文本
 * @returns roomId（36 位 UUID）或 null（非邀请文本）
 * @example
 * const roomId = parseInviteText('私密直播间邀请：https://mp.dayilive.com/live/room/xxx');
 */
export function parseInviteText(text: string): string | null {
  if (!text) return null;
  const match = text.match(INVITE_URL_PATTERN);
  return match ? match[1] : null;
}

/**
 * 标记某房间本次会话已提示（弹窗显示即标记；杀 App 自动清空）
 * @param roomId 房间 UUID
 */
export function markHandled(roomId: string): void {
  promptedThisSession.add(roomId);
}

/**
 * 判断是否应提示进入某房间（会话级：本次进程内已提示过则不再提示）
 * @param roomId 房间 UUID
 * @returns true=应提示；false=本会话已提示过
 */
export function shouldPrompt(roomId: string): boolean {
  return !promptedThisSession.has(roomId);
}

/**
 * 读取剪贴板并解析私密房邀请（会话级防重复）
 * 命中邀请且本会话未提示过 → 标记已提示并返回 roomId；否则返回 null
 * 任何异常静默返回 null（不影响 App 正常启动/回前台）
 *
 * @returns roomId 或 null
 * @example
 * const roomId = await checkClipboardForInvite();
 * if (roomId) { showInviteConfirm(roomId); }
 */
export async function checkClipboardForInvite(): Promise<string | null> {
  try {
    const data = await new Promise<string>((resolve, reject) => {
      uni.getClipboardData({
        success: (res) => resolve(typeof res.data === 'string' ? res.data : ''),
        fail: reject,
      });
    });
    const roomId = parseInviteText(data);
    if (!roomId) return null;
    if (!shouldPrompt(roomId)) return null;
    markHandled(roomId);
    return roomId;
  } catch {
    return null; // 全程静默：读剪贴板失败/解析失败均不打扰用户
  }
}
