# App端登录页面代码生成提示词

---

## 📌 当前实现状态说明

**⚠️ 重要提示：当前项目实际采用的是 V1.0 独立登录方案（完整登录表单），而非 V2.0 跨应用统一登录方案。**

### 当前实际实现（V1.0）

**实现方式**：完整登录表单，直接调用后端登录API

**架构流程**：
```
用户 → 当前APP登录页 → 输入账号密码验证码 → 调用后端登录API → 返回Token → 保存到本地
```

**页面路径**：`src/pages/app/auth/login.vue`（749行）

**主要功能**：
- ✅ 账号名、密码、验证码输入
- ✅ 验证码图片加载与刷新
- ✅ 登录按钮（含loading状态）
- ✅ 注册按钮（占位功能）
- ✅ 忘记密码链接（占位功能）
- ✅ 第三方登录（微信、Apple，占位功能）
- ✅ 使用uni-app原生导航栏
- ✅ 一屏显示，无需滚动

---

## 📱 V1.0 登录页面UI设计规范（当前实际实现）

### 1. 导航栏设计

**使用uni-app原生导航栏**（在pages.json中配置）：

```json
{
  "path": "pages/app/auth/login",
  "style": {
    "navigationBarTitleText": "登录",
    "enablePullDownRefresh": false
  }
}
```

**特点**：
- ✅ 原生导航栏（不是自定义）
- ✅ 标题居中显示"登录"
- ✅ 左侧自动显示返回按钮
- ✅ 与其他页面（如外观设置页）保持统一风格

### 2. 欢迎区域设计

**蓝色渐变背景 + 欢迎文案**：

```vue
<view class="welcome-section">
  <text class="welcome-text">您好，</text>
  <text class="welcome-text">欢迎使用SaaS平台</text>
</view>
```

**样式规范**：
```scss
.welcome-section {
  background: linear-gradient(135deg, #1E90FF 0%, #4169E1 100%);
  padding: 60rpx 40rpx 70rpx 40rpx;
  color: #ffffff;
}

.welcome-text {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  line-height: 1.5;
  color: #ffffff;
}
```

### 3. 表单容器设计

**白色圆角卡片，向上覆盖欢迎区域**：

```scss
.form-container {
  background: #ffffff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 48rpx 40rpx 48rpx 40rpx;
  margin-top: -20rpx;
  flex: 1;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}
```

### 4. 输入框设计

**标签式输入框（账号名、密码、验证码）**：

```vue
<!-- 账号名输入 -->
<view class="input-group">
  <text class="input-label">账号名</text>
  <input
    v-model="formData.username"
    class="input-field"
    type="text"
    placeholder="请输入您的账号"
  />
</view>

<!-- 密码输入（带眼睛图标切换显示） -->
<view class="input-group">
  <text class="input-label">密码</text>
  <view class="input-with-icon">
    <input
      v-model="formData.password"
      class="input-field"
      :type="showPassword ? 'text' : 'password'"
      placeholder="请输入您的密码"
    />
    <text class="toggle-password" @click="togglePasswordVisibility">
      {{ showPassword ? '👁️' : '👁️‍🗨️' }}
    </text>
  </view>
</view>

<!-- 验证码输入（输入框 + 验证码图片） -->
<view class="input-group">
  <text class="input-label">验证码</text>
  <view class="captcha-wrapper">
    <input
      v-model="formData.captcha_solution"
      class="input-field captcha-input"
      type="text"
      placeholder="请输入验证码"
      maxlength="8"
    />
    <view class="captcha-image-container" @click="refreshCaptcha">
      <image :src="captchaUrl" class="captcha-image" mode="aspectFit"></image>
    </view>
  </view>
</view>
```

**样式规范**：
```scss
.input-group {
  margin-bottom: 28rpx;
}

.input-label {
  display: block;
  font-size: 28rpx;
  color: #333333;
  margin-bottom: 16rpx;
  font-weight: 500;
}

.input-field {
  width: 100%;
  height: 80rpx;
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #333333;
  border: 1rpx solid #e8e8e8;
  transition: all 0.3s ease;

  &:focus {
    background: #ffffff;
    border-color: #1E90FF;
  }
}

// 验证码容器
.captcha-wrapper {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.captcha-input {
  flex: 1;
}

.captcha-image-container {
  width: 180rpx;
  height: 80rpx;
  border-radius: 12rpx;
  overflow: hidden;
  background: #f7f8fa;
  border: 1rpx solid #e8e8e8;
  cursor: pointer;
}
```

### 5. 按钮设计

**登录按钮（蓝色渐变）+ 注册按钮（灰色）**：

```vue
<!-- 登录按钮 -->
<button
  class="login-button"
  :class="{ disabled: isLoginDisabled || isLoggingIn }"
  :disabled="isLoginDisabled || isLoggingIn"
  @click="handleLogin"
>
  <text v-if="isLoggingIn">登录中...</text>
  <text v-else-if="isLoginDisabled">请稍后再试 ({{ lockoutCountdown }}s)</text>
  <text v-else>登录</text>
</button>

<!-- 注册按钮 -->
<button class="register-button" @click="showComingSoon">
  注册
</button>
```

**样式规范**：
```scss
.login-button {
  width: 100%;
  height: 80rpx;
  background: linear-gradient(135deg, #1E90FF 0%, #4169E1 100%);
  border-radius: 44rpx;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  margin-top: 32rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 8rpx 20rpx rgba(30, 144, 255, 0.3);

  &:active:not(.disabled) {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(30, 144, 255, 0.2);
  }

  &.disabled {
    background: #d9d9d9;
    box-shadow: none;
    color: #999999;
  }
}

.register-button {
  width: 100%;
  height: 80rpx;
  background: #f7f8fa;
  border-radius: 44rpx;
  color: #333333;
  font-size: 32rpx;
  font-weight: 500;
  border: none;
  margin-bottom: 24rpx;

  &:active {
    background: #e8e8e8;
  }
}
```

### 6. 忘记密码链接

**灰色文字链接，居中显示**：

```vue
<view class="forgot-password" @click="showComingSoon">
  <text class="forgot-text">忘记密码？</text>
</view>
```

```scss
.forgot-password {
  text-align: center;
  padding: 20rpx 0;
  margin-bottom: 32rpx;
}

.forgot-text {
  font-size: 26rpx;
  color: #999999;
  cursor: pointer;

  &:active {
    color: #1E90FF;
  }
}
```

### 7. 第三方登录

**文字链接（微信登录、Apple登录）**：

```vue
<!-- 分割线 -->
<view class="divider">
  <view class="divider-line"></view>
  <text class="divider-text">第三方登录</text>
  <view class="divider-line"></view>
</view>

<!-- 第三方登录链接 -->
<view class="third-party-login">
  <text class="third-party-link" @click="showComingSoon">微信登录</text>
  <text class="third-party-link" @click="showComingSoon">Apple登录</text>
</view>
```

```scss
.divider {
  display: flex;
  align-items: center;
  margin: 32rpx 0 24rpx;
}

.divider-line {
  flex: 1;
  height: 1rpx;
  background: #e8e8e8;
}

.divider-text {
  font-size: 24rpx;
  color: #999999;
  padding: 0 16rpx;
}

.third-party-login {
  display: flex;
  justify-content: center;
  gap: 48rpx;
}

.third-party-link {
  font-size: 28rpx;
  color: #666666;
  padding: 16rpx 24rpx;
  cursor: pointer;

  &:active {
    color: #1E90FF;
  }
}
```

### 8. 布局适配原则

**一屏显示，无需滚动**：

- ✅ 欢迎区域高度：padding 60rpx + 文字 + 70rpx
- ✅ 表单容器：padding 48rpx
- ✅ 输入框间距：28rpx
- ✅ 输入框高度：80rpx
- ✅ 按钮高度：80rpx
- ✅ 所有间距经过调整，确保内容一屏显示完全

### 9. 颜色规范

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 主色（渐变起点） | `#1E90FF` | 蓝色，用于按钮、链接active态 |
| 主色（渐变终点） | `#4169E1` | 深蓝色 |
| 文字主色 | `#333333` | 深灰色 |
| 文字次要色 | `#666666` | 中灰色 |
| 文字辅助色 | `#999999` | 浅灰色 |
| 输入框背景 | `#f7f8fa` | 极浅灰 |
| 边框颜色 | `#e8e8e8` | 浅灰 |
| 白色背景 | `#ffffff` | 纯白 |
| 页面背景 | `#f5f5f5` | 浅灰 |

### 10. 删除的元素

**不再包含的UI元素**：
- ❌ Logo图标区域（已删除）
- ❌ 测试账号提示（已删除）
- ❌ 自定义导航栏（改用原生导航栏）
- ❌ Emoji图标（改用文字或原生图标）

---

## 💼 V1.0 登录页面业务逻辑规范（当前实际实现）

### 1. 数据结构

**表单数据**：
```typescript
interface LoginFormData {
  username: string      // 账号名
  password: string      // 密码
  captcha_solution: string  // 验证码
}

// 响应式数据
const formData = reactive<LoginFormData>({
  username: '',
  password: '',
  captcha_solution: ''
})

const captchaUrl = ref('')           // 验证码图片URL
const showPassword = ref(false)       // 密码可见性
const isLoggingIn = ref(false)        // 登录中状态
const isLoginDisabled = ref(false)    // 登录禁用（429限流）
const lockoutCountdown = ref(0)       // 限流倒计时
```

### 2. 验证码加载逻辑

**页面加载时自动获取验证码**：

```typescript
onMounted(() => {
  getCaptcha()
})

// 获取验证码
const getCaptcha = async () => {
  try {
    const result = await authStore.getCaptcha()
    if (result.success && result.data) {
      captchaUrl.value = result.data.imageUrl
    } else {
      uni.showToast({
        title: '验证码加载失败',
        icon: 'none'
      })
    }
  } catch (error) {
    console.error('获取验证码失败:', error)
  }
}

// 刷新验证码（点击图片）
const refreshCaptcha = () => {
  getCaptcha()
}
```

### 3. 登录逻辑

**登录按钮点击处理**：

```typescript
const handleLogin = async () => {
  // 基础验证
  if (!formData.username || !formData.password || !formData.captcha_solution) {
    uni.showToast({
      title: '请填写完整登录信息',
      icon: 'none'
    })
    return
  }

  // 设置登录中状态
  isLoggingIn.value = true

  try {
    // 调用登录API
    const result = await authStore.login({
      username: formData.username,
      password: formData.password,
      captcha_solution: formData.captcha_solution
    })

    if (result.success) {
      // 登录成功
      uni.showToast({
        title: '登录成功',
        icon: 'success'
      })
      
      // 延迟跳转到首页
      setTimeout(() => {
        uni.reLaunch({
          url: '/pages/app/index'
        })
      }, 500)
    } else {
      // 登录失败 - 处理错误
      handleLoginError(result)
      // 刷新验证码
      getCaptcha()
      // 清空验证码输入
      formData.captcha_solution = ''
    }
  } catch (error) {
    // 网络错误或异常
    console.error('登录异常:', error)
    uni.showToast({
      title: '登录失败，请稍后重试',
      icon: 'none'
    })
    // 刷新验证码
    getCaptcha()
    formData.captcha_solution = ''
  } finally {
    // 重置登录中状态
    isLoggingIn.value = false
  }
}
```

