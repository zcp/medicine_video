import { get, post, patch, del } from '@/utils/request';
import type {
  ExpertDepartment,
  ExpertDepartmentCreatePayload,
  ExpertDepartmentUpdatePayload,
  DepartmentQueryParams,
  UnmappedExpert,
} from '@/types/department';
import type { ApiResponse, PaginatedResponse } from '@/types/common';

export const getDepartments = (
  params: DepartmentQueryParams = {},
  options: { showLoading?: boolean; retry?: number; timeout?: number } = {}
): Promise<ApiResponse<PaginatedResponse<ExpertDepartment>>> => {
  return get<ApiResponse<PaginatedResponse<ExpertDepartment>>>(
    '/admin/expert-departments',
    params,
    { auth: true, showLoading: options.showLoading },
    { retry: options.retry, timeout: options.timeout }
  );
};

export const createDepartment = (
  data: ExpertDepartmentCreatePayload
): Promise<ApiResponse<{ id: string; name: string; category_id: string }>> => {
  return post<ApiResponse<{ id: string; name: string; category_id: string }>>('/admin/expert-departments', data, { auth: true });
};

export const updateDepartment = (
  departmentId: string,
  data: ExpertDepartmentUpdatePayload
): Promise<ApiResponse<{ id: string; name: string; is_verified: boolean }>> => {
  return patch<ApiResponse<{ id: string; name: string; is_verified: boolean }>>(`/admin/expert-departments/${departmentId}`, data, { auth: true });
};

export const deleteDepartment = (
  departmentId: string
): Promise<ApiResponse<{ message: string }>> => {
  return del<ApiResponse<{ message: string }>>(`/admin/expert-departments/${departmentId}`, undefined, { auth: true });
};

export const getUnmappedExperts = (
  params: { page?: number; size?: number } = {},
  options?: { showLoading?: boolean }
): Promise<ApiResponse<PaginatedResponse<UnmappedExpert>>> => {
  return get<ApiResponse<PaginatedResponse<UnmappedExpert>>>('/admin/expert-departments/unmapped', params, { auth: true, ...options }, { retry: 1, timeout: 8000 });
};

export const mergeDepartments = (
  sourceId: string,
  targetId: string
): Promise<ApiResponse<any>> => {
  return post<ApiResponse<any>>('/admin/expert-departments/merge', { source_id: sourceId, target_id: targetId }, { auth: true });
};

export const updateDepartmentCategory = (
  departmentId: string,
  categoryId: string
): Promise<ApiResponse<{ id: string; name: string; category_id: string; category_name: string }>> => {
  return patch<ApiResponse<{ id: string; name: string; category_id: string; category_name: string }>>(
    `/admin/expert-departments/${departmentId}/category`,
    { category_id: categoryId },
    { auth: true }
  );
};

export const batchVerifyDepartments = (data: {
  department_ids: string[];
  verified: boolean;
}): Promise<ApiResponse<{ success_count: number; failed_count: number }>> => {
  return post<ApiResponse<{ success_count: number; failed_count: number }>>('/admin/expert-departments/batch-verify', data, { auth: true });
};

export const getDepartmentDetail = (departmentId: string): Promise<ApiResponse<ExpertDepartment>> => {
  return get<ApiResponse<ExpertDepartment>>(`/admin/expert-departments/${departmentId}`, {}, { auth: true });
};
