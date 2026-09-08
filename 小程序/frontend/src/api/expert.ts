/**
 * 专家相关API - 重构版本
 */

import { request } from '@/utils/request'
import { API_PATHS } from '@/config/api'
import { log } from '@/logs/logger'
import type { MyExpertUpdatePayload } from '@/types/expertMe'

export type SessionExpertItem = {
	id: string
	name: string
	title?: string
	hospital?: string
	avatar_url?: string
	role?: string
	sort_order?: number
}

export type FollowedExpertItem = {
	expert_id: string
	name?: string
	avatar_url?: string
	title?: string
	hospital?: string
	subscribed_at: string
	live_status?: {
		is_live?: boolean
		session_id?: string
	}
}

export type ExpertInfoItem = {
	id: string
	name: string
	avatar_url?: string
	title?: string
	hospital?: string
	/** 过渡文本科室 */
	department?: string | null
	/** 词表科室 ID（《20》） */
	department_id?: string | null
	/** 词表科室名；展示优先 */
	department_name?: string | null
	category_id?: string | null
	category_name?: string | null
	bio?: string
	expertise_areas?: string
}

export type ExpertSessionBriefItem = {
	id: string
	room_id?: string
	roomId?: string
	room_title: string
	cover_url?: string
	status?: string
	start_time?: string
}

// ===== 专家基本信息 (core服务) =====
export const getExpertList = async (params?: any) => {
	const url = API_PATHS.EXPERT.LIST
	log.info('api', '[getExpertList] 发起请求', { url, params })
	const res = await request.get(url, { data: params })
	log.info('api', '[getExpertList] 响应', { code: res?.code, hasData: !!res?.data, dataType: typeof res?.data, dataKeys: res?.data ? Object.keys(res.data) : [], rawPreview: JSON.stringify(res?.data)?.slice(0, 800) })
	return res
}
export const getFeaturedExperts = (limit: number = 50) => request.get(API_PATHS.EXPERT.FEATURED, { data: { limit }, showError: false })
/** 专家详情；补头像等场景传 quiet，避免已下架专家刷 ERROR 日志 */
export const getExpertDetail = (
	id: string,
	config?: { showError?: boolean; quiet?: boolean; auth?: boolean }
) =>
	request.get(API_PATHS.EXPERT.DETAIL(id), {
		showError: config?.showError ?? true,
		quiet: config?.quiet,
		auth: config?.auth
	})
export const getExpertSessions = (expertId: string, params?: { page?: number; size?: number }) =>
	request.get(API_PATHS.EXPERT.SESSIONS(expertId), { data: params, showError: false })

// ===== 专家内容 (注意：这里仍使用professors路径) =====
export const getExpertContent = (expertId: string) => request.get(API_PATHS.EXPERT.CONTENT(expertId))

// ===== 场次专家管理 =====
export const getSessionExperts = (sessionId: string) => request.get(API_PATHS.EXPERT.SESSION_EXPERTS(sessionId))
export const setSessionExperts = (sessionId: string, payload: any[]) =>
	request.post(API_PATHS.EXPERT.SET_SESSION_EXPERTS(sessionId), payload, { loading: true, loadingText: '保存中...' })

// ===== 专家关注状态检查 =====
export const getExpertFollowStatus = (expertId: string) =>
	request.get(API_PATHS.EXPERT.IS_FOLLOWED(expertId), { showError: false })

// ===== 用户关注的专家 (core服务, 独立路由: /api/v1/users/me/followed-experts → core_api) =====
export const getMyFollowedExperts = (params?: { include_live_status?: boolean }) =>
	request.get(API_PATHS.USER_EXPERT_FOLLOW.FOLLOWED_EXPERTS, { data: params, showError: false })

export const followExpert = (expertId: string) =>
	request.post(API_PATHS.USER_EXPERT_FOLLOW.FOLLOWED_EXPERTS, { expert_id: expertId }, { loading: true, loadingText: '关注中...' })

export const unfollowExpert = (expertId: string) =>
	request.delete(API_PATHS.USER_EXPERT_FOLLOW.UNFOLLOW_EXPERT(expertId), { loading: true, loadingText: '取消关注中...' })

// ===== 管理员专家管理 =====
export const getAdminExpertList = async (params?: {
	page?: number
	size?: number
	name?: string
	hospital?: string
	is_featured?: boolean
}) => {
	const url = API_PATHS.ADMIN.EXPERTS
	log.info('api', '[getAdminExpertList] 发起请求', { url, params })
	const res = await request.get(url, { data: params, showError: false })
	log.info('api', '[getAdminExpertList] 响应', { code: res?.code, hasData: !!res?.data, dataType: typeof res?.data, dataKeys: res?.data ? Object.keys(res.data) : [], rawPreview: JSON.stringify(res?.data)?.slice(0, 800) })
	return res
}

