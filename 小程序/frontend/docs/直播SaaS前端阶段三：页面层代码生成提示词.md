# 直播SaaS前端阶段三：页面层代码生成提示词

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通Vue3页面开发和uni-app路由配置。你的任务是将阶段一、二的产出（API、Store、组件）组装成完整的业务页面，实现用户可见、可交互的应用界面。

---

## 2. 任务目标（Task Objective）
本次任务为直播SaaS平台前端项目的**阶段三：页面层**。目标是按照业务模块的依赖顺序，逐个生成所有页面，并配置完整的路由系统。

**生成页面清单（按推荐顺序）：**

### 第9步：认证模块（1个页面）
- `src/pages/auth/Login.vue` (微信授权登录页面)

### 第10步：设置模块（7个页面）
- `src/pages/settings/Settings.vue`
- `src/pages/settings/ChangePassword.vue`
- `src/pages/settings/BindPhone.vue`
- `src/pages/settings/BindEmail.vue`
- `src/pages/settings/ThirdPartyAccounts.vue`
- `src/pages/settings/Blacklist.vue`
- `src/pages/feedback/Feedback.vue`

### 第11步：专家模块（2个页面）
- `src/pages/expert/ExpertList.vue`
- `src/pages/expert/ExpertDetail.vue`

### 第12步：科室模块（1个页面）
- `src/pages/department/DepartmentList.vue`

### 第13步：个人中心模块（8个页面）
- `src/pages/profile/Profile.vue`
- `src/pages/profile/ProfileEdit.vue`
- `src/pages/profile/FollowingList.vue`
- `src/pages/profile/FollowerList.vue`
- `src/pages/profile/ViewHistory.vue`
- `src/pages/profile/CollectionList.vue`
- `src/pages/profile/OrderList.vue`
- `src/pages/profile/CouponList.vue`

### 第14步：房间模块（2个页面）
- `src/pages/room/RoomList.vue`
- `src/pages/room/RoomDetail.vue`

### 第15步：我的直播模块（6个页面）
- `src/pages/my-live/MyLive.vue`
- `src/pages/my-live/CreateSession.vue`
- `src/pages/my-live/EditSession.vue`
- `src/pages/my-live/Statistics.vue`
- `src/pages/my-live/Revenue.vue`
- `src/pages/my-live/HostApply.vue`

### 第16步：直播观看模块（1个页面）
- `src/pages/live/LiveView.vue`

### 第17步：首页模块（1个页面）
- `src/pages/home/Home.vue`

### 第18步：辅助页面（5个页面）
- `src/pages/about/About.vue`
- `src/pages/about/PrivacyPolicy.vue`
- `src/pages/webview/Webview.vue`
- `src/pages/common/NotFound.vue`
- `src/pages/brand/BrandZone.vue`

### 第19步：路由配置
- 更新`src/pages.json`，配置所有页面路由

---

## 3. 核心约束（Core Constraints）

### 3.1 智能组件原则
页面组件是"智能"组件，负责：
- **调用Store**: 通过Store的actions获取和提交数据
- **状态管理**: 监听Store的state变化，更新UI
- **路由跳转**: 使用uni.navigateTo等API进行页面跳转
- **生命周期**: 在onLoad/onShow等钩子中初始化数据

### 3.2 数据单向流动
```
用户交互 → 页面组件 → Store Actions → API层 → 后端
                ↓
            更新State
                ↓
            触发UI重渲染
```

### 3.3 错误处理规范
所有API调用必须：
- 使用try-catch捕获错误
- 显示友好的错误提示（uni.showToast）
- 提供重试机制
- 记录错误日志

### 3.4 加载状态管理
- 初始加载：显示骨架屏
- 数据刷新：显示刷新动画
- 分页加载：显示底部加载提示
- 提交操作：按钮显示loading状态

---

## 4. 页面开发规范

