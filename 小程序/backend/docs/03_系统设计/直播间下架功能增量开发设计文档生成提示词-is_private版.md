# 直播间下架功能增量开发设计文档生成任务（is_private简化版）

## 📋 任务目标
基于现有设计文档和代码实现，设计并生成**直播间下架功能**的完整增量开发文档（使用`is_private`字段实现），确保：
1. **所有需要修改的地方都被识别和记录（无遗漏）**
2. 新增功能符合现有编程规范、异常规范、日志规范、安全规范
3. 不会导致现有代码冲突
4. 包含完整的API接口、CRUD方法、Service方法设计
5. **确保所有功能模块（Brand、Topic、Homepage Search、User Behavior、Expert等）都正确处理下架逻辑**
6. **确保Session继承Room的下架状态，对普通用户不可见**
7. **修复所有通过ORM关系访问Room但未进行权限检查的问题**
8. **最小幅度增量开发**：尽量不影响其他代码，只修改必要的部分，优先复用现有逻辑和函数

## 🎯 核心功能需求

### 功能定义
- **下架状态**：通过将直播间的`is_private`字段设置为`true`实现下架，普通用户（包括其他Regular用户）无法看到该直播间
- **创建者可见**：直播间创建者在下架后仍然可以看到自己的直播间（符合现有`is_private`权限逻辑）
- **管理员可见**：Admin和SuperAdmin可以看到下架的直播间（符合现有`is_private`权限逻辑）
- **URL直接访问**：即使用户通过URL直接访问下架的直播间，也会被拒绝（返回404，除非是创建者或管理员）
- **Session继承**：下架直播间的所有Session对普通用户不可见（继承Room的`is_private`状态）

### 权限矩阵

| 用户类型 | 下架前可见 | 下架后可见（is_private=true） | 说明 |
|---------|-----------|------------------------------|------|
| **Anonymous（匿名）** | ✅ 公开房间 | ❌ 所有房间 | 下架后完全不可见 |
| **Regular User（普通用户，非创建者）** | ✅ 公开+自己的房间 | ❌ 所有房间 | 下架后完全不可见 |
| **Room Owner（创建者）** | ✅ 自己的房间 | ✅ 自己的房间 | **下架后仍可见**（符合现有逻辑） |
| **Admin/SuperAdmin** | ✅ 所有房间 | ✅ 所有房间 | 始终可见（符合现有逻辑） |

### 使用is_private实现下架的可行性分析

#### ✅ 可行性结论：**完全可行**

**原因分析**：
1. **权限逻辑完全匹配**：
   - 现有`_check_room_visibility`函数（`room_service.py`第48-89行）已经实现了`is_private`的权限检查
   - `is_private=true`时，创建者可见（第85行：`room.user_id == user_id`）
   - `is_private=true`时，管理员可见（第74行：`role in ['ADMIN', 'SUPERADMIN']`）
   - `is_private=true`时，普通用户不可见（第89行：抛出`NotFoundException`）

2. **业务语义兼容**：
   - `is_private=true`的语义是"私有"，与"下架"的语义在功能上一致
   - 下架后的房间对普通用户不可见，符合"私有"的定义
   - 创建者和管理员仍然可见，符合现有权限设计

3. **实现简化**：
   - 不需要新增数据库字段
   - 不需要修改`_check_room_visibility`函数
   - 只需要新增下架/上架API接口，将`is_private`设置为`true`/`false`

4. **向后兼容**：
   - 现有代码已经支持`is_private`字段
   - 所有CRUD层查询已经实现了`is_private`过滤
   - 所有Service层已经实现了`is_private`权限检查

#### ⚠️ 注意事项

1. **语义区分**：
   - `is_private=true`原本用于"私有房间"（创建者自己创建的私有房间）
   - 现在也用于"下架房间"（管理员下架的公开房间）
   - 两者在权限逻辑上完全一致，但在业务语义上略有不同
   - **建议**：在API文档和日志中明确说明，`is_private=true`可能表示"私有"或"下架"

2. **数据迁移**：
   - 如果现有数据中有`is_private=true`的房间，需要确认这些房间的语义
   - 如果这些房间原本是"私有房间"，下架功能不会影响它们
   - 如果这些房间原本是"公开房间"但被误设为私有，需要数据清理

3. **权限冲突预防**：
   - 下架操作只能由管理员执行（Admin/SuperAdmin）
   - 创建者不能重新上架被管理员下架的房间（需要权限检查）
   - 上架操作只能由管理员执行（Admin/SuperAdmin）

## 🔍 关键问题：ORM关系访问Room的权限检查缺失

### 问题描述

**发现的问题**：部分模块通过ORM关系（如`session.room`）或直接查询Room后访问Room信息，但没有进行权限检查，导致可能返回私有/下架房间的信息。

**已发现的问题**（必须修复）：

1. **Expert模块**（`expert_service.py`）：
   - `get_expert_sessions`方法（第207行）：通过`session.room`访问Room信息，没有检查Room的可见性
   - `get_followed_experts`方法（第571行）：查询关注列表的直播状态时，通过`get_expert_sessions`间接访问Room，没有检查Room的可见性

2. **User Behavior模块**（`user_behavior_service.py`）：
   - `create_subscription`方法（第124行）：通过`crud.room.get`获取Room，只检查是否存在，没有检查Room的可见性
   - **影响**：普通用户可能订阅私有/下架房间

