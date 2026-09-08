# TopicCreate 页面代码生成提示词（一次性创建并发布，Element Plus 版）

## 角色与目标

你是一名资深前端重构工程师，精通 Element Plus 与 Vue 3 Composition API，严格遵循本项目现有的 API 封装与状态管理方式（Pinia）。

你的任务：实现“创建专题”页面（TopicCreate.vue），用户在一次流程中完成：上传图片、本地填写专题标题与描述、创建分类并在分类下选择直播间，最后点击“创建并发布”，一次性与后端交互并跳转展示页。

- 目标 1：单按钮一次性提交（不提供草稿/中间提交）。
- 目标 2：横幅图先本地预览，提交时上传并用后端返回 URL 回填。
- 目标 3：与现有请求封装、鉴权、URL 规范化保持一致。

## 页面功能范围说明（一次性提交）

- 专题基础信息录入：标题、描述、横幅图（先本地预览）。
- 分类与直播间：提交前即可创建分类并在分类下选择直播间；支持移除与简单排序（提交时一并落库）。
- 提交：仅提供“创建并发布专题”按钮，点击后统一与后端交互。
- 导航：成功后跳转 `/pages/topic/TopicDisplay?topic_id={id}`。
- 横幅图上传策略：提交前仅预览；提交时创建专题拿到 `topic_id` 后上传，使用返回 `banner_url` 覆盖。
- 校验：标题必填（1~100），描述可选（<=500），至少一个分类且至少一类含有直播间。

## 设计与预览（空态与实时变更）

- Banner 画布：固定 450×200，`object-fit: cover`，容器宽度 450px，页面居中；下方所有内容与 Banner 同宽。
- 分类标签（Tabs）实时映射：
  - 新建分类初始显示为“分类一/分类二/分类三…”。
  - 当用户编辑分类名为“云南省”等时，Tabs 标签立即从“分类一”变为“云南省”（双向绑定，失焦或输入节流更新均可）。
- 分类内容区域（预览清单）：
  - 当分类未选择直播间时显示空占位列表（灰底占位缩略图 + 提示文案）。
  - 当选择了直播间后，列表立即切换为“直播间卡片样式”。
  - 直播间卡片样式必须与`src/pages/venue/VenueDisplayPage.vue`中的卡片一致（缩略图、标题、副信息、状态角标），小尺寸密集版：
    - 缩略图 140×84，`object-fit: cover`，圆角 6px；
    - 右侧信息区显示标题（单行/两行溢出省略）、副信息一行（如“开始时间 · 热度”）；
    - 左上角状态 Tag（success/info/warning/primary），文案与`VenueDisplayPage.vue`一致（“直播中/未开始/已结束/回放中”）。

## API 需求说明（顺序与一次性提交匹配）

与后端文档保持一致（示例摘录自《专题功能完整设计文档-修正版.md》）：

- 一次性提交时的调用顺序：
  1) 创建专题（直接发布）
     - `POST /api/v1/topics`
     - Request: `{ "title": "...", "description": "...", "banner_url": "", "status": "published" }`
  2) 上传横幅图（可选）
     - `POST /api/v1/topics/{topic_id}/banner` FormData: `file`，用返回的 `banner_url` 覆盖
     - 请求体：`multipart/form-data`，字段名为 `file`
     - 文件校验：仅支持 PNG、JPG 格式，大小不超过 10MB
     - 权限验证：只能为自己创建的专题上传横幅
     - 成功响应：返回 `banner_url` 字段（相对路径）
  3) 批量创建分类（循环调用）
     - `POST /api/v1/topics/{topic_id}/categories`  Body: `{ name, sort_order }`
  4) 为每个分类批量关联直播间
     - `POST /api/v1/topic-categories/{category_id}/rooms` Body: `{ rooms: [{ room_id, sort_order }] }`
- 获取专题聚合详情（用于创建后跳转验证）
  - `GET /api/v1/topics/{topic_id}`  响应 data 为聚合详情对象（`id/title/description/banner_url/status/categories/...`）。
