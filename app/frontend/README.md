# Live Streaming SaaS - Frontend

This is the frontend for the Live Streaming SaaS platform, built with uni-app, Vue 3, TypeScript, and Vite.

## Project Setup

### Prerequisites

- [Node.js](https://nodejs.org/) (version 18.x or higher recommended)
- [pnpm](https://pnpm.io/) (or npm/yarn)

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    ```
2.  Navigate to the project directory:
    ```bash
    cd frontend_live
    ```
3.  Install dependencies:
    ```bash
    pnpm install
    ```

## Development

### Running the development server

-   **H5:**
    ```bash
    pnpm dev:h5
    ```
-   **WeChat Mini Program:**
    ```bash
    pnpm dev:mp-weixin
    ```

Open [HBuilderX](https://www.dcloud.io/hbuilderx.html) to run the application on a real device or simulator.

## Building for Production

-   **H5:**
    ```bash
    pnpm build:h5
    ```
-   **WeChat Mini Program:**
    ```bash
    pnpm build:mp-weixin
    ```

The production-ready files will be located in the `dist/` directory.

## Linting and Formatting

-   **Lint files:**
    ```bash
    pnpm lint
    ```
-   **Format files:**
    ```bash
    pnpm format
    ```

## Testing

-   **Run unit tests:**
    ```bash
    pnpm test
    ```

## Project Structure

```
frontend_live/
├── src/
│   ├── api/          # API request modules
│   ├── assets/       # Static assets (images, fonts, etc.)
│   ├── components/   # Reusable Vue components
│   ├── pages/        # Application pages
│   ├── store/        # Pinia state management
│   ├── types/        # TypeScript type definitions
│   └── utils/        # Utility functions
├── tests/            # Test files
└── ...               # Configuration files
```

## App Packaging & LivePlayer Playback Module

App 端播放 external m3u8 直播流的目标方案是 `<live-player>` 组件（LivePlayer 原生模块，直播 HLS 兼容性优于 uni `<video>`）。启用前必须完成「自定义基座打包验证」：

- 模块开关：`src/manifest.json` → `app-plus.modules.LivePlayer`
- 使用组件：`src/pages/app/live/LiveView.vue`（当前因标准基座渲染不稳定已降级为 `<video>`/VideoPlayerApp，待自定义基座验证后重新启用）

完整的背景、概念讲解（标准基座 vs 自定义基座）、前置要求、自定义基座创建与真机验证操作流程、代码改动建议及踩坑清单，请阅读后端主仓库文档：

> `D:\live-streaming-saas-v2-main\app修改记录\LivePlayer模块与自定义基座打包验证_讲解与操作文档.md`

相关文件索引：

| 文件 | 说明 |
|---|---|
| `src/manifest.json` | App 模块配置（LivePlayer/VideoPlayer/LivePusher 等）及 Android/iOS 打包配置 |
| `src/pages/app/live/LiveView.vue` | 播放组件使用处（播放源分流、live-player/video 切换） |
| `src/components/app/VideoPlayerApp.vue` | 当前播放组件（uni video + ShadowParser 观看上报） |
| `src/hybrid/html/network_security_config.xml` | Android 明文流量（http）策略 |
| `.env.development.local` / `.env.production` | 后端 API 地址（影响播放代理 URL 是 http 还是 https） |

## Contributing

Please follow the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for commit messages. 