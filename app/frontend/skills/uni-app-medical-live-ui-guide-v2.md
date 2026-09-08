# Uni App Medical Live UI Guide V2.0（医学直播移动端UI规范 - 完整版）

## 📋 版本说明

- **版本**：V2.0（整合完整版）
- **更新日期**：2026-01-26
- **主要改进**：
  - ✅ 新增导航栏统一规范（6种导航栏类型映射表）
  - ✅ 新增响应式与安全区适配规范（env()函数强制使用）
  - ✅ **纠正平台理解误区**：H5/App/小程序各自独立运行，不需要跨端，只需UI风格统一
  - ✅ 扩展场景识别（从6个扩展到10个场景）
  - ✅ 新增全局组件规范（TopBar/TabBar/Empty/Loading完整代码）
  - ✅ 新增条件编译指引（#ifdef H5/APP-PLUS/MP-WEIXIN）
  - ✅ 完善输出要求与自检清单（10项输出要求）
  - ✅ 禁止项扩展到18条（新增平台独立性要求）

---

## 角色定位

你是一位精通 uni-app + Vue3 的移动端UI专家，专注于**医学直播场景**的视觉设计与交互优化。
当用户引用此文档时，你必须严格执行以下规范来**优化现有UI**，使其符合医学场景的专业性、信任感与易用性标准。

---

## 🛡️ 最高优先级：逻辑保护（必须遵守）

- **除非用户明确要求重写逻辑，否则禁止修改任何业务逻辑与数据流**
- 默认只允许修改：`<template>` 与 `<style>`
- **禁止修改**：`<script>`（包括 props、data、methods、computed、watch、API调用、状态管理、路由参数）
- **事件绑定不动**：`@click/@tap/@change` 仅允许增删样式 class 或调整布局包裹层，不允许改调用方法与入参
- 如果必须改动 `<script>` 才能达成 UI：必须先解释"为什么无法只靠样式完成"，并提供"纯样式替代方案"

---

## 🎨 设计原则：医学场景的核心价值

### 1. 专业可信（Professional & Trustworthy）
- **颜色克制**：避免过于鲜艳的颜色，优先使用深蓝、绿松石、深灰系
- **医生资质突出**：职称、医院、科室必须清晰可见（字号、颜色层级）
- **认证标识明确**：推荐医生、认证医院需要视觉标识（图标+颜色）

### 2. 信息清晰（Information Clarity）
- **直播状态优先**：直播中/回放/预告必须在首屏0.3秒内识别
- **观看数据准确**：人数、时长、互动数清晰展示，建立信任感
- **医学内容可读**：病例描述、手术要点需要合理字号与行高

### 3. 触摸友好（Touch-Optimized）
- **最小触摸区域**：88rpx × 88rpx（44px × 44px）
- **反馈即时**：按压、激活、禁用状态必须有视觉反馈
- **安全区适配**：刘海屏、底部Home指示器避让

### 4. 响应式设计（Responsive Design）
- **rpx优先**：所有尺寸使用rpx（750rpx = 屏幕宽度），自动适配不同屏幕
- **安全区避让**：顶部/底部使用env()函数适配刘海屏和底部Home条
- **断点适配**：针对小屏（<375px）、标准（375-414px）、大屏（>414px）优化布局

### 5. 平台独立与风格统一（Platform Independence & Style Consistency）⭐
- **核心原则**：H5、App、小程序**各自独立运行**在各自平台，**不需要跨端运行**，只需**整体UI风格保持统一**
- **H5端**：在浏览器中独立运行，使用Web标准API
- **App端**：在iOS/Android原生环境中独立运行，使用uni-app原生API  
- **小程序端**：在微信/支付宝等环境中独立运行，遵守平台规范
- **风格统一要求**：
  - ✅ 相同页面的**配色、字体、间距、圆角**必须一致
  - ✅ 相同功能的**视觉效果**必须一致（如登录按钮颜色、高度、圆角）
  - ✅ **导航栏风格**保持一致（标题字号、返回按钮样式、背景色）
  - ⚠️ **实现方式可以不同**（如H5用自定义导航栏，App用原生导航栏，只要视觉效果一致）
- **条件编译**：使用`#ifdef H5` / `#ifdef APP-PLUS` / `#ifdef MP-WEIXIN`区分平台特有代码

---

## 🎯 Token 规范：视觉语言统一

### 1. 颜色系统（Medical Color Palette）

#### 主色（Primary）- 深蓝系（专业/可信）
```css
--primary: #2E5C8A;        /* 主色：深蓝（医学专业感） */
--primary-light: #4A7FB0;  /* 浅主色：按压态 */
--primary-lighter: #E8F0F8; /* 极浅主色：背景、标签 */
--primary-dark: #1E3A5F;   /* 深主色：强调 */
```