- 上传横幅图已包含在顺序 2。
- 辅助接口：`GET /api/v1/rooms/{room_id}/topics`、`POST /api/v1/rooms/batch-status`。

鉴权：统一使用 JWT，前端请求工具 `utils/request.ts` 已自动注入 `Authorization: Bearer <token>`。

## 核心原则

1. **组件统一**：所有 UI 使用 Element Plus；表单、弹窗、提示用 EP 组件。
2. **数据契约**：仅提交后端允许的字段（避免 categories 等扩展字段导致 500）。
3. **横幅图策略**："本地预览 + 提交时上传替换 URL"的策略与 Live/Room 模块一致。
4. **代码风格**：复用项目通用请求封装 `get/post/patch/del`、Pinia `useTopicStore()`，与 `RoomCreate.vue`/`LiveView.vue` 的风格保持一致。
5. **API规范**：严格遵循后端API规范，使用正确的HTTP方法（PATCH而非PUT），避免405错误。
6. **错误处理**：所有API调用都要有完善的错误处理，用户能看到具体的错误信息，不能静默失败。
7. **兜底体验**：提交失败/网络失败要有清晰反馈；按钮 loading、防重复提交。

---

## 任务一：创建 TopicCreate 页面（单按钮一次性提交）

文件路径：`/src/pages/topic/TopicCreate.vue`

### 1. 页面布局（<template>）

- 使用 `el-container` + `el-card` 组织页面；
- 顶部按钮区（放在 `el-page-header` 的 `#extra`）仅包含“创建并发布专题”；
- 表单区 `el-form`：
  - 标题（必填，`el-input`，展示字数统计）；
  - 描述（可选，`el-input type="textarea"`，行数 4，最大 500）；
  - 横幅图（自定义上传框）：
    - 若 `bannerPreviewUrl` 存在先显示预览；否则显示占位；
    - 仅选择文件，不立即上传，提交时统一上传；
  - 无状态选择控件；状态在提交时固定为 `published`。
- 分类页签区（未提交前的本地操作能力）：
  - Tabs 标签名绑定 `category.name || '分类' + (index+1)`，用户输入后标签即时更新；
  - 提供“新增分类”按钮；每个 Tab 内提供“重命名/删除分类”操作；删除需二次确认；
  - 每个分类 Tab 内：
    - 当无直播间时显示空态占位；
    - 当有直播间时渲染“VenueDisplayPage.vue 风格”的卡片列表（小尺寸密集版）；
    - 提供“选择直播间”按钮打开弹窗：支持多选添加；
    - 提供“移除”操作从当前分类中删除某个直播间（仅本地修改，提交时再落库）；
    - 可选：简单排序（上移/下移/拖拽或输入 sort_order）。

### 2. 逻辑与样式（<script setup> + <style scoped>）

逻辑要点：
- 状态管理：`useTopicStore()`；
- 本地状态：`formData`、`bannerPreviewUrl`、`categories`（含本地 rooms 列表）、`saving`；
- 分类与直播间（未提交前均为本地编辑能力）：
  - 分类：新增、重命名、删除、（可选）排序；Tabs 名称实时更新。
  - 直播间：在分类下批量添加、删除、去重，同一分类不允许重复 room_id；维护本地 `sort_order`。
- 一次性提交方法 `handleCreateAndPublish()`：
  1) 表单校验（标题/分类/直播间）。
  2) `POST /topics` 创建专题（`status='published'`）。
  3) 若选择横幅：`POST /topics/{id}/banner` 上传并回填 URL：
     - 使用 `uni.uploadFile` 上传到 `POST /api/v1/topics/{topic_id}/banner`
     - 请求体：`multipart/form-data`，字段名为 `file`
     - 文件校验：PNG、JPG 格式，大小 ≤ 10MB
     - 成功响应：使用返回的 `banner_url` 更新表单数据
     - 错误处理：文件格式错误、大小超限、上传失败等场景的友好提示
  4) 依次 `POST /topics/{id}/categories` 创建分类，记录 `category_id`。
  5) 依次 `POST /topic-categories/{cid}/rooms` 批量关联直播间（含 `sort_order`）。
  6) 成功后跳转展示页。
