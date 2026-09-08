/**
 * 专家列表/详情/精选：头像经 utils/url 兜底 API
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('专家链路头像兜底落地', () => {
  it('store 列表与详情均 resolveAvatarUrl', () => {
    const src = readFileSync(resolve(__dirname, '../src/store/expert.ts'), 'utf8')
    expect(src).toContain('resolveAvatarUrl')
    expect(src.match(/avatar: resolveAvatarUrl\(/g)?.length).toBeGreaterThanOrEqual(3)
  })

  it('ExpertCard / ExpertProfile / FeaturedExperts 从 @/utils/url 引入兜底', () => {
    for (const rel of [
      '../src/components/expert/ExpertCard.vue',
      '../src/components/expert/ExpertProfile.vue',
      '../src/components/home/FeaturedExperts.vue'
    ]) {
      const src = readFileSync(resolve(__dirname, rel), 'utf8')
      expect(src).toContain("from '@/utils/url'")
      expect(src).toContain('resolveAvatarUrl')
      expect(src).toContain('shouldMarkAvatarBroken')
      expect(src).toContain('@error')
      expect(src).not.toContain('mediaFallback')
    }
  })
})
