# 小程序端与 App 端管理端页面对比报告

> **文档版本**：v1.0
> **创建日期**：2026-08-09
> **覆盖范围**：小程序端（`app-wechat-frontend-1` 仓库 wechat 分支）管理端页面 vs App 端（`src/pages/app/admin/` 工作区）管理端页面全量对比
> **状态**：已完成

---

## 一、结论摘要

| 维度 | 小程序端（wechat 分支） | App 端（src/pages/app/） |
|------|----------------------|------------------------|
| 管理端页面数 | 13 模块 / 22 个 vue 文件 | 9 模块 / 9 个 index.vue + 2 个共享组件 |
| 访问守卫 | 各页面内联 `ensureAdminAccess()`，**4 个模块缺失** | 统一 `useAdminGuard()`，**9 页全部接入** |
| 列表分页 | 传统分页器（上一页/下一页 + 页码） | 上拉加载 + 下拉刷新（scroll-view） |
| 请求参数 | `page` + `page_size` | `page` + `size` |
| 弹窗方案 | 每页内联 `dialog-overlay` 自绘弹窗 | 共享组件 `ModalDialog.vue` |
| Tab 切换 | 各页自写 | 共享 composable `useSwiperTabs` |
| 兼容代码 | 大量响应形态兼容（extractList/normalizeList 等） | 少，直接消费 `res.data.items` |

**模块对齐总览**：

| # | 模块 | 小程序 | App | 备注 |
|---|------|--------|-----|------|
| 1 | 用户管理 | ✅ UserList + UserEditDialog | ✅ users/index.vue | 交互形态差异大 |
| 2 | 专家管理 | ✅ ExpertAdminList | ✅ expert-list/index.vue | App 多「未映射专家」 |
| 3 | 分类/科室 | ✅ CategoryList + FormDialog | ✅ departments/index.vue | App 为两级结构 + 审核 |
| 4 | 焦点图/轮播图 | ✅ FeaturedContentList + FormDialog | ✅ featured/index.vue | App 多状态 Tab + 日期 |
| 5 | 通知推送 | ❌ **无** | ✅ notification-push/index.vue | App 独有 |
| 6 | 标签管理 | ✅ TagList + FormDialog | ✅ tags/index.vue | App 多启用/禁用 |
| 7 | 品牌管理 | ✅ BrandAdminList | ✅ brands/index.vue | |
| 8 | 品牌成员 | ✅ BrandMemberManager | ❌ **无** | 小程序独有 |
| 9 | 品牌商品 | ✅ BrandProductList | ❌ **无** | 小程序独有 |
| 10 | 留言管理 | ✅ RoomMessageList | ✅ messages/index.vue | App 多时间筛选/批量删除 |
| 11 | 内容安全 | ✅ RuleList + RuleFormDialog + LogList | ❌ **无** | 小程序独有 |
| 12 | 房间 Tab 管理 | ✅ RoomTabManager 三件套 | ✅ room-tabs 壳 + TabManager | 结构不同 |
| 13 | 全站房间管理 | ✅ AdminRoomList + AdminRoomEditDialog | ✅ live-manage/list.vue admin 模式 | App 复用列表页 |

---

## 二、访问守卫对比（关键差异）

### 小程序端：内联 `ensureAdminAccess()`

每个有守卫的页面各自复制一份（逻辑相同，未共享）：

| 页面 | 守卫位置 | 未登录 | 非管理员 |
|------|---------|--------|---------|
| UserList.vue | L313-337 | 跳 `OneTapLogin?redirect=...` | toast「暂无访问权限」+ navigateBack(1500ms) |
| ExpertAdminList.vue | L309 | 同上 | 同上 |
| AdminRoomList.vue | L253 | 同上 | 同上 |
| BrandAdminList.vue | L214-233 | 同上（1200ms） | 同上 |
| BrandMemberManager.vue | L155 | 同上 | 同上 |
| BrandProductList.vue | L160-180 | 同上 | 同上 |
| RoomTabManagerShell.vue | L23-44 | 同上 | 同上 |

**无守卫的页面（漏洞）**：CategoryList.vue、FeaturedContentList.vue、TagList.vue、ContentSafetyRuleList.vue、ContentSafetyLogList.vue —— 未登录/非管理员直接打开即可访问管理接口。

### App 端：统一 `useAdminGuard()`

- 定义：`src/composables/useAdminGuard.ts` L24-50（未登录跳 `APP_LOGIN_PATH?redirect=`，非管理员 toast「暂无访问权限」+ navigateBack/reLaunch 我的页；L55 有 `getCurrentPagePath` 辅助）
- **9 个 admin 页面全部接入**（onShow/onMounted 首行调用 `if (!useAdminGuard()) return;`）：