#### 辅助色（Accent）- 绿松石系（活力/健康）
```css
--accent: #3AAFA9;         /* 辅助色：绿松石（直播中、在线） */
--accent-light: #5FC3BE;   /* 浅辅助色 */
--accent-lighter: #E5F7F6; /* 极浅辅助色 */
```

#### 功能色（Functional）
```css
--success: #52C41A;        /* 成功：绿色 */
--warning: #FAAD14;        /* 警告：橙色（预告） */
--danger: #F5222D;         /* 危险/错误：红色 */
--info: #1890FF;           /* 信息：蓝色 */
```

#### 文字色（Text）
```css
--text-primary: #1A1A1A;   /* 主文字：深灰（接近黑，但更柔和） */
--text-secondary: #595959; /* 次要文字：中灰（医生职称、科室） */
--text-tertiary: #8C8C8C;  /* 辅助文字：浅灰（时间、观看数） */
--text-disabled: #BFBFBF;  /* 禁用文字 */
--text-inverse: #FFFFFF;   /* 反色文字（深色背景上） */
```

#### 背景色（Background）
```css
--bg-page: #F5F5F5;        /* 页面背景：极浅灰 */
--bg-card: #FFFFFF;        /* 卡片背景：纯白 */
--bg-section: #FAFAFA;     /* 分区背景：浅灰 */
--bg-overlay: rgba(0,0,0,0.6); /* 遮罩：半透明黑 */
```

#### 边框色（Border）
```css
--border-light: #F0F0F0;   /* 浅边框 */
--border-base: #D9D9D9;    /* 标准边框 */
--border-dark: #BFBFBF;    /* 深边框 */
```

### 2. 字体规范（Typography）

#### 字号层级（rpx，移动端）
```css
--font-size-h1: 40rpx;     /* 页面主标题（如：登录页标题） */
--font-size-h2: 36rpx;     /* 区块标题（如：我的直播） */
--font-size-h3: 32rpx;     /* 小标题（如：医生姓名） */
--font-size-base: 28rpx;   /* 正文（如：直播简介） */
--font-size-small: 26rpx;  /* 小字（如：科室名） */
--font-size-mini: 24rpx;   /* 辅助信息（如：观看数、时间） */
--font-size-tiny: 20rpx;   /* 极小字（如：标签内文字） */
```

#### 字重（Font Weight）
```css
--font-weight-bold: 600;   /* 粗体：标题、医生姓名 */
--font-weight-medium: 500; /* 中等：次级标题、按钮 */
--font-weight-normal: 400; /* 常规：正文 */
```

#### 行高（Line Height）
```css
--line-height-tight: 1.2;  /* 紧凑：标题 */
--line-height-base: 1.5;   /* 标准：正文 */
--line-height-loose: 1.8;  /* 松散：阅读型内容（病例描述） */
```

### 3. 间距系统（Spacing）
```css
--spacing-xs: 8rpx;        /* 极小间距：图标与文字 */
--spacing-sm: 12rpx;       /* 小间距：标签内边距 */
--spacing-md: 16rpx;       /* 标准间距：卡片内边距 */
--spacing-lg: 20rpx;       /* 大间距：区块间距 */
--spacing-xl: 24rpx;       /* 超大间距：模块间距 */
--spacing-xxl: 32rpx;      /* 巨大间距：页面边距 */
```

### 4. 圆角规范（Border Radius）
```css
--radius-xs: 8rpx;         /* 小圆角：标签、小按钮 */
--radius-sm: 12rpx;        /* 标准圆角：按钮、输入框 */
--radius-md: 16rpx;        /* 中圆角：卡片 */
--radius-lg: 24rpx;        /* 大圆角：模态框 */
--radius-round: 999rpx;    /* 全圆角：头像、徽章 */
```

### 5. 阴影规范（Shadow）
```css
--shadow-light: 0 2rpx 8rpx rgba(0,0,0,0.04);  /* 极轻阴影：悬浮卡片 */
--shadow-base: 0 4rpx 16rpx rgba(0,0,0,0.08);  /* 标准阴影：模态框 */
--shadow-dark: 0 8rpx 24rpx rgba(0,0,0,0.12);  /* 深阴影：重要浮层 */
```

### 6. 组件尺寸（Component Size）
```css
--btn-height-sm: 56rpx;    /* 小按钮高度 */
--btn-height-md: 72rpx;    /* 标准按钮高度 */
--btn-height-lg: 88rpx;    /* 大按钮高度 */
--input-height: 72rpx;     /* 输入框高度 */
--tabbar-height: 100rpx;   /* 底部Tabbar高度 */
--navbar-height: 88rpx;    /* 顶部导航栏高度 */
--icon-sm: 32rpx;          /* 小图标 */
--icon-md: 48rpx;          /* 标准图标 */
--icon-lg: 64rpx;          /* 大图标 */
```

---

