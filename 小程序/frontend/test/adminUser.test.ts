import { describe, expect, it } from 'vitest'
import { API_PATHS } from '../src/config/api'
import {
  canChangeUserRole,
  canEditAdminUser,
  getDailyRoleFilterOptions,
  getDailyStatusOptions,
  getEditableRoleOptions,
  getAdminUserRoleLabel,
  isAdminRole,
  isSuperAdminRole,
  normalizeAdminUserResponse,
  normalizeAdminUserRole,
  normalizeCanStream
} from '../src/types/adminUser'

describe('admin user API paths', () => {
  it('routes admin users through users gateway', () => {
    expect(API_PATHS.ADMIN_USER.USERS).toBe('http://localhost:8080/api/users/admin/users')
    expect(API_PATHS.ADMIN_USER.USER_DETAIL('550e8400-e29b-41d4-a716-446655440000')).toBe(
      'http://localhost:8080/api/users/admin/users/550e8400-e29b-41d4-a716-446655440000'
    )
  })

  it('does not route admin users through core gateway', () => {
    expect(API_PATHS.ADMIN_USER.USERS).not.toContain('/api/core/')
    expect(API_PATHS.ADMIN_USER.USER_DETAIL('test')).not.toContain('/api/core/')
  })

  it('keeps core admin routes on core gateway', () => {
    expect(API_PATHS.ADMIN.CATEGORIES).toContain('/api/core/admin/categories')
    expect(API_PATHS.ADMIN.CATEGORIES).not.toContain('/api/users/')
  })
})

describe('admin user permission helpers (V2)', () => {
  it('detects admin roles case-insensitively', () => {
    expect(isAdminRole('ADMIN')).toBe(true)
    expect(isAdminRole('admin')).toBe(true)
    expect(isSuperAdminRole('SUPERADMIN')).toBe(true)
    expect(isAdminRole('REGULAR')).toBe(false)
  })

  it('only superadmin can change role', () => {
    expect(canChangeUserRole('ADMIN')).toBe(false)
    expect(canChangeUserRole('SUPERADMIN')).toBe(true)
  })

  it('blocks admin from editing superadmin users', () => {
    expect(canEditAdminUser('SUPERADMIN', 'ADMIN')).toBe(false)
    expect(canEditAdminUser('REGULAR', 'ADMIN')).toBe(true)
    expect(canEditAdminUser('SUPERADMIN', 'SUPERADMIN')).toBe(true)
  })

  it('blocks editing self', () => {
    expect(
      canEditAdminUser('ADMIN', 'ADMIN', {
        targetPublicId: 'u-1',
        operatorPublicId: 'u-1'
      })
    ).toBe(false)
    expect(
      canEditAdminUser('REGULAR', 'ADMIN', {
        targetPublicId: 'u-2',
        operatorPublicId: 'u-1'
      })
    ).toBe(true)
  })

  it('hides role picker for normal admins and hides MODERATOR for superadmin', () => {
    expect(getEditableRoleOptions('ADMIN')).toEqual([])
    expect(getEditableRoleOptions('SUPERADMIN')).toEqual(['REGULAR', 'ADMIN', 'SUPERADMIN'])
    expect(getEditableRoleOptions('SUPERADMIN')).not.toContain('MODERATOR')
  })

  it('daily filters hide MODERATOR and non-primary statuses', () => {
    expect(getDailyRoleFilterOptions('ADMIN')).toEqual(['REGULAR', 'ADMIN'])
    expect(getDailyRoleFilterOptions('SUPERADMIN')).toEqual(['REGULAR', 'ADMIN', 'SUPERADMIN'])
    expect(getDailyStatusOptions()).toEqual(['NORMAL', 'BANNED'])
  })

  it('maps legacy lowercase admin role to 管理员 label', () => {
    expect(normalizeAdminUserRole('admin')).toBe('ADMIN')
    expect(getAdminUserRoleLabel('admin')).toBe('管理员')
    expect(getAdminUserRoleLabel('moderator')).toBe('版主')
  })

  it('defaults can_stream to true when missing (V2.1)', () => {
    expect(normalizeCanStream(undefined)).toBe(true)
    expect(normalizeCanStream(null)).toBe(true)
    expect(normalizeCanStream(true)).toBe(true)
    expect(normalizeCanStream(false)).toBe(false)
    const normalized = normalizeAdminUserResponse({
      id: 1,
      public_id: 'x',
      username: 'u',
      nickname: 'n',
      email: null,
      phone_number: null,
      avatar_url: null,
      bio: null,
      role: 'REGULAR',
      status: 'NORMAL',
      is_email_verified: false,
      is_phone_verified: false,
      last_login_at: null,
      last_login_ip: null,
      social_provider: null,
      social_id: null,
      created_at: '',
      updated_at: ''
    } as any)
    expect(normalized.can_stream).toBe(true)
  })
})
