# 搜索框样式统一（B站风格）-实施规划文档（分析版）

> **文档版本**：v1.14（**最终版**——v1.15 已撤回；结构同步全部页面完成）
> **创建日期**：2026-08-31
> **适用范围**：App 端 19 处生效搜索 UI（含首页伪搜索入口与 TargetSelector 弹层搜索）+ 新增 `--search-*` Design Token + 新建清除按钮小组件 + 共享搜索容器样式；不涉及 `src/pages/h5/`（不在实施范围）
> **分析基础**：① App 端源码逐行核查（`src/components/app/SearchBar.vue` / `SearchNavBar.vue` / `src/components/expert/ExpertSearch.vue` / `src/components/brand/BrandHeader.vue` / `src/components/common/TargetSelector.vue` / `src/pages/app/categories/AllCategories.vue` / `src/pages/app/tabbar/my/follows/index.vue` / `src/pages/app/tabbar/home/components/SearchBar.vue` / `src/pages/app/live-manage/list.vue` / `src/pages/app/live-manage/edit.vue` / `src/pages/app/live-manage/create.vue` / `src/components/app/TabManager.vue` / `src/pages/app/admin/*` 7 页 / `src/common/uni.scss` / `src/styles/variables.scss` / `src/static/fonts/iconfont.css` / `src/pages.json`）；② 会话内多轮独立分析对比（B 站截图拆解、双方审查互评，实质结论一致、互为补充）；③ 既有文档范式（`docs/管理页面加载态与分页风险修复-实施规划文档.md`、`docs/搜索页面设计文档.md` 等）
> **状态**：分析完成，待实施（阶段 0 未开始）
> **关联文档**：`docs/搜索页面设计文档.md`（搜索页既有设计规范，本方案为其中搜索框视觉的收敛升级）
> **v1.1 变更**：经方案审查修订——① 管理端 M2 由"5 页同构"拆为三组（M2a 灰底方框 / M2b 灰底胶囊+focus 光晕 / M2c 白底微圆角）；② 补漏 TargetSelector 弹层搜索（第 19 处）；③ 新增共享容器 `.app-search-field`（S3）防复制分叉；④ Token 数量修正为 8 个；⑤ C3/P2 明确"含清除接线逻辑"非纯样式；⑥ 新增 create.vue 死样式清理与 grep 白名单规则；⑦ 风险清单扩展至 17 项；⑧ 实施项 21 → 23 项

---

## 一、背景与结论先行

### 1.1 需求来源

用户对现有搜索框视觉不满：**边框厚重或存在多余的灰色填充块**，不够轻盈简约；期望参考 B 站搜索框——**细线条边框 + 白色底色 + 线稿图标 + 圆形灰底清除钮 + 品牌色仅点缀动作**。用户已确认：C 端与管理端均按此风格统一。

### 1.2 核心结论（多轮独立分析对比）

**现状**：全项目 **19 处**生效搜索 UI 分裂为 **8 套视觉方言**（灰底全圆角胶囊 / 灰底微圆角矩形 / 灰底 2rpx 边框胶囊 / 灰底方框 8rpx / 灰底胶囊+focus 光晕 / 白底微圆角 10rpx / 白底近达标 / 裸 input），另有一处首页伪输入框、一处闲置通用组件。

**B 站公式**（截图拆解结论）：白底 + `1rpx` 浅灰细线 + **全圆角胶囊** + 框内线稿灰图标（无独立色块）+ 有字时显示**浅灰实心圆 + 白色叉**清除钮 + 品牌色只用于"搜索"文字/光标，聚焦态几乎不变。

**可行性**：全部搜索框结构同构（`input + 图标 + 清除`），改造以**样式为主、少量 DOM 归位与清除接线**；业务搜索协议（防抖/过滤/服务端请求/双触发）全部不动。项目内已有 B 站语言的先例（`live-manage/list.vue` 胶囊细边结构、`admin/expert-list`/`admin/departments` 白底细边、auth 页 `$color-border-input` 白底细边），本方案是收敛而非引入。

**红线**：`--home-input-bg`（`uni.scss:120`，`#F5F5F7`）被 **32 处**引用、绝大多数是普通表单输入框/占位块，**一行不改**；硬编码灰底（`#f5f5f5`/`#f0f1f3`）需逐处显式改写。

### 1.3 现状-目标对照（核心差距）

| 维度 | 当前（分裂） | 目标（B 站风格） |
|------|-------------|------------------|
| 底色 | 灰块 `#F4F4F4`/`#f5f5f5`/`#f0f1f3`/`--home-bg`/`--home-input-bg` 五档 | **白底** `#fff` |
| 边框 | 无边框 / `2rpx` 边框 / `1rpx` 半透明 / focus 才显 | 常驻 `1rpx solid #E5E7EB` |
| 圆角 | `999rpx` / `12rpx` / `10rpx` / `8rpx` 四套 | 统一胶囊 `999rpx` |
| 清除钮 | 裸 `icon-error` / 文本 `✕` / 缺失 | 灰圆（40rpx 视觉）+ 白叉（CSS 自绘）+ 热区 ≥64rpx |
| 聚焦态 | 灰→白切换 + 品牌色粗边 + 光晕阴影（厚重主因） | **默认态即最终态**，focus 仅加深边线 |
| 品牌色 | 框体染色（focus 边框/光晕） | 仅"搜索"文字与光标 |

---

## 二、目标视觉规范（Design Token 定义）

### 2.1 新增 `--search-*` Token（`src/common/uni.scss` :root 追加，**只加不改**，共 8 个）

```scss
/* 搜索框统一（B站风格）：白底 + 细线 + 胶囊 + 灰圆白叉清除 */
--search-bg: #FFFFFF;              /* 白底（默认态即最终态） */
--search-border: #E5E7EB;          /* 细边框（与 --home-border / $color-border-input 同值） */
--search-border-focus: #C9CDD4;    /* focus 仅加深边线，不染色 */
--search-icon: #999999;            /* 线稿灰图标，与边框同色系 */
--search-placeholder: #6B7280;     /* 占位文字（--home-text2，保证白底对比度） */
--search-clear-bg: #EBEBEB;        /* 清除钮灰圆底 */
--search-clear-icon: #FFFFFF;      /* 清除钮白色叉 */
--search-radius: 999rpx;           /* 胶囊圆角 */
```

> ⚠️ **红线**：`--home-input-bg`（`uni.scss:120`）及其服务的所有表单输入框、弹层表单、占位块**不在此方案范围内，一行不改**。硬编码灰底（`#f5f5f5`/`#f0f1f3`）不在 token 体系内，**必须逐处显式改写**（新 token 不会自动生效）。

### 2.2 场景分层规范

| 场景 | 高度 | 右侧动作 | 说明 |
|------|:---:|---------|------|
| 导航栏（SearchNavBar、首页伪框） | 64rpx | 主色文字"搜索"（仅真搜索场景） | 受 44px 导航高度约束 |
| C 端列表筛选（Expert/Brand/Categories/Follows） | 72rpx（✅ D2：Expert/Brand 88→72） | 无 | 页面内嵌 |
| 管理端筛选（admin 7 页） | **64rpx**（✅ D6 统一；users 68→64） | 无 | 保持管理端数据密度 |
| 弹层搜索（TabManager×2、标签选择、TargetSelector） | 64rpx | 无 | 可最简，但必须补图标+清除 |
| 首页伪搜索入口 | 64rpx | 无 | 仅外观对齐，保持点击跳转 |
| live-manage/list（特例） | 72rpx（保持现状，与按钮同高对齐） | 主色文字"搜索" | ✅ D6 单独评估结论 |

### 2.3 聚焦态纪律

- **默认态即最终态**：白底 + 细灰边常驻，不依赖 `:focus-within` 做"灰→白"切换（小程序/App 端 `:focus-within` 兼容性不稳，正好规避）。
- focus 仅加深边线（`--search-border-focus`），**去掉品牌色粗边、阴影、光晕**（涉及 SearchNavBar:222-226、AllCategories:248-252、featured:720-725、users:661-663、messages:567 的既有 focus 逻辑，逐一删除）。
- 品牌色 `#0F766E` 只保留：右侧"搜索"文字（500 字重）、输入光标（`caret-color`，弱支持平台忽略）。

### 2.4 清除按钮规范（CSS 自绘，零字形依赖）

> 事实：`icon-close`/`icon-cha`/`icon-error` 在 `src/static/fonts/iconfont.css:184-187/235` **同码点 `\e620`**，字形是否自带圆环无法从代码确认——叠加灰圆底存在"双圆叠影"风险，故**弃用字形、CSS 自绘**。