### 4.1 页面结构模板
```vue
<template>
  <view class="page-container">
    <!-- 骨架屏/加载状态 -->
    <LoadingIndicator v-if="loading && !dataLoaded" />
    
    <!-- 错误状态 -->
    <ErrorBanner 
      v-if="error" 
      :message="error.message"
      @close="error = null"
    />
    
    <!-- 数据内容 -->
    <view v-if="dataLoaded" class="content">
      <!-- 页面内容 -->
    </view>
    
    <!-- 空状态 -->
    <EmptyState 
      v-if="!loading && dataLoaded && isEmpty"
      title="暂无数据"
      description="您还没有相关内容"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useXxxStore } from '@/store/xxx'
import { storeToRefs } from 'pinia'

// 1. Store连接
const xxxStore = useXxxStore()
const { data, loading, error } = storeToRefs(xxxStore)

// 2. 本地状态
const dataLoaded = ref(false)

// 3. 计算属性
const isEmpty = computed(() => data.value.length === 0)

// 4. 方法定义
async function loadData() {
  try {
    await xxxStore.fetchData()
    dataLoaded.value = true
  } catch (err) {
    console.error('加载数据失败', err)
  }
}

function handleRefresh() {
  xxxStore.fetchData({ refresh: true })
}

// 5. 生命周期
onMounted(() => {
  loadData()
})

// 6. uni-app生命周期
onLoad((options) => {
  // 获取页面参数
  const { id } = options
  // 初始化数据
})

onPullDownRefresh(() => {
  handleRefresh()
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  if (!loading.value && xxxStore.pagination.hasMore) {
    xxxStore.loadMore()
  }
})
</script>

<style lang="scss" scoped>
.page-container {
  min-height: 100vh;
  background: var(--color-background);
}
</style>
```

### 4.2 页面生命周期
必须实现的生命周期钩子：
- **onLoad**: 页面加载时，获取参数，初始化数据
- **onShow**: 页面显示时，刷新数据（如从其他页面返回）
- **onPullDownRefresh**: 下拉刷新（列表页必须）
- **onReachBottom**: 上拉加载更多（列表页必须）
- **onShareAppMessage**: 分享配置（需要分享的页面）

### 4.3 路由跳转规范
```typescript
// 1. 普通跳转（可返回）
uni.navigateTo({
  url: '/pages/room/RoomDetail?id=xxx'
})

// 2. 重定向跳转（不可返回）
uni.redirectTo({
  url: '/pages/auth/Login'
})

// 3. Tab切换
uni.switchTab({
  url: '/pages/home/Home'
})

// 4. 返回上一页
uni.navigateBack({
  delta: 1
})

// 5. 重新加载（清空页面栈）
uni.reLaunch({
  url: '/pages/home/Home'
})
```

---

## 5. 核心页面实现要求

### 5.1 认证模块

#### Login.vue（登录页）
**数据流**：
- 使用`useAuthStore`的`login`方法
- 登录成功后跳转到首页或返回页
- 支持手机号+验证码 / 账号密码 两种方式
- 支持微信一键登录（`uni.login`）

**验证规则**：
- 手机号：11位，1开头
- 验证码：6位数字
- 密码：8-20位，字母+数字

**交互要求**：
- 发送验证码：60秒倒计时
- 密码可见性切换
- 记住密码（本地存储）
- 图形验证码刷新

#### Register.vue（注册页）
**数据流**：
- 使用`useAuthStore`的`register`方法
- 注册成功后自动登录并跳转首页

**验证规则**：
- 手机号/邮箱验证
- 密码强度校验
- 确认密码一致性
- 验证码正确性

#### ForgotPassword.vue（忘记密码页）
**数据流**：
- 使用`authApi.resetPassword`
- 重置成功后跳转登录页

**步骤流程**：
1. 输入手机号/邮箱
2. 获取验证码
3. 设置新密码
4. 完成重置

---

### 5.2 设置模块

#### Settings.vue（设置主页）
**组件组合**：
- `GeneralSettings` - 日夜模式/字体/流量提醒
- `AccountSecurity` - 密码/手机/邮箱
- `PrivacySettings` - 授权/黑名单
- `InfoAndActions` - 版本/缓存/协议

**Store连接**：
- `useSettingsStore` - 读取和更新设置

**交互要求**：
- 点击各项跳转到对应详情页
- 退出登录需二次确认

#### ChangePassword.vue（修改密码页）
**数据流**：
- 使用`settingsApi.changePassword`
- 需要旧密码验证

**验证规则**：
- 旧密码正确性
- 新密码强度
- 新旧密码不能相同