3. **Live Features模块**（`live_features_service.py`）：
   - CRUD层通过`selectinload(LiveRoomTab.room)`预加载Room（`crud/live_features.py`第129行）
   - Service层通过`_check_room_exists`获取Room，然后调用`_check_tab_management_permission`进行权限检查
   - **验证结果**：已进行权限检查，但需要确认`_check_tab_management_permission`是否考虑了`is_private`状态

**其他可能存在的类似问题**（需要AI自行搜索验证）：
- 所有通过ORM关系访问Room的地方（`session.room`、`tab.room`等）
- 所有通过`joinedload`或`selectinload`预加载Room的地方
- 所有直接查询Room但只检查是否存在，没有检查可见性的地方

### 解决方案

**原则**：所有通过ORM关系访问Room的地方，在返回结果前必须检查Room的可见性。

**实施方式**：
1. **在Service层过滤**：在构造响应时，对每个Session检查其Room的可见性
2. **调用权限检查函数**：使用`_check_room_visibility`或实现相同的检查逻辑
3. **过滤不可见房间**：在返回结果前，过滤掉对当前用户不可见的房间

**修改模式**：
```python
# 修改前（expert_service.py）
for se in session_experts:
    session = se.session
    room = session.room if hasattr(session, 'room') else None
    session_item = {
        "room_title": room.title if room else None,
        "cover_url": room.cover_url if room else None
    }
    sessions_items.append(session_item)

# 修改后
for se in session_experts:
    session = se.session
    room = session.room if hasattr(session, 'room') else None
    
    # ← 新增：检查Room可见性
    if room:
        try:
            # 调用RoomService的权限检查函数
            from app.services.room_service import RoomService
            room_service = RoomService(self.db)
            room_service._check_room_visibility(room, current_user_id, role_user)
        except NotFoundException:
            # Room不可见，跳过该Session
            continue
    
    session_item = {
        "room_title": room.title if room else None,
        "cover_url": room.cover_url if room else None
    }
    sessions_items.append(session_item)
```

## 📚 需要读取的文档和代码

### 设计文档（按优先级）
1. **权限设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加权限设计版(非独立版).md`
   - 重点关注：
     - Room模块权限设计（第165-445行）
     - `_check_room_visibility`函数设计（第1167-1185行）
     - Session继承Room可见性的设计约束（第513行）
     - **关键约束**：第121行明确要求"CRUD层负责在SQL层面应用权限过滤逻辑——禁止内存过滤"
   
2. **核心功能设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_深度融合最终版.md`
   - 重点关注：live_rooms表结构（第76-103行）、Room API接口设计（第8.1节）、`is_private`字段定义

3. **配置与安全优化方案**：`docs/03_系统设计/直播核心功能设计文档----配置与安全优化方案.md`
   - 重点关注：安全规范、日志规范、环境变量规范、敏感信息处理规范

4. **后端新增API文档**：`docs/03_系统设计/直播核心功能设计文档_v6_后端新增api接口和模块设计文档-v2.md`
   - 重点关注：API接口设计规范、响应格式规范、错误码规范

5. **增量开发参考文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增量开发设计文档-品牌Logo上传-品牌关联直播间-专家头像上传.md`
   - 重点关注：增量开发文档的格式和结构

6. **专题功能设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_增加专题功能完整设计文档-修正版.md`
   - 重点关注：专题模块中涉及Room查询的部分

7. **首页与搜索模块设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_首页与搜索模块设计文档-焦点图-首页API-搜索API.md`
   - 重点关注：首页API直接查询live_rooms表

8. **用户行为模块设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_用户行为模块设计文档-收藏-观看历史-订阅提醒.md`
   - 重点关注：收藏功能涉及room_id，订阅功能验证Room存在性

9. **专家模块设计文档**：`docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md`
   - 重点关注：专家模块通过ORM关系访问Room的部分

### 代码实现（按优先级）
1. **Service层 - Room模块**：`backend/live_core_service/app/services/room_service.py`
   - 重点关注：`_check_room_visibility`（第48-89行）- 现有权限检查逻辑，无需修改
   - 重点关注：`update_room_info`（第274行）- 现有更新逻辑，需要添加下架/上架方法
   
2. **API层 - Room模块**：`backend/live_core_service/app/api/v1/endpoints/room.py`
   - 重点关注：现有Room API接口结构、权限依赖注入方式、Admin接口设计模式
   
3. **Service层 - Session模块**：`backend/live_core_service/app/services/session_service.py`
   - 重点关注：`list_room_sessions`、`get_session_details`方法（验证Session继承Room可见性）
   
4. **Service层 - Expert模块**：`backend/live_core_service/app/services/expert_service.py`
   - 重点关注：`get_expert_sessions`（第165行）- 通过ORM关系访问Room，需要添加权限检查
   - 重点关注：`get_followed_experts`（第540行）- 查询关注列表的直播状态，需要添加权限检查
   
5. **CRUD层 - Room模块**：`backend/live_core_service/app/crud/room.py`
   - 重点关注：现有代码中如何在SQL层面实现is_private过滤（已验证，无需修改）
   
6. **CRUD层 - Brand模块**：`backend/live_core_service/app/crud/brand.py`
   - 重点关注：`get_brand_rooms_paginated`（第524行）- 已实现is_private过滤，无需修改
   
