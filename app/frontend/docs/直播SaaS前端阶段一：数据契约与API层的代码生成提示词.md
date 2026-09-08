# 直播SaaS前端阶段一：数据契约与API层的代码生成提示词 (V2 - 动态逻辑增强版)

---

## 1. 角色定义（Role Definition）
你是一名资深前端工程师，精通uni-app、Vue3、TypeScript和多端适配，具备大型SaaS/直播平台前端架构与实现经验。你的任务是根据详细设计文档和上下文，编写**高质量、功能完整、可直接运行**的前端代码，而不仅仅是静态的结构骨架。

---

## 2. 任务目标（Task Objective）
本次任务为直播SaaS平台前端项目的**阶段一：数据契约与API层**。目标是**实现**所有与后端通信相关的模块，包括TypeScript类型定义、功能完备的API接口函数封装，以及一个带有**实际请求和错误处理逻辑**的统一网络请求工具。

**为确保任务明确、无歧义，本次需具体生成以下文件：**

-   `src/types/room.ts`: **定义** `Room` 接口。
-   `src/types/session.ts`: **定义** `Session` 和 `Statistics` 接口。
-   `src/utils/request.ts`: **实现**一个基于`uni.request`的、包含拦截器和错误处理的统一请求封装。
-   `src/api/room.ts`: **实现**所有与“房间”相关的API请求函数，并**处理**响应数据。
-   `src/api/session.ts`: **实现**所有与“场次”相关的API请求函数，并**处理**响应数据。

---

## 3. 核心上下文信息（Core Context Information）
-   **唯一事实来源**: 《直播SaaS平台前端设计文档.md》是本次任务所有代码生成工作的唯一且最高的设计依据。
-   **TypeScript类型定义**: 必须严格依据设计文档**第6.2节“核心表结构”**进行转换。
-   **API函数**: 必须严格依据设计文档**第8.1节“页面与接口映射总览表”**。

---

## 4. 全局强制性约束与最高准则 (Global Mandatory Constraints & Ultimate Principle)
-   **功能完整性**: 生成的代码必须是功能完整的。例如，`request`工具必须能实际发送请求并处理响应，而不是只有一个空的框架。
-   **零偏差原则**: 严格遵循设计文档，不允许任何形式的“优化”或“变通”。
-   **命名与结构**: 严格遵循《直播SaaS平台前端设计文档.md》**第 3.2 节**中的命名规范。
-   **依赖导入**: 所有模块必须正确地从其他模块导入所需的类型或函数。

---

## 5. 分步生成与交叉验证流程 (Step-by-Step Generation & Cross-Validation Flow)

### 步骤1：TypeScript类型定义生成 (`src/types/`)
-   **目标**: **定义**核心数据实体的TypeScript接口。
-   **要求**: 接口定义必须与设计文档第6.2节的数据库表结构完全匹配。
-   **验证点**:
    -   [ ] `Room`, `Session`, `Statistics` 接口的字段名和类型是否与设计文档的表结构完全一致？

### 步骤2：统一网络请求工具生成 (`src/utils/request.ts`)
-   **目标**: **实现**一个全项目复用的、经过封装的`uni.request`函数。
-   **要求 (强指令)**:
    1.  **实现**请求拦截器逻辑，用于自动**注入**一个静态的认证Token到请求头中。
    2.  **实现**响应拦截器逻辑，**检查**HTTP状态码。如果状态码在`200-299`之间，则**解析**并**返回**`res.data`。
    3.  **实现**统一的错误处理。如果HTTP状态码表示失败，或请求本身（如网络问题）失败，必须：
        a. 在控制台**打印**详细的错误信息。
        b. 使用`uni.showToast`向用户**展示**一个通用的错误提示，如“网络请求失败”。
        c. **`reject`** Promise，以便上层调用者可以捕获异常。
-   **验证点**:
    -   [ ] 是否导出一个名为 `request` 的函数？
    -   [ ] 函数是否**真实地**调用了`uni.request`？
    -   [ ] 是否有**具体的**Token注入和响应错误处理逻辑？

### 步骤3：API层函数生成 (`src/api/`)
-   **目标**: **实现**对所有后端端点的调用封装。
-   **要求 (强指令)**:
    1.  所有API函数必须**导入并调用**步骤2中创建的 `request` 工具函数。
    2.  所有函数的参数和返回数据，必须使用步骤1中定义的TypeScript接口进行**强类型约束**。
    3.  函数命名应清晰地反映其操作，如 `getRoomList`, `createSession`。
    4.  对于分页接口（如`getRoomList`），**定义**并**使用**一个包含`items`, `total`, `page`, `size`字段的泛型`PaginatedResponse<T>`。
