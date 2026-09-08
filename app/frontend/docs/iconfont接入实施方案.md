# iconfont 图标库接入实施方案

## 一、接入步骤（详细版）

### 步骤1：在 iconfont.cn 创建项目

#### 1.1 注册登录
1. 访问 https://www.iconfont.cn/
2. 使用GitHub/微信/支付宝账号登录

#### 1.2 创建项目
1. 点击顶部"资源管理" → "我的项目"
2. 点击"新建项目"
3. 填写项目信息：
   - **项目名称：** 医学直播SaaS平台-移动端
   - **前缀：** `icon-`
   - **FontClass/Symbol 前缀：** `icon-`
   - **Font Family：** `iconfont`
   - **描述：** 医学直播平台移动端图标库

#### 1.3 项目设置（重要）
进入项目设置页面，配置：
- ✅ **生成方式：** Font class（推荐）
- ✅ **字体格式：** TTF + WOFF + WOFF2（勾选全部）
- ✅ **是否压缩：** 是
- ✅ **是否去色：** 是（统一单色图标，便于CSS控制颜色）

---

### 步骤2：搜索并添加图标

#### 2.1 优先级P0图标（必选）

**底部导航栏（5个）：**
```
⚠️ 说明：当前项目TabBar使用图片方案（/static/tabbar/*.png）
可选方案：
1. 保持图片方案（推荐）- 视觉效果更好，无需改动
2. 改用iconfont方案 - 性能更优，需改造CustomTabBar.vue组件

如选择iconfont方案，搜索关键词：
home, brand, building, doctor, user, add, plus
推荐图标库：Ant Design, Material Icons, Feather
```

**播放页面（8个）：**
```
搜索关键词：star, favorite, share, like, thumbs-up, arrow-down, arrow-up
特别注意：star 需要两个状态（空心outline + 实心filled）
```

**我的页面（10个）：**
```
搜索关键词：edit, video, setting, eye, arrow-right, notification, history, bell
```

**首页（6个）：**
```
搜索关键词：search, message, play, live, clock, calendar
```

#### 2.2 添加图标操作
每个图标：
1. 搜索关键词（支持中英文）
2. 找到合适的图标（建议选择线性风格）
3. 点击"购物车"图标
4. 在购物车中点击"添加至项目" → 选择刚创建的项目

**批量操作技巧：**
- 可以先将所有图标加入购物车
- 统一添加到项目
- 统一修改图标名称（去除前缀、统一命名规范）

#### 2.3 图标命名规范
示例：
```
✅ 推荐命名：
icon-home
icon-search
icon-star-outline  （空心星）
icon-star-filled   （实心星）
icon-arrow-right

❌ 避免命名：
icon-home-line-icon
icon_search_1
iconStar
```

---

### 步骤3：下载并集成图标库

#### 3.1 下载图标
1. 进入项目页面
2. 点击右上角"下载至本地"
3. 选择 **Font class** 方式
4. 下载生成的 zip 文件

#### 3.2 解压文件
下载后的文件结构：
```
iconfont/
├── iconfont.css          # CSS文件（核心）
├── iconfont.eot          # IE兼容（可选）
├── iconfont.svg          # SVG格式（可选）
├── iconfont.ttf          # TrueType字体
├── iconfont.woff         # Web字体
├── iconfont.woff2        # Web字体（压缩，推荐）
├── demo_index.html       # 图标演示页面
└── demo.css              # 演示样式
```

#### 3.3 复制文件到项目
将以下文件复制到 `src/static/fonts/` 目录：
```bash
✅ 必需文件：
- iconfont.css
- iconfont.ttf
- iconfont.woff
- iconfont.woff2

⚠️ 可选文件（如需兼容IE）：
- iconfont.eot
- iconfont.svg
```

#### 3.4 修改 CSS 文件路径
打开 `iconfont.css`，修改字体文件路径：

**原始代码：**
```css
@font-face {
  font-family: "iconfont";
  src: url('iconfont.eot?t=1234567890');
  src: url('iconfont.eot?t=1234567890#iefix') format('embedded-opentype'),
       url('iconfont.woff2?t=1234567890') format('woff2'),
       url('iconfont.woff?t=1234567890') format('woff'),
       url('iconfont.ttf?t=1234567890') format('truetype'),
       url('iconfont.svg?t=1234567890#iconfont') format('svg');
}
```

