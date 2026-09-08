# JWT字段与MODERATOR角色设计决策建议

> **日期**: 2025-12-13  
> **基于**: 三文档一致性检查报告 + Role定义一致性检查报告  
> **目标**: 提供切实可行的实施方案

---

## 问题1: JWT字段 - `user_id` vs `sub`

### 1.1 当前状况分析

| 文档 | JWT用户ID字段 | 状态 |
|------|--------------|------|
| 用户模块-文字描述 | `user_id` | ❌ 说是"JWT标准"（错误） |
| 用户模块-JSON示例 | `sub` | ✅ 真正的JWT标准 |
| v6主文档 | `user_id` | 非标准但已统一 |
| 权限设计文档 | `user_id` | 与v6保持一致 |
| **已生成的代码** | `user_id` | ⚠️ 关键因素 |

### 1.2 决策矩阵

#### 方案A: 改为标准`sub`字段

**优势** ✅:
- 符合JWT RFC 7519标准
- 与国际最佳实践一致
- 第三方工具/库兼容性好
- 用户模块文档的JSON示例无需修改
- 长期技术债务更低

**劣势** ❌:
- 需要修改所有已生成的代码
- 需要修改v6主文档
- 需要修改权限设计文档
- 前端可能需要同步修改
- 存在改错的风险

**工作量**: 
- 代码修改: 预计20-30处
- 文档修改: 3个核心文档
- 测试验证: 所有认证相关功能
- **预估时间**: 2-3个工作日

---

#### 方案B: 保持`user_id`（推荐 ⭐）

**优势** ✅:
- 已生成代码无需修改（零风险）
- 三个文档已经统一（仅需修正用户模块文档的描述）
- 前端无需改动
- 团队已经熟悉这个字段名
- **语义清晰**（`user_id`比`sub`更直观）

**劣势** ❌:
- 不符合JWT标准（但不影响功能）
- 用户模块文档的JSON示例需要修改
- 第三方工具集成时可能需要映射

**工作量**:
- 代码修改: 0处 ✅
- 文档修改: 仅用户模块文档1处
- 测试验证: 无需额外测试
- **预估时间**: 0.5个工作日

---

### 1.3 💡 最终建议：**方案B（保持`user_id`）**

**理由**:

1. **已生成代码是最大的约束**
   - 你提到"已经生成的代码都是按照主文档来的"
   - 改动代码的风险 > 文档不符合标准的风险

2. **三个文档已经统一**
   - v6主文档: `user_id`
   - 权限设计文档: `user_id`（刚刚统一的）
   - 仅用户模块文档有矛盾（描述vs示例）

3. **语义优势**
   - `user_id`对中国开发团队更友好
   - 字段含义一目了然，不需要查RFC文档

4. **技术可行性**
   - JWT的自定义字段完全合法
   - 只要前后端约定一致即可
   - 不影响JWT的安全性

---

### 1.4 具体实施方案（方案B）

#### Step 1: 修正用户模块文档的错误描述（必须）

**位置**: `用户模块设计文档authing版+权限设计版.md`

##### 1.4.1 修正第515-523行的文字描述

**修改前**:
```markdown
* **`user_id` (Subject)**: `string`, **必需**. 
  用户的唯一标识符，应使用 `user.public_id`。这是JWT的标准字段。
* **`user_role`**: `string`, **必需**. 
  用户的角色，例如 `'REGULAR'` 或 `'ADMIN'`。此字段是权限系统的核心。
```

**修改后**:
```markdown
* **`user_id`**: `string`, **必需**. 
  用户的唯一标识符（存储users.public_id的UUID值）。
  注：虽然JWT标准推荐使用`sub`字段，但本系统为保持语义清晰，
  统一使用`user_id`字段。
* **`role`**: `string`, **必需**. 
  用户的角色枚举值，如`REGULAR`、`ADMIN`等。
  此字段是权限系统的核心。
```

##### 1.4.2 修正第527-536行的JSON示例

**修改前**:
```json
{
  "sub": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
  "role": "ADMIN",
  "type": "access",
  ...
}
```

**修改后**:
```json
{
  "user_id": "a1b2c3d4-e5f6-4a1b-8c3d-e5f6a1b2c3d4",
  "role": "ADMIN",
  "type": "access",
  ...
}
```

