export type UserRoleType = 'REGULAR' | 'MODERATOR' | 'ADMIN' | 'SUPERADMIN';
export type UserStatusType = 'NORMAL' | 'BANNED' | 'DELETED' | 'PENDING_REVIEW' | 'REJECTED';

export interface AdminUser {
  public_id: string;
  username: string;
  nickname: string;
  email?: string;
  phone_number?: string;
  avatar_url?: string;
  bio?: string;
  role: UserRoleType;
  status: UserStatusType;
  can_stream: boolean;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AdminUserQueryParams {
  page?: number;
  size?: number;
  keyword?: string;           // 统一关键词模糊搜索（跨 username/email/nickname/phone_number，后端 OR 语义）
  username?: string;
  email?: string;
  phone_number?: string;  // 手机号精确筛选（后端支持）
  nickname?: string;      // 昵称模糊筛选（后端支持）
  role?: string;
  status?: string;
  can_stream?: boolean | 'true' | 'false'; // 筛选；false/'false'=禁播（App GET 宜用字符串防序列化丢失）
}