7. **Service层 - Brand模块**：`backend/live_core_service/app/services/brand_service.py`
   - 重点关注：`bind_room_brands`、`get_room_brands_admin`、`get_room_brands_for_tab`方法
   - 验证：是否已调用`_check_room_visibility`或实现相同的权限检查
   
8. **CRUD层 - Topic模块**：`backend/live_core_service/app/crud/topic.py`
   - 重点关注：`get_rooms_by_category`（第657行）- 已实现is_private过滤，无需修改
   
9. **Service层 - Topic模块**：`backend/live_core_service/app/services/topic_service.py`
   - 重点关注：`get_topics_by_room`（第1109行）- 直接查询LiveRoom并检查可见性
   - 验证：是否已调用`_check_room_visibility`或实现相同的权限检查
   
10. **CRUD层 - Homepage Search模块**：`backend/live_core_service/app/crud/homepage_search.py`
    - 重点关注：`get_homepage_rooms_with_details`（第259行）- 已实现is_private过滤，无需修改
    
11. **Service层 - User Behavior模块**：`backend/live_core_service/app/services/user_behavior_service.py`
    - 重点关注：`create_subscription`（第109行）- 验证Room存在性时需要检查权限
    - 重点关注：`get_favorites`（第67行）- 返回的收藏列表包含room_id，需要过滤私有/下架房间
    
12. **CRUD层 - Expert模块**：`backend/live_core_service/app/crud/experts.py`
    - 重点关注：`get_expert_sessions`（第548行）- 通过ORM关系预加载Room信息（selectinload），不直接JOIN live_rooms表
    - **注意**：CRUD层不需要修改，权限检查在Service层完成

## 🔍 详细分析要求

### 1. 功能需求分析
- **下架功能定义**：
  - 通过将`is_private`设置为`true`实现下架
  - 普通用户（非创建者）无法看到下架的直播间
  - **创建者在下架后仍然可以看到自己的直播间**（符合现有`is_private`逻辑）
  - 管理员可以看到下架的直播间（符合现有`is_private`逻辑）
  - 即使用户通过URL直接访问，也会被拒绝（返回404，除非是创建者或管理员）
  - Session会继承Room的`is_private`状态（不可见）

### 2. 数据库设计分析
- **不需要新增字段**：使用现有的`is_private`字段
- **不需要数据库迁移**：现有表结构已支持
- **索引优化**：`is_private`字段已有索引（如果存在），无需新增

### 3. 权限逻辑分析
- **现有权限逻辑完全适用**：
  - `_check_room_visibility`函数已经实现了`is_private`的权限检查
  - 创建者可见：`room.user_id == user_id`（第85行）
  - 管理员可见：`role in ['ADMIN', 'SUPERADMIN']`（第74行）
  - 普通用户不可见：抛出`NotFoundException`（第89行）
- **无需修改权限检查函数**：现有逻辑完全满足需求

### 4. API接口设计分析
- 设计管理员下架接口：`PATCH /api/v1/admin/rooms/{room_id}/offline`
  - 功能：将`is_private`设置为`true`
  - 权限：仅Admin/SuperAdmin
  - 参考现有Admin接口的设计模式（如品牌Logo上传、专家头像上传）
- 设计管理员上架接口：`PATCH /api/v1/admin/rooms/{room_id}/online`
  - 功能：将`is_private`设置为`false`
  - 权限：仅Admin/SuperAdmin
  - **注意**：需要检查房间是否原本就是私有的（创建者创建的私有房间），如果是，上架操作应该保持私有状态或提示用户
- 确保符合现有API规范（认证、权限、响应格式、错误码）
- 参考配置与安全优化方案中的安全规范

### 5. CRUD层修改分析（必须系统性检查）

#### 5.1 验证现有实现（无需修改）

**Room模块**（`crud/room.py`）：
- `get_multi_and_total`（第111行）：已实现`is_private`过滤
- `list_with_search`（第207行）：已实现`is_private`过滤
- `get_sub_venues_with_live_status`（第517行）：已实现`is_private`过滤
- **结论**：无需修改，现有实现已支持`is_private`过滤

**Brand模块**（`crud/brand.py`）：
- `get_brand_rooms_paginated`（第524行）：已实现`is_private`过滤（JOIN查询）
- **结论**：无需修改，现有实现已支持`is_private`过滤

**Topic模块**（`crud/topic.py`）：
- `get_rooms_by_category`（第657行）：已实现`is_private`过滤
- **结论**：无需修改，现有实现已支持`is_private`过滤

**Homepage Search模块**（`crud/homepage_search.py`）：
- `get_homepage_rooms_with_details`（第259行）：已实现`is_private`过滤（原生SQL）
- **结论**：无需修改，现有实现已支持`is_private`过滤

**Expert模块**（`crud/experts.py`）：
- `get_expert_sessions`（第548行）：通过ORM关系预加载Room，不直接JOIN
- **结论**：无需修改，权限检查在Service层完成

### 6. Service层修改分析（必须系统性检查）

#### 6.1 直接修改（room_service.py）

