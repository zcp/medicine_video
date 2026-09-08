/**
 * 手机号工具函数单元测试 - phone.test.ts
 * 覆盖 src/utils/phone.ts（阶段 F 出口审查验收项）
 * 与后端 tests/test_phone.py 用例对齐
 */
import { describe, expect, it } from 'vitest'

import { isValidCnPhone, normalizeCnPhone } from './phone'

describe('normalizeCnPhone', () => {
  it('纯 11 位原样返回', () => {
    expect(normalizeCnPhone('13800138000')).toBe('13800138000')
  })

  it('空格分隔格式归一化', () => {
    expect(normalizeCnPhone('138 0013 8000')).toBe('13800138000')
  })

  it('横线分隔格式归一化', () => {
    expect(normalizeCnPhone('138-0013-8000')).toBe('13800138000')
  })

  it('+86 前缀（含空格）归一化', () => {
    expect(normalizeCnPhone('+86 13800138000')).toBe('13800138000')
  })

  it('+86 前缀（无空格）归一化', () => {
    expect(normalizeCnPhone('+8613800138000')).toBe('13800138000')
  })

  it('86 前缀 13 位归一化', () => {
    expect(normalizeCnPhone('8613800138000')).toBe('13800138000')
  })

  it('空值返回空串', () => {
    expect(normalizeCnPhone('')).toBe('')
    expect(normalizeCnPhone('   ')).toBe('')
  })
})

describe('isValidCnPhone', () => {
  it('合法纯 11 位', () => {
    expect(isValidCnPhone('13800138000')).toBe(true)
  })

  it('+86 前缀合法', () => {
    expect(isValidCnPhone('+8613800138000')).toBe(true)
  })

  it('空格/横线格式合法', () => {
    expect(isValidCnPhone('138 0013 8000')).toBe(true)
    expect(isValidCnPhone('138-0013-8000')).toBe(true)
  })

  it('第二位非 3-9 非法', () => {
    expect(isValidCnPhone('12345678901')).toBe(false)
  })

  it('长度不足非法', () => {
    expect(isValidCnPhone('1380013800')).toBe(false)
  })

  it('含非数字字符非法', () => {
    expect(isValidCnPhone('138abc38000')).toBe(false)
  })

  it('空值非法', () => {
    expect(isValidCnPhone('')).toBe(false)
  })
})
