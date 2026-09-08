# Tab和留言权限修改实施指南

**修改日期**: 2025-12-19  
**修改文件**: `backend/live_core_service/app/services/live_features_service.py`  
**预计工作量**: 1-2小时  
**修改量**: 约57-64行代码

---

## 📋 修改概览

### 修改内容
1. **Tab管理权限**：从 Admin Only 改为 Owner + Admin
2. **留言URL限制**：Regular用户在自己房间允许URL

### 涉及文件
- ✅ **需要修改**：`app/services/live_features_service.py`（1个文件）
- ❌ **不需要修改**：`app/api/v1/endpoints/live_features.py`（API层已提取user_id和role）

---

## 🔧 详细修改步骤

### 步骤1：新增 Tab 管理权限守卫函数

**位置**：在 `TabService` 类中，`_check_admin_role` 方法之后（约第90行之后）

**新增代码**：

```python
def _check_tab_management_permission(
    self,
    room: LiveRoom,
    user_id: uuid.UUID,
    role: str
) -> None:
    """
    检查Tab管理权限（创建者或Admin）
    
    Args:
        room: 直播间对象
        user_id: 当前用户的public_id
        role: 当前用户的角色
        
    Raises:
        PermissionDeniedException: 无权管理Tab（403）
    """
    # Admin：可以管理所有房间
    if role in ['ADMIN', 'SUPERADMIN']:
        # ✅ 记录Admin管理他人房间Tab的审计日志
        if room.user_id != user_id:
            logger.info(
                f"Admin管理他人房间Tab: admin={user_id}, role={role}, "
                f"room_id={room.id}, room_owner={room.user_id}"
            )
        return
    
    # Regular：只能管理自己创建的房间
    if room.user_id == user_id:
        logger.info(f"房间创建者管理Tab: user_id={user_id}, room_id={room.id}")
        return
    
    # 其他情况：拒绝
    logger.warning(
        f"非创建者/Admin尝试管理Tab: user_id={user_id}, role={role}, "
        f"room_id={room.id}, room_owner={room.user_id}"
    )
    raise PermissionDeniedException("您只能管理自己创建的房间的Tab配置")
```

---

### 步骤2：修改 `list_tabs_for_admin` 方法

**位置**：第129行

**修改前**：
```python
# ← 修改：使用字符串格式的role进行权限检查
self._check_admin_role(role)

# 2. 检查房间是否存在
await self._check_room_exists(room_id)
```

**修改后**：
```python
# 2. 检查房间是否存在（先查询room对象）
room = await self._check_room_exists(room_id)

# ← 修改：使用Tab管理权限检查（创建者或Admin）
self._check_tab_management_permission(room, user_id, role)
```

**说明**：将 `await self._check_room_exists(room_id)` 改为 `room = await self._check_room_exists(room_id)`，然后替换权限检查。

---

### 步骤3：修改 `create_tab` 方法

**位置**：第189-192行

**修改前**：
```python
# ← 修改：使用字符串格式的role进行权限检查
self._check_admin_role(role)

# 2. 检查房间是否存在
await self._check_room_exists(room_id)
```

**修改后**：
```python
# 2. 检查房间是否存在（先查询room对象）
room = await self._check_room_exists(room_id)

# ← 修改：使用Tab管理权限检查（创建者或Admin）
self._check_tab_management_permission(room, user_id, role)
```

**说明**：将 `await self._check_room_exists(room_id)` 改为 `room = await self._check_room_exists(room_id)`，然后替换权限检查。

---

### 步骤4：修改 `update_tab` 方法

**位置**：第237-238行

**修改前**：
```python
# ← 修改：使用字符串格式的role进行权限检查
self._check_admin_role(role)

# 2. 获取 Tab
db_tab = await crud_live_features.get_tab(self.db, tab_id)
if db_tab is None:
    raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")
```

**修改后**：
```python
# 2. 获取 Tab
db_tab = await crud_live_features.get_tab(self.db, tab_id)
if db_tab is None:
    raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")

# ← 修改：查询room对象并检查Tab管理权限（创建者或Admin）
room = await self._check_room_exists(db_tab.room_id)
self._check_tab_management_permission(room, user_id, role)
```

**说明**：需要先获取tab，然后从tab中获取room_id，再查询room对象。

---

### 步骤5：修改 `delete_tab` 方法

**位置**：第287-288行

**修改前**：
```python
# ← 修改：使用字符串格式的role进行权限检查
self._check_admin_role(role)

# 2. 获取 Tab
db_tab = await crud_live_features.get_tab(self.db, tab_id)
if db_tab is None:
    raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")
```

**修改后**：
```python
# 2. 获取 Tab
db_tab = await crud_live_features.get_tab(self.db, tab_id)
if db_tab is None:
    raise TabNotFoundException(f"Tab ID: {tab_id} 不存在")

# ← 修改：查询room对象并检查Tab管理权限（创建者或Admin）
room = await self._check_room_exists(db_tab.room_id)
self._check_tab_management_permission(room, user_id, role)
```

**说明**：需要先获取tab，然后从tab中获取room_id，再查询room对象。

---

### 步骤6：修改 `create_message` 方法中的URL过滤逻辑

**位置**：第405-412行