### 4. 429限流处理

**处理登录失败（含429限流）**：

```typescript
const handleLoginError = (result: any) => {
  const error = result.error || {}
  const status = error.status || 0
  const message = error.message || '登录失败'

  if (status === 429) {
    // 429限流 - 提取倒计时秒数
    const match = message.match(/(\d+)\s*秒/)
    const seconds = match ? parseInt(match[1], 10) : 60

    // 禁用登录按钮
    isLoginDisabled.value = true
    lockoutCountdown.value = seconds

    // 倒计时
    const timer = setInterval(() => {
      lockoutCountdown.value--
      if (lockoutCountdown.value <= 0) {
        clearInterval(timer)
        isLoginDisabled.value = false
      }
    }, 1000)

    // 显示提示
    uni.showToast({
      title: `尝试次数过多，请${seconds}秒后重试`,
      icon: 'none',
      duration: 3000
    })
  } else {
    // 其他错误
    uni.showToast({
      title: message,
      icon: 'none'
    })
  }
}
```

### 5. 密码可见性切换

```typescript
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}
```

### 6. 占位功能

**注册、忘记密码、第三方登录暂未实现**：

```typescript
const showComingSoon = () => {
  uni.showToast({
    title: '功能开发中，敬请期待',
    icon: 'none'
  })
}
```

### 7. API调用说明

**依赖Store**：

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 获取验证码
authStore.getCaptcha() // 返回 { success: boolean, data: { imageUrl: string } }

// 登录
authStore.login({ username, password, captcha_solution })
// 返回 { success: boolean, data?: any, error?: { status: number, message: string } }
```

### 8. 错误处理策略

| 错误类型 | 处理方式 | 说明 |
|----------|----------|------|
| 表单验证失败 | 显示提示toast | "请填写完整登录信息" |
| 验证码错误 | 刷新验证码 + toast | 自动刷新验证码，清空输入 |
| 密码错误 | 刷新验证码 + toast | 自动刷新验证码，清空验证码输入 |
| 429限流 | 禁用按钮 + 倒计时 | 60秒倒计时，倒计时结束后恢复 |
| 网络错误 | toast提示 | "登录失败，请稍后重试" |

### 9. 页面生命周期

```typescript
onMounted(() => {
  getCaptcha() // 自动加载验证码
})
```

---

## ⚠️ 以下为V2.0跨应用登录方案（备用，暂未采用）

**V2.0方案说明**：本项目曾计划采用"跨应用统一登录"架构，登录功能由独立的用户服务前端（user_service_frontend）提供。但当前实际采用的是V1.0独立登录方案。

### 🔄 架构变更说明

**原架构（V1.0 - 已废弃）**：
```
用户 → 当前APP → 直接调用后端登录API → 返回Token
```

**新架构（V2.0 - 当前方案）**：
```
用户 → 当前APP → 跳转到统一登录页 → 登录成功回调 → 返回Token
                    ↓
              用户服务前端
              (user_service_frontend)
                    ↓
              调用后端登录API
```

### ⚠️ 已生成代码的处理说明

**如果代码已按照 V1.0 生成，需要进行以下改造：**

1. **删除/简化部分**：
   - ❌ `src/pages/app/auth/login.vue` - 完整登录表单（改为简单跳转页）
   - ❌ `src/api/auth.ts` - `login()` 和 `getCaptcha()` 函数
   - ❌ `src/store/auth.ts` - Mock 登录逻辑
   
2. **保留/新增部分**：
   - ✅ `src/utils/auth.ts` - 安全验证工具函数（新增）
   - ✅ `src/pages/auth/callback.vue` - Token回调处理页（新增）
   - ✅ `src/store/auth.ts` - `forceReauth()` 跳转逻辑（改造）
   - ✅ `src/utils/request.ts` - Token自动注入（保留）

### 📋 新架构技术栈

- ✅ **前端框架**：Vue 3 Composition API + TypeScript + Pinia
- ✅ **登录方式**：跳转到外部登录页（user_service_frontend）
- ✅ **Token获取**：通过URL回调参数接收JWT
- ✅ **安全机制**：Origin白名单 + Token验证 + Redirect验证
- ✅ **多端适配**：iOS/Android/小程序/H5全覆盖

---

## 🏗️ 架构基础（必读）

**在开始开发前，你必须先阅读以下文档：**

📖 **核心设计文档**（⚠️ 必读）：
- `登录功能改造方案.md`（**最重要** - 新架构完整说明）
- `docs/登录与跨应用跳转设计文档.md`（跳转逻辑、回调处理）
- `docs/用户模块设计文档authing版+权限设计版.md`（后端API规范 - 供参考）

📖 **参考页面样式**：
- `src/pages/app/tabbar/my/index.vue`（用户卡片样式、配色方案）
- `src/pages/app/tabbar/home/components/SearchBar.vue`（搜索框样式、阴影效果）

### 🔥 关键技术变更说明

**新架构下的核心变化：**

#### 变更1：不再直接调用登录API ⚠️ **重大变更**

**V1.0（旧方案 - 已废弃）**：
```typescript
// ❌ 不再使用
import { login, getCaptcha } from '@/api/auth';
const response = await login({ username, password });
```

**V2.0（新方案 - 当前）**：
```typescript
// ✅ 跳转到外部登录页
import { useAuthStore } from '@/store/auth';
const authStore = useAuthStore();
authStore.forceReauth('/pages/app/tabbar/home/index');
```

**原因**：登录API由用户服务前端（user_service_frontend）调用，当前应用只负责跳转和接收回调。

#### 变更2：Token获取方式变更 🔄

**V1.0（旧方案）**：
```typescript
// ❌ 不再使用 - 从API响应中获取
const token = response.data.access_token;
```

**V2.0（新方案）**：
```typescript
// ✅ 从回调URL参数中获取
// 在 callback.vue 中：
const token = options.token; // 来自 URL 参数
authStore.setToken(token);
```

#### 变更3：登录页面职责简化 📱

**V1.0（旧方案）**：
- 完整的登录表单（用户名、密码、验证码）
- 调用后端API获取验证码
- 调用后端API执行登录
- 处理登录结果

**V2.0（新方案）**：
```typescript
// ✅ 安全验证工具函数（新增）
import { validateToken, validateRedirectPath, validateOrigin } from '@/utils/auth';

// Origin白名单验证
if (!validateOrigin(window.__ENV.VITE_ALLOWED_ORIGINS)) {
  throw new Error('请求来源验证失败');
}

// Token格式和过期验证
if (!validateToken(token)) {
  throw new Error('Token无效或已过期');
}

