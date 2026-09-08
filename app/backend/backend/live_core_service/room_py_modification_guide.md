# room.py 修改指南 - 扩展 GET /rooms/{id} 接口添加 tabs 字段

## 修改说明

本文档提供对现有 `app/api/v1/endpoints/room.py` 文件的**增量修改**指南，以实现在 `GET /rooms/{id}` 响应中添加 `tabs` 字段。

---

## 修改步骤

### 步骤 1：在 imports 部分添加新的导入

在 `room.py` 文件顶部的导入部分，添加以下内容：

```python
# --- 在现有 imports 后添加 ---
from fastapi import Request  # 导入 Request（如果还没有）
from app.services.live_features_service import TabService  # 导入新 Service
from app.schemas.live_features import LiveRoomTabResponse  # 导入新 Schema
from app.exceptions import RoomNotFoundException  # 导入异常（如果还没有）
```

---

### 步骤 2：修改现有的 get_room_details 端点

找到现有的 `get_room_details` 或类似名称的端点函数，并按以下方式修改：

#### 原始代码（假设）：

```python
@room_router.get("/{room_id}")
async def get_room_details(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取单个直播房间详情"""
    # 原有逻辑...
    room = await crud_room.get(db, room_id)
    if not room:
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="Room not found")
        )
    
    return success_response(data={"id": room.id, "title": room.title, ...})
```

#### 修改后代码（学院派规范）：

```python
@room_router.get("/{room_id}")
async def get_room_details(
    room_id: uuid.UUID,
    request: Request,  # [关键] 注入 Request 用于 URL 拼接
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个直播房间详情（扩展：包含 Tabs）
    """
    room_id_log = str(room_id)
    logger.info(f"Getting room details for room_id={room_id_log}")
    
    # [学院派] 启用 try/except
    try:
        # 1. [原逻辑] 获取房间基本信息
        room = await crud_room.get(db, room_id)
        if not room:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        
        # 2. [新增逻辑] 调用 TabService 获取激活的 Tabs
        tab_service = TabService(db)
        active_tabs = await tab_service.get_active_tabs_for_room(room_id=room_id)
        
        # 3. [新增逻辑] URL 拼接（学院派规范 5.3.C）
        base_url = str(request.base_url).rstrip('/')
        tabs_with_urls = []
        for tab in active_tabs:
            tab_response = LiveRoomTabResponse.model_validate(tab)
            # 拼接 image_url
            if tab_response.image_url and not tab_response.image_url.startswith('http'):
                tab_response.image_url = f"{base_url}{tab_response.image_url}"
            tabs_with_urls.append(tab_response.model_dump())
        
        # 4. [修改逻辑] 组装响应数据（添加 tabs 字段）
        room_response_data = {
            "id": str(room.id),
            "title": room.title,
            "description": room.description,
            "cover_url": room.cover_url,
            "is_private": room.is_private,
            "created_at": room.created_at.isoformat() if room.created_at else None,
            # ... 其他原有字段 ...
            "tabs": tabs_with_urls  # [关键] 添加 tabs 字段
        }
        
        return success_response(data=room_response_data)
    
    except RoomNotFoundException as e:
        logger.warning(f"Room not found: room_id={room_id_log}, error={str(e)}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message=str(e))
        )
    
    except Exception as e:
        logger.error(f"Error getting room details: room_id={room_id_log}, error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message=f"内部错误: {str(e)}")
        )
```

---

## 关键修改点说明

### 1. 注入 Request 依赖（学院派规范 5.3.C）

```python
async def get_room_details(
    room_id: uuid.UUID,
    request: Request,  # 新增
    db: AsyncSession = Depends(get_db)
):
```

**原因**：需要 `request.base_url` 来拼接完整的 URL。

---

### 2. 使用 try/except 块（学院派规范 5.1）

```python
try:
    # 业务逻辑
    ...
except RoomNotFoundException as e:
    # 捕获 Service 层抛出的自定义异常
    return JSONResponse(status_code=404, content=error_response(...))
except Exception as e:
    # 捕获未预期的异常
    return JSONResponse(status_code=500, content=error_response(...))
```

**原因**：Service 层抛出 Python 异常，需要在 API 层捕获并转换为 HTTP 响应。

---

### 3. 调用 TabService 获取 Tabs

```python
tab_service = TabService(db)
active_tabs = await tab_service.get_active_tabs_for_room(room_id=room_id)
```

**原因**：Service 层封装了业务逻辑（检查房间是否存在等）。

---

### 4. URL 拼接（学院派规范 5.3.C）

```python
base_url = str(request.base_url).rstrip('/')
for tab in active_tabs:
    tab_response = LiveRoomTabResponse.model_validate(tab)
    if tab_response.image_url and not tab_response.image_url.startswith('http'):
        tab_response.image_url = f"{base_url}{tab_response.image_url}"
    tabs_with_urls.append(tab_response.model_dump())
```

