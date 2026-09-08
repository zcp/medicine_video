// tests/utils/tagChip.spec.ts
import { describe, it, expect } from 'vitest'
import {
  normalizeTagName,
  tagNamesEqual,
  hasChipName,
  hasChipId,
  pushChipUnique,
  pruneInactiveChips,
} from '../src/utils/tagChip'
import type { TagChip } from '../src/types/tag'

const chipA: TagChip = { id: 'a', name: '手术直播' }
const chipB: TagChip = { id: 'b', name: '病例讨论' }
const chipA2: TagChip = { id: 'a2', name: '手术直播' } // 同名不同 id（resolve 并发复用可能形态）

describe('normalizeTagName', () => {
  it('trim 前后空白', () => {
    expect(normalizeTagName('  手术直播  ')).toBe('手术直播')
  })
  it('英文转小写', () => {
    expect(normalizeTagName('  ICU ')).toBe('icu')
  })
  it('空串安全', () => {
    expect(normalizeTagName('')).toBe('')
    expect(normalizeTagName('   ')).toBe('')
  })
})

describe('tagNamesEqual', () => {
  it('全等为真', () => {
    expect(tagNamesEqual('手术直播', '手术直播')).toBe(true)
  })
  it('忽略首尾空白与大小写', () => {
    expect(tagNamesEqual(' ICU ', 'icu')).toBe(true)
    expect(tagNamesEqual(' 病例讨论 ', '病例讨论')).toBe(true)
  })
  it('不同文本为假', () => {
    expect(tagNamesEqual('手术直播', '手术')).toBe(false)
    expect(tagNamesEqual('ICU', 'Icuu')).toBe(false)
  })
})

describe('hasChipName / hasChipId', () => {
  const chips = [chipA, chipB]
  it('同名命中（忽略大小写/空白）', () => {
    expect(hasChipName(chips, ' 手术直播 ')).toBe(true)
    expect(hasChipName(chips, '手术直')).toBe(false)
  })
  it('id 命中', () => {
    expect(hasChipId(chips, 'b')).toBe(true)
    expect(hasChipId(chips, 'zz')).toBe(false)
  })
  it('空数组安全', () => {
    expect(hasChipName([], 'x')).toBe(false)
    expect(hasChipId([], 'x')).toBe(false)
  })
})

describe('pushChipUnique', () => {
  it('追加新 chip 返回新数组', () => {
    const next = pushChipUnique([chipA], chipB)
    expect(next).toHaveLength(2)
    expect(next).not.toBe([chipA] as unknown as TagChip[])
    expect(next[1]).toEqual(chipB)
  })
  it('id 重复不追加（返回原引用）', () => {
    const chips = [chipA]
    const next = pushChipUnique(chips, chipA)
    expect(next).toBe(chips)
    expect(next).toHaveLength(1)
  })
  it('同名不同 id 不追加（防重复词）', () => {
    const chips = [chipA]
    const next = pushChipUnique(chips, chipA2)
    expect(next).toBe(chips)
    expect(next).toHaveLength(1)
  })
  it('非法 chip（缺 id/name）忽略', () => {
    expect(pushChipUnique([], { id: '', name: 'x' })).toHaveLength(0)
    expect(pushChipUnique([], { id: 'x', name: '' })).toHaveLength(0)
    expect(pushChipUnique([], {} as TagChip)).toHaveLength(0)
  })
  it('已有同名词时对空白敏感名称仍去重', () => {
    const chips = [chipA]
    expect(pushChipUnique(chips, { id: 'c', name: '  手术直播 ' })).toBe(chips)
  })
})

describe('pruneInactiveChips（启用词表差集剔除）', () => {
  const chips = [chipA, chipB]
  it('保留仍在启用集中的 chip', () => {
    const next = pruneInactiveChips(chips, [{ id: 'a' }, { id: 'b' }])
    expect(next).toHaveLength(2)
    expect(next).toBe(chips) // 无剔除时返回原引用
  })
  it('剔除不在启用集中的 chip', () => {
    const next = pruneInactiveChips(chips, [{ id: 'a' }])
    expect(next).toEqual([chipA])
  })
  it('启用集为空数组 → 全剔（差集语义）', () => {
    expect(pruneInactiveChips(chips, [])).toEqual([])
  })
  it('chips 为空 → 原样返回', () => {
    const empty: TagChip[] = []
    expect(pruneInactiveChips(empty, [{ id: 'a' }])).toBe(empty)
  })
  it('防御：非数组输入（信封变化）→ 不剔除原样返回', () => {
    const obj = { items: [{ id: 'a' }] } as unknown
    expect(pruneInactiveChips(chips, obj)).toBe(chips)
    expect(pruneInactiveChips(chips, null)).toBe(chips)
    expect(pruneInactiveChips(chips, undefined)).toBe(chips)
  })
  it('防御：启用集含非法项（无 id）自动忽略', () => {
    const next = pruneInactiveChips(chips, [{ id: 'a' }, { name: 'no-id' }])
    expect(next).toEqual([chipA])
  })
})