#### BindPhone/BindEmail.vue（绑定手机/邮箱页）
**数据流**：
- 使用`settingsApi.bindPhone/bindEmail`
- 需要验证码验证

**步骤流程**：
1. 输入手机号/邮箱
2. 发送验证码
3. 输入验证码
4. 完成绑定

---

### 5.3 专家模块

#### ExpertList.vue（专家列表页）
**数据流**：
- 使用`useExpertStore`的`fetchExperts`方法
- 支持搜索、专业筛选、A-Z索引

**组件组合**：
- `SearchBar` - 搜索专家
- `SpecialtyFilter` - 专业筛选
- `ExpertList` - 专家列表（包含A-Z索引）

**交互要求**：
- 搜索防抖500ms
- 点击专家跳转详情页
- 支持关注/取消关注
- 支持下拉刷新和上拉加载

#### ExpertDetail.vue（专家详情页）
**数据流**：
- 使用`useExpertStore`的`fetchExpertById`方法
- 获取专家信息和直播列表

**页面结构**：
- 顶部：头像、姓名、职称、医院、专业
- 中间：个人简介、主要成就
- 底部：直播列表（Tab切换：预告/历史）

**交互要求**：
- 关注/取消关注按钮
- 点击直播项跳转直播间
- 分享专家主页

---

### 5.4 科室模块

#### DepartmentList.vue（科室列表页）
**数据流**：
- 使用`useDepartmentStore`的`fetchDepartmentContent`方法
- 支持科室分类切换

**组件组合**：
- `DepartmentCategoryNav` - 科室导航
- `DepartmentContentList` - 混合内容列表（直播+专家+文章）

**内容类型**：
- 直播：使用`LiveCard`渲染
- 专家：使用`ExpertCard`渲染
- 文章：使用`ArticleCard`渲染

**交互要求**：
- 点击分类切换内容
- 支持下拉刷新和上拉加载
- 点击内容跳转对应详情页

---

### 5.5 个人中心模块

#### Profile.vue（我的页面）
**组件组合**：
- `UserCard` - 用户信息卡片
- `QuickAccess` - 快捷入口（历史/收藏/订单/优惠）
- `FunctionList` - 功能列表（设置/帮助/关于）
- `LogoutButton` - 退出登录

**状态处理**：
- 未登录：显示登录按钮
- 已登录：显示用户信息和功能列表

**Store连接**：
- `useUserStore` - 用户信息
- `useAuthStore` - 登录状态

#### ProfileEdit.vue（编辑资料页）
**数据流**：
- 使用`userApi.updateProfile`
- 支持上传头像（`uni.chooseImage`）

**可编辑字段**：
- 头像、昵称、性别、生日、个人简介

#### FollowingList/FollowerList.vue（关注/粉丝列表页）
**数据流**：
- 使用`userApi.getFollowingList/getFollowerList`
- 支持取消关注/关注

**交互要求**：
- 点击用户跳转专家详情页
- 关注按钮状态切换
- 支持搜索和筛选

#### ViewHistory.vue（观看历史页）
**数据流**：
- 使用`userApi.getViewHistory`
- 支持删除历史记录

**列表项**：
- 显示直播封面、标题、专家、观看时间
- 支持清空全部历史

#### CollectionList/OrderList/CouponList.vue
按照类似逻辑实现收藏、订单、优惠券列表页

---

### 5.6 房间模块

#### RoomList.vue（房间列表页）
**数据流**：
- 使用`useRoomStore`的`fetchRooms`方法
- 支持增删改查

**交互要求**：
- 创建房间：悬浮按钮（右下角FAB）
- 编辑房间：卡片上的编辑图标
- 删除房间：二次确认后删除
- 点击房间跳转详情页

**下拉刷新/上拉加载**：
```typescript
onPullDownRefresh(() => {
  roomStore.fetchRooms({ refresh: true })
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  if (!loading.value && roomStore.pagination.hasMore) {
    roomStore.fetchRooms()
  }
})
```

#### RoomDetail.vue（房间详情页）
**数据流**：
- 使用`useRoomStore`的`fetchRoomById`方法
- 获取房间信息和场次列表

**组件组合**：
- `RoomHeader` - 房间头部
- `SessionTabs` - 场次Tab切换
- `LiveCard` - 场次列表

