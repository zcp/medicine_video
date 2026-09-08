# iconfont 图标需求清单

## 一、项目背景

当前项目使用unicode字符（如 ★☆↗↑等）作为临时图标方案，用户体验不佳。项目中已有iconfont相关代码残留，恢复使用iconfont图标库是最佳选择。

## 二、图标分类与需求清单

### 1. 底部导航栏（TabBar）- 5个图标
**优先级：P0（最高）**

> ⚠️ **重要说明：** 
> 当前项目使用**图片方案**实现TabBar（`/static/tabbar/*.png`），不使用iconfont。
> 原因：
> 1. ✅ 视觉效果更好（设计师精心设计）
> 2. ✅ 已实现，稳定运行
> 3. ✅ 支持复杂视觉效果
> 
> 如需改用iconfont，请参考：[TabBar图标方案对比.md](TabBar图标方案对比.md)

| 图标名称 | 建议名称 | 使用场景 | 当前方案 | 备注 |
|---------|---------|---------|---------|------|
| 首页 | `icon-home` | 底部导航-首页 | 图片 ✓ | 使用 home.png / home-active.png |
| 品牌 | `icon-brand` / `icon-building` | 底部导航-品牌专区 | 图片 ✓ | 使用 brand.png / brand-active.png |
| 创建/发起 | `icon-add` / `icon-plus-circle` | 底部导航-中间按钮 | 胶囊样式 ✓ | 代码实现，无需图标 |
| 专家 | `icon-expert` / `icon-doctor` | 底部导航-专家专题 | 图片 ✓ | 使用 expert.png / expert-active.png |
| 我的 | `icon-user` / `icon-my` | 底部导航-个人中心 | 图片 ✓ | 使用 my.png / my-active.png |

**文件位置：** `src/components/app/CustomTabBar.vue`
**图片位置：** `src/static/tabbar/`

---

### 2. 首页（Home）- 10个图标
**优先级：P0**

| 图标名称 | 建议名称 | 使用场景 | 当前实现 | 备注 |
|---------|---------|---------|---------|------|
| 搜索 | `icon-search` | 顶部搜索框 | `icon-search` | 已使用，需确认 |
| 消息/通知 | `icon-xiaoxi` / `icon-message` | 顶部右侧消息入口 | `icon-xiaoxi` | 已使用，需确认 |
| 搜索建议 | `icon-search-history` | 搜索历史记录 | 无 | 可选 |
| 认证标记 | `icon-verified` / `icon-badge` | 专家认证标识 | ✓（文字） | 蓝V认证图标 |
| 播放 | `icon-play` | 视频封面播放图标 | 无 | 三角播放图标 |
| 正在直播 | `icon-live` | 直播中状态标识 | 无 | 一般为红点或直播标签 |
| 预告 | `icon-calendar` / `icon-schedule` | 即将开播标识 | 无 | 日历或钟表图标 |
| 观看人数 | `icon-eye` / `icon-view` | 观看数统计 | 无 | 眼睛图标 |
| 时长 | `icon-time` / `icon-clock` | 直播/回放时长 | 无 | 钟表图标 |
| 更多分类 | `icon-more-grid` / `icon-category` | 查看全部科室 | 无 | 网格或列表图标 |

**文件位置：**
- `src/pages/app/tabbar/home/index.vue`
- `src/pages/app/tabbar/home/components/SearchBar.vue`
- `src/pages/app/tabbar/home/components/RoomCardGrid.vue`

---

### 3. 播放页面（LiveView）- 18个图标
**优先级：P0**

