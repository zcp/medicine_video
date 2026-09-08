下面是一份**可直接给 Cursor/放进仓库的「播放页（回放页）UI 优化方案文档」**，结构与您给的 Expert 文档一致，且严格按你的 Design System 原则（ConsumerLayout、去卡片、去油腻、tokens/components 驱动、禁硬编码、动效 180–220ms、避免 layout shift）来写。

---

# Playback（回放/播放）页面 UI 优化提示词（强制基于 Design 文档）

本文档与 **当前实现代码** 保持一致；所有数值与行为以代码为准。
本优化仅做 UI/UX 结构与视觉一致性提升，不改变业务逻辑。

---

## 一、角色与最高优先级

你现在是本项目的 **Design System Architect（UI-UX-PRO-MAX-SKILLS）**。

========================================================
【最高优先级：必须优先遵守 Design 文档（不可违背）】
==============================

必须优先阅读并严格遵守以下两个文档：

1. **Design-System-Rules_UI-UX-PRO-MAX.md**
2. **《登录注册找回-统一设计语言与自适配方案.md》**（Highest Priority Design Language & 响应式策略）

强制要求：

* 在进行任何页面重构、tokens/components/layout 抽象前，必须先阅读并理解上述文档。
* 所有 Design Tokens / Components / Layout Patterns 必须基于文档总结提炼，不允许凭空创造。
* **禁止硬编码**颜色/圆角/阴影/间距/字体。
* 若本提示词与基准文档冲突，以基准文档为最高优先级。

---

## 三、参考来源声明（强制）

========================================================
【允许参考 B 站结构，但禁止复制其平台化视觉】
========================

本次允许参考 B 站播放页的“信息层级结构”：标题层级、Meta 信息、操作区收纳逻辑、Tabs 组织方式。

但必须强制改为医疗产品气质：

* 禁止社交平台风格按钮堆叠
* 禁止红色 CTA
* 禁止热度气泡浮层（如 1.2k bubble）
* 禁止大面积强调点赞/分享

---

## 四、任务与原则

========================================================
【任务：优化 Playback 页面（回放/播放页）】
===========================

* **目标页面**：回放/播放详情页（本仓库为 `pages/app/live/LiveView.vue`；可视为 Replay 页）
* **目标**：在不改业务逻辑前提下，将页面升级为「医疗学术播放页」：去社交化、去娱乐化、结构专业化，与全 App Design Language 一致。

必须做到：

* 不修改业务逻辑、不修改接口/数据结构、不修改功能流程
* 不新增复杂交互逻辑
* 仅优化 UI/UX 结构表现与视觉一致性
* 动效保持 **180–220ms**
* hover / active / focus-visible / disabled 状态必须完整
* 必须避免 layout shift（播放器区、Header 区、Tabs 切换、发送按钮状态变化不得跳动）

---

## 五、当前页面问题（必须承认并修复）

========================================================
【问题】
====

1. Header 信息层级混乱，标题/Meta/专家信息缺乏清晰分组。
2. “专家”信息块没有与标题左对齐，视觉节奏断裂，缺乏医疗文档感。
3. 专家信息使用逗号 `，` 分隔，字段感弱，应该使用 `|` 分隔。
4. 页面操作按钮过多，产生直播平台感。
5. 收藏体系不一致：专家列表页使用 Star（空心/实心），播放页必须统一复用。
6. 播放器上悬浮观看数气泡（如 1.2k）过于平台化，应降级为 MetaRow。
7. Tabs 样式偏传统且对比过强，应轻导航化。
8. Chat 输入框颜色太浅，边界感不足，几乎看不见，属于严重可用性问题。
9. Chat “发送”按钮存在红色/强 CTA 风格，必须回归 Color.Primary。

---

## 六、Layout Pattern（强制）

该页面属于「内容型详情页」，必须使用：**ConsumerLayout（单背景、去卡片、留白分组）**

核心目标：结构轻、留白高级、视觉克制、字段对齐像医疗文档/会议纪要、去平台化。

