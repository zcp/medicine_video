import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  buildInviteText,
  parseInviteText,
  INVITE_BASE_URL,
} from '@/utils/clipboardShare';

const SAMPLE_ROOM_ID = '550e8400-e29b-41d4-a716-446655440000';

function setClipboardData(data: string) {
  (globalThis as any).uni.getClipboardData = vi.fn((opts: any) => {
    opts?.success?.({ data });
  });
}

function setClipboardDataFail() {
  (globalThis as any).uni.getClipboardData = vi.fn((opts: any) => {
    opts?.fail?.({ errMsg: 'getClipboardData:fail' });
  });
}

// 有状态函数（会话级 Set）需 fresh 模块实例，避免测试间共享状态
async function loadFresh() {
  vi.resetModules();
  return await import('@/utils/clipboardShare');
}

beforeEach(() => {
  vi.resetModules();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('buildInviteText', () => {
  it('生成含基础地址、roomId 与使用指引的邀请文本', () => {
    const text = buildInviteText(SAMPLE_ROOM_ID);
    expect(text).toContain(INVITE_BASE_URL);
    expect(text).toContain(SAMPLE_ROOM_ID);
    expect(text).toContain('私密直播间邀请');
    expect(text).toContain('请复制链接直接打开App观看');
  });
});

describe('parseInviteText', () => {
  it('从完整邀请文本解析出 roomId', () => {
    const text = buildInviteText(SAMPLE_ROOM_ID);
    expect(parseInviteText(text)).toBe(SAMPLE_ROOM_ID);
  });

  it('从混合文本中解析出 roomId', () => {
    const text = `收到：${buildInviteText(SAMPLE_ROOM_ID)}，请查收`;
    expect(parseInviteText(text)).toBe(SAMPLE_ROOM_ID);
  });

  it('非邀请文本返回 null', () => {
    expect(parseInviteText('今天天气不错')).toBeNull();
    expect(parseInviteText('https://example.com/live/room/123')).toBeNull();
    expect(parseInviteText('')).toBeNull();
  });

  it('无效 UUID 不匹配', () => {
    expect(parseInviteText(`https://mp.dayilive.com/live/room/not-a-uuid`)).toBeNull();
  });
});

describe('markHandled / shouldPrompt（会话级）', () => {
  it('初始应提示', async () => {
    const mod = await loadFresh();
    expect(mod.shouldPrompt(SAMPLE_ROOM_ID)).toBe(true);
  });

  it('标记后本会话不提示', async () => {
    const mod = await loadFresh();
    mod.markHandled(SAMPLE_ROOM_ID);
    expect(mod.shouldPrompt(SAMPLE_ROOM_ID)).toBe(false);
  });

  it('新会话（模块重置模拟杀 App 重开）后恢复提示', async () => {
    const mod = await loadFresh();
    mod.markHandled(SAMPLE_ROOM_ID);
    expect(mod.shouldPrompt(SAMPLE_ROOM_ID)).toBe(false);
    const fresh = await loadFresh();
    expect(fresh.shouldPrompt(SAMPLE_ROOM_ID)).toBe(true);
  });
});

describe('checkClipboardForInvite', () => {
  it('剪贴板命中邀请文本 → 返回 roomId 并标记本会话', async () => {
    setClipboardData(buildInviteText(SAMPLE_ROOM_ID));
    const mod = await loadFresh();
    const roomId = await mod.checkClipboardForInvite();
    expect(roomId).toBe(SAMPLE_ROOM_ID);
    // 本会话已标记 → 再次调用返回 null（取消/进入后不重复弹）
    expect(await mod.checkClipboardForInvite()).toBeNull();
  });

  it('新会话（杀 App 重开）后同一链接可再次提示', async () => {
    setClipboardData(buildInviteText(SAMPLE_ROOM_ID));
    const mod = await loadFresh();
    expect(await mod.checkClipboardForInvite()).toBe(SAMPLE_ROOM_ID);
    expect(await mod.checkClipboardForInvite()).toBeNull();
    const fresh = await loadFresh();
    expect(await fresh.checkClipboardForInvite()).toBe(SAMPLE_ROOM_ID);
  });

  it('剪贴板无邀请 → 返回 null', async () => {
    setClipboardData('普通文本内容');
    const mod = await loadFresh();
    expect(await mod.checkClipboardForInvite()).toBeNull();
  });

  it('读剪贴板失败 → 静默返回 null', async () => {
    setClipboardDataFail();
    const mod = await loadFresh();
    expect(await mod.checkClipboardForInvite()).toBeNull();
  });
});
