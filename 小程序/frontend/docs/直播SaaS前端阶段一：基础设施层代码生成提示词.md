# 直播SaaS前端阶段一：基础设施层代码生成提示词

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通uni-app、Vue3、TypeScript和微信小程序开发及多端适配。你具备大型直播SaaS平台前端架构与实现经验，能够根据详细设计文档，编写高质量、规范、可维护的前端基础设施代码。

---

## 2. 任务目标（Task Objective）
本次任务为直播SaaS平台前端项目的**阶段一：基础设施层**。目标是搭建项目的底层框架，包括项目配置、类型系统、工具函数、全局样式、API接口封装和状态管理。这是整个项目的**地基**，后续所有模块都将依赖本阶段的产出。

**为确保任务明确、无歧义，本次需具体生成以下内容：**

### A. 项目初始化与配置（第1步）
- `package.json` - 项目依赖配置
- `tsconfig.json` - TypeScript编译配置
- `.eslintrc.js` - 代码规范配置
- `.prettierrc` - 代码格式化配置
- `vite.config.ts` - Vite构建配置
- `.gitignore` - Git忽略文件配置
- `README.md` - 项目说明文档
- `src/pages.json` - uni-app页面路由配置
- `src/manifest.json` - uni-app应用配置
- `src/App.vue` - 应用入口组件
- `src/main.ts` - 应用入口脚本

### B. TypeScript类型定义（第2步）
- `src/types/common.ts` - 通用类型定义
- `src/types/auth.ts` - 认证相关类型
- `src/types/user.ts` - 用户相关类型
- `src/types/room.ts` - 房间相关类型
- `src/types/expert.ts` - 专家相关类型
- `src/types/department.ts` - 科室相关类型（原categories）
- `src/types/banner.ts` - 焦点图相关类型
- `src/types/settings.ts` - 设置相关类型
- `src/types/tags.ts` - 标签相关类型（新增）
- `src/types/brands.ts` - 品牌相关类型（新增）
- `src/types/favorites.ts` - 用户收藏类型（新增）
- `src/types/history.ts` - 观看历史类型（新增）
- `src/types/notifications.ts` - 通知类型（新增）
- `src/types/subscriptions.ts` - 订阅提醒类型（新增）

### C. 工具函数层（第3步）
- `src/utils/request.ts` - 统一网络请求封装
- `src/utils/time.ts` - 时间格式化工具
- `src/utils/validator.ts` - 表单校验工具
- `src/utils/common.ts` - 通用工具函数

### D. 全局样式与常量（第4步）
- `src/common/uni.scss` - 全局样式变量
- `src/common/theme.scss` - 主题样式
- `src/common/responsive.scss` - 响应式断点
- `src/common/constants.ts` - 全局常量定义

### E. API接口封装（第5步）
- `src/api/auth.ts` - 认证接口
- `src/api/user.ts` - 用户接口
- `src/api/banner.ts` - 焦点图接口
- `src/api/department.ts` - 科室接口（原categories）
- `src/api/expert.ts` - 专家接口
- `src/api/room.ts` - 房间接口
- `src/api/settings.ts` - 设置接口
- `src/api/tags.ts` - 标签接口（新增）
- `src/api/brands.ts` - 品牌接口（新增）
- `src/api/favorites.ts` - 用户收藏接口（新增）
- `src/api/history.ts` - 观看历史接口（新增）
- `src/api/notifications.ts` - 通知接口（新增）
- `src/api/subscriptions.ts` - 订阅提醒接口（新增）

### F. 状态管理（第6步）
- `src/store/index.ts` - Pinia入口文件
- `src/store/auth.ts` - 认证状态管理
- `src/store/user.ts` - 用户状态管理
- `src/store/settings.ts` - 设置状态管理
- `src/store/ui.ts` - UI状态管理
- `src/store/room.ts` - 房间状态管理
- `src/store/session.ts` - 场次状态管理
- `src/store/tags.ts` - 标签状态管理（新增）
- `src/store/brands.ts` - 品牌状态管理（新增）
- `src/store/favorites.ts` - 用户收藏状态管理（新增）
- `src/store/notifications.ts` - 通知状态管理（新增）

---

## 3. 核心上下文信息（Core Context Information）