禁止：卡片堆叠感、多个按钮平铺造成社交平台感、任何 hard-coded 阴影或圆角。

---

## 七、优化目标（必须执行）

### 7.1 Header 信息层级重构（强制，四层结构）

Header 必须拆成 **4 层**，且在**同一 header-inner 容器**内、**共享同一 padding-left token**，不允许 ExpertRow 独立缩进。

顺序：**TitleRow → MetaRow → ExpertRow → ActionRow**。

**第一层：TitleRow**

* 标题最多两行，超出省略
* “展开”按钮必须降级为 icon-only（轻按钮），禁止大圆按钮抢视觉权重

**第二层：MetaRow（secondary）**

* 必须统一字段格式，示例：`回放 · 1.2k 观看 · 2025/12/12 15:34`
* 分隔符必须使用 `·`（推荐）或 `|`（可接受）；**禁止逗号 `，`**
* MetaRow 必须为 secondary（--home-text2）

**第三层：ExpertRow（档案化层级，必须左对齐）**

* 视觉权重：**Title（强）> MetaRow（弱）> ExpertRow（中）> ActionBar（弱）**；ExpertRow 内 **姓名（强）> 职称（中）> 医院/科室（弱）**。
* 第一行：**姓名**（--home-text1，稍加粗）+ **" | "** + **职称**（--home-text2，opacity 0.85）；分隔符必须为 `|`，禁止 `，`。
* 第二行：医院 | 科室（--home-text2，opacity 0.75）。
* 禁止整行同色同粗；字段左对齐与标题左边缘一致。

---

### 7.2 Action 区（强制：仅保留 收藏/分享/点赞）

* **删除「更多」按钮与 ActionSheet**：页面上不再显示“更多 …”入口及点赞/下载/分享弹窗；若业务逻辑仍依赖可保留逻辑，UI 上必须移除入口与弹窗展示。
* **仅保留三项操作**：**收藏（Star）**、**分享**、**点赞**，全部放在同一行 ActionRow，作为医疗系统工具栏（与《PlaybackActionBar 组件规范文档》一致）。
* **布局**：三操作平铺整屏（等分，各占 1/3 宽），每项 flex:1；**icon + 轻标签** 垂直排列，居中对齐；热区 ≥44×44px。
* **轻标签（必须）**：每项下方文案为「收藏」「分享」「点赞」；字体 `--home-fs-meta`，颜色 `--home-text2`，opacity 0.75~0.85；禁止 bold、禁止默认 primary。
* **样式**：tokens 驱动；icon 约 20px（如 40rpx）；默认 Neutral（--home-text2）；active 态 Color.Primary；动效 180–220ms；分享无 selected 态，保持 neutral。
* **防 layout shift**：图标置于固定尺寸容器内（如 `.action-icon-wrap` 40rpx×40rpx），★/☆ 切换不改变宽高；ActionBar 设置 min-height 保持整块高度稳定。
* **图标统一**：收藏 ★/☆、分享 ↗、点赞 **↑**（与 Star/Share 同一线性符号体系）；禁止彩色 emoji；三枚图标统一 20px、默认 --home-text2 opacity 0.8、active 仅 icon 变 primary、label 不变 primary；transition 180–220ms。
* **去社交化**：禁止红色/粉色 CTA、禁止 heart 图标；收藏 Star 必须与专家页完全一致（★/☆）。

---

### 7.3 收藏体系强制统一（必须与专家页一致）

* 收藏必须完全复用专家页 Star 体系：未收藏 = 空心 Star（☆，Neutral），已收藏 = 实心 Star（★，Color.Primary）
* 点击热区 ≥ 44×44px；hover/active/focus-visible/disabled 状态完整；动效 180–220ms
* 禁止心形、禁止红色、禁止默认蓝色

---

### 7.4 播放器区域去平台化（强制）