-   **验证点**:
    -   [ ] 设计文档第8.1节中的每一个API端点是否都有对应的函数**实现**？
    -   [ ] 函数签名（参数和返回值）是否都使用了正确的TypeScript类型进行标注？
    -   [ ] 函数内部是否**正确调用**了 `utils/request` 并传递了正确的`url`, `method`, `data`？

---

## 6. 模块生成指令 (Module Generation Instructions)

*此部分保持不变，因为具体的代码实现细节已在上面的强指令中详细定义。AI在执行生成时，会遵循这些指令来填充具体的逻辑。*

### 6.1 `src/types/room.ts`
- **目标**: 定义 `Room` 接口。
- **约束**: 严格依据设计文档 `6.2.1 live_rooms（直播房间表）`。
```typescript
// 严格依据设计文档 6.2.1 live_rooms（直播房间表）
export interface Room {
  id: string; // UUID
  user_id: string | null; // UUID
  parent_room_id: string | null; // UUID
  title: string;
  description: string | null;
  cover_url: string | null;
  stream_key: string;
  is_private: boolean;
  record_by_default: boolean;
  category_id: string | null; // UUID
  created_at: string; // TIMESTAMPTZ
  updated_at: string; // TIMESTAMPTZ
}
```

### 6.2 `src/types/session.ts`
- **目标**: 定义 `Session` 和 `Statistics` 接口。
- **约束**: 严格依据设计文档 `6.2.2 live_sessions` 和 `6.2.3 session_statistics`。
```typescript
// 严格依据设计文档 6.2.3 session_statistics（场次统计表）
export interface Statistics {
  id: string; // UUID
  session_id: string; // UUID
  peak_viewer_count: number; // INT
  total_viewer_count: number; // BIGINT
  total_like_count: number; // BIGINT
  total_share_count: number; // BIGINT
  created_at: string; // TIMESTAMPTZ
  updated_at: string; // TIMESTAMPTZ
}

// 严格依据设计文档 6.2.2 live_sessions（直播场次表）
export type SessionStatus = 'scheduled' | 'live' | 'ended' | 'archived';

export interface Session {
  id: string; // UUID
  room_id: string; // UUID
  status: SessionStatus;
  start_time: string; // TIMESTAMPTZ
  end_time: string | null; // TIMESTAMPTZ
  video_id: string | null; // UUID
  created_at: string; // TIMESTAMPTZ
  updated_at: string; // TIMESTAMPTZ
  statistics?: Statistics; // 关联的统计数据，可选
}
```

### 6.3 `src/utils/request.ts`
- **目标**: 创建统一请求封装。
- **约束**: 包含请求/响应拦截逻辑的框架，并正确处理泛型。
```typescript
// src/utils/request.ts

const BASE_URL = 'https://your-api-base-url.com/api/v1'; // 替换为真实的API地址

// 这是一个示例Token，后续会从状态管理中获取
const getAuthToken = () => 'your-static-test-token';

interface RequestOptions {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  data?: any;
  header?: any;
}

export const request = <T = any>(options: RequestOptions): Promise<T> => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
        ...options.header,
      },
      success: (res: any) => {
        // 响应拦截器
        if (res.statusCode >= 200 && res.statusCode < 300) {
          // 后端返回的数据通常在 res.data 中
          resolve(res.data as T);
        } else {
          // 处理HTTP错误
          console.error(`HTTP Error: ${res.statusCode}`, res);
          uni.showToast({
            title: `请求错误: ${res.statusCode}`,
            icon: 'none',
          });
          reject(res);
        }
      },
      fail: (err) => {
        // 网络或其他请求失败
        console.error('Request Failed', err);
        uni.showToast({
          title: '网络请求失败',
          icon: 'none',
        });
        reject(err);
      },
    });
  });
};
```

