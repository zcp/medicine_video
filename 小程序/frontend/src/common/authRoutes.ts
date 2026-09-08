/** 认证相关路由（登录默认入口为一键登录页） */

export const AUTH_ROUTES = {
  ONE_TAP_LOGIN: '/pages/auth/OneTapLogin',
  /** 密码登录（账号支持手机号/邮箱/用户名） */
  PASSWORD_LOGIN: '/pages/auth/Login',
  /** 验证码登录（短信 OTP） */
  CODE_LOGIN: '/pages/auth/PhoneLogin',
  /** @deprecated 使用 CODE_LOGIN */
  PHONE_LOGIN: '/pages/auth/PhoneLogin',
  /** @deprecated 使用 PASSWORD_LOGIN */
  EMAIL_LOGIN: '/pages/auth/Login',
  REGISTER_CHOICE: '/pages/auth/RegisterChoice',
  REGISTER: '/pages/auth/Register',
  FORGOT_PASSWORD: '/pages/auth/ForgotPassword'
} as const

export type AuthRoutePath = (typeof AUTH_ROUTES)[keyof typeof AUTH_ROUTES]

export function normalizePath(url: string): string {
  const raw = String(url || '').trim()
  if (!raw) return ''
  const qIdx = raw.indexOf('?')
  return qIdx >= 0 ? raw.slice(0, qIdx) : raw
}

export function isAuthLoginPath(path: string): boolean {
  const normalized = normalizePath(path)
  return (
    normalized === AUTH_ROUTES.ONE_TAP_LOGIN ||
    normalized === AUTH_ROUTES.PASSWORD_LOGIN ||
    normalized === AUTH_ROUTES.CODE_LOGIN
  )
}

export function buildAuthUrl(base: string, redirect?: string): string {
  const target = String(redirect || '').trim()
  if (!target) return base
  return `${base}?redirect=${encodeURIComponent(target)}`
}

export function buildOneTapLoginUrl(redirect?: string): string {
  return buildAuthUrl(AUTH_ROUTES.ONE_TAP_LOGIN, redirect)
}

export function buildPasswordLoginUrl(redirect?: string): string {
  return buildAuthUrl(AUTH_ROUTES.PASSWORD_LOGIN, redirect)
}

export function buildCodeLoginUrl(redirect?: string): string {
  return buildAuthUrl(AUTH_ROUTES.CODE_LOGIN, redirect)
}

/** @deprecated 使用 buildCodeLoginUrl */
export function buildPhoneLoginUrl(redirect?: string): string {
  return buildCodeLoginUrl(redirect)
}

/** @deprecated 使用 buildPasswordLoginUrl */
export function buildEmailLoginUrl(redirect?: string): string {
  return buildPasswordLoginUrl(redirect)
}

export function buildRegisterUrl(mode: 'phone' | 'email'): string {
  return `${AUTH_ROUTES.REGISTER}?mode=${mode}`
}