- **新增方法**：`offline_room`（下架房间）
  ```python
  async def offline_room(
      self,
      room_id: uuid.UUID,
      user_id: uuid.UUID,
      role: str
  ) -> RoomItem:
      """
      下架直播间（将is_private设置为true）
      
      Args:
          room_id: 直播间ID
          user_id: 当前用户ID
          role: 用户角色
      
      Returns:
          RoomItem: 更新后的直播间信息
      
      Raises:
          PermissionDeniedException: 如果无管理员权限
          NotFoundException: 如果房间不存在
      """
      # 权限检查：仅Admin/SuperAdmin
      self._check_admin_permission(role)
      
      # 查询房间
      room = await crud_room.get(self.db, room_id)
      if not room:
          raise NotFoundException(f"Room not found: {room_id}")
      
      # 更新is_private
      room.is_private = True
      await self.db.flush()
      await self.db.refresh(room)
      
      self.logger.info(f"下架直播间: room_id={str(room_id)[:8]}, admin={str(user_id)[:8]}")
      return RoomItem.model_validate(room)
  ```

- **新增方法**：`online_room`（上架房间）
  ```python
  async def online_room(
      self,
      room_id: uuid.UUID,
      user_id: uuid.UUID,
      role: str
  ) -> RoomItem:
      """
      上架直播间（将is_private设置为false）
      
      Args:
          room_id: 直播间ID
          user_id: 当前用户ID
          role: 用户角色
      
      Returns:
          RoomItem: 更新后的直播间信息
      
      Raises:
          PermissionDeniedException: 如果无管理员权限
          NotFoundException: 如果房间不存在
      """
      # 权限检查：仅Admin/SuperAdmin
      self._check_admin_permission(role)
      
      # 查询房间
      room = await crud_room.get(self.db, room_id)
      if not room:
          raise NotFoundException(f"Room not found: {room_id}")
      
      # 更新is_private
      room.is_private = False
      await self.db.flush()
      await self.db.refresh(room)
      
      self.logger.info(f"上架直播间: room_id={str(room_id)[:8]}, admin={str(user_id)[:8]}")
      return RoomItem.model_validate(room)
  ```

- **验证现有方法**：
  - `_check_room_visibility`（第48行）：无需修改，现有逻辑完全适用
  - `get_room_list`、`get_room_details`：已调用`_check_room_visibility`，无需修改

#### 6.2 间接修改（需要验证和修改）

**Session模块**（`services/session_service.py`）：
- `list_room_sessions`（第200行）：已调用`_check_room_visibility`（第216行），会自动继承
  - **验证**：确认调用`_check_room_visibility`，无需修改
- `get_session_details`（第240行）：已调用`_check_room_visibility`（第278行），会自动继承
  - **验证**：确认调用`_check_room_visibility`，无需修改

**Topic模块**（`services/topic_service.py`）：
- `get_topics_by_room`（第1109行）：直接查询LiveRoom并检查可见性
  - 当前实现：第1128-1133行只检查了is_private
  - **验证**：确认是否已调用`_check_room_visibility`或实现相同的检查逻辑
  - **如果需要修改**：改为调用RoomService的`_check_room_visibility`方法

**Brand模块**（`services/brand_service.py`）：
- `bind_room_brands`（第625行）：验证直播间存在（第655行），但没有权限检查
  - 当前实现：只检查room是否存在
  - **需要修改**：添加`_check_room_visibility`检查（管理员接口，但需要确保房间可见）
- `get_room_brands_admin`（第690行）：验证直播间存在（第717行），但没有权限检查
  - 当前实现：只检查room是否存在
  - **需要修改**：添加`_check_room_visibility`检查（管理员接口，但需要确保房间可见）
- `get_room_brands_for_tab`（第734行）：验证直播间存在（第762行），但没有权限检查
  - 当前实现：只检查room是否存在
  - **需要修改**：添加`_check_room_visibility`检查（公开接口，需要检查可见性）

**Homepage Search模块**（`services/homepage_search_service.py`）：
- `get_homepage_rooms`（第456行）：调用CRUD层，CRUD层已过滤
  - 当前实现：调用`crud.get_homepage_rooms_with_details`
  - **验证**：CRUD层已实现is_private过滤，Service层无需修改

**User Behavior模块**（`services/user_behavior_service.py`）：
- `create_subscription`（第109行）：验证Room存在性（第124行），但没有权限检查
  - 当前实现：只检查room是否存在
  - **需要修改**：添加`_check_room_visibility`检查（确保私有/下架房间不能被订阅，但创建者可以订阅自己的房间）
- `get_favorites`（第67行）：返回收藏列表，包含room_id
  - 当前实现：只返回收藏记录，不查询Room详情
  - **需要修改**：在返回收藏列表时，需要过滤掉私有/下架的房间（但创建者可以看到自己房间的收藏）
  - **注意**：这需要在Service层过滤，因为CRUD层只返回收藏记录，不包含Room信息

**Expert模块**（`services/expert_service.py`）：
- `get_expert_sessions`（第165行）：通过ORM关系访问Room（第207行），没有权限检查
  - 当前实现：通过`session.room`访问Room信息，没有检查Room可见性
  - **需要修改**：在返回场次列表前，需要过滤掉私有/下架Room的Session（但创建者可以看到自己的Session）
  - **修改方式**：在构造响应时，对每个Session检查其Room的可见性（**优先复用`_check_room_visibility`函数**，避免重复实现）
  - **注意**：由于是通过ORM关系访问Room，CRUD层不需要修改，只需在Service层过滤（最小幅度修改）
- `get_followed_experts`（第540行）：查询关注列表的直播状态，通过`get_expert_sessions`查询（第571行）
  - 当前实现：查询专家参与的正在直播的场次，没有检查Room可见性
  - **需要修改**：在查询直播状态时，需要过滤掉私有/下架Room的Session（但创建者可以看到自己的Session）
  - **修改方式**：在查询直播状态后，对每个Session检查其Room的可见性（**优先复用`_check_room_visibility`函数**）