// Redirect参数验证（防止开放重定向）
const safeRedirect = validateRedirectPath(redirect);
```

**V1.0中没有的安全机制**：
- ❌ 无Origin白名单验证
- ❌ 无Redirect参数验证
- ❌ 无Token过期时间检查

---

## 第0章：强制性前置检查 ⚡（必须先执行）

### 0.1 避免重复生成说明 ⚠️ **重要**

**如果代码已按照 V1.0 生成过，必须采用改造模式而非重新生成！**

#### 检查清单：

```bash
必须检查的已生成文件：
❓ src/pages/app/auth/login.vue - 是否存在完整登录表单？
❓ src/api/auth.ts - 是否有 login() 和 getCaptcha() 函数？
❓ src/types/auth.ts - 是否定义了 LoginRequest 等类型？
❓ src/store/auth.ts - 是否有 login() 方法和 Mock 登录逻辑？
```

**判断逻辑**：

| 情况 | 操作模式 | 说明 |
|:-----|:--------|:-----|
| ✅ 以上文件全部存在且包含登录逻辑 | **改造模式** | 按照《登录功能改造方案.md》进行改造 |
| ❌ 以上文件不存在或仅有基础结构 | **新建模式** | 直接按照 V2.0 新架构生成 |
| ⚠️ 部分存在，部分缺失 | **混合模式** | 先清理旧代码，再按 V2.0 生成 |

#### 改造模式的具体操作：

**如果采用改造模式，必须执行以下步骤：**

1. **删除/简化文件**：
   ```typescript
   // src/pages/app/auth/login.vue
   // ❌ 删除：完整登录表单、验证码输入框、登录按钮点击逻辑
   // ✅ 保留：简化为跳转页（显示"正在跳转..."）
   ```

2. **删除API函数**：
   ```typescript
   // src/api/auth.ts
   // ❌ 删除以下函数：
   export function getCaptcha() { ... }          // 删除
   export function login(data) { ... }            // 删除
   
   // ✅ 保留以下函数：
   export function refreshToken(data) { ... }     // 保留
   export function getCurrentUser() { ... }       // 保留
   export function logout() { ... }               // 保留
   ```

3. **修改Store方法**：
   ```typescript
   // src/store/auth.ts
   // ❌ 删除：Mock登录逻辑、generateMockToken()、login()中的API调用
   // ✅ 新增：forceReauth()、handleAuthRedirect()
   // ✅ 修改：ensureAuthenticated() 添加白名单逻辑
   ```

4. **新增文件**：
   ```typescript
   // ✅ 必须新增：
   src/utils/auth.ts          // 安全验证工具函数
   src/pages/auth/callback.vue // Token回调处理页
   ```

### 0.2 检查目的

在生成任何代码前，必须全面了解项目现状，避免：
- ❌ 覆盖已有的完善代码
- ❌ 与现有类型定义冲突
- ❌ 创建重复的工具函数
- ❌ 破坏现有的导入依赖关系
- ❌ 重复生成已废弃的 V1.0 代码

### 0.3 必须执行的检查步骤

#### 步骤1：读取现有核心文件（强制）

你必须先读取以下文件，了解现有实现：

```bash
必须读取的文件清单（V2.0 新架构）：
✅ 登录功能改造方案.md - 新架构完整说明（**最重要**）
✅ docs/登录与跨应用跳转设计文档.md - 跳转逻辑详解
✅ src/store/auth.ts - 检查是否有forceReauth/ensureAuthenticated方法
✅ src/utils/request.ts - 检查Token注入逻辑
✅ src/pages/app/tabbar/my/index.vue - 参考样式（仅用于简化登录页）
✅ src/pages.json - 路由配置
✅ public/config.js - 检查是否已配置VITE_LOGIN_URL
```

**⚠️ V1.0 文件检查（判断是否需要改造）**：
```bash
检查是否存在旧版本文件：
❓ src/pages/app/auth/login.vue - 是否包含完整登录表单？
❓ src/api/auth.ts - 是否有login()和getCaptcha()函数？
❓ src/types/auth.ts - 是否定义了LoginRequest类型？
```

**执行命令**：使用 `read_file` 工具逐个读取以上文件。

#### 步骤2：扫描目录结构（强制）

```bash
必须扫描的目录：
✅ src/api/ - 列出所有.ts文件，检查是否已有auth.ts
✅ src/types/ - 列出所有.ts文件，检查是否已有auth.ts
✅ src/pages/app/ - 确认页面目录结构
✅ src/pages/app/auth/ - 检查是否已存在登录页面
```

**执行命令**：使用 `list_dir` 工具扫描目录。

#### 步骤3：在聊天窗口输出项目现状分析（强制）

**重要**：❗ 不要生成单独的分析报告文件，直接在聊天窗口中展示分析结果！

基于步骤1和步骤2的检查结果，在聊天窗口中输出以下结构化分析：

---

**📊 登录页面开发现状分析**

**一、已存在且可直接复用的文件（✅ 直接使用）**

| 文件路径 | 核心功能 | 可复用内容 | 结论 |
|---------|---------|-----------|------|
| `src/store/auth.ts` | 认证状态管理 | - getToken()<br>- setToken()<br>- clearToken()<br>- checkTokenExpiry()<br>- parseUserFromToken() | ✅ 直接导入使用 |
| `src/utils/request.ts` | 网络请求封装 | - 统一请求函数<br>- Token自动注入<br>- 错误处理 | ✅ 直接使用 |
| `src/static/fonts/iconfont.css` | 图标库 | - icon-user<br>- icon-lock<br>- icon-eye<br>- icon-refresh<br>- icon-warning | ✅ 直接使用 |

**二、已存在但需要扩展的文件（🔧 需要补充）**

| 文件路径 | 现有功能 | 缺失功能 | 操作方式 |
|---------|---------|---------|---------|
| `src/store/auth.ts` | - initializeAuth()<br>- setToken()<br>- logout() | - **login()**方法<br>- **refreshAccessToken()**方法<br>- Refresh Token存储 | 🔧 使用replace_string_in_file补充 |
| `src/utils/request.ts` | - Token注入<br>- 错误处理 | - **响应自动解包data字段**（可选） | 🔧 检查是否已实现 |
| `src/pages.json` | 已有路由配置 | - 登录页路由<br>- 注册页路由 | 🔧 添加新路由 |

**三、需要新建的文件（➕ 需新建）**

| 文件路径 | 类型 | 预计行数 | 说明 |
|---------|------|---------|------|
| `src/api/auth.ts` | API接口 | ~150行 | 登录、验证码、SSO、刷新Token、获取用户信息 |
| `src/types/auth.ts` | 类型定义 | ~80行 | 登录请求/响应、验证码、用户信息等类型 |
| `src/pages/app/auth/login.vue` | 登录页面 | ~600行 | 完整登录页面（含第三方登录） |
| `src/pages/app/auth/register.vue` | 注册页面 | ~500行 | 用户注册页（可选，后续开发） |
| `src/pages/app/auth/forgot-password.vue` | 忘记密码页 | ~400行 | 密码重置流程（可选） |

**四、样式参考来源（📐 复用规范）**

| 样式元素 | 参考文件 | 具体样式 | 数值 |
|---------|---------|---------|------|
| **背景渐变** | `callback.vue` | `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` | 页面背景 |
| **主题蓝色** | `my/index.vue` | `linear-gradient(135deg, #509CEC 0%, #3B7DD8 100%)` | 按钮、卡片 |
| **页面padding** | `my/index.vue` | `32rpx` | 左右边距 |
| **搜索框阴影** | `SearchBar.vue` | `box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06)` | 输入框阴影 |
| **圆角** | `my/index.vue` | `16rpx` | 按钮、输入框 |
| **字号** | `my/index.vue` | 24/26/28/32rpx | 小字/链接/正文/标题 |

**五、技术决策确认（🔒 强制规范）**

| 决策项 | 选择方案 | 理由 | 当前阶段实现方式 |
|--------|---------|------|----------------|
| **Token存储** | ✅ 方案B：uni.setStorageSync持久化 | App端需保持登录状态，安全性由沙盒保证 | ✅ 完整实现 |
| **自动登录** | ✅ 实现（7天，基于Refresh Token） | 提升用户体验，后端已支持 | ✅ 完整实现 |
| **记住密码** | ❌ 不实现 | 严重安全风险，违反医学平台规范 | ❌ 不实现 |
| **图形验证码** | ✅ 必须实现（P0） | 防止暴力破解，后端强制校验 | ✅ 完整实现 |
| **OTP验证码** | ❌ 登录不实现 | 登录无需验证邮箱/手机，注册时再实现 | ❌ 不实现 |
| **跨应用登录** | ❌ App端不实现 | App独立登录，不需要跳转到其他应用 | ❌ 不实现 |
| **第三方登录** | ⚠️ 占位实现（P1） | 后端已支持SSO，但当前优先核心功能 | 🔵 占位（点击显示"功能开发中"） |
| **密码重置** | ⚠️ 占位实现（P1） | 后续优化时补充完整流程 | 🔵 占位（跳转占位页面） |
| **生物识别登录** | ⏳ V2.0补充 | 优化功能，非必需 | ❌ 不实现 |
| **响应格式** | ✅ 手动解包（与现有一致） | 保持ApiResponse<T>包装 | ✅ 无需修改 |

**六、当前阶段实现范围（📋 功能边界）**

#### ✅ P0核心功能（必须完整实现）

1. **账号密码登录**
   - 支持用户名/邮箱/手机号三种格式
   - 密码显示/隐藏切换
   - 完整的表单验证和错误提示

2. **图形验证码**
   - 调用GET /api/v1/auth/captcha
   - 显示Base64图片
   - 点击刷新（防抖1秒）
   - 登录失败自动刷新（一次性消费机制）

3. **Token管理**
   - Access Token存储（15分钟）
   - Refresh Token存储（7天）
   - Token过期检查
   - 自动刷新Token
   - 登录成功跳转首页

4. **用户信息获取**
   - 调用GET /api/v1/users/me
   - 存储到authStore.user
   - 设置isAuthenticated=true

#### 🔵 P1占位功能（仅实现UI占位）

5. **第三方登录按钮**
   - 显示微信/Apple登录按钮
   - 点击后显示Toast：`uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' })`
   - **不要**集成Authing SDK（后续迭代时再实现）
   - **不要**调用POST /api/v1/auth/sso-login接口

6. **忘记密码入口**
   - 显示"忘记密码？"链接
   - 点击后显示Toast：`uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' })`
   - **不要**跳转到任何页面

7. **注册入口**
   - 显示"没有账号？立即注册"链接
   - 点击后显示Toast：`uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' })`
   - **不要**跳转到任何页面

#### ❌ 明确不实现的功能

- ❌ 跨应用登录（external_callback参数、Origin验证、Redirect验证）
- ❌ OTP验证码（登录场景不需要，注册时再实现）
- ❌ 生物识别登录（V2.0优化功能）
- ❌ Authing SDK集成（第三方登录占位即可）
- ❌ 完整的密码重置流程（占位即可）

#### 🎯 当前阶段目标

**实现基本的账号密码登录功能，确保用户可以完成"登录 → 获取Token → 访问其他功能"的完整流程。**

**为什么这样设计？**
- ✅ **优先核心流程**：先实现登录和注册的基本功能，验证评论、收藏等其他页面的功能
- ✅ **降低复杂度**：第三方登录需要Authing配置，延后实现不影响核心流程
- ✅ **渐进式开发**：先完成MVP，后续迭代时补充完整功能

**七、安全性分析（⚠️ 风险评估）**

| 潜在风险 | 解决方案 |
|---------|---------|
| Token明文存储 | ✅ uni.setStorageSync在App端已加密（系统级） |
| XSS攻击 | ✅ App端无DOM，天然免疫 |
| 密码明文传输 | ✅ 强制HTTPS（后端已配置） |
| 验证码被绕过 | ✅ 后端强制校验，3分钟过期 |
| Token被劫持 | ✅ 15分钟过期+黑名单机制 |

---

#### 步骤4：等待用户确认（强制）

在聊天窗口输出分析结果后，**必须等待用户确认**才能继续生成代码。

向用户提问：
```
📋 以上是登录页面开发现状分析结果。

请确认：
1. 分析结果是否准确？
2. 是否有遗漏或需要调整的地方？
3. 如果确认无误，请输入"确认继续"开始代码生成。
```

**禁止**在用户确认前开始生成任何代码！

---

## 第1章：角色定义（Role Definition）

你是一名**资深uni-app移动端前端工程师**，拥有以下专业技能：

### 1.1 核心技能树

- ✅ **Vue 3生态专家**：精通Composition API、Pinia状态管理、响应式原理
- ✅ **TypeScript大师**：严格类型系统、泛型编程、类型推导
- ✅ **uni-app跨端开发**：iOS/Android/小程序/H5多端适配
- ✅ **安全架构师**：JWT认证、Token管理、敏感信息脱敏
- ✅ **UI/UX设计师**：移动端交互设计、无障碍支持、响应式布局
- ✅ **API集成专家**：RESTful接口对接、错误处理、异步流程

### 1.2 开发准则

1. **安全第一**：所有敏感信息必须脱敏，Token存储符合规范
2. **类型严格**：禁止使用any，所有接口必须有完整类型定义
3. **错误处理完善**：所有API调用必须try-catch，用户友好的错误提示
4. **性能优化**：防抖节流、懒加载、虚拟滚动
5. **代码可读性**：完整的JSDoc注释、清晰的变量命名
6. **无障碍支持**：aria标签、焦点管理、屏幕阅读器优化

---

## 第2章：核心API规范（精简版）

### 2.1 通用响应格式

**后端返回标准格式**：

```typescript
{
  code: 200,           // 业务状态码（200成功，其他为错误）
  message: "success",  // 消息描述
  data: {...}          // 实际数据在这里
  timestamp: "2025-07-22T19:50:00Z"
}
```

**前端API层返回格式（手动解包模式）**：

```typescript
// ✅ 与现有API保持一致：返回完整响应
export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return post<ApiResponse<LoginResponse>>('/auth/login', data);
};

// 调用时手动解包
const response = await login(data);
const token = response.data.access_token;  // ← 手动 .data 解包
const code = response.code;                 // ← 可访问状态码
const message = response.message;           // ← 可访问消息
```

**为什么使用手动解包？**
- ✅ 与现有所有API（room.ts、topic.ts、favorite.ts等）保持100%一致
- ✅ 可以访问 `code`、`message` 进行更精细的错误处理
- ✅ 类型安全，明确知道响应结构

### 📌 **关键理解：request.ts 的返回值机制**

**request.ts 的行为（src/utils/request.ts 第183行）：**
```typescript
resolve(res.data as T);
```

**这里的 `res.data` 是什么？**
- `res` 是 `uni.request` 的响应对象：`{ statusCode: 200, data: {...}, header: {...} }`
- `res.data` 是**后端返回的完整 JSON 响应体**：
  ```json
  {
    "code": 200,
    "message": "success",
    "data": { "access_token": "...", "refresh_token": "..." },
    "timestamp": "2025-01-14T10:00:00Z"
  }
  ```

**所以 request.ts 返回的就是这个完整对象，没有自动解包！**

**为什么叫"手动解包"？**
- 因为你需要**手动访问 `response.data`** 来获取业务数据
- 不像有些项目会在 request.ts 中自动返回 `res.data.data`（自动解包）
- 现有项目保持了后端响应的完整性，便于错误处理

**正确的调用方式：**
```typescript
// ✅ 步骤1：调用 API，获取完整响应
const response = await login(data);
// response = { code: 200, message: 'ok', data: { access_token, refresh_token }, timestamp: '...' }

// ✅ 步骤2：手动解包，访问 response.data 获取业务数据
const { access_token, refresh_token } = response.data;

// ✅ 步骤3：也可以访问状态码和消息，便于精细化错误处理
if (response.code === 200) {
  console.log(response.message); // 'success'
  // 登录成功，使用 response.data 中的 token
} else if (response.code === 3001) {
  // 用户名或密码错误
  console.error(response.message);
}
```

**与现有 API 的一致性验证：**
```typescript
// ✅ room.ts 的写法（现有代码）
const response = await getRoomDetail(roomId);
if (response.code === 200) {
  const room = response.data;  // ← 手动访问 .data
}

// ✅ auth.ts 的写法（提示词生成，与现有代码完全一致）
const response = await login(data);
if (response.code === 200) {
  const token = response.data.access_token;  // ← 手动访问 .data
}
```

**常见错误示例：**
```typescript
// ❌ 错误：以为 request.ts 会自动解包到业务数据
const token = await login(data);  // 错误！返回的是 ApiResponse 对象，不是 token

// ✅ 正确：先获取响应对象，再访问 data
const response = await login(data);
const token = response.data.access_token;  // 正确！
```

### 2.2 登录相关API清单

| 功能 | API路径 | 方法 | 请求体 | 响应 |
|------|--------|------|--------|------|
| **获取验证码** | `/api/v1/auth/captcha` | GET | - | `{captcha_id, image_base64}` |
| **用户登录** | `/api/v1/auth/login` | POST | `{username, password, captcha_id, captcha_solution}` | `{access_token, refresh_token, token_type}` |
| **刷新Token** | `/api/v1/auth/refresh` | POST | `{refresh_token}` | `{access_token, token_type}` |
| **获取用户信息** | `/api/v1/users/me` | GET | - | `{uuid, username, email, ...}` |
| **用户登出** | `/api/v1/auth/logout` | POST | - | - |
| **SSO登录** | `/api/v1/auth/sso-login` | POST | `{id_token}` | `{access_token, refresh_token, token_type}` |
| **请求密码重置** | `/api/v1/auth/password-reset-request` | POST | `{email, captcha_id, captcha_solution}` | `{reset_token}` |
| **执行密码重置** | `/api/v1/auth/password-reset` | POST | `{reset_token, new_password}` | - |

### 2.3 关键字段说明

#### 登录请求（LoginRequest）

```typescript
{
  username: string;        // 支持用户名/邮箱/手机号三种格式
  password: string;        // 密码（前端不需要验证强度）
  captcha_id: string;      // 验证码ID（UUID格式）
  captcha_solution: string; // 验证码答案（4位字母数字）
}
```

#### 登录响应（LoginResponse）

```typescript
{
  access_token: string;    // JWT Token，15分钟有效
  refresh_token: string;   // 7天有效，用于自动刷新
  token_type: "bearer";    // 固定值
}
```

#### 用户信息（UserInfo）

```typescript
{
  uuid: string;
  username: string;
  email: string;
  phone_number?: string;
  nickname: string;
  avatar_url?: string;
  bio?: string;
  role: 'REGULAR' | 'ADMIN' | 'SUPERADMIN';
  status: 'NORMAL' | 'BANNED';
  is_email_verified: boolean;
  is_phone_verified?: boolean;
}
```

### 2.4 登录数据流向图

```
页面加载 (onMounted)
  ↓
调用 getCaptcha() 获取验证码
  ├─ 成功 → 显示Base64图片
  └─ 失败 → Toast提示，3秒后自动重试
  ↓
用户填写表单 (username/password/captcha)
  ├─ 实时验证 → @focus清除错误，@blur验证格式
  └─ 防抖处理 → 密码输入300ms防抖
  ↓
点击登录按钮
  ├─ 表单验证（validateForm）
  │   ├─ 用户名非空
  │   ├─ 密码≥8位
  │   └─ 验证码=4位
  ↓
调用 authStore.login()
  ├─ POST /api/v1/auth/login
  │   ├─ 请求拦截器：添加Content-Type
  │   └─ 响应拦截器：自动解包data字段
  ↓
处理响应
  ├─ 成功 (code=200)
  │   ├─ 存储Token（uni.setStorageSync）
  │   │   ├─ jwt_token → Access Token（15分钟）
  │   │   └─ refresh_token → Refresh Token（7天）
  │   ├─ 调用 getCurrentUser() 获取用户信息
  │   ├─ 更新authStore状态（isAuthenticated=true）
  │   ├─ Toast提示"登录成功"
  │   └─ 1.5秒后跳转首页（uni.switchTab）
  │
  └─ 失败
      ├─ code=3001 → "用户名或密码错误"（标红密码框）
      ├─ code=4003 → "验证码错误"（刷新验证码）
      ├─ code=429 → "请求过于频繁"（禁用按钮60秒）
      └─ 其他 → Toast显示error.message
  ↓
初始化自动登录 (initializeAuth)
  ├─ 检查Access Token有效期
  │   ├─ 有效 → 直接使用
  │   └─ 过期 → 检查Refresh Token
  │       ├─ 有效 → 调用refreshAccessToken()
  │       └─ 过期 → 清除认证，显示登录页
  └─ 更新用户信息
```

### 2.5 错误码处理

| HTTP状态码 | 业务code | 含义 | 前端处理 |
|-----------|---------|------|---------|
| 200 | 200 | 成功 | 正常处理 |
| 401 | 3001 | 用户名或密码错误 | 显示错误提示 |
| 401 | 3003 | Token无效或过期 | 清除Token，跳转登录 |
| 400 | 4003 | 验证码错误或过期 | 刷新验证码，提示重试 |
| 429 | 4029 | 请求过于频繁 | Toast提示"请稍后重试" |
| 500 | 1001 | 系统内部错误 | Toast提示"服务异常" |

---

## 第3章：后端API对接说明

### 3.1 后端API现状

**✅ 后端已完整实现所有登录相关API，可直接调用真实接口！**

根据 `docs/用户模块设计文档authing版+权限设计版.md`，后端已实现：

| API接口 | 状态 | 说明 |
|---------|------|------|
| `GET /api/v1/auth/captcha` | ✅ 已实现 | 获取图形验证码（Base64图片） |
| `POST /api/v1/auth/login` | ✅ 已实现 | 用户登录（用户名/密码/验证码） |
| `POST /api/v1/auth/refresh` | ✅ 已实现 | 刷新Access Token |
| `GET /api/v1/users/me` | ✅ 已实现 | 获取当前用户信息 |
| `POST /api/v1/auth/logout` | ✅ 已实现 | 用户登出 |
| `POST /api/v1/auth/sso-login` | ✅ 已实现 | SSO第三方登录 |

### 3.2 环境配置

**确认 `.env.development` 已正确配置：**

```bash
# ✅ 后端API地址（已包含 /api/v1 前缀）
VITE_BASE_API_URL=http://124.220.235.226:8000/api/v1

# ⚠️ Mock开关配置说明
# 方案A（推荐）：关闭Mock，直接使用真实后端API
VITE_USE_MOCK=false

# 方案B（当前配置）：开启Mock，需额外创建 src/api/auth.mock.ts
# VITE_USE_MOCK=true  # ← 当前.env.development的配置
# ⚠️ 如果使用Mock，登录功能将无法调用真实后端，需自行实现Mock文件

# ✅ 登录页面路径（App端）
VITE_LOGIN_URL=http://localhost:5173/pages/app/auth/login
```

**说明**：
- 项目中的 `src/api/room.ts`、`src/api/session.ts` 等已成功调用真实API
- 登录API同样可以直接调用，**无需创建Mock文件**
- 如果后端服务未启动，可以临时设置 `VITE_USE_MOCK=true`（需自行创建 `auth.mock.ts`）

### 3.3 API调用示例

**所有API返回格式统一为 `ApiResponse<T>`：**

```typescript
// ✅ 正确：与现有API保持一致
export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return post<ApiResponse<LoginResponse>>('/auth/login', data);
};

// 调用时手动解包
const response = await login(data);
const { access_token, refresh_token } = response.data;  // ← 手动解包
```

### 3.4 测试账号（后端真实数据）

**✅ 后端数据库中已有测试账号，可直接登录，无需开发注册页面！**

| 账号 | 密码 | 角色 | 说明 |
|------|------|------|------|
| **admin** | **Admin@123** | **SUPERADMIN** | 超级管理员（推荐测试用） |
| **testuser** | **Test@123** | **REGULAR** | 普通用户 |

**登录测试步骤：**
1. 打开登录页面：`/pages/app/auth/login`
2. 输入账号：`admin`
3. 输入密码：`Admin@123`
4. 输入验证码（从后端动态获取）
5. 点击登录 → 自动跳转首页

**⚠️ 重要说明：**
- ✅ 当前阶段**不需要**开发注册页面
- ✅ 测试账号已由后端预先创建
- ✅ 生产环境可由管理员后台创建账号
- 🔵 注册页面可作为V2.0功能，当前阶段占位即可

---

## 第3.5章：如何触发登录页面

### 3.5.1 自动触发（推荐）

**方式1：通过401拦截自动跳转（已实现）**

现有的 `request.ts` 已包含401拦截逻辑：
```typescript
// src/utils/request.ts 第191-203行
if (res.statusCode === 401) {
  const authStore = useAuthStore();
  authStore.forceReauth(`/pages/${currentPath}`);
}
```

**触发场景：**
- 访问需要登录的API（获取用户信息、收藏列表等）
- Token过期或无效
- 未登录状态访问受保护资源

**方式2：App启动检查（建议添加到App.vue）**

```vue
<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';

onLaunch(async () => {
  console.log('🚀 App启动');
  
  const authStore = useAuthStore();
  await authStore.initializeAuth();
  
  // 检查是否已登录
  if (!authStore.isAuthenticated) {
    console.log('❌ 未登录，跳转登录页');
    uni.navigateTo({
      url: '/pages/app/auth/login'
    });
  } else {
    console.log('✅ 已登录，用户:', authStore.user?.username);
  }
});
</script>
```

### 3.5.2 手动触发（用于测试）

**在任意页面添加测试按钮：**
```vue
<button @click="goToLogin">测试登录</button>

<script setup>
function goToLogin() {
  uni.navigateTo({
    url: '/pages/app/auth/login'
  });
}
</script>
```

**或在浏览器地址栏直接访问：**
```
http://localhost:5173/#/pages/app/auth/login
```

### 3.5.3 登录成功后的跳转逻辑

**登录成功后会自动跳转到：**
```typescript
// login.vue中的处理
setTimeout(() => {
  uni.switchTab({
    url: '/pages/app/tabbar/home/index' // ← 跳转到首页
  });
}, 1500);
```

**如果是从其他页面被401拦截跳转过来的：**
- ✅ 会自动跳转回原页面（通过`redirectPath`记录）
- ✅ 保证用户体验的连贯性

---

## 第4章：生成任务清单

### 4.1 复用策略分层

#### 4.1.1 完全复用层（100%复用，直接导入）

| 文件路径 | 功能 | 使用方式 |
|---------|------|----------|
| `src/utils/request.ts` | 网络请求封装 | `import { request } from '@/utils/request'` |
| `src/store/auth.ts` | 认证状态管理 | `import { useAuthStore } from '@/store/auth'` |
| `src/config/env.ts` | 环境配置 | `import { VITE_USE_MOCK } from '@/config/env'` |
| `src/utils/common.ts` | 通用工具函数 | `import { debounce } from '@/utils/common'` |

#### 4.1.2 部分复用层（60-80%复用，需扩展）

| 文件路径 | 现有功能 | 缺失功能 | 操作方式 |
|---------|---------|---------|----------|
| `src/store/auth.ts` | setToken/getToken/logout | **login()**、**refreshAccessToken()** | 使用replace_string_in_file补充 |
| `src/utils/request.ts` | Token注入、错误拦截 | ✅ 完整（手动解包模式） | 无需修改 |

#### 4.1.3 新建层（0%复用，需创建）

| 文件路径 | 类型 | 预计行数 | 说明 |
|---------|------|---------|------|
| `src/api/auth.ts` | API接口 | ~150行 | 登录/验证码/SSO/刷新Token |
| `src/types/auth.ts` | 类型定义 | ~80行 | 请求/响应类型 |
| `src/pages/app/auth/login.vue` | 登录页面 | ~600行 | 完整登录页面 |

### 4.2 任务优先级

#### P0（必须生成）

**1. src/types/auth.ts**（约80行）

```typescript
// 类型定义文件内容要求：

/** 验证码响应 */
export interface CaptchaResponse {
  captcha_id: string;
  image_base64: string;  // data:image/png;base64,xxx格式
}

/** 登录请求 */
export interface LoginRequest {
  username: string;
  password: string;
  captcha_id: string;
  captcha_solution: string;
}

/** 登录响应 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

/** SSO登录请求 */
export interface SSOLoginRequest {
  id_token: string;
}

/** 刷新Token请求 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/** 刷新Token响应 */
export interface RefreshTokenResponse {
  access_token: string;
  token_type: 'bearer';
}

/** 用户信息 */
export interface UserInfo {
  uuid: string;
  username: string;
  email: string;
  phone_number?: string;
  nickname: string;
  avatar_url?: string;
  bio?: string;
  role: 'REGULAR' | 'ADMIN' | 'SUPERADMIN';
  status: 'NORMAL' | 'BANNED';
  is_email_verified: boolean;
  is_phone_verified?: boolean;
}

/** 密码重置请求 */
export interface PasswordResetRequest {
  email: string;
  captcha_id: string;
  captcha_solution: string;
}

/** 密码重置执行 */
export interface PasswordResetExecute {
  reset_token: string;
  new_password: string;
}
```

---

**2. src/api/auth.ts**（约150行）

```typescript
// API接口文件内容要求：

import { post, get } from '@/utils/request';
import type { ApiResponse } from '@/types/common';
import type {
  CaptchaResponse,
  LoginRequest,
  LoginResponse,
  SSOLoginRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  UserInfo,
  PasswordResetRequest,
  PasswordResetExecute
} from '@/types/auth';

/**
 * 获取图形验证码
 * @returns 验证码ID和Base64图片
 * @example
 * const response = await getCaptcha();
 * const captchaData = response.data;
 */
export const getCaptcha = (): Promise<ApiResponse<CaptchaResponse>> => {
  return get<ApiResponse<CaptchaResponse>>('/auth/captcha');
};

/**
 * 用户登录
 * @param data 登录信息（用户名/密码/验证码）
 * @returns Access Token和Refresh Token
 * @example
 * const response = await login({ username: 'test', password: 'test123' });
 * const { access_token, refresh_token } = response.data;
 */
export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return post<ApiResponse<LoginResponse>>('/auth/login', data);
};

/**
 * 刷新Access Token
 * @param data Refresh Token
 * @returns 新的Access Token
 * @example
 * const response = await refreshToken({ refresh_token: 'xxx' });
 * const newToken = response.data.access_token;
 */
export const refreshToken = (data: RefreshTokenRequest): Promise<ApiResponse<RefreshTokenResponse>> => {
  return post<ApiResponse<RefreshTokenResponse>>('/auth/refresh', data);
};

/**
 * 获取当前用户信息
 * @returns 用户详细信息
 * @example
 * const response = await getCurrentUser();
 * const user = response.data;
 */
export const getCurrentUser = (): Promise<ApiResponse<UserInfo>> => {
  return get<ApiResponse<UserInfo>>('/users/me', undefined, { auth: true });
};

/**
 * 用户登出
 * @example
 * await logout();
 */
export const logout = (): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>('/auth/logout', undefined, { auth: true });
};

/**
 * SSO第三方登录（微信/Apple）
 * @param data Authing返回的id_token
 * @returns Access Token和Refresh Token
 * @example
 * const response = await ssoLogin({ id_token: 'xxx' });
 * const { access_token, refresh_token } = response.data;
 */
export const ssoLogin = (data: SSOLoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return post<ApiResponse<LoginResponse>>('/auth/sso-login', data);
};

/**
 * 请求密码重置
 * @param data 邮箱和验证码
 * @example
 * await requestPasswordReset({ email: 'test@example.com', captcha_id: 'xxx', captcha_solution: '1234' });
 */
export const requestPasswordReset = (data: PasswordResetRequest): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>('/auth/password-reset-request', data);
};

/**
 * 执行密码重置
 * @param data 重置令牌和新密码
 * @example
 * await resetPassword({ reset_token: 'xxx', new_password: 'NewPass@123' });
 */
export const resetPassword = (data: PasswordResetExecute): Promise<ApiResponse<void>> => {
  return post<ApiResponse<void>>('/auth/password-reset', data);
};
```

**关键点**：
- ✅ 所有API返回 `Promise<ApiResponse<T>>`，与现有API（room.ts、favorite.ts）保持一致
- ✅ 使用 `get`、`post` 方法（从 `@/utils/request` 导入）
- ✅ URL使用相对路径（`/auth/login` 而非 `/api/v1/auth/login`）
- ✅ 调用时需手动解包：`response.data.access_token`

---

**3. 扩展 src/store/auth.ts**（补充login/refreshAccessToken方法）

**检查现有方法**：
- ✅ 如果已有`login()`方法 → 跳过
- ❌ 如果没有 → 使用replace_string_in_file补充

**需要补充的方法**：

```typescript
// 在actions中补充以下方法：

/**
 * 用户登录
 * @param payload 登录信息
 */
async login(payload: LoginRequest) {
  try {
    // 1. 调用登录API
    const response = await login(payload);
    
    // 2. 检查响应状态
    if (response.code !== 200) {
      throw new Error(response.message || '登录失败');
    }
    
    // 3. 手动解包数据
    const { access_token, refresh_token } = response.data;
    
    // 4. 存储Token（🔴 必须同时存储Access Token和Refresh Token）
    this.setToken(access_token);
    uni.setStorageSync('refresh_token', refresh_token); // ← 🔴 P0必须添加！
    
    // 5. 解析Token获取用户基本信息
    this.parseUserFromToken(access_token);
    
    // 6. 获取完整用户信息
    await this.fetchUserProfile();
    
    return response.data;
  } catch (error) {
    console.error('登录失败:', error);
    throw error;
  }
},

/**
 * 刷新Access Token（实现7天自动登录）
 */
async refreshAccessToken() {
  try {
    const refreshTokenValue = uni.getStorageSync('refresh_token');
    
    if (!refreshTokenValue) {
      throw new Error('No refresh token');
    }
    
    // 调用刷新接口
    const response = await refreshToken({ refresh_token: refreshTokenValue });
    
    // 手动解包并更新Access Token
    const { access_token } = response.data;
    this.setToken(access_token);
    
    return response.data;
  } catch (error) {
    console.error('刷新Token失败:', error);
    this.clearAuth();
    throw error;
  }
},

/**
 * 获取用户信息
 */
async fetchUserProfile() {
  try {response = await getCurrentUser();
    this.user = response.data;  // 手动解包t getCurrentUser();
    this.user = user;
    this.isAuthenticated = true;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    throw error;
  }
},

/**
 * 增强版初始化认证（支持7天自动登录）
 * 🔴 P0必须替换现有的initializeAuth方法
 */
async initializeAuth() {
  console.log('🔄 初始化认证状态...');
  
  const accessToken = getToken();
  const refreshToken = uni.getStorageSync('refresh_token');
  
  if (accessToken && checkTokenExpiry(accessToken)) {
    // ✅ Access Token有效，直接使用
    console.log('✅ Access Token有效');
    this.setToken(accessToken);
    this.parseUserFromToken(accessToken);
    try {
      await this.fetchUserProfile();
    } catch (error) {
      console.error('获取用户信息失败:', error);
      // 用户信息获取失败不影响认证状态
    }
  } else if (refreshToken && checkTokenExpiry(refreshToken)) {
    // ⚠️ Access Token过期，但Refresh Token有效，自动刷新
    console.log('⚠️ Access Token过期，尝试自动刷新...');
    try {
      await this.refreshAccessToken();
      await this.fetchUserProfile();
      console.log('✅ 自动登录成功');
    } catch (error) {
      console.error('❌ 自动登录失败:', error);
      this.clearAuth();
    }
  } else {
    // ❌ 两个Token都过期或不存在，清除认证
    console.log('❌ Token已过期或不存在，需要重新登录');
    this.clearAuth();
  }
},

/**
 * 强制重新认证（🔴 修复版：生产环境跳转登录页）
 * @param targetPath 目标路径
 */
forceReauth(targetPath: string) {
  this.clearAuth();
  this.setRedirectPath(targetPath);
  
  // 🔴 修复：区分开发环境和生产环境
  // #ifdef H5
  if (import.meta.env.DEV) {
    // 开发环境：使用mock登录快速测试
    console.log('🔧 [DEV] 使用mock登录');
    this.mockLoginWithRealToken();
  } else {
    // 生产环境：跳转登录页
    console.log('🔐 [PROD] 跳转登录页');
    uni.navigateTo({
      url: '/pages/app/auth/login'
    });
  }
  // #endif
  
  // #ifndef H5
  // App端、小程序端：直接跳转登录页
  console.log('📱 [APP] 跳转登录页');
  uni.navigateTo({
    url: '/pages/app/auth/login',
    fail: () => {
      uni.showToast({
        title: '请重新登录',
        icon: 'none'
      });
    }
  });
  // #endif
},
```

---

**4. src/pages/app/auth/login.vue**（约728行 - V2.0简化版）

**⚠️ 重要变更说明**：
- ✅ 使用uni-app原生导航栏（在pages.json配置，不在template中）
- ✅ 蓝色渐变欢迎区 + 白色卡片表单（替代紫色渐变背景）
- ✅ 标签式输入框（label在上方，替代图标在左侧）
- ✅ 第三方登录简化为文字链接（替代圆形图标按钮）
- ❌ 删除测试账号提示（不显示测试账号信息）
- ✅ 一屏显示完全（通过调整padding/margin实现）

**页面结构要求**：

```vue
<template>
  <view class="login-container">
    <!-- Logo区域 -->
    <view class="logo-section">
      <image class="logo-icon" src="/static/logo.png" mode="aspectFit" />
      <text class="app-name">医学直播平台</text>
    </view>

    <!-- 表单容器 -->
    <view class="form-container">
      <!-- 用户名输入框 -->
      <view class="input-group">
        <view class="input-wrapper" :class="{ focused: focusedField === 'username', error: !!errors.username }">
          <text class="iconfont icon-user input-icon"></text>
          <input
            class="input-field"
            type="text"
            placeholder="用户名/邮箱/手机号"
            v-model="username"
            @focus="handleFocus('username')"
            @blur="handleBlur('username')"
          />
        </view>
        <view v-if="errors.username" class="error-tip">
          <text class="iconfont icon-warning"></text>
          <text>{{ errors.username }}</text>
        </view>
      </view>

      <!-- 密码输入框 -->
      <view class="input-group">
        <view class="input-wrapper" :class="{ focused: focusedField === 'password', error: !!errors.password }">
          <text class="iconfont icon-lock input-icon"></text>
          <input
            class="input-field"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
            v-model="password"
            @focus="handleFocus('password')"
            @blur="handleBlur('password')"
          />
          <view class="toggle-password" @tap="togglePasswordVisibility">
            <text class="iconfont" :class="showPassword ? 'icon-eye' : 'icon-eye-close'"></text>
          </view>
        </view>
        <view v-if="errors.password" class="error-tip">
          <text class="iconfont icon-warning"></text>
          <text>{{ errors.password }}</text>
        </view>
      </view>

      <!-- 验证码 -->
      <view class="input-group">
        <view class="captcha-container">
          <view class="captcha-image-wrapper" @tap="refreshCaptcha">
            <image v-if="captchaUrl" class="captcha-image" :src="captchaUrl" mode="aspectFill" />
            <view class="captcha-refresh">
              <text class="iconfont icon-refresh"></text>
            </view>
            <view v-if="isCaptchaLoading" class="loading-mask">
              <view class="loading-spinner"></view>
            </view>
          </view>
          
          <input
            class="captcha-input"
            type="text"
            maxlength="4"
            placeholder="验证码"
            v-model="captchaCode"
          />
        </view>
        <view v-if="errors.captcha" class="error-tip">
          <text class="iconfont icon-warning"></text>
          <text>{{ errors.captcha }}</text>
        </view>
      </view>

      <!-- 功能链接 -->
      <view class="function-links">
        <text class="forgot-password" @tap="handleForgotPassword">忘记密码？</text>
        <view class="other-login" @tap="showOtherLoginOptions">
          <text>其他方式登录</text>
          <text class="iconfont icon-arrow-right"></text>
        </view>
      </view>

      <!-- 登录按钮 -->
      <view class="login-button" :class="loginButtonState" @tap="handleLogin">
        <view v-if="!isLoading" class="button-text">登 录</view>
        <view v-else class="loading-content">
          <view class="loading-icon"></view>
          <text>登录中...</text>
        </view>
      </view>

      <!-- 分割线 -->
      <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">或使用以下方式登录</text>
        <view class="divider-line"></view>
      </view>

      <!-- 第三方登录 -->
      <view class="social-login">
        <view class="social-btn" @tap="handleWechatLogin">
          <view class="social-icon">
            <image src="/static/icons/wechat.png" mode="aspectFit" />
          </view>
          <text class="social-text">微信</text>
        </view>
        
        <view class="social-btn" @tap="handleAppleLogin">
          <view class="social-icon">
            <image src="/static/icons/apple.png" mode="aspectFit" />
          </view>
          <text class="social-text">Apple</text>
        </view>
      </view>

      <!-- 注册链接 -->
      <view class="register-link">
        <text class="register-text">
          还没有账号？<text class="link" @tap="handleGoToRegister">去注册</text>
        </text>
      </view>

      <!-- 隐私协议 -->
      <view class="privacy-agreement">
        <text class="agreement-text">
          登录即表示同意
          <text class="link" @tap="handleUserAgreement">《用户协议》</text>
          和
          <text class="link" @tap="handlePrivacyPolicy">《隐私政策》</text>
        </text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
// 导入必需的依赖
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import { getCaptcha } from '@/api/auth';
import type { LoginRequest } from '@/types/auth';

// ========== 状态管理 ==========
const authStore = useAuthStore();

// 表单数据
const username = ref('');
const password = ref('');
const captchaCode = ref('');
const captchaId = ref('');
const captchaUrl = ref('');

// UI状态
const showPassword = ref(false);
const isLoading = ref(false);
const isCaptchaLoading = ref(false);
const focusedField = ref('');
const errors = ref<Record<string, string>>({});

// 🔴 隐患修复1：登录按钮防抖（防止重复点击）
const isLoggingIn = ref(false);

// 🔴 隐患修复2：验证码重试限制（防止死循环）
const captchaRetryCount = ref(0);
const MAX_CAPTCHA_RETRY = 3;

// 🔴 隐患修复3：速率限制状态
const isLoginDisabled = ref(false);

// ========== 计算属性 ==========
const loginButtonState = computed(() => {
  if (!username.value || !password.value || !captchaCode.value) {
    return 'disabled';
  }
  if (isLoading.value) {
    return 'loading';
  }
  return 'normal';
});

// ========== 生命周期 ==========
onMounted(() => {
  loadCaptcha();
});

// ========== 核心方法 ==========

/**
 * 加载验证码（🔴 修复版：增加重试限制）
 */
async function loadCaptcha() {
  // 🔴 检查重试次数
  if (captchaRetryCount.value >= MAX_CAPTCHA_RETRY) {
    uni.showModal({
      title: '加载失败',
      content: '验证码服务异常，请稍后重试',
      showCancel: false
    });
    return;
  }
  
  try {
    isCaptchaLoading.value = true;
    const response = await getCaptcha();
    
    // 检查响应状态
    if (response.code !== 200) {
      throw new Error(response.message || '获取验证码失败');
    }
    
    // 手动解包
    const { captcha_id, image_base64 } = response.data;
    captchaId.value = captcha_id;
    captchaUrl.value = image_base64;
    
    // 🔴 成功后重置重试计数
    captchaRetryCount.value = 0;
  } catch (error) {
    captchaRetryCount.value++;
    
    if (captchaRetryCount.value < MAX_CAPTCHA_RETRY) {
      uni.showToast({
        title: `验证码加载失败(${captchaRetryCount.value}/${MAX_CAPTCHA_RETRY})`,
        icon: 'none'
      });
      // 2秒后自动重试
      setTimeout(() => {
        loadCaptcha();
      }, 2000);
    } else {
      uni.showToast({
        title: '验证码加载失败，请稍后重试',
        icon: 'none'
      });
    }
  } finally {
    isCaptchaLoading.value = false;
  }
}

/**
 * 刷新验证码
 */
function refreshCaptcha() {
  captchaCode.value = '';
  loadCaptcha();
}

/**
 * 表单验证
 */
function validateForm(): boolean {
  errors.value = {};
  
  if (!username.value.trim()) {
    errors.value.username = '请输入用户名、邮箱或手机号';
    return false;
  }
  
  if (!password.value) {
    errors.value.password = '请输入密码';
    return false;
  }
  
  if (password.value.length < 8) {
    errors.value.password = '密码至少8位';
    return false;
  }
  
  if (!captchaCode.value) {
    errors.value.captcha = '请输入验证码';
    return false;
  }
  
  if (captchaCode.value.length !== 4) {
    errors.value.captcha = '验证码为4位';
    return false;
  }
  
  return true;
}

/**
 * 处理登录（🔴 修复版：增加防抖+429处理）
 */
async function handleLogin() {
  // 🔴 防抖检查：防止重复点击
  if (isLoggingIn.value) {
    console.warn('登录请求进行中，忽略重复点击');
    return;
  }
  
  // 🔴 速率限制检查
  if (isLoginDisabled.value) {
    uni.showToast({
      title: '操作过于频繁，请稍后重试',
      icon: 'none'
    });
    return;
  }
  
  // 表单验证
  if (!validateForm()) {
    uni.vibrateShort();
    return;
  }
  
  try {
    isLoggingIn.value = true;  // 🔴 设置防抖标志
    isLoading.value = true;
    
    const loginData: LoginRequest = {
      username: username.value,
      password: password.value,
      captcha_id: captchaId.value,
      captcha_solution: captchaCode.value
    };
    
    await authStore.login(loginData);
    
    uni.showToast({
      title: '登录成功',
      icon: 'success',
      duration: 1500
    });
    
    setTimeout(() => {
      uni.switchTab({
        url: '/pages/app/tabbar/home/index'
      });
    }, 1500);
    
  } catch (error: any) {
    // 🔴 精细化错误处理
    if (error.code === 3001) {
      errors.value.password = '用户名或密码错误';
    } else if (error.code === 4003) {
      errors.value.captcha = '验证码错误或已过期';
      refreshCaptcha();  // 自动刷新验证码
    } else if (error.code === 4029 || error.statusCode === 429) {
      // 🔴 隐患修复4：速率限制处理
      uni.showToast({
        title: '操作过于频繁，请60秒后重试',
        icon: 'none',
        duration: 3000
      });
      isLoginDisabled.value = true;
      setTimeout(() => {
        isLoginDisabled.value = false;
      }, 60000);  // 60秒后恢复
    } else {
      uni.showToast({
        title: error.message || '登录失败，请重试',
        icon: 'none',
        duration: 2000
      });
      // 登录失败也刷新验证码（防止验证码被消费）
      refreshCaptcha();
    }
  } finally {
    isLoading.value = false;
    isLoggingIn.value = false;  // 🔴 重置防抖标志
  }
}

/**
 * 微信登录（占位功能）
 */
async function handleWechatLogin() {
  uni.showModal({
    title: '功能开发中',
    content: '微信登录功能将在后续版本中推出，敬请期待！当前阶段请使用账号密码登录。',
    showCancel: false,
    confirmText: '知道了'
  });
  // TODO: V2.0 集成Authing SDK实现微信登录
}

/**
 * Apple登录（占位功能）
 */
async function handleAppleLogin() {
  uni.showModal({
    title: '功能开发中',
    content: 'Apple登录功能将在后续版本中推出，敬请期待！当前阶段请使用账号密码登录。',
    showCancel: false,
    confirmText: '知道了'
  });
  // TODO: V2.0 集成Authing SDK实现Apple登录
}

/**
 * 跳转注册页面（占位功能）
 */
function handleGoToRegister() {
  uni.showModal({
    title: '功能开发中',
    content: '注册功能将在后续版本中推出，敬请期待！如需测试账号，请联系管理员。',
    showCancel: false,
    confirmText: '知道了'
  });
  // TODO: V2.0 创建注册页面
}

/**
 * 忘记密码（占位功能）
 */
function handleForgotPassword() {
  uni.showModal({
    title: '功能开发中',
    content: '密码重置功能将在后续版本中推出，敬请期待！如需重置密码，请联系管理员。',
    showCancel: false,
    confirmText: '知道了'
  });
  // TODO: V2.0 实现密码重置流程
}

// ... 其他辅助方法
</script>

<style lang="scss" scoped>
// ✅ V2.0简化版样式（蓝色渐变 + 白色卡片）
.login-container {
  min-height: 100vh;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
}

/* 欢迎区域（蓝色渐变背景） */
.welcome-section {
  background: linear-gradient(135deg, #1E90FF 0%, #4169E1 100%);
  padding: 60rpx 40rpx 70rpx 40rpx;
  color: #ffffff;
}

.welcome-text {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  line-height: 1.5;
  color: #ffffff;
}

/* 表单容器（白色卡片） */
.form-container {
  background: #ffffff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 48rpx 40rpx 48rpx 40rpx;
  margin-top: -20rpx;  /* 与欢迎区重叠 */
  flex: 1;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}

/* 输入框组（标签式设计） */
.input-group {
  margin-bottom: 28rpx;
}

.input-label {
  display: block;
  font-size: 28rpx;
  color: #333333;
  margin-bottom: 16rpx;
  font-weight: 500;
}

.input-field {
  width: 100%;
  height: 80rpx;
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #333333;
  border: 1rpx solid #e8e8e8;
  transition: all 0.3s ease;

  &:focus {
    background: #ffffff;
    border-color: #1E90FF;
  }

  &::placeholder {
    color: #aaaaaa;
  }
}

/* 登录按钮 */
.login-button {
  width: 100%;
  height: 80rpx;
  background: linear-gradient(135deg, #1E90FF 0%, #4169E1 100%);
  border-radius: 44rpx;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  margin-top: 32rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 8rpx 20rpx rgba(30, 144, 255, 0.3);
  transition: all 0.3s ease;

  &:active:not(.disabled) {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(30, 144, 255, 0.2);
  }

  &.disabled {
    background: #d9d9d9;
    box-shadow: none;
    color: #999999;
  }
}

// ... 其他样式
</style>
```

---

**5. 修改 src/pages.json**（添加登录页路由）

```json
// 在pages数组中添加：
{
  "path": "pages/app/auth/login",
  "style": {
    "navigationBarTitleText": "登录",
    "navigationStyle": "custom",
    "enablePullDownRefresh": false
  }
}
```

---

#### P1（第一阶段建议实现）

6. ✅ 完善SSO登录（handleWechatLogin/handleAppleLogin）
7. ✅ 添加注册页面入口（handleGoToRegister）
8. ✅ 添加忘记密码入口（handleForgotPassword）

#### P2（可选优化）

9. ⏳ 生物识别登录（指纹/面容ID）
10. ⏳ 页面进入/退出动画
11. ⏳ 登录失败抖动动画

---

## 第4章：关键技术规范

### 4.1 样式规范（V2.0简化版 - 当前实现）

```scss
// ✅ 当前使用的配色方案（简化蓝色系）
$welcome-bg-gradient: linear-gradient(135deg, #1E90FF 0%, #4169E1 100%); // 欢迎区蓝色渐变
$button-blue-gradient: linear-gradient(135deg, #1E90FF 0%, #4169E1 100%); // 登录按钮渐变
$error-color: #ff4d4f;
$warning-color: #fa8c16;
$text-primary: #333333;
$text-secondary: #666666;
$text-placeholder: #aaaaaa;
$border-color: #e8e8e8;
$bg-gray: #f7f8fa;

// ✅ 圆角规范
$border-radius-card: 32rpx;  // 表单容器上圆角
$border-radius-button: 44rpx; // 按钮全圆角
$border-radius-input: 12rpx;  // 输入框圆角

// ✅ 阴影规范
$shadow-card: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);  // 表单容器阴影
$shadow-button: 0 8rpx 20rpx rgba(30, 144, 255, 0.3); // 登录按钮阴影

// ✅ 间距规范
$welcome-padding: 60rpx 40rpx 70rpx 40rpx; // 欢迎区内边距
$form-padding: 48rpx 40rpx; // 表单容器内边距
$input-gap: 28rpx;  // 输入框间距
$button-margin-top: 32rpx; // 登录按钮上边距
```

### 4.2 安全规范

```typescript
// ✅ 正确的Token存储
uni.setStorageSync('jwt_token', accessToken);
uni.setStorageSync('refresh_token', refreshToken);

// ❌ 禁止存储密码
// uni.setStorageSync('password', password); // 严格禁止！

// ✅ Token检查
function checkTokenExpiry(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp > currentTime;
  } catch {
    return false;
  }
}
```

### 4.3 错误处理规范

```typescript
// 所有API调用必须try-catch
try {
  const result = await authStore.login(loginData);
  // 成功处理
} catch (error: any) {
  // 根据错误码分类处理
  if (error.code === 3001) {
    errors.value.password = '用户名或密码错误';
  } else if (error.code === 4003) {
    errors.value.captcha = '验证码错误或已过期';
    refreshCaptcha();
  } else {
    uni.showToast({
      title: error.message || '操作失败，请重试',
      icon: 'none'
    });
  }
}
```

### 4.4 表单验证规范

```typescript
// 实时验证 vs 提交时验证
// ✅ 推荐：提交时统一验证，实时清除错误
function validateForm(): boolean {
  errors.value = {};
  
  if (!username.value.trim()) {
    errors.value.username = '请输入用户名、邮箱或手机号';
    return false;
  }
  
  // ... 其他验证
  
  return true;
}

// 实时清除错误
function handleFocus(field: string) {
  focusedField.value = field;
  delete errors.value[field]; // 聚焦时清除该字段的错误
}
```

### 4.5 可访问性规范

```vue
<!-- aria标签 -->
<input
  type="text"
  placeholder="用户名/邮箱/手机号"
  aria-label="用户名输入框"
  aria-required="true"
  :aria-invalid="!!errors.username"
/>

<!-- 错误提示关联 -->
<view v-if="errors.username" role="alert" class="error-tip">
  {{ errors.username }}
</view>
```

---

## 第5章：生成流程

### 5.1 执行顺序（严格按照）

1. ✅ **读取文件** → 第0章的文件清单
2. ✅ **输出分析** → 在聊天窗口展示现状
3. ✅ **等待确认** → 用户输入"确认继续"
4. ✅ **生成类型** → src/types/auth.ts
5. ✅ **生成API** → src/api/auth.ts
6. ✅ **扩展Store** → src/store/auth.ts（检查后补充）
7. ✅ **生成页面** → src/pages/app/auth/login.vue
8. ✅ **修改路由** → src/pages.json
9. ✅ **验证测试** → 提供测试步骤

### 5.2 代码质量要求

- ✅ TypeScript严格模式（无any类型）
- ✅ 完整的JSDoc注释
- ✅ 错误处理覆盖所有API调用
- ✅ 加载状态反馈
- ✅ 响应式布局（适配不同屏幕）
- ✅ 无障碍支持（aria标签）

---

## 第6章：验收标准

生成完成后，提供以下测试清单：

### 6.1 功能测试

- [ ] 验证码图片正常显示，点击刷新
- [ ] 输入用户名/密码，表单验证生效
- [ ] 登录成功后跳转首页，Token存储成功
- [ ] 登录失败显示错误提示，验证码自动刷新
- [ ] 密码显示/隐藏切换正常
- [ ] 忘记密码入口可点击
- [ ] 注册入口可点击

### 6.2 样式测试

- [ ] 页面背景渐变与callback.vue一致
- [ ] 登录按钮渐变与my/index.vue用户卡片一致
- [ ] 输入框阴影效果正常
- [ ] 左右padding为32rpx
- [ ] 圆角为16rpx
- [ ] 字号符合规范（24/26/28/32rpx）

### 6.3 安全测试

- [ ] Token存储在uni.setStorageSync
- [ ] Refresh Token正确存储
- [ ] 密码不存储在本地
- [ ] 验证码3分钟过期
- [ ] Token自动注入到请求头

### 6.4 体验测试

- [ ] 页面进入动画流畅
- [ ] 输入框聚焦有视觉反馈
- [ ] 登录按钮有加载状态
- [ ] 错误提示清晰友好
- [ ] 支持键盘Enter切换焦点

### 6.5 性能测试

- [ ] 页面加载时间 < 1秒
- [ ] 验证码加载时间 < 500ms
- [ ] 登录API响应时间 < 2秒
- [ ] 内存占用 < 50MB
- [ ] 页面进入动画帧率 ≥ 30fps

---

## 第7章：性能监控与调试

### 7.1 性能监控指标

**在login.vue中添加性能埋点：**

```typescript
interface PerformanceMetrics {
  pageLoadTime: number;        // 页面加载时间
  captchaLoadTime: number;     // 验证码加载时间
  loginApiTime: number;        // 登录API耗时
  firstInputDelay: number;     // 首次输入延迟
  memoryUsage: number;         // 内存占用
}

const metrics = ref<PerformanceMetrics>({
  pageLoadTime: 0,
  captchaLoadTime: 0,
  loginApiTime: 0,
  firstInputDelay: 0,
  memoryUsage: 0
});

// 页面加载性能监控
onMounted(() => {
  const startTime = performance.now();
  
  nextTick(() => {
    metrics.value.pageLoadTime = performance.now() - startTime;
    console.log('📊 页面加载时间:', metrics.value.pageLoadTime + 'ms');
    
    // 上报性能数据（可选）
    if (metrics.value.pageLoadTime > 1000) {
      console.warn('⚠️ 页面加载超过1秒，需优化');
    }
  });
});

// 验证码加载监控
async function loadCaptcha() {
  const startTime = performance.now();
  try {
    isCaptchaLoading.value = true;
    const result = await getCaptcha();
    captchaId.value = result.captcha_id;
    captchaUrl.value = result.image_base64;
    
    metrics.value.captchaLoadTime = performance.now() - startTime;
    console.log('📊 验证码加载时间:', metrics.value.captchaLoadTime + 'ms');
  } catch (error) {
    uni.showToast({ title: '验证码加载失败', icon: 'none' });
  } finally {
    isCaptchaLoading.value = false;
  }
}

// 登录API监控
async function handleLogin() {
  const startTime = performance.now();
  try {
    isLoading.value = true;
    await authStore.login(loginData);
    
    metrics.value.loginApiTime = performance.now() - startTime;
    console.log('📊 登录API耗时:', metrics.value.loginApiTime + 'ms');
    
    // 成功处理...
  } catch (error) {
    // 错误处理...
  } finally {
    isLoading.value = false;
  }
}
```

### 7.2 内存泄漏防护

```typescript
// 组件卸载时清理定时器
const timers: number[] = [];

const setTimeoutSafe = (callback: () => void, delay: number) => {
  const timer = setTimeout(callback, delay);
  timers.push(timer);
  return timer;
};

onBeforeUnmount(() => {
  // 清理所有定时器
  timers.forEach(timer => clearTimeout(timer));
  timers.length = 0;
  
  // 清理事件监听
  uni.offNetworkStatusChange();
  uni.offKeyboardHeightChange();
  
  console.log('🧹 登录页面已清理资源');
});
```

### 7.3 调试策略

#### 7.3.1 开发环境调试

```bash
# 1. 浏览器调试（H5模式）
npm run dev:h5
# 打开 http://localhost:5173
# 使用Chrome DevTools调试

# 2. 真机调试（App模式）
# HBuilderX → 运行 → 运行到手机或模拟器 → Android/iOS
# 打开HBuilderX控制台查看日志

# 3. 小程序调试
npm run dev:mp-weixin
# 微信开发者工具 → 调试 → 控制台
```

#### 7.3.2 生产环境调试

```typescript
// 生产环境错误收集（集成Sentry）
import * as Sentry from '@sentry/vue';

// main.ts中初始化
if (import.meta.env.PROD) {
  Sentry.init({
    app,
    dsn: 'YOUR_SENTRY_DSN',
    environment: import.meta.env.MODE,
    beforeSend(event, hint) {
      // 脱敏处理
      if (event.request?.data) {
        delete event.request.data.password;
      }
      return event;
    }
  });
}
```

#### 7.3.3 常见问题排查清单

| 问题 | 排查步骤 | 解决方案 |
|------|---------|----------|
| 验证码不显示 | 1. 检查网络请求 2. 查看Base64格式 | 使用`<image>`标签的`:src`属性 |
| 登录无响应 | 1. 检查authStore.login方法 2. 查看控制台错误 | try-catch捕获异常 |
| Token丢失 | 1. 检查uni.setStorageSync调用 2. 查看Application/Storage | 确认key为'jwt_token' |
| 自动登录失败 | 1. 检查initializeAuth逻辑 2. 验证Token过期时间 | 使用checkTokenExpiry检查有效期 |
| 第三方登录失败 | 1. 检查Authing配置 2. 查看id_token获取 | 参考Q3完整实现 |

---

## 第8章：进阶优化（可选）

### 8.1 页面动画

```scss
.login-page {
  animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### 8.2 登录失败抖动

```scss
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8rpx); }
  75% { transform: translateX(8rpx); }
}

