/**
 * 微信 DevTools 把 console.warn([], circularObj) 显示成 [] [object Object]。
 * 必须在 Vue/uni 任何 console 调用之前打补丁：由 vite 注入到 vendor.js 顶部，
 * 并在 main.ts 再 import 一次作为双保险。
 */

const PATCHED = '__liveSaasConsolePatched'

function toConsoleText(value: unknown): string {
  if (value == null) return String(value)
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (typeof value === 'symbol') return value.toString()
  if (typeof value === 'function') return `[Function ${value.name || 'anonymous'}]`
  if (value instanceof Error) return `${value.name}: ${value.message}`
  if (Array.isArray(value)) {
    if (value.length === 0) return ''
    try {
      return JSON.stringify(value)
    } catch {
      return `[Array(${value.length})]`
    }
  }
  try {
    return JSON.stringify(value)
  } catch {
    try {
      const keys = Object.keys(value as object).slice(0, 8)
      return keys.length ? `{${keys.join(',')}}` : ''
    } catch {
      return ''
    }
  }
}

function shouldDrop(text: string): boolean {
  if (!text) return true
  if (text === '[object Object]') return true
  if (/^\[\]\s*(\[object Object\])?$/.test(text)) return true
  if (/^\[object Object\]$/.test(text)) return true
  return false
}

export function patchConsoleForWeixinMp(): void {
  const g = globalThis as typeof globalThis & { [PATCHED]?: boolean }
  if (g[PATCHED]) return
  g[PATCHED] = true

  ;(['log', 'info', 'warn', 'error', 'debug'] as const).forEach((method) => {
    const original = console[method].bind(console)
    console[method] = (...args: unknown[]) => {
      const text = args
        .map(toConsoleText)
        .map((s) => s.trim())
        .filter(Boolean)
        .join(' ')
      if (shouldDrop(text)) return
      original(text)
    }
  })
}

patchConsoleForWeixinMp()
