# 专家模块API路径对比分析

## 📊 API路径对比

### 当前生成的代码API URL（提示词文档）

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 创建专家 | POST | `/api/v1/experts/{expert_id}` | 专家模块命名空间 |
| 更新专家 | PATCH | `/api/v1/experts/{expert_id}` | 专家模块命名空间 |
| 删除专家 | DELETE | `/api/v1/experts/{expert_id}` | 专家模块命名空间 |
| 获取专家详情 | GET | `/api/v1/experts/{expert_id}` | 专家模块命名空间 |
| 获取专家列表 | GET | `/api/v1/experts` | 专家模块命名空间 |
| 获取推荐专家列表 | GET | `/api/v1/experts/featured` | 专家模块命名空间 |
| 设置专家推荐 | POST | `/api/v1/experts/{expert_id}/set-featured` | 专家模块命名空间 |
| 取消专家推荐 | DELETE | `/api/v1/experts/{expert_id}/set-featured` | 专家模块命名空间 |
| 关注专家 | POST | `/api/v1/experts/{expert_id}/follow` | 专家模块命名空间 |
| 取消关注专家 | DELETE | `/api/v1/experts/{expert_id}/follow` | 专家模块命名空间 |
| 检查是否已关注 | GET | `/api/v1/experts/{expert_id}/is-followed` | 专家模块命名空间 |
| 获取关注的专家列表 | GET | `/api/v1/experts/followed` | ⚠️ 专家模块命名空间 |
| 批量获取关注专家的直播状态 | POST | `/api/v1/experts/followed/live-status` | 专家模块命名空间 |

---

### 设计文档API URL

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取推荐专家列表 | GET | `/api/v1/featured-experts` | 顶层资源 |
| 获取专家详情及关联内容 | GET | `/api/v1/experts/{expert_id}/sessions` | 专家→场次，层次清晰 |
| 创建专家（Admin） | POST | `/api/v1/admin/experts` | 管理员命名空间 |
| 获取专家列表（Admin） | GET | `/api/v1/admin/experts` | 管理员命名空间 |
| 关注专家 | POST | `/api/v1/users/me/followed-experts` | 用户中心设计 |
| 取消关注专家 | DELETE | `/api/v1/users/me/followed-experts/{expert_id}` | 用户中心设计 |
| 获取关注的专家列表 | GET | `/api/v1/users/me/followed-experts` | ✅ 用户中心设计 |

---

## 🎯 差异分析

### 1. 管理员操作

| 操作 | 提示词文档路径 | 设计文档路径 | 差异 |
|-----|-------------|-----------|------|
| 创建专家 | `/api/v1/experts` | `/api/v1/admin/experts` | ⚠️ 命名空间不同 |
| 获取专家列表 | `/api/v1/experts` | `/api/v1/admin/experts` | ⚠️ 命名空间不同 |

**差异说明**：
- 提示词文档：使用专家模块命名空间（`/experts/`）
- 设计文档：使用管理员命名空间（`/admin/`）

---

### 2. 用户关注操作

| 操作 | 提示词文档路径 | 设计文档路径 | 差异 |
|-----|-------------|-----------|------|
| 关注专家 | `/api/v1/experts/{expert_id}/follow` | `/api/v1/users/me/followed-experts` | ⚠️ 路径设计不同 |
| 取消关注专家 | `/api/v1/experts/{expert_id}/follow` | `/api/v1/users/me/followed-experts/{expert_id}` | ⚠️ 路径设计不同 |
| 获取关注的专家列表 | `/api/v1/experts/followed` | `/api/v1/users/me/followed-experts` | ⚠️ 路径设计不同 |

**差异说明**：
- 提示词文档：使用专家模块命名空间（`/experts/`）
- 设计文档：使用用户中心命名空间（`/users/me/`）

---

### 3. 推荐专家

| 操作 | 提示词文档路径 | 设计文档路径 | 差异 |
|-----|-------------|-----------|------|
| 获取推荐专家列表 | `/api/v1/experts/featured` | `/api/v1/featured-experts` | ⚠️ 层次不同 |
| 设置专家推荐 | `/api/v1/experts/{expert_id}/set-featured` | 未在设计文档中 | ⚠️ 设计文档未定义 |
| 取消专家推荐 | `/api/v1/experts/{expert_id}/set-featured` | 未在设计文档中 | ⚠️ 设计文档未定义 |

**差异说明**：
- 提示词文档：`/experts/featured`（专家→推荐）
- 设计文档：`/featured-experts`（顶层资源）

---

## 🔍 RESTful符合度对比

### 提示词文档路径