| 页面 | 调用位置 |
|------|---------|
| users/index.vue | L458（onShow） |
| expert-list/index.vue | L751（onShow） |
| departments/index.vue | L686（onShow） |
| featured/index.vue | L481（onShow） |
| messages/index.vue | L178（onShow） |
| notification-push/index.vue | L210（onMounted） |
| room-tabs/index.vue | L30（onShow） |
| tags/index.vue | L168（onShow） |
| brands/index.vue | L242（onShow） |

### 结论

> **小程序可采纳**：将 App 的 `useAdminGuard` 抽成共享 composable，替换 6 处内联守卫，并为 CategoryList/FeaturedContentList/TagList/ContentSafety 系列补齐守卫。

---

## 三、各模块详细对比

### 模块 1：用户管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/user/UserList.vue`(749) + `UserEditDialog.vue`(505) | `admin/users/index.vue`(717) |
| 守卫 | ensureAdminAccess L313 | useAdminGuard L458 |
| 分页 | 分页器 changePage L414-418，currentPage L225、totalPages L241、pageSize ref | 上拉加载 loadMore L434 + 下拉刷新 onRefresh L443，防抖 2s L393 |
| 筛选 | 7 条件：username/email/phone_number/nickname/role/status/can_stream（L345-356） | Tab（全部/已封禁/无开播权限 L243-246）+ 搜索用户名或邮箱（L34-44）+ role/status picker（L45-50） |
| 编辑方式 | UserEditDialog 弹窗：status picker + role picker（仅超管）+ can_stream 开关；canEditUser 权限模型（L306-311，不能编辑自己/超管） | 无编辑弹窗：角色用 popup 快速切换（rolePopupUser L297、handleRoleSelect L508）；封禁/解封/开播开关直接操作（L463-505） |
| 批量操作 | 无 | 多选 + 批量封禁 handleBatchBan L527 / 批量关闭开播 handleBatchCloseStream L535 |
| 类型/API | `src/types/adminUser.ts`（198 行权限模型：ADMIN_USER_ROLE_LABEL、canChangeUserRole、getEditableRoleOptions、normalize 系列）；`src/api/user.ts` L144-163：getAdminUsers({page,size})、adminUpdateUser PATCH | `@/api/adminUsers`：getAdminUsers/updateAdminUser（同上接口） |

### 模块 2：专家管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/expert/ExpertAdminList.vue`(976) | `admin/expert-list/index.vue`(1202) |
| 守卫 | L309 | L751 |
| 分页 | 分页器 page/pageSize=20（L250、L289） | 上拉加载 loadExperts/loadMore（L409-513）+ 刷新冷却 800ms（L298、REFRESH_COOLDOWN） |
| 数据源 | getAdminExperts 单通道 | **双通道**：getUnmappedExperts（未映射专家）+ getAdminExperts（L435/447/483/489） |
| 筛选 | 简单 keyword | getCategories + getDepartments({page:1,size:200})（L541-546），Tab 直链（onLoad options L741-742） |
| 弹窗 | 自绘 dialog | ModalDialog（L261） |
| 附加功能 | 无 | 指派场次 handleAssignConfirm L711（updateExpert 带 session 关联）、表单组件、创建/编辑共用 |
| 特色 | — | watch/onShow/筛选合并刷新 pendingRefresh L296-303、L459-462 |

### 模块 3：分类/科室管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/category/CategoryList.vue`(487) + `CategoryFormDialog.vue`(455) | `admin/departments/index.vue`(1293) |
| 守卫 | **无** | L686 |
| 结构 | 单级分类（name/slug/icon/description/sort_order/is_active） | **两级**：根分类 category（createCategory/updateCategory L299）+ 科室 department（getDepartments L298） |
| 分页 | 分页器 page/page_size（L148、totalPages L140） | getDepartments({page,size}) 上拉加载 loadMore L462 + 刷新防抖 2s L417 |
| 附加功能 | 无 | **审核认证** handleAudit L564（updateDepartment is_verified）、批量认证 handleBatchVerify L627、科室合并 handleMergeConfirm L663（mergeDepartments）、Tab 分组展示（all/未分/分组） |
| Tab | 无 | useSwiperTabs |
| 弹窗 | CategoryFormDialog（mode create/edit） | ModalDialog（科室/根分类两个表单 catFormMode L374） |

