# 📱 App 端配置完成说明

> 配置完成时间：2025-11-19  
> 配置阶段：Phase 1 - 基础配置

---

## ✅ 已完成的配置项

### 1. **manifest.json - App 核心配置** ✅

**文件路径**：`src/manifest.json`

**新增内容**：
```json
"app-plus": {
  // 已添加完整的 App 配置节
}
```

**关键配置项说明**：

| 配置项 | 当前值 | 说明 | 何时修改 |
|--------|--------|------|----------|
| **appid** | `__UNI__XXXXXXX` | DCloud 应用ID（占位符） | 和老师商量后申请，替换为真实ID |
| **packagename** | `com.livesaas.app` | Android 包名 | 如需修改可随时改，不影响开发 |
| **bundle** | `com.livesaas.app` | iOS Bundle ID | 同上 |
| **versionName** | `1.0.0` | 版本名称（展示给用户） | 发布新版本时递增 |
| **versionCode** | `100` | 版本号（数字） | 发布新版本时递增 |

**已启用的模块**：

| 模块名 | 用途 | 代码位置 |
|--------|------|---------|
| **VideoPlayer** | 视频播放 | `LiveView.vue` - 直播观看 |
| **Gallery** | 相册选择 | `RoomCreate.vue` - `uni.chooseImage()` |
| **Camera** | 相机 | 未来推流功能 |
| **LivePusher** | 推流 | 未来推流功能（预留） |

**已配置的权限**（Android）：

- ✅ 相机权限（CAMERA）
- ✅ 相册权限（READ_EXTERNAL_STORAGE）
- ✅ 存储权限（WRITE_EXTERNAL_STORAGE）
- ✅ 网络权限（INTERNET）
- ✅ 网络状态（ACCESS_NETWORK_STATE）
- ✅ WiFi状态（ACCESS_WIFI_STATE）
- ✅ 录音权限（RECORD_AUDIO）
- ✅ 音频设置（MODIFY_AUDIO_SETTINGS）
- ✅ 保持唤醒（WAKE_LOCK）

**已配置的隐私说明**（iOS）：

- ✅ NSPhotoLibraryUsageDescription - 相册访问说明
- ✅ NSCameraUsageDescription - 相机使用说明
- ✅ NSMicrophoneUsageDescription - 麦克风使用说明

---

### 2. **package.json - 编译脚本** ✅

**文件路径**：`package.json`

**新增脚本**：

```json
{
  "scripts": {
    "dev:app-android": "uni -p app-android",     // Android 开发模式
    "dev:app-ios": "uni -p app-ios",             // iOS 开发模式
    "build:app-android": "uni build -p app-android", // Android 构建
    "build:app-ios": "uni build -p app-ios"          // iOS 构建
  }
}
```

**使用方法**：
```bash
# 命令行编译 Android（需先配置好环境）
npm run dev:app-android

# HBuilderX 中更常用（推荐）
# 运行 → 运行到手机或模拟器
```

---

### 3. **static 目录 - 应用资源** ✅

**目录路径**：`src/static/`

**当前状态**：
- ✅ 目录已创建
- ⚠️ **需要你手动操作**：复制应用图标

**请执行以下操作**：

```bash
# 方法1：命令行（在项目根目录）
copy public\logo.png src\static\logo.png

# 方法2：文件管理器
# 1. 打开 public 文件夹
# 2. 找到 logo.png（绿色 "U" 图标）
# 3. 复制到 src\static\logo.png
```

**图标规格**：
- 尺寸：1024x1024（当前 logo.png 可能需要调整）
- 格式：PNG
- 用途：App 安装到手机后桌面显示的图标

---

### 4. **.env.app - App 端环境变量** ✅

**文件路径**：`.env.app`

**关键配置**：

```env
# App 端统一使用 HTTPS（安全要求）
VITE_BASE_API_URL=https://124.220.235.226/api/core/
VITE_AUTH_API_URL=https://124.220.235.226/api/users/

# 应用信息
VITE_APP_TITLE=直播SaaS平台
VITE_APP_VERSION=1.0.0
```

**与现有配置的关系**：

| 环境 | 配置文件 | API 协议 | 用途 |
|------|---------|---------|------|
| **H5 开发** | `.env.development` | HTTP | 快速调试 |
| **H5 生产** | `vite.config.ts` | HTTPS | 生产部署 |
| **App 端** | `.env.app` | HTTPS | Android/iOS |
| **小程序** | `.env.mp` | HTTPS | 微信小程序 |

**对现有 H5 开发的影响**：❌ **完全无影响**
- H5 继续使用 `.env.development`
- 可以继续用 HTTP 快速调试
- App 独立使用 `.env.app`

---

### 5. **网络安全配置 - Android** ✅

**文件路径**：`src/hybrid/html/network_security_config.xml`

**作用**：
- 控制 Android App 的网络请求安全策略
- 配置 HTTP/HTTPS 访问规则
- 满足 Android 9+ 的安全要求

**当前配置**：
- ✅ 默认禁止 HTTP 明文流量（安全）
- ✅ 信任系统和用户证书
- ✅ 支持调试抓包（开发环境）