### 3.1 唯一事实来源
- **设计文档**：《直播SaaS平台移动端前端设计文档(微信小程序).md》和《直播SaaS平台微信小程序前端代码生成提示词（总体）.md》是本次任务所有代码生成工作的唯一且最高的设计依据。
- **后端API接口规范**：严格遵循《后端新增api接口和模块设计文档-v2.md》中的接口定义，确保前后端数据结构100%一致。
- **新增模块**：必须完整封装Tags、Brands、Experts、Session_Tags、User_Favorites、Watch_History、Notifications等模块的API接口。

### 3.2 技术栈确认
- **核心框架**：uni-app（Vue3 + Composition API + TypeScript）
- **状态管理**：Pinia
- **UI组件库**：uni-ui（DCloud官方，MIT许可证，商业友好）
- **构建工具**：Vite
- **代码规范**：ESLint + Prettier
- **包管理**：npm

### 3.3 依赖关系说明
本阶段各模块的依赖关系：
```
第1步(项目配置) 
  ↓
第2步(类型定义) ← 独立，无依赖
  ↓
第3步(工具函数) ← 依赖第2步
  ↓
第4步(全局样式) ← 独立，无依赖
  ↓
第5步(API层) ← 依赖第2步、第3步
  ↓
第6步(状态管理) ← 依赖第2步、第3步、第5步
```

---

## 4. 全局强制性约束与最高准则（Global Mandatory Constraints & Ultimate Principle）

### 4.1 最高准则
**零偏差原则**：所有生成内容必须与设计文档**100%完全一致**。任何细节的偏离、遗漏或自由发挥都是**绝对禁止**的。

### 4.2 命名规范（强制执行）
- **变量/函数**：`camelCase`（如：`getUserInfo`、`isLoggedIn`）
- **组件/页面**：`PascalCase`（如：`LoginForm.vue`、`Home.vue`）
- **类型定义**：`PascalCase`（如：`User`、`Room`、`ApiResponse`）
- **常量**：`UPPER_SNAKE_CASE`（如：`API_BASE_URL`、`MAX_PAGE_SIZE`）
- **文件名**：
  - API文件：小写（如：`auth.ts`、`room.ts`）
  - Store文件：小写（如：`user.ts`、`settings.ts`）
  - 工具文件：小写（如：`request.ts`、`time.ts`）

### 4.3 代码质量要求
- **TypeScript强类型**：所有函数必须有明确的参数类型和返回值类型
- **完整注释**：关键业务逻辑、接口调用、复杂计算必须有JSDoc风格注释
- **错误处理**：所有API调用必须有完整的错误处理逻辑
- **统一风格**：2空格缩进，无分号，单引号，统一使用Prettier格式化

### 4.4 安全规范
- **XSS防护**：所有用户输入必须进行转义
- **Token管理**：Token存储于uni.setStorageSync，自动加密
- **HTTPS强制**：所有API请求必须通过HTTPS
- **敏感信息脱敏**：前端日志禁止包含敏感信息

---

## 5. 分步生成与交叉验证流程（Step-by-Step Generation & Cross-Validation Flow）

### 步骤1：项目初始化与配置
**目标**：生成项目基础配置文件，确保项目可以正常运行和构建。

**生成文件列表**：
- `package.json`
- `tsconfig.json`
- `.eslintrc.js`
- `.prettierrc`
- `vite.config.ts`
- `.gitignore`
- `README.md`
- `src/pages.json`
- `src/manifest.json`
- `src/App.vue`
- `src/main.ts`

**验证点**：
- [ ] package.json是否包含所有必需依赖（Vue3、Pinia、TypeScript、uView Plus等）？
- [ ] tsconfig.json配置是否支持uni-app和Vue3？
- [ ] pages.json是否配置了底部TabBar（首页、品牌、我的直播、专家、我的）？
- [ ] App.vue是否初始化了Pinia和全局样式？
- [ ] main.ts是否正确挂载了Pinia？

---

### 步骤2：TypeScript类型定义生成
**目标**：定义所有核心数据实体的TypeScript接口，为整个项目提供类型安全保障。

**生成文件列表**：
- `src/types/common.ts`
- `src/types/auth.ts`
- `src/types/user.ts`
- `src/types/room.ts`
- `src/types/expert.ts`
- `src/types/department.ts`
- `src/types/banner.ts`
- `src/types/settings.ts`
- `src/types/tags.ts` - 标签相关类型（新增）
- `src/types/brands.ts` - 品牌相关类型（新增）
- `src/types/favorites.ts` - 用户收藏类型（新增）
- `src/types/history.ts` - 观看历史类型（新增）
- `src/types/notifications.ts` - 通知类型（新增）
- `src/types/subscriptions.ts` - 订阅提醒类型（新增）