**修改前**：
```python
# ← 保持不变：URL 过滤（学院派规范 5.3.B）
is_admin = role in ['ADMIN', 'SUPERADMIN']  # ← 修改：使用字符串格式的role
has_url = bool(URL_REGEX.search(obj_in.content))

if not is_admin and has_url:
    raise InvalidParameterException(
        code=4004, 
        message="普通用户不允许发送包含 URL 的留言"
    )
```

**修改后**：
```python
# ← 修改：URL 过滤（房间创建者在自己房间允许URL）
is_admin = role in ['ADMIN', 'SUPERADMIN']
has_url = bool(URL_REGEX.search(obj_in.content))

if has_url:
    # Admin：允许任意内容
    if is_admin:
        pass  # 允许
    # 房间创建者：允许在自己房间发送URL
    elif room.user_id == user_id:
        logger.info(
            f"房间创建者发送URL留言: user_id={user_id}, room_id={room.id}, "
            f"room_owner={room.user_id}"
        )
        pass  # 允许
    # 其他用户：禁止URL
    else:
        logger.warning(
            f"非管理员/创建者尝试发送URL留言: user_id={user_id}, role={role}, "
            f"room_id={room.id}, room_owner={room.user_id}"
        )
        raise InvalidParameterException(
            code=4004, 
            message="非管理员用户不允许发送包含 URL 的留言"
        )
```

**或者更简洁的写法（推荐）**：
```python
# ← 修改：URL 过滤（房间创建者在自己房间允许URL）
is_admin = role in ['ADMIN', 'SUPERADMIN']
has_url = bool(URL_REGEX.search(obj_in.content))

if has_url:
    # Admin：允许任意内容
    if is_admin:
        pass
    # 房间创建者：允许在自己房间发送URL
    elif room.user_id == user_id:
        logger.info(
            f"房间创建者发送URL留言: user_id={user_id}, room_id={room.id}, "
            f"room_owner={room.user_id}"
        )
    # 其他用户：禁止URL
    else:
        logger.warning(
            f"非管理员/创建者尝试发送URL留言: user_id={user_id}, role={role}, "
            f"room_id={room.id}, room_owner={room.user_id}"
        )
        raise InvalidParameterException(
            code=4004, 
            message="非管理员用户不允许发送包含 URL 的留言"
        )
```

---

## ✅ 修改检查清单

### Tab 管理权限修改

- [ ] **步骤1**：新增 `_check_tab_management_permission` 方法（约30行）
- [ ] **步骤2**：修改 `list_tabs_for_admin` 方法（替换权限检查）
- [ ] **步骤3**：修改 `create_tab` 方法（替换权限检查）
- [ ] **步骤4**：修改 `update_tab` 方法（添加room查询 + 替换权限检查）
- [ ] **步骤5**：修改 `delete_tab` 方法（添加room查询 + 替换权限检查）

### 留言 URL 限制修改

- [ ] **步骤6**：修改 `create_message` 方法中的URL过滤逻辑（约8-10行）

---

## 🧪 测试建议

### Tab 管理权限测试

1. **Admin用户测试**：
   - [ ] Admin可以管理所有房间的Tab（包括他人创建的房间）
   - [ ] Admin管理他人房间Tab时，日志记录正确

2. **Regular用户测试**：
   - [ ] Regular用户可以管理自己创建的房间的Tab
   - [ ] Regular用户无法管理他人创建的房间的Tab（返回403）
   - [ ] Regular用户管理自己房间Tab时，日志记录正确

3. **匿名用户测试**：
   - [ ] 匿名用户无法访问Tab管理接口（返回401）

### 留言 URL 限制测试

1. **Admin用户测试**：
   - [ ] Admin可以在任何房间发送包含URL的留言

2. **房间创建者测试**：
   - [ ] 房间创建者可以在自己创建的直播间中发送包含URL的留言
   - [ ] 房间创建者发送URL留言时，日志记录正确

3. **Regular用户（非创建者）测试**：
   - [ ] Regular用户在他人创建的直播间中无法发送包含URL的留言（返回400）
   - [ ] Regular用户尝试发送URL留言时，警告日志记录正确

---

## 📝 注意事项

1. **保留 `_check_admin_role` 方法**：
   - 该方法可能用于其他功能，**不要删除**
   - 只在Tab管理相关方法中使用新的 `_check_tab_management_permission` 方法

2. **房间查询顺序**：
   - `update_tab` 和 `delete_tab` 需要先获取tab，然后从tab中获取room_id
   - `list_tabs_for_admin` 和 `create_tab` 已经有room_id参数，可以直接查询room

3. **日志记录**：
   - 确保所有权限检查都包含适当的日志记录
   - Admin管理他人房间Tab：INFO级别
   - 创建者管理Tab：INFO级别
   - 非授权尝试：WARNING级别

4. **异常处理**：
   - 权限不足时抛出 `PermissionDeniedException`（403）
   - 房间不存在时抛出 `RoomNotFoundException`（404）

---

## 🎯 修改完成确认

修改完成后，请确认：

- [ ] 所有Tab管理方法都使用 `_check_tab_management_permission` 替代 `_check_admin_role`
- [ ] `create_message` 方法中的URL过滤逻辑已更新
- [ ] 所有日志记录都已添加
- [ ] 代码可以正常编译/运行
- [ ] 所有测试用例通过

---

**修改完成时间**: ___________  
**修改人**: ___________  
**测试状态**: ___________

