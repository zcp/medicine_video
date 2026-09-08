# 直播 SaaS 微信小程序前端

uni-app + Vue 3 + TypeScript 的医学直播 SaaS **微信小程序前端**（观众端与管理端页面同仓）。

## 技术栈

- 框架：uni-app（Vue 3 + Composition API + TypeScript）
- UI：uni-ui
- 状态：Pinia + 持久化插件
- 构建：Vite
- 测试：Vitest
- 其它：Day.js、Lodash-es、@vueuse/core

## 环境要求

- Node.js >= 16
- npm >= 7

## 快速开始

```bash
npm install

# 微信小程序开发
npm run dev:mp-weixin

# H5 开发
npm run dev:h5

# 微信小程序生产构建
npm run build:mp-weixin

# 测试（一次性）
npm run test:run
```

其它常用脚本：`lint`、`format`、`check:types`、`dev:debug`、`build:h5`（见根目录 `package.json`）。

微信开发者工具请打开构建产物目录（开发一般为 `dist/dev/mp-weixin/`，以本地构建输出为准）。

## 环境变量

| 文件 | 用途 |
|------|------|
| `.env.development` | 本地开发（已在 `.gitignore`，勿提交） |
| `.env.production` | 生产构建用网关地址等 |

常用变量（只列名，按环境自行填写）：

| 变量 | 含义 |
|------|------|
| `VITE_BASE_API_URL` | Live Core 网关 base（如 `/api/core`） |
| `VITE_AUTH_API_URL` | 用户服务网关 base（如 `/api/users`） |
| `VITE_API_PATH_PREFIX` | 路径前缀（多数情况可为空） |
| `VITE_LOGIN_URL` | 登录页 URL |
| `VITE_MEDIA_BASE_URL` | 媒体资源 base（开发常用） |

真机调试时请使用本机局域网地址，不要把个人 IP 写进仓库。

## 微信 AppID

在 `src/manifest.json` 的 `mp-weixin.appid` 与根目录 `project.config.json` 的 `appid` 填写你的小程序 AppID。个人 AppID / AppSecret 勿提交仓库。

## 目录速览

```
src/
  api/          # 接口
  pages/        # 页面（含 admin）
  store/        # Pinia
  types/        # 类型契约
  components/   # 公共组件
  config/       # API 与配置
  utils/        # 工具
docs/           # 设计文档与规范
test/           # Vitest
```

## 文档入口

- 业务与契约：[`docs/`](docs/)
- AI / 协作习惯：[`docs/AI-工作约定.md`](docs/AI-工作约定.md)
- 前端写法样本：[`docs/前端规范样本/`](docs/前端规范样本/)

## 敏感信息（勿提交）

以下已在 `.gitignore` 或应仅留本机：

- `docs/测试账号信息.md`（本地自备测试账号，勿提交密码）
- `.env.development`、`.env.local`、`.env.*.local`
- `generate-jwt.js`（本地联调脚本）

测试账号请本地维护；仓库内文档若引用测试账号，只写角色/用户名，不写真实密码。
