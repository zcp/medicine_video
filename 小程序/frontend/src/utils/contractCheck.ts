/**
 * 运行时契约校验工具（仅用于开发期日志提示）
 * - 不抛异常，避免影响线上
 * - 用于发现“后端返回字段/前端预期字段”不一致
 */

export type ContractDiff = {
  ok: boolean
  missingRequiredKeys: string[]
  extraKeys: string[]
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/**
 * 校验对象 keys 是否严格落在 allowList 中，并且包含 requiredKeys。
 */
export function diffObjectKeys(
  value: unknown,
  allowList: readonly string[],
  requiredKeys: readonly string[] = []
): ContractDiff {
  if (!isPlainObject(value)) {
    return {
      ok: false,
      missingRequiredKeys: [...requiredKeys],
      extraKeys: []
    }
  }

  const keys = Object.keys(value)
  const allowSet = new Set(allowList)
  const requiredSet = new Set(requiredKeys)

  const extraKeys = keys.filter(k => !allowSet.has(k))
  const missingRequiredKeys = [...requiredSet].filter(k => !(k in value))

  return {
    ok: extraKeys.length === 0 && missingRequiredKeys.length === 0,
    extraKeys,
    missingRequiredKeys
  }
}
