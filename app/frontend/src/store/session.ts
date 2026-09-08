import { defineStore } from 'pinia';
import { getSessionList, getSessionDetail, createSession, updateSession, importSession, deleteSession, updateSessionStatus } from '../api/session';
import type { Session, SessionCreatePayload, SessionUpdatePayload, SessionImportPayload } from '../types/session';

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessions: [] as Session[],
    currentSession: null as Session | null,
    loading: false,
    error: null as Error | null,
    pagination: {
      page: 1,
      size: 10,
      hasMore: true,
      total: 0,
    },
  }),
  actions: {
    async fetchSessionsByRoomId(roomId: string, options: { refresh?: boolean } = {}) {
      console.log(`🔍 SessionStore: 开始获取房间 ${roomId} 的session数据`);
      
      if (this.loading && !options.refresh) return;
      this.loading = true;
      this.error = null;
      if (options.refresh) {
        this.pagination.page = 1;
        this.sessions = [];
      }
      try {
        console.log(`📡 SessionStore: 调用API获取房间 ${roomId} 的session数据`);
        const response: any = await getSessionList(roomId, {
          page: this.pagination.page,
          size: this.pagination.size,
        });
        console.log(`📊 SessionStore: API响应数据:`, response);
        
        // 兼容统一响应结构和直接业务数据两种情况
        let items, total, page, size;
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            ({ items, total, page, size } = response.data);
            console.log(`✅ SessionStore: 解析后的数据 - items:`, items, 'total:', total);
          } else {
            console.error(`❌ SessionStore: API返回错误 - code:`, response.code, 'message:', response.message);
            throw new Error(response.message || 'Failed to fetch sessions');
          }
        } else {
          ({ items, total, page, size } = response);
          console.log(`✅ SessionStore: 直接解析数据 - items:`, items, 'total:', total);
        }
        const newSessions = items || [];
        console.log(`📋 SessionStore: 处理后的session数据:`, newSessions);
        
        if (options.refresh) {
          this.sessions = newSessions;
        } else {
          this.sessions.push(...newSessions);
        }
        this.pagination.total = total || 0;
        this.pagination.hasMore = newSessions.length === this.pagination.size;
        if (this.pagination.hasMore) {
          this.pagination.page++;
        }
        
        console.log(`✅ SessionStore: 最终sessions数组:`, this.sessions);
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to fetch sessions for roomId=${roomId}:`, err);
        throw new Error(err.message || 'Failed to fetch sessions');
      } finally {
        this.loading = false;
      }
    },
    async fetchSessionById(id: string) {
      this.loading = true;
      this.error = null;
      this.currentSession = null;
      try {
        const response: any = await getSessionDetail(id);
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            console.log('getSessionDetail返回：', response);
            this.currentSession = response.data;
            console.log('赋值后currentSession：', this.currentSession);
          } else {
            throw new Error(response.message || 'Failed to fetch session details');
          }
        } else {
          this.currentSession = response;
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to fetch session detail, id=${id}:`, err);
        throw new Error(err.message || 'Failed to fetch session details');
      } finally {
        this.loading = false;
      }
    },
    async createSession(roomId: string, payload: SessionCreatePayload): Promise<{ success: boolean; message?: string }> {
      console.log('🎯 [SessionStore] ========== createSession 开始 ==========');
      console.log('🎯 [SessionStore] roomId:', roomId);
      console.log('🎯 [SessionStore] payload:', JSON.stringify(payload, null, 2));
      
      this.loading = true;
      this.error = null;
      try {
        console.log('📡 [SessionStore] 调用 createSession API...');
        const response: any = await createSession(roomId, payload);
        console.log('📥 [SessionStore] API响应:', JSON.stringify(response, null, 2));
        
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            console.log('✅ [SessionStore] Session创建成功，返回数据:', response.data);
            await this.fetchSessionsByRoomId(roomId, { refresh: true });
            return { success: true, message: '场次创建成功' };
          } else {
            console.error('❌ [SessionStore] API返回错误:', response.message);
            return { success: false, message: response.message || '创建失败' };
          }
        } else {
          console.log('✅ [SessionStore] Session创建成功（直接返回数据）');
          await this.fetchSessionsByRoomId(roomId, { refresh: true });
          return { success: true, message: '场次创建成功' };
        }
      } catch (err: any) {
        this.error = err;
        console.error(`❌ [SessionStore] 创建Session失败, roomId=${roomId}:`, err);
        return { success: false, message: err.message || '创建失败' };
      } finally {
        this.loading = false;
        console.log('🎯 [SessionStore] ========== createSession 结束 ==========');
      }
    },
    async updateSession(id: string, payload: SessionUpdatePayload) {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await updateSession(id, payload);
        console.log('📡 [SessionStore] API响应:', response);
        
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            console.log('✅ [SessionStore] Session更新成功, session_id:', response.data.id);
            return { success: true, session_id: response.data.id };
          } else if (response.code === 422) {
            console.error('❌ [SessionStore] API返回422错误:', response.message);
            console.error('🔍 [SessionStore] 错误详情:', {
              statusCode: response.statusCode,
              code: response.code,
              message: response.message,
              data: response.data,
              fullResponse: response
            });
            throw new Error(response.message || '更新失败');
          } else {
            throw new Error(response.message || '更新失败');
          }
        } else {
          console.log('✅ [SessionStore] Session更新成功（非标准响应）');
          return { success: true };
        }
      } catch (err: any) {
        this.error = err;
        console.error(`❌ [SessionStore] 更新Session失败, id=${id}:`, err);
        console.error('🔍 [SessionStore] 错误详情:', {
          statusCode: err.statusCode,
          code: err.code,
          message: err.message,
          data: err.data,
          fullResponse: err.fullResponse
        });
        throw new Error(err.message || '更新失败');
      } finally {
        this.loading = false;
      }
    },
    async deleteSession(id: string, roomId: string) {
      this.loading = true;
      this.error = null;
      try {
        const response: any = await deleteSession(id);
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            await this.fetchSessionsByRoomId(roomId, { refresh: true });
            uni.showToast({ title: '删除成功', icon: 'success' });
            return true;
          } else {
            throw new Error(response.message || '删除失败');
          }
        } else {
          await this.fetchSessionsByRoomId(roomId, { refresh: true });
          uni.showToast({ title: '删除成功', icon: 'success' });
          return true;
        }
      } catch (err: any) {
        this.error = err;
        console.error(`Failed to delete session id=${id}:`, err);
        throw new Error(err.message || '删除失败');
      } finally {
        this.loading = false;
      }
    },
    async importSession(roomId: string, payload: SessionImportPayload): Promise<{ success: boolean; message?: string }> {
      console.log('🎯 [SessionStore] ========== importSession 开始 ==========');
      console.log('🎯 [SessionStore] roomId:', roomId);
      console.log('🎯 [SessionStore] payload:', JSON.stringify(payload, null, 2));
      
      this.loading = true;
      this.error = null;
      try {
        console.log('📡 [SessionStore] 调用 importSession API...');
        const response: any = await importSession(roomId, payload);
        console.log('📥 [SessionStore] API响应:', JSON.stringify(response, null, 2));
        
        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            console.log('✅ [SessionStore] Session导入成功，返回数据:', response.data);
            await this.fetchSessionsByRoomId(roomId, { refresh: true });
            return { success: true, message: '场次导入成功' };
          } else {
            console.error('❌ [SessionStore] API返回错误:', response.message);
            return { success: false, message: response.message || '导入失败' };
          }
        } else {
          console.log('✅ [SessionStore] Session导入成功（直接返回数据）');
          await this.fetchSessionsByRoomId(roomId, { refresh: true });
          return { success: true, message: '场次导入成功' };
        }
      } catch (err: any) {
        this.error = err;
        console.error(`❌ [SessionStore] 导入Session失败, roomId=${roomId}:`, err);
        return { success: false, message: err.message || '导入失败' };
      } finally {
        this.loading = false;
        console.log('🎯 [SessionStore] ========== importSession 结束 ==========');
      }
    },

    // 设置当前session
    setCurrentSession(session: Session | null) {
      this.currentSession = session;
    },

    // V15：手动切换场次状态（external 场次专用：开播/停播/转回放/回退预告）
    async updateSessionStatus(
      sessionId: string,
      roomId: string,
      data: { status: string; playback_url?: string }
    ): Promise<{ success: boolean; message?: string }> {
      console.log('🎯 [SessionStore] ========== updateSessionStatus 开始 ==========');
      console.log('🎯 [SessionStore] sessionId:', sessionId, 'data:', JSON.stringify(data));

      this.loading = true;
      this.error = null;
      try {
        const response: any = await updateSessionStatus(sessionId, data);
        console.log('📥 [SessionStore] updateSessionStatus API响应:', JSON.stringify(response, null, 2));

        if ('code' in response && 'data' in response) {
          if (response.code === 200 && response.data) {
            console.log('✅ [SessionStore] 状态切换成功:', response.data);
            await this.fetchSessionsByRoomId(roomId, { refresh: true });
            return { success: true, message: '状态切换成功' };
          } else {
            console.error('❌ [SessionStore] API返回错误:', response.message);
            return { success: false, message: response.message || '状态切换失败' };
          }
        } else {
          console.log('✅ [SessionStore] 状态切换成功（直接返回数据）');
          await this.fetchSessionsByRoomId(roomId, { refresh: true });
          return { success: true, message: '状态切换成功' };
        }
      } catch (err: any) {
        this.error = err;
        console.error(`❌ [SessionStore] 切换Session状态失败, sessionId=${sessionId}:`, err);
        return { success: false, message: err.message || '状态切换失败' };
      } finally {
        this.loading = false;
        console.log('🎯 [SessionStore] ========== updateSessionStatus 结束 ==========');
      }
    },
  },
});