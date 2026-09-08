# 品牌软删 · C 端挂靠与货架不可售 — 前端设计文档（16-D5）

**项目**: Live-Saas-Wechat  
**模块编号**: 16-D5  
**版本**: V1.0.2  
**日期**: 2026-07-23  
**状态**: 📋 设计定稿，待开发；Admin 品牌成员/商品治理页 **前端已下线**（2026-08-01）
**技术栈**: uni-app + Vue 3 + TypeScript  
**基于**: 《14》品牌 / 商品工作台既有前端；直播间品牌 Tab；品牌专区 / 详情  
**后端对齐**: 《16-D5-品牌软删-C端挂靠与货架不可售-后端设计文档》V1.1（最小落地）  
**关联**: 《14-管理端用户管理-账号能力模型与权限修订》P2 品牌成员/商品；品牌软删约定 `is_active=false`

---

## ⚠️ 重要声明

- 本文档是对品牌 **C 端可见性 / 不可售语义** 的**增量**，不替代品牌 CRUD、工作台主设计（Admin 商品/成员治理页已下线）
- P0 后端策略：**只做读路径 `is_active` 过滤审计**；软删 **不** 批量 `OFF_SALE`、**不** 删 `brand_members`
- 前端 P0 = **兜底过滤 + 错误态对齐 + Admin 软删文案确认**；**无新 API、无新表**
- **现网无订单**：不做订单/退款 UI
- 不可售语义 = **C 端不可见 / 不可达**（含外链 `external_url` 随商品隐藏）

---

## 📌 变更范围

| 变更类型 | 说明 |
|----------|------|
| 【修改·兜底】 | C 端房间品牌列表、品牌专区、挂靠入口：若响应仍含 `is_active=false`，前端过滤不展示 |
| 【修改·错误态】 | 品牌详情遇 `2001`（未启用视同不存在）：友好空态，不暴露内部挂靠 |
| 【修改·文案】 | Admin 软删确认：停用后 C 端不可见；成员保留；复开可恢复 |
| 【说明】 | C 端公开货架：现网 `BrandDetail` **不**拉商品；`getBrandProducts` 主要用于 `BrandWorkbench`（成员侧）。不可售对 C 端主要体现为「品牌/挂靠不可见」；成员工作台商品列表仍按既有 API |
| 【维持】 | Admin 仍可见未启用品牌及挂靠/成员（便于恢复） |
| 【维持】 | 品牌工作台成员行：软删后仍可进工作台（后端不删成员）；商品行 status 不因软删批量改写 |
| 【不做·P0】 | 软删时前端批量调 OFF_SALE；新商品状态流转页；订单相关 |

---

## 一、涉及文件

```
src/pages/live/LiveView.vue                 # 房间品牌 Tab / room_brands 归一化
src/pages/live/CreateLive.vue               # 创建直播选品牌（可选：仅展示启用）
src/pages/brand/BrandZone.vue               # C 端品牌列表
src/pages/brand/BrandDetail.vue             # 品牌 content；2001 空态
src/pages/brand/BrandWorkbench.vue          # 成员工作台（软删后成员保留）
src/pages/admin/brand/BrandAdminList.vue    # 软删确认文案；已停用展示
src/components/brand/BrandCard.vue          # is_active=false 标记（C 端应过滤，一般不露出）
src/components/brand/BrandGrid.vue          # 列表渲染
src/api/brands.ts                           # 路径不变；错误码消费
src/types/brands.ts / brandCommerce.ts      # RoomBrandItem 现无 is_active；兜底过滤时作可选字段读取即可
```

**现网缺口速查（自测）**：

| 落点 | 现状 | P0 |
|------|------|-----|
| `LiveView.normalizeRoomBrandItems` | 不读 `is_active` | 兜底过滤 |
| `BrandZone.loadBrands` / `filtered` | 只滤 id/name，**不**滤 `is_active` | `.filter(b => b.is_active !== false)` |
| `CreateLive.loadBrands` | 不滤 `is_active`（分类侧已滤） | 可选：与分类一致 |
| `BrandDetail` | 2001/失败用 `ErrorBanner` 展示 `error.message`；**未**统一人话「已下架」；成功后**不**校验 `brand_info.is_active` | 补 2001 文案 + 漏网 `is_active=false` 当不可用 |
| `BrandAdminList.handleDelete` | 确认框仅「一般为停用」；成功 Toast「已删除」 | 补语义文案；Toast 可改「已停用」 |
| 硬删入口 | **现网无** `hard_delete` 参数/独立硬删 UI，仅软删 DELETE | T5 以后端/另入口为准，前端勿虚构硬删按钮 |

