/**
 * 科室分类组合函数
 * @description 适用于首页、品牌分类、专家分类等所有需要科室分类的场景
 * @author 直播SaaS团队
 *
 * 使用场景：
 *   - 首页科室分类 Tab 导航
 *   - 品牌分类筛选
 *   - 专家分类筛选
 *
 * 返回数据：只返回 is_active=true 的分类，按 sort_order 升序排列
 */

import { ref, onMounted } from 'vue'
import { logger } from '@/logs/logger'
import { getAllCategories } from '@/api/categories'
import type { Category } from '@/types/category'

/**
 * 科室分类组合函数
 * @returns categories - 分类列表（只包含 is_active=true 的分类）
 * @returns loading - 加载状态
 * @returns error - 错误信息
 * @returns refresh - 刷新数据方法
 */
export function useCategory() {
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchCategories = async () => {
    loading.value = true
    error.value = null
    try {
      logger.info('network', '[useCategory] 加载科室分类')
      categories.value = await getAllCategories()
      logger.info('network', '[useCategory] 科室分类加载完成', {
        count: categories.value.length,
        sample: categories.value.slice(0, 5).map(c => ({
          id: c.id,
          name: c.name,
          sort_order: c.sort_order
        }))
      })
    } catch (err: any) {
      error.value = err.message || '加载分类失败'
      logger.error('system', '[useCategory] 加载科室分类失败', { error: err })
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchCategories()
  })

  return {
    categories,
    loading,
    error,
    refresh: fetchCategories
  }
}

export default useCategory