### 模块 4：焦点图/轮播图管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/featuredContent/FeaturedContentList.vue`(604) + `FeaturedContentFormDialog.vue`(716) | `admin/featured/index.vue`(826) |
| 守卫 | **无** | L481 |
| 分页 | 分页器 currentPage L142、page/page_size L246-251 | loadList/loadMore L307-364：请求序号防竞态 L310、500ms 防抖 L361、去重合并 L341-342 |
| 状态筛选 | 无（全量+本地资源名缓存 resourceNameCache） | **status 参数** active/inactive L327-328 + Tab all/active/inactive（filterItemsByTab L301-305，inactive 含 expired） |
| 目标类型 | session/topic/expert/brand/external（targetTypeMap L174-180） | 同 targetLabel L273 |
| 图片 | 本地临时路径判断 L465-470；创建用 DEFAULT_BANNER 占位后补传 L507、L516-523；兼容多种返回格式 L518-520 | handleChooseImage L373 + uploadFeaturedContentImage |
| 日期 | 无 | **WdDatetimePicker 有效期**（L190 wot-design-uni） |
| 弹窗 | FeaturedContentFormDialog | ModalDialog |

### 模块 5：通知推送

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | ❌ **无**（仅用户侧 src/api/notifications.ts、src/pages/profile/Notifications.vue） | `admin/notification-push/index.vue`(453) |
| 守卫 | — | useAdminGuard L210（onMounted） |
| 推送 | — | createNotification（全员）/ batchCreateNotifications（指定 user_ids，多行输入 L157-166） |
| 历史 | — | getAllNotifications({page:1,size:20}) L179-191，typeLabel L204 |

### 模块 6：标签管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/tag/TagList.vue`(393) + `TagFormDialog.vue`(396) | `admin/tags/index.vue`(550) |
| 守卫 | **无** | L168 |
| API | getTags + deleteTag（L89） | getAdminTags/createTag/updateTag（L127） |
| 表单 | name + **slug 必填**（^[a-z0-9-]+$，L200-208）+ description + is_active | ModalDialog：name/description/is_active（TagCreatePayload & TagUpdatePayload L161） |
| 操作 | 增删改 | 增删改 + **toggleActive 启用/禁用** L287-289 |

### 模块 7：品牌管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/brand/BrandAdminList.vue`(698) | `admin/brands/index.vue`(790) |
| 守卫 | L214 | L242 |
| 分页 | 分页器 page/pageSize L285-289 | loadBrands L273 + loadMore L302 |
| API | getAdminBrandList/getAdminBrandDetail(L354)/deleteBrand | getAdminBrands/createBrand/updateBrand/deleteBrand/uploadBrandLogo（L194） |
| 兼容 | Admin 列表空时回退公开 getBrandList({limit:500}) L292-295；extractList 兼容 5 种响应形态 L235-252 | 直接消费 res.data.items L289 |
| 图片 | logoSrc/onLogoError 断裂标记 L269-277 | handleUploadLogo L353 |
| 操作 | 增删改（表单页内嵌 handleSaveForm L401） | 增删改 + handleEnable 启用/禁用 L431 |

### 模块 8：品牌成员（仅小程序）

- `admin/brand/BrandMemberManager.vue`(507)，守卫 L155
- 管理品牌下的用户成员（add/remove member）

### 模块 9：品牌商品（仅小程序）

- `admin/brandProduct/BrandProductList.vue`(535)，守卫 L160
- getAdminBrandProducts（buildProductQuery **同时发 size+page_size** L210-215 兼容双端）、adminDeleteBrandProduct L331
- 品牌筛选器：getAdminBrandList({page:1,size:100}) 空时回退 getBrandList({limit:500}) L264-270

### 模块 10：留言管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/roomMessage/RoomMessageList.vue`(655) | `admin/messages/index.vue`(903) |
| 守卫 | authStore 检查 L135/152 | L178 |
| 入口 | AdminRoomEditDialog goMessages L334-341 跳转（带 roomId） | onLoad roomId 预填 L173-175 + 独立入口 |
| 筛选 | 房间维度为主 | **时间 Tab**：全部/今日/近7天/近30天（L142-147、getStartTime L227-238）+ 关键词搜索 L187 + 按房间筛选 openRoomFilter L198（弹输入框输房间 ID） |
| 删除 | 单条 deleteMessage + 清空 clearRoomMessages | 单条 + **批量删除 handleBatchDelete L362**（batchDeleteMessages，返回 deleted_count L379-380）+ 清空房间 handleClearRoom L391（clearRoomMessages） |
| 分页 | page/page_size | page/pageSize=20（L152、L276）上拉加载 loadMore L295 |

