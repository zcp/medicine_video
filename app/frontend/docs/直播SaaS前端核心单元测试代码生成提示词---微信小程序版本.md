# 直播SaaS前端核心单元测试代码生成提示词---微信小程序版本

---

## 1. 角色定义 (Role Definition)

你是一名资深前端工程师，精通 Vue3、TypeScript、Pinia，并且是 **uni-app 微信小程序** 开发和测试专家。你擅长为 uni-app 页面编写高质量的单元测试和集成测试，能够精准地模拟 uni-app 的 API 和生命周期。你将为 `frontend_live/src/pages/` 下的核心页面编写 Vitest 测试代码，确保其在微信小程序环境下的稳定性和正确性。

---

## 2. 任务目标 (Task Objective)

你的目标是为以下三个核心页面生成完整、可运行的 **微信小程序端** 集成测试代码：
- `src/pages/room/RoomList.vue` - 房间列表页面
- `src/pages/room/RoomDetail.vue` - 房间详情页面
- `src/pages/live/LiveView.vue` - 直播观看页面

每个测试文件需覆盖页面在小程序环境下的渲染、用户交互（如点击、滑动）、store 集成、API 调用、路由跳转以及 uni-app 生命周期钩子等核心功能。所有测试用例需独立，并 mock 所有外部依赖。

---

## 3. 核心上下文信息 (Core Context Information)

### 3.1. Testing Strategy
- **页面渲染**：测试页面在小程序环境下的正常渲染、加载、错误和空状态。
- **用户交互**：测试按钮点击、表单提交、模态框操作，特别关注小程序特有的交互模式。
- **Store 集成**：测试页面与 Pinia store 的数据同步和状态管理。
- **API 集成**：测试页面触发的 API 调用及响应处理。
- **路由跳转**：使用 `uni.navigateTo` 等 mock 方法测试页面间的导航和参数传递。
- **生命周期**：重点测试 `onLoad`, `onPullDownRefresh`, `onReachBottom` 等 uni-app 钩子。
- **条件编译**：确保测试覆盖到为微信小程序 (`#ifdef MP`) 编写的特定代码逻辑。
- 所有测试用例严格遵循 AAA（Arrange-Act-Assert）模式，确保隔离和独立性。

### 3.2. Testing Environment Setup
- **测试运行器**: Vitest
- **组件挂载**: @vue/test-utils
- **Store 测试**: `createTestingPinia`
- **依赖模拟**: 所有 `uni-app` API (如 `uni.navigateTo`, `uni.showToast`) 和网络请求都必须使用 `vi.fn` 或 `vi.mock` 进行模拟。
- **测试文件位置**: `tests/pages/` 目录下，与被测页面同名，后缀为 `.spec.ts`。

### 3.3. Project Structure (Relevant Files)
```
frontend_live/
├── src/
│   ├── pages/
│   │   ├── room/
│   │   │   ├── RoomList.vue
│   │   │   └── RoomDetail.vue
│   │   ├── live/
│   │   │   └── LiveView.vue
│   ├── store/
│   │   ├── room.ts
│   │   └── session.ts
│   └── api/
│       ├── room.ts
│       └── session.ts
└── tests/
    └── pages/  # 测试文件存放目录
```

### 3.4. 页面功能概览

#### 3.4.1. RoomList.vue (房间列表页)
- **核心功能**: 展示房间列表、分页加载、下拉刷新和上拉加载更多。
- **关键交互**:
    - 与 `useRoomStore` 集成，调用 `fetchRooms`, `addNewRoom`, `updateRoom`, `deleteRoom`。
    - 通过 `ModalDialog` 组件进行房间的创建和编辑，包含表单验证。
    - 响应式布局：在移动端（小程序）通过“更多”按钮触发操作菜单，进行编辑和删除。
    - 通过 `uni.navigateTo` 跳转到房间详情页。
    - 生命周期钩子 `onLoad`, `onPullDownRefresh`, `onReachBottom` 的应用。

#### 3.4.2. RoomDetail.vue (房间详情页)
- **核心功能**: 展示房间详细信息、关联的场次列表和分会场列表（仅主会场）。
- **关键交互**:
    - 与 `useRoomStore` 和 `useSessionStore` 深度集成，获取房间、场次和分会场数据。
    - 场次和分会场的创建、编辑、删除操作，均通过 `ModalDialog` 实现。
    - 场次状态 (`status`) 的正确显示和逻辑判断（如“播放”按钮仅在 `live` 状态时可跳转）。
    - 路由参数处理：通过 `onLoad` 钩子获取房间 `id`。
    - 响应式表格布局，在小程序上展示为卡片式列表。