**如果需要临时使用 HTTP**：
取消注释配置文件中的域名白名单部分即可

---

## 📋 配置检查清单

### ✅ 已完成项

- [x] manifest.json 添加 app-plus 配置节
- [x] 配置 4 个必需模块（VideoPlayer, Gallery, Camera, LivePusher）
- [x] 配置 Android 11 项权限
- [x] 配置 iOS 4 项隐私说明
- [x] 设置包名：com.livesaas.app
- [x] package.json 添加 App 编译脚本
- [x] 创建 src/static 目录
- [x] 创建 .env.app 环境变量
- [x] 创建 Android 网络安全配置

### ⏸️ 待完成项（需要你操作）

- [ ] **复制应用图标** - `copy public\logo.png src\static\logo.png`
- [ ] 申请 DCloud AppID（和老师商量后）
- [ ] 替换 manifest.json 中的 AppID
- [ ] 在 HBuilderX 中打开项目
- [ ] 制作自定义调试基座（真机测试前）

### 🔄 未来需要配置（后期优化）

- [ ] Android 签名证书（打包正式版时）
- [ ] iOS 开发者证书（如有 Mac 电脑）
- [ ] 优化应用图标和启动页
- [ ] 配置第三方 SDK（推送、统计等）
- [ ] 推流功能代码实现

---

## 🚀 下一步操作指南

### 立即操作（5分钟）

**1. 复制应用图标**
```bash
copy public\logo.png src\static\logo.png
```

**2. 验证配置**
```bash
# 检查 manifest.json
cat src/manifest.json | grep "app-plus"

# 检查编译脚本
npm run | grep "app"
```

### 准备真机测试时（和老师商量后）

**3. 申请 AppID**
- 访问：https://dev.dcloud.net.cn/
- 创建应用，获取 AppID
- 替换 `src/manifest.json` 中的 `__UNI__XXXXXXX`

**4. 使用 HBuilderX**
- 文件 → 导入 → 从本地目录导入
- 运行 → 运行到手机或模拟器 → Android
- 首次运行选择 "制作自定义调试基座"

---

## ⚠️ 重要注意事项

### 1. AppID 占位符
- ✅ 现在使用 `__UNI__XXXXXXX` 不影响开发
- ✅ H5 和小程序开发完全不受影响
- ⚠️ 真机调试和云打包时必须替换为真实 AppID

### 2. 包名可以随时修改
- ✅ `com.livesaas.app` 是临时包名
- ✅ 和老师商量后可以改成其他名称（如 `com.university.livesaas`）
- ✅ 修改包名不影响代码，只需改 manifest.json

### 3. API 协议分离
- ✅ H5 开发继续用 HTTP（快速）
- ✅ App 使用 HTTPS（安全）
- ✅ 互不影响

### 4. iOS 开发限制
- ⚠️ iOS 开发必须有 Mac 电脑
- ⚠️ 需要 Apple 开发者账号（$99/年）
- ✅ 现在配置已预留 iOS 配置，代码通用

---

## 🐛 常见问题

### Q1: 为什么需要自定义调试基座？
**A**: 因为你使用了原生功能（相机、视频、相册），标准基座不包含这些模块。

### Q2: 修改代码后需要重新制作基座吗？
**A**: 
- ❌ 修改 Vue/JS/CSS 代码 → 不需要
- ✅ 修改 manifest.json → 需要
- ✅ 添加/删除模块 → 需要

### Q3: 如何测试 App 功能？
**A**: 三种方式
1. HBuilderX 真机调试（推荐，需要自定义基座）
2. 云打包测试版 APK（需要 AppID）
3. Android 模拟器（性能较差）

### Q4: Element Plus 在 App 上能用吗？
**A**: 
- ⚠️ Element Plus 主要为 H5 设计
- ⚠️ App 端部分组件样式可能不一致
- ✅ 功能可用，但建议后续用 uni-ui 替换

### Q5: 推流功能如何实现？
**A**: 
- ✅ 模块已配置（LivePusher）
- ✅ 权限已配置（相机、麦克风）
- ⏸️ 代码需要后续实现
- 📚 参考：uni-app 官方文档 `<live-pusher>` 组件

---

## 📞 技术支持

### 配置文件位置速查

```
项目根目录/
├── src/
│   ├── manifest.json           ← App 核心配置 ⭐
│   ├── static/
│   │   └── logo.png           ← 应用图标（需复制）
│   └── hybrid/
│       └── html/
│           └── network_security_config.xml  ← 网络安全
├── .env.app                    ← App 环境变量
├── .env.development            ← H5 开发环境
├── package.json                ← 编译脚本
└── docs/
    └── APP端配置完成说明.md    ← 本文档
```

### 相关文档

- 📘 uni-app 官方文档：https://uniapp.dcloud.net.cn/
- 📘 manifest.json 配置：https://uniapp.dcloud.net.cn/collocation/manifest.html
- 📘 DCloud 开发者中心：https://dev.dcloud.net.cn/

---

**配置完成！** 🎉

现在你的项目已经具备 App 端开发的基础配置，可以继续进行 H5 和小程序开发，等条件成熟后随时可以开始 App 端真机测试。
