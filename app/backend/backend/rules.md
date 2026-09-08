# 直播SaaS平台开发规范

## 一、代码规范

### 1.1 通用规范
- 遵循 PEP 8 规范
- 使用 UTF-8 编码
- 使用 4 个空格缩进
- 行尾不保留空格
- 文件末尾保留一个空行
- 每行代码不超过 120 个字符
- 导入顺序：标准库、第三方库、本地模块
- 使用空行分隔函数和类
- 使用空格分隔运算符
- 使用空行分隔逻辑块
- 使用跨平台的方式创建路径

### 1.2 命名规范

#### 1.2.1 后端（Python）命名规范
- 类名：使用大驼峰命名法（PascalCase）
- 函数名：使用下划线命名法（snake_case）
- 变量名：使用下划线命名法（snake_case）
- 常量名：使用全大写下划线命名法（UPPER_SNAKE_CASE）
- 文件名：使用小写下划线命名法（snake_case）

#### 1.2.2 前端（JavaScript/TypeScript）命名规范
- 类名：使用大驼峰命名法（PascalCase）
- 函数名：使用小驼峰命名法（camelCase）
- 变量名：使用小驼峰命名法（camelCase）
- 常量名：使用全大写下划线命名法（UPPER_SNAKE_CASE）
- 文件名：使用小写下划线命名法（snake_case）

### 1.3 注释规范
- 类注释：说明类的用途、作者、创建时间
- 函数注释：说明函数的功能、参数、返回值
- 关键代码注释：说明复杂逻辑的实现思路
- 使用统一的注释格式

### 1.4 代码质量指标
- 代码复杂度：圈复杂度不超过10
- 代码重复率：不超过5%
- 测试覆盖率：>80%
- 代码审查：至少一个审查者批准
- 静态代码分析：通过所有检查
- 代码可维护性：遵循SOLID原则
- 代码可读性：清晰的命名和注释

## 二、项目结构

### 2.1 前端项目结构
```
src/
├── assets/        # 静态资源
├── components/    # 公共组件
├── views/         # 页面组件
├── router/        # 路由配置
├── store/         # Pinia状态管理
├── composables/   # 组合式函数
├── utils/         # 工具函数
├── api/           # 接口定义
└── styles/        # 样式文件
```

### 2.2 后端项目结构
```
app/
├── api/           # API路由
├── core/          # 核心配置
├── models/        # SQLAlchemy模型
├── schemas/       # Pydantic模型
├── services/      # 业务逻辑
├── utils/         # 工具函数
└── middleware/    # 中间件
```

## 三、技术栈规范

### 3.1 前端技术栈
- Vue 3 + JavaScript
- 使用组合式API（Composition API）
- 使用ESLint + Prettier进行代码格式化
- 使用Vite作为构建工具
- 使用Pinia进行状态管理
- 使用Tailwind CSS进行样式开发

### 3.2 Vue 3 开发规范
- 使用组合式API（Composition API）
- 使用ESLint + Prettier进行代码格式化
- 使用Vite作为构建工具
- 使用Pinia进行状态管理

### 3.3 Tailwind CSS规范
- 使用响应式设计
- 遵循移动优先原则
- 使用自定义主题配置
- 保持样式一致性

### 3.4 WebSocket规范
- 使用WebSocket进行实时通信
- 实现心跳检测机制
- 处理断线重连
- 实现消息队列

### 3.5 后端技术栈
- FastAPI + Python 3.9+
- 使用依赖注入系统
- 使用异步处理
- 使用中间件
- 使用异常处理
- 使用日志记录

### 3.6 数据库技术栈
- PostgreSQL
- SQLAlchemy ORM
- Pydantic数据验证
- Redis缓存

### 3.7 数据库设计规范
- 使用Schema多租户
- 使用RDS托管
- 使用连接池
- 遵循数据库设计范式
- 合理使用索引
- 定期维护和优化
- 数据迁移策略
- 备份恢复策略

## 四、开发流程