* 视频容器背景统一为纯黑或统一 Neutral；去除灰+黑混合边缘
* 禁止视频区域右上角浮动观看数气泡；观看数只能在 MetaRow 展示
* 播放按钮居中，透明度不超过 0.8；Loading 层克制（降低遮罩强度、避免大黑块），播放器容器稳定高度、禁止加载时跳动

---

### 7.5 Tabs 医疗化（直播介绍 / 互动讨论）（强制）

* Tab 文案：**「聊天」改为「互动讨论」**（医疗化命名）
* 选中态：Color.Primary；未选中：--home-text2 + opacity 0.75
* 下划线**更细**（如 2rpx）、克制；动效 180–220ms；禁止默认蓝色
* Tabs 与内容区之间用 **spacing**（如 --home-spacing-inner）分隔，不建议用明显 divider

---

### 7.6 Chat 输入区可见性修复（强制）

* 输入框：背景 Neutral-0/50（不可透明）、1px border（var(--home-border)）、hover/focus-visible 时 border-color 主色、placeholder opacity ≥ 0.7、高度 ≥ 44px、padding/圆角来自 tokens
* **聊天气泡**：系统/他人消息背景 **--home-card**（与页面 --home-bg 区分，避免过于接近）；自己消息背景 **Primary 极浅 tint**（如 --home-tag-forecast-bg）；边框 --home-border、圆角 --home-r-md；用户名与正文 --home-text1/--home-fs-meta，时间 --home-text2 + opacity 0.7；禁止气泡与页面背景过于接近

---

### 7.7 发送按钮（强制）

* 发送按钮颜色必须使用 Color.Primary；禁止红色发送按钮
* 输入为空必须 disabled；disabled 状态必须明显（opacity + neutral）
* 动效 180–220ms；不允许出现多个“发送”按钮入口

---

## 八、去社交化原则（医疗领域强制）

* 不使用红色 CTA
* 不使用 heart 图标（点赞用与 Star/Share 同一体系的线性 icon，如 ↑）
* 不使用大号粉色按钮
* 不强调点赞数量
* 保持克制

---

## 九、文案与字段语义修正（强制）

* “专家” → “主讲专家”（或保留“专家”但结构必须字段化）
* “一项多中心”等内部术语 → 改为医疗可读语义（如“系列活动：多中心联合文献分享会”或“主办单位/协作中心”）
* 只允许改展示文案，不改数据结构

---

## 十、必须执行的高级感规则（来自 Design 文档）

* **去油腻**：优先 spacing 分组；Divider 若必须存在则极浅（5%~10% Neutral）；禁止粗线/厚边框。
* **去卡片化**：整体单背景，不使用多层背景块/圆角卡片堆叠；视频区也不要再包卡片。
* **色彩清洗**：禁止默认亮蓝；主色仅用于选中态/收藏激活态/关键 CTA。
* **点击热区**：展开、收藏、分享、点赞、Tab、播放器关键按钮均 ≥44×44px。
* **避免 layout shift**：展开标题、切换 Tab、收藏/点赞状态切换，不得引发布局跳动。

---

## 十一、必须使用或复用的组件（建议清单）

> 组件名以你项目现有为准；若缺失，必须在 components 层补齐再引用，禁止页面临时造轮子。

* **AppContainer / ConsumerLayout**（全局容器与响应式）
* **PageHeader / NavBar**（返回 + 标题）
* **TitleRow / ExpandIconButton**（标题与展开）
* **PlaybackActionBar / IconButton**（收藏 Star / 分享 / 点赞，icon+轻标签；实现须符合《PlaybackActionBar 组件规范文档》）
* **VideoPlayer**（播放器容器，保持纯净）
* **FilterTabs / Tabs**（直播介绍/聊天）
* **EmptyState**（暂无介绍/暂无聊天）
* **Divider（可选，极浅）**

---

## 十二、强制输出格式（代码前必须先输出）

在输出任何代码前，必须先输出：