**要求**：
1. 类型定义必须与后端数据库表结构和API响应格式**完全一致**
2. 必须定义分页响应的泛型类型`PaginatedResponse<T>`
3. 必须定义统一的API响应格式`ApiResponse<T>`
4. 所有枚举类型使用`type`而非`enum`（更符合TypeScript最佳实践）

**验证点**：
- [ ] 每个类型的字段名、类型、是否可选是否与设计文档一致？
- [ ] 是否定义了通用的分页和响应类型？
- [ ] 是否所有类型都导出（export）？

---

### 步骤3：工具函数层生成
**目标**：实现通用工具函数，包括网络请求、时间处理、表单校验等。

**生成文件列表**：
- `src/utils/request.ts`
- `src/utils/time.ts`
- `src/utils/validator.ts`
- `src/utils/common.ts`

**request.ts 强制要求**：
1. **必须实现**基于`uni.request`的统一封装
2. **必须包含**请求拦截器（自动注入Token）
3. **必须包含**响应拦截器（统一处理状态码）
4. **必须实现**完整的错误处理（网络错误、超时、业务错误）
5. **必须支持**泛型，返回类型化的Promise
6. **必须实现**请求重试机制（最多3次）
7. **必须实现**Token过期自动刷新逻辑

**time.ts 要求**：
- 实现日期格式化函数（`formatDate`, `formatTime`, `formatRelativeTime`）
- 实现倒计时函数（用于直播预告）
- 实现时间差计算函数

**validator.ts 要求**：
- 实现手机号验证
- 实现邮箱验证
- 实现密码强度验证
- 实现验证码验证

**验证点**：
- [ ] request.ts是否正确调用了uni.request？
- [ ] 是否实现了Token自动注入和刷新？
- [ ] 错误处理是否完整（包括console.error和uni.showToast）？
- [ ] 工具函数是否都有完整的JSDoc注释？

---

### 步骤4：全局样式与常量生成
**目标**：定义全局CSS变量、主题配置和常量，确保UI一致性。

**生成文件列表**：
- `src/common/uni.scss`
- `src/common/theme.scss`
- `src/common/responsive.scss`
- `src/common/constants.ts`

**uni.scss 必须包含**：
- 颜色变量（主题色、文本色、背景色、边框色、状态色）
- 字体变量（字号、行高、字重）
- 间距变量（padding、margin标准值）
- 圆角变量（border-radius标准值）
- 阴影变量（box-shadow标准值）
- 动画变量（transition、animation标准值）

**theme.scss 要求**：
- 定义日间/夜间模式的颜色方案
- 实现主题切换的CSS变量覆盖

**constants.ts 必须包含**：
- `API_BASE_URL` - API基础地址
- `TOKEN_KEY` - Token存储键名
- `MAX_PAGE_SIZE` - 分页最大数量
- `REQUEST_TIMEOUT` - 请求超时时间
- 其他业务常量

**验证点**：
- [ ] CSS变量命名是否遵循BEM规范？
- [ ] 颜色值是否与设计稿一致？
- [ ] 是否支持日间/夜间模式切换？

---

### 步骤5：API接口封装生成
**目标**：封装所有后端API接口，提供类型安全的调用方法。

**生成文件列表**：
- `src/api/auth.ts`
- `src/api/user.ts`
- `src/api/banner.ts`
- `src/api/department.ts`
- `src/api/expert.ts`
- `src/api/room.ts`
- `src/api/settings.ts`
- `src/api/tags.ts` - 标签API（基于后端Tags模块）
- `src/api/brands.ts` - 品牌API（基于后端Brands模块）
- `src/api/favorites.ts` - 用户收藏API（基于后端user_favorites表）
- `src/api/history.ts` - 观看历史API（基于后端watch_history表）
- `src/api/notifications.ts` - 通知API（基于后端notifications表）
- `src/api/subscriptions.ts` - 订阅提醒API（基于后端user_subscriptions表）

