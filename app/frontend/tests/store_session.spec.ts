// tests/store_session.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSessionStore } from '../src/store/session'
import * as sessionApi from '../src/api/session'
import type { Session, SessionCreatePayload } from '../src/types/session'

// Mock session API
vi.mock('../src/api/session', () => ({
  getSessionList: vi.fn(),
  getSessionDetail: vi.fn(),
  createSession: vi.fn(),
  updateSession: vi.fn(),
  deleteSession: vi.fn()
}))

// Mock uni-app
vi.mock('@dcloudio/uni-app', () => ({
  showToast: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn()
}))

// Mock uni global
const mockUni = {
  showToast: vi.fn()
}
// @ts-ignore
global.uni = mockUni

describe('useSessionStore', () => {
  let store: any

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSessionStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('初始状态测试', () => {
    it('初始状态正确', () => {
      // Assert
      expect(store.sessions).toEqual([])
      expect(store.currentSession).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.pagination).toEqual({
        page: 1,
        size: 10,
        hasMore: true,
        total: 0
      })
    })
  })

  describe('fetchSessionsByRoomId 测试', () => {
    const mockRoomId = 'room-123'
    const mockSessions: Session[] = [
      {
        id: 'session-1',
        room_id: mockRoomId,
        status: 'scheduled',
        start_time: '2023-01-01T10:00:00Z',
        end_time: null,
        video_id: null,
        created_at: '2023-01-01T09:00:00Z',
        updated_at: '2023-01-01T09:00:00Z'
      },
      {
        id: 'session-2',
        room_id: mockRoomId,
        status: 'live',
        start_time: '2023-01-01T11:00:00Z',
        end_time: null,
        video_id: null,
        created_at: '2023-01-01T10:00:00Z',
        updated_at: '2023-01-01T10:00:00Z'
      }
    ]

    it('成功获取场次列表 - 统一响应结构', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        message: 'success',
        data: {
          items: mockSessions,
          total: 2,
          page: 1,
          size: 10
        }
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId(mockRoomId)

      // Assert
      expect(sessionApi.getSessionList).toHaveBeenCalledWith(mockRoomId, {
        page: 1,
        size: 10
      })
      expect(store.sessions).toEqual(mockSessions)
      expect(store.pagination.total).toBe(2)
      expect(store.pagination.page).toBe(1)
      expect(store.pagination.hasMore).toBe(false)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('成功获取场次列表 - 直接业务数据结构', async () => {
      // Arrange
      const mockResponse = {
        items: mockSessions,
        total: 2,
        page: 1,
        size: 10
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId(mockRoomId)

      // Assert
      expect(store.sessions).toEqual(mockSessions)
      expect(store.pagination.total).toBe(2)
      expect(store.loading).toBe(false)
    })

    it('刷新时重置状态', async () => {
      // Arrange
      store.sessions = [mockSessions[0]]
      store.pagination.page = 3
      const mockResponse = {
        code: 200,
        data: {
          items: [mockSessions[1]],
          total: 1,
          page: 1,
          size: 10
        }
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId(mockRoomId, { refresh: true })

      // Assert
      expect(store.sessions).toEqual([mockSessions[1]])
      expect(store.pagination.page).toBe(1)
    })

    it('非刷新模式应该追加数据', async () => {
      // Arrange
      store.sessions = [mockSessions[0]]
      store.pagination.page = 2
      const mockResponse = {
        code: 200,
        data: {
          items: [mockSessions[1]],
          total: 2,
          page: 2,
          size: 10
        }
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId(mockRoomId)

      // Assert
      expect(store.sessions).toEqual(mockSessions)
      expect(store.pagination.page).toBe(2)
    })

    it('当正在加载且非刷新模式时应该直接返回', async () => {
      // Arrange
      store.loading = true

      // Act
      await store.fetchSessionsByRoomId(mockRoomId)

      // Assert
      expect(sessionApi.getSessionList).not.toHaveBeenCalled()
    })

    it('API 错误时正确处理', async () => {
      // Arrange
      const mockError = new Error('API Error')
      vi.mocked(sessionApi.getSessionList).mockRejectedValue(mockError)

      // Act & Assert
      await expect(store.fetchSessionsByRoomId(mockRoomId)).rejects.toThrow('API Error')
      expect(store.error).toEqual(mockError)
      expect(store.loading).toBe(false)
    })

    it('处理API错误响应', async () => {
      // Arrange
      const mockErrorResponse = {
        code: 400,
        message: 'Bad Request',
        data: null
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockErrorResponse as any)

      // Act & Assert
      await expect(store.fetchSessionsByRoomId(mockRoomId)).rejects.toThrow('Bad Request')
      expect(store.error).toBeInstanceOf(Error)
      expect(store.loading).toBe(false)
    })

    it('正确设置hasMore标志', async () => {
      // Arrange - 返回数据量等于页面大小
      const mockResponse = {
        code: 200,
        data: {
          items: new Array(10).fill(mockSessions[0]),
          total: 20,
          page: 1,
          size: 10
        }
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId(mockRoomId)

      // Assert
      expect(store.pagination.hasMore).toBe(true)
      expect(store.pagination.page).toBe(2)
    })
  })

  describe('fetchSessionById 测试', () => {
    const mockSessionId = 'session-123'
    const mockSession: Session = {
      id: mockSessionId,
      room_id: 'room-123',
      status: 'live',
      start_time: '2023-01-01T10:00:00Z',
      end_time: null,
      video_id: null,
      created_at: '2023-01-01T09:00:00Z',
      updated_at: '2023-01-01T09:00:00Z'
    }

    it('成功获取场次详情 - 统一响应结构', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        message: 'success',
        data: mockSession
      }
      vi.mocked(sessionApi.getSessionDetail).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionById(mockSessionId)

      // Assert
      expect(sessionApi.getSessionDetail).toHaveBeenCalledWith(mockSessionId)
      expect(store.currentSession).toEqual(mockSession)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('成功获取场次详情 - 直接业务数据结构', async () => {
      // Arrange
      vi.mocked(sessionApi.getSessionDetail).mockResolvedValue(mockSession)

      // Act
      await store.fetchSessionById(mockSessionId)

      // Assert
      expect(store.currentSession).toEqual(mockSession)
      expect(store.loading).toBe(false)
    })

    it('场次不存在时正确处理', async () => {
      // Arrange
      const mockErrorResponse = {
        code: 404,
        message: 'Session not found',
        data: null
      }
      vi.mocked(sessionApi.getSessionDetail).mockResolvedValue(mockErrorResponse as any)

      // Act & Assert
      await expect(store.fetchSessionById(mockSessionId)).rejects.toThrow('Session not found')
      expect(store.error).toBeInstanceOf(Error)
      expect(store.currentSession).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('网络请求异常时正确处理', async () => {
      // Arrange
      const networkError = new Error('Network Error')
      vi.mocked(sessionApi.getSessionDetail).mockRejectedValue(networkError)

      // Act & Assert
      await expect(store.fetchSessionById(mockSessionId)).rejects.toThrow('Network Error')
      expect(store.error).toBe(networkError)
      expect(store.loading).toBe(false)
    })
  })

  describe('createSession 测试', () => {
    const mockRoomId = 'room-123'
    const mockPayload: SessionCreatePayload = {
      start_time: '2023-01-01T10:00:00Z'
    }
    const mockCreatedSession: Session = {
      id: 'session-new',
      room_id: mockRoomId,
      status: 'scheduled',
      start_time: mockPayload.start_time,
      end_time: null,
      video_id: null,
      created_at: '2023-01-01T09:00:00Z',
      updated_at: '2023-01-01T09:00:00Z'
    }

    it('成功创建场次 - 统一响应结构', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        message: 'success',
        data: mockCreatedSession
      }
      vi.mocked(sessionApi.createSession).mockResolvedValue(mockResponse as any)
      vi.mocked(sessionApi.getSessionList).mockResolvedValue({
        code: 200,
        data: { items: [mockCreatedSession], total: 1, page: 1, size: 10 }
      } as any)

      // Act
      const result = await store.createSession(mockRoomId, mockPayload)

      // Assert
      expect(sessionApi.createSession).toHaveBeenCalledWith(mockRoomId, mockPayload)
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '创建成功',
        icon: 'success'
      })
      expect(result).toBe(true)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('成功创建场次 - 直接业务数据结构', async () => {
      // Arrange
      vi.mocked(sessionApi.createSession).mockResolvedValue(mockCreatedSession)
      vi.mocked(sessionApi.getSessionList).mockResolvedValue({
        items: [mockCreatedSession],
        total: 1,
        page: 1,
        size: 10
      } as any)

      // Act
      const result = await store.createSession(mockRoomId, mockPayload)

      // Assert
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '创建成功',
        icon: 'success'
      })
      expect(result).toBe(true)
    })

    it('创建失败时抛出错误', async () => {
      // Arrange
      const mockError = new Error('Creation failed')
      vi.mocked(sessionApi.createSession).mockRejectedValue(mockError)

      // Act & Assert
      await expect(store.createSession(mockRoomId, mockPayload)).rejects.toThrow('Creation failed')
      expect(store.error).toEqual(mockError)
      expect(store.loading).toBe(false)
    })

    it('处理API错误响应', async () => {
      // Arrange
      const mockErrorResponse = {
        code: 400,
        message: 'Invalid data',
        data: null
      }
      vi.mocked(sessionApi.createSession).mockResolvedValue(mockErrorResponse as any)

      // Act & Assert
      await expect(store.createSession(mockRoomId, mockPayload)).rejects.toThrow('Invalid data')
      expect(store.error).toBeInstanceOf(Error)
      expect(store.loading).toBe(false)
      expect(mockUni.showToast).not.toHaveBeenCalled()
    })
  })

  describe('updateSession 测试', () => {
    const mockSessionId = 'session-123'
    const mockPayload: Partial<Session> = {
      status: 'live',
      end_time: '2023-01-01T11:00:00Z'
    }
    const mockUpdatedSession: Session = {
      id: mockSessionId,
      room_id: 'room-123',
      status: 'live',
      start_time: '2023-01-01T10:00:00Z',
      end_time: '2023-01-01T11:00:00Z',
      video_id: null,
      created_at: '2023-01-01T09:00:00Z',
      updated_at: '2023-01-01T10:30:00Z'
    }

    it('成功更新场次 - 统一响应结构', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        message: 'success',
        data: mockUpdatedSession
      }
      vi.mocked(sessionApi.updateSession).mockResolvedValue(mockResponse as any)

      // Act
      const result = await store.updateSession(mockSessionId, mockPayload)

      // Assert
      expect(sessionApi.updateSession).toHaveBeenCalledWith(mockSessionId, mockPayload)
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '更新成功',
        icon: 'success'
      })
      expect(result).toBe(true)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('成功更新场次 - 直接业务数据结构', async () => {
      // Arrange
      vi.mocked(sessionApi.updateSession).mockResolvedValue(mockUpdatedSession)

      // Act
      const result = await store.updateSession(mockSessionId, mockPayload)

      // Assert
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '更新成功',
        icon: 'success'
      })
      expect(result).toBe(true)
    })

    it('更新失败时抛出错误', async () => {
      // Arrange
      const mockError = new Error('Update failed')
      vi.mocked(sessionApi.updateSession).mockRejectedValue(mockError)

      // Act & Assert
      await expect(store.updateSession(mockSessionId, mockPayload)).rejects.toThrow('Update failed')
      expect(store.error).toEqual(mockError)
      expect(store.loading).toBe(false)
    })

    it('处理API错误响应', async () => {
      // Arrange
      const mockErrorResponse = {
        code: 403,
        message: 'Forbidden',
        data: null
      }
      vi.mocked(sessionApi.updateSession).mockResolvedValue(mockErrorResponse as any)

      // Act & Assert
      await expect(store.updateSession(mockSessionId, mockPayload)).rejects.toThrow('Forbidden')
      expect(store.error).toBeInstanceOf(Error)
      expect(store.loading).toBe(false)
      expect(mockUni.showToast).not.toHaveBeenCalled()
    })
  })

  describe('deleteSession 测试', () => {
    const mockSessionId = 'session-123'
    const mockRoomId = 'room-123'
    const mockDeleteResponse = {
      id: mockSessionId,
      status: 'deleted'
    }

    it('成功删除场次 - 统一响应结构', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        message: 'success',
        data: mockDeleteResponse
      }
      vi.mocked(sessionApi.deleteSession).mockResolvedValue(mockResponse as any)
      vi.mocked(sessionApi.getSessionList).mockResolvedValue({
        code: 200,
        data: { items: [], total: 0, page: 1, size: 10 }
      } as any)

      // Act
      const result = await store.deleteSession(mockSessionId, mockRoomId)

      // Assert
      expect(sessionApi.deleteSession).toHaveBeenCalledWith(mockSessionId)
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '删除成功',
        icon: 'success'
      })
      expect(result).toBe(true)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('成功删除场次 - 直接业务数据结构', async () => {
      // Arrange
      vi.mocked(sessionApi.deleteSession).mockResolvedValue(mockDeleteResponse)
      vi.mocked(sessionApi.getSessionList).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        size: 10
      } as any)

      // Act
      const result = await store.deleteSession(mockSessionId, mockRoomId)

      // Assert
      expect(mockUni.showToast).toHaveBeenCalledWith({
        title: '删除成功',
        icon: 'success'
      })
      expect(result).toBe(true)
    })

    it('删除失败时抛出错误', async () => {
      // Arrange
      const mockError = new Error('Delete failed')
      vi.mocked(sessionApi.deleteSession).mockRejectedValue(mockError)

      // Act & Assert
      await expect(store.deleteSession(mockSessionId, mockRoomId)).rejects.toThrow('Delete failed')
      expect(store.error).toEqual(mockError)
      expect(store.loading).toBe(false)
    })

    it('处理API错误响应', async () => {
      // Arrange
      const mockErrorResponse = {
        code: 404,
        message: 'Session not found',
        data: null
      }
      vi.mocked(sessionApi.deleteSession).mockResolvedValue(mockErrorResponse as any)

      // Act & Assert
      await expect(store.deleteSession(mockSessionId, mockRoomId)).rejects.toThrow('Session not found')
      expect(store.error).toBeInstanceOf(Error)
      expect(store.loading).toBe(false)
      expect(mockUni.showToast).not.toHaveBeenCalled()
    })
  })

  describe('边界条件和异常情况', () => {
    it('处理空的items数组', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        data: {
          items: [],
          total: 0,
          page: 1,
          size: 10
        }
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId('room-123')

      // Assert
      expect(store.sessions).toEqual([])
      expect(store.pagination.total).toBe(0)
      expect(store.pagination.hasMore).toBe(false)
    })

    it('处理缺少total字段的响应', async () => {
      // Arrange
      const mockResponse = {
        items: [{ id: 'session-1' }],
        page: 1,
        size: 10
        // 缺少total字段
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId('room-123')

      // Assert
      expect(store.pagination.total).toBe(0)
    })

    it('处理undefined的items', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        data: {
          items: undefined,
          total: 0,
          page: 1,
          size: 10
        }
      }
      vi.mocked(sessionApi.getSessionList).mockResolvedValue(mockResponse as any)

      // Act
      await store.fetchSessionsByRoomId('room-123')

      // Assert
      expect(store.sessions).toEqual([])
    })
  })
})