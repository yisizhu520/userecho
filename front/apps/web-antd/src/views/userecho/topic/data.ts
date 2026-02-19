import type { VbenFormSchema } from '#/adapter/form';
import type {
  OnActionClickFn,
  VxeGridProps,
} from '#/adapter/vxe-table';
import type { Topic } from '#/api';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';
import { TOPIC_CATEGORIES, TOPIC_STATUSES } from '#/api';

/** 查询表单配置 */
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'search_query',
    label: '主题搜索',
    componentProps: {
      placeholder: '搜索主题标题或描述（按 Enter 搜索）',
      allowClear: true,
    },
  },
  {
    component: 'RadioGroup',
    fieldName: 'search_mode',
    label: '搜索模式',
    defaultValue: 'keyword',
    componentProps: {
      options: [
        {
          label: '关键词 ⚡',
          value: 'keyword',
        },
        {
          label: '语义理解 🤖',
          value: 'semantic',
        },
      ],
      buttonStyle: 'solid',
      optionType: 'button',
      class: 'search-mode-radio',
    },
  },
  {
    component: 'Select',
    fieldName: 'status',
    label: '主题状态',
    componentProps: {
      allowClear: true,
      options: TOPIC_STATUSES,
      placeholder: '全部状态',
    },
  },
  {
    component: 'Select',
    fieldName: 'category',
    label: '主题分类',
    componentProps: {
      allowClear: true,
      options: TOPIC_CATEGORIES,
      placeholder: '全部分类',
    },
  },
];

/** 排序选项 */
export const sortOptions = [
  { label: '按创建时间', value: 'created_time' },
  { label: '按反馈数量', value: 'feedback_count' },
  { label: '按优先级评分', value: 'priority' },
];

/** 表格列配置 */
export function useColumns(
  onActionClick?: OnActionClickFn<Topic>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('common.table.id'),
      type: 'seq',
      fixed: 'left',
      width: 50,
    },
    {
      field: 'title',
      title: '主题标题',
      minWidth: 250,
      showOverflow: 'tooltip',
      slots: { default: 'title' },
    },
    {
      field: 'category',
      title: '分类',
      width: 120,
      slots: { default: 'category' },
    },
    {
      field: 'status',
      title: '状态',
      width: 120,
      slots: { default: 'status' },
    },
    {
      field: 'priority_score',
      title: '优先级',
      width: 120,
      sortable: true,
      slots: { default: 'priority_score' },
    },
    {
      field: 'feedback_count',
      title: '反馈数量',
      width: 100,
      sortable: true,
      slots: { default: 'feedback_count' },
    },
    {
      field: 'ai_generated',
      title: 'AI 生成',
      width: 100,
      slots: { default: 'ai_generated' },
    },
    {
      field: 'ai_confidence',
      title: 'AI 置信度',
      width: 120,
      formatter({ cellValue }) {
        return cellValue ? `${(cellValue * 100).toFixed(0)}%` : '-';
      },
    },
    {
      field: 'created_time',
      title: '创建时间',
      width: 168,
      sortable: true,
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 150,
      cellRender: {
        attrs: {
          nameField: 'title',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'detail',
            text: '查看详情',
            icon: 'lucide:eye',
          },
          'edit',
          {
            code: 'delete',
            popconfirm: {
              title: '确认删除此主题？',
            },
          },
        ],
      },
    },
  ];
}

/** 新建/编辑主题表单 */
export const topicFormSchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'title',
    label: '主题标题',
    rules: z.string().min(1, '请输入主题标题').max(100, '标题长度不能超过100字'),
    componentProps: {
      placeholder: '输入需求主题标题，建议15字以内',
      maxlength: 100,
      showCount: true,
    },
  },
  {
    component: 'Select',
    fieldName: 'category',
    label: '主题分类',
    rules: 'selectRequired',
    componentProps: {
      options: TOPIC_CATEGORIES,
      placeholder: '选择分类',
    },
    defaultValue: 'feature',
  },
  {
    component: 'Select',
    fieldName: 'status',
    label: '主题状态',
    componentProps: {
      options: TOPIC_STATUSES,
      placeholder: '选择状态',
    },
    defaultValue: 'pending',
  },
  {
    component: 'Textarea',
    fieldName: 'description',
    label: '主题描述',
    componentProps: {
      rows: 4,
      placeholder: '详细描述此需求主题...',
      maxlength: 500,
      showCount: true,
    },
  },
];

/** 状态更新表单 */
export const statusFormSchema: VbenFormSchema[] = [
  {
    component: 'Select',
    fieldName: 'status',
    label: '目标状态',
    rules: 'selectRequired',
    componentProps: {
      options: TOPIC_STATUSES,
      placeholder: '选择新状态',
    },
  },
  {
    component: 'Textarea',
    fieldName: 'reason',
    label: '变更原因',
    componentProps: {
      rows: 3,
      placeholder: '如：需求已完成开发并上线...',
      maxlength: 200,
    },
  },
];

/** 获取状态配置 */
export function getStatusConfig(status: string) {
  return TOPIC_STATUSES.find((s) => s.value === status) || TOPIC_STATUSES[0]!;
}

/** 获取分类配置 */
export function getCategoryConfig(category: string) {
  return TOPIC_CATEGORIES.find((c) => c.value === category) || TOPIC_CATEGORIES[4]!;
}

/** 分类图标映射 */
export const categoryIcons: Record<string, string> = {
  bug: '🐛',
  improvement: '✨',
  feature: '🚀',
  performance: '⚡',
  other: '📌',
};
