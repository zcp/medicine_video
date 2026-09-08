import { defineConfig, type Plugin } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import { resolve } from 'path'
import { writeFileSync, readFileSync, existsSync } from 'fs'

const CONSOLE_PATCH_MARKER = '/* __live_saas_console_patch__ */'
const CONSOLE_PATCH = `${CONSOLE_PATCH_MARKER}
(function(){try{
  var g=typeof globalThis!=='undefined'?globalThis:typeof wx!=='undefined'?wx:{};
  if(g.__liveSaasConsolePatched)return;
  g.__liveSaasConsolePatched=true;
  function t(v){
    if(v==null)return String(v);
    var ty=typeof v;
    if(ty==='string'||ty==='number'||ty==='boolean')return String(v);
    if(ty==='symbol')return v.toString();
    if(ty==='function')return '[Function]';
    if(v instanceof Error)return v.name+': '+v.message;
    if(Array.isArray(v)){if(!v.length)return'';try{return JSON.stringify(v)}catch(e){return'[Array('+v.length+')]'}}
    try{return JSON.stringify(v)}catch(e){
      try{var ks=Object.keys(v).slice(0,8);return ks.length?'{'+ks.join(',')+'}':''}catch(e2){return''}
    }
  }
  function drop(s){return!s||s==='[object Object]'||/^\\[\\]\\s*(\\[object Object\\])?$/.test(s)}
  ;['log','info','warn','error','debug'].forEach(function(m){
    var o=console[m].bind(console);
    console[m]=function(){
      var a=[].slice.call(arguments).map(t).map(function(x){return String(x).trim()}).filter(Boolean).join(' ');
      if(drop(a))return;
      o(a);
    };
  });
}catch(e){}})();
`

/** 把控制台补丁写到 mp-weixin 最先执行的 vendor.js / app.js 顶部 */
function mpConsolePatchPlugin(): Plugin {
  const targets = () =>
    [resolve(__dirname, 'dist/dev/mp-weixin'), resolve(__dirname, 'dist/build/mp-weixin')].flatMap((root) => [
      resolve(root, 'common/vendor.js'),
      resolve(root, 'app.js')
    ])

  const injectFile = (filePath: string) => {
    if (!existsSync(filePath)) return
    const code = readFileSync(filePath, 'utf8')
    if (code.includes(CONSOLE_PATCH_MARKER)) return
    writeFileSync(filePath, CONSOLE_PATCH + '\n' + code, 'utf8')
  }

  const injectAll = () => {
    for (const file of targets()) injectFile(file)
  }

  return {
    name: 'mp-console-patch',
    apply: 'build',
    enforce: 'post',
    writeBundle() {
      injectAll()
      // uni 可能在 hook 之后再次覆写产物，短延迟再补一次
      setTimeout(injectAll, 100)
      setTimeout(injectAll, 500)
      setTimeout(injectAll, 1500)
    },
    closeBundle() {
      injectAll()
    }
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    uni({
      vueOptions: {
        template: {
          compilerOptions: {
            preserveWhitespace: true
          }
        }
      }
    }),
    mpConsolePatchPlugin()
  ],
  
  resolve: {
    // 优先 .ts，避免曾存在的同名 .js（如 store/ui.js）抢解析或缓存指向已删除文件
    extensions: ['.ts', '.tsx', '.vue', '.mjs', '.js', '.jsx', '.json'],
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
        // 须以换行结尾，避免与页面首条规则粘连；页面内勿再 @import 同一 uni.scss
        additionalData: `@use "@/common/uni.scss" as *;\n`
      }
    }
  },
  
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
    'process.env.UNI_PLATFORM': JSON.stringify(process.env.UNI_PLATFORM)
  },
  
  server: {
    port: 3000,
    open: false,
    host: '0.0.0.0',
    hmr: true
  },
  
  build: {
    target: 'es6',
    outDir: 'dist',
    assetsDir: 'static',
    sourcemap: true,
    minify: process.env.NODE_ENV === 'production' ? 'terser' : false,
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: process.env.NODE_ENV === 'production'
      }
    },
    rollupOptions: {
      external: process.env.NODE_ENV === 'development' ? [] : undefined,
      output: {
        chunkFileNames: 'static/js/[name]-[hash].js',
        entryFileNames: 'static/js/[name]-[hash].js',
        assetFileNames: 'static/[ext]/[name]-[hash].[ext]'
      }
    }
  },
  
  optimizeDeps: {
    include: [
      // 'vue',
      // 'pinia',
      'dayjs',
      'lodash-es'
    ]
  }
})