### 模块 11：内容安全（仅小程序）

- 三个文件：`ContentSafetyRuleList.vue`(353)、`ContentSafetyRuleFormDialog.vue`(499)、`ContentSafetyLogList.vue`(267)，**均无守卫**
- RuleList：**page_size=100 全量拉取合并**（后端上限 100，L135-147 循环翻页）；按 pattern 分组批量编辑 openEditGroup L171-177；保存时逐条 updateContentSafetyRule（L315-317）
- RuleFormDialog：action(block/warn/allow) + severity + priority + enabled + remark；法定必应规则强制 block（isStatutory L309-313）
- LogList：scene/decision 筛选；**enrichUserLabels 用户昵称补全** L133-168（用 getAdminUsers 逐页扫描最多 5 页，按 public_id 匹配 nickname）；logContentSafetyAuditDetail 审计埋点 L181

### 模块 12：直播间 Tab 管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/roomTab/RoomTabManager.vue`(367) + `RoomTabManagerShell.vue`(59) + `TabEditDialog.vue`(456) | `room-tabs/index.vue`(58 壳) + `src/components/app/TabManager.vue` |
| 守卫 | Shell 内联 L23-44 | 壳页 L30 |
| 排序 | handleMoveUp L209 / handleMoveDown L221 + persistSortOrder L233 | TabManager 同款 handleMoveUp/Down + persistSortOrder |
| 加载 | loadTabs L137（sort_order 排序） | loadTabs L137（同） |
| 表单 | TabEditDialog：tab_key 创建后不可改（L257）、图片 2MB 校验 L200、uploadTabImage、content_type 固定 mixed | TabManager 内联（无独立对话框组件） |

### 模块 13：全站房间管理

| 项 | 小程序 | App |
|----|--------|-----|
| 文件 | `admin/room/AdminRoomList.vue`(693) + `AdminRoomEditDialog.vue`(623) | `live-manage/list.vue`(1811) **admin 模式内嵌** |
| 守卫 | L253 | onLoad `mode==='admin'` 检查 authStore.isAdmin L592-601（非管理员 toast+navigateBack） |
| 列表 | getAdminRoomList 独立管理页 | loadAdminRooms 复用房间列表页（navigationBarTitle「全站房间」L599） |
| 编辑 | AdminRoomEditDialog：updateRoom(L260)/uploadRoomCover(L301)/goTabs(L325)/goMessages(L334)/handleClearMessages(L343)/handleDeleteRoom(L373) | 内联编辑弹窗 L1067-1283：loadAdminRoomDetail L1093、handleAdminPickCover L1128、handleAdminSave L1173；无 Tab/留言跳转 |
| 内容安全 | handleContentSafetyError 拦截 L266/L277 | — |

---

## 四、小程序可采纳清单（App → 小程序回灌）

按价值排序：

1. **统一访问守卫**：抽 `useAdminGuard` 到共享 composable（对齐 `src/composables/useAdminGuard.ts`），替换 6 处内联 `ensureAdminAccess`，并**补齐 CategoryList / FeaturedContentList / TagList / ContentSafetyRuleList / ContentSafetyLogList 的守卫**（当前可直开管理页，安全隐患）。
2. **ModalDialog 共享弹窗**：App 用 `src/components/shared/ModalDialog.vue`（title/confirmText/update:visible 协议），小程序可抽取，消灭 22 个文件中的重复 `dialog-overlay` 模板。
3. **useSwiperTabs composable**：App 的 Tab 头点击↔swiper 双向联动（含同索引判重、越界归一化），小程序各页可复用。
4. **统一分页参数**：小程序的 `page_size` 与 App 的 `size` 混用（BrandProductList 甚至双发 size+page_size），建议 API 层统一映射。
5. **上拉加载 + 下拉刷新**：小程序全用分页器（用户体验割裂），可对齐 App 的 scroll-view + refresher 方案。
6. **留言管理增强**：时间筛选（今日/近7天/近30天）、关键词搜索、批量删除、按房间筛选弹窗（RoomMessageList 目前只有房间维度）。
7. **焦点图状态 Tab**：App 的 active/inactive/expired 状态筛选 + status 参数。
8. **标签启用/禁用开关**：App toggleActive 一键切换 vs 小程序仅增删改。
9. **科室审核能力**（若小程序需要科室场景）：is_verified 审核 + 批量认证 + 合并。
10. **请求防抖/防竞态**：App 的请求序号竞态保护（featured L310）、刷新冷却（expert-list REFRESH_COOLDOWN）、加载去重 —— 小程序 fetchData 全部裸奔。
11. **图片上传统一**：App 品牌 uploadBrandLogo、Tab 图片上传等可抽取共享上传组件（2MB 校验在 TabEditDialog L200，其他页面各写各的）。

