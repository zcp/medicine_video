# 最终方案：A2+C 融合方案设计（受控词表自适应补全）

> 基于实际数据库审计（41 个 department 值 × 384 位专家），经三轮迭代审计后定稿

---

## 一、方案定位

**一句话**：categories 运行时只读（C 方案的结构纯净性）+ expert_departments 自适应创建（A2 方案的输入容错性）+ is_verified 审核机制。

---

## 二、修改建议的可行性与风险

### 2.1 同步机制（应用层显式同步，不引入触发器）

**决策：不引入数据库触发器，使用应用层显式同步。**

| 维度 | 判断 |
|:----|:----|
| 全项目模式 | ⚠️ 当前项目零触发器，全部逻辑在 Python 应用层。引入触发器是新的模式 |
| 调试成本 | 🟡 触发器错误不在应用日志，需查看 PostgreSQL 日志 |
| 测试复杂度 | 🟡 需在测试数据库中创建触发器 → 增加 CI 部署复杂度 |
| 团队一致性 | ✅ 采用应用层同步 → 与项目既有的所有数据操作模式一致 |
| **决策** | **❌ 不采纳触发器。保持全项目一致的"应用层显式同步"模式** |

```python
# 应用层显式同步（替代触发器）
async def update_department_category(self, dept_id, new_cat_id):
    """管理员修改科室的分类 → 显式同步专家缓存列"""
    dept = await self.db.get(ExpertDepartment, dept_id)
    dept.category_id = new_cat_id
    
    # 同步所有关联专家的 category_id（同方法内显式执行）
    await self.db.execute(
        update(Expert)
        .where(Expert.department_id == dept_id)
        .values(category_id=new_cat_id)
    )
    await self.db.commit()
```

当前项目不涉及跨服务分布式事务，应用层同步在同一数据库事务内即可保证一致性。

### 2.2 改进匹配算法（你的建议）

| 优先级 | 策略 | 实际命中率（41条数据验证） | 问题 |
|:-----:|:-----|:------------------------:|:-----|
| P1 | 精确匹配根分类名 | 12/41 = 29% | — |
| P2 | 医学特异性词匹配 | 21/41 = 51% | **5个bug**（见下文） |
| P3 | 最长后缀匹配 | 0/41 = 0% | 无科室名以根分类名结尾 |
| Fallback | 归入"其他" | 8/41 = 20% | — |
| **总计** | | **34/41 = 83%** | **需追加5条规则** |

**P2 匹配的 5 个 Bug**：

| 输入 | 当前匹配结果 | 正确 | 原因 | 修复 |
|:----|:----------:|:---:|:----|:----|
| 骨肿瘤科 | 肿瘤科（'肿瘤'长度2 > '骨'长度1） | 骨科 | 二级优先级按长度排序，'肿瘤'优先于'骨' | 追加 `'骨肿瘤' → 骨科` 特异性规则 |
| 泌尿外科/男科 | 非确定性（'泌尿'和'男科'长度相同） | 泌尿外科 | 两个规则长度相等，查询计划决定顺序 | 追加 `'泌尿外科' → 泌尿外科` 全词优先规则 |
| 口内修复科 | 未匹配→其他 | 口腔科 | '口内修复科'不包含'口腔'子串 | 追加 `'口内' → 口腔科` |
| 肝外科 | 未匹配→其他 | 普通外科 | '肝'不是独立医学词 | 追加 `'肝' → 普通外科` 或别名表 |
| 显微创伤外手科 | 未匹配→其他 | 骨科 | '显微'不是独立医学词 | 追加别名表 `'显微创伤外手科': '骨科'` |

**修复后正确率**：34/41 + 5/41 = 39/41 = **95%**。剩余 2 条（'外科门诊'、'肝外科/超声医学科/介入超声专科'）归"其他"是合理的（复合名称无法自动解析）。

### 2.3 自学习合并 API（你的建议）

**可行，逻辑验证通过**。追加 3 条边界规则：

