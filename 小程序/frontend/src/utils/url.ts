/**
 * URL / 资源地址相关工具
 */

import { DEFAULT_CONFIG } from '@/common/constants'

function isLoopbackHost(hostname?: string | null): boolean {
  const v = String(hostname || '').trim().toLowerCase()
  return v === 'localhost' || v === '127.0.0.1' || v === '::1'
}

function repairLocalMediaAbsoluteUrl(rawUrl: string, mediaBaseUrl?: string): string {
  const raw = String(rawUrl || '').trim()
  if (!/^https?:\/\//i.test(raw)) return raw

  const mediaBase = String(mediaBaseUrl || '').trim().replace(/\/+$/, '')
  if (!mediaBase) return raw

  const parseAbsolute = (input: string): { protocol: string; host: string; hostname: string; port: string; pathWithQueryHash: string } | null => {
    const m = String(input || '').match(/^(https?):\/\/([^/?#]+)([^?#]*)(\?[^#]*)?(#.*)?$/i)
    if (!m) return null
    const protocol = `${String(m[1] || '').toLowerCase()}:`
    const host = String(m[2] || '').trim()
    const path = String(m[3] || '') || '/'
    const query = String(m[4] || '')
    const hash = String(m[5] || '')

    const isBracketIPv6 = host.startsWith('[')
    let hostname = host
    let port = ''
    if (isBracketIPv6) {
      const i = host.indexOf(']')
      if (i > 0) {
        hostname = host.slice(1, i)
        const rest = host.slice(i + 1)
        if (rest.startsWith(':')) port = rest.slice(1)
      }
    } else {
      const i = host.lastIndexOf(':')
      if (i > -1 && host.indexOf(':') === i) {
        hostname = host.slice(0, i)
        port = host.slice(i + 1)
      }
    }

    return {
      protocol,
      host,
      hostname: hostname.toLowerCase(),
      port,
      pathWithQueryHash: `${path}${query}${hash}`
    }
  }

  const parsedRaw = parseAbsolute(raw)
  const parsedBase = parseAbsolute(mediaBase)
  if (parsedRaw && parsedBase) {
    if (!String(parsedRaw.pathWithQueryHash || '').startsWith('/media/')) return raw

    // 后端常把 PUBLIC_HOST 写成无端口绝对地址（如 http://10.x.x.x/media/...），
    // 而本地网关实际在 :8080。旧逻辑只修 loopback，局域网同主机缺端口/端口不一致时也会裂图。
    const sameHost = parsedRaw.hostname === parsedBase.hostname
    const rawIsLoopback = isLoopbackHost(parsedRaw.hostname)
    if (!rawIsLoopback && !sameHost) return raw
    if (!parsedBase.host) return raw
    if (sameHost && parsedRaw.port && parsedRaw.port === parsedBase.port) return raw

    return `${parsedBase.protocol}//${parsedBase.host}${parsedRaw.pathWithQueryHash}`
  }

  try {
    const u = new URL(raw)
    if (!u.pathname.startsWith('/media/')) return raw

    const b = new URL(mediaBase)
    const sameHost = u.hostname.toLowerCase() === b.hostname.toLowerCase()
    const rawIsLoopback = isLoopbackHost(u.hostname)
    if (!rawIsLoopback && !sameHost) return raw
    if (sameHost && u.port && b.port && u.port === b.port) return raw

    return `${b.protocol}//${b.host}${u.pathname}${u.search}${u.hash}`
  } catch {
    return raw
  }
}

/**
 * 小程序 image 不支持 http（开发者工具/真机都会告警或失败）。
 * 这里统一升级到 HTTPS，仅有 IPv4 地址例外（用于本地资源服务器）。
 */
export function normalizeImageUrl(url?: string | null): string | null {
  if (!url) return null
  const trimmed = String(url).trim()
  if (!trimmed) return null

  const getHostname = (fullUrl: string): string | null => {
    const m = String(fullUrl || '').match(/^https?:\/\/([^/?#]+)/i)
    const hostWithPort = m?.[1] || null
    if (!hostWithPort) return null
    // 去掉端口号，只保留主机名（isLoopbackHost 需要纯主机名进行比较）
    return hostWithPort.split(':')[0]
  }

  if (trimmed.startsWith('//')) {
    // 所有主机都升级到 HTTPS
    return `https:${trimmed}`
  }

  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    const isHttps = trimmed.startsWith('https://')
    try {
      const u = new URL(trimmed)
      const isIPv4 = /^\d{1,3}(?:\.\d{1,3}){3}$/.test(u.hostname)
      // 若为 IPv4 主机（如资源服务器仅支持明文 http），避免强制 https 导致连接失败
      if (isIPv4) {
        return trimmed
      }
      // 本地回环地址（localhost / 127.0.0.1 / ::1）也应保持原协议，避免本地开发时触发 HTTPS 证书错误
      if (isLoopbackHost(u.hostname)) {
        return trimmed
      }
    } catch {
      const hostname = getHostname(trimmed)
      if (hostname && /^\d{1,3}(?:\.\d{1,3}){3}$/.test(hostname)) {
        return trimmed
      }
      // URL 不可用（如部分小程序运行时）时，同样保留本地回环地址原协议
      if (isLoopbackHost(hostname)) {
        return trimmed
      }
      // 无法解析则按原逻辑升级协议
    }
    // 所有非 IPv4 的主机都升级到 HTTPS
    if (isHttps) return trimmed
    return `https://${trimmed.slice('http://'.length)}`
  }
  return trimmed
}

function deriveOriginFromBaseApiUrl(raw?: string): string | null {
  const v = (raw || '').trim().replace(/\/+$/, '')
  if (!v) return null
  try {
    const u = new URL(v)
    return u.origin
  } catch {
    // 小程序环境可能没有 URL；用正则兜底提取 origin
    const m = v.match(/^(https?:\/\/[^/?#]+)/i)
    return m?.[1] || null
  }
}

/**
 * 将后端返回的媒体路径（如 /media/xxx.png）转换为可访问的完整 URL。
 *
 * 优先使用 VITE_MEDIA_BASE_URL（建议配置为域名 origin，例如 https://mp.xxx.com）
 * 否则从 VITE_BASE_API_URL 推导 origin（例如 https://mp.xxx.com/api/core -> https://mp.xxx.com）
 */
export function resolveMediaUrl(path?: string | null): string {
  const trimmed = String(path || '').trim()
  if (!trimmed) return ''

  // 过滤小程序本地临时路径（uni.chooseImage 返回的 https://tmp/ 或 http://tmp/）
  if (/^https?:\/\/tmp\//i.test(trimmed)) return ''

  const mediaBase = (import.meta as any).env?.VITE_MEDIA_BASE_URL as string | undefined

  // 已经是完整URL
  if (/^https?:\/\//i.test(trimmed) || trimmed.startsWith('//')) {
    const repaired = repairLocalMediaAbsoluteUrl(trimmed, mediaBase)
    return normalizeImageUrl(repaired) || ''
  }

  // 小程序包内静态资源
  if (trimmed.startsWith('/static/') || trimmed.startsWith('static/')) {
    return trimmed.startsWith('/') ? trimmed : `/${trimmed}`
  }

  // 后端返回的相对路径（通常以 /media 开头）
  const baseApi = (import.meta as any).env?.VITE_BASE_API_URL as string | undefined
  const origin = (mediaBase || '').trim().replace(/\/+$/, '') || deriveOriginFromBaseApiUrl(baseApi) || ''

  // 诊断：/media 仍然是相对路径时，打印一次原因（仅开发态）
  if (process.env.NODE_ENV === 'development' && !origin) {
    const normalizedPathPreview = trimmed.startsWith('/') ? trimmed : `/${trimmed}`
    if (normalizedPathPreview.startsWith('/media/')) {
      ;(globalThis as any).__logged_media_origin_missing ||= false
      if (!(globalThis as any).__logged_media_origin_missing) {
        ;(globalThis as any).__logged_media_origin_missing = true
        const baseApiHost = String(baseApi || '').match(/^https?:\/\/([^/?#]+)/i)?.[1] || ''
        const mediaBaseHost = String(mediaBase || '').match(/^https?:\/\/([^/?#]+)/i)?.[1] || ''
        // eslint-disable-next-line no-console
        console.warn('🖼️ resolveMediaUrl: origin 为空，/media 将退化为本地路径', {
          VITE_MEDIA_BASE_URL: mediaBaseHost ? `set(${mediaBaseHost})` : String(!!(mediaBase || '').trim()),
          VITE_BASE_API_URL: baseApiHost ? `set(${baseApiHost})` : String(!!(baseApi || '').trim())
        })
      }
    }
  }

  const normalizedPath = trimmed.startsWith('/') ? trimmed : `/${trimmed}`
  const full = origin ? `${origin}${normalizedPath}` : normalizedPath

  const normalizedFull = normalizeImageUrl(full) || full

  // 仅在开发态对相对媒体路径打印一次调试信息，便于排查 /media 500
  if (process.env.NODE_ENV === 'development' && normalizedPath.startsWith('/media/')) {
    // 延迟引入，避免在某些构建链路里形成不必要的强耦合
    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { logger } = require('@/logs/logger')
      logger.debug('network', 'resolveMediaUrl', {
        input: trimmed,
        origin,
        output: normalizedFull,
        hasMediaBase: !!(mediaBase || '').trim(),
        hasBaseApi: !!(baseApi || '').trim()
      })
    } catch {
      // ignore
    }
  }

  return normalizedFull
}

// ================== 媒体兜底（并入 url，避免微信小程序对新增独立模块热更未注册） ==================

export const FALLBACK_AVATAR = DEFAULT_CONFIG.DEFAULT_AVATAR
export const FALLBACK_COVER = DEFAULT_CONFIG.DEFAULT_COVER
export const FALLBACK_COVER_ERROR = DEFAULT_CONFIG.COVER_LOAD_ERROR
export const FALLBACK_BRAND_LOGO = DEFAULT_CONFIG.DEFAULT_BRAND_LOGO
export const FALLBACK_BRAND_LOGO_ERROR = DEFAULT_CONFIG.BRAND_LOGO_LOAD_ERROR
export const FALLBACK_BANNER = DEFAULT_CONFIG.DEFAULT_BANNER

function isTmpMediaUrl(raw: string): boolean {
  return /^https?:\/\/tmp\//i.test(raw)
}

function isAvatarFallback(raw: string): boolean {
  return !raw || raw === FALLBACK_AVATAR || raw.includes('avatar-default.')
}

function isCoverFallback(raw: string): boolean {
  return (
    !raw ||
    raw === FALLBACK_COVER ||
    raw === FALLBACK_COVER_ERROR ||
    raw.includes('cover-default.') ||
    raw.includes('cover-error.')
  )
}

function isBrandLogoFallback(raw: string): boolean {
  return (
    !raw ||
    raw === FALLBACK_BRAND_LOGO ||
    raw === FALLBACK_BRAND_LOGO_ERROR ||
    raw.includes('brand-logo-default.') ||
    raw.includes('brand-logo-error.')
  )
}

function isBannerFallback(raw: string): boolean {
  return !raw || raw === FALLBACK_BANNER || raw.includes('banner-default.')
}

/** 头像：空值 → DEFAULT_AVATAR；broken → 同套兜底 */
export function resolveAvatarUrl(raw?: string | null, broken: boolean = false): string {
  if (broken) return FALLBACK_AVATAR
  const s = String(raw || '').trim()
  if (!s || isTmpMediaUrl(s)) return FALLBACK_AVATAR
  return resolveMediaUrl(s) || FALLBACK_AVATAR
}

/** 头像 @error 是否应标记 broken（本地兜底失败返回 false，防死循环） */
export function shouldMarkAvatarBroken(raw?: string | null, alreadyBroken: boolean = false): boolean {
  if (alreadyBroken) return false
  return !isAvatarFallback(String(raw || '').trim())
}

/** 封面：空 → DEFAULT_COVER；broken → COVER_LOAD_ERROR */
export function resolveCoverUrl(raw?: string | null, broken: boolean = false): string {
  if (broken) return FALLBACK_COVER_ERROR
  const s = String(raw || '').trim()
  if (!s || isTmpMediaUrl(s)) return FALLBACK_COVER
  return resolveMediaUrl(s) || FALLBACK_COVER
}

export function shouldMarkCoverBroken(raw?: string | null, alreadyBroken: boolean = false): boolean {
  if (alreadyBroken) return false
  return !isCoverFallback(String(raw || '').trim())
}

/** 品牌 Logo：空 → DEFAULT_BRAND_LOGO；broken → BRAND_LOGO_LOAD_ERROR */
export function resolveBrandLogoUrl(raw?: string | null, broken: boolean = false): string {
  if (broken) return FALLBACK_BRAND_LOGO_ERROR
  const s = String(raw || '').trim()
  if (!s || isTmpMediaUrl(s)) return FALLBACK_BRAND_LOGO
  return resolveMediaUrl(s) || FALLBACK_BRAND_LOGO
}

export function shouldMarkBrandLogoBroken(raw?: string | null, alreadyBroken: boolean = false): boolean {
  if (alreadyBroken) return false
  return !isBrandLogoFallback(String(raw || '').trim())
}

/** Banner：空/失败 → DEFAULT_BANNER */
export function resolveBannerUrl(raw?: string | null, broken: boolean = false): string {
  if (broken) return FALLBACK_BANNER
  const s = String(raw || '').trim()
  if (!s || isTmpMediaUrl(s)) return FALLBACK_BANNER
  return resolveMediaUrl(s) || FALLBACK_BANNER
}

export function shouldMarkBannerBroken(raw?: string | null, alreadyBroken: boolean = false): boolean {
  if (alreadyBroken) return false
  return !isBannerFallback(String(raw || '').trim())
}