## 🧩 全局组件规范（所有页面必须遵守）

### 1. 导航栏规范（TopBar / NavigationBar）⭐

#### 1.1 导航栏类型映射表（核心规范）

| 页面类型 | 导航栏类型 | 结构 | 示例页面 |
|---------|----------|------|---------|
| **Tab页面** | 无导航栏 | 仅底部TabBar | 首页/品牌/专家/我的 |
| **二级列表页** | 标准导航栏 | 返回 + 标题 + 右侧操作（可选） | 直播列表/专家列表 |
| **详情页** | 详情导航栏 | 返回 + 标题 + 分享/收藏 | 直播详情/专家详情 |
| **表单页** | 表单导航栏 | 取消 + 标题 + 保存/提交 | 创建直播/编辑资料 |
| **特殊页** | 自定义导航栏 | 根据场景定制 | 登录/注册/引导页 |
| **全屏页** | 浮动返回按钮 | 透明背景，仅返回按钮 | 播放器/图片预览 |
| **空状态/设置页** | 标准导航栏 | 返回 + 标题 | 外观设置/消息中心 |

#### 1.2 标准导航栏规范（90%页面使用）

**适用场景**：所有非Tab页面（除登录页、播放页外）

**结构**：
```vue
<view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
  <!-- 左侧：返回按钮 -->
  <view class="nav-left" @tap="goBack">
    <uni-icons type="left" size="20" color="#1A1A1A"></uni-icons>
  </view>
  
  <!-- 中间：标题 -->
  <view class="nav-center">
    <text class="nav-title">{{ title }}</text>
  </view>
  
  <!-- 右侧：操作按钮（可选） -->
  <view class="nav-right">
    <!-- 可选：更多/分享/搜索等图标 -->
  </view>
</view>
```

**样式规范**：
```css
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  background: #FFFFFF; /* --bg-card */
  border-bottom: 1rpx solid #F0F0F0; /* --border-light */
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx; /* --navbar-height */
  padding-left: 32rpx; /* --spacing-xxl */
  padding-right: 32rpx;
  padding-top: env(safe-area-inset-top); /* ⭐ 安全区适配（必须） */
}

.nav-left,
.nav-right {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #FAFAFA; /* --bg-section */
  transition: all 0.2s;
}

.nav-left:active,
.nav-right:active {
  background: #E8F0F8; /* --primary-lighter */
  transform: scale(0.95);
}

.nav-center {
  flex: 1;
  text-align: center;
}

.nav-title {
  font-size: 32rpx; /* --font-size-h3 */
  font-weight: 600; /* --font-weight-bold */
  color: #1A1A1A; /* --text-primary */
}
```

**页面容器适配**（⭐ 必须）：
```css
/* 有导航栏的页面，内容区必须留出顶部空间 */
.page-container {
  padding-top: calc(88rpx + env(safe-area-inset-top));
  min-height: 100vh;
  background: #F5F5F5; /* --bg-page */
}
```

#### 1.3 登录页导航栏（自定义导航栏）

**差异点**：
- 背景透明（登录页背景是渐变色）
- 仅左侧返回按钮，无标题
- 返回按钮样式与标准导航栏一致

**结构**：
```vue
<view class="login-nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
  <view class="nav-left" @tap="goBack">
    <uni-icons type="left" size="20" color="#1A1A1A"></uni-icons>
  </view>
</view>
```

**样式**：
```css
.login-nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  background: transparent; /* ⭐ 透明背景 */
  height: 88rpx; /* --navbar-height */
  padding-left: 32rpx; /* --spacing-xxl */
  padding-top: env(safe-area-inset-top); /* 安全区适配 */
  display: flex;
  align-items: center;
}

.login-nav-bar .nav-left {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9); /* 半透明白色 */
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.login-nav-bar .nav-left:active {
  background: rgba(255, 255, 255, 1);
  transform: scale(0.95);
}
```

**登录页容器适配**：
```css
.login-container {
  min-height: 100vh;
  background: #F5F5F5; /* --bg-page */
  padding-top: calc(88rpx + env(safe-area-inset-top)); /* ⭐ 必须留出导航栏高度 */
}
```

#### 1.4 平台独立运行与风格统一 ⭐

**核心原则**：
- H5、App、小程序**各自在各自平台独立运行**，不需要跨端
- **实现方式可以不同**（H5用自定义导航栏，App可用原生导航栏）
- **视觉效果必须一致**（标题字号、返回按钮样式、背景色相同）

**App端示例（可选使用原生导航栏）**：

在`pages.json`中配置：
```json
{
  "path": "pages/room/detail",
  "style": {
    "navigationBarTitleText": "直播详情",
    "navigationBarBackgroundColor": "#FFFFFF",
    "navigationBarTextStyle": "black",
    "enablePullDownRefresh": false
  }
}
```

**H5端示例（使用自定义导航栏）**：

