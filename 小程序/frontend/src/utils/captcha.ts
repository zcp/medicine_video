/**
 * 图形验证码工具
 * 后端 CaptchaResponse 标准字段 captcha_image；兼容旧版 image_base64
 */

export interface CaptchaPayload {
  captcha_id?: string
  captcha_image?: string
  image_base64?: string
}

export function resolveCaptchaImage(data: CaptchaPayload | null | undefined): string {
  if (!data) return ''
  const img = data.captcha_image ?? data.image_base64
  return typeof img === 'string' ? img : ''
}

export function pickCaptchaFields(data: CaptchaPayload | null | undefined): {
  captchaId: string
  captchaImage: string
} {
  return {
    captchaId: data?.captcha_id || '',
    captchaImage: resolveCaptchaImage(data)
  }
}
