/**
 * 专家详情匿名浏览契约：未登录仅看公开内容，不得触发用户态接口
 * 对齐：docs/专家系统功能模块开发指南.md、首页精选专家模块开发设计文档.md
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const detailSource = readFileSync(
  resolve(__dirname, '../src/pages/expert/ExpertDetail.vue'),
  'utf8'
)

describe('ExpertDetail 匿名浏览鉴权边界', () => {
  it('加载阶段用 isAuthed 门禁用户态接口（关注检查 + 收藏列表）', () => {
    expect(detailSource).toContain('const isAuthed = authStore.isAuthenticated')
    expect(detailSource).toContain('isAuthed ? expertStore.checkFollow(id) : Promise.resolve()')
    expect(detailSource).toMatch(/if\s*\(\s*isAuthed\s*\)\s*\{[\s\S]*favStore\.fetch/)
  })

  it('未登录收藏集合应置空，避免残留登录态收藏星标', () => {
    expect(detailSource).toMatch(/else\s*\{\s*favSet\.value\s*=\s*new\s+Set\(\)/)
  })

  it('关注/收藏写操作仍走 ensureAuthed（行为才要登录）', () => {
    expect(detailSource).toContain('if (!ensureAuthed(id)) return')
    expect(detailSource).toContain('if (!ensureAuthed(expertId)) return')
  })
})