```scss
/* 视觉 40rpx 圆；热区外扩至 ≥64rpx（透明 padding） */
.search-clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx; height: 64rpx;      /* 热区（含透明外扩） */
  &::before {
    content: '';
    width: 40rpx; height: 40rpx;
    border-radius: 50%;
    background: var(--search-clear-bg);
  }
  /* 白色叉：两段旋转细线 */
  &::after {
    content: '';
    width: 16rpx; height: 16rpx;
    border-top: 2rpx solid var(--search-clear-icon);
    border-right: 2rpx solid var(--search-clear-icon);
    transform: rotate(45deg);
  }
}
```

### 2.5 共享搜索容器（S3，防复制分叉；✅ D5 已定方案 A）

仅 S2 不够：16+ 处各自抄 8 个 token 仍会形成"近似拷贝"。阶段 1 同时抽出共享容器：

**方案 A（✅ 已确认）**：公共样式类 `.app-search-field`（置于 `src/common/uni.scss`）：白底/细边/胶囊/内边距/图标槽/flex 布局全封装，各页只需引用类名 + 覆盖高度与图标。

> ⚠️ 引入后需验证公共类与各页 scoped 样式的优先级（公共类不被局部覆盖、局部尺寸变量可覆盖高度）。覆盖链验证失败时回退方案 B（`AppSearchField.vue` 包装组件）。

---

## 三、现状盘点：19 处搜索 UI 清单与差距

| # | 文件 | 类型 | 当前实现（行级） | 与目标差距 |
|:-:|------|------|------------------|-----------|
| 1 | `src/components/app/SearchNavBar.vue` | 通用·导航栏 | 灰底 `#f5f5f5`+`12rpx`（209-217）；focus 白底+`#0F766E` 2rpx 边+阴影（222-226）；清除 icon-error（34-36）；右侧主色"搜索"（41-43） | 圆角/灰底/focus 三处全改；清除换组件 |
| 2 | `src/components/app/SearchBar.vue` | 通用（**全仓 0 引用**） | 灰底 `#F4F4F4`+胶囊+72rpx+取消按钮（145-159） | 删除或重构为范本（建议删除防误用） |
| 3 | `src/components/expert/ExpertSearch.vue` | 通用·C 端 | 底 `--home-bg`+`2rpx --home-border`+pill+88rpx（78-88）；图标+清除齐（4-18） | 去灰底/粗边 → 白底细边 1rpx |
| 4 | `src/components/brand/BrandHeader.vue` | 通用·C 端 | 与 ExpertSearch 同款（70-80） | 同上 |
| 5 | `src/pages/app/tabbar/home/components/SearchBar.vue` | **伪输入框** | `--home-action-secondary-bg` 灰块+pill+64rpx（167-183）；点击跳转（84-86） | 外观改白底细边；保持伪框 |
| 6 | `src/pages/app/categories/AllCategories.vue` | C 端内嵌 | `#f5f5f5`+`12rpx`+focus 品牌边+阴影（237-252）；清除 icon-close（23-25） | 胶囊化+去灰+弱化 focus+换组件 |
| 7 | `src/pages/app/tabbar/my/follows/index.vue` | C 端内嵌 | 底 `--home-bg`+pill（344-362）；**有图标、无清除 DOM**（4-13） | 白底细边+**补清除钮 DOM+接线** |
| 8 | `src/pages/app/live-manage/list.vue` | 管理端/主播端 | 默认底 `--home-input-bg`、focus 才白+主色边（1791/1794-1797）；胶囊+`1rpx $color-border-input`（1783-1791）；**无图标**（4-7）；**实心主色按钮**（1800-1817）；回车+按钮双触发 | 去默认灰底+补图标+按钮实心→主色文字+**删 focus 灰白切换**；**保留双触发** |
| 9 | `src/pages/app/admin/expert-list/index.vue` | 管理端 | **最接近目标**：`--home-card` 白底+`1rpx --home-divider`（半透明）+`12rpx`（864-873）；文本 `✕`（892-896）；框内 `filter-tag`×2（898-909） | 圆角→胶囊+边框改实心 `#E5E7EB`+换组件+标签圆角同步 |
| 10 | `admin/brands/index.vue` | 管理端 | 灰底 `#f0f1f3`+`8rpx`+文本 `✕`（530-563）；高 64rpx | 全量改（M2a） |
| 11 | `admin/tags/index.vue` | 管理端 | 同款：`#f0f1f3`+`8rpx`+文本 `✕`（374-391） | 同 M2a |
| 12 | `admin/users/index.vue` | 管理端 | **灰底胶囊+focus 光晕**：`--home-input-bg`+`$radius-full`+高 **68rpx**（651-660）；`:focus-within` 白底+`box-shadow 0 0 0 3rpx $color-primary-light`（661-663）；文本 `✕`（43） | 去灰+**删 focus 光晕**+换组件+高度 68→64（M2b） |
| 13 | `admin/messages/index.vue` | 管理端 | 同 users：`--home-input-bg`+`$radius-full`（556-561）；focus 白底（567）；文本 `✕`（38） | 同 M2b |
| 14 | `admin/departments/index.vue` | 管理端 | **白底微圆角**：`--home-card`+`10rpx`（1287-1294）；文本 `✕`（42） | 10rpx→胶囊+边框实心化+换组件（M2c，改动最小） |
| 15 | `src/pages/app/admin/featured/index.vue` | 管理端 | 灰底 `--home-input-bg`+pill+focus 品牌边+光晕（708-725）；**图标/清除在 input 胶囊外**并列（22-36） | **图标收进胶囊**+去灰+弱化 focus |
| 16 | `src/components/app/TabManager.vue`（专家弹层） | 弹层 | **裸 input**：无图标、无清除（237-246），服务端搜索 | 补图标+清除+白底细边胶囊 |
| 17 | `src/components/app/TabManager.vue`（品牌弹层） | 弹层 | 同上（289-298） | 同上 |
| 18 | `src/pages/app/live-manage/edit.vue`（标签弹层） | 弹层 | **裸 input**（357-365），客户端过滤 579 标签 | 补图标+清除（**含接线**：清空 tagKeyword+刷新过滤） |
| 19 | `src/components/common/TargetSelector.vue`（弹层搜索） | 弹层 | `ts-popup-search`：灰底胶囊（`ts-popup-input`:333-341 `--home-input-bg`+`--home-r-pill`+64rpx，右侧预留 64rpx 清除位）、**无图标**、文本 `✕`（清除热区仅 44rpx，347-361），`handleSearch/applySearch/clearSearch` 接线 | 去灰底+补图标+清除换 S2（**保留搜索接线**）+清除热区 44→64rpx |

**被动生效（无需直接改）**：`src/pages/app/search/index.vue`、`results.vue`（复用 SearchNavBar，随范本生效）。

**方言归类（8 组）**：灰底无边框胶囊（#2/5/7 及弹层缺）、灰底微圆角 12rpx（#1/6）、灰底 2rpx 边框（#3/4）、灰底方框 8rpx（#10/11）、灰底胶囊+focus 光晕（#12/13）、白底微圆角 10rpx（#14）、白底近达标（#9）、灰底胶囊+实心按钮（#8）、灰底胶囊无图标（#15/19）、裸 input（#16-18）。

---

## 四、实施目标与边界

### 4.1 实施目标

1. 19 处搜索 UI 视觉统一为 B 站风格（白底 + 细边 + 胶囊 + 线稿图标 + 灰圆白叉清除 + 品牌色点缀）。
2. 新增 `--search-*` token、`ClearButton` 小组件与共享容器 `.app-search-field`，形成唯一视觉来源，杜绝复制分叉。
3. 聚焦态改为"默认态即最终态"，删除全部 focus 灰→白切换/品牌色粗边/光晕阴影。
4. 分 6 个阶段独立提交，每阶段可独立编译验证、可回滚。

### 4.2 实施边界（不包含）

| 项 | 原因 |
|----|------|
| ❌ 修改 `--home-input-bg` 及任何表单输入框/弹层表单/占位块（32 处引用中非搜索部分） | 红线：token 误伤会导致全站表单视觉漂移 |
| ❌ 修改业务搜索协议（防抖 400ms、客户端过滤、服务端搜索、回车/按钮双触发、search store/API） | 协议不动；仅 C3/P2 新增"清除→清空关键词→刷新过滤"的小逻辑接线 |
| ❌ 合并 `$color-*`（SCSS，variables.scss）与 `--home-*`（CSS）两套 token 体系 | 超范围；仅收敛搜索框边框色值 |
| ❌ `src/pages/h5/` 下任何页面 | 不在实施范围（AGENTS.md）；H5 仅作预览端 |
| ❌ 搜索页附属灰块（`search/index.vue`/`results.vue` 的 `#f5f5f5` 历史/标签区） | 非输入框，同屏观感弱相关，本轮不阻塞 |
| ❌ 首页伪搜索框改为真输入框 | 保持点击跳转，仅外观对齐 |
| ❌ 新增依赖 / 修改 iconfont 字体文件 / 修改测试与构建配置 | 零新增 |