- 字段清洗：仅提交非空字段；`title` 去首尾空格；
- 成功/失败：EP `ElMessage` 确认；按钮 loading 防抖；
- URL 规范化：展示时 `getBannerSrc(url)`：若相对路径以 `/media` 开头，则以 `BASE_API_URL` 推导 origin 拼接；

### 3. 组件与依赖

必用 EP 组件：`ElContainer`、`ElMain`、`ElPageHeader`、`ElCard`、`ElForm`、`ElFormItem`、`ElInput`、`ElUpload`、`ElButton`、`ElMessage`、`ElText`、`ElSpace`、`ElTabs/ElTabPane`、`ElDialog`、`ElTable`、`ElTableColumn`、`ElPagination`、`ElPopconfirm`、`ElTag`、`ElImage`、`ElDivider`。

---

## 任务二：数据与交互细节

1) 表单数据模型（对齐前端类型 `src/types/topic.ts`）
```ts
interface TopicCreateForm {
  title: string
  description?: string
  banner_url?: string
  status: 'published'
}
```

2) 分类数据模型
```ts
interface CategoryForm {
  id?: string
  name: string
  sort_order?: number
  rooms?: Array<{ id: string; title: string; cover_url?: string; live_status: string; start_time?: string; heat: number; sort_order?: number }>
}
```

3) 校验规则
- 标题：必填 1~100；描述：<= 500；横幅：文件 < 10MB（与后端一致）；
- 分类：名称必填 1~50；排序为整数 >=0；
- 关联：至少一个分类且至少一个分类含有直播间；批量添加时去重同一分类下的 `room_id`。

### 4) 一次性提交流程（重要）
1) 前端收集：标题/描述/横幅预览/分类与直播间。
2) 点击“创建并发布”：按“API 需求说明”的顺序调用；任一步失败提示并保留本地状态，允许重试。

5) 失败与回退
- 创建或任意子步骤失败：toast + 保留表单/本地分类与直播间选择；
- 横幅上传失败：toast + 保留预览，提示可稍后在管理页重试上传；
- 文件校验失败：提示文件格式或大小不符合要求（PNG、JPG 格式，≤10MB）；
- 权限验证失败：提示无权限上传横幅，跳转到专题列表页。

6) 安全与鉴权
- 请求头自动注入 JWT；必要时在 401 触发强制重登；
- 控制台打印必要调试信息（接口 URL、headers 片段、入参出参片段）。

---

## 任务三：路由与接入

- 新增/确认路由：`/pages/topic/TopicCreate`；
- 入口：
  - 从专题列表页/管理页“新建专题”按钮进入；
  - 从 LiveView/Room 列表场景的引导按钮进入（可选）。
- 退出/返回：使用 `uni.navigateBack()`。

---

## 关键实现要点 Checklist

- [ ] **表单结构与校验**：标题/描述/横幅；分类与直播间的本地校验。
- [ ] **Tabs 标签名与分类名称双向绑定**：实时更新；支持新增/重命名/删除分类。
- [ ] **空态与实态切换**：无直播间显示占位；选择后渲染卡片；支持在未提交前增加/删除直播间并去重。
- [ ] **本地横幅预览**：提交时上传并回填：
  - 文件校验：PNG、JPG 格式，大小 ≤ 10MB
  - 上传逻辑：使用 `uni.uploadFile` 上传到 `POST /api/v1/topics/{topic_id}/banner`
  - 响应处理：使用返回的 `banner_url` 更新表单数据
  - 错误处理：文件格式错误、大小超限、上传失败等场景的友好提示
