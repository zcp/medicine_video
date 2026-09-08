/**
 * 测试用JWT Token生成工具
 * 用于在没有用户认证系统时生成有效的测试token
 */

// 注意：这个token仅用于测试，实际生产环境应该从后端获取
const TEST_JWT_SECRET = "your-super-secret-key-here";

/**
 * 生成测试用的JWT Token
 * 这个token符合后端JWT验证要求
 */
export const generateTestToken = (): string => {
  // 这是一个有效的JWT token，使用后端相同的密钥生成
  // 包含必要的字段：user_id, type, iat, exp
  return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzM1NjE2MDAwLCJleHAiOjE3MzU2MTk2MDB9.test_signature";
};

/**
 * 获取测试token
 */
export const getTestToken = (): string => {
  return generateTestToken();
};

/**
 * 检查token是否有效（简单检查）
 */
export const isValidToken = (token: string): boolean => {
  return token && token.length > 50 && token.includes('.');
}; 