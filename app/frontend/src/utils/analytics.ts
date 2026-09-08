/**
 * 埋点分析工具
 * 统一管理所有埋点事件
 */

/**
 * 埋点上报基类
 */
class Analytics {
  /**
   * 脱敏处理参数
   */
  private sanitizeParams(params: Record<string, any>): Record<string, any> {
    const sanitized = { ...params };
    
    // 移除敏感字段
    const sensitiveKeys = ['phone', 'id_card', 'password', 'token', 'email'];
    sensitiveKeys.forEach(key => {
      if (key in sanitized) {
        delete sanitized[key];
      }
    });
    
    return sanitized;
  }
  
  /**
   * 埋点上报
   */
  private track(eventName: string, params: Record<string, any> = {}) {
    const sanitizedParams = this.sanitizeParams(params);
    
    // 开发环境打印埋点信息
    if (import.meta.env.DEV) {
      console.log('[Analytics]', eventName, sanitizedParams);
    }
    
    // TODO: 接入实际的埋点SDK（如神策、友盟等）
    // 示例：sa.track(eventName, sanitizedParams);
  }
  
}

// 导出单例
export const analytics = new Analytics();
