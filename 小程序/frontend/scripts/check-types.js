const { execSync } = require('child_process')
const path = require('path')

/**
 * 类型检查脚本（使用项目 tsconfig）
 *
 * 说明：旧实现按“单文件 + isolatedModules”逐个跑 tsc，会忽略项目 tsconfig，
 * 导致 uni/wx、import.meta、esModuleInterop 等配置失效，从而产生大量误报。
 *
 * 这里改为使用 vue-tsc 读取 tsconfig.json 做一次全量类型检查。
 */

function checkTypes() {
  console.log('🔍 开始TypeScript类型检查...\n')
  const cwd = path.join(__dirname, '..')
  // 注意：主 tsconfig.json 引用了 tsconfig.node.json（composite + declaration），
  // vue-tsc 在 noEmit 模式下会触发 TS6305（要求先构建 dist/node/*.d.ts）。
  // 因此前端类型检查使用专用配置，避免被 node 子工程的 build 输出阻塞。
  const cmd = 'npx vue-tsc --noEmit -p tsconfig.vuetsc.json'
  execSync(cmd, { stdio: 'inherit', cwd })
}

try {
  checkTypes()
  console.log('\n🎉 类型检查通过！')
  process.exit(0)
} catch (error) {
  process.exit(1)
}