**每个API文件必须包含**：
1. 导入相关类型定义（从`src/types/`）
2. 导入request工具（从`src/utils/request`）
3. 实现所有接口方法（严格按照设计文档的接口列表）
4. 每个方法必须有完整的JSDoc注释
5. 所有方法必须使用泛型指定返回类型

**auth.ts 接口清单**（示例）：
- `login(params: LoginParams): Promise<LoginResponse>` - 登录
- `register(params: RegisterParams): Promise<User>` - 注册
- `sendVerifyCode(phone: string): Promise<void>` - 发送验证码
- `getCaptcha(): Promise<CaptchaResponse>` - 获取图形验证码
- `refreshToken(): Promise<TokenResponse>` - 刷新Token
- `logout(): Promise<void>` - 退出登录

**tags.ts 接口清单**（新增，基于后端Tags模块）：
- `getTagList(params?: TagListParams): Promise<Tag[]>` - 获取标签列表
- `createTag(data: CreateTagData): Promise<Tag>` - 创建标签（Admin）
- `updateTag(tagId: string, data: UpdateTagData): Promise<Tag>` - 更新标签（Admin）
- `deleteTag(tagId: string, hardDelete?: boolean): Promise<void>` - 删除标签（Admin）

**brands.ts 接口清单**（新增，基于后端Brands模块）：
- `getBrandList(params?: BrandListParams): Promise<Brand[]>` - 获取品牌列表
- `getBrandContent(brandId: string): Promise<BrandContentResponse>` - 获取品牌详情及关联专题
- `createBrand(data: CreateBrandData): Promise<Brand>` - 创建品牌（Admin）
- `updateBrand(brandId: string, data: UpdateBrandData): Promise<Brand>` - 更新品牌（Admin）
- `deleteBrand(brandId: string, hardDelete?: boolean): Promise<void>` - 删除品牌（Admin）
- `addBrandTopics(brandId: string, topicIds: string[]): Promise<void>` - 批量关联专题到品牌（Admin）
- `removeBrandTopic(brandId: string, topicId: string): Promise<void>` - 解除品牌-专题关联（Admin）

**favorites.ts 接口清单**（新增，基于后端user_favorites表）：
- `getFavoriteList(params?: PaginationParams): Promise<PaginatedResponse<UserFavorite>>` - 获取用户收藏列表
- `addFavorite(roomId: string): Promise<UserFavorite>` - 添加收藏
- `removeFavorite(roomId: string): Promise<void>` - 取消收藏
- `checkFavoriteStatus(roomId: string): Promise<boolean>` - 检查收藏状态

**history.ts 接口清单**（新增，基于后端watch_history表）：
- `getWatchHistory(params?: PaginationParams): Promise<PaginatedResponse<WatchHistory>>` - 获取观看历史
- `addWatchHistory(sessionId: string, progress?: number): Promise<WatchHistory>` - 添加观看记录
- `updateWatchProgress(sessionId: string, progress: number): Promise<WatchHistory>` - 更新观看进度
- `deleteWatchHistory(historyId: string): Promise<void>` - 删除单条历史
- `clearAllHistory(): Promise<void>` - 清空所有历史

**notifications.ts 接口清单**（新增，基于后端notifications表）：
- `getNotificationList(params?: NotificationListParams): Promise<PaginatedResponse<Notification>>` - 获取通知列表
- `markAsRead(notificationId: string): Promise<void>` - 标记为已读
- `markAllAsRead(): Promise<void>` - 全部标记为已读
- `getUnreadCount(): Promise<number>` - 获取未读数量
- `deleteNotification(notificationId: string): Promise<void>` - 删除通知

**subscriptions.ts 接口清单**（新增，基于后端user_subscriptions表）：
- `getSubscriptionList(params?: PaginationParams): Promise<PaginatedResponse<UserSubscription>>` - 获取订阅列表
- `subscribeRoom(roomId: string): Promise<UserSubscription>` - 订阅房间开播提醒
- `subscribeSession(sessionId: string): Promise<UserSubscription>` - 订阅单场次提醒
- `unsubscribe(subscriptionId: string): Promise<void>` - 取消订阅
- `checkSubscriptionStatus(targetId: string, targetType: 'room' | 'session'): Promise<boolean>` - 检查订阅状态

**验证点**：
- [ ] 设计文档中的每个接口是否都已实现？
- [ ] 接口路径、请求方法、参数、返回值是否与后端一致？
- [ ] 是否正确使用了request工具？
- [ ] 是否有完整的类型标注？