#### 3.4.3. LiveView.vue (直播观看页)
- **核心功能**: 直播视频播放、房间信息展示和推荐房间列表。
- **关键交互**:
    - 与 `useSessionStore` 和 `useRoomStore` 集成，获取当前场次和推荐房间列表。
    - **平台条件编译**: 包含针对 H5 和小程序环境的不同实现（如 `VideoPlayer` 组件仅在 H5 使用，返回按钮在小程序端隐藏）。测试需关注小程序环境下的渲染结果。
    - 路由参数处理：通过 `onLoad` 钩子获取场次 `id`。
    - 页面布局在小程序端会从左右布局变为上下布局。

---

## 4. Mock 策略和依赖隔离

### 4.1. uni-app API Mock
```typescript
// 统一方案 Part 1：使用 global.uni 提供导航与 UI 能力
const createUniMock = () => ({
  navigateTo: vi.fn(),
  navigateBack: vi.fn(),
  reLaunch: vi.fn(),
  showToast: vi.fn(),
  showModal: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
  stopPullDownRefresh: vi.fn(),
});

beforeEach(() => {
  // @ts-ignore
  global.uni = createUniMock();
});

afterEach(() => {
  vi.clearAllMocks();
});
```

### 4.2. uni-app 生命周期 Mock
```typescript
// 统一方案 Part 2：用 vi.mock('@dcloudio/uni-app') 捕获生命周期注册
const lifecycles = {
  onLoad: [] as Array<(options?: any) => void>,
  onPullDownRefresh: [] as Array<() => void>,
  onReachBottom: [] as Array<() => void>
};

vi.mock('@dcloudio/uni-app', () => ({
  onLoad: (cb: (options?: any) => void) => lifecycles.onLoad.push(cb),
  onPullDownRefresh: (cb: () => void) => lifecycles.onPullDownRefresh.push(cb),
  onReachBottom: (cb: () => void) => lifecycles.onReachBottom.push(cb)
}));

// 测试助手：在用例中手动触发生命周期
export const captureLifecycle = () => ({
  triggerOnLoad: (options?: any) => lifecycles.onLoad.forEach(cb => cb(options)),
  triggerOnPullDown: () => lifecycles.onPullDownRefresh.forEach(cb => cb()),
  triggerOnReachBottom: () => lifecycles.onReachBottom.forEach(cb => cb()),
  reset: () => {
    lifecycles.onLoad.length = 0;
    lifecycles.onPullDownRefresh.length = 0;
    lifecycles.onReachBottom.length = 0;
  }
});
```

---

## 5. 测试用例结构示例

### 5.1. RoomList.vue 测试结构
```typescript
describe('RoomList.vue (WeChat Mini Program)', () => {
  describe('页面渲染与交互', () => {
    it('应正确渲染房间列表');
    it('在移动端（小程序）应显示“更多”操作按钮');
    it('点击“更多”按钮应弹出操作菜单');
    it('从操作菜单中可以触发编辑和删除流程');
  });

  describe('房间操作', () => {
    it('点击悬浮按钮应打开创建房间模态框');
    it('应能成功创建和编辑房间，并刷新列表');
    it('删除有场次的房间时应显示提示');
  });

  describe('生命周期', () => {
    it('onLoad 时应调用 fetchRooms 获取数据');
    it('onPullDownRefresh 时应刷新列表');
    it('onReachBottom 时应加载下一页');
  });
});
```

### 5.2. RoomDetail.vue 测试结构
```typescript
describe('RoomDetail.vue (WeChat Mini Program)', () => {
  describe('数据渲染', () => {
    it('onLoad 时应根据路由参数获取并渲染房间详情');
    it('应正确渲染场次和分会场列表');
    it('在小程序上表格应展示为卡片式布局');
  });

  describe('场次与分会场操作', () => {
    it('应能打开、提交和关闭创建/编辑场次的模态框');
    it('当场次状态不为 live 时，点击“播放”按钮应提示用户');
    it('应能成功删除场次和分会场');
  });
});
```

### 5.3. LiveView.vue 测试结构
```typescript
describe('LiveView.vue (WeChat Mini Program)', () => {
  describe('页面渲染与平台差异', () => {
    it('onLoad 时应根据路由参数获取场次信息');
    it('在小程序环境下不应渲染返回按钮');
    it('在小程序环境下不应渲染 VideoPlayer 组件');
    it('在小程序上应展示为上下垂直布局');
  });

  describe('功能交互', () => {
    it('应正确显示房间简介和模拟评论');
    it('应正确显示推荐房间列表');
    it('点击推荐房间应能跳转到对应的房间详情页');
  });
});
```

---

## 6. 最终交付 (Final Deliverable)

请为以下三个页面文件分别生成完整、可运行的 Vitest 集成测试文件 (`.spec.ts`)，确保所有测试用例都针对 **微信小程序** 环境的特性进行设计和断言。

1.  **`tests/weixin/RoomList.spec.ts`**
2.  **`tests/weixin/RoomDetail.spec.ts`**
3.  **`tests/weixin/LiveView.spec.ts`**

所有测试必须严格遵循 AAA 模式，并 mock 所有外部依赖。

