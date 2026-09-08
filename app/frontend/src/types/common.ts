/**
 * 通用类型定义
 * 阶段一新建：2025
 * 用于所有API接口的统一响应结构和查询参数
 */

/**
 * 统一API响应结构
 * @template T 响应数据的类型
 * @example
 * ```typescript
 * const response: ApiResponse<User> = {
 *   code: 200,
 *   message: 'success',
 *   data: { id: '123', name: 'John' },
 *   timestamp: '2025-10-23T10:00:00Z'
 * };
 * ```
 */
export interface ApiResponse<T = any> {
  /** 业务状态码：200=成功，2xxx=业务错误，3xxx=权限错误，4xxx=参数错误 */
  code: number;
  /** 响应消息 */
  message: string;
  /** 响应数据，成功时返回具体数据，失败时可能为null */
  data: T;
  /** 服务器响应时间戳（ISO 8601格式） */
  timestamp: string;
}

/**
 * 分页响应结构
 * @template T 分页项的类型
 * @example
 * ```typescript
 * const response: PaginatedResponse<Room> = {
 *   total: 100,
 *   page: 1,
 *   size: 10,
 *   items: [...]
 * };
 * ```
 */
export interface PaginatedResponse<T = any> {
  /** 总记录数 */
  total: number;
  /** 当前页码（从1开始） */
  page: number;
  /** 每页大小 */
  size: number;
  /** 数据项列表 */
  items: T[];
}

/**
 * API错误响应
 * 用于错误处理场景
 */
export interface ApiError {
  /** 错误状态码 */
  code: number;
  /** 错误消息 */
  message: string;
  /** 错误详情（可选） */
  details?: string;
  /** 错误时间戳 */
  timestamp: string;
}

/**
 * 基础查询参数
 * 用于分页查询
 */
export interface QueryParams {
  /** 页码（从1开始，默认1） */
  page?: number;
  /** 每页大小（默认10） */
  size?: number;
  /** 限制返回数量（部分API使用limit代替size） */
  limit?: number;
  /** 搜索关键词（部分API使用q代替search） */
  q?: string;
  /** 通用搜索关键词 */
  keyword?: string;
}

/**
 * 可搜索查询参数
 * 继承基础查询参数，增加搜索功能
 */
export interface SearchableQueryParams extends QueryParams {
  /** 搜索关键词 */
  search?: string;
}

/**
 * 可排序查询参数
 * 继承基础查询参数，增加排序功能
 */
export interface SortableQueryParams extends QueryParams {
  /** 排序字段 */
  order_by?: string;
  /** 排序方向：'asc'=升序，'desc'=降序 */
  order?: 'asc' | 'desc';
}
