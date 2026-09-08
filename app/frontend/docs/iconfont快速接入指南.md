# iconfont 快速接入指南（30分钟完成版）

> 本文档是精简版，完整文档请参考：`iconfont接入实施方案.md` 和 `iconfont图标需求清单.md`

## 🎯 目标
30分钟内完成iconfont图标库的接入，替换项目中的unicode字符。

---

## ⚡ 快速上手（5步搞定）

### 步骤1：创建iconfont项目（5分钟）
1. 访问 https://www.iconfont.cn/ 并登录
2. 点击 "资源管理" → "我的项目" → "新建项目"
3. 设置：
   - 项目名称：`医学直播SaaS-移动端`
   - 前缀：`icon-`
   - Font Family：`iconfont`

### 步骤2：搜索并添加图标（10分钟）
**优先添加这些（P0必需）：**

| 分类 | 图标关键词 | 数量 | 说明 |
|------|-----------|------|------|
| ~~导航~~ | ~~home, brand, doctor, user~~ | ~~4个~~ | ⚠️ TabBar当前用图片，可不用iconfont |
| 播放 | star, share, like, arrow-down, arrow-up | 5个 | 必需 |
| 通用 | search, message, edit, setting, arrow-right | 5个 | 必需 |
| 功能 | video, eye, notification, history, bell | 5个 | 必需 |

> 💡 **说明：** TabBar图标当前使用图片方案（`/static/tabbar/*.png`），建议保持不变。
> 如需改用iconfont，请参考 [TabBar图标方案对比.md](TabBar图标方案对比.md)

**操作步骤：**
1. 在搜索框输入关键词（如 `home`）
2. 找到线性风格的图标
3. 点击"购物车"图标添加
4. 重复以上步骤添加所有图标
5. 进入购物车 → "添加至项目" → 选择刚创建的项目

**⚠️ 注意：**
- 选择**单色线性**图标（便于CSS控制颜色）
- `star` 需要两个：`icon-star-outline`（空心）和 `icon-star-filled`（实心）
- 统一图标风格（推荐Ant Design或Material Icons风格）

### 步骤3：下载并导入项目（5分钟）
1. 进入项目页面 → 点击"下载至本地"
2. 选择 **Font class** 方式
3. 解压后，复制以下文件到 `src/static/fonts/`：
   - `iconfont.css`
   - `iconfont.ttf`
   - `iconfont.woff`
   - `iconfont.woff2`

4. 修改 `iconfont.css` 第一行：
```css
/* 原始 */
@font-face {
  font-family: "iconfont";
  src: url('iconfont.woff2?t=xxx') format('woff2'),
       url('iconfont.woff?t=xxx') format('woff'),
       url('iconfont.ttf?t=xxx') format('truetype');
}

/* 改为（适配uniapp） */
@font-face {
  font-family: "iconfont";
  src: url('~@/static/fonts/iconfont.woff2') format('woff2'),
       url('~@/static/fonts/iconfont.woff') format('woff'),
       url('~@/static/fonts/iconfont.ttf') format('truetype');
}
```

### 步骤4：全局引入（2分钟）
打开 `src/App.vue`，在 `<style>` 中添加：

```vue
<style lang="scss">
/* 引入iconfont图标库 */
@import '@/static/fonts/iconfont.css';

/* ... 其他样式 */
</style>
```

### 步骤5：替换Unicode字符（8分钟）
#### 5.1 播放页面
**文件：** `src/pages/app/live/LiveView.vue`

**查找并替换（行50-65）：**

**原代码：**
```vue
<!-- 收藏 -->
<text class="action-icon-inner">{{ isFavorited ? '★' : '☆' }}</text>
<!-- 分享 -->
<text class="action-icon-inner action-icon-share">↗</text>
<!-- 点赞 -->
<text class="action-icon-inner">↑</text>
```

**替换为：**
```vue
<!-- 收藏 -->
<text class="iconfont" :class="isFavorited ? 'icon-star-filled' : 'icon-star-outline'"></text>
<!-- 分享 -->
<text class="iconfont icon-share"></text>
<!-- 点赞 -->
<text class="iconfont" :class="isLiked ? 'icon-like-filled' : 'icon-like-outline'"></text>
```

**同时修改CSS（行2082-2090）：**
```scss
.action-row .iconfont {
  font-size: 40rpx;
  color: var(--action-icon-color, #666);
  transition: color 0.2s ease;
}

.action-row .action-item.is-active .iconfont {
  color: var(--primary-color, #0F766E);
}
```

