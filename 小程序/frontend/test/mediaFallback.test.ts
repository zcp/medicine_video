/**
 * 全局媒体兜底契约（实现已并入 utils/url.ts，避免微信对新增模块热更未注册）
 */
import { describe, it, expect } from 'vitest'
import {
  FALLBACK_AVATAR,
  FALLBACK_COVER,
  FALLBACK_COVER_ERROR,
  FALLBACK_BRAND_LOGO,
  FALLBACK_BRAND_LOGO_ERROR,
  FALLBACK_BANNER,
  resolveAvatarUrl,
  shouldMarkAvatarBroken,
  resolveCoverUrl,
  shouldMarkCoverBroken,
  resolveBrandLogoUrl,
  shouldMarkBrandLogoBroken,
  resolveBannerUrl,
  shouldMarkBannerBroken
} from '../src/utils/url'

describe('mediaFallback (via url.ts)', () => {
  it('空值/空白走对应 DEFAULT_*', () => {
    expect(resolveAvatarUrl(null)).toBe(FALLBACK_AVATAR)
    expect(resolveAvatarUrl('')).toBe(FALLBACK_AVATAR)
    expect(resolveAvatarUrl('   ')).toBe(FALLBACK_AVATAR)
    expect(resolveCoverUrl(null)).toBe(FALLBACK_COVER)
    expect(resolveBrandLogoUrl(null)).toBe(FALLBACK_BRAND_LOGO)
    expect(resolveBannerUrl(null)).toBe(FALLBACK_BANNER)
  })

  it('broken 回落到失败图或同套头像兜底', () => {
    expect(resolveAvatarUrl('https://x.com/a.png', true)).toBe(FALLBACK_AVATAR)
    expect(resolveCoverUrl('https://x.com/c.jpg', true)).toBe(FALLBACK_COVER_ERROR)
    expect(resolveBrandLogoUrl('https://x.com/l.png', true)).toBe(FALLBACK_BRAND_LOGO_ERROR)
    expect(resolveBannerUrl('https://x.com/b.jpg', true)).toBe(FALLBACK_BANNER)
  })

  it('本地兜底图 @error 不得再标记 broken（防死循环）', () => {
    expect(shouldMarkAvatarBroken(FALLBACK_AVATAR)).toBe(false)
    expect(shouldMarkAvatarBroken('')).toBe(false)
    expect(shouldMarkAvatarBroken('https://x.com/a.png')).toBe(true)
    expect(shouldMarkAvatarBroken('https://x.com/a.png', true)).toBe(false)

    expect(shouldMarkCoverBroken(FALLBACK_COVER)).toBe(false)
    expect(shouldMarkCoverBroken(FALLBACK_COVER_ERROR)).toBe(false)
    expect(shouldMarkCoverBroken('https://x.com/c.jpg')).toBe(true)

    expect(shouldMarkBrandLogoBroken(FALLBACK_BRAND_LOGO)).toBe(false)
    expect(shouldMarkBrandLogoBroken('https://x.com/l.png')).toBe(true)

    expect(shouldMarkBannerBroken(FALLBACK_BANNER)).toBe(false)
    expect(shouldMarkBannerBroken('https://x.com/b.jpg')).toBe(true)
  })
})
