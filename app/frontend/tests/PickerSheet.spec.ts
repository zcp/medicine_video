// tests/components/PickerSheet.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import { nextTick } from 'vue'
import PickerSheet from '../src/components/common/PickerSheet.vue'

interface MountOptions {
  props?: Record<string, any>
  attrs?: Record<string, any>
}

const mountSheet = (options: MountOptions = {}) => {
  return mount(PickerSheet, {
    props: {
      visible: true,
      title: '选择标签',
      items: [],
      ...options.props,
    },
    attrs: options.attrs,
    global: {
      stubs: {
        ProxyAvatarImage: true,
        ClearButton: true,
        'scroll-view': { template: '<div class="scroll-view-stub"><slot /></div>' },
      },
    },
  })
}

const inputKeyword = async (wrapper: any, kw: string) => {
  await wrapper.find('.ps-input').setValue(kw)
  await nextTick()
}

describe('PickerSheet 默认行为（createable 缺省关闭，零变化）', () => {
  it('无 createable：搜索无匹配只显示空文案，不渲染创建行', async () => {
    const wrapper = mountSheet({
      props: { searchable: true, emptyText: '未找到匹配的标签' },
    })
    await inputKeyword(wrapper, '不存在词')
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.text()).toContain('未找到匹配的标签')
    expect(wrapper.find('.create-row').exists()).toBe(false)
  })

  it('非 searchable 时 createable 不生效（无创建行）', async () => {
    const wrapper = mountSheet({ props: { createable: true } })
    expect(wrapper.find('.search').exists()).toBe(false)
    expect(wrapper.find('.create-row').exists()).toBe(false)
  })
})

describe('createable 显示规则', () => {
  it('搜无任何匹配 → 渲染创建行（关键词入文案），且空文案不重复显示', async () => {
    const wrapper = mountSheet({
      props: { searchable: true, createable: true, emptyText: '暂无标签' },
    })
    await inputKeyword(wrapper, '新标签词')
    expect(wrapper.find('.empty-state').exists()).toBe(false)
    const row = wrapper.find('.create-row')
    expect(row.exists()).toBe(true)
    expect(row.text()).toContain('新标签词')
  })

  it('关键词为空白 → 不渲染创建行', async () => {
    const wrapper = mountSheet({ props: { searchable: true, createable: true } })
    await inputKeyword(wrapper, '   ')
    expect(wrapper.find('.create-row').exists()).toBe(false)
  })

  it('items 含精确同名（忽略首尾空白/大小写）→ 不渲染创建行', async () => {
    const wrapper = mountSheet({
      props: {
        searchable: true,
        createable: true,
        items: [{ id: 'a', name: ' 手术直播 ' }],
      },
    })
    await inputKeyword(wrapper, '手术直播')
    expect(wrapper.find('.create-row').exists()).toBe(false)
    expect(wrapper.findAll('.list-item')).toHaveLength(1)
  })

  it('仅模糊匹配（无精确同名）→ 列表项与创建行并存', async () => {
    const wrapper = mountSheet({
      props: {
        searchable: true,
        createable: true,
        items: [{ id: 'a', name: '手术直播回放' }],
      },
    })
    await inputKeyword(wrapper, '手术')
    expect(wrapper.findAll('.list-item')).toHaveLength(1)
    expect(wrapper.find('.create-row').exists()).toBe(true)
  })

  it('英文大小写差异视为同名 → 不渲染创建行', async () => {
    const wrapper = mountSheet({
      props: {
        searchable: true,
        createable: true,
        items: [{ id: 'a', name: 'ICU' }],
      },
    })
    await inputKeyword(wrapper, 'icu')
    expect(wrapper.find('.create-row').exists()).toBe(false)
  })
})

describe('create 事件与 createPending', () => {
  it('点击创建行 → emit("create", trim 后关键词)；关键词保留不回填清空', async () => {
    const wrapper = mountSheet({ props: { searchable: true, createable: true } })
    await inputKeyword(wrapper, '  新词  ')
    await wrapper.find('.create-row').trigger('click')
    const emitted = wrapper.emitted('create')
    expect(emitted).toBeTruthy()
    expect(emitted![0]).toEqual(['新词'])
    const inputEl = wrapper.find('.ps-input').element as HTMLInputElement
    expect(inputEl.value).toBe('  新词  ')
  })

  it('createPending=true → 显示"创建中..."且点击不再 emit', async () => {
    const wrapper = mountSheet({
      props: { searchable: true, createable: true, createPending: true },
    })
    await inputKeyword(wrapper, '新词')
    expect(wrapper.find('.create-row').text()).toContain('创建中')
    await wrapper.find('.create-row').trigger('click')
    expect(wrapper.emitted('create')).toBeUndefined()
  })

  it('空白关键词点击创建行不 emit', async () => {
    const wrapper = mountSheet({ props: { searchable: true, createable: true } })
    const row = wrapper.find('.create-row')
    expect(row.exists()).toBe(false)
  })
})

describe('multiple 模式回归（createable 不影响 toggle 与满员）', () => {
  it('toggle 正常：勾选未选项照常 emit update:selectedIds', async () => {
    const wrapper = mountSheet({
      props: {
        mode: 'multiple',
        searchable: true,
        createable: true,
        max: 2,
        selectedIds: ['a'],
        items: [
          { id: 'a', name: '手术直播' },
          { id: 'b', name: '病例讨论' },
        ],
      },
    })
    await wrapper.findAll('.list-item')[1].trigger('click')
    const emitted = wrapper.emitted('update:selectedIds')
    expect(emitted).toBeTruthy()
    expect(emitted![0]).toEqual([['a', 'b']])
  })

  it('满员时未选项置灰不可点（行为不变）', async () => {
    const wrapper = mountSheet({
      props: {
        mode: 'multiple',
        max: 2,
        selectedIds: ['a', 'b'],
        items: [
          { id: 'a', name: '手术直播' },
          { id: 'b', name: '病例讨论' },
          { id: 'c', name: '医学前沿' },
        ],
      },
    })
    const third = wrapper.findAll('.list-item')[2]
    expect(third.classes()).toContain('is-disabled')
    await third.trigger('click')
    expect(wrapper.emitted('update:selectedIds')).toBeUndefined()
  })
})
