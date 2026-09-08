/**
 * 16-D5 品牌软删 C 端过滤 — 前端自测（纯逻辑）
 * 对齐《16-D5-品牌软删-C端挂靠与货架不可售-后端设计文档》V1.1
 */
import { describe, it, expect } from 'vitest'

/** 与 LiveView / BrandZone 口径一致：未回传视为启用，显式 false 丢弃 */
function isBrandActive(it: any, brandObj?: any): boolean {
  const flag = it?.is_active ?? brandObj?.is_active ?? it?.brand_is_active
  return flag !== false
}

function filterActiveBrands<T extends { is_active?: boolean; id?: string; name?: string }>(
  list: T[]
): T[] {
  return list.filter((b) => b.is_active !== false && !!b.id && !!b.name)
}

describe('16-D5 品牌软删 C 端过滤', () => {
  it('T3: 显式 is_active=false 丢弃', () => {
    const items = [
      { id: '1', name: '启用品牌', is_active: true },
      { id: '2', name: '停用品牌', is_active: false },
      { id: '3', name: '未回传字段' }
    ]
    const out = filterActiveBrands(items)
    expect(out.map((x) => x.id)).toEqual(['1', '3'])
  })

  it('房间挂靠：brand 嵌套 is_active=false 丢弃', () => {
    const it = { brand_id: 'b1', brand: { id: 'b1', name: 'X', is_active: false } }
    expect(isBrandActive(it, it.brand)).toBe(false)
  })

  it('房间挂靠：未回传 is_active 视为启用', () => {
    const it = { brand_id: 'b2', name: 'Y' }
    expect(isBrandActive(it, null)).toBe(true)
  })

  it('T1 口径：2001 / is_active=false 均按不可用', () => {
    const cases = [
      { code: 2001, is_active: true, unavailable: true },
      { code: 200, is_active: false, unavailable: true },
      { code: 200, is_active: true, unavailable: false }
    ]
    for (const c of cases) {
      const unavailable = c.code === 2001 || c.is_active === false
      expect(unavailable).toBe(c.unavailable)
    }
  })
})
