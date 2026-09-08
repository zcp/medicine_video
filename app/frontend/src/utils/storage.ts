/**
 * 本地存储封装工具
 * 阶段一新建：2025
 * 封装uni-app的本地存储API，集成日志和安全脱敏
 */

import { logger } from '@/utils/logger';
import { autoDesensitize } from '@/utils/security';

/**
 * 获取本地存储数据
 * @param key 存储键名
 * @returns Promise<T | null> 存储的数据，失败返回null
 * @example
 * const userInfo = await getStorage<User>('userInfo');
 * if (userInfo) {
 *   console.log(userInfo.name);
 * }
 */
export const getStorage = async <T = any>(key: string): Promise<T | null> => {
  try {
    const result = await new Promise<T>((resolve, reject) => {
      uni.getStorage({
        key,
        success: (res) => {
          logger.info('读取存储成功', { key });
          resolve(res.data as T);
        },
        fail: reject,
      });
    });
    return result;
  } catch (error) {
    logger.error('读取存储失败', { key, error });
    // 不抛出异常，返回null，避免中断业务流程
    return null;
  }
};

/**
 * 设置本地存储数据
 * @param key 存储键名
 * @param value 要存储的数据
 * @example
 * await setStorage('userInfo', { name: '张三', phone: '13800138000' });
 */
export const setStorage = async <T = any>(key: string, value: T): Promise<void> => {
  try {
    // 自动脱敏敏感数据后记录日志
    logger.info('设置存储', { key, value: autoDesensitize(value) });
    
    await new Promise<void>((resolve, reject) => {
      uni.setStorage({
        key,
        data: value,
        success: () => resolve(),
        fail: reject,
      });
    });
  } catch (error) {
    logger.error('设置存储失败', { key, error });
    throw error; // 抛出异常，让调用方处理
  }
};

/**
 * 删除本地存储数据
 * @param key 存储键名
 * @example
 * await removeStorage('userInfo');
 */
export const removeStorage = async (key: string): Promise<void> => {
  try {
    logger.info('删除存储', { key });
    
    await new Promise<void>((resolve, reject) => {
      uni.removeStorage({
        key,
        success: () => resolve(),
        fail: reject,
      });
    });
  } catch (error) {
    logger.error('删除存储失败', { key, error });
    throw error;
  }
};

/**
 * 清空所有本地存储数据
 * @example
 * await clearStorage();
 */
export const clearStorage = async (): Promise<void> => {
  try {
    logger.warn('清空所有存储');
    
    await new Promise<void>((resolve, reject) => {
      uni.clearStorage({
        success: () => resolve(),
        fail: reject,
      });
    });
  } catch (error) {
    logger.error('清空存储失败', { error });
    throw error;
  }
};
