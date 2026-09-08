# 🚀 App 配置快速指引卡片

> 打印或保存此卡片，便于快速查阅

---

## ✅ 已完成配置总览

| 配置项 | 状态 | 文件路径 |
|--------|------|---------|
| manifest.json | ✅ 完成 | `src/manifest.json` |
| 编译脚本 | ✅ 完成 | `package.json` |
| 环境变量 | ✅ 完成 | `.env.app` |
| 网络安全 | ✅ 完成 | `src/hybrid/html/network_security_config.xml` |
| static 目录 | ✅ 创建 | `src/static/` |
| 应用图标 | ⏸️ 待复制 | `src/static/logo.png` |

---

## 📝 立即操作（2分钟）

### 复制应用图标（必需）

```bash
# 在项目根目录执行
copy public\logo.png src\static\logo.png
```

或手动复制：`public/logo.png` → `src/static/logo.png`

---

## 🔑 关键信息速查

### AppID（占位符）
```
当前：__UNI__XXXXXXX
说明：暂不影响开发，真机测试前需替换
```

### 包名
```
Android: com.livesaas.app
iOS:     com.livesaas.app
说明：可随时修改，和老师商量后确定
```

### API 地址
```
H5 开发：http://124.220.235.226:8000/api/v1  (HTTP - 快速调试)
App 端： https://124.220.235.226/api/core/   (HTTPS - 安全要求)
说明：互不影响，H5 继续用 HTTP
```

---

## 📱 启用的功能模块

| 模块 | 用途 | 状态 |
|------|------|------|
| VideoPlayer | 视频播放 | ✅ 已配置 |
| Gallery | 相册选择 | ✅ 已配置 |
| Camera | 相机 | ✅ 已配置 |
| LivePusher | 推流 | ✅ 已配置（预留） |

---

## 🎯 下一步计划

### Phase 1（当前）- 继续开发
- ✅ 配置已完成
- ✅ 可以继续 H5 和小程序开发
- ⏸️ App 端等真机测试时再启动

### Phase 2（和老师商量后）- 真机测试
1. 申请 DCloud AppID
2. 替换 manifest.json 中的 AppID  
3. 在 HBuilderX 制作自定义调试基座
4. 连接手机进行真机测试

### Phase 3（项目后期）- 发布准备
1. 配置 Android 签名证书
2. 优化应用图标和启动页
3. 打包正式版 APK
4. （可选）配置 iOS 证书和打包

---

## ⚠️ 注意事项

1. **H5 开发不受影响** - 继续用 `.env.development`
2. **AppID 是占位符** - 真机测试前需替换
3. **包名可以改** - 和老师商量后确定正式包名
4. **iOS 需要 Mac** - 暂时可以只开发 Android

---

## 📞 需要帮助？

查看详细文档：`docs/APP端配置完成说明.md`

---

**配置日期**: 2025-11-19  
**配置版本**: v1.0 - Phase 1 基础配置
