# 直播SaaS前端阶段二：组件层代码生成提示词

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通Vue3组件化开发、UI/UX设计和无障碍规范。你的任务是根据设计文档，创建一套高质量、可复用、风格统一的UI组件库。

---

## 2. 任务目标（Task Objective）
本次任务为直播SaaS平台前端项目的**阶段二：组件层**。目标是构建通用基础组件和业务领域组件。

**生成组件清单：**

### 通用基础组件（7个）
- `src/components/common/AppButton.vue`
- `src/components/common/LoadingIndicator.vue`
- `src/components/common/ErrorBanner.vue`
- `src/components/common/ModalDialog.vue`
- `src/components/common/LiveCard.vue`
- `src/components/common/ExpertCard.vue`
- `src/components/common/ArticleCard.vue`

### 业务组件（31个，按模块分组）
- **认证模块(2)**: LoginForm, ThirdPartyLogin
- **首页模块(6)**: TopBar, CategoryTabs, FollowingUpdates, Banner3D, FeedList, QuickMenu
- **房间模块(3)**: RoomHeader, SessionTabs, ExpertMiniCard
- **科室模块(2)**: DepartmentCategoryNav, DepartmentContentList
- **专家模块(3)**: SearchBar, SpecialtyFilter, ExpertList
- **我的直播模块(4)**: QuickActions, LiveStatusCard, SessionHistory, HostApplyGuide
- **个人中心模块(4)**: UserCard, QuickAccess, FunctionList, LogoutButton
- **设置模块(4)**: GeneralSettings, AccountSecurity, PrivacySettings, InfoAndActions
- **其他(3)**: DataUsageAlert, SkeletonScreen, EmptyState

---

## 3. 核心约束（Core Constraints）

### 3.1 哑组件原则
- **无状态**：不维护复杂业务状态
- **纯展示**：通过props接收数据，通过emits发出事件
- **不调用API**：严禁直接调用API或访问Store
- **可复用**：通用性强，可在多场景使用

### 3.2 质量标准
- **TypeScript强类型**：所有props、emits必须有类型定义
- **JSDoc注释**：组件必须有完整注释
- **无障碍支持**：必须添加ARIA属性
- **样式变量**：必须使用`uni.scss`中的CSS变量
- **主题支持**：必须支持日间/夜间模式

### 3.3 性能要求
- 图片懒加载
- 长列表虚拟滚动
- 搜索防抖/节流
- 避免不必要的重渲染

---

## 4. 组件API设计规范

每个组件必须包含：

```typescript
// 1. Props定义
interface Props {
  // 必填props
  data: DataType
  // 可选props with默认值
  size?: 'large' | 'medium' | 'small'
}

// 2. Emits定义
const emit = defineEmits<{
  click: []
  change: [value: string]
}>()

// 3. Slots定义（如有）
// - default: 默认内容
// - header: 头部内容
// - footer: 底部内容
```

---

## 5. 通用基础组件规范

### 5.1 AppButton.vue
**Props**: type, size, loading, disabled, block, round, icon  
**Emits**: click  
**样式**: 6种type（primary/success/warning/danger/info/default），4种size

### 5.2 LoadingIndicator.vue
**Props**: type(spinner/dots/bar), size, text, overlay  
**样式**: 3种加载动画，支持全屏遮罩

### 5.3 ErrorBanner.vue
**Props**: type(error/warning/success/info), message, description, closable, duration  
**Emits**: close  
**交互**: 支持手动/自动关闭，滑动关闭手势

### 5.4 ModalDialog.vue
**Props**: visible, title, width, confirmText, cancelText, confirmLoading, closeOnClickModal  
**Emits**: update:visible, confirm, cancel, close  
**Slots**: default, footer  
**交互**: 支持ESC键关闭，防止背景滚动穿透

### 5.5 LiveCard.vue
**Props**: session, layout(vertical/horizontal), showDescription, showStats  
**Emits**: click, clickExpert  
**样式**: 16:9封面，直播中红色LIVE标签（呼吸灯）

### 5.6 ExpertCard.vue
**Props**: expert, layout, showFollow  
**Emits**: click, follow, unfollow  
**样式**: 圆形头像，显示职称/医院/专业

### 5.7 ArticleCard.vue
**Props**: article, showAuthor, showReadCount  
**Emits**: click  
**样式**: 卡片式布局，支持封面图

---

## 6. 业务组件规范（按模块）

### 6.1 认证模块
**LoginForm**: 支持手机号/密码两种登录方式，验证码倒计时，实时校验  
**ThirdPartyLogin**: 图标式布局，支持微信/支付宝登录

### 6.2 首页模块
**TopBar**: 固定顶部44px，Logo+搜索+消息  
**CategoryTabs**: 横向滚动，支持星标固定，长按操作  
**FollowingUpdates**: 横向滚动专家头像，直播中红色边框  
**Banner3D**: 3D透视效果轮播，自动播放  
**FeedList**: 支持单列/双列切换，虚拟滚动，懒加载  
**QuickMenu**: 长按Tab唤起，从底部滑入

### 6.3 房间模块
**RoomHeader**: 全屏宽封面，渐变遮罩叠加信息  
**SessionTabs**: 预告/历史Tab切换  
**ExpertMiniCard**: 横向布局，80px高度迷你卡片