- [ ] **一次性创建并发布**：创建专题 -> 上传横幅 -> 创建分类 -> 关联直播间 -> 跳转。
- [ ] **列表卡片视觉**：与 `VenueDisplayPage.vue` 保持一致（小尺寸密集版）。
- [ ] **错误处理**：提示并保留本地状态，支持重试。
- [ ] **数据契约**：与 `TopicDisplay.vue` 的数据契约一致：详情接口 data 为聚合对象。
- [ ] **API调用规范**：统一使用 `topicStore` 或 `topicApi`；严格按契约提交。
- [ ] **HTTP方法规范**：确保使用正确的HTTP方法（PATCH而非PUT），避免405错误。
- [ ] **错误处理规范**：所有API调用都要有try-catch包装，用户能看到具体错误信息。
- [ ] **状态管理**：确保loading状态正确设置和清除，操作失败时保持数据一致性。

---

## 任务四：编辑功能扩展（从 TopicList 跳转编辑）

### 1. 编辑模式识别与数据预填充

**路由参数处理**：
- 支持 `topic_id` 参数：`/pages/topic/TopicCreate?topic_id=xxx`
- 页面加载时检测 `topic_id` 参数，如果存在则进入编辑模式
- 编辑模式下页面标题显示"编辑专题"，按钮文字改为"保存并发布"

**数据预填充流程**：
1. 页面加载时调用 `GET /api/v1/topics/{topic_id}` 获取专题详情
2. 解析响应数据，填充表单字段：
   - `formData.title` = 专题标题
   - `formData.description` = 专题描述  
   - `formData.banner_url` = 横幅图URL（用于显示现有图片）
   - `formData.status` = 专题状态
3. 调用 `GET /api/v1/topics/{topic_id}/categories` 获取分类列表
4. 为每个分类调用 `GET /api/v1/topic-categories/{category_id}/rooms` 获取关联的直播间
5. 构建本地 `formData.categories` 数据结构，包含分类名称和关联的直播间列表

**编辑模式状态管理**：
```ts
// 编辑模式标识
const isEditMode = ref(false)
const editingTopicId = ref('')

// 页面加载逻辑
onLoad((options) => {
  if (options.topic_id) {
    isEditMode.value = true
    editingTopicId.value = options.topic_id
    loadTopicForEdit(options.topic_id)
  } else {
    // 创建模式逻辑
  }
})
```

### 2. 编辑模式下的数据加载方法

**加载专题详情**：
```ts
const loadTopicForEdit = async (topicId: string) => {
  try {
    // 1. 加载专题基本信息
    const topicDetail = await topicStore.fetchTopicDetail(topicId)
    
    // 填充表单数据
    formData.title = topicDetail.title
    formData.description = topicDetail.description || ''
    formData.banner_url = topicDetail.banner_url || ''
    formData.status = topicDetail.status
    
    // 2. 加载分类列表
    await topicStore.fetchCategories(topicId)
    
    // 3. 为每个分类加载关联的直播间
    const categoriesWithRooms = []
    for (const category of topicStore.categories) {
      const rooms = await topicStore.fetchCategoryRooms(category.id)
      categoriesWithRooms.push({
        id: category.id,
        name: category.name,
        sort_order: category.sort_order,
        rooms: rooms
      })
    }
    
    // 更新本地分类数据
    formData.categories = categoriesWithRooms
    
    // 4. 建立分类ID映射
    categoriesWithRooms.forEach((cat, index) => {
      categoryIds[index] = cat.id
    })
    
  } catch (error: any) {
    console.error('加载专题详情失败:', error)
    ElMessage.error(error.message || '加载专题详情失败')
  }
}
```

### 3. 编辑模式下的提交逻辑

**更新专题信息**：
```ts
const handleUpdateAndPublish = async () => {
  try {
    await validateForm()
    validateBeforePublish()
    
    saving.value = true
    
    // 1. 更新专题基本信息
    await topicStore.updateTopic(editingTopicId.value, {
      title: formData.title,
      description: formData.description,
      banner_url: formData.banner_url,
      status: formData.status
    })
    
    // 2. 处理横幅图上传（如果用户选择了新图片）
    if (selectedBannerTempPath.value) {
      try {
        await uploadBannerToServer(editingTopicId.value, selectedBannerTempPath.value)
        ElMessage.success('横幅图已更新')
        bannerPreviewUrl.value = ''
        selectedBannerTempPath.value = ''
      } catch (e: any) {
        console.error('横幅图上传失败:', e)
        ElMessage.warning(e?.message || '横幅图上传失败，可稍后重试')
      }
    }
    
    // 3. 处理分类更新
    await syncCategoriesForEdit()
    
    ElMessage.success('专题更新成功')
    uni.navigateTo({
      url: `/pages/topic/TopicDisplay?topic_id=${editingTopicId.value}`
    })
    
  } catch (error: any) {
    console.error('更新专题失败:', error)
    ElMessage.error(error.message || '更新专题失败')
  } finally {
    saving.value = false
  }
}
```

