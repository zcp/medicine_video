/**
 * 标签 chip 纯逻辑工具（create/edit 共享，防两页复制漂移）
 * 定位：只做本地状态运算（去重 / 同名判定 / 差集剔除），不发起任何请求；
 * 服务端归因（4001 → 启用词表全集差集）由调用方拉取词表后调用 pruneInactiveChips。
 */

import type { TagChip } from '@/types/tag'

/** 归一化标签名：trim + 小写（仅用于同名判定；展示仍用原名） */
export const normalizeTagName = (name: string): string => name.trim().toLowerCase()

/** 标签名精确相等判定（trim + 小写；忽略大小写差异） */
export const tagNamesEqual = (a: string, b: string): boolean => normalizeTagName(a) === normalizeTagName(b)

/** chips 中是否存在同名 chip（不同 id 同名视为重复，防重复添加） */
export const hasChipName = (chips: TagChip[], name: string): boolean =>
  chips.some((c) => tagNamesEqual(c.name, name))

/** chips 中是否存在指定 id */
export const hasChipId = (chips: TagChip[], id: string): boolean => chips.some((c) => c.id === id)

/**
 * 追加 chip（幂等去重）：id 重复或同名重复 → 返回原数组引用（不变）；
 * 否则返回追加后的新数组。非法 chip（缺 id/name）直接忽略。
 */
export const pushChipUnique = (chips: TagChip[], chip: TagChip): TagChip[] => {
  if (!chip?.id || !chip?.name) return chips
  if (hasChipId(chips, chip.id) || hasChipName(chips, chip.name)) return chips
  return [...chips, { id: chip.id, name: chip.name }]
}

/**
 * 剔除已失效 chip（启用词表差集）：仅保留 id 仍出现在 activeTags 中的 chip。
 * 防御性降级（§4.7）：activeTags 非数组（后端未来若改信封）→ 原样返回不剔除，
 * 避免把「未返回的启用词」误判为失效而误删。
 */
export const pruneInactiveChips = (chips: TagChip[], activeTags: unknown): TagChip[] => {
  if (!Array.isArray(activeTags)) return chips
  if (chips.length === 0) return chips
  const activeIds = new Set(
    activeTags
      .map((t) => (t && typeof t === 'object' && 'id' in t ? (t as { id: unknown }).id : undefined))
      .filter((id): id is string => typeof id === 'string')
  )
  const retained = chips.filter((c) => activeIds.has(c.id))
  return retained.length === chips.length ? chips : retained
}
