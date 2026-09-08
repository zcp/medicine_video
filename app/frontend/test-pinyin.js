/**
 * pinyin-pro 兼容性测试
 * 测试库在 uni-app 环境中的基本功能
 */

const { pinyin } = require('pinyin-pro');

console.log('========================================');
console.log('pinyin-pro 兼容性测试');
console.log('========================================\n');

// 测试用例
const tests = [
  {
    name: '测试1: 基础拼音转换（无声调）',
    fn: () => {
      const result = pinyin('张三', { toneType: 'none' });
      console.log(`  输入: pinyin('张三', { toneType: 'none' })`);
      console.log(`  输出: '${result}'`);
      console.log(`  预期: 'zhang san'`);
      console.log(`  结果: ${result === 'zhang san' ? '✅ 通过' : '❌ 失败'}`);
      return result === 'zhang san';
    }
  },
  {
    name: '测试2: 首字母提取',
    fn: () => {
      const result = pinyin('张三', { pattern: 'first', toneType: 'none' });
      console.log(`  输入: pinyin('张三', { pattern: 'first', toneType: 'none' })`);
      console.log(`  输出: '${result}'`);
      console.log(`  预期: 'z s'`);
      console.log(`  结果: ${result === 'z s' ? '✅ 通过' : '❌ 失败'}`);
      return result === 'z s';
    }
  },
  {
    name: '测试3: 数组格式输出（无声调）',
    fn: () => {
      const result = pinyin('张三', { type: 'array', toneType: 'none' });
      console.log(`  输入: pinyin('张三', { type: 'array', toneType: 'none' })`);
      console.log(`  输出:`, result);
      console.log(`  预期: ['zhang', 'san']`);
      const isValid = Array.isArray(result) && result[0] === 'zhang' && result[1] === 'san';
      console.log(`  结果: ${isValid ? '✅ 通过' : '❌ 失败'}`);
      return isValid;
    }
  },
  {
    name: '测试4: 多音字处理',
    fn: () => {
      const result = pinyin('解文');
      console.log(`  输入: '解文'`);
      console.log(`  输出: '${result}'`);
      console.log(`  说明: 多音字可能有多种读音，只要有输出即为通过`);
      const isValid = result.length > 0;
      console.log(`  结果: ${isValid ? '✅ 通过' : '❌ 失败'}`);
      return isValid;
    }
  },
  {
    name: '测试5: 特殊字符和数字混合（无声调）',
    fn: () => {
      const result = pinyin('张@三#123', { toneType: 'none' });
      console.log(`  输入: pinyin('张@三#123', { toneType: 'none' })`);
      console.log(`  输出: '${result}'`);
      console.log(`  说明: 应保留特殊字符，只转换中文`);
      const hasZhang = result.includes('zhang');
      const hasSan = result.includes('san');
      const isValid = hasZhang && hasSan;
      console.log(`  结果: ${isValid ? '✅ 通过' : '❌ 失败'}`);
      return isValid;
    }
  },
  {
    name: '测试6: 空字符串',
    fn: () => {
      const result = pinyin('');
      console.log(`  输入: ''`);
      console.log(`  输出: '${result}'`);
      console.log(`  预期: ''`);
      console.log(`  结果: ${result === '' ? '✅ 通过' : '❌ 失败'}`);
      return result === '';
    }
  },
  {
    name: '测试7: 中英文混合（真实场景）',
    fn: () => {
      const result = pinyin('张伟ABC', { toneType: 'none' });
      console.log(`  输入: pinyin('张伟ABC', { toneType: 'none' })`);
      console.log(`  输出: '${result}'`);
      console.log(`  说明: 中英文混合场景，中文转拼音，英文保持`);
      const hasZhang = result.includes('zhang');
      const hasWei = result.includes('wei');
      const isValid = hasZhang && hasWei;
      console.log(`  结果: ${isValid ? '✅ 通过' : '❌ 失败'}`);
      return isValid;
    }
  }
];

// 运行测试
let passCount = 0;
let failCount = 0;

tests.forEach((test, index) => {
  console.log(`\n${test.name}`);
  console.log('-'.repeat(40));
  try {
    const passed = test.fn();
    if (passed) {
      passCount++;
    } else {
      failCount++;
    }
  } catch (error) {
    console.log(`  结果: ❌ 异常 - ${error.message}`);
    failCount++;
  }
});

// 总结
console.log('\n========================================');
console.log('测试总结');
console.log('========================================');
console.log(`总计: ${tests.length} 个测试`);
console.log(`✅ 通过: ${passCount} 个`);
console.log(`❌ 失败: ${failCount} 个`);
console.log(`成功率: ${((passCount / tests.length) * 100).toFixed(1)}%`);
console.log('========================================\n');

if (failCount === 0) {
  console.log('🎉 恭喜！所有测试通过，pinyin-pro 可以正常使用！\n');
  process.exit(0);
} else {
  console.log('⚠️  警告：部分测试失败，请检查库的兼容性。\n');
  process.exit(1);
}