.input-wrapper.error {
  animation: shake 0.3s;
}
```

### 8.3 键盘弹出适配

```typescript
onMounted(() => {
  uni.onKeyboardHeightChange((res) => {
    if (res.height > 0) {
      // 键盘弹出，调整滚动位置
      const query = uni.createSelectorQuery();
      query.select('.login-button').boundingClientRect();
      query.exec((result) => {
        const buttonRect = result[0];
        const windowHeight = uni.getSystemInfoSync().windowHeight;
        
        if (buttonRect.bottom > windowHeight - res.height) {
          uni.pageScrollTo({
            scrollTop: buttonRect.bottom - windowHeight + res.height + 100,
            duration: 300
          });
        }
      });
    }
  });
});
```

---

## 总结

本提示词提供了完整的登录页面生成指南，包含以下关键内容：

### 当前阶段实现范围总结

#### ✅ P0核心功能（完整实现）

1. **账号密码登录**：支持用户名/邮箱/手机号，完整的表单验证和错误处理
2. **图形验证码**：自动加载、点击刷新、登录失败自动刷新（一次性消费机制）
3. **Token管理**：Access Token（15分钟）+ Refresh Token（7天）+ 自动刷新
4. **用户信息获取**：登录成功后自动获取并存储用户信息
5. **安全性保证**：Token持久化存储、不存储密码、敏感信息脱敏

#### 🔵 P1占位功能（仅UI占位）

6. **第三方登录**：仅显示微信/Apple按钮，点击显示Toast"功能开发中，敬请期待"
7. **忘记密码**：仅显示链接，点击显示Toast"功能开发中，敬请期待"
8. **注册入口**：仅显示链接，点击显示Toast"功能开发中，敬请期待"

#### ❌ 明确不实现的功能

9. **跨应用登录**：App端不需要，不实现external_callback等参数
10. **OTP验证码**：登录场景不需要，注册时再实现
11. **生物识别**：V2.0优化功能

### 关键技术决策

**核心原则**：
- 🔒 使用uni.setStorageSync存储Token（方案B）
- ✅ 实现7天自动登录（Refresh Token）
- ✅ 实现图形验证码（防止暴力破解）
- ❌ 不实现记住密码（安全风险）
- ❌ 不实现OTP验证码（登录不需要，注册时实现）
- ❌ 不实现跨应用登录（App端独立登录）
- 🔵 第三方登录占位（不集成Authing SDK，后续迭代补充）
- 🔵 密码重置占位（不实现完整流程，后续优化补充）
- 🎨 样式与my/index.vue、callback.vue保持一致
- ✅ **API响应格式**：使用手动解包模式（`ApiResponse<T>`），与现有所有API保持100%一致

**实现优先级说明**：

为什么第三方登录和密码重置只做占位？

- 🎯 **当前目标**：快速实现核心登录功能，验证评论、收藏等其他页面的功能实现
- ⏱️ **时间成本**：Authing SDK集成需要2-4小时，密码重置流程需要3-5小时
- ✅ **不影响核心流程**：用户可以通过账号密码登录，获取Token后访问所有需要登录的功能
- 🔄 **渐进式开发**：先完成MVP（最小可行产品），后续迭代时补充完整功能

---

**开始生成前，请务必执行第0章的强制检查流程！**

---

## 🎯 执行指令（Execution Instructions）

**AI，现在请严格按照以下流程生成登录页面代码：**

### 执行流程

#### 第1步：强制性前置检查（必须先执行）
```
1. 读取9个核心文件（auth.ts、request.ts、my/index.vue等）
2. 扫描5个目录（src/api/、src/types/等）
3. 在聊天窗口输出6张分析表格：
   - 表1：可直接复用的文件（✅ 直接使用）
   - 表2：需要扩展的文件（🔧 需要补充）
   - 表3：需要新建的文件（➕ 需新建）
   - 表4：样式参考来源（📐 复用规范）
   - 表5：技术决策确认（🔒 强制规范）
   - 表6：安全性分析（⚠️ 风险评估）