**交互要求**：
- 关注/取消关注房间
- 分享房间
- 编辑/删除房间（房主权限）
- 查看场次列表
- 点击场次跳转直播间

---

### 5.7 我的直播模块

#### MyLive.vue（我的直播主页）
**权限控制**：
- 未登录：引导登录
- 非主播：显示`HostApplyGuide`
- 已认证：显示主播功能

**组件组合**：
- `QuickActions` - 快捷操作（创建/房间/统计/收益）
- `LiveStatusCard` - 当前直播状态
- `SessionHistory` - 历史直播列表

**Store连接**：
- `useUserStore` - 用户角色
- `useRoomStore` - 房间列表
- `useSessionStore` - 场次列表

#### CreateSession.vue（创建场次页）
**数据流**：
- 使用`sessionApi.createSession`

**表单字段**：
- 房间选择、标题、简介、开始时间、预计时长、封面图

**验证规则**：
- 标题不能为空
- 开始时间必须晚于当前时间
- 封面图推荐16:9

#### EditSession.vue（编辑场次页）
类似`CreateSession`，但支持预填充数据

#### Statistics.vue（数据统计页）
**数据流**：
- 使用`sessionApi.getStatistics`

**统计指标**：
- 总观看人数、峰值人数、点赞数、分享数、弹幕数
- 时间趋势图表
- 观众地域分布

#### Revenue.vue（收益中心页）
**数据流**：
- 使用`userApi.getRevenue`

**收益数据**：
- 总收益、本月收益、待结算
- 收益明细列表
- 提现功能

#### HostApply.vue（主播申请页）
**数据流**：
- 使用`userApi.applyHost`

**申请表单**：
- 真实姓名、身份证、联系方式、从业证明、个人简介

---

### 5.8 直播观看模块

#### LiveView.vue（直播观看页）
**数据流**：
- 使用`useSessionStore`的`fetchSessionById`方法
- 实时获取直播状态和统计数据

**核心功能**：
- 视频播放器（`<live-player>`组件）
- 实时弹幕（WebSocket连接）
- 点赞动画
- 观看人数显示
- 分享按钮

**小窗模式**：
- 支持小窗播放（Picture-in-Picture）
- 边看边浏览其他内容

**流量提醒**：
- 使用`DataUsageAlert`组件
- 检测网络类型（`uni.getNetworkType`）
- 非WiFi时提醒用户

---

### 5.9 首页模块

#### Home.vue（首页）
**组件组合**（按顺序）：
1. `TopBar` - 顶部栏（搜索/消息）
2. `CategoryTabs` - 科室筛选（吸顶）
3. `FollowingUpdates` - 关注动态
4. `Banner3D` - 3D焦点图
5. `FeedList` - Feed流列表

**数据流**：
- `useCategoryStore` - 科室分类
- `useUserStore` - 关注列表
- `useBannerStore` - 焦点图
- `useSessionStore` - Feed流数据

**交互要求**：
- 切换科室筛选，Feed流数据更新
- 支持视图模式切换（单列/双列）
- 长按Tab唤起快捷菜单
- 下拉刷新，上拉加载

**视图模式**：
```typescript
const viewMode = computed(() => uiStore.viewMode) // 'single' | 'double'

function toggleViewMode() {
  uiStore.setViewMode(viewMode.value === 'single' ? 'double' : 'single')
}
```

---

### 5.10 辅助页面

#### About.vue（关于我们页）
显示应用信息、版本号、团队介绍

#### PrivacyPolicy.vue（隐私政策页）
显示隐私政策和用户协议

#### Webview.vue（通用Webview页）
用于加载外部H5页面

#### NotFound.vue（404页面）
显示友好的404提示和返回首页按钮

#### BrandZone.vue（品牌专区页）
Tab页之一，展示合作品牌和广告

---

## 6. 路由配置（pages.json）