#### 5.2 验证其他页面
检查这些文件中的图标是否正常：
- `src/pages/app/tabbar/my/index.vue`（已使用iconfont）
- `src/pages/app/tabbar/home/components/SearchBar.vue`（已使用iconfont）

---

## ✅ 验证测试

### 测试1：浏览器测试
1. 创建 `test-iconfont.html`（项目根目录）：
```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="src/static/fonts/iconfont.css">
  <style>
    .iconfont { font-size: 48px; margin: 10px; }
  </style>
</head>
<body>
  <h1>图标测试</h1>
  <i class="iconfont icon-home"></i>
  <i class="iconfont icon-search"></i>
  <i class="iconfont icon-star-outline"></i>
  <i class="iconfont icon-star-filled"></i>
</body>
</html>
```

2. 用浏览器打开，检查图标是否显示

### 测试2：运行项目
```bash
# H5端
npm run dev:h5

# 微信小程序
npm run dev:mp-weixin
```

访问播放页面，检查：
- [ ] 收藏图标（空心星/实心星）
- [ ] 分享图标
- [ ] 点赞图标
- [ ] 图标颜色变化正常

---

## 🔧 常见问题（1分钟解决）

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 图标显示方块 | 路径错误 | 检查CSS中的url路径是否正确 |
| 图标太小/太大 | 未设置size | 添加 `font-size: XXrpx` |
| 图标颜色无法修改 | 多色图标 | 在iconfont.cn重新下载单色图标 |
| 小程序不显示 | 路径问题 | 使用在线CDN路径 |

---

## 📦 已使用的图标类名（无需修改）

项目中这些地方已正确使用iconfont：
```
✅ icon-search       // 搜索
✅ icon-xiaoxi       // 消息
✅ icon-edit         // 编辑
✅ icon-video        // 视频
✅ icon-add          // 添加
✅ icon-arrow-right  // 右箭头
✅ icon-setting      // 设置
✅ icon-eye          // 眼睛
✅ icon-more         // 更多
✅ icon-user         // 用户
```

**注意：** 在iconfont.cn添加图标时，确保使用这些相同的名称。

---

## 📚 图标使用示例

### 方式1：直接使用（推荐）
```vue
<template>
  <text class="iconfont icon-home"></text>
  <text class="iconfont icon-search" style="font-size: 32rpx; color: #0F766E;"></text>
</template>
```

### 方式2：使用AppIcon组件
```vue
<template>
  <AppIcon name="home" size="32" color="primary" />
  <AppIcon name="star" size="40" color="#FF6B6B" @click="handleClick" />
</template>

<script setup lang="ts">
import AppIcon from '@/components/shared/AppIcon.vue';
</script>
```

### 方式3：动态切换
```vue
<template>
  <text 
    class="iconfont" 
    :class="isFavorited ? 'icon-star-filled' : 'icon-star-outline'"
  ></text>
</template>

<script setup lang="ts">
import { ref } from 'vue';
const isFavorited = ref(false);
</script>
```

---

## 🎨 推荐图标库

在iconfont.cn搜索时，推荐使用这些图标库：
1. **Ant Design Icons**（最推荐，风格统一）
2. **Material Icons**（Google官方，质量高）
3. **Feather Icons**（极简风格）
4. **Remix Icon**（现代设计）

---

## 📋 下一步

接入完成后，建议：
1. ✅ 浏览完整文档：`docs/iconfont图标需求清单.md`
2. ✅ 按需添加P1、P2优先级图标
3. ✅ 更新项目文档，记录图标库版本
4. ✅ 定期同步iconfont.cn项目

---

## 📞 技术支持

- **iconfont官网：** https://www.iconfont.cn/
- **帮助文档：** https://www.iconfont.cn/help/
- **项目issue：** 详见项目README.md

---

**快速指南版本：** v1.0  
**最后更新：** 2026-03-04  
**预计完成时间：** 30分钟  
**难度等级：** ⭐⭐☆☆☆（简单）

---

## ✨ 效果对比

### 替换前（Unicode字符）
```
收藏: ★ ☆
分享: ↗
点赞: ↑
```
- ❌ 样式不统一
- ❌ 尺寸难控制
- ❌ 跨平台兼容性差

### 替换后（iconfont）
```
收藏: icon-star-filled icon-star-outline
分享: icon-share
点赞: icon-like
```
- ✅ 专业美观
- ✅ 尺寸灵活
- ✅ 颜色可控
- ✅ 跨平台兼容

---

**祝接入顺利！🎉**