**分类同步逻辑**：
```ts
const syncCategoriesForEdit = async () => {
  const topicId = editingTopicId.value
  
  // 获取当前后端分类列表
  const currentCategories = await topicStore.fetchCategories(topicId)
  const currentCategoryIds = currentCategories.map(cat => cat.id)
  
  // 处理分类更新
  for (let i = 0; i < formData.categories.length; i++) {
    const localCategory = formData.categories[i]
    const categoryId = categoryIds[i]
    
    if (categoryId) {
      // 更新现有分类
      await topicStore.updateCategory(categoryId, {
        name: localCategory.name,
        sort_order: i
      })
      
      // 更新分类下的直播间关联
      await syncCategoryRooms(categoryId, localCategory.rooms)
    } else {
      // 创建新分类
      const created = await topicStore.createCategory(topicId, {
        name: localCategory.name,
        sort_order: i
      })
      categoryIds[i] = created.id
      
      // 关联直播间
      if (localCategory.rooms.length > 0) {
        const associations = localCategory.rooms.map((room, idx) => ({
          room_id: room.id,
          sort_order: room.sort_order || idx + 1
        }))
        await topicStore.addRoomsToCategory(created.id, associations)
      }
    }
  }
  
  // 删除不再需要的分类
  const localCategoryIds = Object.values(categoryIds).filter(Boolean)
  for (const categoryId of currentCategoryIds) {
    if (!localCategoryIds.includes(categoryId)) {
      await topicStore.deleteCategory(categoryId)
    }
  }
}

const syncCategoryRooms = async (categoryId: string, rooms: RoomInCategory[]) => {
  // 获取当前分类的直播间
  const currentRooms = await topicStore.fetchCategoryRooms(categoryId)
  const currentRoomIds = currentRooms.map(room => room.id)
  
  // 要添加的直播间
  const newRoomIds = rooms.map(room => room.id)
  const toAdd = newRoomIds.filter(id => !currentRoomIds.includes(id))
  const toRemove = currentRoomIds.filter(id => !newRoomIds.includes(id))
  
  // 添加新直播间
  if (toAdd.length > 0) {
    const associations = toAdd.map((roomId, idx) => ({
      room_id: roomId,
      sort_order: rooms.find(r => r.id === roomId)?.sort_order || idx + 1
    }))
    await topicStore.addRoomsToCategory(categoryId, associations)
  }
  
  // 移除不需要的直播间
  if (toRemove.length > 0) {
    await topicStore.removeRoomsFromCategory(categoryId, toRemove)
  }
}
```

### 4. TopicList 页面的编辑按钮跳转

**修改 TopicList.vue 的编辑按钮**：
```ts
const handleAction = async (action: string, topic: Topic) => {
  try {
    switch (action) {
      case 'edit':
        // 跳转到编辑页面
        uni.navigateTo({
          url: `/pages/topic/TopicCreate?topic_id=${topic.id}`
        })
        break
      case 'delete':
        // 删除逻辑保持不变
        await ElMessageBox.confirm(
          '确定要删除这个专题吗？此操作不可恢复！',
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await topicStore.deleteTopic(topic.id)
        ElMessage.success('删除成功')
        await loadTopics()
        break
      default:
        ElMessage.info(`${action}功能待开发，敬请期待`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error(error.message || '操作失败')
    }
  }
}
```

### 5. 编辑模式下的UI调整