##### 1.4.3 修正第807-850行（SSO登录章节）

同样的修改：描述和示例都改为`user_id`。

#### Step 2: 在所有文档开头添加"JWT字段使用说明"（建议）

在三个核心文档的开头添加统一说明：

```markdown
## 🔴 JWT Payload字段规范

本系统JWT Token的Payload结构：

```json
{
  "user_id": "UUID字符串",  // 用户的public_id（非标准字段，但语义清晰）
  "role": "REGULAR",         // 用户角色枚举值
  "type": "access",          // Token类型
  "exp": 1234567890,         // 过期时间
  "iat": 1234567890,         // 签发时间
  "jti": "UUID字符串"        // Token唯一ID
}
```

**字段说明**:
- `user_id`: 虽然JWT标准推荐使用`sub`字段，但本系统为保持代码语义清晰，
  统一使用`user_id`存储用户的public_id（UUID）。
- `role`: 用户角色，参见《用户模块设计文档》§4.2 角色定义。

**前后端对接要点**:
- 后端生成Token时，使用`user_id`字段存储users.public_id
- 前端/客户端解析Token时，从`user_id`字段获取用户标识
- 严禁在JWT中混用`sub`和`user_id`字段
```

---

## 问题2: MODERATOR角色的权限设计策略

### 2.1 当前问题总结

| 问题 | 影响 | 严重程度 |
|------|------|---------|
| URL过滤使用`role == 'REGULAR'` | MODERATOR可绕过URL限制 | 🔴 高 |
| 权限矩阵未说明MODERATOR | 文档理解混乱 | 🟡 中 |
| 未来扩展性考虑不足 | 第二阶段改动大 | 🟢 低 |

### 2.2 💡 推荐策略：**三层防御模式**

#### 策略1: 代码层 - "白名单管理员"模式（当前已采用 ✅）

**核心原则**: 只明确定义管理员，其他角色自动归为普通用户。

**正确模式**:
```python
# ✅ 推荐写法（当前大部分代码已采用）
if role in ['ADMIN', 'SUPERADMIN']:
    # 管理员特权
else:
    # 普通用户（自动包含REGULAR和MODERATOR）
```

**错误模式**:
```python
# ❌ 错误写法（仅在URL过滤处出现）
if role == 'REGULAR':
    # 限制逻辑（遗漏了MODERATOR）
```

**优点**:
- ✅ MVP阶段MODERATOR自动等同于REGULAR
- ✅ 未来启用MODERATOR时，只需在特定位置添加白名单
- ✅ 代码简洁，不需要到处判断MODERATOR

---

#### 策略2: 文档层 - 明确标注来源

**在权限设计文档中添加角色处理说明**:

**位置**: `直播核心功能设计文档_v6_增加权重设计版(非独立版).md` 第1672行前

**建议添加**:
```markdown
## 6. 完整接口权限矩阵（快速参考）

### 6.1 角色说明与MODERATOR处理策略

本系统定义四种用户角色（详见《用户模块设计文档》§4.2）：

| 角色 | 枚举值 | MVP阶段权限 | 第二阶段规划 |
|------|-------|-----------|------------|
| 普通用户 | `REGULAR` | ✅ 基础权限 | 不变 |
| 房管 | `MODERATOR` | ⚠️ **等同于REGULAR** | 特定房间管理权限 |
| 管理员 | `ADMIN` | ✅ 平台管理权限 | 不变 |
| 超级管理员 | `SUPERADMIN` | ✅ 最高权限 | 不变 |

**MVP阶段MODERATOR处理原则**:

1. **代码实现**: 使用"白名单管理员"模式
   ```python
   # ✅ 正确写法
   if role in ['ADMIN', 'SUPERADMIN']:
       # 管理员特权
   else:
       # 普通用户（包括REGULAR和MODERATOR）
   ```

2. **权限矩阵列说明**:
   - **匿名**: 未携带JWT Token的请求
   - **Regular**: 包括`REGULAR`和`MODERATOR`角色（MVP阶段等价）
   - **Admin**: 包括`ADMIN`和`SUPERADMIN`角色

3. **未来扩展路径**:
   当第二阶段启用MODERATOR特权时，只需在特定功能点添加：
   ```python
   # 第二阶段：MODERATOR可删除留言
   if role in ['ADMIN', 'SUPERADMIN', 'MODERATOR']:
       # 允许删除留言
   ```
   但全局性功能（如Tab管理、批量导入）仍只允许ADMIN/SUPERADMIN。
```

