# 专家模块测试错误分析：Service 层签名与可见性

## 错误信息

| 用例 | 错误信息 |
|------|----------|
| test_check_user_resource_permission_success / test_check_user_resource_permission_denied | `TypeError: _check_user_resource_permission() missing 2 required positional arguments: 'current_user_id' and 'role'` |
| test_check_expert_visibility_soft_deleted | `Failed: DID NOT RAISE <class 'app.exceptions.NotFoundException'>` |
| test_check_is_followed_true / test_check_is_followed_false | `TypeError: object Mock can't be used in 'await' expression`（发生在 `crud.get_expert` 内 `await db.execute(stmt)`） |
| test_delete_expert_success（CRUD） | `assert True is False`（断言 `db_expert.is_featured is False` 失败） |

---

## 错误原因

1. **签名不一致**：`_check_user_resource_permission` 实现为 `(self, resource_owner_id, current_user_id, role)`，测试只传了 `(role)`，少传两个位置参数。
2. **可见性语义变更**：实现已改为用 **is_active** 判断软删除/下架，测试仍用 **is_featured=False** 构造“软删除”专家；mock 默认 `is_active=True`，故不抛 NotFound。
3. **Mock 不完整**：`check_is_followed` 会先调用 `get_expert(self.db, expert_id)`，再 `get_subscription`。测试只 mock 了 `get_subscription`，真实代码用 `mock_db`（同步 Mock）执行 `await db.execute()`，导致 “object Mock can't be used in 'await' expression”。
4. **断言与实现脱节**：CRUD 软删除已改为设置 `is_active=False`，测试仍断言 `is_featured is False`。

---

## 解决办法

| 问题 | 修改 |
|------|------|
| _check_user_resource_permission 签名 | 测试改为传入三参：`service._check_user_resource_permission(user_id, user_id, role)`；denied 用例传 `(user_id, user_id, None)`。 |
| 软删除可见性 | 用 `create_mock_expert(is_active=False)` 构造“已下架”专家；`test_check_expert_visibility_admin` 同样改为 `is_active=False`。 |
| check_is_followed 的 await | 同时 mock `get_expert`（AsyncMock，返回 `create_mock_expert(expert_id=expert_id, is_active=True)`），避免真实 crud 对 mock_db 做 await。 |
| delete 软删除断言 | 断言改为 `assert db_expert.is_active is False`，注释改为“软删除：is_active=false”。 |

---

## 涉及文件

- `backend/live_core_service/tests/unit/test_service_experts.py`（5 处）
- `backend/live_core_service/tests/unit/test_crud_experts.py`（1 处注释 + 断言若尚未改则改为 is_active）

**未修改**：conftest、其他测试、后端实现。

---

## 改进建议（避免同类问题）

### 1. 设计文档（含增量设计文档）

- **显式列出“行为契约”**：凡涉及权限、可见性、软删除的变更，在「修改点」或「执行流程」中写清：
  - 方法签名（参数个数、含义、顺序），例如：`_check_user_resource_permission(resource_owner_id, current_user_id, role)`。
  - 软删除/可见性判定字段（如：**软删除 = is_active=false**，is_featured 仅表示首页推荐），避免测试继续用旧字段断言。
- **在“测试建议”中指名字段**：写清“软删除/下架场景用 is_active=False 构造数据”“断言软删除后 is_active 为 False”，减少 AI 或人工沿用 is_featured。

### 2. 测试母版（《测试代码生成提示词母版》）

- **“动态读取”必须包含方法签名**：Section 6 或“执行顺序”中明确：生成 Service 层测试前，必须从 **Service 源码** 读取被测方法的**完整签名**（参数名、类型、顺序），禁止仅凭方法名或旧用例推断参数。
- **Mock 完整性规范**：对“调用链中有多个 CRUD/外部依赖”的 Service 方法，明确要求：**凡在实现代码路径上会被调用的依赖，均须 mock**（如 check_is_followed 先 get_expert 再 get_subscription，则两者都要 mock）；且传入 Service 的 `db` 若为 Mock，不得让真实 CRUD 对同一 Mock 做 `await`，应通过 mock CRUD 函数隔离。
- **“软删除/可见性”约定**：在测试数据与断言规范中增加一条：**软删除、下架、可见性** 的构造与断言必须与**当前设计文档**一致（若设计写 is_active，则测试用 is_active；禁止沿用旧字段如 is_featured）。

### 3. 模块特定测试代码生成文档（如《专家模块增量开发_测试代码生成提示词》）

- **Section 6 依赖清单**：确保列出 **app/services/expert_service.py**，并在 Section 1 或“强制读取步骤”中写明：生成权限/可见性/关注相关测试前，必须读取 Service 中 `_check_user_resource_permission`、`_check_expert_visibility`、`check_is_followed` 的**完整定义与调用关系**。
- **Section 7 任务说明**：对“检查写权限”“检查专家可见性（软删除）”“检查是否已关注”等用例，在任务描述中注明：
  - 调用签名以源码为准（如三参 _check_user_resource_permission）；
  - 软删除/下架使用 is_active=False；
  - check_is_followed 需 mock get_expert 与 get_subscription。
- **Section 8 自检清单**：增加项：“Service 层被测方法签名与测试调用是否一致”“可见性/软删除是否使用设计文档指定字段（如 is_active）”“多步调用的 Service 方法是否已 mock 所有被调用的 CRUD”。