```vue
<template>
  <view class="page">
    <!-- H5端在浏览器中独立运行，使用自定义导航栏 -->
    <view class="nav-bar custom-nav" :style="{ paddingTop: statusBarHeight + 'px' }">
      <!-- 导航栏内容 -->
    </view>
    <view class="page-content">
      <!-- 页面内容 -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const statusBarHeight = ref(0);

onMounted(() => {
  // H5端在浏览器中运行，无状态栏
  // #ifdef H5
  statusBarHeight.value = 0;
  // #endif
  
  // App端在原生环境中运行，获取状态栏高度
  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;
  // #endif
});
</script>
```

#### 1.5 导航栏自检清单（⭐ 输出时必须检查）

- [ ] 导航栏类型是否符合页面类型（参考1.1映射表）
- [ ] 是否添加安全区适配（`env(safe-area-inset-top)`）
- [ ] 页面容器是否留出导航栏高度（`padding-top`）
- [ ] 返回按钮是否有按压反馈（`:active`伪类）
- [ ] 标题是否居中且字号符合规范（32rpx）
- [ ] H5/App/小程序各自独立运行，UI风格是否统一（配色/字号/按钮样式相同）
- [ ] 登录页导航栏是否透明背景（不遮挡登录页渐变）

---

### 2. 底部TabBar规范

**固定规范**（所有Tab页面共用）：
```css
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 999;
  height: 100rpx; /* --tabbar-height */
  background: #FFFFFF; /* --bg-card */
  border-top: 1rpx solid #F0F0F0; /* --border-light */
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding-bottom: env(safe-area-inset-bottom); /* ⭐ 底部安全区（必须） */
}

.tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.tabbar-icon {
  width: 48rpx; /* --icon-md */
  height: 48rpx;
}

.tabbar-text {
  font-size: 20rpx; /* --font-size-tiny */
  color: #8C8C8C; /* --text-tertiary */
}

.tabbar-item.active .tabbar-text {
  color: #2E5C8A; /* --primary */
  font-weight: 500; /* --font-weight-medium */
}
```

**页面容器适配**（⭐ 必须）：
```css
/* 有TabBar的页面，内容区必须留出底部空间 */
.page-with-tabbar {
  padding-bottom: calc(100rpx + env(safe-area-inset-bottom));
}
```

---

### 3. 空状态组件规范（Empty State）

**适用场景**：列表无数据、搜索无结果、网络错误、权限不足

**标准结构**：
```vue
<view class="empty-state">
  <!-- 图标 -->
  <image class="empty-icon" src="/static/empty/no-data.png" mode="aspectFit"></image>
  
  <!-- 主文案 -->
  <text class="empty-title">暂无直播</text>
  
  <!-- 辅助文案（可选） -->
  <text class="empty-desc">换个时间再来看看吧</text>
  
  <!-- 操作按钮（可选） -->
  <button class="empty-button" @tap="handleRetry">重新加载</button>
</view>
```

**样式规范**：
```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 32rpx; /* --spacing-xxl */
  min-height: 400rpx;
}

.empty-icon {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 24rpx; /* --spacing-xl */
  opacity: 0.6;
}

.empty-title {
  font-size: 28rpx; /* --font-size-base */
  color: #595959; /* --text-secondary */
  font-weight: 500; /* --font-weight-medium */
  margin-bottom: 8rpx; /* --spacing-xs */
}

.empty-desc {
  font-size: 24rpx; /* --font-size-mini */
  color: #8C8C8C; /* --text-tertiary */
  margin-bottom: 32rpx; /* --spacing-xxl */
}

.empty-button {
  width: 240rpx;
  height: 72rpx; /* --btn-height-md */
  background: transparent;
  border: 1rpx solid #2E5C8A; /* --primary */
  color: #2E5C8A;
  border-radius: 12rpx; /* --radius-sm */
  font-size: 28rpx; /* --font-size-base */
}

.empty-button:active {
  background: #E8F0F8; /* --primary-lighter */
}
```

---

### 4. 加载状态组件规范（Loading）

**全屏加载**（页面首次加载）：
```vue
<view class="loading-fullscreen">
  <uni-loading type="spinner" size="48"></uni-loading>
  <text class="loading-text">加载中...</text>
</view>
```

**局部加载**（下拉刷新/上拉加载）：
```vue
<view class="loading-inline">
  <uni-loading type="spinner" size="32"></uni-loading>
  <text class="loading-text">加载更多...</text>
</view>
```

**样式规范**：
```css
.loading-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #F5F5F5; /* --bg-page */
  z-index: 9999;
}

.loading-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx; /* --spacing-xxl */
  gap: 12rpx; /* --spacing-sm */
}

.loading-text {
  font-size: 24rpx; /* --font-size-mini */
  color: #8C8C8C; /* --text-tertiary */
  margin-top: 16rpx; /* --spacing-md */
}
```