### 4.3 例外项（✅ 2026-08-31 全部已确认）

| 项 | 结论 |
|----|------|
| ⚠️ 闲置 `SearchBar.vue`（全仓 0 引用）处置 | ✅ **D1 删除** |
| ⚠️ 管理端 `expert-list` 框内 `filter-tag` 圆角处理 | ✅ **D4 同步胶囊** |
| ⚠️ 共享容器形式 | ✅ **D5 方案 A 公共类 `.app-search-field`** |
| ⚠️ 管理端高度定档 | ✅ **D6 统一 64rpx**；live-manage/list 单独保持 72rpx（按钮对齐） |
| ⚠️ TargetSelector 纳入范围确认 | ✅ 弹层搜索纳入；`ts-trigger` 触发器排除 |

---

## 五、实施项总清单（23 项）

### 基础设施（S1-S3）

| # | 实施项 | 位置 | 改动量 | 难度 | 风险 | 阻碍项 |
|:-:|--------|------|:---:|:---:|:---:|--------|
| S1 | 新增 8 个 `--search-*` token（2.1） | `src/common/uni.scss` :root | S | 低 | 低：误改既有 token → 全站漂移 | 无（只加不改） |
| S2 | 新建 `ClearButton.vue`（CSS 自绘灰圆白叉 + 热区 64rpx + `@tap.stop`） | `src/components/app/` | S | 低 | 中：伪元素跨端渲染差异 | 三端验证；备选内层 view 画叉 |
| S3 | 共享容器 `.app-search-field`（✅ D5 方案 A 公共类） | `uni.scss` | S | 低-中 | 中：公共类与 scoped 样式优先级冲突 | 阶段 1 验证覆盖链；失败回退方案 B |

### 范本（T1）

| # | 实施项 | 位置 | 改动量 | 难度 | 风险 | 阻碍项 |
|:-:|--------|------|:---:|:---:|:---:|--------|
| T1 | SearchNavBar 按 2.2/2.3/2.4 规范改造（胶囊+白底细边+弱化 focus+换清除组件） | `SearchNavBar.vue:209-226` 等 | S-M | 低 | 低：被搜索两页共用 | 无 |

### C 端（C1-C5）

| # | 实施项 | 位置 | 改动量 | 难度 | 风险 | 阻碍项 |
|:-:|--------|------|:---:|:---:|:---:|--------|
| C1 | AllCategories：胶囊化+去灰+弱化 focus+换清除组件 | `AllCategories.vue:232-287` | S | 低 | 低：72rpx 内三元素布局 | 无 |
| C2 | ExpertSearch/BrandHeader：去灰底/2rpx 边框 → 白底细边（✅ D2 高度 72rpx） | `ExpertSearch.vue:78-88`、`BrandHeader.vue:70-80` | S | 低 | 低 | 无 |
| C3 | follows：白底细边 + **补清除钮 DOM + 接线**（清空 keyword + 触发本地过滤） | `follows/index.vue:4-13,340-363` | S | 低-中 | 低：**含小逻辑接线** | 接线需与 `handleSearch` 联动 |
| C4 | 首页伪框：外观改白底细边胶囊（✅ D3 兜底链：`#E5E7EB` 起手，不足加深，仍不足加极轻阴影） | `home/components/SearchBar.vue:167-183` | S | 低 | 中：白底融入白导航，辨识度难 | 按 D3 链实施 |
| C5 | 闲置 SearchBar.vue **删除**（✅ D1 已确认） | `components/app/SearchBar.vue` | S | 低 | 低 | 无 |

### 管理端（M1、M2a-c、M3、M4）

| # | 实施项 | 位置 | 改动量 | 难度 | 风险 | 阻碍项 |
|:-:|--------|------|:---:|:---:|:---:|--------|
| M1 | expert-list：圆角→胶囊+边框实心 `#E5E7EB`+换组件+filter-tag 圆角同步（✅ D4 同步胶囊） | `expert-list/index.vue:864-909` | S | 低 | 低 | 标签不裁切验证 |
| M2c | departments：`10rpx`→胶囊+边框实心化+换组件（并入 M1 批次） | `departments/index.vue:1287-1315` | S | 低 | 低 | 无 |
| M2a | brands/tags：灰底方框 `#f0f1f3`+`8rpx` → 白底细边胶囊+换组件 | `brands:530-563`、`tags:374-391` | S×2 | 低 | 低 | 无 |
| M2b | users/messages：去灰底 + **删 focus 光晕**（`--home-input-bg`→白、`:focus-within` 白底+光晕删除）+换组件+高度 68→64（✅ D6） | `users:651-663`、`messages:556-567` | S×2 | 低-中 | 中：focus 灰→白逻辑删除不彻底 → 残留光晕 | 逐一核对 `:focus-within` 块 |
| M3 | featured：**图标收进胶囊**（结构归位）+去灰+弱化 focus | `featured/index.vue:22-36,693-725` | S-M | 中 | 中：模板重排，64rpx 内三元素，placeholder 截断 | 单独三端验证 |
| M4 | live-manage/list：去默认灰底+补图标+按钮实心→主色文字+**删 focus 灰白切换**（高度保持 72rpx，✅ D6） | `list.vue:4-7,1783-1817` | S-M | 中 | 中：按钮语义（双触发）、admin/manage 双模式 | 热区 ≥64rpx；仅改样式 |

### 弹层与收尾（P0-P3）

| # | 实施项 | 位置 | 改动量 | 难度 | 风险 | 阻碍项 |
|:-:|--------|------|:---:|:---:|:---:|--------|
| P0 | TargetSelector 弹层搜索：去灰底→白底细边胶囊+补图标+清除换 S2（**保留 search 接线**） | `TargetSelector.vue:25-38` | S | 低-中 | 中：`handleSearch/applySearch/clearSearch` 事件链（featured 链路） | 弹层单独三端验证 |
| P1 | TabManager 专家/品牌两弹层：补图标+清除+白底细边胶囊 | `TabManager.vue:237-246,289-298` | S×2 | 低-中 | 中：DOM 结构调整，服务端 `@input` 链不变 | 两弹层单独三端验证 |
| P2 | edit.vue 标签弹层：补图标+清除（**含接线**：清空 tagKeyword+刷新 filteredTagItems） | `edit.vue:357-365` | S | 低-中 | 中：同 P1 | 同 P1 |
| P3 | 收尾：create.vue 死样式删除（`create.vue:2080-2117`）+ 19 处逐项勾验 + grep 白名单校验 | 全仓 | S | 低 | 低 | — |

---

## 六、涉及文件与当前实现状态（行级）

### 样式基础设施

| 文件 | 当前实现状态 |
|------|-------------|
| `src/common/uni.scss:120` | `--home-input-bg:#F5F5F7`（**32 处引用，红线不动**）；`:root` 已有 `--home-border:#E5E7EB`（:68）、`--home-r-pill:999rpx`（:74）、`--home-bg:#F7F9FB`（:63）、`--home-text2:#6B7280`（:66） |
| `src/styles/variables.scss:27,35,61` | `$color-surface-page:#f7f8fa`、`$color-border-input:#e5e7eb`、`$radius-full:999rpx`（auth 三页与 live-manage/list 使用，不改） |
| `src/static/fonts/iconfont.css:184-187,235` | `icon-close`/`icon-cha`/`icon-error` 同码点 `\e620`（字形圆环不确定 → CSS 自绘规避） |

### 组件层

| 文件 | 当前实现状态 |
|------|-------------|
| `SearchNavBar.vue` | 灰底 `#f5f5f5`+`12rpx`（216-217）；focus 白底+品牌 2rpx 边+阴影（222-226）；清除 icon-error（34-36）；`#0F766E` 搜索文字（301-305） |
| `SearchBar.vue` | 灰底 `#F4F4F4`+`999rpx`+72rpx+取消按钮（145-159）；**全仓 0 引用** |
| `ExpertSearch.vue` / `BrandHeader.vue` | 底 `--home-bg`+`2rpx --home-border`+pill+88rpx；清除 icon-error；防抖 400ms（不动） |
| `TabManager.vue` | 两弹层裸 input（237-246/289-298）；表单输入框走 `--home-input-bg`（1141/1154 等，**不在范围**） |
| `TargetSelector.vue` | `ts-popup-search` 弹层搜索（25-38）：灰底胶囊（样式 ~337）、无图标、文本 `✕`（35-37）；`ts-trigger` 触发器（213-245，**非搜索框、不在范围**） |