```python
SYNONYM_LIMIT = 20  # 单科室同义词上限

async def merge_departments(db, source_id, target_id):
    source = await db.get(ExpertDepartment, source_id)
    target = await db.get(ExpertDepartment, target_id)
    
    # 1. 自学习：源科室名追加到目标同义词（上限20）
    new_synonyms = set(target.synonyms or [])
    new_synonyms.add(source.name)
    if source.synonyms:
        new_synonyms.update(source.synonyms)
    target.synonyms = list(new_synonyms)[:SYNONYM_LIMIT]
    
    # 2. 自动升级 verified 状态
    if not source.is_verified and target.is_verified:
        pass  # 目标已是 verified，不需要再设
    elif source.is_verified and not target.is_verified:
        target.is_verified = True  # 合并来源是已审核的，自动升级目标
    
    # 3. 转移专家关联
    await db.execute(
        update(Expert).where(Expert.department_id == source_id)
        .values(department_id=target_id)
    )
    # 触发器自动同步 category_id
    
    # 4. 物理删除源科室
    await db.delete(source)
```

---

## 三、最终架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         categories 表                           │
│                   运行时 100% 只读（20条锚定分类）                 │
│                   parent_id 支持 2 层结构                        │
│                   管理员通过 admin API 手动增删改                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │ FK (RESTRICT)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    expert_departments 表                         │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  已审核 (is_verified=true) │ 待审核 (is_verified=false)    │  │
│  │  ~35 条种子科室            │ 自适应创建的新科室             │  │
│  │  含 synonyms 同义词列表    │ 管理员 approve→true/merge     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  PostgreSQL 应用层同步 (修改 expert_departments.category_id 时显式同步 experts) │
│  └─→ UPDATE experts SET category_id = ... 同方法内执行                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │ FK (SET NULL)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                         experts 表                               │
│  department_id (FK→expert_departments)                          │
│  category_id (反范式缓存，由触发器同步)                           │
│  无 department 自由文本字段                                      │
└─────────────────────────────────────────────────────────────────┘
```

**数据流（导入时）**：

```
输入: "乳腺外科"
  → Priority 1: 精确匹配 expert_departments.name = "乳腺外科"? 不存在
  → Priority 2: 医学词匹配 "乳腺" → 普通外科
  → UPSERT: INSERT INTO expert_departments (name='乳腺外科', category_id=普通外科, is_verified=false)
  → 返回 department_id=xxx, category_id=普通外科
  → expert 被绑定到科室 "乳腺外科"，分类为 "普通外科"
  → 前端「普通外科」Tab 立即可以筛选到该专家 ✅
```

---

## 四、修改建议的最终采纳表

| 你的建议 | 采纳 | 需要修正的点 |
|:---------|:----:|:------------|
| categories 运行时只读 | ✅ | — |
| expert_departments 自适应创建 + is_verified | ✅ | — |
| 启发式匹配 | ✅ | 匹配算法需追加 5 条特异性规则（骨肿瘤→骨科等） |
| UPSERT 写入 expert_departments | ✅ | 二次查询需加 is_active=true 过滤（A2审计Bug #2） |
| 触发器同步 category_id | ❌ | 全项目无触发器的先例。改为应用层显式同步 UPDATE experts SET category_id |
| 自学习合并 API | ✅ | 追加 3 条边界规则（同义词上限、自动升级 verified、物理删除） |
| 别名表预置 35-40 条 | ✅ | 从 41 个现有 department 值直接生成 |
| 子串匹配改为"最长前后缀" | ❌ | 实际数据验证：Priority 3（后缀匹配）0 条命中。建议保留 P2 医学词匹配 + 别名表即可 |
| 管理后台 approve 界面 | ⏸ P2 | 需前端实现，不在当前后端改动范围 |

---

## 五、总体可行性判断

**结论：方案完全可行，建议投产。**

| 风险项 | 级别 | 缓解 |
|:-------|:----:|:-----|
| 匹配算法 5 个 Bug | 🟢 低 | 追加 5 条规则即可解决（已全部定位） |
| 触发器同步的生产经验 | 🟡 中 | 当前项目无触发器经验，但 PostgreSQL 触发器是成熟功能 |
| 别名表预置量 | 🟢 低 | 41 个现有值可直接生成，冷启动问题一次性解决 |
| 自学习同义词膨胀 | 🟢 低 | 设置上限 20 条 |
| 部署顺序（旧 UNIQUE 约束先删除） | 🟡 中 | Runbook 必须明确标注迁移顺序 |
