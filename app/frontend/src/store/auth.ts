import { defineStore } from 'pinia';
import { LOGIN_URL, FRONTEND_USER_URL, APP_BASE_PATH, AUTH_REDIRECT_PATH } from '@/constants/api';
import { APP_LOGIN_PATH, APP_HOME_PATH, APP_MY_PATH, APP_MY_LIVE_PATH, APP_EXPERT_PATH } from '@/constants/routes';
import { login as loginApi, refreshToken as refreshTokenApi, getCurrentUser, logout as logoutApi } from '@/api/auth';
import type { LoginRequest, UserInfo } from '@/types/auth';
import { jwtDecode } from 'jwt-decode';
import { useFavoriteStore } from './favorite';
import { useFollowStore } from './follow';
import { resolveMediaUrl } from '@/utils/url';

// 认证工具函数
export const getToken = (): string | null => {
  return uni.getStorageSync('jwt_token') || null;
};

const setToken = (token: string): void => {
  uni.setStorageSync('jwt_token', token);
};

const clearToken = (): void => {
  uni.removeStorageSync('jwt_token');
  uni.removeStorageSync('loginRedirectPath');
};

const checkTokenExpiry = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    const currentTime = Date.now() / 1000;
    return payload.exp > currentTime;
  } catch {
    return false;
  }
};

const parseUserFromToken = (token: string): User | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return {
      user_id: payload.user_id || payload.sub,
      username: payload.username,
      email: payload.email,
      role: payload.role || undefined,
      can_stream: payload.can_stream
    };
  } catch (error) {
    console.error('解析Token失败:', error);
    return null;
  }
};

const setRedirectPath = (path: string): void => {
  uni.setStorageSync('loginRedirectPath', path);
};

const getRedirectPath = (): string | null => {
  return uni.getStorageSync('loginRedirectPath') || null;
};

const clearRedirectPath = (): void => {
  uni.removeStorageSync('loginRedirectPath');
};

