import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import { resolve } from 'path'

// 开发环境专用配置
export default defineConfig({
  plugins: [uni()],
  
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@/components': resolve(__dirname, 'src/components'),
      '@/pages': resolve(__dirname, 'src/pages'),
      '@/static': resolve(__dirname, 'src/static'),
      '@/utils': resolve(__dirname, 'src/utils'),
      '@/api': resolve(__dirname, 'src/api'),
      '@/store': resolve(__dirname, 'src/store'),
      '@/types': resolve(__dirname, 'src/types'),
      '@/common': resolve(__dirname, 'src/common')
    }
  },
  
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/common/uni.scss" as *;\n`
      }
    },
    devSourcemap: true
  },
  
  define: {
    'process.env.NODE_ENV': '"development"',
    'process.env.UNI_PLATFORM': '"mp-weixin"',
    '__DEV__': true
  },
  
  server: {
    port: 3000,
    open: false,
    host: '0.0.0.0',
    hmr: true
  },
  
  build: {
    target: 'es6',
    outDir: 'dist/dev',
    assetsDir: 'static',
    sourcemap: 'inline', // 内联sourcemap，便于调试
    minify: false, // 开发模式下不压缩
    rollupOptions: {
      output: {
        format: 'es', // 使用ES模块格式，便于调试
        preserveModules: true, // 保持模块结构
        preserveModulesRoot: 'src' // 保持src目录结构
      }
    }
  },
  
  optimizeDeps: {
    include: [
      'vue',
      'pinia',
      'dayjs',
      'lodash-es'
    ]
  },
  
  // 开发调试配置
  esbuild: {
    drop: [], // 不删除任何调试信息
    keepNames: true // 保持函数和类名
  }
})
