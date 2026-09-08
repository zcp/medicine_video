import { createSSRApp } from "vue";
import * as Pinia from "pinia";
import App from "./App.vue";
import '@/common/uni.scss'
import logger from './utils/logger';
import { vPermission } from './directives/permission';

// #ifdef H5
// 仅 H5 平台注册 Element Plus（减少 App/小程序 包体积）
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
// #endif

export function createApp() {
  const app = createSSRApp(App);
  const pinia = Pinia.createPinia();
  app.use(pinia);

  // 全局注册权限指令（所有平台）
  app.directive('permission', vPermission);

  // #ifdef H5
  app.use(ElementPlus);
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
  }
  // #endif
  
  // 零阶段：初始化日志系统
  logger.initialize().then(() => {
    logger.info('App', '应用启动', {
      version: import.meta.env.VITE_APP_VERSION,
      env: import.meta.env.MODE
    });
  }).catch((error) => {
    console.error('[Main] 日志系统初始化失败:', error);
  });
  
  // 认证状态由首页 onMounted 统一初始化（避免与 home/index.vue 重复调用）
  // const authStore = useAuthStore();
  // authStore.initializeAuth();
  
  return {
    app,
    Pinia,
  };
} 