**User Behavior模块**（`services/user_behavior_service.py`）：
- `create_subscription`（第109行）：通过`crud.room.get`获取Room（第124行），只检查是否存在，没有权限检查
  - 当前实现：只检查room是否存在
  - **需要修改**：添加`_check_room_visibility`检查（确保私有/下架房间不能被订阅，但创建者可以订阅自己的房间）
  - **修改方式**：在验证Room存在后，调用`_check_room_visibility`检查可见性（**优先复用现有函数**）

**Live Features模块**（`services/live_features_service.py`）：
- Tab相关方法：通过`_check_room_exists`获取Room，然后调用`_check_tab_management_permission`进行权限检查
  - 当前实现：已进行权限检查（创建者或Admin）
  - **需要验证**：确认`_check_tab_management_permission`是否考虑了`is_private`状态
  - **如果未考虑**：需要修改`_check_tab_management_permission`，确保私有/下架房间的Tab对普通用户不可见（但创建者和Admin可见）

**验证方法**：
- 搜索所有包含`session.room`或通过ORM关系访问Room的文件
- 确认这些访问都会进行权限检查
- 确保没有遗漏任何访问点

### 7. 其他模块影响分析（必须系统性检查）

**检查方法**：
1. 使用grep搜索所有通过ORM关系访问Room的文件
2. 逐个分析是否需要添加权限检查
3. 确定修改方案

**可能受影响的模块**：
- ✅ **Expert模块**：`expert_service.py` - 需要修改（通过ORM关系访问Room，需要添加权限检查）
- ✅ **User Behavior模块**：`user_behavior_service.py` - 需要修改（验证Room存在性、过滤收藏列表）
- ⚠️ **Topic模块**：`topic_service.py` - 需要验证（是否已调用`_check_room_visibility`）
- ⚠️ **Brand模块**：`brand_service.py` - 需要验证（是否已调用`_check_room_visibility`）
- ⚠️ **首页搜索**：`homepage_search.py`、`homepage_search_service.py` - 已验证，CRUD层已过滤，无需修改
- ⚠️ **内容管理模块**：通过session间接关联，Session会继承Room的`is_private`状态，无需修改
- ⚠️ **用户偏好与通知模块**：只存储related_id，不直接查询Room，无需修改
- ⚠️ **Live Features模块**：需要验证Tab相关方法的权限检查是否考虑了`is_private`状态

### 8. 编程规范检查
确保新增代码符合：
- **异常规范**：使用项目定义的异常类（NotFoundException、PermissionDeniedException等）
- **日志规范**（参考配置与安全优化方案）：
  - 使用logger，记录关键操作（INFO级别）
  - 错误记录（ERROR级别）
  - 权限相关记录（WARNING级别）
  - **禁止**：日志中泄露敏感信息（如完整UUID、密码等）
  - UUID脱敏：使用前8位（如`user_id[:8]`）
- **安全规范**（参考配置与安全优化方案）：
  - 权限检查
  - 参数验证
  - 环境变量使用（不使用硬编码）
- **代码风格**：遵循现有代码风格，使用类型提示，添加docstring

## 📝 输出文档要求

生成一份完整的增量开发设计文档，参考格式：`docs/03_系统设计/直播核心功能设计文档_v6_增量开发设计文档-品牌Logo上传-品牌关联直播间-专家头像上传.md`

### 文档结构要求

#### 1. 文档头部信息
- 版本号
- 创建日期
- 更新日期
- 状态
- 基于文档清单
- **特别说明**：使用`is_private`字段实现下架功能，无需新增数据库字段

#### 2. 增量开发定位
- 核心目标
- **增量原则**（必须强调）：
  - ✅ **最小幅度修改**：只修改必要的代码，尽量不影响其他功能
  - ✅ **优先复用**：优先复用现有的权限检查函数（`_check_room_visibility`），避免重复实现
  - ✅ **向后兼容**：使用现有`is_private`字段，不影响现有数据
  - ✅ **最小影响范围**：只修改直接相关的模块，避免大规模重构
  - ✅ **保持一致性**：修改模式与现有代码保持一致，遵循现有架构设计
- 技术依赖
- **is_private实现说明**（说明为什么使用`is_private`而不是新增字段）

#### 3. 依赖文档清单
- 列出所有依赖的设计文档

#### 4. 功能概述
- 功能描述
- 业务需求
- 设计原则
- **is_private实现说明**（说明使用`is_private`的可行性和注意事项）
- **ORM关系权限检查说明**（说明需要修复的权限检查缺失问题）

#### 5. 数据库设计
- **不需要新增字段**：使用现有的`is_private`字段
- **不需要数据库迁移**：现有表结构已支持
- **索引说明**：`is_private`字段已有索引（如果存在）

#### 6. 模型和Schema修改
- **LiveRoom模型**：无需修改，使用现有的`is_private`字段
- **Pydantic Schema**：无需修改，使用现有的Schema

#### 7. 函数依赖关系图（关键章节）
**必须包含**：
- 所有需要修改的函数列表（按文件分类）
- 每个函数的调用关系（谁调用它，它调用谁）
- 修改类型（新增/修改/验证）
- 修改内容（简要说明）

