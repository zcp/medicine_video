# 直播SaaS前端端到端(E2E)测试代码生成提示词——第三批次

---

## 1. 角色定义 (Role Definition)
你是一名资深前端工程师与测试工程师，精通 Vue3、TypeScript、Pinia、uni-app 与浏览器自动化测试。你将为 frontend_live 的典型业务流程编写高质量、可维护的端到端测试代码。E2E 使用 Playwright + TypeScript，覆盖真实渲染、真实路由与交互，并通过网络拦截进行可控的后端模拟，严格遵循 AAA（Arrange-Act-Assert）。

---

## 2. 目标与范围 (Objectives & Scope)
- 覆盖 H5 端核心用户旅程（RoomList -> RoomDetail -> LiveView 等）：
  - 流程A：创建房间 -> 列表刷新 -> 进入详情 -> 创建场次 -> 前往播放页
  - 流程B：删除房间的安全限制（有场次时禁止；清空场次后允许）
  - 流程C：分会场（主会场-分会场）列表与 CRUD 的关键路径
  - 流程D：分页/下拉刷新/上拉加载更多（滚动触发）
  - 流程E：XSS 防护（v-html 与 escapeHtml 的输出安全性验证）
- 权限、异常、边界：401/403/404、超时、网络失败、空数据、表单校验、无变更保存等
- 非目标：后端系统的真连通性；多端（小程序）自动化；音视频内核本身

---

## 3. 测试栈与运行方式 (Stack & Runner)
- Runner：Playwright Test + TypeScript
- 浏览器：Chromium（默认）
- 环境：使用“dev:h5”或“vite preview/uni h5”作为被测站点，Playwright baseURL 指向本地服务
- 网络：使用 Playwright route 拦截与 fulfill 返回模拟接口
- 文件组织：tests/e2e/**.spec.ts，按流程/页面拆分

安装建议（文档指引，不在本提示词中自动执行）：
- npm i -D @playwright/test
- npx playwright install
- 在 package.json 添加：
  - "e2e": "playwright test"
  - "e2e:ui": "playwright test --ui"
  - "e2e:headed": "playwright test --headed"

playwright.config.ts 关键建议：
- use.baseURL: http://localhost:PORT （dev:h5 启动的端口）
- use.viewport: { width: 1440, height: 900 }
- timeout: 30_000，expect: { timeout: 5_000 }
- fullyParallel: true，retries: 1

---

## 4. 关键上下文 (来自第一批次要求的延伸)
- 所有用例仍需遵循 AAA，且每个测试相互独立、隔离
- 真实 UI 交互：点击、输入、滚动、等待网络
- 所有对后端的请求统一用拦截与 mock，避免真实请求与不可控波动
- 统一断言：使用 toHaveURL、toBeVisible、toHaveText、toHaveValue、toHaveCount、toHaveBeenCalledTimes 等具体断言
- 清理：每个用例结束需恢复路由与网络拦截、清除 localStorage/cookies（如设置了 csrftoken）

---

## 5. 被测页面与业务流 (Pages & Flows)
- RoomList.vue
  - 功能：房间列表、创建/编辑/删除、跳转详情、分页/下拉刷新/上拉加载
- RoomDetail.vue
  - 功能：房间详情、场次列表 CRUD、主会场/分会场、跳转播放
- LiveView.vue
  - 功能：播放（H5 下 iframe，App 下 VideoPlayer 组件）、推荐房间、返回导航
- NotFound.vue
  - 功能：404 页返回首页

---

## 6. 网络拦截与数据工厂 (Network & Factories)
- 统一用 page.route 拦截 API：
  - GET /rooms, POST /rooms, PUT/PATCH /rooms/:id, DELETE /rooms/:id
  - GET /rooms/:id, GET /rooms/:id/sessions, POST /rooms/:id/sessions
  - GET /sessions/:id, PATCH /sessions/:id, DELETE /sessions/:id
- 根据页面真实逻辑设置 code/message/data 统一响应结构或直返业务数据（两种都需要兼容）
- 使用简易数据工厂：makeRoom(), makeSession()，以及集合工厂 makeRooms(n)
- 权限/异常模拟：
  - 401 -> 提示“登录已过期”类文案，阻断后续
  - 403 -> 提示“没有权限”类文案
  - 404 -> 资源不存在
  - 超时/网络失败 -> Toast“网络请求失败”

---

## 7. 选择器与可用性 (Selectors)
- 优先使用可读性强的选择器：
  - getByRole('button', { name: '创建新房间' })
  - getByText('直播房间列表')
  - data-testid（如可在按钮/关键元素上添加）
- 回退：CSS 类选择器（如 .room-item, .table-row, .actions-cell）
- 对 v-html 输出的内容使用 getByText 或 locator('.selector').innerHTML() 断言不含危险标签/脚本

---

## 8. 通用前置与清理 (Hooks)
- beforeEach:
  - 清空 storage/cookies；设置 csrftoken（如 request.ts 会读取）
  - 启用默认网络拦截（/rooms 列表返回空或样本数据）
- afterEach:
  - 清理路由拦截 routes.reset()
  - page.close()

---

## 9. 典型用例设计 (Scenarios)

### 9.1 流程A：创建房间 -> 列表刷新 -> 详情 -> 创建场次 -> 播放
- Arrange：
  - 拦截 GET /rooms 初始为空；POST /rooms 返回新房间；GET /rooms（刷新）返回包含新房间
  - 拦截 GET /rooms/:id 返回房间详情；GET /rooms/:id/sessions 初始空；POST /rooms/:id/sessions 返回新场次
  - GET /sessions/:id 返回场次详情用于 LiveView
- Act：
  - 打开 RoomList -> 点击“+” -> 填写标题/简介 -> 确认
  - 列表刷新出现新房间 -> 点击房间进入详情
  - 点击“创建新场次” -> 填写并提交 -> 点击“播放”
- Assert：
  - 列表出现新房间项；URL 切到 /pages/room/RoomDetail?id=xxx
  - 详情页表格出现新场次；跳转到 /pages/live/LiveView?id=xxx
  - LiveView 中根据平台渲染 iframe（H5）或 VideoPlayer（非H5）

### 9.2 流程B：删除限制（有场次禁止）
- Arrange：
  - GET /rooms/:id/sessions 返回 total > 0
  - DELETE /rooms/:id 不会被调用（因为前置禁止）
- Act：RoomList 点击“删除”
- Assert：弹出“无法删除”模态；没有 DELETE 请求；提示正确

### 9.3 流程C：分会场
- Arrange：
  - GET /rooms/:id 返回主会场；GET /rooms/:id/sub-venues 返回若干分会场
- Act：
  - 进入详情 -> 分会场表格渲染 -> 点击分会场“查看详情”
- Assert：跳转到 /pages/room/RoomDetail?id=subVenueId，且不加载子分会场列表

### 9.4 流程D：分页/下拉/上拉
- Arrange：
  - GET /rooms?page=1 返回 size 条；page=2 返回 size 条；page=3 返回不足 size（hasMore=false）
- Act：
  - 打开列表；滚动至底部两次；或触发 onReachBottom 多次
- Assert：
  - 累加渲染条目；第三次不再请求
  - 下拉刷新后重置到第一页数据

### 9.5 流程E：XSS 安全
- Arrange：
  - GET /rooms 返回包含恶意字符串标题/简介，如 `<img src=x onerror=alert(1)>`、`<script>...</script>`
- Act：进入列表与详情
- Assert：
  - 页面文本显示被转义/清洗后的安全内容；DOM 中不出现 <script>、onerror 等危险属性

### 9.6 权限/异常
- 401：任意接口返回 401 -> 断言弹 Toast，页面停留原地
- 403：接口返回 403 -> 断言 Toast，禁止操作
- 404：详情接口 404 -> 断言错误提示与空内容
- 超时/网络失败：显示“网络请求失败”提示

---

## 10. 代码骨架与示例 (Skeletons & Samples)

测试目录结构建议：
```
frontend_live/
└── tests/
    └── e2e/
        ├── flows.create-room-to-play.spec.ts
        ├── flows.delete-guard.spec.ts
        ├── flows.sub-venues.spec.ts
        ├── flows.pagination-refresh.spec.ts
        ├── flows.security-xss.spec.ts
        └── helpers/
            ├── server.ts       # 统一路由拦截与数据工厂
            └── selectors.ts    # 选择器/role 封装
```

路由拦截（片段示例）：
```ts
// server.ts
import { Page, Route } from '@playwright/test'

export async function mockRoomsList(page: Page, pages: Array<any[]>) {
  let idx = 0
  await page.route('**/rooms**', async (route: Route) => {
    const url = new URL(route.request().url())
    const p = Number(url.searchParams.get('page') || '1')
    const size = Number(url.searchParams.get('size') || '10')
    const list = pages[Math.min(p - 1, pages.length - 1)] ?? []
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, data: { items: list, total: 25, page: p, size } })
    })
  })
}
```

场景示例（创建到播放，片段）：
```ts
import { test, expect } from '@playwright/test'
import { mockRoomsList } from './helpers/server'

