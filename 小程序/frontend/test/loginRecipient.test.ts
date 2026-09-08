import { describe, expect, it } from 'vitest'
import { detectLoginRecipient, validateLoginRecipient } from '@/composables/useOtpTicket'

describe('detectLoginRecipient', () => {
  it('识别中国大陆手机号', () => {
    expect(detectLoginRecipient('13800138000')).toEqual({
      type: 'phone',
      channel: 'SMS',
      recipient: '13800138000'
    })
  })

  it('识别邮箱并转小写', () => {
    expect(detectLoginRecipient(' User@Example.COM ')).toEqual({
      type: 'email',
      channel: 'EMAIL',
      recipient: 'user@example.com'
    })
  })

  it('拒绝非法邮箱', () => {
    expect(detectLoginRecipient('not-an-email')).toBeNull()
    expect(detectLoginRecipient('bad@')).toBeNull()
  })

  it('拒绝非法手机号', () => {
    expect(detectLoginRecipient('12345')).toBeNull()
    expect(detectLoginRecipient('23800138000')).toBeNull()
  })

  it('validateLoginRecipient 返回统一错误文案', () => {
    const result = validateLoginRecipient('abc')
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.message).toBe('请输入正确的手机号或邮箱')
    }
  })
})