### 页面层

| 文件 | 当前实现状态 |
|------|-------------|
| `home/components/SearchBar.vue` | 伪框：`--home-action-secondary-bg`+pill+64rpx（167-183）；`navigateTo` 跳搜索页（84-86）；不在 32 处 token 引用内 |
| `AllCategories.vue` | `#f5f5f5`+`12rpx`+focus 品牌边+阴影（237-252）；清除 icon-close（23-25） |
| `follows/index.vue` | 底 `--home-bg`+pill（344-362）；**无清除 DOM**（4-13） |
| `live-manage/list.vue` | 白底胶囊+`1rpx $color-border-input`+`$radius-full`，**默认底 `--home-input-bg`**（1783-1791）；focus 白底主色边（1794-1797）；无图标+实心按钮（4-7/1800-1817）；回车+按钮双触发 |
| `live-manage/edit.vue` | 标签弹层裸 input（357-365）；过滤逻辑 `filteredTagItems`（369-377） |
| `live-manage/create.vue` | `.picker-search`/`.search-input`/`.search-btn`（2080-2117）**死样式，无模板对应** |
| `admin/expert-list/index.vue` | `--home-card` 白底+`1rpx --home-divider`（半透明）+`12rpx`（864-873）；`filter-tag`（898-909） |
| `admin/brands` / `admin/tags` | `#f0f1f3`+`8rpx`+文本 `✕`（brands:530-563 / tags:374-391） |
| `admin/users/index.vue` | `--home-input-bg`+`$radius-full`+高 68rpx（651-660）；`:focus-within` 白底+`box-shadow 0 0 0 3rpx $color-primary-light`（661-663）；文本 `✕`（43） |
| `admin/messages/index.vue` | `--home-input-bg`+`$radius-full`（556-561）；focus 白底（567）；文本 `✕`（38） |
| `admin/departments/index.vue` | `--home-card`+`10rpx`（1287-1294）；文本 `✕`（42） |
| `admin/featured/index.vue` | 图标/清除在 input 胶囊外（22-36）；`--home-input-bg`+pill+focus 品牌边+光晕（708-725）；`:focus-within`（721） |

### 被动生效

| 文件 | 说明 |
|------|------|
| `src/pages/app/search/index.vue`、`results.vue` | 复用 SearchNavBar，随范本生效；页面布局不改 |

---

## 七、风险与阻碍项清单（17 项）

| # | 阻碍项/风险 | 严重度 | 影响 | 处理建议 |
|:-:|------------|:---:|------|----------|
| 1 | **token 误伤**：`--home-input-bg` 32 处引用多为表单/弹层/占位 | 🔴 高 | 全站表单输入框视觉漂移 | 红线：token 只加不改；改动文件清单内不得出现非搜索选择器 |
| 2 | **硬编码灰底改写遗漏**：`#f5f5f5`×2、`#f0f1f3`×2、`--home-input-bg`×5 | 🔴 高 | 部分搜索框残留灰底，风格不齐 | 每阶段结束后 grep 校验（按搜索容器选择器，见 P3 白名单规则） |
| 3 | **无共享容器 + 多页手改** | 🔴 高 | "统一"做成 16 份近似拷贝，下轮又分裂 | S3 共享容器先于批量铺开 |
| 4 | **M2 当同构批量改**（users/messages 有 focus 光晕、departments 是白底） | 🔴 高 | 改错或漏删 focus 光晕 | 已拆 M2a/b/c 三组，逐组核对 `:focus-within` 块 |
| 5 | **清除钮字形不确定**：`\e620` 是否自带圆环不可知 | 🟠 中 | 双圆叠影脏视觉 | CSS 自绘（S2），零字形依赖 |
| 6 | **对比度**：页面背景 `#F7F9FB`/白导航上白底胶囊轮廓弱 | 🟠 中 | 输入区"隐形"或过重 | 边框 `#E5E7EB` + 零阴影；C4 兜底链（2.2） |
| 7 | **弹层 DOM 结构调整**（P0/P1/P2 裸 input 或灰底补图标/清除） | 🟠 中 | 搜索接线/事件链受影响 | 只加并列元素不改 input 属性；各弹层单独三端验证 |
| 8 | **清除接线回归**（C3/P2：清除→清空 keyword→刷新过滤） | 🟠 中 | 清除后列表不刷新 | 接线挂既有过滤函数，单独验证 |
| 9 | **live-manage/list 按钮语义**：实心→文字后热区缩小 | 🟠 中 | 双触发破坏、误触率上升 | 只改样式保留 DOM；热区 ≥64rpx |
| 10 | **featured 图标收进胶囊**：64rpx 内三元素同排 | 🟢 低 | placeholder 截断/布局挤压 | 图标 28rpx + padding 收敛，单独验证 |
| 11 | **MP 兼容**：`:focus-within`/`caret-color` 不稳定；S2 伪元素渲染差异 | 🟠 中 | 聚焦态失效/清除钮渲染异常 | 范本纪律：默认态即最终态；S2 备选内层 view 画叉 |
| 12 | **两套 token 体系并存**（CSS `--home-*` vs SCSS `$color-*`） | 🟢 低 | 色值细差 | 收敛到 `#E5E7EB` 同值，不合并体系 |
| 13 | **filter-tag 共存**（expert-list） | 🟢 低 | 标签与胶囊不齐/裁切 | 圆角同步 + 验证 |
| 14 | **管理端高度三档未定**（64/68/72） | 🟢 低 | 改完仍高低不齐 | 阶段 0 定档：统一 64rpx，list 单独评估 |
| 15 | **共享容器优先级冲突**（公共类 vs scoped 样式） | 🟠 中 | 局部覆盖失败/公共类被覆盖 | 阶段 1 验证覆盖链（类名权重+局部变量） |
| 16 | **TargetSelector 搜索接线**（featured 链路） | 🟠 中 | 选择器搜索失效 | P0 单独验证 `handleSearch/applySearch/clearSearch` |
| 17 | **无样式测试**（Vitest 全 mock，无样式回归能力） | 🟠 中 | 回归靠人工 | 6 批小步提交 + 每批三端预览 + 19 处勾验表 |

---

## 八、阶段实施规划

> 每阶段完成后必须通过对应核查评估（清单全部打勾）方可进入下一阶段；任一核查不达标 → 修复后重验。
> **通用退出条件（所有阶段强制）**：`pnpm lint`（针对性，零新增问题）+ `pnpm build:h5` 编译通过；涉及交互的改动三端（微信小程序/App/H5）预览验证。

### 阶段 0：前置核查（0.25d）

**内容**：① 19 处现状三端截图基线（回归对照用）；② 用户确认例外项（4.3 五项）——C5（闲置 SearchBar 删/留）、C2 高度档位（72/88）、C4 白底胶囊辨识度兜底方案、M1 filter-tag 圆角、共享容器形式（S3 方案 A/B）；③ 管理端高度定档（统一 64rpx，list 单独评估）；④ TargetSelector 纳入范围确认（弹层搜索在、触发器不在）；⑤ S2/S3 跨端可行性验证（伪元素与公共类覆盖链）。

**执行记录（2026-08-31）**：

| 项 | 结果 |
|----|------|
| ① 基线 | ✅ 19 处清单已含行级现状快照（第三章，代码侧基线）；⏳ 三端截图待人工（微信开发者工具/App 真机/H5 浏览器各 19 张，存 `docs/` 或团队共享目录） |
| ② 决策 6 项 | ✅ **全部确认（2026-08-31）**：D1 删除 / D2 72rpx / D3 边框起手 / D4 同步胶囊 / D5 方案 A / D6 统一 64rpx（list 保持 72rpx 特殊评估，见下） |
| ③ 管理端高度 | ✅ 统一 64rpx（users 68→64）；**live-manage/list 单独保持 72rpx**（输入框与文字化按钮同高对齐、场景特殊，阶段 4 实施时复核） |
| ④ TargetSelector 范围 | ✅ 已静态核实：弹层搜索（25-38/333-361）纳入；`ts-trigger` 触发器（213-245，非搜索框）排除 |
| ⑤ S2 可行性 | ✅ **静态证实**：全仓 `::before/::after` 跨端先例 18+ 处（TabManager:1390、ChatTab:495、InputModal:214、ScrollablePickerSheet:257、ModalDialog:227、follows:416、live-manage 系列等，App 端组件为主）→ CSS 自绘方案可行；`caret-color` 品牌色有先例（SearchNavBar:248、AllCategories:269） |
| ⑤ S3 覆盖链 | ⏳ 待阶段 1 实机验证（公共类 + scoped 局部覆盖的类名权重链路；静态上项目无先例，属新引入模式） |

