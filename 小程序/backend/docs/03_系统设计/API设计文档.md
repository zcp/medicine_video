# 直播SaaS平台API设计文档

## 一、API概述

### 1.1 基本信息
- 基础URL: `https://api.example.com/v1`
- 认证方式: JWT Token
- 响应格式: JSON
- 字符编码: UTF-8

### 1.2 通用响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 实际数据内容
  }
}
```

### 1.3 错误码说明
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查参数格式 |
| 401 | 未授权 | 重新登录获取token |
| 403 | 禁止访问 | 检查权限 |
| 404 | 资源不存在 | 检查资源ID |
| 500 | 服务器错误 | 联系管理员 |

### 1.4 接口命名规范
- 使用RESTful风格
  - GET：获取资源
  - POST：创建资源
  - PUT：更新资源
  - DELETE：删除资源
  - PATCH：部分更新资源
- 使用小写字母
- 使用连字符（-）分隔单词
- 使用复数形式表示资源集合
- 使用动词表示操作
- 使用版本号前缀
- 使用资源层级关系

示例：
```
GET /v1/streams                    # 获取直播列表
POST /v1/streams                   # 创建直播
GET /v1/streams/{stream_id}        # 获取直播详情
PUT /v1/streams/{stream_id}        # 更新直播信息
DELETE /v1/streams/{stream_id}     # 删除直播
GET /v1/streams/{stream_id}/comments  # 获取直播评论
```

### 1.5 参数验证规范
- 必填参数验证
  - 使用required标记必填参数
  - 提供清晰的错误提示
- 参数类型验证
  - 字符串：长度、格式、正则
  - 数字：范围、精度
  - 布尔值：true/false
  - 日期时间：格式、范围
- 参数长度验证
  - 字符串最大/最小长度
  - 数组最大/最小长度
- 参数格式验证
  - 邮箱格式
  - 手机号格式
  - URL格式
  - 日期格式
- 参数范围验证
  - 数值范围
  - 枚举值范围
- 参数关联验证
  - 参数之间的依赖关系
  - 参数之间的互斥关系

### 1.6 参数安全验证
- 输入验证
  - 参数类型验证
  - 参数长度验证
  - 参数格式验证
  - 特殊字符过滤
- 输出转义
  - HTML转义
  - SQL转义
  - 特殊字符转义
- 安全过滤
  - XSS防护
  - CSRF防护
  - 敏感信息过滤
  - 文件上传验证

### 1.7 响应格式规范
- 统一响应结构
  ```json
  {
    "code": 200,           // 状态码
    "message": "success",  // 状态信息
    "data": {},           // 响应数据
    "timestamp": "2024-03-20T10:00:00Z"  // 时间戳
  }
  ```
- 统一错误码
  - 2xx：成功
  - 4xx：客户端错误
  - 5xx：服务器错误
- 统一时间格式
  - ISO 8601格式
  - UTC时区
- 统一分页格式
  ```json
  {
    "total": 100,         // 总记录数
    "page": 1,           // 当前页码
    "size": 10,          // 每页大小
    "items": []          // 数据列表
  }
  ```
- 统一空值处理
  - null：表示空值
  - []：表示空数组
  - {}：表示空对象
- 统一数据格式
  - 使用驼峰命名
  - 使用下划线命名
- 统一编码格式
  - UTF-8编码
  - Base64编码（二进制数据）

### 1.7 错误处理规范
- 错误码定义
  - 系统级错误：1xxx
  - 业务级错误：2xxx
  - 权限级错误：3xxx
  - 参数级错误：4xxx
- 错误信息格式
  ```json
  {
    "code": 400,
    "message": "参数错误",
    "details": {
      "field": "username",
      "error": "用户名不能为空"
    }
  }
  ```
- 错误处理流程
  1. 参数验证
  2. 业务验证
  3. 权限验证
  4. 异常捕获
  5. 错误响应
- 错误日志记录
  - 错误时间
  - 错误类型
  - 错误信息
  - 错误堆栈
  - 请求信息
  - 用户信息
- 错误通知机制
  - 邮件通知
  - 短信通知
  - 系统通知
- 错误恢复机制
  - 重试机制
  - 降级处理
  - 熔断处理
- 错误监控机制
  - 错误统计
  - 错误分析
  - 错误预警

### 1.8 版本控制规范
- 版本号格式
  - 主版本号：不兼容的API修改
  - 次版本号：向下兼容的功能性新增
  - 修订号：向下兼容的问题修正
- 版本升级策略
  - 主版本升级：需要客户端适配
  - 次版本升级：客户端可选适配
  - 修订版本升级：客户端无需适配
- 版本兼容性
  - 向下兼容
  - 向上兼容
  - 跨版本兼容
- 版本废弃策略
  - 提前通知
  - 过渡期
  - 替代方案
- 版本文档管理
  - 版本说明
  - 更新日志
  - 迁移指南
- 版本测试要求
  - 功能测试
  - 兼容性测试
  - 性能测试
- 版本发布流程
  1. 版本规划
  2. 开发测试
  3. 文档更新
  4. 评审发布
  5. 监控反馈

## 二、认证相关API

### 2.1 用户登录
- **接口**: `POST /auth/login`
- **描述**: 用户登录获取token
- **请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 3600,
    "user_info": {
      "user_id": "123",
      "username": "test_user",
      "role": "admin"
    }
  }
}
```

