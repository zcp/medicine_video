# 设计系统官方通用模板（通用 + 认证）

> 目的：栈无关、高实用性的执行模板。认证基线优先级最高，其他页面共享同一设计语言。

---

## 优先级与范围
- 最高优先级：认证基线，见 docs/登录注册找回-统一设计语言与自适配方案.md。
- 适用：ADMIN_TABLE / ADMIN_DETAIL / ADMIN_FORM / ADMIN_CONFIG / ADMIN_WORKBENCH / LIVE_VIEW / CONTENT 以及所有认证流（登录/注册/找回/一键/SSO）。
- 设计语言必须全局一致；布局模式可随页面目标变化。

## 角色（栈无关）
你负责在不改业务逻辑前提下统一密度、对齐、层级、响应式。
- 框架无关：React/Vue/Svelte/Angular/原生均可；沿用现有 UI 库，不强行换栈。
- 跨端：默认 Web/H5；若需小程序/App，映射为等价原生组件，不改变交互语义。

## 逻辑护栏（必须遵守）
- 默认只改模板/样式；不改逻辑/状态/数据流/事件/API/权限。
- 若 UI 需改逻辑，先给纯样式替代；仍需改时明确说明改动与风险。

## 响应式与容器基线（来自认证文档，全球适用）
- Mobile <480：width 92vw，max-width 420，居中，无横向滚动。
- Tablet 480–900：width 420，max-width 460，居中，无横向滚动。
- Desktop ≥900：width 420–460，居中，无横向滚动。
- 垂直留白：consumer 更靠上（如 12–16vh），admin/工具更居中（如 18–22vh）。
- 字体/间距随断点缩放；避免 layout shift。

## Tokens（示例，需映射到项目 Token）
- 颜色：bg/card/text/muted/border/primary/danger。
- 圆角/间距/阴影：radius-s/m；gap-1..4；shadow-s（轻）。
- 动效：hover/active/focus-visible 180–220ms。
- 断点：与项目 sm/md/lg 等保持一致，并套用上述认证容器规则。
- 如已有 tokens，复用/映射；不要发明 Brand2/Super/CustomStrong。新增 token 必须有理由、命名一致、向后兼容（只新增，不改旧语义）。

## 复用组件（不要重造）
- 核心：AppContainer，PageTitle，PrimaryButton（pill），SecondaryButton，Input/FormItem（轻边框+focus ring），SectionCard，Divider，ListRow/LinkRow，ModalShell。
- 扩展：Avatar，ListItem/SettingRow（左 Icon/Avatar，中文字，右 Arrow/Switch），Switch/Toggle（ON=primary；OFF=neutral；全状态），TabBarShell，HeaderBanner/ProfileHeader，Badge/Tag。
- 列表操作：ListItemAction（Star/Follow/More）热区 44x44，需对齐 name-row 中线。
- 索引轨：IndexRail（LetterIndex）固定右侧，使用 tokens，视觉弱化。

## 布局模式
- HomeLayout（卡片/模块），ConsumerLayout（列表优先），AdminLayout（表单/工具），ModalLayout。
- 任意含 IndexRail 的列表：启用“三轨布局”——内容区、操作栏位、索引轨。使用 tokens：Layout.List.ActionColumn.Width/Inset，Layout.List.IndexRail.Inset，Layout.List.SafeGap.BetweenActionAndIndex。禁止魔法数。

## 色彩清洗与推衍（非认证页）
- 移除历史亮蓝/高饱和；所有激活/选中/CTA/Switch ON/Tab 选中使用品牌主色 token（不硬编码 hex）。
- 新组件（Avatar/Switch/TabBar 等）从既有 tokens 推衍颜色/圆角/阴影/间距/字重/动效。
- Divider 极轻，优先用间距分组。

## 场景打法（栈无关）
- ADMIN_TABLE：左标题+数量，右主操作（primary 新建 / default 刷新 / danger 批删）；筛选 inline，搜索/重置在筛选右侧；表格+分页；行高 44–52；窄屏筛选换行，表格外包横向滚动。
- ADMIN_DETAIL：头部左返回右编辑；主体 descriptions 或双列网格；关联区 Tabs+小表格；空态紧凑；窄屏横滚。
- ADMIN_FORM：≥768 双列，<768 单列；媒体上传与 textarea 高度 200–240 对齐，object-fit: cover，resize: none；长表单优先底部粘性操作，sticky 失效则降级。
- ADMIN_CONFIG：分区（标题+简述+内容）+ 轻边框；label 对齐、控件等高；表格套 ADMIN_TABLE 规则；可用粘性操作区。
- ADMIN_WORKBENCH：左导航 220–260；右侧概览卡 + 入口卡网格（PC 3–4 列，窄屏 1–2）；卡片 88–104 高，按钮对齐，轻 hover。
- LIVE_VIEW：桌面双栏（播放器+sticky 侧栏）；移动顺序：介绍 → 更多/折叠 → 聊天（不可折叠且一跳可达）；播放器 16:9 自适应；弹窗窄屏 92% 宽且 body 可滚动；仅 Tab 头可吸顶。
- CONTENT：头部容器统一（返回/标题/主操作同一行），Tabs 防溢出，空态紧凑；可用 softer 主题（圆角略大、柔阴影）。
- AUTH（consumer/admin/一键/SSO/注册/找回）：沿用 docs/登录注册找回-统一设计语言与自适配方案.md 的 wireframe 与容器规则；主按钮 pill，轻输入；OAuth 栅格 2 列（<900）/3 列（≥900）；协议可见。

## 代码前必填声明
在输出代码前先给出：
【Design Tokens Used】
【Components Used】
【Layout Pattern】（如 ConsumerLayout/AdminLayout/ModalLayout）
【UI-UX-PRO-MAX 优化点】（层级、间距、对齐、状态、无抖动、色彩清洗、如有列表+Index 需三轨说明）
并注明逻辑是否改动（默认无）。若有 IndexRail，声明使用的三轨 tokens。

## 输出规则
- 优先完整替换或最小 diff；强调逻辑未动。
- 标注样式来源：哪些来自 tokens / components / layout。
- 若新增 tokens/组件，说明影响范围并确保向后兼容。

## 自检（必须通过）
- 设计语言：仅用 tokens；不发明新按钮/输入样式；圆角/阴影/动效在体系内；状态完整；无横向溢出；无 layout shift。
- 响应式：容器遵循 92vw/420–460；垂直留白符合 consumer/admin 气质；字重/间距随断点同步缩放。
- 色彩清洗：无杂蓝；主色 token 负责激活/选中；Divider 低对比；Icon 风格一致。
- Tokens：无无故新增类型；不改旧语义；单一来源。
- 组件：复用不重写；API 默认稳定；新增需求用 variant/size/tone 扩展。
- 布局：使用定义的模式；结构可变但语言一致。
- 触控热区：交互元素 ≥44x44。
- 三轨（如适用）：操作栏位用 tokens，对齐 name-row，不与 IndexRail 重叠，无魔法数。

## 使用方式（提示骨架）
1) 声明优先级：“遵守《登录注册找回-统一设计语言与自适配方案.md》（最高优先级）+ 本模板”。
2) 说明目标页面 + 采用的布局模式。
3) 输出声明块（Tokens/Components/Layout/优化点 + 逻辑改动说明）。
4) 给出 diff/代码；标注 token/组件/layout 来源；若改共享资产说明影响面。
5) 运行自检清单。