**核查评估**：
- [x] 19 处代码侧基线快照已登记（行级）
- [x] 6 项决策已确认（D1-D6，2026-08-31）
- [x] ClearButton 伪元素可行性静态确认（18+ 跨端先例）；共享容器覆盖链待阶段 1 实机验证
- [ ] 三端截图基线（⏳ 待人工，不阻塞阶段 1 代码实施）

**退出条件**：代码侧核查项已全过；截图项不阻塞阶段 1（阶段 5 勾验前补齐即可）。**阶段 0 结论：核查完成，可进入阶段 1。**

**阶段 0 决策记录（2026-08-31 已确认）**：

| # | 决策 | 结论 | 影响 |
|:-:|------|------|------|
| D1 | C5 闲置 `SearchBar.vue` | **删除** | C5 实施=删除文件 |
| D2 | C2 高度档位 | **72rpx** | Expert/Brand 88→72，与 C 端列表档一致 |
| D3 | C4 辨识度兜底 | **边框 `#E5E7EB` 起手**，不足再加深、仍不足加极轻阴影 | C4 按此链实施 |
| D4 | M1 filter-tag 圆角 | **同步胶囊** | M1 同步标签圆角 |
| D5 | S3 共享容器 | **方案 A 公共类 `.app-search-field`** | 覆盖链验证失败才回退方案 B |
| D6 | 管理端高度 | **统一 64rpx**；list 单独保持 72rpx（按钮对齐） | M2b users 68→64；M4 list 保持 72 |

### 阶段 1：基础设施（S1-S3，0.25d）✅ 完成（2026-08-31）

**内容**：S1（8 个 token 追加）→ S2（ClearButton 组件）→ S3（共享容器 `.app-search-field`）。

**代码落地记录**：

| 项 | 文件:位置 | 修改内容 |
|:-:|----------|----------|
| S1 | `src/common/uni.scss:143-151` | :root 追加 8 个 `--search-*` token（**纯新增**，git diff 证实 0 删除；既有 token 零修改） |
| S2 | 新建 `src/components/app/ClearButton.vue` | 清除钮小组件：热区 64rpx（size prop 可调）+ 视觉 40rpx 灰圆（`--search-clear-bg`）+ 内层双 view 画白叉（`--search-clear-icon`）；`@tap.stop` emit `clear`；**零 iconfont 依赖**（采用文档 2.4 备选方案"内层 view 画叉"，规避伪元素跨端差异） |
| S3 | `src/common/uni.scss:174-207` | 新增 `.app-search-field`（容器：白底/1rpx 细边/胶囊/72rpx 默认高，页面按场景覆盖）+ `__icon`（线稿灰标槽）+ `__input`（透明重置 + caret-color 未写入，遵循"默认态即最终态"纪律；placeholder 注释说明小程序走 placeholder-class） |

**核查评估**：
- [x] 针对性 eslint（ClearButton.vue）：**零问题**（npx eslint 无输出）
- [x] 全量 lint：46 errors/146 warnings 均为**存量**（docs/ref-wechat、h5、auth、LiveView 等未改动文件；与管理页面实施文档记载的存量基线一致），本次改动文件零新增
- [x] `pnpm build:h5` 编译通过（DONE Build complete；platform.ts dynamic-import 警告为存量环境性提示）
- [x] git diff 确认改动范围最小：仅 `uni.scss` +45 行（0 删除）+ 新建 `ClearButton.vue`；工作区其余 15 个 M 文件为既有未提交状态（管理页面修复实施遗留），非本次改动
- [x] 命名冲突检查：`--search-*`/`.app-search-field`/`ClearButton` 全仓无既有同名（grep 已证）
- [x] 共享容器覆盖链：静态成立（scoped 局部类权重 0,2,0 > 公共类 0,1,0，局部高度可覆盖）；实机验证随阶段 2 T1 引用该容器时执行

**阶段 1 结论**：S1-S3 共 3 处代码落地完成，静态检查与编译全部通过，零冲突、零既有代码改动。**遗留：共享容器实机覆盖链验证（阶段 2 执行）。**

**退出条件**：全过 ✅ → 进入阶段 2。

### 阶段 2：范本（T1，0.25d）✅ 代码落地完成（2026-08-31），三端预览待人工

**内容**：SearchNavBar 按 2.2/2.3/2.4 改造（默认态即白底细边胶囊、focus 仅加深边线、清除换组件、保留主色"搜索"文字与返回/搜索交互）。

**代码落地记录**：

| 项 | 文件:位置 | 修改内容 |
|:-:|----------|----------|
| T1-模板 | `SearchNavBar.vue:15` | 胶囊容器叠加共享类：`class="search-capsule"` → `class="app-search-field search-capsule"`（**S3 覆盖链首次实机验证点**） |
| T1-模板 | `SearchNavBar.vue:33-35` | 清除按钮替换：旧 `view.clear-btn + iconfont icon-error` → `<ClearButton v-if="keyword" @clear="handleClear" />`（灰圆白叉共享组件；`@tap.stop` 内置，handleClear 逻辑不变） |
| T1-脚本 | `SearchNavBar.vue:54` | `import ClearButton from './ClearButton.vue'` |
| T1-样式 | `SearchNavBar.vue:209-217` | `.search-capsule` 精简：仅保留 `width/height:64rpx`（覆盖公共类默认 72rpx，验证 scoped 覆盖链）+ `padding/box-sizing`；底色/边框/圆角全部由 `.app-search-field` 提供；`:focus-within` 改为仅 `border-color: var(--search-border-focus)`（去白底切换/品牌色边框/阴影） |
| T1-样式 | `SearchNavBar.vue:219-226` | `.search-icon`：`#999` → `var(--search-icon)`；**删除** `.search-capsule:focus-within .search-icon { color:#0F766E }`（品牌色只留光标与搜索文字） |
| T1-样式 | `SearchNavBar.vue:246-250` | `.search-placeholder`：`#999999` → `var(--search-placeholder)` |
| T1-样式 | 删除 | `.clear-btn`/`.clear-icon` 样式块（模板已换 ClearButton，无残留引用） |

**核查评估**：
- [x] 针对性 eslint（SearchNavBar + ClearButton）：**0 errors**（2 个存量 warnings：`navbarHeight`/`handleSearchBoxClick` 未使用，改动前已存在）
- [x] `pnpm build:h5` 编译通过（DONE Build complete）
- [x] `pnpm build:mp-weixin`：**失败为存量问题**——`src/pages/h5/room/RoomList.vue` 的 `v-loading` 指令（Element Plus 指令不支持 mp 编译），该文件未改动且 h5 不在实施范围；本次组件未在错误列表中出现
- [x] **S3 覆盖链验证**：`.app-search-field`（0,1,0）高度 72rpx 被 scoped `.search-capsule`（0,2,0）64rpx 成功覆盖，H5 构建产物确认生效；后续各页沿用此模式
- [ ] 三端人工预览（微信开发者工具导入 `dist/build/mp-weixin` / App 真机 / H5）：默认态白底细边、无品牌色 focus 边框；清除钮灰圆白叉热区正常；聚焦态不依赖灰→白切换（⏳ 待人工，不阻塞阶段 3 代码实施）
- [x] 交互零改动：`handleClear`/`handleInput`/`handleConfirm`/`handleSearch`/`handleBack` 全部保留（仅清除按钮由 view 换组件，事件语义一致）

**阶段 2 结论**：T1 共 7 处代码落地完成，编译与静态检查通过，S3 覆盖链实证生效，交互逻辑零改动。**遗留：三端人工预览（验证环境执行）。**

**退出条件**：代码层全过 ✅（预览项人工执行，不阻塞代码层面）→ 进入阶段 3。

### 阶段 3：C 端批量（C1-C5，0.5d）✅ 代码落地完成（2026-08-31），三端预览待人工

**内容**：C1（AllCategories）→ C2（ExpertSearch/BrandHeader）→ C3（follows，补清除 DOM+接线）→ C4（首页伪框）→ C5（闲置组件删除）。

**代码落地记录**：