---

#### 策略3: 测试层 - 显式测试MODERATOR

**即使MVP阶段不启用特殊权限，也应该测试MODERATOR的行为**:

```python
# test_permissions.py

class TestModeratorRole:
    """MODERATOR角色权限测试（MVP阶段）"""
    
    def test_moderator_create_room_success(self):
        """MODERATOR可以创建房间（等同REGULAR）"""
        # 测试MODERATOR能执行REGULAR的所有操作
        
    def test_moderator_cannot_manage_tabs(self):
        """MODERATOR不能管理Tab（等同REGULAR）"""
        # 确保MODERATOR被正确归类为非管理员
        
    def test_moderator_cannot_send_url_message(self):
        """🔴 MODERATOR不能发送包含URL的留言（bug修复验证）"""
        # 这是当前的bug，修复后必须通过此测试
        
    def test_moderator_same_as_regular(self):
        """MODERATOR与REGULAR的权限完全相同（MVP阶段）"""
        # 遍历所有接口，验证MODERATOR和REGULAR的响应一致
```

**测试覆盖清单**:
- [ ] MODERATOR创建/修改/删除自己的房间 → 成功
- [ ] MODERATOR访问他人私有房间 → 404
- [ ] MODERATOR发送普通留言 → 成功
- [ ] MODERATOR发送URL留言 → **400（当前bug，修复后应该拒绝）**
- [ ] MODERATOR管理Tab → 403
- [ ] MODERATOR批量导入 → 403
- [ ] MODERATOR获取推流密钥 → 仅自己房间成功

---

### 2.3 具体修改清单

#### 修改1: 修正URL过滤逻辑（🔴 必须）

**位置1**: `直播核心功能设计文档_v6_增加权重设计版(非独立版).md` 第996行

```python
# 修改前
if role == 'REGULAR':
    content_lower = content.lower()
    if 'http://' in content_lower or 'https://' in content_lower:
        logger.warning(f"普通用户尝试发送URL留言: user_id={user_id}")
        raise InvalidParameterException("普通用户不允许发送包含 URL 的留言")

# 修改后
if role not in ['ADMIN', 'SUPERADMIN']:
    content_lower = content.lower()
    if 'http://' in content_lower or 'https://' in content_lower:
        logger.warning(f"非管理员用户尝试发送URL留言: user_id={user_id}, role={role}")
        raise InvalidParameterException("非管理员用户不允许发送包含 URL 的留言")
```

**位置2**: 第1390行（BaseService示例）

同样的修改。

---

#### 修改2: 添加角色说明章节（🟡 建议）

**位置**: 第1672行前

参见上面"策略2"的完整内容。

---

#### 修改3: 在代码示例中添加注释（🟢 可选）

在关键权限判断处添加注释：

```python
# ✅ 管理员白名单（MVP阶段MODERATOR不在此列）
if role in ['ADMIN', 'SUPERADMIN']:
    return  # 管理员特权通过

# ✅ 非管理员限制（包括REGULAR和MODERATOR）
if role not in ['ADMIN', 'SUPERADMIN']:
    # 执行限制逻辑
```

---

### 2.4 未来扩展路径（第二阶段）

**第二阶段启用MODERATOR时的改动点**:

#### 场景A: 房间留言管理

```python
# 当前（MVP）
if role in ['ADMIN', 'SUPERADMIN']:
    # 可删除任意留言

# 第二阶段
if role in ['ADMIN', 'SUPERADMIN']:
    # 可删除任意留言
elif role == 'MODERATOR':
    # 检查是否是该房间的房管
    if await self._is_room_moderator(user_id, room_id):
        # 可删除该房间的留言
```

#### 场景B: 禁言功能

```python
# 第二阶段新增
if role in ['ADMIN', 'SUPERADMIN']:
    # 可禁言任意用户
elif role == 'MODERATOR':
    # 检查是否是该房间的房管
    if await self._is_room_moderator(user_id, room_id):
        # 可禁言该房间的用户
```

#### 场景C: Tab管理（仍然限制）

```python
# 不变（MODERATOR不应有Tab管理权限）
if role not in ['ADMIN', 'SUPERADMIN']:
    raise PermissionDeniedException("仅管理员可管理Tab")
```