test('创建房间->详情->创建场次->播放', async ({ page, context }) => {
  await context.addCookies([{ name: 'csrftoken', value: 'csrf', url: 'http://localhost' }])
  await mockRoomsList(page, [[]])

  await page.goto('/')
  await page.getByRole('button', { name: '+' }).click()
  await page.fill('input[placeholder="请输入房间标题"]', '新房间')
  await page.getByRole('button', { name: '立即创建' }).click()

  // ...后续断言：列表更新、进入详情、创建场次、进入播放
})
```

---

## 11. 断言规范与稳定性 (Assertions & Stability)
- 断言具体、可复现，不使用模糊断言
- 对网络/动画/加载使用 page.waitForResponse、locator.waitFor()、toBeVisible 等
- 避免依赖视觉像素；多用文本、aria role、data-testid
- 对时间相关交互 prefer useFakeTimers 仅用于单元/集成；E2E 中尽量真实等待网络/DOM 状态

---

## 12. 运行方式 (How to Run)
- 启动被测站点（任选其一）：
  - npm run dev:h5（uni h5 开发服务，记录端口）
  - 或构建并预览：vite/uni h5 preview
- 运行 E2E：
  - npm run e2e
  - npm run e2e:ui（可视化）
  - npm run e2e -- tests/e2e/flows.create-room-to-play.spec.ts

---

## 13. 交付 (Deliverables)
- 完整的 Playwright 配置与命令
- tests/e2e/** 覆盖本提示词中所有场景的测试代码
- helpers/server.ts（网络拦截与数据工厂）、helpers/selectors.ts（选择器封装）
- 文档：如何启动、如何切换平台分支（process.env.UNI_PLATFORM = 'h5'）、如何扩展新场景

---

## 14. 注意事项 (Notes)
- 不进行真实后端调用；全部通过拦截与可控数据驱动
- H5 播放页 LiveView：H5 下使用 iframe，非 H5 使用 VideoPlayer；测试中按 H5 为主（也可新增一条用例设置非 H5 分支）
- 若页面缺少稳定选择器，建议在组件中补充 data-testid，不改变用户 UI

---

本提示词面向第三批次 E2E 测试代码生成，配合第一/第二批次单元/集成测试共同保障质量。