**修改为（uniapp兼容）：**
```css
@font-face {
  font-family: "iconfont";
  src: url('~@/static/fonts/iconfont.woff2') format('woff2'),
       url('~@/static/fonts/iconfont.woff') format('woff'),
       url('~@/static/fonts/iconfont.ttf') format('truetype');
}

.iconfont {
  font-family: "iconfont" !important;
  font-size: 16px;
  font-style: normal;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 图标类名（保持iconfont.cn生成的原样） */
.icon-home:before { content: "\e600"; }
.icon-search:before { content: "\e601"; }
/* ... 其他图标 */
```

---

### 步骤4：在项目中引入图标库

#### 4.1 在 App.vue 中全局引入
打开 `src/App.vue`，在 `<style>` 标签中添加：

```vue
<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app';
// ... 其他导入
</script>

<style lang="scss">
/* 引入iconfont图标库 */
@import '@/static/fonts/iconfont.css';

/* 全局样式 */
/* ... 其他样式 */
</style>
```

#### 4.2 验证引入是否成功
创建测试页面 `test-iconfont.html`（项目根目录）：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>iconfont 图标测试</title>
  <link rel="stylesheet" href="src/static/fonts/iconfont.css">
  <style>
    body { padding: 40px; font-family: sans-serif; }
    .icon-test { font-size: 32px; margin: 20px; }
    .icon-demo { display: inline-block; margin: 10px; text-align: center; }
    .icon-demo i { font-size: 48px; display: block; margin-bottom: 8px; }
  </style>
</head>
<body>
  <h1>iconfont 图标测试页面</h1>
  
  <h2>底部导航图标</h2>
  <div class="icon-demo">
    <i class="iconfont icon-home"></i>
    <span>首页</span>
  </div>
  <div class="icon-demo">
    <i class="iconfont icon-brand"></i>
    <span>品牌</span>
  </div>
  <div class="icon-demo">
    <i class="iconfont icon-add"></i>
    <span>创建</span>
  </div>
  <div class="icon-demo">
    <i class="iconfont icon-expert"></i>
    <span>专家</span>
  </div>
  <div class="icon-demo">
    <i class="iconfont icon-user"></i>
    <span>我的</span>
  </div>
  
  <h2>播放页图标</h2>
  <div class="icon-demo">
    <i class="iconfont icon-star"></i>
    <span>收藏</span>
  </div>
  <div class="icon-demo">
    <i class="iconfont icon-share"></i>
    <span>分享</span>
  </div>
  <div class="icon-demo">
    <i class="iconfont icon-like"></i>
    <span>点赞</span>
  </div>
  
  <script>
    // 检查图标是否加载成功
    window.onload = function() {
      const icons = document.querySelectorAll('.iconfont');
      const loaded = Array.from(icons).some(icon => {
        const computed = getComputedStyle(icon);
        return computed.fontFamily.includes('iconfont');
      });
      
      if (loaded) {
        console.log('✅ iconfont 图标库加载成功');
      } else {
        console.error('❌ iconfont 图标库加载失败');
      }
    };
  </script>
</body>
</html>
```

**测试步骤：**
1. 用浏览器打开 `test-iconfont.html`
2. 检查图标是否正常显示
3. 打开浏览器控制台，查看是否有错误
4. 如果看到图标，说明引入成功！

---

### 步骤5：替换现有的 Unicode 字符

#### 5.1 播放页面图标替换

**文件：** `src/pages/app/live/LiveView.vue`

**原代码（行50-62）：**
```vue
<view class="action-icon-wrap">
  <text class="action-icon-inner">{{ isFavorited ? '★' : '☆' }}</text>
</view>
<text class="action-label">收藏</text>

<view class="action-icon-wrap">
  <text class="action-icon-inner action-icon-share">↗</text>
</view>
<text class="action-label">分享</text>

<view class="action-icon-wrap">
  <text class="action-icon-inner">↑</text>
</view>
<text class="action-label">点赞</text>
```

**替换为：**
```vue
<view class="action-icon-wrap">
  <text class="iconfont" :class="isFavorited ? 'icon-star-filled' : 'icon-star-outline'"></text>
</view>
<text class="action-label">收藏</text>

<view class="action-icon-wrap">
  <text class="iconfont icon-share"></text>
</view>
<text class="action-label">分享</text>

<view class="action-icon-wrap">
  <text class="iconfont" :class="isLiked ? 'icon-like-filled' : 'icon-like-outline'"></text>