* **【Design Tokens Used】**：Color / Spacing / Radius / Typography / Motion / Shadow（若使用）
* **【Components Used】**：PlaybackHeader / PlayerContainer / IconButton / ActionSheet / Tabs / ChatInput / EmptyState 等（按项目真实组件列出）
* **【Layout Pattern】**：ConsumerLayout
* **【UI-UX-PRO-MAX 优化点】**：Header 四层层级与对齐、删除更多与 ActionSheet、ActionRow 仅 收藏/分享/点赞 三操作平铺整屏（等分）、**icon+轻标签**、固定 icon 容器防 layout shift、Star 与专家页一致、MetaRow/Player 去平台化、Tabs 轻导航、Chat 输入框可见性及发送主色、去卡片/留白/避免 layout shift

---

## 十三、必须输出最小 diff（强制）

输出最小 git diff（只改 UI 样式与组件组合，不改业务逻辑）。diff 至少包含：

1. 删除“更多”按钮及 ActionSheet 入口展示
2. ActionRow：仅保留 收藏(Star)/分享/点赞 三项，平铺整屏（等分）轻工具栏
3. 专家信息块左对齐（与标题同基线），专家字段分隔符用 `|`
4. 收藏 Star 复用专家页同一套样式与状态
5. Chat 输入框边界增强（可见性修复）+ 发送按钮 Color.Primary

禁止回答“已满足无需修改”。

---

## 十四、强制工作流程（改造时必遵）

### Step 1：现状分析（结构摘要）

* Header：标题/回放标签/观看数/时间/专家信息/操作区
* Player：视频区域 + 悬浮观看气泡
* Tabs：直播介绍/聊天
* Content：暂无介绍（empty）

### Step 2：重排信息层级（落地方式）

* 将观看数移到 MetaRow（文本）
* 删除「更多」与 ActionSheet；ActionRow 仅保留 收藏(Star)/分享/点赞 三 IconButton 平铺整屏（等分）
* Tabs 改轻导航；empty 收敛高度

### Step 3：页面改动前声明（必须输出）

【Design Tokens Used】
【Components Used】
【Layout Pattern】ConsumerLayout
【UI-UX-PRO-MAX 优化点】

### Step 4–5：最小 diff 原则

* 只改模板结构（行重排）+ 样式（tokens 引用）
* 不改播放逻辑、不改数据绑定、不改接口
* 新增 tokens 仅允许在全局 tokens 文件集中定义，并保持语义清晰、向后兼容

### Step 6：自检清单

* [ ] 单背景、无卡片、无阴影
* [ ] 观看数不再悬浮在视频上
* [ ] ActionRow 仅 收藏(Star) + 分享 + 点赞，平铺整屏（等分），icon+轻标签，无 layout shift
* [ ] 专家信息左对齐、`|` 分隔
* [ ] Tabs 轻导航、动效 180–220ms、状态齐全
* [ ] Chat 输入框可见、发送按钮主色、空内容 disabled
* [ ] 所有交互热区 ≥44px
* [ ] 无 layout shift

---

## 十五、验收目标与实施记录

### 验收目标（最终效果）

* 像“医疗会议回放系统”而不是短视频平台
* Header 对齐像医疗文档，字段可扫读
* 操作按钮克制（收藏 Star + 分享 + 点赞，平铺整屏，icon+轻标签，与 PlaybackActionBar 规范一致）
* 收藏体系与专家页完全一致（★/☆）
* 输入框清晰可见，交互状态完整
* 发送按钮主色化，不再红色
* Tabs 与全 App 统一，轻导航化
* 全页面 tokens 驱动，无硬编码

### 实施记录与修改方法（已落地）

以下为本次按本提示词对 `LiveView.vue` 与 `ChatTab.vue` 的修改摘要，便于后续维护与复现。