**格式示例**：
```markdown
## 7. 函数依赖关系图

### 7.1 CRUD层修改清单

| 文件 | 函数名 | 行号 | 修改类型 | 修改内容 | 调用者 | 被调用者 |
|------|--------|------|----------|----------|--------|----------|
| crud/room.py | get_multi_and_total | 111 | 验证 | 已实现is_private过滤，无需修改 | room_service.get_room_list | - |
| crud/brand.py | get_brand_rooms_paginated | 524 | 验证 | 已实现is_private过滤，无需修改 | brand_service.get_brand_rooms_paginated | - |
| crud/topic.py | get_rooms_by_category | 657 | 验证 | 已实现is_private过滤，无需修改 | topic_service.get_rooms_in_category | - |
| crud/homepage_search.py | get_homepage_rooms_with_details | 259 | 验证 | 已实现is_private过滤，无需修改 | homepage_search_service.get_homepage_rooms | - |
| crud/experts.py | get_expert_sessions | 548 | 验证 | 通过ORM关系预加载，权限检查在Service层 | expert_service.get_expert_sessions | - |

### 7.2 Service层修改清单

| 文件 | 函数名 | 行号 | 修改类型 | 修改内容 | 调用者 | 被调用者 |
|------|--------|------|----------|----------|--------|----------|
| services/room_service.py | offline_room | 新增 | 新增 | 下架接口（设置is_private=true） | API层 | - |
| services/room_service.py | online_room | 新增 | 新增 | 上架接口（设置is_private=false） | API层 | - |
| services/room_service.py | _check_room_visibility | 48 | 验证 | 现有逻辑完全适用，无需修改 | get_room_details, get_room_list, session_service | - |
| services/session_service.py | list_room_sessions | 200 | 验证 | 已调用_check_room_visibility，自动继承 | API层 | _check_room_visibility |
| services/expert_service.py | get_expert_sessions | 165 | 修改 | 添加Room可见性检查（过滤私有/下架房间） | API层 | _check_room_visibility |
| services/expert_service.py | get_followed_experts | 540 | 修改 | 添加Room可见性检查（过滤私有/下架房间） | API层 | _check_room_visibility |
| services/topic_service.py | get_topics_by_room | 1109 | 验证 | 验证是否已调用_check_room_visibility | API层 | - |
| services/brand_service.py | bind_room_brands | 625 | 修改 | 添加_check_room_visibility检查 | API层 | _check_room_visibility |
| services/brand_service.py | get_room_brands_for_tab | 734 | 修改 | 添加_check_room_visibility检查 | API层 | _check_room_visibility |
| services/user_behavior_service.py | create_subscription | 109 | 修改 | 添加_check_room_visibility检查 | API层 | _check_room_visibility |
| services/user_behavior_service.py | get_favorites | 67 | 修改 | 过滤私有/下架房间（创建者除外） | API层 | - |
| services/live_features_service.py | _check_tab_management_permission | 104 | 验证 | 验证是否考虑了is_private状态 | Tab相关方法 | - |

### 7.3 API层修改清单

| 文件 | 函数名 | 行号 | 修改类型 | 修改内容 | 调用者 | 被调用者 |
|------|--------|------|----------|----------|--------|----------|
| api/v1/endpoints/room.py | offline_room | 新增 | 新增 | 下架接口 | FastAPI路由 | room_service.offline_room |
| api/v1/endpoints/room.py | online_room | 新增 | 新增 | 上架接口 | FastAPI路由 | room_service.online_room |
```

#### 8. CRUD层修改清单（详细）
列出所有需要验证的CRUD方法，每个方法包含：
- 方法名称和位置（文件路径+行号）
- 当前实现（代码片段）
- 验证结果（是否已实现is_private过滤）
- 结论（是否需要修改）

**必须包含的模块**：
- Room模块（`crud/room.py`）- 验证，无需修改
- Brand模块（`crud/brand.py`）- 验证，无需修改
- Topic模块（`crud/topic.py`）- 验证，无需修改
- Homepage Search模块（`crud/homepage_search.py`）- 验证，无需修改
- Expert模块（`crud/experts.py`）- 验证，无需修改（权限检查在Service层）

#### 9. Service层修改清单（详细）
列出所有需要修改或验证的Service方法，每个方法包含：
- 方法名称和位置（文件路径+行号）
- 当前实现（代码片段）
- 修改后实现（代码片段）
- 修改原因
- 测试要点

**必须包含的模块**：
- Room模块（`services/room_service.py`）- 新增下架/上架方法
- Session模块（`services/session_service.py`）- 验证继承性
- Expert模块（`services/expert_service.py`）- 修改，添加权限检查
- Topic模块（`services/topic_service.py`）- 验证，确认是否已调用权限检查
- Brand模块（`services/brand_service.py`）- 修改，添加权限检查
- Homepage Search模块（`services/homepage_search_service.py`）- 验证，无需修改
- User Behavior模块（`services/user_behavior_service.py`）- 修改，添加权限检查
- Live Features模块（`services/live_features_service.py`）- 验证

#### 10. API接口设计
- 下架接口设计（Endpoint、认证、请求参数、响应格式、错误码、执行流程）
- 上架接口设计（同上）
- 参考现有Admin接口的设计模式

#### 11. ORM关系权限检查修复
**关键章节**：列出所有通过ORM关系访问Room或直接查询Room但未进行权限检查的地方