</view>
<text class="action-label">点赞</text>
```

**CSS调整（行2082-2090）：**
```scss
.action-row .action-icon-wrap {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.action-row .iconfont {
  font-size: 40rpx;  /* 调整图标大小 */
  color: var(--action-icon-color, #666);
  transition: color 0.2s ease;
}

.action-row .action-item.is-active .iconfont {
  color: var(--primary-color, #0F766E);
}
```

#### 5.2 "我的"页面图标替换

**文件：** `src/pages/app/tabbar/my/index.vue`

**示例修改：**
```vue
<!-- 原代码 -->
<text class="iconfont icon-video"></text>

<!-- 如果图标不显示，改为 -->
<text class="iconfont icon-shipin"></text>
<!-- 或 -->
<text class="iconfont icon-live"></text>
```

**注意：** 项目中已有 `icon-video` 等类名，需要确保 iconfont.cn 中的图标名称匹配。

#### 5.3 首页搜索栏图标验证

**文件：** `src/pages/app/tabbar/home/components/SearchBar.vue`

**检查代码（行15-21）：**
```vue
<text class="search-icon iconfont icon-search"></text>
<text class="search-placeholder">搜索直播 / 医生 / 医院</text>

<!-- 消息图标 -->
<text class="message-icon iconfont icon-xiaoxi"></text>
```

**验证步骤：**
1. 确保 iconfont.cn 项目中有 `icon-search` 和 `icon-xiaoxi`（或 `icon-message`）
2. 如果图标名称不匹配，修改为实际的图标类名
3. 运行项目，检查图标是否显示

---

### 步骤6：在小程序中配置（重要）

#### 6.1 修改 project.config.json
小程序需要特殊配置字体文件路径：

```json
{
  "miniprogramRoot": "dist/dev/mp-weixin/",
  "setting": {
    "packOptions": {
      "ignore": [
        {
          "type": "file",
          "value": "src/static/fonts/iconfont.eot"
        },
        {
          "type": "file",
          "value": "src/static/fonts/iconfont.svg"
        }
      ]
    }
  }
}
```

#### 6.2 确保字体文件在正确目录
小程序打包后，字体文件应该在：
```
dist/dev/mp-weixin/static/fonts/
├── iconfont.css
├── iconfont.ttf
├── iconfont.woff
└── iconfont.woff2
```

---

### 步骤7：使用 AppIcon 组件（推荐）

项目中已有封装好的 `AppIcon` 组件，可以直接使用：

#### 7.1 使用示例
```vue
<template>
  <view class="demo">
    <!-- 基础用法 -->
    <AppIcon name="home" size="32" />
    
    <!-- 自定义颜色（预设） -->
    <AppIcon name="star" color="primary" />
    
    <!-- 自定义颜色（HEX） -->
    <AppIcon name="heart" color="#FF6B6B" />
    
    <!-- 带点击事件 -->
    <AppIcon name="share" size="40" @click="handleShare" />
    
    <!-- 动态切换图标 -->
    <AppIcon 
      :name="isFavorited ? 'star-filled' : 'star-outline'" 
      color="primary" 
    />
  </view>
</template>

<script setup lang="ts">
import AppIcon from '@/components/shared/AppIcon.vue';

const isFavorited = ref(false);

function handleShare() {
  console.log('分享按钮被点击');
}
</script>
```

#### 7.2 AppIcon 组件说明
- **位置：** `src/components/shared/AppIcon.vue`
- **Props：**
  - `name`：图标名称（不含 `icon-` 前缀）
  - `size`：图标大小（数字单位rpx，字符串保持原样）
  - `color`：颜色（支持预设：primary、success、warning、danger，或HEX值）
- **事件：** `@click` 点击事件

---

## 二、常见问题解决

### Q1：图标不显示，显示方块
**原因：** 字体文件路径错误或未加载

**解决方案：**
1. 检查 `iconfont.css` 中的路径是否正确
2. 确保字体文件在 `src/static/fonts/` 目录
3. 清除缓存重新编译：
   ```bash
   # 停止开发服务器
   # 删除 dist 目录
   rm -rf dist
   # 重新运行
   npm run dev:h5
   ```

### Q2：小程序中图标不显示
**原因：** 小程序不支持本地字体文件加载（部分平台）

**解决方案：**
1. **方案A：使用在线字体（推荐）**
   ```css
   @font-face {
     font-family: "iconfont";
     src: url('https://at.alicdn.com/t/font_xxx.woff2') format('woff2'),
          url('https://at.alicdn.com/t/font_xxx.woff') format('woff');
   }
   ```
   
2. **方案B：转为 base64 内联（不推荐，文件会很大）**
   ```bash
   # 使用工具转换
   npm install -g base64-encode-cli
   base64-encode iconfont.woff2 > iconfont-base64.txt
   ```

### Q3：图标颜色无法修改
**原因：** 图标是多色图标（colored），不是单色图标

**解决方案：**
1. 返回 iconfont.cn
2. 编辑图标 → 去色
3. 重新下载图标库

### Q4：部分图标名称冲突
**原因：** 项目中已有同名类名

**解决方案：**
1. 修改 iconfont 项目前缀为 `iconfont-` 或 `if-`
2. 或者在代码中使用命名空间：
   ```vue
   <text class="iconfont iconfont-home"></text>
   ```

### Q5：图标加载慢
**原因：** 字体文件较大

**解决方案：**
1. 只下载需要的图标（避免全量下载）
2. 使用 woff2 格式（压缩率更高）
3. 考虑 CDN 加载
4. 分包：核心图标 + 扩展图标

---

## 三、图标库维护

### 3.1 新增图标流程
1. 访问 iconfont.cn 项目
2. 搜索并添加新图标
3. 统一图标命名规则
4. 重新下载图标库
5. 替换 `src/static/fonts/` 中的文件
6. 更新图标文档 `docs/iconfont图标需求清单.md`

### 3.2 图标更新记录
建议创建 `src/static/fonts/CHANGELOG.md`：

```markdown
# iconfont 图标库更新日志

## v1.0.0 (2026-03-04)
### 新增
- 底部导航图标：home, brand, add, expert, user
- 播放页图标：star-outline, star-filled, share, like
- 通用图标：search, message, arrow-right

### 总计
- 图标数量：32个
- 文件大小：iconfont.woff2 (12KB)

---

## v1.1.0 (待定)
### 计划新增
- 视频播放器图标
- 社交互动图标
```

---

## 四、性能优化建议

### 4.1 按需加载（可选）
如果图标库较大（>50个），可考虑分包：

**核心图标（core）：**
- 底部导航
- 播放页面
- 常用操作

**扩展图标（extended）：**
- 设置页面
- 数据分析
- 管理后台

**实现方式：**
```typescript
// src/utils/iconLoader.ts
export async function loadExtendedIcons() {
  if (!window.__ICONFONT_EXTENDED_LOADED__) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/fonts/iconfont-extended.css';
    document.head.appendChild(link);
    window.__ICONFONT_EXTENDED_LOADED__ = true;
  }
}
```

### 4.2 使用 SVG Sprite（高级方案）
对于需要精细控制的图标（多色、动画），可以使用 SVG：

```vue
<!-- src/components/SvgIcon.vue -->
<template>
  <svg class="svg-icon" aria-hidden="true">
    <use :xlink:href="`#icon-${name}`"></use>
  </svg>
</template>

<script setup lang="ts">
defineProps<{ name: string }>();
</script>

<style scoped>
.svg-icon {
  width: 1em;
  height: 1em;
  fill: currentColor;
}
</style>
```

---

## 五、检查清单

### 接入前检查
- [ ] 确认 iconfont.cn 账号已注册
- [ ] 确认图标需求清单（参考 `docs/iconfont图标需求清单.md`）
- [ ] 准备好图标搜索关键词

### 接入中检查
- [ ] 图标项目已创建，命名规范设置正确
- [ ] 已添加所有P0优先级图标
- [ ] 图标命名符合规范（icon-xxx）
- [ ] 已下载图标库（Font class方式）
- [ ] 字体文件已复制到 `src/static/fonts/`
- [ ] CSS文件路径已修改（适配uniapp）
- [ ] 已在 `App.vue` 中全局引入
- [ ] 测试页面图标显示正常

### 接入后检查
- [ ] H5端图标显示正常
- [ ] 小程序端图标显示正常
- [ ] App端图标显示正常
- [ ] 图标颜色可以通过CSS修改
- [ ] 图标大小响应式正常
- [ ] 已替换播放页面的Unicode字符
- [ ] 已替换"我的"页面的Unicode字符
- [ ] 已更新项目文档
- [ ] 已提交代码到版本库

---

## 六、技术支持

### 官方资源
- **iconfont帮助文档：** https://www.iconfont.cn/help/
- **uniapp字体图标文档：** https://uniapp.dcloud.net.cn/component/text.html#字体图标
- **CSS @font-face：** https://developer.mozilla.org/zh-CN/docs/Web/CSS/@font-face

### 社区资源
- **阿里图标库：** https://www.iconfont.cn/collections/index
- **iconfont论坛：** https://github.com/thx/iconfont
- **uni-app社区：** https://ask.dcloud.net.cn/

---

**文档版本：** v1.0  
**最后更新：** 2026-03-04  
**适用项目：** 医学直播SaaS平台-移动端  
**技术栈：** Vue3 + TypeScript + uniapp + iconfont
