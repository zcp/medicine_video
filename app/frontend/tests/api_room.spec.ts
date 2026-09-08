// tests/api/room.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as roomApi from '../src/api/room'
import { get, post, patch, del } from '../src/utils/request'

// Mock request utilities
vi.mock('@/utils/request', () => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  del: vi.fn()
}))

describe('room.ts API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('getRoomList', () => {
    it('正确调用获取房间列表', async () => {
      // Arrange
      const mockResponse = {
        items: [{ id: '1', title: 'Room 1' }],
        total: 1,
        page: 1,
        size: 10
      }
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      const result = await roomApi.getRoomList({ page: 1, size: 10 })

      // Assert
      expect(get).toHaveBeenCalledWith('/rooms', { page: 1, size: 10 })
      expect(result).toEqual(mockResponse)
    })

    it('使用默认参数', async () => {
      // Arrange
      const mockResponse = { items: [], total: 0, page: 1, size: 10 }
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      await roomApi.getRoomList()

      // Assert
      expect(get).toHaveBeenCalledWith('/rooms', {})
    })
  })

  describe('getRoomDetail', () => {
    it('正确调用获取房间详情', async () => {
      // Arrange
      const mockResponse = { id: '1', title: 'Room 1' }
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      const result = await roomApi.getRoomDetail('1')

      // Assert
      expect(get).toHaveBeenCalledWith('/rooms/1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('createRoom', () => {
    it('正确调用创建房间', async () => {
      // Arrange
      const mockPayload = { title: 'New Room', description: 'Test' }
      const mockResponse = { id: '1', title: 'New Room' }
      vi.mocked(post).mockResolvedValue(mockResponse)

      // Act
      const result = await roomApi.createRoom(mockPayload)

      // Assert
      expect(post).toHaveBeenCalledWith('/rooms', mockPayload, { auth: true })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateRoom', () => {
    it('正确调用更新房间', async () => {
      // Arrange
      const mockData = { title: 'Updated Room' }
      const mockResponse = { id: '1', title: 'Updated Room' }
      vi.mocked(patch).mockResolvedValue(mockResponse)

      // Act
      const result = await roomApi.updateRoom('1', mockData)

      // Assert
      expect(patch).toHaveBeenCalledWith('/rooms/1', mockData, { auth: true })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteRoom', () => {
    it('正确调用删除房间', async () => {
      // Arrange
      vi.mocked(del).mockResolvedValue(undefined)

      // Act
      await roomApi.deleteRoom('1')

      // Assert
      expect(del).toHaveBeenCalledWith('/rooms/1', undefined, { auth: true })
    })
  })

  describe('getSubVenues', () => {
    it('正确调用获取分会场', async () => {
      // Arrange
      const mockResponse = [{ id: '2', title: 'Sub Room' }]
      vi.mocked(get).mockResolvedValue(mockResponse)

      // Act
      const result = await roomApi.getSubVenues('1')

      // Assert
      expect(get).toHaveBeenCalledWith('/rooms/1/sub-venues', {})
      expect(result).toEqual(mockResponse)
    })
  })

  describe('createSubVenue', () => {
    it('正确调用创建分会场', async () => {
      // Arrange
      const mockPayload = { 
        title: 'Sub Room', 
        parent_room_id: '1' 
      }
      const mockResponse = { id: '2', title: 'Sub Room' }
      vi.mocked(post).mockResolvedValue(mockResponse)

      // Act
      const result = await roomApi.createSubVenue(mockPayload)

      // Assert
      expect(post).toHaveBeenCalledWith('/rooms', mockPayload, { auth: true })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateSubVenue', () => {
    it('正确调用更新分会场', async () => {
      // Arrange
      const mockData = { title: 'Updated Sub Room' }
      const mockResponse = { id: '2', title: 'Updated Sub Room' }
      vi.mocked(patch).mockResolvedValue(mockResponse)

      // Act
      const result = await roomApi.updateSubVenue('2', mockData)

      // Assert
      expect(patch).toHaveBeenCalledWith('/rooms/2', mockData, { auth: true })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteSubVenue', () => {
    it('正确调用删除分会场', async () => {
      // Arrange
      vi.mocked(del).mockResolvedValue(undefined)

      // Act
      await roomApi.deleteSubVenue('2')

      // Assert
      expect(del).toHaveBeenCalledWith('/rooms/2', undefined, { auth: true })
    })
  })
})