---

## 五、App 已实现但小程序没有的清单（反向补充）

| # | 能力 | App 位置 | 小程序现状 |
|---|------|---------|-----------|
| 1 | 通知推送管理（全员/指定用户/历史） | admin/notification-push/index.vue | ❌ 完全缺失 |
| 2 | 用户批量操作（批量封禁/批量关开播） | users/index.vue L527/L535 | ❌ 仅单条 |
| 3 | 用户角色快速切换 popup | users/index.vue L214-227/L508 | ❌ 需打开编辑弹窗 |
| 4 | 用户列表 Tab（已封禁/无开播权限） | users/index.vue L243-246 | ❌ 仅筛选器 |
| 5 | 未映射专家管理（双通道列表） | expert-list L435/447 | ❌ 仅已映射专家 |
| 6 | 专家指派场次 | expert-list handleAssignConfirm L711 | ❌ |
| 7 | 留言时间范围筛选 + 批量删除 | messages L142-147/L362 | ❌ 仅单条删除 |
| 8 | 焦点图有效期（WdDatetimePicker） | featured L190 | ❌ 仅 sort_order/is_active |
| 9 | 标签启用/禁用开关 | tags toggleActive L287 | ❌ |
| 10 | 品牌启用/禁用 | brands handleEnable L431 | ❌ 仅删除 |
| 11 | 统一 ModalDialog / useSwiperTabs / useAdminGuard | components/shared + composables | ❌ 各页自绘自写 |

---

## 六、App 缺失但小程序已有的模块（需补时参考）

| 模块 | 小程序实现文件 | 关键能力 | App 接入建议 |
|------|--------------|---------|-------------|
| 品牌成员 | BrandMemberManager.vue(507) | 品牌下用户成员管理 | 新页面 admin/brand-members |
| 品牌商品 | BrandProductList.vue(535) | 商品 CRUD + 品牌筛选 + 状态筛选 | 新页面 admin/brand-products |
| 内容安全 | ContentSafetyRuleList/FormDialog/LogList | 规则分组批量编辑、全量拉取、审计日志 + 用户昵称补全 | 新页面 admin/content-safety/ |

（注：docs 下「小程序端管理功能接入App端实现方案设计文档.md」已规划 8 模块批量接入，本报告可作为其子文档的差异化数据来源。）

---

## 七、关键文件索引

**App 端**：
- `src/composables/useAdminGuard.ts`（L24-50 useAdminGuard、L55 getCurrentPagePath）
- `src/composables/useSwiperTabs.ts`（全文 94 行）
- `src/components/shared/ModalDialog.vue`
- `src/components/app/TabManager.vue`（loadTabs L137、handleMoveUp/Down）
- `src/pages/app/admin/{users,expert-list,departments,featured,notification-push,tags,brands,messages,room-tabs}/index.vue`
- `src/pages/app/live-manage/list.vue`（admin 模式 L592-601、编辑弹窗 L1067-1283）

**小程序端（wechat 分支，`git show wechat:<path>` 读取）**：
- `src/pages/admin/user/UserList.vue`（ensureAdminAccess L313）
- `src/pages/admin/expert/ExpertAdminList.vue`（L309）
- `src/pages/admin/category/CategoryList.vue`（无守卫）
- `src/pages/admin/featuredContent/FeaturedContentList.vue`（无守卫）
- `src/pages/admin/tag/TagList.vue`（无守卫）
- `src/pages/admin/brand/BrandAdminList.vue`（L214）、`BrandMemberManager.vue`（L155）
- `src/pages/admin/brandProduct/BrandProductList.vue`（L160）
- `src/pages/admin/roomMessage/RoomMessageList.vue`
- `src/pages/admin/contentSafety/{ContentSafetyRuleList,ContentSafetyRuleFormDialog,ContentSafetyLogList}.vue`（无守卫）
- `src/pages/admin/roomTab/{RoomTabManager,RoomTabManagerShell,TabEditDialog}.vue`
- `src/pages/admin/room/{AdminRoomList,AdminRoomEditDialog}.vue`
- `src/types/adminUser.ts`、`src/api/user.ts`（getAdminUsers L144、adminUpdateUser L155）
