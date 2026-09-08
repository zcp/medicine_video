/// <reference types="vitest" />
import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";
import path from "path";

// 根据环境设置不同的 base 路径
const isProduction = process.env.NODE_ENV === 'production';
const base = isProduction ? '/live-center/' : '/';

// https://vitejs.dev/config/
export default defineConfig({
  base: base,  // 添加这行
  server: {
	port: 5173,
    proxy: {
      '/api': {
        target: 'http://124.220.235.226:8000',
        changeOrigin: true,
      },
      // 添加HLS流代理
      '/hls-proxy': {
        target: 'https://124.220.235.226',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/hls-proxy/, '/hls'),
        secure: false, // 忽略SSL证书验证
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // 添加CORS头
            proxyReq.setHeader('Access-Control-Allow-Origin', '*');
            proxyReq.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
            proxyReq.setHeader('Access-Control-Allow-Headers', 'Range, Content-Type');
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 添加CORS响应头
            proxyRes.headers['Access-Control-Allow-Origin'] = '*';
            proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS';
            proxyRes.headers['Access-Control-Allow-Headers'] = 'Range, Content-Type';
            proxyRes.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range';
          });
        }
      }
    },
    // 确保静态文件能够正确访问
    fs: {
      allow: ['..']
    }
  },
    // 添加环境变量定义
    define: {
      'process.env': {},
    },
  plugins: [
    uni(),
  ],
  test: {
    environment: 'jsdom',
    deps: {
      // Force Vitest to transform uni-ui, as it's not published as standard ESM.
      inline: [/@dcloudio\/uni-ui/],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      // Add an alias to hijack the problematic component and replace it with an empty one.
      "@dcloudio/uni-ui/lib/uni-datetime-picker/uni-datetime-picker.vue": path.resolve(__dirname, "tests/EmptyComponent.vue"),
      // 注意：不要把 @vue/* 映射到 vue/*，否则会触发
      // "Missing \"./runtime-dom\" specifier in \"vue\" package" 错误。
      // 让 bundler 直接解析官方包的子入口即可。
    },
  },
  // 确保环境变量能被正确加载
  // 排除 hls.js 在非 H5 环境中的打包
  build: {
    rollupOptions: {
      external: (id) => {
        // 在非 H5 环境中排除 hls.js
        if (process.env.UNI_PLATFORM !== 'h5' && id.includes('hls.js')) {
          return true;
        }
        return false;
      },
       // 添加复制插件
      plugins: [
        // 注意：env.prod.js 已废弃，改用 .env.production 文件管理环境变量
        {
          name: 'copy-public-files',
          generateBundle() {
            const fs = require('fs');
            const files = ['public/hls-player.html', 'public/simple-callback.html'] as const;
            const names = ['hls-player.html', 'simple-callback.html'] as const;
            files.forEach((path, i) => {
              if (fs.existsSync(path)) {
                this.emitFile({ type: 'asset', fileName: names[i], source: fs.readFileSync(path, 'utf8') });
              }
            });
          }
        }
      ]
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 注意：uni.scss 使用 CSS 变量，不需要全局注入
        // 已在 main.ts 中导入，避免循环引用
        // 只对依赖静默警告（Dart Sass 选项）
        quietDeps: true,
        // 精准静默本次出现的三类弃用
        silenceDeprecations: ['legacy-js-api', 'global-builtin', 'color-functions', 'import'],
      },
    },
  },
});