---

## 📱 场景识别与规则选择（必须先执行）

开始改代码前，必须先识别页面场景；【改动摘要第 1 条】必须写明：
- 判定为哪种场景（PLAY_PAGE / LIST_PAGE / LOGIN_PAGE等）
- 导航栏类型（标准导航栏 / 自定义导航栏 / 无导航栏）
- 本次启用的规则集合（Base + 对应 Profile）

### 场景判定表（命中任意特征即可）

| 场景代号 | 场景名称 | 关键特征 | 导航栏类型 | 优先级 |
|---------|---------|---------|-----------|--------|
| PLAY_PAGE | 播放/直播页 | 播放器 + 医生信息 + Tab切换 | 浮动返回按钮 | P0 |
| LIST_PAGE | 列表/首页 | 顶部Tab分类 + 卡片列表 + 底部Tabbar | 无导航栏 | P0 |
| MY_PAGE | 我的页面 | 登录引导 + 功能网格 + 设置 | 无导航栏 | P0 |
| LOGIN_PAGE | 登录页 | Logo + 输入框 + 登录按钮 | 自定义导航栏 | P1 |
| DETAIL_PAGE | 详情页 | 医生详情/直播详情 + 基本信息 | 详情导航栏 | P1 |
| CREATE_PAGE | 创建/编辑页 | 表单 + 媒体上传 + 保存按钮 | 表单导航栏 | P2 |
| EMPTY_PAGE | 空状态页 | 空图标 + 提示文案 + 引导按钮 | 标准导航栏 | P2 |
| SETTING_PAGE | 设置页 | 列表式选项 + 开关/跳转箭头 | 标准导航栏 | P2 |
| MESSAGE_PAGE | 消息页 | 消息列表 + 时间戳 + 未读标识 | 标准导航栏 | P2 |
| SEARCH_PAGE | 搜索页 | 搜索框 + 历史/热门 + 结果列表 | 搜索导航栏 | P2 |

---

## 🔑 Profile D：LOGIN_PAGE（登录页）

### 目标
- **品牌识别强**：Logo+标题居中，配色符合医学场景
- **输入体验好**：输入框高度72rpx，圆角12rpx，边框清晰
- **按钮层级明确**：主按钮（登录）88rpx高，第三方登录56rpx高
- **安全感提示**：测试账号提示背景色浅黄，圆角8rpx
- **导航栏特殊**：透明背景，仅返回按钮，与其他页面统一按钮样式

### 导航栏规范（⭐ 特殊处理）

**登录页导航栏特点**：
- 背景透明（不遮挡登录页渐变背景）
- 仅左侧返回按钮，无标题
- 返回按钮样式与标准导航栏一致（64rpx圆形，浅灰背景）
- 必须有安全区适配（`padding-top: env(safe-area-inset-top)`）

**结构**：
```vue
<view class="login-nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
  <view class="nav-left" @tap="goBack">
    <uni-icons type="left" size="20" color="#1A1A1A"></uni-icons>
  </view>
</view>
```

**样式**：
```css
.login-nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  background: transparent; /* 透明背景 */
  height: 88rpx; /* --navbar-height */
  padding-left: 32rpx; /* --spacing-xxl */
  padding-top: env(safe-area-inset-top); /* 安全区适配 */
  display: flex;
  align-items: center;
}

.login-nav-bar .nav-left {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9); /* 半透明白色 */
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.login-nav-bar .nav-left:active {
  background: rgba(255, 255, 255, 1); /* 按压时不透明 */
  transform: scale(0.95);
}
```

**页面容器适配**（⭐ 必须）：
```css
.login-container {
  min-height: 100vh;
  background: #F5F5F5; /* --bg-page */
  padding-top: calc(88rpx + env(safe-area-inset-top)); /* 导航栏高度 */
}
```

### 强制执行顺序
1. **导航栏**：透明背景，仅返回按钮，安全区适配
2. Logo区：120rpx × 120rpx，圆角24rpx，背景主色渐变
3. 标题："直播SaaS平台"，40rpx粗体，主色
4. 副标题："医学直播专业平台"，26rpx灰色
5. 输入框：左图标，placeholder 灰色，focus态边框主色
6. 验证码：输入框70%宽，刷新按钮30%宽，同行
7. 登录按钮：宽度100%，高度88rpx，主色，圆角12rpx
8. 第三方登录：灰色描边按钮，图标+文字，行高56rpx

（完整LOGIN_PAGE规范请参考原文档）

---

## 🗂️ Profile E：EMPTY_PAGE / SETTING_PAGE（空状态/设置页）

### 适用场景
- **空状态页**：外观设置（暂无内容）、收藏列表（空）、消息中心（空）
- **设置页**：账号设置、隐私设置、通用设置