---

### 步骤6：状态管理生成
**目标**：实现Pinia状态管理，管理全局状态和业务逻辑。

**生成文件列表**：
- `src/store/index.ts`
- `src/store/auth.ts`
- `src/store/user.ts`
- `src/store/settings.ts`
- `src/store/ui.ts`
- `src/store/room.ts`
- `src/store/session.ts`
- `src/store/tags.ts` - 标签状态管理（新增）
- `src/store/brands.ts` - 品牌状态管理（新增）
- `src/store/favorites.ts` - 用户收藏状态管理（新增）
- `src/store/notifications.ts` - 通知状态管理（新增）

**每个Store必须包含**：
1. **state**：定义状态数据结构
2. **getters**：定义计算属性
3. **actions**：定义异步操作和业务逻辑
4. 完整的错误处理（try-catch）
5. 加载状态管理（loading标志）
6. 持久化配置（需要持久化的Store）

**auth.ts Store示例结构**：
```typescript
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    refreshToken: null as string | null,
    isLoggedIn: false,
    loading: false,
    error: null as Error | null,
  }),
  
  getters: {
    hasToken: (state) => !!state.token,
  },
  
  actions: {
    async login(params: LoginParams) {
      this.loading = true
      this.error = null
      try {
        const response = await authApi.login(params)
        this.token = response.access_token
        this.refreshToken = response.refresh_token
        this.isLoggedIn = true
        // 存储Token到本地
        uni.setStorageSync('token', this.token)
        return response
      } catch (error) {
        this.error = error as Error
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.token = null
        this.refreshToken = null
        this.isLoggedIn = false
        uni.removeStorageSync('token')
      }
    },
  },
  
  persist: true, // 持久化配置
})
```

**room.ts Store特殊要求**：
- 必须支持分页加载（page、size、total、hasMore）
- 必须实现数据追加逻辑（加载更多时追加而非覆盖）
- 必须实现刷新逻辑（下拉刷新时覆盖数据）

**新增Store模块特殊要求**：

**tags.ts Store**：
- 管理标签列表和选中状态
- 支持标签的CRUD操作（Admin用户）
- 支持按名称搜索和筛选

**brands.ts Store**：
- 管理品牌列表和品牌详情
- 支持品牌的CRUD操作（Admin用户）
- 管理品牌与专题的关联关系

**favorites.ts Store**：
- 管理用户收藏列表和收藏状态
- 支持分页加载收藏列表
- 实时同步收藏状态（添加/移除）
- 支持本地缓存和数据持久化

**notifications.ts Store**：
- 管理通知列表和未读数量
- 支持实时更新未读数量
- 支持批量标记为已读
- 支持通知类型筛选（system/subscription/interaction）

**验证点**：
- [ ] State的数据结构是否与类型定义一致？
- [ ] Actions是否正确调用了API层方法？
- [ ] 是否有完整的错误处理？
- [ ] 是否管理了loading状态？
- [ ] 分页逻辑是否正确实现？

---

## 6. 模块生成指令（Module Generation Instructions）

### 6.1 package.json 配置要求
```json
{
  "name": "live-streaming-wechat",
  "version": "1.0.0",
  "description": "医学直播SaaS平台微信小程序",
  "scripts": {
    "dev:mp-weixin": "uni -p mp-weixin",
    "build:mp-weixin": "uni build -p mp-weixin",
    "dev:h5": "uni -p h5",
    "build:h5": "uni build -p h5",
    "lint": "eslint --ext .js,.ts,.vue src",
    "format": "prettier --write \"src/**/*.{js,ts,vue,json,css,scss}\""
  },
  "dependencies": {
    "@dcloudio/uni-app": "^3.0.0",
    "@dcloudio/uni-mp-weixin": "^3.0.0",
    "pinia": "^2.1.0",
    "pinia-plugin-persistedstate": "^3.2.0",
    "vue": "^3.3.0"
  },
  "devDependencies": {
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vue/eslint-config-prettier": "^8.0.0",
    "@vue/eslint-config-typescript": "^12.0.0",
    "eslint": "^8.45.0",
    "eslint-plugin-vue": "^9.15.0",
    "prettier": "^3.0.0",
    "typescript": "^5.1.0",
    "vite": "^4.4.0"
  }
}
```

