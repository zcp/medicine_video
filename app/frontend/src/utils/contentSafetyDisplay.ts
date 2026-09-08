/**
 * 内容安全展示辅助（标签格式化 / 场景与决策选项）
 */

import type { AdminContentScene, ContentSafetyRule } from '@/types/contentSafety';

const SCENE_LABELS: Record<string, string> = {
  message: '留言',
  room_title: '直播标题',
  room_description: '直播间简介',
  room_tab: '直播间栏目',
  search_query: '搜索词',
  nickname: '昵称',
};

const ACTION_LABELS: Record<string, string> = {
  block: '拦截',
  warn: '警告',
  allow: '放行',
};

const DECISION_LABELS: Record<string, string> = {
  allow: '放行',
  warn: '警告',
  block: '拦截',
};

const SEVERITY_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重',
};

export function formatSceneLabel(scene?: string | null): string {
  if (!scene) return '—';
  return SCENE_LABELS[scene] || '其他位置';
}

export function formatActionLabel(action?: string | null): string {
  if (!action) return '—';
  return ACTION_LABELS[action] || '按默认处理';
}

export function formatDecisionLabel(decision?: string | null): string {
  if (!decision) return '—';
  return DECISION_LABELS[decision] || '其他结果';
}

export function formatSeverityLabel(severity?: string | null): string {
  if (!severity) return '—';
  return SEVERITY_LABELS[severity] || severity;
}

export function formatBindingLabel(bindingLevel?: string | null): string {
  if (bindingLevel === 'statutory') return '系统自带';
  if (bindingLevel === 'platform') return '可自行改';
  return '—';
}

/** 管理端可维护的全部位置（不含昵称） */
export const ADMIN_SCENE_OPTIONS: { label: string; value: AdminContentScene | '' }[] = [
  { label: '全部位置', value: '' },
  { label: '留言', value: 'message' },
  { label: '直播标题', value: 'room_title' },
  { label: '直播间简介', value: 'room_description' },
  { label: '直播间栏目', value: 'room_tab' },
  { label: '搜索词', value: 'search_query' },
];

/** 表单可用场景（不含"全部位置"） */
export const ADMIN_SCENE_FORM_OPTIONS = ADMIN_SCENE_OPTIONS.filter((o) => o.value !== '');

/** 动作表单选项 */
export const ADMIN_ACTION_FORM_OPTIONS: { label: string; value: ContentSafetyRule['action'] }[] = [
  { label: '拦截', value: 'block' },
  { label: '警告', value: 'warn' },
  { label: '放行', value: 'allow' },
];

/** 日志决策筛选选项 */
export const ADMIN_DECISION_FILTER_OPTIONS: { label: string; value: string }[] = [
  { label: '全部结果', value: '' },
  { label: '拦截', value: 'block' },
  { label: '警告', value: 'warn' },
  { label: '放行', value: 'allow' },
];

/** 场景默认 target_field（新建规则时预填） */
export const SCENE_DEFAULT_TARGET_FIELD: Record<string, string> = {
  message: 'content',
  room_title: 'title',
  room_description: 'description',
  room_tab: 'title',
  search_query: 'query',
  nickname: 'nickname',
};