**页面标题和按钮文字**：
```vue
<template>
  <el-container class="topic-create-container">
    <!-- 页面头部 -->
    <el-page-header @back="goBack" :title="isEditMode ? '编辑专题' : '创建专题'">
      <template #extra>
        <el-button 
          type="primary" 
          @click="isEditMode ? handleUpdateAndPublish : handleCreateAndPublish" 
          :loading="saving"
        >
          {{ isEditMode ? '保存并发布' : '创建并发布专题' }}
        </el-button>
      </template>
    </el-page-header>
    <!-- 其余内容保持不变 -->
  </el-container>
</template>
```

**横幅图显示逻辑**：
```vue
<div class="banner-uploader" @click="selectBannerAndPreview">
  <!-- 优先显示新选择的图片预览 -->
  <img v-if="bannerPreviewUrl" :src="bannerPreviewUrl" class="banner-preview" />
  <!-- 其次显示现有的横幅图 -->
  <img v-else-if="formData.banner_url" :src="getCoverSrc(formData.banner_url)" class="banner-preview" />
  <!-- 最后显示占位符 -->
  <div v-else class="upload-placeholder">
    <el-icon class="upload-icon"><Plus /></el-icon>
    <div class="upload-text">点击选择图片进行本地预览</div>
    <div class="upload-hint">{{ isEditMode ? '选择新图片将替换现有横幅' : '创建成功后上传，最终以后端返回URL展示' }}</div>
  </div>
</div>
```

### 6. 编辑模式的关键实现要点

- [ ] **路由参数处理**：支持 `topic_id` 参数，识别编辑模式
- [ ] **数据预填充**：调用专题详情接口，填充表单和分类数据
- [ ] **分类ID映射**：建立本地分类索引与后端分类ID的映射关系
- [ ] **更新接口调用**：使用 `PATCH /api/v1/topics/{topic_id}` 和 `PATCH /api/v1/topic-categories/{category_id}` 接口（注意：后端要求PATCH方法，前端API需使用patch而非put）
- [ ] **分类同步逻辑**：处理分类的新增、更新、删除和直播间关联的变更
- [ ] **横幅图处理**：支持替换现有横幅图，保持上传逻辑一致性
- [ ] **UI状态调整**：编辑模式下调整页面标题和按钮文字
- [ ] **错误处理**：编辑失败时保留用户输入，支持重试
- [ ] **权限验证**：确保只有专题创建者可以编辑
- [ ] **数据一致性**：编辑完成后跳转到专题展示页验证结果

### 7. API 接口需求（编辑模式）

**获取专题详情**：
- `GET /api/v1/topics/{topic_id}` - 获取专题基本信息
- `GET /api/v1/topics/{topic_id}/categories` - 获取专题分类列表
- `GET /api/v1/topic-categories/{category_id}/rooms` - 获取分类下的直播间

**更新专题信息**：
- `PATCH /api/v1/topics/{topic_id}` - 更新专题基本信息（前端API需使用patch方法）
- `PATCH /api/v1/topic-categories/{category_id}` - 更新分类信息（前端API需使用patch方法）
- `POST /api/v1/topics/{topic_id}/banner` - 上传新横幅图（可选）
- `POST /api/v1/topic-categories/{category_id}/rooms` - 添加直播间到分类
- `DELETE /api/v1/topic-categories/{category_id}/rooms` - 从分类移除直播间
- `DELETE /api/v1/topic-categories/{category_id}` - 删除分类

**权限验证**：
- 所有编辑操作都需要 JWT 认证
- 后端验证用户是否为专题创建者
- 403 错误时提示权限不足并跳转到专题列表页

---

## 任务五：错误处理与API规范修正

### 1. HTTP方法规范修正

**问题**：后端API要求使用PATCH方法，但前端使用了PUT方法导致405错误

**解决方案**：
- 专题更新：`PATCH /api/v1/topics/{topic_id}` （前端API需使用patch方法）
- 分类更新：`PATCH /api/v1/topic-categories/{category_id}` （前端API需使用patch方法）