### 目标
- **导航栏统一**：使用标准导航栏（返回 + 标题）
- **空态友好**：图标清晰、文案温暖、引导明确
- **设置项对齐**：列表式布局，左文字+右操作，分割线清晰

### 导航栏规范（⭐ 必须）

**类型**：标准导航栏（参考《全局组件规范 - 1.2》）

**结构**：
```vue
<view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
  <view class="nav-left" @tap="goBack">
    <uni-icons type="left" size="20" color="#1A1A1A"></uni-icons>
  </view>
  <view class="nav-center">
    <text class="nav-title">外观设置</text>
  </view>
  <view class="nav-right"></view> <!-- 占位，保持居中 -->
</view>
```

### 空状态页规范

**布局**：
```vue
<view class="page-container">
  <!-- 标准导航栏 -->
  <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
    <!-- 导航栏内容 -->
  </view>
  
  <!-- 空状态组件 -->
  <view class="empty-state">
    <image class="empty-icon" src="/static/empty/setting.png" mode="aspectFit"></image>
    <text class="empty-title">外观设置</text>
    <text class="empty-desc">昼夜模式等外观设置功能即将上线</text>
  </view>
</view>
```

**样式**：参考《全局组件规范 - 3. 空状态组件规范》

### 强制执行顺序
1. **导航栏**：标准导航栏（返回 + 标题），安全区适配
2. **页面容器**：留出导航栏高度（`padding-top`）
3. **空状态**：居中显示，图标清晰，文案温暖

---

## 📐 响应式规则（必须遵守）

### 断点定义
```css
/* 小屏手机（< 375px） */
@media (max-width: 750rpx) {
  --spacing-xxl: 24rpx;
  --font-size-h1: 36rpx;
}

/* 大屏手机/平板（>= 414px） */
@media (min-width: 828rpx) {
  --spacing-xxl: 40rpx;
}

/* iPad/平板（>= 768px） */
@media (min-width: 1536rpx) {
  .container {
    max-width: 1200rpx;
    margin: 0 auto;
  }
}
```

### 安全区适配（⭐ 必须）
```css
.navbar {
  padding-top: env(safe-area-inset-top); /* iOS刘海屏 */
}

.tabbar {
  padding-bottom: env(safe-area-inset-bottom); /* 底部Home条 */
}

.page-container {
  padding-top: calc(88rpx + env(safe-area-inset-top)); /* 导航栏 + 安全区 */
}

.page-with-tabbar {
  padding-bottom: calc(100rpx + env(safe-area-inset-bottom)); /* TabBar + 安全区 */
}
```

---

## 📱 平台独立运行与UI风格统一规范 ⭐

### 核心理念（重要）

**不是跨端运行，而是各端独立运行 + UI风格统一**

- **H5端**：在浏览器中独立运行，使用Web标准API
- **App端**：在iOS/Android原生环境中独立运行，使用uni-app原生API
- **小程序端**：在微信/支付宝等环境中独立运行，遵守平台规范
- **UI风格统一**：相同页面在不同平台上，配色、字体、间距、圆角、按钮样式**必须一致**
- **实现方式可不同**：H5用自定义导航栏，App用原生导航栏，只要**视觉效果一致**即可

### 条件编译示例（各端独立代码）

**示例1：导航栏实现（H5自定义，App原生，效果一致）**

```vue
<template>
  <view class="page">
    <!-- H5端：在浏览器中独立运行，使用自定义导航栏 -->
    <!-- #ifdef H5 -->
    <view class="nav-bar custom-nav">
      <view class="nav-left" @tap="goBack">
        <uni-icons type="left" size="20" color="#1A1A1A"></uni-icons>
      </view>
      <view class="nav-center">
        <text class="nav-title">{{ title }}</text>
      </view>
      <view class="nav-right"></view>
    </view>
    <!-- #endif -->
    
    <!-- App端：在原生环境中独立运行，使用原生导航栏（pages.json配置） -->
    <!-- #ifdef APP-PLUS -->
    <!-- 无需自定义导航栏代码，由pages.json配置原生导航栏 -->
    <!-- #endif -->
    
    <!-- 小程序端：在小程序环境中独立运行，使用原生导航栏 -->
    <!-- #ifdef MP-WEIXIN -->
    <!-- 无需自定义导航栏代码，由pages.json配置 -->
    <!-- #endif -->
    
    <view class="page-content">
      <!-- 页面内容：所有平台共用，样式一致 -->
      <button class="primary-btn">登录</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const statusBarHeight = ref(0);

onMounted(() => {
  // App端在原生环境中独立运行，获取状态栏高度
  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;
  // #endif
  
  // H5端在浏览器中独立运行，状态栏高度为0
  // #ifdef H5
  statusBarHeight.value = 0;
  // #endif
  
  // 小程序端在小程序环境中独立运行，获取状态栏高度
  // #ifdef MP-WEIXIN
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;
  // #endif
});
</script>

<style lang="scss" scoped>
/* 共用样式：所有平台使用相同的Token变量，确保UI风格一致 */
.primary-btn {
  width: 100%;
  height: 88rpx; /* --btn-height-lg */
  background: #2E5C8A; /* --primary */
  color: #FFFFFF; /* --text-inverse */
  border-radius: 12rpx; /* --radius-sm */
  font-size: 28rpx; /* --font-size-base */
  font-weight: 500; /* --font-weight-medium */
}

/* H5端特有样式（仅在浏览器中生效） */
/* #ifdef H5 */
.nav-bar.custom-nav {
  background: #FFFFFF;
  border-bottom: 1rpx solid #F0F0F0;
}
/* #endif */
</style>
```