### 2.2 刷新Token
- **接口**: `POST /auth/refresh`
- **描述**: 刷新访问token
- **请求头**: `Authorization: Bearer {token}`
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 3600
  }
}
```

## 三、直播管理API

### 3.1 创建直播
- **接口**: `POST /streams`
- **描述**: 创建新的直播
- **请求参数**:
```json
{
  "title": "直播标题",
  "description": "直播描述",
  "cover_url": "封面图片URL",
  "start_time": "2024-03-20T10:00:00Z",
  "is_private": false,
  "category_id": "分类ID",
  "tags": ["标签1", "标签2"]
}
```
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "stream_id": "stream_123",
    "rtmp_url": "rtmp://push.example.com/live",
    "stream_key": "stream_key_123",
    "play_url": "https://play.example.com/live/stream_123"
  }
}
```

### 3.2 获取直播列表
- **接口**: `GET /streams`
- **描述**: 获取直播列表
- **查询参数**:
  - page: 页码
  - size: 每页数量
  - status: 直播状态
  - category_id: 分类ID
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "items": [
      {
        "stream_id": "stream_123",
        "title": "直播标题",
        "cover_url": "封面URL",
        "status": "live",
        "viewer_count": 100,
        "start_time": "2024-03-20T10:00:00Z"
      }
    ]
  }
}
```

### 3.3 获取直播详情
- **接口**: `GET /streams/{stream_id}`
- **描述**: 获取直播详细信息
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "stream_id": "stream_123",
    "title": "直播标题",
    "description": "直播描述",
    "cover_url": "封面URL",
    "status": "live",
    "viewer_count": 100,
    "like_count": 50,
    "comment_count": 30,
    "start_time": "2024-03-20T10:00:00Z",
    "end_time": null,
    "rtmp_url": "rtmp://push.example.com/live",
    "play_url": "https://play.example.com/live/stream_123"
  }
}
```

## 四、互动功能API

### 4.1 发送弹幕
- **接口**: `POST /streams/{stream_id}/danmaku`
- **描述**: 发送弹幕消息
- **请求参数**:
```json
{
  "content": "弹幕内容",
  "color": "#FFFFFF",
  "position": "top"
}
```
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "danmaku_id": "danmaku_123",
    "send_time": "2024-03-20T10:30:00Z"
  }
}
```

### 4.2 发送评论
- **接口**: `POST /streams/{stream_id}/comments`
- **描述**: 发送评论
- **请求参数**:
```json
{
  "content": "评论内容",
  "parent_id": "父评论ID"
}
```
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "comment_id": "comment_123",
    "content": "评论内容",
    "user_info": {
      "user_id": "123",
      "username": "test_user",
      "avatar": "头像URL"
    },
    "create_time": "2024-03-20T10:30:00Z"
  }
}
```

## 五、回放管理API

### 5.1 获取回放列表
- **接口**: `GET /streams/{stream_id}/playbacks`
- **描述**: 获取直播回放列表
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 10,
    "items": [
      {
        "playback_id": "playback_123",
        "title": "回放标题",
        "duration": 3600,
        "cover_url": "封面URL",
        "play_url": "https://play.example.com/playback/playback_123",
        "create_time": "2024-03-20T11:00:00Z"
      }
    ]
  }
}
```

### 5.2 获取回放详情
- **接口**: `GET /playbacks/{playback_id}`
- **描述**: 获取回放详细信息
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "playback_id": "playback_123",
    "title": "回放标题",
    "description": "回放描述",
    "duration": 3600,
    "cover_url": "封面URL",
    "play_url": "https://play.example.com/playback/playback_123",
    "resolution": "1920x1080",
    "file_size": 1024000,
    "create_time": "2024-03-20T11:00:00Z"
  }
}
```

## 六、统计分析API

### 6.1 获取直播统计数据
- **接口**: `GET /streams/{stream_id}/statistics`
- **描述**: 获取直播统计数据
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "viewer_count": {
      "total": 1000,
      "peak": 100,
      "average": 80
    },
    "interaction_count": {
      "like": 500,
      "comment": 200,
      "share": 100
    },
    "duration": 3600,
    "start_time": "2024-03-20T10:00:00Z",
    "end_time": "2024-03-20T11:00:00Z"
  }
}
```

### 6.2 获取用户观看记录
- **接口**: `GET /users/{user_id}/watch-history`
- **描述**: 获取用户观看历史
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 50,
    "items": [
      {
        "stream_id": "stream_123",
        "title": "直播标题",
        "cover_url": "封面URL",
        "watch_duration": 1800,
        "watch_time": "2024-03-20T10:00:00Z"
      }
    ]
  }
}
```