// 类型定义
export interface User {
  user_id: string;
  username?: string;
  email?: string;
  phone_number?: string;
  is_phone_verified?: boolean;
  has_password?: boolean;
  avatar?: string;
  nickname?: string;
  bio?: string;
  role?: string;
  status?: string;
  can_stream?: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  tokenExpiry: number | null;
  redirectPath: string | null;
  loginBannerDismissed: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
    isAuthenticated: false,
    tokenExpiry: null,
    redirectPath: null,
    loginBannerDismissed: false
  }),

  getters: {
    isTokenValid: (state) => {
      if (!state.token) return false;
      return checkTokenExpiry(state.token);
    },
    userRole: (state): string | null => {
      return state.user?.role || null;
    },
    isAdmin: (state): boolean => {
      const role = state.user?.role;
      return role === 'ADMIN' || role === 'SUPERADMIN';
    },
    isSuperAdmin: (state): boolean => {
      return state.user?.role === 'SUPERADMIN';
    }
  },

  actions: {
    /**
     * 用户登录
     * @param data 登录信息（用户名/密码/验证码）
     */
    async login(data: LoginRequest): Promise<void> {
      try {
        console.log('🔐 [Store] 调用登录API...');
        const response = await loginApi(data);
        console.log('📥 [Store] 登录API响应:', { code: response.code, message: response.message });
        
        const { access_token, refresh_token } = response.data;
        console.log('🔑 [Store] 获取到Token:', { 
          access_token_length: access_token.length,
          refresh_token: refresh_token ? '存在' : '不存在' 
        });
        
        // 🔴 P0必须存储refresh_token！
        this.setToken(access_token);
        uni.setStorageSync('refresh_token', refresh_token);
        console.log('💾 [Store] Token已保存到Storage');
        
        // 解析token中的用户信息
        this.parseUserFromToken(access_token);
        console.log('👤 [Store] Token解析完成，用户ID:', this.user?.user_id ? '***' + this.user.user_id.substring(this.user.user_id.length - 4) : 'null');
        
        // 获取完整用户信息
        console.log('🔄 [Store] 准备获取用户详细信息...');
        await this.fetchUserProfile();
        console.log('👤 [Store] 用户信息获取完成:', this.user?.username);
        
        // 加载收藏和关注列表
        await this._loadPostLoginData();
        
        console.log('✅ [Store] 登录流程全部完成');
      } catch (error: any) {
        console.error('❌ [Store] 登录失败:', error);
        throw error;
      }
    },

    /**
     * 登录成功后统一处理 token 存储、用户信息获取、收藏关注加载
     * @description 供密码登录/手机号登录/一键登录共享使用，消除重复代码
     */
    async loginWithTokens(access_token: string, refresh_token: string): Promise<void> {
      console.log('🔑 [Store] loginWithTokens: 存储Token...');
      this.setToken(access_token);
      uni.setStorageSync('refresh_token', refresh_token);

      // 解析token中的用户信息
      this.parseUserFromToken(access_token);

      // 获取完整用户信息
      await this.fetchUserProfile();

      // 加载收藏和关注列表（不阻塞主流程）
      try {
        const favoriteStore = useFavoriteStore();
        const followStore = useFollowStore();
        Promise.all([
          favoriteStore.loadFavorites(),
          followStore.loadFollowedExperts()
        ]).catch(err => console.warn('[loginWithTokens] 收藏/关注加载失败:', err));
      } catch (err) {
        console.warn('[loginWithTokens] 加载Store失败:', err);
      }
    },

    /** 内部: 加载收藏和关注列表 */
    async _loadPostLoginData(): Promise<void> {
      console.log('🔄 [Store] 开始加载收藏和关注列表...');
      try {
        const favoriteStore = useFavoriteStore();
        const followStore = useFollowStore();
        
        await Promise.all([
          favoriteStore.loadFavorites(),
          followStore.loadFollowedExperts()
        ]);
        
        console.log('✅ [Store] 收藏和关注列表加载完成');
      } catch (error) {
        console.error('❌ [Store] 加载收藏和关注列表失败:', error);
        // 不影响登录流程，继续
      }
    },

    /**
     * 刷新Access Token
     * @returns 是否刷新成功
     */
    async refreshAccessToken(): Promise<boolean> {
      try {
        const refresh_token = uni.getStorageSync('refresh_token');
        if (!refresh_token) {
          console.error('❌ 未找到refresh_token');
          return false;
        }
        
        const response = await refreshTokenApi({ refresh_token });
        const { access_token } = response.data;
        
        this.setToken(access_token);
        this.parseUserFromToken(access_token);
        
        console.log('✅ Token刷新成功');
        return true;
      } catch (error: any) {
        console.error('❌ Token刷新失败:', error);
        // 刷新失败，清除认证状态
        this.clearAuth();
        return false;
      }
    },

    /**
     * 🔴 P0: 获取完整用户信息
     * 登录成功后必须调用此方法获取用户详细资料
     */
    async fetchUserProfile(): Promise<void> {
      try {
        console.log('🔄 开始获取用户信息...');
        
        // 1. 检查Token是否存在
        if (!this.token) {
          throw new Error('未找到访问Token，请先登录');
        }
        
        // 2. 调用API获取用户信息
        const response = await getCurrentUser();
        
        // 3. 验证响应
        if (response.code !== 200) {
          throw new Error(`获取用户信息失败: ${response.message}`);
        }
        
        const userInfo: UserInfo = response.data;
        
        // 4. 更新用户状态（解析头像URL为完整可访问路径）
        const resolvedAvatar = resolveMediaUrl(userInfo.avatar_url);
        
        // 生成兜底展示名称：当 nickname 为空时从手机号或 user_id 派生
        const fallbackName = userInfo.phone_number
          ? `用户${userInfo.phone_number.slice(-4)}`
          : userInfo.uuid
            ? `用户${userInfo.uuid.slice(-4)}`
            : '新用户';
        
        this.user = {
          user_id: userInfo.uuid,
          username: userInfo.username,
          email: userInfo.email,
          phone_number: userInfo.phone_number,
          is_phone_verified: userInfo.is_phone_verified,
          has_password: userInfo.has_password,
          avatar: resolvedAvatar,
          nickname: userInfo.nickname || fallbackName,
          bio: userInfo.bio,
          role: userInfo.role,
          status: userInfo.status,
          can_stream: userInfo.can_stream
        };
        
        console.log('✅ 用户信息获取成功:', {
          username: this.user.username,
          email: this.user.email,
          uuid: this.user.user_id,
          avatar: this.user.avatar ? '已设置' : '默认头像'
        });
        console.log('[auth-store] current avatar after fetchUserProfile:', this.user.avatar);
        console.log('[auth-store] resolved avatar (full URL):', resolvedAvatar);
        
      } catch (error: any) {
        console.error('❌ 获取用户信息失败:', error);
        
        // 5. 错误处理
        if (error.statusCode === 401) {
          // Token失效，清除认证状态
          console.log('🔄 Token失效，清除认证状态');
          this.clearAuth();
        }
        
        throw error;
      }
    },

    // 初始化认证状态
    async initializeAuth() {
      console.log('[Auth] ========== 开始初始化认证状态 ==========');
      
      // 首先尝试从uni-app存储读取
      const savedToken = getToken();
      console.log('📱 [初始化] 从uni-app存储读取token:', {
        存在: !!savedToken,
        tokenPreview: savedToken ? savedToken.substring(0, 30) + '...' : 'null',
        tokenLength: savedToken ? savedToken.length : 0
      });
      
      // 如果uni-app存储中没有，尝试从localStorage读取（H5平台）
      let token = savedToken;
      if (!token && typeof window !== 'undefined') {
        const localStorageToken = localStorage.getItem('jwt_token');
        console.log('🌐 [初始化] 从localStorage读取token:', localStorageToken ? '存在' : '不存在');
        if (localStorageToken) {
          // 将localStorage中的token同步到uni-app存储
          setToken(localStorageToken);
          token = localStorageToken;
          console.log('🔄 [初始化] 已同步token到uni-app存储');
        }
      }
      
      // 检查URL参数中是否有token（用于认证回调）
      if (!token && typeof window !== 'undefined') {
        const urlParams = new URLSearchParams(window.location.search);
        const urlToken = urlParams.get('token');
        console.log('🔗 [初始化] 从URL参数读取token:', urlToken ? '存在' : '不存在');
        if (urlToken) {
          token = urlToken;
          // 将URL中的token存储到localStorage
          localStorage.setItem('jwt_token', urlToken);
          setToken(urlToken);
          console.log('💾 [初始化] 已保存URL中的token');
        }
      }
      
      if (token) {
        console.log('🔍 [初始化] 开始验证token有效性...');
        const isValid = checkTokenExpiry(token);
        console.log('🔍 [初始化] Token验证结果:', isValid ? '有效' : '已过期');
        
        if (isValid) {
          console.log('✅ [初始化] Token有效，设置认证状态');
          this.setToken(token);
          this.parseUserFromToken(token);
          console.log('👤 [初始化] 当前用户:', this.user?.username || '未知');
          
          // ===== 关键修复：初始化时从API获取完整用户信息（包含role等字段） =====
          try {
            await this.fetchUserProfile();
            console.log('✅ [初始化] 用户详细信息加载完成，role:', this.user?.role || '无');
          } catch (err: any) {
            console.warn('⚠️ [初始化] 获取用户详细信息失败:', err?.message || err, '(此时用户仅有token中解析的username/role，缺少nickname/avatar等字段)');
          }
          
          // ===== 关键修复：初始化时也加载收藏和关注列表 =====
          try {
            const favoriteStore = useFavoriteStore();
            const followStore = useFollowStore();
            
            // 异步加载，不阻塞初始化流程
            Promise.all([
              favoriteStore.loadFavorites(),
              followStore.loadFollowedExperts()
            ]).then(() => {
              console.log('✅ [初始化] 收藏和关注列表加载完成');
            }).catch(err => {
              console.warn('⚠️ [初始化] 收藏/关注列表加载失败:', err);
            });
          } catch (err) {
            console.warn('⚠️ [初始化] 加载Store失败:', err);
          }
        } else {
          console.log('❌ [初始化] Token已过期，清除认证状态');
          this.clearAuth();
        }
      } else {
        console.log('❌ [初始化] 未找到有效token，用户未登录');
        this.isAuthenticated = false;
      }
      
      console.log('🏁 [初始化] 最终认证状态:', {
        isAuthenticated: this.isAuthenticated,
        hasToken: !!this.token,
        hasUser: !!this.user,
        username: this.user?.username
      });
      console.log('🏁 ========== 认证状态初始化完成 ==========');
    },

    /**
     * 导航到登录页面
     */
    navigateToLogin() {
      uni.navigateTo({ url: APP_LOGIN_PATH });
    },

    // 设置Token
    setToken(token: string) {
      console.log('🔑 [Store] ========== 开始设置Token ==========');
      console.log('🔑 [Store] 接收到的Token:', token ? token.substring(0, 30) + '...' : 'null');
      
      this.token = token;
      setToken(token);
      this.isAuthenticated = true;
      
      // 验证Token是否成功保存到Storage
      const savedToken = uni.getStorageSync('jwt_token');
      console.log('🔑 [Store] Storage验证:', {
        保存成功: savedToken === token,
        savedTokenPreview: savedToken ? savedToken.substring(0, 30) + '...' : 'null',
        storeToken: this.token ? this.token.substring(0, 30) + '...' : 'null',
        isAuthenticated: this.isAuthenticated
      });
      
      console.log('✅ [Store] Token设置完成，认证状态已更新');
      console.log('🔑 [Store] ========== Token设置完成 ==========');
    },

    // 解析用户信息
    parseUserFromToken(token: string) {
      const user = parseUserFromToken(token);
      if (user) {
        this.user = user;
        try {
          const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
          this.tokenExpiry = payload.exp * 1000;
        } catch (error) {
          console.error('解析Token过期时间失败:', error);
        }
      }
    },

    // 清除认证状态
    clearAuth() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      this.tokenExpiry = null;
      clearToken();
    },

    // 设置重定向路径
    setRedirectPath(path: string) {
      this.redirectPath = path;
      setRedirectPath(path);
    },

    // 获取重定向路径
    getRedirectPath() {
      return this.redirectPath || getRedirectPath();
    },

    // 清除重定向路径
    clearRedirectPath() {
      this.redirectPath = null;
      clearRedirectPath();
    },

    // 🔴 P0: 处理认证后的智能重定向
    handleAuthRedirect() {
      console.log('[Auth] ========== 开始处理登录后跳转 ==========');
      
      // 1. 获取记录的重定向路径
      const redirectPath = this.getRedirectPath();
      console.log('📍 最终重定向目标:', redirectPath || '默认首页');
      
      // 2. 清除重定向标记
      console.log('🧹 清除重定向标记...');
      uni.removeStorageSync('loginRedirectPath');
      this.clearRedirectPath();
      
      // 3. 智能跳转逻辑
      if (redirectPath && redirectPath !== APP_LOGIN_PATH) {
        // 判断是否为TabBar页面
        const tabBarPages = [
          APP_HOME_PATH,
          '/pages/app/tabbar/brand/index',
          APP_MY_LIVE_PATH,
          APP_EXPERT_PATH,
          APP_MY_PATH
        ];
        
        if (tabBarPages.includes(redirectPath)) {
          console.log('✅ 目标是TabBar页面，使用 switchTab:', redirectPath);
          uni.switchTab({ 
            url: redirectPath,
            success: () => {
              console.log('✅ switchTab 成功:', redirectPath);
            },
            fail: (err) => {
              console.error('❌ switchTab 失败:', err);
              console.log('🔄 尝试跳转到默认首页...');
              uni.switchTab({ url: APP_HOME_PATH });
            }
          });
        } else {
          console.log('✅ 目标是普通页面，使用 navigateTo:', redirectPath);
          uni.navigateTo({ 
            url: redirectPath,
            success: () => {
              console.log('✅ navigateTo 成功:', redirectPath);
            },
            fail: (err) => {
              console.error('❌ navigateTo 失败:', err);
              console.log('🔄 回退到首页...');
              uni.switchTab({ url: APP_HOME_PATH });
            }
          });
        }
      } else {
        // 4. 默认跳转到首页
        console.log('✅ 无重定向路径或路径是登录页，跳转到默认首页');
        // #ifdef H5
        console.log('🌐 H5平台，跳转到:', AUTH_REDIRECT_PATH);
        uni.navigateTo({ 
          url: AUTH_REDIRECT_PATH,
          success: () => console.log('✅ H5跳转成功'),
          fail: (err) => console.error('❌ H5跳转失败:', err)
        });
        // #endif
        // #ifndef H5
        console.log('📱 App平台，跳转到首页 TabBar');
          uni.switchTab({ 
          url: APP_HOME_PATH,
          success: () => {
            console.log('✅ App跳转首页成功');
          },
          fail: (err) => {
            console.error('❌ App跳转首页失败:', err);
          }
        });
        // #endif
      }
      
      console.log('🏁 ========== 跳转处理完成 ==========');
    },

    // 强制重新认证
    forceReauth(targetPath: string) {
      this.clearAuth();
      this.setRedirectPath(targetPath);

      // 无条件跳转登录页（去掉 DEV mock 自动登录逻辑）
      console.log('🚫 Token失效，跳转到登录页');
      // #ifdef H5
      window.location.href = LOGIN_URL;
      // #endif
      // #ifndef H5
      uni.navigateTo({ url: APP_LOGIN_PATH });
      // #endif
    },

    // 登出并跳转到登录页面
    async logout() {
      try {
        // 调用后端登出API
        await logoutApi();
      } catch (error) {
        console.error('❌ 调用登出API失败:', error);
        // 即使API失败也继续清除本地状态
      }
      
      this.clearAuth();
      this.clearRedirectPath();
      // 清除refresh_token
      uni.removeStorageSync('refresh_token');
      
      // 清空收藏和关注Store
      try {
        const favoriteStore = useFavoriteStore();
        const followStore = useFollowStore();
        
        favoriteStore.clear();
        followStore.clear();
        
        console.log('🧹 [登出] 已清空收藏和关注Store');
      } catch (error) {
        console.error('❌ [登出] 清空Store失败:', error);
      }
      
      console.log('🧹 [登出] 已清除所有认证信息');
      
      // #ifdef H5
      // H5平台：使用window.location.href跳转
      window.location.href = LOGIN_URL;
      // #endif
      
      // #ifndef H5
      // 非H5平台（App/小程序）：跳转到登录页面
      uni.navigateTo({
        url: APP_LOGIN_PATH,
        fail: () => {
          uni.showToast({
            title: '跳转失败，请手动打开登录页面',
            icon: 'none'
          });
        }
      });
      // #endif
    },

    // 跳转到用户服务
    goToUserService(page: string) {
      const userServiceUrl = `${FRONTEND_USER_URL}${page}`;
      
      // #ifdef H5
      // H5平台：使用window.location.href进行跨服务跳转
      window.location.href = userServiceUrl;
      // #endif
      
      // #ifdef MP-WEIXIN
      // 微信小程序：跳转到其他小程序
      uni.navigateToMiniProgram({
        appId: '用户服务小程序的appId', // 需要配置用户服务小程序的appId
        path: page,
        success: () => {
          console.log('跳转到用户服务小程序成功');
        },
        fail: (err) => {
          console.error('跳转到用户服务小程序失败:', err);
          // 降级处理：显示提示信息
          uni.showToast({
            title: '跳转失败，请手动打开用户服务',
            icon: 'none'
          });
        }
      });
      // #endif
      
      // #ifdef APP-PLUS
      // App平台：使用uni.navigateTo进行页面跳转
      uni.navigateTo({
        url: userServiceUrl,
        fail: (err) => {
          console.error('App跳转失败:', err);
          // 降级处理：尝试使用redirectTo
          uni.redirectTo({
            url: userServiceUrl,
            fail: () => {
              uni.showToast({
                title: '跳转失败，请手动打开用户服务',
                icon: 'none'
              });
            }
          });
        }
      });
      // #endif
    }
  }
});
