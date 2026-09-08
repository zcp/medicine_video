# API 接口说明

> 更新时间：YYYY-MM-DD

---

## 一、API 概览

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **请求格式**: JSON
- **响应格式**: JSON

### 通用响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": 1234567890
}
```

### 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 二、认证接口

### 2.1 用户登录

**接口**: `POST /auth/login`

**请求参数**:
```json
{
  "username": "user123",
  "password": "password123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "user123",
      "email": "user@example.com"
    }
  }
}
```

### 2.2 用户注册

**接口**: `POST /auth/register`

**请求参数**:
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "password123",
  "phone": "13800138000"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "public_id": "usr_abc123xyz"
  }
}
```

### 2.3 刷新Token

**接口**: `POST /auth/refresh`

**请求头**:
```
Authorization: Bearer {old_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "new_token_here"
  }
}
```

---

## 三、直播接口

### 3.1 创建直播间

**接口**: `POST /live/rooms`

**请求头**:
```
Authorization: Bearer {token}
```

**请求参数**:
```json
{
  "title": "我的直播",
  "description": "直播描述",
  "category_id": 1
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room_id": "live_abc123",
    "stream_key": "stream_key_here",
    "rtmp_url": "rtmp://push.example.com/live",
    "hls_url": "http://pull.example.com/live/abc123.m3u8"
  }
}
```

### 3.2 获取直播间列表

**接口**: `GET /live/rooms`

**请求参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `status`: 状态筛选（0:未开始,1:直播中,2:已结束）
- `category_id`: 分类筛选

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "room_id": "live_abc123",
        "title": "我的直播",
        "status": 1,
        "viewer_count": 1000,
        "host": {
          "username": "主播名",
          "avatar_url": "http://..."
        }
      }
    ]
  }
}
```

### 3.3 获取直播间详情

**接口**: `GET /live/rooms/{room_id}`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room_id": "live_abc123",
    "title": "我的直播",
    "description": "直播描述",
    "status": 1,
    "viewer_count": 1000,
    "start_time": "2026-01-01T10:00:00Z",
    "rtmp_url": "rtmp://push.example.com/live",
    "hls_url": "http://pull.example.com/live/abc123.m3u8"
  }
}
```

### 3.4 开始直播

**接口**: `POST /live/rooms/{room_id}/start`

**请求头**:
```
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room_id": "live_abc123",
    "status": 1,
    "start_time": "2026-01-01T10:00:00Z"
  }
}
```

### 3.5 结束直播

**接口**: `POST /live/rooms/{room_id}/end`

**请求头**:
```
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room_id": "live_abc123",
    "status": 2,
    "end_time": "2026-01-01T12:00:00Z",
    "duration": 7200
  }
}
```

---

## 四、用户接口

### 4.1 获取用户信息

**接口**: `GET /users/{user_id}`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "public_id": "usr_abc123xyz",
    "username": "user123",
    "email": "user@example.com",
    "avatar_url": "http://...",
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

### 4.2 更新用户信息

**接口**: `PUT /users/me`

**请求头**:
```
Authorization: Bearer {token}
```

**请求参数**:
```json
{
  "username": "new_username",
  "avatar_url": "http://new-avatar-url"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "new_username",
    "avatar_url": "http://new-avatar-url"
  }
}
```

---

## 五、互动接口

### 5.1 发送聊天消息

**接口**: `POST /live/rooms/{room_id}/chat`

**请求头**:
```
Authorization: Bearer {token}
```

**请求参数**:
```json
{
  "message": "大家好！"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "message_id": 12345,
    "message": "大家好！",
    "user": {
      "username": "user123"
    },
    "created_at": "2026-01-01T10:00:00Z"
  }
}
```

### 5.2 获取聊天消息列表

**接口**: `GET /live/rooms/{room_id}/chat`

**请求参数**:
- `last_id`: 最后一条消息ID（用于分页）
- `limit`: 数量（默认20，最大100）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "message_id": 12345,
        "message": "大家好！",
        "user": {
          "username": "user123",
          "avatar_url": "http://..."
        },
        "created_at": "2026-01-01T10:00:00Z"
      }
    ]
  }
}
```

### 5.3 点赞

**接口**: `POST /live/rooms/{room_id}/like`

**请求头**:
```
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room_id": "live_abc123",
    "like_count": 100
  }
}
```

---

## 六、分类接口

### 6.1 获取分类列表

**接口**: `GET /categories`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "教育",
      "slug": "education",
      "parent_id": null,
      "children": [
        {
          "id": 11,
          "name": "在线课程",
          "slug": "online-course",
          "parent_id": 1
        }
      ]
    }
  ]
}
```

---

## 七、WebSocket 接口

### 7.1 连接

**地址**: `ws://localhost:8000/ws/live/{room_id}`

**请求头**:
```
Authorization: Bearer {token}
```

### 7.2 消息类型

#### 客户端 -> 服务端

```json
{
  "type": "chat",
  "data": {
    "message": "消息内容"
  }
}
```

#### 服务端 -> 客户端

```json
{
  "type": "chat",
  "data": {
    "message_id": 12345,
    "message": "消息内容",
    "user": {
      "username": "user123",
      "avatar_url": "http://..."
    },
    "created_at": "2026-01-01T10:00:00Z"
  }
}
```

### 7.3 心跳保活

- 客户端每30秒发送一次 `ping`
- 服务端响应 `pong`

---

## 八、限流规则

| 接口类型 | 限制 |
|----------|------|
| 登录/注册 | 10次/分钟/IP |
| 发送消息 | 60次/分钟/用户 |
| 创建直播间 | 5次/小时/用户 |
| 其他接口 | 1000次/分钟/IP |

---

## 九、Swagger 文档

- **Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 十、接口变更历史

| 日期 | 接口 | 变更类型 | 说明 |
|------|------|----------|------|
| YYYY-MM-DD | /live/rooms | 新增 | 创建直播间接口 |
| YYYY-MM-DD | /live/rooms/{room_id}/chat | 修改 | 添加消息类型字段 |