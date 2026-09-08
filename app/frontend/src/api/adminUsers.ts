import { get, patch } from '@/utils/request';
import type { AdminUser, AdminUserQueryParams } from '@/types/adminUser';
import type { ApiResponse, PaginatedResponse } from '@/types/common';
import { AUTH_API_URL } from '@/constants/api';

const usersUrl = (path: string) => `${AUTH_API_URL.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;

export const getAdminUsers = (
  params: AdminUserQueryParams = {}
): Promise<ApiResponse<PaginatedResponse<AdminUser>>> => {
  return get<ApiResponse<PaginatedResponse<AdminUser>>>(usersUrl('/admin/users'), params, { auth: true, showLoading: false }, { retry: 1, timeout: 8000 });
};

export const updateAdminUser = (
  userUuid: string,
  data: { role?: string; status?: string; can_stream?: boolean }
): Promise<ApiResponse<AdminUser>> => {
  return patch<ApiResponse<AdminUser>>(usersUrl(`/admin/users/${userUuid}`), data, { auth: true });
};