**前端API调用规范**：
```ts
// 错误的调用方式（会导致405错误）
updateTopic: (topicId: string, data: TopicUpdate): Promise<ApiResponse<Topic>> =>
  put(`/topics/${topicId}`, data, { auth: true }),

updateCategory: (categoryId: string, data: CategoryUpdate): Promise<ApiResponse<TopicCategory>> =>
  put(`/topic-categories/${categoryId}`, data, { auth: true }),

// 正确的调用方式
updateTopic: (topicId: string, data: TopicUpdate): Promise<ApiResponse<Topic>> =>
  patch(`/topics/${topicId}`, data, { auth: true }),

updateCategory: (categoryId: string, data: CategoryUpdate): Promise<ApiResponse<TopicCategory>> =>
  patch(`/topic-categories/${categoryId}`, data, { auth: true }),
```

### 2. 错误处理规范化

**问题**：更新失败时用户看不到错误提示，错误被捕获但没有正确显示

**解决方案**：
```ts
const handleUpdateAndPublish = async () => {
  try {
    await validateForm()
    validateBeforePublish()
    
    saving.value = true
    
    // 1. 更新专题基本信息
    try {
      await topicStore.updateTopic(editingTopicId.value, {
        title: formData.title,
        description: formData.description,
        banner_url: formData.banner_url,
        status: formData.status
      })
    } catch (error: any) {
      console.error('更新专题基本信息失败:', error)
      ElMessage.error(`更新专题失败: ${error.message || '未知错误'}`)
      return // 提前返回，不继续执行后续步骤
    }
    
    // 2. 处理横幅图上传（如果用户选择了新图片）
    if (selectedBannerTempPath.value) {
      try {
        await uploadBannerToServer(editingTopicId.value, selectedBannerTempPath.value)
        ElMessage.success('横幅图已更新')
        bannerPreviewUrl.value = ''
        selectedBannerTempPath.value = ''
      } catch (e: any) {
        console.error('横幅图上传失败:', e)
        ElMessage.warning(`横幅图上传失败: ${e?.message || '未知错误'}，可稍后重试`)
        // 横幅图上传失败不阻止整个更新流程
      }
    }
    
    // 3. 处理分类更新
    try {
      await syncCategoriesForEdit()
    } catch (error: any) {
      console.error('分类同步失败:', error)
      ElMessage.error(`分类更新失败: ${error.message || '未知错误'}`)
      return // 提前返回，不继续执行后续步骤
    }
    
    ElMessage.success('专题更新成功')
    uni.navigateTo({
      url: `/pages/topic/TopicDisplay?topic_id=${editingTopicId.value}`
    })
    
  } catch (error: any) {
    console.error('更新专题失败:', error)
    ElMessage.error(`更新专题失败: ${error.message || '未知错误'}`)
  } finally {
    saving.value = false
  }
}
```

### 3. 分类同步错误处理

**问题**：分类同步逻辑中任何一步失败都会导致整个更新失败，但错误信息不够明确

