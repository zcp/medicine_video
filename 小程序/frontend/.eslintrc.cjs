module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
    'vue/setup-compiler-macros': true
  },
  extends: [
    'eslint:recommended',
    '@vue/eslint-config-typescript/recommended',
    '@vue/eslint-config-prettier/skip-formatting'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  plugins: ['vue', '@typescript-eslint'],
  rules: {
    // Vue相关规则
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'off',
    'vue/require-default-prop': 'off',
    'vue/require-explicit-emits': 'error',
    'vue/require-prop-types': 'error',
    'vue/component-name-in-template-casing': ['error', 'PascalCase'],
    
    // TypeScript相关规则
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
    '@typescript-eslint/prefer-nullish-coalescing': 'error',
    '@typescript-eslint/prefer-optional-chain': 'error',
    
    // 通用规则
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-var': 'error',
    'prefer-const': 'error',
    'prefer-template': 'error',
    'object-shorthand': 'error',
    'arrow-spacing': 'error',
    'comma-dangle': ['error', 'never'],
    'semi': ['error', 'never'],
    'quotes': ['error', 'single'],
    
    // uni-app特定规则
    'no-undef': 'off' // uni-app全局变量
  },
  globals: {
    // uni-app全局变量
    uni: 'readonly',
    wx: 'readonly',
    getCurrentPages: 'readonly',
    getApp: 'readonly',
    
    // 微信小程序全局变量
    App: 'readonly',
    Page: 'readonly',
    Component: 'readonly',
    Behavior: 'readonly'
  },
  ignorePatterns: [
    'dist',
    'node_modules',
    'unpackage',
    '*.d.ts'
  ]
}