### 6.1 全局配置
```json
{
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "医学直播",
    "navigationBarBackgroundColor": "#FFFFFF",
    "backgroundColor": "#F8F8F8"
  },
  "tabBar": {
    "color": "#999999",
    "selectedColor": "#509CEC",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "black",
    "list": [
      {
        "pagePath": "pages/home/Home",
        "text": "首页",
        "iconPath": "static/tab-home.png",
        "selectedIconPath": "static/tab-home-active.png"
      },
      {
        "pagePath": "pages/brand/BrandZone",
        "text": "品牌",
        "iconPath": "static/tab-brand.png",
        "selectedIconPath": "static/tab-brand-active.png"
      },
      {
        "pagePath": "pages/my-live/MyLive",
        "text": "我的直播",
        "iconPath": "static/tab-live.png",
        "selectedIconPath": "static/tab-live-active.png"
      },
      {
        "pagePath": "pages/expert/ExpertList",
        "text": "专家",
        "iconPath": "static/tab-expert.png",
        "selectedIconPath": "static/tab-expert-active.png"
      },
      {
        "pagePath": "pages/profile/Profile",
        "text": "我的",
        "iconPath": "static/tab-profile.png",
        "selectedIconPath": "static/tab-profile-active.png"
      }
    ]
  }
}
```

### 6.2 页面路由配置
每个页面必须配置：
- `path`: 页面路径
- `style`: 页面样式配置
  - `navigationBarTitleText`: 导航栏标题
  - `enablePullDownRefresh`: 是否启用下拉刷新（列表页必须）
  - `onReachBottomDistance`: 触发上拉加载的距离（默认50px）

示例：
```json
{
  "pages": [
    {
      "path": "pages/home/Home",
      "style": {
        "navigationBarTitleText": "首页",
        "enablePullDownRefresh": true
      }
    },
    {
      "path": "pages/room/RoomList",
      "style": {
        "navigationBarTitleText": "房间列表",
        "enablePullDownRefresh": true,
        "onReachBottomDistance": 50
      }
    }
  ]
}
```

---

## 7. 安全与性能

### 7.1 XSS防护
- 必须使用`{{ }}`渲染文本
- 严禁使用`v-html`
- 用户输入必须转义

### 7.2 权限控制
```typescript
// 页面访问权限检查
onLoad(() => {
  const isLoggedIn = authStore.isLoggedIn
  if (!isLoggedIn) {
    uni.showModal({
      title: '提示',
      content: '请先登录',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/auth/Login' })
        } else {
          uni.navigateBack()
        }
      }
    })
  }
})
```

### 7.3 性能优化
- 图片懒加载
- 长列表虚拟滚动
- 路由懒加载
- 防抖节流

---

## 8. 最终交付

### 8.1 输出格式
- 每个页面一个独立的`.vue`文件
- 完整的`pages.json`配置
- 代码必须完整，可直接运行

### 8.2 自我验证清单
- [ ] 所有页面是否都已生成？
- [ ] 是否正确连接了Store？
- [ ] 是否实现了下拉刷新和上拉加载？
- [ ] 是否有完整的错误处理？
- [ ] 是否有加载状态和空状态？
- [ ] pages.json是否配置完整？

### 8.3 完成断言
```
[阶段三完成断言 - PHASE THREE COMPLETION ASSERTION]
✓ 认证模块：3个页面，已生成
✓ 设置模块：7个页面，已生成
✓ 专家模块：2个页面，已生成
✓ 科室模块：1个页面，已生成
✓ 个人中心模块：8个页面，已生成
✓ 房间模块：2个页面，已生成
✓ 我的直播模块：6个页面，已生成
✓ 直播观看模块：1个页面，已生成
✓ 首页模块：1个页面，已生成
✓ 辅助页面：5个页面，已生成
✓ 路由配置：pages.json已完整配置
✓ Store连接：所有页面正确连接Store
✓ 错误处理：所有API调用包含try-catch
✓ 加载状态：支持骨架屏/loading/empty状态
✓ 交互完整：支持下拉刷新/上拉加载/跳转/分享
✓ 零偏差原则：已遵循

[重要提示]
- 本阶段完成后，整个前端项目基本可运行
- 建议在微信开发者工具中进行真机测试
- 后续可根据实际需求进行功能迭代和优化
```

---

**[开始生成指令]**
请严格按照本文档要求，从第9步认证模块开始，按推荐顺序逐个生成所有页面代码和路由配置。每个页面必须包含完整的数据流、状态管理、错误处理和交互逻辑。
