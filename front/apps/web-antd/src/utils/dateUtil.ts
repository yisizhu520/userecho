import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

/**
 * 智能日期格式化 (3-Day Rule)
 * 
 * 规则：
 * 1. 小于3天：显示相对时间（如“2小时前”，“昨天”）
 * 2. 大于等于3天且是当年：显示“MM-DD”（如“01-15”）
 * 3. 跨年：显示“YYYY-MM-DD”（如“2025-01-15”）
 * 
 * @param dateStr 日期字符串或 Date 对象
 * @returns 格式化后的字符串
 */
export function formatToSmartTime(dateStr: string | Date | undefined | null): string {
    if (!dateStr) return '-';

    const date = dayjs(dateStr);
    const now = dayjs();

    // 确保日期有效
    if (!date.isValid()) return '-';

    const diffDays = now.diff(date, 'day');

    // 3天内显示相对时间
    if (diffDays < 3) {
        return date.fromNow();
    }

    // 跨年显示完整日期
    if (date.year() !== now.year()) {
        return date.format('YYYY-MM-DD');
    }

    // 当年显示月日
    return date.format('MM-DD');
}

/**
 * 格式化为完整日期时间 (Tooltip 用)
 * @param dateStr 
 * @returns YYYY-MM-DD HH:mm:ss
 */
export function formatToDateTime(dateStr: string | Date | undefined | null): string {
    if (!dateStr) return '';
    const date = dayjs(dateStr);
    if (!date.isValid()) return '';
    return date.format('YYYY-MM-DD HH:mm:ss');
}