### 4.1 分支管理
- main：主分支，用于生产环境
- develop：开发分支，用于开发环境
- feature/*：功能分支，用于新功能开发
- hotfix/*：修复分支，用于紧急bug修复
- release/*：发布分支，用于版本发布

### 4.2 提交规范
- feat：新功能
- fix：修复bug
- docs：文档更新
- style：代码格式
- refactor：重构
- test：测试
- chore：构建过程或辅助工具的变动

### 4.3 代码审查
- 提交前自测
- 使用Pull Request进行代码审查
- 至少需要一个审查者批准
- 通过所有自动化测试
- 遵循代码审查清单
- 保持提交信息清晰
- 及时处理审查意见
- 确保代码风格一致
- 检查测试覆盖率
- 验证功能完整性

### 4.4 版本发布
- 遵循语义化版本
- 更新版本号
- 更新CHANGELOG
- 创建发布标签
- 合并到主分支
- 部署到生产环境
- 通知相关团队
- 监控系统状态

## 五、测试规范

### 5.1 单元测试
- 测试文件命名：test_*.py
- 测试类命名：Test*
- 测试方法命名：test_*
- 测试覆盖率要求：>80%
- 使用pytest框架
- 使用mock进行依赖隔离
- 使用fixture管理测试数据
- 使用参数化测试
- 使用断言验证结果
- 使用测试装饰器

### 5.2 接口测试
- 使用FastAPI TestClient
- 测试用例文档
- 自动化测试脚本
- 测试报告生成
- 接口参数验证
- 接口响应验证
- 接口性能测试
- 接口安全测试
- 接口兼容性测试
- 接口异常测试

### 5.3 性能测试
- 使用JMeter
- 性能指标定义
- 压力测试方案
- 性能优化建议
- 并发用户测试
- 响应时间测试
- 吞吐量测试
- 资源使用测试
- 稳定性测试
- 负载测试

### 5.4 安全测试
- 认证测试
- 授权测试
- 数据安全测试
- 接口安全测试
- SQL注入测试
- XSS攻击测试
- CSRF攻击测试
- 文件上传测试
- 敏感信息测试
- 加密算法测试

### 5.5 自动化测试
- 测试环境配置
- 测试数据准备
- 测试用例管理
- 测试执行自动化
- 测试报告生成
- 测试结果分析
- 测试覆盖率统计
- 持续集成测试
- 回归测试
- 性能监控

## 六、安全规范

### 6.1 认证授权
- JWT认证
- OAuth2授权
- 角色权限控制
- 会话管理

### 6.2 数据安全
- 敏感数据加密
- 密码安全存储
- 数据备份
- 访问控制

### 6.3 网络安全
- HTTPS配置
- WAF配置
- DDoS防护
- 防火墙配置

## 七、性能规范

### 7.1 代码性能
- 避免循环中的数据库操作
- 使用缓存
- 优化查询
- 异步处理

### 7.2 系统性能
- 响应时间要求
- 并发处理能力
- 资源使用限制
- 监控告警

### 7.3 代码质量指标
- 代码复杂度：圈复杂度不超过10
- 代码重复率：不超过5%
- 测试覆盖率：>80%
- 代码审查：至少一个审查者批准
- 静态代码分析：通过所有检查
- 代码可维护性：遵循SOLID原则
- 代码可读性：清晰的命名和注释

## 八、日志规范

### 8.1 日志级别
- ERROR：系统错误、业务异常
- WARNING：警告信息
- INFO：重要业务操作
- DEBUG：调试信息

### 8.2 日志格式
- 时间戳
- 日志级别
- 模块名
- 函数名
- 行号
- 消息内容
- 异常堆栈（如果有）

### 8.3 日志内容
- 系统启动/关闭
- 用户登录/登出
- 重要业务操作
- 异常信息
- 性能监控数据

### 8.4 日志存储
- 按日期分割
- 定期归档
- 敏感信息脱敏
- 使用ELK进行日志管理

## 九、异常处理规范

### 9.1 异常分类
- 系统异常：系统级错误
- 业务异常：业务逻辑错误
- 参数异常：输入参数错误
- 权限异常：访问权限错误

### 9.2 异常处理原则
- 明确异常类型
- 提供详细错误信息
- 记录异常日志
- 优雅降级处理
- 避免异常吞没
- 使用自定义异常类
- 实现统一的异常处理中间件
- 异常响应格式统一
- 异常日志记录完整

### 9.3 异常处理流程
1. 捕获异常
2. 记录日志
3. 转换异常类型
4. 返回错误响应
5. 清理资源

### 9.4 错误码规范
- 系统错误：5xx
- 业务错误：4xx
- 成功：2xx
- 每个错误码对应具体说明

## 十、部署与运维规范

### 10.1 Docker规范
- 镜像构建规范
- 容器运行规范
- 网络配置规范
- 数据持久化规范

### 10.2 Nginx规范
- 反向代理配置
- WebSocket配置
- SSL配置
- 负载均衡配置

### 10.3 CI/CD规范
- GitHub Actions配置
- 自动化测试
- 自动化部署
- 环境管理

### 10.4 监控规范
- 使用Prometheus
- 使用Grafana
- 监控指标定义
- 告警规则配置

## 十一、媒体服务规范

### 11.1 文件命名规范

#### 11.1.1 视频ID命名规范
- 格式：`{room_id}_{uuid4后缀}`
- room_id：10或16位随机数
- uuid4后缀：4位uuid
- 示例：`8723901837_f22d`

#### 11.1.2 文件命名规范
- 格式：`{资源类型}_{video_id}_{操作类型}_{时间戳}.{文件后缀}`
- 资源类型：video, cover, thumbnail等
- video_id：遵循11.1.1规范
- 操作类型：upload, transcoded等
- 时间戳：ISO格式无符号，如20250528T153000
- 文件后缀：mp4, jpg, webp等
- 示例：`video_8723901837_f22d4c_upload_20250528T153000.mp4`

#### 11.1.3 存储目录规范
```
/media/video_{video_id}/
├── images/                    # 图片资源目录
│   ├── cover_{video_id}_{操作类型}_{时间戳}.jpg
│   └── thumbnail_{video_id}_{操作类型}_{时间戳}.webp
├── raw/                      # 原始视频目录
│   └── video_{video_id}_{操作类型}_{时间戳}.mp4
├── hls_{清晰度}_{码率}/      # HLS视频目录
│   ├── index_{video_id}_{操作类型}_{时间戳}.m3u8
│   └── ts/                   # TS分片目录
│       └── segment_{序号}_{video_id}_{操作类型}_{时间戳}.ts
├── mp4/                      # MP4视频目录
│   └── video_{video_id}_{操作类型}_{清晰度}_{时间戳}.mp4
└── metadata.json            # 元数据文件
```

### 11.2 元数据管理规范

#### 11.2.1 metadata.json规范
- 必须包含字段：
  - video_id：视频唯一标识
  - room_id：直播间ID
  - title：视频标题
  - created_at：创建时间
  - updated_at：更新时间
  - status：视频状态

#### 11.2.2 关系管理
- 剪辑关系：original_id, clip_start, clip_end
- 分集关系：series_id, episode_index
- 合集关系：collection_id, order
- 播放列表：playlist_id, order
- 多会场关系：main_room_id, sub_room_id

### 11.3 资源访问规范

#### 11.3.1 访问控制
- 所有资源必须通过签名URL或中转服务访问
- 禁止直接暴露存储路径
- 实现防盗链机制
- 支持访问权限控制

#### 11.3.2 URL设计
- 实际存储路径：`https://storage.example.com/media/video_{video_id}/...`
- 用户访问路径：`https://media.example.com/v/{short_id}`
- 支持CDN加速
- 支持防盗链签名

### 11.4 SRS配置规范
- 配置RTMP推流
- 配置HLS播放
- 配置WebRTC
- 配置转码参数

### 11.5 FFmpeg规范
- 视频转码参数
- 视频录制参数
- 视频截图参数
- 性能优化参数

### 11.6 WebRTC规范
- 信令服务器配置
- ICE服务器配置
- 媒体协商参数
- 网络传输参数

## 十二、存储与缓存规范

### 12.1 Redis规范
- 缓存策略
- 数据结构选择
- 过期策略
- 集群配置

### 12.2 对象存储规范
- 存储桶配置
- 访问权限控制
- 生命周期管理
- CDN配置

### 12.3 数据库规范
- 使用PostgreSQL
- 使用Schema多租户
- 使用RDS托管
- 使用连接池

### 12.4 数据库安全规范
- SQL注入防护
  - 使用参数化查询
  - 使用ORM框架
  - 避免直接拼接SQL
  - 使用预编译语句
  - 使用参数绑定
  - 使用输入验证
  - 使用输出转义
  - 使用错误处理
- 数据库访问控制
  - 使用强密码策略
  - 定期更换密码
  - 限制IP访问
  - 使用SSL连接
  - 记录访问日志
- 数据加密
  - 敏感数据加密
  - 传输数据加密
  - 备份数据加密
  - 密钥管理
- 数据备份
  - 定期备份
  - 增量备份
  - 异地备份
  - 备份验证
- 数据恢复
  - 恢复流程
  - 恢复测试
  - 灾难恢复
  - 业务连续性

## 十三、媒体下载服务规范

### 13.1 下载任务状态定义
```python
class TaskStatus:
    PENDING = 'pending'           # 等待下载
    PROCESSING = 'processing'     # 下载中
    COMPLETED = 'completed'       # 完全成功（视频和图片都下载成功）
    PARTIAL_COMPLETED = 'partial_completed'  # 部分成功（视频基本完成但有少量分片失败，或视频成功但图片失败）
    FAILED = 'failed'            # 失败（视频下载失败或失败分片过多）
    CANCELLED = 'cancelled'      # 已取消
```

### 13.2 下载失败处理规范
- 失败类型分类：
  - network_error：网络错误
  - timeout：超时错误
  - invalid_content：内容无效
  - storage_error：存储错误
  - permission_error：权限错误

- 重试策略：
  - 最大重试次数：3次
  - 重试间隔：指数退避（1分钟、2分钟、4分钟）
  - HLS分片失败容忍度：5%
  - 失败记录保留时间：7天

### 13.3 并发控制规范
- 全局并发限制：
  - 最大并发下载任务数：100
  - 单个任务最大并发数：10
  - 任务队列容量：1000

- 资源限制：
  - 内存使用限制：2GB/任务
  - CPU使用限制：50%/任务
  - 磁盘IO限制：100MB/s
  - 网络带宽限制：10MB/s

### 13.4 存储路径规范
```
/media/video_{video_id}/
├── images/                    # 图片资源目录
│   ├── cover_{video_id}_{操作类型}_{时间戳}.jpg
│   └── thumbnail_{video_id}_{操作类型}_{时间戳}.webp
├── raw/                      # 原始视频目录
│   └── video_{video_id}_{操作类型}_{时间戳}.mp4
├── hls_{清晰度}_{码率}/      # HLS视频目录
│   ├── index_{video_id}_{操作类型}_{时间戳}.m3u8
│   └── ts/                   # TS分片目录
│       └── segment_{序号}_{video_id}_{操作类型}_{时间戳}.ts
├── mp4/                      # MP4视频目录
│   └── video_{video_id}_{操作类型}_{清晰度}_{时间戳}.mp4
└── metadata.json            # 元数据文件
```

### 13.5 日志记录规范
- 日志级别：
  - ERROR：下载失败、系统错误
  - WARNING：部分下载失败、重试操作
  - INFO：任务状态变更、下载进度
  - DEBUG：详细下载信息

- 日志内容：
  - 任务ID
  - 视频ID
  - 操作类型
  - 错误信息
  - 重试次数
  - 时间戳
  - 性能指标

### 13.6 监控指标规范
- 任务监控：
  - 任务处理状态
  - 下载速度
  - 失败率
  - 重试次数

- 资源监控：
  - CPU使用率
  - 内存使用率
  - 磁盘使用率
  - 网络带宽使用率

- 告警规则：
  - 任务失败率 > 10%
  - 重试次数 > 3次
  - 资源使用率 > 80%
  - 下载速度 < 1MB/s

### 13.7 安全规范
- 访问控制：
  - API认证
  - 任务权限控制
  - 资源访问控制
  - 操作审计日志

- 数据安全：
  - 下载内容验证
  - 文件完整性校验
  - 敏感信息加密
  - 临时文件清理

- 防护措施：
  - 请求频率限制
  - 并发任务限制
  - 下载大小限制
  - 异常行为监控

### 13.8 错误码规范
| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查参数格式 |
| 401 | 未授权 | 重新登录获取token |
| 403 | 禁止访问 | 检查权限 |
| 404 | 资源不存在 | 检查资源ID |
| 500 | 服务器错误 | 联系管理员 |

## 八、API设计规范

### 8.1 通用规范
- 使用 RESTful API 设计风格
- 使用 JSON 作为数据交换格式
- 使用 HTTP 状态码表示请求结果
- 使用版本号管理 API（如 /api/v1/）
- 使用统一的错误响应格式
- 使用标准的 HTTP 方法（GET、POST、PUT、DELETE）
- 使用查询参数进行过滤和分页
- 使用 URL 参数传递资源标识符

### 8.2 请求规范
- 请求头必须包含 Content-Type: application/json
- 请求体使用 JSON 格式
- 参数命名使用下划线命名法（snake_case）
- 必填参数必须进行验证
- 可选参数提供默认值
- 参数类型必须明确
- 参数范围必须限制
- 参数长度必须限制

### 8.3 响应规范
- 成功响应格式：
```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": "2024-03-20T10:00:00Z"
}
```
- 错误响应格式：
```json
{
    "code": 400,
    "message": "参数错误",
    "details": {
        "field": "video_id",
        "error": "视频ID格式不正确"
    },
    "timestamp": "2024-03-20T10:00:00Z"
}
```
- 分页响应格式：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total": 100,
        "page": 1,
        "size": 10,
        "items": []
    },
    "timestamp": "2024-03-20T10:00:00Z"
}
```

### 8.4 状态码使用规范
- 200：请求成功
- 201：创建成功
- 400：请求参数错误
- 401：未认证
- 403：无权限
- 404：资源不存在
- 500：服务器内部错误

### 8.5 媒体下载服务API接口

#### 8.5.1 任务管理接口
- 创建下载任务
  - `POST /api/v1/download/tasks`
  - 请求参数：
    ```json
    {
      "video_id": "string",
      "liveroom_id": "string",
      "liveroom_title": "string",
      "liveroom_url": "string",
      "video_url": "string",
      "video_type": "string",
      "storage_path": "string"
    }
    ```
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "task_id": "uuid",
        "status": "pending",
        "created_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```
- 查询下载任务
  - `GET /api/v1/download/tasks/{task_id}`
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "task_id": "uuid",
        "video_id": "string",
        "liveroom_id": "string",
        "status": "string",
        "progress": 0.5,
        "failed_segments": [
          {
            "segment_id": "uuid",
            "segment_url": "string",
            "error_message": "string"
          }
        ],
        "created_at": "2024-03-20T10:00:00Z",
        "updated_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```
- 取消下载任务
  - `DELETE /api/v1/download/tasks/{task_id}`
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "task_id": "uuid",
        "status": "cancelled",
        "updated_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```

#### 8.5.2 下载控制接口
- 暂停下载任务
  - `POST /api/v1/download/tasks/{task_id}/pause`
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "task_id": "uuid",
        "status": "paused",
        "updated_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```
- 恢复下载任务
  - `POST /api/v1/download/tasks/{task_id}/resume`
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "task_id": "uuid",
        "status": "processing",
        "updated_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```
- 重试失败任务
  - `POST /api/v1/download/tasks/{task_id}/retry`
  - 请求参数：
    ```json
    {
      "segment_ids": ["uuid"],
      "resource_type": "string"
    }
    ```
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "task_id": "uuid",
        "status": "retrying",
        "updated_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```

#### 8.5.3 失败任务管理接口
- 查询失败记录
  - `GET /api/v1/download/tasks/{task_id}/failures`
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "total": 10,
        "page": 1,
        "size": 10,
        "items": [
          {
            "failure_id": "uuid",
            "segment_id": "uuid",
            "failure_type": "string",
            "error_message": "string",
            "retry_count": 0,
            "next_retry_time": "2024-03-20T10:00:00Z",
            "created_at": "2024-03-20T10:00:00Z"
          }
        ]
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```
- 重试失败任务
  - `POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/retry`
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "failure_id": "uuid",
        "status": "retrying",
        "next_retry_time": "2024-03-20T10:00:00Z",
        "updated_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```
- 放弃失败任务
  - `POST /api/v1/download/tasks/{task_id}/failures/{failure_id}/abandon`
  - 响应示例：
    ```json
    {
      "code": 200,
      "message": "success",
      "data": {
        "failure_id": "uuid",
        "status": "abandoned",
        "updated_at": "2024-03-20T10:00:00Z"
      },
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```

### 8.6 错误处理规范
- 使用统一的异常处理中间件
- 记录详细的错误日志
- 返回友好的错误信息
- 区分客户端错误和服务器错误
- 提供错误追踪信息
- 实现错误重试机制
- 支持错误通知
- 错误信息国际化 