| 项 | 文件:位置 | 修改内容 |
|:-:|----------|----------|
| C1 | `AllCategories.vue` | 模板（12-27）：容器叠加 `app-search-field search-box`、清除 icon-close → `<ClearButton @clear="searchKeyword=''">`；import ClearButton；样式：删 `.search-box` 灰底/12rpx/2rpx 透明边/focus 品牌块/icon 聚焦变色/`.clear-btn/.clear-icon`，icon `var(--search-icon)`+margin-right 12rpx、placeholder `var(--search-placeholder)`；`.search-container` 外层容器保留 |
| C2 | `ExpertSearch.vue` | 容器叠加 `app-search-field`（高度 88→72rpx，D2）、删 `--home-bg` 灰底+2rpx 边框+pill 圆角、清除 icon-error → `<ClearButton @clear="onClear">`、自绘 placeholder 颜色 `var(--search-placeholder)`、icon `var(--search-icon)`；防抖 400ms 逻辑零改动 |
| C2 | `BrandHeader.vue` | 同上（高度 88→72、去灰底/2rpx 边、清除换组件、icon token 化）；`onClear` 逻辑零改动 |
| C3 | `follows/index.vue` | 模板（4-14）：容器叠加 `app-search-field`、**补清除 DOM** `<ClearButton v-if="searchKeyword" @clear="handleClearSearch">`；script 新增 `handleClearSearch`（清空 `searchKeyword`，过滤由 `filteredListByTab` 计算属性实时驱动——**接线完成**）；样式：容器删 `--home-bg` 灰底/pill 圆角/padding，icon `var(--search-icon)` |
| C4 | `home/components/SearchBar.vue` | 伪框叠加 `app-search-field`（高度覆盖 64rpx 导航档，D6 档位）；删 `--home-action-secondary-bg` 灰块；`:active` 改 opacity 反馈（保持白底细边最终态）；icon/占位文字 token 化（D3 兜底链：细边框起手）；点击跳转逻辑零改动 |
| C5 | 删除 `src/components/app/SearchBar.vue` | ✅ D1 确认：全仓 0 引用，`Remove-Item` 删除（Test-Path 确认不存在） |

**核查评估**：
- [x] 针对性 eslint（5 个改动文件）：**0 errors**（1 个存量 warning：ExpertSearch `props` 未使用，改动前已存在）
- [x] `pnpm build:h5` 编译通过（DONE Build complete）
- [x] **grep 白名单校验**：C 端 5 文件搜索容器灰底零残留——AllCategories:313 `#f5f5f5` 为 `.tag-item` 标签背景（白名单允许）；follows:346 `--home-bg` 为页面容器背景（白名单允许）；ExpertSearch/BrandHeader/home SearchBar 搜索容器零匹配
- [x] C3 接线验证（静态）：清除 → 清空 `searchKeyword` → 计算属性 `filteredListByTab` 自动刷新
- [x] 交互零改动：各页 `@input/@confirm/handleSearch` 等事件保留；C5 删除前 grep 确认无引用
- [ ] 三端人工预览：4 页白底细边胶囊、清除钮灰圆白叉、首页伪框与头像/消息并排对比度达标（⏳ 待人工，不阻塞阶段 4）

**阶段 3 结论**：C1-C5 共 6 处代码落地 + 1 文件删除，编译与静态检查通过，搜索容器灰底零残留。**遗留：三端人工预览。**

**退出条件**：代码层全过 ✅ → 进入阶段 4。

### 阶段 4：管理端（M1→M2c→M2a→M2b→M3→M4，0.5d）✅ 代码落地完成（2026-08-31），三端预览待人工

**内容**：M1（expert-list 微调）→ M2c（departments，并入批次）→ M2a（brands/tags）→ M2b（users/messages，**含删 focus 光晕**）→ M3（featured 结构归位）→ M4（list 去灰底+补图标+按钮文字化+删 focus 灰白切换）。

**代码落地记录**：

| 项 | 文件 | 修改内容 |
|:-:|------|----------|
| M1 | `expert-list/index.vue` | `filter-search` 叠加 `.app-search-field`（高度 64 覆盖）；边框 `--home-divider` 半透明→实心 `--search-border`（公共类）；清除文本 `✕` → `<ClearButton @clear="searchKeyword=''">`；**filter-tag 圆角同步胶囊**（D4：`--home-r-md`→`--home-r-pill`，边框同步实心） |
| M2c | `departments/index.vue` | 白底近达标仅微调：`10rpx`→胶囊（公共类）、删除 `rgba(0,0,0,0.06)` 边框、清除换 ClearButton、icon/placeholder token 化 |
| M2a | `brands/index.vue`、`tags/index.vue` | 灰底 `#f0f1f3`+`8rpx` 方框 → 公共类白底细边胶囊（高度 64）；清除换 ClearButton（复用既有 `clearSearch` 函数）；icon `var(--search-icon)` |
| M2b | `users/index.vue`、`messages/index.vue` | **删除 `:focus-within` 白底+`box-shadow 0 0 0 3rpx $color-primary-light` 光晕**（users:661-663 / messages:567，grep 验证零残留）；`--home-input-bg` 灰底→公共类白底；**高度 68→64rpx**（D6）；清除换 ClearButton |
| M3 | `featured/index.vue` | **结构归位**：图标/清除从胶囊外收进胶囊（新增 `search-capsule` 容器包 icon+input+ClearButton）；删 `--home-input-bg` 灰底、focus 品牌边+光晕（含 `:focus-within`）；`@input/@confirm` 事件绑定原样保留；删 `.search-clear/.search-clear-text`（原 72rpx 圆形灰底文本 ✕） |
| M4 | `live-manage/list.vue` | **结构改造**：新增 `admin-search-field` 胶囊容器（icon+input+ClearButton 收进）；**默认底去灰**（`--home-input-bg`→公共类白底，删除 focus 灰→白切换+主色边框）；**按钮实心主色→主色文字**（热区 72rpx、active opacity 反馈）；新增 `handleAdminClearSearch` 接线（清空 `adminSearchQuery` → 复用 `handleSearch()` 分发刷新，admin/manage 双模式）；**回车+按钮双触发保留**；高度保持 72rpx（D6 特例） |

**核查评估**：
- [x] 针对性 eslint（8 个改动文件）：**零新增**——4 项全存量：expert-list `expandedExpertId/getBio` 2 warnings（基线 347/403 位移至 349/405）、featured `no-unsafe-finally`（基线 408→423 位移）、list `withRetry` 泛型箭头解析错误（基线 462→487 位移，管理页面实施文档均记载）
- [x] `pnpm build:h5` 编译通过（DONE Build complete）
- [x] **grep 校验**：admin 目录 `filter-search:focus-within`/`filter-clear`/`search-clear` **零残留**（M2b 光晕删除彻底、M3 旧清除样式删除）；`--home-input-bg` 仅存于非搜索处（list:1536 `.admin-owner` 标签、detail/create 表单，白名单允许）
- [x] list 双触发保留（`@confirm="handleSearch"` + 按钮 `@tap="handleSearch"`）；按钮热区 72rpx ≥64rpx；admin/manage 双模式共用同一搜索栏
- [x] M3 结构归位：事件绑定 `handleSearchInput/handleSearchConfirm/clearSearch` 原样保留
- [ ] 三端人工预览：7 页视觉统一、filter-tag 不裁切、featured placeholder 不截断、list 双模式外观一致（⏳ 待人工，不阻塞阶段 5）

**阶段 4 结论**：M1-M4 共 8 文件 14 处代码落地，编译与静态检查通过，focus 光晕零残留。**遗留：三端人工预览。**

**退出条件**：代码层全过 ✅ → 进入阶段 5。

### 阶段 5：弹层与收尾（P0-P3，0.5d）✅ 完成（2026-08-31）—— 实施全部闭环（三端人工预览待执行）

**内容**：P0（TargetSelector）→ P1（TabManager 两弹层）→ P2（edit.vue 标签弹层，含接线）→ P3 收尾（create.vue 死样式删除 + 19 处勾验 + grep 白名单）。

**代码落地记录**：

| 项 | 文件 | 修改内容 |
|:-:|------|----------|
| P0 | `TargetSelector.vue` | 弹层搜索补图标+胶囊（`ts-popup-field` 叠加公共类，高度 64）；灰底 `--home-input-bg`→白底细边；文本 `✕`→`<ClearButton @clear="clearSearch">`（**接线复用既有 clearSearch：清空+loadOptions 重载**）；删 `.ts-popup-clear/.ts-popup-clear-text`（原热区仅 44rpx）；placeholder token 化 |
| P1 | `TabManager.vue`（两弹层） | 专家/品牌弹层裸 input → 胶囊+图标+ClearButton（`handleExpertClearSearch`/`handleBrandClearSearch`：清空 keyword → 复用防抖搜索 `handleExpertSearchInput`/`handleBrandSearchInput` 重新加载）；删 `--home-bg` 灰底+1.5rpx 边框+12rpx |
| P2 | `edit.vue`（标签弹层） | 裸 input → 胶囊+图标+ClearButton（**接线：清空 `tagKeyword`，`filteredTagItems` 计算属性自动刷新**）；删灰底/边框 |
| P3 | `create.vue` | **删除死样式** `.picker-search`/`.search-input`/`.search-btn`（2080-2117，grep 证实无模板引用） |

