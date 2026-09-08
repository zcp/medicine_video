/**
 * OTP 发码 + verify → ticket 封装
 * 对齐 V3.5 增量文档 §4.1 / §5.7（含邮箱验证码登录）
 */

import { ref } from 'vue'
import { sendVerificationCode, verifyVerificationCode } from '@/api/auth'
import type { ChannelType, ScenarioType } from '@/types/auth'
import { REGEX_PATTERNS } from '@/utils/validator'

export type LoginRecipientType = 'phone' | 'email'

export interface DetectedLoginRecipient {
  type: LoginRecipientType
  channel: ChannelType
  recipient: string
}

const INVALID_LOGIN_RECIPIENT_MSG = '请输入正确的手机号或邮箱'

/** 根据输入识别验证码登录账号类型（手机 / 邮箱） */
export function detectLoginRecipient(input: string): DetectedLoginRecipient | null {
  const trimmed = input.trim()
  if (!trimmed) return null

  if (trimmed.includes('@')) {
    if (!REGEX_PATTERNS.EMAIL.test(trimmed)) return null
    return { type: 'email', channel: 'EMAIL', recipient: trimmed.toLowerCase() }
  }

  if (isValidCnPhone(trimmed)) {
    return { type: 'phone', channel: 'SMS', recipient: trimmed }
  }

  return null
}

/** 校验验证码登录账号，失败时返回错误文案 */
export function validateLoginRecipient(input: string): { ok: true; value: DetectedLoginRecipient } | { ok: false; message: string } {
  const detected = detectLoginRecipient(input)
  if (!detected) {
    return { ok: false, message: INVALID_LOGIN_RECIPIENT_MSG }
  }
  return { ok: true, value: detected }
}

export function useOtpTicket() {
  const cooldown = ref(0)
  let cooldownTimer: ReturnType<typeof setInterval> | null = null

  function clearCooldown() {
    if (cooldownTimer) {
      clearInterval(cooldownTimer)
      cooldownTimer = null
    }
    cooldown.value = 0
  }

  function startCooldown(seconds = 60) {
    clearCooldown()
    cooldown.value = seconds
    cooldownTimer = setInterval(() => {
      cooldown.value--
      if (cooldown.value <= 0) clearCooldown()
    }, 1000)
  }

  async function sendOtp(params: {
    channel: ChannelType
    recipient: string
    scenario: ScenarioType
    captchaId?: string
    captchaSolution?: string
  }): Promise<void> {
    const body: Parameters<typeof sendVerificationCode>[0] = {
      channel: params.channel,
      recipient: params.recipient,
      scenario: params.scenario
    }
    if (params.captchaId && params.captchaSolution) {
      body.captcha_id = params.captchaId
      body.captcha_solution = params.captchaSolution
    }
    const res = await sendVerificationCode(body)
    if (res.code !== 200) {
      throw new Error(res.message || '发送验证码失败')
    }
    startCooldown()
  }

  async function verifyOtp(params: {
    channel: ChannelType
    recipient: string
    scenario: ScenarioType
    code: string
  }): Promise<string> {
    const res = await verifyVerificationCode({
      channel: params.channel,
      recipient: params.recipient,
      scenario: params.scenario,
      code: params.code
    })
    if (res.code !== 200 || !res.data?.ticket) {
      throw new Error(res.message || '验证码错误或已过期')
    }
    return res.data.ticket
  }

  /** 统一处理 ticket 无效（4011） */
  function handleTicketError(error: unknown): string {
    const msg = (error as { message?: string })?.message || ''
    const code = (error as { code?: number })?.code
    if (code === 4011 || msg.includes('ticket') || msg.includes('过期')) {
      return '验证已过期，请重新获取验证码'
    }
    return msg || '操作失败，请稍后重试'
  }

  return {
    cooldown,
    sendOtp,
    verifyOtp,
    startCooldown,
    clearCooldown,
    handleTicketError
  }
}

/** 中国大陆手机号校验 */
export function isValidCnPhone(phone: string): boolean {
  return /^1\d{10}$/.test(phone.trim())
}

/** 注册/改密密码强度（与后端一致：大小写+数字+特殊符号，min 8） */
const SPECIAL_CHAR_RE = /[!@#$%^&*(),.?":{}|<>]/

export function validateStrongPassword(pwd: string): string | null {
  if (pwd.length < 8) return '密码至少8位'
  if (!/[A-Z]/.test(pwd)) return '密码需包含大写字母'
  if (!/[a-z]/.test(pwd)) return '密码需包含小写字母'
  if (!/\d/.test(pwd)) return '密码需包含数字'
  if (!SPECIAL_CHAR_RE.test(pwd)) return '密码需包含特殊符号'
  return null
}