**解决方案**：
```ts
const syncCategoriesForEdit = async () => {
  const topicId = editingTopicId.value
  
  try {
    // 获取当前后端分类列表
    const currentCategories = await topicStore.fetchCategories(topicId)
    const currentCategoryIds = currentCategories.map(cat => cat.id)
    
    // 处理分类更新
    for (let i = 0; i < formData.categories.length; i++) {
      const localCategory = formData.categories[i]
      const categoryId = categoryIds[i]
      
      if (categoryId) {
        // 更新现有分类
        try {
          await topicStore.updateCategory(categoryId, {
            name: localCategory.name,
            sort_order: i
          })
        } catch (error: any) {
          console.error(`更新分类 ${localCategory.name} 失败:`, error)
          throw new Error(`更新分类"${localCategory.name}"失败: ${error.message || '未知错误'}`)
        }
        
        // 更新分类下的直播间关联
        try {
          await syncCategoryRooms(categoryId, localCategory.rooms)
        } catch (error: any) {
          console.error(`同步分类"${localCategory.name}"的直播间失败:`, error)
          throw new Error(`同步分类"${localCategory.name}"的直播间失败: ${error.message || '未知错误'}`)
        }
      } else {
        // 创建新分类
        try {
          const created = await topicStore.createCategory(topicId, {
            name: localCategory.name,
            sort_order: i
          })
          categoryIds[i] = created.id
        } catch (error: any) {
          console.error(`创建分类"${localCategory.name}"失败:`, error)
          throw new Error(`创建分类"${localCategory.name}"失败: ${error.message || '未知错误'}`)
        }
        
        // 关联直播间
        if (localCategory.rooms.length > 0) {
          try {
            const associations = localCategory.rooms.map((room, idx) => ({
              room_id: room.id,
              sort_order: room.sort_order || idx + 1
            }))
            await topicStore.addRoomsToCategory(created.id, associations)
          } catch (error: any) {
            console.error(`为分类"${localCategory.name}"添加直播间失败:`, error)
            throw new Error(`为分类"${localCategory.name}"添加直播间失败: ${error.message || '未知错误'}`)
          }
        }
      }
    }
    
    // 删除不再需要的分类
    const localCategoryIds = Object.values(categoryIds).filter(Boolean)
    for (const categoryId of currentCategoryIds) {
      if (!localCategoryIds.includes(categoryId)) {
        try {
          await topicStore.deleteCategory(categoryId)
        } catch (error: any) {
          console.error(`删除分类失败:`, error)
          // 删除分类失败不阻止整个流程，但记录错误
          ElMessage.warning(`删除分类失败: ${error.message || '未知错误'}`)
        }
      }
    }
  } catch (error: any) {
    console.error('分类同步失败:', error)
    throw error // 重新抛出错误，让上层处理
  }
}
```

### 4. 直播间同步错误处理

**问题**：直播间添加和移除操作失败时错误信息不够明确

**解决方案**：
```ts
const syncCategoryRooms = async (categoryId: string, rooms: RoomInCategory[]) => {
  try {
    // 获取当前分类的直播间
    const currentRooms = await topicStore.fetchCategoryRooms(categoryId)
    const currentRoomIds = currentRooms.map(room => room.id)
    
    // 要添加的直播间
    const newRoomIds = rooms.map(room => room.id)
    const toAdd = newRoomIds.filter(id => !currentRoomIds.includes(id))
    const toRemove = currentRoomIds.filter(id => !newRoomIds.includes(id))
    
    // 添加新直播间
    if (toAdd.length > 0) {
      try {
        const associations = toAdd.map((roomId, idx) => ({
          room_id: roomId,
          sort_order: rooms.find(r => r.id === roomId)?.sort_order || idx + 1
        }))
        await topicStore.addRoomsToCategory(categoryId, associations)
      } catch (error: any) {
        console.error(`添加直播间失败:`, error)
        throw new Error(`添加直播间失败: ${error.message || '未知错误'}`)
      }
    }
    
    // 移除不需要的直播间
    if (toRemove.length > 0) {
      try {
        await topicStore.removeRoomsFromCategory(categoryId, toRemove)
      } catch (error: any) {
        console.error(`移除直播间失败:`, error)
        throw new Error(`移除直播间失败: ${error.message || '未知错误'}`)
      }
    }
  } catch (error: any) {
    console.error('直播间同步失败:', error)
    throw error // 重新抛出错误，让上层处理
  }
}
```

### 5. API调用规范检查清单

- [ ] **HTTP方法检查**：确保使用正确的HTTP方法（PATCH而非PUT）
- [ ] **错误处理**：每个API调用都要有try-catch包装
- [ ] **用户反馈**：所有错误都要显示给用户，不能静默失败
- [ ] **错误信息**：错误信息要具体明确，包含操作名称和错误原因
- [ ] **流程控制**：关键步骤失败时要提前返回，避免继续执行
- [ ] **日志记录**：所有错误都要记录到控制台，便于调试
- [ ] **状态管理**：确保loading状态正确设置和清除
- [ ] **数据一致性**：操作失败时要保持数据状态一致