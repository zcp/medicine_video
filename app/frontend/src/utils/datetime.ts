/**
 * 时间选择器工具函数
 * 用于抽屉组件和全屏页面的时间选择功能
 */

export interface DateTimePickerData {
  dateTimeRange: string[][];
  dateTimeValue: number[];
  displayDateTime: string;
}

function pad2(num: number): string {
  return String(num).padStart(2, '0');
}

/**
 * 后端 ISO 时间字符串 → 本地日期 YYYY-MM-DD
 * 用于列表/表单回显，避免直接 slice(0,10) 截取 UTC 日期导致少一天。
 * @param iso 后端返回的 ISO 字符串（如 2026-08-01T16:00:00.000Z 或带 +08:00 偏移）
 * @returns 本地日期字符串 YYYY-MM-DD，无效输入返回 null
 */
export function isoToLocalDateStr(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return null;
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

/**
 * 本地日期 YYYY-MM-DD → 带本地时区偏移的 ISO 字符串（如 2026-08-01T00:00:00+08:00）
 * 替代 new Date(x + 'T00:00:00').toISOString()（后者转成 UTC，日期会偏移）。
 * @param dateStr 本地日期字符串 YYYY-MM-DD
 * @returns 带时区偏移的 ISO 字符串
 */
export function localDateStrToISO(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return localDateToISO(d, 'start');
}

function localDateToISO(date: Date, boundary: 'start' | 'end' = 'start'): string {
  const d = new Date(date);
  if (boundary === 'start') {
    d.setHours(0, 0, 0, 0);
  } else {
    d.setHours(23, 59, 59, 999);
  }

  const offsetMinutes = -d.getTimezoneOffset();
  const offsetSign = offsetMinutes >= 0 ? '+' : '-';
  const offsetAbs = Math.abs(offsetMinutes);
  const offsetStr = `${offsetSign}${pad2(Math.floor(offsetAbs / 60))}:${pad2(offsetAbs % 60)}`;
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}${offsetStr}`;
}

/**
 * 后端 ISO 时间字符串 → 本地时间戳
 * 用于 wd-datetime-picker 的 v-model，避免字符串/数字混用导致组件内部范围计算异常。
 */
export function isoToLocalTimestamp(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return null;
  return d.getTime();
}

/**
 * 本地时间戳 → 本地日期 YYYY-MM-DD
 * 用于 wd-datetime-picker default slot 的表单展示。
 */
export function timestampToLocalDateStr(timestamp: number | null | undefined): string {
  if (!timestamp) return '';
  const d = new Date(timestamp);
  if (isNaN(d.getTime())) return '';
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

/**
 * 本地时间戳 → 带本地时区偏移的 ISO 字符串。
 * 上线时间取当天开始，下线时间取当天结束，保证“下线日期当天仍展示”。
 */
export function timestampToLocalDateISO(timestamp: number, boundary: 'start' | 'end' = 'start'): string {
  return localDateToISO(new Date(timestamp), boundary);
}

/**
 * 本地时间戳 → 带本地时区偏移的 ISO 字符串（保留时分秒原值，wd-datetime-picker datetime 精度专用）。
 * 注意区别于 timestampToLocalDateISO（整日边界 start/end），本函数不做边界截断。
 */
export function timestampToLocalDateTimeISO(timestamp: number): string {
  const d = new Date(timestamp);
  if (isNaN(d.getTime())) return '';

  const offsetMinutes = -d.getTimezoneOffset();
  const offsetSign = offsetMinutes >= 0 ? '+' : '-';
  const offsetAbs = Math.abs(offsetMinutes);
  const offsetStr = `${offsetSign}${pad2(Math.floor(offsetAbs / 60))}:${pad2(offsetAbs % 60)}`;
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}${offsetStr}`;
}

/**
 * ISO 时间字符串 → 中文时间显示文本（如「2026年9月2日 08时45分」）
 * 用于时间选择器触发区展示（与原生 multiSelector 时代的 getDisplayDateTime 输出格式对齐）。
 */
