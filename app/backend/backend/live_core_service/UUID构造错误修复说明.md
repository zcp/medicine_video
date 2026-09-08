# UUID 构造错误修复说明

## 🚨 问题诊断

**错误信息**：
```
TypeError: one of the hex, bytes, bytes_le, fields, or int arguments must be given
```

**根本原因**：
- 测试环境中的 `current_user` 字典只有 `user_id` 字段，没有 `public_id` 字段
- 代码直接使用 `UUID(current_user.get("public_id"))`，当 `public_id` 为 `None` 时会抛出 TypeError

---

## ✅ 修复方案

### 修复思路

兼容测试环境和生产环境：
1. **优先使用 `public_id`**（生产环境）
2. **回退到 `user_id`**（测试环境）
3. **再回退到 `sub`**（其他情况）
4. **都不存在时返回 401 错误**

### 修改的文件

#### 1. `app/api/v1/endpoints/batch_import.py`

**修复前**：
```python
# 提取用户信息
public_id = UUID(current_user.get("public_id"))
```

**修复后**：
```python
# 提取用户信息（兼容测试环境和生产环境）
# 优先使用 public_id，如果不存在则使用 user_id 或 sub
public_id_str = current_user.get("public_id") or current_user.get("user_id") or current_user.get("sub")
if not public_id_str:
    return JSONResponse(
        status_code=401,
        content=error_response(code=3001, message="用户身份信息缺失")
    )
public_id = UUID(public_id_str)
```

#### 2. `app/api/v1/endpoints/session_import.py`

同样的修复逻辑。

#### 3. Deprecation Warning 修复

将 `Query` 参数从 `regex` 改为 `pattern`（FastAPI 新版本要求）：

```python
# 修复前
mode: str = Query("dry_run", regex="^(dry_run|apply)$")

# 修复后
mode: str = Query("dry_run", pattern="^(dry_run|apply)$")
```

---

## 📋 测试环境 vs 生产环境

### 测试环境（conftest.py）

```python
override_get_current_user() -> {
    "user_id": "12345678-1234-5678-1234-567812345678",
    "sub": "12345678-1234-5678-1234-567812345678",
    "email": "test@example.com",
    "exp": ...
}
```

### 生产环境（预期）

```python
get_current_user() -> {
    "public_id": "12345678-1234-5678-1234-567812345678",
    "user_id": ...,
    "sub": ...,
    ...
}
```

---

## ✅ 验证

修复后，代码应该能够：
1. ✅ 在测试环境中正常工作（使用 `user_id`）
2. ✅ 在生产环境中正常工作（使用 `public_id`）
3. ✅ 正确处理缺少用户身份信息的情况（返回 401）

运行测试：
```bash
pytest tests/integration/test_import_batch.py -v
```


















