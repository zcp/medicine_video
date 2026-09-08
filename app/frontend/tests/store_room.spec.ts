// tests/store/room.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRoomStore } from '../src/store/room'
import * as roomApi from '../src/api/room'

// Mock API
vi.mock('@/api/room', () => ({
  getSubVenues: vi.fn(),
  createSubVenue: vi.fn(),
  updateSubVenue: vi.fn(),
  deleteSubVenue: vi.fn()
}))

// Mock request utilities
vi.mock('@/utils/request', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  patch: vi.fn()
}))

// Mock uni-app
vi.mock('@dcloudio/uni-app', () => ({
  showToast: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn()
}))

describe('useRoomStore', () => {
  let store: any

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useRoomStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('初始状态测试', () => {
    it('初始状态正确', () => {
      // Assert
      expect(store.rooms).toEqual([])
      expect(store.currentRoom).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.pagination).toEqual({
        page: 1,
        size: 10,
        hasMore: true,
        total: 0
      })
      expect(store.subVenues).toEqual([])
      expect(store.subVenuesLoading).toBe(false)
      expect(store.subVenuesError).toBeNull()
    })
  })

  describe('fetchRooms 测试', () => {
    it('成功获取房间列表', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        data: {
          items: [{ id: '1', title: 'Room 1' }],
          total: 1,
          page: 1,
          size: 10
        }
      }
      const { get } = await import('../src/utils/request')
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      await store.fetchRooms()

      // Assert
      expect(store.rooms).toEqual([{ id: '1', title: 'Room 1' }])
      expect(store.pagination.total).toBe(1)
      expect(store.pagination.page).toBe(2)
      expect(store.pagination.hasMore).toBe(false)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('刷新时重置状态', async () => {
      // Arrange
      store.rooms = [{ id: 'old', title: 'Old Room' }]
      store.pagination.page = 5
      const mockResponse = {
        code: 200,
        data: {
          items: [{ id: '1', title: 'New Room' }],
          total: 1,
          page: 1,
          size: 10
        }
      }
      const { get } = await import('../src/utils/request')
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      await store.fetchRooms({ refresh: true })

      // Assert
      expect(store.rooms).toEqual([{ id: '1', title: 'New Room' }])
      expect(store.pagination.page).toBe(2)
    })

    it('API 错误时正确处理', async () => {
      // Arrange
      const mockError = new Error('API Error')
      const { get } = await import('../src/utils/request')
      vi.mocked(get).mockRejectedValue(mockError)

      // Act
      await store.fetchRooms()

      // Assert
      expect(store.error).toEqual(mockError)
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchRoomById 测试', () => {
    it('成功获取房间详情', async () => {
      // Arrange
      const mockResponse = {
        code: 200,
        data: { id: '1', title: 'Room 1' }
      }
      const { get } = await import('../src/utils/request')
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      await store.fetchRoomById('1')

      // Assert
      expect(store.currentRoom).toEqual({ id: '1', title: 'Room 1' })
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('房间不存在时正确处理', async () => {
      // Arrange
      const mockResponse = {
        code: 404,
        message: 'Room not found'
      }
      const { get } = await import('../src/utils/request')
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      await store.fetchRoomById('999')

      // Assert
      expect(store.currentRoom).toBeNull()
      expect(store.error).toBeDefined()
    })
  })

  describe('addNewRoom 测试', () => {
    it('成功创建房间', async () => {
      // Arrange
      const mockPayload = { title: 'New Room', description: 'Test' }
      const mockResponse = {
        code: 200,
        data: { id: '1', title: 'New Room' }
      }
      const { post, get } = await import('../src/utils/request')
      vi.mocked(post).mockResolvedValue(mockResponse)
      vi.mocked(get).mockResolvedValue(mockResponse) // fetchRooms 使用 get 方法

      // Act
      const result = await store.addNewRoom(mockPayload)

      // Assert
      expect(result).toBe(true)
      expect(post).toHaveBeenCalledWith('/rooms', mockPayload)
    })

    it('创建失败时返回 false', async () => {
      // Arrange
      const mockPayload = { title: 'New Room' }
      const mockError = new Error('Creation failed')
      const { post } = await import('../src/utils/request')
      vi.mocked(post).mockRejectedValue(mockError)

      // Act
      const result = await store.addNewRoom(mockPayload)

      // Assert
      expect(result).toBe(false)
      expect(store.error).toEqual(mockError)
    })
  })

  describe('updateRoom 测试', () => {
    it('成功更新房间', async () => {
      // Arrange
      const mockPayload = { title: 'Updated Room' }
      const mockResponse = {
        code: 200,
        data: { id: '1', title: 'Updated Room'}
      }
      const { patch } = await import('../src/utils/request')
      vi.mocked(patch).mockResolvedValue(mockResponse)

      // Act
      const result = await store.updateRoom('1', mockPayload)

      // Assert
      expect(result).toBe(true)
      expect(patch).toHaveBeenCalledWith('/rooms/1', mockPayload)
    })

    it('更新失败时抛出错误', async () => {
      // Arrange
      const mockPayload = { title: 'Updated Room' }
      const mockError = new Error('Update failed')
      const { patch } = await import('../src/utils/request')
      vi.mocked(patch).mockRejectedValue(mockError)

      // Act & Assert
      await expect(store.updateRoom('1', mockPayload)).rejects.toThrow('Update failed')
      expect(store.error).toEqual(mockError)
    })
  })
})