### 6.4 科室模块
**DepartmentCategoryNav**: 横向滚动导航，选中居中  
**DepartmentContentList**: 混合渲染LiveCard/ExpertCard/ArticleCard

### 6.5 专家模块
**SearchBar**: 防抖500ms，清除按钮  
**SpecialtyFilter**: 专业领域筛选器  
**ExpertList**: 支持A-Z索引，快速跳转

### 6.6 我的直播模块
**QuickActions**: 2x2网格布局快捷按钮  
**LiveStatusCard**: 显示直播状态，实时数据/倒计时  
**SessionHistory**: 历史场次列表，支持编辑/删除  
**HostApplyGuide**: 非主播用户引导卡片

### 6.7 个人中心模块
**UserCard**: 渐变背景用户卡片，未登录显示登录按钮  
**QuickAccess**: 4个快捷功能入口（历史/收藏/订单/优惠）  
**FunctionList**: 设置/帮助/关于等功能列表  
**LogoutButton**: 退出登录确认按钮

### 6.8 设置模块
**GeneralSettings**: 日夜模式/字体/流量提醒等通用设置  
**AccountSecurity**: 密码/手机/邮箱等账号安全设置  
**PrivacySettings**: 授权管理/黑名单等隐私设置  
**InfoAndActions**: 版本信息/清理缓存/用户协议等

---

## 7. 组件样式规范

### 7.1 CSS变量使用
所有颜色、字体、间距必须使用变量：
```scss
// 颜色
color: var(--color-text-primary);
background: var(--color-primary);

// 字体
font-size: var(--font-size-base);

// 间距
padding: var(--spacing-md);

// 圆角
border-radius: var(--border-radius-base);
```

### 7.2 BEM命名规范
```scss
.component-name {
  &__element {
    // 元素样式
  }
  &--modifier {
    // 修饰符样式
  }
  &.is-active {
    // 状态样式
  }
}
```

### 7.3 响应式设计
```scss
// 小屏幕 (<768px)
@media (max-width: 767px) {
  .component { font-size: 14px; }
}

// 中屏幕 (768px-1024px)
@media (min-width: 768px) and (max-width: 1024px) {
  .component { font-size: 16px; }
}

// 大屏幕 (>1024px)
@media (min-width: 1025px) {
  .component { font-size: 18px; }
}
```

---

## 8. 无障碍支持

所有交互组件必须添加：
- **role**: 明确组件角色（button/dialog/tab等）
- **aria-label**: 描述组件用途
- **aria-disabled**: 禁用状态
- **tabindex**: 键盘导航顺序
- **@keydown**: 键盘事件处理（Enter/Space/ESC）

示例：
```vue
<button
  role="button"
  :aria-label="buttonLabel"
  :aria-disabled="disabled"
  :tabindex="disabled ? -1 : 0"
  @keydown.enter="handleClick"
  @keydown.space.prevent="handleClick"
>
  {{ text }}
</button>
```

---

## 9. 性能优化

### 9.1 图片懒加载
```vue
<image
  :src="imageUrl"
  lazy-load
  mode="aspectFill"
  @error="handleImageError"
/>
```

### 9.2 长列表虚拟滚动
使用uni-app的`recycle-view`或第三方虚拟滚动组件

### 9.3 防抖节流
```typescript
import { debounce } from 'lodash-es'

const handleSearch = debounce((keyword: string) => {
  // 搜索逻辑
}, 500)
```

### 9.4 计算属性优化
```typescript
// ❌ 每次都重新计算
const filteredList = () => list.filter(...)

// ✅ 使用computed缓存
const filteredList = computed(() => list.value.filter(...))
```

---

## 10. 测试要求

每个组件必须包含：
- **Props测试**: 验证所有props的默认值和类型
- **Emits测试**: 验证所有事件是否正确触发
- **Slots测试**: 验证插槽内容是否正确渲染
- **交互测试**: 验证点击、输入等交互是否正常
- **无障碍测试**: 验证ARIA属性是否正确

---

## 11. 最终交付

### 11.1 输出格式
- 每个组件一个独立的`.vue`文件
- 文件路径必须标注清楚
- 代码必须完整，可直接运行

### 11.2 自我验证清单
- [ ] 所有组件是否都已生成？
- [ ] Props/Emits是否有完整的TypeScript类型定义？
- [ ] 是否使用了CSS变量？
- [ ] 是否添加了ARIA属性？
- [ ] 是否有JSDoc注释？
- [ ] 样式是否使用了scoped？

### 11.3 完成断言
```
[阶段二完成断言 - PHASE TWO COMPLETION ASSERTION]
✓ 通用基础组件：7个，已生成
✓ 业务领域组件：31个，已生成
✓ 哑组件原则：已遵循
✓ TypeScript类型：100%覆盖
✓ 无障碍支持：已添加ARIA属性
✓ 样式变量：已使用uni.scss变量
✓ 性能优化：已实现懒加载/虚拟滚动/防抖
✓ 零偏差原则：已遵循

[重要提示]
- 本阶段组件为纯展示组件，不包含业务逻辑
- 组件通过uni-app的easycom机制自动引入
- 页面组件将在阶段三中使用这些组件进行组装
```

---

**[开始生成指令]**
请严格按照本文档要求，从通用基础组件开始，逐个生成所有组件代码。每个组件必须包含完整的Props/Emits定义、样式和交互逻辑。