**原因**：
- 数据库只存储相对路径（如 `/media/tabs/xxx.png`）
- API 响应需要返回完整 URL（如 `http://example.com/media/tabs/xxx.png`）

---

### 5. 添加 tabs 字段到响应

```python
room_response_data = {
    # ... 原有字段 ...
    "tabs": tabs_with_urls  # 新增
}
```

**原因**：扩展现有接口，向前端返回 Tab 列表。

---

## 完整修改示例（最小化版本）

如果现有的 `get_room_details` 函数比较简单，可以参考以下最小化修改：

```python
from fastapi import Request
from app.services.live_features_service import TabService
from app.schemas.live_features import LiveRoomTabResponse
from app.exceptions import RoomNotFoundException

@room_router.get("/{room_id}")
async def get_room_details(
    room_id: uuid.UUID,
    request: Request,  # ← 新增
    db: AsyncSession = Depends(get_db)
):
    """获取单个直播房间详情（包含 Tabs）"""
    try:
        # 原有逻辑
        room = await crud_room.get(db, room_id)
        if not room:
            raise RoomNotFoundException(f"Room ID: {room_id} 不存在")
        
        # ========== 新增逻辑：获取 Tabs ==========
        tab_service = TabService(db)
        active_tabs = await tab_service.get_active_tabs_for_room(room_id)
        
        # URL 拼接
        base_url = str(request.base_url).rstrip('/')
        tabs_with_urls = []
        for tab in active_tabs:
            tab_dict = LiveRoomTabResponse.model_validate(tab).model_dump()
            if tab_dict.get('image_url') and not tab_dict['image_url'].startswith('http'):
                tab_dict['image_url'] = f"{base_url}{tab_dict['image_url']}"
            tabs_with_urls.append(tab_dict)
        # ==========================================
        
        # 组装响应（添加 tabs）
        room_data = {
            "id": str(room.id),
            "title": room.title,
            # ... 其他字段 ...
            "tabs": tabs_with_urls  # ← 新增
        }
        
        return success_response(data=room_data)
    
    except RoomNotFoundException as e:
        return JSONResponse(status_code=404, content=error_response(code=2001, message=str(e)))
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response(code=1000, message=str(e)))
```

---

## 响应格式示例

修改后的接口响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "我的直播间",
    "description": "直播间描述",
    "cover_url": "/media/rooms/xxx/cover.jpg",
    "is_private": false,
    "created_at": "2025-11-26T10:00:00Z",
    "tabs": [  // ← 新增字段
      {
        "id": "223e4567-e89b-12d3-a456-426614174001",
        "room_id": "123e4567-e89b-12d3-a456-426614174000",
        "tab_key": "introduction",
        "title": "直播介绍",
        "content_type": "text",
        "text_content": "欢迎来到我的直播间",
        "image_url": null,
        "sort_order": 0,
        "is_active": true,
        "created_at": "2025-11-26T10:00:00Z",
        "updated_at": "2025-11-26T10:00:00Z"
      },
      {
        "id": "323e4567-e89b-12d3-a456-426614174002",
        "tab_key": "products",
        "title": "商品展示",
        "content_type": "image",
        "text_content": null,
        "image_url": "http://example.com/media/tabs/products.jpg",  // ← 已拼接完整 URL
        "sort_order": 1,
        "is_active": true,
        "created_at": "2025-11-26T10:00:00Z",
        "updated_at": "2025-11-26T10:00:00Z"
      }
    ]
  }
}
```

---

## 注意事项

1. ✅ **Request 注入**：必须注入 `Request` 依赖用于 URL 拼接
2. ✅ **异常处理**：必须使用 try/except 捕获 Service 层异常
3. ✅ **URL 拼接**：只拼接相对路径，已是完整 URL 的跳过
4. ✅ **响应格式**：tabs 是一个数组，包含完整的 Tab 信息
5. ✅ **性能考虑**：`get_active_tabs_for_room` 只返回激活的 Tab，已按 sort_order 排序

---

## 测试建议

修改后，建议进行以下测试：

1. **基本功能测试**：
   ```bash
   curl -X GET http://localhost:8000/api/v1/rooms/{room_id}
   ```

2. **URL 拼接测试**：
   - 检查返回的 `tabs[].image_url` 是否为完整 URL
   - 检查相对路径是否正确拼接了 base_url

3. **异常测试**：
   - 测试不存在的 room_id（应返回 404）
   - 测试房间没有 tabs（应返回空数组）

---

## 总结

通过上述修改，`GET /rooms/{id}` 接口将：
- ✅ 返回房间的基本信息（原有功能）
- ✅ 返回房间的激活 Tab 列表（新增功能）
- ✅ 自动拼接完整的图片 URL（新增功能）
- ✅ 遵循学院派架构规范（异常处理、职责分离）

**修改完成后，前端即可通过该接口获取房间详情和 Tab 列表。**