export const createExpert = (data: any) => request.post(API_PATHS.ADMIN.CREATE_EXPERT, data, { loading: true, loadingText: '创建中...' })
export const updateExpert = (expertId: string, data: any) => request.patch(API_PATHS.ADMIN.UPDATE_EXPERT(expertId), data, { loading: true, loadingText: '更新中...' })
export const deleteExpert = (expertId: string) => request.delete(API_PATHS.ADMIN.DELETE_EXPERT(expertId), { loading: true, loadingText: '删除中...' })

/** POST /admin/experts/{id}/avatar — multipart file */
export const uploadAdminExpertAvatar = (expertId: string, filePath: string) =>
	request.upload({
		url: API_PATHS.ADMIN.EXPERT_AVATAR(expertId),
		filePath,
		name: 'file',
		loading: true,
		loadingText: '上传头像中...',
		showError: false
	})

// ===== 搜索专家（优先走 /experts keyword 查询，空结果时回退精选专家本地筛选） =====
export const searchExperts = (params: any) => {
	const keyword = typeof params?.keyword === 'string'
		? params.keyword
		: (typeof params?.q === 'string' ? params.q : '')
	const page = Number(params?.page || 1)
	const size = Number(params?.size || 20)

	return request.get(API_PATHS.EXPERT.LIST, {
		data: {
			...params,
			q: keyword,
			keyword,
			page,
			size
		},
		showError: false
	}).then(async (resp: any) => {
		const raw = resp?.data
		const items = Array.isArray(raw?.items) ? raw.items : (Array.isArray(raw) ? raw : [])
		if (resp?.code === 200 && items.length > 0) {
			return resp
		}

		if (!keyword) {
			return resp
		}

		try {
			const featuredResp: any = await getFeaturedExperts(50)
			const featuredRaw = featuredResp?.data
			const featuredItems = Array.isArray(featuredRaw?.items)
				? featuredRaw.items
				: (Array.isArray(featuredRaw) ? featuredRaw : [])
			const kw = keyword.trim().toLowerCase()
			const filtered = featuredItems.filter((item: any) => {
				const haystack = [item?.name, item?.title, item?.hospital, item?.department, item?.bio]
					.filter(Boolean)
					.map((value) => String(value).toLowerCase())
					.join(' ')
				return kw ? haystack.includes(kw) : true
			})
			return {
				code: 200,
				message: 'success',
				data: {
					total: filtered.length,
					page,
					size,
					items: filtered.slice((page - 1) * size, page * size),
					hasMore: page * size < filtered.length
				},
				timestamp: new Date().toISOString()
			}
		} catch {
			return resp
		}
	})
}

// ===== P1 专家认领：V2.2 已裁剪（后端 /experts/me* 已删除）=====
const EXPERT_CLAIM_REMOVED = '专家认领功能已下线，请联系运营在管理端维护专家资料'

/** @deprecated V2.2 已裁剪，调用将直接失败，勿再使用 */
export const getMyExpert = () =>
	Promise.reject(Object.assign(new Error(EXPERT_CLAIM_REMOVED), { code: 404, statusCode: 404 }))

/** @deprecated V2.2 已裁剪 */
export const updateMyExpert = (_data: MyExpertUpdatePayload) =>
	Promise.reject(Object.assign(new Error(EXPERT_CLAIM_REMOVED), { code: 404, statusCode: 404 }))

/** @deprecated V2.2 已裁剪 */
export const uploadMyExpertAvatar = (_filePath: string, _syncUserAvatar = true) =>
	Promise.reject(Object.assign(new Error(EXPERT_CLAIM_REMOVED), { code: 404, statusCode: 404 }))

export default {
	getExpertList,
	getFeaturedExperts,
	getExpertDetail,
	getExpertSessions,
	getExpertContent,
	getSessionExperts,
	setSessionExperts,
	getMyFollowedExperts,
	followExpert,
	unfollowExpert,
	getAdminExpertList,
	createExpert,
	updateExpert,
	deleteExpert,
	uploadAdminExpertAvatar,
	getExpertFollowStatus,
	searchExperts,
	getMyExpert,
	updateMyExpert,
	uploadMyExpertAvatar
}