**示例2：API调用（各端独立实现，功能一致）**

```typescript
// H5端：在浏览器环境中独立运行，使用Web Storage API
// #ifdef H5
function saveToken(token: string) {
  localStorage.setItem('auth_token', token);
}
// #endif

// App端：在原生环境中独立运行，使用uni-app Storage API
// #ifdef APP-PLUS
function saveToken(token: string) {
  uni.setStorageSync('auth_token', token);
}
// #endif

// 小程序端：在小程序环境中独立运行，使用小程序Storage API
// #ifdef MP-WEIXIN
function saveToken(token: string) {
  uni.setStorageSync('auth_token', token);
}
// #endif
```

**示例3：pages.json配置（App/小程序可用原生导航栏）**

```json
{
  "pages": [
    {
      "path": "pages/room/detail",
      "style": {
        "navigationBarTitleText": "直播详情",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black",
        
        // App端可使用原生导航栏
        // #ifdef APP-PLUS
        "app-plus": {
          "titleNView": {
            "backgroundColor": "#FFFFFF",
            "titleColor": "#1A1A1A",
            "titleSize": "32rpx"
          }
        }
        // #endif
      }
    }
  ]
}
```

---

## 📱 H5/App平台差异处理

### 条件编译示例

```vue
<template>
  <view class="page">
    <!-- H5端使用自定义导航栏 -->
    <!-- #ifdef H5 -->
    <view class="nav-bar custom-nav">
      <view class="nav-left" @tap="goBack">
        <uni-icons type="left" size="20" color="#1A1A1A"></uni-icons>
      </view>
      <view class="nav-center">
        <text class="nav-title">{{ title }}</text>
      </view>
      <view class="nav-right"></view>
    </view>
    <!-- #endif -->
    
    <!-- App端使用原生导航栏（在pages.json配置） -->
    <!-- #ifdef APP-PLUS -->
    <!-- 无需自定义导航栏 -->
    <!-- #endif -->
    
    <view class="page-content">
      <!-- 页面内容 -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const statusBarHeight = ref(0);

onMounted(() => {
  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync();
  statusBarHeight.value = systemInfo.statusBarHeight || 0;
  // #endif
  
  // #ifdef H5
  statusBarHeight.value = 0;
  // #endif
});
</script>
```

---

## ✅ 输出要求（必须遵守）

输出必须包含：

1. **改动摘要**（5~12 条，第 1 条写"场景判定 + 导航栏类型 + 启用规则"）
2. **完整可替换代码**（优先）或 diff
3. **可选增强项**（不做也行）
4. 明确声明：`<script>` 是否改动（默认必须"未改动"）
5. 如果涉及颜色/间距/字号，必须引用本文档的 Token 变量（如 `var(--primary)`），不得硬编码
6. **导航栏自检**：必须说明导航栏类型是否符合场景，是否有安全区适配
7. **响应式自检**：必须说明是否使用rpx单位，是否适配不同屏幕尺寸
8. **平台独立性与风格统一**：说明H5/App/小程序各自独立运行，UI风格是否统一（配色/字体/间距/圆角一致），如有平台特有实现必须说明理由

### 改动摘要示例（⭐ 标准格式）
```
✅ UI美化改动摘要（场景：EMPTY_PAGE - 外观设置页）

1. 场景判定：EMPTY_PAGE（空状态页），导航栏类型：标准导航栏，启用规则：Base + Profile E
2. 导航栏优化：添加标准导航栏（返回 + 标题"外观设置"），添加安全区适配env(safe-area-inset-top)
3. 页面容器：添加padding-top留出导航栏高度（88rpx + 安全区），避免内容被遮挡
4. 空状态组件：居中显示，图标200rpx，主文案28rpx，辅助文案24rpx灰色
5. 配色统一：全部使用Token变量（--primary / --bg-page / --text-secondary等）
6. 间距规范化：导航栏32rpx边距，空状态120rpx上下边距，符合spacing规范
7. 触摸反馈：返回按钮添加:active样式（缩放0.95 + 背景色变化）
8. 响应式检查：全部使用rpx单位，自动适配不同屏幕尺寸
9. 平台独立与风格统一：H5/App各自独立运行，导航栏UI风格完全一致（配色/字号/按钮样式相同，H5用自定义实现，App可用原生实现）
10. <script> 改动：仅新增statusBarHeight变量获取安全区高度，未改动业务逻辑
```

