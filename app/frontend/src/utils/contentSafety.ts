/**
 * 内容安全错误码与用户友好文案
 * 对齐后端全局异常：422/2005（内容违规）、422/2004（内容安全检查服务异常）
 */

export const CONTENT_SAFETY_CODE = {
  SERVICE_ERROR: 2004,
  CONTENT_BLOCKED: 2005,
} as const;

/** C 端固定文案 */
export const USER_CONTENT_BLOCKED_MESSAGE = '内容未通过审核，请修改后重试';
export const USER_IMAGE_BLOCKED_MESSAGE = '暂时无法使用此图片，请更换后再试';
export const USER_SERVICE_UNAVAILABLE_MESSAGE = '内容安全检查暂不可用，请稍后重试';

export function isContentSafetyCode(code: number): boolean {
  return code === CONTENT_SAFETY_CODE.SERVICE_ERROR || code === CONTENT_SAFETY_CODE.CONTENT_BLOCKED;
}

/**
 * 2004/2005 用户可见文案
 * 2005 一律固定文案（含图片场景细分）；2004 透传已人话化的后端 message（如限流），否则用固定文案
 */
export function getContentSafetyMessage(code: number, backendMessage?: string): string {
  if (code === CONTENT_SAFETY_CODE.CONTENT_BLOCKED) {
    const hint = backendMessage?.trim() || '';
    if (/图片|头像|avatar|image/i.test(hint)) {
      return USER_IMAGE_BLOCKED_MESSAGE;
    }
    return USER_CONTENT_BLOCKED_MESSAGE;
  }
  if (code === CONTENT_SAFETY_CODE.SERVICE_ERROR) {
    const text = backendMessage?.trim();
    return text || USER_SERVICE_UNAVAILABLE_MESSAGE;
  }
  return backendMessage?.trim() || '操作失败，请稍后再试';
}