**核查评估**：
- [x] 针对性 eslint（4 文件）：**0 errors**（4 个存量 warnings：create `get`、edit `onMounted/statusLabelMap/result` 未使用）
- [x] `pnpm build:h5` 编译通过（DONE Build complete）
- [x] **19 处逐项勾验**：`.app-search-field` 模板容器 18 处（TabManager×2 计 2 处）+ C5 删除 1 处 = 19/19 全覆盖；ClearButton 引用 17 处（16 文件）
- [x] **grep 白名单**：TargetSelector `ts-popup-clear` 零残留；`--home-input-bg` 仅存于非搜索处（`ts-trigger` 触发器、表单、`.admin-owner` 标签等，白名单允许）
- [x] **测试基线**：`pnpm test:run` **12 failed / 70 passed（82）与存量一致，零回归**——13 个 Failed Suites 为测试路径过时（`AppButton.vue` 等旧路径）；12 个 Failed Tests 中 3 个（api_room options 断言）为管理页面阶段 7 加向后兼容 options 参数引入、9 个（store_room/store_session）为 store 行为变更遗留；本次改动文件（纯 .vue/.scss）不涉及 api/store/request 逻辑，零影响
- [ ] 三端人工预览（⏳ 待执行）：19 处视觉统一、四弹层接线、list 双模式、首页伪框对比度

**阶段 5 结论**：P0-P3 共 4 文件 7 处代码落地 + 死样式清理，编译/静态/测试基线全部通过，19 处勾验闭环。**遗留：三端人工预览清单（见下）。**

**退出条件**：全过 ✅ → 发布（代码层已达成；人工预览项完成后即可发布）。

**三端人工预览清单（待执行）**：
1. 微信开发者工具导入 `dist/build/mp-weixin`（需先解决存量 `h5/room/RoomList.vue` v-loading 编译问题或按单页调试）；App 真机（HBuilderX）；H5 `dist/build/h5`
2. 19 处逐处核对：白底+1rpx 细边+胶囊、灰圆白叉清除钮（热区正常）、无品牌色 focus 边框/光晕
3. 交互冒烟：清除按钮各页生效（follows/edit/TabManager/list 接线）、list 回车+按钮双触发、首页伪框跳转、TargetSelector 选择器搜索
4. 首页伪框与头像/消息并排对比度（D3 兜底链：细边框不足再加深/加阴影）

---

## 九、改动量与难度汇总

| 量级 | 项数 | 明细 | 小计 |
|:---:|:---:|------|:---:|
| S | 17 | S1-S3、T1、C1-C5、M1、M2a、M2c、P0、P2、P3 | 1.5-2d |
| M | 6 | C3（接线）、M2b、M3、M4、P1、S3（容器方案 B 时） | 1-1.5d |
| 前置/收尾 | 2 | 阶段 0、阶段 5 勾验 | 0.5d |
| **合计** | **23** | | **3-4 人日**（纯样式/DOM 归位/少量接线，无后端依赖） |

---

## 十、验收标准（总）

1. 19 处搜索 UI 三端（微信小程序/App/H5）视觉统一：白底 + `1rpx #E5E7EB` 细边 + 胶囊圆角 + 线稿灰图标 + 灰圆白叉清除钮；管理端高度统一 64rpx。
2. 聚焦态无品牌色粗边/阴影/光晕；品牌色仅出现于"搜索"文字与光标；全部 `:focus-within` 灰→白切换逻辑已删除。
3. 全部交互零回归：防抖、客户端过滤、服务端搜索、回车/按钮双触发、伪框跳转、TargetSelector 搜索接线行为不变；C3/P2 新增清除接线工作正常。
4. `--home-input-bg` 及其 32 处非搜索引用零改动；表单输入框视觉零变化。
5. grep 白名单校验通过：搜索容器选择器无灰底残留；`--home-input-bg` 仅存在于非搜索处。
6. `pnpm lint` 针对性零新增问题；`pnpm build:h5` 通过；`pnpm test:run` 存量基线对比零回归。

---

## 十一、变更记录