| 图标名称 | 建议名称 | 使用场景 | 当前实现 | 备注 |
|---------|---------|---------|---------|------|
| 收藏 | `icon-star` / `icon-favorite` | 收藏功能 | ★☆（unicode） | 空心/实心两种状态 |
| 分享 | `icon-share` | 分享功能 | ↗（unicode） | 标准分享图标 |
| 点赞 | `icon-like` / `icon-thumbs-up` | 点赞功能 | ↑（unicode） | 点赞图标 |
| 返回 | `icon-back` / `icon-arrow-left` | 顶部返回按钮 | 无 | 左箭头 |
| 展开 | `icon-arrow-down` | 标题展开 | ▼（unicode） | 下箭头 |
| 收起 | `icon-arrow-up` | 标题收起 | ▲（unicode） | 上箭头 |
| 播放 | `icon-play-circle` | 视频播放 | 原生控件 | 播放按钮 |
| 暂停 | `icon-pause` | 视频暂停 | 原生控件 | 暂停按钮 |
| 全屏 | `icon-fullscreen` | 全屏播放 | 原生控件 | 全屏图标 |
| 音量 | `icon-volume` / `icon-sound` | 音量控制 | 原生控件 | 音量图标 |
| 快进 | `icon-forward` | 快进15秒 | 无 | 可选 |
| 快退 | `icon-backward` | 快退15秒 | 无 | 可选 |
| 清晰度 | `icon-quality` / `icon-hd` | 清晰度选择 | 无 | HD图标 |
| 倍速 | `icon-speed` | 倍速播放 | 无 | 1x图标 |
| 弹幕 | `icon-danmu` / `icon-comment` | 弹幕开关 | 无 | 气泡图标 |
| 发送 | `icon-send` | 聊天消息发送 | 无 | 发送图标 |
| 表情 | `icon-emoji` / `icon-smile` | 表情选择器 | 无 | 笑脸图标 |
| 关注 | `icon-follow` / `icon-follow-add` | 关注专家 | + 关注（文字） | 加号或+用户图标 |

**文件位置：** `src/pages/app/live/LiveView.vue`

---

### 4. "我的"页面（My）- 15个图标
**优先级：P0**

| 图标名称 | 建议名称 | 使用场景 | 当前实现 | 备注 |
|---------|---------|---------|---------|------|
| 编辑 | `icon-edit` | 编辑个人资料 | `icon-edit` | 已使用，需确认 |
| 收藏 | `icon-star` / `icon-collection` | 我的收藏 | 无 | 星标图标 |
| 关注 | `icon-heart` / `icon-follow` | 我的关注 | 无 | 爱心或关注图标 |
| 历史 | `icon-history` / `icon-clock-circle` | 观看历史 | 无 | 历史记录图标 |
| 订阅 | `icon-bell` / `icon-subscribe` | 我的订阅 | 无 | 铃铛图标 |
| 通知 | `icon-notification` / `icon-message` | 通知消息 | 无 | 消息图标 |
| 直播 | `icon-video` | 我的直播 | `icon-video` | 已使用，需确认 |
| 创建 | `icon-add` | 创建直播 | `icon-add` | 已使用，需确认 |
| 设置 | `icon-setting` / `icon-gear` | 外观设置 | `icon-setting` | 已使用，需确认 |
| 流量提醒 | `icon-eye` / `icon-data` | 流量提醒开关 | `icon-eye` | 已使用，需确认 |
| 关于 | `icon-info` / `icon-more` | 关于我们 | `icon-more` | 已使用，需确认 |
| 隐私 | `icon-user` / `icon-lock` | 隐私政策 | `icon-user` | 已使用，需确认 |
| 右箭头 | `icon-arrow-right` | 菜单项跳转指示 | `icon-arrow-right` | 已使用，需确认 |
| 主播标识 | `icon-broadcast` | 主播身份 | 🎙️（emoji） | 麦克风图标 |
| 专家标识 | `icon-badge-expert` | 专家身份 | 👨‍⚕️（emoji） | 专家徽章 |

**文件位置：** `src/pages/app/tabbar/my/index.vue`

---

### 5. 品牌专区（Brand）- 5个图标
**优先级：P1**

