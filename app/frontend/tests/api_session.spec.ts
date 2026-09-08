// tests/api/session.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as sessionApi from '../src/api/session'
import { request } from '../src/utils/request'

// Mock request utility
vi.mock('@/utils/request', () => ({
  request: vi.fn()
}))

describe('session.ts API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('getSessionList', () => {
    it('正确调用获取场次列表', async () => {
      // Arrange
      const mockResponse = {
        total: 1,
        page: 1,
        size: 10,
        items: [{ id: '1', title: 'Session 1' }]
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      // Act
      const result = await sessionApi.getSessionList('room-1', { page: 1, size: 10 })

      // Assert
      expect(request).toHaveBeenCalledWith({
        url: '/rooms/room-1/sessions',
        method: 'GET',
        data: { page: 1, size: 10 }
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSessionDetail', () => {
    it('正确调用获取场次详情', async () => {
      // Arrange
      const mockResponse = { id: '1', title: 'Session 1' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      // Act
      const result = await sessionApi.getSessionDetail('1')

      // Assert
      expect(request).toHaveBeenCalledWith({
        url: '/sessions/1',
        method: 'GET'
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('createSession', () => {
    it('正确调用创建场次', async () => {
      // Arrange
      const mockData = { title: 'New Session', start_time: '2023-01-01T00:00:00Z' }
      const mockResponse = { id: '1', title: 'New Session' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      // Act
      const result = await sessionApi.createSession('room-1', mockData)

      // Assert
      expect(request).toHaveBeenCalledWith({
        url: '/rooms/room-1/sessions',
        method: 'POST',
        data: mockData
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateSession', () => {
    it('正确调用更新场次', async () => {
      // Arrange
      const mockData = { status: 'live' as const, end_time: '2023-01-01T01:00:00Z' }
      const mockResponse = { 
        id: '1', 
        room_id: 'room-1',
        status: 'live' as const,
        start_time: '2023-01-01T00:00:00Z',
        end_time: '2023-01-01T01:00:00Z',
        video_id: null,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      // Act
      const result = await sessionApi.updateSession('1', mockData)

      // Assert
      expect(request).toHaveBeenCalledWith({
        url: '/sessions/1',
        method: 'PATCH',
        data: mockData
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteSession', () => {
    it('正确调用删除场次', async () => {
      // Arrange
      const mockResponse = { id: '1', status: 'deleted' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      // Act
      const result = await sessionApi.deleteSession('1')

      // Assert
      expect(request).toHaveBeenCalledWith({
        url: '/sessions/1',
        method: 'DELETE'
      })
      expect(result).toEqual(mockResponse)
    })
  })
})