**必须包含**（已发现的问题）：
- Expert模块的`get_expert_sessions`方法
- Expert模块的`get_followed_experts`方法
- User Behavior模块的`create_subscription`方法
- Live Features模块的Tab相关方法（验证`_check_tab_management_permission`是否考虑了`is_private`）
- **其他可能存在的类似问题**（AI需要自行搜索验证）

**每个问题包含**：
- 问题描述
- 当前实现（代码片段）
- 修改方案（代码片段）
- 修改原因
- 测试要点

**搜索方法**（AI必须执行）：
1. 使用grep搜索所有包含`session.room`、`tab.room`、`.room`的代码
2. 使用grep搜索所有包含`joinedload.*room`、`selectinload.*room`的代码
3. 使用grep搜索所有包含`crud.room.get`、`select(LiveRoom)`的代码
4. 逐个分析每个访问点是否进行了权限检查
5. 列出所有需要修改的地方
6. **最小幅度修改说明**：对于每个需要修改的地方，说明如何以最小幅度修改，优先复用现有函数（如`_check_room_visibility`）
6. **最小幅度修改说明**：对于每个需要修改的地方，说明如何以最小幅度修改，优先复用现有函数（如`_check_room_visibility`）

#### 12. 其他模块影响分析
- 列出所有可能受影响的其他模块
- 说明是否需要修改
- 如需修改，提供修改方案（**强调最小幅度修改，优先复用现有函数**）
- **如果不需要修改，说明原因**（例如：已通过调用`_check_room_visibility`自动继承，或CRUD层已实现过滤）

#### 13. 系统性检查验证清单
**必须包含以下检查结果**：

##### 13.1 `_check_room_visibility`调用点检查
- [ ] 搜索所有调用`_check_room_visibility`的文件
- [ ] 列出所有调用点（文件+函数+行号）
- [ ] 确认每个调用点都会受到`is_private`逻辑影响
- [ ] 验证没有遗漏任何调用点

##### 13.2 Room查询CRUD方法检查
- [ ] 搜索所有涉及Room查询的CRUD方法
- [ ] 列出所有需要验证的方法（包括其他模块）
- [ ] 确认每个方法都已实现`is_private`过滤（创建者除外）
- [ ] 验证没有遗漏任何查询方法

##### 13.3 Room查询Service方法检查
- [ ] 搜索所有涉及Room查询的Service方法
- [ ] 列出所有需要修改或验证的方法
- [ ] 确认每个方法都正确处理了`is_private`逻辑（包括创建者可见）
- [ ] 验证没有遗漏任何方法

##### 13.4 ORM关系访问Room检查（关键）
- [ ] 搜索所有通过ORM关系访问Room的地方（`session.room`、`tab.room`、`joinedload`、`selectinload`）
- [ ] 搜索所有直接查询Room但只检查是否存在的地方（`crud.room.get`、`select(LiveRoom)`）
- [ ] 列出所有需要添加权限检查的地方（包括已发现的Expert模块和User Behavior模块）
- [ ] 确认每个访问点都进行了权限检查（调用`_check_room_visibility`或实现相同的检查逻辑）
- [ ] 验证没有遗漏任何访问点
- [ ] **特别检查**：
  - Expert模块的`get_expert_sessions`和`get_followed_experts`方法
  - User Behavior模块的`create_subscription`方法
  - Live Features模块的Tab相关方法（验证`_check_tab_management_permission`是否考虑了`is_private`）
  - 其他可能通过ORM关系访问Room的模块

##### 13.5 Room相关API端点检查
- [ ] 搜索所有Room相关的API端点
- [ ] 列出所有端点及其权限检查
- [ ] 确认每个端点都正确处理了`is_private`逻辑
- [ ] 验证没有遗漏任何端点

##### 13.6 间接调用链检查
- [ ] 从API层追踪到Service层
- [ ] 从Service层追踪到CRUD层
- [ ] 确保整个调用链都考虑了`is_private`过滤（创建者除外）
- [ ] 验证没有遗漏任何调用链

##### 13.7 Session继承性验证
- [ ] 验证Session的所有查询方法都调用了`_check_room_visibility`
- [ ] 确认Session会继承Room的`is_private`状态
- [ ] 验证私有/下架房间的Session对普通用户不可见（但创建者可见）

##### 13.8 其他模块Room查询检查
- [ ] Brand模块：检查所有Room查询方法
- [ ] Topic模块：检查所有Room查询方法
- [ ] Homepage Search模块：检查所有Room查询方法
- [ ] User Behavior模块：检查所有Room相关方法（订阅、收藏）
- [ ] Expert模块：检查所有通过ORM关系访问Room的方法（get_expert_sessions、get_followed_experts）
- [ ] 其他可能涉及Room查询的模块

##### 13.9 创建者可见性验证
- [ ] 验证私有/下架后创建者仍可见的逻辑
- [ ] 验证CRUD层过滤时创建者除外
- [ ] 验证Service层检查时创建者可见
- [ ] 验证所有相关模块都正确处理了创建者可见性

#### 14. 测试设计
- 单元测试用例
- 集成测试用例
- 权限测试用例
- 边界测试用例（私有/下架房间的各种访问场景）
- Session继承性测试用例
- **创建者可见性测试用例**（私有/下架后创建者仍可见）
- **ORM关系权限检查测试用例**（验证通过ORM关系访问Room时是否正确进行权限检查）

#### 15. 实施检查清单
- 代码修改清单（按文件分类，包含行号）
- 测试清单
- 部署注意事项
- **特别说明**：不需要数据库迁移，不需要新增字段