export function isoToLocalDateTimeDisplay(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return null;
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${pad2(d.getHours())}时${pad2(d.getMinutes())}分`;
}

/**
 * 初始化时间选择器数据（支持选择历史日期和年份）
 * @returns DateTimePickerData
 */
export function initDateTimePickerData(): DateTimePickerData {
  const years: string[] = [];
  const months: string[] = [];
  const days: string[] = [];
  const hours: string[] = [];
  const minutes: string[] = [];
  
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;
  const currentDay = now.getDate();
  
  // 生成年份：过去10年到未来2年（参考H5端）
  for (let i = currentYear - 10; i <= currentYear + 2; i++) {
    years.push(i + '年');
  }
  
  // 生成月份：1-12月
  for (let i = 1; i <= 12; i++) {
    months.push(i + '月');
  }
  
  // 生成日期：1-31日
  for (let i = 1; i <= 31; i++) {
    days.push(i + '日');
  }
  
  // 生成24小时
  for (let i = 0; i < 24; i++) {
    hours.push(i.toString().padStart(2, '0') + '时');
  }
  
  // 生成分钟（每5分钟一档）
  for (let i = 0; i < 60; i += 5) {
    minutes.push(i.toString().padStart(2, '0') + '分');
  }
  
  const dateTimeRange = [years, months, days, hours, minutes];
  
  // 设置默认时间为当前时间+30分钟
  now.setMinutes(now.getMinutes() + 30);
  const roundedMinutes = Math.ceil(now.getMinutes() / 5) * 5;
  now.setMinutes(roundedMinutes);
  
  const defaultYearIdx = 10; // 当前年份索引（过去10年 + 当前年）
  const defaultMonthIdx = currentMonth - 1;
  const defaultDayIdx = currentDay - 1;
  const defaultHour = now.getHours();
  const defaultMinute = Math.floor(now.getMinutes() / 5);
  
  const dateTimeValue = [defaultYearIdx, defaultMonthIdx, defaultDayIdx, defaultHour, defaultMinute];
  const displayDateTime = getDisplayDateTime(dateTimeRange, dateTimeValue);
  
  return {
    dateTimeRange,
    dateTimeValue,
    displayDateTime
  };
}

/**
 * 获取显示的时间文本
 * @param dateTimeRange 时间范围数组
 * @param dateTimeValue 选中的索引数组
 * @returns 格式化的时间字符串
 */
export function getDisplayDateTime(
  dateTimeRange: string[][],
  dateTimeValue: number[]
): string {
  const [yearIdx, monthIdx, dayIdx, hourIdx, minuteIdx] = dateTimeValue;
  const yearStr = dateTimeRange[0][yearIdx] || '';
  const monthStr = dateTimeRange[1][monthIdx] || '';
  const dayStr = dateTimeRange[2][dayIdx] || '';
  const hourStr = dateTimeRange[3][hourIdx] || '';
  const minuteStr = dateTimeRange[4][minuteIdx] || '';
  return `${yearStr}${monthStr}${dayStr} ${hourStr}${minuteStr}`;
}

/**
 * 将选择器值转换为ISO时间字符串（带时区）
 * @param dateTimeValue 选中的索引数组
 * @returns ISO格式的时间字符串，带时区信息（如 2026-02-01T20:00:00+08:00）
 */
export function dateTimeValueToISO(dateTimeValue: number[]): string {
  const [yearIdx, monthIdx, dayIdx, hourIdx, minuteIdx] = dateTimeValue;
  
  const now = new Date();
  const currentYear = now.getFullYear();
  
  // 计算实际年份（过去10年到未来2年）
  const year = currentYear - 10 + yearIdx;
  const month = monthIdx; // 月份0-11
  const day = dayIdx + 1; // 日期1-31
  
  const targetDate = new Date(year, month, day, hourIdx, minuteIdx * 5, 0, 0);
  
  // 获取时区偏移量（分钟）
  const timezoneOffset = -targetDate.getTimezoneOffset();
  const offsetHours = Math.floor(Math.abs(timezoneOffset) / 60);
  const offsetMinutes = Math.abs(timezoneOffset) % 60;
  const offsetSign = timezoneOffset >= 0 ? '+' : '-';
  
  // 格式化为 YYYY-MM-DDTHH:mm:ss+HH:mm
  const yearStr = targetDate.getFullYear();
  const monthStr = String(targetDate.getMonth() + 1).padStart(2, '0');
  const dayStr = String(targetDate.getDate()).padStart(2, '0');
  const hours = String(targetDate.getHours()).padStart(2, '0');
  const minutes = String(targetDate.getMinutes()).padStart(2, '0');
  const seconds = String(targetDate.getSeconds()).padStart(2, '0');
  
  return `${yearStr}-${monthStr}-${dayStr}T${hours}:${minutes}:${seconds}${offsetSign}${String(offsetHours).padStart(2, '0')}:${String(offsetMinutes).padStart(2, '0')}`;
}