| 项目 | 修改内容 | 方法/文件 |
|------|----------|-----------|
| **MetaRow** | 统一为 `回放 · 1.2k 观看 · 12/15 14:34` 格式，分隔符 `·`，无 emoji 短状态 | 新增 `metaStatusShort`、`metaRowText` 计算属性；模板单行 `<text class="meta-row-text">{{ metaRowText }}</text>` |
| **ExpertRow** | 档案化层级：第一行 姓名（--home-text1 加粗）\| 职称（--home-text2 opacity 0.85），第二行 医院\|科室（--home-text2 opacity 0.75） | `formatExpertName`、`formatExpertTitle`、`formatExpertLine2`；`.host-name` / `.host-title` / `.host-hospital` 分层样式；左对齐 |
| **收藏** | 改为 Star IconButton（☆ 未收藏 / ★ 已收藏），主色激活，热区 ≥44px | 模板用 `<view class="star-btn-wrap">` + `<text class="star-icon">★/☆</text>`；样式 `.star-icon.active { color: var(--home-primary) }`；移除原收藏 icon 与“收藏”文案 |
| **Action 区** | 平铺一行：★ 收藏、↗ 分享、↑ 点赞（同一线性图标体系，禁止 emoji）；icon+轻标签；固定 icon 容器防 layout shift；Star 与专家页一致 | 结构含 `.action-icon-wrap` + `.action-label`；三图标统一 20px、opacity 0.8、active 仅 icon primary；与 PlaybackActionBar 规范一致 |
| **Header 四层** | TitleRow/MetaRow/ExpertRow/ActionRow 同处 header-inner，共享 padding-left | `.info-header.header-inner` + `.info-section .header-inner { padding-* }`，ExpertRow 不独立缩进 |
| **Tabs 医疗化** | 「聊天」→「互动讨论」；下划线 2px，选中 Primary、未选中 Neutral | fallback 与补充 Tab 的 title 改为「互动讨论」；tabs 计算属性中 tab_key===`chat` 时 label 为「互动讨论」 |
| **聊天气泡** | 他人/系统 --home-card 背景（与页面区分）；自己 Primary 极浅 tint（--home-tag-forecast-bg）；文本 text1/text2；禁止与页面背景过于接近 | ChatTab.vue `.message-content` 用 --home-card；`.message-item.self .message-content` 用 --home-tag-forecast-bg；isSelf(msg) 判断 |
| **视频/加载** | 容器纯黑；Loading 层克制，透明度不超过 0.8 | VideoPlayerApp 根背景 #000；`.loading-overlay` background rgba(0,0,0,0.5)、文案弱化 |
| **Chat 输入框** | 背景/边框可见，focus 主色，placeholder 不透明度过低，高度 ≥44px | LiveView 降级聊天区：`.chat-input-field` 使用 `--home-card`、`--home-border`，focus `--home-primary`；ChatTab.vue：`.message-input` 同上 tokens |
| **发送按钮** | Color.Primary，空内容 disabled，禁用态中性 | LiveView：`.chat-send-btn` 使用 `--home-primary`，`:disabled="!chatInput.trim()"`，`[disabled]` 样式；ChatTab：`.send-btn` 同上，已有 `:disabled="!inputText.trim()"` |
| **Tabs** | 轻导航；未选中 --home-text2 opacity 0.75，选中 primary；下划线 2rpx 更细；与内容区用 spacing 分隔 | `.tab-item` opacity 0.75，`.tab-item.active` opacity 1；`::after` height 2rpx；`.content-section` padding-top --home-spacing-inner |
| **Tokens** | 全页无硬编码颜色/圆角/间距 | `--home-bg`、`--home-primary`、`--home-text1`/`--home-text2`、`--home-border`、`--home-spacing-*`、`--home-fs-*`、`--home-r-*`、`--transition-base` |

**涉及文件：**

* `src/pages/app/live/LiveView.vue`：Header 四层（header-inner 共享 padding）、ActionRow（★↗👍 平铺、点赞用 👍 去 heart）、Tabs 文案「互动讨论」、降级聊天输入/发送、样式 tokens 化
* `src/components/ChatTab.vue`：聊天气泡（Neutral-100/边框/--home-r-md）、用户名与时间 tokens；输入框与发送按钮主色与 disabled 态
* `src/components/app/VideoPlayerApp.vue`：Loading 层克制（透明度 0.5）、容器纯黑

---