4. 等待用户确认（输入"确认继续"）
```确认使用手动解包模式
```typescript
// ✅ 确认：当前项目所有API使用手动解包模式
// src/api/room.ts 示例：
export const getRoomList = (): Promise<ApiResponse<PaginatedResponse<Room>>> => {
  return get<ApiResponse<PaginatedResponse<Room>>>('/rooms', params);
};

// 调用时需手动解包
const response = await getRoomList();
const rooms = response.data.items;  // ← 手动 .data 解包

// ✅ LoginPage的API也采用相同格式
// src/api/auth.ts 示例：
export const login = (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  return post<ApiResponse<LoginResponse>>('/auth/login', data);
};

// 调用时同样手动解包
const response = await login(data);
const token = response.data.access_token;  // ← 手动 .data 解包f (response.code === 200 || response.code === 201) {
  resolve(response.data as T);  // ✅ 自动解包
}
```

#### 第3步：生成类型定义文件
```bash
创建 src/types/auth.ts（80行）
- LoginRequest、LoginResponse、CaptchaResponse
- UserInfo、RefreshTokenRequest、SSOLoginRequest
- PasswordResetRequest、PasswordResetExecute
```

#### 第4步：生成API接口文件
```bash
创建 src/api/auth.ts（150行）
- getCaptcha()、login()、refreshToken()
- getCurrentUser()、logout()、ssoLogin()
- requestPasswordReset()、resetPassword()
```

#### 第5步：扩展认证Store
```bash
修改 src/store/auth.ts（使用replace_string_in_file）
- 在actions中补充 login() 方法
- 在actions中补充 refreshAccessToken() 方法
- 在actions中补充 fetchUserProfile() 方法
- 增强 initializeAuth() 支持Refresh Token自动登录
```

#### 第6步：生成登录页面
```bash
创建 src/pages/app/auth/login.vue（600行）
- 完整的template（Logo区、表单区、第三方登录）
- 完整的script setup（表单验证、登录逻辑、错误处理）
- 完整的style scoped（参考my/index.vue样式）
```

#### 第7步：修改路由配置
```bash
修改 src/pages.json（使用replace_string_in_file）
- 在pages数组中添加登录页路由
- 配置navigationStyle为custom（自定义导航栏）
```

#### 第8步：输出验收清单
```bash
在聊天窗口输出完整的测试清单：
- 功能测试（7项）
- 样式测试（6项）
- 安全测试（5项）
- 体验测试（4项）
- 性能测试（5项）
```

#### 第9步：提供启动命令
```bash
# 开发环境（使用真实API）
npm run dev:h5
# 访问 http://localhost:5173