| 图标名称 | 建议名称 | 使用场景 | 当前实现 | 备注 |
|---------|---------|---------|---------|------|
| 搜索 | `icon-search` | 搜索品牌 | 复用 | 复用首页搜索图标 |
| 排序 | `icon-sort` / `icon-filter` | 排序筛选 | 无 | 排序图标 |
| 品牌logo占位 | `icon-brand-placeholder` | 品牌无logo时占位 | 无 | 可选 |
| 右箭头 | `icon-arrow-right` | 进入品牌详情 | 复用 | 复用 |
| 网格/列表切换 | `icon-grid` / `icon-list` | 切换展示模式 | 无 | 可选 |

**文件位置：** `src/pages/app/tabbar/brand/index.vue`

---

### 6. 专家专题（Expert）- 8个图标
**优先级：P1**

| 图标名称 | 建议名称 | 使用场景 | 当前实现 | 备注 |
|---------|---------|---------|---------|------|
| 搜索 | `icon-search` | 搜索专家 | 复用 | 复用首页搜索图标 |
| 关注 | `icon-follow` / `icon-add-user` | 关注专家 | 无 | 加好友图标 |
| 已关注 | `icon-followed` / `icon-user-check` | 已关注状态 | 无 | 已添加图标 |
| 粉丝数 | `icon-users` / `icon-team` | 粉丝数量 | 无 | 用户群组图标 |
| 直播数 | `icon-video-camera` | 直播场次 | 无 | 摄像机图标 |
| 观看数 | `icon-eye` | 观看数量 | 复用 | 复用 |
| 电话 | `icon-phone` | 联系方式 | 无 | 可选 |
| 医院 | `icon-hospital` / `icon-building` | 所在医院 | 无 | 医院图标 |

**文件位置：** `src/pages/app/tabbar/expert/index.vue`

---

### 7. 功能性图标（通用）- 12个图标
**优先级：P1**

| 图标名称 | 建议名称 | 使用场景 | 当前实现 | 备注 |
|---------|---------|---------|---------|------|
| 加载中 | `icon-loading` | 数据加载状态 | 系统loading | 旋转圆圈 |
| 刷新 | `icon-refresh` | 下拉刷新 | 系统 | 刷新图标 |
| 错误 | `icon-error` / `icon-close-circle` | 错误提示 | ❌（emoji） | 错误图标 |
| 成功 | `icon-success` / `icon-check-circle` | 成功提示 | ✅（emoji） | 成功图标 |
| 警告 | `icon-warning` | 警告提示 | ⚠️（emoji） | 警告图标 |
| 信息 | `icon-info-circle` | 信息提示 | 无 | 信息图标 |
| 空状态 | `icon-empty` / `icon-inbox` | 空数据占位 | 无 | 空箱子图标 |
| 关闭 | `icon-close` / `icon-x` | 关闭弹窗/对话框 | ×（unicode） | 叉号 |
| 下拉 | `icon-chevron-down` | 下拉菜单 | ▼（unicode） | 下箭头 |
| 上拉 | `icon-chevron-up` | 收起菜单 | ▲（unicode） | 上箭头 |
| 更多 | `icon-more` / `icon-ellipsis` | 更多操作 | ⋮（unicode） | 三点图标 |
| 删除 | `icon-delete` / `icon-trash` | 删除功能 | 🗑️（emoji） | 垃圾桶图标 |

---

### 8. 视频播放器图标（增强）- 8个图标
**优先级：P2（可选）**

| 图标名称 | 建议名称 | 使用场景 | 备注 |
|---------|---------|---------|------|
| 锁定 | `icon-lock` | 屏幕锁定 | 锁定图标 |
| 解锁 | `icon-unlock` | 屏幕解锁 | 解锁图标 |
| 画中画 | `icon-pip` | 画中画模式 | PIP图标 |
| 截屏 | `icon-camera` | 截图功能 | 相机图标 |
| 投屏 | `icon-cast` / `icon-airplay` | 投屏功能 | 投屏图标 |
| 字幕 | `icon-subtitle` | 字幕开关 | CC图标 |
| 章节 | `icon-chapters` / `icon-list` | 章节列表 | 列表图标 |
| 下载 | `icon-download` | 下载回放 | 下载图标 |

