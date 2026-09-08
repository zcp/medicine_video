/**
 * 品牌相关API
 * 公开：GET /brands, GET /brands/{id}/content, GET /rooms/{id}/brands
 * Admin：POST/PATCH/DELETE /admin/brands, logo, rooms
 * 非目标：本版不做专题关联 UI；不做品牌成员 / 成员货架
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'

// ===== 公开接口 =====
export const getBrandList = (params?: { q?: string; limit?: number }) =>
  request.get(API_PATHS.BRAND.LIST, {
    data: params
      ? {
          ...params,
          keyword: params.q
        }
      : params,
    auth: false
  })

export const getBrandContent = (brandId: string) =>
  request.get(API_PATHS.BRAND.CONTENT(brandId), { auth: false })

export const getRoomBrands = (roomId: string) =>
  request.get(API_PATHS.BRAND.ROOM_BRANDS(roomId))

// ===== Admin 接口 =====
export const getAdminBrandList = (params?: {
  page?: number
  size?: number
  name?: string
  is_active?: boolean
  sort?: string
}) => request.get(API_PATHS.BRAND.ADMIN_LIST, { data: params })

export const getAdminBrandDetail = (brandId: string) =>
  request.get(API_PATHS.BRAND.ADMIN_DETAIL(brandId))

export const getAdminBrandRooms = (brandId: string, params?: { page?: number; size?: number }) =>
  request.get(API_PATHS.BRAND.ADMIN_ROOMS(brandId), { data: params, showError: false })

export const createBrand = (data: any) =>
  request.post(API_PATHS.BRAND.ADMIN_LIST, data, { loading: true, loadingText: '创建中...' })

export const updateBrand = (brandId: string, data: any) =>
  request.patch(API_PATHS.BRAND.ADMIN_DETAIL(brandId), data, { loading: true, loadingText: '更新中...' })

export const deleteBrand = (brandId: string) =>
  request.delete(API_PATHS.BRAND.ADMIN_DETAIL(brandId), { loading: true, loadingText: '停用中...' })

/** POST /admin/brands/{id}/logo — multipart file */
export const uploadBrandLogo = (brandId: string, filePath: string) =>
  request.upload({
    url: API_PATHS.BRAND.ADMIN_LOGO(brandId),
    filePath,
    name: 'file',
    loading: true,
    loadingText: '上传 Logo 中...',
    showError: false
  })

/** 专题关联 API 保留封装；本版管理端 UI 不接线 */
export const addBrandTopics = (brandId: string, data: { topic_ids: string[] }) =>
  request.post(API_PATHS.BRAND.ADMIN_TOPICS(brandId), data, { loading: true })

export const removeBrandTopic = (brandId: string, topicId: string) =>
  request.delete(API_PATHS.BRAND.ADMIN_TOPIC_DETAIL(brandId, topicId), { loading: true })

export default {
  getBrandList,
  getBrandContent,
  getRoomBrands,
  getAdminBrandList,
  getAdminBrandDetail,
  getAdminBrandRooms,
  createBrand,
  updateBrand,
  deleteBrand,
  uploadBrandLogo,
  addBrandTopics,
  removeBrandTopic
}