# 真机调试
# HBuilderX → 运行 → 运行到手机或模拟器 → Android/iOS
```

### 关键提醒

✅ **代码质量保证**
- 所有文件使用TypeScript严格模式（无any）
- 所有函数包含完整JSDoc注释
- 所有API调用包含try-catch错误处理
- 所有UI状态包含加载/错误/成功反馈

✅ **样式100%一致**
- 背景渐变：`linear-gradient(135deg, #667EEA 0%, #764BA2 100%)`
- 按钮渐变：`linear-gradient(135deg, #509CEC 0%, #3B7DD8 100%)`
- 左右padding：`32rpx`
- 圆角：`16rpx`
- 阴影：`0 2rpx 8rpx rgba(0, 0, 0, 0.06)`

✅ **安全性保证**
- Token存储使用 `uni.setStorageSync`（App沙盒加密）
- 禁止存储密码（任何形式）
- 验证码3分钟过期，60秒内最多请求5次
- 所有敏感信息脱敏（日志、错误上报）

✅ **可运行性保证**
- 所有import路径使用绝对路径（@/开头）
- 所有组件已注册或按需引入
- 所有类型已定义或导入
- 所有API接口已实现或Mock

---

**[LoginPage页面代码生成提示词文档 - V1.1 - 完成]**