## ✅ 验证要求

生成的文档必须确保：

1. **完整性**：
   - ✅ 所有需要修改的地方都已列出，无遗漏
   - ✅ 函数依赖关系图完整
   - ✅ 系统性检查验证清单全部完成
   - ✅ 所有模块（Brand、Topic、Homepage Search、User Behavior、Expert等）都已检查
   - ✅ **所有通过ORM关系访问Room的地方都已检查**

2. **一致性**：
   - ✅ 新增代码符合现有代码风格和规范
   - ✅ CRUD层和Service层的权限检查逻辑一致
   - ✅ 与现有`is_private`过滤模式一致
   - ✅ **创建者可见性逻辑一致**（私有/下架后创建者仍可见）

3. **安全性**：
   - ✅ 权限检查完整，无安全漏洞
   - ✅ 符合配置与安全优化方案中的安全规范
   - ✅ 日志规范符合要求（不泄露敏感信息）
   - ✅ **ORM关系访问Room时都进行了权限检查**

4. **可追溯性**：
   - ✅ 每个修改都有明确的理由和参考依据
   - ✅ 函数依赖关系清晰
   - ✅ 调用链完整

5. **可实施性**：
   - ✅ 修改步骤清晰，可以直接按文档实施
   - ✅ 每个修改点都有具体的代码示例
   - ✅ 测试用例完整
   - ✅ **不需要数据库迁移，实施简单**

## 🎯 特别注意事项

1. **最小幅度增量开发原则**：
   - ✅ **只修改必要的代码**：优先复用现有函数（如`_check_room_visibility`），避免重复实现
   - ✅ **最小影响范围**：只修改直接相关的模块，避免大规模重构
   - ✅ **保持一致性**：修改模式与现有代码保持一致，遵循现有架构设计
   - ✅ **向后兼容**：使用现有`is_private`字段，完全向后兼容，不影响现有数据
   - ✅ **避免过度修改**：不要修改不相关的代码，不要改变现有函数的签名（除非必要）

2. **is_private实现说明**：必须在文档中明确说明为什么使用`is_private`而不是新增字段，以及语义上的注意事项

3. **Session继承性**：确保Session会继承Room的`is_private`状态，无需单独处理Session（但需要验证所有Session查询都调用了`_check_room_visibility`）

4. **权限优先级**：`is_private`检查已在现有`_check_room_visibility`函数中实现，无需修改

5. **管理员权限**：管理员应能看到所有房间（包括私有/下架的）

6. **创建者权限**：**创建者在私有/下架后仍然可以看到自己的直播间**（这是关键需求，符合现有逻辑）

7. **错误处理**：私有/下架房间对普通用户应返回404（隐藏存在性），而非403

8. **系统性检查**：必须使用grep等工具搜索所有相关函数，确保无遗漏

9. **函数依赖关系**：必须绘制完整的函数依赖关系图，标注所有调用关系

10. **其他模块**：必须检查Brand、Topic、Homepage Search、User Behavior、Expert等所有涉及Room查询的模块

11. **创建者可见性**：在所有权限检查逻辑中，都要确保创建者可以看到自己的私有/下架房间

12. **ORM关系权限检查**：**必须修复所有通过ORM关系访问Room但未进行权限检查的问题**（这是关键安全问题），优先复用`_check_room_visibility`函数

## 📌 输出格式

请以Markdown格式输出，使用清晰的章节结构，代码示例使用代码块，重要内容使用表格或列表展示。

**关键章节格式要求**：
- 函数依赖关系图必须使用表格格式
- 每个修改点必须标注文件路径和行号
- 系统性检查验证清单必须使用复选框格式
- 代码修改必须提供修改前后的对比
- 参考增量开发文档的格式和结构
- **ORM关系权限检查修复章节必须详细列出所有问题和解决方案**

## 🔍 生成文档后的验证步骤

生成文档后，请执行以下验证：

1. **完整性验证**：
   - [ ] 所有CRUD方法都已验证（包括其他模块）
   - [ ] 所有Service方法都已列出（包括其他模块）
   - [ ] 所有API接口都已设计
   - [ ] 函数依赖关系图完整
   - [ ] 创建者可见性逻辑在所有相关方法中都已体现
   - [ ] **所有通过ORM关系访问Room的地方都已检查**

2. **一致性验证**：
   - [ ] 修改模式与现有代码一致
   - [ ] 权限检查逻辑一致
   - [ ] 错误处理方式一致
   - [ ] 创建者可见性逻辑一致

3. **可实施性验证**：
   - [ ] 每个修改点都有明确的代码示例
   - [ ] 修改步骤清晰
   - [ ] 测试用例完整
   - [ ] 创建者可见性的测试用例完整
   - [ ] **ORM关系权限检查的测试用例完整**

4. **无遗漏验证**：
   - [ ] 系统性检查清单全部完成
   - [ ] 所有模块都已检查
   - [ ] 所有调用链都已追踪
   - [ ] 创建者可见性在所有相关方法中都已实现
   - [ ] **所有通过ORM关系访问Room的地方都已添加权限检查**

5. **最小幅度增量开发验证**：
   - [ ] 所有修改都优先复用了现有函数（如`_check_room_visibility`）
   - [ ] 没有修改不相关的代码
   - [ ] 没有改变现有函数的签名（除非必要）
   - [ ] 修改范围最小化，只修改直接相关的模块
