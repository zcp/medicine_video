/**
 * 个人信息展示：UID 短码、邮箱脱敏（与设计文档一致）
 */

/** UUID/公开 ID：前 6 + … + 后 4（无连字符时按连续字符截取） */
export function formatShortPublicId(id: string | undefined | null): string {
  if (!id) return '-';
  const clean = id.replace(/-/g, '');
  if (clean.length <= 10) return id;
  return `${clean.slice(0, 6)}...${clean.slice(-4)}`;
}

/** 手机号脱敏：138****8888 风格 */
export function maskPhone(phone: string | undefined | null): string {
  if (!phone) return '未绑定';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length < 7) return phone;
  return `${cleaned.slice(0, 3)}****${cleaned.slice(-4)}`;
}

/** 邮箱脱敏：user***@domain.com 风格 */
export function maskEmail(email: string | undefined | null): string {
  if (!email || !email.includes('@')) return '—';
  const [local, domain] = email.split('@');
  if (!domain) return '—';
  if (!local) return `***@${domain}`;
  if (local.length <= 3) return `${local[0]}***@${domain}`;
  return `${local.slice(0, 3)}***@${domain}`;
}

const ROLE_LABELS: Record<string, string> = {
  REGULAR: '普通用户',
  MODERATOR: '房管',
  ADMIN: '管理员',
  SUPERADMIN: '超管'
};

export function mapRoleLabel(role: string | undefined | null): string {
  if (!role) return '普通用户';
  return ROLE_LABELS[role] || role;
}

const STATUS_LABELS: Record<string, string> = {
  NORMAL: '正常',
  PENDING_REVIEW: '审核中',
  BANNED: '已封禁',
  DELETED: '已注销',
  REJECTED: '已拒绝'
};

export function mapStatusLabel(status: string | undefined | null): string {
  if (!status) return '正常';
  return STATUS_LABELS[status] || status;
}

export type StatusTone = 'normal' | 'warning' | 'danger' | 'muted';

export function mapStatusTone(status: string | undefined | null): StatusTone {
  switch (status) {
    case 'NORMAL':
      return 'normal';
    case 'PENDING_REVIEW':
      return 'warning';
    case 'BANNED':
    case 'REJECTED':
      return 'danger';
    case 'DELETED':
      return 'muted';
    default:
      return 'normal';
  }
}