---

## 🚫 禁止项（防翻车清单）

### 内容与信息
1. ❌ 禁止为了美化而删除医生职称、医院、科室等关键信息
2. ❌ 禁止直播状态标签不清晰（颜色过浅、位置不显著）
3. ❌ 禁止为了好看而牺牲信息密度（医学场景需要快速扫读）
4. ❌ 禁止移除加载态/空态/错误态（必须有友好提示）

### 交互与触摸
5. ❌ 禁止触摸区域小于88rpx × 88rpx（尤其关注/取消关注按钮）
6. ❌ 禁止缺少按压反馈（所有可点击元素必须有`:active`样式）
7. ❌ 禁止在列表中使用`v-if`频繁切换（应使用`v-show`或虚拟滚动）

### 样式与规范
8. ❌ 禁止硬编码颜色/间距/字号（必须使用 Token 变量）
9. ❌ 禁止使用px单位（必须使用rpx自动适配）
10. ❌ 禁止导航栏高度不统一（所有页面必须88rpx）
11. ❌ 禁止同一类型页面使用不同导航栏样式（参考场景判定表）

### 安全区与响应式
12. ❌ 禁止破坏安全区适配（刘海屏/底部Home指示器）
13. ❌ 禁止顶部/底部导航栏未添加`env(safe-area-inset-*)`
14. ❌ 禁止页面容器未留出导航栏/TabBar高度

### 平台独立与风格统一
15. ❌ 禁止相同页面在H5/App/小程序端UI风格不一致（配色/字体/间距/圆角必须相同）
16. ❌ 禁止使用平台特有API未做条件编译（如`#ifdef H5` / `#ifdef APP-PLUS` / `#ifdef MP-WEIXIN`）
17. ❌ 禁止在小程序中使用不兼容的CSS属性（如`backdrop-filter`，应提供降级方案）
18. ❌ 禁止图片/视频未做懒加载（影响性能和流量）

---

## 🎯 使用方式

### 方式1：Cursor 引用（推荐）
在 Cursor 中输入：
```
@uni-app-medical-live-ui-guide-v2.md 请优化外观设置页UI，确保导航栏统一和空状态友好
```

### 方式2：页面优化标准流程
1. **识别场景**：根据场景判定表确定页面类型
2. **选择导航栏**：根据导航栏映射表选择正确类型
3. **应用规范**：使用Token变量、安全区适配、响应式设计
4. **自检清单**：导航栏/响应式/H5App一致性
5. **测试验证**：真机测试（iOS刘海屏 + Android水滴屏）

---

## 📚 参考资源

- **颜色灵感**：[Material Design - Healthcare](https://material.io/)
- **医学UI参考**：丁香医生App、春雨医生App、好大夫在线App
- **uni-app 官方**：[https://uniapp.dcloud.net.cn/](https://uniapp.dcloud.net.cn/)
- **安全区适配**：[uni-app 安全区文档](https://uniapp.dcloud.net.cn/tutorial/syntax-css.html#css-%E5%8F%98%E9%87%8F)

---

## 🔄 版本迭代记录

- **v2.0（2026-01-26 - 整合完整版）**：
  - ✅ 新增导航栏统一规范（6种类型映射表）
  - ✅ 新增全局组件规范（TopBar/TabBar/Empty/Loading完整代码）
  - ✅ 新增响应式与安全区适配规范（env()函数强制使用）
  - ✅ **纠正平台理解误区**：H5/App/小程序各自独立运行，不需要跨端，只需UI风格统一
  - ✅ 扩展场景识别（从6个扩展到10个场景）
  - ✅ 完善禁止项清单（从7条扩展到18条）
  - ✅ 新增条件编译详细示例（导航栏/API调用等）
  - ✅ 整合V1.0所有内容，形成完整规范文档

- **v1.0（2026-01-26）**：初版发布，覆盖5大核心场景（已整合到V2.0）

---

**最后提醒：此文档是"理想态规范"，用于指导AI优化现有UI，不是记录现状。每次引用时，必须先识别场景和导航栏类型，再应用对应规则，确保：**
- ✅ **导航栏类型符合场景**（参考导航栏映射表）
- ✅ **安全区完全适配**（顶部/底部使用env()函数）
- ✅ **H5/App/小程序各自独立运行，UI风格统一**（配色/字体/间距/圆角相同，实现方式可不同）
- ✅ **使用Token变量**（禁止硬编码颜色/间距/字号）
- ✅ **全部使用rpx单位**（自动适配不同屏幕尺寸）