---

### 9. 社交互动图标 - 6个图标
**优先级：P2**

| 图标名称 | 建议名称 | 使用场景 | 备注 |
|---------|---------|---------|------|
| 评论 | `icon-comment` / `icon-message-circle` | 评论功能 | 对话气泡 |
| 转发 | `icon-retweet` / `icon-share-forward` | 转发内容 | 转发图标 |
| 举报 | `icon-flag` / `icon-report` | 举报不良内容 | 旗帜图标 |
| 屏蔽 | `icon-block` / `icon-eye-off` | 屏蔽用户 | 禁止图标 |
| 私信 | `icon-mail` / `icon-send-message` | 私信功能 | 信封图标 |
| 礼物 | `icon-gift` | 送礼物 | 礼物盒图标 |

---

## 三、图标使用统计

### 按优先级分类
- **P0（必须）：** 61个图标
- **P1（重要）：** 37个图标
- **P2（可选）：** 14个图标
- **合计：** 约 **110个图标**

### 按功能分类
1. 导航类：5个
2. 操作类：25个
3. 状态类：15个
4. 社交类：10个
5. 媒体类：20个
6. 功能类：15个
7. 装饰类：20个

---

## 四、当前项目中已使用的iconfont类名

根据代码扫描，项目中已有以下iconfont类名引用：

```
icon-search        // 搜索
icon-xiaoxi        // 消息
icon-edit          // 编辑
icon-video         // 视频
icon-add           // 添加
icon-arrow-right   // 右箭头
icon-setting       // 设置
icon-eye           // 眼睛
icon-more          // 更多
icon-user          // 用户
```

**建议：** 在iconfont.cn创建项目时，优先确保这些图标名称保持一致。

---

## 五、图标文件组织建议

### 5.1 目录结构
```
src/static/fonts/
├── iconfont.css         # 图标样式文件
├── iconfont.ttf         # 字体文件
├── iconfont.woff        # Web字体文件
├── iconfont.woff2       # Web字体文件（压缩）
└── iconfont.json        # 图标配置（可选）
```

### 5.2 iconfont.css 基础结构
```css
@font-face {
  font-family: "iconfont";
  src: url('iconfont.woff2?t=1234567890') format('woff2'),
       url('iconfont.woff?t=1234567890') format('woff'),
       url('iconfont.ttf?t=1234567890') format('truetype');
}

.iconfont {
  font-family: "iconfont" !important;
  font-size: 16px;
  font-style: normal;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 各个图标的unicode映射 */
.icon-home:before { content: "\e600"; }
.icon-search:before { content: "\e601"; }
/* ... 更多图标 */
```

### 5.3 AppIcon组件增强建议

当前项目已有 `src/components/shared/AppIcon.vue` 组件，建议用法：

```vue
<!-- 基础用法 -->
<AppIcon name="search" size="32" />

<!-- 自定义颜色 -->
<AppIcon name="star" color="primary" />
<AppIcon name="heart" color="#FF6B6B" />

<!-- 带点击事件 -->
<AppIcon name="message" @click="handleClick" />
```

---

## 六、iconfont.cn 操作步骤建议

