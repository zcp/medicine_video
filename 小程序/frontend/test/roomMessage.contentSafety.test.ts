/**

 * 直播间留言 — 内容安全（V2）自测

 * 对齐《07-直播间留言-V2-内容安全-前端设计文档.md》§四

 */



import { describe, it, expect, vi, beforeEach } from 'vitest'

import {
  CONTENT_SAFETY_CODE,
  extractBusinessCode,
  getContentSafetyMessage,
  handleContentSafetyError,
  isTechnicalBackendMessage,
  pickUserFacingMessage,
  getUserFacingErrorMessage
} from '@/utils/contentSafety'

import { getRoomMessageErrorMessage, ROOM_MESSAGE_ERROR_CODES } from '@/types/roomMessage'



describe('07-直播间留言 V2 内容安全', () => {

  beforeEach(() => {

    vi.stubGlobal('uni', {

      showToast: vi.fn()

    })

  })



  describe('extractBusinessCode', () => {

    it('从 Error.code 提取业务码', () => {

      expect(extractBusinessCode({ code: 2005, message: '内容违规' })).toBe(2005)

    })



    it('从 raw.data.code 提取业务码', () => {

      expect(extractBusinessCode({ raw: { data: { code: 2004 } } })).toBe(2004)

    })

  })



  describe('isTechnicalBackendMessage', () => {

    it('识别含「规则」等实现术语的后端文案', () => {

      expect(isTechnicalBackendMessage('内容违规：留言命中广告引流拦截规则')).toBe(true)

      expect(isTechnicalBackendMessage('内容安全校验暂不可用')).toBe(true)

    })



    it('限流等人话文案可通过', () => {

      expect(isTechnicalBackendMessage('发送过于频繁，请 5 秒后再试')).toBe(false)

      expect(isTechnicalBackendMessage('直播间已关闭')).toBe(false)

    })

  })



  describe('2005 内容违规（block）', () => {

    it('技术规则文案回退为审核兜底，不暴露 rule 细节', () => {
      const msg = getContentSafetyMessage(
        CONTENT_SAFETY_CODE.CONTENT_BLOCKED,
        '内容违规：留言命中广告引流拦截规则'
      )
      expect(msg).toBe('内容未通过审核，请修改后重试')
      expect(msg).not.toMatch(/规则|命中|rule/i)
    })

    it('后端中文审核文案原样透传', () => {
      const hint = '内容未通过审核：疑似含广告引流话术，请修改后重试'
      expect(getContentSafetyMessage(CONTENT_SAFETY_CODE.CONTENT_BLOCKED, hint)).toBe(hint)
    })

    it('图片类违规使用专用文案', () => {
      expect(getContentSafetyMessage(CONTENT_SAFETY_CODE.CONTENT_BLOCKED, '图片内容违规')).toBe(
        '暂无法使用此图片，请更换后再试'
      )
    })

    it('handleContentSafetyError 命中 2005 返回 true', () => {
      const handled = handleContentSafetyError(
        { code: 2005, message: '内容违规：含外链' },
        { showToast: false }
      )
      expect(handled).toBe(true)
    })

    it('showError:false 仅 __handled 时仍应可弹（不因 __handled 静默）', () => {
      const handled = handleContentSafetyError(
        { code: 2005, message: '内容未通过审核，请修改后重试', __handled: true },
        { showToast: false }
      )
      expect(handled).toBe(true)
    })

    it('request 已 __toastShown 时跳过重复 toast 逻辑但仍返回 true', () => {
      const handled = handleContentSafetyError(
        { code: 2005, message: '内容未通过审核，请修改后重试', __handled: true, __toastShown: true },
        { showToast: false }
      )
      expect(handled).toBe(true)
    })
  })

  describe('2004 服务异常 / 限流', () => {
    it('无后端 message 时使用默认文案', () => {
      expect(getContentSafetyMessage(CONTENT_SAFETY_CODE.SERVICE_ERROR)).toBe(
        '审核服务暂不可用，请稍后再试'
      )
      expect(getContentSafetyMessage(CONTENT_SAFETY_CODE.SERVICE_ERROR)).not.toMatch(
        /内容安全|校验|规则/
      )
    })



    it('限流场景透传人话 message', () => {

      const rateLimitMsg = '发送过于频繁，请 5 秒后再试'

      expect(pickUserFacingMessage(rateLimitMsg, '暂时无法提交，请稍后再试')).toBe(rateLimitMsg)

    })



    it('技术 message 回退为默认文案', () => {

      expect(

        pickUserFacingMessage('内容安全服务异常', '暂时无法提交，请稍后再试')

      ).toBe('暂时无法提交，请稍后再试')

    })

  })



  describe('其他业务错误码', () => {

    it('3001 引导登录', () => {

      expect(getRoomMessageErrorMessage(ROOM_MESSAGE_ERROR_CODES.UNAUTHORIZED)).toContain('登录')

    })



    it('3002 只能删自己的留言', () => {

      expect(getRoomMessageErrorMessage(ROOM_MESSAGE_ERROR_CODES.FORBIDDEN)).toContain('自己')

    })



    it('3003 管理员权限', () => {

      expect(getRoomMessageErrorMessage(ROOM_MESSAGE_ERROR_CODES.ADMIN_FORBIDDEN)).toContain('管理员')

    })



    it('2004 业务错误不透传含规则的后端 message', () => {

      expect(

        getRoomMessageErrorMessage(

          ROOM_MESSAGE_ERROR_CODES.BUSINESS_ERROR,

          '内容违规：留言命中外链拦截规则'

        )

      ).toBe('暂时无法发送讨论，请稍后再试')

    })

  })



  describe('getUserFacingErrorMessage', () => {
    it('从 error 对象提取并过滤技术文案', () => {
      expect(
        getUserFacingErrorMessage(
          { message: '内容违规：留言命中外链拦截规则' },
          '操作失败，请稍后再试'
        )
      ).toBe('操作失败，请稍后再试')
    })

    it('从 raw.data.message 提取人话文案', () => {
      expect(
        getUserFacingErrorMessage(
          { raw: { data: { message: '发送过于频繁，请 5 秒后再试' } } },
          '暂时无法提交，请稍后再试'
        )
      ).toBe('发送过于频繁，请 5 秒后再试')
    })
  })

  describe('warn 路径（HTTP 200）', () => {

    it('成功时不应被 contentSafety 拦截', () => {

      expect(handleContentSafetyError({ code: 200 }, { showToast: false })).toBe(false)

    })

  })

})