### 6.2 tsconfig.json 配置要求
必须支持uni-app的路径别名和Vue3的类型检查。

### 6.3 pages.json 配置要求
必须配置底部TabBar，包含5个Tab：
1. 首页（pages/home/Home）
2. 品牌（pages/brand/BrandZone）
3. 我的直播（pages/my-live/MyLive）- 中间位置
4. 专家（pages/expert/ExpertList）
5. 我的（pages/profile/Profile）

### 6.4 类型定义示例
所有类型必须与后端数据结构完全一致，包括字段名、类型、可选性。

### 6.5 request.ts 核心逻辑
必须实现：
- 请求拦截：自动注入Token
- 响应拦截：统一处理状态码
- 错误处理：网络错误、超时、业务错误
- 重试机制：失败自动重试最多3次
- Token刷新：401时自动刷新Token并重试

### 6.6 Store Actions设计原则
1. 所有异步操作必须返回Promise
2. 成功时resolve，失败时reject
3. 必须管理loading状态
4. 必须捕获并存储error
5. 分页数据必须支持追加和刷新两种模式

---

## 7. 最终交付与质量保证协议（Final Delivery & Quality Assurance Protocol）

### 7.1 输出格式要求
- 每个文件必须输出完整代码，不能有省略或占位符
- 每个代码块前必须标注完整的文件路径
- 禁止在代码之外添加多余的解释

### 7.2 自我验证清单
在提交前，必须确认：
- [ ] 所有文件是否都已生成？
- [ ] 代码是否可以直接运行（无语法错误）？
- [ ] 类型定义是否完整？
- [ ] API接口是否与设计文档一致？
- [ ] Store逻辑是否完整（包含错误处理）？
- [ ] 是否遵循了命名规范？

### 7.3 最终一致性断言
生成完成后，必须输出以下断言：

```
[阶段一完成断言 - PHASE ONE COMPLETION ASSERTION]
✓ 项目配置文件：已生成且可运行
✓ TypeScript类型定义：100%覆盖核心实体（包含新增6个模块类型）
✓ 工具函数层：已实现request、time、validator、common
✓ 全局样式：已定义CSS变量和主题
✓ API接口层：已封装所有后端接口（包含新增6个API模块）
  - ✓ 原有API：auth、user、banner、department、expert、room、settings
  - ✓ 新增API：tags、brands、favorites、history、notifications、subscriptions
✓ 状态管理：已实现Pinia Store，包含完整业务逻辑（包含新增4个Store）
  - ✓ 原有Store：auth、user、settings、ui、room、session
  - ✓ 新增Store：tags、brands、favorites、notifications
✓ 代码质量：符合ESLint和Prettier规范
✓ 类型安全：100%类型覆盖
✓ 错误处理：所有API调用包含try-catch
✓ 后端API对接：与《后端新增api接口和模块设计文档-v2.md》100%一致
✓ 零偏差原则：已遵循

[新增功能模块覆盖]
✓ Tags模块：标签管理（查询/Admin CRUD）
✓ Brands模块：品牌管理（查询/Admin CRUD/专题关联）
✓ User Favorites：用户收藏功能（增删查/状态检查）
✓ Watch History：观看历史功能（记录/进度/删除/清空）
✓ Notifications：通知系统（列表/已读/未读计数）
✓ Subscriptions：订阅提醒（房间/场次订阅/取消）

[重要提示]
- 本阶段为地基，所有后续开发依赖本阶段产出
- 新增API模块已完整对接后端v2.md文档
- 请确保所有文件可直接复制使用
- 建议生成后立即运行`npm run dev:mp-weixin`验证
```

---

## 8. 特别注意事项

### 8.1 微信小程序特性
- 使用`uni.request`而非`axios`
- 使用`uni.setStorageSync`而非`localStorage`
- 使用`uni.navigateTo`而非`router.push`
- 使用`uni.showToast`而非`alert`

### 8.2 性能优化
- request工具必须支持请求取消
- 图片懒加载
- 列表虚拟滚动
- 防抖节流

### 8.3 错误边界
- 所有API调用必须有降级方案
- 网络异常时显示友好提示
- 关键操作失败时提供重试按钮

---

**[开始生成指令]**
请严格按照本文档要求，从步骤1开始，逐步生成阶段一的所有代码文件。每完成一个步骤，进行自我验证后再继续下一步。
