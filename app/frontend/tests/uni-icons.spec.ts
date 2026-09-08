// 阶段0工具链验证：uni-icons 组件可被 vitest 正确加载并渲染
// 验证点：vite.config.ts 中 deps.inline 对 @dcloudio/uni-ui 的转换是否生效
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import UniIcons from '../node_modules/@dcloudio/uni-ui/lib/uni-icons/uni-icons.vue';

describe('uni-icons（工具链验证）', () => {
  it('渲染指定 type 的图标类名与字符', () => {
    const wrapper = mount(UniIcons, {
      props: { type: 'notification', size: 24, color: '#ff0000' },
    });
    // 注：vitest 不剥离 uni 条件编译，模板会同时渲染 NVUE 分支与普通分支的 text
    const texts = wrapper.findAll('text');
    expect(texts.length).toBeGreaterThanOrEqual(2);
    const iconEl = texts.find((t) => t.classes().includes('uniui-notification'));
    expect(iconEl).toBeTruthy();
    expect(iconEl!.classes()).toContain('uni-icons');
    expect(iconEl!.attributes('style')).toContain('font-size: 24px');
    expect(iconEl!.attributes('style')).toContain('color: #ff0000');
    // 字符数据由 unicode computed 提供（NVUE 分支渲染该字符）
    expect((wrapper.vm as any).unicode).not.toBe('');
  });

  it('支持阶段2计划使用的关键图标 type', () => {
    const types = [
      'notification',
      'locked',
      'folder-add',
      'mail-open',
      'calendar',
      'videocam',
      'gear',
      'person',
      'trash',
      'search',
      'eye',
      'images',
      'sound',
      'chatbubble',
      'phone',
      'list',
      'refresh',
      'settings',
      'weixin',
    ];
    for (const type of types) {
      const wrapper = mount(UniIcons, { props: { type } });
      expect(wrapper.find('text').text(), `type=${type} 应渲染出字符`).not.toBe('');
    }
  });

  it('未知 type 渲染为空字符（不抛错）', () => {
    const wrapper = mount(UniIcons, { props: { type: 'globe-not-exist' } });
    expect(wrapper.find('text').text()).toBe('');
  });
});