| 接口 | 路径 | RESTful符合度 | 分析 |
|-----|------|--------------|------|
| 获取推荐的专家列表 | `/api/v1/experts/featured` | ⚠️ 70% | 层次结构不够清晰 |
| 获取关注的专家列表 | `/api/v1/experts/followed` | ⚠️ 70% | `followed` 是形容词，不是标准名词资源 |
| 关注专家 | `/api/v1/experts/{expert_id}/follow` | ⚠️ 80% | `follow` 是动词，不是标准名词资源 |
| 取消关注专家 | `/api/v1/experts/{expert_id}/follow` | ⚠️ 80% | `follow` 是动词，不是标准名词资源 |

**总体符合度**：⚠️ **约75%符合**

---

### 设计文档路径

| 接口 | 路径 | RESTful符合度 | 分析 |
|-----|------|--------------|------|
| 获取推荐的专家列表 | `/api/v1/featured-experts` | ✅ 100% | 资源导向，名词 |
| 获取关注的专家列表 | `/api/v1/users/me/followed-experts` | ✅ 95% | 资源导向，层次清晰 |
| 关注专家 | `/api/v1/users/me/followed-experts` | ✅ 95% | 资源导向，层次清晰 |
| 取消关注专家 | `/api/v1/users/me/followed-experts/{expert_id}` | ✅ 100% | 资源导向，层次清晰 |

**总体符合度**：✅ **约97%符合**

---

## 🎯 对前端开发的影响分析

### 场景：前后端分离开发

**假设**：
- 前端开发人员只有设计文档
- 后端已经实现了API（使用提示词文档的路径）
- 前端开发人员根据设计文档调用API

**影响分析**：

| 场景 | 前端调用 | 后端实现 | 结果 | 影响 |
|-----|---------|---------|------|------|
| 获取关注的专家列表 | `GET /api/v1/users/me/followed-experts` | `GET /api/v1/experts/followed` | ❌ 404 Not Found | **严重影响** |
| 关注专家 | `POST /api/v1/users/me/followed-experts` | `POST /api/v1/experts/{expert_id}/follow` | ❌ 404 Not Found | **严重影响** |
| 取消关注专家 | `DELETE /api/v1/users/me/followed-experts/{expert_id}` | `DELETE /api/v1/experts/{expert_id}/follow` | ❌ 404 Not Found | **严重影响** |

**结论**：**严重影响前端开发**

---

### 影响程度

| 影响方面 | 严重程度 | 说明 |
|---------|---------|------|
| **接口调用失败** | 🔴 **严重** | 前端调用API时返回404 Not Found |
| **沟通成本增加** | 🔴 **严重** | 前后端开发人员需要沟通确认正确的API路径 |
| **开发效率降低** | 🔴 **严重** | 前端开发人员需要不断调整API调用代码 |
| **测试成本增加** | 🟠 **中等** | 需要为不同的API路径编写测试用例 |
| **文档维护成本增加** | 🟠 **中等** | 需要维护设计文档和实际API文档的一致性 |

**总体影响**：🔴 **严重影响前端开发**

---

## 🎯 修改建议

### 方案1：修改API路径（推荐）

**修改内容**：将所有API路径改为符合设计文档的路径

**优点**：
- ✅ 与设计文档一致，前端开发可以直接按照设计文档调用API
- ✅ 更符合RESTful规范
- ✅ 更清晰的层次结构和语义化

**缺点**：
- ❌ 需要修改大量代码（13个端点）
- ❌ 可能影响其他模块（如果有其他模块依赖这些API）
- ❌ 需要更新API文档

**修改范围**：
1. 修改用户关注相关API（3个端点）
2. 修改管理员相关API（2个端点）
3. 修改推荐专家API（1个端点）
4. 更新路由注册（`api/v1/api.py`）

---

### 方案2：更新设计文档（不推荐）

**修改内容**：将设计文档中的API路径改为符合当前代码的路径

**优点**：
- ✅ 不需要修改代码
- ✅ 修改成本较低

**缺点**：
- ❌ 不符合RESTful规范
- ❌ 语义不够清晰
- ❌ 层次结构不够明确
- ❌ 需要重新发布设计文档

---

### 方案3：提供API路径映射文档（临时方案）

**修改内容**：提供一个API路径映射文档，说明设计文档路径与实际路径的对应关系

**优点**：
- ✅ 修改成本最低
- ✅ 前端开发人员可以快速找到对应的实际路径

**缺点**：
- ❌ 前后端开发人员需要额外查阅映射文档
- ❌ 增加维护成本
- ❌ 只能作为临时方案

---

## 🎯 最终建议

### 推荐：方案1（修改API路径）

**理由**：
1. ✅ 与设计文档一致，前端开发可以直接按照设计文档调用API
2. ✅ 更符合RESTful规范
3. ✅ 更清晰的层次结构和语义化
4. ✅ 长远来看，有利于项目维护和扩展

**修改建议**：
1. 优先修改用户关注相关API（对前端开发影响最大）
2. 其次修改管理员相关API
3. 最后修改推荐专家API

**修改原则**：
- 最小幅度修改
- 确保不引入冲突
- 保持代码的一致性

