# 直播SaaS前端测试代码生成提示词（AAA模式 & 独立隔离）

> 本文档适用于 frontend_live/src/ 现有代码结构，指导自动化生成高质量前端测试代码。所有测试均需遵循 AAA（Arrange-Act-Assert）模式，保证每个测试用例独立、隔离，便于维护和持续集成。

---

## 1. 测试组织结构建议

- 所有测试文件应与被测模块同名，存放于 `tests/` 目录或同级 `__tests__` 目录下。
- 组件测试：`src/components/ComponentName.spec.ts`
- 页面测试：`src/pages/xxx/PageName.spec.ts`
- 工具函数测试：`src/utils/xxx.spec.ts`
- 状态管理测试：`src/store/xxx.spec.ts`

---

## 2. 测试代码生成提示词（通用模板）

### 基本要求
- 每个测试用例必须严格遵循 AAA（Arrange-Act-Assert）三段式结构：
  1. **Arrange**：准备测试数据、mock依赖、初始化组件/状态
  2. **Act**：执行被测操作（如方法调用、事件触发、API请求）
  3. **Assert**：断言输出、状态、UI、回调等结果
- 每个测试用例必须**独立**，不能依赖其它测试的副作用。
- 所有 mock、全局变量、定时器等必须在每个测试后清理，保证隔离。

### 代码生成提示词示例

```
请为【src/components/RoomCard.vue】生成单元测试代码，要求：
- 使用 Vitest + @vue/test-utils + TypeScript
- 每个测试用例严格遵循 AAA（Arrange-Act-Assert）模式
- 每个测试用例独立、互不依赖，mock 依赖和副作用需在 afterEach/teardown 清理
- 覆盖以下场景：
  1. 正常渲染 props 数据
  2. 点击事件能正确触发
  3. slot 内容渲染
- 断言需明确，避免模糊判断
- 代码风格与 src/ 现有项目一致
- 输出完整 .spec.ts 文件内容
```

---

## 3. 命名规范与隔离性原则

- 测试文件名：`xxx.spec.ts`，与被测文件同名
- describe/it/测试用例命名需清晰表达行为和预期
- 每个测试用例前后需清理副作用（如 mock、定时器、全局变量）
- 不允许在多个测试间共享状态

---

## 4. Mock/依赖隔离建议

- 对 API、store、全局方法、外部依赖等全部使用 mock
- 使用 Vitest 的 `vi.mock`、`vi.fn`、`beforeEach/afterEach` 实现依赖隔离
- 不允许真实网络请求、真实全局状态污染

---

## 5. 典型用例模板（AAA模式）

```ts
import { mount } from '@vue/test-utils'
import RoomCard from '@/components/RoomCard.vue'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('RoomCard.vue', () => {
  let wrapper: any
  const mockClick = vi.fn()

  beforeEach(() => {
    // Arrange: 初始化组件和依赖
    wrapper = mount(RoomCard, {
      props: { title: '测试房间', clickable: true },
      slots: { default: '<div>slot内容</div>' },
      attrs: { onClick: mockClick }
    })
  })

  afterEach(() => {
    // 清理副作用，保证隔离
    wrapper.unmount()
    vi.clearAllMocks()
  })

  it('正常渲染 props', () => {
    // Act: 无需操作
    // Assert: 检查渲染内容
    expect(wrapper.text()).toContain('测试房间')
  })

  it('点击事件触发', async () => {
    // Act
    await wrapper.trigger('click')
    // Assert
    expect(mockClick).toHaveBeenCalled()
  })

  it('slot 内容渲染', () => {
    // Assert
    expect(wrapper.html()).toContain('slot内容')
  })
})
```

---

## 6. 断言规范
- 断言需具体、可复现，如 `toBe`, `toEqual`, `toContain`, `toHaveBeenCalled` 等
- 避免使用 `toBeTruthy`、`toBeFalsy` 等模糊断言

---

## 7. 覆盖范围建议
- 组件/页面的 props、事件、UI渲染、交互、边界条件、异常分支
- 工具函数的输入输出、异常、边界
- store 的状态变更、action、getter
- API 封装的参数、返回、异常

---

## 8. 端到端测试（E2E）建议
- 使用 Cypress 或 uni-app 官方测试工具
- 每个 E2E 测试用例独立，前后清理测试数据
- 场景覆盖：页面跳转、表单交互、接口联调、权限校验等

---

## 9. 参考
- Vitest 官方文档：https://vitest.dev/
- @vue/test-utils：https://test-utils.vuejs.org/
- Cypress：https://www.cypress.io/
- uni-app 官方测试文档：https://uniapp.dcloud.net.cn/tutorial/unit-test.html

---

> 本文档可直接作为代码生成提示词模板，适用于所有 frontend_live/src/ 目录下的前端测试代码自动化生成场景。