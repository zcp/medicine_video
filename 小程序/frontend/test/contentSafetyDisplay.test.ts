/**
 * 内容安全展示映射 — 自测
 * 对齐《12-全局内容安全与审核-前端设计文档》§3.0、§6
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  formatSceneLabel,
  formatDecisionLabel,
  formatActionLabel,
  formatRuleDisplayName,
  formatRuleTypeName,
  formatScenesSummary,
  groupContentSafetyRules,
  isUserFacingText,
  logContentSafetyAuditDetail
} from '@/utils/contentSafetyDisplay'
import type { ContentSafetyRule } from '@/types/contentSafety'

function makeRule(partial: Partial<ContentSafetyRule>): ContentSafetyRule {
  return {
    id: partial.id || '1',
    rule_name: partial.rule_name || 'x',
    scene: partial.scene || 'message',
    target_field: partial.target_field || 'content',
    match_type: partial.match_type || 'keyword',
    pattern: partial.pattern || '最,第一',
    action: partial.action || 'block',
    severity: partial.severity || 'high',
    priority: partial.priority ?? 11,
    enabled: partial.enabled ?? true,
    remark: partial.remark,
    binding_level: partial.binding_level || 'statutory',
    rule_category: partial.rule_category || 'absolute_superlative',
    created_at: partial.created_at || '2026-07-09T00:00:00Z',
    updated_at: partial.updated_at || '2026-07-09T00:00:00Z'
  }
}

describe('contentSafetyDisplay 全员人话映射', () => {
  beforeEach(() => {
    vi.stubGlobal('uni', { showToast: vi.fn() })
  })

  it('scene 展示中文来源', () => {
    expect(formatSceneLabel('message')).toBe('留言')
    expect(formatSceneLabel('search_query')).toBe('搜索词')
    expect(formatSceneLabel('unknown_enum')).toBe('其他位置')
  })

  it('decision 不暴露 block/warn 原文', () => {
    expect(formatDecisionLabel('block')).toBe('未过审')
    expect(formatDecisionLabel('warn')).toBe('已留底')
    expect(formatDecisionLabel('allow')).toBe('已通过')
  })

  it('action 不暴露 block/warn 原文', () => {
    expect(formatActionLabel('block')).toBe('不让发布')
    expect(formatActionLabel('warn')).toBe('可以发布，但留个底')
  })

  it('限制词名称优先用户备注，不暴露英文技术名', () => {
    expect(
      formatRuleDisplayName({
        rule_name: 'message-content-url',
        remark: '留言外链检查',
        scene: 'message'
      })
    ).toBe('留言外链检查')
    expect(
      formatRuleTypeName({
        rule_name: 'message-content-url',
        remark: '',
        scene: 'message'
      })
    ).toBe('自定义限制')
  })

  it('不展示「医学合规词库 / add-docs」开发备注，改用类目人话名（不带场景前缀）', () => {
    expect(
      isUserFacingText('医学合规词库 absolute_superlative，见 add-docs/13')
    ).toBe(false)

    expect(
      formatRuleTypeName({
        rule_name: 'message-content-absolute_superlative',
        remark: '医学合规词库 absolute_superlative，见 add-docs/13',
        scene: 'message',
        rule_category: 'absolute_superlative'
      })
    ).toBe('绝对化用语')

    expect(
      formatRuleTypeName({
        rule_name: 'message-content-framework_url',
        remark: '医学合规词库 framework_url，见 add-docs/13',
        scene: 'message',
        rule_category: 'framework_url'
      })
    ).toBe('外链')
  })

  it('可从中文后缀 rule_name 生成可读名', () => {
    expect(
      formatRuleTypeName({
        rule_name: 'message-content-外链',
        remark: '',
        scene: 'message'
      })
    ).toBe('外链')
  })

  it('同类规则跨位置合并为一条，用在「全部位置」', () => {
    const groups = groupContentSafetyRules([
      makeRule({
        id: '1',
        scene: 'message',
        rule_name: 'message-content-absolute_superlative',
        rule_category: 'absolute_superlative'
      }),
      makeRule({
        id: '2',
        scene: 'search_query',
        target_field: 'query',
        rule_name: 'search_query-query-absolute_superlative',
        rule_category: 'absolute_superlative'
      }),
      makeRule({
        id: '3',
        scene: 'room_title',
        target_field: 'title',
        rule_name: 'room_title-title-absolute_superlative',
        rule_category: 'absolute_superlative'
      }),
      makeRule({
        id: '4',
        scene: 'room_description',
        target_field: 'description',
        rule_name: 'room_description-description-absolute_superlative',
        rule_category: 'absolute_superlative'
      }),
      makeRule({
        id: '5',
        scene: 'room_tab',
        rule_name: 'room_tab-content-absolute_superlative',
        rule_category: 'absolute_superlative'
      })
    ])

    expect(groups).toHaveLength(1)
    expect(groups[0].displayName).toBe('绝对化用语')
    expect(groups[0].scenesLabel).toBe('全部位置')
    expect(groups[0].rules).toHaveLength(5)
  })

  it('不同类目不合并；自定义相同词表可合并', () => {
    const groups = groupContentSafetyRules([
      makeRule({
        id: '1',
        rule_category: 'framework_url',
        pattern: 'http'
      }),
      makeRule({
        id: '2',
        rule_category: 'absolute_superlative',
        pattern: '最,第一'
      }),
      makeRule({
        id: '3',
        scene: 'message',
        rule_category: 'platform_custom',
        binding_level: 'platform',
        pattern: '加V,私聊',
        remark: '引流词'
      }),
      makeRule({
        id: '4',
        scene: 'search_query',
        rule_category: 'platform_custom',
        binding_level: 'platform',
        pattern: '私聊,加V',
        remark: '引流词'
      })
    ])

    expect(groups).toHaveLength(3)
    const custom = groups.find((g) => g.displayName === '引流词')
    expect(custom?.rules).toHaveLength(2)
    expect(formatScenesSummary(['message', 'search_query'])).toBe('留言、搜索词')
  })

  it('logContentSafetyAuditDetail 可调用（技术字段仅 logger）', () => {
    expect(() =>
      logContentSafetyAuditDetail({
        id: '1',
        scene: 'message',
        decision: 'block',
        reason_message: '内容违规：命中外链拦截规则',
        matched_rule_names: ['message-content-url'],
        input_excerpt: 'http://a.com',
        created_at: '2026-07-09T00:00:00Z'
      } as any)
    ).not.toThrow()
  })
})