## 七、WebSocket API

### 7.1 连接信息
- **URL**: `wss://api.example.com/ws`
- **认证**: 通过URL参数传递token
- **心跳间隔**: 30秒

### 7.2 消息类型
```json
{
  "type": "danmaku|comment|like|viewer_count",
  "data": {
    // 具体消息内容
  }
}
```

### 7.3 事件类型
| 事件类型 | 说明 | 数据格式 |
|----------|------|----------|
| danmaku | 弹幕消息 | {content, color, position} |
| comment | 评论消息 | {content, user_info} |
| like | 点赞消息 | {user_info} |
| viewer_count | 观看人数 | {count} |

## 八、API安全规范

### 8.1 认证要求
- 所有API请求必须携带JWT token
- token过期时间：1小时
- 支持token刷新机制

### 8.2 访问控制
- 基于角色的访问控制（RBAC）
- API访问频率限制
- IP白名单控制

### 8.3 数据安全
- 所有请求必须使用HTTPS
- 敏感数据加密传输
- 防止SQL注入和XSS攻击

## 九、API版本控制

### 9.1 版本号规则
- 主版本号：重大更新
- 次版本号：功能更新
- 修订号：bug修复

### 9.2 版本兼容性
- 向下兼容原则
- 废弃API提前通知
- 版本过渡期支持

## 十、API文档更新记录

| 版本 | 更新日期 | 更新内容 | 作者 |
|------|----------|----------|------|
| v1.0 | 2024-03-20 | 初始版本 | 开发团队 |
| v1.1 | 2024-03-21 | 添加WebSocket API | 开发团队 |

## 三、媒体资源API

### 3.1 视频资源管理

#### 3.1.1 创建视频资源
- **接口**: `POST /v1/videos`
- **描述**: 创建新的视频资源
- **请求参数**:
```json
{
  "room_id": "string",           // 直播间ID
  "title": "string",            // 视频标题
  "description": "string",      // 视频描述
  "category_id": "string",      // 分类ID
  "is_public": boolean,         // 是否公开
  "permission_level": integer   // 权限级别
}
```
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "video_id": "8723901837_f22d",  // 遵循视频ID命名规范
    "storage_path": "/media/video_8723901837_f22d/",  // 遵循存储目录结构
    "created_at": "2024-03-20T10:00:00Z"
  }
}
```

#### 3.1.2 上传视频文件
- **接口**: `POST /v1/videos/{video_id}/upload`
- **描述**: 上传视频文件
- **请求参数**:
```json
{
  "file": "binary",            // 视频文件
  "file_type": "string",      // 文件类型(原始视频/封面/缩略图)
  "operation_type": "string"  // 操作类型(upload/transcoded)
}
```
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "file_name": "video_8723901837_f22d_upload_20240320T100000.mp4",  // 遵循文件命名规范
    "file_path": "/media/video_8723901837_f22d/raw/video_8723901837_f22d_upload_20240320T100000.mp4",
    "file_size": 1024000,
    "uploaded_at": "2024-03-20T10:00:00Z"
  }
}
```

#### 3.1.3 获取视频资源
- **接口**: `GET /v1/videos/{video_id}`
- **描述**: 获取视频资源信息
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "video_id": "8723901837_f22d",
    "room_id": "8723901837",
    "title": "视频标题",
    "description": "视频描述",
    "storage_path": "/media/video_8723901837_f22d/",
    "files": {
      "raw": {
        "path": "/media/video_8723901837_f22d/raw/video_8723901837_f22d_upload_20240320T100000.mp4",
        "size": 1024000,
        "created_at": "2024-03-20T10:00:00Z"
      },
      "hls": {
        "path": "/media/video_8723901837_f22d/hls_1080p_4000k/",
        "m3u8": "index_8723901837_f22d_upload_20240320T100000.m3u8",
        "created_at": "2024-03-20T10:00:00Z"
      },
      "cover": {
        "path": "/media/video_8723901837_f22d/images/cover_8723901837_f22d_upload_20240320T100000.jpg",
        "size": 50000,
        "created_at": "2024-03-20T10:00:00Z"
      }
    },
    "metadata": {
      "video_id": "8723901837_f22d",
      "room_id": "8723901837",
      "title": "视频标题",
      "created_at": "2024-03-20T10:00:00Z",
      "updated_at": "2024-03-20T10:00:00Z",
      "status": "active"
    }
  }
}
```

#### 3.1.4 获取视频访问URL
- **接口**: `GET /v1/videos/{video_id}/url`
- **描述**: 获取视频资源的访问URL
- **请求参数**:
```json
{
  "file_type": "string",      // 文件类型(raw/hls/mp4/cover/thumbnail)
  "expires_in": integer      // URL有效期(秒)
}
```
- **响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "url": "https://cdn.example.com/videos/8723901837_f22d/raw/video_8723901837_f22d_upload_20240320T100000.mp4?signature=xxx&expires=1710921600",
    "expires_at": "2024-03-21T10:00:00Z"
  }
}
``` 