### 6.1 创建项目
1. 访问 [iconfont.cn](https://www.iconfont.cn/)
2. 登录账号
3. 创建新项目：`医学直播SaaS平台 - 移动端`
4. 设置 FontClass 前缀：`icon-`
5. 设置 Font Family：`iconfont`

### 6.2 添加图标
根据上述清单，按分类搜索并添加图标：

**P0优先添加：**
- 导航类：home, brand, add, expert, user
- 播放页：star（空心/实心）, share, like, arrow-down, arrow-up
- 通用：search, message, edit, arrow-right, setting

**搜索关键词参考：**
- 导航：`home`, `brand`, `doctor`, `user`, `profile`
- 播放：`star`, `share`, `thumbs-up`, `play`, `pause`
- 操作：`edit`, `delete`, `more`, `close`, `arrow`
- 社交：`comment`, `heart`, `follow`, `notification`
- 状态：`loading`, `success`, `error`, `warning`, `empty`

### 6.3 下载图标
1. 全选图标
2. 添加到购物车
3. 下载代码 → 选择 `Font Class` 方式
4. 解压后将文件放到 `src/static/fonts/` 目录

### 6.4 引入项目
在 `App.vue` 或主入口文件中引入：

```vue
<style>
@import '@/static/fonts/iconfont.css';
</style>
```

---

## 七、图标设计规范建议

### 7.1 尺寸规范
- 导航图标：48-56rpx
- 功能图标：32-40rpx
- 装饰图标：24-28rpx
- 最小尺寸：不小于 20rpx

### 7.2 颜色规范
- 主色：`#0F766E`（品牌绿）
- 次色：`#509CEC`（品牌蓝）
- 成功：`#28a745`
- 警告：`#ffc107`
- 危险：`#dc3545`
- 灰色：`#999999`（次要信息）
- 深灰：`#333333`（主要文字）

### 7.3 风格规范
- **风格**：线性图标（Outline）为主
- **粗细**：统一线宽 2px
- **圆角**：圆角 2px
- **填充**：重要操作可用填充图标（如已收藏、已点赞）

---

## 八、替换计划

### Phase 1：核心功能（P0）- 优先完成
- [ ] 底部导航栏图标（5个）
- [ ] 播放页面图标（收藏、分享、点赞）
- [ ] "我的"页面图标（快捷入口）
- [ ] 首页搜索和消息图标

**预计时间：** 1-2小时

### Phase 2：完善体验（P1）
- [ ] 品牌页面图标
- [ ] 专家页面图标
- [ ] 通用功能图标
- [ ] 状态提示图标

**预计时间：** 2-3小时

### Phase 3：增强功能（P2）- 可选
- [ ] 视频播放器增强图标
- [ ] 社交互动图标
- [ ] 装饰性图标

**预计时间：** 1-2小时

---

## 九、注意事项

### 9.1 兼容性
- ✅ 支持微信小程序
- ✅ 支持 H5
- ✅ 支持 App（iOS/Android）
- ⚠️ 字体文件需配置在 `project.config.json` 的 `setting.packOptions.ignore` 中避免被压缩

### 9.2 性能优化
- 只下载需要的图标，避免字体文件过大
- 使用 woff2 格式优先（体积更小）
- 考虑分包加载：核心图标 + 扩展图标

### 9.3 维护建议
- 在 iconfont.cn 保持项目同步更新
- 为每个图标添加清晰的命名和描述
- 定期清理未使用的图标
- 版本管理：每次更新记录版本号（在文件名或注释中）

---

## 十、参考资源

- **iconfont官网：** https://www.iconfont.cn/
- **阿里图标库：** https://www.iconfont.cn/collections/index
- **Material Icons：** https://fonts.google.com/icons
- **Font Awesome：** https://fontawesome.com/icons
- **Feather Icons：** https://feathericons.com/

---

## 十一、后续扩展

### 11.1 SVG图标方案
如果项目需要更精细的图标控制（多色、动画），可考虑引入 SVG 图标：
- 每个图标独立的 SVG 文件
- 使用 `<svg>` 组件或 `<image>` 标签
- 支持更丰富的样式和交互

### 11.2 图标动画
对于需要动效的图标（如点赞、收藏），可以：
- CSS transition/animation
- Lottie 动画（JSON格式）
- GIF 动图（不推荐，性能较差）

---

**文档版本：** v1.0  
**创建日期：** 2026-03-04  
**维护者：** 开发团队  
**审核状态：** 待审核
