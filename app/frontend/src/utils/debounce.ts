/**
 * 防抖和节流工具函数
 * @description 用于防止用户快速点击导致的重复请求
 */

/**
 * 防抖函数
 * @description 在事件触发n秒后才执行，如果在n秒内又触发，则重新计时
 * @param func 要执行的函数
 * @param wait 等待时间（毫秒）
 * @returns 防抖后的函数
 * 
 * @example
 * const handleSearch = debounce((keyword: string) => {
 *   searchApi(keyword);
 * }, 300);
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  
  return function(this: any, ...args: Parameters<T>) {
    const context = this;
    
    if (timeout !== null) {
      clearTimeout(timeout);
    }
    
    timeout = setTimeout(() => {
      func.apply(context, args);
      timeout = null;
    }, wait);
  };
}

/**
 * 节流函数
 * @description 在n秒内只执行一次，如果在n秒内多次触发，只有第一次生效
 * @param func 要执行的函数
 * @param wait 等待时间（毫秒）
 * @returns 节流后的函数
 * 
 * @example
 * const handleScroll = throttle(() => {
 *   loadMore();
 * }, 1000);
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  let previous = 0;
  
  return function(this: any, ...args: Parameters<T>) {
    const context = this;
    const now = Date.now();
    const remaining = wait - (now - previous);
    
    if (remaining <= 0 || remaining > wait) {
      if (timeout !== null) {
        clearTimeout(timeout);
        timeout = null;
      }
      previous = now;
      func.apply(context, args);
    } else if (timeout === null) {
      timeout = setTimeout(() => {
        previous = Date.now();
        timeout = null;
        func.apply(context, args);
      }, remaining);
    }
  };
}

/**
 * 异步防抖函数（支持Promise）
 * @description 防抖的同时支持异步操作，避免重复请求
 * @param func 要执行的异步函数
 * @param wait 等待时间（毫秒）
 * @returns 防抖后的异步函数
 * 
 * @example
 * const handleSubscribe = debounceAsync(async (sessionId: string) => {
 *   await subscriptionStore.subscribe('session', sessionId);
 * }, 300);
 */
export function debounceAsync<T extends (...args: any[]) => Promise<any>>(
  func: T,
  wait: number
): (...args: Parameters<T>) => Promise<ReturnType<T>> {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  let pendingPromise: Promise<ReturnType<T>> | null = null;
  
  return function(this: any, ...args: Parameters<T>): Promise<ReturnType<T>> {
    const context = this;
    
    if (timeout !== null) {
      clearTimeout(timeout);
    }
    
    if (!pendingPromise) {
      pendingPromise = new Promise((resolve, reject) => {
        timeout = setTimeout(async () => {
          try {
            const result = await func.apply(context, args);
            resolve(result);
          } catch (error) {
            reject(error);
          } finally {
            timeout = null;
            pendingPromise = null;
          }
        }, wait);
      });
    }
    
    return pendingPromise;
  };
}

/**
 * 请求锁（防止重复请求）
 * @description 确保同一时间只有一个请求在执行
 * 
 * @example
 * const requestLock = new RequestLock();
 * 
 * async function handleSubscribe() {
 *   if (requestLock.isLocked()) {
 *     console.log('请求进行中，请稍候...');
 *     return;
 *   }
 *   
 *   requestLock.lock();
 *   try {
 *     await subscriptionStore.subscribe('session', sessionId);
 *   } finally {
 *     requestLock.unlock();
 *   }
 * }
 */
export class RequestLock {
  private locked: boolean = false;
  
  /**
   * 检查是否已锁定
   */
  isLocked(): boolean {
    return this.locked;
  }
  
  /**
   * 加锁
   */
  lock(): void {
    this.locked = true;
  }
  
  /**
   * 解锁
   */
  unlock(): void {
    this.locked = false;
  }
  
  /**
   * 执行带锁的异步操作
   * @param func 要执行的异步函数
   * @returns Promise
   */
  async execute<T>(func: () => Promise<T>): Promise<T | null> {
    if (this.isLocked()) {
      console.warn('⚠️ 请求进行中，跳过重复请求');
      return null;
    }
    
    this.lock();
    try {
      return await func();
    } finally {
      this.unlock();
    }
  }
}