**API（行为增量，路径不变）**：

| 场景 | 网关路径（示意） | 预期行为 |
|------|------------------|----------|
| 软删品牌 | `DELETE /api/core/admin/brands/{id}` | `is_active=false`；不删成员；不批量 OFF_SALE |
| C 端商品 | `GET /api/core/brands/{id}/products` | 未启用品牌 → `2001`（回归） |
| C 端 content | `GET /api/core/brands/{id}/content` | 未启用 → `2001` / 不可见 |
| 房间挂靠 | `GET .../rooms/{id}/brands` 等 | 后端过滤 `is_active`；前端兜底再滤 |

---

## 二、语义与分层

### 2.1 软删后各端预期

| 端 | 品牌详情 / 挂靠 | 商品货架 | 成员行 |
|----|-----------------|----------|--------|
| C 端 | **不可见**（过滤或 2001） | **不可售/不可见** | 不相关 |
| Admin | **仍可见**（已停用；品牌管理页） | 后端 Admin 商品 API 仍可；**前端商品治理页已下线** | **保留**（`brand_members`）；**前端成员管理页已下线** |
| 品牌工作台（成员 JWT） | 品牌已停用时：可进工作台看自家数据；**勿**在 C 端入口链出该品牌 | 商品 status 未批量 OFF_SALE；复开品牌后仍 ON_SALE 的可自然恢复 C 端可见 | 行保留 |

### 2.2 与封主播 SOP 的区分

| 场景 | 前端 |
|------|------|
| 封主播 | 仍按《14-V2》：人工下架相关商品（后端 Admin API；**前端商品治理页已下线**） |
| 品牌软删 | **不**要求运营在前端批量点 OFF_SALE；靠 `is_active` + 读过滤 |

### 2.3 前端禁止事项

- ❌ 软删成功后前端循环调商品 OFF_SALE
- ❌ C 端把 `is_active=false` 品牌以「已禁用」卡片继续展示（Admin/内部除外）
- ❌ 把 2001 当系统崩溃弹一堆技术错误码；应人话空态
- ❌ 假设软删会清空 `brand_members`（回归：成员仍在）

---

## 三、交互设计

### 3.1 C 端房间品牌挂靠（LiveView）

**现网缺口**：`normalizeRoomBrandItems` 未读 `is_active`，若后端漏过滤会露出已停用品牌。

```
loadRoomBrands / normalizeRoomBrandItems
  → 合并 room_brands / topic_brands
  → 【P0 兜底】丢弃 is_active === false 的项
       （字段可能在 item 或 item.brand / brand_info 上）
  → 渲染品牌列表；点击进 BrandDetail
```

```typescript
function isBrandActive(it: any, brandObj: any): boolean {
  const flag = it?.is_active ?? brandObj?.is_active ?? it?.brand_is_active
  // 后端未回传时默认视为启用（信任服务端已过滤）；显式 false 才丢弃
  return flag !== false
}
```

### 3.2 C 端品牌专区（BrandZone）

- 列表接口应只返回启用品牌；前端再 `.filter(b => b.is_active !== false)`
- `BrandCard` 的「已禁用」角标：**C 端列表过滤后不应出现**；保留组件能力供 Admin/调试

### 3.3 C 端品牌详情（BrandDetail）

> 现网：`getBrandContent` +（可选）`getAdminBrandRooms`；**不**调用 `getBrandProducts`。

```
进入 BrandDetail(id)
  → getBrandContent(id)
  → 200 + is_active!==false：正常展示
  → 200 但 is_active=false（异常漏网）：按不可用处理，不展示专题/关联房
  → code=2001 / 捕获业务不存在：空态「品牌不存在或已下架」，提供返回
  → 其它错误：ErrorBanner「加载失败，请稍后再试」（避免直接甩后端原始 message）
```

成员侧货架 `BrandWorkbench.getBrandProducts`：品牌停用后是否 2001 以后端成员接口语义为准；P0 **不**在软删时前端批量 OFF_SALE。

**文案建议**（人话，不透出内部挂靠）：

| 场景 | Toast / 空态 |
|------|----------------|
| 2001 / 未启用漏网 | 「品牌不存在或已下架」 |
| 网络错误 | 「加载失败，请稍后再试」 |

### 3.4 Admin 软删（BrandAdminList）

**现网**：确认框已提示「一般为停用（软删除）」。P0 补全语义：