**关键设计点**:
- MODERATOR的权限是**房间级别**的，需要额外的`room_moderators`表
- 全局性功能（Tab、批量导入）仍然只允许ADMIN
- 需要实现`_is_room_moderator`辅助方法

---

## 3. 实施路线图

### Phase 1: 立即修正（本周完成）

#### Day 1: 修正用户模块文档
- [ ] 修改JWT字段描述（user_id）
- [ ] 修改JSON示例（user_id）
- [ ] 添加JWT字段使用说明章节

#### Day 2: 修正权限设计文档
- [ ] 修正URL过滤逻辑（2处）
- [ ] 添加角色说明章节
- [ ] 添加JWT role合法性校验

#### Day 3: 验证与测试
- [ ] 编写MODERATOR角色测试用例
- [ ] 验证所有权限判断逻辑
- [ ] 更新v6主文档的JWT说明

---

### Phase 2: 文档完善（下周完成）

- [ ] 创建《JWT字段使用规范》独立文档
- [ ] 创建《角色权限设计规范》独立文档
- [ ] 在所有代码示例中添加注释
- [ ] 整理三文档一致性最终报告

---

### Phase 3: 第二阶段准备（未来）

- [ ] 设计`room_moderators`表结构
- [ ] 实现房管邀请/移除功能
- [ ] 实现MODERATOR的留言管理权限
- [ ] 实现MODERATOR的禁言权限

---

## 4. 决策总结表

| 问题 | 推荐方案 | 理由 | 工作量 |
|------|---------|------|--------|
| **JWT user_id vs sub** | 保持`user_id` ⭐ | 已生成代码无需改，语义清晰 | 0.5天 |
| **MODERATOR设计** | 白名单管理员模式 | MVP简单，未来易扩展 | 1天 |
| **URL过滤bug** | 改为`not in ['ADMIN', 'SUPERADMIN']` | 修复权限漏洞 | 0.5天 |
| **文档完善** | 添加角色说明章节 | 提升文档可读性 | 1天 |

**总工作量**: 约3个工作日

---

## 5. 最终建议（TL;DR）

### 对问题1的回答：

**不建议改为`sub`，保持`user_id`**

**原因**:
1. 已生成代码都使用`user_id`，改动风险大
2. 三个核心文档已经统一为`user_id`
3. `user_id`语义更清晰，团队更容易理解
4. JWT自定义字段完全合法，不影响安全性

**行动**: 
- 仅修正用户模块文档的描述和示例（从`sub`改为`user_id`）
- 在所有文档开头添加"JWT字段使用说明"

---

### 对问题2的回答：

**采用"三层防御"策略**

**核心原则**: 白名单管理员 + 显式文档说明 + 完善测试覆盖

**行动**:
1. **立即修正**: URL过滤逻辑的bug（2处）
2. **文档完善**: 添加角色说明和MODERATOR处理策略
3. **测试覆盖**: 即使不启用，也要测试MODERATOR的行为

**优势**:
- MVP阶段简单（MODERATOR自动等同REGULAR）
- 未来扩展容易（只需在特定位置添加白名单）
- 代码清晰（白名单模式一目了然）

---

## 6. 风险提示

### 6.1 如果选择改为`sub`

**风险**:
- 🔴 所有已生成代码需要修改（20-30处）
- 🔴 前端可能需要同步修改
- 🔴 改错一处就可能导致认证失败
- 🟡 需要重新测试所有认证功能

**建议**: 除非有强烈的技术规范要求，否则不建议现阶段修改。

### 6.2 如果不修正URL过滤bug

**风险**:
- 🔴 MODERATOR角色可以绕过URL限制发送垃圾链接
- 🔴 违反了"MODERATOR等同REGULAR"的设计原则
- 🟡 未来启用MODERATOR时会产生困惑

**建议**: **必须修正**，这是一个明确的权限漏洞。

---

**文档版本**: v1.0  
**创建日期**: 2025-12-13  
**作者**: AI Assistant  
**审核状态**: 待用户确认决策

---

*本文档基于三文档一致性检查和Role定义一致性检查的结果，提供了JWT字段和MODERATOR角色设计的实施建议。推荐保持`user_id`字段并采用"白名单管理员"模式处理MODERATOR角色。*