### 6.4 `src/api/room.ts`
- **目标**: 封装所有与“房间”相关的API。
- **约束**: 严格依据设计文档 8.1.1 节。导入 `Room` 类型和 `request` 函数。
```typescript
// src/api/room.ts
import { request } from '../utils/request';
import type { Room } from '../types/room';

// 定义分页响应体
interface PaginatedRooms {
  items: Room[];
  total: number;
  page: number;
  size: number;
}

// 获取房间列表 (GET /rooms)
export const getRoomList = (params: { page?: number; size?: number }) => {
  return request<PaginatedRooms>({
    url: '/rooms',
    method: 'GET',
    data: params,
  });
};

// 获取单个房间详情 (GET /rooms/{room_id})
export const getRoomDetail = (roomId: string) => {
  return request<Room>({
    url: `/rooms/${roomId}`,
    method: 'GET',
  });
};

// 创建房间 (POST /rooms)
// body 的类型可以更具体，这里用 Partial<Room> 作为示例
export const createRoom = (data: Partial<Room>) => {
  return request<Room>({
    url: '/rooms',
    method: 'POST',
    data,
  });
};

// 更新房间 (PATCH /rooms/{room_id})
export const updateRoom = (roomId: string, data: Partial<Room>) => {
  return request<Room>({
    url: `/rooms/${roomId}`,
    method: 'PATCH',
    data,
  });
};

// 删除房间 (DELETE /rooms/{room_id})
export const deleteRoom = (roomId: string) => {
  return request<any>({ // 根据后端返回值确定类型
    url: `/rooms/${roomId}`,
    method: 'DELETE',
  });
};

// 获取主会场下所有分会场 (GET /rooms/{room_id}/sub-venues)
export const getSubVenues = (roomId: string) => {
  return request<Room[]>({
    url: `/rooms/${roomId}/sub-venues`,
    method: 'GET',
  });
};
```

### 6.5 `src/api/session.ts`
- **目标**: 封装所有与“场次”相关的API。
- **约束**: 严格依据设计文档 8.1.2 节。导入 `Session` 类型和 `request` 函数。
```typescript
// src/api/session.ts
import { request } from '../utils/request';
import type { Session } from '../types/session';

// 定义分页响应体
interface PaginatedSessions {
  items: Session[];
  total: number;
  page: number;
  size: number;
}

// 获取房间下所有场次 (GET /rooms/{room_id}/sessions)
export const getSessionList = (roomId: string, params: { page?: number, size?: number }) => {
  return request<PaginatedSessions>({
    url: `/rooms/${roomId}/sessions`,
    method: 'GET',
    data: params,
  });
};

// 获取单个场次详情 (GET /sessions/{session_id})
export const getSessionDetail = (sessionId: string) => {
  return request<Session>({
    url: `/sessions/${sessionId}`,
    method: 'GET',
  });
};

// 创建场次 (POST /rooms/{room_id}/sessions)
export const createSession = (roomId: string, data: Partial<Session>) => {
  return request<Session>({
    url: `/rooms/${roomId}/sessions`,
    method: 'POST',
    data,
  });
};

// 更新场次 (PATCH /sessions/{session_id})
export const updateSession = (sessionId: string, data: Partial<Session>) => {
  return request<Session>({
    url: `/sessions/${sessionId}`,
    method: 'PATCH',
    data,
  });
};

// 删除场次 (DELETE /sessions/{session_id})
export const deleteSession = (sessionId: string) => {
  return request<any>({ // 根据后端返回值确定类型
    url: `/sessions/${sessionId}`,
    method: 'DELETE',
  });
};
```

---

## 7. 最终交付与质量保证协议 (Final Delivery & Quality Assurance Protocol)
- **输出格式**:
  - 每个文件一个完整、可直接运行的代码块，并标注清晰的文件路径。
  - 你必须为每个需要生成的文件，单独输出一个完整、可直接运行的代码块。
  - 每个代码块前必须用Markdown语法标注清晰的文件路径，例如：`// frontend_live/src/types/room.ts`。
  - 禁止在代码之外添加任何解释、道歉或不必要的寒暄。你的回答**只能是代码**和**文件路径标注**。
- **自我修正**: 在每一步生成后，你必须在内部进行自查。如果发现与设计文档或本提示词有任何偏差，必须**立即撤销并重新生成**。
- **最终一致性断言**: 在完成所有文件生成后，你必须在回答的末尾输出以下文本：
  ```
  [FINAL ASSERTION]
  All generated code has been cross-validated against the design documents and backend specifications.
  - Feature Completeness: 100%
  - API Consistency: 100%
  - Data Model Consistency: 100%
  - Code Standard Compliance: 100%
  - Zero Deviation Principle: Adhered
  ``` 