```
确定停用「{name}」？
· C 端将不再展示该品牌及其挂靠/商品
· 成员关系保留，复开后可恢复
· 不会批量下架商品状态（复开更友好）
```

- 成功 Toast：「已停用」优于笼统「已删除」（可选优化）
- 列表已有「已停用」状态；成员入口 `goMembers` **保留**（对齐后端不删成员）
- **硬删**：现网 Admin 仅软删 DELETE，无独立硬删按钮；若后续加 `hard_delete`，有引用拒删 → Toast `2004` /「仍有关联，无法删除」

### 3.5 品牌工作台（BrandWorkbench）

- 软删后成员仍在：可进入工作台；商品列表按既有 API
- **不**因品牌停用前端强制改本地商品 status
- 若工作台入口来自 C 端品牌详情：详情已 2001 则自然进不去；入口应来自「我的品牌」类成员侧路径

### 3.6 复开（is_active=true）

- Admin 将品牌重新启用后：C 端挂靠/商品（仍为 ON_SALE 的）自然恢复
- 前端无需清特殊本地缓存键；若有品牌列表缓存，软删/复开后下拉刷新即可

---

## 四、错误码处理（本包相关）

| 错误码 | 场景 | 前端处理 |
|--------|------|----------|
| `200` | 软删/查询成功 | 刷新列表 |
| `2001` | C 端视未启用品牌为不存在 | 空态「品牌不存在或已下架」 |
| `2004` | 硬删仍有引用 | Toast 后端 message /「仍有关联，无法删除」 |
| `3002` | 非 Admin 软删 | Toast「权限不足」 |
| `4001` | 参数校验失败 | Toast 校验提示 |

---

## 五、行动清单

| # | 任务 | 验收 |
|---|------|------|
| 1 | `LiveView.normalizeRoomBrandItems` 兜底过滤 `is_active===false` | 自测 T3 |
| 2 | `BrandZone`：`normalized` / `filtered` 过滤未启用 | 自测 T3 |
| 3 | `BrandDetail`：2001 / 漏网 `is_active=false` → 人话空态 | 自测 T1 |
| 4 | Admin 软删确认文案对齐「C 端不可见、成员保留、不批量 OFF_SALE」 | 文案评审 |
| 5 | 回归：软删后 `brand_members` 仍保留（前端成员管理页已下线；可用工作台/后端验证） | 自测 T2 |
| 6 | 回归：复开后 ON_SALE 商品对 C 端品牌入口重新可见 | 自测 T6 |
| 7 | CreateLive 选品牌：优先只列启用品牌（可选，与分类侧 `is_active!==false` 一致） | 创建页无已停用项 |

---

## 六、自测清单（对齐后端 T 编号）

| # | 测试项 | 预期 | 验证 |
|---|--------|------|------|
| T1 | 软删后 C 端打开品牌详情 | 2001 或「已下架」空态；无专题/关联房 | [ ] |
| T2 | 软删后成员行仍在 | `brand_members` 保留；可用 `BrandWorkbench` / 后端验证（**前端成员管理页已下线**） | [ ] |
| T3 | 软删后直播间品牌 Tab / 专区 | 不出现该品牌（含前端兜底） | [ ] |
| T4 | Admin 列表仍可见「已停用」 | 可见；可用 `is_active` 开关/编辑复开 | [ ] |
| T5 | 硬删有引用（若后端/后续入口具备） | Toast 拒绝，品牌仍在；现网无硬删 UI 则跳过 | [ ] |
| T6 | 复开后 C 端品牌入口 + 挂靠 | 重新可见；成员侧仍 ON_SALE 的商品不因软删被前端改掉 | [ ] |
| T7 | 软删后网络面板 | **无** 批量 OFF_SALE 请求 | [ ] |
| T8 | 品牌工作台成员账号 | 仍可进工作台（成员行保留） | [ ] |

---

## 七、修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-07-23 | 初版：对齐后端 16-D5 V1.1 最小落地；C 端兜底过滤 + 2001 空态 + Admin 软删文案 |
| V1.0.1 | 2026-07-23 | 自测修订：澄清 BrandDetail 无商品列表；补 BrandZone/CreateLive 缺口表；硬删 UI 现网不存在；T5/T6 表述对齐 |
| V1.0.2 | 2026-08-01 | 对齐 Admin「品牌商品管理 / 品牌成员管理」前端下线：§2.1 / SOP / T2 改为后端 API + 工作台验证，不依赖已移除页面 |

---

**文档结束** ✅
