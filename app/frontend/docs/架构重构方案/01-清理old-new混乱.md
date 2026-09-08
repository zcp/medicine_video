# 步骤1：清理 old/new 混乱状态

## 📊 当前状态分析

### pages.json 路由配置
当前 `pages.json` 中引用的都是 **new/** 目录下的页面：
- `pages/room/new/RoomList`
- `pages/room/new/RoomCreate`
- `pages/room/new/RoomManage`
- `pages/room/new/RoomBasicSettings`
- `pages/room/new/MultiVenueManage`
- `pages/live/new/LiveView`

### 废弃的旧版本文件
以下文件**未被引用**，属于废弃代码：
- `pages/room/RoomList.vue` (41KB) - ❌ 旧版本
- `pages/room/RoomDetail.vue` (49KB) - ✅ 仍在使用（不在new目录）
- `pages/live/LiveView.vue` (18KB) - ❌ 旧版本

---

## 🎯 清理方案

### 方案A：归档旧代码（推荐）

**目的**：保留历史代码作为参考，但不影响项目结构

```bash
# 1. 创建归档目录
mkdir -p @archive/pages/room
mkdir -p @archive/pages/live

# 2. 移动旧版本到归档目录
mv src/pages/room/RoomList.vue @archive/pages/room/RoomList.vue.old
mv src/pages/live/LiveView.vue @archive/pages/live/LiveView.vue.old

# 3. 添加说明文件
echo "# 归档说明\n\n这些文件是旧版本，已被 new/ 目录下的新版本替代。\n保留仅供参考，不要在项目中引用。" > @archive/README.md
```

### 方案B：直接删除（更彻底）

**目的**：完全清理废弃代码

```bash
# 直接删除旧版本文件
rm src/pages/room/RoomList.vue
rm src/pages/live/LiveView.vue
```

---

## 🚀 执行步骤

### 第1步：备份当前代码（安全第一）

```bash
# 在执行任何操作前，先提交现有代码
git add .
git commit -m "chore: 架构重构前的备份"
```

### 第2步：移动 new/ 目录内容到父目录

```bash
# Room相关页面
mv src/pages/room/new/RoomList.vue src/pages/room/RoomList.new.vue
mv src/pages/room/new/RoomCreate.vue src/pages/room/RoomCreate.vue
mv src/pages/room/new/RoomManage.vue src/pages/room/RoomManage.vue
mv src/pages/room/new/RoomBasicSettings.vue src/pages/room/RoomBasicSettings.vue
mv src/pages/room/new/MultiVenueManage.vue src/pages/room/MultiVenueManage.vue

# Live相关页面
mv src/pages/live/new/LiveView.vue src/pages/live/LiveView.new.vue
```

### 第3步：删除空的 new/ 目录

```bash
rmdir src/pages/room/new
rmdir src/pages/live/new
```

### 第4步：处理旧版本文件

**选项A：归档（推荐）**
```bash
mkdir -p @archive/pages/room
mkdir -p @archive/pages/live

mv src/pages/room/RoomList.vue @archive/pages/room/RoomList.vue.old
mv src/pages/live/LiveView.vue @archive/pages/live/LiveView.vue.old
```

**选项B：直接删除**
```bash
rm src/pages/room/RoomList.vue
rm src/pages/live/LiveView.vue
```

### 第5步：重命名新版本为正式版本

```bash
mv src/pages/room/RoomList.new.vue src/pages/room/RoomList.vue
mv src/pages/live/LiveView.new.vue src/pages/live/LiveView.vue
```

### 第6步：更新 pages.json 路由配置

修改 `src/pages.json`，将所有 `pages/*/new/*` 路径改为 `pages/*/*`：

```json
{
  "pages": [
    // ... 其他页面
    {
      "path": "pages/room/RoomList",  // ✅ 改：去掉 new/
      "style": {
        "navigationBarTitleText": "",
        "navigationStyle": "custom",
        "enablePullDownRefresh": true
      }
    },
    {
      "path": "pages/room/RoomCreate",  // ✅ 改
      "style": {
        "navigationBarTitleText": "",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/room/RoomManage",  // ✅ 改
      "style": {
        "navigationBarTitleText": "房间管理",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/room/RoomBasicSettings",  // ✅ 改
      "style": {
        "navigationBarTitleText": "基本设置",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/room/MultiVenueManage",  // ✅ 改
      "style": {
        "navigationBarTitleText": "多会场管理",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/room/RoomDetail",  // ✅ 保持不变
      "style": {
        "navigationBarTitleText": "房间详情"
      }
    },
    {
      "path": "pages/live/LiveView",  // ✅ 改
      "style": {
        "navigationBarTitleText": "正在直播",
        "navigationStyle": "custom"
      }
    }
    // ... 其他页面
  ]
}
```

---

## ✅ 验证清单

清理完成后，检查以下项目：

- [ ] `src/pages/room/new/` 目录已删除
- [ ] `src/pages/live/new/` 目录已删除
- [ ] `pages.json` 中没有 `pages/*/new/*` 路径
- [ ] 所有页面文件都在正确的位置（无 `.new` 后缀）
- [ ] 旧版本文件已归档到 `@archive/` 或已删除
- [ ] 运行 `npm run dev:h5` 无错误
- [ ] 页面路由跳转正常

---

## 📝 注意事项

1. **检查代码引用**：如果其他文件中有直接 import 路径，需要同步更新
   ```typescript
   // ❌ 旧的导入路径
   import RoomList from '@/pages/room/new/RoomList.vue'
   
   // ✅ 新的导入路径
   import RoomList from '@/pages/room/RoomList.vue'
   ```

2. **Git 提交规范**：
   ```bash
   git add .
   git commit -m "refactor: 清理 pages/ 目录的 old/new 混乱状态
   
   - 移除废弃的旧版本文件
   - 将 new/ 目录内容移到父目录
   - 更新 pages.json 路由配置"
   ```

---

## 🎯 预期结果

清理后的目录结构：

```
src/pages/
├── room/
│   ├── RoomList.vue          ✅ 统一版本
│   ├── RoomCreate.vue        ✅ 统一版本
│   ├── RoomManage.vue        ✅ 统一版本
│   ├── RoomBasicSettings.vue ✅ 统一版本
│   ├── MultiVenueManage.vue  ✅ 统一版本
│   └── RoomDetail.vue        ✅ 保持不变
├── live/
│   └── LiveView.vue          ✅ 统一版本
├── topic/
├── venue/
├── auth/
├── common/
└── index/

@archive/                      📦 归档目录（可选）
└── pages/
    ├── room/
    │   └── RoomList.vue.old
    └── live/
        └── LiveView.vue.old
```

---

## ⏱️ 预计时间

- **方案选择与备份**：10分钟
- **执行文件移动和清理**：20分钟
- **更新 pages.json**：10分钟
- **验证和测试**：20分钟

**总计：约1小时**