| 版本 | 日期 | 变更内容 |
|:----:|:----:|---------|
| v1.0 | 2026-08-31 | 初版：基于会话内多轮独立分析对比（B 站截图拆解 / 双方审查互评） + 18 处源码逐行核实的实施规划（21 项 + 5 套方言归类 + 13 项风险阻碍 + 6 阶段 + 边界清单）；吸取既有文档范式（实施规划文档：结论先行/清单表/阶段退出条件；设计文档：Design Token 定义/组件规范） |
| v1.1 | 2026-08-31 | **方案审查修订**：① 管理端 M2 拆三组（M2a brands/tags 灰底方框、M2b users/messages 灰底胶囊+focus 光晕、M2c departments 白底微圆角 10rpx），修正"5 页同构"误判；② 补漏 TargetSelector 弹层搜索（第 19 处，P0）；③ 新增 S3 共享容器 `.app-search-field` 防复制分叉（风险 #3）；④ Token 数量修正 7→8；⑤ C3/P2 明确含清除接线逻辑（非纯样式）；⑥ M4 明确删 focus 灰白切换；⑦ 新增 create.vue 死样式清理（P3）与 grep 白名单规则；⑧ 新增风险 #14-17（高度定档/容器优先级/TargetSelector 接线）；⑨ 实施项 21→23 项，工作量 2.5-3.5 → 3-4 人日；⑩ 阶段 0 决策扩为 6 项 |
| v1.2 | 2026-08-31 | **阶段 0 完成（核查+决策）**：① 基线快照登记（19 处行级现状，第三章）；② **6 项决策全部确认**——D1 删除闲置 SearchBar / D2 Expert·Brand 高度 72rpx / D3 C4 兜底链边框 `#E5E7EB` 起手 / D4 filter-tag 同步胶囊 / D5 共享容器方案 A 公共类 / D6 管理端统一 64rpx（list 保持 72rpx）；③ TargetSelector 范围确认（弹层搜索纳入、触发器排除）；④ S2 可行性静态证实（全仓 `::before/::after` 跨端先例 18+ 处、caret-color 先例 2 处）；⑤ 相关章节（2.2/2.5/4.3/五/八）同步决策结论；⏳ 遗留：三端截图基线（人工，不阻塞阶段 1） |
| v1.3 | 2026-08-31 | **阶段 1 完成（S1-S3 基础设施）**：uni.scss 追加 8 个 `--search-*` token（纯新增、git diff 证实 0 删除）；新建 ClearButton.vue（内层 view 画叉方案，零 iconfont 依赖）；新增 `.app-search-field` 公共容器类；针对性 eslint 零问题、build:h5 通过、命名冲突零；工作区其余 15 个 M 文件为既有未提交状态（非本次改动）；遗留：共享容器实机覆盖链验证（阶段 2 T1 执行） |
| v1.4 | 2026-08-31 | **阶段 2 完成（T1 范本）**：SearchNavBar 改造——胶囊叠加 `.app-search-field` 公共类（覆盖链实证：scoped 64rpx 覆盖公共 72rpx）、清除按钮换 ClearButton 组件（删 `.clear-btn/.clear-icon`）、focus 仅加深边线（去白底切换/品牌色边框/阴影）、图标与 placeholder token 化、删 icon focus 变色；eslint 0 errors（2 存量 warnings）、build:h5 通过、build:mp-weixin 失败为存量（h5 RoomList v-loading，非本次引入）；交互逻辑零改动；遗留：三端人工预览 |
| v1.5 | 2026-08-31 | **阶段 3 完成（C 端批量 C1-C5）**：AllCategories/ExpertSearch/BrandHeader 容器叠加 `.app-search-field`（高度 88→72rpx）、清除全部换 ClearButton；follows 补清除 DOM + `handleClearSearch` 接线（计算属性驱动）；首页伪框对齐（64rpx 覆盖 + opacity 按压反馈 + D3 兜底链）；**删除闲置 SearchBar.vue（D1）**；eslint 0 errors（1 存量 warning）、build:h5 通过、grep 白名单校验搜索容器灰底零残留（tag-item/页面背景为白名单允许）；遗留：三端人工预览 |
| v1.6 | 2026-08-31 | **阶段 4 完成（管理端 M1-M4）**：expert-list（filter-tag 同步胶囊 D4）+ departments（M2c 微调）+ brands/tags（M2a 灰底方框全量改）+ users/messages（M2b **删 focus 光晕**、高度 68→64 D6）+ featured（M3 **结构归位**：图标收进胶囊）+ live-manage/list（M4：包容器补图标、去默认灰底、删 focus 灰白切换、按钮实心→主色文字、新增 `handleAdminClearSearch` 接线复用 handleSearch 分发、双触发保留）；eslint 零新增（4 项全存量：expert-list 2 warnings/featured no-unsafe-finally/list withRetry 解析错误，行号随改动位移）；build:h5 通过；grep 校验 admin `:focus-within` 光晕与旧清除样式零残留、`--home-input-bg` 仅存于非搜索处；遗留：三端人工预览 |
| v1.7 | 2026-08-31 | **阶段 5 完成（P0-P3 弹层与收尾）→ 实施全部闭环**：TargetSelector 补图标+胶囊+ClearButton（接线复用 clearSearch）；TabManager 两弹层补图标+清除（`handleExpertClearSearch`/`handleBrandClearSearch` 复用防抖搜索）；edit.vue 标签弹层补图标+清除（计算属性自动刷新）；**create.vue 死样式删除**（picker-search/search-input/search-btn）；eslint 0 errors（4 存量 warnings）、build:h5 通过；**19 处勾验全覆盖**（app-search-field 容器 18 处 + 删除 1 处）；grep 白名单通过；`pnpm test:run` 12 failed/70 passed 与存量一致零回归（api_room 3 失败为管理页面阶段 7 options 参数引入、store_* 9 失败为行为变更遗留，均非本次）；遗留：三端人工预览清单（已文档化） |
| v1.8 | 2026-08-31 | **清除钮叉号几何修复**：ClearButton.vue 原用"横线+竖线"（视觉 **+** 加号，S2 实现错误），改为**两条 ±45° 对角线**（视觉 **×** 叉号，对齐 B 站）；仅改该组件内部（模板类名 `--h/--v`→`--a/--b`、样式 transform 加 rotate），17 处引用零页面改动自动修复；eslint 零问题、build:h5 通过、`bar--h/--v` 残留零 |
| v1.9 | 2026-08-31 | **SearchNavBar 一体结构范本（消除三块分割缝）**：B 站截图对比诊断——"三块视觉/聚焦边界高亮"根因是 **flex 三列（icon｜原生 input｜清除）的兄弟缝**（App/部分小程序原生 input 层间渲染缝，CSS 边框清除压不掉）；改造为 **"输入区铺满 + absolute 悬浮装饰"**：`.search-capsule` 加 `position:relative`；`.search-icon` absolute 左 24rpx（z-index 2）；`.search-input` absolute 四边铺满整条胶囊（z-index 1，padding 左 68rpx 让位 icon/右 84rpx 让位清除区）；`.search-clear-slot`（新模板包装层）absolute 右 10rpx 悬浮 ClearButton——**v-if 显隐不再影响布局，框宽恒定**；**删除 `:focus-within` 边框加深**（聚焦零框变化，仅品牌色光标 `caret-color`）；eslint 0 errors（2 存量 warnings）、build:h5 通过；**待三端真机验证缝消失后，将本结构抽入 `.app-search-field` 公共类并铺开其余 17 处** |
| v1.10 | 2026-08-31 | **视觉收敛调整（用户实机反馈）**：① **边界加深**：`--search-border` #E5E7EB→**#C9CDD4**（更明显）；② **形状改圆角矩形**：`--search-radius` 999rpx（全胶囊）→**20rpx**（B 站 UISearchBar 圆角矩形比例）；③ **清除钮去圆底改 iconfont 叉**：ClearButton 重构——删除灰圆+CSS 白叉绘制（circle/bar 全移除），改为 `<text class="iconfont icon-close">` 直出（`--search-clear-icon` #FFFFFF→**#6B7280** 可见灰），热区 64rpx 保留；④ **光标压图标修复（初版）**：SearchNavBar `.search-input` 改几何让位（`left:68rpx; right:84rpx`）；⑤ 清理无引用 token：删除 `--search-clear-bg`、`--search-border-focus` |
| v1.11 | 2026-08-31 | **三块视觉回归修复（实机反馈 v2）**：v1.10 几何让位（`right:84rpx` 常驻预留）导致**无字时右端 84rpx 空槽** → 三块视觉回归（图标区/输入岛/空槽）。修复：`.search-input` 恢复 **absolute 铺满整条胶囊**（覆盖图标与清除钮下方 → input 区域=整条，任何平台原生样式差异不可见，结构上杜绝三块）；文字起点 padding-left 68rpx 让位图标；**清除区预留动态化**——新增 `search-input--clear` class（`:class` 绑定 `keyword`），**无字时 padding-right=0（占位文字可用全宽、无空槽），有字时 padding-right=84rpx（防文字压清除钮）**；eslint 0 errors（2 存量 warnings）、build:h5 通过 |
| v1.12 | 2026-08-31 | **App 端实机反馈修复 v3**：① **全局圆角回全胶囊**（`--search-radius` 20rpx→**999rpx**，用户确认"其余页面参考首页形状"= 全站胶囊；首页伪框随 token 自动恢复胶囊形态，零代码）；② **input 文字起点改几何让位**（`.search-input` `left:68rpx; right:0; padding:0`，有字时 `.search-input--clear` 收窄 `right:84rpx`）——文字/光标起点物理保证在图标之后，**不依赖 input padding**（App 端原生 input padding 渲染不确定性是"光标压图标"反复出现的根因）；③ 首页伪框确认回退白底细边胶囊（用户选型，随 ① 达成）；eslint 0 errors（2 存量 warnings）、build:h5 通过；**待 App 真机重新编译验证；其余 17 处 flex 页面结构待验证后铺开** |
| v1.13 | 2026-08-31 | **flex 稳定版定型（放弃 absolute 覆盖层，用户决策"退回三块分区"）**：复盘结论——B 站样式**可实现、非致命缺陷**；反复失败主因：absolute 覆盖层方案依赖 input padding（App 原生 input 渲染不确定）+ 各轮未在 App 真机闭环验证即迭代。定稿：SearchNavBar 改回 **flex 三区（图标｜input(flex:1)｜ClearButton v-if）**，铁律四条——① input 边框/背景/outline/box-shadow 全清（!important，无分隔线来源）；② 文字/光标起点由 flex 文档流保证（input 物理位于图标后，与 padding 无关，跨端可靠）；③ 外框宽恒定（容器 flex:1），input 无边框故 v-if 清除钮显隐零视觉变化（输入不变长）；④ 清除钮 = iconfont `icon-close` 叉号（v1.10 选型）；删除全部 absolute 定位/`search-input--has-clear`/`search-clear-slot`/APP-PLUS 条件编译；eslint 零问题、absolute 残留 0、build:h5 通过；**待 App 真机重新编译闭环验证（此前各轮均未完成此步）** |
| v1.14 | 2026-08-31 | **清除钮悬浮化（实机反馈：flex 版 v-if 清除钮挤占 input 64rpx 宽度 → 输入后右端区域左扩/分区变化；叉号仅 30rpx 视觉却引发 64rpx 布局变动）**：修复——清除钮改 **absolute 悬浮**（`.search-clear-slot` right:10rpx 垂直居中，不参与 flex）；input 增加**恒定** `padding-right: 56rpx`（预留悬浮叉位，不随内容/显隐变化）；文字起点仍由 flex 保证（图标后）。效果：输入/删除/叉号显隐全程 **input 宽度与布局零变化**；叉号视觉仅 30rpx 无大块区域。eslint 零问题、build:h5 通过。**【最终版 ✅ 全页面同步完成】**：`.search-clear-slot` 抽为全局公共类（uni.scss，absolute 右 10rpx）+ `.app-search-field` 加 `position:relative`；17 处搜索框全部同步"flex + 悬浮清除"结构——ExpertSearch/BrandHeader/AllCategories/follows/list/admin 8 页/TabManager×2/PickerSheet/TargetSelector/messages room-picker，input 统一恒定 `padding-right: 56rpx`（edit.vue 经外部重构为 PickerSheet 方案，无内联搜索框无需同步）；eslint 零新增（存量 2 errors 5 warnings 均位于未触碰 script 区）、build:h5 通过；**待 App 真机闭环验证** |
| ~~v1.15~~ | 2026-08-31 | ~~叉号贴右端圆角 + 输入区延长（slot right 4rpx/热区 44rpx/input padding-right 26rpx）~~ **❌ 已撤回（用户决定保留 v1.14 观感）** |
